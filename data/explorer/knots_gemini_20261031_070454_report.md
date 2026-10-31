# Knotted-sphere run: gemini, 2026-10-31 07:04

Source: `data/explorer/knots_gemini_20261031_070454.jsonl`  
Model `gemini-4-argon`, thinking `medium`, probe budget 20, seed(s) [0]  
Estimated spend $2.46, wall time 2056s  
Score = 0.5 × knotted right + 0.25 × construction right + 0.25 × held-out accuracy.

## Summary

| object | seed | knotted (true / answer) | built (true / answer) | built right | max linking seen | held-out | score | cost |
|---|---|---|---|---|---|---|---|---|
| unknotted_sphere | 0 | False / False | spun unknot / unknotted unknot | yes | 0 | 0.67 | 0.92 | $0.149 |
| spun_trefoil | 0 | True / True | spun 3_1 / spun 3_1 | yes | 0 | 0.33 | 0.83 | $0.595 |
| spun_figure_eight | 0 | True / True | spun 4_1 / spun 4_1 | yes | 0 | 0.33 | 0.83 | $0.379 |
| twist1_trefoil | 0 | False / True | twist-spun 3_1 twist 1 / spun 3_1 | no | 0 | 0.00 | 0.00 | $0.635 |
| twist1_figure_eight | 0 | False / False | twist-spun 4_1 twist 1 / unknotted 4_1 twist 1 | yes | 1 | 0.33 | 0.83 | $0.041 |
| twist2_trefoil | 0 | True / True | twist-spun 3_1 twist 2 / spun 3_1 | no | 2 | 0.67 | 0.67 | $0.041 |
| twist3_trefoil | 0 | True / True | twist-spun 3_1 twist 3 / twist-spun 3_1 twist 3 | yes | 3 | 0.00 | 0.75 | $0.617 |

**Mean score 0.69**, knotted right 6/7, construction right 5/7, held-out 0.33

## Comparison with baselines (same objects)

Baseline runs: `knots_prior_20261031_051702.jsonl`, `knots_naive_20261031_051702.jsonl`, `knots_linker_20261031_051702.jsonl`

| agent | object | trials | knotted right | built right | held-out | mean score |
|---|---|---|---|---|---|---|
| prior | all | 21 | 12/21 | 3/21 | 0.27 | 0.39 |
| naive | all | 21 | 15/21 | 9/21 | 0.40 | 0.56 |
| linker | all | 21 | 16/21 | 10/21 | 0.40 | 0.60 |
| **gemini** | all | 7 | 6/7 | 5/7 | 0.33 | 0.69 |
| prior | unknotted_sphere | 3 | 0/3 | 0/3 | 0.00 | 0.00 |
| naive | unknotted_sphere | 3 | 3/3 | 3/3 | 0.33 | 0.83 |
| linker | unknotted_sphere | 3 | 3/3 | 3/3 | 0.33 | 0.83 |
| **gemini** | unknotted_sphere | 1 | 1/1 | 1/1 | 0.67 | 0.92 |
| prior | spun_trefoil | 3 | 3/3 | 3/3 | 0.44 | 0.86 |
| naive | spun_trefoil | 3 | 3/3 | 3/3 | 0.22 | 0.81 |
| linker | spun_trefoil | 3 | 3/3 | 3/3 | 0.22 | 0.81 |
| **gemini** | spun_trefoil | 1 | 1/1 | 1/1 | 0.33 | 0.83 |
| prior | spun_figure_eight | 3 | 3/3 | 0/3 | 0.00 | 0.50 |
| naive | spun_figure_eight | 3 | 3/3 | 3/3 | 0.44 | 0.86 |
| linker | spun_figure_eight | 3 | 3/3 | 3/3 | 0.44 | 0.86 |
| **gemini** | spun_figure_eight | 1 | 1/1 | 1/1 | 0.33 | 0.83 |
| prior | twist1_trefoil | 3 | 0/3 | 0/3 | 0.44 | 0.11 |
| naive | twist1_trefoil | 3 | 0/3 | 0/3 | 0.22 | 0.06 |
| linker | twist1_trefoil | 3 | 0/3 | 0/3 | 0.22 | 0.06 |
| **gemini** | twist1_trefoil | 1 | 0/1 | 0/1 | 0.00 | 0.00 |
| prior | twist1_figure_eight | 3 | 0/3 | 0/3 | 0.00 | 0.00 |
| naive | twist1_figure_eight | 3 | 0/3 | 0/3 | 0.56 | 0.14 |
| linker | twist1_figure_eight | 3 | 1/3 | 1/3 | 0.56 | 0.39 |
| **gemini** | twist1_figure_eight | 1 | 1/1 | 1/1 | 0.33 | 0.83 |
| prior | twist2_trefoil | 3 | 3/3 | 0/3 | 0.78 | 0.69 |
| naive | twist2_trefoil | 3 | 3/3 | 0/3 | 0.78 | 0.69 |
| linker | twist2_trefoil | 3 | 3/3 | 0/3 | 0.78 | 0.69 |
| **gemini** | twist2_trefoil | 1 | 1/1 | 0/1 | 0.67 | 0.67 |
| prior | twist3_trefoil | 3 | 3/3 | 0/3 | 0.22 | 0.56 |
| naive | twist3_trefoil | 3 | 3/3 | 0/3 | 0.22 | 0.56 |
| linker | twist3_trefoil | 3 | 3/3 | 0/3 | 0.22 | 0.56 |
| **gemini** | twist3_trefoil | 1 | 1/1 | 1/1 | 0.00 | 0.75 |

