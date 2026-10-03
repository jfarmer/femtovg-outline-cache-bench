# Provisional eight-block cold reanalysis

explicit post hoc provisional reanalysis; not the planned 12-block primary cold cohort.

Choose the chronologically earliest interrupted finalgenericrestore cold campaign and its first eight complete logical blocks 0 through 7; exclude its partial block 8 and all other campaigns. Never choose or combine records using timing effects.

Used all 1584 records in the complete 66-configuration × 3-variant × 8-block matrix; excluded the 174 records from partial block 8. All font, executable and harness hashes, command arguments, glyph/frame counts, and emitted/stored timing identities passed independent checks. Original campaign files were unchanged.

Paired-block medians and exploratory 95% percentile bootstrap intervals: 10,000 resamples of eight whole paired blocks, seed 61432; endpoints 250/9750. All 198 rows and 66 final-versus-master rows are in RESULT.json.

Controlled sequence costs include every measured frame: singleton 1, two phases 2, distinct sizes 32, distinct normalized variable instances 32, pollution 67 (hot population + 64 pollution frames + return). Costs are compared per complete sequence before calculating paired statistics. The 64-size pollution workload measures pressure and return together; it has no instrumentation proving actual eviction. Roboto Flex natural/one-phase text uses weight 450; the controlled instance sweep uses weights 100 through 875.

Selection was declared after the campaign stopped, before this cold numerical analysis. The original guard checked before configurations, not continuously or after each process; later detected interference neither establishes earlier idle conditions nor invalidates every earlier record. Individual seven-sample values were not emitted. Intervals are exploratory, without multiplicity adjustment, on one machine; CPU glyph drawing and Void flush only, excluding layout and GPU work.

Exploratory final/master ratio intervals: 63 wholly below one, 0 wholly above one, 3 crossing one.

