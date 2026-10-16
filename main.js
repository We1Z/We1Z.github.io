/* ============================================================
   WEI ZENG — PORTFOLIO · main.js
   Content lives in the DATA objects below.
   To add a new project: copy an object, change the fields.
   ============================================================ */

/* ---------- 01 · SELECTED WORK ---------- */
const work = [
  {
    kind: "featured",
    date: "2023 — PRESENT",
    code: "UE-PIPE-TD",
    org: "WILDBRAIN STUDIOS · VANCOUVER",
    title: "Unreal Production Tools on the Studio Pipeline Framework",
    desc: "The studio's Unreal pipeline framework was built by a colleague; I build the production tool layer on top of it and feed improvements back down. Six tools in daily use: asset & shot importers, crowd VAT baking, light rig workflow, turntable scripted actions, and a light mixer — plus custom C++ where Python can't reach. UE 5.8, wired into ShotGrid, Perforce and the render farm.",
    tags: ["Unreal Engine 5.8", "Python 3.11", "C++ / Blueprint Function Libraries", "Asset & Shot Importers", "VAT Crowd Baking", "Light Rig · Light Mixer", "ShotGrid · Perforce"],
    visual: "nodemap",
    link: null,
    writeup: [
      { label: "Problem", text: "The framework supplies the plumbing — menus, bootstrap, shared APIs — but artists still need show-floor tools: getting assets and shots into the engine, baking crowds, building and mixing light rigs, and turning turntables. Done by hand, those jobs ate artist hours every day." },
      { label: "Approach", text: "Built six production tools on the framework in Python, and extended the framework itself where the editor exposed no API: custom C++ Blueprint Function Libraries exposing User-Defined Enum editing and Blueprint component manipulation (add / reparent / inherited-template overrides), plus a crowd VAT baker — skeletal animation baked to vertex-animation textures with auto-fit bake resolution and skeletal→static mesh conversion. Daily scripting keeps feeding fixes and utilities back into the shared framework." },
      { label: "Result", text: "Import, crowd, lighting and turntable work that used to be manual is now one-click and repeatable on the show — and every new tool lands on a framework that gets stronger with each production." }
    ]
  },
  {
    kind: "case",
    date: "2022 — 2023",
    code: "TECH-ART",
    org: "WILDBRAIN STUDIOS · STRAWBERRY SHORTCAKE 3D SPECIALS",
    title: "Technical Artist on a Netflix-bound series",
    desc: "Kept assets and workflows healthy across departments — rigging, surfacing, modeling and render fixes (lighting glitches, render presets) — and built Unreal Blueprints, Editor Utility Widgets, material functions and FX to automate the repetitive and invent the new. Aired on Family Jr in Canada and Netflix in the US.",
    tags: ["Unreal Engine", "Blueprints", "Editor Utility Widgets", "Materials & FX", "Maya", "Arnold"],
    visual: "dossier",
    link: { label: "VIEW ON IMDB", href: "https://www.imdb.com/title/tt29389870/" }
  },
  {
    kind: "case",
    date: "2022",
    code: "VIRTUAL-PROD",
    org: "BRON STUDIOS · VANCOUVER",
    title: "UE Generalist for Virtual Production",
    desc: "Scene assembly, debugging and performance optimization in UE4 for the virtual-production stage; render-footage setup and QC; virtual-camera data integration. Made rapid technical changes — lighting, animation, set dressing, color correction — to hit the key creatives' goals in an iterative, on-set-paced pipeline.",
    tags: ["UE4", "Virtual Camera", "Scene Optimization", "Lighting", "Render QC"],
    visual: "dossier",
    link: null
  },
  {
    kind: "case",
    date: "2021",
    code: "CINEMATICS",
    org: "IGG CANADA · LORDS MOBILE UA TEAM",
    title: "Cinematic Designer",
    desc: "Storyboarded marketing content and assembled live-action, gameplay and animated footage into trailers and promotional pieces, bringing pitch beats to life in Unreal before the edit.",
    tags: ["Unreal Engine", "Trailer Editing", "Storyboarding", "Previs"],
    visual: "dossier",
    link: null
  },
  {
    kind: "case",
    date: "2021",
    code: "GAME-DEV",
    org: "VANCOUVER FILM SCHOOL · FINAL PROJECT",
    title: "Tokyo Takeover — Stealth-Horror Game",
    desc: "Third-person stealth horror set in a shopping mall overrun by blind mutants. Sculpted five characters in ZBrush, modelled and textured ~90% of props (high/low poly), rigged the bat-mutant enemy and prepared humanoid rigs for mocap, then lit and set-dressed all three levels in Unity.",
    tags: ["Unity", "Maya", "ZBrush", "Substance Painter", "Rigging", "Lighting"],
    visual: "image",
    img: "assets/work/tokyotakeover_gameplay.jpg",
    alt: "Top-down gameplay view of Tokyo Takeover: a blind mutant hunting through a neon-lit shopping mall atrium in Unity",
    link: { label: "VIEW ON ARTSTATION", href: "https://www.artstation.com/artwork/WKNPAJ" }
  }
];

