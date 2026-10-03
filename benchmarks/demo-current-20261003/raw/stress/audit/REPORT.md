# Independent proof-sheet audit

PASS: both complete cohorts were reconstructed from their original CSV stdout without importing the runner. The DPI 1 cohort is primary; DPI 2 remains a separate control. The DPI 1 plan was declared for a fresh campaign after the DPI 2 units error was identified. No measured records were excluded or merged.

Each cohort has 72 processes, 288 phase records, 12 complete paired blocks, and 6 master-first/6 final-first pairs per font. Each process reports a 44-frame sequence: first paint 1, warm 30, changing size 12, return 1. Every reported frame requests 1,980 glyphs through 30 public text calls, with 198 distinct glyph/font/size instances and 66 characters per row. Workload counts and finite 1800×1200 logical dimensions match between variants.

All 15 summary rows per cohort reproduce within the stated numerical tolerance. Intervals are exploratory paired median bootstraps with 10,000 resamples, seed 61432, percentile order positions 250/9750, and no multiplicity correction. Complete sequence totals are formed inside each process before pairing; they include all 44 measured frames. Marginal medians can differ from the paired median difference.

Frozen binaries, all frozen source files, compiler artifact manifests/features, dependency graphs, lock dependency records, harness digest and build conditions pass. Five existing baseline files match upstream 6a5f15a, and the new Swash module is absent from both baseline and upstream. Six final files match the primary source pin and released code at b87a94d. The only whole-file difference is two comment lines inside the Swash test module. Its entire prefix before the test module is identical. The final snapshot registration retains an old working-tree revision label; full hashes and commit comparisons establish the actual identity.

Font files and supplied license/acquisition records match their predeclared digests. All three fonts use SIL OFL 1.1. The predeclared LICENSE-Roboto is a preserved legacy Apache 2.0 file: verifying its hash does not establish applicability to this Roboto Flex font. The exact Roboto Flex font bytes match the benchmark asset whose ATTRIBUTION.md maps it to licenses/RobotoFlex-OFL.txt; that applicable OFL file and mapping were verified separately in LICENSE-SUPPLEMENT.json. Original plans and measurements remain unchanged. The original compiler-guard prestart abort remains separate with zero timing records. Six API/count smoke processes are excluded from both cohorts.

## paired12-dpi1 (DPI 1)

| Font | Phase | Master ms | Final ms | Paired delta ms [95% CI] | Paired reduction % [95% CI] |
|---|---|---:|---:|---:|---:|
| FleurDeLeah | first_paint | 89.304 | 19.936 | -69.192 [-70.555, -68.633] | 77.93 [77.37, 78.13] |
| FleurDeLeah | warm | 0.151 | 0.143 | -0.007 [-0.013, -0.005] | 4.81 [3.56, 8.33] |
| FleurDeLeah | new_size | 90.612 | 21.685 | -68.946 [-69.474, -68.088] | 76.10 [75.96, 76.15] |
| FleurDeLeah | return | 0.238 | 0.221 | -0.018 [-0.025, -0.011] | 7.42 [4.84, 10.51] |
| FleurDeLeah | complete_sequence | 1181.153 | 284.902 | -895.539 [-904.365, -888.109] | 75.91 [75.79, 76.01] |
| RobotoFlex | first_paint | 4.551 | 3.766 | -0.787 [-0.813, -0.751] | 17.40 [16.37, 17.89] |
| RobotoFlex | warm | 0.159 | 0.150 | -0.007 [-0.010, -0.005] | 4.68 [3.13, 6.08] |
| RobotoFlex | new_size | 5.068 | 4.245 | -0.836 [-0.855, -0.811] | 16.52 [16.17, 16.95] |
| RobotoFlex | return | 0.201 | 0.187 | -0.011 [-0.025, -0.004] | 5.80 [1.91, 11.54] |
| RobotoFlex | complete_sequence | 70.493 | 59.384 | -10.948 [-11.363, -10.687] | 15.72 [15.22, 16.13] |
| Rye | first_paint | 51.453 | 12.771 | -38.513 [-39.176, -38.079] | 75.18 [74.66, 75.54] |
| Rye | warm | 0.152 | 0.140 | -0.012 [-0.014, -0.009] | 7.81 [6.10, 9.11] |
| Rye | new_size | 52.582 | 13.799 | -38.860 [-39.190, -38.293] | 73.84 [73.48, 73.93] |
| Rye | return | 0.233 | 0.222 | -0.018 [-0.033, -0.004] | 7.64 [1.85, 13.59] |
| Rye | complete_sequence | 687.949 | 183.041 | -505.635 [-509.973, -498.262] | 73.44 [73.15, 73.61] |

