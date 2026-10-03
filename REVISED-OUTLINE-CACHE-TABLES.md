# Revised Swash outline-cache measurements

Four freshly built versions share one campaign: master, the committed selected arena (`prior`), the captured fixes 4–5 tree (`updated45`), and the complete revised tree (`final`). Historical observations remain preserved and are not pooled here. **Final/master is the primary acceptance comparison.** The other columns isolate the minimum-growth/typed-run changes and then the routing/key/target fixes. All six pairings remain in the complete statistics.

Cells show median paired duration change, an exploratory 95% whole-block bootstrap interval, and paired absolute change. Negative durations mean faster. Absolute columns are process-median ms; median paired percentages need not equal ratios of those absolute medians. Small differences are shown in µs. Intervals have no multiplicity or selection adjustment.

## First reported paint

| Font | Scene / phase | Measurement | Master ms | Final ms | Final/master | Fixes 4–5/prior | Final/fixes 4–5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PT Sans | demo/first_paint | CPU draw | 2.031 | 1.734 | -14.89% [-15.63, -13.13]<br>Δ -0.302 ms | +0.48% [+0.033, +0.80]<br>Δ +8.396 µs | +0.047% [-0.92, +1.24]<br>Δ +0.730 µs |
| PT Sans | text/first_paint | CPU draw | 9.271 | 8.412 | -9.58% [-9.78, -8.90]<br>Δ -0.892 ms | +0.81% [-0.38, +1.60]<br>Δ +0.068 ms | -0.38% [-1.27, +0.29]<br>Δ -0.032 ms |
| Roboto Flex | demo/first_paint | CPU draw | 1.498 | 1.429 | -4.69% [-7.04, -3.84]<br>Δ -0.069 ms | +0.20% [-2.15, +1.09]<br>Δ +2.792 µs | +1.44% [+0.22, +2.31]<br>Δ +0.020 ms |
| Roboto Flex | font_variations/first_paint | CPU draw | 1.018 | 0.981 | -4.33% [-6.08, -2.75]<br>Δ -0.043 ms | +0.12% [-1.21, +1.71]<br>Δ +1.146 µs | -0.10% [-1.11, +1.14]<br>Δ -1.000 µs |
| Roboto Flex | text/first_paint | CPU draw | 7.670 | 7.254 | -5.38% [-6.55, -4.38]<br>Δ -0.413 ms | -0.35% [-1.28, +1.13]<br>Δ -0.026 ms | +0.44% [-0.45, +1.01]<br>Δ +0.033 ms |
| Vollkorn | demo/first_paint | CPU draw | 6.716 | 4.552 | -32.61% [-33.61, -31.83]<br>Δ -2.197 ms | -0.34% [-1.74, +0.22]<br>Δ -0.016 ms | +1.24% [+0.71, +2.21]<br>Δ +0.055 ms |
| Vollkorn | text/first_paint | CPU draw | 27.310 | 20.673 | -24.10% [-24.95, -23.57]<br>Δ -6.639 ms | +2.44% [+1.42, +3.45]<br>Δ +0.504 ms | -1.85% [-2.39, -1.44]<br>Δ -0.393 ms |
| PT Sans | demo/first_paint | GPU completion | 12.327 | 11.482 | -7.20% [-17.25, +4.44]<br>Δ -0.901 ms | -4.10% [-8.85, -1.53]<br>Δ -0.492 ms | +0.74% [-8.69, +12.74]<br>Δ +0.088 ms |
| PT Sans | text/first_paint | GPU completion | 31.627 | 30.144 | -7.63% [-13.40, -0.54]<br>Δ -2.381 ms | -1.85% [-5.20, -0.08]<br>Δ -0.576 ms | +1.42% [-7.20, +4.21]<br>Δ +0.427 ms |
| Roboto Flex | demo/first_paint | GPU completion | 11.214 | 11.319 | -0.83% [-6.53, +4.22]<br>Δ -0.086 ms | +9.50% [-11.15, +21.05]<br>Δ +1.069 ms | -8.60% [-20.36, +2.11]<br>Δ -0.981 ms |
| Roboto Flex | font_variations/first_paint | GPU completion | 5.325 | 4.924 | -4.87% [-13.97, +4.31]<br>Δ -0.232 ms | -0.29% [-14.13, +9.56]<br>Δ -0.021 ms | -12.62% [-18.47, -0.81]<br>Δ -0.806 ms |
| Roboto Flex | text/first_paint | GPU completion | 31.009 | 30.194 | -2.20% [-7.28, +0.18]<br>Δ -0.682 ms | -0.76% [-5.54, +1.22]<br>Δ -0.237 ms | -1.42% [-6.15, +2.29]<br>Δ -0.398 ms |
| Vollkorn | demo/first_paint | GPU completion | 16.960 | 14.884 | -12.35% [-14.21, -8.40]<br>Δ -2.090 ms | +2.00% [-1.57, +11.16]<br>Δ +0.297 ms | +1.09% [-3.84, +10.66]<br>Δ +0.162 ms |
| Vollkorn | text/first_paint | GPU completion | 51.095 | 44.221 | -13.29% [-15.38, -11.79]<br>Δ -6.677 ms | -0.26% [-3.03, +6.31]<br>Δ -0.115 ms | +0.07% [-0.67, +4.35]<br>Δ +0.029 ms |

## Warm example redraws

| Font | Scene / phase | Measurement | Master ms | Final ms | Final/master | Fixes 4–5/prior | Final/fixes 4–5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PT Sans | demo/warm | CPU draw | 0.214 | 0.214 | +0.78% [-0.84, +1.16]<br>Δ +1.664 µs | +0.47% [-0.047, +1.10]<br>Δ +1.013 µs | +0.11% [-0.49, +0.89]<br>Δ +0.239 µs |
| PT Sans | text/warm | CPU draw | 0.247 | 0.255 | +3.15% [+2.54, +3.89]<br>Δ +7.758 µs | +0.33% [-0.07, +0.96]<br>Δ +0.821 µs | +0.90% [+0.028, +1.53]<br>Δ +2.280 µs |
| Roboto Flex | demo/warm | CPU draw | 0.217 | 0.217 | +0.69% [-0.95, +1.33]<br>Δ +1.474 µs | -0.19% [-1.29, +2.17]<br>Δ -0.416 µs | +0.74% [-0.79, +1.46]<br>Δ +1.597 µs |
| Roboto Flex | font_variations/warm | CPU draw | 0.037 | 0.037 | -0.77% [-1.89, +1.35]<br>Δ -0.295 µs | -0.91% [-2.08, +0.26]<br>Δ -0.333 µs | +1.43% [+0.15, +2.52]<br>Δ +0.524 µs |
| Roboto Flex | text/warm | CPU draw | 0.262 | 0.264 | +0.94% [-1.00, +2.20]<br>Δ +2.398 µs | +0.19% [-0.87, +1.62]<br>Δ +0.497 µs | +0.85% [-0.36, +2.80]<br>Δ +2.213 µs |
| Vollkorn | demo/warm | CPU draw | 0.216 | 0.216 | +0.004% [-1.35, +1.63]<br>Δ +0.009 µs | +0.56% [-1.01, +1.88]<br>Δ +1.190 µs | -0.26% [-1.38, +2.40]<br>Δ -0.576 µs |
| Vollkorn | text/warm | CPU draw | 0.249 | 0.256 | +2.88% [+2.10, +4.06]<br>Δ +7.158 µs | +0.56% [+0.09, +1.20]<br>Δ +1.442 µs | +1.05% [+0.44, +2.09]<br>Δ +2.650 µs |
| PT Sans | demo/warm | GPU completion | 1.032 | 1.068 | -0.23% [-5.74, +2.63]<br>Δ -2.480 µs | -1.31% [-4.63, +1.74]<br>Δ -0.012 ms | +3.73% [-4.30, +7.76]<br>Δ +0.045 ms |
| PT Sans | text/warm | GPU completion | 0.759 | 0.745 | +1.18% [-5.83, +5.82]<br>Δ +7.318 µs | +2.26% [-7.10, +4.39]<br>Δ +0.014 ms | +1.79% [-6.06, +13.12]<br>Δ +0.019 ms |
| Roboto Flex | demo/warm | GPU completion | 1.073 | 0.990 | +6.11% [-8.99, +10.68]<br>Δ +0.063 ms | +5.85% [-5.05, +15.69]<br>Δ +0.052 ms | -6.15% [-12.78, +3.53]<br>Δ -0.062 ms |
| Roboto Flex | font_variations/warm | GPU completion | 0.308 | 0.312 | -1.73% [-6.00, +7.15]<br>Δ -4.903 µs | -1.09% [-19.58, +2.51]<br>Δ -3.101 µs | +1.09% [-6.25, +8.94]<br>Δ +3.496 µs |
| Roboto Flex | text/warm | GPU completion | 0.742 | 0.703 | -0.37% [-11.00, +4.86]<br>Δ -2.243 µs | -9.26% [-14.48, -3.41]<br>Δ -0.081 ms | +1.50% [-1.04, +7.28]<br>Δ +0.011 ms |
| Vollkorn | demo/warm | GPU completion | 1.195 | 1.049 | -1.50% [-9.72, +3.25]<br>Δ -0.017 ms | +2.75% [-6.79, +4.50]<br>Δ +0.024 ms | +4.21% [-1.78, +17.22]<br>Δ +0.043 ms |
| Vollkorn | text/warm | GPU completion | 0.721 | 0.708 | +2.37% [-1.11, +6.04]<br>Δ +0.016 ms | -1.65% [-8.23, +8.72]<br>Δ -0.013 ms | +4.55% [+1.72, +7.53]<br>Δ +0.034 ms |

## Every other reported example phase

