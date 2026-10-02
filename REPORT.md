# FemtoVG Swash outline-cache study

Selected: keep the eager Swash outline cache with lazy native Scaler reuse, a legacy-preserving PNG prepass, and compact outline arenas with public soft accounting. The arena removes the measured unique-instance CPU downside in the cheap-font controls and preserves the larger reuse gains. Its incremental application effect is mostly uncertain; the selection rests on the directly paired miss controls and example results as well as the overall patch-versus-master comparison.

The primary comparison is the selected patch versus master. Original-cache and prototype comparisons explain the selection. Negative duration changes mean faster. Cells show median paired changes, 95% whole-block bootstrap intervals, and median paired absolute changes. Absolute medians need not reproduce the paired percentage.

## Selected patch versus master: existing examples

| Font | Scene | Measurement | Master → selected (ms) | Selected/master |
| --- | --- | --- | --- | --- |
| Roboto Flex | demo | CPU drawing | 1.485 → 1.408 | -5.4% [-6.5, -4.2]<br>Δ -0.080 ms |
| Roboto Flex | text | CPU drawing | 7.590 → 7.310 | -3.8% [-5.2, -2.5]<br>Δ -0.289 ms |
| Vollkorn Medium | demo | CPU drawing | 6.761 → 4.539 | -33.0% [-33.7, -32.5]<br>Δ -2.233 ms |
| Vollkorn Medium | text | CPU drawing | 27.332 → 20.877 | -24.0% [-24.3, -23.3]<br>Δ -6.512 ms |
| PT Sans Regular | demo | CPU drawing | 2.039 → 1.730 | -14.8% [-16.0, -13.8]<br>Δ -0.295 ms |
| PT Sans Regular | text | CPU drawing | 9.336 → 8.461 | -9.4% [-10.3, -8.3]<br>Δ -0.871 ms |
| Roboto Flex | demo | GPU completion | 10.275 → 10.603 | -1.4% [-7.4, +13.4]<br>Δ -0.122 ms |
| Roboto Flex | text | GPU completion | 30.604 → 29.621 | -2.3% [-4.7, -0.6]<br>Δ -0.712 ms |
| Vollkorn Medium | demo | GPU completion | 16.580 → 14.181 | -15.9% [-19.8, -9.9]<br>Δ -2.584 ms |
| Vollkorn Medium | text | GPU completion | 49.674 → 43.851 | -11.9% [-13.6, -9.2]<br>Δ -6.028 ms |
| PT Sans Regular | demo | GPU completion | 11.440 → 11.106 | -3.1% [-4.2, +1.1]<br>Δ -0.362 ms |
| PT Sans Regular | text | GPU completion | 31.647 → 30.722 | -2.6% [-4.4, +3.1]<br>Δ -0.818 ms |

GPU completion includes drawing and submission and is not a GPU timestamp. All original example phases remain in the complete [per-phase statistics](analysis/selection-examples/summary.csv).

## Alustin first-render CPU

These diagnostic spans measure renderer-thread host work, including component rendering and flush. They do not establish GPU completion, compositor latency, or diagnostics-off startup.

| Font | Backend | Master → selected (ms) | Selected/master | Original cache/master |
| --- | --- | --- | --- | --- |
| Roboto Flex | WGPU | 15.007 → 14.645 | -0.8% [-3.6, +0.3]<br>Δ -0.112 ms | +0.5% [-3.2, +3.2]<br>Δ +0.082 ms |
| Roboto Flex | OpenGL | 16.008 → 15.526 | -2.5% [-5.2, -1.2]<br>Δ -0.396 ms | -0.9% [-3.0, +2.3]<br>Δ -0.151 ms |
| Vollkorn Medium | WGPU | 22.783 → 17.748 | -22.6% [-24.1, -19.0]<br>Δ -5.222 ms | -19.8% [-23.5, -18.6]<br>Δ -4.478 ms |
| Vollkorn Medium | OpenGL | 24.175 → 19.018 | -20.5% [-21.8, -19.6]<br>Δ -4.897 ms | -19.6% [-20.9, -18.6]<br>Δ -4.784 ms |
| PT Sans Regular | WGPU | 15.587 → 14.856 | -4.1% [-7.5, +1.4]<br>Δ -0.636 ms | -3.4% [-6.2, -1.8]<br>Δ -0.531 ms |
| PT Sans Regular | OpenGL | 17.015 → 16.025 | -6.5% [-8.4, -1.8]<br>Δ -1.098 ms | -4.7% [-5.3, -3.6]<br>Δ -0.806 ms |

