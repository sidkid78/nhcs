"""
Tests: 4D explorer benchmark — hidden objects, probes, scoring, explorers.
"""

import json
import math
from types import SimpleNamespace

import numpy as np
import pytest

from nhcs.explorer import objects as O
from nhcs.explorer.agents import ClaudeExplorer, NaiveExplorer, PriorExplorer, TilerExplorer
from nhcs.explorer.probes import ProbeError, ProbeSession
from nhcs.explorer.topology import betti_at_scale, voxel_downsample


def _unposed_torus():
    u, v = O._grid(130, 130)
    pts = np.stack([np.cos(u), np.sin(u), np.cos(v), np.sin(v)], -1).reshape(-1, 4) / math.sqrt(2)
    return O._finish("torus_unposed", pts, [1, 2, 1], 2, True, np.random.default_rng(0), pose=False)


class TestObjects:
    @pytest.mark.parametrize("name", list(O.SUITE))
    def test_ground_truth_betti_verified_at_resolution(self, name):
        obj = O.make(name, seed=0)
        scale = O.RESOLUTION * obj.spacing
        pts = voxel_downsample(obj.points, scale / 2.5)
        assert betti_at_scale(pts, scale, 2) == obj.betti

    def test_objects_are_normalised(self):
        for name in O.SUITE:
            p = O.make(name, 1).points
            assert p.shape[1] == 4
            assert np.allclose(p.mean(0), 0, atol=1e-9)
            assert np.linalg.norm(p, axis=1).max() == pytest.approx(1.0)

    def test_connected_sums_have_known_euler(self):
        assert [O.euler(O.make(n, 0).betti) for n in ("genus_2", "genus_3", "dyck_surface")] == [-2, -4, -1]
        assert O.orientability_decidable(O.make("dyck_surface", 0))
        assert O.orientability_decidable(O.make("projective_plane", 0))
        assert not O.orientability_decidable(O.make("klein_bottle", 0))
        assert not O.orientability_decidable(O.make("genus_2", 0))

    def test_pose_depends_on_seed(self):
        a, b = O.make("clifford_torus", 0).points, O.make("clifford_torus", 1).points
        assert not np.allclose(a[:10], b[:10])


class TestProbes:
    def test_torus_slice_movie_matches_theory(self):
        """Clifford torus sliced by w = c: two circles, merging near 1/sqrt2, then nothing."""
        s = ProbeSession(_unposed_torus(), budget=10, n_held_out=0)
        assert s.slice([0, 0, 0, 1], 0.0)["betti"][:2] == [2, 2]
        assert s.slice([0, 0, 0, 1], 0.6)["betti"][:2] == [2, 2]
        assert s.slice([0, 0, 0, 1], 0.70)["betti"][:2] == [1, 1]
        assert s.slice([0, 0, 0, 1], 0.75)["empty"]

    def test_projection_never_splits_components(self):
        obj = O.make("torus_plus_sphere", 0)
        s = ProbeSession(obj, budget=6, n_held_out=0)
        rng = np.random.default_rng(3)
        for _ in range(6):
            assert s.project(rng.standard_normal(4))["betti"][0] <= obj.betti[0]

    def test_budget_is_enforced(self):
        s = ProbeSession(O.make("circle", 0), budget=2, n_held_out=0)
        s.project([1, 0, 0, 0]); s.project([0, 1, 0, 0])
        with pytest.raises(ProbeError, match="budget"):
            s.project([0, 0, 1, 0])

    def test_held_out_slices_cannot_be_probed(self):
        s = ProbeSession(O.make("sphere", 0), budget=5, n_held_out=2, seed=4)
        h = s.held_out[0]
        with pytest.raises(ProbeError, match="held-out"):
            s.slice(h.normal, h.offset)
        with pytest.raises(ProbeError, match="held-out"):  # the same hyperplane, written with -normal
            s.slice([-x for x in h.normal], -h.offset)
        with pytest.raises(ProbeError, match="held-out"):  # the mirror image: same answer on symmetric objects
            s.slice(h.normal, -h.offset)
        with pytest.raises(ProbeError, match="held-out"):
            s.slice([-x for x in h.normal], h.offset)
        assert s.remaining == 5  # rejected probes cost nothing

    def test_mirrored_slice_would_leak_on_a_symmetric_object(self):
        """Why the mirror is blocked: the sphere's slice at -offset has the held-out answer."""
        from nhcs.explorer.probes import _unit
        s = ProbeSession(O.make("sphere", 0), budget=1, n_held_out=4, seed=4)
        for h, t in zip(s.held_out, s._held_truth):
            assert s._measure_slice(_unit(h.normal), -h.offset)["betti"][:2] == t

    @pytest.mark.parametrize("name,chi", [("clifford_torus", 0), ("klein_bottle", 0), ("sphere", 2),
                                          ("projective_plane", 1), ("torus_plus_sphere", 2), ("dyck_surface", -1)])
    def test_slab_tiling_recovers_euler(self, name, chi):
        s = ProbeSession(O.make(name, 1), budget=7, n_held_out=0)
        n = np.random.default_rng(7).standard_normal(4)
        total = (sum(s.slab(n, lo, hi)["euler"] for lo, hi in TilerExplorer.SLABS)
                 - sum(s.slab(n, lo, hi)["euler"] for lo, hi in TilerExplorer.OVERLAPS))
        assert total == chi

    def test_slab_width_limits(self):
        s = ProbeSession(O.make("sphere", 0), budget=5, n_held_out=0)
        with pytest.raises(ProbeError, match="width"):
            s.slab([1, 0, 0, 0], -1, 1)  # would swallow the whole object
        with pytest.raises(ProbeError, match="width"):
            s.slab([1, 0, 0, 0], 0, 0.05)
        assert s.remaining == 5

    def test_slab_near_held_out_rejected(self):
        s = ProbeSession(O.make("sphere", 0), budget=5, n_held_out=1, seed=4)
        h = s.held_out[0]
        with pytest.raises(ProbeError, match="held-out"):
            s.slab(h.normal, h.offset - 0.05, h.offset + 0.05)
        with pytest.raises(ProbeError, match="held-out"):
            s.slab(h.normal, -h.offset - 0.05, -h.offset + 0.05)
        far = abs(h.offset) + 0.1  # same normal, clear of both the offset and its mirror: fine
        s.slab(h.normal, far, far + 0.2)

    def test_bad_direction_rejected(self):
        s = ProbeSession(O.make("circle", 0), budget=3, n_held_out=0)
        with pytest.raises(ProbeError):
            s.project([0, 0, 0, 0])
        with pytest.raises(ProbeError):
            s.slice([1, 0, 0], 0.0)


