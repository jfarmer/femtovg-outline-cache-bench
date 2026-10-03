# Existing open fonts with greater outline-cache benefit

Rye Regular is a confirmed useful stress case. With the existing FemtoVG demo at DPR2, the complete final patch reduced CPU Canvas draw time from **6.396 to 3.761 ms** on first paint, saving **2.634 [2.564, 2.704] ms** (41.19%). Real offscreen GPU completion fell from **16.235 to 13.427 ms**, saving **2.808 [2.272, 3.323] ms**. Positive savings below mean faster final execution.

This is an existing, unmodified open font found by an intentionally favorable search. It establishes a larger benefit for this scene/font combination, rather than a representative-font or universally faster result. Previous benchmark reports and their controls remain applicable; this adds evidence rather than replacing them. [Full confirmation CSV](analysis/font-stress-confirmation/summary.csv), [machine-readable analysis](analysis/font-stress-confirmation/summary.json), and [retained raw campaign](results/font-stress-search/) support the tables.

## Confirmation against master

| Font | CPU master → final (ms) | CPU saving, 95% CI (ms) | CPU reduction | GPU completion saving, 95% CI (ms) |
| --- | --- | --- | --- | --- |
| Rye-Regular | 6.396 → 3.761 | 2.634 [2.564, 2.704] | 41.19% | 2.808 [2.272, 3.323] |
| DoulosSIL-Regular | 7.056 → 4.840 | 2.217 [2.173, 2.260] | 31.42% | 1.651 [0.755, 2.421] |
| Vollkorn-Medium | 6.675 → 4.491 | 2.184 [2.119, 2.248] | 32.72% | 2.032 [1.534, 2.466] |

Rye saves an additional **0.450 ms [0.358, 0.547]** versus the simultaneously measured Vollkorn control. Doulos saves **0.032 ms [-0.011, 0.076]** more than Vollkorn; its interval crosses zero, so greater benefit is uncertain. Its own master/final improvement is clear. The Rye increase over Vollkorn is real but moderate; a 41% demo reduction does not imply an order-of-magnitude increase over the previous favorable font.

| Font | CPU saving across 65 reported demo frames (ms) | GPU completion saving (ms) |
| --- | --- | --- |
| Rye-Regular | 53.621 [52.919, 54.343] | 69.199 [63.618, 75.326] |
| DoulosSIL-Regular | 43.862 [43.278, 44.465] | 51.815 [48.106, 55.068] |
| Vollkorn-Medium | 44.645 [43.849, 45.452] | 59.016 [53.034, 66.563] |

The 65-frame sequence is a sum of measured phase time × recorded frames, with a process median of trial totals. It excludes 119 unreported warm-up frames between first paint and the warm measurement. It is not wall-clock replay duration. CPU draw, GPU submit and GPU completion are cumulative alternative endpoints and must not be added together.

| Font | CPU zoom in (ms/frame) | CPU zoom out (ms/frame) | CPU warm (µs/frame) | CPU pan (µs/frame) |
| --- | --- | --- | --- | --- |
| Rye-Regular | 2.570 [2.537, 2.604] | 1.671 [1.649, 1.694] | 1.81 [0.20, 3.52] | -0.23 [-2.29, 1.78] |
| DoulosSIL-Regular | 2.068 [2.042, 2.096] | 1.407 [1.385, 1.429] | -0.28 [-1.38, 1.09] | 2.33 [0.26, 4.32] |
| Vollkorn-Medium | 2.081 [2.043, 2.119] | 1.446 [1.426, 1.465] | -1.63 [-3.71, 0.31] | 1.45 [-0.70, 4.27] |

All cells show savings with nominal 95% intervals. Zoom benefits continue; atlas-warm costs are much smaller. Rye's CPU pan effect crosses zero, as do all three GPU warm effects at DPR2. GPU zoom-in/out savings for Rye are 3.192 [3.011, 3.364] and 2.137 [1.898, 2.368] ms/frame. DPR1, text, all variation and grid phases, and every metric remain in the full CSV.

## Tradeoffs retained

