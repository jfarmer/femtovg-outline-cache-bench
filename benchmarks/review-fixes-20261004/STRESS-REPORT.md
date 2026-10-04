All values are microseconds of CPU drawing (demo), the complete miss workload (cold), or CPU drawing plus Void flush (stress).
Demo setup/font loading and GPU rendering are excluded. Cold canvas/font setup is excluded.

| Case | Phase | Master | Before | After | After / Master | After / Before |
|---|---|---:|---:|---:|---:|---:|
| stress-FleurDeLeah | complete_sequence | 1240644.269 | 302261.087 | 299713.669 | -75.84% | +0.23% |
| stress-FleurDeLeah | first_paint | 94626.605 | 21631.771 | 21571.625 | -77.14% | +1.02% |
| stress-FleurDeLeah | new_size | 95098.887 | 22774.924 | 22757.016 | -76.13% | -0.08% |
| stress-FleurDeLeah | return | 246.312 | 227.938 | 223.396 | -9.26% | -3.36% |
| stress-FleurDeLeah | warm | 169.715 | 143.477 | 144.015 | -13.25% | -1.44% |

Negative percentages mean lower CPU time. Paired block bootstrap intervals are in SUMMARY.json.
Master is frozen upstream 9d574e0; Before is af989d9; After includes the review fixes. See METADATA.json for exact source and binary identities.
