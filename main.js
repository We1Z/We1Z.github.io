/* ============================================================
   WEI ZENG — PORTFOLIO · main.js
   Content lives in the DATA objects below.
   To add a project: copy an object, change the fields.
   Old dark-terminal version: git show 81d683e:main.js
   ============================================================ */

/* ---------- SELECTED WORK ---------- */
const work = [
  { title: "NBB Asset Manager — Blender Pipeline Addon",
    img: "assets/work/nbb_asset_manager.jpg",
    alt: "NBB Asset Manager — scan-based asset pipeline addon for Blender",
    href: "projects/nbb-asset-manager.html",
    wide: true }
];

/* ---------- ORIGINS (ArtStation archive) ---------- */
const origins = [
  { title: "PrimoGem — Genshin Impact", tools: "Maya · Substance · UE Material Graph", img: "assets/work/primogem.jpg", href: "https://www.artstation.com/artwork/1xLwvZ" },
  { title: "Widebody Cyber Jeep", tools: "Maya · Substance Painter", img: "assets/work/cyberjeep.jpg", href: "https://www.artstation.com/artwork/3q9EGD" },
  { title: "Moonshot — Destiny 2 Hand Cannon", tools: "Maya · Substance Painter", img: "assets/work/moonshot.jpg", href: "https://www.artstation.com/artwork/3dO3YB" },
  { title: "Desert Eagle — Clips & Bullets", tools: "Maya · Substance · Unreal", img: "assets/work/deagle.jpg", href: "https://www.artstation.com/artwork/Rn0JJX" },
  { title: "Bat Mutant — Creature Rig", tools: "Maya · ZBrush · Substance", img: "assets/work/batmutant.jpg", href: "https://www.artstation.com/artwork/oAgbxz" },
  { title: "Tokyo Takeover — Mall Environments", tools: "Unity · Maya · Substance", img: "assets/work/tokyotakeover.jpg", href: "https://www.artstation.com/artwork/WKNPAJ" },
  { title: "Lightsaber — Realtime Prop", tools: "Hard Surface · Realtime", img: "assets/work/lightsaber.jpg", href: "https://www.artstation.com/artwork/J9myqd" }
];

/* ---------- EXPERIENCE ---------- */
const experience = [
  { role: "Unreal Pipeline TD", org: "WildBrain Studios", date: "2023 — Present",
    desc: "Production tools on the studio Unreal pipeline framework — asset & shot importers, crowd VAT baking, light rigs, turntable actions, light mixer — plus C++ framework extensions (enum editing, blueprint components). Python 3.11, ShotGrid, Perforce, farm." },
  { role: "Technical Artist", org: "WildBrain — Strawberry Shortcake 3D", date: "2022 — 2023",
    desc: "Cross-department asset & workflow support, Unreal tools, materials, FX and render fixes." },
  { role: "Unreal Generalist", org: "BRON Studios", date: "2022",
    desc: "Virtual production scene setup, optimization, virtual-camera integration and render QC in UE4." },
  { role: "Cinematic Designer", org: "IGG Canada — Lords Mobile", date: "2021",
    desc: "Storyboards and trailer assembly across live-action, gameplay and animated footage." },
  { role: "Lab Analyst → QA Officer", org: "ALS Environmental · Bio-Chem Consulting", date: "2018 — 2020",
    desc: "HPLC / ICP-MS method development, instrument troubleshooting, SOPs and ISO 17025 audits." }
];

/* ---------- EDUCATION ---------- */
const education = [
  { role: "Technical Artist Diploma", org: "British Columbia Institute of Technology", date: "2023 — 2024" },
  { role: "Game Design Diploma", org: "Vancouver Film School", date: "2020 — 2021" },
  { role: "BSc Chemistry", org: "University of Calgary", date: "2014 — 2018" }
];

/* ---------- SKILLS (grouped) ---------- */
const skills = [
  { group: "Pipeline & Code", items: ["Python", "JSON", "Git", "ShotGrid / sgtk", "Perforce"] },
  { group: "Engines & DCC", items: ["Unreal Engine 5", "Maya", "Houdini", "Blender", "Unity", "ZBrush", "Substance Suite"] },
  { group: "3D Craft", items: ["Hard-Surface Modeling", "Character Rigging", "Texturing & Surfacing", "Lighting & Rendering", "Set Dressing", "Realtime Materials"] }
];

/* ---------- RENDER ---------- */

/* Selected Work — image cards (ready for data) */
document.getElementById("workGrid").innerHTML = work.length === 0
  ? `<p class="workgrid__empty reveal">Case studies in curation — new writeups shipping soon.</p>`
  : work.map((item, i) => `
    <figure class="wcard${item.wide ? " wcard--wide" : ""} reveal" style="--d:${Math.min(i * .07, .28)}s">
      ${item.href ? `<a href="${item.href}"${/^https?:/.test(item.href) ? ' target="_blank" rel="noopener"' : ""}>` : ""}
        <img src="${item.img}" alt="${item.alt || item.title}" loading="lazy" />
        <figcaption><span>${item.title}</span><span class="wcard__arrow">→</span></figcaption>
      ${item.href ? `</a>` : ""}
    </figure>`).join("");