gemini ran 1 trial per object; treat differences from the baselines as indicative only.

## Flags

- **unknotted_sphere** (seed 0): nothing unusual
- **spun_trefoil** (seed 0): nothing unusual
- **spun_figure_eight** (seed 0): nothing unusual
- **twist1_trefoil** (seed 0): fell for the 1-twist trap: called a knotted-looking but unknotted sphere knotted; never found the spin axis: no slice with linked circles (truth: twist 1)
- **twist1_figure_eight** (seed 0): found the spin axis: circles linking 1 times
- **twist2_trefoil** (seed 0): found the spin axis: circles linking 2 times; saw circles linking 2 times but answered 'spun 3_1'
- **twist3_trefoil** (seed 0): found the spin axis: circles linking 3 times

## unknotted_sphere (seed 0)

20/20 probes, 6 turns, 9079 thinking tokens, 143.6s

**Explorer's explanation:**

> We probed 20 hyperplane cross-sections across a full basis of normal directions in R^4 and across multiple offsets (0, 0.05, 0.1, 0.15, 0.2, 0.4, 0.5). Every single cross-section consists exclusively of unlinked unknots (from 1 to 4 components depending on the angle relative to the symmetry axis and the offset). Specifically, normals orthogonal to the axis direction u ≈ [-0.12, -0.18, 0.63, 0.74] (including the spinning plane directions) yield a single unknot at offset 0 and small offsets, showing that the underlying knot K is trivial (the unknot) and the embedded 2-sphere is unknotted in R^4.

**Held-out slices:**

| # | normal | offset | truth | answer |  |
|---|---|---|---|---|---|
| H1 | [-0.1211, -0.183, 0.633, 0.7424] | 0.0061 | unknot, unknot, unknot | unknot, unknot, unknot | ✓ |
| H2 | [-0.8128, 0.1294, 0.0272, -0.5674] | 0.4935 | unknot | unknot | ✓ |
| H3 | [0.4134, -0.5852, 0.3669, -0.5933] | 0.1438 | unknot, unknot | unknot | ✗ |

**Probes:**

| # | normal | offset | components | knots | linking | held-out |
|---|---|---|---|---|---|---|
| 1 | [1.0, 0.0, 0.0, 0.0] | 0.0 | 1 | unknot |  |  |
| 2 | [0.0, 1.0, 0.0, 0.0] | 0.0 | 1 | unknot |  |  |
| 3 | [0.0, 0.0, 1.0, 0.0] | 0.0 | 3 | 3×unknot |  |  |
| 4 | [0.0, 0.0, 0.0, 1.0] | 0.0 | 3 | 3×unknot |  |  |
| 5 | [0.7071, 0.7071, 0.0, 0.0] | 0.0 | 1 | unknot |  |  |
| 6 | [0.7071, -0.7071, 0.0, 0.0] | 0.0 | 1 | unknot |  |  |
| 7 | [0.0, 0.0, 0.7071, 0.7071] | 0.0 | 3 | 3×unknot |  |  |
| 8 | [0.0, 0.0, 0.7071, -0.7071] | 0.0 | 1 | unknot |  |  |
| 9 | [0.0, 0.0, 1.0, 0.0] | 0.2 | 2 | 2×unknot |  |  |
| 10 | [0.0, 0.0, 1.0, 0.0] | 0.4 | 2 | 2×unknot |  |  |
| 11 | [1.0, 0.0, 0.0, 0.0] | 0.2 | 1 | unknot |  |  |
| 12 | [1.0, 0.0, 0.0, 0.0] | 0.4 | 1 | unknot |  |  |
| 13 | [0.0, 1.0, 0.0, 0.0] | 0.2 | 1 | unknot |  |  |
| 14 | [0.0, 0.0, 0.0, 1.0] | 0.1 | 2 | 2×unknot |  |  |
| 15 | [0.0, 0.0, 1.0, 0.0] | 0.05 | 4 | 4×unknot |  |  |
| 16 | [0.5, 0.5, 0.5, 0.5] | 0.1 | 1 | unknot |  |  |
| 17 | [0.3498, 0.7795, 0.4797, -0.1999] | 0.0 | 1 | unknot |  |  |
| 18 | [0.3498, 0.7795, 0.4797, -0.1999] | 0.15 | 1 | unknot |  |  |
| 19 | [0.5, 0.5, -0.5, 0.5] | 0.15 | 1 | unknot |  |  |
| 20 | [0.0, 0.0, 0.7071, -0.7071] | 0.5 | 2 | 2×unknot |  |  |

