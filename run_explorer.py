"""
Run the 4D explorer benchmark.

    python run_explorer.py                              # prior, naive and tiler baselines, all objects, 3 seeds
    python run_explorer.py --agent claude --seeds 1     # Claude explorer (needs ANTHROPIC_API_KEY)
    python run_explorer.py --agent claude --model claude-sonnet-5-5 --objects klein_bottle,clifford_torus
    python run_explorer.py --agent gemini --seeds 1 --max-cost 10      # gemini-4-argon (needs GEMINI_API_KEY)
    python run_explorer.py --agent gemini --model gemini-3.8-flash      # cheaper; has a free tier

Every trial gets a freshly posed copy of the object (seed sets the random
rotation and the held-out slices). Results go to
data/explorer/<agent>_<timestamp>.jsonl, one line per trial, including the
explorer's own description and its probe log; a summary table is printed,
and LLM runs also get a Markdown report (<run>_report.md, see
explorer_report.py; --report all|llm|none).

Headline score = 0.5 * core + 0.5 * held-out accuracy, where core = pieces,
dimension and Euler characteristic all right (what the probes can decide).
Exact Betti numbers are reported alongside; for chi-even surfaces they need an
orientability guess.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from nhcs.explorer.agents import EXPLORERS
from nhcs.explorer.objects import SUITE, make
from nhcs.explorer.probes import ProbeSession


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="prior,naive,tiler", help="comma list of: " + ", ".join(EXPLORERS))
    ap.add_argument("--objects", default="all", help="comma list of: " + ", ".join(SUITE))
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--budget", type=int, default=20)
    ap.add_argument("--held-out", type=int, default=4)
    ap.add_argument("--model", default=None, help="default: claude-opus-5-5 / gemini-4-argon")
    ap.add_argument("--thinking", default="medium", help="gemini thinking_level: low | medium | high")
    ap.add_argument("--max-cost", type=float, default=10.0,
                    help="stop starting new gemini trials once estimated spend passes this many USD")
    ap.add_argument("--report", default="llm", choices=["llm", "all", "none"],
                    help="write <run>_report.md for LLM agents (default), every agent, or none")
    args = ap.parse_args()

    names = list(SUITE) if args.objects == "all" else args.objects.split(",")
    out_dir = Path("data/explorer"); out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")

    for agent_name in args.agent.split(","):
        path = out_dir / f"{agent_name}_{stamp}.jsonl"
        rows = []
        spent = 0.0
        with path.open("w", encoding="utf-8") as f:
            for name in names:
                for seed in range(args.seeds):
                    obj = make(name, seed)
                    session = ProbeSession(obj, budget=args.budget, n_held_out=args.held_out, seed=1000 + seed)
                    if agent_name == "gemini" and spent >= args.max_cost:
                        print(f"[gemini] cost cap ${args.max_cost:.2f} reached (spent ~${spent:.2f}); skipping {name} seed={seed}")
                        continue
                    if agent_name == "claude":
                        agent = EXPLORERS["claude"](model=args.model or "claude-opus-5-5")
                    elif agent_name == "gemini":
                        agent = EXPLORERS["gemini"](model=args.model or "gemini-4-argon", thinking_level=args.thinking)
                    elif agent_name in ("naive", "tiler"):
                        agent = EXPLORERS[agent_name](seed)
                    else:
                        agent = EXPLORERS[agent_name]()
                    t0 = time.perf_counter()
                    answer = agent.run(session)
                    result = session.score(answer)
                    result.update(agent=agent_name, seed=seed, seconds=round(time.perf_counter() - t0, 1),
                                  description=answer.get("description", ""), probes=session.log)
                    if agent_name in ("claude", "gemini"):
                        result["model"] = agent.model
                    if agent_name == "gemini":
                        cost = agent.cost_usd() or 0.0
                        spent += cost
                        result.update(usage=agent.usage, cost_usd=round(cost, 4), notes=agent.notes,
                                      thinking_level=agent.thinking_level)
                    f.write(json.dumps(result) + "\n"); f.flush()
                    rows.append(result)
                    print(f"[{agent_name}] {name:20s} seed={seed}  betti {result['betti_answer']} vs {result['betti_true']}"
                          f"  chi {result['euler_answer']} vs {result['euler_true']}  core {'Y' if result['core_correct'] else 'n'}"
                          f"  held-out {result['held_out_accuracy']:.2f}  score {result['score']:.2f}"
                          + (f"  ~${result['cost_usd']:.3f}" if "cost_usd" in result else ""), flush=True)
        if not rows:
            continue
        print(f"\n== {agent_name}: {len(rows)} trials -> {path}" + (f"  (estimated spend ${spent:.2f})" if spent else ""))
        print(f"   {'object':20s} core   betti exact   held-out acc   mean score")

        def line(label, r):
            print(f"   {label:20s} {sum(x['core_correct'] for x in r)}/{len(r):<4d} "
                  f"{sum(x['betti_exact'] for x in r)}/{len(r):<11d} "
                  f"{sum(x['held_out_accuracy'] for x in r) / len(r):.2f}           "
                  f"{sum(x['score'] for x in r) / len(r):.2f}")

        for name in names:
            r = [x for x in rows if x["object"] == name]
            if r:
                line(name, r)
        line("ALL", rows)
        if args.report == "all" or (args.report == "llm" and agent_name in ("claude", "gemini")):
            from explorer_report import write as write_report
            print(f"   report -> {write_report(path)}")
        print()


if __name__ == "__main__":
    main()
