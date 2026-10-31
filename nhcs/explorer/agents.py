"""
Explorers: two scripted baselines and an LLM explorer.

Every explorer gets a ProbeSession and returns an answer dict:
    {"betti": [b0, b1, b2], "dimension": 1 | 2, "orientable": bool | None,
     "held_out": [[b0, b1], ...], "description": str}

PriorExplorer
    Spends no probes. Answers the single most common case (one circle-like
    surface: b = (1, 1, 0)) and predicts every held-out slice is one closed
    curve. Any explorer worth anything has to beat this.
NaiveExplorer
    Spends half its budget on random projections and half on random slices.
    Reports the most common projection topology as the object's topology and
    the most common slice topology for every held-out slice. Projections can
    merge components and invent loops and voids, so this baseline is fooled
    in exactly the ways the benchmark is designed to expose.
TilerExplorer
    A scripted solver that knows the trick: shadows for the number of pieces,
    a slab tiling for chi, slices for the dimension and the held-out guesses.
    It shows what the probes can decide; it cannot settle orientability when
    chi is even, and it predicts held-out slices only by the commonest slice.
ClaudeExplorer
    An LLM explorer driven through tool use: it chooses its own probes, then
    submits. Needs the ``anthropic`` package and ANTHROPIC_API_KEY.
GeminiExplorer
    The same task through Google's Interactions API (google-genai SDK):
    function calling with server-side conversation state. Needs GEMINI_API_KEY
    (or GOOGLE_API_KEY). Tracks token usage, including thinking tokens, and
    reports an estimated cost.
"""

from __future__ import annotations

import json
import os
from collections import Counter

import numpy as np

from nhcs.explorer.probes import ProbeError, ProbeSession


def _mode(rows, default):
    rows = [tuple(r) for r in rows]
    return list(Counter(rows).most_common(1)[0][0]) if rows else list(default)


def dispatch(session: ProbeSession, name: str, args: dict) -> dict:
    """Run one LLM tool call against the session (raises ProbeError/KeyError/TypeError on bad calls)."""
    if name == "slice":
        return session.slice(args["normal"], args["offset"])
    if name == "project":
        return session.project(args["direction"])
    if name == "slab":
        return session.slab(args["normal"], args["lo"], args["hi"])
    if name == "knot_slice":
        return session.knot_slice(args["normal"], args["offset"])
    raise KeyError(f"unknown probe {name!r}")


class PriorExplorer:
    name = "prior"

    def run(self, session: ProbeSession) -> dict:
        return {"betti": [1, 1, 0], "dimension": 2, "orientable": None,
                "held_out": [[1, 1] for _ in session.held_out],
                "description": "No probes. Most common case guessed."}


class NaiveExplorer:
    name = "naive"

    def __init__(self, seed: int = 0) -> None:
        self.rng = np.random.default_rng(seed)

    def _dir(self):
        v = self.rng.standard_normal(4)
        return v / np.linalg.norm(v)

    def run(self, session: ProbeSession) -> dict:
        proj, sl = [], []
        n_proj = session.remaining // 2
        for _ in range(n_proj):
            proj.append(session.project(self._dir())["betti"])
        tries = 0
        while session.remaining > 0 and tries < 50:
            tries += 1
            n = self._dir()
            h = session.obj.points @ n  # the naive explorer peeks at the extent only
            c = float(self.rng.uniform(*np.percentile(h, [8, 92])))
            try:
                sl.append(session.slice(n, c)["betti"][:2])
            except ProbeError:
                continue
        b = _mode(proj, [1, 1, 0])
        s = _mode(sl, [1, 1])
        return {"betti": b, "dimension": 2 if s[1] > 0 else 1, "orientable": None,
                "held_out": [s for _ in session.held_out],
                "description": "Most common projection topology; most common slice topology."}


