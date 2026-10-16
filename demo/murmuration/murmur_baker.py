"""
Murmuration — Crowd VAT (Vertex Animation Texture) baker
=========================================================

An original, portfolio-grade demo by Wei Zeng. Mirrors the crowd-VAT baking
workflow I built for production: skeletal/clip animation is baked into textures
so thousands of characters can play back on the GPU with one draw call.

Here the animation source is a fully self-contained boids flocking simulation
(no source assets, no studio data). The bake is the real thing:

    boids sim (frames × agents × xyz)
        -> 16-bit POSITION texture   one column per agent, one row per frame
        -> 16-bit DIRECTION texture  normalized velocity per agent/frame
        -> quad mesh OBJ             one camera-facing card per agent,
                                     UV.x identifies the agent texel
        -> header JSON               fps, frames, texel mapping, bounds,
                                     decode rules consumed by the UE importer

Texture convention (matches Unreal import): frame 0 lives on the BOTTOM row,
so material UV.y = frame / (frames - 1).

Run (plain Python 3, needs numpy + Pillow):

    python3 murmur_baker.py --out baked
    python3 murmur_baker.py --boids 120 --frames 256 --fps 24 --out baked
    python3 murmur_baker.py --out baked --preview baked/preview.jpg

Outputs land in --out:
    VAT_Murmuration_Pos.png  (uint16, width × height)
    VAT_Murmuration_Dir.png  (uint16)
    VAT_Murmuration_Mesh.obj (boids × one quad)
    VAT_Murmuration_Header.json
    preview.jpg              (only with --preview)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import struct
import zlib
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def save_png16(path: str, arr: np.ndarray) -> None:
    """Write a 48-bit RGB PNG (uint16 samples) without external deps.
    Pillow has no writer for this mode, so encode the chunks directly.
    PNG stores 16-bit samples big-endian."""
    height, width, _ = arr.shape
    be = arr.astype(">u2")
    scanlines = b"".join(b"\x00" + be[y].tobytes() for y in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        head = tag + data
        return (struct.pack(">I", len(data)) + head
                + struct.pack(">I", zlib.crc32(head) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 16, 2, 0, 0, 0)
    with open(path, "wb") as fh:
        fh.write(b"\x89PNG\r\n\x1a\n")
        fh.write(chunk(b"IHDR", ihdr))
        fh.write(chunk(b"IDAT", zlib.compress(scanlines, 6)))
        fh.write(chunk(b"IEND", b""))


# --------------------------------------------------------------------------- #
#  Boids simulation (vectorized)
# --------------------------------------------------------------------------- #

@dataclass
class SimConfig:
    boids: int = 224
    frames: int = 256
    fps: int = 24
    seed: int = 20261002
    world: float = 260.0          # flock lives in a cube roughly ±world/2 (cm-ish)
    perception: float = 46.0      # neighbor radius
    max_speed: float = 54.0       # cm / s
    sep_radius: float = 14.0
    dt: float = 1.0 / 24.0


def simulate(cfg: SimConfig) -> np.ndarray:
    """Return positions array of shape (frames, boids, 3), float, world units."""
    rng = np.random.default_rng(cfg.seed)
    n = cfg.boids

    pos = rng.uniform(-cfg.world * 0.32, cfg.world * 0.32, size=(n, 3))
    vel = rng.normal(0, 1, size=(n, 3))
    vel /= np.linalg.norm(vel, axis=1, keepdims=True)
    vel *= cfg.max_speed * 0.6

    frames = np.empty((cfg.frames, n, 3), dtype=np.float64)
    dt = cfg.dt

    for f in range(cfg.frames):
        frames[f] = pos

        # Pairwise deltas (n,n,3) — demo scale (a few hundred agents), keep simple.
        delta = pos[:, None, :] - pos[None, :, :]
        dist = np.linalg.norm(delta, axis=2)
        np.fill_diagonal(dist, np.inf)

        nb = dist < cfg.perception
        nb_count = np.maximum(nb.sum(axis=1), 1)

        # Separation — push away from very close neighbors.
        close = dist < cfg.sep_radius
        sep_vec = np.where(close[:, :, None], delta, 0.0).sum(axis=1)

        # Alignment — steer toward average neighbor heading.
        align = (nb[:, :, None] * vel[None, :, :]).sum(axis=1) / nb_count[:, None]

        # Cohesion — steer toward average neighbor position.
        center = (nb[:, :, None] * pos[None, :, :]).sum(axis=1) / nb_count[:, None]
        cohesion = center - pos

        # Gentle gravity toward the flock centroid keeps it a tight murmuration.
        centroid = pos.mean(axis=0)
        home = (centroid - pos) * 0.35

        acc = (sep_vec * 2.4
               + align * 0.55
               + cohesion * 0.9
               + home)

        # Soft wind curl so the flock turns instead of collapsing into a ball.
        t = f * dt
        acc += np.array([math.sin(t * 0.7) * 26.0,
                         math.cos(t * 0.5) * 18.0,
                         math.sin(t * 0.33 + 1.2) * 22.0])

        vel += acc * dt
        speed = np.linalg.norm(vel, axis=1, keepdims=True)
        vel = np.where(speed > cfg.max_speed,
                       vel / speed * cfg.max_speed, vel)
        pos = pos + vel * dt

        # Soft bounds: steer back inside the world cube.
        over = np.abs(pos) > cfg.world * 0.5
        vel -= np.where(over, np.sign(pos) * cfg.max_speed * 1.6 * dt, 0.0)

    return frames


# --------------------------------------------------------------------------- #
#  Bake
# --------------------------------------------------------------------------- #

@dataclass
class BakeResult:
    pos_png: str
    dir_png: str
    obj: str
    header: dict
    pos_rows01: np.ndarray   # frame-0-bottom normalized VAT, for previewing


def _u16(values01: np.ndarray) -> np.ndarray:
    return np.rint(np.clip(values01, 0.0, 1.0) * 65535.0).astype(np.uint16)


def bake(positions: np.ndarray, cfg: SimConfig, out_dir: str) -> BakeResult:
    frames, n, _ = positions.shape

    # Padding makes the texture width a power of two (GPU-friendly).
    width = 1 << (n - 1).bit_length()
    height = frames

    padded = np.zeros((frames, width, 3), dtype=np.float64)
    padded[:, :n, :] = positions

    # Directions = normalized per-frame velocity; last frame copies its predecessor.
    delta = np.diff(padded, axis=0, prepend=padded[:1])
    norms = np.linalg.norm(delta, axis=2, keepdims=True)
    direction = np.where(norms > 1e-6, delta / np.maximum(norms, 1e-6), 0.0)

    # Bounds from real agents only, with a little headroom (world units = cm here).
    lo = positions.reshape(-1, 3).min(axis=0) - 6.0
    hi = positions.reshape(-1, 3).max(axis=0) + 6.0
    size = np.maximum(hi - lo, 1e-6)

    pos01 = (padded - lo) / size
    dir01 = direction * 0.5 + 0.5

    # Frame 0 on the BOTTOM row to match Unreal's UV origin.
    pos_rows = pos01[::-1]
    dir_rows = dir01[::-1]

    os.makedirs(out_dir, exist_ok=True)
    pos_png = os.path.join(out_dir, "VAT_Murmuration_Pos.png")
    dir_png = os.path.join(out_dir, "VAT_Murmuration_Dir.png")
    obj_path = os.path.join(out_dir, "VAT_Murmuration_Mesh.obj")

    save_png16(pos_png, _u16(pos_rows))
    save_png16(dir_png, _u16(dir_rows))
    _write_card_mesh(obj_path, n, width, card_cm=10.0)

    header = {
        "tool": "Murmuration",
        "version": 1,
        "content": "procedural boids crowd — original demo data",
        "fps": cfg.fps,
        "frame_count": frames,
        "agent_count": n,
        "texture": {
            "width": width,
            "height": height,
            "format": "uint16",
            "frame_0_row": "bottom",
            "agent": "column x = (agent_index + 0.5) / width",
            "frame": "row y = frame / (frame_count - 1)"
        },
        "position": {
            "texture": os.path.basename(pos_png),
            "encoding": "rgb = (position_cm - bounds_min) / bounds_size",
            "bounds_min_cm": [round(float(v), 3) for v in lo],
            "bounds_size_cm": [round(float(v), 3) for v in size]
        },
        "direction": {
            "texture": os.path.basename(dir_png),
            "encoding": "rgb = normalize(velocity) * 0.5 + 0.5"
        },
        "mesh": os.path.basename(obj_path),
        "playback": {
            "scalar_parameter": "Frame",
            "range": [0, frames - 1],
            "loop": True
        }
    }
    header_path = os.path.join(out_dir, "VAT_Murmuration_Header.json")
    with open(header_path, "w", encoding="utf-8") as fh:
        json.dump(header, fh, indent=2)

    return BakeResult(pos_png, dir_png, obj_path, header, pos_rows)


def _write_card_mesh(path: str, n: int, width: int, card_cm: float) -> None:
    """One flat quad per agent, all authored at the local origin. UV.x carries
    the agent's texel column; the material adds the VAT position via WPO."""
    h = card_cm * 0.5
    corners = [(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)]
    lines = ["# Murmuration VAT card mesh — original demo",
             f"# {n} agents, texture width {width}"]
    for i in range(n):
        u = (i + 0.5) / width
        for x, y, z in corners:
            lines.append(f"v {x:.4f} {y:.4f} {z:.4f}")
        for _ in corners:
            lines.append(f"vt {u:.6f} 0.000000")
    for i in range(n):
        b = i * 4 + 1
        lines.append(f"f {b}/{b} {b+1}/{b+1} {b+2}/{b+2} {b+3}/{b+3}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- #
#  Contact-sheet preview (also used as the portfolio case image)
# --------------------------------------------------------------------------- #

def _site_palette() -> tuple:
    """Read the portfolio theme.json (two levels up) so the preview matches the
    site. Falls back to the built-in Jedi green when run standalone."""
    theme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "..", "theme.json")
    fallback = {
        "ink": "#070d09", "panel": "#0e1a12", "bone": "#e8f7ec",
        "dim": "#718a79", "blue": "#2ee07a", "blue-deep": "#0f9d58",
    }
    try:
        with open(theme_path, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        theme = cfg["themes"][cfg["active"]]
        merged = {**fallback, **theme}
        return merged
    except Exception:
        return fallback


def _hex_rgb(value: str) -> tuple:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def make_preview(positions: np.ndarray, pos_rows01: np.ndarray,
                 header: dict, path: str) -> None:
    W, H = 1600, 980
    pal = _site_palette()
    bg = _hex_rgb(pal["ink"])
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    font_m = _font(22)
    font_s = _font(15)
    font_xs = _font(13)

    cyan = _hex_rgb(pal["blue"])       # site accent (theme.json)
    cyan_dim = _hex_rgb(pal["blue-deep"])
    white = _hex_rgb(pal["bone"])
    grey = _hex_rgb(pal["dim"])
    outline = tuple(int(bg[i] + (cyan[i] - bg[i]) * 0.28) for i in range(3))

    d.text((48, 40), "MURMURATION", font=font_m, fill=white)
    d.text((48, 72), "CROWD VAT BAKER — GPU INSTANCED PLAYBACK", font=font_s, fill=cyan)

    # Left: the actual position VAT (from the in-memory bake), nearest-neighbor.
    tex_rgb = Image.fromarray((pos_rows01 * 255).astype(np.uint8))
    box = 340
    tex_big = tex_rgb.resize((box, box), Image.NEAREST)
    tx, ty = 48, 150
    d.rectangle((tx - 10, ty - 10, tx + box + 10, ty + box + 10),
                outline=outline)
    img.paste(tex_big, (tx, ty))
    d.text((tx, ty + box + 16), "POSITION VAT", font=font_s, fill=white)
    d.text((tx, ty + box + 40),
           f'{header["texture"]["width"]}x{header["texture"]["height"]} · uint16 · column = agent, row = frame',
           font=font_xs, fill=grey)

    # Right: three frames of the flock projected to 2D, with short trails.
    frames_i = [header["frame_count"] // 6,
                header["frame_count"] // 2,
                header["frame_count"] * 5 // 6]
    pw, ph = 620, 220
    px0 = 460
    for k, fi in enumerate(frames_i):
        py0 = 150 + k * (ph + 34)
        d.rectangle((px0 - 10, py0 - 10, px0 + pw + 10, py0 + ph + 10),
                    outline=outline)
        _draw_frame(d, positions, fi, px0, py0, pw, ph, cyan, cyan_dim, grey)
        d.text((px0, py0 + ph + 8),
               f"FRAME {fi:03d} / {header['frame_count']-1} · "
               f'{header["agent_count"]} AGENTS · {header["fps"]} FPS',
               font=font_xs, fill=grey)

    img.save(path, quality=90)


def _draw_frame(d: ImageDraw.ImageDraw, positions: np.ndarray, fi: int,
                x0: int, y0: int, w: int, h: int,
                cyan: tuple, cyan_dim: tuple, grey: tuple) -> None:
    # Slight 3D camera rotation around the Z axis for depth.
    a = 0.6
    ca, sa = math.cos(a), math.sin(a)
    p = positions[max(0, fi - 8): fi + 1]
    trail_len = p.shape[0]
    flat_x = p[..., 0] * ca - p[..., 1] * sa
    flat_y = p[..., 2]
    lo = min(flat_x.min(), flat_y.min()) - 4
    hi = max(flat_x.max(), flat_y.max()) + 4

    def map2(x, y):
        return (x0 + (x - lo) / (hi - lo) * w,
                y0 + h - (y - lo) / (hi - lo) * h)

    for ti in range(trail_len - 1):
        k = ti / trail_len
        col = tuple(int(grey[i] + (cyan[i] - grey[i]) * k) for i in range(3))
        for agent in range(p.shape[1]):
            x1, y1 = map2(flat_x[ti, agent], flat_y[ti, agent])
            x2, y2 = map2(flat_x[ti + 1, agent], flat_y[ti + 1, agent])
            d.line((x1, y1, x2, y2), fill=col, width=1)

    for agent in range(positions.shape[1]):
        x, y = map2(flat_x[-1, agent], flat_y[-1, agent])
        d.ellipse((x - 1.6, y - 1.6, x + 1.6, y + 1.6), fill=cyan)


def _font(size: int):
    for cand in ("/System/Library/Fonts/Menlo.ttc",
                 "/System/Library/Fonts/SFNSMono.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"):
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size)
            except OSError:
                continue
    return ImageFont.load_default()


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description="Murmuration — crowd VAT baker (demo)")
    ap.add_argument("--boids", type=int, default=224)
    ap.add_argument("--frames", type=int, default=256)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--seed", type=int, default=20261002)
    ap.add_argument("--out", default="baked", help="output directory")
    ap.add_argument("--preview", help="optional contact-sheet JPG path")
    args = ap.parse_args()

    cfg = SimConfig(boids=args.boids, frames=args.frames, fps=args.fps, seed=args.seed)
    print(f"Simulating {cfg.boids} boids × {cfg.frames} frames …")
    positions = simulate(cfg)

    result = bake(positions, cfg, args.out)
    h = result.header
    print(f"Baked {h['agent_count']} agents / {h['frame_count']} frames "
          f"into {h['texture']['width']}x{h['texture']['height']} uint16 VAT")
    print(f"  {result.pos_png}")
    print(f"  {result.dir_png}")
    print(f"  {result.obj}")
    print(f"  {os.path.join(args.out, 'VAT_Murmuration_Header.json')}")

    if args.preview:
        make_preview(positions, result.pos_rows01, h, args.preview)
        print(f"  {args.preview}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