Largest absolute discrepancy from stored statistics: 0. CI classification: {'saving_ci_below_zero': 15, 'loss_ci_above_zero': 0, 'inconclusive_ci_crosses_zero': 0}.

## paired12-native (DPI 2)

| Font | Phase | Master ms | Final ms | Paired delta ms [95% CI] | Paired reduction % [95% CI] |
|---|---|---:|---:|---:|---:|
| FleurDeLeah | first_paint | 53.253 | 15.141 | -38.220 [-38.690, -37.749] | 71.73 [71.50, 72.21] |
| FleurDeLeah | warm | 0.150 | 0.141 | -0.009 [-0.011, -0.005] | 6.14 [3.27, 7.05] |
| FleurDeLeah | new_size | 53.749 | 15.790 | -37.950 [-38.164, -37.785] | 70.60 [70.42, 70.68] |
| FleurDeLeah | return | 0.212 | 0.194 | -0.021 [-0.028, -0.005] | 9.72 [2.58, 13.26] |
| FleurDeLeah | complete_sequence | 702.934 | 209.137 | -493.423 [-496.066, -492.460] | 70.24 [70.15, 70.35] |
| RobotoFlex | first_paint | 2.976 | 2.460 | -0.514 [-0.538, -0.491] | 17.43 [16.53, 18.05] |
| RobotoFlex | warm | 0.155 | 0.145 | -0.008 [-0.013, -0.007] | 5.20 [4.49, 8.55] |
| RobotoFlex | new_size | 2.887 | 2.282 | -0.593 [-0.651, -0.551] | 20.64 [19.42, 22.18] |
| RobotoFlex | return | 0.163 | 0.159 | -0.001 [-0.010, +0.002] | 0.43 [-1.37, 6.20] |
| RobotoFlex | complete_sequence | 42.438 | 34.381 | -7.846 [-8.535, -7.414] | 18.63 [17.63, 19.85] |
| Rye | first_paint | 30.934 | 9.423 | -21.570 [-21.864, -21.203] | 69.68 [68.98, 69.98] |
| Rye | warm | 0.150 | 0.137 | -0.013 [-0.014, -0.010] | 8.56 [6.94, 9.41] |
| Rye | new_size | 31.263 | 9.617 | -21.547 [-21.947, -21.490] | 69.23 [69.13, 69.42] |
| Rye | return | 0.215 | 0.175 | -0.033 [-0.046, -0.026] | 15.73 [12.88, 20.39] |
| Rye | complete_sequence | 411.007 | 129.123 | -281.005 [-285.763, -279.357] | 68.56 [68.47, 68.80] |

Largest absolute discrepancy from stored statistics: 0. CI classification: {'saving_ci_below_zero': 14, 'loss_ci_above_zero': 0, 'inconclusive_ci_crosses_zero': 1}.

## Interpretation limits

- At identity canvas transform, native atlas font sizes are 14/20/28 pixels plus the changing-size delta, independent of layout DPR. DPI 1 requests row shifts 0..0.9 in 0.1 native units; DPI 2 requests 0..0.45 in 0.05 units. Individual glyph advances and floating-point quantization mean the defensible claim is **up to ten requested canonical phase bins**, rather than a verified ten bins for every glyph.
- Returned public TextMetrics positions are the invscaled positions passed to the identity-transform atlas path. They could diagnose requested canonical bins, but this unchanged harness stores counts rather than every glyph position. Request counts are not instrumented bitmap or outline cache hits, misses, admissions, or evictions.
- Changing-size frames avoid previous-size bitmap reuse but retain repeated same-frame geometry opportunities across rows. They are not a pure miss-only control. A fast return can reuse the outer bitmap atlas; it does not independently prove outline-cache retention.
- The three-typeface dense proof sheet demonstrates a large bounded public-API CPU cost and patch saving. It does not establish a globally maximal font/workload, isolate hinting alone, isolate the arena, or prove eviction. It is not an application/GPU/window frame-time claim. Void produces no captured proof-sheet pixels.
- Timings retain only phase means, not every individual frame time. Public count assertions in the harness enforce the reported count across each phase. Process-name checks before/after cannot prove continuous machine isolation or absence of unrelated CPU load; successful before checks are inferred from the hash-bound runner control flow, whereas after status and timestamps are explicit in raw records.
- DPI 1 and DPI 2 are separate chronological studies, not paired cross-DPI experiments. Their difference cannot be assigned solely to phase coverage because shaping/layout scale also changes.
- Existing synthetic non-Swash warm-paragraph costs of about 1.3–2.4 microseconds per frame remain part of the broader patch assessment; this Swash-only stress comparison does not erase or measure them.