class TilerExplorer:
    name = "tiler"
    # four slabs over [-1, 1] overlapping in 0.1-wide bands at -0.5, 0, 0.5
    SLABS = [(-1.0, -0.45), (-0.55, 0.05), (-0.05, 0.55), (0.45, 1.0)]
    OVERLAPS = [(-0.55, -0.45), (-0.05, 0.05), (0.45, 0.55)]

    def __init__(self, seed: int = 0, n_proj: int = 2) -> None:
        self.rng = np.random.default_rng(seed)
        self.n_proj = n_proj

    def _dir(self):
        v = self.rng.standard_normal(4)
        return v / np.linalg.norm(v)

    def _tile(self, session):
        for _ in range(20):
            n = self._dir()
            try:
                return (sum(session.slab(n, lo, hi)["euler"] for lo, hi in self.SLABS)
                        - sum(session.slab(n, lo, hi)["euler"] for lo, hi in self.OVERLAPS))
            except ProbeError:  # a held-out slice is in the way: the refused probe cost nothing
                if session.remaining < 7:
                    return None
                continue  # (any slabs already spent are lost; rare)
        return None

    def run(self, session: ProbeSession) -> dict:
        b0 = max([session.project(self._dir())["betti"][0] for _ in range(min(self.n_proj, session.remaining))] or [1])
        chi = self._tile(session) if session.remaining >= 7 else None
        sl = []
        tries = 0
        while session.remaining > 0 and tries < 50:
            tries += 1
            try:
                sl.append(session.slice(self._dir(), float(self.rng.uniform(-0.6, 0.6)))["betti"][:2])
            except ProbeError:
                continue
        nonempty = [x for x in sl if x != [0, 0]]
        s = _mode(sl, [1, 1])
        dim = 2 if any(x[1] > 0 for x in nonempty) or not nonempty else 1
        if chi is None:
            chi = 0
        orient = None
        if dim == 1:
            betti = [b0, b0 - chi, 0]
        elif b0 == 1 and chi % 2:
            betti, orient = [1, 1 - chi, 0], False
        else:  # even chi: guess every piece orientable (a sphere if chi = 2 per piece)
            betti = [b0, 2 * b0 - chi, b0]
            orient = True if (b0 == 1 and chi == 2) else None
        return {"betti": betti, "dimension": dim, "orientable": orient,
                "held_out": [s for _ in session.held_out],
                "description": f"Slab tiling gives chi = {chi}; shadows give {b0} piece(s); slices say dimension {dim}."}


SYSTEM_PROMPT = """You are exploring a hidden object in four-dimensional space (R^4). You cannot see it. You can only probe it, and you have a limited probe budget.

What you may assume: the object is compact and centred at the origin, with every point inside the unit ball. It is made of finitely many smooth closed curves and/or smooth closed surfaces (surfaces may be non-orientable), embedded in R^4. Pieces are usually disjoint, but curves may also meet at isolated points, forming a graph rather than a set of separate circles. The object is turned to a random orientation, so no coordinate axis is special. It is tame: no feature (a tube, a neck, a hole, the gap between two pieces) is narrower than about 0.08, so probes taken at generic positions show the object as it is.

Probes (each costs one unit of budget):
- slice(normal, offset): the 3D cross-section {x in R^4 : normal . x = offset}. A slice of a surface is generically a set of closed curves; a slice of a curve is generically a finite set of points.
- project(direction): the 3D shadow of the object along `direction`. Shadows never split a connected piece, but they can merge pieces and they can create loops and voids that are not in the object, where the shadow crosses itself.
- slab(normal, lo, hi): the part of the object with lo <= normal . x <= hi, measured in R^4 itself (nothing is projected). The width hi - lo must be between 0.1 and 0.6. Overlapping slabs form a cover of the object, so Mayer-Vietoris arguments apply; overlaps should be at least 0.1 wide (slabs that merely touch do not give a usable cover).

Every probe reports the Betti numbers [b0, b1, b2] of what it saw (b0 = connected pieces, b1 = independent loops, b2 = enclosed voids), their alternating sum `euler`, the point count, the sizes of the largest connected pieces, and the extent. Betti numbers here are rational (computed over a field of characteristic 0), so torsion is invisible: a Klein bottle is (1,1,0) and a projective plane is (1,0,0).

Your job:
1. Work out the object's own Betti numbers [b0, b1, b2] (rational), its dimension (1 for curves, 2 for surfaces), and whether it is orientable if it is made of surfaces. Some properties may not be decidable from these probes; if you cannot determine orientability, give your best guess for the Betti numbers and set orientable to null, and say so in the description.
2. Predict the [b0, b1] of each held-out slice listed below. You may not probe those slices, or probe near them along nearly the same normal.
3. Describe in plain words what you think the object is and why.

Think like a topologist. A family of slices swept along one normal is a Morse-theory movie of the object. Be economical with probes, and do not trust a single projection. When you are done, call submit. If you run out of budget you must still submit."""