Warm text is slower in the CPU harness for every selected font at both DPRs: roughly 6–8 µs/frame. Size-return, x-return and y-advance also have CPU regressions. These are retained outcomes, not excluded noise.

| Endpoint | Extra final cost, 95% CI (µs/frame) |
| --- | --- |
| Rye-Regular, DPR2, cpu text/warm | 7.51 [5.71, 9.86] |
| Rye-Regular, DPR2, cpu text/x_return | 10.55 [8.47, 13.05] |
| DoulosSIL-Regular, DPR2, gpu text/warm | 120.38 [11.26, 312.09] |
| DoulosSIL-Regular, DPR2, gpu text/x_return | 147.80 [12.24, 362.85] |
| Vollkorn-Medium, DPR1, gpu grid_unique_sizes/sweep | 303.60 [0.23, 869.17] |

Doulos' GPU warm/x-return intervals are broad but exclude zero. Vollkorn's DPR1 unique-size sweep interval barely excludes zero; it is a secondary endpoint among many unadjusted comparisons. The cause of these regressions is not established by this campaign. Some fixed-Roboto variation phases also regress by small amounts; those repeated controls are not independent font-specific evidence.

The DPR2 94-glyph second-subpixel-phase control saves 1.840 [1.811, 1.870] ms/frame of CPU work for Rye and 2.421 [2.202, 2.616] ms/frame of GPU completion. CPU unique-size sweeps improve for Rye and Doulos; Vollkorn is uncertain at DPR2. Pollution and hot-return effects vary: Rye's CPU hot-return improves, while Doulos/Vollkorn CPU hot-return and all three GPU hot-return effects at DPR2 cross zero. This evidence does not establish universal improvement on misses, warm frames or cache churn.

## What the font search measures

Two exploratory waves retained 57 native and actual-demo candidate entries representing 56 distinct font files, including a repeated Vollkorn control. The native screen used ASCII94 and the demo's unique regular-font glyphs at logical sizes 11, 12, 14, 15 and 16 and DPR1/2. It compares native hinted outline scaling, native rendering, geometry reuse plus identical Alpha rasterization, and an unhinted diagnostic. Prepared scaler setup, warm-up and geometry population are excluded. Hinted geometry float bits, alpha bytes and placement match at all ten positive subpixel phases before native timing; unhinted geometry may differ by design.

| Font | All glyf program bytes | ASCII95 glyf bytes | ASCII94 expanded points | Native hinted outline (µs/glyph) | Hinted−unhinted diagnostic (µs/glyph) |
| --- | --- | --- | --- | --- | --- |
| Rye-Regular | 94918 | 33387 | 9707 | 18.86 | 18.38 |
| DoulosSIL-Regular | 286811 | 8565 | 3679 | 14.71 | 14.47 |
| Vollkorn-Medium | 85955 | 6907 | 4471 | 14.71 | 14.43 |

Rye concentrates more stored instructions and points in the ASCII actually exercised: 33,387 glyf program bytes and 9,707 expanded points versus Vollkorn's 6,907 and 4,471. Whole-font size and unused glyph coverage cannot establish this benefit. Rye's declared twilight/storage/stack maxima are only 60/71/241 versus Vollkorn's 524/810/1320, so larger VM buffer declarations are not necessary for greater savings either. The native hinted−unhinted diagnostic supports expensive repeated hinted-outline work as a useful screening signal. It does not isolate every interpreter operation or prove an exact source-level cause for the final demo difference.

The native screen does not model arena admission, eviction, shaping, actual atlas misses or the remaining rasterization cost. The final/master confirmation tests the complete patch, including scaler reuse and correctness fixes, and does not isolate the outline cache alone. No font, hinting program, scene, text, zoom schedule or cache parameter was modified to create a winner. [All 56 static font inspections](analysis/font-stress-confirmation/font-inspection.csv) and [both exploratory waves](analysis/font-stress-confirmation/search-metrics.csv) retain program bytes, maxp declarations, expanded points, versions, hashes and measured selection metrics. Large stored bytecode alone remains an inadequate cutoff.