/* ---------- DEMO DOCS (opened by clicking nodemap nodes) ---------- */
const demoDocs = {
  clapper: {
    date: "2024 — DEMO",
    code: "DEMO-TOOL",
    org: "ORIGINAL · IN-ENGINE PYTHON",
    title: "Clapper — Asset & Shot Importer",
    desc: "An original demo of the work I do daily: a manifest-driven Unreal Python importer. One JSON builds the sequence/shot structure, creates a LevelSequence per shot, imports FBX/textures through the real AssetTools pipeline, auto-conforms names to prefix conventions, and tags metadata. Dry-run by default with a JSON report — and the validator runs in plain Python for CI pre-flight.",
    tags: ["Unreal Python API", "Asset & Shot Import", "Naming Conventions", "LevelSequence", "JSON Manifests", "Dry-run Safe"],
    link: { label: "VIEW SOURCE", href: "https://github.com/We1Z/We1Z.github.io/blob/main/demo/clapper/clapper_importer.py" },
    visual: () => {
      const rows = [
        { action: "MKDIR",    detail: "/Game/Cinematics/Sequences/SQ010/SH010", status: "planned" },
        { action: "SEQUENCE", detail: "LS_SQ010_SH010 · frames 1001–1085",      status: "planned" },
        { action: "SEQUENCE", detail: "LS_SQ010_SH020 · frames 1086–1210",      status: "planned" },
        { action: "CONFORM",  detail: "Prop_Chair_01 → SM_Prop_Chair_01",       status: "conform" },
        { action: "IMPORT",   detail: "chair_01.fbx → /Game/03_Assets/Props",   status: "skip", note: "source fictional" },
        { action: "IMPORT",   detail: "hero.fbx → /Game/03_Assets/Characters",  status: "skip", note: "source fictional" },
        { action: "TAG",      detail: "LS_SQ010_SH010: sequence · shot · frames", status: "planned" }
      ];
      const c = { planned: "var(--dim)", conform: "var(--blue-soft)", skip: "#fbbf24" };
      return `
      <div class="mock">
        <div class="mock__titlebar">
          <span class="mock__sym">▶</span>
          <span class="mock__title">CLAPPER</span>
          <span class="mock__sub">manifest: SQ010_ingest.json</span>
          <span class="mock__mode">DRY-RUN</span>
        </div>
        <div class="mock__body">
          <div class="mock__stats">
            <span class="mock__stat" style="color:var(--bone)">ASSETS <b>4</b></span>
            <span class="mock__stat" style="color:var(--bone)">SHOTS <b>3</b></span>
            <span class="mock__stat" style="color:var(--blue-soft)">CONFORM <b>1</b></span>
            <span class="mock__stat" style="color:#4ade80">ERRORS <b>0</b></span>
          </div>
          <div class="mock__table">
            <div class="mock__row mock__row--head"><span>ACTION</span><span>PLAN</span><span>STATUS</span></div>
            ${rows.map(r => `
              <div class="mock__row">
                <span class="mock__action">${r.action}</span>
                <span class="mock__detail">${r.detail}${r.note ? ` <em>${r.note}</em>` : ""}</span>
                <span class="mock__status" style="color:${c[r.status]}">${r.status.toUpperCase()}</span>
              </div>`).join("")}
          </div>
          <div class="mock__log">py clapper_importer.py --manifest SQ010_ingest.json — add <b>--commit</b> to apply</div>
        </div>
      </div>`;
    }
  },
  murmuration: {
    date: "2024 — DEMO",
    code: "DEMO-TOOL",
    org: "ORIGINAL · STANDALONE + IN-UE",
    title: "Murmuration — Crowd VAT Baker",
    desc: "GPU-crowd playback, from scratch: a self-contained boids flock is baked into 48-bit position + direction VAT textures, one quad-card mesh per agent, and a JSON header carrying fps, texel mapping and bounds. An in-Unreal script then imports the bake and constructs the material graph itself — World Position Offset decode driven by a Frame parameter — so an entire crowd animates through one material, no skeletal evaluation.",
    tags: ["Python · numpy", "VAT Bake / GPU Crowd", "48-bit Textures", "Unreal Material Graph", "WPO Playback"],
    link: { label: "VIEW SOURCE", href: "https://github.com/We1Z/We1Z.github.io/blob/main/demo/murmuration/README.md" },
    visual: () => `
      <img class="case__img" src="assets/work/murmuration_vat.jpg"
           alt="Murmuration demo: a 256x256 uint16 position VAT texture beside three frames of a 224-agent boids flock with motion trails" loading="lazy" />
      <span class="case__corner case__corner--tl"></span><span class="case__corner case__corner--br"></span>`
  },
  relay: {
    date: "2024 — DEMO",
    code: "DEMO-TOOL",
    org: "ORIGINAL · UNREAL ⇄ SHOTGRID API",
    title: "Relay — ShotGrid Sync",
    desc: "Bidirectional sync against a mocked ShotGrid site — a JSON-backed stand-in that implements find / find_one / create / update, entity links and EventLogEntry exactly like shotgun_api3. PULL turns SG shots into LevelSequences tagged with frames, status codes and assignees using updated_at conflict detection; PUSH scans the content browser and reports meshes, LOD counts and package paths back as SG assets. Idempotent, dry-run safe; point it at a real site by swapping one object.",
    tags: ["shotgun_api3 pattern", "find / create / update", "LevelSequence Metadata", "SG Status Codes", "EventLogEntry Audit"],
    link: { label: "VIEW SOURCE", href: "https://github.com/We1Z/We1Z.github.io/blob/main/demo/relay/README.md" },
    visual: () => {
      const rows = [
        { dir: "PULL", glyph: "⤓", entity: "shot",  key: "SQ010/SH020",     action: "update",   note: "shotgrid newer · sg_status_list=ip" },
        { dir: "PULL", glyph: "⤓", entity: "shot",  key: "SQ010/SH030",     action: "create",   note: "LevelSequence missing" },
        { dir: "PULL", glyph: "⤓", entity: "shot",  key: "SQ010/SH010",     action: "skip",     note: "in sync · apr" },
        { dir: "PUSH", glyph: "⤒", entity: "asset", key: "SM_Prop_Lamp_02", action: "create",   note: "sg.create Asset · Prop · LOD 2" },
        { dir: "PUSH", glyph: "⤒", entity: "asset", key: "SK_Char_Hero",    action: "skip",     note: "unchanged" },
        { dir: "BOTH", glyph: "⚑", entity: "shot",  key: "SQ020/SH040",     action: "conflict", note: "hld · stamp mismatch — SG wins" }
      ];
      const c = { create: "var(--blue)", update: "var(--blue-soft)", skip: "var(--dim)", conflict: "#fbbf24" };
      return `
      <div class="mock">
        <div class="mock__titlebar">
          <span class="mock__sym">⇄</span>
          <span class="mock__title">RELAY</span>
          <span class="mock__sub">unreal ⇄ shotgrid</span>
          <span class="mock__mode">DRY-RUN</span>
        </div>
        <div class="mock__body">
          <div class="mock__stats">
            <span class="mock__stat">PULL <b style="color:var(--blue)">3</b></span>
            <span class="mock__stat">PUSH <b style="color:var(--blue)">2</b></span>
            <span class="mock__stat">CONFLICTS <b style="color:#fbbf24">1</b></span>
            <span class="mock__stat">SG SITE <b style="color:var(--bone)">JSON</b></span>
          </div>
          <div class="mock__table">
            <div class="mock__row mock__row--head"><span>DIR</span><span>ENTITY</span><span>ACTION</span></div>
            ${rows.map(r => `
              <div class="mock__row">
                <span class="mock__dir${r.dir === "PUSH" ? " is-push" : ""}${r.dir === "BOTH" ? " is-both" : ""}">${r.glyph} ${r.dir}</span>
                <span class="mock__detail"><em>${r.entity}</em> ${r.key} <small>${r.note}</small></span>
                <span class="mock__status" style="color:${c[r.action]}">${r.action.toUpperCase()}</span>
              </div>`).join("")}
          </div>
          <div class="mock__log">py ue_relay.py --direction both <b>--commit</b> &nbsp;·&nbsp; same calls as <b>shotgun_api3</b> · swap one object for a live site</div>
        </div>
      </div>`;
    }
  }
};