## spun_trefoil (seed 0)

20/20 probes, 6 turns, 45494 thinking tokens, 476.9s

**Explorer's explanation:**

> The hidden surface is the Artin spun trefoil knot (spun 3_1), which is a knotted 2-sphere in R^4. Cross-sections along normals with a significant projection onto the spinning plane (such as e1 and e2 for offsets up to 0.5-0.7) yield the ribbon knot 3_1 # m3_1 (genus 2, fibered, tau = 0, Alexander polynomial [1, -2, 3, -2, 1]). Cross-sections along normals near the 2-dimensional axis plane (such as e3) slice the profile trefoil into 1, 2, or 3 concentric unlinked unknots. Because all multi-component slices near the axis plane have pairwise linking numbers equal to 0, the twist parameter is n = 0 (Artin spinning rather than twist-spinning). Using the O(2) symmetry in the spinning plane and reflection symmetry along the tangle axis, all three held-out slices lie in the regime where the hyperplane intersects the full knotted tangle on both sides of the spinning axis, yielding a single component of type 3_1 # m3_1.

**Held-out slices:**

| # | normal | offset | truth | answer |  |
|---|---|---|---|---|---|
| H1 | [-0.1211, -0.183, 0.633, 0.7424] | 0.0210 | unknot, unknot, unknot | 3_1 # m3_1 | ✗ |
| H2 | [-0.8128, 0.1294, 0.0272, -0.5674] | 0.4998 | 3_1 # m3_1 | 3_1 # m3_1 | ✓ |
| H3 | [0.4134, -0.5852, 0.3669, -0.5933] | 0.1370 | unknot, unknot | 3_1 # m3_1 | ✗ |

**Probes:**