| Features | Workload/font | Frames | Master us/frame | Final us/frame | Paired ratio (95% CI) | Paired delta us/frame (95% CI) | Master us/sequence | Final us/sequence | Paired delta us/sequence (95% CI) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| swash_only | cold_labels_natural/Arial | 1 | 956.500 | 428.208 | 0.4418 [0.4184, 0.5063] | -540.958 [-564.751, -526.250] | 956.500 | 428.208 | -540.958 [-564.751, -526.250] |
| swash_only | cold_labels_natural/RobotoFlex | 1 | 333.917 | 219.250 | 0.6606 [0.5806, 0.7124] | -112.146 [-146.166, -88.375] | 333.917 | 219.250 | -112.146 [-146.166, -88.375] |
| swash_only | cold_labels_natural/Vollkorn | 1 | 3287.729 | 1109.896 | 0.3396 [0.3320, 0.3493] | -2161.792 [-2221.666, -2125.584] | 3287.729 | 1109.896 | -2161.792 [-2221.666, -2125.584] |
| swash_only | cold_labels_natural/PTSans | 1 | 677.958 | 336.083 | 0.4869 [0.4726, 0.5353] | -343.000 [-357.708, -333.918] | 677.958 | 336.083 | -343.000 [-357.708, -333.918] |
| swash_only | cold_labels_onephase/Arial | 1 | 346.438 | 300.167 | 0.8756 [0.8212, 0.9012] | -42.646 [-67.333, -36.208] | 346.438 | 300.167 | -42.646 [-67.333, -36.208] |
| swash_only | cold_labels_onephase/RobotoFlex | 1 | 165.750 | 107.771 | 0.6477 [0.6158, 0.7161] | -57.396 [-67.625, -52.167] | 165.750 | 107.771 | -57.396 [-67.625, -52.167] |
| swash_only | cold_labels_onephase/Vollkorn | 1 | 1059.313 | 954.625 | 0.8992 [0.8769, 0.9272] | -108.208 [-132.041, -76.042] | 1059.313 | 954.625 | -108.208 [-132.041, -76.042] |
| swash_only | cold_labels_onephase/PTSans | 1 | 280.271 | 234.896 | 0.8355 [0.7488, 0.9108] | -46.604 [-70.959, -24.292] | 280.271 | 234.896 | -46.604 [-70.959, -24.292] |
| swash_only | cold_para_natural/Arial | 1 | 2185.521 | 676.750 | 0.3157 [0.3035, 0.3213] | -1507.000 [-1517.999, -1452.916] | 2185.521 | 676.750 | -1507.000 [-1517.999, -1452.916] |
| swash_only | cold_para_natural/RobotoFlex | 1 | 840.938 | 527.605 | 0.6310 [0.6073, 0.6823] | -306.146 [-330.167, -265.625] | 840.938 | 527.605 | -306.146 [-330.167, -265.625] |
| swash_only | cold_para_natural/Vollkorn | 1 | 7679.145 | 1318.292 | 0.1720 [0.1647, 0.1741] | -6381.250 [-6547.042, -6244.751] | 7679.145 | 1318.292 | -6381.250 [-6547.042, -6244.751] |
| swash_only | cold_para_natural/PTSans | 1 | 1639.771 | 575.875 | 0.3556 [0.3417, 0.3655] | -1053.188 [-1095.375, -1025.374] | 1639.771 | 575.875 | -1053.188 [-1095.375, -1025.374] |
| swash_only | cold_para_onephase/Arial | 1 | 325.542 | 284.938 | 0.8606 [0.8448, 0.9309] | -45.625 [-50.249, -25.041] | 325.542 | 284.938 | -45.625 [-50.249, -25.041] |
| swash_only | cold_para_onephase/RobotoFlex | 1 | 208.646 | 142.959 | 0.6883 [0.6026, 0.7044] | -66.688 [-107.541, -58.543] | 208.646 | 142.959 | -66.688 [-107.541, -58.543] |
| swash_only | cold_para_onephase/Vollkorn | 1 | 857.896 | 811.042 | 0.9407 [0.9325, 0.9483] | -51.500 [-57.457, -44.459] | 857.896 | 811.042 | -51.500 [-57.457, -44.459] |
| swash_only | cold_para_onephase/PTSans | 1 | 284.437 | 224.480 | 0.8004 [0.7510, 0.8214] | -57.687 [-71.958, -47.792] | 284.437 | 224.480 | -57.687 [-71.958, -47.792] |
| swash_only | grid_singleton/Arial | 1 | 494.396 | 397.083 | 0.8046 [0.8002, 0.8196] | -94.709 [-98.125, -90.458] | 494.396 | 397.083 | -94.709 [-98.125, -90.458] |
| swash_only | grid_singleton/RobotoFlex | 1 | 217.417 | 124.729 | 0.5518 [0.5380, 0.5990] | -97.438 [-109.625, -81.542] | 217.417 | 124.729 | -97.438 [-109.625, -81.542] |
| swash_only | grid_singleton/Vollkorn | 1 | 1551.458 | 1424.708 | 0.9276 [0.9062, 0.9694] | -109.417 [-146.167, -48.916] | 1551.458 | 1424.708 | -109.417 [-146.167, -48.916] |
| swash_only | grid_singleton/PTSans | 1 | 413.312 | 324.604 | 0.7847 [0.7446, 0.8035] | -91.208 [-110.375, -77.417] | 413.312 | 324.604 | -91.208 [-110.375, -77.417] |
| swash_only | grid_two_phases/Arial | 2 | 429.927 | 251.740 | 0.5842 [0.5619, 0.6594] | -180.854 [-186.188, -153.646] | 859.855 | 503.479 | -361.709 [-372.375, -307.293] |
| swash_only | grid_two_phases/RobotoFlex | 2 | 174.396 | 121.011 | 0.6814 [0.6410, 0.7042] | -56.750 [-76.709, -50.333] | 348.791 | 242.021 | -113.499 [-153.417, -100.666] |
| swash_only | grid_two_phases/Vollkorn | 2 | 1481.979 | 784.052 | 0.5257 [0.5118, 0.5348] | -703.896 [-716.542, -681.875] | 2963.958 | 1568.104 | -1407.792 [-1433.083, -1363.751] |
| swash_only | grid_two_phases/PTSans | 2 | 374.719 | 209.729 | 0.5599 [0.5466, 0.6286] | -162.719 [-170.354, -138.833] | 749.438 | 419.459 | -325.438 [-340.708, -277.666] |
| swash_only | grid_unique_sizes/Arial | 32 | 448.891 | 439.487 | 0.9763 [0.9727, 0.9774] | -10.497 [-12.443, -10.062] | 14364.521 | 14063.583 | -335.896 [-398.167, -322.000] |
| swash_only | grid_unique_sizes/RobotoFlex | 32 | 182.126 | 171.118 | 0.9340 [0.9281, 0.9493] | -12.016 [-13.298, -9.134] | 5828.020 | 5475.792 | -384.520 [-425.541, -292.292] |
| swash_only | grid_unique_sizes/Vollkorn | 32 | 1500.402 | 1475.557 | 0.9870 [0.9786, 0.9912] | -19.488 [-32.319, -12.979] | 48012.854 | 47217.834 | -623.603 [-1034.208, -415.333] |
| swash_only | grid_unique_sizes/PTSans | 32 | 376.917 | 363.124 | 0.9641 [0.9457, 0.9760] | -13.494 [-20.331, -8.956] | 12061.333 | 11619.979 | -431.812 [-650.583, -286.583] |
| swash_only | grid_pollution/Arial | 67 | 467.552 | 452.952 | 0.9659 [0.9579, 0.9708] | -15.789 [-20.110, -13.644] | 31325.979 | 30347.771 | -1057.896 [-1347.374, -914.124] |
| swash_only | grid_pollution/RobotoFlex | 67 | 201.874 | 188.386 | 0.9332 [0.9275, 0.9368] | -13.492 [-14.538, -12.806] | 13525.562 | 12621.855 | -903.958 [-974.041, -858.001] |
| swash_only | grid_pollution/Vollkorn | 67 | 1528.826 | 1488.388 | 0.9737 [0.9672, 0.9765] | -40.227 [-50.521, -35.602] | 102431.334 | 99721.980 | -2695.229 [-3384.916, -2385.333] |
| swash_only | grid_pollution/PTSans | 67 | 394.133 | 376.872 | 0.9538 [0.9490, 0.9612] | -18.254 [-20.306, -15.058] | 26406.938 | 25250.438 | -1223.041 [-1360.500, -1008.917] |
| default_swash | cold_labels_natural/Arial | 1 | 961.771 | 433.562 | 0.4469 [0.4400, 0.4915] | -527.563 [-544.708, -509.291] | 961.771 | 433.562 | -527.563 [-544.708, -509.291] |
| default_swash | cold_labels_natural/RobotoFlex | 1 | 335.000 | 230.562 | 0.6888 [0.6273, 0.7175] | -102.021 [-125.875, -91.750] | 335.000 | 230.562 | -102.021 [-125.875, -91.750] |
| default_swash | cold_labels_natural/Vollkorn | 1 | 3270.708 | 1110.979 | 0.3419 [0.3276, 0.3500] | -2154.583 [-2176.667, -2086.375] | 3270.708 | 1110.979 | -2154.583 [-2176.667, -2086.375] |
| default_swash | cold_labels_natural/PTSans | 1 | 650.230 | 342.416 | 0.5307 [0.5130, 0.5676] | -298.022 [-319.666, -266.958] | 650.230 | 342.416 | -298.022 [-319.666, -266.958] |
| default_swash | cold_labels_onephase/Arial | 1 | 331.917 | 315.458 | 0.9556 [0.8948, 1.0287] | -15.146 [-34.167, +9.042] | 331.917 | 315.458 | -15.146 [-34.167, +9.042] |
| default_swash | cold_labels_onephase/RobotoFlex | 1 | 166.500 | 119.291 | 0.7319 [0.6888, 0.8724] | -45.980 [-52.417, -20.084] | 166.500 | 119.291 | -45.980 [-52.417, -20.084] |
| default_swash | cold_labels_onephase/Vollkorn | 1 | 1005.250 | 985.125 | 0.9766 [0.9513, 0.9998] | -23.396 [-50.709, -0.250] | 1005.250 | 985.125 | -23.396 [-50.709, -0.250] |
| default_swash | cold_labels_onephase/PTSans | 1 | 261.583 | 243.396 | 0.9162 [0.8301, 0.9686] | -21.021 [-46.042, -7.917] | 261.583 | 243.396 | -21.021 [-46.042, -7.917] |
| default_swash | cold_para_natural/Arial | 1 | 2177.333 | 661.125 | 0.3031 [0.2965, 0.3245] | -1493.292 [-1570.750, -1461.542] | 2177.333 | 661.125 | -1493.292 [-1570.750, -1461.542] |
| default_swash | cold_para_natural/RobotoFlex | 1 | 831.021 | 535.167 | 0.6569 [0.6161, 0.7016] | -279.812 [-321.666, -245.125] | 831.021 | 535.167 | -279.812 [-321.666, -245.125] |
| default_swash | cold_para_natural/Vollkorn | 1 | 7660.666 | 1324.459 | 0.1739 [0.1697, 0.1837] | -6279.459 [-6425.959, -6232.875] | 7660.666 | 1324.459 | -6279.459 [-6425.959, -6232.875] |
| default_swash | cold_para_natural/PTSans | 1 | 1651.375 | 588.562 | 0.3602 [0.3374, 0.3711] | -1053.833 [-1130.166, -1014.292] | 1651.375 | 588.562 | -1053.833 [-1130.166, -1014.292] |
| default_swash | cold_para_onephase/Arial | 1 | 316.104 | 286.125 | 0.9120 [0.8753, 1.0149] | -27.333 [-39.708, +4.750] | 316.104 | 286.125 | -27.333 [-39.708, +4.750] |
| default_swash | cold_para_onephase/RobotoFlex | 1 | 195.959 | 146.021 | 0.7494 [0.7272, 0.8022] | -47.604 [-52.958, -41.584] | 195.959 | 146.021 | -47.604 [-52.958, -41.584] |
| default_swash | cold_para_onephase/Vollkorn | 1 | 843.833 | 816.958 | 0.9572 [0.9319, 0.9872] | -37.646 [-56.250, -10.833] | 843.833 | 816.958 | -37.646 [-56.250, -10.833] |
| default_swash | cold_para_onephase/PTSans | 1 | 257.354 | 227.959 | 0.8783 [0.8493, 0.9246] | -31.312 [-40.583, -18.250] | 257.354 | 227.959 | -31.312 [-40.583, -18.250] |
| default_swash | grid_singleton/Arial | 1 | 456.250 | 403.938 | 0.8978 [0.8561, 0.9059] | -47.208 [-68.083, -41.000] | 456.250 | 403.938 | -47.208 [-68.083, -41.000] |
| default_swash | grid_singleton/RobotoFlex | 1 | 189.646 | 127.292 | 0.6998 [0.6573, 0.7323] | -55.354 [-64.333, -50.374] | 189.646 | 127.292 | -55.354 [-64.333, -50.374] |
| default_swash | grid_singleton/Vollkorn | 1 | 1485.604 | 1420.374 | 0.9551 [0.9300, 0.9683] | -66.396 [-109.376, -46.667] | 1485.604 | 1420.374 | -66.396 [-109.376, -46.667] |
| default_swash | grid_singleton/PTSans | 1 | 377.042 | 336.916 | 0.9060 [0.8613, 0.9486] | -34.437 [-53.833, -19.333] | 377.042 | 336.916 | -34.437 [-53.833, -19.333] |
| default_swash | grid_two_phases/Arial | 2 | 419.135 | 259.521 | 0.6154 [0.5654, 0.6435] | -161.969 [-183.375, -143.834] | 838.270 | 519.042 | -323.937 [-366.750, -287.667] |
| default_swash | grid_two_phases/RobotoFlex | 2 | 161.844 | 116.417 | 0.7140 [0.6757, 0.7672] | -46.646 [-57.333, -35.625] | 323.688 | 232.834 | -93.291 [-114.666, -71.249] |
| default_swash | grid_two_phases/Vollkorn | 2 | 1458.646 | 775.781 | 0.5355 [0.5250, 0.5463] | -683.229 [-688.917, -662.729] | 2917.292 | 1551.562 | -1366.458 [-1377.834, -1325.458] |
| default_swash | grid_two_phases/PTSans | 2 | 348.531 | 216.927 | 0.6156 [0.6014, 0.6648] | -131.469 [-138.791, -110.875] | 697.062 | 433.855 | -262.938 [-277.583, -221.750] |
| default_swash | grid_unique_sizes/Arial | 32 | 453.781 | 447.747 | 0.9858 [0.9735, 0.9873] | -6.535 [-12.267, -5.793] | 14521.000 | 14327.917 | -209.124 [-392.541, -185.375] |
| default_swash | grid_unique_sizes/RobotoFlex | 32 | 182.984 | 171.719 | 0.9408 [0.9278, 0.9438] | -10.947 [-13.354, -10.151] | 5855.500 | 5495.020 | -350.291 [-427.334, -324.833] |
| default_swash | grid_unique_sizes/Vollkorn | 32 | 1485.536 | 1486.021 | 0.9947 [0.9924, 1.0107] | -7.876 [-11.435, +15.863] | 47537.146 | 47552.688 | -252.021 [-365.917, +507.625] |
| default_swash | grid_unique_sizes/PTSans | 32 | 378.204 | 366.505 | 0.9639 [0.9580, 0.9765] | -13.712 [-16.654, -8.751] | 12102.541 | 11728.145 | -438.791 [-532.917, -280.041] |
| default_swash | grid_pollution/Arial | 67 | 473.031 | 459.224 | 0.9725 [0.9560, 0.9755] | -12.816 [-20.962, -11.685] | 31693.104 | 30767.979 | -858.645 [-1404.459, -782.917] |
| default_swash | grid_pollution/RobotoFlex | 67 | 202.479 | 191.481 | 0.9450 [0.9319, 0.9483] | -11.185 [-13.924, -10.433] | 13566.105 | 12829.208 | -749.375 [-932.917, -699.043] |
| default_swash | grid_pollution/Vollkorn | 67 | 1519.841 | 1498.042 | 0.9911 [0.9817, 0.9923] | -13.473 [-27.831, -11.537] | 101829.375 | 100368.834 | -902.687 [-1864.667, -772.959] |
| default_swash | grid_pollution/PTSans | 67 | 393.986 | 378.687 | 0.9632 [0.9355, 0.9641] | -14.388 [-26.090, -14.146] | 26397.041 | 25372.021 | -964.021 [-1748.000, -947.749] |
| swash_only | grid_unique_variations/RobotoFlex | 32 | 270.820 | 168.417 | 0.6250 [0.6191, 0.6333] | -101.650 [-103.279, -98.385] | 8666.229 | 5389.333 | -3252.792 [-3304.916, -3148.334] |
| default_swash | grid_unique_variations/RobotoFlex | 32 | 246.713 | 171.491 | 0.6925 [0.6856, 0.7044] | -76.370 [-77.490, -72.905] | 7894.812 | 5487.709 | -2443.854 [-2479.667, -2332.958] |
