## 🧪 Pytest Execution Report

- **Status:** ❌ Failed
- **Platform:** win32 | **Python:** 3.12.6 | **Pytest:** 9.0.3
- **Duration:** 163.33s (0:02:43)


### 📊 Summary

- **Metric**            	**Count**
- **Total Tests**        	35
- **✅ Passed**	        	23
- **❌3**	                	
- **❌ Failed**	        	12
- **⚠️ Warnings**	        	9


## ❌ Failure Details & Insights

### 1. TPMM Frequency Mapping 

`(tests/test_tpmm.py)`

All failing tests in this module appear to be caused by a system guardrail overriding the expected theoretical mathematical mappings.

- **The Issue:** The tests assert exact topological-physical invariant frequencies (e.g., 1.0 Hz, 10.83 Hz, >55.0 Hz). However, the actual logic is clamping the output down to the 15.0 - 40.0 Hz range.
- **Evidence:** The logs clearly state warnings like: TPMM freq 1.00 Hz outside RSR [15.0-40.0] ... Clamping.
- **Context Match:** This clamping matches the "Resonant Stability Regime" limits explicitly defined in your RetargetRequest schema in schemas.py. You may need to bypass or mock the RSR guardrails during pure mathematical invariant tests.
- **Test Case / Topology:**	
  - **[1, 0, 0], D=0**	1.0 Hz	15.0 Hz
  - **[1, 0, 0], D=1**	1.0 Hz	15.0 Hz
  - **[1, 1, 0], D=1**	10.83 Hz	15.75 Hz
  - **[1, 0, 0], D=2**	1.0 Hz	15.0 Hz
  - **[1, 0, 1], D=2**	17.86 Hz	24.6 Hz
  - **[1, 2, 1], D=2**	27.22 Hz	34.714 Hz
  - **[2, 2, 0], D=1**	17.86 Hz	24.6 Hz
  - **Point Min Freq**	~1.0 Hz	15.0 Hz
  - **High Complexity**	> 55.0 Hz	40.0 Hz

### 2. End-to-End Pipeline 

`(tests/test_e2e_smoke.py)`

- **The Issue:** The full pipeline runs (test_e2e_smoke_runs_without_exception, test_e2e_sdr_non_negative) are failing with assert 0 >= 1 because the engine returns zero successful integration feedbacks.
- **Evidence:** Pipeline components are aggressively rejecting the generated relational topologies at various stages:
- 1. **AIAN Rejections:** All candidates rejected by AIAN. According to your aian_design.md specifications, the Anti-Imitation Discriminator is likely flagging these concepts due to high Anthropomorphic Penalties.
- 2. **Airlock Rejections:** Airlock: high charge error 100.0% — topology may be degraded. This implies the Layer 3 physical realization is entirely failing to reconstruct the expected Hopf charge.

### 3. Topological Invariants 

`(tests/test_invariants.py)`

- **The Issue:** TestBettiNumbers.test_single_point fails with assert 0 == 1.
- **Evidence:** The geometry logic for computing Betti numbers is failing to identify the single connected component for a lone origin coordinate [[0.0, 0.0]]. It returns betti[0] == 0 instead of the mathematically correct 1.

#### ⚠️ Warnings

