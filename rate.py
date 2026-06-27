"""
NHCS Phenomenological Rating Tool
==================================
Local Flask app for collecting prime activation ratings from renders.
Saves to data/prime_ratings.csv — these become training data for W.

Run:  .venv\Scripts\python.exe rate.py
Open: http://localhost:8765
"""

from __future__ import annotations
import csv, glob, json, os, sys
from pathlib import Path
from flask import Flask, jsonify, request, send_file, render_template_string

# ── Paths ────────────────────────────────────────────────────────────────────
BASE        = Path(__file__).parent
RENDERS_DIR = BASE / "renders"
DATA_DIR    = BASE / "data"
RATINGS_CSV = DATA_DIR / "prime_ratings.csv"

# ── Load concept metadata from all CSVs ──────────────────────────────────────
def load_concepts() -> dict[str, dict]:
    concepts: dict[str, dict] = {}
    for csv_path in sorted(DATA_DIR.glob("nhcs_run_*.csv")):
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row.get("concept_id", "").strip()
                if cid:
                    row["_run"] = csv_path.stem
                    concepts[cid] = row
    return concepts

def load_ratings() -> dict[str, dict]:
    ratings: dict[str, dict] = {}
    if RATINGS_CSV.exists():
        with open(RATINGS_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                cid = row.get("concept_id", "").strip()
                if cid:
                    ratings[cid] = row
    return ratings

# ── NSM Primes grouped by category ───────────────────────────────────────────
PRIME_GROUPS = {
    "SUBSTANTIVES": ["I","YOU","SOMEONE","SOMETHING/THING","PEOPLE","BODY"],
    "DETERMINERS":  ["THIS","THE SAME","OTHER/ELSE"],
    "QUANTIFIERS":  ["ONE","TWO","SOME","ALL","MUCH/MANY","LITTLE/FEW"],
    "EVALUATORS":   ["GOOD","BAD"],
    "DESCRIPTORS":  ["BIG","SMALL"],
    "MENTAL":       ["THINK","KNOW","WANT","FEEL","SEE","HEAR"],
    "SPEECH":       ["SAY","WORDS","TRUE"],
    "ACTIONS":      ["DO","HAPPEN","MOVE","TOUCH"],
    "EXISTENCE":    ["THERE IS","HAVE"],
    "LIFE":         ["LIVE","DIE"],
    "TIME":         ["WHEN/TIME","NOW","BEFORE","AFTER","A LONG TIME","A SHORT TIME","FOR SOME TIME","MOMENT"],
    "SPACE":        ["WHERE/PLACE","HERE","ABOVE","BELOW","FAR","NEAR","SIDE","INSIDE"],
    "LOGICAL":      ["NOT","MAYBE","CAN","BECAUSE","IF"],
    "INTENSIFIER":  ["VERY","MORE"],
    "SIMILARITY":   ["LIKE/AS/WAY"],
}
ALL_PRIMES = [p for group in PRIME_GROUPS.values() for p in group]

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NHCS — Phenomenological Rating Interface</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
  --bg:       #070b0d;
  --panel:    #0c1218;
  --panel2:   #101820;
  --border:   #1c2d3a;
  --amber:    #e8a33c;
  --amber-dim:#7a4e10;
  --blue:     #5ab4d4;
  --blue-dim: #1a3d52;
  --text:     #c4d4de;
  --muted:    #4a6070;
  --green:    #4ecb8f;
  --red:      #e05a5a;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; background: var(--bg); color: var(--text); font-family: 'DM Mono', monospace; font-size: 13px; overflow: hidden; }

/* ── Header ── */
#header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 20px; border-bottom: 1px solid var(--border);
  background: var(--panel);
}
#header .title { font-family: 'Syne', sans-serif; font-weight: 800; font-size: 15px; letter-spacing: 0.12em; color: var(--amber); text-transform: uppercase; }
#header .subtitle { font-size: 10px; color: var(--muted); letter-spacing: 0.08em; margin-top: 2px; }
#progress-bar-wrap { flex: 1; margin: 0 30px; height: 3px; background: var(--border); border-radius: 2px; }
#progress-bar { height: 100%; background: var(--amber); border-radius: 2px; transition: width 0.4s ease; }
#progress-label { font-size: 11px; color: var(--muted); white-space: nowrap; }
#skip-rated { background: none; border: 1px solid var(--border); color: var(--muted); padding: 4px 10px; border-radius: 3px; cursor: pointer; font-family: 'DM Mono', monospace; font-size: 11px; transition: all 0.2s; }
#skip-rated:hover { border-color: var(--amber); color: var(--amber); }

