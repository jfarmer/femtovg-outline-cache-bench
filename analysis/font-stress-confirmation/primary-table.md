Absolute first-paint host CPU savings in the unchanged demo, final versus master, DPR2. Positive values save time. Fonts were chosen by an exploratory search, then measured in a separate 12-block confirmation.

| Font | Master | Final | Paired savings (95% CI) | Secondary ratio change | Evidence |
|---|---:|---:|---:|---:|---|
| DoulosSIL-Regular | 7.056 ms | 4.840 ms | +2.217 ms [+2.173, +2.260] | -31.42% | improvement |
| Rye-Regular | 6.396 ms | 3.761 ms | +2.634 ms [+2.564, +2.704] | -41.19% | improvement |
| Vollkorn-Medium | 6.675 ms | 4.491 ms | +2.184 ms [+2.119, +2.248] | -32.72% | improvement |

| Selected font | Additional savings versus control (95% CI) | Evidence |
|---|---:|---|
| Rye-Regular versus Vollkorn-Medium | +0.450 ms [+0.358, +0.547] | larger_savings |
| DoulosSIL-Regular versus Vollkorn-Medium | +0.032 ms [-0.011, +0.076] | uncertain |

All phase/metric and weighted reported-sequence results, including warm costs, uncertain intervals and regressions, remain in [summary.csv](summary.csv). Paired raw-derived process values are in [paired-processes.csv](paired-processes.csv); the independent preflight/order/count audit is [raw-audit.json](raw-audit.json). See [summary.json](summary.json) for estimator definitions, exact resample seeds, conditional selection scope and machine quiet caveats. These host drawing measurements are not end-to-end launch or FPS estimates. GPU completion is separately retained when supplied.