| Font | Scene / phase | Measurement | Master ms | Final ms | Final/master | Fixes 4–5/prior | Final/fixes 4–5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PT Sans | demo/pan | CPU draw | 0.219 | 0.219 | +0.26% [-0.82, +0.78]<br>Δ +0.569 µs | -0.34% [-0.74, +1.31]<br>Δ -0.756 µs | +0.012% [-0.66, +0.76]<br>Δ +0.025 µs |
| PT Sans | demo/zoom_in | CPU draw | 1.874 | 1.565 | -16.24% [-16.92, -15.54]<br>Δ -0.306 ms | +0.13% [-0.20, +0.62]<br>Δ +1.962 µs | -0.49% [-1.62, +0.20]<br>Δ -7.788 µs |
| PT Sans | demo/zoom_out | CPU draw | 1.219 | 0.996 | -18.49% [-19.05, -17.47]<br>Δ -0.224 ms | -0.30% [-1.02, +0.69]<br>Δ -2.981 µs | -0.62% [-0.98, +0.34]<br>Δ -6.207 µs |
| PT Sans | text/reflow | CPU draw | 2.074 | 2.072 | +0.22% [-0.35, +0.79]<br>Δ +4.521 µs | +0.22% [-0.33, +0.85]<br>Δ +4.610 µs | +0.43% [-0.21, +0.87]<br>Δ +8.848 µs |
| PT Sans | text/size_advance | CPU draw | 5.527 | 5.004 | -9.55% [-9.62, -9.08]<br>Δ -0.528 ms | +0.69% [+0.31, +1.10]<br>Δ +0.034 ms | -0.24% [-0.84, +0.25]<br>Δ -0.012 ms |
| PT Sans | text/size_return | CPU draw | 0.264 | 0.271 | +3.01% [+1.64, +3.73]<br>Δ +7.998 µs | -0.67% [-1.39, -0.38]<br>Δ -1.797 µs | +2.07% [+1.13, +3.41]<br>Δ +5.467 µs |
| PT Sans | text/x_advance | CPU draw | 0.421 | 0.363 | -13.83% [-14.09, -13.41]<br>Δ -0.058 ms | -0.45% [-1.26, +0.29]<br>Δ -1.581 µs | +1.49% [+0.97, +2.84]<br>Δ +5.329 µs |
| PT Sans | text/x_return | CPU draw | 0.253 | 0.260 | +2.65% [+1.63, +3.61]<br>Δ +6.613 µs | -0.14% [-0.71, +0.18]<br>Δ -0.371 µs | +1.34% [+0.46, +1.85]<br>Δ +3.423 µs |
| PT Sans | text/y_advance | CPU draw | 0.249 | 0.255 | +2.23% [+1.20, +3.29]<br>Δ +5.596 µs | -0.30% [-1.26, +0.55]<br>Δ -0.759 µs | +1.18% [+0.78, +2.05]<br>Δ +2.967 µs |
| Roboto Flex | demo/pan | CPU draw | 0.221 | 0.221 | -0.40% [-2.50, +0.22]<br>Δ -0.865 µs | +0.47% [-1.26, +1.42]<br>Δ +1.021 µs | +0.38% [-0.28, +0.94]<br>Δ +0.819 µs |
| Roboto Flex | demo/zoom_in | CPU draw | 1.334 | 1.289 | -3.89% [-4.80, -1.94]<br>Δ -0.051 ms | -0.09% [-1.04, +0.68]<br>Δ -1.106 µs | -0.25% [-0.72, +1.35]<br>Δ -3.238 µs |
| Roboto Flex | demo/zoom_out | CPU draw | 0.874 | 0.843 | -3.57% [-4.62, -3.01]<br>Δ -0.031 ms | +0.16% [-0.63, +1.39]<br>Δ +1.326 µs | +0.13% [-1.16, +1.15]<br>Δ +1.073 µs |
| Roboto Flex | font_variations/slant_advance | CPU draw | 0.468 | 0.454 | -3.07% [-4.36, -1.76]<br>Δ -0.014 ms | -0.26% [-1.57, +0.69]<br>Δ -1.160 µs | +0.56% [-0.44, +2.42]<br>Δ +2.504 µs |
| Roboto Flex | font_variations/slant_return | CPU draw | 0.040 | 0.039 | -3.35% [-4.59, +0.30]<br>Δ -1.381 µs | -0.38% [-2.72, +1.73]<br>Δ -0.140 µs | +2.75% [-0.001, +6.77]<br>Δ +1.046 µs |
| Roboto Flex | font_variations/weight_advance | CPU draw | 0.508 | 0.499 | -2.07% [-3.18, -1.24]<br>Δ -0.010 ms | -0.42% [-0.89, +0.37]<br>Δ -2.094 µs | +0.78% [+0.20, +3.12]<br>Δ +3.781 µs |
| Roboto Flex | font_variations/weight_return | CPU draw | 0.038 | 0.037 | -2.74% [-3.33, +0.06]<br>Δ -1.038 µs | +1.33% [-2.19, +3.61]<br>Δ +0.489 µs | -1.41% [-2.72, +0.95]<br>Δ -0.524 µs |
| Roboto Flex | text/reflow | CPU draw | 2.007 | 2.023 | +0.75% [-1.11, +1.33]<br>Δ +0.015 ms | -0.07% [-0.61, +0.56]<br>Δ -1.320 µs | +0.51% [-0.51, +1.97]<br>Δ +0.010 ms |
| Roboto Flex | text/size_advance | CPU draw | 5.042 | 4.911 | -2.67% [-3.65, -2.13]<br>Δ -0.132 ms | +0.48% [-0.003, +1.61]<br>Δ +0.024 ms | +0.09% [-0.38, +0.61]<br>Δ +4.462 µs |
| Roboto Flex | text/size_return | CPU draw | 0.278 | 0.279 | +0.14% [-0.95, +2.80]<br>Δ +0.380 µs | -0.09% [-0.92, +1.44]<br>Δ -0.239 µs | +1.20% [-0.12, +2.07]<br>Δ +3.248 µs |
| Roboto Flex | text/x_advance | CPU draw | 0.415 | 0.384 | -7.86% [-8.95, -6.13]<br>Δ -0.032 ms | +0.25% [-1.57, +1.71]<br>Δ +0.919 µs | +0.57% [-0.018, +1.97]<br>Δ +2.158 µs |
| Roboto Flex | text/x_return | CPU draw | 0.266 | 0.271 | +2.44% [+1.24, +3.03]<br>Δ +6.402 µs | -0.004% [-1.85, +0.93]<br>Δ -0.008 µs | +1.84% [+1.08, +2.34]<br>Δ +4.850 µs |
| Roboto Flex | text/y_advance | CPU draw | 0.259 | 0.263 | +1.50% [-0.73, +2.73]<br>Δ +3.844 µs | -0.14% [-1.42, +1.40]<br>Δ -0.346 µs | +1.06% [-0.16, +1.78]<br>Δ +2.819 µs |
| Vollkorn | demo/pan | CPU draw | 0.219 | 0.218 | -0.16% [-0.84, +1.60]<br>Δ -0.358 µs | -0.35% [-1.65, +0.59]<br>Δ -0.761 µs | +1.19% [-0.91, +3.56]<br>Δ +2.561 µs |
| Vollkorn | demo/zoom_in | CPU draw | 6.195 | 4.073 | -34.32% [-34.77, -33.76]<br>Δ -2.123 ms | -0.70% [-1.69, -0.044]<br>Δ -0.028 ms | +0.94% [+0.13, +1.80]<br>Δ +0.038 ms |
| Vollkorn | demo/zoom_out | CPU draw | 4.055 | 2.586 | -36.09% [-36.46, -35.73]<br>Δ -1.464 ms | -0.05% [-0.60, +0.65]<br>Δ -1.309 µs | +0.81% [+0.05, +1.47]<br>Δ +0.021 ms |
| Vollkorn | text/reflow | CPU draw | 2.852 | 2.860 | +0.42% [-0.31, +1.45]<br>Δ +0.012 ms | +0.54% [-0.08, +1.45]<br>Δ +0.016 ms | -0.52% [-1.11, +0.42]<br>Δ -0.015 ms |
| Vollkorn | text/size_advance | CPU draw | 11.404 | 7.722 | -32.43% [-32.54, -32.11]<br>Δ -3.688 ms | +1.23% [+0.77, +1.64]<br>Δ +0.094 ms | -1.44% [-1.95, -1.21]<br>Δ -0.112 ms |
| Vollkorn | text/size_return | CPU draw | 0.268 | 0.273 | +1.68% [+0.44, +3.02]<br>Δ +4.570 µs | -1.36% [-3.48, -0.36]<br>Δ -3.620 µs | +1.44% [+0.23, +5.43]<br>Δ +3.948 µs |
| Vollkorn | text/x_advance | CPU draw | 0.684 | 0.385 | -44.05% [-44.74, -43.40]<br>Δ -0.301 ms | -0.06% [-1.45, +0.73]<br>Δ -0.235 µs | +1.54% [+0.20, +2.15]<br>Δ +5.727 µs |
| Vollkorn | text/x_return | CPU draw | 0.255 | 0.260 | +2.07% [+1.10, +3.72]<br>Δ +5.233 µs | -0.62% [-1.04, +0.022]<br>Δ -1.573 µs | +1.56% [+0.96, +2.25]<br>Δ +4.002 µs |
| Vollkorn | text/y_advance | CPU draw | 0.250 | 0.257 | +3.07% [+2.42, +3.77]<br>Δ +7.763 µs | -0.44% [-1.09, +1.21]<br>Δ -1.121 µs | +1.61% [+1.14, +2.41]<br>Δ +4.048 µs |
| PT Sans | demo/pan | GPU completion | 1.087 | 0.995 | -2.56% [-22.36, +5.09]<br>Δ -0.053 ms | -0.19% [-2.28, +13.11]<br>Δ -3.506 µs | -0.86% [-12.54, +4.35]<br>Δ -7.915 µs |
| PT Sans | demo/zoom_in | GPU completion | 4.862 | 4.591 | -7.47% [-15.02, -2.88]<br>Δ -0.419 ms | +0.42% [-7.94, +3.10]<br>Δ +0.017 ms | -0.80% [-8.98, +8.25]<br>Δ -0.031 ms |
| PT Sans | demo/zoom_out | GPU completion | 3.578 | 3.298 | -11.80% [-25.12, +3.81]<br>Δ -0.478 ms | +3.40% [-0.43, +6.24]<br>Δ +0.097 ms | -2.77% [-13.97, +5.79]<br>Δ -0.109 ms |
| PT Sans | text/reflow | GPU completion | 2.927 | 2.852 | -1.17% [-7.23, +3.36]<br>Δ -0.033 ms | +1.70% [-1.30, +4.88]<br>Δ +0.047 ms | -2.07% [-7.26, +3.93]<br>Δ -0.060 ms |
| PT Sans | text/size_advance | GPU completion | 11.365 | 10.245 | -5.18% [-13.28, +1.91]<br>Δ -0.527 ms | +1.54% [-2.15, +4.47]<br>Δ +0.147 ms | -0.72% [-4.17, +5.23]<br>Δ -0.071 ms |
| PT Sans | text/size_return | GPU completion | 0.871 | 0.913 | +1.08% [-12.74, +17.53]<br>Δ -4.370 µs | +0.92% [-11.78, +10.29]<br>Δ +8.059 µs | +10.83% [-6.54, +15.32]<br>Δ +0.084 ms |
| PT Sans | text/x_advance | GPU completion | 1.601 | 1.636 | -4.60% [-8.58, +6.12]<br>Δ -0.091 ms | -1.59% [-8.62, +8.46]<br>Δ -0.024 ms | +7.12% [-0.70, +10.88]<br>Δ +0.106 ms |
| PT Sans | text/x_return | GPU completion | 0.777 | 0.768 | +2.09% [-11.46, +12.40]<br>Δ +0.014 ms | -3.83% [-7.67, +2.91]<br>Δ -0.035 ms | +2.95% [-9.45, +11.55]<br>Δ +0.022 ms |
| PT Sans | text/y_advance | GPU completion | 0.744 | 0.713 | -1.01% [-15.55, +9.49]<br>Δ -5.948 µs | -0.36% [-10.35, +8.79]<br>Δ -3.138 µs | +7.54% [-10.61, +10.98]<br>Δ +0.055 ms |
| Roboto Flex | demo/pan | GPU completion | 0.958 | 0.940 | -1.06% [-3.48, +1.94]<br>Δ -0.013 ms | -1.29% [-5.79, +4.80]<br>Δ -0.012 ms | -1.90% [-18.85, +0.72]<br>Δ -0.018 ms |
| Roboto Flex | demo/zoom_in | GPU completion | 4.225 | 3.908 | -4.82% [-9.60, +1.02]<br>Δ -0.205 ms | +0.07% [-11.85, +13.24]<br>Δ +0.012 ms | -3.93% [-11.17, -0.72]<br>Δ -0.146 ms |
| Roboto Flex | demo/zoom_out | GPU completion | 2.892 | 3.076 | -0.16% [-3.32, +2.34]<br>Δ -6.267 µs | -1.17% [-4.58, +2.22]<br>Δ -0.035 ms | -1.78% [-17.41, +3.30]<br>Δ -0.048 ms |
| Roboto Flex | font_variations/slant_advance | GPU completion | 1.670 | 1.402 | -3.37% [-21.31, +2.98]<br>Δ -0.055 ms | -0.15% [-29.46, +3.48]<br>Δ -6.454 µs | -1.36% [-16.39, +1.43]<br>Δ -0.017 ms |
| Roboto Flex | font_variations/slant_return | GPU completion | 0.332 | 0.323 | -1.76% [-12.41, +1.41]<br>Δ -5.240 µs | -3.09% [-10.75, +2.02]<br>Δ -0.011 ms | -5.20% [-23.01, +3.94]<br>Δ -0.015 ms |
| Roboto Flex | font_variations/weight_advance | GPU completion | 1.536 | 1.656 | +1.91% [-4.43, +10.97]<br>Δ +0.038 ms | +3.99% [-21.53, +12.76]<br>Δ +0.064 ms | -3.65% [-20.63, +7.01]<br>Δ -0.053 ms |
| Roboto Flex | font_variations/weight_return | GPU completion | 0.301 | 0.299 | -1.40% [-9.12, +1.21]<br>Δ -4.166 µs | -8.72% [-17.64, +1.58]<br>Δ -0.026 ms | +1.15% [-10.57, +4.58]<br>Δ +3.153 µs |
| Roboto Flex | text/reflow | GPU completion | 2.830 | 2.872 | +1.42% [-4.34, +3.24]<br>Δ +0.039 ms | -0.043% [-4.71, +1.91]<br>Δ -1.062 µs | -0.63% [-4.39, +2.29]<br>Δ -0.017 ms |
| Roboto Flex | text/size_advance | GPU completion | 10.660 | 10.094 | -3.66% [-12.14, -1.30]<br>Δ -0.371 ms | -0.30% [-10.84, +2.00]<br>Δ -0.032 ms | -0.75% [-3.27, +0.19]<br>Δ -0.077 ms |
| Roboto Flex | text/size_return | GPU completion | 0.891 | 0.828 | -2.47% [-11.71, +5.04]<br>Δ -0.018 ms | -3.46% [-10.76, +10.80]<br>Δ -0.028 ms | -5.86% [-12.61, +0.23]<br>Δ -0.049 ms |
| Roboto Flex | text/x_advance | GPU completion | 1.566 | 1.457 | -5.92% [-11.62, -0.87]<br>Δ -0.091 ms | -15.86% [-20.98, -4.69]<br>Δ -0.263 ms | -0.71% [-5.44, +7.10]<br>Δ -6.019 µs |
| Roboto Flex | text/x_return | GPU completion | 0.793 | 0.809 | -0.18% [-7.80, +7.15]<br>Δ -4.729 µs | -6.93% [-11.93, +0.005]<br>Δ -0.076 ms | -0.54% [-5.42, +6.34]<br>Δ -4.739 µs |
| Roboto Flex | text/y_advance | GPU completion | 0.721 | 0.732 | +4.95% [-5.97, +8.16]<br>Δ +0.034 ms | -4.68% [-9.10, +8.87]<br>Δ -0.034 ms | -1.99% [-9.44, +3.81]<br>Δ -0.014 ms |
| Vollkorn | demo/pan | GPU completion | 1.217 | 1.297 | +3.06% [-11.26, +12.04]<br>Δ +0.040 ms | -3.59% [-20.90, +21.81]<br>Δ -0.038 ms | +4.00% [-0.89, +24.91]<br>Δ +0.046 ms |
| Vollkorn | demo/zoom_in | GPU completion | 10.097 | 7.651 | -22.14% [-26.83, -20.30]<br>Δ -2.265 ms | -0.96% [-4.12, +2.09]<br>Δ -0.080 ms | +1.15% [-3.18, +12.87]<br>Δ +0.088 ms |
| Vollkorn | demo/zoom_out | GPU completion | 7.345 | 5.348 | -23.10% [-29.98, -19.08]<br>Δ -1.634 ms | +3.58% [-2.66, +5.53]<br>Δ +0.183 ms | +2.36% [-6.77, +8.35]<br>Δ +0.120 ms |
| Vollkorn | text/reflow | GPU completion | 3.778 | 3.811 | +1.53% [-1.25, +2.64]<br>Δ +0.055 ms | +0.18% [-3.43, +3.48]<br>Δ +6.403 µs | +1.27% [-0.20, +4.40]<br>Δ +0.049 ms |
| Vollkorn | text/size_advance | GPU completion | 18.199 | 13.971 | -23.54% [-25.29, -20.68]<br>Δ -4.367 ms | -1.14% [-1.66, +2.02]<br>Δ -0.157 ms | +1.63% [+0.49, +5.13]<br>Δ +0.214 ms |
| Vollkorn | text/size_return | GPU completion | 0.937 | 0.941 | +6.58% [-9.57, +12.79]<br>Δ +0.061 ms | +2.45% [-9.09, +7.39]<br>Δ +0.020 ms | +5.15% [+0.64, +9.52]<br>Δ +0.047 ms |
| Vollkorn | text/x_advance | GPU completion | 2.043 | 1.577 | -19.96% [-21.63, -14.90]<br>Δ -0.373 ms | +4.48% [-6.86, +17.61]<br>Δ +0.062 ms | +0.58% [-1.92, +6.94]<br>Δ +8.129 µs |
| Vollkorn | text/x_return | GPU completion | 0.841 | 0.863 | +1.51% [-2.85, +8.20]<br>Δ +0.013 ms | -4.30% [-7.94, +4.05]<br>Δ -0.033 ms | +4.01% [-1.66, +11.87]<br>Δ +0.029 ms |
| Vollkorn | text/y_advance | GPU completion | 0.759 | 0.768 | +5.62% [-0.56, +9.45]<br>Δ +0.037 ms | -0.89% [-10.95, +10.83]<br>Δ -6.215 µs | +6.31% [-2.27, +23.55]<br>Δ +0.049 ms |

