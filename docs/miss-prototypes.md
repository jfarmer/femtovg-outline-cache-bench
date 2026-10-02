# Outline-miss prototypes and what they establish

These experiments preserve eager admission: a successful first outline render can supply an immediate geometry-cache hit at a second subpixel atlas phase. They start from the original local patch, `7a278ca4f947658d01c355c450edc6abcdbe3958`, and compare against master `f57a2c39e9836c146556c58c98d80c5bf7899029`. The feature remains Swash-only. No Swash implementation, package version, renderer shader, scaler, or hint interpreter was replaced.

The original eight-variant campaign is screening evidence, not the final PR comparison. Its sources, independent prototypes, allocation observations, failed attempts, timing records, and analyses are retained in the [screening manifest](../results/miss-screening-examples/archive.json) and [screening records](../results/miss-screening-examples/records.tar.gz). Relevant archive members include `snapshots/arena`, `snapshots/pixels`, `BUFFER-VARIANTS.md`, `buffer-variants-validation.json`, `allocations/`, and `results/screening-analysis/` under the `miss-screening-examples/` prefix.

## Use the native operation; change ownership and retention

Swash already supplies `Scaler::scale_outline_into`, `Render::render_into`, and public `Outline::points`, `verbs`, and `clear`. Its owning `scale_outline` convenience method creates a new Outline and calls the same `_into` operation. `Outline::clear` clears lengths while retaining working buffers. Zeno already accepts the native point/verb slices as `PathData`, so the prototype needs no copied path representation or second outline interpreter.

Swash's existing context reuse remains authoritative for font/scaler state. The additional cache retains the resulting hinted, scaled monochrome geometry across requests; it does not reproduce native scaling or hinting. The key still distinguishes face, size, and variation coordinates, while subpixel placement is applied during rasterization. Native color-source rendering stays separate. Existing native-image equivalence tests exercise faces, sizes, variation coordinates, offsets, color sources, and missing glyphs.

| Independent prototype | Native operation reused | Work removed after buffers reach their high water | Work that remains |
| --- | --- | --- | --- |
| `arena` | `scale_outline_into`; native point/verb slices; existing Zeno mask rasterization | Repeated working-outline Vec allocation and separate retained point/verb/layer allocations per cached glyph; geometry arenas reuse capacity across full clears | First scratch/arena allocations, growth, eager geometry copy, key ownership, map operations, Image/padded-upload allocation |
| `pixels` | Native `Render::render_into` for colors; existing outline/mask calls into a caller-owned Image | Repeated Image-data and padded RGBA Vec allocation/growth | Clearing pixel bytes/borders, alpha-to-RGBA expansion, outline allocation/copy and key/map work |
| `gray8` | Existing Gray8/R8 upload and font-mask shader support | Three quarters of mask pixel storage and upload bytes; alpha-to-RGBA expansion | Fresh image/upload allocations, outline admission; separate format pools and allocation scans |

The independent arena passed 164 library tests; pixels passed 165, including a reusable-image test alternating font faces, colors, sizes, and missing glyphs. Both passed minimal Swash checks and formatting. The original eight-variant GPU replay subsequently passed all 1,176 candidate/master image comparisons across its three fonts and DPR1/DPR2. Gray8 had separate validation and was rejected after a mixed-scene pixel failure; see the [causal diagnosis](gray8-diagnosis.md).

## Arena accounting: screening estimate versus public soft budget

The original screening `arena` uses ranges into two contiguous geometry Vecs. Its nominal 1 MiB accounting charges exact point/verb arena capacities and logical key/range metadata, plus an estimate for Swash's private working-outline buffers. That estimate assumes pinned-source append behavior and Rust Vec growth minimums, and charges 64 bytes per private layer. It is an estimate, not measured private capacity. Map spare buckets and allocator overhead are excluded. Failed and oversized scaling attempts contribute to scratch high-water tracking; oversized retained scratch is discarded after use.

This changes the effective admission/clear boundary from the original patch's logical outline-length accounting. Fewer heap allocations therefore do not establish equal hit capacity at the same nominal 1 MiB setting. Arena clears retain reusable geometry backing; key/map clearing still costs work. Cold allocation and growth remain necessary, including after an oversized scratch buffer is dropped.

