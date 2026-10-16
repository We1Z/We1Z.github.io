/* ============================================================
   WEI ZENG — PORTFOLIO · main.js
   Content lives in the DATA objects below.
   To add a project: copy an object, change the fields.
   Old dark-terminal version: git show 81d683e:main.js
   ============================================================ */

/* ---------- SELECTED WORK ----------
   Empty while the section is replanned. Card markup is ready:
   add { title, img, alt, href, wide:true? } and the grid renders. */
const work = [];

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
  { role: "Technical Artist Certificate", org: "British Columbia Institute of Technology", date: "2023 — 2024" },
  { role: "Game Design Diploma", org: "Vancouver Film School", date: "2020 — 2021" },
  { role: "BSc Chemistry", org: "University of Calgary", date: "2014 — 2018" }
];

/* ---------- SKILLS ---------- */
const skills = [
  "Python", "MEL", "Bash / Shell", "JSON · YAML", "Git · GitLab CI",
  "Unreal Engine 5", "Maya", "Houdini", "Blender", "Unity", "ZBrush", "Substance Suite",
  "ShotGrid / sgtk", "Perforce", "Environment & Build Systems",
  "Hard-Surface Modeling", "Character Rigging", "Texturing & Surfacing",
  "Lighting & Rendering", "Set Dressing", "Realtime Materials"
];

/* ---------- RENDER ---------- */

/* Selected Work — image cards (ready for data) */
document.getElementById("workGrid").innerHTML = work.length === 0
  ? `<p class="workgrid__empty reveal">Case studies in curation — new writeups shipping soon.</p>`
  : work.map((item, i) => `
    <figure class="wcard${item.wide ? " wcard--wide" : ""} reveal" style="--d:${Math.min(i * .07, .28)}s">
      ${item.href ? `<a href="${item.href}" target="_blank" rel="noopener">` : ""}
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

/* Skills — sky-block mosaic */
document.getElementById("skillsGrid").innerHTML = skills.map((s, i) => `
  <div class="sblock reveal" style="--d:${Math.min(i * .04, .32)}s">
    <span class="sblock__icon">✚</span>
    <span class="sblock__label">${s}</span>
  </div>`).join("");

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
