All values are microseconds of CPU drawing (demo) or the complete miss workload (cold).
Demo setup/font loading and GPU rendering are excluded. Cold canvas/font setup is excluded.

| Case | Phase | Master | Full | Simple | Simple / Master | Simple / Full |
|---|---|---:|---:|---:|---:|---:|
| demo-RobotoFlex | first_paint | 1802.229 | 1681.354 | 1743.958 | -3.30% | +2.49% |
| demo-RobotoFlex | pan | 218.758 | 217.156 | 215.811 | -0.76% | -0.46% |
| demo-RobotoFlex | warm | 218.019 | 215.895 | 214.895 | -1.42% | -0.39% |
| demo-RobotoFlex | zoom_in | 1332.064 | 1309.757 | 1299.978 | -2.41% | -0.84% |
| demo-RobotoFlex | zoom_out | 873.703 | 846.675 | 844.998 | -4.19% | -0.36% |
| demo-RobotoFlex-no-swash | first_paint | 4181.062 | 3968.667 | 3906.438 | -6.14% | -2.10% |
| demo-RobotoFlex-no-swash | pan | 221.381 | 221.971 | 222.388 | +0.55% | -0.88% |
| demo-RobotoFlex-no-swash | warm | 220.500 | 222.892 | 223.015 | +2.25% | -0.07% |
| demo-RobotoFlex-no-swash | zoom_in | 3331.017 | 3345.858 | 3309.220 | -0.04% | -1.25% |
| demo-RobotoFlex-no-swash | zoom_out | 2200.800 | 2211.575 | 2202.087 | +0.26% | -0.33% |
| demo-Rye | first_paint | 6787.645 | 4153.521 | 4077.688 | -39.79% | +2.06% |
| demo-Rye | pan | 222.242 | 223.829 | 219.548 | -2.01% | -1.32% |
| demo-Rye | warm | 217.719 | 218.213 | 210.701 | -3.48% | -3.36% |
| demo-Rye | zoom_in | 6104.281 | 3448.691 | 3480.906 | -42.93% | +0.72% |
| demo-Rye | zoom_out | 4014.891 | 2292.368 | 2310.913 | -42.67% | +0.91% |
| demo-Vollkorn | first_paint | 6919.146 | 4841.062 | 4874.812 | -29.38% | +0.36% |
| demo-Vollkorn | pan | 220.946 | 222.702 | 213.883 | -1.06% | -3.01% |
| demo-Vollkorn | warm | 216.862 | 215.404 | 210.813 | -2.21% | -1.12% |
| demo-Vollkorn | zoom_in | 6179.399 | 4032.066 | 4063.967 | -34.44% | +0.51% |
| demo-Vollkorn | zoom_out | 4046.457 | 2550.096 | 2572.899 | -36.45% | +0.44% |
| grid_singleton-RobotoFlex | all_misses | 187.916 | 138.853 | 156.146 | -17.35% | +13.76% |
| grid_singleton-Vollkorn | all_misses | 1491.792 | 1462.042 | 1486.375 | -2.02% | +1.78% |
| grid_unique_sizes-RobotoFlex | all_misses | 5694.604 | 5329.291 | 5871.187 | +3.27% | +10.66% |
| grid_unique_sizes-Vollkorn | all_misses | 46609.395 | 46566.938 | 47103.041 | +1.38% | +1.11% |

Negative percentages mean lower CPU time. Paired block bootstrap intervals are in SUMMARY.json.
Comparisons are an engineering experiment between three exact snapshots; see METADATA.json for source and binary identities.