The later v2 `final` candidate supersedes that private estimate. It charges exact capacities of FemtoVG's own point/verb arenas and logical metadata, plus public high-water point/verb lengths and the native Outline value. It explicitly calls the 1 MiB setting a **soft accounting budget**. Swash spare capacity, private layer storage, map buckets, and allocator overhead are outside it; oversized logical scratch is reset. No RawVec growth assumption or guessed private-layer size remains. The screening arena's capacity observations and timing results must not be presented as measurements of this revised candidate.

V2 compares that soft-accounting arena combined with the guarded native routing/scaler improvements against `route`, which has the guarded routing/scaler improvements and the original cache storage. Selection uses the final v2 master comparisons, including the direct marginal comparison. This document records the rationale and prior screening; the report owns final statistics and the selection.

## Pixel buffers and retained-memory tradeoff

The pixels prototype leaves original cache keys, eager admission, outline accounting, and clear policy intact. It clears/resizes a reusable Image and padded RGBA upload Vec, preserving zero borders and native image placement. The pool is taken out of its RefCell before rendering/upload callbacks, then returned after ordinary results/errors; it does not introduce a pool borrow spanning renderer callbacks. Each buffer retains at most 256 KiB of Vec backing capacity per GlyphAtlas, for at most 512 KiB together. Oversized working buffers can exist temporarily and are dropped after consumption. Existing cache/context/renderer allocations are additional.

The untimed observer measured the following successful malloc/calloc/realloc calls during drawing at DPR2. Scene initialization and flush/output work are excluded; requested bytes count allocation traffic, not live or peak memory.

| Font and workload | Original patch calls | Arena calls | Pixels calls |
| --- | ---: | ---: | ---: |
| Stock Roboto Flex, demo first paint | 12,247 | 11,317 | 11,771 |
| Stock Roboto Flex, text first paint | 59,370 | 53,961 | 56,985 |
| Stock Roboto Flex, 3,008 unique size/glyph misses | 29,188 | 7,401 | 23,182 |
| Vollkorn, 3,008 unique size/glyph misses | 40,238 | 10,675 | 34,232 |
| PT Sans, 3,008 unique size/glyph misses | 30,803 | 7,450 | 24,798 |

All eager prototypes retained 94/94 second-phase outline hits in the controlled two-phase run. Pixels reduced that phase's allocation calls from 205 to 17 for each font, consistent with removing two transient buffers per new atlas glyph. It did not remove the miss's eager outline allocation cost.

For the unique-size sweep, observed pixels Image/RGBA capacity peaks were respectively 1,248/6,720 bytes for stock, 1,120/6,144 for Vollkorn, and 1,152/4,160 for PT Sans. These are exact retained Vec gauges, not transient allocation peaks. The original arena's point/verb capacity peaks were 688,128/61,440 bytes, 704,512/50,176 bytes, and 753,664/69,632 bytes. Its additional scratch charges of 1,424, 2,512, and 2,512 bytes remain estimates. Peaks are separate per-frame maxima and need not coincide. Clear counters were unavailable for arena/pixels; unavailable is not zero.

## Fewer allocations did not eliminate cold regressions

The screening CPU campaign used eight balanced process blocks, five trials per process, and DPR2. The following are paired median changes in draw time versus master; positive is slower. These are exploratory screening estimates with no multiplicity adjustment, and refer to the original independent arena and pixels implementations.

| Zero-reuse workload | Font | Original patch | Arena | Pixels |
| --- | --- | ---: | ---: | ---: |
| 94 one-use glyphs | Stock | +6.48% | +1.56% | +6.70% |
| 94 one-use glyphs | Vollkorn | +1.69% | −0.27% | +1.91% |
| 94 one-use glyphs | PT Sans | +3.88% | +0.96% | +4.40% |
| 3,008 unique size/glyph misses | Stock | +11.31% | +3.16% | +14.60% |
| 3,008 unique size/glyph misses | Vollkorn | +2.41% | −0.12% | +3.68% |
| 3,008 unique size/glyph misses | PT Sans | +5.43% | +1.15% | +7.97% |

The stock unique-size arena regression had a bootstrap 95% interval of +1.41% to +4.50%; pixels was +10.79% to +15.88%. Several smaller arena estimates include zero. Pixel pooling saves allocation traffic but was neutral or slower in these timing cases, so allocation counts alone cannot justify it. Existing demo first-paint benefits were preserved in the screening campaign, but those scenes already reuse geometry within a first paint; the controlled one-use scenes expose eager-cache costs separately. Both forms of evidence remain in the archive.
