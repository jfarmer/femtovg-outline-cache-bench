Warm public glyph-run CPU comparison; primary baseline is exact upstream 6a5f15a.

| Features | Workload | Font | Variant | ns/glyph | us/frame | us/sequence | Paired ratio | 95% interval | Paired delta us/frame |
|---|---|---|---|---:|---:|---:|---:|---|---:|
| swash_only | labels | Arial | master | 85.11 | 28.94 | 28.94 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | labels | Arial | base | 91.24 | 31.02 | 31.02 | 1.071 | 1.045–1.088 | +2.08 |
| swash_only | labels | Arial | final | 83.03 | 28.23 | 28.23 | 0.976 | 0.948–0.985 | -0.71 |
| swash_only | labels | Arial | ordinary-inline | 89.89 | 30.56 | 30.56 | 1.042 | 1.033–1.066 | +1.29 |
| swash_only | labels | RobotoFlex | master | 87.13 | 29.62 | 29.62 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | labels | RobotoFlex | base | 89.95 | 30.58 | 30.58 | 1.046 | 1.037–1.073 | +1.38 |
| swash_only | labels | RobotoFlex | final | 85.05 | 28.92 | 28.92 | 0.968 | 0.956–0.981 | -0.92 |
| swash_only | labels | RobotoFlex | ordinary-inline | 88.66 | 30.15 | 30.15 | 1.043 | 1.025–1.056 | +1.27 |
| swash_only | para | Arial | master | 50.23 | 92.22 | 92.22 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | para | Arial | base | 52.57 | 96.52 | 96.52 | 1.057 | 1.037–1.071 | +5.28 |
| swash_only | para | Arial | final | 45.19 | 82.96 | 82.96 | 0.904 | 0.900–0.912 | -8.94 |
| swash_only | para | Arial | ordinary-inline | 53.65 | 98.50 | 98.50 | 1.075 | 1.066–1.095 | +6.88 |
| swash_only | para | RobotoFlex | master | 51.98 | 95.44 | 95.44 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | para | RobotoFlex | base | 54.01 | 99.15 | 99.15 | 1.051 | 1.033–1.062 | +4.87 |
| swash_only | para | RobotoFlex | final | 46.57 | 85.50 | 85.50 | 0.911 | 0.895–0.921 | -8.32 |
| swash_only | para | RobotoFlex | ordinary-inline | 52.97 | 97.24 | 97.24 | 1.030 | 1.020–1.053 | +2.88 |
| default_swash | labels | Arial | master | 112.01 | 38.08 | 38.08 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | labels | Arial | base | 120.34 | 40.92 | 40.92 | 1.079 | 1.053–1.088 | +3.00 |
| default_swash | labels | Arial | final | 108.58 | 36.92 | 36.92 | 0.974 | 0.958–0.986 | -0.98 |
| default_swash | labels | Arial | ordinary-inline | 118.56 | 40.31 | 40.31 | 1.059 | 1.043–1.070 | +2.23 |
| default_swash | labels | RobotoFlex | master | 120.41 | 40.94 | 40.94 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | labels | RobotoFlex | base | 126.29 | 42.94 | 42.94 | 1.047 | 1.037–1.056 | +1.94 |
| default_swash | labels | RobotoFlex | final | 118.94 | 40.44 | 40.44 | 0.989 | 0.980–0.999 | -0.44 |
| default_swash | labels | RobotoFlex | ordinary-inline | 124.15 | 42.21 | 42.21 | 1.032 | 1.022–1.044 | +1.29 |
| default_swash | para | Arial | master | 49.66 | 91.17 | 91.17 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | para | Arial | base | 53.99 | 99.13 | 99.13 | 1.098 | 1.090–1.107 | +8.77 |
| default_swash | para | Arial | final | 46.33 | 85.06 | 85.06 | 0.939 | 0.935–0.951 | -5.50 |
| default_swash | para | Arial | ordinary-inline | 55.09 | 101.15 | 101.15 | 1.119 | 1.109–1.127 | +10.75 |
| default_swash | para | RobotoFlex | master | 53.21 | 97.69 | 97.69 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | para | RobotoFlex | base | 55.80 | 102.44 | 102.44 | 1.050 | 1.045–1.066 | +4.87 |
| default_swash | para | RobotoFlex | final | 47.19 | 86.64 | 86.64 | 0.891 | 0.886–0.898 | -10.77 |
| default_swash | para | RobotoFlex | ordinary-inline | 55.95 | 102.72 | 102.72 | 1.055 | 1.049–1.073 | +5.27 |

Ratios are paired per process block. 95% percentile bootstrap intervals resample paired blocks (10,000 draws); exploratory, without multiplicity adjustment.
One machine, fixed positive-position glyph runs, release profile, no LTO. These measurements cover warm CPU glyph drawing; they do not measure full application or GPU frame latency.