class TestScoring:
    def test_perfect_answer(self):
        s = ProbeSession(O.make("clifford_torus", 0), budget=4, n_held_out=3, seed=1)
        r = s.score({"betti": [1, 2, 1], "dimension": 2, "orientable": True, "held_out": s._held_truth})
        assert r["core_correct"] and r["betti_exact"] and r["held_out_accuracy"] == 1.0 and r["score"] == 1.0
        assert r["orientable_correct"] is True

    def test_wrong_answer(self):
        s = ProbeSession(O.make("klein_bottle", 0), budget=4, n_held_out=2, seed=1)
        r = s.score({"betti": [1, 0, 1], "dimension": 2, "orientable": True, "held_out": []})
        assert not r["core_correct"] and not r["betti_exact"] and r["betti_abs_error"] == 2
        assert r["orientable_correct"] is False and r["score"] == 0.0

    def test_torus_for_klein_gets_core_credit_only(self):
        """chi and b0 are what the probes decide; the orientation guess is reported separately."""
        s = ProbeSession(O.make("klein_bottle", 0), budget=4, n_held_out=2, seed=1)
        r = s.score({"betti": [1, 2, 1], "dimension": 2, "orientable": True, "held_out": []})
        assert r["core_correct"] and not r["betti_exact"] and r["score"] == 0.5
        assert r["orientability_decidable"] is False

    def test_curve_for_surface_is_not_core(self):
        s = ProbeSession(O.make("clifford_torus", 0), budget=4, n_held_out=0)
        assert not s.score({"betti": [1, 1, 0], "dimension": 1, "held_out": []})["core_correct"]

    def test_missing_answer_scores_zero(self):
        s = ProbeSession(O.make("sphere", 0), budget=4, n_held_out=2, seed=1)
        assert s.score({})["score"] == 0.0


class TestBaselines:
    def test_prior_spends_nothing(self):
        s = ProbeSession(O.make("sphere", 0), budget=8, n_held_out=2)
        PriorExplorer().run(s)
        assert s.remaining == 8

    def test_naive_spends_budget_and_answers(self):
        s = ProbeSession(O.make("circle", 0), budget=6, n_held_out=2)
        a = NaiveExplorer(0).run(s)
        assert s.remaining == 0 and len(a["held_out"]) == 2 and len(a["betti"]) == 3

    @pytest.mark.parametrize("name", ["projective_plane", "genus_2", "bouquet_3_circles"])
    def test_tiler_gets_the_core_right(self, name):
        s = ProbeSession(O.make(name, 0), budget=20, n_held_out=2)
        assert s.score(TilerExplorer(0).run(s))["core_correct"]


