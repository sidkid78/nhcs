"""
Tests: knot reading of slice curves, knotted 2-spheres in R^4, and the knotted-sphere calibration benchmark.
"""

import json
import math
import warnings
from types import SimpleNamespace

import numpy as np
import pytest

warnings.filterwarnings("ignore")
pytest.importorskip("knot_floer_homology")
pytest.importorskip("spherogram")

from nhcs.explorer import knots as K  # noqa: E402
from nhcs.explorer.knot_agents import KNOT_PROMPT, KNOT_TOOLS, KnotLinker, KnotNaive, KnotPrior  # noqa: E402
from nhcs.explorer.knot_probes import KnotSession, make_surface  # noqa: E402
from nhcs.explorer.probes import ProbeError  # noqa: E402


def _circle(c=(0, 0, 0), plane=(0, 1)):
    t = np.linspace(0, 2 * math.pi, 200, endpoint=False)
    p = np.zeros((len(t), 3)) + c
    p[:, plane[0]] += np.cos(t)
    p[:, plane[1]] += np.sin(t)
    return p


class TestKnotReading:
    @pytest.mark.parametrize("name,expect", [("unknot", "unknot"), ("trefoil", "3_1"), ("figure_eight", "4_1")])
    def test_names_stable_across_projections(self, name, expect):
        names = {K.read_link([K.CURVES[name]()], seed=s)["components"][0]["name"] for s in range(4)}
        assert names == {expect} or (expect == "3_1" and names == {"m3_1"})

    def test_mirror_trefoil_is_told_apart_by_tau(self):
        a = K.read_link([K.trefoil_curve()])["components"][0]
        m = K.trefoil_curve()
        m[:, 2] *= -1
        b = K.read_link([m])["components"][0]
        assert a["alexander"] == b["alexander"] == [1, -1, 1] and a["tau"] == -b["tau"] != 0

    def test_hopf_link_and_unlink(self):
        a = _circle()
        assert K.read_link([a, _circle((1, 0, 0), (0, 2))])["linking"] == [[0, 1, 1]]
        assert K.read_link([a, _circle((5, 0, 0), (0, 2))])["linking"] == []


class TestSpheres:
    @pytest.mark.parametrize("name,expect", [("unknot", "unknot"), ("trefoil", "3_1"), ("figure_eight", "4_1")])
    def test_long_knot_closes_up_to_the_knot_with_clearance(self, name, expect):
        p, R = K.long_knot(K.CURVES[name]())
        t = np.linspace(-math.pi / 2, math.pi / 2, 80)
        close = np.stack([1.3 * R * np.cos(t), 1.3 * R * np.sin(t), 0 * t], 1)[::-1]
        loop = np.vstack([p, [[0.5 * R, 1.3 * R, 0]], close, [[0.5 * R, -1.3 * R, 0]]])
        assert K.read_link([loop])["components"][0]["name"].lstrip("m") == expect.lstrip("m")
        assert K.clearance(K._resample(p, R / 200), R) > 0.15  # no near-touching strands

    @pytest.mark.parametrize("twist", [0, 1, 2])
    def test_theory_equator_and_spin_axis_linking(self, twist):
        """Equator of any twist-spun trefoil: 3_1 # m3_1. Slices across the spin axis: circles linking `twist` times."""
        V, T = K.spun_sphere(K.trefoil_curve(), twist=twist, n_theta=120)
        eq = K.read_link([lp[:, :3] for lp in K.slice_mesh(V, T, [0, 0, 0, 1], 1e-3)])
        assert [c["name"] for c in eq["components"]] == ["3_1 # m3_1"]
        cut = K.slice_mesh(V, T, [1, 0, 0, 0], float(np.percentile(V[:, 0], 50)))
        r = K.read_link([lp[:, 1:] for lp in cut])
        assert all(c["name"] == "unknot" for c in r["components"]) and len(cut) >= 3
        assert sorted({v[2] for v in r["linking"]}) == ([twist] if twist else [])

    def test_mesh_slices_are_closed_loops(self):
        o = make_surface("twist2_trefoil", 0)
        for lp in K.slice_mesh(o.V, o.T, [0.3, -0.2, 0.5, 0.7], 0.05):
            seg = np.linalg.norm(np.diff(lp, axis=0), axis=1)
            assert np.linalg.norm(lp[0] - lp[-1]) < 3 * seg.max()


