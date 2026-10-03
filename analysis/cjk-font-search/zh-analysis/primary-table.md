Absolute first-paint host CPU savings in the localized demo, final versus master, DPR2. Positive values save time. Fonts were chosen by an exploratory search, then measured in a separate 12-block confirmation.

| Font | Master | Final | Paired savings (95% CI) | Secondary ratio change | Evidence |
|---|---:|---:|---:|---:|---|
| BabelStoneHan | 1.896 ms | 1.896 ms | +0.001 ms [-0.018, +0.016] | -0.04% | uncertain |
| NotoSansSC-VF | 2.899 ms | 2.740 ms | +0.159 ms [+0.102, +0.210] | -5.50% | improvement |
| NotoSerifSC-VF | 6.864 ms | 6.636 ms | +0.228 ms [+0.169, +0.288] | -3.32% | improvement |

| Selected font | Additional savings versus control (95% CI) | Evidence |
|---|---:|---|
| BabelStoneHan versus NotoSansSC-VF | -0.159 ms [-0.217, -0.098] | smaller_savings |
| NotoSerifSC-VF versus NotoSansSC-VF | +0.069 ms [-0.025, +0.178] | uncertain |

All phase/metric and weighted reported-sequence results, including warm costs, uncertain intervals and regressions, remain in [summary.csv](summary.csv). Paired raw-derived process values are in [paired-processes.csv](paired-processes.csv); the independent preflight/order/count audit is [raw-audit.json](raw-audit.json). See [summary.json](summary.json) for estimator definitions, exact resample seeds, conditional selection scope and machine quiet caveats. These host drawing measurements are not end-to-end launch or FPS estimates. GPU completion is separately retained when supplied.
