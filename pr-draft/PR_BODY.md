Swash caches font information and hinting setup, but not the outline produced by hinting a glyph. FemtoVG repeats that work when it needs bitmaps of the same glyph at different fractional pixel positions. This change caches the hinted outline and reuses it to generate those bitmaps.

A simple implementation added allocations on cache misses and made some fonts and workloads with changing sizes slower. This version stores the outline points and drawing commands in shared buffers (an arena), and reuses the working buffers used to generate and rasterize outlines. Across the Swash text-fill benchmarks, the final version showed no clear slowdown, including tests with little reuse.

How noticeable the improvement is depends on:

- How expensive the font’s glyph hinting is.
- How often the UI needs new bitmaps of the same glyph at the same size at different fractional pixel positions.

For an extreme example, a [font specimen](https://github.com/jfarmer/femtovg-outline-cache-bench/blob/main/benchmarks/demo-current-20261003/raw/stress/harness-src/main.rs) draws 1,980 glyphs at three sizes, with ten fractionally shifted rows per size. Fleur de Leah has particularly expensive hinting; Rye and Roboto Flex provide comparisons. First-frame CPU times:

| Font | Master | Proposed |
|---|---:|---:|
| Fleur de Leah | 89.30 ms | 19.94 ms |
| Rye | 51.45 ms | 12.77 ms |
| Roboto Flex | 4.55 ms | 3.77 ms |

When the specimen changes sizes each frame, Fleur de Leah takes **90.61 → 21.69 ms/frame**.

First-frame CPU times from [FemtoVG’s own demo drawing code](https://github.com/jfarmer/femtovg-outline-cache-bench/blob/main/benchmarks/demo-current-20261003/raw/scenes/harness-src/demo.rs):

| Font | Master | Proposed |
|---|---:|---:|
| Roboto Flex | 1.69 ms | 1.68 ms |
| PT Sans | 2.19 ms | 1.90 ms |
| Vollkorn | 6.73 ms | 4.62 ms |
| Rye | 6.51 ms | 3.88 ms |
| Fleur de Leah | 7.24 ms | 4.92 ms |
| Diplomata SC | 7.32 ms | 4.53 ms |

The cache is private to the shared Swash text context, with a 1 MiB soft budget. No public API, dependency or backend changes.

M4 Max/macOS, twelve paired blocks versus `6a5f15a`; layout/drawing plus Void flush, excluding setup and GPU work. Demo DPI 2, specimen DPI 1. [Source, setup and raw results](https://github.com/jfarmer/femtovg-outline-cache-bench) are in the benchmark repository. Tests pass with defaults and both Swash configurations. The follow-up covers methods, atlas fixes and small costs measured outside the cached Swash fill path.

Built with assistance from OpenAI Codex.
