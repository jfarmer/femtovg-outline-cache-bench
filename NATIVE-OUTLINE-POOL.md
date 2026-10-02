# Shared geometry arena versus pooled native Swash Outline

**Keep the shared arena.** The native Swash `Outline` pool is correct and preserves much of the cache benefit, but its small code reduction does not justify the measured costs in this implementation.

The pool takes 2.18% longer for Roboto demo first paint (95% interval 1.03%–3.21%) and 1.91% longer for PT Sans (1.41%–2.99%). The complete Roboto 32-size sweep is 9.05% slower (8.46%–9.55%), and the 32-weight sweep is 8.80% slower (8.41%–9.55%). The larger CPU-only text example with Vollkorn is 36.00% slower on first paint (35.11%–36.48%): the arena is 23.99% faster than master there, while the pool is 3.65% slower than master. These are host drawing measurements with the Void renderer. The real WGPU host drawing measurement is only 0.77% longer (0.008%–1.01%), and its completion interval spans zero; the large disparity is not explained by GPU waiting alone. Both modes request the same 1,278 new atlas entries, but atlas entries do not reveal outline-cache misses. The cause of this backend-dependent disparity remains unresolved. Keep these observations distinct, and use the independently measured miss controls and allocation evidence alongside the application results.

Alustin supplies a useful counterweight: every direct first-frame renderer CPU interval spans zero, and both candidates retain substantial Vollkorn gains over master. The pool wins the Roboto/OpenGL search comparison by 2.49% (0.44%–5.14% less CPU); the other direct search intervals span zero. PT Sans/WGPU process high-water RSS rises by 0.52 MiB (0.20–1.23 MiB); the other direct RSS intervals span zero. The full GPU and warm tables below retain uncertain effects and isolated regressions. Failure to resolve a difference is not proof of equivalence.

The untimed probe gives a concrete reason for keeping shared storage. For 94 cold Roboto glyphs, native pooling makes 799 allocation/reallocation requests versus the arena's 144. Across 32 sizes it makes 24,022 versus 3,135, and retains 2,273,456 versus 1,033,832 bytes of rasterizer-owned requested Rust heap. Pooling avoids copying geometry, but an outline that becomes a cache entry cannot immediately serve the next cold miss. The arena reuses one native working outline between misses and copies its public point/verb slices into amortized shared storage. Scaling, hinting, native geometry and mask generation still come from Swash/Zeno; this storage adapter does not reimplement those algorithms.

The pool removes only 13 production lines (293 → 280), while replacing range/growth/copy code with acquire/recycle/high-water/trim code. Its nominal 1 MiB accounting target also retains a different amount of real memory and cache entries because Swash does not expose private vector capacities. These results compare the two complete policies; they do not show that every conceivable native pool or different budget must lose. They do provide an empirical reason for the current arena, beyond a preference for custom code. The production FemtoVG patch remains the selected Swash-only arena, with no dependency edits.

This follow-up compares the previously selected shared geometry arena (`final`) with cached, recycled native Swash `Outline` objects (`pool`). Master and the original cache (`current`) remain in the same fresh four-version campaign. The prior [REPORT.md](REPORT.md) and every earlier benchmark remain preserved; these new observations are not pooled with earlier cohorts.

Each cell shows median paired change, an exploratory 95% whole-block bootstrap interval, and paired absolute change. Negative duration changes mean faster. **Pool/arena is the direct storage comparison**; arena/master and pool/master show whether either complete patch merits inclusion. Absolute medians need not reproduce a median paired percentage.

## Existing example first paint

| Font | Scene | Measurement | Arena/master | Pool/master | Pool/arena |
| --- | --- | --- | --- | --- | --- |
| Roboto Flex | demo | CPU drawing | -4.81% [-5.49, -3.68]<br>Δ -0.070 ms | -2.65% [-3.98, -1.37]<br>Δ -0.039 ms | +2.18% [+1.03, +3.21]<br>Δ +0.030 ms |
| Roboto Flex | text | CPU drawing | -4.29% [-5.04, -3.74]<br>Δ -0.323 ms | -2.25% [-3.01, -1.57]<br>Δ -0.168 ms | +1.86% [+1.14, +2.20]<br>Δ +0.134 ms |
| Vollkorn Medium | demo | CPU drawing | -32.82% [-33.17, -32.15]<br>Δ -2.203 ms | -32.32% [-33.04, -31.32]<br>Δ -2.179 ms | +0.82% [-0.33, +2.43]<br>Δ +0.037 ms |
| Vollkorn Medium | text | CPU drawing | -23.99% [-24.17, -23.05]<br>Δ -6.492 ms | +3.65% [+3.32, +4.13]<br>Δ +0.993 ms | +36.00% [+35.11, +36.48]<br>Δ +7.451 ms |
| PT Sans Regular | demo | CPU drawing | -15.56% [-16.13, -14.10]<br>Δ -0.313 ms | -13.99% [-14.64, -11.95]<br>Δ -0.281 ms | +1.91% [+1.41, +2.99]<br>Δ +0.033 ms |
| PT Sans Regular | text | CPU drawing | -9.57% [-10.41, -9.23]<br>Δ -0.885 ms | -7.56% [-8.68, -6.87]<br>Δ -0.705 ms | +2.43% [+2.07, +2.63]<br>Δ +0.201 ms |
| Roboto Flex | demo | GPU completion | +2.36% [-2.15, +12.60]<br>Δ +0.266 ms | -0.82% [-3.40, +6.59]<br>Δ -0.088 ms | -1.75% [-11.00, +5.88]<br>Δ -0.189 ms |
| Roboto Flex | text | GPU completion | +2.21% [-4.66, +6.59]<br>Δ +0.667 ms | -1.90% [-8.08, +1.38]<br>Δ -0.577 ms | -2.02% [-9.15, +1.22]<br>Δ -0.601 ms |
| Vollkorn Medium | demo | GPU completion | -14.13% [-22.55, -12.66]<br>Δ -2.315 ms | -15.31% [-21.93, -12.71]<br>Δ -2.505 ms | +0.72% [-4.59, +1.66]<br>Δ +0.101 ms |
| Vollkorn Medium | text | GPU completion | -12.74% [-14.78, -11.45]<br>Δ -6.465 ms | -13.88% [-16.07, -12.27]<br>Δ -7.003 ms | -1.24% [-2.78, +0.68]<br>Δ -0.547 ms |
| PT Sans Regular | demo | GPU completion | -3.76% [-8.76, +9.45]<br>Δ -0.416 ms | +3.34% [-10.16, +10.33]<br>Δ +0.361 ms | +2.49% [-4.23, +10.40]<br>Δ +0.247 ms |
| PT Sans Regular | text | GPU completion | -4.46% [-5.86, +1.67]<br>Δ -1.393 ms | -2.03% [-4.38, +0.58]<br>Δ -0.634 ms | +0.025% [-2.09, +4.63]<br>Δ +0.009 ms |

