# Original and rerun confirmation comparison

Separate repeats on the same machine, unchanged fixed fonts/scene/source/binaries and recorded pixel reference. All 1,116 endpoint estimates retained without exclusions. Original and rerun block labels are not paired across campaigns; no pooled estimate or CI for between-campaign change is computed. CI overlap is not an equivalence test. Game/background-load overlap with original measurement is not established; recorded collector starts are shown without inferring missing per-process timestamps or an exact campaign end.

Primary CPU demo first paint at DPR2; positive savings mean faster final execution.

| Font | Original CPU saving, ms [95% CI] | Rerun CPU saving, ms [95% CI] | Original → rerun inference |
| --- | --- | --- | --- |
| DoulosSIL-Regular | 2.217 [2.173, 2.260] | 2.230 [2.183, 2.269] | improvement → improvement |
| Rye-Regular | 2.634 [2.564, 2.704] | 2.655 [2.615, 2.692] | improvement → improvement |
| Vollkorn-Medium | 2.184 [2.119, 2.248] | 2.203 [2.161, 2.250] | improvement → improvement |

GPU completion is a secondary endpoint.

| Font | Original GPU completion saving, ms [95% CI] | Rerun GPU completion saving, ms [95% CI] |
| --- | --- | --- |
| DoulosSIL-Regular | 1.651 [0.755, 2.421] | 2.889 [2.235, 3.473] |
| Rye-Regular | 2.808 [2.272, 3.323] | 2.790 [2.542, 3.151] |
| Vollkorn-Medium | 2.032 [1.534, 2.466] | 2.924 [2.256, 3.542] |

Additional saving versus simultaneous Vollkorn.

| Font versus control | Original extra saving, ms [95% CI] | Rerun extra saving, ms [95% CI] | Original → rerun inference |
| --- | --- | --- | --- |
| DoulosSIL-Regular versus Vollkorn-Medium | 0.032 [-0.011, 0.076] | 0.027 [-0.034, 0.089] | uncertain → uncertain |
| Rye-Regular versus Vollkorn-Medium | 0.450 [0.358, 0.547] | 0.452 [0.409, 0.492] | larger_savings → larger_savings |

All warm draw/completion outcomes are retained below, including regressions and uncertain intervals.

| Font/DPR/backend/scene | Original saving, µs [95% CI] | Rerun saving, µs [95% CI] | Original → rerun inference |
| --- | --- | --- | --- |
| DoulosSIL-Regular / 1 / cpu / demo | 2.93 [-0.18, 7.95] | 0.12 [-1.40, 1.53] | uncertain → uncertain |
| DoulosSIL-Regular / 1 / cpu / text | -7.15 [-8.46, -5.75] | -6.78 [-9.86, -4.19] | regression → regression |
| DoulosSIL-Regular / 2 / cpu / demo | -0.28 [-1.38, 1.09] | 0.25 [-1.51, 2.00] | uncertain → uncertain |
| DoulosSIL-Regular / 2 / cpu / text | -7.59 [-9.06, -6.27] | -6.14 [-8.81, -3.65] | regression → regression |
| Rye-Regular / 1 / cpu / demo | 1.03 [-0.71, 3.22] | -1.03 [-2.60, 0.55] | uncertain → uncertain |
| Rye-Regular / 1 / cpu / text | -5.56 [-6.74, -4.31] | -6.81 [-8.66, -5.29] | regression → regression |
| Rye-Regular / 2 / cpu / demo | 1.81 [0.20, 3.52] | 0.54 [-1.15, 2.25] | improvement → uncertain |
| Rye-Regular / 2 / cpu / text | -7.51 [-9.86, -5.71] | -6.50 [-8.30, -4.83] | regression → regression |
| Vollkorn-Medium / 1 / cpu / demo | -0.48 [-2.11, 1.18] | -0.78 [-2.45, 1.29] | uncertain → uncertain |
| Vollkorn-Medium / 1 / cpu / text | -6.04 [-7.90, -4.24] | -7.68 [-9.41, -6.05] | regression → regression |
| Vollkorn-Medium / 2 / cpu / demo | -1.63 [-3.71, 0.31] | -0.08 [-1.20, 1.09] | uncertain → uncertain |
| Vollkorn-Medium / 2 / cpu / text | -6.86 [-8.61, -5.23] | -7.86 [-10.52, -5.63] | regression → regression |
| DoulosSIL-Regular / 1 / gpu / demo | 75.76 [-17.24, 178.62] | 27.80 [-28.35, 81.67] | uncertain → uncertain |
| DoulosSIL-Regular / 1 / gpu / text | 22.09 [-33.77, 89.91] | 2.28 [-21.33, 27.29] | uncertain → uncertain |
| DoulosSIL-Regular / 2 / gpu / demo | -22.71 [-70.16, 30.33] | -29.50 [-77.13, 20.68] | uncertain → uncertain |
| DoulosSIL-Regular / 2 / gpu / text | -120.38 [-312.09, -11.26] | -28.80 [-43.50, -16.50] | regression → regression |
| Rye-Regular / 1 / gpu / demo | -21.62 [-112.83, 64.64] | -38.08 [-83.43, 13.25] | uncertain → uncertain |
| Rye-Regular / 1 / gpu / text | 8.77 [-18.05, 38.45] | -4.61 [-11.04, 1.88] | uncertain → uncertain |
| Rye-Regular / 2 / gpu / demo | 14.36 [-17.72, 44.48] | -26.44 [-91.32, 39.13] | uncertain → uncertain |
| Rye-Regular / 2 / gpu / text | 4.27 [-11.87, 22.12] | -13.04 [-18.86, -6.95] | uncertain → regression |
| Vollkorn-Medium / 1 / gpu / demo | -130.94 [-423.32, 42.61] | -10.73 [-71.96, 54.47] | uncertain → uncertain |
| Vollkorn-Medium / 1 / gpu / text | -99.52 [-274.87, 0.70] | -15.45 [-28.65, -2.45] | uncertain → regression |
| Vollkorn-Medium / 2 / gpu / demo | 36.86 [-18.56, 90.19] | 20.34 [-15.01, 53.47] | uncertain → uncertain |
| Vollkorn-Medium / 2 / gpu / text | 9.01 [-25.75, 54.96] | -13.80 [-29.72, 1.15] | uncertain → uncertain |

Recorded chronology (start/analysis records only).

| UTC record | Campaign | Backend/stage |
| --- | --- | --- |
| 2026-10-02T20:25:14.206965+00:00 | original | cpu |
| 2026-10-02T20:32:43.385339+00:00 | original | gpu |
| 2026-10-02T20:42:39.860779+00:00 | original | analysis |
| 2026-10-02T21:46:52.545023+00:00 | rerun | cpu |
| 2026-10-02T21:54:09.383871+00:00 | rerun | gpu |
| 2026-10-02T22:03:33.924457+00:00 | rerun | analysis |

[All 1,116 endpoint comparisons](comparison.csv) and [complete structured comparison](comparison.json) retain every phase and metric. Classification-transition counts are descriptive and the many secondary intervals are not multiplicity-adjusted.
