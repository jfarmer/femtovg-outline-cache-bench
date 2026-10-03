Static CJK/Hangul candidate findings
===================================

Inspection completed successfully for all 13 acquired font files, both
WenQuanYi TTC faces, and the Rye/Vollkorn controls: 15 files, 16 faces.
All acquired input hashes and byte lengths matched the acquisition manifest.
The original text corpus coverage includes newline as an unmapped control;
the renderable coverage below excludes only Unicode category Cc controls.

| Candidate | All direct glyf program bytes | fpgm | prep | ASCII95 direct bytes |
| --- | ---: | ---: | ---: | ---: |
| Nanum Myeongjo ExtraBold | 1,123,697 | 742 | 165 | 19,233 |
| Nanum Myeongjo Regular | 1,123,547 | 1,341 | 220 | 19,456 |
| Nanum Myeongjo Bold | 1,072,122 | 1,341 | 202 | 19,158 |
| D2Coding Regular | 815,434 | 371 | 78 | 8,275 |
| Rye Regular | 94,918 | 1,865 | 96 | 33,387 |
| Vollkorn Medium | 85,955 | 3,596 | 250 | 6,907 |

Nanum and D2Coding cover all 115 distinct renderable characters in the fixed
Korean UI corpus. Nanum covers only 3 of the 105 Chinese corpus characters,
so it must be evaluated with Korean text rather than allowing `.notdef`
substitution to masquerade as a CJK benchmark.

| Candidate | Korean occurrence-weighted direct glyf bytes | Korean occurrence-weighted expanded points |
| --- | ---: | ---: |
| D2Coding Regular | 39,177 | 6,626 |
| Nanum Myeongjo Regular | 37,737 | 17,728 |
| Nanum Myeongjo ExtraBold | 36,264 | 20,030 |
| Nanum Myeongjo Bold | 35,114 | 18,975 |
| Nanum Gothic Coding Regular | 29,212 | 13,706 |
| Nanum Gothic Regular | 26,367 | 13,706 |
| Nanum Gothic ExtraBold | 23,384 | 13,938 |

All of BabelStone Han, Droid Sans Fallback, Droid Sans Fallback Full, Noto
Sans SC, Noto Serif SC, and both WenQuanYi Micro Hei faces cover all 105
renderable Chinese corpus characters. BabelStone, Droid, and Noto have zero
direct glyph instruction bytes in that corpus; WenQuanYi has three bytes.
Those fonts are primarily candidates for outline/variation decoding and
geometry cost, rather than extreme TrueType hint execution.

| Candidate | Chinese occurrence-weighted expanded points |
| --- | ---: |
| BabelStone Han | 19,544 |
| Noto Serif SC | 12,368 |
| Noto Sans SC | 8,758 |
| WenQuanYi Micro Hei, either face | 6,277 |
| Droid Sans Fallback, either file | 5,730 |

BabelStone, both Droid files, both Noto SC fonts, and both WenQuanYi faces
also fully cover the Japanese UI corpus. Its expanded point totals are
19,862 for BabelStone, 18,121 for Noto Serif SC, 12,596 for Noto Sans SC,
7,185 for WenQuanYi, and 6,442 for Droid. Direct corpus hint bytes are zero.

The million-byte Nanum totals describe the entire font repertoire, not the
per-glyph cost of the Latin demo. Rye still has the largest ASCII95 direct
program total among these candidates. Direct byte lengths omit component
instruction execution and do not count VM loop/function execution. Expanded
points are unhinted default-instance geometry; they are not runtime Swash
outline sizes. Native Swash and actual master-versus-patch timing must decide
which candidates are more expensive in the workload being reported.