/* ---------- 02 · ORIGINS (ArtStation) ---------- */
const origins = [
  { title: "PrimoGem — Genshin Impact", tools: "Maya · Substance · UE Material Graph", img: "assets/work/primogem.jpg", href: "https://www.artstation.com/artwork/1xLwvZ" },
  { title: "Widebody Cyber Jeep", tools: "Maya · Substance Painter", img: "assets/work/cyberjeep.jpg", href: "https://www.artstation.com/artwork/3q9EGD" },
  { title: "Moonshot — Destiny 2 Hand Cannon", tools: "Maya · Substance Painter", img: "assets/work/moonshot.jpg", href: "https://www.artstation.com/artwork/3dO3YB" },
  { title: "Desert Eagle — Clips & Bullets", tools: "Maya · Substance · Unreal", img: "assets/work/deagle.jpg", href: "https://www.artstation.com/artwork/Rn0JJX" },
  { title: "Bat Mutant — Creature Rig", tools: "Maya · ZBrush · Substance", img: "assets/work/batmutant.jpg", href: "https://www.artstation.com/artwork/oAgbxz" },
  { title: "Tokyo Takeover — Mall Environments", tools: "Unity · Maya · Substance", img: "assets/work/tokyotakeover.jpg", href: "https://www.artstation.com/artwork/WKNPAJ" },
  { title: "Lightsaber — Realtime Prop", tools: "Hard Surface · Realtime", img: "assets/work/lightsaber.jpg", href: "https://www.artstation.com/artwork/J9myqd" }
];