/* ── Main layout ── */
#main { display: flex; height: calc(100vh - 45px); }

/* ── Left: image panel ── */
#left {
  width: 380px; min-width: 280px; flex-shrink: 0;
  display: flex; flex-direction: column;
  border-right: 1px solid var(--border); background: var(--panel);
}
#render-wrap {
  flex: 1; display: flex; align-items: center; justify-content: center;
  padding: 20px; position: relative; overflow: hidden;
}
#render-wrap::before {
  content: ''; position: absolute; inset: 0;
  background: radial-gradient(circle at center, transparent 40%, #050709 100%);
  pointer-events: none; z-index: 1;
}
#render-img { max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 4px; position: relative; z-index: 0; }
#render-placeholder { color: var(--muted); font-size: 12px; text-align: center; }

#concept-meta {
  padding: 14px 18px; border-top: 1px solid var(--border);
  display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px;
}
.meta-item { display: flex; flex-direction: column; }
.meta-label { font-size: 9px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2px; }
.meta-value { font-size: 13px; color: var(--blue); font-weight: 500; }
.meta-betti { color: var(--amber); }

#nav { display: flex; padding: 12px 18px; gap: 10px; border-top: 1px solid var(--border); }
#nav button {
  flex: 1; padding: 8px; background: var(--panel2); border: 1px solid var(--border);
  color: var(--text); font-family: 'DM Mono', monospace; font-size: 12px;
  cursor: pointer; border-radius: 3px; transition: all 0.2s; letter-spacing: 0.05em;
}
#nav button:hover { border-color: var(--blue); color: var(--blue); }
#nav #btn-save { background: var(--amber); color: #000; border-color: var(--amber); font-weight: 500; }
#nav #btn-save:hover { background: #f0b84a; }
#nav #btn-save.saved { background: var(--green); border-color: var(--green); }

/* ── Right: rating panel ── */
#right { flex: 1; overflow-y: auto; padding: 16px 20px; display: flex; flex-direction: column; gap: 14px; }
#right::-webkit-scrollbar { width: 4px; }
#right::-webkit-scrollbar-track { background: var(--bg); }
#right::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

.prime-section {}
.section-label {
  font-size: 9px; color: var(--muted); text-transform: uppercase;
  letter-spacing: 0.12em; margin-bottom: 8px; padding-bottom: 4px;
  border-bottom: 1px solid var(--border);
}
.prime-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 6px; }

.prime-card {
  background: var(--panel); border: 1px solid var(--border); border-radius: 4px;
  padding: 7px 10px; cursor: pointer; transition: all 0.15s; user-select: none;
  position: relative; overflow: hidden;
}
.prime-card:hover { border-color: var(--blue-dim); }
.prime-card.active { border-color: var(--amber); background: #12180d; }
.prime-card.pipeline { border-color: var(--amber-dim); }
.prime-card.pipeline .prime-name::after {
  content: '●'; font-size: 7px; color: var(--amber-dim);
  margin-left: 6px; vertical-align: middle;
}

.prime-fill { position: absolute; bottom: 0; left: 0; height: 3px; background: var(--amber); transition: width 0.1s; border-radius: 0 0 4px 4px; }
.prime-card.active .prime-fill { background: var(--amber); }

.prime-name { font-size: 11px; color: var(--text); letter-spacing: 0.04em; margin-bottom: 4px; display: block; }
.prime-card.active .prime-name { color: var(--amber); }
.prime-val { font-size: 10px; color: var(--muted); }
.prime-card.active .prime-val { color: var(--amber); }

/* click-hold drag to set value */

/* ── Pipeline activations ── */
#pipeline-box {
  background: var(--panel2); border: 1px solid var(--border); border-radius: 4px;
  padding: 10px 14px; margin-bottom: 4px;
}
#pipeline-box .pb-label { font-size: 9px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 6px; }
#pipeline-activations { display: flex; flex-wrap: wrap; gap: 6px; }
.pa-chip {
  padding: 3px 8px; background: var(--amber-dim); border: 1px solid var(--amber-dim);
  border-radius: 2px; font-size: 10px; color: var(--amber); letter-spacing: 0.05em;
}