## Controlled population, reuse and miss-churn phases

| Font | Scene / phase | Measurement | Master ms | Final ms | Final/master | Fixes 4–5/prior | Final/fixes 4–5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PT Sans | grid_pollution/hot_first | CPU draw | 0.469 | 0.413 | -12.46% [-12.69, -9.68]<br>Δ -0.059 ms | -0.66% [-1.28, +0.05]<br>Δ -2.771 µs | +1.17% [-1.01, +2.65]<br>Δ +4.771 µs |
| PT Sans | grid_pollution/hot_return | CPU draw | 0.404 | 0.393 | -2.94% [-4.01, -2.02]<br>Δ -0.012 ms | +0.23% [-0.90, +2.14]<br>Δ +0.917 µs | -0.90% [-1.89, -0.44]<br>Δ -3.562 µs |
| PT Sans | grid_pollution/hot_second | CPU draw | 0.386 | 0.148 | -61.29% [-62.67, -60.93]<br>Δ -0.238 ms | +1.59% [-1.76, +4.18]<br>Δ +2.291 µs | +0.10% [-2.79, +3.91]<br>Δ +0.145 µs |
| PT Sans | grid_pollution/pollution | CPU draw | 0.390 | 0.381 | -1.99% [-2.81, -1.76]<br>Δ -7.675 µs | +0.57% [-0.29, +0.82]<br>Δ +2.158 µs | -0.72% [-1.33, -0.30]<br>Δ -2.762 µs |
| PT Sans | grid_singleton/once | CPU draw | 0.474 | 0.421 | -11.37% [-13.51, -10.04]<br>Δ -0.055 ms | -1.09% [-1.56, -0.031]<br>Δ -4.667 µs | -0.56% [-2.54, +0.005]<br>Δ -2.354 µs |
| PT Sans | grid_two_phases/first | CPU draw | 0.426 | 0.372 | -12.35% [-13.72, -11.49]<br>Δ -0.053 ms | +0.68% [-0.61, +2.28]<br>Δ +2.521 µs | -0.98% [-2.27, -0.07]<br>Δ -3.625 µs |
| PT Sans | grid_two_phases/second | CPU draw | 0.380 | 0.140 | -63.61% [-64.35, -62.13]<br>Δ -0.240 ms | +5.21% [+1.44, +8.20]<br>Δ +7.230 µs | -4.31% [-9.48, +0.28]<br>Δ -6.375 µs |
| PT Sans | grid_unique_sizes/sweep | CPU draw | 0.377 | 0.369 | -1.86% [-2.15, -1.52]<br>Δ -7.040 µs | +0.63% [+0.015, +1.67]<br>Δ +2.314 µs | -0.62% [-0.92, +0.47]<br>Δ -2.281 µs |
| Roboto Flex | grid_pollution/hot_first | CPU draw | 0.222 | 0.170 | -24.43% [-27.47, -21.84]<br>Δ -0.055 ms | -2.79% [-4.52, +0.27]<br>Δ -4.667 µs | +4.57% [+2.26, +6.68]<br>Δ +7.459 µs |
| Roboto Flex | grid_pollution/hot_return | CPU draw | 0.219 | 0.208 | -5.49% [-7.73, +0.30]<br>Δ -0.012 ms | +1.78% [-2.72, +3.33]<br>Δ +3.730 µs | +1.02% [-4.64, +3.52]<br>Δ +2.250 µs |
| Roboto Flex | grid_pollution/hot_second | CPU draw | 0.167 | 0.130 | -21.87% [-23.63, -19.37]<br>Δ -0.037 ms | -2.04% [-5.76, +0.18]<br>Δ -2.709 µs | +0.24% [-2.54, +2.84]<br>Δ +0.313 µs |
| Roboto Flex | grid_pollution/pollution | CPU draw | 0.199 | 0.192 | -4.03% [-5.08, -2.87]<br>Δ -8.083 µs | -0.19% [-0.92, +0.52]<br>Δ -0.364 µs | +0.40% [-0.49, +1.24]<br>Δ +0.760 µs |
| Roboto Flex | grid_singleton/once | CPU draw | 0.244 | 0.189 | -22.90% [-25.34, -22.20]<br>Δ -0.057 ms | -2.75% [-4.78, +0.61]<br>Δ -5.374 µs | +2.65% [+1.17, +4.18]<br>Δ +4.855 µs |
| Roboto Flex | grid_two_phases/first | CPU draw | 0.203 | 0.147 | -26.11% [-30.38, -23.49]<br>Δ -0.055 ms | +4.06% [+1.15, +6.21]<br>Δ +5.959 µs | -3.32% [-5.39, +1.04]<br>Δ -5.124 µs |
| Roboto Flex | grid_two_phases/second | CPU draw | 0.175 | 0.135 | -20.03% [-22.34, -18.61]<br>Δ -0.036 ms | +2.74% [-0.11, +5.89]<br>Δ +3.666 µs | +0.86% [-3.81, +2.77]<br>Δ +1.103 µs |
| Roboto Flex | grid_unique_sizes/sweep | CPU draw | 0.183 | 0.173 | -5.72% [-6.53, -4.88]<br>Δ -0.011 ms | +0.45% [-0.83, +1.01]<br>Δ +0.791 µs | -1.08% [-2.03, +0.07]<br>Δ -1.885 µs |
| Roboto Flex | grid_unique_variations/sweep | CPU draw | 0.246 | 0.171 | -30.53% [-31.10, -29.40]<br>Δ -0.075 ms | +0.29% [-0.90, +1.05]<br>Δ +0.505 µs | -0.34% [-0.79, +0.09]<br>Δ -0.590 µs |
| Vollkorn | grid_pollution/hot_first | CPU draw | 1.602 | 1.512 | -4.96% [-5.96, -4.02]<br>Δ -0.080 ms | -0.35% [-1.35, +0.43]<br>Δ -5.334 µs | +0.77% [-0.82, +1.34]<br>Δ +0.012 ms |
| Vollkorn | grid_pollution/hot_return | CPU draw | 1.521 | 1.497 | -1.54% [-2.24, -0.29]<br>Δ -0.023 ms | -0.25% [-0.91, +0.69]<br>Δ -3.812 µs | +0.28% [-0.55, +0.86]<br>Δ +4.188 µs |
| Vollkorn | grid_pollution/hot_second | CPU draw | 1.456 | 0.197 | -86.41% [-86.52, -86.14]<br>Δ -1.264 ms | +0.80% [-1.68, +2.09]<br>Δ +1.562 µs | -0.16% [-2.28, +3.77]<br>Δ -0.312 µs |
| Vollkorn | grid_pollution/pollution | CPU draw | 1.517 | 1.503 | -0.82% [-1.03, +0.029]<br>Δ -0.012 ms | +0.049% [-0.49, +0.43]<br>Δ +0.731 µs | +0.42% [+0.12, +0.66]<br>Δ +6.250 µs |
| Vollkorn | grid_singleton/once | CPU draw | 1.611 | 1.525 | -5.18% [-5.95, -4.59]<br>Δ -0.083 ms | -1.16% [-1.72, -0.43]<br>Δ -0.018 ms | +0.50% [-0.32, +1.09]<br>Δ +7.520 µs |
| Vollkorn | grid_two_phases/first | CPU draw | 1.545 | 1.474 | -4.68% [-5.89, -4.05]<br>Δ -0.073 ms | -0.06% [-0.77, +0.65]<br>Δ -1.041 µs | +0.66% [-0.87, +1.31]<br>Δ +9.896 µs |
| Vollkorn | grid_two_phases/second | CPU draw | 1.462 | 0.190 | -86.92% [-87.11, -86.60]<br>Δ -1.268 ms | +2.50% [-1.32, +2.94]<br>Δ +4.771 µs | -1.58% [-4.71, +1.75]<br>Δ -3.084 µs |
| Vollkorn | grid_unique_sizes/sweep | CPU draw | 1.496 | 1.481 | -0.97% [-1.61, +0.19]<br>Δ -0.014 ms | +0.46% [-0.08, +1.02]<br>Δ +6.671 µs | +0.30% [-0.45, +0.93]<br>Δ +4.380 µs |
| PT Sans | grid_pollution/hot_first | GPU completion | 3.353 | 2.981 | -6.85% [-12.45, +0.25]<br>Δ -0.250 ms | -1.35% [-5.18, +3.17]<br>Δ -0.042 ms | -4.37% [-10.21, +8.98]<br>Δ -0.131 ms |
| PT Sans | grid_pollution/hot_return | GPU completion | 1.252 | 1.508 | +8.69% [-1.73, +28.34]<br>Δ +0.141 ms | +0.07% [-5.87, +8.43]<br>Δ +0.561 µs | +9.84% [-11.92, +35.05]<br>Δ +0.117 ms |
| PT Sans | grid_pollution/hot_second | GPU completion | 1.499 | 0.911 | -31.23% [-43.97, -17.45]<br>Δ -0.423 ms | -0.64% [-9.67, +5.37]<br>Δ -9.020 µs | +1.79% [-17.50, +22.76]<br>Δ +0.016 ms |
| PT Sans | grid_pollution/pollution | GPU completion | 1.365 | 1.346 | -4.33% [-9.50, +1.47]<br>Δ -0.057 ms | -3.50% [-6.22, +0.11]<br>Δ -0.053 ms | +1.48% [-5.65, +11.65]<br>Δ +0.019 ms |
| PT Sans | grid_singleton/once | GPU completion | 3.484 | 3.289 | +0.44% [-7.39, +5.45]<br>Δ +0.016 ms | +5.44% [-1.93, +11.07]<br>Δ +0.160 ms | -4.56% [-9.18, +5.42]<br>Δ -0.152 ms |
| PT Sans | grid_two_phases/first | GPU completion | 3.411 | 3.192 | -0.36% [-10.42, +4.95]<br>Δ -0.013 ms | +2.41% [-5.27, +14.62]<br>Δ +0.078 ms | -3.49% [-7.72, +4.48]<br>Δ -0.119 ms |
| PT Sans | grid_two_phases/second | GPU completion | 1.711 | 1.210 | -16.73% [-46.78, -8.75]<br>Δ -0.278 ms | +14.72% [+0.99, +49.53]<br>Δ +0.123 ms | -1.79% [-30.29, +7.06]<br>Δ -0.025 ms |
| PT Sans | grid_unique_sizes/sweep | GPU completion | 1.569 | 1.553 | +0.14% [-9.16, +1.94]<br>Δ +2.757 µs | -1.44% [-5.52, +3.51]<br>Δ -0.019 ms | +4.69% [-14.79, +10.85]<br>Δ +0.064 ms |
| Roboto Flex | grid_pollution/hot_first | GPU completion | 2.902 | 2.796 | -2.28% [-14.98, +0.33]<br>Δ -0.065 ms | -0.18% [-17.51, +5.52]<br>Δ -4.438 µs | -2.80% [-12.73, +2.69]<br>Δ -0.087 ms |
| Roboto Flex | grid_pollution/hot_return | GPU completion | 0.998 | 1.026 | -1.65% [-3.48, +5.61]<br>Δ -0.019 ms | +1.74% [-15.90, +7.66]<br>Δ +0.028 ms | +0.07% [-4.89, +3.09]<br>Δ +0.729 µs |
| Roboto Flex | grid_pollution/hot_second | GPU completion | 0.944 | 0.951 | -3.11% [-9.20, +5.04]<br>Δ -0.027 ms | -7.15% [-18.01, +0.92]<br>Δ -0.080 ms | -0.23% [-7.43, +8.56]<br>Δ -1.792 µs |
| Roboto Flex | grid_pollution/pollution | GPU completion | 1.156 | 1.036 | -6.45% [-19.69, +4.53]<br>Δ -0.083 ms | -4.08% [-15.47, +6.53]<br>Δ -0.041 ms | -0.51% [-19.64, +1.23]<br>Δ -7.435 µs |
| Roboto Flex | grid_singleton/once | GPU completion | 3.341 | 3.121 | -2.53% [-5.65, -0.12]<br>Δ -0.073 ms | -5.05% [-12.90, +1.05]<br>Δ -0.165 ms | -0.016% [-5.36, +6.72]<br>Δ -1.021 µs |
| Roboto Flex | grid_two_phases/first | GPU completion | 2.924 | 3.019 | -1.69% [-6.45, +2.99]<br>Δ -0.050 ms | -0.39% [-9.58, +2.20]<br>Δ -0.010 ms | +2.00% [-5.54, +4.61]<br>Δ +0.053 ms |
| Roboto Flex | grid_two_phases/second | GPU completion | 0.989 | 1.470 | -7.58% [-9.63, +19.69]<br>Δ -0.090 ms | -3.80% [-17.74, +3.70]<br>Δ -0.071 ms | -2.06% [-20.65, +2.12]<br>Δ -0.022 ms |
| Roboto Flex | grid_unique_sizes/sweep | GPU completion | 1.262 | 1.156 | -4.92% [-13.26, -3.32]<br>Δ -0.066 ms | -3.43% [-6.78, +3.18]<br>Δ -0.049 ms | -4.94% [-13.17, +0.016]<br>Δ -0.058 ms |
| Roboto Flex | grid_unique_variations/sweep | GPU completion | 1.253 | 1.077 | -8.70% [-22.34, +1.15]<br>Δ -0.091 ms | -6.82% [-20.57, +2.84]<br>Δ -0.096 ms | -1.01% [-8.21, +9.79]<br>Δ -0.017 ms |
| Vollkorn | grid_pollution/hot_first | GPU completion | 4.603 | 4.420 | -2.46% [-7.57, +1.93]<br>Δ -0.118 ms | +0.64% [-2.05, +7.09]<br>Δ +0.028 ms | +1.04% [-1.16, +12.56]<br>Δ +0.043 ms |
| Vollkorn | grid_pollution/hot_return | GPU completion | 3.224 | 3.150 | -0.88% [-7.95, +10.44]<br>Δ -0.028 ms | +0.62% [-2.27, +4.06]<br>Δ +0.018 ms | +1.86% [-1.54, +8.86]<br>Δ +0.058 ms |
| Vollkorn | grid_pollution/hot_second | GPU completion | 3.061 | 1.158 | -60.95% [-64.71, -53.94]<br>Δ -1.701 ms | +4.07% [-4.96, +31.74]<br>Δ +0.037 ms | -0.032% [-11.54, +4.77]<br>Δ -0.584 µs |
| Vollkorn | grid_pollution/pollution | GPU completion | 3.219 | 3.108 | -0.88% [-3.63, +3.97]<br>Δ -0.025 ms | +0.18% [-5.38, +2.48]<br>Δ +4.238 µs | +3.50% [+1.10, +7.73]<br>Δ +0.104 ms |
| Vollkorn | grid_singleton/once | GPU completion | 4.688 | 4.784 | +1.49% [-4.94, +6.31]<br>Δ +0.067 ms | +1.20% [-1.29, +9.22]<br>Δ +0.058 ms | +1.30% [-1.19, +10.50]<br>Δ +0.054 ms |
| Vollkorn | grid_two_phases/first | GPU completion | 4.650 | 4.540 | -4.56% [-10.59, +2.71]<br>Δ -0.233 ms | -0.07% [-8.46, +7.38]<br>Δ -3.666 µs | +2.69% [-0.72, +7.99]<br>Δ +0.113 ms |
| Vollkorn | grid_two_phases/second | GPU completion | 3.208 | 1.537 | -53.10% [-62.75, -50.13]<br>Δ -1.753 ms | +2.01% [-1.81, +44.39]<br>Δ +0.033 ms | -0.27% [-18.41, +4.30]<br>Δ -5.479 µs |
| Vollkorn | grid_unique_sizes/sweep | GPU completion | 3.204 | 3.171 | -1.72% [-3.19, +3.14]<br>Δ -0.055 ms | -0.37% [-2.20, +4.38]<br>Δ -0.010 ms | +2.10% [-0.48, +3.65]<br>Δ +0.061 ms |