Rye version 1.001 came from the [pinned Google Fonts source](https://github.com/google/fonts/tree/9710da1eacb3be272583c3224dcb70f9da6eadbb/ofl/rye), with its [SIL Open Font License](https://github.com/google/fonts/blob/9710da1eacb3be272583c3224dcb70f9da6eadbb/ofl/rye/OFL.txt). Doulos SIL version 7.000 came from the [official SIL release](https://github.com/silnrsi/font-doulos/releases/tag/v7.000), with the release's OFL retained. Both original binaries and licenses are archived. Vollkorn is the same version 5.000 file used as the prior beneficial control; all three hashes are bound by the frozen selection.

## Protocol, identity and limits

Font selection was frozen before new confirmation data. Confirmation retained 144 CPU and 144 GPU processes, each with all 28 phases: 12 paired blocks × 3 fonts × 2 DPRs × 2 versions, with six master→final and six final→master orders per font/DPR and rotated configurations. CPU uses five trial medians per process through Canvas with the Void renderer; GPU uses three with real offscreen WGPU/Metal. The CPU path exercises text layout, atlas creation and rasterization, while discarding rendering output. These are draw/submit/completion measurements, not application launch, displayed FPS or Alustin results. No confirmation process was excluded or retried.

Means of paired process medians give absolute savings. The percentage is the ratio of those means, which differs from older reports' median paired percentages. Nominal 95% intervals use 10,000 whole-block bootstrap resamples, seed 72531, with the same backend resamples shared across fonts/DPRs/endpoints. The control advantage subtracts simultaneous Vollkorn savings within each block. Intervals are conditional on selected fonts, unadjusted for the many secondary endpoints, and from one machine: Apple M4 Max, Mac16,5, 128 GiB RAM, 16 physical/logical CPUs, recorded macOS 26.6.2 arm64. Source and order checks do not prove absence of background activity, thermal drift or DVFS.

Before timing, six font/DPR configurations × 28 phases × master/final/native oracle produced 504 retained captures. Final RGBA bytes and atlas counts exactly match the independently built native-master oracle, whose only semantic change keys atlas entries by the actual signed raster offset. Original master parity is preserved separately; the final negative-position correctness fix need not reproduce master's aliasing. Fixed Roboto variation-control pixels are unchanged across font substitutions. Live font, source, executable, raw output and RGBA bindings passed the analysis audit. The separate direct raw/indexed-bootstrap checker reproduced 1,116 effects and 2,234 intervals within 1e-6; every retained float result is finite.

The analyzer emitted divide-by-zero, overflow and invalid-value warnings at its NumPy matmul expression. The retained warning observation was copied from the tool response, not a redirected process log. The independent indexed-bootstrap result and finite-value checks passed; no warning cause is inferred, no measurement was removed, and the measured analyzer remains unchanged.

Baseline is master `f57a2c39e9836c146556c58c98d80c5bf7899029`; final is the frozen full patch from the revised-cache campaign, using Swash 0.2.10. Prior/updated45 identities are retained but were not timed for this confirmation.

| Frozen final production source | SHA-256 |
| --- | --- |
| src/lib.rs | ae79b1702bb44fcef401b47dda0b38458160a57876f74b10cbb445d4d97c8798 |
| src/text.rs | 6ec9215f1ab17cad624fca578ef327af2bf842554d322a06887fc26b8204ca5f |
| src/text/swash_rasterizer.rs | fa2fc5852710952ee3122500e08bda3a1dd38d69a39cd0420604f51c9488ee92 |

[The report input manifest](analysis/font-stress-original-report-inputs.json) binds these reports, tables, proofs, font bytes and licenses. Acceptance of the retained evidence requires all-member archive verification followed by the independent raw/statistical audit; an offline statistical check alone does not replace pixel/source/font byte integrity. [Reproduction instructions](docs/font-stress-reproduction.md) describe the separately prepared fresh-build adaptation. Fresh reproduction builds and new timings are not claimed by this report; any later validation is recorded separately. Earlier reports remain unchanged.