/* ── Instructions ── */
#instructions {
  font-size: 10px; color: var(--muted); line-height: 1.7;
  padding: 8px 12px; background: var(--panel2); border-radius: 4px;
  border-left: 2px solid var(--border);
}

/* ── Toast ── */
#toast {
  position: fixed; bottom: 20px; right: 20px; padding: 10px 16px;
  background: var(--green); color: #000; font-family: 'DM Mono', monospace;
  font-size: 12px; border-radius: 3px; opacity: 0; transition: opacity 0.3s;
  pointer-events: none; z-index: 100;
}
#toast.show { opacity: 1; }

/* ── Rating mode selector ── */
.mode-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.mode-bar label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; }
.mode-btn { padding: 3px 10px; background: none; border: 1px solid var(--border); color: var(--muted); font-family: 'DM Mono', monospace; font-size: 10px; border-radius: 2px; cursor: pointer; }
.mode-btn.active { border-color: var(--amber); color: var(--amber); }

/* ── Concept list sidebar ── */
#concept-list-toggle { position: absolute; top: 55px; left: 0; z-index: 10; }
</style>
</head>
<body>

<div id="header">
  <div>
    <div class="title">NHCS — Phenomenological Rating Interface</div>
    <div class="subtitle">NSM Prime Activation Collection &nbsp;·&nbsp; Training data for projection matrix W</div>
  </div>
  <div style="display:flex;align-items:center;gap:16px;">
    <div id="progress-bar-wrap"><div id="progress-bar" style="width:0%"></div></div>
    <span id="progress-label">— / —</span>
    <button id="skip-rated" onclick="skipToUnrated()">UNRATED</button>
  </div>
</div>

<div id="main">
  <!-- Left: render + metadata -->
  <div id="left">
    <div id="render-wrap">
      <div id="render-placeholder">Loading...</div>
      <img id="render-img" style="display:none" alt="Hopf field render" />
    </div>

    <div id="concept-meta">
      <div class="meta-item"><span class="meta-label">Concept</span><span class="meta-value" id="m-id">—</span></div>
      <div class="meta-item"><span class="meta-label">Run</span><span class="meta-value" id="m-run">—</span></div>
      <div class="meta-item"><span class="meta-label">Betti</span><span class="meta-value meta-betti" id="m-betti">—</span></div>
      <div class="meta-item"><span class="meta-label">I_f</span><span class="meta-value meta-betti" id="m-if">—</span></div>
      <div class="meta-item"><span class="meta-label">Freq (Hz)</span><span class="meta-value" id="m-freq">—</span></div>
      <div class="meta-item"><span class="meta-label">Wavelength (nm)</span><span class="meta-value" id="m-wl">—</span></div>
      <div class="meta-item"><span class="meta-label">B Mean (mT)</span><span class="meta-value" id="m-b">—</span></div>
      <div class="meta-item"><span class="meta-label">Novelty</span><span class="meta-value" id="m-nov">—</span></div>
      <div class="meta-item"><span class="meta-label">SDR</span><span class="meta-value" id="m-sdr">—</span></div>
      <div class="meta-item"><span class="meta-label">BHI</span><span class="meta-value" id="m-bhi">—</span></div>
    </div>

    <div id="nav">
      <button onclick="navigate(-1)">◀ PREV</button>
      <button onclick="navigate(1)">NEXT ▶</button>
      <button id="btn-save" onclick="saveRating()">SAVE</button>
    </div>
  </div>

  <!-- Right: prime ratings -->
  <div id="right">
    <div id="instructions">
      Look at the render. For each word below, rate how strongly it resonates with what you perceive (0 = not at all, 1 = strongly activates).
      <br>Click a card to toggle it on/off. Drag horizontally to set intensity. <span style="color:var(--amber)">●</span> = pipeline prediction.
    </div>

    <div id="pipeline-box">
      <div class="pb-label">Pipeline Predictions</div>
      <div id="pipeline-activations">—</div>
    </div>

    <div class="mode-bar">
      <label>Intensity mode:</label>
      <button class="mode-btn active" id="mode-binary" onclick="setMode('binary')">BINARY</button>
      <button class="mode-btn" id="mode-slider" onclick="setMode('slider')">CONTINUOUS</button>
    </div>

    <div id="prime-groups"></div>
  </div>
