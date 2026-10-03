Swash currently re-hints a glyph when a new subpixel position misses the atlas. Retaining its hinted geometry avoids that work; the saving grows with the cost of the typeface’s glyph programs.

A Fleur de Leah proof sheet with 1,980 glyph requests across sizes and subpixel positions takes **89.30 → 19.94 ms**. Frames at new sizes take **90.61 → 21.69 ms/frame**.

In FemtoVG’s demo, first-paint CPU time with Swash is:

| Typeface | Master | Proposed |
|---|---:|---:|
| Roboto Flex | 1.69 ms | 1.68 ms |
| PT Sans | 2.19 ms | 1.90 ms |
| Vollkorn | 6.73 ms | 4.62 ms |
| Rye | 6.51 ms | 3.88 ms |
| Fleur de Leah | 7.24 ms | 4.92 ms |
| Diplomata SC | 7.32 ms | 4.53 ms |

Shared geometry buffers and reused working storage limit miss costs. Adding these during development changed a Roboto Flex size sweep from 0.37 ms slower to 0.27 ms faster than master.

The private Swash cache lives in the shared text context, with a 1 MiB soft budget and whole-cache eviction. Swash supplies hinting and color rendering. No public API, dependency or backend changes.

M4 Max/macOS, twelve paired blocks versus `6a5f15a`; CPU drawing/layout, excluding setup/GPU. Demo DPI 2, proof sheet DPI 1. Non-Swash demo controls show no resolved change; small generic-path costs and atlas fixes are detailed separately. Tests pass with defaults and both Swash configurations.

Built with assistance from OpenAI Codex.