[All Alustin spans, first and filtered search frames](analysis/selection-alustin/summary.csv) retain gains, regressions, and uncertain effects.

## Alustin filtered search-frame CPU

The search update can introduce new atlas keys. It is a repeated application interaction, not a completely warm redraw.

| Font | Backend | Master → selected (ms) | Selected/master |
| --- | --- | --- | --- |
| Roboto Flex | WGPU | 2.348 → 2.267 | -4.6% [-7.0, -0.5]<br>Δ -0.109 ms |
| Roboto Flex | OpenGL | 2.193 → 2.235 | +5.1% [-1.3, +10.1]<br>Δ +0.110 ms |
| Vollkorn Medium | WGPU | 2.581 → 2.423 | -5.7% [-12.9, -4.4]<br>Δ -0.148 ms |
| Vollkorn Medium | OpenGL | 2.405 → 2.212 | -8.4% [-9.9, -8.2]<br>Δ -0.209 ms |
| PT Sans Regular | WGPU | 2.370 → 2.345 | -2.1% [-3.8, +0.2]<br>Δ -0.054 ms |
| PT Sans Regular | OpenGL | 2.212 → 2.241 | +0.8% [-3.9, +3.9]<br>Δ +0.017 ms |

## Alustin process memory

Process-lifetime high-water RSS comes from the same diagnostics-on application cohort. It includes host memory for the application, renderer, fonts, driver state, and transient work; it measures neither device VRAM nor the outline cache alone.

| Font | Backend | Master → selected peak RSS (MiB) | Paired RSS Δ, 95% CI (MiB) |
| --- | --- | --- | --- |
| Roboto Flex | WGPU | 278.26 → 278.98 | +0.180 [-1.000, +1.719] |
| Roboto Flex | OpenGL | 248.91 → 249.19 | +0.172 [-1.305, +1.531] |
| Vollkorn Medium | WGPU | 275.09 → 275.49 | +0.242 [+0.039, +0.562] |
| Vollkorn Medium | OpenGL | 249.05 → 248.76 | -0.414 [-1.773, +0.148] |
| PT Sans Regular | WGPU | 276.70 → 277.29 | +0.938 [-0.609, +1.711] |
| PT Sans Regular | OpenGL | 248.96 → 249.11 | +0.211 [-0.367, +0.711] |

## Miss downside and complete controlled sequences

Each controlled frame introduces 94 new atlas keys. The two-phase total includes both populations; pollution includes both hot-population frames, all 64 pollution frames, and hot return. The variation grid always uses Roboto Flex, so only its stock-font factor is shown here.