GPU completion includes CPU drawing, submission and waiting for completion; it is not a GPU timestamp. All 28 phases remain in the [per-phase statistics](analysis/native-pool-examples/summary.csv).

## Complete controlled sequences

Each controlled frame introduces 94 distinct atlas keys. Size and variation sweeps deliberately provide no cross-instance outline reuse. The two-phase total includes population and reuse. Pollution includes both hot frames, all 64 pollution frames and hot return. Variation controls always use Roboto Flex and are shown once.

| Font | Complete sequence | Measurement | Arena/master | Pool/master | Pool/arena |
| --- | --- | --- | --- | --- | --- |
| Roboto Flex | 94 one-use glyphs | CPU | -24.43% [-25.27, -20.86]<br>Δ -0.057 ms | -18.19% [-19.12, -16.12]<br>Δ -0.044 ms | +7.42% [+3.87, +9.62]<br>Δ +0.013 ms |
| Roboto Flex | First + second phase | CPU | -24.95% [-25.86, -23.91]<br>Δ -0.092 ms | -21.38% [-22.47, -20.46]<br>Δ -0.078 ms | +5.78% [+2.78, +7.86]<br>Δ +0.016 ms |
| Roboto Flex | 32 unique sizes | CPU | -5.89% [-6.76, -4.91]<br>Δ -0.338 ms | +2.75% [+2.18, +3.09]<br>Δ +0.161 ms | +9.05% [+8.46, +9.55]<br>Δ +0.497 ms |
| Roboto Flex | 32 unique weights | CPU | -30.40% [-30.52, -30.02]<br>Δ -2.375 ms | -23.96% [-24.43, -23.65]<br>Δ -1.866 ms | +8.80% [+8.41, +9.55]<br>Δ +0.483 ms |
| Roboto Flex | Hot + 64-size pollution + return | CPU | -5.62% [-6.02, -5.41]<br>Δ -0.751 ms | +1.38% [+0.12, +1.86]<br>Δ +0.184 ms | +7.19% [+6.31, +7.83]<br>Δ +0.905 ms |
| Vollkorn Medium | 94 one-use glyphs | CPU | -4.36% [-5.21, -3.51]<br>Δ -0.070 ms | -2.27% [-3.00, -1.58]<br>Δ -0.036 ms | +2.26% [+1.17, +2.94]<br>Δ +0.034 ms |
| Vollkorn Medium | First + second phase | CPU | -44.23% [-44.84, -43.75]<br>Δ -1.321 ms | -43.50% [-43.77, -42.90]<br>Δ -1.295 ms | +1.68% [+1.13, +2.16]<br>Δ +0.028 ms |
| Vollkorn Medium | 32 unique sizes | CPU | -1.09% [-1.73, -0.72]<br>Δ -0.515 ms | +1.38% [+0.59, +1.75]<br>Δ +0.652 ms | +2.38% [+1.75, +3.18]<br>Δ +1.123 ms |
| Vollkorn Medium | Hot + 64-size pollution + return | CPU | -2.09% [-2.76, -1.82]<br>Δ -2.098 ms | -0.59% [-0.94, -0.41]<br>Δ -0.596 ms | +1.55% [+0.69, +2.36]<br>Δ +1.527 ms |
| PT Sans Regular | 94 one-use glyphs | CPU | -12.36% [-13.49, -10.87]<br>Δ -0.059 ms | -9.52% [-10.51, -8.19]<br>Δ -0.046 ms | +2.92% [+1.63, +4.14]<br>Δ +0.012 ms |
| PT Sans Regular | First + second phase | CPU | -36.50% [-36.69, -35.84]<br>Δ -0.294 ms | -33.94% [-34.42, -33.42]<br>Δ -0.274 ms | +4.07% [+2.85, +4.49]<br>Δ +0.021 ms |
| PT Sans Regular | 32 unique sizes | CPU | -2.94% [-3.30, -2.64]<br>Δ -0.356 ms | +1.85% [+1.57, +2.19]<br>Δ +0.225 ms | +5.01% [+4.59, +5.25]<br>Δ +0.585 ms |
| PT Sans Regular | Hot + 64-size pollution + return | CPU | -4.39% [-4.77, -3.91]<br>Δ -1.156 ms | +0.29% [-0.29, +1.36]<br>Δ +0.077 ms | +5.12% [+4.34, +5.90]<br>Δ +1.290 ms |
| Roboto Flex | 94 one-use glyphs | GPU completion | -4.25% [-8.39, +0.36]<br>Δ -0.120 ms | +2.05% [-3.46, +3.12]<br>Δ +0.060 ms | +3.67% [+1.58, +7.15]<br>Δ +0.099 ms |
| Roboto Flex | First + second phase | GPU completion | -10.74% [-19.60, -0.65]<br>Δ -0.376 ms | -2.77% [-13.87, +0.83]<br>Δ -0.098 ms | +5.86% [-3.34, +21.94]<br>Δ +0.195 ms |
| Roboto Flex | 32 unique sizes | GPU completion | +7.59% [-3.82, +18.04]<br>Δ +2.624 ms | +8.53% [+3.82, +15.68]<br>Δ +2.975 ms | +4.39% [-3.63, +15.62]<br>Δ +1.561 ms |
| Roboto Flex | 32 unique weights | GPU completion | -7.93% [-17.93, -5.80]<br>Δ -2.634 ms | -5.30% [-14.97, -3.25]<br>Δ -1.746 ms | +3.45% [-0.29, +10.79]<br>Δ +1.057 ms |
| Roboto Flex | Hot + 64-size pollution + return | GPU completion | -0.39% [-2.64, +3.54]<br>Δ -0.265 ms | +2.48% [-0.29, +7.68]<br>Δ +1.650 ms | +0.78% [-3.92, +8.38]<br>Δ +0.500 ms |
| Vollkorn Medium | 94 one-use glyphs | GPU completion | -2.92% [-4.83, +1.01]<br>Δ -0.122 ms | -0.78% [-2.68, +2.40]<br>Δ -0.032 ms | +1.27% [-1.81, +6.01]<br>Δ +0.051 ms |
| Vollkorn Medium | First + second phase | GPU completion | -23.10% [-28.65, -16.38]<br>Δ -1.639 ms | -26.54% [-31.52, -20.34]<br>Δ -1.734 ms | -4.26% [-14.15, +3.62]<br>Δ -0.228 ms |
| Vollkorn Medium | 32 unique sizes | GPU completion | -2.10% [-2.96, -0.50]<br>Δ -1.951 ms | -0.79% [-2.06, +0.14]<br>Δ -0.727 ms | +1.27% [+0.041, +4.68]<br>Δ +1.164 ms |
| Vollkorn Medium | Hot + 64-size pollution + return | GPU completion | -1.66% [-3.72, +0.49]<br>Δ -3.136 ms | -1.25% [-2.23, +0.63]<br>Δ -2.385 ms | +1.16% [-0.99, +1.95]<br>Δ +2.145 ms |
| PT Sans Regular | 94 one-use glyphs | GPU completion | +1.74% [-4.56, +5.01]<br>Δ +0.053 ms | +1.24% [-3.76, +4.79]<br>Δ +0.037 ms | -0.81% [-3.15, +5.81]<br>Δ -0.024 ms |
| PT Sans Regular | First + second phase | GPU completion | -8.66% [-11.91, -3.55]<br>Δ -0.348 ms | -6.32% [-8.19, -2.93]<br>Δ -0.258 ms | +1.57% [-2.67, +4.96]<br>Δ +0.058 ms |
| PT Sans Regular | 32 unique sizes | GPU completion | -1.72% [-4.30, +1.01]<br>Δ -0.755 ms | -0.003% [-3.67, +3.90]<br>Δ -0.002 ms | -0.12% [-1.31, +7.02]<br>Δ -0.054 ms |
| PT Sans Regular | Hot + 64-size pollution + return | GPU completion | -3.11% [-5.10, -0.49]<br>Δ -2.716 ms | -3.15% [-6.18, +4.57]<br>Δ -2.639 ms | +0.05% [-2.62, +7.17]<br>Δ -0.003 ms |