</div>

<div id="toast">Rating saved</div>

<script>
const PRIME_GROUPS = {{ prime_groups_json | safe }};
const ALL_PRIMES   = {{ all_primes_json | safe }};

let concepts    = [];
let ratings     = {};
let currentIdx  = 0;
let ratingMode  = 'binary';  // 'binary' | 'slider'
let currentRating = {};
let pipelinePrimes = [];

// ── Init ──────────────────────────────────────────────────────────────────
async function init() {
  const [cRes, rRes] = await Promise.all([
    fetch('/api/concepts'),
    fetch('/api/ratings')
  ]);
  const data  = await cRes.json();
  concepts    = data.concepts;
  ratings     = await rRes.json();
  buildPrimeGroups();
  loadConcept(currentIdx);
  updateProgress();
}

// ── Build prime UI ────────────────────────────────────────────────────────
function buildPrimeGroups() {
  const container = document.getElementById('prime-groups');
  container.innerHTML = '';
  for (const [group, primes] of Object.entries(PRIME_GROUPS)) {
    const section = document.createElement('div');
    section.className = 'prime-section';
    section.innerHTML = `<div class="section-label">${group}</div><div class="prime-grid" id="grp-${group}"></div>`;
    container.appendChild(section);
    const grid = section.querySelector(`#grp-${group}`);
    for (const prime of primes) {
      const card = document.createElement('div');
      card.className = 'prime-card';
      card.id = `prime-${prime.replace(/[^a-zA-Z0-9]/g, '_')}`;
      card.innerHTML = `
        <span class="prime-name">${prime}</span>
        <span class="prime-val" id="val-${prime.replace(/[^a-zA-Z0-9]/g, '_')}">0.00</span>
        <div class="prime-fill" id="fill-${prime.replace(/[^a-zA-Z0-9]/g, '_')}" style="width:0%"></div>`;
      card.addEventListener('click', () => togglePrime(prime, card));
      addDragRating(card, prime);
      grid.appendChild(card);
    }
  }
}

function safeId(prime) { return prime.replace(/[^a-zA-Z0-9]/g, '_'); }

function togglePrime(prime, card) {
  const current = currentRating[prime] || 0;
  if (ratingMode === 'binary') {
    currentRating[prime] = current > 0 ? 0 : 1.0;
  } else {
    currentRating[prime] = current > 0 ? 0 : 0.7;
  }
  updatePrimeCard(prime);
}

function updatePrimeCard(prime) {
  const val  = currentRating[prime] || 0;
  const sid  = safeId(prime);
  const card = document.getElementById(`prime-${sid}`);
  const valEl = document.getElementById(`val-${sid}`);
  const fill  = document.getElementById(`fill-${sid}`);
  if (!card) return;
  const isPipeline = pipelinePrimes.includes(prime);
  card.className = 'prime-card' + (val > 0 ? ' active' : '') + (isPipeline ? ' pipeline' : '');
  valEl.textContent = val.toFixed(2);
  fill.style.width = (val * 100) + '%';
}

