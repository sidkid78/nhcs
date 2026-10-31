"""
Markdown report for a knotted-sphere run (run_knots.py).

    python knot_report.py data/explorer/knots_gemini_20261031_070454.jsonl
    python knot_report.py --latest gemini

Writes <run>_report.md next to the .jsonl. run_knots.py calls this after
Claude or Gemini runs. Rows are re-scored with the current rule (older logs
counted "unknotted" as a wrong construction for the 1-twist-spun spheres,
which are unknotted).

Flags look for what this benchmark is about:
  - the 1-twist trap: knotted slices, unknotted sphere;
  - whether the explorer ever found the spin axis (a slice whose circles
    link: the linking number there is the twist), and whether its answer
    agrees with the largest linking number it saw;
  - probes along a held-out slice's normal near its offset or mirror image.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from explorer_report import _held_tag, _stamp, _table

BASELINES = ("prior", "naive", "linker")
TWIST = {"twist1_trefoil": 1, "twist1_figure_eight": 1, "twist2_trefoil": 2, "twist3_trefoil": 3}


def rescore(r: dict) -> dict:
    ans = (r.get("construction_answer") or "").strip().lower()
    if r["object"].startswith("twist1_") and ans.startswith("unknotted"):
        r["construction_correct"] = True
    r["score"] = 0.5 * r["knotted_correct"] + 0.25 * r["construction_correct"] + 0.25 * r["held_out_accuracy"]
    return r


def load(path: Path) -> list[dict]:
    return [rescore(json.loads(x)) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _labels(p: dict) -> str:
    if p.get("empty"):
        return "empty"
    ks = [k["name"] or f"knot(alex={k['alexander']}, g={k['genus']})" for k in p["knots"]]
    out = {}
    for k in ks:
        out[k] = out.get(k, 0) + 1
    return ", ".join(f"{n}×{k}" if n > 1 else k for k, n in out.items())


def _max_lk(r: dict) -> int:
    return max([x["lk"] for p in r["probes"] for x in p.get("linking", [])] or [0])


def _answer_twist(r: dict) -> int:
    m = re.search(r"twist (\d+)", r.get("construction_answer") or "")
    return int(m.group(1)) if m else 0


def _flags(r: dict) -> list[str]:
    f = []
    lk = _max_lk(r)
    o = r["object"]
    if o.startswith("twist1_") and r.get("knotted_answer") is True:
        f.append("fell for the 1-twist trap: called a knotted-looking but unknotted sphere knotted")
    if o in TWIST:
        if lk == 0:
            f.append(f"never found the spin axis: no slice with linked circles (truth: twist {TWIST[o]})")
        elif lk == TWIST[o]:
            f.append(f"found the spin axis: circles linking {lk} times")
    if lk and _answer_twist(r) != lk and not (lk == 1 and not r.get("knotted_answer")):
        f.append(f"saw circles linking {lk} times but answered {r.get('construction_answer')!r}")
    held = r.get("held_out_slices") or []
    for i, p in enumerate(r["probes"]):
        tag, k, kind = _held_tag(p, held)
        if kind in ("near", "mirrored"):
            f.append(f"probe {i + 1} sat near held-out H{k + 1} ({tag})")
    return f


def newest_baselines(folder: Path, before: str | None = None) -> list[Path]:
    out = []
    for name in BASELINES:
        c = sorted(p for p in folder.glob(f"knots_{name}_*.jsonl") if p.stat().st_size and (not before or _stamp(p) <= before))
        if c:
            out.append(c[-1])
    return out


def build(path: Path, baselines: list[Path] | None = None) -> str:
    rows = load(path)
    if not rows:
        return f"# Knotted-sphere run\n\n`{path}` has no trials.\n"
    agent, st = rows[0]["agent"], _stamp(path)
    when = f"{st[:4]}-{st[4:6]}-{st[6:8]} {st[9:11]}:{st[11:13]}" if st else ""
    spend = sum(r.get("cost_usd") or 0 for r in rows)
    n = len(rows)
    yn = lambda x: "yes" if x else "no"  # noqa: E731
    L = [f"# Knotted-sphere run: {agent}" + (f", {when}" if when else ""), "",
         f"Source: `{path.as_posix()}`  ",
         (f"Model `{rows[0].get('model')}`, thinking `{rows[0].get('thinking_level')}`, " if rows[0].get("model") else "")
         + f"probe budget {rows[0].get('budget')}, seed(s) {sorted({r['seed'] for r in rows})}  ",
         (f"Estimated spend ${spend:.2f}, " if spend else "") + f"wall time {sum(r.get('seconds') or 0 for r in rows):.0f}s  ",
         "Score = 0.5 × knotted right + 0.25 × construction right + 0.25 × held-out accuracy.", "", "## Summary", ""]
    L += _table(["object", "seed", "knotted (true / answer)", "built (true / answer)", "built right", "max linking seen", "held-out", "score", "cost"],
                [[r["object"], r["seed"], f"{r['knotted_true']} / {r['knotted_answer']}", f"{r['construction_true']} / {r['construction_answer']}",
                  yn(r["construction_correct"]), _max_lk(r), f"{r['held_out_accuracy']:.2f}", f"{r['score']:.2f}",
                  f"${r['cost_usd']:.3f}" if r.get("cost_usd") is not None else "–"] for r in rows])
    L += ["", f"**Mean score {sum(r['score'] for r in rows) / n:.2f}**, knotted right {sum(r['knotted_correct'] for r in rows)}/{n}, "
              f"construction right {sum(r['construction_correct'] for r in rows)}/{n}, held-out {sum(r['held_out_accuracy'] for r in rows) / n:.2f}"]
    if baselines is None:
        baselines = [p for p in newest_baselines(path.parent, st) if p != path]
    objs = list(dict.fromkeys(r["object"] for r in rows))
    base = {p: [r for r in load(p) if r["object"] in objs] for p in baselines}
    base = {p: b for p, b in base.items() if b}
    if base:
        L += ["", "## Comparison with baselines (same objects)", "", "Baseline runs: " + ", ".join(f"`{p.name}`" for p in base), ""]

        def agg(rs):
            k = len(rs)
            return [k, f"{sum(x['knotted_correct'] for x in rs)}/{k}", f"{sum(x['construction_correct'] for x in rs)}/{k}",
                    f"{sum(x['held_out_accuracy'] for x in rs) / k:.2f}", f"{sum(x['score'] for x in rs) / k:.2f}"]
        tr = []
        for b in base.values():
            tr.append([b[0]["agent"], "all"] + agg(b))
        tr.append([f"**{agent}**", "all"] + agg(rows))
        for o in objs:
            for b in base.values():
                rb = [x for x in b if x["object"] == o]
                if rb:
                    tr.append([rb[0]["agent"], o] + agg(rb))
            tr.append([f"**{agent}**", o] + agg([x for x in rows if x["object"] == o]))
        L += _table(["agent", "object", "trials", "knotted right", "built right", "held-out", "mean score"], tr)
        if len({r["seed"] for r in rows}) == 1:
            L += ["", f"{agent} ran 1 trial per object; treat differences from the baselines as indicative only."]
    L += ["", "## Flags", ""]
    for r in rows:
        f = _flags(r)
        L.append(f"- **{r['object']}** (seed {r['seed']}): " + ("; ".join(f) if f else "nothing unusual"))
    for r in rows:
        u = r.get("usage") or {}
        L += ["", f"## {r['object']} (seed {r['seed']})", "",
              f"{r['probes_used']}/{r['budget']} probes" + (f", {u.get('turns')} turns, {u.get('thought')} thinking tokens" if u else "")
              + f", {r.get('seconds')}s", "", "**Explorer's explanation:**", "",
              "> " + (r.get("description") or "(none)").replace("\n", "\n> "), "", "**Held-out slices:**", ""]
        ans = r.get("held_out_answer") or []
        L += _table(["#", "normal", "offset", "truth", "answer", ""],
                    [[f"H{i + 1}", h["normal"], f"{h['offset']:.4f}", ", ".join(t), ", ".join(ans[i]) if i < len(ans) and ans[i] else "–",
                      "✓" if i < len(ans) and sorted(map(str, ans[i] or [])) == t else "✗"]
                     for i, (h, t) in enumerate(zip(r.get("held_out_slices") or [], r["held_out_truth"]))])
        L += ["", "**Probes:**", ""]
        L += _table(["#", "normal", "offset", "components", "knots", "linking", "held-out"],
                    [[i + 1, p["normal"], p.get("offset_used", p["offset"]), p.get("components", 0), _labels(p),
                      ", ".join(f"{x['pair'][0]}–{x['pair'][1]}: {x['lk']}" for x in p.get("linking", [])[:6])
                      + (f" (+{len(p['linking']) - 6} more)" if len(p.get("linking", [])) > 6 else ""),
                      _held_tag(p, r.get("held_out_slices") or [])[0]] for i, p in enumerate(r["probes"])])
    return "\n".join(L) + "\n"


def write(path: Path, baselines: list[Path] | None = None) -> Path:
    out = path.with_name(path.stem + "_report.md")
    out.write_text(build(path, baselines), encoding="utf-8")
    return out


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?")
    ap.add_argument("--latest", metavar="AGENT")
    ap.add_argument("--baseline", action="append")
    a = ap.parse_args()
    if a.latest:
        c = sorted((p for p in Path("data/explorer").glob(f"knots_{a.latest}_*.jsonl") if p.stat().st_size), key=_stamp)
        if not c:
            ap.error(f"no non-empty knots_{a.latest} runs in data/explorer")
        path = c[-1]
    elif a.run:
        path = Path(a.run)
    else:
        ap.error("give a run file or --latest AGENT")
    print(write(path, [Path(b) for b in a.baseline] if a.baseline else None))


if __name__ == "__main__":
    main()
