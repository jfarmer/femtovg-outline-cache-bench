Absolute first-paint host CPU savings in the localized demo, final versus master, DPR2. Positive values save time. Fonts were chosen by an exploratory search, then measured in a separate 12-block confirmation.

| Font | Master | Final | Paired savings (95% CI) | Secondary ratio change | Evidence |
|---|---:|---:|---:|---:|---|
| NanumGothic-ExtraBold | 2.093 ms | 2.013 ms | +0.080 ms [+0.052, +0.105] | -3.81% | improvement |
| NanumMyeongjo-ExtraBold | 2.074 ms | 1.977 ms | +0.097 ms [+0.070, +0.130] | -4.67% | improvement |
| NanumMyeongjo-Regular | 2.059 ms | 2.003 ms | +0.055 ms [+0.019, +0.089] | -2.69% | improvement |

| Selected font | Additional savings versus control (95% CI) | Evidence |
|---|---:|---|
| NanumGothic-ExtraBold versus NanumMyeongjo-Regular | +0.024 ms [-0.018, +0.072] | uncertain |
| NanumMyeongjo-ExtraBold versus NanumMyeongjo-Regular | +0.042 ms [+0.002, +0.083] | larger_savings |

All phase/metric and weighted reported-sequence results, including warm costs, uncertain intervals and regressions, remain in [summary.csv](summary.csv). Paired raw-derived process values are in [paired-processes.csv](paired-processes.csv); the independent preflight/order/count audit is [raw-audit.json](raw-audit.json). See [summary.json](summary.json) for estimator definitions, exact resample seeds, conditional selection scope and machine quiet caveats. These host drawing measurements are not end-to-end launch or FPS estimates. GPU completion is separately retained when supplied.
