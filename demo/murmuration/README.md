# Murmuration — Crowd VAT Baker (Demo)

An original demo by Wei Zeng. It mirrors the production crowd-VAT workflow I
built — baking animation into textures so a whole crowd plays back on the GPU
with a single draw call — without any studio code or data. The animation source
here is a self-contained boids flocking simulation.

## Pipeline

```
murmur_baker.py (plain Python 3: numpy + Pillow)
  procedural boids sim
      ├─ VAT_Murmuration_Pos.png   48-bit (uint16/channel) RGB, column = agent, row = frame
      ├─ VAT_Murmuration_Dir.png   normalized velocity per agent/frame
      ├─ VAT_Murmuration_Mesh.obj  one quad card per agent, UV.x = agent texel
      └─ VAT_Murmuration_Header.json   fps · frames · bounds · decode rules

ue_import_vat.py (in the Unreal editor)
      imports textures + mesh, builds the decode material graph:
      UV = (vertex.u, Frame/(frames-1))
      WPO = bounds_min + PosTex.rgb * bounds_size
      Emissive = DirTex.rgb * 0.2   (heading tint)
      + MI_VAT_Murmuration instance with a drivable Frame scalar
```

## Bake (outside Unreal, fully runnable)

```bash
pip install numpy pillow
python3 murmur_baker.py --out baked --preview baked/preview.jpg
```

Options: `--boids 224 --frames 256 --fps 24 --seed 20261002`. Texture width
pads to a power of two. Frame 0 is written to the bottom row to match Unreal's
UV origin. The 16-bit PNG is encoded with a small hand-rolled PNG writer
(Pillow can't write 48-bit RGB), so there are no heavyweight image deps.

## Apply (inside Unreal)

Enable the Python Editor Script Plugin, then Output Log → Cmd:

```
py ue_import_vat.py --header baked/VAT_Murmuration_Header.json
py ue_import_vat.py --header baked/VAT_Murmuration_Header.json --commit
```

Drop **SM_VAT_Murmuration** in a level with **MI_VAT_Murmuration** on it. Drive
the `Frame` scalar 0 → 255 (looping) from a Timeline or Blueprint for playback;
224 cards then follow independent baked paths via World Position Offset.

## Why it exists

My production crowd system converts skeletal animation to VAT (bake resolution
auto-fit, skeletal→static conversion, lightmap UVs). That code is confidential,
so Murmuration independently demonstrates the same core skills: simulation/
bake math, fixed-point texture encoding, header-driven interchange, and
automated Unreal material graph construction.