| # | normal | offset | components | knots | linking | held-out |
|---|---|---|---|---|---|---|
| 1 | [1.0, 0.0, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 2 | [0.0, 1.0, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 3 | [0.0, 0.0, 1.0, 0.0] | 0.0 | 3 | 3×unknot |  |  |
| 4 | [0.0, 0.0, 0.0, 1.0] | 0.0 | 2 | unknot, 3_1 # m3_1 |  |  |
| 5 | [1.0, 0.0, 0.0, 0.0] | 0.25 | 1 | 3_1 # m3_1 |  |  |
| 6 | [0.0, 1.0, 0.0, 0.0] | 0.25 | 1 | 3_1 # m3_1 |  |  |
| 7 | [0.0, 0.0, 1.0, 0.0] | 0.25 | 2 | 2×unknot |  |  |
| 8 | [0.0, 0.0, 0.0, 1.0] | 0.25 | 3 | 3×unknot |  |  |
| 9 | [1.0, 0.0, 0.0, 0.0] | 0.5 | 1 | 3_1 # m3_1 |  |  |
| 10 | [0.0, 1.0, 0.0, 0.0] | 0.5 | 1 | 3_1 # m3_1 |  |  |
| 11 | [0.0, 0.0, 1.0, 0.0] | -0.25 | 3 | 3×unknot |  |  |
| 12 | [0.0, 0.0, 0.0, 1.0] | -0.25 | 3 | 3×unknot |  |  |
| 13 | [1.0, 0.0, 0.0, 0.0] | 0.7 | 1 | 3_1 # m3_1 |  |  |
| 14 | [0.0, 1.0, 0.0, 0.0] | 0.7 | 3 | 3×unknot |  |  |
| 15 | [0.0, 0.0, 1.0, 0.0] | 0.5 | 1 | unknot |  |  |
| 16 | [0.0, 0.0, 1.0, 0.0] | -0.496 | 2 | 2×unknot |  |  |
| 17 | [0.8128, -0.1294, 0.0272, -0.5674] | 0.4998 | 2 | 2×unknot |  |  |
| 18 | [0.1294, 0.8128, 0.0272, -0.5674] | 0.4998 | 1 | 3_1 # m3_1 |  |  |
| 19 | [0.5852, 0.4134, 0.3669, -0.5933] | 0.137 | 1 | 3_1 # m3_1 |  |  |
| 20 | [0.1211, 0.183, 0.633, -0.7424] | 0.021 | 1 | 3_1 # m3_1 |  |  |

## spun_figure_eight (seed 0)

20/20 probes, 8 turns, 20776 thinking tokens, 307.5s

**Explorer's explanation:**

> The surface is the Artin spin of the figure-eight knot (4_1), which is a knotted 2-sphere in R^4. Slicing along planes nearly containing the spinning axis (such as [1,0,0,0] and [0,1,0,0] for offsets up to 0.6) yields the connected sum K # -K = 4_1 # 4_1 as a single component. Slicing with normals nearly in the fixed 2-plane (such as [0,0,1,0] and [0,0,0,1]) at offsets >= 0.05 or 0.15 yields collections of unlinked unknots, confirming that the twist number is n = 0 (Artin spinning rather than twist-spinning, which would produce non-trivial braiding/linking). Using the SO(2) rotational symmetry in the spinning plane, we matched the held-out slices to determine their cross-sections.

**Held-out slices:**

| # | normal | offset | truth | answer |  |
|---|---|---|---|---|---|
| H1 | [-0.1211, -0.183, 0.633, 0.7424] | 0.0027 | unknot, unknot | 4_1 # 4_1, unknot, unknot | ✗ |
| H2 | [-0.8128, 0.1294, 0.0272, -0.5674] | 0.5034 | 4_1 # 4_1 | 4_1 # 4_1 | ✓ |
| H3 | [0.4134, -0.5852, 0.3669, -0.5933] | 0.1286 | 4_1 # 4_1, unknot | 4_1 # 4_1 | ✗ |

**Probes:**

| # | normal | offset | components | knots | linking | held-out |
|---|---|---|---|---|---|---|
| 1 | [1.0, 0.0, 0.0, 0.0] | 0.0 | 1 | 4_1 # 4_1 |  |  |
| 2 | [0.0, 1.0, 0.0, 0.0] | 0.0 | 1 | 4_1 # 4_1 |  |  |
| 3 | [0.0, 0.0, 1.0, 0.0] | 0.0 | 3 | 2×unknot, 4_1 # 4_1 |  |  |
| 4 | [0.0, 0.0, 0.0, 1.0] | 0.0 | 2 | unknot, 4_1 # 4_1 |  |  |
| 5 | [1.0, 0.0, 0.0, 0.0] | 0.3 | 1 | 4_1 # 4_1 |  |  |
| 6 | [0.0, 1.0, 0.0, 0.0] | 0.3 | 1 | 4_1 # 4_1 |  |  |
| 7 | [0.0, 0.0, 1.0, 0.0] | 0.3 | 4 | 4×unknot |  |  |
| 8 | [0.0, 0.0, 0.0, 1.0] | 0.3 | 4 | 4×unknot |  |  |
| 9 | [1.0, 0.0, 0.0, 0.0] | 0.6 | 1 | 4_1 # 4_1 |  |  |
| 10 | [0.0, 0.0, 1.0, 0.0] | 0.15 | 3 | 3×unknot |  |  |
| 11 | [0.0, 0.0, 0.0, 1.0] | 0.15 | 3 | 3×unknot |  |  |
| 12 | [0.0, 1.0, 0.0, 0.0] | 0.6 | 1 | 4_1 # 4_1 |  |  |
| 13 | [1.0, 0.0, 0.0, 0.0] | 0.75 | 3 | 3×unknot |  |  |
| 14 | [0.0, 1.0, 0.0, 0.0] | 0.75 | 5 | 5×unknot |  |  |
| 15 | [0.0, 0.0, 1.0, 0.0] | 0.05 | 3 | 2×unknot, 4_1 # 4_1 |  |  |
| 16 | [0.0, 0.0, 0.0, 1.0] | 0.05 | 3 | 3×unknot |  |  |
| 17 | [0.0, 0.823, 0.0272, -0.5674] | 0.5034 | 1 | 4_1 # 4_1 |  |  |
| 18 | [0.5852, 0.4134, 0.3669, -0.5933] | 0.1286 | 1 | 4_1 # 4_1 |  |  |
| 19 | [-0.2506, -0.3509, 0.9023, 0.0] | 0.05 | 3 | 4_1 # 4_1, 2×unknot |  |  |
| 20 | [0.4517, 0.3514, 0.522, 0.6324] | 0.0027 | 1 | 4_1 # 4_1 |  |  |

## twist1_trefoil (seed 0)

20/20 probes, 8 turns, 39789 thinking tokens, 492.7s

**Explorer's explanation:**

> The hidden surface is the Artin spun trefoil knot (spun 3_1), which is a knotted 2-sphere in R^4. Across all probes along the coordinate axes and diagonal directions, every connected cross-section component is either the unknot or the connected sum 3_1 # m3_1 (Alexander polynomial [1, -2, 3, -2, 1], genus 2, fibered, tau=0), with all pairwise linking numbers zero. This is the classic signature of Artin (untwisted) spinning of K = 3_1: any hyperplane intersecting the spinning circle slices the knotted arc in two mirror-symmetric branches joined at the boundary of the slice interval, producing 3_1 # m3_1 whenever the slice interval covers the knotted tangle, and unlinked unknots when the hyperplane misses or slices through the tangle lobes. Using Morse theory on the height function f(s) +/- g(s) and our probe measurements to locate the spinning plane P^perp and axis plane P (where e_1, e_2 lie primarily in P^perp with critical offsets > 0.4 and > 0.5, while e_4 lies nearly in P), all three held-out slices lie within the single-component knotted regime and therefore each has cross-section ["3_1 # m3_1"].

**Held-out slices:**

| # | normal | offset | truth | answer |  |
|---|---|---|---|---|---|
| H1 | [-0.1211, -0.183, 0.633, 0.7424] | 0.0195 | 3_1 # m3_1, unknot | 3_1 # m3_1 | ✗ |
| H2 | [-0.8128, 0.1294, 0.0272, -0.5674] | 0.3902 | 3_1 # m3_1, unknot | 3_1 # m3_1 | ✗ |
| H3 | [0.4134, -0.5852, 0.3669, -0.5933] | 0.1031 | unknot, unknot | 3_1 # m3_1 | ✗ |

**Probes:**

| # | normal | offset | components | knots | linking | held-out |
|---|---|---|---|---|---|---|
| 1 | [1.0, 0.0, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 2 | [0.0, 1.0, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 3 | [0.0, 0.0, 1.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 4 | [0.0, 0.0, 0.0, 1.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 5 | [1.0, 0.0, 0.0, 0.0] | 0.3 | 1 | 3_1 # m3_1 |  |  |
| 6 | [0.0, 1.0, 0.0, 0.0] | 0.3 | 1 | 3_1 # m3_1 |  |  |
| 7 | [0.0, 0.0, 1.0, 0.0] | 0.3 | 2 | 2×unknot |  |  |
| 8 | [0.0, 0.0, 0.0, 1.0] | 0.3 | 2 | 2×unknot |  |  |
| 9 | [1.0, 0.0, 0.0, 0.0] | 0.5 | 2 | 2×unknot |  |  |
| 10 | [0.0, 1.0, 0.0, 0.0] | 0.5 | 2 | unknot, 3_1 # m3_1 |  |  |
| 11 | [0.0, 0.0, 1.0, 0.0] | 0.15 | 1 | 3_1 # m3_1 |  |  |
| 12 | [0.0, 0.0, 0.0, 1.0] | 0.15 | 3 | 3×unknot |  |  |
| 13 | [0.0, 1.0, 0.0, 0.0] | -0.5 | 1 | 3_1 # m3_1 |  |  |
| 14 | [0.0, 0.0, 0.0, 1.0] | -0.15 | 3 | 3×unknot |  |  |
| 15 | [0.0, 0.0, 0.7071, -0.7071] | 0.15 | 1 | 3_1 # m3_1 |  |  |
| 16 | [1.0, 0.0, 0.0, 0.0] | 0.4 | 1 | 3_1 # m3_1 |  |  |
| 17 | [1.0, 0.0, 0.0, 0.0] | -0.4 | 1 | 3_1 # m3_1 |  |  |
| 18 | [0.0, 0.0, 0.0, 1.0] | 0.05 | 3 | 3×unknot |  |  |
| 19 | [1.0, 0.0, 0.0, 0.0] | -0.5 | 2 | unknot, 3_1 # m3_1 |  |  |
| 20 | [-0.7071, 0.0, 0.0, 0.7071] | 0.39 | 3 | 3×unknot |  |  |

## twist1_figure_eight (seed 0)

20/20 probes, 6 turns, 0 thinking tokens, 77.1s

**Explorer's explanation:**

> The central cross-sections (offset=0) along the standard axes all yield the connected sum 4_1 # 4_1, which is the standard equatorial cross-section of a spun or twist-spun figure-eight knot (4_1). Probing along the diagonal [0, 0, 1, 1] at offset 0 reveals 7 unknotted components with every pair having linking number 1 (a 7-component Hopf link). This occurs when slicing along the spinning plane of a 1-twist-spun knot where the knot diagram is twisted during the spin. By Zeeman's theorem, any 1-twist-spun knot in R^4 is unknotted (isotopic to the standard 2-sphere). For the held-out slices: Slice 1 is nearly aligned with [0, 0, 1, 1] at near-zero offset, giving a single unknot component; Slice 2 is predominantly in the x_1-x_4 plane at offset 0.3815, which lies within the knotted core region and yields 4_1 # 4_1; Slice 3 has offset 0.1079 and substantial components in the x_1-x_2 plane, so it also intersects the core and yields 4_1 # 4_1.

**Held-out slices:**

| # | normal | offset | truth | answer |  |
|---|---|---|---|---|---|
| H1 | [-0.1211, -0.183, 0.633, 0.7424] | 0.0171 | unknot, unknot, unknot | unknot | ✗ |
| H2 | [-0.8128, 0.1294, 0.0272, -0.5674] | 0.3815 | 4_1 # 4_1, unknot | 4_1 # 4_1 | ✗ |
| H3 | [0.4134, -0.5852, 0.3669, -0.5933] | 0.1079 | 4_1 # 4_1 | 4_1 # 4_1 | ✓ |

**Probes:**

| # | normal | offset | components | knots | linking | held-out |
|---|---|---|---|---|---|---|
| 1 | [1.0, 0.0, 0.0, 0.0] | 0.0 | 1 | 4_1 # 4_1 |  |  |
| 2 | [0.0, 1.0, 0.0, 0.0] | 0.0 | 1 | 4_1 # 4_1 |  |  |
| 3 | [0.0, 0.0, 1.0, 0.0] | 0.0 | 1 | 4_1 # 4_1 |  |  |
| 4 | [0.0, 0.0, 0.0, 1.0] | 0.0 | 1 | 4_1 # 4_1 |  |  |
| 5 | [1.0, 0.0, 0.0, 0.0] | 0.38 | 1 | 4_1 # 4_1 |  |  |
| 6 | [0.0, 1.0, 0.0, 0.0] | 0.38 | 1 | 4_1 # 4_1 |  |  |
| 7 | [0.0, 0.0, 1.0, 0.0] | 0.38 | 2 | 2×unknot |  |  |
| 8 | [0.0, 0.0, 0.0, 1.0] | 0.38 | 2 | 2×unknot |  |  |
| 9 | [1.0, 0.0, 0.0, 0.0] | -0.38 | 1 | 4_1 # 4_1 |  |  |
| 10 | [0.0, 1.0, 0.0, 0.0] | -0.38 | 1 | 4_1 # 4_1 |  |  |
| 11 | [0.0, 0.0, 1.0, 0.0] | -0.38 | 2 | 2×unknot |  |  |
| 12 | [0.0, 0.0, 0.0, 1.0] | -0.38 | 2 | 2×unknot |  |  |
| 13 | [1.0, 0.0, 0.0, 0.0] | 0.6 | 4 | 4×unknot |  |  |
| 14 | [0.0, 1.0, 0.0, 0.0] | 0.6 | 4 | 4×unknot |  |  |
| 15 | [0.0, 0.0, 1.0, 0.0] | 0.6 | 0 | empty |  |  |
| 16 | [0.0, 0.0, 0.0, 1.0] | 0.6 | 0 | empty |  |  |
| 17 | [0.7071, -0.7071, 0.0, 0.0] | 0.6 | 4 | 4×unknot |  |  |
| 18 | [0.0, 0.0, 0.7071, 0.7071] | 0.0 | 7 | 7×unknot | 0–1: 1, 0–2: 1, 0–3: 1, 0–4: 1, 0–5: 1, 0–6: 1 (+15 more) |  |
| 19 | [0.0, 0.0, 0.7071, -0.7071] | 0.0 | 1 | 4_1 # 4_1 |  |  |
| 20 | [0.7071, 0.7071, 0.0, 0.0] | 0.6 | 4 | 4×unknot |  |  |

## twist2_trefoil (seed 0)

20/20 probes, 6 turns, 0 thinking tokens, 58.6s

**Explorer's explanation:**

> The surface is the Artin spun trefoil (K = 3_1). Central slices Containing or near the spinning plane yield the square knot 3_1 # m3_1, which is the signature of spinning a trefoil knot. Non-central slices or slices along the spinning axis decompose into unknotted components, and a slice aligned with the spinning plane (such as [0,0,1,1] at offset 0) intersects the torus of revolution of the trefoil in linked unknots. Since it is a 0-twist-spun (Artin spun) non-trivial knot, the 2-sphere is knotted in R^4.

**Held-out slices:**

| # | normal | offset | truth | answer |  |
|---|---|---|---|---|---|
| H1 | [-0.1211, -0.183, 0.633, 0.7424] | 0.0231 | 3_1 # m3_1, unknot | 3_1 # m3_1, unknot | ✓ |
| H2 | [-0.8128, 0.1294, 0.0272, -0.5674] | 0.3984 | 3_1 # m3_1 | unknot, unknot | ✗ |
| H3 | [0.4134, -0.5852, 0.3669, -0.5933] | 0.1028 | 3_1 # m3_1 | 3_1 # m3_1 | ✓ |

**Probes:**

| # | normal | offset | components | knots | linking | held-out |
|---|---|---|---|---|---|---|
| 1 | [1.0, 0.0, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 2 | [0.0, 1.0, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 3 | [0.0, 0.0, 1.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 4 | [0.0, 0.0, 0.0, 1.0] | 0.0 | 2 | unknot, 3_1 # m3_1 |  |  |
| 5 | [1.0, 0.0, 0.0, 0.0] | 0.3 | 1 | 3_1 # m3_1 |  |  |
| 6 | [0.0, 1.0, 0.0, 0.0] | 0.3 | 2 | 3_1 # m3_1, unknot |  |  |
| 7 | [0.0, 0.0, 1.0, 0.0] | 0.3 | 3 | 3×unknot |  |  |
| 8 | [0.0, 0.0, 0.0, 1.0] | 0.3 | 3 | 3×unknot |  |  |
| 9 | [0.7071, 0.7071, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 10 | [0.7071, -0.7071, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 11 | [0.7071, 0.0, 0.7071, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 12 | [0.0, 0.0, 0.7071, 0.7071] | 0.0 | 5 | 5×unknot | 0–1: 2, 0–2: 2, 0–3: 2, 0–4: 2, 1–2: 2, 1–3: 2 (+4 more) |  |
| 13 | [1.0, 0.0, 0.0, 0.0] | 0.6 | 3 | 3×unknot |  |  |
| 14 | [0.0, 1.0, 0.0, 0.0] | 0.6 | 3 | 3×unknot |  |  |
| 15 | [0.0, 0.0, 1.0, 0.0] | 0.6 | 0 | empty |  |  |
| 16 | [0.0, 0.0, 0.0, 1.0] | 0.6 | 0 | empty |  |  |
| 17 | [-0.101, 0.5051, 0.6061, 0.6061] | 0.0 | 2 | unknot, 3_1 # m3_1 |  |  |
| 18 | [-0.101, 0.5051, 0.6061, 0.6061] | 0.1 | 2 | unknot, 3_1 # m3_1 |  |  |
| 19 | [0.796, -0.0995, 0.0, -0.597] | 0.4 | 2 | 2×unknot |  |  |
| 20 | [0.6092, 0.4061, 0.3046, -0.6092] | 0.1 | 1 | 3_1 # m3_1 |  |  |

## twist3_trefoil (seed 0)

20/20 probes, 7 turns, 38274 thinking tokens, 499.8s

**Explorer's explanation:**

> The hidden 2-sphere is a 3-twist-spun trefoil (K = 3_1, twist n = 3), which is knotted in R^4 by Zeeman's theorem (n >= 2 for a nontrivial knot K).
> 
> 1. Identifying K = 3_1:
> Generic hyperplane slices with a significant projection onto the spinning plane (roughly the (x_1, x_2)-plane) intersect the spinning circle S^1 at two angles, cutting through the knotted tangle in opposite orientations to form the connected sum K # -K = 3_1 # m3_1 (Alexander polynomial [1, -2, 3, -2, 1], genus 2, fibered = true, tau = 0).
> 
> 2. Identifying the construction (twist-spun) and twist parameter (n = 3):
> The fixed plane (e_x, e_y) is closely aligned with the (x_3, x_4)-plane, with the twist axis e_x pointing near [0, 0, 0.7071, 0.7071] (and held-out normal #1, [-0.1211, -0.183, 0.633, 0.7424]). Probing along [0, 0, 0.7071, 0.7071] at offset 0.1 slices perpendicular to the twist axis through the tangle, producing 6 unknot components: 3 unlinked unknots from the untwisted return strands and 3 linked unknots from the 3 strands inside the twist box, which revolve n times around each other as the spinning angle theta goes from 0 to 2*pi. Their pairwise linking numbers are all lk = 3, which directly gives the twist parameter n = 3.
> 
> 3. Predicting the held-out slices:
> - Slice 1 (normal=[-0.1211, -0.183, 0.633, 0.7424], offset=0.022): The normal is aligned with the twist axis e_x and the small offset 0.022 cuts directly through the middle of the twist box and return strands, yielding 6 unknots: ["unknot", "unknot", "unknot", "unknot", "unknot", "unknot"].
> - Slice 2 (normal=[-0.8128, 0.1294, 0.0272, -0.5674], offset=0.3885): The normal has a large projection (0.823) onto the spinning plane. By the 3-fold rotational symmetry of the 3-twist-spun knot in the spinning plane, probing the -120 degree and -60 degree rotated normals in the spinning plane at offset 0.3885 confirms a single component: ["3_1 # m3_1"].
> - Slice 3 (normal=[0.4134, -0.5852, 0.3669, -0.5933], offset=0.105): The normal also has a large projection (0.716) onto the spinning plane. Probing the +120 degree rotated normal and reflected normal in the spinning plane at offset 0.105 confirms a single component: ["3_1 # m3_1"].

**Held-out slices:**

| # | normal | offset | truth | answer |  |
|---|---|---|---|---|---|
| H1 | [-0.1211, -0.183, 0.633, 0.7424] | 0.0220 | 3_1 # m3_1, unknot | unknot, unknot, unknot, unknot, unknot, unknot | ✗ |
| H2 | [-0.8128, 0.1294, 0.0272, -0.5674] | 0.3885 | 3_1 # m3_1, unknot | 3_1 # m3_1 | ✗ |
| H3 | [0.4134, -0.5852, 0.3669, -0.5933] | 0.1050 | 3_1 # m3_1, unknot, unknot | 3_1 # m3_1 | ✗ |

**Probes:**

| # | normal | offset | components | knots | linking | held-out |
|---|---|---|---|---|---|---|
| 1 | [1.0, 0.0, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 2 | [0.0, 1.0, 0.0, 0.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 3 | [0.0, 0.0, 1.0, 0.0] | 0.0 | 4 | 3_1 # m3_1, 3×unknot |  |  |
| 4 | [0.0, 0.0, 0.0, 1.0] | 0.0 | 1 | 3_1 # m3_1 |  |  |
| 5 | [1.0, 0.0, 0.0, 0.0] | 0.2 | 1 | 3_1 # m3_1 |  |  |
| 6 | [0.0, 1.0, 0.0, 0.0] | 0.2 | 1 | 3_1 # m3_1 |  |  |
| 7 | [0.0, 0.0, 1.0, 0.0] | 0.2 | 3 | 3×unknot |  |  |
| 8 | [0.0, 0.0, 0.0, 1.0] | 0.2 | 3 | 3×unknot |  |  |
| 9 | [0.0, 0.0, 0.7071, 0.7071] | 0.1 | 6 | 6×unknot | 0–4: 3, 0–5: 3, 4–5: 3 |  |
| 10 | [0.0, 0.0, 0.7071, -0.7071] | 0.1 | 2 | 3_1 # m3_1, unknot |  |  |
| 11 | [1.0, 0.0, 0.0, 0.0] | 0.5 | 1 | 3_1 # m3_1 |  |  |
| 12 | [0.0, 1.0, 0.0, 0.0] | 0.5 | 2 | unknot, 3_1 # m3_1 |  |  |
| 13 | [0.5185, 0.6392, 0.0272, -0.5674] | 0.3885 | 1 | 3_1 # m3_1 |  |  |
| 14 | [0.3001, 0.6506, 0.3669, -0.5933] | 0.105 | 1 | 3_1 # m3_1 |  |  |
| 15 | [0.5, 0.0, 0.6124, 0.6124] | 0.022 | 3 | 3_1 # m3_1, 2×unknot |  |  |
| 16 | [0.3536, 0.3536, 0.6124, 0.6124] | 0.022 | 1 | 3_1 # m3_1 |  |  |
| 17 | [-0.2943, 0.7686, 0.0272, -0.5674] | 0.3885 | 1 | 3_1 # m3_1 |  |  |
| 18 | [0.3536, -0.3536, 0.6124, 0.6124] | 0.022 | 1 | 3_1 # m3_1 |  |  |
| 19 | [-0.3536, 0.3536, 0.6124, 0.6124] | 0.022 | 2 | 3_1 # m3_1, unknot |  |  |
| 20 | [-0.5852, 0.4134, 0.3669, -0.5933] | 0.105 | 1 | 3_1 # m3_1 |  |  |