class _FakeClient:
    """Replays scripted assistant turns so the tool-use loop runs without the API."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.messages = SimpleNamespace(create=self._create)
        self.seen = []

    def _create(self, **kw):
        self.seen.append(kw["messages"][-1])
        return SimpleNamespace(content=self.turns.pop(0))


def _tool(i, name, inp):
    return {"type": "tool_use", "id": f"t{i}", "name": name, "input": inp}


class TestClaudeExplorerLoop:
    def test_probe_then_submit(self):
        s = ProbeSession(O.make("circle", 0), budget=5, n_held_out=1, seed=2)
        client = _FakeClient([
            [{"type": "text", "text": "Look at a shadow first."}, _tool(1, "project", {"direction": [0, 0, 0, 1]})],
            [_tool(2, "slice", {"normal": [1, 0, 0, 0], "offset": 0.0})],
            [_tool(3, "submit", {"betti": [1, 1, 0], "orientable": None, "held_out": [[2, 0]],
                                 "description": "A single closed curve."})],
        ])
        ex = ClaudeExplorer(client=client)
        ans = ex.run(s)
        assert ans["betti"] == [1, 1, 0]
        assert s.remaining == 3
        first_result = client.seen[1]["content"][0]
        assert first_result["type"] == "tool_result" and "betti" in json.loads(first_result["content"])

    def test_probe_errors_are_reported_not_raised(self):
        s = ProbeSession(O.make("circle", 0), budget=1, n_held_out=0)
        client = _FakeClient([
            [_tool(1, "project", {"direction": [1, 0, 0, 0]}), _tool(2, "project", {"direction": [0, 1, 0, 0]})],
            [_tool(3, "submit", {"betti": [1, 1, 0], "held_out": [], "description": "x"})],
        ])
        ClaudeExplorer(client=client).run(s)
        results = client.seen[1]["content"]
        assert results[1].get("is_error") and "budget" in results[1]["content"]

    def test_no_submit_gives_empty_answer(self):
        s = ProbeSession(O.make("circle", 0), budget=3, n_held_out=0)
        client = _FakeClient([[{"type": "text", "text": "thinking"}]] * 3)
        ans = ClaudeExplorer(client=client, max_turns=3).run(s)
        assert s.score(ans)["score"] == 0.0


class _FakeGemini:
    """Replays scripted Interactions API responses."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.calls = []
        self.interactions = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls.append(kw)
        steps, usage = self.turns.pop(0)
        return SimpleNamespace(id=f"i{len(self.calls)}", steps=steps,
                               usage=SimpleNamespace(total_input_tokens=usage[0], total_output_tokens=usage[1],
                                                     total_thought_tokens=usage[2]))


def _fc(i, name, args):
    return SimpleNamespace(type="function_call", id=f"c{i}", name=name, arguments=args)


class TestGeminiExplorerLoop:
    def test_probe_then_submit_and_cost(self):
        from nhcs.explorer.agents import GeminiExplorer, gemini_price
        s = ProbeSession(O.make("circle", 0), budget=5, n_held_out=1, seed=2)
        fake = _FakeGemini([
            ([SimpleNamespace(type="text", text="Start with a shadow."), _fc(1, "project", {"direction": [0, 0, 0, 1]})], (1000, 200, 800)),
            ([_fc(2, "submit", {"betti": [1, 1, 0], "held_out": [[2, 0]], "description": "One closed curve."})], (1500, 100, 400)),
        ])
        ex = GeminiExplorer(model="gemini-4-argon", client=fake)
        ans = ex.run(s)
        assert ans["betti"] == [1, 1, 0] and s.remaining == 4
        second = fake.calls[1]
        assert second["previous_interaction_id"] == "i1"
        fr = second["input"][0]
        assert fr["type"] == "function_result" and fr["call_id"] == "c1" and "betti" in json.loads(fr["result"][0]["text"])
        assert fake.calls[0]["generation_config"] == {"thinking_level": "medium"}
        assert ex.usage == {"input": 2500, "output": 300, "thought": 1200, "turns": 2}
        pin, pout = gemini_price("gemini-4-argon")
        assert ex.cost_usd() == pytest.approx((2500 * pin + 1500 * pout) / 1e6)
        assert ex.notes == ["Start with a shadow."]

    def test_price_switches_on_date(self):
        from nhcs.explorer.agents import gemini_price
        assert gemini_price("gemini-4-argon", "2026-11-30") == (2.00, 10.00)
        assert gemini_price("gemini-4-argon", "2026-12-01") == (4.00, 20.00)
        assert gemini_price("unknown-model") is None

    def test_tool_schemas_use_single_types(self):
        from nhcs.explorer.agents import GeminiExplorer
        tools = GeminiExplorer._tools()
        assert [t["name"] for t in tools] == ["slice", "project", "slab", "submit"]
        assert all(t["type"] == "function" for t in tools)
        assert tools[3]["parameters"]["properties"]["orientable"] == {"type": "boolean"}

    def test_slab_tool_call(self):
        from nhcs.explorer.agents import GeminiExplorer
        s = ProbeSession(O.make("sphere", 0), budget=3, n_held_out=0)
        fake = _FakeGemini([
            ([_fc(1, "slab", {"normal": [1, 0, 0, 0], "lo": -0.2, "hi": 0.2})], (10, 10, 0)),
            ([_fc(2, "submit", {"betti": [1, 0, 1], "dimension": 2, "held_out": [], "description": "sphere"})], (10, 10, 0)),
        ])
        GeminiExplorer(client=fake).run(s)
        res = json.loads(fake.calls[1]["input"][0]["result"][0]["text"])
        assert res["euler"] == 0 and res["probes_remaining"] == 2  # a band of the sphere: an annulus