HuggingFace Hub: Warning: You are sending unauthenticated requests... (Consider setting a HF_TOKEN environment variable to ensure model downloads don't hit rate limits).
Dateutil Deprecation: datetime.datetime.utcfromtimestamp() is deprecated in Python 3.12. To future-proof the pipeline, standard libraries or specific integrations (like tqdm and dateutil) are indicating a move toward datetime.datetime.fromtimestamp(timestamp, datetime.UTC).









====================================================================== test session starts =======================================================================
platform win32 -- Python 3.12.6, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\sidki\source\repos\alien
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.9.0, dash-4.1.0, asyncio-1.3.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 35 items

tests\test_consensus.py ......                                                                                                                              [ 17%]
tests\test_e2e_smoke.py FF..                                                                                                                                [ 28%]
tests\test_invariants.py F.....                                                                                                                             [ 45%]
tests\test_pid_stability.py ...                                                                                                                             [ 54%]
tests\test_tpmm.py FFFFFFF.......FF                                                                                                                         [100%]

============================================================================ FAILURES ============================================================================ 
_____________________________________________________________ test_e2e_smoke_runs_without_exception ______________________________________________________________ 

    @pytest.mark.asyncio
    async def test_e2e_smoke_runs_without_exception():
        """Full pipeline: RSE → AIAN → ICVP → TMFT → CRIM should complete."""
        reset_bus()
        runner = EndToEndRunner(
            n_validators=3,
            n_crim_steps=10,
            ledger_path=":memory:",
            rng_seed=7,
        )
        feedbacks = await runner.run(n_concepts=1)
>       assert len(feedbacks) >= 1
E       assert 0 >= 1
E        +  where 0 = len([])

tests\test_e2e_smoke.py:23: AssertionError
---------------------------------------------------------------------- Captured stderr call ---------------------------------------------------------------------- 
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|██████████| 103/103 [00:00<00:00, 2733.05it/s]
Loading weights: 100%|██████████| 103/103 [00:00<00:00, 5671.70it/s]
----------------------------------------------------------------------- Captured log call ------------------------------------------------------------------------ 
WARNING  huggingface_hub.utils._http:_http.py:904 Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
WARNING  nhcs.layer3_crim.airlock:airlock.py:80 Airlock: high charge error 100.0% — topology may be degraded.
WARNING  nhcs.orchestrator.runner:runner.py:227 Airlock rejected realization for concept fdd2306f.
WARNING  nhcs.orchestrator.runner:runner.py:100 All candidates rejected by AIAN.
WARNING  nhcs.orchestrator.runner:runner.py:100 All candidates rejected by AIAN.
WARNING  nhcs.layer3_crim.airlock:airlock.py:80 Airlock: high charge error 100.0% — topology may be degraded.
WARNING  nhcs.orchestrator.runner:runner.py:227 Airlock rejected realization for concept dc9c13da.
WARNING  nhcs.layer3_crim.airlock:airlock.py:80 Airlock: high charge error 100.0% — topology may be degraded.
WARNING  nhcs.orchestrator.runner:runner.py:227 Airlock rejected realization for concept 7f531231.
___________________________________________________________________ test_e2e_sdr_non_negative ____________________________________________________________________ 

    @pytest.mark.asyncio
    async def test_e2e_sdr_non_negative():
        reset_bus()
        runner = EndToEndRunner(n_validators=3, n_crim_steps=10, ledger_path=":memory:", rng_seed=13)
        feedbacks = await runner.run(n_concepts=1)
>       assert len(feedbacks) >= 1
E       assert 0 >= 1
E        +  where 0 = len([])

tests\test_e2e_smoke.py:31: AssertionError
---------------------------------------------------------------------- Captured stderr call ---------------------------------------------------------------------- 
Loading weights: 100%|██████████| 103/103 [00:00<00:00, 5596.17it/s]
Loading weights: 100%|██████████| 103/103 [00:00<00:00, 5552.37it/s]
----------------------------------------------------------------------- Captured log call ------------------------------------------------------------------------ 
WARNING  nhcs.layer3_crim.airlock:airlock.py:80 Airlock: high charge error 100.0% — topology may be degraded.
WARNING  nhcs.orchestrator.runner:runner.py:227 Airlock rejected realization for concept 77a45b05.
WARNING  nhcs.layer3_crim.airlock:airlock.py:80 Airlock: high charge error 100.0% — topology may be degraded.
WARNING  nhcs.orchestrator.runner:runner.py:227 Airlock rejected realization for concept cfe57486.
WARNING  nhcs.layer3_crim.airlock:airlock.py:80 Airlock: high charge error 100.0% — topology may be degraded.
WARNING  nhcs.orchestrator.runner:runner.py:227 Airlock rejected realization for concept f92ff0fc.
WARNING  nhcs.layer2_tmft.topology_to_field:topology_to_field.py:69 TPMM freq 42.30 Hz outside RSR [15.0-40.0] for I_f=7 (betti=[5, 7, 0]). Clamping.
WARNING  nhcs.layer3_crim.airlock:airlock.py:80 Airlock: high charge error 100.0% — topology may be degraded.
WARNING  nhcs.orchestrator.runner:runner.py:227 Airlock rejected realization for concept 84832be6.
WARNING  nhcs.layer3_crim.airlock:airlock.py:80 Airlock: high charge error 100.0% — topology may be degraded.
WARNING  nhcs.orchestrator.runner:runner.py:227 Airlock rejected realization for concept 6c5fcd8c.
_______________________________________________________________ TestBettiNumbers.test_single_point _______________________________________________________________ 

self = <tests.test_invariants.TestBettiNumbers object at 0x0000020967476840>

    def test_single_point(self):
        pts = np.array([[0.0, 0.0]])
        profile = compute_betti(pts, max_dimension=2, max_edge_length=5.0)
>       assert profile.betti[0] == 1   # 1 connected component
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       assert 0 == 1

tests\test_invariants.py:37: AssertionError
____________________________________________________________ test_tpmm_frequency[betti0-0-1.0-420.0] _____________________________________________________________ 

betti = [1, 0, 0], D = 0, expected_f = 1.0, expected_wl = 420.0

    @pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
    def test_tpmm_frequency(betti, D, expected_f, expected_wl):
        f, wl = betti_to_physical(betti, D)
>       assert abs(f - expected_f) <= FREQ_TOLERANCE, \
            f"betti={betti} D={D}: got freq={f:.3f}, expected {expected_f}"
E       AssertionError: betti=[1, 0, 0] D=0: got freq=15.000, expected 1.0
E       assert 14.0 <= 0.5
E        +  where 14.0 = abs((15.0 - 1.0))

tests\test_tpmm.py:29: AssertionError
----------------------------------------------------------------------- Captured log call ------------------------------------------------------------------------ 
WARNING  nhcs.layer2_tmft.topology_to_field:topology_to_field.py:69 TPMM freq 1.00 Hz outside RSR [15.0-40.0] for I_f=0 (betti=[1, 0, 0]). Clamping.
____________________________________________________________ test_tpmm_frequency[betti1-1-1.0-470.0] _____________________________________________________________ 

betti = [1, 0, 0], D = 1, expected_f = 1.0, expected_wl = 470.0

    @pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
    def test_tpmm_frequency(betti, D, expected_f, expected_wl):
        f, wl = betti_to_physical(betti, D)
>       assert abs(f - expected_f) <= FREQ_TOLERANCE, \
            f"betti={betti} D={D}: got freq={f:.3f}, expected {expected_f}"
E       AssertionError: betti=[1, 0, 0] D=1: got freq=15.000, expected 1.0
E       assert 14.0 <= 0.5
E        +  where 14.0 = abs((15.0 - 1.0))

tests\test_tpmm.py:29: AssertionError
----------------------------------------------------------------------- Captured log call ------------------------------------------------------------------------ 
WARNING  nhcs.layer2_tmft.topology_to_field:topology_to_field.py:69 TPMM freq 1.00 Hz outside RSR [15.0-40.0] for I_f=0 (betti=[1, 0, 0]). Clamping.
___________________________________________________________ test_tpmm_frequency[betti2-1-10.83-470.0] ____________________________________________________________ 

betti = [1, 1, 0], D = 1, expected_f = 10.83, expected_wl = 470.0

    @pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
    def test_tpmm_frequency(betti, D, expected_f, expected_wl):
        f, wl = betti_to_physical(betti, D)
>       assert abs(f - expected_f) <= FREQ_TOLERANCE, \
            f"betti={betti} D={D}: got freq={f:.3f}, expected {expected_f}"
E       AssertionError: betti=[1, 1, 0] D=1: got freq=15.750, expected 10.83
E       assert 4.92 <= 0.5
E        +  where 4.92 = abs((15.75 - 10.83))

tests\test_tpmm.py:29: AssertionError
____________________________________________________________ test_tpmm_frequency[betti3-2-1.0-505.71] ____________________________________________________________ 

betti = [1, 0, 0], D = 2, expected_f = 1.0, expected_wl = 505.71

    @pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
    def test_tpmm_frequency(betti, D, expected_f, expected_wl):
        f, wl = betti_to_physical(betti, D)
>       assert abs(f - expected_f) <= FREQ_TOLERANCE, \
            f"betti={betti} D={D}: got freq={f:.3f}, expected {expected_f}"
E       AssertionError: betti=[1, 0, 0] D=2: got freq=15.000, expected 1.0
E       assert 14.0 <= 0.5
E        +  where 14.0 = abs((15.0 - 1.0))

tests\test_tpmm.py:29: AssertionError
----------------------------------------------------------------------- Captured log call ------------------------------------------------------------------------ 
WARNING  nhcs.layer2_tmft.topology_to_field:topology_to_field.py:69 TPMM freq 1.00 Hz outside RSR [15.0-40.0] for I_f=0 (betti=[1, 0, 0]). Clamping.
___________________________________________________________ test_tpmm_frequency[betti4-2-17.86-505.71] ___________________________________________________________ 

betti = [1, 0, 1], D = 2, expected_f = 17.86, expected_wl = 505.71

    @pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
    def test_tpmm_frequency(betti, D, expected_f, expected_wl):
        f, wl = betti_to_physical(betti, D)
>       assert abs(f - expected_f) <= FREQ_TOLERANCE, \
            f"betti={betti} D={D}: got freq={f:.3f}, expected {expected_f}"
E       AssertionError: betti=[1, 0, 1] D=2: got freq=24.600, expected 17.86
E       assert 6.740000000000002 <= 0.5
E        +  where 6.740000000000002 = abs((24.6 - 17.86))

tests\test_tpmm.py:29: AssertionError
___________________________________________________________ test_tpmm_frequency[betti5-2-27.22-505.71] ___________________________________________________________ 

betti = [1, 2, 1], D = 2, expected_f = 27.22, expected_wl = 505.71

    @pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
    def test_tpmm_frequency(betti, D, expected_f, expected_wl):
        f, wl = betti_to_physical(betti, D)
>       assert abs(f - expected_f) <= FREQ_TOLERANCE, \
            f"betti={betti} D={D}: got freq={f:.3f}, expected {expected_f}"
E       AssertionError: betti=[1, 2, 1] D=2: got freq=34.714, expected 27.22
E       assert 7.494285714285716 <= 0.5
E        +  where 7.494285714285716 = abs((34.714285714285715 - 27.22))

tests\test_tpmm.py:29: AssertionError
___________________________________________________________ test_tpmm_frequency[betti6-1-17.86-505.71] ___________________________________________________________ 

betti = [2, 2, 0], D = 1, expected_f = 17.86, expected_wl = 505.71

    @pytest.mark.parametrize("betti,D,expected_f,expected_wl", TPMM_DATA_TABLE)
    def test_tpmm_frequency(betti, D, expected_f, expected_wl):
        f, wl = betti_to_physical(betti, D)
>       assert abs(f - expected_f) <= FREQ_TOLERANCE, \
            f"betti={betti} D={D}: got freq={f:.3f}, expected {expected_f}"
E       AssertionError: betti=[2, 2, 0] D=1: got freq=24.600, expected 17.86
E       assert 6.740000000000002 <= 0.5
E        +  where 6.740000000000002 = abs((24.6 - 17.86))

tests\test_tpmm.py:29: AssertionError
____________________________________________________________________ test_tpmm_point_min_freq ____________________________________________________________________ 

    def test_tpmm_point_min_freq():
        """A point (all Betti=0 except β0=1, D=0) → minimum frequency."""
        f, _ = betti_to_physical([1, 0, 0], 0)
>       assert f == pytest.approx(1.0, abs=0.01)
E       assert 15.0 == 1.0 ± 0.01
E
E         comparison failed
E         Obtained: 15.0
E         Expected: 1.0 ± 0.01

tests\test_tpmm.py:43: AssertionError
----------------------------------------------------------------------- Captured log call ------------------------------------------------------------------------ 
WARNING  nhcs.layer2_tmft.topology_to_field:topology_to_field.py:69 TPMM freq 1.00 Hz outside RSR [15.0-40.0] for I_f=0 (betti=[1, 0, 0]). Clamping.
____________________________________________________________ test_tpmm_high_complexity_approaches_max ____________________________________________________________ 

    def test_tpmm_high_complexity_approaches_max():
        """Very high complexity → frequency asymptotically approaches 60 Hz."""
        f, _ = betti_to_physical([1, 100, 50], 10)
>       assert f > 55.0
E       assert 40.0 > 55.0

tests\test_tpmm.py:49: AssertionError
----------------------------------------------------------------------- Captured log call ------------------------------------------------------------------------ 
WARNING  nhcs.layer2_tmft.topology_to_field:topology_to_field.py:69 TPMM freq 59.13 Hz outside RSR [15.0-40.0] for I_f=200 (betti=[1, 100, 50]). Clamping.
======================================================================== warnings summary ======================================================================== 
..\..\..\AppData\Local\Programs\Python\Python312\Lib\site-packages\dateutil\tz\tz.py:37
  C:\Users\sidki\AppData\Local\Programs\Python\Python312\Lib\site-packages\dateutil\tz\tz.py:37: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC).
    EPOCH = datetime.datetime.utcfromtimestamp(0)

