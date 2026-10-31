"""
Markdown report for a 4D explorer run.

    python explorer_report.py data/explorer/gemini_20261030_143255.jsonl
    python explorer_report.py --latest gemini          # newest gemini run in data/explorer
    python explorer_report.py RUN.jsonl --baseline data/explorer/tiler_20261030_142212.jsonl

Writes <run>_report.md next to the .jsonl and prints its path. run_explorer.py
calls this automatically after LLM runs.

The report has a summary table, per-object aggregates when there are several
seeds, a comparison with the newest baseline runs (prior, naive, tiler) on the
same objects, automatic flags, and per-trial detail: the agent's description,
the held-out slices, and every probe. Probes taken along a held-out normal are
marked with their offset distance, and *mirrored* when they sit at the negated
offset (a free answer on centrally symmetric objects; refused since the
mirrored-slice fix, so it should only appear in older runs).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

BASELINES = ("prior", "naive", "tiler")
NEAR_ANGLE_DEG = 10.0
NEAR_OFFSET = 0.15


def _upgrade(r: dict) -> dict:
    """Fill fields that logs written before the slab/chi scoring change do not have."""
    from nhcs.explorer.objects import make, orientability_decidable
    b, t = r.get("betti_answer") or [0, 0, 0], r["betti_true"]
    r.setdefault("euler_true", t[0] - t[1] + t[2])
    r.setdefault("euler_answer", b[0] - b[1] + b[2])
    if "dimension_true" not in r:
        obj = make(r["object"], r.get("seed", 0))
        r["dimension_true"] = obj.intrinsic_dim
        r.setdefault("orientability_decidable", orientability_decidable(obj))
    if "dimension_answer" not in r:  # older prompts did not ask for it: judge b0 and chi only
        r["dimension_answer"] = None
        r.setdefault("core_correct", b[0] == t[0] and r["euler_answer"] == r["euler_true"])
    return r


def load(path: Path) -> list[dict]:
    return [_upgrade(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _stamp(path: Path) -> str:
    m = re.search(r"(\d{8}_\d{6})", path.name)
    return m.group(1) if m else ""


def _held_slices(row: dict) -> list[dict]:
    """Held-out slices of a trial. Older logs did not store them, so rebuild the session."""
    if row.get("held_out_slices"):
        return row["held_out_slices"]
    from nhcs.explorer.objects import make
    from nhcs.explorer.probes import ProbeSession
    s = ProbeSession(make(row["object"], row["seed"]), budget=row.get("budget", 20),
                     n_held_out=len(row.get("held_out_truth", [])), seed=1000 + row["seed"])
    return [h.as_dict() for h in s.held_out]


def _held_tag(probe: dict, held: list[dict]) -> tuple[str, int | None, str | None]:
    """Label a probe that runs along a held-out normal: (text, index, kind)."""
    n = probe.get("normal")
    if n is None:
        return "", None, None
    n = np.asarray(n, float)
    if "offset" in probe:
        lo = hi = probe["offset"]
    else:
        lo, hi = probe["lo"], probe["hi"]
    best = ("", None, None, 9.0)
    for i, h in enumerate(held):
        hn = np.asarray(h["normal"], float)
        hn = hn / np.linalg.norm(hn)
        c = float(hn @ n)
        if np.degrees(np.arccos(min(1.0, abs(c)))) >= NEAR_ANGLE_DEG:
            continue
        o = h["offset"] if c > 0 else -h["offset"]  # held-out offset written in this probe's orientation

        def dist(t):
            return 0.0 if lo <= t <= hi else min(abs(t - lo), abs(t - hi))

        d, dm = dist(o), dist(-o)
        if abs(o) <= 0.08:  # the slice nearly is its own mirror image: just report the nearer distance
            d = dm = min(d, dm)
        if dm < d and dm < NEAR_OFFSET:
            if dm < best[3]:
                best = (f"**H{i + 1} mirrored** (Δ{dm:.2f})", i, "mirrored", dm)
        elif d < NEAR_OFFSET and d < best[3]:
            best = (f"H{i + 1} Δ{d:.2f}", i, "near", d)
        elif best[1] is None:
            best = (f"H{i + 1} normal", i, "normal", 9.0)
    return best[0], best[1], best[2]


def _params(p: dict) -> str:
    if p["probe"] == "project":
        return f"direction {p['direction']}"
    if p["probe"] == "slice":
        return f"normal {p['normal']}, offset {p['offset']}"
    return f"normal {p['normal']}, [{p['lo']}, {p['hi']}]"


def _flags(row: dict, held: list[dict]) -> list[str]:
    out = []
    slabs = sum(p["probe"] == "slab" for p in row["probes"])
    if slabs:
        out.append(f"used {slabs} slab probe(s)")
    if not row.get("core_correct"):
        out.append(f"core wrong: answered χ={row['euler_answer']}, b0={row['betti_answer'][0]}, "
                   f"dim={row.get('dimension_answer')}; truth χ={row['euler_true']}, "
                   f"b0={row['betti_true'][0]}, dim={row.get('dimension_true')}")
    if row.get("orientable_true") is not None and row.get("orientable_answer") is not None \
            and row["orientable_answer"] != row["orientable_true"]:
        dec = "decidable" if row.get("orientability_decidable") else "not decidable from these probes"
        out.append(f"orientability wrong ({dec})")
    ans = row.get("held_out_answer") or []
    for p in row["probes"]:
        tag, i, kind = _held_tag(p, held)
        if i is None or p["probe"] != "slice" or kind not in ("near", "mirrored"):
            continue
        seen = p["betti"][:2]
        a = ans[i] if i < len(ans) else None
        truth = row["held_out_truth"][i]
        if kind == "mirrored":
            out.append(f"probed H{i + 1}'s mirror image (saw {seen}; truth {truth})")
        if seen == truth and a is not None and list(a) != truth:
            out.append(f"H{i + 1}: its own probe ({tag.replace('**', '')}) returned the right answer {seen}, "
                       f"but it submitted {a}")
    if row.get("probes_used", 0) < row.get("budget", 0):
        out.append(f"left {row['budget'] - row['probes_used']} probe(s) unused")
    if row.get("description", "").startswith("(no answer"):
        out.append("never submitted")
    return out


def _table(header: list[str], rows: list[list]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + \
           ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]


def _agg(rows: list[dict]) -> list:
    n = len(rows)
    return [n, f"{sum(r['core_correct'] for r in rows)}/{n}", f"{sum(r['betti_exact'] for r in rows)}/{n}",
            f"{sum(r['held_out_accuracy'] for r in rows) / n:.2f}", f"{sum(r['score'] for r in rows) / n:.2f}"]


def newest_baselines(folder: Path, before: str | None = None) -> list[Path]:
    out = []
    for name in BASELINES:
        cands = sorted(p for p in folder.glob(f"{name}_*.jsonl") if not before or _stamp(p) <= before)
        if cands:
            out.append(cands[-1])
    return out


def build(path: Path, baselines: list[Path] | None = None) -> str:
    rows = load(path)
    if not rows:
        return f"# Explorer run\n\n`{path}` has no trials.\n"
    agent = rows[0]["agent"]
    objects = list(dict.fromkeys(r["object"] for r in rows))
    seeds = sorted({r["seed"] for r in rows})
    spend = sum(r.get("cost_usd") or 0 for r in rows)
    wall = sum(r.get("seconds") or 0 for r in rows)
    st = _stamp(path)
    when = f"{st[:4]}-{st[4:6]}-{st[6:8]} {st[9:11]}:{st[11:13]}" if st else ""
    model = rows[0].get("model")
    L = [f"# Explorer run: {agent}" + (f", {when}" if when else ""), "",
         f"Source: `{path.as_posix()}`  ",
         (f"Model `{model}`, thinking `{rows[0].get('thinking_level')}`, " if model else "")
         + f"probe budget {rows[0].get('budget')}, seed(s) {seeds}  ",
         (f"Total estimated spend: ${spend:.2f}, " if spend else "") + f"wall time {wall:.0f}s  ",
         "Score = 0.5 × core (b0, Euler characteristic and dimension all right) + 0.5 × held-out accuracy.",
         "", "## Summary", ""]

    def yn(x):
        return "yes" if x else "no"

    def orient(r):
        if r.get("orientable_true") is None:
            return "–"
        s = f"{r['orientable_true']} / {r.get('orientable_answer')}"
        return s if r.get("orientability_decidable") else s + " (not decidable)"

    L += _table(["object", "seed", "true Betti", "answer", "χ (true / answer)", "dim", "core",
                 "orientable (true / answer)", "held-out acc", "score", "cost"],
                [[r["object"], r["seed"], r["betti_true"], r["betti_answer"], f"{r['euler_true']} / {r['euler_answer']}",
                  f"{r.get('dimension_true')} / {r.get('dimension_answer')}", yn(r["core_correct"]), orient(r),
                  f"{r['held_out_accuracy']:.2f}", f"{r['score']:.2f}",
                  f"${r['cost_usd']:.3f}" if r.get("cost_usd") is not None else "–"] for r in rows])
    n = len(rows)
    L += ["", f"**Mean score {sum(r['score'] for r in rows) / n:.2f}**, core {sum(r['core_correct'] for r in rows)}/{n}, "
              f"Betti exact {sum(r['betti_exact'] for r in rows)}/{n}, "
              f"held-out accuracy {sum(r['held_out_accuracy'] for r in rows) / n:.2f}"]

    if len(seeds) > 1:
        L += ["", "## By object", ""]
        L += _table(["object", "trials", "core", "Betti exact", "held-out acc", "mean score"],
                    [[o] + _agg([r for r in rows if r["object"] == o]) for o in objects])

    if baselines is None:
        baselines = [p for p in newest_baselines(path.parent, st) if p != path]
    base = {p: [r for r in load(p) if r["object"] in objects] for p in baselines}
    base = {p: b for p, b in base.items() if b}
    if base:
        L += ["", "## Comparison with baselines (same objects)", "",
              "Baseline runs: " + ", ".join(f"`{p.name}`" for p in base), ""]
        trs = []
        for o in objects:
            for p, b in base.items():
                rb = [r for r in b if r["object"] == o]
                if rb:
                    trs.append([rb[0]["agent"], o] + _agg(rb))
            trs.append([f"**{agent}**", o] + _agg([r for r in rows if r["object"] == o]))
        L += _table(["agent", "object", "trials", "core", "Betti exact", "held-out acc", "mean score"], trs)
        if len(seeds) == 1:
            L += ["", f"{agent} ran 1 trial per object; treat differences from the baselines as indicative only."]

    L += ["", "## Flags", ""]
    held_by_row = [_held_slices(r) for r in rows]
    for r, held in zip(rows, held_by_row):
        f = _flags(r, held)
        L.append(f"- **{r['object']}** (seed {r['seed']}): " + ("; ".join(f) if f else "nothing unusual"))

    for r, held in zip(rows, held_by_row):
        u = r.get("usage") or {}
        L += ["", f"## {r['object']} (seed {r['seed']})", "",
              f"{r['probes_used']}/{r['budget']} probes"
              + (f", {u.get('turns')} turns, {u.get('input')} in / {u.get('output')} out / {u.get('thought')} thinking tokens"
                 if u else "") + f", {r.get('seconds')}s", "",
              "**Agent's description:**", "", "> " + (r.get("description") or "(none)").replace("\n", "\n> "), ""]
        if r.get("notes"):
            L += ["**Agent's notes along the way:**", ""] + [f"> {t.strip()}" for t in r["notes"] if t.strip()] + [""]
        ans = r.get("held_out_answer") or []
        L += ["**Held-out slices:**", ""]
        L += _table(["#", "normal", "offset", "truth", "answer", ""],
                    [[f"H{i + 1}", h["normal"], f"{h['offset']:.4f}", t, ans[i] if i < len(ans) else "–",
                      "✓" if i < len(ans) and list(ans[i]) == t else "✗"]
                     for i, (h, t) in enumerate(zip(held, r["held_out_truth"]))])
        L += ["", "**Probes** (last column: probe runs along held-out slice Hn's normal; Δ = offset distance; "
                  "*mirrored* = at the negated offset):", ""]
        L += _table(["#", "probe", "parameters", "Betti", "χ", "points", "components", "held-out"],
                    [[i + 1, p["probe"], _params(p), p["betti"],
                      p.get("euler", p["betti"][0] - p["betti"][1] + p["betti"][2]),
                      p.get("n_points"), len(p.get("components", [])), _held_tag(p, held)[0]]
                     for i, p in enumerate(r["probes"])])
    return "\n".join(L) + "\n"


def write(path: Path, baselines: list[Path] | None = None) -> Path:
    out = path.with_name(path.stem + "_report.md")
    out.write_text(build(path, baselines), encoding="utf-8")
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?", help="a data/explorer/<agent>_<stamp>.jsonl file")
    ap.add_argument("--latest", metavar="AGENT", help="use the newest run of this agent in data/explorer")
    ap.add_argument("--baseline", action="append", help="baseline .jsonl to compare against (default: newest prior/naive/tiler)")
    args = ap.parse_args()
    if args.latest:
        cands = sorted(Path("data/explorer").glob(f"{args.latest}_*.jsonl"), key=_stamp)
        if not cands:
            ap.error(f"no {args.latest} runs in data/explorer")
        path = cands[-1]
    elif args.run:
        path = Path(args.run)
    else:
        ap.error("give a run file or --latest AGENT")
    print(write(path, [Path(b) for b in args.baseline] if args.baseline else None))


if __name__ == "__main__":
    main()