GPU completion includes CPU drawing, submission and waiting; it is not a GPU timestamp. Variation-scene/unique-weight repeats under other regular-font factors are the same Roboto control, so tables show them once. Every controlled frame retains exactly 94 fresh atlas keys. Unique sizes/weights expose low reuse; pollution includes the hot frames, 64-size sweep and hot return.

## Complete reported sequences

Each controlled sequence includes its population and churn. Example totals include every reported phase, but exclude 119 unreported warmup frames and are not launch-to-end durations. Each trial is summed before process medians and pairing.

| Font | Reported sequence | Frames | Measurement | Master ms | Final ms | Final/master | Fixes 4–5/prior | Final/fixes 4–5 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PT Sans | demo | 65 | CPU draw | 47.778 | 41.209 | -13.47% [-14.26, -13.29]<br>Δ -6.449 ms | +0.36% [-0.33, +0.60]<br>Δ +0.149 ms | -0.15% [-1.03, +0.55]<br>Δ -0.061 ms |
| PT Sans | Hot + 64-size pollution + return | 67 | CPU draw | 26.247 | 25.328 | -3.11% [-3.93, -2.94]<br>Δ -0.810 ms | +0.55% [-0.18, +1.06]<br>Δ +0.141 ms | -0.78% [-1.46, -0.36]<br>Δ -0.198 ms |
| PT Sans | 94 one-use glyphs | 1 | CPU draw | 0.474 | 0.421 | -11.37% [-13.51, -10.04]<br>Δ -0.055 ms | -1.09% [-1.56, -0.031]<br>Δ -4.667 µs | -0.56% [-2.54, +0.005]<br>Δ -2.354 µs |
| PT Sans | Population + second phase | 2 | CPU draw | 0.806 | 0.516 | -36.19% [-36.68, -35.67]<br>Δ -0.293 ms | +1.53% [-0.64, +2.67]<br>Δ +7.876 µs | -1.66% [-2.40, -0.55]<br>Δ -8.771 µs |
| PT Sans | 32 unique sizes | 32 | CPU draw | 12.058 | 11.811 | -1.86% [-2.15, -1.52]<br>Δ -0.225 ms | +0.63% [+0.015, +1.67]<br>Δ +0.074 ms | -0.62% [-0.92, +0.47]<br>Δ -0.073 ms |
| PT Sans | text | 88 | CPU draw | 101.471 | 94.548 | -7.00% [-7.31, -6.76]<br>Δ -7.064 ms | +0.44% [+0.07, +0.60]<br>Δ +0.420 ms | +0.27% [-0.33, +0.50]<br>Δ +0.249 ms |
| Roboto Flex | demo | 65 | CPU draw | 36.757 | 35.893 | -2.30% [-4.06, -1.89]<br>Δ -0.867 ms | +0.22% [-0.59, +1.22]<br>Δ +0.077 ms | +0.29% [-0.59, +0.73]<br>Δ +0.103 ms |
| Roboto Flex | font_variations | 63 | CPU draw | 10.505 | 10.301 | -2.50% [-3.67, -1.65]<br>Δ -0.263 ms | -0.20% [-1.07, +0.45]<br>Δ -0.021 ms | +0.64% [+0.05, +2.52]<br>Δ +0.065 ms |
| Roboto Flex | Hot + 64-size pollution + return | 67 | CPU draw | 13.356 | 12.765 | -4.61% [-5.44, -3.30]<br>Δ -0.620 ms | -0.26% [-0.70, +0.48]<br>Δ -0.033 ms | +0.17% [-0.40, +1.47]<br>Δ +0.022 ms |
| Roboto Flex | 94 one-use glyphs | 1 | CPU draw | 0.244 | 0.189 | -22.90% [-25.34, -22.20]<br>Δ -0.057 ms | -2.75% [-4.78, +0.61]<br>Δ -5.374 µs | +2.65% [+1.17, +4.18]<br>Δ +4.855 µs |
| Roboto Flex | Population + second phase | 2 | CPU draw | 0.375 | 0.285 | -23.37% [-27.51, -21.71]<br>Δ -0.089 ms | +3.19% [-0.68, +6.62]<br>Δ +8.667 µs | -1.34% [-3.36, +0.24]<br>Δ -3.958 µs |
| Roboto Flex | 32 unique sizes | 32 | CPU draw | 5.856 | 5.545 | -5.72% [-6.53, -4.88]<br>Δ -0.338 ms | +0.45% [-0.83, +1.01]<br>Δ +0.025 ms | -1.08% [-2.03, +0.07]<br>Δ -0.060 ms |
| Roboto Flex | 32 unique weights | 32 | CPU draw | 7.863 | 5.479 | -30.53% [-31.10, -29.40]<br>Δ -2.404 ms | +0.29% [-0.90, +1.05]<br>Δ +0.016 ms | -0.34% [-0.79, +0.09]<br>Δ -0.019 ms |
| Roboto Flex | text | 88 | CPU draw | 94.783 | 92.400 | -2.51% [-3.06, -1.69]<br>Δ -2.383 ms | +0.61% [-0.041, +1.57]<br>Δ +0.563 ms | +0.09% [-0.52, +0.69]<br>Δ +0.079 ms |
| Vollkorn | demo | 65 | CPU draw | 138.123 | 93.036 | -32.68% [-33.05, -32.45]<br>Δ -44.926 ms | -0.32% [-1.00, -0.16]<br>Δ -0.300 ms | +0.64% [+0.25, +1.69]<br>Δ +0.596 ms |
| Vollkorn | Hot + 64-size pollution + return | 67 | CPU draw | 101.637 | 99.366 | -2.06% [-2.36, -1.32]<br>Δ -2.067 ms | +0.032% [-0.47, +0.41]<br>Δ +0.031 ms | +0.36% [+0.17, +0.68]<br>Δ +0.349 ms |
| Vollkorn | 94 one-use glyphs | 1 | CPU draw | 1.611 | 1.525 | -5.18% [-5.95, -4.59]<br>Δ -0.083 ms | -1.16% [-1.72, -0.43]<br>Δ -0.018 ms | +0.50% [-0.32, +1.09]<br>Δ +7.520 µs |
| Vollkorn | Population + second phase | 2 | CPU draw | 3.013 | 1.662 | -44.69% [-45.01, -44.21]<br>Δ -1.344 ms | +0.16% [-0.60, +0.65]<br>Δ +2.666 µs | +0.015% [-0.70, +0.73]<br>Δ +0.250 µs |
| Vollkorn | 32 unique sizes | 32 | CPU draw | 47.861 | 47.377 | -0.97% [-1.61, +0.19]<br>Δ -0.459 ms | +0.46% [-0.08, +1.02]<br>Δ +0.213 ms | +0.30% [-0.45, +0.93]<br>Δ +0.140 ms |
| Vollkorn | text | 88 | CPU draw | 195.363 | 142.033 | -27.33% [-27.51, -27.20]<br>Δ -53.331 ms | +1.12% [+0.55, +1.66]<br>Δ +1.571 ms | -1.02% [-1.73, -0.82]<br>Δ -1.467 ms |
| PT Sans | demo | 65 | GPU completion | 158.181 | 159.837 | -5.77% [-10.43, -2.51]<br>Δ -9.693 ms | +0.48% [-2.16, +5.03]<br>Δ +0.668 ms | -0.79% [-7.16, +5.43]<br>Δ -1.095 ms |
| PT Sans | Hot + 64-size pollution + return | 67 | GPU completion | 92.902 | 91.884 | -4.60% [-9.82, +1.33]<br>Δ -3.998 ms | -2.97% [-6.07, +0.24]<br>Δ -3.089 ms | +1.56% [-5.91, +11.23]<br>Δ +1.386 ms |
| PT Sans | 94 one-use glyphs | 1 | GPU completion | 3.484 | 3.289 | +0.44% [-7.39, +5.45]<br>Δ +0.016 ms | +5.44% [-1.93, +11.07]<br>Δ +0.160 ms | -4.56% [-9.18, +5.42]<br>Δ -0.152 ms |
| PT Sans | Population + second phase | 2 | GPU completion | 5.216 | 4.495 | -6.29% [-24.19, -1.37]<br>Δ -0.330 ms | +4.61% [-3.24, +22.23]<br>Δ +0.191 ms | -0.59% [-15.79, +5.20]<br>Δ -0.023 ms |
| PT Sans | 32 unique sizes | 32 | GPU completion | 50.219 | 49.702 | +0.14% [-9.16, +1.94]<br>Δ +0.088 ms | -1.44% [-5.52, +3.51]<br>Δ -0.616 ms | +4.69% [-14.79, +10.85]<br>Δ +2.055 ms |
| PT Sans | text | 88 | GPU completion | 238.046 | 222.242 | -4.29% [-10.49, +4.84]<br>Δ -9.822 ms | +0.50% [-0.85, +3.90]<br>Δ +1.109 ms | +0.64% [-2.98, +6.19]<br>Δ +1.385 ms |
| Roboto Flex | demo | 65 | GPU completion | 137.835 | 132.365 | -0.17% [-5.31, +2.35]<br>Δ -0.228 ms | -0.97% [-6.35, +4.51]<br>Δ -1.368 ms | -4.05% [-12.36, +0.43]<br>Δ -5.159 ms |
| Roboto Flex | font_variations | 63 | GPU completion | 45.038 | 44.073 | -0.32% [-7.97, +4.49]<br>Δ -0.133 ms | -1.39% [-14.14, +2.28]<br>Δ -0.565 ms | -0.28% [-9.71, +3.77]<br>Δ -0.118 ms |
| Roboto Flex | Hot + 64-size pollution + return | 67 | GPU completion | 79.002 | 71.339 | -5.88% [-19.29, +4.44]<br>Δ -5.158 ms | -3.54% [-15.92, +5.86]<br>Δ -2.414 ms | -0.37% [-18.79, +1.28]<br>Δ -0.412 ms |
| Roboto Flex | 94 one-use glyphs | 1 | GPU completion | 3.341 | 3.121 | -2.53% [-5.65, -0.12]<br>Δ -0.073 ms | -5.05% [-12.90, +1.05]<br>Δ -0.165 ms | -0.016% [-5.36, +6.72]<br>Δ -1.021 µs |
| Roboto Flex | Population + second phase | 2 | GPU completion | 3.891 | 4.469 | -3.91% [-7.58, +9.22]<br>Δ -0.173 ms | -0.06% [-16.33, +7.55]<br>Δ -0.604 µs | +0.88% [-5.63, +3.12]<br>Δ +0.031 ms |
| Roboto Flex | 32 unique sizes | 32 | GPU completion | 40.396 | 36.990 | -4.92% [-13.26, -3.32]<br>Δ -2.102 ms | -3.43% [-6.78, +3.18]<br>Δ -1.579 ms | -4.94% [-13.17, +0.016]<br>Δ -1.866 ms |
| Roboto Flex | 32 unique weights | 32 | GPU completion | 40.107 | 34.456 | -8.70% [-22.34, +1.15]<br>Δ -2.926 ms | -6.82% [-20.57, +2.84]<br>Δ -3.065 ms | -1.01% [-8.21, +9.79]<br>Δ -0.533 ms |
| Roboto Flex | text | 88 | GPU completion | 226.991 | 221.987 | -1.26% [-8.60, -0.63]<br>Δ -2.778 ms | +0.07% [-8.50, +1.29]<br>Δ +0.161 ms | -1.46% [-3.36, +0.77]<br>Δ -3.202 ms |
| Vollkorn | demo | 65 | GPU completion | 271.123 | 219.181 | -19.07% [-21.85, -16.04]<br>Δ -49.615 ms | +0.91% [-0.37, +2.62]<br>Δ +2.041 ms | +2.36% [-2.76, +8.47]<br>Δ +4.843 ms |
| Vollkorn | Hot + 64-size pollution + return | 67 | GPU completion | 217.260 | 207.616 | -1.59% [-4.07, +3.09]<br>Δ -3.016 ms | -0.11% [-5.62, +2.64]<br>Δ -0.192 ms | +3.66% [+1.07, +7.62]<br>Δ +7.478 ms |
| Vollkorn | 94 one-use glyphs | 1 | GPU completion | 4.688 | 4.784 | +1.49% [-4.94, +6.31]<br>Δ +0.067 ms | +1.20% [-1.29, +9.22]<br>Δ +0.058 ms | +1.30% [-1.19, +10.50]<br>Δ +0.054 ms |
| Vollkorn | Population + second phase | 2 | GPU completion | 7.799 | 6.156 | -23.72% [-30.64, -15.84]<br>Δ -1.993 ms | +2.61% [-7.63, +10.52]<br>Δ +0.161 ms | +3.64% [-6.22, +7.55]<br>Δ +0.174 ms |
| Vollkorn | 32 unique sizes | 32 | GPU completion | 102.537 | 101.457 | -1.72% [-3.19, +3.14]<br>Δ -1.749 ms | -0.37% [-2.20, +4.38]<br>Δ -0.328 ms | +2.10% [-0.48, +3.65]<br>Δ +1.966 ms |
| Vollkorn | text | 88 | GPU completion | 349.448 | 289.947 | -17.01% [-18.97, -15.52]<br>Δ -58.481 ms | -0.14% [-2.02, +2.80]<br>Δ -0.440 ms | +2.19% [+0.18, +4.38]<br>Δ +5.813 ms |

