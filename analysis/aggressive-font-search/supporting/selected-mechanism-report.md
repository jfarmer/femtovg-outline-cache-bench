Selected font mechanism evidence

This is count-only explanatory evidence. The production event traces use the sealed English CPU-only demo at requested DPR2; their initial outlines are11/12/14/15/16px. VM DPR1 rows therefore match those sizes. No new performance timing or pixel proof is claimed.

| Font | ASCII94 dispatches/glyph | Unique-demo dispatches/glyph | Mapped actual graphic-hit dispatches/glyph | First hits / misses | First retained points | Zoom clears |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Rye-Regular | 2604 | 2848 | 2666 | 156 / 112 | 15000 | 2 |
| Vollkorn-Medium | 1648 | 2034 | 2069 | 151 / 112 | 8658 | 1 |
| FleurDeLeah-Regular | 3985 | 2942 | 2029 | 152 / 112 | 17961 | 2 |
| WaterBrush-Regular | 3316 | 2781 | 2248 | 160 / 112 | 39848 | 6 |
| DiplomataSC-Regular | 2323 | 2559 | 2625 | 151 / 112 | 8228 | 1 |
| LavishlyYours-Regular | 3055 | 2602 | 1929 | 151 / 112 | 9573 | 1 |

ASCII/demo columns are medians of five per-size unique-glyph means. The hit column weights the exact first-paint repeated graphic glyphs. It is a partial join: spaces, glyph0 and any extra non-ASCII glyph omitted by the sealed VM driver remain explicitly unmeasured. All588 duplicate ASCII/demo records match, and632 mapped production misses have matching point/verb counts. Counts are dispatches, not cycles or predicted frame savings.

All six files resolve to the TrueType interpreter by actual maxp/fpgm/prep predicate. Direct stored glyph byte lengths omit called font functions and loop iterations; nearly all measured glyph dispatches come from called fpgm bodies.
ASCII94, median demo-unique glyph work, and first-paint hit-weighted work are distinct quantities. Fleur is more aggressive on full ASCII, but its actual mapped graphic hit mix executes less work than Rye. Glyph shape, text selection, point size and reuse frequency matter.
WaterBrush has many more retained points and more observed budget clears than Rye. Native unhinted/reuse costs and source-level point loops support extra geometry/memory work as an explanation; no isolated arena cost or eviction counterfactual is measured here.
Every first-paint native request stream matches between master and final, and no first-paint budget clear occurs. Fonts all produce112 regular misses but differing repeat hits and geometry. Full-patch benefit also includes batching scalers and removing redundant generic outline decoding; instruction counts cannot attribute the entire application effect to outline retention.
Every measured warm and pan phase has zero outline requests, hits, misses, native calls or scaler builds. Any measured timing difference in those phases is outside direct outline-cache work or measurement variation, and remains unexplained by these counters.
Font/prep builder counts are separate and retained by native instance caching; fpgm-origin dispatches during glyph execution represent called functions rather than rerunning the whole font program. Dispatch counts are not CPU cycles and do not measure internal point loops, scratch copies, allocations, parsing or rasterization.

All six master native-render streams exactly equal final outline-request streams, including size bits, coordinates, subpixel phases and order. Every trace matches the preserved application atlas counts. Fresh VM runs match120 retained ten-phase native alpha cases; the reused Fleur/Rye/Voll campaign matched another120. No VM errors occurred. All four collector/analyzer commands exited0; outer stderr files are empty.

The bound JSON retains every phase and role, both native DPRs, per-size records, opcode/origin details, unmatched joins, source excerpts and separate native cost-screen cohorts. The JSON manifest records original absolute paths for provenance; these Markdown links preserve the study-relative layout.

[Machine-readable report](selected-mechanism-report.json), [VM profiles](selected-mechanism-vm-profiles.csv), [all phase counts](selected-mechanism-trace-phases.csv), [partial hit-weighted join](selected-mechanism-hit-weighted-first-paint.csv), [input bindings](selected-mechanism-input-bindings.json).

[Production event analysis](../mechanism-production-trace-v1/counts-analysis.json), [independent event recount](../mechanism-production-trace-v1/independent-count-audit.json), [combined six-font VM analysis](../mechanism-vm-ornate-v1/analysis/combined-six-font-counts.json).
