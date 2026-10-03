Absolute first-paint host CPU savings in the unchanged demo, final versus master, DPR2. Positive values save time. Fonts were chosen by an exploratory search, then measured in a separate 12-block confirmation.

| Font | Master | Final | Paired savings (95% CI) | Secondary ratio change | Evidence |
|---|---:|---:|---:|---:|---|
| DiplomataSC-Regular | 6.741 ms | 3.982 ms | +2.759 ms [+2.710, +2.808] | -40.93% | improvement |
| FleurDeLeah-Regular | 6.703 ms | 4.431 ms | +2.272 ms [+2.209, +2.332] | -33.89% | improvement |
| Rye-Regular | 6.422 ms | 3.744 ms | +2.677 ms [+2.617, +2.736] | -41.69% | improvement |
| Vollkorn-Medium | 6.759 ms | 4.488 ms | +2.271 ms [+2.173, +2.386] | -33.60% | improvement |
| WaterBrush-Regular | 7.516 ms | 4.866 ms | +2.650 ms [+2.561, +2.745] | -35.26% | improvement |

| Selected font | Additional savings versus control (95% CI) | Evidence |
|---|---:|---|
| WaterBrush-Regular versus Rye-Regular | -0.027 ms [-0.114, +0.079] | uncertain |
| DiplomataSC-Regular versus Rye-Regular | +0.082 ms [+0.029, +0.143] | larger_savings |
| FleurDeLeah-Regular versus Rye-Regular | -0.405 ms [-0.462, -0.349] | smaller_savings |
| Vollkorn-Medium versus Rye-Regular | -0.407 ms [-0.524, -0.257] | smaller_savings |

All phase/metric and weighted reported-sequence results, including warm costs, uncertain intervals and regressions, remain in [summary.csv](summary.csv). Paired raw-derived process values are in [paired-processes.csv](paired-processes.csv); the independent preflight/order/count audit is [raw-audit.json](raw-audit.json). See [summary.json](summary.json) for estimator definitions, exact resample seeds, conditional selection scope and machine quiet caveats. These host drawing measurements are not end-to-end launch or FPS estimates. GPU completion is separately retained when supplied.