TOOLS = [
    {"name": "slice", "description": "3D cross-section of the hidden object by the hyperplane normal . x = offset.",
     "input_schema": {"type": "object", "properties": {
         "normal": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
         "offset": {"type": "number"}}, "required": ["normal", "offset"]}},
    {"name": "project", "description": "3D shadow of the hidden object along a 4D direction.",
     "input_schema": {"type": "object", "properties": {
         "direction": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4}},
         "required": ["direction"]}},
    {"name": "slab", "description": "The part of the hidden object with lo <= normal . x <= hi, in R^4 (0.1 <= hi - lo <= 0.6).",
     "input_schema": {"type": "object", "properties": {
         "normal": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
         "lo": {"type": "number"}, "hi": {"type": "number"}}, "required": ["normal", "lo", "hi"]}},
    {"name": "submit", "description": "Submit your final answer. Ends the exploration.",
     "input_schema": {"type": "object", "properties": {
         "betti": {"type": "array", "items": {"type": "integer"}, "minItems": 3, "maxItems": 3},
         "dimension": {"type": "integer", "description": "1 for curves, 2 for surfaces"},
         "orientable": {"type": ["boolean", "null"]},
         "held_out": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}, "minItems": 2, "maxItems": 2}},
         "description": {"type": "string"}},
         "required": ["betti", "dimension", "held_out", "description"]}},
]


class ClaudeExplorer:
    """
    LLM explorer using the Anthropic Messages API with tool use.

    Parameters
    ----------
    model : str
        Model id, e.g. "claude-opus-5-5".
    max_turns : int
        Hard cap on API round-trips (each turn may contain several tool calls).
    """

    name = "claude"

    def __init__(self, model: str = "claude-opus-5-5", max_turns: int = 40, client=None,
                 system_prompt: str | None = None, tools: list | None = None) -> None:
        self.model = model
        self.max_turns = max_turns
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.tools = tools or TOOLS
        if client is None:
            try:
                import anthropic  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("ClaudeExplorer needs the anthropic package: pip install anthropic") from exc
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError("set ANTHROPIC_API_KEY to run ClaudeExplorer")
            client = anthropic.Anthropic()
        self.client = client
        self.transcript: list = []

    def run(self, session: ProbeSession) -> dict:
        held = "\n".join(f"  {i + 1}. normal={h.as_dict()['normal']}, offset={h.as_dict()['offset']}"
                         for i, h in enumerate(session.held_out))
        messages = [{"role": "user", "content":
                     f"Probe budget: {session.budget}.\nHeld-out slices to predict:\n{held}\n\nBegin exploring."}]
        answer = None
        for _ in range(self.max_turns):
            resp = self.client.messages.create(model=self.model, max_tokens=4000, system=self.system_prompt,
                                               tools=self.tools, messages=messages)
            content = [b.model_dump() if hasattr(b, "model_dump") else b for b in resp.content]
            messages.append({"role": "assistant", "content": content})
            calls = [b for b in content if b.get("type") == "tool_use"]
            if not calls:
                messages.append({"role": "user", "content": "Use a probe or call submit."})
                continue
            results = []
            for c in calls:
                name, args = c["name"], c.get("input", {})
                if name == "submit":
                    answer = args
                    results.append({"type": "tool_result", "tool_use_id": c["id"], "content": "submitted"})
                    continue
                try:
                    out = dispatch(session, name, args)
                    out = {**out, "probes_remaining": session.remaining}
                    results.append({"type": "tool_result", "tool_use_id": c["id"], "content": json.dumps(out)})
                except (ProbeError, KeyError, TypeError) as exc:
                    results.append({"type": "tool_result", "tool_use_id": c["id"], "is_error": True,
                                    "content": f"{exc}. Probes remaining: {session.remaining}."})
            messages.append({"role": "user", "content": results})
            if answer is not None:
                break
        self.transcript = messages
        return answer or {"betti": [], "held_out": [], "description": "(no answer submitted)"}


# USD per 1M tokens (input, output incl. thinking), from ai.google.dev, checked 2026-10-30.
# gemini-4-argon is introductory through 2026-11-30, then $4.00 / $20.00.
GEMINI_PRICES = {
    "gemini-4-argon": ((2.00, 10.00), (4.00, 20.00), "2026-12-01"),
    "gemini-3.8-flash": ((0.75, 3.75), (1.50, 7.50), "2027-01-01"),
}


def gemini_price(model: str, today: str | None = None) -> tuple[float, float] | None:
    import datetime as _dt
    entry = GEMINI_PRICES.get(model)
    if entry is None:
        return None
    now, later, switch = entry
    today = today or _dt.date.today().isoformat()
    return later if today >= switch else now


