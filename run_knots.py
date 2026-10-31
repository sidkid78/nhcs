"""
Run the knotted-sphere calibration benchmark.

    python run_knots.py                                   # prior, naive, linker baselines, 7 spheres, 3 seeds
    python run_knots.py --agent gemini --seeds 1 --max-cost 5
    python run_knots.py --agent gemini --objects twist1_trefoil,spun_trefoil

Every hidden object is a 2-sphere in R^4 (Betti numbers are always [1, 0, 1]);
the question is whether it is knotted and how it was built. See
nhcs/explorer/knot_probes.py. Results go to data/explorer/knots_<agent>_<stamp>.jsonl;
LLM runs also get <run>_report.md (knot_report.py; --report all|llm|none).

Score = 0.5 * knotted right + 0.25 * construction right + 0.25 * held-out accuracy.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

from nhcs.explorer.agents import ClaudeExplorer, GeminiExplorer
from nhcs.explorer.knot_agents import KNOT_EXPLORERS, KNOT_PROMPT, KNOT_TOOLS
from nhcs.explorer.knot_probes import KNOT_SUITE, KnotSession, make_surface


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="prior,naive,linker", help="comma list of: prior, naive, linker, claude, gemini")
    ap.add_argument("--objects", default="all", help="comma list of: " + ", ".join(KNOT_SUITE))
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--budget", type=int, default=20)
    ap.add_argument("--held-out", type=int, default=3)
    ap.add_argument("--model", default=None, help="default: claude-opus-5-5 / gemini-4-argon")
    ap.add_argument("--thinking", default="medium", help="gemini thinking_level: low | medium | high")
    ap.add_argument("--max-cost", type=float, default=10.0, help="stop starting new gemini trials past this many USD")
    ap.add_argument("--report", default="llm", choices=["llm", "all", "none"],
                    help="write <run>_report.md for LLM agents (default), every agent, or none")
    args = ap.parse_args()

    names = list(KNOT_SUITE) if args.objects == "all" else args.objects.split(",")
    out_dir = Path("data/explorer"); out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    for agent_name in args.agent.split(","):
        path = out_dir / f"knots_{agent_name}_{stamp}.jsonl"
        rows, spent = [], 0.0
        with path.open("w", encoding="utf-8") as f:
            for name in names:
                for seed in range(args.seeds):
                    if agent_name == "gemini" and spent >= args.max_cost:
                        print(f"[gemini] cost cap ${args.max_cost:.2f} reached; skipping {name} seed={seed}")
                        continue
                    session = KnotSession(make_surface(name, seed), budget=args.budget, n_held_out=args.held_out, seed=1000 + seed)
                    if agent_name == "claude":
                        agent = ClaudeExplorer(model=args.model or "claude-opus-5-5", system_prompt=KNOT_PROMPT, tools=KNOT_TOOLS)
                    elif agent_name == "gemini":
                        agent = GeminiExplorer(model=args.model or "gemini-4-argon", thinking_level=args.thinking,
                                               system_prompt=KNOT_PROMPT, tools=KNOT_TOOLS)
                    elif agent_name == "prior":
                        agent = KNOT_EXPLORERS["prior"]()
                    else:
                        agent = KNOT_EXPLORERS[agent_name](seed)
                    t0 = time.perf_counter()
                    answer = agent.run(session)
                    r = session.score(answer)
                    r.update(agent=agent_name, seed=seed, seconds=round(time.perf_counter() - t0, 1),
                             description=answer.get("description", ""), probes=session.log)
                    if agent_name in ("claude", "gemini"):
                        r["model"] = agent.model
                    if agent_name == "gemini":
                        cost = agent.cost_usd() or 0.0
                        spent += cost
                        r.update(usage=agent.usage, cost_usd=round(cost, 4), notes=agent.notes, thinking_level=agent.thinking_level)
                    f.write(json.dumps(r) + "\n"); f.flush()
                    rows.append(r)
                    print(f"[{agent_name}] {name:20s} seed={seed}  knotted {r['knotted_answer']} vs {r['knotted_true']}"
                          f"  built: {r['construction_answer']!r} vs {r['construction_true']!r}"
                          f"  held-out {r['held_out_accuracy']:.2f}  score {r['score']:.2f}"
                          + (f"  ~${r['cost_usd']:.3f}" if "cost_usd" in r else ""), flush=True)
        if not rows:
            continue
        print(f"\n== {agent_name}: {len(rows)} trials -> {path}" + (f"  (estimated spend ${spent:.2f})" if spent else ""))
        print(f"   {'object':20s} knotted   built   held-out   score")

        def line(label, r):
            print(f"   {label:20s} {sum(x['knotted_correct'] for x in r)}/{len(r):<6d} {sum(x['construction_correct'] for x in r)}/{len(r):<5d} "
                  f"{sum(x['held_out_accuracy'] for x in r) / len(r):.2f}       {sum(x['score'] for x in r) / len(r):.2f}")

        for name in names:
            r = [x for x in rows if x["object"] == name]
            if r:
                line(name, r)
        line("ALL", rows)
        if args.report == "all" or (args.report == "llm" and agent_name in ("claude", "gemini")):
            from knot_report import write as write_report
            print(f"   report -> {write_report(path)}")
        print()


if __name__ == "__main__":
    main()
