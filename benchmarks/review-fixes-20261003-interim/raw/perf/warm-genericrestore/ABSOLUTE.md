Paired absolute CPU costs derived from retained process blocks.

| Features | Workload | Font | Variant | Master us/frame | Candidate us/frame | Paired delta us/frame [95% interval] | Master us/sequence | Candidate us/sequence | Paired delta us/sequence [95% interval] |
|---|---|---|---|---:|---:|---|---:|---:|---|
| default_swash | labels | Arial | base | 39.36 | 42.69 | +3.27 [+3.02, +3.48] | 39.36 | 42.69 | +3.27 [+3.02, +3.48] |
| default_swash | labels | Arial | finalgenericrestore | 39.36 | 38.52 | -0.87 [-1.31, -0.14] | 39.36 | 38.52 | -0.87 [-1.31, -0.14] |
| default_swash | labels | RobotoFlex | base | 42.13 | 44.42 | +2.31 [+1.94, +2.50] | 42.13 | 44.42 | +2.31 [+1.94, +2.50] |
| default_swash | labels | RobotoFlex | finalgenericrestore | 42.13 | 40.96 | -1.46 [-1.62, -1.16] | 42.13 | 40.96 | -1.46 [-1.62, -1.16] |
| default_swash | para | Arial | base | 94.36 | 107.60 | +13.79 [+13.48, +14.50] | 94.36 | 107.60 | +13.79 [+13.48, +14.50] |
| default_swash | para | Arial | finalgenericrestore | 94.36 | 89.61 | -4.46 [-5.35, -4.15] | 94.36 | 89.61 | -4.46 [-5.35, -4.15] |
| default_swash | para | RobotoFlex | base | 102.86 | 111.42 | +9.46 [+8.73, +9.75] | 102.86 | 111.42 | +9.46 [+8.73, +9.75] |
| default_swash | para | RobotoFlex | finalgenericrestore | 102.86 | 94.50 | -8.09 [-9.24, -7.73] | 102.86 | 94.50 | -8.09 [-9.24, -7.73] |
| swash_only | labels | Arial | base | 29.92 | 33.15 | +2.98 [+2.86, +3.48] | 29.92 | 33.15 | +2.98 [+2.86, +3.48] |
| swash_only | labels | Arial | finalgenericrestore | 29.92 | 30.29 | +0.36 [-0.11, +0.85] | 29.92 | 30.29 | +0.36 [-0.11, +0.85] |
| swash_only | labels | RobotoFlex | base | 31.10 | 33.10 | +2.23 [+1.79, +2.50] | 31.10 | 33.10 | +2.23 [+1.79, +2.50] |
| swash_only | labels | RobotoFlex | finalgenericrestore | 31.10 | 30.50 | -0.44 [-0.81, -0.29] | 31.10 | 30.50 | -0.44 [-0.81, -0.29] |
| swash_only | para | Arial | base | 95.56 | 105.43 | +9.87 [+8.71, +10.98] | 95.56 | 105.43 | +9.87 [+8.71, +10.98] |
| swash_only | para | Arial | finalgenericrestore | 95.56 | 89.77 | -5.76 [-6.30, -5.37] | 95.56 | 89.77 | -5.76 [-6.30, -5.37] |
| swash_only | para | RobotoFlex | base | 100.47 | 108.76 | +8.42 [+8.23, +8.87] | 100.47 | 108.76 | +8.42 [+8.23, +8.87] |
| swash_only | para | RobotoFlex | finalgenericrestore | 100.47 | 94.71 | -4.52 [-5.00, -4.13] | 100.47 | 94.71 | -4.52 [-5.00, -4.13] |

Paired deltas compare each candidate process with the master process from the same rotating block; therefore the median paired delta need not equal the difference between marginal medians. Intervals resample complete paired blocks (10,000 median percentile bootstrap draws, seed 61432, indices 250/9750); exploratory, without multiplicity correction. Sequence totals are complete controlled sequences or the actual scene phase frame count; single-frame glyph workloads use the same per-frame/sequence value. CPU Canvas/Void only, no GPU or presented-frame timing.