## Every reported example sequence

These sums include every reported phase: movement, reflow, zoom and font-instance changes. They exclude 119 unreported warmup frames per scene and are not launch-to-end durations. Each trial is summed before process medians and block pairing.

| Font factor | Scene | Reported frames | Measurement | Arena/master | Pool/master | Pool/arena |
| --- | --- | --- | --- | --- | --- | --- |
| Roboto Flex | demo | 65 | CPU | -2.98% [-3.69, -2.27]<br>Δ -1.090 ms | -1.77% [-2.13, -1.41]<br>Δ -0.642 ms | +1.32% [+0.99, +1.48]<br>Δ +0.467 ms |
| Roboto Flex | text | 88 | CPU | -2.68% [-3.14, -1.93]<br>Δ -2.507 ms | -1.89% [-2.48, -1.48]<br>Δ -1.760 ms | +0.62% [+0.23, +0.99]<br>Δ +0.577 ms |
| Roboto Flex | font_variations | 63 | CPU | -2.05% [-2.83, -1.65]<br>Δ -0.214 ms | -0.21% [-0.51, +0.13]<br>Δ -0.022 ms | +2.13% [+1.57, +2.76]<br>Δ +0.215 ms |
| Vollkorn Medium | demo | 65 | CPU | -32.69% [-33.10, -32.37]<br>Δ -44.929 ms | -32.13% [-32.38, -31.73]<br>Δ -44.161 ms | +1.02% [+0.45, +1.65]<br>Δ +0.938 ms |
| Vollkorn Medium | text | 88 | CPU | -27.23% [-27.88, -26.46]<br>Δ -52.878 ms | -19.32% [-19.77, -18.54]<br>Δ -37.466 ms | +11.04% [+9.77, +11.41]<br>Δ +15.691 ms |
| PT Sans Regular | demo | 65 | CPU | -13.43% [-13.80, -12.72]<br>Δ -6.377 ms | -12.07% [-12.44, -11.82]<br>Δ -5.736 ms | +1.40% [+0.38, +1.81]<br>Δ +0.576 ms |
| PT Sans Regular | text | 88 | CPU | -7.72% [-8.20, -7.35]<br>Δ -7.867 ms | -7.38% [-7.59, -7.09]<br>Δ -7.503 ms | +0.65% [-0.08, +0.92]<br>Δ +0.610 ms |
| Roboto Flex | demo | 65 | GPU completion | -1.21% [-2.74, +1.93]<br>Δ -1.557 ms | -0.22% [-1.40, +3.81]<br>Δ -0.286 ms | -0.53% [-1.92, +2.89]<br>Δ -0.672 ms |
| Roboto Flex | text | 88 | GPU completion | -0.032% [-1.18, +2.43]<br>Δ -0.069 ms | -0.94% [-3.41, +1.84]<br>Δ -2.034 ms | -2.04% [-4.29, +0.12]<br>Δ -4.418 ms |
| Roboto Flex | font_variations | 63 | GPU completion | -2.71% [-4.30, +0.41]<br>Δ -1.051 ms | -1.77% [-3.32, +5.30]<br>Δ -0.683 ms | +1.71% [-1.23, +8.53]<br>Δ +0.645 ms |
| Vollkorn Medium | demo | 65 | GPU completion | -22.10% [-22.74, -20.67]<br>Δ -55.703 ms | -21.68% [-23.68, -20.82]<br>Δ -55.167 ms | -0.50% [-1.57, +1.08]<br>Δ -0.983 ms |
| Vollkorn Medium | text | 88 | GPU completion | -18.16% [-20.07, -17.70]<br>Δ -60.422 ms | -18.79% [-20.04, -17.87]<br>Δ -62.383 ms | -0.37% [-1.58, +1.18]<br>Δ -1.022 ms |
| PT Sans Regular | demo | 65 | GPU completion | -5.73% [-6.82, -3.64]<br>Δ -8.170 ms | -6.78% [-8.11, -2.54]<br>Δ -9.485 ms | -1.14% [-3.32, +2.41]<br>Δ -1.520 ms |
| PT Sans Regular | text | 88 | GPU completion | -4.59% [-4.99, -2.55]<br>Δ -10.015 ms | -3.75% [-5.89, -2.14]<br>Δ -8.102 ms | +0.94% [-0.25, +1.15]<br>Δ +1.922 ms |

