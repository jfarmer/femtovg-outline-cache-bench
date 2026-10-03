# Independently recomputed absolute costs

All final candidate rows are retained. Confidence intervals are exploratory paired-block percentile bootstraps; a positive point estimate whose interval crosses zero is inconclusive.

| Suite/features | Workload/font | Master us/frame | Final us/frame | Paired ratio | Paired delta us/frame (95% CI) | Paired delta us/sequence (95% CI) |
|---|---|---:|---:|---:|---:|---:|
| warm/swash_only | labels/Arial | 29.917 | 30.292 | 1.01185 | +0.355 [-0.105, +0.853] | +0.355 [-0.105, +0.853] |
| warm/swash_only | labels/RobotoFlex | 31.103 | 30.500 | 0.98580 | -0.437 [-0.813, -0.291] | -0.437 [-0.813, -0.291] |
| warm/swash_only | para/Arial | 95.564 | 89.771 | 0.93897 | -5.756 [-6.297, -5.370] | -5.756 [-6.297, -5.370] |
| warm/swash_only | para/RobotoFlex | 100.466 | 94.710 | 0.95500 | -4.517 [-5.003, -4.131] | -4.517 [-5.003, -4.131] |
| warm/default_swash | labels/Arial | 39.355 | 38.520 | 0.97794 | -0.874 [-1.312, -0.145] | -0.874 [-1.312, -0.145] |
| warm/default_swash | labels/RobotoFlex | 42.126 | 40.958 | 0.96527 | -1.459 [-1.624, -1.165] | -1.459 [-1.624, -1.165] |
| warm/default_swash | para/Arial | 94.361 | 89.606 | 0.95210 | -4.461 [-5.352, -4.149] | -4.461 [-5.352, -4.149] |
| warm/default_swash | para/RobotoFlex | 102.862 | 94.499 | 0.92051 | -8.088 [-9.235, -7.730] | -8.088 [-9.235, -7.730] |
| generic/swash_only | warm_labels_stroke_positive/Arial | 29.312 | 29.813 | 1.01923 | +0.562 [+0.125, +0.896] | +0.562 [+0.125, +0.896] |
| generic/swash_only | warm_labels_stroke_negative/Arial | 29.291 | 29.771 | 1.01271 | +0.375 [+0.251, +0.708] | +0.375 [+0.251, +0.708] |
| generic/swash_only | warm_para_stroke_positive/Arial | 92.959 | 90.208 | 0.96928 | -2.854 [-3.625, -1.855] | -2.854 [-3.625, -1.855] |
| generic/swash_only | warm_para_stroke_negative/Arial | 92.291 | 89.604 | 0.96865 | -2.917 [-3.312, -1.812] | -2.917 [-3.312, -1.812] |
| generic/swash_only | cold_labels_stroke_positive/Arial | 1431.000 | 1446.854 | 1.00255 | +3.625 [-1.939, +32.417] | +3.625 [-1.939, +32.417] |
| generic/swash_only | cold_labels_stroke_negative/Arial | 1248.208 | 1259.104 | 1.02866 | +35.396 [-13.395, +46.875] | +35.396 [-13.395, +46.875] |
| generic/swash_only | cold_para_stroke_positive/Arial | 3822.167 | 3836.250 | 1.00500 | +18.958 [-33.250, +32.875] | +18.958 [-33.250, +32.875] |
| generic/swash_only | cold_para_stroke_negative/Arial | 905.271 | 921.604 | 1.01813 | +16.250 [+0.938, +26.354] | +16.250 [+0.938, +26.354] |
| generic/default_swash | warm_labels_stroke_positive/Arial | 37.604 | 38.020 | 1.01228 | +0.458 [+0.292, +0.854] | +0.458 [+0.292, +0.854] |
| generic/default_swash | warm_labels_stroke_negative/Arial | 37.041 | 37.896 | 1.02212 | +0.834 [+0.416, +1.292] | +0.834 [+0.416, +1.292] |
| generic/default_swash | warm_para_stroke_positive/Arial | 93.459 | 93.229 | 0.99833 | -0.146 [-1.062, +0.605] | -0.146 [-1.062, +0.605] |
| generic/default_swash | warm_para_stroke_negative/Arial | 92.625 | 92.250 | 0.99712 | -0.270 [-1.188, +0.249] | -0.270 [-1.188, +0.249] |
| generic/default_swash | cold_labels_stroke_positive/Arial | 1430.021 | 1423.208 | 0.99836 | -2.333 [-13.000, +15.646] | -2.333 [-13.000, +15.646] |
| generic/default_swash | cold_labels_stroke_negative/Arial | 1229.501 | 1238.750 | 1.00616 | +7.646 [-7.146, +23.833] | +7.646 [-7.146, +23.833] |
| generic/default_swash | cold_para_stroke_positive/Arial | 3867.438 | 3859.208 | 0.99820 | -7.042 [-26.729, +10.833] | -7.042 [-26.729, +10.833] |
| generic/default_swash | cold_para_stroke_negative/Arial | 903.708 | 899.875 | 0.99996 | -0.021 [-13.188, +11.063] | -0.021 [-13.188, +11.063] |
| generic/default_no_swash | warm_labels_fill_positive/Arial | 37.604 | 37.604 | 1.00055 | +0.021 [-0.645, +0.375] | +0.021 [-0.645, +0.375] |
| generic/default_no_swash | warm_labels_fill_negative/Arial | 37.499 | 37.270 | 0.99774 | -0.084 [-0.355, +0.168] | -0.084 [-0.355, +0.168] |
| generic/default_no_swash | warm_labels_stroke_positive/Arial | 37.688 | 37.729 | 1.00882 | +0.333 [-0.125, +0.603] | +0.333 [-0.125, +0.603] |
| generic/default_no_swash | warm_labels_stroke_negative/Arial | 37.480 | 37.562 | 0.99945 | -0.021 [-0.250, +0.250] | -0.021 [-0.250, +0.250] |
| generic/default_no_swash | warm_para_fill_positive/Arial | 89.251 | 92.146 | 1.02680 | +2.416 [+1.834, +3.355] | +2.416 [+1.834, +3.355] |
| generic/default_no_swash | warm_para_fill_negative/Arial | 90.041 | 91.667 | 1.01455 | +1.313 [+0.813, +2.166] | +1.313 [+0.813, +2.166] |
| generic/default_no_swash | warm_para_stroke_positive/Arial | 89.312 | 91.834 | 1.02633 | +2.355 [+1.959, +3.083] | +2.355 [+1.959, +3.083] |
| generic/default_no_swash | warm_para_stroke_negative/Arial | 89.334 | 91.562 | 1.02188 | +1.957 [+1.688, +2.562] | +1.957 [+1.688, +2.562] |
| generic/default_no_swash | cold_labels_fill_positive/Arial | 1631.438 | 1664.667 | 1.01974 | +32.188 [-0.416, +73.792] | +32.188 [-0.416, +73.792] |
| generic/default_no_swash | cold_labels_fill_negative/Arial | 1425.125 | 1418.833 | 0.99837 | -2.312 [-21.834, +16.334] | -2.312 [-21.834, +16.334] |
| generic/default_no_swash | cold_labels_stroke_positive/Arial | 1439.833 | 1426.896 | 0.98739 | -18.084 [-35.375, -3.896] | -18.084 [-35.375, -3.896] |
| generic/default_no_swash | cold_labels_stroke_negative/Arial | 1255.271 | 1233.792 | 0.98137 | -23.271 [-44.625, +6.584] | -23.271 [-44.625, +6.584] |
| generic/default_no_swash | cold_para_fill_positive/Arial | 4375.708 | 4359.208 | 0.99650 | -15.209 [-78.750, +87.916] | -15.209 [-78.750, +87.916] |
| generic/default_no_swash | cold_para_fill_negative/Arial | 1023.604 | 1027.062 | 0.99908 | -0.938 [-20.938, +5.271] | -0.938 [-20.938, +5.271] |
| generic/default_no_swash | cold_para_stroke_positive/Arial | 3881.271 | 3861.729 | 0.99685 | -12.229 [-47.229, +28.500] | -12.229 [-47.229, +28.500] |
| generic/default_no_swash | cold_para_stroke_negative/Arial | 904.458 | 905.938 | 0.99660 | -3.062 [-9.209, +17.229] | -3.062 [-9.209, +17.229] |
