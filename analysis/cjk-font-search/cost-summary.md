# Warm Swash cost decomposition

All 18 timing processes and 12,960 rows passed independent live source/build/font/order/arithmetic checks. Each timing case retained exact native/rebuilt geometry and ten-offset native/reused alpha-image agreement. The reader-only correction is preserved separately; timed inputs and outputs were unchanged.

Values below are **µs per glyph iteration**, with builder-only measured per scaler build/drop. Each table entry is the median of the five logical-size medians (11, 12, 14, 15, 16 px); each size has six balanced trials of twenty repeats. ASCII94 controls and all 360 exact-size cases remain in the JSON and CSV outputs. These are exploratory warm-cost diagnostics, without confidence intervals or application-percentage claims.

## DPR 1: initial-atlas size controls

### Default coordinates

| Workload | Font / weight | Builder | Rebuild + outline | Hinted | Unhinted | Native render | Geometry reuse |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| en | BabelStoneHan | 0.139 | 0.364 | 0.215 | 0.220 | 0.771 | 0.537 |
| en | NanumMyeongjo-Regular | 0.130 | 1.802 | 1.661 | 0.263 | 2.385 | 0.659 |
| en | NotoSansSC-VF | 0.138 | 0.337 | 0.180 | 0.182 | 0.729 | 0.545 |
| en | NotoSerifSC-VF | 0.137 | 0.374 | 0.236 | 0.232 | 0.963 | 0.696 |
| en | Rye-Regular | 0.118 | 18.868 | 18.624 | 0.469 | 20.847 | 1.647 |
| en | Vollkorn-Medium | 0.140 | 14.654 | 14.474 | 0.248 | 15.425 | 0.702 |
| ko | NanumMyeongjo-Regular | 0.129 | 2.560 | 2.351 | 0.404 | 3.676 | 1.255 |
| zh | BabelStoneHan | 0.132 | 0.637 | 0.532 | 0.501 | 2.262 | 1.878 |
| zh | NotoSansSC-VF | 0.134 | 0.499 | 0.353 | 0.354 | 1.360 | 1.036 |
| zh | NotoSerifSC-VF | 0.134 | 0.600 | 0.435 | 0.425 | 1.860 | 1.497 |

### Explicit demo weights

| Workload | Font / weight | Builder | Rebuild + outline | Hinted | Unhinted | Native render | Geometry reuse |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| en | NotoSansSC-VF / 300 | 0.138 | 0.423 | 0.255 | 0.257 | 0.834 | 0.561 |
| en | NotoSansSC-VF / 400 | 0.145 | 0.408 | 0.267 | 0.263 | 0.831 | 0.543 |
| en | NotoSerifSC-VF / 300 | 0.132 | 0.451 | 0.306 | 0.294 | 1.052 | 0.705 |
| en | NotoSerifSC-VF / 400 | 0.140 | 0.462 | 0.310 | 0.308 | 1.072 | 0.737 |
| zh | NotoSansSC-VF / 300 | 0.134 | 0.601 | 0.455 | 0.425 | 1.530 | 1.131 |
| zh | NotoSansSC-VF / 400 | 0.135 | 0.580 | 0.448 | 0.458 | 1.624 | 1.142 |
| zh | NotoSerifSC-VF / 300 | 0.138 | 0.708 | 0.567 | 0.561 | 2.082 | 1.507 |
| zh | NotoSerifSC-VF / 400 | 0.138 | 0.713 | 0.543 | 0.531 | 2.242 | 1.557 |

## DPR 2: larger-size controls

### Default coordinates

| Workload | Font / weight | Builder | Rebuild + outline | Hinted | Unhinted | Native render | Geometry reuse |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| en | BabelStoneHan | 0.138 | 0.364 | 0.215 | 0.217 | 1.139 | 0.903 |
| en | NanumMyeongjo-Regular | 0.131 | 1.816 | 1.659 | 0.268 | 2.868 | 1.074 |
| en | NotoSansSC-VF | 0.139 | 0.335 | 0.184 | 0.180 | 1.031 | 0.852 |
| en | NotoSerifSC-VF | 0.137 | 0.373 | 0.234 | 0.243 | 1.396 | 1.136 |
| en | Rye-Regular | 0.119 | 19.370 | 19.071 | 0.471 | 22.221 | 2.507 |
| en | Vollkorn-Medium | 0.132 | 14.903 | 14.698 | 0.255 | 16.231 | 1.098 |
| ko | NanumMyeongjo-Regular | 0.131 | 2.531 | 2.396 | 0.412 | 4.459 | 2.224 |
| zh | BabelStoneHan | 0.139 | 0.652 | 0.515 | 0.513 | 3.929 | 3.543 |
| zh | NotoSansSC-VF | 0.135 | 0.470 | 0.347 | 0.328 | 2.199 | 1.967 |
| zh | NotoSerifSC-VF | 0.133 | 0.571 | 0.431 | 0.434 | 3.068 | 2.832 |

