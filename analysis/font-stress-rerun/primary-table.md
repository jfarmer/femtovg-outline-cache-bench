Absolute first-paint host CPU savings in the unchanged demo, final versus master, DPR2. Positive values save time. Fonts were chosen by an exploratory search, then measured in a separate 12-block confirmation.

| Font | Master | Final | Paired savings (95% CI) | Secondary ratio change | Evidence |
|---|---:|---:|---:|---:|---|
| DoulosSIL-Regular | 7.121 ms | 4.891 ms | +2.230 ms [+2.183, +2.269] | -31.31% | improvement |
| Rye-Regular | 6.450 ms | 3.795 ms | +2.655 ms [+2.615, +2.692] | -41.16% | improvement |
| Vollkorn-Medium | 6.754 ms | 4.551 ms | +2.203 ms [+2.161, +2.250] | -32.62% | improvement |

| Selected font | Additional savings versus control (95% CI) | Evidence |
|---|---:|---|
| Rye-Regular versus Vollkorn-Medium | +0.452 ms [+0.409, +0.492] | larger_savings |
| DoulosSIL-Regular versus Vollkorn-Medium | +0.027 ms [-0.034, +0.089] | uncertain |

All phase/metric and weighted reported-sequence results, including warm costs, uncertain intervals and regressions, remain in [summary.csv](summary.csv). Paired raw-derived process values are in [paired-processes.csv](paired-processes.csv); the independent preflight/order/count audit is [raw-audit.json](raw-audit.json). See [summary.json](summary.json) for estimator definitions, exact resample seeds, conditional selection scope and machine quiet caveats. These host drawing measurements are not end-to-end launch or FPS estimates. GPU completion is separately retained when supplied.