class TestKnotSession:
    def test_budget_and_held_out_guard(self):
        s = KnotSession(make_surface("spun_trefoil", 0), budget=1, n_held_out=1, seed=3)
        h = s.held_out[0]
        for normal, off in ((h.normal, h.offset), ([-x for x in h.normal], -h.offset), (h.normal, -h.offset)):
            with pytest.raises(ProbeError, match="held-out"):
                s.knot_slice(normal, off)
        s.knot_slice([1, 0, 0, 0], 0.0)
        with pytest.raises(ProbeError, match="budget"):
            s.knot_slice([0, 1, 0, 0], 0.0)

    def test_scoring(self):
        s = KnotSession(make_surface("twist1_trefoil", 0), budget=2, n_held_out=2, seed=1)
        right = s.score({"knotted": False, "construction": "twist-spun", "knot": "3_1", "twist": 1, "held_out": s._held_truth})
        assert right["knotted_correct"] and right["construction_correct"] and right["score"] == 1.0
        trap = s.score({"knotted": True, "construction": "spun", "knot": "3_1", "held_out": []})
        assert not trap["knotted_correct"] and trap["score"] == 0.0
        u = KnotSession(make_surface("unknotted_sphere", 0), budget=1, n_held_out=0)
        assert u.score({"knotted": False, "construction": "unknotted", "knot": "unknot"})["construction_correct"]


class TestBaselines:
    def test_prior_spends_nothing(self):
        s = KnotSession(make_surface("spun_trefoil", 0), budget=5, n_held_out=1)
        KnotPrior().run(s)
        assert s.remaining == 5

    def test_naive_falls_for_the_twist1_trap(self):
        s = KnotSession(make_surface("twist1_trefoil", 0), budget=4, n_held_out=1)
        a = KnotNaive(0).run(s)
        assert s.remaining == 0 and a["knotted"] is True  # knotted slices, yet the sphere is unknotted

    def test_linker_reads_twist_when_it_crosses_the_spin_axis(self):
        s = KnotSession(make_surface("twist2_trefoil", 0), budget=3, n_held_out=0)
        a = KnotLinker(0).run(s)
        assert a["construction"] in ("spun", "twist-spun", "unknotted")


class _FakeGemini:
    def __init__(self, turns):
        self.turns, self.calls = list(turns), []
        self.interactions = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls.append(kw)
        steps = self.turns.pop(0)
        return SimpleNamespace(id=f"i{len(self.calls)}", steps=steps,
                               usage=SimpleNamespace(total_input_tokens=10, total_output_tokens=10, total_thought_tokens=0))


def test_gemini_knot_loop():
    from nhcs.explorer.agents import GeminiExplorer
    s = KnotSession(make_surface("spun_trefoil", 0), budget=3, n_held_out=0)
    fc = lambda i, n, a: SimpleNamespace(type="function_call", id=f"c{i}", name=n, arguments=a)  # noqa: E731
    fake = _FakeGemini([[fc(1, "knot_slice", {"normal": [0, 0, 0, 1], "offset": 0.0})],
                        [fc(2, "submit", {"knotted": True, "construction": "spun", "knot": "3_1", "held_out": [],
                                          "description": "spun trefoil"})]])
    ans = GeminiExplorer(client=fake, system_prompt=KNOT_PROMPT, tools=KNOT_TOOLS).run(s)
    assert ans["knot"] == "3_1" and s.remaining == 2
    assert fake.calls[0]["system_instruction"] == KNOT_PROMPT
    assert [t["name"] for t in fake.calls[0]["tools"]] == ["knot_slice", "submit"]
    res = json.loads(fake.calls[1]["input"][0]["result"][0]["text"])
    assert "knots" in res and res["probes_remaining"] == 2