/* Origins — ArtStation grid */
document.getElementById("originsGrid").innerHTML = origins.map((item, i) => `
  <a class="ocell reveal" href="${item.href}" target="_blank" rel="noopener" style="--d:${Math.min(i * .06, .3)}s">
    <img src="${item.img}" alt="${item.title}" loading="lazy" />
    <span class="ocell__cap">
      <span>${item.title}<br /><small>${item.tools}</small></span>
      <span class="ocell__arrow">→</span>
    </span>
  </a>`).join("");

/* Experience — numbered rows */
document.getElementById("expList").innerHTML = experience.map((e, i) => `
  <div class="xrow reveal" style="--d:${Math.min(i * .05, .2)}s">
    <span class="xrow__num">0${i + 1}</span>
    <h3 class="xrow__role">${e.role}</h3>
    <p class="xrow__org">${e.org}<span>${e.date}</span></p>
    <p class="xrow__desc">${e.desc}</p>
  </div>`).join("");

/* Education — numbered rows */
document.getElementById("eduList").innerHTML = education.map((e, i) => `
  <div class="xrow xrow--plain reveal" style="--d:${Math.min(i * .05, .2)}s">
    <span class="xrow__num">0${i + 1}</span>
    <h3 class="xrow__role">${e.role}</h3>
    <p class="xrow__org">${e.org}<span>${e.date}</span></p>
  </div>`).join("");

/* Skills — grouped chips */
document.getElementById("skillsGrid").innerHTML = `<div class="sgroups">` + skills.map((g, gi) => `
  <div class="sgroup reveal" style="--d:${gi * .08}s">
    <h3 class="sgroup__label">${g.group}</h3>
    <div class="sgroup__chips">${g.items.map(s => `<span class="chip">${s}</span>`).join("")}</div>
  </div>`).join("") + `</div>`;

/* ---------- day / night toggle ---------- */
(function () {
  const btn = document.getElementById("themeToggle");
  const rootEl = document.documentElement;
  function apply(pal) {
    if (!pal) return;
    for (const k in pal) if (!k.startsWith("_")) rootEl.style.setProperty("--" + k, pal[k]);
  }
  btn.addEventListener("click", () => {
    const night = rootEl.getAttribute("data-theme") !== "night";
    if (night) rootEl.setAttribute("data-theme", "night");
    else rootEl.removeAttribute("data-theme");
    try { localStorage.setItem("wz-theme", night ? "night" : "day"); } catch (e) {}
    /* theme.json palettes take precedence over stylesheet defaults */
    if (window.__wzTheme) apply(window.__wzTheme[night ? "night" : "day"] || window.__wzTheme.day);
  });
})();

/* ---------- footer: year + Vancouver clock ---------- */
(function () {
  document.getElementById("year").textContent = new Date().getFullYear();
  const clock = document.getElementById("footClock");
  const fmt = new Intl.DateTimeFormat("en-CA", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "America/Vancouver" });
  const tick = () => { clock.textContent = fmt.format(new Date()); };
  tick();
  setInterval(tick, 30000);
})();

/* ---------- scroll reveal: adds .is-in when .reveal enters viewport ---------- */
(function () {
  const els = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    els.forEach(el => el.classList.add("is-in"));
    return;
  }
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
  els.forEach(el => io.observe(el));
})();

/* ---------- hero name: magnetic letters ----------
   Splits the h1 into spans; letters near the cursor are pushed
   away and tinted with the theme accent, then drift back. */
(function () {
  const nameEl = document.querySelector(".hero__name");
  if (!nameEl || matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const text = nameEl.textContent.trim();
  nameEl.setAttribute("aria-label", text);
  nameEl.textContent = "";
  const letters = [...text].map(ch => {
    const s = document.createElement("span");
    s.textContent = ch;
    s.setAttribute("aria-hidden", "true");
    if (ch === " ") s.style.whiteSpace = "pre";
    nameEl.appendChild(s);
    return s;
  });

  const RADIUS = 170;   // influence distance from cursor (px)
  const PUSH = 0.6;     // horizontal repel strength
  const LIFT = 14;      // max upward drift for the closest letter (px)
  let raf = 0, mx = 0, my = 0, active = false, centers = null;

  const measure = () =>
    letters.map(s => {
      const r = s.getBoundingClientRect();
      return r.left + r.width / 2;
    });

  const apply = () => {
    raf = 0;
    if (active && centers === null) centers = measure();
    letters.forEach((s, i) => {
      if (!active || centers === null) { s.style.transform = ""; s.style.color = ""; return; }
      const r = s.getBoundingClientRect();
      const cy = r.top + r.height / 2;
      const dx = centers[i] - mx, dy = cy - my;
      const dist = Math.hypot(dx, dy);
      if (dist >= RADIUS) { s.style.transform = ""; s.style.color = ""; return; }
      const f = 1 - dist / RADIUS;              // 0 at edge, 1 at cursor
      const ux = dist > 0.01 ? dx / dist : (i % 2 ? 1 : -1);
      s.style.transform =
        `translate(${(ux * f * f * RADIUS * PUSH).toFixed(1)}px, ${(-f * LIFT).toFixed(1)}px)`;
      s.style.color = f > 0.5 ? "var(--sky)" : "";
    });
  };

  nameEl.addEventListener("mouseenter", () => { centers = null; });
  nameEl.addEventListener("mousemove", e => {
    mx = e.clientX; my = e.clientY; active = true;
    if (!raf) raf = requestAnimationFrame(apply);
  });
  nameEl.addEventListener("mouseleave", () => {
    active = false; centers = null;
    if (!raf) raf = requestAnimationFrame(apply);
  });
})();
