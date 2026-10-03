Native CJK/Hangul screening results
==================================

The independent audit passed all 9,600 rows from 30 successful processes
across 4 campaigns. Rejected launches retained: 0. Every process
retained twenty cases, four trials, four balanced kernels, and twenty repeats.
Live source, build records, executable hashes, dependency graph,
lockfile, fonts, counts, native exact-proof digests, timing arithmetic, and
kernel order were checked. The native untimed assertions prove exact points,
verbs, and ten-phase alpha images; this CSV audit does not reconstruct pixels.

The values below are microseconds per glyph at DPR2: first take each case's
median across its four trials, then take the median of five logical sizes
(11, 12, 14, 15, 16). Maximum shows the largest single size median in that
profile. Corpora differ between languages; units are comparable, characters
are not matched. These are exploratory ranking kernels, without confidence
intervals or predicted application gains. Full DPR1 and per-size results
remain in the independent JSON audit.

Rye remains the most expensive retained candidate by a wide margin. Its
English-demo outline cost is 20.049 µs/glyph, versus 2.521 for the strongest
Korean profile and 0.603 for the largest Chinese CJK94 profile. The large
Chinese fonts mostly spend time rasterizing the retained geometry, a step
the outline cache still performs. The million-byte Nanum program totals
describe their entire Hangul repertoire; they did not produce more expensive
per-glyph VM work than Rye in these fixed ordinary UI corpora.

Actual-demo text profiles

| Screen | Font | Profile | Hinted outline | Unhinted outline | Native render | Geometry reuse | Potential avoided | Maximum outline (logical size) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| english | Rye-Regular | demo_unique | 20.049 | 0.476 | 22.831 | 2.656 | 20.435 | 20.727 (14) |
| english | Vollkorn-Medium | demo_unique | 15.253 | 0.270 | 16.814 | 1.198 | 15.500 | 15.676 (16) |
| ko | NanumGothic-ExtraBold | cjk_demo_unique | 2.521 | 0.354 | 4.147 | 1.630 | 2.608 | 2.716 (14) |
| ko | NanumMyeongjo-Regular | cjk_demo_unique | 2.503 | 0.422 | 4.693 | 2.213 | 2.629 | 2.881 (14) |
| ko | NanumMyeongjo-ExtraBold | cjk_demo_unique | 2.487 | 0.478 | 4.977 | 2.886 | 2.559 | 2.917 (14) |
| ko | NanumGothic-Regular | cjk_demo_unique | 2.428 | 0.343 | 3.987 | 1.644 | 2.562 | 2.692 (14) |
| ko | NanumMyeongjo-Bold | cjk_demo_unique | 2.370 | 0.452 | 4.756 | 2.496 | 2.593 | 2.859 (14) |
| english | NanumMyeongjo-Regular | demo_unique | 1.707 | 0.274 | 2.920 | 1.129 | 1.791 | 1.766 (16) |
| english | NanumMyeongjo-Bold | demo_unique | 1.689 | 0.268 | 3.120 | 1.230 | 1.771 | 1.965 (15) |
| english | NanumMyeongjo-ExtraBold | demo_unique | 1.511 | 0.278 | 2.831 | 1.216 | 1.593 | 1.570 (15) |
| english | NanumGothic-ExtraBold | demo_unique | 1.295 | 0.240 | 2.391 | 1.009 | 1.332 | 1.630 (12) |
| english | NanumGothic-Regular | demo_unique | 1.237 | 0.228 | 2.437 | 0.983 | 1.347 | 1.483 (12) |
| ko | NanumGothicCoding-Regular | cjk_demo_unique | 1.126 | 0.367 | 2.762 | 1.536 | 1.235 | 1.272 (14) |
| ko | D2Coding-Regular | cjk_demo_unique | 0.954 | 0.224 | 2.112 | 1.141 | 0.988 | 1.058 (14) |
| english | WenQuanYiMicroHei-face0 | demo_unique | 0.753 | 0.230 | 1.683 | 0.902 | 0.781 | 0.834 (14) |
| english | NanumGothicCoding-Regular | demo_unique | 0.677 | 0.255 | 1.650 | 0.980 | 0.711 | 0.727 (12) |
| english | D2Coding-Regular | demo_unique | 0.587 | 0.195 | 1.419 | 0.807 | 0.637 | 0.616 (12) |
| zh | BabelStoneHan | cjk_demo_unique | 0.525 | 0.503 | 4.270 | 3.752 | 0.519 | 0.665 (15) |
| zh | NotoSerifSC-VF | cjk_demo_unique | 0.438 | 0.446 | 3.553 | 3.132 | 0.421 | 0.544 (15) |
| zh | NotoSansSC-VF | cjk_demo_unique | 0.340 | 0.337 | 2.554 | 2.235 | 0.329 | 0.419 (15) |
| zh | WenQuanYiMicroHei-face0 | cjk_demo_unique | 0.334 | 0.294 | 2.258 | 1.785 | 0.430 | 0.785 (12) |
| english | NotoSerifSC-VF | demo_unique | 0.234 | 0.236 | 1.474 | 1.258 | 0.224 | 0.263 (15) |
| english | BabelStoneHan | demo_unique | 0.207 | 0.225 | 1.194 | 0.975 | 0.219 | 0.222 (15) |
| english | NotoSansSC-VF | demo_unique | 0.194 | 0.190 | 1.169 | 0.890 | 0.235 | 0.214 (12) |