## Alustin renderer-thread CPU

First paint and filtered-search spans measure renderer-thread host work, not GPU-completion or display latency. Search can populate new atlas entries; it is not necessarily a fully warm redraw.

| Font | Backend | Frame | Master ms | Final ms | Final/master | Fixes 4–5/prior | Final/fixes 4–5 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Roboto Flex | WGPU | First paint | 14.833 | 14.401 | -3.74% [-5.86, -0.25]<br>Δ -0.560 ms | +1.39% [-2.27, +5.93]<br>Δ +0.196 ms | -1.03% [-2.92, +0.96]<br>Δ -0.147 ms |
| Roboto Flex | WGPU | Filtered search | 2.273 | 2.287 | +0.83% [-3.55, +6.47]<br>Δ +0.018 ms | +1.65% [-1.05, +6.31]<br>Δ +0.037 ms | +0.018% [-3.47, +5.31]<br>Δ +0.876 µs |
| Roboto Flex | OpenGL | First paint | 17.540 | 17.161 | -0.99% [-2.68, +0.017]<br>Δ -0.172 ms | +0.12% [-2.68, +3.02]<br>Δ +0.021 ms | +0.34% [-0.23, +1.21]<br>Δ +0.059 ms |
| Roboto Flex | OpenGL | Filtered search | 2.169 | 2.162 | -0.29% [-2.88, +2.12]<br>Δ -6.188 µs | +1.07% [-4.41, +3.98]<br>Δ +0.024 ms | +1.50% [-3.44, +4.15]<br>Δ +0.032 ms |
| Vollkorn | WGPU | First paint | 22.404 | 17.356 | -23.96% [-24.80, -21.45]<br>Δ -5.360 ms | -0.51% [-1.92, +2.54]<br>Δ -0.088 ms | -0.022% [-2.17, +0.70]<br>Δ -3.853 µs |
| Vollkorn | WGPU | Filtered search | 2.520 | 2.385 | -5.04% [-12.79, -0.79]<br>Δ -0.125 ms | -1.50% [-5.38, +3.54]<br>Δ -0.035 ms | +1.80% [-5.57, +7.01]<br>Δ +0.042 ms |
| Vollkorn | OpenGL | First paint | 25.666 | 21.123 | -18.19% [-20.25, -17.27]<br>Δ -4.736 ms | +0.22% [-1.53, +2.03]<br>Δ +0.046 ms | +2.15% [-0.10, +4.00]<br>Δ +0.446 ms |
| Vollkorn | OpenGL | Filtered search | 2.404 | 2.239 | -8.00% [-10.10, -4.56]<br>Δ -0.193 ms | -1.09% [-2.86, +1.21]<br>Δ -0.025 ms | -0.85% [-4.20, +5.13]<br>Δ -0.019 ms |
| PT Sans | WGPU | First paint | 15.315 | 14.428 | -6.80% [-7.88, -4.78]<br>Δ -1.027 ms | -1.32% [-2.62, +1.65]<br>Δ -0.196 ms | -0.009% [-2.71, +1.67]<br>Δ -1.500 µs |
| PT Sans | WGPU | Filtered search | 2.333 | 2.250 | -5.39% [-10.72, +1.66]<br>Δ -0.121 ms | -1.78% [-3.97, +3.41]<br>Δ -0.040 ms | +0.94% [-3.57, +6.81]<br>Δ +0.020 ms |
| PT Sans | OpenGL | First paint | 18.420 | 17.515 | -4.63% [-6.96, -2.49]<br>Δ -0.861 ms | +1.44% [-0.72, +2.42]<br>Δ +0.254 ms | +0.26% [-2.23, +2.03]<br>Δ +0.045 ms |
| PT Sans | OpenGL | Filtered search | 2.185 | 2.150 | -0.85% [-5.21, +3.65]<br>Δ -0.019 ms | +0.58% [-2.20, +2.46]<br>Δ +0.013 ms | -0.028% [-2.51, +4.88]<br>Δ -0.979 µs |