def _attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


class GeminiExplorer:
    """
    LLM explorer on the Gemini Interactions API.

    Parameters
    ----------
    model : str
        e.g. "gemini-4-argon" (flagship) or "gemini-3.8-flash" (cheaper, free tier).
    thinking_level : "low" | "medium" | "high"
    max_turns : int
        Hard cap on API round-trips.
    client : optional
        Pre-built client (tests pass a fake).
    """

    name = "gemini"

    def __init__(self, model: str = "gemini-4-argon", thinking_level: str = "medium",
                 max_turns: int = 40, client=None, system_prompt: str | None = None, tools: list | None = None) -> None:
        self.model = model
        self.system_prompt = system_prompt or SYSTEM_PROMPT
        self.tool_specs = tools or TOOLS
        self.thinking_level = thinking_level
        self.max_turns = max_turns
        if client is None:
            try:
                from google import genai  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("GeminiExplorer needs google-genai: pip install google-genai") from exc
            if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
                raise RuntimeError("set GEMINI_API_KEY to run GeminiExplorer")
            client = genai.Client()
        self.client = client
        self.usage = {"input": 0, "output": 0, "thought": 0, "turns": 0}
        self.notes: list[str] = []

    @staticmethod
    def _tools(tools: list | None = None):
        out = []
        for t in tools or TOOLS:
            schema = json.loads(json.dumps(t["input_schema"]))
            for k, v in schema.get("properties", {}).items():  # Gemini schemas take a single type
                if isinstance(v.get("type"), list):
                    schema["properties"][k] = {**v, "type": [x for x in v["type"] if x != "null"][0]}
            out.append({"type": "function", "name": t["name"], "description": t["description"], "parameters": schema})
        return out

    def cost_usd(self) -> float | None:
        p = gemini_price(self.model)
        if p is None:
            return None
        return (self.usage["input"] * p[0] + (self.usage["output"] + self.usage["thought"]) * p[1]) / 1e6

    def _call(self, **kw):
        it = self.client.interactions.create(model=self.model, system_instruction=self.system_prompt, tools=self._tools(self.tool_specs),
                                            generation_config={"thinking_level": self.thinking_level}, **kw)
        u = _attr(it, "usage")
        if u is not None:
            self.usage["input"] += _attr(u, "total_input_tokens", 0) or 0
            self.usage["output"] += _attr(u, "total_output_tokens", 0) or 0
            self.usage["thought"] += _attr(u, "total_thought_tokens", 0) or 0
        self.usage["turns"] += 1
        return it

    def run(self, session: ProbeSession) -> dict:
        held = "\n".join(f"  {i + 1}. normal={h.as_dict()['normal']}, offset={h.as_dict()['offset']}"
                         for i, h in enumerate(session.held_out))
        it = self._call(input=f"Probe budget: {session.budget}.\nHeld-out slices to predict:\n{held}\n\nBegin exploring.")
        answer = None
        for _ in range(self.max_turns - 1):
            steps = _attr(it, "steps", []) or []
            for st in steps:
                txt = _attr(st, "text")
                if _attr(st, "type") == "text" and txt:
                    self.notes.append(txt)
            calls = [st for st in steps if _attr(st, "type") == "function_call"]
            if not calls:
                it = self._call(input="Use a probe or call submit.", previous_interaction_id=_attr(it, "id"))
                continue
            results = []
            for c in calls:
                name, args = _attr(c, "name"), dict(_attr(c, "arguments", {}) or {})
                if name == "submit":
                    answer = args
                    out = "submitted"
                else:
                    try:
                        res = dispatch(session, name, args)
                        out = json.dumps({**res, "probes_remaining": session.remaining})
                    except (ProbeError, KeyError, TypeError) as exc:
                        out = f"error: {exc}. Probes remaining: {session.remaining}."
                results.append({"type": "function_result", "name": name, "call_id": _attr(c, "id"),
                                "result": [{"type": "text", "text": out}]})
            if answer is not None:
                break
            it = self._call(input=results, previous_interaction_id=_attr(it, "id"))
        return answer or {"betti": [], "held_out": [], "description": "(no answer submitted)"}


EXPLORERS = {"prior": PriorExplorer, "naive": NaiveExplorer, "tiler": TilerExplorer, "claude": ClaudeExplorer, "gemini": GeminiExplorer}