## Alustin first and filtered search renderer-thread CPU

These diagnostics measure renderer-thread host work; they do not measure GPU completion, compositor scanout or diagnostics-off startup. The filtered search can introduce new atlas entries and is not necessarily a completely warm redraw.

| Font | Backend | Frame | Arena/master | Pool/master | Pool/arena |
| --- | --- | --- | --- | --- | --- |
| Roboto Flex | WGPU | First | -3.59% [-5.03, -0.33]<br>Δ -0.511 ms | -3.17% [-4.28, -1.67]<br>Δ -0.443 ms | +1.02% [-2.93, +2.65]<br>Δ +0.140 ms |
| Roboto Flex | OpenGL | First | -1.97% [-4.09, +0.07]<br>Δ -0.335 ms | -2.52% [-4.61, -0.93]<br>Δ -0.440 ms | +0.05% [-4.86, +2.66]<br>Δ +0.009 ms |
| Vollkorn Medium | WGPU | First | -23.84% [-24.39, -22.60]<br>Δ -5.184 ms | -22.28% [-24.51, -20.73]<br>Δ -4.956 ms | +2.32% [-0.24, +4.30]<br>Δ +0.388 ms |
| Vollkorn Medium | OpenGL | First | -19.89% [-21.91, -17.17]<br>Δ -4.989 ms | -20.65% [-21.51, -18.97]<br>Δ -5.205 ms | -1.15% [-2.36, +0.36]<br>Δ -0.233 ms |
| PT Sans Regular | WGPU | First | -2.56% [-11.63, -0.49]<br>Δ -0.364 ms | -4.01% [-9.57, -1.18]<br>Δ -0.584 ms | -0.23% [-1.96, +2.90]<br>Δ -0.031 ms |
| PT Sans Regular | OpenGL | First | -3.66% [-5.92, -2.01]<br>Δ -0.661 ms | -4.57% [-6.61, -2.63]<br>Δ -0.816 ms | -1.19% [-3.74, +3.73]<br>Δ -0.204 ms |
| Roboto Flex | WGPU | Search | -0.20% [-2.32, +1.90]<br>Δ -0.004 ms | -0.53% [-4.31, +3.54]<br>Δ -0.013 ms | -1.93% [-3.87, +2.29]<br>Δ -0.043 ms |
| Roboto Flex | OpenGL | Search | -0.83% [-4.36, +7.51]<br>Δ -0.017 ms | +2.57% [-3.31, +4.93]<br>Δ +0.054 ms | -2.49% [-5.14, -0.44]<br>Δ -0.052 ms |
| Vollkorn Medium | WGPU | Search | -7.35% [-10.54, -2.58]<br>Δ -0.181 ms | -2.22% [-10.72, +1.57]<br>Δ -0.053 ms | +2.69% [-1.55, +9.40]<br>Δ +0.060 ms |
| Vollkorn Medium | OpenGL | Search | -6.79% [-9.99, -2.27]<br>Δ -0.156 ms | -5.10% [-8.48, +1.43]<br>Δ -0.121 ms | +1.39% [-5.49, +5.92]<br>Δ +0.030 ms |
| PT Sans Regular | WGPU | Search | -4.31% [-10.06, -0.06]<br>Δ -0.100 ms | -2.52% [-5.79, +0.75]<br>Δ -0.059 ms | +2.11% [-1.25, +6.03]<br>Δ +0.045 ms |
| PT Sans Regular | OpenGL | Search | -2.24% [-6.35, +1.04]<br>Δ -0.047 ms | -0.51% [-5.40, +1.47]<br>Δ -0.011 ms | +1.06% [-1.64, +3.54]<br>Δ +0.023 ms |

