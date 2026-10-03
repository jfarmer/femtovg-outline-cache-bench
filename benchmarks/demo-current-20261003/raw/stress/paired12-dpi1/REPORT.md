# Paired public font proof-sheet stress scene

Designed stress case, not a representative application or a proved globally worst font. No GPU/window/pixel timing; font cost attribution not isolated to hinting. Pressure does not prove eviction.

| Font | Phase | Master us | Final us | Paired ratio [95% CI] | Paired delta us [95% CI] |
|---|---|---:|---:|---|---|
| FleurDeLeah | first_paint (us/frame) | 89303.959 | 19935.770 | 0.2207 [0.2187, 0.2263] | -69192.458 [-70555.292, -68632.542] |
| FleurDeLeah | warm (us/frame) | 151.109 | 142.631 | 0.9519 [0.9167, 0.9644] | -7.336 [-12.711, -5.293] |
| FleurDeLeah | new_size (us/frame) | 90611.728 | 21685.146 | 0.2390 [0.2385, 0.2404] | -68946.208 [-69473.984, -68087.800] |
| FleurDeLeah | return (us/frame) | 238.021 | 220.562 | 0.9258 [0.8949, 0.9516] | -17.834 [-24.791, -11.229] |
| FleurDeLeah | complete_sequence (us/sequence) | 1181152.520 | 284902.080 | 0.2409 [0.2399, 0.2421] | -895538.915 [-904365.269, -888108.647] |
| RobotoFlex | first_paint (us/frame) | 4550.667 | 3766.479 | 0.8260 [0.8211, 0.8363] | -786.896 [-813.084, -750.896] |
| RobotoFlex | warm (us/frame) | 159.018 | 150.316 | 0.9532 [0.9392, 0.9687] | -7.381 [-9.731, -4.886] |
| RobotoFlex | new_size (us/frame) | 5068.379 | 4245.184 | 0.8348 [0.8305, 0.8383] | -836.358 [-855.007, -810.866] |
| RobotoFlex | return (us/frame) | 200.625 | 187.250 | 0.9420 [0.8846, 0.9809] | -11.166 [-25.063, -3.730] |
| RobotoFlex | complete_sequence (us/sequence) | 70493.065 | 59383.957 | 0.8428 [0.8387, 0.8478] | -10947.941 [-11363.415, -10686.583] |
| Rye | first_paint (us/frame) | 51452.959 | 12771.417 | 0.2482 [0.2446, 0.2534] | -38513.062 [-39175.999, -38079.397] |
| Rye | warm (us/frame) | 151.522 | 139.609 | 0.9219 [0.9089, 0.9390] | -11.761 [-13.974, -9.163] |
| Rye | new_size (us/frame) | 52581.828 | 13799.469 | 0.2616 [0.2607, 0.2652] | -38860.377 [-39190.330, -38292.820] |
| Rye | return (us/frame) | 233.312 | 222.355 | 0.9236 [0.8641, 0.9815] | -17.792 [-33.312, -4.291] |
| Rye | complete_sequence (us/sequence) | 687949.042 | 183040.585 | 0.2656 [0.2639, 0.2685] | -505634.981 [-509973.437, -498261.771] |