## Process high-water RSS

RSS includes the application, renderer, fonts, driver and transient work. It is not the outline cache alone or device VRAM. These cells show absolute paired MiB change and its preserved 95% interval.

| Font | Backend | Final/master | Fixes 4–5/prior | Final/fixes 4–5 |
| --- | --- | --- | --- | --- |
| Roboto Flex | WGPU | -0.250 [-0.664, +0.859] MiB | +0.375 [-0.742, +1.664] MiB | -0.062 [-1.391, +0.344] MiB |
| Roboto Flex | OpenGL | +0.219 [-0.031, +1.000] MiB | -0.086 [-1.367, +0.141] MiB | +0.992 [-0.680, +2.422] MiB |
| Vollkorn | WGPU | +0.500 [-0.625, +0.844] MiB | +0.945 [+0.062, +1.758] MiB | -0.672 [-1.727, +0.352] MiB |
| Vollkorn | OpenGL | -0.680 [-1.695, +0.461] MiB | -0.156 [-0.516, +0.859] MiB | -0.164 [-1.734, +1.453] MiB |
| PT Sans | WGPU | -0.656 [-1.523, -0.203] MiB | +0.031 [-0.477, +0.836] MiB | -0.367 [-1.414, +0.453] MiB |
| PT Sans | OpenGL | -0.234 [-0.625, +0.047] MiB | -0.328 [-0.750, +0.273] MiB | -0.156 [-0.492, +0.117] MiB |