## Alustin process high-water RSS

RSS includes the application, renderer, fonts, driver and transient host work. It is neither device VRAM nor the outline cache alone. The following effects are absolute MiB changes rather than percentages.

| Font | Backend | Arena−master, 95% CI | Pool−master, 95% CI | Pool−arena, 95% CI |
| --- | --- | --- | --- | --- |
| Roboto Flex | WGPU | -0.102 [-1.109, +0.312] MiB | -0.461 [-1.281, -0.055] MiB | -0.594 [-1.305, +0.102] MiB |
| Roboto Flex | OpenGL | +0.516 [-0.648, +2.000] MiB | -0.250 [-1.812, +0.773] MiB | -1.570 [-2.234, +0.391] MiB |
| Vollkorn Medium | WGPU | -0.203 [-0.914, +0.844] MiB | +0.078 [-0.445, +1.016] MiB | +0.188 [-0.297, +0.891] MiB |
| Vollkorn Medium | OpenGL | +0.094 [-0.555, +1.422] MiB | +0.219 [-0.625, +1.172] MiB | +0.086 [-0.039, +0.305] MiB |
| PT Sans Regular | WGPU | +0.188 [-0.102, +1.414] MiB | +1.062 [+0.375, +2.023] MiB | +0.523 [+0.203, +1.227] MiB |
| PT Sans Regular | OpenGL | -0.570 [-2.312, +1.352] MiB | -0.500 [-1.586, +1.375] MiB | +0.164 [-1.477, +1.273] MiB |

## Warm redraws

All warm example phases are shown, including intervals crossing zero. Variation-scene repetitions under other regular-font factors are duplicate Roboto control workloads.

| Font factor | Scene | Measurement | Arena/master | Pool/master | Pool/arena |
| --- | --- | --- | --- | --- | --- |
| Roboto Flex | demo | CPU | -0.72% [-1.96, +0.021]<br>Δ -0.002 ms | -0.37% [-0.66, +0.40]<br>Δ -0.001 ms | +0.72% [-0.52, +1.71]<br>Δ +0.002 ms |
| Roboto Flex | text | CPU | -0.71% [-1.48, -0.40]<br>Δ -0.002 ms | -0.95% [-2.66, -0.15]<br>Δ -0.003 ms | -0.37% [-1.45, +0.67]<br>Δ -0.001 ms |
| Roboto Flex | font_variations | CPU | -1.34% [-2.60, -0.66]<br>Δ -0.001 ms | -1.31% [-1.99, -0.84]<br>Δ -0.000 ms | -0.20% [-0.76, +1.48]<br>Δ -0.000 ms |
| Vollkorn Medium | demo | CPU | +0.43% [-0.91, +0.79]<br>Δ +0.001 ms | +1.27% [+0.22, +1.73]<br>Δ +0.003 ms | +0.99% [+0.75, +1.73]<br>Δ +0.002 ms |
| Vollkorn Medium | text | CPU | +0.20% [-0.25, +1.54]<br>Δ +0.001 ms | +1.55% [+0.56, +2.59]<br>Δ +0.004 ms | +0.97% [+0.67, +1.54]<br>Δ +0.002 ms |
| PT Sans Regular | demo | CPU | +0.012% [-1.14, +0.61]<br>Δ +0.000 ms | +0.36% [-0.84, +1.27]<br>Δ +0.001 ms | +0.19% [-0.52, +1.23]<br>Δ +0.000 ms |
| PT Sans Regular | text | CPU | -0.40% [-1.02, -0.06]<br>Δ -0.001 ms | +0.48% [-0.31, +1.39]<br>Δ +0.001 ms | +1.00% [-0.25, +2.23]<br>Δ +0.003 ms |
| Roboto Flex | demo | GPU completion | +2.54% [-7.73, +8.99]<br>Δ +0.024 ms | +1.19% [-5.54, +15.01]<br>Δ +0.010 ms | +1.43% [-3.13, +5.94]<br>Δ +0.014 ms |
| Roboto Flex | text | GPU completion | -0.31% [-2.85, +3.13]<br>Δ -0.002 ms | +2.69% [-1.04, +4.93]<br>Δ +0.017 ms | +2.07% [-2.17, +7.54]<br>Δ +0.013 ms |
| Roboto Flex | font_variations | GPU completion | -0.71% [-2.70, +0.86]<br>Δ -0.002 ms | +1.07% [-2.22, +2.42]<br>Δ +0.003 ms | +2.70% [-0.014, +4.25]<br>Δ +0.007 ms |
| Vollkorn Medium | demo | GPU completion | +1.43% [-3.96, +7.28]<br>Δ +0.013 ms | +3.52% [-3.98, +7.02]<br>Δ +0.032 ms | +0.52% [-7.91, +6.27]<br>Δ +0.005 ms |
| Vollkorn Medium | text | GPU completion | +0.11% [-3.71, +3.00]<br>Δ +0.001 ms | +0.53% [-3.52, +1.76]<br>Δ +0.003 ms | -0.26% [-2.75, +1.11]<br>Δ -0.002 ms |
| PT Sans Regular | demo | GPU completion | +0.81% [-6.97, +3.75]<br>Δ +0.008 ms | -4.23% [-11.44, +5.53]<br>Δ -0.041 ms | -4.05% [-7.69, +1.03]<br>Δ -0.039 ms |
| PT Sans Regular | text | GPU completion | +1.45% [-0.014, +6.06]<br>Δ +0.009 ms | +2.02% [-1.31, +7.05]<br>Δ +0.012 ms | -0.24% [-2.03, +1.94]<br>Δ -0.002 ms |

