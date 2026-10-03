Warm public glyph-run CPU comparison; primary baseline is exact upstream 6a5f15a.

| Features | Workload | Font | Variant | ns/glyph | us/frame | us/sequence | Paired ratio | 95% interval | Paired delta us/frame |
|---|---|---|---|---:|---:|---:|---:|---|---:|
| swash_only | labels | Arial | master | 87.99 | 29.92 | 29.92 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | labels | Arial | base | 97.49 | 33.15 | 33.15 | 1.101 | 1.093–1.119 | +2.98 |
| swash_only | labels | Arial | finalgenericrestore | 89.09 | 30.29 | 30.29 | 1.012 | 0.996–1.029 | +0.36 |
| swash_only | labels | RobotoFlex | master | 91.48 | 31.10 | 31.10 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | labels | RobotoFlex | base | 97.37 | 33.10 | 33.10 | 1.072 | 1.059–1.081 | +2.23 |
| swash_only | labels | RobotoFlex | finalgenericrestore | 89.70 | 30.50 | 30.50 | 0.986 | 0.974–0.991 | -0.44 |
| swash_only | para | Arial | master | 52.05 | 95.56 | 95.56 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | para | Arial | base | 57.42 | 105.43 | 105.43 | 1.104 | 1.090–1.116 | +9.87 |
| swash_only | para | Arial | finalgenericrestore | 48.90 | 89.77 | 89.77 | 0.939 | 0.935–0.943 | -5.76 |
| swash_only | para | RobotoFlex | master | 54.72 | 100.47 | 100.47 | 1.000 | 1.000–1.000 | +0.00 |
| swash_only | para | RobotoFlex | base | 59.24 | 108.76 | 108.76 | 1.086 | 1.081–1.090 | +8.42 |
| swash_only | para | RobotoFlex | finalgenericrestore | 51.59 | 94.71 | 94.71 | 0.955 | 0.950–0.958 | -4.52 |
| default_swash | labels | Arial | master | 115.75 | 39.36 | 39.36 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | labels | Arial | base | 125.55 | 42.69 | 42.69 | 1.083 | 1.076–1.090 | +3.27 |
| default_swash | labels | Arial | finalgenericrestore | 113.30 | 38.52 | 38.52 | 0.978 | 0.967–0.996 | -0.87 |
| default_swash | labels | RobotoFlex | master | 123.90 | 42.13 | 42.13 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | labels | RobotoFlex | base | 130.64 | 44.42 | 44.42 | 1.055 | 1.045–1.059 | +2.31 |
| default_swash | labels | RobotoFlex | finalgenericrestore | 120.47 | 40.96 | 40.96 | 0.965 | 0.961–0.973 | -1.46 |
| default_swash | para | Arial | master | 51.39 | 94.36 | 94.36 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | para | Arial | base | 58.61 | 107.60 | 107.60 | 1.148 | 1.142–1.156 | +13.79 |
| default_swash | para | Arial | finalgenericrestore | 48.81 | 89.61 | 89.61 | 0.952 | 0.944–0.957 | -4.46 |
| default_swash | para | RobotoFlex | master | 56.02 | 102.86 | 102.86 | 1.000 | 1.000–1.000 | +0.00 |
| default_swash | para | RobotoFlex | base | 60.69 | 111.42 | 111.42 | 1.093 | 1.084–1.097 | +9.46 |
| default_swash | para | RobotoFlex | finalgenericrestore | 51.47 | 94.50 | 94.50 | 0.921 | 0.909–0.925 | -8.09 |

Ratios are paired per process block. 95% percentile bootstrap intervals resample paired blocks (10,000 draws); exploratory, without multiplicity adjustment.
One machine, the recorded precomputed glyph runs, release profile, no LTO. These measurements cover CPU glyph drawing and Void flush; they do not measure full application or GPU frame latency.
