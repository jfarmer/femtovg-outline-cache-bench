The cache avoids running a glyph’s hinting program again when only the bitmap’s fractional position changes. Expensive glyph programs therefore save more work. Shared geometry buffers and reused working storage also reduce the cost of populating the cache when reuse is low. The Swash text-fill comparisons found no clear slowdown; measured costs outside that path remain disclosed below.

The main comparison is proposed released code at `b87a94dd` against upstream master `6a5f15a`. The frozen candidate differs only in two test comments; source and artifact identities are recorded. The comparison includes the whole patch: geometry retention, reused buffers/scaler and native glyph routing.

The demo keeps FemtoVG’s drawing and performance graph, including layout, paths, images and strokes. Its first-paint gains recur during zoom, when new sizes require new atlas entries:

| Typeface | Zoom-in master → proposed (ms/frame) | All 65 reported frames master → proposed (ms/sequence) |
|---|---:|---:|
| Roboto Flex | 1.315 → 1.279 | 36.649 → 35.563 |
| PT Sans | 1.846 → 1.550 | 47.249 → 40.826 |
| Vollkorn | 6.038 → 4.014 | 135.338 → 91.777 |
| Rye | 5.979 → 3.420 | 134.702 → 81.109 |
| Fleur de Leah | 6.456 → 4.291 | 144.695 → 99.668 |
| Diplomata SC | 6.697 → 3.901 | 153.401 → 94.557 |

The 65-frame sequence includes first paint, 30 warm, 12 zoom-in, 12 zoom-out and 10 pan frames. The 119 intervening warmup frames are excluded. Once the bitmap atlas is warm, little hinting work remains; warm-frame changes cannot be attributed to outline-cache hits.

The proof sheet deliberately requests many positions for each hinted result: 66 Latin letters/digits/symbols in ten rows at each of three logical sizes, 14/20/28 at DPI 1. Row origins advance by 0.1 native atlas units. Public TextMetrics confirms 1,980 requests and 198 glyph-size instances per frame in both variants. Everything fits inside a finite 1800 × 1200 page; there is no invisible or clipped extra text. The rows request up to ten phase bins per instance; actual bitmap and outline-cache misses are not instrumented.

| Typeface | First paint master → proposed (ms) | Paired first-paint saving (ms, exploratory 95% interval) | All 44 frames master → proposed (ms) |
|---|---:|---:|---:|
| Fleur de Leah | 89.304 → 19.936 | 69.192 [68.633, 70.555] | 1181.153 → 284.902 |
| Rye | 51.453 → 12.771 | 38.513 [38.079, 39.176] | 687.949 → 183.041 |
| Roboto Flex | 4.551 → 3.766 | 0.787 [0.751, 0.813] | 70.493 → 59.384 |

The 44 frames include first paint, 30 warm, twelve unique size changes and one return. New sizes still repeat glyphs across positions: this stresses useful reuse rather than all misses. The earlier same-binary DPI 2 control has fewer phase bins and is archived separately.

Executed glyph programs, glyph mix, size and reuse matter; total bytecode bytes are not a cutoff. Fleur de Leah is more expensive per selected glyph than Rye in native probes, yet saves less in the ordinary demo.

Swash already caches font/scaler data and hinting instances. It still generates hinted points/commands for each scaled outline. FemtoVG’s generic cache retains unhinted font-unit paths, while its atlas retains separate bitmaps for each position. The shared text context owns the missing result between these layers without application plumbing. One private immutable run object supplies both scaler settings and the cache key, preventing independently supplied settings from disagreeing.

Color glyphs remain on Swash Render. For retained plain outlines, Render has no entry point taking scaled geometry: it takes a scaler and glyph ID and would regenerate the outline. The additional rasterization code therefore uses Zeno, already supplied by Swash, following its offset/mask construction. There is no new hinting interpreter or dependency.

The arena is two append-only vectors with map entries holding ranges. Clearing resets entries and vectors together. A working native Outline and rasterizer scratch are reused; misses share a lazy scaler within a run. The existing development comparison illustrates why those buffers matter:

| 32 unique-size glyph populations | Earlier cache vs its master (ms/sequence) | With arena/working-buffer reuse vs its master (ms/sequence) |
|---|---:|---:|
| Roboto Flex | +0.373 | −0.266 |
| PT Sans | +0.301 | −0.297 |

These are earlier paired development measurements with an older baseline (`f57a2c3`), not final-code/current-master results or a pure allocator ablation. The earlier variant already included lazy scaler reuse and PNG routing. The added storage/buffer implementation removed the measured downside in these controls. It does not establish that an arena wins over every alternative representation.

The 1 MiB soft budget counts arena capacity, logical entry metadata and logical working-outline high water. Spare map buckets, Zeno/Swash private storage, allocator overhead and transient memory are outside it. Growth tries geometric then exact capacity before eviction; oversized outlines render without admission. There is no per-entry eviction or free list.

Native fill routing also avoids building a generic unhinted outline solely for PNG classification. Generic strokes retain their existing cache. Three already-present atlas bugs are fixed in the integration: PNG initialization’s nested mutable borrow, negative native-outline phase placement and render-target restoration on glyph errors. The shared restoration fix applies outside Swash; successful generic traces match master in the checked corpus. There are no new error variants or backend changes.

The demo uses 288 processes across two cohorts; the full-phase proof sheet adds 72. Each configuration has twelve rotating pairs, six AB/six BA. No measured process was excluded or retried; initial zero-measurement failures are preserved. Build checks bracket processes after 60 quiet seconds. Release: opt-level 3, no LTO, 16 codegen units, rustc 1.96/LLVM 22.1.2. Intervals use 10,000 paired-block bootstraps without multiplicity correction. Paired differences need not equal differences of marginal medians. These are CPU measurements, excluding font/image setup, GPU and presentation.

All 36 non-Swash demo phase/sequence intervals cross zero. Earlier isolated current-runtime controls remain relevant: non-Swash warm paragraphs add 1.3–2.4 µs/frame, generic Swash label strokes add 0.4–0.8 µs/frame, and one Swash-only cold negative-position paragraph stroke adds 16.3 µs with an interval above zero. The earlier cold synthetic eight-block analysis is provisional and post hoc; its interrupted campaigns remain archived separately. The new scene results do not erase those small costs or establish a universal speedup.

Tests cover native rendering/phase agreement, variations, growth/eviction, oversized glyphs, scaler settings, color/bitmap handling and target restoration. Default tests, both Swash configurations and selected offscreen Metal checks pass. [Sources, scripts, raw results and independent audits](https://github.com/jfarmer/femtovg-outline-cache-bench) are public, with [current results and analysis](https://github.com/jfarmer/femtovg-outline-cache-bench/blob/main/benchmarks/demo-current-20261003/SUMMARY.md). The repository’s opening table links the exact drawing code, plans and results for both scenes.