## Exploratory regression audit

This lists primary example drawing/completion and Alustin first/search renderer-thread CPU effects whose preserved 95% interval lies entirely above zero. Intervals are per-metric and unadjusted for multiple comparisons. Small isolated differences do not establish a general regression. All uncertain effects remain in the full statistics.

| Font | Observation | Comparison | Duration change |
| --- | --- | --- | --- |
| PT Sans Regular | demo/first_paint cpu | Pool/arena | +1.91% [+1.41, +2.99]<br>Δ +0.033 ms |
| PT Sans Regular | demo/pan cpu | Arena/master | +0.75% [+0.23, +0.94]<br>Δ +0.002 ms |
| PT Sans Regular | demo/zoom_in cpu | Pool/arena | +1.55% [+0.89, +1.95]<br>Δ +0.024 ms |
| PT Sans Regular | demo/zoom_out cpu | Pool/arena | +1.19% [+0.68, +2.21]<br>Δ +0.012 ms |
| PT Sans Regular | text/first_paint cpu | Pool/arena | +2.43% [+2.07, +2.63]<br>Δ +0.201 ms |
| Roboto Flex | demo/first_paint cpu | Pool/arena | +2.18% [+1.03, +3.21]<br>Δ +0.030 ms |
| Roboto Flex | demo/zoom_in cpu | Pool/arena | +1.62% [+1.16, +2.48]<br>Δ +0.021 ms |
| Roboto Flex | demo/zoom_out cpu | Pool/arena | +1.76% [+1.30, +2.08]<br>Δ +0.015 ms |
| Roboto Flex | font_variations/first_paint cpu | Pool/arena | +2.36% [+1.55, +3.07]<br>Δ +0.023 ms |
| Roboto Flex | font_variations/slant_advance cpu | Pool/arena | +2.54% [+1.47, +2.99]<br>Δ +0.011 ms |
| Roboto Flex | font_variations/weight_advance cpu | Pool/master | +0.73% [+0.003, +0.98]<br>Δ +0.004 ms |
| Roboto Flex | font_variations/weight_advance cpu | Pool/arena | +2.86% [+2.57, +3.90]<br>Δ +0.014 ms |
| Roboto Flex | text/first_paint cpu | Pool/arena | +1.86% [+1.14, +2.20]<br>Δ +0.134 ms |
| Roboto Flex | text/reflow cpu | Pool/arena | +0.78% [+0.21, +1.51]<br>Δ +0.016 ms |
| Roboto Flex | text/size_advance cpu | Pool/arena | +0.51% [+0.24, +1.08]<br>Δ +0.025 ms |
| Vollkorn Medium | demo/warm cpu | Pool/master | +1.27% [+0.22, +1.73]<br>Δ +0.003 ms |
| Vollkorn Medium | demo/warm cpu | Pool/arena | +0.99% [+0.75, +1.73]<br>Δ +0.002 ms |
| Vollkorn Medium | demo/zoom_in cpu | Pool/arena | +1.19% [+0.13, +1.77]<br>Δ +0.048 ms |
| Vollkorn Medium | demo/zoom_out cpu | Pool/arena | +0.99% [+0.69, +1.56]<br>Δ +0.025 ms |
| Vollkorn Medium | text/first_paint cpu | Pool/master | +3.65% [+3.32, +4.13]<br>Δ +0.993 ms |
| Vollkorn Medium | text/first_paint cpu | Pool/arena | +36.00% [+35.11, +36.48]<br>Δ +7.451 ms |
| Vollkorn Medium | text/size_advance cpu | Pool/arena | +8.46% [+6.93, +8.87]<br>Δ +0.653 ms |
| Vollkorn Medium | text/warm cpu | Pool/master | +1.55% [+0.56, +2.59]<br>Δ +0.004 ms |
| Vollkorn Medium | text/warm cpu | Pool/arena | +0.97% [+0.67, +1.54]<br>Δ +0.002 ms |
| Vollkorn Medium | text/y_advance cpu | Arena/master | +1.10% [+0.35, +1.66]<br>Δ +0.003 ms |
| Vollkorn Medium | text/y_advance cpu | Pool/master | +1.42% [+0.46, +2.59]<br>Δ +0.004 ms |
| PT Sans Regular | text/y_advance gpu | Pool/master | +2.41% [+0.25, +4.82]<br>Δ +0.015 ms |
| Vollkorn Medium | demo/pan gpu | Pool/arena | +4.25% [+2.00, +17.36]<br>Δ +0.046 ms |

