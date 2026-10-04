All values are microseconds of CPU drawing (demo), the complete miss workload (cold), or CPU drawing plus Void flush (stress).
Demo setup/font loading and GPU rendering are excluded. Cold canvas/font setup is excluded.

| Case | Phase | Master | Before | After | After / Master | After / Before |
|---|---|---:|---:|---:|---:|---:|
| demo-RobotoFlex | first_paint | 1831.979 | 1784.687 | 1766.583 | -2.76% | +0.20% |
| demo-RobotoFlex | pan | 223.956 | 219.827 | 221.185 | -1.73% | -0.97% |
| demo-RobotoFlex | warm | 224.311 | 220.901 | 216.928 | -3.12% | -1.10% |
| demo-RobotoFlex | zoom_in | 1351.368 | 1313.438 | 1309.853 | -3.03% | -0.08% |
| demo-RobotoFlex | zoom_out | 887.930 | 853.342 | 849.807 | -3.17% | -0.32% |
| demo-RobotoFlex-no-swash | first_paint | 4116.292 | 3978.104 | 3985.146 | -2.89% | -0.60% |
| demo-RobotoFlex-no-swash | pan | 225.106 | 224.562 | 224.133 | -0.28% | -0.36% |
| demo-RobotoFlex-no-swash | warm | 221.548 | 223.264 | 229.376 | +1.31% | -0.26% |
| demo-RobotoFlex-no-swash | zoom_in | 3356.309 | 3360.222 | 3354.880 | -0.27% | -0.60% |
| demo-RobotoFlex-no-swash | zoom_out | 2211.458 | 2232.852 | 2221.207 | +0.40% | -0.67% |
| demo-Rye | first_paint | 7012.979 | 4230.896 | 4242.416 | -39.21% | +0.27% |
| demo-Rye | pan | 225.989 | 224.846 | 221.746 | -1.57% | -0.86% |
| demo-Rye | warm | 221.265 | 214.563 | 214.569 | -2.11% | +0.34% |
| demo-Rye | zoom_in | 6128.238 | 3538.637 | 3517.608 | -42.40% | -0.60% |
| demo-Rye | zoom_out | 4069.444 | 2332.101 | 2349.823 | -41.94% | +0.81% |
| demo-Vollkorn | first_paint | 7200.604 | 5001.541 | 5096.938 | -28.41% | +1.24% |
| demo-Vollkorn | pan | 218.013 | 229.946 | 220.825 | +0.35% | -1.24% |
| demo-Vollkorn | warm | 221.401 | 215.149 | 215.541 | -3.14% | +0.19% |
| demo-Vollkorn | zoom_in | 6408.602 | 4088.030 | 4104.526 | -35.57% | -0.17% |
| demo-Vollkorn | zoom_out | 4189.029 | 2585.736 | 2624.139 | -37.05% | +0.62% |
| grid_unique_sizes-RobotoFlex | all_misses | 5894.625 | 5984.208 | 5962.438 | +1.21% | -1.48% |
| grid_unique_sizes-Vollkorn | all_misses | 47702.812 | 47883.209 | 47695.270 | -0.35% | -0.90% |
| stress-FleurDeLeah | complete_sequence | 1257524.647 | 303075.334 | 301262.000 | -76.08% | -0.67% |
| stress-FleurDeLeah | first_paint | 94840.791 | 20822.396 | 21430.438 | -77.39% | +1.51% |
| stress-FleurDeLeah | new_size | 96495.405 | 23157.601 | 22848.866 | -76.23% | -1.03% |
| stress-FleurDeLeah | return | 247.042 | 213.896 | 226.250 | -6.27% | +2.68% |
| stress-FleurDeLeah | warm | 162.469 | 143.833 | 145.695 | -11.42% | +3.74% |

Negative percentages mean lower CPU time. Paired block bootstrap intervals are in SUMMARY.json.
Master is frozen upstream 9d574e0; Before is committed cache branch 907bb37; After is the frozen working tree with the miss fast path. See METADATA.json for exact source and binary identities.
