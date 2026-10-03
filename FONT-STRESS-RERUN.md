# Repeat of the favorable-font performance measurements

With the unchanged FemtoVG demo at DPR2, Rye Regular reduced CPU Canvas draw time from **6.450 to 3.795 ms** on first paint, saving **2.655 [2.615, 2.692] ms**. Real offscreen GPU completion changed from **15.924 to 13.133 ms**, saving **2.790 [2.542, 3.151] ms**. Positive savings mean faster final execution; intervals are nominal 95% bootstrap intervals.

This is a complete fresh repeat of the fixed three-font master/final cohort, requested because of a background-load concern. Overlap between the reported game activity and the original measurement was not established. The original [numeric report](FONT-STRESS-SEARCH.md) and [archive](results/font-stress-search/) remain unchanged. The repeat changes no font, scene, production source, executable, native pixel proof, selection, schedule or estimator. It adds observations rather than selecting runs from either cohort.

## Fresh repeat against master

| Font | CPU master → final (ms) | CPU saving, 95% CI (ms) | GPU completion master → final (ms) | GPU completion saving, 95% CI (ms) |
| --- | --- | --- | --- | --- |
| Rye-Regular | 6.450 → 3.795 | 2.655 [2.615, 2.692] | 15.924 → 13.133 | 2.790 [2.542, 3.151] |
| DoulosSIL-Regular | 7.121 → 4.891 | 2.230 [2.183, 2.269] | 16.471 → 13.582 | 2.889 [2.235, 3.473] |
| Vollkorn-Medium | 6.754 → 4.551 | 2.203 [2.161, 2.250] | 16.039 → 13.115 | 2.924 [2.256, 3.542] |

The primary endpoint remains first-paint host CPU draw time at DPR2. GPU completion is a secondary endpoint. These are deliberately selected favorable fonts from the retained 56-face search, not an estimate for typical fonts or a claim of universal improvement. The complete patch is measured, including scaler reuse and correctness fixes; this campaign does not isolate the arena cache alone.

| Font versus Vollkorn | Additional CPU saving, 95% CI (ms) | Inference |
| --- | --- | --- |
| Rye-Regular | 0.452 [0.409, 0.492] | larger_savings |
| DoulosSIL-Regular | 0.027 [-0.034, 0.089] | uncertain |

The control comparison subtracts the simultaneously measured Vollkorn master/final savings within each block. A `larger_savings` interval excludes zero in the positive direction; `uncertain` means the interval crosses zero. Greater saving in a selected font does not imply an order-of-magnitude increase over the prior favorable font.

| Font | CPU saving across 65 reported demo frames (ms) | GPU completion saving (ms) |
| --- | --- | --- |
| Rye-Regular | 54.467 [53.980, 54.967] | 65.321 [62.017, 68.650] |
| DoulosSIL-Regular | 44.710 [44.070, 45.421] | 52.802 [51.198, 54.180] |
| Vollkorn-Medium | 45.230 [44.688, 45.786] | 57.848 [55.603, 60.278] |

The 65-frame demo total sums each trial's measured phase time × recorded frames before taking the process median. It includes first paint, 30 warm frames, 12 zoom-in, 12 zoom-out and 10 pan frames. It excludes 119 unreported warm-up frames; it is not elapsed wall-clock replay duration. CPU draw, GPU submit and GPU completion are cumulative alternative endpoints and must not be added together.

| Font | CPU zoom in saving (ms/frame) | CPU zoom out saving (ms/frame) | CPU warm saving (µs/frame) | CPU pan saving (µs/frame) |
| --- | --- | --- | --- | --- |
| Rye-Regular | 2.606 [2.581, 2.631] | 1.702 [1.682, 1.723] | 0.54 [-1.15, 2.25] | 0.40 [-1.24, 2.12] |
| DoulosSIL-Regular | 2.099 [2.071, 2.130] | 1.435 [1.411, 1.462] | 0.25 [-1.51, 2.00] | 3.76 [1.15, 6.62] |
| Vollkorn-Medium | 2.113 [2.092, 2.133] | 1.475 [1.457, 1.500] | -0.08 [-1.20, 1.09] | 1.61 [0.84, 2.44] |

## Costs and limits

Atlas-warm text costs remain explicit. Positive values below mean extra final CPU cost; a negative value would mean a saving.

| Font | DPR | Extra final CPU text/warm cost, 95% CI (µs/frame) |
| --- | --- | --- |
| Rye-Regular | 1 | 6.81 [5.29, 8.66] |
| Rye-Regular | 2 | 6.50 [4.83, 8.30] |
| DoulosSIL-Regular | 1 | 6.78 [4.19, 9.86] |
| DoulosSIL-Regular | 2 | 6.14 [3.65, 8.81] |
| Vollkorn-Medium | 1 | 7.68 [6.05, 9.41] |
| Vollkorn-Medium | 2 | 7.86 [5.63, 10.52] |

