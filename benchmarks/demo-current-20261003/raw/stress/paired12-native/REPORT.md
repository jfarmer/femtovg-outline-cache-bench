# Paired public font proof-sheet stress scene

Designed stress case, not a representative application or a proved globally worst font. No GPU/window/pixel timing; font cost attribution not isolated to hinting. Pressure does not prove eviction.

| Font | Phase | Master us | Final us | Paired ratio [95% CI] | Paired delta us [95% CI] |
|---|---|---:|---:|---|---|
| FleurDeLeah | first_paint (us/frame) | 53253.291 | 15141.209 | 0.2827 [0.2779, 0.2850] | -38219.916 [-38689.812, -37749.499] |
| FleurDeLeah | warm (us/frame) | 150.136 | 140.978 | 0.9386 [0.9295, 0.9673] | -9.267 [-10.708, -4.812] |
| FleurDeLeah | new_size (us/frame) | 53749.123 | 15789.976 | 0.2940 [0.2932, 0.2958] | -37950.130 [-38164.441, -37784.809] |
| FleurDeLeah | return (us/frame) | 211.730 | 193.917 | 0.9028 [0.8674, 0.9742] | -21.021 [-27.791, -5.334] |
| FleurDeLeah | complete_sequence (us/sequence) | 702933.669 | 209136.731 | 0.2976 [0.2965, 0.2985] | -493423.209 [-496066.483, -492459.771] |
| RobotoFlex | first_paint (us/frame) | 2975.667 | 2459.667 | 0.8257 [0.8195, 0.8347] | -514.459 [-538.063, -491.104] |
| RobotoFlex | warm (us/frame) | 155.019 | 145.449 | 0.9480 [0.9145, 0.9551] | -8.037 [-13.496, -6.924] |
| RobotoFlex | new_size (us/frame) | 2886.904 | 2281.556 | 0.7936 [0.7782, 0.8058] | -592.845 [-650.912, -551.358] |
| RobotoFlex | return (us/frame) | 162.500 | 159.438 | 0.9957 [0.9380, 1.0137] | -0.688 [-10.125, +2.229] |
| RobotoFlex | complete_sequence (us/sequence) | 42437.893 | 34380.708 | 0.8137 [0.8015, 0.8237] | -7845.831 [-8535.460, -7414.464] |
| Rye | first_paint (us/frame) | 30934.062 | 9423.188 | 0.3032 [0.3002, 0.3102] | -21569.938 [-21863.834, -21203.500] |
| Rye | warm (us/frame) | 149.914 | 136.665 | 0.9144 [0.9059, 0.9306] | -12.916 [-14.126, -10.179] |
| Rye | new_size (us/frame) | 31262.618 | 9616.625 | 0.3077 [0.3058, 0.3087] | -21546.710 [-21946.502, -21490.147] |
| Rye | return (us/frame) | 215.230 | 175.250 | 0.8427 [0.7961, 0.8712] | -33.208 [-45.668, -25.562] |
| Rye | complete_sequence (us/sequence) | 411007.292 | 129123.247 | 0.3144 [0.3120, 0.3153] | -281005.294 [-285763.376, -279357.023] |