/* ---------- 03 · TIMELINE ---------- */
const timeline = [
  { date: "2023 — PRESENT", role: "Unreal Pipeline TD", org: "WildBrain Studios", desc: "Builds production tools on the studio Unreal pipeline framework — asset & shot importers, crowd VAT baking, light rigs, turntable actions, light mixer — and extends the framework in C++ (enum editing, blueprint components). Python 3.11, ShotGrid / Perforce / farm." },
  { date: "2023 — 2024", role: "Technical Artist Certificate", org: "British Columbia Institute of Technology", desc: "Part-time professional development alongside studio work." },
  { date: "2022 — 2023", role: "Technical Artist", org: "WildBrain Studios — Strawberry Shortcake 3D", desc: "Cross-department asset & workflow support, Unreal tools, materials, FX and render fixes." },
  { date: "2022", role: "Unreal Generalist", org: "BRON Studios", desc: "Virtual production scene setup, optimization, virtual-camera integration and render QC in UE4." },
  { date: "2021", role: "Cinematic Designer", org: "IGG Canada — Lords Mobile", desc: "Storyboards and trailer assembly across live-action, gameplay and animated footage." },
  { date: "2020 — 2021", role: "Game Design Diploma", org: "Vancouver Film School", desc: "Shipped Tokyo Takeover (3D stealth horror) and Ancient Abyss (2D pixel shooter) as artist/rigger/lighting." },
  { date: "2018 — 2020", role: "Lab Analyst → QA Officer", org: "ALS Environmental · Bio-Chem Consulting", desc: "HPLC / ICP-MS method development, instrument troubleshooting, SOPs and ISO 17025 audits." },
  { date: "2014 — 2018", role: "BSc Chemistry", org: "University of Calgary", desc: "Co-authored research on shape-controlled MnO nanoparticles as MRI contrast agents (J. Chem. Phys.)." }
];

/* ---------- 04 · STACK ---------- */
const stack = [
  { head: "Languages & Core", items: ["Python", "MEL", "Bash / shell", "JSON · YAML configs", "Git · GitLab CI"] },
  { head: "DCC & Realtime", items: ["Autodesk Maya", "Unreal Engine 5", "Houdini", "Blender", "Unity · ZBrush", "Substance Suite"] },
  { head: "Pipeline", items: ["ShotGrid / sgtk", "Perforce (P4)", "Environment & build systems"] },
  { head: "3D Craft", items: ["Hard-surface modeling", "Character rigging", "Texturing & surfacing", "Lighting & rendering", "Set dressing", "Realtime materials"] }
];

/* Marquee vocabulary — sanitized pipeline terms, no internal show codenames */
const flavours = ["ASSET IMPORT","SHOT IMPORT","CROWD VAT","LIGHT RIG","TURNTABLE","LIGHT MIXER","SHOTGRID","PERFORCE","PYTHON 3.11","C++ / BLUEPRINT LIBS","EDITOR UTILITY WIDGETS","DATA VALIDATION","FARM SUBMISSION","UE 5.8"];