| Font | Complete sequence | Original/master | Route/master | Arena/master | Arena/route |
| --- | --- | --- | --- | --- | --- |
| Roboto Flex | 94 one-use glyphs | +7.4% [+5.4, +9.3]<br>Δ +0.018 ms | -18.5% [-20.4, -17.3]<br>Δ -0.045 ms | -23.7% [-25.0, -23.0]<br>Δ -0.058 ms | -6.7% [-7.3, -4.7]<br>Δ -0.013 ms |
| Roboto Flex | First + second phase | -4.0% [-6.3, -2.5]<br>Δ -0.015 ms | -18.6% [-20.7, -17.8]<br>Δ -0.069 ms | -25.1% [-25.9, -23.7]<br>Δ -0.093 ms | -6.5% [-9.0, -6.2]<br>Δ -0.020 ms |
| Roboto Flex | 32 unique sizes | +13.3% [+12.8, +14.0]<br>Δ +0.776 ms | +6.4% [+5.7, +7.3]<br>Δ +0.373 ms | -4.6% [-5.4, -4.2]<br>Δ -0.266 ms | -10.4% [-10.8, -10.1]<br>Δ -0.657 ms |
| Roboto Flex | 32 unique weights | +10.9% [+10.4, +11.2]<br>Δ +0.837 ms | -21.6% [-22.0, -21.2]<br>Δ -1.682 ms | -29.7% [-30.0, -29.1]<br>Δ -2.327 ms | -10.2% [-10.7, -9.7]<br>Δ -0.623 ms |
| Roboto Flex | Hot + 64-size pollution + return | +11.1% [+10.2, +12.0]<br>Δ +1.432 ms | +5.0% [+4.7, +5.1]<br>Δ +0.658 ms | -5.1% [-5.2, -4.7]<br>Δ -0.673 ms | -9.4% [-9.8, -9.1]<br>Δ -1.299 ms |
| Vollkorn Medium | 94 one-use glyphs | +1.6% [+0.7, +2.9]<br>Δ +0.025 ms | -3.3% [-4.5, -2.6]<br>Δ -0.052 ms | -4.7% [-5.0, -3.9]<br>Δ -0.074 ms | -1.0% [-2.3, -0.5]<br>Δ -0.016 ms |
| Vollkorn Medium | First + second phase | -41.0% [-41.9, -40.8]<br>Δ -1.238 ms | -43.8% [-44.4, -43.5]<br>Δ -1.316 ms | -44.7% [-45.2, -44.3]<br>Δ -1.349 ms | -2.0% [-3.0, -0.3]<br>Δ -0.034 ms |
| Vollkorn Medium | 32 unique sizes | +1.5% [+1.2, +2.7]<br>Δ +0.720 ms | +1.5% [+0.4, +2.1]<br>Δ +0.684 ms | -0.6% [-1.2, +0.5]<br>Δ -0.285 ms | -1.6% [-2.6, -0.9]<br>Δ -0.756 ms |
| Vollkorn Medium | Hot + 64-size pollution + return | +0.4% [-0.3, +0.9]<br>Δ +0.413 ms | -0.4% [-0.7, +0.9]<br>Δ -0.392 ms | -2.3% [-2.7, -2.0]<br>Δ -2.353 ms | -2.2% [-2.9, -1.9]<br>Δ -2.197 ms |
| PT Sans Regular | 94 one-use glyphs | +3.7% [+2.8, +4.6]<br>Δ +0.018 ms | -7.9% [-9.3, -7.1]<br>Δ -0.038 ms | -11.3% [-11.9, -11.1]<br>Δ -0.055 ms | -3.7% [-4.2, -2.8]<br>Δ -0.016 ms |
| PT Sans Regular | First + second phase | -27.4% [-27.8, -27.2]<br>Δ -0.224 ms | -33.5% [-33.9, -32.5]<br>Δ -0.272 ms | -36.1% [-37.1, -35.6]<br>Δ -0.292 ms | -4.7% [-5.2, -3.5]<br>Δ -0.025 ms |
| PT Sans Regular | 32 unique sizes | +6.5% [+5.7, +7.0]<br>Δ +0.793 ms | +2.5% [+2.0, +3.1]<br>Δ +0.301 ms | -2.4% [-2.6, -2.0]<br>Δ -0.297 ms | -4.8% [-5.7, -4.0]<br>Δ -0.586 ms |
| PT Sans Regular | Hot + 64-size pollution + return | +4.9% [+4.4, +6.0]<br>Δ +1.294 ms | +2.2% [+1.7, +3.1]<br>Δ +0.568 ms | -2.9% [-3.2, -2.4]<br>Δ -0.770 ms | -5.0% [-5.5, -4.7]<br>Δ -1.338 ms |

## Marginal arena benefit in the examples and application

Route combines lazy native Scaler reuse and the legacy-preserving PNG prepass. Arena adds reusable native Outline scratch and compact cached geometry. This direct pairing measures the complete added storage/accounting implementation; it cannot attribute the result solely to allocation changes.

| Font | Scene | Arena/route |
| --- | --- | --- |
| Roboto Flex | demo CPU first paint | -1.0% [-2.9, -0.6]<br>Δ -0.014 ms |
| Roboto Flex | text CPU first paint | -0.7% [-1.9, -0.1]<br>Δ -0.052 ms |
| Vollkorn Medium | demo CPU first paint | -0.9% [-1.3, +0.6]<br>Δ -0.038 ms |
| Vollkorn Medium | text CPU first paint | -0.4% [-0.7, -0.1]<br>Δ -0.086 ms |
| PT Sans Regular | demo CPU first paint | -0.7% [-1.7, +0.5]<br>Δ -0.012 ms |
| PT Sans Regular | text CPU first paint | -1.5% [-2.1, -0.7]<br>Δ -0.128 ms |
| Roboto Flex | Alustin WGPU first CPU | -0.3% [-1.8, +1.9]<br>Δ -0.043 ms |
| Roboto Flex | Alustin OpenGL first CPU | -1.5% [-2.9, +0.0]<br>Δ -0.230 ms |
| Vollkorn Medium | Alustin WGPU first CPU | +0.5% [-0.7, +1.9]<br>Δ +0.098 ms |
| Vollkorn Medium | Alustin OpenGL first CPU | -0.5% [-2.6, +0.7]<br>Δ -0.087 ms |
| PT Sans Regular | Alustin WGPU first CPU | +1.3% [-3.0, +4.2]<br>Δ +0.193 ms |
| PT Sans Regular | Alustin OpenGL first CPU | +0.4% [-4.5, +2.3]<br>Δ +0.062 ms |