function addDragRating(card, prime) {
  let dragging = false, startX = 0, startVal = 0;
  card.addEventListener('mousedown', e => {
    dragging = true; startX = e.clientX; startVal = currentRating[prime] || 0;
    e.preventDefault();
  });
  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    const dx = (e.clientX - startX) / 120;
    currentRating[prime] = Math.max(0, Math.min(1, startVal + dx));
    updatePrimeCard(prime);
  });
  document.addEventListener('mouseup', () => { dragging = false; });
}

// ── Load concept ──────────────────────────────────────────────────────────
function loadConcept(idx) {
  if (!concepts.length) return;
  currentIdx = ((idx % concepts.length) + concepts.length) % concepts.length;
  const c = concepts[currentIdx];

  document.getElementById('m-id').textContent   = c.concept_id || '—';
  document.getElementById('m-run').textContent  = (c._run || '—').replace('nhcs_', '');
  const b = [c.beta0||0, c.beta1||0, c.beta2||0];
  document.getElementById('m-betti').textContent= `[${b.join(',')}]`;
  const If = parseInt(c.beta1||0) + 2*parseInt(c.beta2||0);
  document.getElementById('m-if').textContent   = If;
  document.getElementById('m-freq').textContent = parseFloat(c.target_freq_hz||0).toFixed(2);
  document.getElementById('m-wl').textContent   = parseFloat(c.target_wl_nm||0).toFixed(1);
  document.getElementById('m-b').textContent    = parseFloat(c.mean_b_mt||0).toFixed(4);
  document.getElementById('m-nov').textContent  = parseFloat(c.novelty_aggregate||0).toFixed(3);
  document.getElementById('m-sdr').textContent  = parseFloat(c.sdr||0).toFixed(4);
  document.getElementById('m-bhi').textContent  = parseFloat(c.bhi||0).toFixed(4);

  // Pipeline primes
  pipelinePrimes = [];
  const paDiv = document.getElementById('pipeline-activations');
  paDiv.innerHTML = '';
  for (let k = 1; k <= 5; k++) {
    const p = c[`prime${k}`], w = parseFloat(c[`w${k}`]||0);
    if (p && p.trim()) {
      pipelinePrimes.push(p.trim());
      const chip = document.createElement('span');
      chip.className = 'pa-chip';
      chip.textContent = `${p} ${w.toFixed(2)}`;
      paDiv.appendChild(chip);
    }
  }

  // Load image
  const img = document.getElementById('render-img');
  const placeholder = document.getElementById('render-placeholder');
  img.style.display = 'none';
  placeholder.style.display = 'block';
  placeholder.textContent = 'Loading...';
  img.onload = () => { img.style.display = 'block'; placeholder.style.display = 'none'; };
  img.onerror = () => { placeholder.textContent = 'No render found'; };
  img.src = `/render/${c.concept_id}`;

  // Load existing rating or reset
  const existing = ratings[c.concept_id];
  currentRating = {};
  if (existing) {
    for (const prime of ALL_PRIMES) {
      const key = `r_${safeId(prime)}`;
      const val = parseFloat(existing[key] || 0);
      if (val > 0) currentRating[prime] = val;
    }
  }
  ALL_PRIMES.forEach(p => updatePrimeCard(p));

  // Save button state
  const saveBtn = document.getElementById('btn-save');
  saveBtn.classList.toggle('saved', !!existing);
  saveBtn.textContent = existing ? 'SAVED ✓' : 'SAVE';
  updateProgress();
}

// ── Navigation ─────────────────────────────────────────────────────────────
function navigate(dir) { loadConcept(currentIdx + dir); }

function skipToUnrated() {
  for (let i = 0; i < concepts.length; i++) {
    const idx = (currentIdx + 1 + i) % concepts.length;
    if (!ratings[concepts[idx].concept_id]) {
      loadConcept(idx);
      return;
    }
  }
  showToast('All concepts rated!');
}

function updateProgress() {
  const rated = concepts.filter(c => ratings[c.concept_id]).length;
  const total = concepts.length;
  document.getElementById('progress-label').textContent = `${rated} / ${total}`;
  const pct = total > 0 ? (rated / total * 100) : 0;
  document.getElementById('progress-bar').style.width = pct + '%';
}