## Targeted public-API cache boundary

Roboto working sets contain 3300/3440/3600 geometry keys across ten phase-specific fresh Canvas/atlas instances sharing one TextContext. Population is shown separately, reuse contains all nine later phases, and complete10 includes both. This targeted synthetic test models retained geometry across fresh atlases; it does not establish application latency or infer outline hits from atlas counts. Timing excludes font registration and Canvas creation/destruction. Every phase still rasterizes masks.

| Keys | Scope | Master ms | Final ms | Final/master | Fixes 4–5/prior | Final/fixes 4–5 |
| --- | --- | --- | --- | --- | --- | --- |
| 3300 | population | 7.529 | 7.194 | -4.41% [-6.93, -3.07]<br>Δ -0.332 ms | +0.22% [-0.22, +0.94]<br>Δ +0.015 ms | -0.009% [-0.79, +0.44]<br>Δ -0.604 µs |
| 3300 | reuse9 | 66.752 | 56.575 | -15.18% [-15.42, -14.83]<br>Δ -10.109 ms | -12.17% [-12.67, -11.81]<br>Δ -7.774 ms | +0.82% [+0.32, +1.17]<br>Δ +0.461 ms |
| 3300 | complete10 | 74.306 | 63.802 | -14.22% [-14.56, -13.77]<br>Δ -10.558 ms | -11.12% [-11.41, -10.65]<br>Δ -7.923 ms | +0.86% [+0.25, +1.04]<br>Δ +0.544 ms |
| 3440 | population | 7.907 | 7.655 | -3.02% [-4.04, -2.49]<br>Δ -0.237 ms | +0.16% [-0.06, +0.79]<br>Δ +0.012 ms | +0.73% [+0.47, +1.48]<br>Δ +0.055 ms |
| 3440 | reuse9 | 70.720 | 59.950 | -15.34% [-15.58, -14.76]<br>Δ -10.843 ms | -12.41% [-12.76, -12.03]<br>Δ -8.412 ms | +0.80% [+0.46, +1.30]<br>Δ +0.475 ms |
| 3440 | complete10 | 78.553 | 67.650 | -13.80% [-14.35, -13.59]<br>Δ -10.843 ms | -11.13% [-11.53, -10.72]<br>Δ -8.373 ms | +0.81% [+0.46, +1.21]<br>Δ +0.545 ms |
| 3600 | population | 8.457 | 8.158 | -3.88% [-4.23, -3.07]<br>Δ -0.331 ms | -0.09% [-1.37, +0.19]<br>Δ -7.042 µs | +0.74% [+0.50, +1.60]<br>Δ +0.060 ms |
| 3600 | reuse9 | 75.385 | 72.310 | -3.85% [-4.35, -3.66]<br>Δ -2.897 ms | -0.57% [-0.75, -0.37]<br>Δ -0.407 ms | +0.52% [+0.041, +1.03]<br>Δ +0.374 ms |
| 3600 | complete10 | 83.884 | 80.552 | -3.86% [-4.29, -3.53]<br>Δ -3.229 ms | -0.55% [-0.88, -0.37]<br>Δ -0.442 ms | +0.70% [+0.17, +1.07]<br>Δ +0.560 ms |

## Exploratory positive-interval audit

The following preserved intervals lie entirely above zero for a displayed comparison. This lists tiny absolute effects as well as larger ones. It is an exploratory selection of correlated phase/sequence/application/boundary observations, not an adjusted test of universal regression. Every uncertain or negative effect remains in the full tables/statistics.