## Storage, reuse and code volume

The arena stores point/verb ranges in shared vectors and uses one native Outline scratch object. The pool stores native Outline objects directly, removing range management and scratch-to-cache geometry copying. It adds object acquisition, recycling, per-object high-water tracking and free-pool trimming. The production rasterizer is **293 → 280 lines**, 13 fewer; this describes source volume, not a demonstrated maintainability improvement.

Both candidates are internal to FemtoVG and Swash-only, with identical cache keys, eager admission, native scaling/hinting and bitmap/scaler routing. No Swash or transitive dependency changes are included.

**The equal 1 MiB nominal targets do not impose equal heap limits or cache residency.** The arena charges its shared-vector capacities exactly plus logical key/range metadata and native scratch public length high-water. The pool charges logical point/verb length high-water separately for each native object, cached metadata and the free-pool wrapper vector capacity. Neither can account for inaccessible native spare capacities/layers; map capacity, allocator overhead, shared ScaleContext and transient work are excluded. Differences in eviction or retained private capacity are part of this implementation comparison.

### Untimed residency and requested heap

Values are **arena → pool** at the end of each complete control. Hits and clears are cumulative through the same replay prefix. Owned requested heap is measured by dropping only the rasterizer while fonts and its external ScaleContext remain alive and every output Image has already been dropped. It includes native private buffers, map buckets and Zeno scratch; it is requested Rust heap memory, not RSS or allocator bookkeeping.

| Font | Complete control | Hits | Nonempty clears | Cached entries | Free pool entries | Accounted KiB | Owned requested KiB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Roboto Flex | 94 one-use glyphs | 0 → 0 | 0 → 0 | 94 → 94 | 0 | 29.5 → 33.6 | 40.5 → 70.5 |
| Roboto Flex | First + second phase | 94 → 94 | 0 → 0 | 94 → 94 | 0 | 29.5 → 33.6 | 40.5 → 70.5 |
| Roboto Flex | 32 unique sizes | 0 → 0 | 0 → 1 | 3008 → 147 | 2470 | 920.8 → 1024.0 | 1009.6 → 2220.2 |
| Roboto Flex | 32 unique weights | 0 → 0 | 0 → 1 | 3008 → 178 | 2392 | 932.5 → 1023.6 | 1013.2 → 2199.8 |
| Roboto Flex | Hot + 64-size pollution + return | 94 → 94 | 1 → 2 | 3064 → 842 | 856 | 924.3 → 1023.8 | 1009.7 → 1958.2 |
| Vollkorn Medium | 94 one-use glyphs | 0 → 0 | 0 → 0 | 94 → 94 | 0 | 99.3 → 63.1 | 110.8 → 113.3 |
| Vollkorn Medium | First + second phase | 94 → 94 | 0 → 0 | 94 → 94 | 0 | 99.3 → 63.1 | 110.8 → 113.3 |
| Vollkorn Medium | 32 unique sizes | 0 → 0 | 2 → 2 | 317 → 170 | 1045 | 758.1 → 1024.0 | 885.7 → 1804.5 |
| Vollkorn Medium | Hot + 64-size pollution + return | 94 → 94 | 4 → 4 | 817 → 903 | 22 | 789.4 → 1023.8 | 885.8 → 1590.0 |
| PT Sans Regular | 94 one-use glyphs | 0 → 0 | 0 → 0 | 94 → 94 | 0 | 55.3 → 39.4 | 66.8 → 79.5 |
| PT Sans Regular | First + second phase | 94 → 94 | 0 → 0 | 94 → 94 | 0 | 55.3 → 39.4 | 66.8 → 79.5 |
| PT Sans Regular | 32 unique sizes | 0 → 0 | 1 → 1 | 306 → 568 | 1133 | 824.4 → 1024.0 | 1082.6 → 2020.0 |
| PT Sans Regular | Hot + 64-size pollution + return | 94 → 94 | 2 → 2 | 800 → 1687 | 0 | 855.3 → 896.0 | 1082.7 → 1808.5 |

### Untimed allocation traffic

Every endpoint is replayed from a fresh rasterizer/context through the whole prefix. Allocation traffic and peak growth include temporary images and shared-context preparation. Allocation counts do not predict elapsed time; timed binaries contain none of this instrumentation. Values are arena → pool; fresh/pool-acquired native object counts apply to the pool only.