Synthetic pure-CJK profiles

| Screen | Font | Profile | Hinted outline | Unhinted outline | Native render | Geometry reuse | Potential avoided | Maximum outline (logical size) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| zh-pure-ui | BabelStoneHan | cjk94 | 0.603 | 0.614 | 5.931 | 5.011 | 0.749 | 0.623 (14) |
| zh-pure-ui | BabelStoneHan | pure_cjk_ui_unique | 0.561 | 0.558 | 4.869 | 4.568 | 0.326 | 0.570 (16) |
| zh-pure-ui | NotoSerifSC-VF | cjk94 | 0.496 | 0.501 | 5.051 | 4.554 | 0.464 | 0.501 (16) |
| zh-pure-ui | NotoSerifSC-VF | pure_cjk_ui_unique | 0.475 | 0.478 | 3.777 | 3.567 | 0.289 | 0.547 (15) |
| zh-pure-ui | NotoSansSC-VF | cjk94 | 0.380 | 0.380 | 3.404 | 3.052 | 0.386 | 0.381 (15) |
| zh-pure-ui | NotoSansSC-VF | pure_cjk_ui_unique | 0.357 | 0.353 | 2.753 | 2.420 | 0.333 | 0.381 (15) |
| zh-pure-ui | WenQuanYiMicroHei-face0 | cjk94 | 0.309 | 0.311 | 3.156 | 2.852 | 0.266 | 0.312 (14) |
| zh-pure-ui | WenQuanYiMicroHei-face0 | pure_cjk_ui_unique | 0.294 | 0.310 | 2.329 | 2.030 | 0.184 | 0.382 (15) |
| zh-pure-ui | DroidSansFallback | cjk94 | 0.275 | 0.274 | 2.983 | 2.749 | 0.234 | 0.284 (14) |
| zh-pure-ui | DroidSansFallbackFull | cjk94 | 0.273 | 0.275 | 2.986 | 2.823 | 0.191 | 0.281 (12) |
| zh-pure-ui | DroidSansFallback | pure_cjk_ui_unique | 0.264 | 0.268 | 2.173 | 1.959 | 0.214 | 0.314 (15) |
| zh-pure-ui | DroidSansFallbackFull | pure_cjk_ui_unique | 0.264 | 0.262 | 2.190 | 2.020 | 0.215 | 0.305 (15) |

Original ASCII94 control profiles