tests/test_e2e_smoke.py::test_e2e_smoke_runs_without_exception
tests/test_e2e_smoke.py::test_e2e_smoke_runs_without_exception
tests/test_e2e_smoke.py::test_e2e_sdr_non_negative
tests/test_e2e_smoke.py::test_e2e_sdr_non_negative
tests/test_e2e_smoke.py::test_e2e_ledger_grows
tests/test_e2e_smoke.py::test_e2e_ledger_grows
tests/test_e2e_smoke.py::test_e2e_cli_bounded
tests/test_e2e_smoke.py::test_e2e_cli_bounded
  C:\Users\sidki\AppData\Local\Programs\Python\Python312\Lib\site-packages\tqdm\std.py:580: DeprecationWarning: datetime.datetime.utcfromtimestamp() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.fromtimestamp(timestamp, datetime.UTC). 
    if rate and total else datetime.utcfromtimestamp(0))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
==================================================================== short test summary info ===================================================================== 
FAILED tests/test_e2e_smoke.py::test_e2e_smoke_runs_without_exception - assert 0 >= 1
FAILED tests/test_e2e_smoke.py::test_e2e_sdr_non_negative - assert 0 >= 1
FAILED tests/test_invariants.py::TestBettiNumbers::test_single_point - assert 0 == 1
FAILED tests/test_tpmm.py::test_tpmm_frequency[betti0-0-1.0-420.0] - AssertionError: betti=[1, 0, 0] D=0: got freq=15.000, expected 1.0
FAILED tests/test_tpmm.py::test_tpmm_frequency[betti1-1-1.0-470.0] - AssertionError: betti=[1, 0, 0] D=1: got freq=15.000, expected 1.0
FAILED tests/test_tpmm.py::test_tpmm_frequency[betti2-1-10.83-470.0] - AssertionError: betti=[1, 1, 0] D=1: got freq=15.750, expected 10.83
FAILED tests/test_tpmm.py::test_tpmm_frequency[betti3-2-1.0-505.71] - AssertionError: betti=[1, 0, 0] D=2: got freq=15.000, expected 1.0
FAILED tests/test_tpmm.py::test_tpmm_frequency[betti4-2-17.86-505.71] - AssertionError: betti=[1, 0, 1] D=2: got freq=24.600, expected 17.86
FAILED tests/test_tpmm.py::test_tpmm_frequency[betti5-2-27.22-505.71] - AssertionError: betti=[1, 2, 1] D=2: got freq=34.714, expected 27.22
FAILED tests/test_tpmm.py::test_tpmm_frequency[betti6-1-17.86-505.71] - AssertionError: betti=[2, 2, 0] D=1: got freq=24.600, expected 17.86
FAILED tests/test_tpmm.py::test_tpmm_point_min_freq - assert 15.0 == 1.0 ± 0.01
FAILED tests/test_tpmm.py::test_tpmm_high_complexity_approaches_max - assert 40.0 > 55.0
===================================================== 12 failed, 23 passed, 9 warnings in 163.33s (0:02:43) ====================================================== 