| Font | Complete control | Glyph requests | Allocation calls | Requested KiB | Peak live growth KiB | Fresh native objects | Pool acquisitions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Roboto Flex | 94 one-use glyphs | 94 | 144 → 799 | 127.3 → 169.2 | 46.6 → 72.0 | 94 | 0 |
| Roboto Flex | First + second phase | 188 | 238 → 893 | 173.3 → 215.1 | 46.6 → 73.3 | 94 | 0 |
| Roboto Flex | 32 unique sizes | 3008 | 3135 → 24022 | 4129.5 → 6228.0 | 1135.6 → 2326.8 | 2862 | 146 |
| Roboto Flex | 32 unique weights | 3008 | 6158 → 26914 | 3546.2 → 5634.4 | 1142.6 → 2305.5 | 2831 | 177 |
| Roboto Flex | Hot + 64-size pollution + return | 6298 | 6459 → 37433 | 8435.9 → 12644.4 | 1135.5 → 2345.5 | 3935 | 2269 |
| Vollkorn Medium | 94 one-use glyphs | 94 | 245 → 1139 | 2065.6 → 2052.6 | 146.0 → 147.6 | 94 | 0 |
| Vollkorn Medium | First + second phase | 188 | 339 → 1233 | 2110.8 → 2097.7 | 146.0 → 147.6 | 94 | 0 |
| Vollkorn Medium | 32 unique sizes | 3008 | 6166 → 24947 | 61037.8 → 64065.1 | 1063.1 → 2037.3 | 1817 | 1191 |
| Vollkorn Medium | Hot + 64-size pollution + return | 6298 | 12686 → 38045 | 125901.1 → 131105.0 | 1063.0 → 2036.8 | 2389 | 3815 |
| PT Sans Regular | 94 one-use glyphs | 94 | 149 → 850 | 175.8 → 183.1 | 69.0 → 81.2 | 94 | 0 |
| PT Sans Regular | First + second phase | 188 | 243 → 944 | 215.2 → 222.5 | 69.7 → 82.4 | 94 | 0 |
| PT Sans Regular | 32 unique sizes | 3008 | 3153 → 22816 | 4088.1 → 6353.7 | 1210.9 → 2356.0 | 2441 | 567 |
| PT Sans Regular | Hot + 64-size pollution + return | 6298 | 6477 → 39964 | 7973.9 → 13086.8 | 1210.7 → 2373.2 | 3970 | 2234 |

The [full probe](analysis/native-pool-probe.json) retains all 54 prefix records and all 6 executions. Pixel FNV digests are a mechanism sanity check; the independent complete RGBA campaign is the visual correctness evidence.

## Validation and study limits

The native pool passed 173 library tests and formatting. Final rendering validation contains 504 exact replay comparisons at DPR 1/2 and 18 exact Alustin comparisons, with actual primary/fallback font bytes checked in untimed application diagnostics. Source review verifies that only the Swash rasterizer storage/accounting file differs. Initial invalid allocation-probe root-package reuse is preserved separately and excluded from the valid probe; corrected unique package/executable guards are recorded.

Timing uses 12 balanced Williams blocks per font/DPR, five CPU or three GPU replay trials per process, and a balanced Williams schedule for 12 Alustin rounds per font/backend. Three input-contaminated queries caused whole-block retries: the accepted PT Sans cohorts have order counts 2/3/3/4 on both backends, while the other four cohorts retain 3/3/3/3. All valid observations are retained; no duration-based exclusions or retries are permitted. These are exploratory intervals without multiplicity adjustment or adjustment for implementation selection. They describe these workloads and this machine, not a universal speedup.

The raw replay and application independent audits reconstruct primary point effects and confidence intervals from retained records. Source, lock, feature-graph, executable identity, ordering and exact pixel audits are separate evidence. All six original-cache/master/candidate comparisons remain in the complete CSV/JSON statistics even though the report highlights three.

## Reproduction and preserved inputs

The three new campaign archives are `native-pool-examples`, `native-pool-alustin`, and `native-pool-source-bundle` in [results/index.json](results/index.json). The source-bundle archive contains the isolated portable wrappers and pinned native-pool source snapshots; extract it into a fresh directory, then use its prepare/build/run/analyze commands as described in [native pool reproduction](docs/native-pool-reproduction.md). Existing repository vendor inputs remain unchanged.

| Preserved input | SHA-256 |
| --- | --- |
| core/analysis/phase/summary.csv | `403d7bcb564d2113ff4544ad7a9f8763311c62c37627c13711d3507965c41b85` |
| core/analysis/sequence/summary.csv | `ae7098b3a73eae30d38ab3c83b55204609d5780dd0521089a938c4724c50f06f` |
| app/analysis/summary.csv | `fa10e3a0a24687b600a805800cd2bec965a570b5836cd2c3a0b965c6e77dd1c9` |
| core/probe/results.json | `25b686b7c9c5d7ab5b4023158b089c0f55fbb7d7e1e0687a2453e745cbbf8275` |
| core/source-review.json | `7283fdc15003c2fc3400da16bce68520d98095f2bd346d34f434de963ccb5235` |
| core/candidate-proof.json | `bc2b46ee94d2aee2f1f49e7c3d196041a0b670e0c6ea6a2334fd29a270ad34b2` |
| core/runtime/core/experiment.json | `e370d187cee3441c647489d2f8d40191b8a4c916d74fe5d32d8393407ca965d2` |
| core/independent-replay-statistics-audit.json | `10f7285bd619536250fbb88fbf5022021f4f1c142d7df886d0020060f37e011e` |
| core/independent-identity-pixel-audit.json | `0e1eb1cb151e57dcc2e70674a54507cb346e4838753f3808e0bc69ba24148119` |
| app/independent-app-statistics-audit.json | `19d94a76ff02cb6a5a736cef7949f0d0478b1183a3de469750f8a8a30f07a3ed` |
| core/maintainer-assessment.md | `6287b09c145f4e9e0761ce2bbb53d4d47d684b6189c53a6ba25fb07ecd5b5a60` |