// ── Save rating ────────────────────────────────────────────────────────────
async function saveRating() {
  const c = concepts[currentIdx];
  const payload = { concept_id: c.concept_id, ratings: currentRating };
  const res = await fetch('/api/rate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (res.ok) {
    ratings[c.concept_id] = await res.json();
    showToast('Rating saved');
    const saveBtn = document.getElementById('btn-save');
    saveBtn.classList.add('saved');
    saveBtn.textContent = 'SAVED ✓';
    updateProgress();
  }
}

// ── Mode ──────────────────────────────────────────────────────────────────
function setMode(mode) {
  ratingMode = mode;
  document.getElementById('mode-binary').classList.toggle('active', mode === 'binary');
  document.getElementById('mode-slider').classList.toggle('active', mode === 'slider');
}

// ── Toast ──────────────────────────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === 'd') navigate(1);
  if (e.key === 'ArrowLeft'  || e.key === 'a') navigate(-1);
  if (e.key === 'Enter' || e.key === 's') saveRating();
  if (e.key === 'n') skipToUnrated();
});

init();
</script>
</body>
</html>
"""

# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(
        HTML,
        prime_groups_json=json.dumps(PRIME_GROUPS),
        all_primes_json=json.dumps(ALL_PRIMES),
    )

@app.route("/render/<concept_id>")
def serve_render(concept_id):
    """Serve a render PNG by concept_id prefix."""
    pattern = str(RENDERS_DIR / f"{concept_id}*_hopf.png")
    matches = glob.glob(pattern)
    if not matches:
        # Try exact match
        exact = RENDERS_DIR / f"{concept_id}_hopf.png"
        if exact.exists():
            return send_file(exact, mimetype="image/png")
        return "Not found", 404
    return send_file(matches[0], mimetype="image/png")


@app.route("/api/primes")
def api_primes():
    return jsonify({"groups": PRIME_GROUPS, "all": ALL_PRIMES})

@app.route("/api/concepts")
def api_concepts():
    concepts = load_concepts()
    # Only include concepts that have a render
    result = []
    for cid, meta in concepts.items():
        render = RENDERS_DIR / f"{cid}_hopf.png"
        if render.exists():
            result.append(meta)
    # Sort by run then by idx
    result.sort(key=lambda r: (r.get("_run", ""), int(r.get("run_idx", 0))))
    return jsonify({"concepts": result, "total": len(result)})

@app.route("/api/ratings")
def api_ratings():
    return jsonify(load_ratings())

@app.route("/api/rate", methods=["POST"])
def api_rate():
    data       = request.json
    concept_id = data["concept_id"]
    user_ratings = data["ratings"]   # {prime: float}

    # Build CSV row
    row = {"concept_id": concept_id, "timestamp": __import__("datetime").datetime.now().isoformat()}
    for prime in ALL_PRIMES:
        safe = prime.replace("/", "_").replace(" ", "_").replace(".", "_")
        row[f"r_{safe}"] = round(float(user_ratings.get(prime, 0.0)), 4)

    # Write / update
    existing_ratings = load_ratings()
    existing_ratings[concept_id] = row

    fieldnames = ["concept_id", "timestamp"] + [
        f"r_{p.replace('/', '_').replace(' ', '_').replace('.', '_')}"
        for p in ALL_PRIMES
    ]
    with open(RATINGS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_ratings.values())

    return jsonify(row)


if __name__ == "__main__":
    port = 8765
    print(f"\n  NHCS Rating Tool")
    print(f"  ─────────────────────────────────────")
    print(f"  Renders:  {RENDERS_DIR}")
    print(f"  Ratings:  {RATINGS_CSV}")
    print(f"  Concepts: loading...")
    print(f"\n  Open → http://localhost:{port}")
    print(f"  Keys: ←/→ navigate  |  Enter = save  |  n = next unrated\n")
    app.run(host="127.0.0.1", port=port, debug=False)
