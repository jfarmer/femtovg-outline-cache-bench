Generic public glyph-run CPU comparison; primary baseline is exact upstream 6a5f15a.

| Features | Workload | Font | Variant | ns/glyph | us/frame | us/sequence | Paired ratio | 95% interval | Paired delta us/frame |
|---|---|---|---|---:|---:|---:|---:|---|---:|
| swash_only | warm_labels_stroke_positive | Arial | master | 86.64 | 29.46 | 29.46 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | warm_labels_stroke_positive | Arial | final | 84.74 | 28.81 | 28.81 | 0.978 | 0.971–0.996 | -0.65 |
| swash_only | warm_labels_stroke_negative | Arial | master | 84.62 | 28.77 | 28.77 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | warm_labels_stroke_negative | Arial | final | 83.94 | 28.54 | 28.54 | 0.993 | 0.970–1.000 | -0.21 |
| swash_only | warm_para_stroke_positive | Arial | master | 50.12 | 92.02 | 92.02 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | warm_para_stroke_positive | Arial | final | 47.53 | 87.27 | 87.27 | 0.947 | 0.946–0.962 | -4.85 |
| swash_only | warm_para_stroke_negative | Arial | master | 49.95 | 91.71 | 91.71 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | warm_para_stroke_negative | Arial | final | 46.98 | 86.27 | 86.27 | 0.940 | 0.933–0.942 | -5.52 |
| swash_only | cold_labels_stroke_positive | Arial | master | 4072.80 | 1384.75 | 1384.75 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | cold_labels_stroke_positive | Arial | final | 4150.74 | 1411.25 | 1411.25 | 1.024 | 1.015–1.032 | +32.81 |
| swash_only | cold_labels_stroke_negative | Arial | master | 3597.55 | 1223.17 | 1223.17 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | cold_labels_stroke_negative | Arial | final | 3588.36 | 1220.04 | 1220.04 | 0.998 | 0.984–1.017 | -2.33 |
| swash_only | cold_para_stroke_positive | Arial | master | 2040.18 | 3745.77 | 3745.77 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | cold_para_stroke_positive | Arial | final | 2040.53 | 3746.42 | 3746.42 | 1.000 | 0.994–1.016 | -1.02 |
| swash_only | cold_para_stroke_negative | Arial | master | 476.03 | 874.00 | 874.00 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | cold_para_stroke_negative | Arial | final | 488.04 | 896.04 | 896.04 | 1.016 | 0.987–1.070 | +13.50 |
| default_swash | warm_labels_stroke_positive | Arial | master | 109.13 | 37.10 | 37.10 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | warm_labels_stroke_positive | Arial | final | 111.83 | 38.02 | 38.02 | 1.024 | 1.016–1.033 | +0.87 |
| default_swash | warm_labels_stroke_negative | Arial | master | 108.58 | 36.92 | 36.92 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | warm_labels_stroke_negative | Arial | final | 111.70 | 37.98 | 37.98 | 1.023 | 1.007–1.050 | +0.83 |
| default_swash | warm_para_stroke_positive | Arial | master | 50.37 | 92.48 | 92.48 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | warm_para_stroke_positive | Arial | final | 49.03 | 90.02 | 90.02 | 0.972 | 0.967–0.986 | -2.62 |
| default_swash | warm_para_stroke_negative | Arial | master | 50.11 | 92.00 | 92.00 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | warm_para_stroke_negative | Arial | final | 48.59 | 89.21 | 89.21 | 0.969 | 0.953–0.977 | -2.85 |
| default_swash | cold_labels_stroke_positive | Arial | master | 4072.12 | 1384.52 | 1384.52 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | cold_labels_stroke_positive | Arial | final | 4069.42 | 1383.60 | 1383.60 | 1.011 | 0.984–1.030 | +15.73 |
| default_swash | cold_labels_stroke_negative | Arial | master | 3471.57 | 1180.33 | 1180.33 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | cold_labels_stroke_negative | Arial | final | 3549.57 | 1206.85 | 1206.85 | 1.008 | 0.996–1.042 | +9.96 |
| default_swash | cold_para_stroke_positive | Arial | master | 2059.41 | 3781.08 | 3781.08 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | cold_para_stroke_positive | Arial | final | 2062.55 | 3786.83 | 3786.83 | 1.002 | 0.990–1.018 | +8.19 |
| default_swash | cold_para_stroke_negative | Arial | master | 475.38 | 872.79 | 872.79 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | cold_para_stroke_negative | Arial | final | 484.75 | 890.00 | 890.00 | 1.017 | 0.982–1.024 | +14.92 |
| default_no_swash | warm_labels_fill_positive | Arial | master | 109.38 | 37.19 | 37.19 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_labels_fill_positive | Arial | final | 110.41 | 37.54 | 37.54 | 1.008 | 0.999–1.016 | +0.31 |
| default_no_swash | warm_labels_fill_negative | Arial | master | 110.11 | 37.44 | 37.44 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_labels_fill_negative | Arial | final | 111.15 | 37.79 | 37.79 | 1.006 | 1.001–1.014 | +0.23 |
| default_no_swash | warm_labels_stroke_positive | Arial | master | 110.30 | 37.50 | 37.50 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_labels_stroke_positive | Arial | final | 110.66 | 37.62 | 37.62 | 0.997 | 0.982–1.015 | -0.10 |
| default_no_swash | warm_labels_stroke_negative | Arial | master | 109.50 | 37.23 | 37.23 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_labels_stroke_negative | Arial | final | 110.97 | 37.73 | 37.73 | 1.011 | 0.996–1.017 | +0.40 |
| default_no_swash | warm_para_fill_positive | Arial | master | 48.19 | 88.48 | 88.48 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_para_fill_positive | Arial | final | 48.55 | 89.15 | 89.15 | 1.015 | 1.000–1.019 | +1.33 |
| default_no_swash | warm_para_fill_negative | Arial | master | 48.34 | 88.75 | 88.75 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_para_fill_negative | Arial | final | 48.84 | 89.67 | 89.67 | 1.008 | 0.998–1.013 | +0.67 |
| default_no_swash | warm_para_stroke_positive | Arial | master | 48.19 | 88.48 | 88.48 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_para_stroke_positive | Arial | final | 48.96 | 89.90 | 89.90 | 1.017 | 0.982–1.022 | +1.52 |
| default_no_swash | warm_para_stroke_negative | Arial | master | 48.41 | 88.88 | 88.88 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | warm_para_stroke_negative | Arial | final | 48.84 | 89.67 | 89.67 | 1.011 | 1.003–1.018 | +0.96 |
| default_no_swash | cold_labels_fill_positive | Arial | master | 4657.73 | 1583.63 | 1583.63 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_labels_fill_positive | Arial | final | 4628.01 | 1573.52 | 1573.52 | 1.004 | 0.985–1.017 | +6.38 |
| default_no_swash | cold_labels_fill_negative | Arial | master | 4125.91 | 1402.81 | 1402.81 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_labels_fill_negative | Arial | final | 3991.18 | 1357.00 | 1357.00 | 0.986 | 0.959–1.004 | -21.52 |
| default_no_swash | cold_labels_stroke_positive | Arial | master | 4098.16 | 1393.38 | 1393.38 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_labels_stroke_positive | Arial | final | 4032.84 | 1371.17 | 1371.17 | 0.987 | 0.970–0.997 | -18.04 |
| default_no_swash | cold_labels_stroke_negative | Arial | master | 3554.53 | 1208.54 | 1208.54 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_labels_stroke_negative | Arial | final | 3508.52 | 1192.90 | 1192.90 | 0.989 | 0.970–1.006 | -13.25 |
| default_no_swash | cold_para_fill_positive | Arial | master | 2347.30 | 4309.65 | 4309.65 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_para_fill_positive | Arial | final | 2348.34 | 4311.54 | 4311.54 | 1.000 | 0.992–1.010 | -1.77 |
| default_no_swash | cold_para_fill_negative | Arial | master | 537.01 | 985.96 | 985.96 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_para_fill_negative | Arial | final | 538.33 | 988.38 | 988.38 | 0.995 | 0.974–1.019 | -5.33 |
| default_no_swash | cold_para_stroke_positive | Arial | master | 2060.11 | 3782.35 | 3782.35 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_para_stroke_positive | Arial | final | 2054.75 | 3772.52 | 3772.52 | 0.996 | 0.982–1.007 | -14.62 |
| default_no_swash | cold_para_stroke_negative | Arial | master | 472.95 | 868.33 | 868.33 | 1.000 | 1.000–1.000 | +0.00 |
| default_no_swash | cold_para_stroke_negative | Arial | final | 477.61 | 876.88 | 876.88 | 1.001 | 0.973–1.030 | +0.54 |

Ratios are paired per process block. 95% percentile bootstrap intervals resample paired blocks (10,000 draws); exploratory, without multiplicity adjustment.
One machine, fixed positive-position glyph runs, release profile, no LTO. These measurements cover warm CPU glyph drawing; they do not measure full application or GPU frame latency.