## Reported example sequences

These totals include every reported phase, including movement, reflow, zoom, size, weight, and slant changes. They exclude 119 unreported warmup frames per scene and are not full launch-to-end durations.

| Regular-font factor | Scene | Reported frames | Measurement | Selected/master |
| --- | --- | --- | --- | --- |
| Roboto Flex | demo | 65 | CPU | -2.8% [-3.8, -2.4]<br>Δ -1.044 ms |
| Roboto Flex | text | 88 | CPU | -2.7% [-3.2, -2.1]<br>Δ -2.548 ms |
| Roboto Flex | font_variations | 63 | CPU | -2.9% [-3.3, -2.5]<br>Δ -0.303 ms |
| Vollkorn Medium | demo | 65 | CPU | -32.5% [-33.1, -32.2]<br>Δ -45.129 ms |
| Vollkorn Medium | text | 88 | CPU | -27.0% [-27.3, -26.8]<br>Δ -52.851 ms |
| PT Sans Regular | demo | 65 | CPU | -13.4% [-13.7, -13.0]<br>Δ -6.323 ms |
| PT Sans Regular | text | 88 | CPU | -7.4% [-7.8, -7.0]<br>Δ -7.486 ms |
| Roboto Flex | demo | 65 | GPU completion | -1.0% [-2.5, +0.4]<br>Δ -1.255 ms |
| Roboto Flex | text | 88 | GPU completion | -1.2% [-2.5, +0.3]<br>Δ -2.551 ms |
| Roboto Flex | font_variations | 63 | GPU completion | -0.1% [-2.0, +1.3]<br>Δ -0.049 ms |
| Vollkorn Medium | demo | 65 | GPU completion | -22.0% [-23.8, -20.4]<br>Δ -56.204 ms |
| Vollkorn Medium | text | 88 | GPU completion | -19.1% [-20.7, -17.9]<br>Δ -63.392 ms |
| PT Sans Regular | demo | 65 | GPU completion | -7.8% [-8.9, -3.7]<br>Δ -11.222 ms |
| PT Sans Regular | text | 88 | GPU completion | -3.9% [-4.7, -2.2]<br>Δ -8.564 ms |

## Exploratory regression audit

The following selected/master example CPU-drawing, example GPU-completion, and Alustin CPU effects have a positive 95% interval. The complete tables also retain every interval spanning zero. These are exploratory per-metric intervals without multiplicity adjustment, so isolated effects should not be treated as universal regressions.

| Font | Observation | Selected/master |
| --- | --- | --- |
| PT Sans Regular | text/warm CPU | +0.7% [+0.0, +2.0]<br>Δ +0.002 ms |
| Roboto Flex | demo/pan CPU | +0.2% [+0.0, +1.2]<br>Δ +0.001 ms |
| Vollkorn Medium | text/warm CPU | +0.9% [+0.3, +1.5]<br>Δ +0.002 ms |
| Vollkorn Medium | text/x_return CPU | +0.6% [+0.0, +1.7]<br>Δ +0.002 ms |

## Correctness, source scope, and limits

The selected production sources match the frozen timed snapshot byte-for-byte. Workspace default+Swash tests pass 171/171; default-without-Swash and Swash-only library checks and formatting pass. The frozen Swash-only suite passes 155/155. All 504 example, 144 mixed-color-validator, and 18 Alustin RGBA comparisons match master. Separate accepted Alustin pixel launches verify the intended primary faces and bundled Inter fallback. Independent audits recompute all 3,888 replay point effects and 1,296 primary interval rows, plus all 684 application point effects and 72 first/search CPU interval rows.