| Observation | Comparison | Duration increase |
| --- | --- | --- |
| PT Sans cpu demo/first_paint | Fixes 4–5/prior | +0.48% [+0.033, +0.80]<br>Δ +8.396 µs |
| PT Sans cpu grid_two_phases/second | Fixes 4–5/prior | +5.21% [+1.44, +8.20]<br>Δ +7.230 µs |
| PT Sans cpu grid_unique_sizes/sweep | Fixes 4–5/prior | +0.63% [+0.015, +1.67]<br>Δ +2.314 µs |
| PT Sans cpu text/size_advance | Fixes 4–5/prior | +0.69% [+0.31, +1.10]<br>Δ +0.034 ms |
| PT Sans cpu text/size_return | Final/master | +3.01% [+1.64, +3.73]<br>Δ +7.998 µs |
| PT Sans cpu text/size_return | Final/fixes 4–5 | +2.07% [+1.13, +3.41]<br>Δ +5.467 µs |
| PT Sans cpu text/warm | Final/master | +3.15% [+2.54, +3.89]<br>Δ +7.758 µs |
| PT Sans cpu text/warm | Final/fixes 4–5 | +0.90% [+0.028, +1.53]<br>Δ +2.280 µs |
| PT Sans cpu text/x_advance | Final/fixes 4–5 | +1.49% [+0.97, +2.84]<br>Δ +5.329 µs |
| PT Sans cpu text/x_return | Final/master | +2.65% [+1.63, +3.61]<br>Δ +6.613 µs |
| PT Sans cpu text/x_return | Final/fixes 4–5 | +1.34% [+0.46, +1.85]<br>Δ +3.423 µs |
| PT Sans cpu text/y_advance | Final/master | +2.23% [+1.20, +3.29]<br>Δ +5.596 µs |
| PT Sans cpu text/y_advance | Final/fixes 4–5 | +1.18% [+0.78, +2.05]<br>Δ +2.967 µs |
| Roboto Flex cpu demo/first_paint | Final/fixes 4–5 | +1.44% [+0.22, +2.31]<br>Δ +0.020 ms |
| Roboto Flex cpu font_variations/warm | Final/fixes 4–5 | +1.43% [+0.15, +2.52]<br>Δ +0.524 µs |
| Roboto Flex cpu font_variations/weight_advance | Final/fixes 4–5 | +0.78% [+0.20, +3.12]<br>Δ +3.781 µs |
| Roboto Flex cpu grid_pollution/hot_first | Final/fixes 4–5 | +4.57% [+2.26, +6.68]<br>Δ +7.459 µs |
| Roboto Flex cpu grid_singleton/once | Final/fixes 4–5 | +2.65% [+1.17, +4.18]<br>Δ +4.855 µs |
| Roboto Flex cpu grid_two_phases/first | Fixes 4–5/prior | +4.06% [+1.15, +6.21]<br>Δ +5.959 µs |
| Roboto Flex cpu text/x_return | Final/master | +2.44% [+1.24, +3.03]<br>Δ +6.402 µs |
| Roboto Flex cpu text/x_return | Final/fixes 4–5 | +1.84% [+1.08, +2.34]<br>Δ +4.850 µs |
| Vollkorn cpu demo/first_paint | Final/fixes 4–5 | +1.24% [+0.71, +2.21]<br>Δ +0.055 ms |
| Vollkorn cpu demo/zoom_in | Final/fixes 4–5 | +0.94% [+0.13, +1.80]<br>Δ +0.038 ms |
| Vollkorn cpu demo/zoom_out | Final/fixes 4–5 | +0.81% [+0.05, +1.47]<br>Δ +0.021 ms |
| Vollkorn cpu grid_pollution/pollution | Final/fixes 4–5 | +0.42% [+0.12, +0.66]<br>Δ +6.250 µs |
| Vollkorn cpu text/first_paint | Fixes 4–5/prior | +2.44% [+1.42, +3.45]<br>Δ +0.504 ms |
| Vollkorn cpu text/size_advance | Fixes 4–5/prior | +1.23% [+0.77, +1.64]<br>Δ +0.094 ms |
| Vollkorn cpu text/size_return | Final/master | +1.68% [+0.44, +3.02]<br>Δ +4.570 µs |
| Vollkorn cpu text/size_return | Final/fixes 4–5 | +1.44% [+0.23, +5.43]<br>Δ +3.948 µs |
| Vollkorn cpu text/warm | Final/master | +2.88% [+2.10, +4.06]<br>Δ +7.158 µs |
| Vollkorn cpu text/warm | Fixes 4–5/prior | +0.56% [+0.09, +1.20]<br>Δ +1.442 µs |
| Vollkorn cpu text/warm | Final/fixes 4–5 | +1.05% [+0.44, +2.09]<br>Δ +2.650 µs |
| Vollkorn cpu text/x_advance | Final/fixes 4–5 | +1.54% [+0.20, +2.15]<br>Δ +5.727 µs |
| Vollkorn cpu text/x_return | Final/master | +2.07% [+1.10, +3.72]<br>Δ +5.233 µs |
| Vollkorn cpu text/x_return | Final/fixes 4–5 | +1.56% [+0.96, +2.25]<br>Δ +4.002 µs |
| Vollkorn cpu text/y_advance | Final/master | +3.07% [+2.42, +3.77]<br>Δ +7.763 µs |
| Vollkorn cpu text/y_advance | Final/fixes 4–5 | +1.61% [+1.14, +2.41]<br>Δ +4.048 µs |
| PT Sans gpu grid_two_phases/second | Fixes 4–5/prior | +14.72% [+0.99, +49.53]<br>Δ +0.123 ms |
| Vollkorn gpu grid_pollution/pollution | Final/fixes 4–5 | +3.50% [+1.10, +7.73]<br>Δ +0.104 ms |
| Vollkorn gpu text/size_advance | Final/fixes 4–5 | +1.63% [+0.49, +5.13]<br>Δ +0.214 ms |
| Vollkorn gpu text/size_return | Final/fixes 4–5 | +5.15% [+0.64, +9.52]<br>Δ +0.047 ms |
| Vollkorn gpu text/warm | Final/fixes 4–5 | +4.55% [+1.72, +7.53]<br>Δ +0.034 ms |
| PT Sans cpu grid_unique_sizes total | Fixes 4–5/prior | +0.63% [+0.015, +1.67]<br>Δ +0.074 ms |
| PT Sans cpu text total | Fixes 4–5/prior | +0.44% [+0.07, +0.60]<br>Δ +0.420 ms |
| Roboto Flex cpu font_variations total | Final/fixes 4–5 | +0.64% [+0.05, +2.52]<br>Δ +0.065 ms |
| Roboto Flex cpu grid_singleton total | Final/fixes 4–5 | +2.65% [+1.17, +4.18]<br>Δ +4.855 µs |
| Vollkorn cpu demo total | Final/fixes 4–5 | +0.64% [+0.25, +1.69]<br>Δ +0.596 ms |
| Vollkorn cpu grid_pollution total | Final/fixes 4–5 | +0.36% [+0.17, +0.68]<br>Δ +0.349 ms |
| Vollkorn cpu text total | Fixes 4–5/prior | +1.12% [+0.55, +1.66]<br>Δ +1.571 ms |
| Vollkorn gpu grid_pollution total | Final/fixes 4–5 | +3.66% [+1.07, +7.62]<br>Δ +7.478 ms |
| Vollkorn gpu text total | Final/fixes 4–5 | +2.19% [+0.18, +4.38]<br>Δ +5.813 ms |
| Boundary 3300 keys reuse9 | Final/fixes 4–5 | +0.82% [+0.32, +1.17]<br>Δ +0.461 ms |
| Boundary 3300 keys complete10 | Final/fixes 4–5 | +0.86% [+0.25, +1.04]<br>Δ +0.544 ms |
| Boundary 3440 keys population | Final/fixes 4–5 | +0.73% [+0.47, +1.48]<br>Δ +0.055 ms |
| Boundary 3440 keys reuse9 | Final/fixes 4–5 | +0.80% [+0.46, +1.30]<br>Δ +0.475 ms |
| Boundary 3440 keys complete10 | Final/fixes 4–5 | +0.81% [+0.46, +1.21]<br>Δ +0.545 ms |
| Boundary 3600 keys population | Final/fixes 4–5 | +0.74% [+0.50, +1.60]<br>Δ +0.060 ms |
| Boundary 3600 keys reuse9 | Final/fixes 4–5 | +0.52% [+0.041, +1.03]<br>Δ +0.374 ms |
| Boundary 3600 keys complete10 | Final/fixes 4–5 | +0.70% [+0.17, +1.07]<br>Δ +0.560 ms |

## Correctness and limits

Final is validated against a separately built uncached-master native renderer whose atlas identity is constructed from actual raster-offset f32 bits, with signed zero normalized. Only master text.rs changes for the oracle; none of the arena, signed-bin implementation or other fixes are copied. All 168 final captures match that oracle. Prior/updated45 remain legacy-master parity. The original-master difference is retained; `rgba_identical` in accepted final rows means oracle parity, not unchanged legacy output. The rejected original equality cohort remains preserved. Alustin retains all 18 exact master comparisons and actual primary/fallback font byte diagnostics.

**The 1 MiB cache target is soft accounting, not a bound on total heap or RSS.** It charges shared-vector capacities, logical key/range metadata and public scratch length high-water. Inaccessible native spare capacities, hash-map spare capacity, allocator overhead, shared ScaleContext and transient work are excluded. Cache residency and allocator growth behavior matter; allocation requests are not proof that all old capacities were physically copied. A cache hit avoids native outline scaling/hinting while masks remain phase-specific.

The study uses 12 planned Williams blocks/rounds with five CPU or three GPU example trials per process and five boundary trials. No timing-based trimming or retries are used. Alustin retries only whole query-contaminated blocks and preserves attempts; the independent order proof records accepted counts. These results describe this machine and these workloads, with exploratory unadjusted intervals. Swash and transitive dependencies are unchanged. The implementation remains internal to FemtoVG and Swash-only.

## Preserved evidence and reproduction

Three added archives retain all accepted/rejected raw records, frozen sources, native-oracle captures, validation overlays, actual-font evidence and targeted boundary data: `updated-cache-examples`, `updated-cache-alustin`, `updated-cache-source-bundle`. Prior reports/archives and the original vendor bundle remain unchanged. See [reproduction](docs/revised-cache-reproduction.md), [phase statistics](analysis/updated-cache-examples/summary.csv), [sequence statistics](analysis/updated-cache-sequences/summary.csv), and [Alustin statistics](analysis/updated-cache-alustin/summary.csv). All six comparisons remain available even though these tables highlight three.