/* ---------- NODE MAP (framework → my tools → Unreal) ---------- */
function nodemapSVG() {
  const tools = [
    { y: 22,  label: "ASSET IMPORT", demo: "clapper" },
    { y: 78,  label: "SHOT IMPORT",  demo: "clapper" },
    { y: 134, label: "CROWD VAT",    demo: "murmuration", hot: true },
    { y: 190, label: "LIGHT RIG" },
    { y: 246, label: "TURNTABLE" },
    { y: 302, label: "LIGHT MIXER" }
  ];
  const midY = 177;
  const inEdges = tools.map(r =>
    `<path class="nm-edge ${r.hot ? "nm-edge--hot" : ""}" d="M170 ${midY + 14} C 208 ${midY + 14}, 200 ${r.y + 15}, 238 ${r.y + 15}"/>`).join("");
  const outEdges = tools.map(r =>
    `<path class="nm-edge" d="M356 ${r.y + 15} C 392 ${r.y + 15}, 390 ${midY + 16}, 414 ${midY + 16}"/>`).join("");

  return `
  <svg class="nodemap" viewBox="0 0 580 380" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Six production tools I built on the studio Unreal framework — asset import, shot import, crowd VAT baking, light rig, turntable actions, light mixer — feeding Unreal Engine 5.8">
    <defs>
      <pattern id="nmgrid" width="28" height="28" patternUnits="userSpaceOnUse">
        <path d="M28 0H0V28" fill="none" stroke-width="1"/>
      </pattern>
    </defs>
    <rect width="580" height="380" fill="url(#nmgrid)"/>
    ${inEdges}${outEdges}
    <g>
      <rect class="nm-node nm-node--external" x="40" y="${midY - 18}" width="130" height="64" rx="2"/>
      <text x="105" y="${midY + 6}" text-anchor="middle" style="fill:var(--bone-dim)">pipeline</text>
      <text x="105" y="${midY + 26}" text-anchor="middle" style="fill:var(--bone-dim)">framework</text>
    </g>
    ${tools.map(r => `
      <g class="nm-tool${r.demo ? " nm-tool--hasdemo" : ""}"${r.demo ? ` data-demo="${r.demo}" tabindex="0" role="button" aria-label="View demo for ${r.label}"` : ""}>
        <rect class="nm-node ${r.hot ? "nm-node--dcc" : ""}" x="238" y="${r.y}" width="118" height="30" rx="2"/>
        <text x="297" y="${r.y + 19}" text-anchor="middle" style="font-size:9.5px">${r.label}</text>
        ${r.demo ? `<text class="nm-badge" x="352" y="${r.y + 4}" text-anchor="end">▸ DEMO</text>` : ""}
      </g>`).join("")}
    <g>
      <rect class="nm-node nm-node--dcc" x="414" y="${midY - 32}" width="138" height="96" rx="2"/>
      <text x="483" y="${midY + 6}" text-anchor="middle" style="letter-spacing:.1em">UNREAL</text>
      <text x="483" y="${midY + 28}" text-anchor="middle" style="fill:var(--blue);letter-spacing:.1em">5.8</text>
    </g>
    <g>
      <text x="105" y="246" text-anchor="middle" style="font-size:9px;letter-spacing:.18em;fill:var(--dim)">TEAM-OWNED</text>
      <text x="297" y="354" text-anchor="middle" style="font-size:9px;letter-spacing:.16em;fill:var(--dim)">CLICK A NODE TO OPEN ITS DEMO ▸</text>
      <g class="nm-tool nm-tool--hasdemo" data-demo="relay" tabindex="0" role="button" aria-label="View demo for ShotGrid sync">
        <text x="483" y="${midY + 86}" text-anchor="middle" style="font-size:9px;letter-spacing:.14em;fill:var(--dim)">SHOTGRID · PERFORCE · FARM</text>
        <text class="nm-badge" x="483" y="${midY + 100}" text-anchor="middle">▸ DEMO</text>
      </g>
    </g>
  </svg>`;
}

