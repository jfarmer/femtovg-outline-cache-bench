Generic public glyph-run CPU comparison; primary baseline is exact upstream 6a5f15a.

| Features | Workload | Font | Variant | ns/glyph | us/frame | us/sequence | Paired ratio | 95% interval | Paired delta us/frame |
|---|---|---|---|---:|---:|---:|---:|---|---:|
| swash_only | warm_labels_stroke_positive | Arial | master | 86.21 | 29.31 | 29.31 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | warm_labels_stroke_positive | Arial | finalgenericrestore | 87.69 | 29.81 | 29.81 | 1.019 | 1.004–1.031 | +0.56 |
| swash_only | warm_labels_stroke_negative | Arial | master | 86.15 | 29.29 | 29.29 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | warm_labels_stroke_negative | Arial | finalgenericrestore | 87.56 | 29.77 | 29.77 | 1.013 | 1.008–1.024 | +0.38 |
| swash_only | warm_para_stroke_positive | Arial | master | 50.63 | 92.96 | 92.96 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | warm_para_stroke_positive | Arial | finalgenericrestore | 49.13 | 90.21 | 90.21 | 0.969 | 0.961–0.980 | -2.85 |
| swash_only | warm_para_stroke_negative | Arial | master | 50.27 | 92.29 | 92.29 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | warm_para_stroke_negative | Arial | finalgenericrestore | 48.80 | 89.60 | 89.60 | 0.969 | 0.964–0.980 | -2.92 |
| swash_only | cold_labels_stroke_positive | Arial | master | 4208.82 | 1431.00 | 1431.00 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | cold_labels_stroke_positive | Arial | finalgenericrestore | 4255.45 | 1446.85 | 1446.85 | 1.003 | 0.999–1.023 | +3.62 |
| swash_only | cold_labels_stroke_negative | Arial | master | 3671.20 | 1248.21 | 1248.21 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | cold_labels_stroke_negative | Arial | finalgenericrestore | 3703.24 | 1259.10 | 1259.10 | 1.029 | 0.989–1.038 | +35.40 |
| swash_only | cold_para_stroke_positive | Arial | master | 2081.79 | 3822.17 | 3822.17 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | cold_para_stroke_positive | Arial | finalgenericrestore | 2089.46 | 3836.25 | 3836.25 | 1.005 | 0.991–1.009 | +18.96 |
| swash_only | cold_para_stroke_negative | Arial | master | 493.07 | 905.27 | 905.27 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | cold_para_stroke_negative | Arial | finalgenericrestore | 501.97 | 921.60 | 921.60 | 1.018 | 1.001–1.029 | +16.25 |
| default_swash | warm_labels_stroke_positive | Arial | master | 110.60 | 37.60 | 37.60 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | warm_labels_stroke_positive | Arial | finalgenericrestore | 111.83 | 38.02 | 38.02 | 1.012 | 1.008–1.023 | +0.46 |
| default_swash | warm_labels_stroke_negative | Arial | master | 108.94 | 37.04 | 37.04 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | warm_labels_stroke_negative | Arial | finalgenericrestore | 111.46 | 37.90 | 37.90 | 1.022 | 1.011–1.035 | +0.83 |
| default_swash | warm_para_stroke_positive | Arial | master | 50.91 | 93.46 | 93.46 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | warm_para_stroke_positive | Arial | finalgenericrestore | 50.78 | 93.23 | 93.23 | 0.998 | 0.989–1.007 | -0.15 |
| default_swash | warm_para_stroke_negative | Arial | master | 50.45 | 92.62 | 92.62 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | warm_para_stroke_negative | Arial | finalgenericrestore | 50.25 | 92.25 | 92.25 | 0.997 | 0.987–1.003 | -0.27 |
| default_swash | cold_labels_stroke_positive | Arial | master | 4205.94 | 1430.02 | 1430.02 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | cold_labels_stroke_positive | Arial | finalgenericrestore | 4185.90 | 1423.21 | 1423.21 | 0.998 | 0.991–1.011 | -2.33 |
| default_swash | cold_labels_stroke_negative | Arial | master | 3616.18 | 1229.50 | 1229.50 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | cold_labels_stroke_negative | Arial | finalgenericrestore | 3643.39 | 1238.75 | 1238.75 | 1.006 | 0.994–1.020 | +7.65 |
| default_swash | cold_para_stroke_positive | Arial | master | 2106.44 | 3867.44 | 3867.44 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | cold_para_stroke_positive | Arial | finalgenericrestore | 2101.97 | 3859.21 | 3859.21 | 0.998 | 0.993–1.003 | -7.04 |
| default_swash | cold_para_stroke_negative | Arial | master | 492.22 | 903.71 | 903.71 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | cold_para_stroke_negative | Arial | finalgenericrestore | 490.13 | 899.87 | 899.87 | 1.000 | 0.985–1.012 | -0.02 |
| default_no_swash | warm_labels_fill_positive | Arial | master | 110.60 | 37.60 | 37.60 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_labels_fill_positive | Arial | finalgenericrestore | 110.60 | 37.60 | 37.60 | 1.001 | 0.983–1.010 | +0.02 |
| default_no_swash | warm_labels_fill_negative | Arial | master | 110.29 | 37.50 | 37.50 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_labels_fill_negative | Arial | finalgenericrestore | 109.62 | 37.27 | 37.27 | 0.998 | 0.991–1.005 | -0.08 |
| default_no_swash | warm_labels_stroke_positive | Arial | master | 110.85 | 37.69 | 37.69 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_labels_stroke_positive | Arial | finalgenericrestore | 110.97 | 37.73 | 37.73 | 1.009 | 0.997–1.016 | +0.33 |
| default_no_swash | warm_labels_stroke_negative | Arial | master | 110.23 | 37.48 | 37.48 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_labels_stroke_negative | Arial | finalgenericrestore | 110.47 | 37.56 | 37.56 | 0.999 | 0.993–1.007 | -0.02 |
| default_no_swash | warm_para_fill_positive | Arial | master | 48.61 | 89.25 | 89.25 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_para_fill_positive | Arial | finalgenericrestore | 50.19 | 92.15 | 92.15 | 1.027 | 1.020–1.038 | +2.42 |
| default_no_swash | warm_para_fill_negative | Arial | master | 49.05 | 90.04 | 90.04 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_para_fill_negative | Arial | finalgenericrestore | 49.93 | 91.67 | 91.67 | 1.015 | 1.009–1.024 | +1.31 |
| default_no_swash | warm_para_stroke_positive | Arial | master | 48.64 | 89.31 | 89.31 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_para_stroke_positive | Arial | finalgenericrestore | 50.02 | 91.83 | 91.83 | 1.026 | 1.022–1.035 | +2.35 |
| default_no_swash | warm_para_stroke_negative | Arial | master | 48.66 | 89.33 | 89.33 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_para_stroke_negative | Arial | finalgenericrestore | 49.87 | 91.56 | 91.56 | 1.022 | 1.019–1.029 | +1.96 |
| default_no_swash | cold_labels_fill_positive | Arial | master | 4798.35 | 1631.44 | 1631.44 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_labels_fill_positive | Arial | finalgenericrestore | 4896.07 | 1664.67 | 1664.67 | 1.020 | 1.000–1.046 | +32.19 |
| default_no_swash | cold_labels_fill_negative | Arial | master | 4191.55 | 1425.12 | 1425.12 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_labels_fill_negative | Arial | finalgenericrestore | 4173.03 | 1418.83 | 1418.83 | 0.998 | 0.985–1.012 | -2.31 |
| default_no_swash | cold_labels_stroke_positive | Arial | master | 4234.81 | 1439.83 | 1439.83 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_labels_stroke_positive | Arial | finalgenericrestore | 4196.76 | 1426.90 | 1426.90 | 0.987 | 0.976–0.997 | -18.08 |
| default_no_swash | cold_labels_stroke_negative | Arial | master | 3691.97 | 1255.27 | 1255.27 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_labels_stroke_negative | Arial | finalgenericrestore | 3628.80 | 1233.79 | 1233.79 | 0.981 | 0.965–1.005 | -23.27 |
| default_no_swash | cold_para_fill_positive | Arial | master | 2383.28 | 4375.71 | 4375.71 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_para_fill_positive | Arial | finalgenericrestore | 2374.30 | 4359.21 | 4359.21 | 0.996 | 0.982–1.020 | -15.21 |
| default_no_swash | cold_para_fill_negative | Arial | master | 557.52 | 1023.60 | 1023.60 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_para_fill_negative | Arial | finalgenericrestore | 559.40 | 1027.06 | 1027.06 | 0.999 | 0.980–1.005 | -0.94 |
| default_no_swash | cold_para_stroke_positive | Arial | master | 2113.98 | 3881.27 | 3881.27 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_para_stroke_positive | Arial | finalgenericrestore | 2103.34 | 3861.73 | 3861.73 | 0.997 | 0.988–1.007 | -12.23 |
| default_no_swash | cold_para_stroke_negative | Arial | master | 492.62 | 904.46 | 904.46 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_para_stroke_negative | Arial | finalgenericrestore | 493.43 | 905.94 | 905.94 | 0.997 | 0.990–1.019 | -3.06 |

Ratios are paired per process block. 95% percentile bootstrap intervals resample paired blocks (10,000 draws); exploratory, without multiplicity adjustment.
One machine, the recorded precomputed glyph runs, release profile, no LTO. These measurements cover CPU glyph drawing and Void flush; they do not measure full application or GPU frame latency.
