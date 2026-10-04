All times are milliseconds of CPU draw + flush with the Void renderer, at DPI 1.
The first four phases report time per frame. Sequence44 reports the complete weighted 44-frame total.

| Font | Phase | Master | Full | Simple | Simple / Master | Simple / Full |
|---|---|---:|---:|---:|---:|---:|
| FleurDeLeah | first_paint | 90.256 | 20.183 | 20.504 | -77.30% | +2.25% |
| FleurDeLeah | new_size | 91.617 | 21.734 | 21.740 | -76.14% | -0.11% |
| FleurDeLeah | warm | 0.154 | 0.144 | 0.139 | -9.86% | -3.58% |
| FleurDeLeah | return | 0.237 | 0.220 | 0.214 | -9.78% | -2.35% |
| FleurDeLeah | sequence44 | 1194.589 | 285.742 | 286.643 | -75.98% | +0.00% |
| RobotoFlex | first_paint | 4.705 | 3.966 | 4.001 | -15.14% | -0.01% |
| RobotoFlex | new_size | 5.101 | 4.207 | 4.302 | -16.12% | +1.25% |
| RobotoFlex | warm | 0.166 | 0.159 | 0.146 | -12.56% | -8.42% |
| RobotoFlex | return | 0.205 | 0.179 | 0.197 | -6.10% | +7.45% |
| RobotoFlex | sequence44 | 71.033 | 59.390 | 60.169 | -15.80% | +0.59% |
| Rye | first_paint | 52.129 | 13.078 | 13.380 | -74.33% | +2.24% |
| Rye | new_size | 52.772 | 13.767 | 13.926 | -73.60% | +0.94% |
| Rye | warm | 0.154 | 0.145 | 0.140 | -7.64% | -3.22% |
| Rye | return | 0.227 | 0.216 | 0.210 | -6.54% | -0.26% |
| Rye | sequence44 | 689.915 | 182.903 | 184.764 | -73.20% | +0.95% |

Source/binary identities are in METADATA.json; paired block-bootstrap intervals are in SUMMARY.json.
Actual shaped glyph counts and viewport dimensions match across all three versions and all accepted blocks; see SCENE_COUNTS.json.