### Explicit demo weights

| Workload | Font / weight | Builder | Rebuild + outline | Hinted | Unhinted | Native render | Geometry reuse |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| en | NotoSansSC-VF / 300 | 0.134 | 0.406 | 0.254 | 0.262 | 1.180 | 0.910 |
| en | NotoSansSC-VF / 400 | 0.138 | 0.415 | 0.269 | 0.257 | 1.176 | 0.984 |
| en | NotoSerifSC-VF / 300 | 0.141 | 0.465 | 0.309 | 0.306 | 1.502 | 1.227 |
| en | NotoSerifSC-VF / 400 | 0.141 | 0.457 | 0.302 | 0.306 | 1.570 | 1.241 |
| zh | NotoSansSC-VF / 300 | 0.134 | 0.604 | 0.432 | 0.457 | 2.721 | 2.128 |
| zh | NotoSansSC-VF / 400 | 0.134 | 0.587 | 0.455 | 0.443 | 3.046 | 2.429 |
| zh | NotoSerifSC-VF / 300 | 0.136 | 0.699 | 0.558 | 0.559 | 3.636 | 2.852 |
| zh | NotoSerifSC-VF / 400 | 0.133 | 0.717 | 0.551 | 0.565 | 3.613 | 2.898 |

## Matched variation cost at DPR 1

Each ratio is the median of five ratios matched at identical font SHA, text profile and logical size. The default weight is 100 for Noto Sans SC and 200 for Noto Serif SC; normalized coordinates are computed once outside every timer. The public Swash API yields `[1556]` for Noto Serif SC weight 300, while the production trace uses `[1555]`: this one case is a nearby instance, one 2.14 fixed-point step apart. All other supplemental coordinate vectors match the production trace.

| Workload | Font / weight | Hinted increment (µs) | Hinted ratio | Render increment (µs) | Render ratio |
| --- | --- | ---: | ---: | ---: | ---: |
| en | NotoSansSC-VF / 300 | 0.073 | 1.43× | 0.112 | 1.18× |
| en | NotoSansSC-VF / 400 | 0.085 | 1.47× | 0.121 | 1.18× |
| en | NotoSerifSC-VF / 300 | 0.079 | 1.36× | 0.080 | 1.09× |
| en | NotoSerifSC-VF / 400 | 0.077 | 1.33× | 0.109 | 1.11× |
| zh | NotoSansSC-VF / 300 | 0.102 | 1.29× | 0.173 | 1.13× |
| zh | NotoSansSC-VF / 400 | 0.103 | 1.32× | 0.204 | 1.15× |
| zh | NotoSerifSC-VF / 300 | 0.111 | 1.24× | 0.222 | 1.12× |
| zh | NotoSerifSC-VF / 400 | 0.103 | 1.27× | 0.242 | 1.14× |

## What these measurements establish

Warm scaler construction is small and similar across these fonts. Rye and Vollkorn instead have a large difference between prepared hinted and unhinted outline cost. Nanum Myeongjo's hinted outline work is smaller but remains material, including its Korean glyphs. Noto default and nondefault instances have closely matched hinted/unhinted costs; requesting nondefault weights increases outline and raster work without creating a large hinting-specific cost.

These observations distinguish expensive hinted outline work from scaler setup and raster complexity. They do not by themselves explain the application's cache overhead or its miss sequence. The production counter traces establish those separate facts. Rebuild, outline and rendering timings are independent kernels; subtracting medians is an estimate, not a strict sum of isolated pipeline stages.

All six kernels exclude cold context creation and perform their own warmup. Geometry reuse includes a standalone hash lookup and rasterizes retained native outlines; it excludes FemtoVG's real cache-key allocation, arena budget/admission, atlas and rendering loop. Noto normalization is performed once outside every timer. Application benchmarks remain the evidence for the patch's overall performance.
