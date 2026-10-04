All values are microseconds of CPU drawing (demo), the complete miss workload (cold), or CPU drawing plus Void flush (stress).
Demo setup/font loading and GPU rendering are excluded. Cold canvas/font setup is excluded.

| Case | Phase | Master | Before | After | After / Master | After / Before |
|---|---|---:|---:|---:|---:|---:|
| demo-RobotoFlex | first_paint | 1711.417 | 1721.812 | 1711.521 | -0.24% | +3.80% |
| demo-RobotoFlex | pan | 226.590 | 222.240 | 224.783 | -0.60% | +0.63% |
| demo-RobotoFlex | warm | 229.799 | 222.749 | 227.709 | +0.24% | +1.65% |
| demo-RobotoFlex | zoom_in | 1390.865 | 1364.922 | 1375.988 | -2.25% | -1.55% |
| demo-RobotoFlex | zoom_out | 915.674 | 869.910 | 885.990 | -3.05% | +1.21% |
| demo-RobotoFlex-no-swash | first_paint | 4216.833 | 4388.646 | 4059.250 | -5.24% | -6.29% |
| demo-RobotoFlex-no-swash | pan | 229.733 | 230.969 | 229.817 | +0.14% | -0.12% |
| demo-RobotoFlex-no-swash | warm | 234.295 | 230.962 | 228.140 | -2.77% | +0.29% |
| demo-RobotoFlex-no-swash | zoom_in | 3428.293 | 3456.005 | 3424.845 | -0.12% | -0.28% |
| demo-RobotoFlex-no-swash | zoom_out | 2308.125 | 2282.727 | 2272.351 | -1.34% | +0.05% |
| demo-Rye | first_paint | 7003.812 | 4268.688 | 4287.521 | -38.65% | +0.89% |
| demo-Rye | pan | 233.669 | 229.342 | 228.240 | -2.66% | -0.68% |
| demo-Rye | warm | 228.333 | 221.341 | 220.173 | -3.56% | -0.53% |
| demo-Rye | zoom_in | 6282.655 | 3628.875 | 3636.708 | -42.33% | +0.52% |
| demo-Rye | zoom_out | 4147.418 | 2374.866 | 2432.500 | -41.19% | +2.55% |
| demo-Vollkorn | first_paint | 7170.500 | 4996.209 | 4982.542 | -31.35% | -2.94% |
| demo-Vollkorn | pan | 225.987 | 232.925 | 228.123 | +2.02% | -2.23% |
| demo-Vollkorn | warm | 226.110 | 222.801 | 222.042 | -1.09% | +0.45% |
| demo-Vollkorn | zoom_in | 6313.696 | 4206.080 | 4195.969 | -33.64% | -0.35% |
| demo-Vollkorn | zoom_out | 4150.293 | 2661.957 | 2670.955 | -35.61% | -0.02% |
| grid_unique_sizes-RobotoFlex | all_misses | 5997.688 | 6160.604 | 6178.480 | +3.27% | +0.75% |
| grid_unique_sizes-Vollkorn | all_misses | 48637.416 | 48806.312 | 49033.521 | +0.48% | +0.37% |

Negative percentages mean lower CPU time. Paired block bootstrap intervals are in SUMMARY.json.
Master is frozen upstream 9d574e0; Before is af989d9; After includes the review fixes. See METADATA.json for exact source and binary identities.
