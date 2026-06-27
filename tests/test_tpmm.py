"""
Tests: TPMM frequency/wavelength mapping.

Values cross-referenced against mapping_logic.json data table.
Tolerance: ±0.5 Hz / ±1.0 nm.
"""

import pytest
from nhcs.layer2_tmft.topology_to_field import betti_to_physical

TPMM_DATA_TABLE = [
    # (betti, D, expected_freq_hz, expected_wl_nm)
    ([1, 0, 0], 0, 1.0,   420.0),    # 0-simplex (point)
    ([1, 0, 0], 1, 1.0,   470.0),    # 1-simplex (line)
    ([1, 1, 0], 1, 10.83, 470.0),    # circle S1
    ([1, 0, 0], 2, 1.0,   505.71),   # filled triangle
    ([1, 0, 1], 2, 17.86, 505.71),   # sphere S2
    ([1, 2, 1], 2, 27.22, 505.71),   # torus T2
    ([2, 2, 0], 1, 17.86, 505.71),   # two disjoint circles
]

FREQ_TOLERANCE = 0.5
WL_TOLERANCE = 1.0


@pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
def test_tpmm_frequency(betti, D, expected_f, expected_wl):
    f, wl = betti_to_physical(betti, D)
    assert abs(f - expected_f) <= FREQ_TOLERANCE, \
        f"betti={betti} D={D}: got freq={f:.3f}, expected {expected_f}"


@pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
def test_tpmm_wavelength(betti, D, expected_f, expected_wl):
    f, wl = betti_to_physical(betti, D)
    assert abs(wl - expected_wl) <= WL_TOLERANCE, \
        f"betti={betti} D={D}: got wl={wl:.3f}, expected {expected_wl}"


def test_tpmm_point_min_freq():
    """A point (all Betti=0 except β0=1, D=0) → minimum frequency."""
    f, _ = betti_to_physical([1, 0, 0], 0)
    assert f == pytest.approx(1.0, abs=0.01)


def test_tpmm_high_complexity_approaches_max():
    """Very high complexity → frequency asymptotically approaches 60 Hz."""
    f, _ = betti_to_physical([1, 100, 50], 10)
    assert f > 55.0
