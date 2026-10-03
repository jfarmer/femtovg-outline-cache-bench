Dynamic TrueType execution diagnostic
===================================

This is an isolated count-only diagnostic, never a timing result. Instrumented
Skrifa 0.44.0 was copied under this study; production FemtoVG, Swash, and the
Cargo registry were not edited. Only the dispatch loop and a counter API were
added in the private copy. The unchanged-reference package and counted package
use identical drivers and pinned dependency versions/features, separate names
and separate targets. All 560 ten-phase native alpha cases match retained
screen counts/digests; hinted and unhinted per-glyph geometry hashes agree
between unchanged and counted builds. No VM execution errors occurred.

DPR2 values below are medians across five logical sizes of the per-case mean
completed VM dispatches per unique glyph. Builder Font/prep dispatches are
separate cold preparation counts per instance, excluded from glyph counts.

| Locale/profile | Font | Glyph dispatches | Called fpgm dispatches | CALLs | LOOPCALLs | Builder Font | Builder prep |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| en/demo_unique | Rye-Regular | 2884.48 | 2865.22 | 45.18 | 25.56 | 120.00 | 929.00 |
| en/demo_unique | Vollkorn-Medium | 2078.59 | 2068.67 | 41.80 | 24.07 | 280.00 | 3488.00 |
| ko/cjk_demo_unique | NanumGothic-ExtraBold | 239.29 | 196.42 | 5.21 | 0.00 | 104.00 | 7439.00 |
| ko/cjk_demo_unique | NanumMyeongjo-Regular | 232.54 | 166.33 | 4.50 | 0.00 | 96.00 | 790.00 |
| ko/cjk_demo_unique | NanumMyeongjo-ExtraBold | 226.38 | 163.42 | 4.46 | 0.00 | 40.00 | 613.00 |
| en/demo_unique | NanumMyeongjo-Regular | 158.13 | 82.65 | 2.58 | 0.00 | 96.00 | 790.00 |
| en/demo_unique | NanumMyeongjo-ExtraBold | 126.07 | 60.30 | 2.07 | 0.00 | 40.00 | 613.00 |
| en/demo_unique | NanumGothic-ExtraBold | 97.95 | 49.90 | 1.85 | 0.00 | 104.00 | 7439.00 |
| en/demo_unique | BabelStoneHan | 0.00 | 0.00 | 0.00 | 0.00 | 6.00 | 4.00 |
| en/demo_unique | NotoSansSC-VF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 4.00 |
| en/demo_unique | NotoSerifSC-VF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 4.00 |
| zh/cjk_demo_unique | BabelStoneHan | 0.00 | 0.00 | 0.00 | 0.00 | 6.00 | 4.00 |
| zh/cjk_demo_unique | NotoSansSC-VF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 4.00 |
| zh/cjk_demo_unique | NotoSerifSC-VF | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 4.00 |

These counts explain why whole-font stored bytes are a weak predictor. Rye
and Vollkorn execute thousands of dispatches for each selected Latin glyph,
including calls into shared fpgm functions. The Nanum programs cover a much
larger repertoire but execute only hundreds for the sampled Latin/Hangul
glyphs. Gothic ExtraBold has substantial prep work, which occurs during
prepared-instance setup and is reused by Swash; it is not repeated per glyph.
Noto SC and BabelStone execute zero glyph VM dispatches here even though
their outlines still require decoding, scaling, and rasterization.

A dispatch is not a constant-cost machine operation. PUSH operands and code
scanned through skipped branches or function definitions are not additional
dispatches; instructions can contain internal point loops. Twilight/storage
copies, scratch initialization, allocation, parsing, variable-outline decoding
and mask rasterization remain outside this count. Font geometry, program
operations, declared scratch sizes, glyph reuse, and workload all matter.
All per-size, ASCII94, opcode and origin details remain in JSON/CSV/raw files.
