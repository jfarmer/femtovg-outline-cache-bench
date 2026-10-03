# Summary of the repeated favorable-font cohort

The fixed master/final comparison was repeated in full after a background-load concern. Overlap with the original measurement is unestablished; both numerical cohorts remain retained.

| Font | CPU master → final (ms) | CPU saving, 95% CI (ms) | GPU completion master → final (ms) | GPU completion saving, 95% CI (ms) |
| --- | --- | --- | --- | --- |
| Rye-Regular | 6.450 → 3.795 | 2.655 [2.615, 2.692] | 15.924 → 13.133 | 2.790 [2.542, 3.151] |
| DoulosSIL-Regular | 7.121 → 4.891 | 2.230 [2.183, 2.269] | 16.471 → 13.582 | 2.889 [2.235, 3.473] |
| Vollkorn-Medium | 6.754 → 4.551 | 2.203 [2.161, 2.250] | 16.039 → 13.115 | 2.924 [2.256, 3.542] |

| Font versus Vollkorn | Additional CPU saving, 95% CI (ms) | Inference |
| --- | --- | --- |
| Rye-Regular | 0.452 [0.409, 0.492] | larger_savings |
| DoulosSIL-Regular | 0.027 [-0.034, 0.089] | uncertain |

Rye CPU text/warm at DPR2 has an extra final cost of **6.50 [4.83, 8.30] µs/frame**. All fonts, costs, uncertain intervals and every phase remain in the [full CSV](analysis/font-stress-rerun/summary.csv). This remains selected favorable-font evidence, not universal improvement.

The repeat retains all 288 processes, the original binaries/fonts/scenes/native pixels, and the balanced schedule. Independent checking reproduced 1,116 effects and 2,234 intervals. No runs were excluded or pooled across cohorts.

[Full report](FONT-STRESS-RERUN.md), [original report](FONT-STRESS-SEARCH.md), and [all original-versus-repeat comparisons](analysis/font-stress-rerun/comparison/COMPARISON.md) supply the evidence and limits.