/* ---------- RENDER ---------- */
function visualHTML(item, i) {
  if (item.visual === "nodemap") return `<div class="case__visual" id="featuredVisual"><div class="stage-inner">${nodemapSVG()}</div></div>`;
  if (item.visual === "image") {
    return `<div class="case__visual">
      <img class="case__img" src="${item.img}" alt="${item.alt || item.title}" loading="lazy" />
      <span class="case__corner case__corner--tl"></span><span class="case__corner case__corner--br"></span>
    </div>`;
  }
  const words = item.title.split(" ");
  const word = words.length > 2 ? words.slice(0, 2).join(" ") : item.title;
  return `<div class="case__visual">
    <div class="dossier">
      <span class="dossier__index">0${i + 1}</span>
      <span class="dossier__word">${word}</span>
      <span class="dossier__sub">${item.code}</span>
      <span class="dossier__bars" aria-hidden="true">${"<i></i>".repeat(7)}</span>
    </div>
  </div>`;
}

document.getElementById("workGrid").innerHTML = work.map((item, i) => `
  <article class="case ${item.kind === "featured" ? "case--featured" : ""} reveal"${item.kind === "featured" ? ' id="featuredCard"' : ""} style="--d:${Math.min(i * .08, .32)}s">
    ${visualHTML(item, i)}
    <div class="case__body"${item.kind === "featured" ? ' id="featuredBody"' : ""}>
      <div class="case__meta mono">
        <span><b>${item.code}</b></span><span>${item.date}</span>
      </div>
      <p class="case__org">${item.org}</p>
      <h3 class="case__title">${item.title}</h3>
      <p class="case__desc">${item.desc}</p>
      ${item.writeup ? `<div class="case__writeup">${item.writeup.map(w => `
        <div class="writeup-row">
          <span class="writeup-label mono">${w.label}</span>
          <p class="writeup-text">${w.text}</p>
        </div>`).join("")}</div>` : ""}
      <div class="case__tags">${item.tags.map(t => `<span class="tag">${t}</span>`).join("")}</div>
      ${item.link ? `<a class="case__link" href="${item.link.href}" target="_blank" rel="noopener">${item.link.label} <span>↗</span></a>` : ""}
    </div>
  </article>`).join("");

/* ---------- FEATURED CASE: nodemap opens a full-card demo overlay ---------- */
(function () {
  const card = document.getElementById("featuredCard");
  if (!card) return;

  const overlay = document.createElement("div");
  overlay.className = "demo-overlay";
  overlay.innerHTML = `<div class="demo-overlay__visual"></div><div class="demo-overlay__body"></div>`;
  card.appendChild(overlay);
  const oVis = overlay.querySelector(".demo-overlay__visual");
  const oBody = overlay.querySelector(".demo-overlay__body");
  let activeDemo = null;

  function openDemo(key) {
    const d = demoDocs[key];
    if (!d) return;
    if (activeDemo === key) { closeDemo(); return; }
    activeDemo = key;
    oVis.innerHTML = `
      <div class="stage-inner stage-inner--demo">
        <button class="case__back case__back--visual mono" type="button" data-back><span class="case__back-arrow">←</span> BACK TO NODEMAP</button>
        <div class="mock-wrap">${d.visual()}</div>
      </div>`;
    oBody.innerHTML = `
      <button class="case__back mono" type="button" data-back>← PIPELINE OVERVIEW</button>
      <div class="case__meta mono"><span><b>${d.code}</b></span><span>${d.date}</span></div>
      <p class="case__org">${d.org}</p>
      <h3 class="case__title">${d.title}</h3>
      <p class="case__desc">${d.desc}</p>
      <div class="case__tags">${d.tags.map(t => `<span class="tag">${t}</span>`).join("")}</div>
      <a class="case__link" href="${d.link.href}" target="_blank" rel="noopener">${d.link.label} <span>↗</span></a>`;
    overlay.classList.add("is-open");
    overlay.setAttribute("aria-hidden", "false");
    markActive(key);
    overlay.querySelectorAll("[data-back]").forEach(b => b.addEventListener("click", closeDemo));
  }

  function closeDemo() {
    activeDemo = null;
    overlay.classList.remove("is-open");
    overlay.setAttribute("aria-hidden", "true");
    markActive(null);
  }

  function markActive(key) {
    document.querySelectorAll(".nm-tool--hasdemo").forEach(el =>
      el.classList.toggle("is-active", el.dataset.demo === key));
  }

  document.querySelectorAll(".nm-tool--hasdemo").forEach(el => {
    el.addEventListener("click", () => openDemo(el.dataset.demo));
    el.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openDemo(el.dataset.demo); }
    });
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeDemo(); });
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
