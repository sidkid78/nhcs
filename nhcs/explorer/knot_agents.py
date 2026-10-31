"""
Explorers for the knotted-sphere calibration benchmark (see knot_probes.py).

Scripted baselines:
  KnotPrior   no probes; answers the commonest case (knotted, spun trefoil).
  KnotNaive   random slices; "knotted" if any slice shows a knotted component;
              base knot = the prime factor seen most. Falls for the 1-twist trap.
  KnotLinker  random slices, and also reads the linking numbers: the largest
              pairwise linking number seen is taken as the twist n (slices across
              the spin axis link n times), then applies Zeeman: twist 1 means
              unknotted. Shows how far the probe data get a script that knows
              the theory, if its random slices happen to cross the spin axis.

LLM explorers reuse ClaudeExplorer / GeminiExplorer with KNOT_PROMPT and KNOT_TOOLS.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from nhcs.explorer.knot_probes import KnotSession, _label
from nhcs.explorer.probes import ProbeError

KNOT_PROMPT = """You are exploring a hidden surface in four-dimensional space (R^4). You cannot see it. You can only probe it, and you have a limited probe budget.

What you may assume: the surface is a smooth 2-sphere embedded in R^4, centred at the origin, inside the unit ball, and turned to a random orientation, so no coordinate axis is special. It was made by one of two classical constructions applied to a classical knot K in R^3 (K may be the unknot):
- Artin spinning of K ("spun"), or
- Zeeman n-twist-spinning of K with n >= 1 ("twist-spun").

Probe (each costs one unit of budget):
- knot_slice(normal, offset): the 3D cross-section {x in R^4 : normal . x = offset}, which is a link in R^3. It reports the number of components; for each component its knot type when it is small enough to name (names like "unknot", "3_1", "m3_1" for the mirror image, "4_1", "3_1 # m3_1" for a connected sum), always with its Alexander polynomial (coefficients, lowest power first), Seifert genus, whether it is fibred, and tau (from knot Floer homology); and the pairwise linking numbers of the components (absolute values, since the components carry no orientation; pairs with linking number 0 are omitted).

Your job:
1. Decide whether the sphere is knotted in R^4 (not isotopic to the standard unknotted 2-sphere).
2. Identify the construction: "unknotted", "spun" or "twist-spun"; the knot K (e.g. "3_1", "4_1"); and for twist-spinning the twist n.
3. Predict each held-out slice listed below: the list of its components' labels, sorted alphabetically, where a component's label is its name, or "knot(alexander=[...], genus=g)" exactly as the probe would print it when there is no name. You may not probe those slices, or probe near them along nearly the same normal.
4. Explain your reasoning.

Use what you know about these constructions and their cross-sections. Knotted cross-sections do not by themselves make a sphere knotted. Be economical with probes. When you are done, call submit. If you run out of budget you must still submit."""

KNOT_TOOLS = [
    {"name": "knot_slice", "description": "Cross-section of the hidden sphere by the hyperplane normal . x = offset, read as a link in R^3.",
     "input_schema": {"type": "object", "properties": {
         "normal": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
         "offset": {"type": "number"}}, "required": ["normal", "offset"]}},
    {"name": "submit", "description": "Submit your final answer. Ends the exploration.",
     "input_schema": {"type": "object", "properties": {
         "knotted": {"type": "boolean"},
         "construction": {"type": "string", "enum": ["unknotted", "spun", "twist-spun"]},
         "knot": {"type": "string", "description": "the knot K, e.g. 3_1 or 4_1; 'unknot' if K is trivial"},
         "twist": {"type": "integer", "description": "the twist n for twist-spinning; 0 otherwise"},
         "held_out": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
         "description": {"type": "string"}},
         "required": ["knotted", "construction", "knot", "held_out", "description"]}},
]


def _dir(rng):
    v = rng.standard_normal(4)
    return v / np.linalg.norm(v)


def _random_slices(session: KnotSession, rng) -> list[dict]:
    out, tries = [], 0
    while session.remaining > 0 and tries < 80:
        tries += 1
        n = _dir(rng)
        h = session.obj.V @ n  # scripted baselines peek at the extent only, like NaiveExplorer
        try:
            out.append(session.knot_slice(n, float(rng.uniform(*np.percentile(h, [10, 90])))))
        except ProbeError:
            continue
    return out


def _prime(label: str | None) -> str | None:
    if not label or label == "unknot":
        return None
    first = label.split(" # ")[0].strip("()")
    return first[1:] if first.startswith("m") and not first.startswith("m(") else first


def _summary(sl: list[dict]) -> tuple[Counter, list[str], int]:
    primes = Counter(p for s in sl for c in s["knots"] if (p := _prime(c["name"])))
    labels = [sorted(_label(c) for c in s["knots"]) for s in sl if not s["empty"]]
    lk = max([x["lk"] for s in sl for x in s["linking"]] or [0])
    return primes, labels, lk


class KnotPrior:
    name = "prior"

    def run(self, session: KnotSession) -> dict:
        return {"knotted": True, "construction": "spun", "knot": "3_1", "twist": 0,
                "held_out": [["3_1 # m3_1"] for _ in session.held_out], "description": "No probes. Commonest case."}


class KnotNaive:
    name = "naive"

    def __init__(self, seed: int = 0) -> None:
        self.rng = np.random.default_rng(seed)

    def run(self, session: KnotSession) -> dict:
        primes, labels, _ = _summary(_random_slices(session, self.rng))
        mode = list(Counter(tuple(x) for x in labels).most_common(1)[0][0]) if labels else ["unknot"]
        if primes:
            k = primes.most_common(1)[0][0]
            return {"knotted": True, "construction": "spun", "knot": k, "twist": 0,
                    "held_out": [mode for _ in session.held_out], "description": f"Knotted slices ({k}) seen: guessed spun {k}."}
        return {"knotted": False, "construction": "unknotted", "knot": "unknot", "twist": 0,
                "held_out": [mode for _ in session.held_out], "description": "No knotted slice seen."}


class KnotLinker:
    name = "linker"

    def __init__(self, seed: int = 0) -> None:
        self.rng = np.random.default_rng(seed)

    def run(self, session: KnotSession) -> dict:
        primes, labels, lk = _summary(_random_slices(session, self.rng))
        mode = list(Counter(tuple(x) for x in labels).most_common(1)[0][0]) if labels else ["unknot"]
        held = [mode for _ in session.held_out]
        if not primes:
            return {"knotted": False, "construction": "unknotted", "knot": "unknot", "twist": 0, "held_out": held,
                    "description": "No knotted slice seen."}
        k = primes.most_common(1)[0][0]
        if lk == 0:
            return {"knotted": True, "construction": "spun", "knot": k, "twist": 0, "held_out": held,
                    "description": f"Knotted slices ({k}), no linked circles: spun {k}."}
        return {"knotted": lk != 1, "construction": "twist-spun", "knot": k, "twist": lk, "held_out": held,
                "description": f"Slice circles link {lk} times: {lk}-twist-spun {k}" + (" (unknotted by Zeeman)" if lk == 1 else "") + "."}


KNOT_EXPLORERS = {"prior": KnotPrior, "naive": KnotNaive, "linker": KnotLinker}
