# Why the Gray8 atlas prototype was rejected

The Gray8 prototype uses native Swash output and existing FemtoVG renderer support. It changes only Swash mask atlas storage/upload in `src/text.rs`: masks use Gray8, color and GPU path/stroke glyphs use RGBA. Cache keys, outline accounting, eager admission, dependencies, and Swash remain unchanged. The renderer already supports Gray8 as R8Unorm/RED, and its font-mask shaders replicate the sampled red channel. No backend or shader implementation was added.

For a 512×512 atlas, mask pixel storage falls from 1 MiB to 256 KiB, excluding driver metadata and attachments. Padded mask uploads and CPU pixel buffers use one quarter as many bytes. A mixed scene can instead need both a Gray8 and an RGBA texture, totaling 1.25 MiB of pixel backing instead of one shared 1 MiB atlas. The format split also changes packing, bindings, and allocation timing.

Unit capture tests matched native Swash mask/color upload bytes, placement, formats, and zero borders, and verified that strokes remain RGBA. All 165 library tests, minimal-feature checks, and formatting passed. That validation was insufficient to establish end-to-end equivalence.

## Actual GPU failure and causal experiment

The first draft final cohort compared master/current/combined-final/Gray8 on real Metal. For the completed stock DPR1 configuration, current and combined final matched master for all 28 phases. Gray8 matched all 20 non-text phases but differed in all eight text phases at pixel (794,16). The size-advance text phase had one additional pixel differing by one gray level. The cohort stopped and retained the failure; it is not a successful Gray8 performance comparison.

The persistent mismatch is the rust-colored instruction text at the top right, away from the screen-space RUST strokes. Instrumented source copies identify two 16px mask quads covering pixel center (794.5,16.5): an `r` at screen (789,15)..(797,26), and an `e` at (794,15)..(805,27). Master's `e` starts at atlas (325,451), so this screen pixel samples its zero left padding at atlas (325,452). The adjacent 72px stroked R uses allocation (267,388), dimensions (57,68). GPU path rendering does not clip to its allocated glyph rectangle.

A diagnostic master clone retained all packing, metrics, quads, native mask uploads, and deferred commands, changing only the GPU path-mask RGB factor from 1/8 to zero. Real Metal readback gave:

| Variant | RGBA at screen pixel (794,16) |
| --- | --- |
| Diagnostic master | 206,147,122,255 |
| Diagnostic Gray8 | 209,159,137,255 |
| Master with identical packing and zero path-mask RGB writes | 209,159,137,255 |

The causal test establishes that deferred path-stroke writes contaminate adjacent native-mask padding in master's shared RGBA atlas. Separate R8 and RGBA textures remove that coverage. This is a packing/render-target interaction, not evidence that native Swash returned different mask pixels or that R8 normalized sampling changed them.

Gray8 therefore fails the required master-exact mixed-scene gate. Preserving only logical placement across formats would not reproduce cross-format contamination. Correcting the existing path-atlas overflow should be a separate rendering change with explicit before/after validation. The extra size-advance gray-level discrepancy was not separately localized; the persistent causal failure is enough to reject this prototype from the cache PR. Original sources, failed output, and diagnostic output remain intact; no Gray8 v2 fix was substituted.

The [diagnostic manifest](../results/gray8-diagnosis/archive.json) and [diagnostic records](../results/gray8-diagnosis/records.tar.gz) contain `DIAGNOSIS.md`, `provenance.json`, `pixel-results.json`, instrumented source copies, and raw CPU/GPU logs/readbacks under `gray8-diagnosis/`. Diagnostic provenance SHA256 is `5fe5a92c3344b767ee097453f60067dd8e6104ca496eeedac5e378efbed7078f`. Compiled binaries are omitted by the archive policy; their exact hashes and rebuild inputs remain recorded.

The original failed cohort and optional Gray8 source/validation are preserved in the [draft-final manifest](../results/draft-final-examples/archive.json), [draft-final records](../results/draft-final-examples/records.tar.gz), and [screening records](../results/miss-screening-examples/records.tar.gz). The failure is `draft-final-examples/results/pixels-provenance.json`; it has `complete: false` and must not be presented as completed correctness or timing evidence.

## Separate successful mixed-font validation

A separate untimed helper validates the frozen v2 master/current/final/route cohort using native WGPURenderer. It reuses the existing dependency lock and native Swash 0.2.10. A test-only font builder adds an sbix PNG to the existing Bungee COLR subset, retains the outlines, recomputes every SFNT table checksum and head.checkSumAdjustment, and validates all checksums. Native source checks establish nine public glyph IDs, glyph 8 outline/Mask, glyph 2 COLR/Color, and glyph 7 sbix PNG/Color. The PNG is independently decoded by native Swash and checked against its exact 24×24 RGBA payload.

Eight scenes cover masks, mask+COLR+PNG in one run, negative/fractional placement and clipping, overlapping PNG-first/COLR-second input and both explicit orders, strokes after masks, and nonuniform direct outlines after masks plus an atlas PNG. Each runs cold at phase 0.3, second at 0.4, and warm at 0.4, with configured DPR1/DPR2. Explicit glyph-run font size/positions stay fixed; DPR changes canvas/renderer configuration and path tolerances.

All four executables produced 48 images. All 144 candidate/master RGBA comparisons were byte-identical. Each executable passed six observable painter-order checks: PNG-first/COLR-second input equals explicit legacy COLR-then-PNG drawing and differs from the opposite order. Read-only checks of all 24 legacy-overlap captures found exactly 576 non-background pixels equal to the native PNG's [255,0,64,255]. Existing public atlas-inspector/image_info APIs verified atlas formats; the helper enables debug_inspector uniformly in release, with debug atlas initialization disabled.

Master panics if a direct/nonuniform bitmap glyph initializes its ephemeral atlas while draw_glyph_run already holds text_context mutably borrowed. This native baseline failure is retained in `color-validator/results-baseline-v3/master/{stdout,stderr}.txt`. The successful direct case draws its PNG through the supported atlas path before drawing the nonuniform outline. No master fix or custom renderer was introduced. The WGPU get_native_texture API is unsupported, and Renderer::render exposes a private ImageStore type; earlier API probes are preserved rather than worked around with library exports.

The successful helper and raw proof are archived inside [draft-final records](../results/draft-final-examples/records.tar.gz), under `draft-final-examples/color-validator/`, although its tested source cohort is the later v2 master/current/final/route selection. Its own frozen source maps identify that cohort precisely. `results-selection-v2/summary.json` SHA256 is `043c0a1dd28f8475a718656640f2669f0f70d69b3da21c459cd1edd5111a5239`; `build-selection-v2/provenance.json` SHA256 is `ac94351ac7df23b233b5c536068fbdc56f288492dddb184603c0ac8f30ab3e72`. These are correctness results, not performance measurements or validation of the rejected Gray8 prototype.