| Screen | Font | Profile | Hinted outline | Unhinted outline | Native render | Geometry reuse | Potential avoided | Maximum outline (logical size) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| english | Rye-Regular | ascii94 | 18.255 | 0.457 | 22.442 | 3.645 | 18.797 | 18.450 (15) |
| english | Vollkorn-Medium | ascii94 | 12.695 | 0.260 | 14.632 | 1.612 | 12.887 | 12.773 (16) |
| ko | NanumMyeongjo-Regular | ascii94 | 1.616 | 0.251 | 3.271 | 1.603 | 1.667 | 1.631 (16) |
| english | NanumMyeongjo-Bold | ascii94 | 1.614 | 0.254 | 3.263 | 1.578 | 1.743 | 1.640 (15) |
| ko | NanumMyeongjo-Bold | ascii94 | 1.609 | 0.254 | 3.405 | 1.602 | 1.720 | 1.627 (11) |
| english | NanumMyeongjo-Regular | ascii94 | 1.604 | 0.248 | 3.266 | 1.577 | 1.722 | 1.606 (11) |
| ko | NanumMyeongjo-ExtraBold | ascii94 | 1.490 | 0.266 | 3.330 | 1.800 | 1.625 | 1.530 (14) |
| english | NanumMyeongjo-ExtraBold | ascii94 | 1.467 | 0.267 | 3.337 | 1.682 | 1.574 | 1.486 (16) |
| ko | NanumGothic-ExtraBold | ascii94 | 1.326 | 0.235 | 2.823 | 1.402 | 1.404 | 1.350 (14) |
| english | NanumGothic-ExtraBold | ascii94 | 1.318 | 0.231 | 2.836 | 1.411 | 1.416 | 1.340 (16) |
| ko | NanumGothic-Regular | ascii94 | 1.270 | 0.219 | 2.687 | 1.337 | 1.357 | 1.285 (16) |
| english | NanumGothic-Regular | ascii94 | 1.264 | 0.218 | 2.766 | 1.355 | 1.378 | 1.287 (11) |
| zh | WenQuanYiMicroHei-face0 | ascii94 | 0.763 | 0.207 | 2.018 | 1.155 | 0.827 | 0.804 (11) |
| english | WenQuanYiMicroHei-face0 | ascii94 | 0.760 | 0.203 | 2.007 | 1.187 | 0.817 | 0.785 (14) |
| english | NanumGothicCoding-Regular | ascii94 | 0.635 | 0.234 | 2.051 | 1.245 | 0.749 | 0.649 (12) |
| ko | NanumGothicCoding-Regular | ascii94 | 0.635 | 0.234 | 2.010 | 1.287 | 0.715 | 0.644 (12) |
| english | D2Coding-Regular | ascii94 | 0.557 | 0.185 | 1.635 | 1.040 | 0.595 | 0.571 (11) |
| ko | D2Coding-Regular | ascii94 | 0.556 | 0.194 | 1.623 | 1.012 | 0.636 | 0.575 (12) |
| english | NotoSerifSC-VF | ascii94 | 0.234 | 0.230 | 2.051 | 1.745 | 0.250 | 0.249 (12) |
| zh | NotoSerifSC-VF | ascii94 | 0.233 | 0.233 | 1.973 | 1.685 | 0.251 | 0.234 (11) |
| zh | BabelStoneHan | ascii94 | 0.204 | 0.206 | 1.527 | 1.303 | 0.237 | 0.206 (15) |
| english | BabelStoneHan | ascii94 | 0.203 | 0.200 | 1.574 | 1.303 | 0.231 | 0.210 (15) |
| zh | NotoSansSC-VF | ascii94 | 0.186 | 0.186 | 1.391 | 1.173 | 0.214 | 0.194 (14) |
| english | NotoSansSC-VF | ascii94 | 0.184 | 0.183 | 1.322 | 1.139 | 0.185 | 0.186 (11) |