The optimization paths are Swash-only and internal to FemtoVG. They use existing native Swash scaling/source APIs; shared atlas helper factoring also compiles outside Swash with unchanged behavior. No Swash source, version requirement, or hint interpreter changes are included. The cache remains eager; the nominal budget remains 1 MiB. There is no validated static bytecode cutoff.

The original budget is logical accounting. Arena counts its own capacities plus public logical native-scratch high-water lengths. Neither is a total-heap limit; map spare storage, allocator overhead, native ScaleContext storage, private Swash scratch capacity, and transient allocations are excluded. See [methodology](docs/methodology.md).

The initial prepass changed mixed PNG/COLR painter order and was replaced by the guarded version. Gray8 removes an existing path-stroke contamination of adjacent native-mask padding, causing a master pixel difference; it is excluded from this cache change. Its [causal diagnosis](docs/gray8-diagnosis.md) and incomplete cohort remain archived. The original private-allocation-estimation arena was superseded by public-only accounting.

The original Image/RGBA pool reduced allocation requests but regressed some cold controls. Instance indexing and Entry lookup had mixed small effects and did not justify additional production changes. [Prototype evidence](docs/miss-prototypes.md) preserves those benefits and costs. Earlier admission experiments remain archived, including complete sequence penalties and excluded startup attempts.

Final results come from complete fresh-process balanced blocks, 5 CPU or 3 GPU trials per replay process, and diagnostic Alustin render spans. Raw observations, all six comparisons, failures, scripts, snapshots, locks, and source/executable hashes remain in [the archive index](results/index.json). [Reproduction instructions](README.md) distinguish a standalone replay from the application checkout and its external fixture requirements.

The final cohorts recorded arm64 macOS 26.6.2. Every timed GPU replay reported an Apple M4 Max integrated GPU using Metal through WGPU; Alustin exercised WGPU30 and OpenGL at 2560 × 1600 pixels with scale factor 2. Both build records identify rustc 1.96.0 (ac68faa20, 2026-05-25) and Cargo 1.96.0 (30a34c682, 2026-05-25). CPU core configuration and memory capacity were not recorded, so this report does not infer them from the current host.

The implementation selection is exploratory and uses these same cohorts. Its intervals describe process variability; they do not adjust for choosing among prototypes, fonts, or endpoints. The study supports the measured workloads on this machine rather than a universal application speedup.

## Source pins and report inputs

Upstream master: `f57a2c39e9836c146556c58c98d80c5bf7899029`. Original eager cache: `7a278ca4f947658d01c355c450edc6abcdbe3958`. Alustin main: `ac35d4e0b5c52edb7defb9feccdadfd584635c14`. Locally modified candidates are identified by complete source maps and executable hashes, rather than represented as additional source commits.

| Preserved statistics | SHA-256 |
| --- | --- |
| [selection.json](selection.json) | `a0e3752ccabb3bd1db9c45c6a97a20c7d32d8c6a0f0e48ca9ecae7c03d7577eb` |
| [scripts/render-report.py](scripts/render-report.py) | `6d4448eeab29e9e25b48550f6eeb3f8055699790b0b341a482c0d123df9b2e7c` |
| [analysis/selection-examples/summary.csv](analysis/selection-examples/summary.csv) | `5163c9fee6e5d1c5c71cb91e74934a7fef2ed39a0ad560f6f6ba7a9a0c3ec6f0` |
| [analysis/selection-examples/summary.json](analysis/selection-examples/summary.json) | `ecec9d8c49aefe2ffba9aafa1b731665873bb9fd74f18ee0bf64f0131bcaada7` |
| [analysis/selection-sequences/summary.csv](analysis/selection-sequences/summary.csv) | `4fa74c4f1506f7cb479207250acb2a14095c6d15b0bdef669a1545684b5a6eea` |
| [analysis/selection-sequences/summary.json](analysis/selection-sequences/summary.json) | `3921a9a6ecc8306fcf1ea46867b82a7285d8db6a33e28721d6983a71d523736b` |
| [analysis/selection-alustin/summary.csv](analysis/selection-alustin/summary.csv) | `0ed5c649db122463eaba88309484909cdb8e68ce4ce2c515d3465d7d0bbb6a04` |
| [analysis/selection-alustin/summary.json](analysis/selection-alustin/summary.json) | `a9eeb49f5f6008c93acf7289c076cbcd3dc3c66d56d8e28e13bf159e9507008a` |