All text, variation, unique-size, unique-variation, pollution and hot-return phases at both DPRs are retained, including regressions and uncertain intervals, in the [1,116-endpoint CSV](analysis/font-stress-rerun/summary.csv). Variation controls keep Roboto rather than the substituted font. These repeated controls are not independent font-specific evidence. The repeat does not establish universally faster misses, warm frames or cache churn. The prior [revised-cache report](REVISED-OUTLINE-CACHE.md) retains the separate capacity/memory investigation and Alustin evidence; this font repeat does not remeasure those applications or memory costs.

## Original cohort versus repeat

| Font | Original CPU saving, 95% CI (ms) | Repeat CPU saving, 95% CI (ms) | Original → repeat inference |
| --- | --- | --- | --- |
| Rye-Regular | 2.634 [2.564, 2.704] | 2.655 [2.615, 2.692] | improvement → improvement |
| DoulosSIL-Regular | 2.217 [2.173, 2.260] | 2.230 [2.183, 2.269] | improvement → improvement |
| Vollkorn-Medium | 2.184 [2.119, 2.248] | 2.203 [2.161, 2.250] | improvement → improvement |

| Font | Original GPU completion saving, 95% CI (ms) | Repeat GPU completion saving, 95% CI (ms) |
| --- | --- | --- |
| Rye-Regular | 2.808 [2.272, 3.323] | 2.790 [2.542, 3.151] |
| DoulosSIL-Regular | 1.651 [0.755, 2.421] | 2.889 [2.235, 3.473] |
| Vollkorn-Medium | 2.032 [1.534, 2.466] | 2.924 [2.256, 3.542] |

The [complete comparison](analysis/font-stress-rerun/comparison/COMPARISON.md), [all endpoint pairs](analysis/font-stress-rerun/comparison/comparison.csv), and [structured comparison](analysis/font-stress-rerun/comparison/comparison.json) retain both cohorts. They verify identical recorded inputs and preserve all 1,116 endpoints. Estimates remain separate: blocks are not paired across cohorts, no pooled estimate or between-cohort change interval is computed, and confidence-interval overlap is not an equivalence test. This comparison cannot establish that background activity caused any difference.

## Protocol and checks

The repeat retained 144 CPU plus 144 GPU processes: 12 paired blocks × three fonts × two DPRs × two versions. Every font/DPR has six master→final and six final→master orders, with configurations rotated by block. CPU uses five trials per process through Canvas with the Void renderer; GPU uses three with real offscreen WGPU/Metal. Every process contributes all 28 phases. No process was retried or excluded. These are draw/submit/completion measurements, not application startup, displayed FPS or Alustin measurements.

Absolute effects are means of paired process medians. Nominal 95% intervals use 10,000 whole-block bootstrap resamples with seed 72531; the same backend resamples are shared across fonts/DPRs/endpoints. Percentages in the machine-readable output are ratios of means. The intervals are conditional on the selected fonts and unadjusted for the many secondary endpoints. Both cohorts use the same Apple M4 Max machine with 128 GiB RAM. One-machine repeats and order checks do not prove absence of thermal drift, DVFS or competing work throughout an interval.

The original native pixel proof's 504 captures are reused unchanged; this repeat takes no new pixel captures. Final RGBA and atlas counts match the independent uncached-master reference keyed by actual signed raster-offset bits; master's original aliasing behavior is preserved separately. Live source/executable/font/raw/pixel binding passed the new analyzer. The unchanged direct raw/indexed-bootstrap checker reproduced **1,116 effects and 2,234 intervals**. [Audit](analysis/font-stress-rerun-independent-audit.json), [complete analysis](analysis/font-stress-rerun/summary.json), and [raw/live audit](analysis/font-stress-rerun/raw-audit.json) retain the validation.

| Frozen final source | SHA-256 |
| --- | --- |
| src/lib.rs | ae79b1702bb44fcef401b47dda0b38458160a57876f74b10cbb445d4d97c8798 |
| src/text.rs | 6ec9215f1ab17cad624fca578ef327af2bf842554d322a06887fc26b8204ca5f |
| src/text/swash_rasterizer.rs | fa2fc5852710952ee3122500e08bda3a1dd38d69a39cd0420604f51c9488ee92 |

[Rerun context](analysis/font-stress-rerun/rerun-context.md) records the initial process-name observation and its limited scope. The same machine and frozen baseline/final source identities as the [original protocol](FONT-STRESS-SEARCH.md) apply. [Current workspace identity](analysis/font-stress-rerun/current-workspace-identity.json) verifies that the three production files still match this measured final, and [hardware](analysis/font-stress-rerun/hardware.json) retains the machine observation. No new source build occurred for this repeat. The [new raw archive](results/font-stress-rerun/) retains the attempts, analysis, exact seven selection aliases and report inputs; original absolute source/pixel references resolve through the unchanged companion archives. [Offline verification and reproduction](docs/font-stress-rerun-reproduction.md) describe that mapping and the separately disclosed fresh-build path.

[The report input manifest](analysis/font-stress-rerun-original-report-inputs.json) binds the displayed report to its source estimates, independent proofs and all-endpoint comparison. Original numerical reports, source bundles and archives remain preserved.

Captured analyzer logs contain RuntimeWarning output. The unchanged direct checker reproduced the retained finite effects and intervals; no warning cause is inferred and no measurements are excluded. The logs remain visible under [analysis logs](analysis/font-stress-rerun/logs/).
