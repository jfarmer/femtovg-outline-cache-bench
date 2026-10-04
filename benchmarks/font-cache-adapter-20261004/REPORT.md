All values are microseconds of CPU drawing (demo), the complete miss workload (cold), or CPU drawing plus Void flush (stress).
Demo setup/font loading and GPU rendering are excluded. Cold canvas/font setup is excluded.

| Case | Phase | Master | Simple | Adapter | Adapter / Master | Adapter / Simple |
|---|---|---:|---:|---:|---:|---:|
| demo-RobotoFlex | first_paint | 1964.958 | 1921.729 | 1838.874 | -8.34% | -5.07% |
| demo-RobotoFlex | pan | 237.031 | 227.767 | 219.352 | -6.82% | -3.64% |
| demo-RobotoFlex | warm | 234.930 | 226.039 | 227.929 | -3.65% | -0.27% |
| demo-RobotoFlex | zoom_in | 1430.719 | 1406.621 | 1386.837 | -3.54% | -0.08% |
| demo-RobotoFlex | zoom_out | 922.200 | 928.106 | 884.814 | -4.66% | -2.50% |
| demo-RobotoFlex-no-swash | first_paint | 4304.562 | 4235.708 | 4262.937 | -0.47% | -2.43% |
| demo-RobotoFlex-no-swash | pan | 229.877 | 229.277 | 231.315 | -0.82% | +1.72% |
| demo-RobotoFlex-no-swash | warm | 233.088 | 234.220 | 228.824 | -1.18% | -3.46% |
| demo-RobotoFlex-no-swash | zoom_in | 3487.984 | 3519.231 | 3455.734 | -0.22% | -1.54% |
| demo-RobotoFlex-no-swash | zoom_out | 2251.064 | 2273.215 | 2285.425 | -0.03% | -1.22% |
| demo-Rye | first_paint | 6963.230 | 4261.521 | 4287.313 | -38.22% | +1.79% |
| demo-Rye | pan | 236.346 | 227.852 | 229.615 | -3.24% | +0.96% |
| demo-Rye | warm | 231.325 | 221.792 | 224.878 | -2.25% | +2.50% |
| demo-Rye | zoom_in | 6315.530 | 3723.719 | 3665.337 | -42.75% | -0.97% |
| demo-Rye | zoom_out | 4211.403 | 2432.774 | 2422.420 | -42.20% | -0.23% |
| demo-Vollkorn | first_paint | 7367.625 | 5136.021 | 4968.792 | -33.50% | -5.52% |
| demo-Vollkorn | pan | 234.027 | 228.538 | 239.469 | +2.36% | +8.26% |
| demo-Vollkorn | warm | 228.474 | 224.417 | 225.219 | -0.38% | +0.20% |
| demo-Vollkorn | zoom_in | 6395.038 | 4389.373 | 4350.861 | -32.43% | -2.73% |
| demo-Vollkorn | zoom_out | 4225.766 | 2760.686 | 2751.257 | -34.67% | -0.88% |
| grid_unique_sizes-RobotoFlex | all_misses | 6073.791 | 6161.896 | 6175.312 | +2.22% | -0.88% |
| grid_unique_sizes-Vollkorn | all_misses | 48260.125 | 49083.167 | 50111.104 | +2.21% | +0.86% |

Negative percentages mean lower CPU time. Paired block bootstrap intervals are in SUMMARY.json.
Master is frozen upstream 6a5f15a; Simple is the previous measured lower-touch integration; Adapter is the private Font cache adapter. See METADATA.json for exact source and binary identities.
