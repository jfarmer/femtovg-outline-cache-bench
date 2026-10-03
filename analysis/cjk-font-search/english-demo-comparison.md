English-demo exploratory font comparisons
=========================================

All thirteen fonts were evaluated in the unchanged English FemtoVG demo
with the same master and final binaries at DPR2. Two balanced blocks each
ran three trials. The independent audit passed 52 processes and all 4,368
raw phase rows, source/build/font/aggregate/count/order bindings, and 1,209
endpoint effects. All executable bodies were checked live; audit stderr
was empty. These are exploratory comparisons, without confidence intervals
or confirmation claims; this cohort did not require an actual-demo pixel
preflight. Every attempted font and all effects remain preserved.

The largest observed first-paint savings remain Rye (2.507 ms) and
Vollkorn (2.177 ms). The largest CJK-family font result on these English
strings is Nanum Myeongjo Regular (0.304 ms), followed by Noto Serif SC
(0.295 ms). This tests their Latin glyphs; separate localized scenes
evaluate Korean and Chinese glyphs. D2Coding's first-paint block effects
have opposing signs (+0.131 and −0.052 ms), and Nanum Gothic Coding's
mean first-paint effect is −0.002 ms. Small effects need additional evidence.

First paint: means of each process's three-trial median, in milliseconds.
Positive savings mean less work in the patch; negative values mean more.

| Font | Master | Patch | Saved | Block 1 saved | Block 2 saved |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rye-Regular | 6.561 | 4.054 | 2.507 | 2.542 | 2.472 |
| Vollkorn-Medium | 6.818 | 4.641 | 2.177 | 2.167 | 2.187 |
| NanumMyeongjo-Regular | 1.788 | 1.484 | 0.304 | 0.241 | 0.367 |
| NotoSerifSC-VF | 4.686 | 4.391 | 0.295 | 0.156 | 0.435 |
| NanumMyeongjo-ExtraBold | 1.689 | 1.447 | 0.242 | 0.298 | 0.187 |
| NotoSansSC-VF | 2.293 | 2.056 | 0.236 | 0.348 | 0.125 |
| NanumGothic-ExtraBold | 1.770 | 1.536 | 0.234 | 0.236 | 0.232 |
| NanumMyeongjo-Bold | 1.723 | 1.522 | 0.201 | 0.210 | 0.192 |
| NanumGothic-Regular | 1.736 | 1.543 | 0.193 | 0.213 | 0.173 |
| WenQuanYiMicroHei-face0 | 1.582 | 1.421 | 0.161 | 0.105 | 0.216 |
| BabelStoneHan | 1.210 | 1.134 | 0.076 | 0.032 | 0.120 |
| D2Coding-Regular | 1.105 | 1.065 | 0.039 | 0.131 | -0.052 |
| NanumGothicCoding-Regular | 1.075 | 1.077 | -0.002 | 0.022 | -0.027 |

Other demo phases: paired savings in microseconds per frame. Pan is the
existing demo movement phase. The reported sequence covers 65 frames,
shown in milliseconds saved; it excludes unreported warmups. Sequence
values sum weighted phases within each trial before taking medians, so
they need not equal a sum of the phase medians displayed here.

| Font | Warm µs | Zoom in µs | Zoom out µs | Pan µs | 65-frame sequence ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rye-Regular | -10.02 | 2457.39 | 1619.65 | -0.09 | 52.024 |
| Vollkorn-Medium | 0.30 | 2167.31 | 1475.70 | 1.84 | 46.257 |
| NanumMyeongjo-Regular | -2.77 | 322.72 | 198.48 | -0.91 | 6.676 |
| NotoSerifSC-VF | 12.05 | 231.55 | 29.69 | -2.35 | 3.397 |
| NanumMyeongjo-ExtraBold | -0.51 | 229.46 | 161.29 | 1.74 | 5.057 |
| NotoSansSC-VF | -7.11 | 34.81 | 27.34 | 4.07 | 0.164 |
| NanumGothic-ExtraBold | -1.64 | 220.21 | 158.81 | 0.28 | 5.063 |
| NanumMyeongjo-Bold | -4.48 | 242.43 | 168.38 | 5.47 | 5.256 |
| NanumGothic-Regular | -1.55 | 232.60 | 176.48 | 0.50 | 5.028 |
| WenQuanYiMicroHei-face0 | -3.28 | 157.76 | 103.62 | -3.31 | 3.193 |
| BabelStoneHan | 4.27 | 95.49 | 77.67 | 5.51 | 2.275 |
| D2Coding-Regular | 0.05 | 70.62 | 62.91 | -3.80 | 1.702 |
| NanumGothicCoding-Regular | -0.28 | 132.11 | 50.37 | -9.32 | 2.215 |

Text example: paired savings in microseconds per frame, and the 88-frame
reported sequence in milliseconds. Every font has an observed warm-text
cost in this exploratory cohort; this cache is not a universal improvement.

| Font | Warm µs | X advance µs | Y advance µs | Reflow µs | 88-frame sequence ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Rye-Regular | -13.74 | 357.24 | -14.81 | -23.09 | 60.235 |
| Vollkorn-Medium | -6.52 | 305.27 | -9.04 | 9.10 | 55.762 |
| NanumMyeongjo-Regular | -8.25 | 58.21 | -3.24 | -12.50 | 7.513 |
| NotoSerifSC-VF | -4.07 | 48.30 | 8.24 | 742.74 | 18.863 |
| NanumMyeongjo-ExtraBold | -5.47 | 46.32 | -9.64 | -28.87 | 6.344 |
| NotoSansSC-VF | -7.79 | 20.40 | -15.64 | 93.55 | 5.564 |
| NanumGothic-ExtraBold | -5.37 | 47.39 | -6.21 | 27.38 | 5.692 |
| NanumMyeongjo-Bold | -9.73 | 57.83 | -3.89 | 0.28 | 6.791 |
| NanumGothic-Regular | -3.91 | 53.48 | -3.07 | 36.90 | 6.106 |
| WenQuanYiMicroHei-face0 | -8.20 | 29.85 | -7.54 | 17.68 | 4.704 |
| BabelStoneHan | -8.15 | 60.91 | -14.80 | 101.60 | 4.210 |
| D2Coding-Regular | -4.99 | 48.98 | 0.31 | -59.05 | 1.566 |
| NanumGothicCoding-Regular | -8.82 | 56.33 | 1.34 | 38.15 | 2.797 |

The machine-readable comparison retains draw, submit, and completion
metrics for these phases and all three reported sequences (65/88/63
frames). Submission and completion are cumulative host endpoints. Fixed
Roboto variation scenes and every controlled phase remain in the complete
audit JSON/CSVs. Font loading, process launch, and setup are outside these
reported renderer timings. The current comparison says none of the new
CJK-family candidates replaces Rye as the strongest English-demo example.
