# CJK font investigation and cache cost decomposition

None of the thirteen acquired CJK font files displaced Rye as the strongest
demonstration of this patch's savings. Nanum Myeongjo has over 1.12 MB of direct
glyph hinting programs, versus Rye's 94,918 bytes, but its ordinary Korean glyphs
were much cheaper to process. The unchanged English demo and separately localized
Chinese/Korean demos were both measured; replacing the font in an English scene
does not measure CJK glyph processing.

This study compares frozen upstream master f57a2c39e9836c146556c58c98d80c5bf7899029
against the final Swash-only arena patch, including correctness fixes #1–5.
It changes no production or Swash checkout code. Measurements used an Apple M4 Max,
Mac16,5, 128 GiB, macOS 26.6.2 arm64. Application comparisons are DPR2 host drawing
time in the offscreen example replay, excluding font loading, process launch,
setup and unreported warmups. They are not launch/FPS or hardware GPU measurements.
No new CJK GPU-completion timing was collected; GPU runs validated localized pixels.
All older benchmarks, font cohorts and numerical reports remain retained.

## Same unchanged English demo

Thirteen fonts, master/final, two rotated AB/BA blocks and three trials per
process: 52 processes and 4,368 raw rows. The independent live audit checked all
1,209 effects, source/build/font/order/count bindings and executable bytes.
Each process endpoint is its three-trial median; effects average the two paired
differences. This is exploratory screening, without confidence intervals or an
English application pixel-proof campaign. Small effects are not established wins.
First-paint values below are milliseconds; positive savings save time.

| Font | Master ms | Patch ms | Saved ms |
| --- | --- | --- | --- |
| Rye-Regular | 6.561 | 4.054 | +2.507 |
| Vollkorn-Medium | 6.818 | 4.641 | +2.177 |
| NanumMyeongjo-Regular | 1.788 | 1.484 | +0.304 |
| NotoSerifSC-VF | 4.686 | 4.391 | +0.295 |
| NanumMyeongjo-ExtraBold | 1.689 | 1.447 | +0.242 |
| NotoSansSC-VF | 2.293 | 2.056 | +0.236 |
| NanumGothic-ExtraBold | 1.770 | 1.536 | +0.234 |
| NanumMyeongjo-Bold | 1.723 | 1.522 | +0.201 |
| NanumGothic-Regular | 1.736 | 1.543 | +0.193 |
| WenQuanYiMicroHei-face0 | 1.582 | 1.421 | +0.161 |
| BabelStoneHan | 1.210 | 1.134 | +0.076 |
| D2Coding-Regular | 1.105 | 1.065 | +0.039 |
| NanumGothicCoding-Regular | 1.075 | 1.077 | -0.002 |

All thirteen fonts showed an observed warm-text cost in this exploratory run.
Both block effects, all five demo phases, text phases and trial-weighted
65/88/63-frame sequences are retained in
[the English comparison](analysis/cjk-font-search/english-demo-comparison.md),
and every raw-derived effect remains in its independent audit CSV.

## Separate localized confirmations

Only thirteen regular-font demo text literals were localized; layout, drawing,
sizes, transitions, other scenes and fixed Roboto variation controls were kept.
Candidate sets were frozen from native screening before application timing:
three Korean fonts with Nanum Myeongjo Regular as control, and three Chinese fonts
with Noto Sans SC as control. Each locale ran 12 balanced master/final blocks and
five trials: 72 processes and 10,080 raw rows. Each independently checked
279 effects and 560 confidence intervals, including two control advantages.

The estimator averages twelve paired process medians. Intervals use 10,000
whole-block percentile bootstrap resamples with shared indices across endpoints;
they are conditional on the selected fonts/protocol and are not familywise
adjusted. Setup/launch/untimed warmups are outside the reported sequence. Selected
first-paint host CPU results follow; savings and 95% intervals are microseconds.

| Locale | Font | Master ms | Patch ms | Saved µs [95% CI] |
| --- | --- | --- | --- | --- |
| ko | NanumGothic-ExtraBold | 2.093 | 2.013 | +79.750 [+52.239, +105.132] |
| ko | NanumMyeongjo-ExtraBold | 2.074 | 1.977 | +96.913 [+69.514, +130.248] |
| ko | NanumMyeongjo-Regular | 2.059 | 2.003 | +55.358 [+19.246, +88.706] |
| zh | BabelStoneHan | 1.896 | 1.896 | +0.719 [-18.184, +16.407] |
| zh | NotoSansSC-VF | 2.899 | 2.740 | +159.371 [+101.753, +210.081] |
| zh | NotoSerifSC-VF | 6.864 | 6.636 | +227.879 [+168.823, +287.605] |

First paint alone does not describe the tradeoffs. Below are all localized demo
draw endpoints. A reported sequence is the sum of each trial's phase mean times
its recorded frame count, followed by a process median and paired-block effect.
It covers 65 reported demo frames; it is not a sum of displayed phase medians.

| Locale | Font | Phase | Units | Saved [95% CI] | Evidence |
| --- | --- | --- | --- | --- | --- |
| ko | NanumGothic-ExtraBold | first_paint | us/frame | +79.750 [+52.239, +105.132] | improvement |
| ko | NanumGothic-ExtraBold | pan | us/frame | -1.383 [-5.113, +1.663] | uncertain |
| ko | NanumGothic-ExtraBold | reported_sequence | us/sequence | +1579.359 [+1085.926, +2017.838] | improvement |
| ko | NanumGothic-ExtraBold | warm | us/frame | -0.729 [-2.390, +1.103] | uncertain |
| ko | NanumGothic-ExtraBold | zoom_in | us/frame | +63.937 [+43.443, +83.596] | improvement |
| ko | NanumGothic-ExtraBold | zoom_out | us/frame | +47.750 [+35.789, +59.698] | improvement |
| ko | NanumMyeongjo-ExtraBold | first_paint | us/frame | +96.913 [+69.514, +130.248] | improvement |
| ko | NanumMyeongjo-ExtraBold | pan | us/frame | -2.377 [-3.675, -1.083] | regression |
| ko | NanumMyeongjo-ExtraBold | reported_sequence | us/sequence | +1574.405 [+1243.366, +1937.851] | improvement |
| ko | NanumMyeongjo-ExtraBold | warm | us/frame | -0.342 [-2.222, +1.409] | uncertain |
| ko | NanumMyeongjo-ExtraBold | zoom_in | us/frame | +62.884 [+45.048, +79.954] | improvement |
| ko | NanumMyeongjo-ExtraBold | zoom_out | us/frame | +50.991 [+38.248, +64.072] | improvement |
| ko | NanumMyeongjo-Regular | first_paint | us/frame | +55.358 [+19.246, +88.706] | improvement |
| ko | NanumMyeongjo-Regular | pan | us/frame | +1.239 [-1.940, +5.033] | uncertain |
| ko | NanumMyeongjo-Regular | reported_sequence | us/sequence | +1407.825 [+909.541, +1880.040] | improvement |
| ko | NanumMyeongjo-Regular | warm | us/frame | -1.621 [-3.042, -0.099] | regression |
| ko | NanumMyeongjo-Regular | zoom_in | us/frame | +66.209 [+40.685, +89.430] | improvement |
| ko | NanumMyeongjo-Regular | zoom_out | us/frame | +43.438 [+26.913, +58.965] | improvement |
| zh | BabelStoneHan | first_paint | us/frame | +0.719 [-18.184, +16.407] | uncertain |
| zh | BabelStoneHan | pan | us/frame | -2.391 [-3.995, -0.837] | regression |
| zh | BabelStoneHan | reported_sequence | us/sequence | +1771.890 [+55.062, +4760.522] | improvement |
| zh | BabelStoneHan | warm | us/frame | -0.653 [-2.843, +1.702] | uncertain |
| zh | BabelStoneHan | zoom_in | us/frame | +27.324 [+7.539, +50.567] | improvement |
| zh | BabelStoneHan | zoom_out | us/frame | +9.248 [-2.606, +21.862] | uncertain |
| zh | NotoSansSC-VF | first_paint | us/frame | +159.371 [+101.753, +210.081] | improvement |
| zh | NotoSansSC-VF | pan | us/frame | +0.304 [-2.231, +2.419] | uncertain |
| zh | NotoSansSC-VF | reported_sequence | us/sequence | -3055.313 [-11739.860, +1653.761] | uncertain |
| zh | NotoSansSC-VF | warm | us/frame | -3.584 [-7.319, -0.868] | regression |
| zh | NotoSansSC-VF | zoom_in | us/frame | -168.386 [-604.443, +63.489] | uncertain |
| zh | NotoSansSC-VF | zoom_out | us/frame | -48.119 [-218.187, +44.142] | uncertain |
| zh | NotoSerifSC-VF | first_paint | us/frame | +227.879 [+168.823, +287.605] | improvement |
| zh | NotoSerifSC-VF | pan | us/frame | +3.429 [+1.505, +5.482] | improvement |
| zh | NotoSerifSC-VF | reported_sequence | us/sequence | +2671.363 [+1646.412, +3927.011] | improvement |
| zh | NotoSerifSC-VF | warm | us/frame | +1.981 [+0.088, +3.821] | improvement |
| zh | NotoSerifSC-VF | zoom_in | us/frame | +139.783 [+89.084, +201.122] | improvement |
| zh | NotoSerifSC-VF | zoom_out | us/frame | +46.674 [+26.359, +76.372] | improvement |

Confirmed draw regressions in the demo or unchanged English text scene are retained explicitly:

| Locale | Font | Scene | Phase | Units | Saved [95% CI] |
| --- | --- | --- | --- | --- | --- |
| ko | NanumGothic-ExtraBold | text | size_return | us/frame | -8.364 [-13.471, -4.843] |
| ko | NanumGothic-ExtraBold | text | warm | us/frame | -6.939 [-9.242, -4.613] |
| ko | NanumGothic-ExtraBold | text | x_return | us/frame | -8.084 [-10.938, -5.245] |
| ko | NanumGothic-ExtraBold | text | y_advance | us/frame | -5.522 [-9.223, -1.995] |
| ko | NanumMyeongjo-ExtraBold | demo | pan | us/frame | -2.377 [-3.675, -1.083] |
| ko | NanumMyeongjo-ExtraBold | text | size_return | us/frame | -4.995 [-8.719, -0.976] |
| ko | NanumMyeongjo-ExtraBold | text | warm | us/frame | -8.012 [-10.042, -5.833] |
| ko | NanumMyeongjo-ExtraBold | text | x_return | us/frame | -8.517 [-10.357, -6.621] |
| ko | NanumMyeongjo-ExtraBold | text | y_advance | us/frame | -9.760 [-14.290, -6.559] |
| ko | NanumMyeongjo-Regular | demo | warm | us/frame | -1.621 [-3.042, -0.099] |
| ko | NanumMyeongjo-Regular | text | size_return | us/frame | -6.292 [-12.697, -0.111] |
| ko | NanumMyeongjo-Regular | text | warm | us/frame | -7.349 [-11.653, -3.341] |
| ko | NanumMyeongjo-Regular | text | x_return | us/frame | -8.937 [-13.862, -4.525] |
| ko | NanumMyeongjo-Regular | text | y_advance | us/frame | -8.338 [-12.360, -4.413] |
| zh | BabelStoneHan | demo | pan | us/frame | -2.391 [-3.995, -0.837] |
| zh | BabelStoneHan | text | size_return | us/frame | -7.832 [-10.911, -4.484] |
| zh | BabelStoneHan | text | warm | us/frame | -6.750 [-10.166, -2.690] |
| zh | BabelStoneHan | text | x_return | us/frame | -7.972 [-10.286, -5.595] |
| zh | BabelStoneHan | text | y_advance | us/frame | -7.007 [-10.667, -3.258] |
| zh | NotoSansSC-VF | demo | warm | us/frame | -3.584 [-7.319, -0.868] |
| zh | NotoSansSC-VF | text | size_return | us/frame | -8.883 [-16.954, -1.972] |
| zh | NotoSansSC-VF | text | warm | us/frame | -9.711 [-12.465, -6.810] |
| zh | NotoSansSC-VF | text | x_return | us/frame | -7.797 [-9.615, -5.724] |
| zh | NotoSansSC-VF | text | y_advance | us/frame | -7.181 [-10.093, -3.878] |
| zh | NotoSerifSC-VF | text | size_return | us/frame | -4.246 [-7.457, -0.518] |
| zh | NotoSerifSC-VF | text | warm | us/frame | -5.750 [-8.057, -3.416] |
| zh | NotoSerifSC-VF | text | x_return | us/frame | -3.344 [-6.056, -0.230] |
| zh | NotoSerifSC-VF | text | y_advance | us/frame | -3.771 [-6.129, -1.001] |

All controlled ASCII grids, fixed Roboto variation phases, other metrics,
uncertain effects and regressions remain in the full
[Korean summary](analysis/cjk-font-search/ko-summary.csv) and
[Chinese summary](analysis/cjk-font-search/zh-summary.csv).
Those unchanged scenes are not CJK workload results. A proposed CJK controlled
grid was prepared but not run; do not infer CJK eviction guarantees from it.

Localized pixel preflights passed nine master/patch/native-oracle processes per
locale, 252 captures each. Exact patch RGBA and atlas counts matched the uncached
native oracle using actual signed offsets. Every regular-font character was
covered in the actual Swash charmap. Droid fonts lack ASCII and were only used
in explicitly pure-CJK native kernels, never silently substituted in a demo.

## Native cost screening

Four separate screens retained 30 successful processes and all 9,600 raw rows.
Each used twenty size/DPR/profile cases, four trials, four balanced kernel orders
and twenty repeats. Exact points/verbs and ten subpixel alpha images were checked
before timing. These per-glyph kernels exclude prepared scaler construction,
cache admission, arena eviction and bitmap-atlas behavior; they neither simulate
the full patch nor predict app gains. The table takes each case's trial median,
then the median across five logical sizes (11/12/14/15/16) at DPR2, in µs/glyph.
Different language profiles contain different characters. The native screen's
DPR is its explicit size multiplier: DPR2 scales outlines at 22/24/28/30/32 px.
The actual application at requested DPR2 still traces first-paint atlas sizes
11/12/14/15/16 px, so native DPR1 cases match those initial outline sizes and
native DPR2 cases are larger-size controls. Actual demo Noto labels also request
nondefault weights; the original native screens use the default instance.
Neither mismatch permits multiplying an across-screen average by application
hit counts to claim an exact timing prediction. Separate decomposition kernels
and actual-weight supplements retain their own measured scopes.

| Screen | Font | Profile | Hinted outline | Unhinted outline | Reused raster |
| --- | --- | --- | --- | --- | --- |
| english | Rye-Regular | demo_unique | 20.049 | 0.476 | 2.656 |
| english | Vollkorn-Medium | demo_unique | 15.253 | 0.270 | 1.198 |
| ko | NanumGothic-ExtraBold | cjk_demo_unique | 2.521 | 0.354 | 1.630 |
| ko | NanumMyeongjo-Regular | cjk_demo_unique | 2.503 | 0.422 | 2.213 |
| ko | NanumMyeongjo-ExtraBold | cjk_demo_unique | 2.487 | 0.478 | 2.886 |
| ko | NanumGothic-Regular | cjk_demo_unique | 2.428 | 0.343 | 1.644 |
| ko | NanumMyeongjo-Bold | cjk_demo_unique | 2.370 | 0.452 | 2.496 |
| english | NanumMyeongjo-Regular | demo_unique | 1.707 | 0.274 | 1.129 |
| english | NanumMyeongjo-Bold | demo_unique | 1.689 | 0.268 | 1.230 |
| english | NanumMyeongjo-ExtraBold | demo_unique | 1.511 | 0.278 | 1.216 |
| english | NanumGothic-ExtraBold | demo_unique | 1.295 | 0.240 | 1.009 |
| english | NanumGothic-Regular | demo_unique | 1.237 | 0.228 | 0.983 |
| ko | NanumGothicCoding-Regular | cjk_demo_unique | 1.126 | 0.367 | 1.536 |
| ko | D2Coding-Regular | cjk_demo_unique | 0.954 | 0.224 | 1.141 |
| english | WenQuanYiMicroHei-face0 | demo_unique | 0.753 | 0.230 | 0.902 |
| english | NanumGothicCoding-Regular | demo_unique | 0.677 | 0.255 | 0.980 |
| english | D2Coding-Regular | demo_unique | 0.587 | 0.195 | 0.807 |
| zh | BabelStoneHan | cjk_demo_unique | 0.525 | 0.503 | 3.752 |
| zh | NotoSerifSC-VF | cjk_demo_unique | 0.438 | 0.446 | 3.132 |
| zh | NotoSansSC-VF | cjk_demo_unique | 0.340 | 0.337 | 2.235 |
| zh | WenQuanYiMicroHei-face0 | cjk_demo_unique | 0.334 | 0.294 | 1.785 |
| english | NotoSerifSC-VF | demo_unique | 0.234 | 0.236 | 1.258 |
| english | BabelStoneHan | demo_unique | 0.207 | 0.225 | 0.975 |
| english | NotoSansSC-VF | demo_unique | 0.194 | 0.190 | 0.890 |

The million-byte Nanum totals cover the whole repertoire. Static direct glyph
program bytes exclude component execution, function calls and loops; dynamic VM
work can differ sharply. The measured Chinese corpora have zero direct glyph
instructions in BabelStone/Droid/Noto and only three bytes in WenQuanYi.
Complex outlines still need rasterization even when their geometry is cached.
Rye's expensive hinted processing is already visible in the hinting ablation;
per-glyph cost and opportunities to reuse it must both be established.

The [static inspection](analysis/cjk-font-search/static-findings.md), original
font bytes, pinned acquisition URLs/commits, licenses and full native rankings
are preserved. Counts inspect fifteen files/sixteen faces including Rye/Vollkorn
controls and both WenQuanYi collection faces. Application/screen renders use face 0.

## Why fonts differ

# Why these fonts produce different cache results

The evidence supports two independent causes: the CPU cost of computing an outline, and the number of bitmap-atlas misses that request geometry already computed for another horizontal phase. Rye and Vollkorn have both expensive glyph-program execution and substantial phase reuse. The ordinary Chinese demo has inexpensive glyph outlines and little additional phase reuse. Large font files, large repertoires and whole-font instruction totals are weak proxies for these conditions.

The patch also removes unnecessary generic outline construction and reuses native scalers within a run segment. Those changes can benefit a font even when retaining outlines contributes little. The retention ablation below separates the retention implementation from those remaining changes; it does not isolate the remaining changes from each other. This is supporting mechanism evidence for the CJK study, not a general performance guarantee or a replacement for the recorded master-versus-patch application benchmarks.

## Glyph work and existing Swash caches

Swash already retains prepared hinting instances in an eight-entry LRU per outline format, keyed by font, size and variation coordinates. Master therefore does not normally rerun the whole `fpgm`/`prep` program for every glyph. It does construct a scaler for each bitmap-atlas miss and repeats glyph decoding, scaling, applicable glyph hint execution, temporary-memory work and path conversion. Final can retain that resulting geometry and rasterize it at another phase; native rasterization and bitmap upload remain. It also constructs the scaler lazily and shares it within the current run segment. Blank-image fallback ends that segment.

The private Skrifa diagnostic counts completed VM dispatches separately from cold builder preparation. The values below use the native screen's **DPR1 initial-size controls**, not an application-request-weighted estimate: each value is the median across five outline sizes of its case mean over unique glyphs. Called `fpgm` dispatches are a subset of total glyph dispatches, not an additional cost to add. All native/count-instrumented geometry hashes and 560 ten-phase alpha-image cases agreed, and no VM errors occurred.

| Native profile | Font | Glyph VM dispatches | Called `fpgm` dispatches | CALLs | LOOPCALLs |
| --- | --- | ---: | ---: | ---: | ---: |
| English unique demo glyphs | Rye | 2,848.40 | 2,836.90 | 43.18 | 24.96 |
| English unique demo glyphs | Vollkorn | 2,033.94 | 2,026.74 | 41.75 | 24.00 |
| English unique demo glyphs | Nanum Myeongjo Regular | 158.03 | 82.55 | 2.58 | 0 |
| Korean unique demo glyphs | Nanum Myeongjo Regular | 238.13 | 171.92 | 4.50 | 0 |
| English/Chinese unique demo glyphs | BabelStone Han and Noto SC | 0 | 0 | 0 | 0 |

The Korean fonts contain programs for a large repertoire, but the selected glyphs execute hundreds of dispatches rather than Rye/Vollkorn's thousands. BabelStone and Noto have no glyph VM execution in these cases, although they still decode, scale and rasterize geometry. Their small prep programs select the interpreter path; they do not demonstrate expensive glyph hinting. A dispatch is not a constant-cost CPU operation: internal point loops, skipped bytecode scanning, decoding, composite traversal, memory initialization/copies and rasterization are outside this count.

The independently audited warm native decomposition supplies corresponding timings. These are medians of five exact-size medians at **11, 12, 14, 15 and 16px**, with six balanced trials per size; builder-only is per scaler build/drop, other values are per glyph iteration.

| Native unique-glyph workload, default coordinates | Builder | Rebuild + outline | Prepared hinted outline | Prepared unhinted outline | Native render | Geometry reuse |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| English / Rye | 0.118 | 18.868 | 18.624 | 0.469 | 20.847 | 1.647 |
| English / Vollkorn | 0.140 | 14.654 | 14.474 | 0.248 | 15.425 | 0.702 |
| English / Myeongjo Regular | 0.130 | 1.802 | 1.661 | 0.263 | 2.385 | 0.659 |
| Korean / Myeongjo Regular | 0.129 | 2.560 | 2.351 | 0.404 | 3.676 | 1.255 |
| Chinese / BabelStone Han | 0.132 | 0.637 | 0.532 | 0.501 | 2.262 | 1.878 |
| Chinese / Noto Sans SC | 0.134 | 0.499 | 0.353 | 0.354 | 1.360 | 1.036 |
| Chinese / Noto Serif SC | 0.134 | 0.600 | 0.435 | 0.425 | 1.860 | 1.497 |

All values are **µs**. Warm scaler construction is small and similar across these candidates; it does not explain a multi-millisecond cold application difference by itself. Rye and Vollkorn instead have a large hinted-versus-unhinted cost, consistent with the dynamic VM evidence. Noto default instances have closely matched hinted and unhinted outline costs. The weighted supplement increases Noto outline/render costs modestly without creating expensive glyph VM execution. The 18 warm-cost timing processes and 12,960 rows passed independent source/build/font/order/arithmetic and image/geometry checks. These kernels exclude cold context construction and preparation, and do not simulate real cache admission, arena clearing, coordinate-key allocation or atlas traversal. Subtracting independently measured kernel medians is an estimate, not a strict decomposition into additive stages.

## Actual demo reuse and overhead

An untimed observational replay used unchanged source workload, all five demo phases and all 119 warmup frames. Every master native-render request sequence exactly matched final's outline-request sequence, including glyph, font role, exact size bits, coordinates and horizontal phase. All 120 reported atlas-count rows matched the original measured applications. Independent checks reconstructed the inserted logging edits back to the original source bytes, matched six dependency/feature graphs, and recounted 24 processes.

| First paint, regular font | Master native calls | Final nonempty geometry hits | Empty geometry hits | Final misses | Final scaler builds |
| --- | ---: | ---: | ---: | ---: | ---: |
| English / Rye | 268 | 137 | 19 | 112 | 39 |
| English / Vollkorn | 263 | 133 | 18 | 112 | 37 |
| English / Myeongjo Regular | 269 | 141 | 16 | 112 | 37 |
| Korean / Myeongjo Regular | 198 | 31 | 16 | 151 | 47 |
| Chinese / BabelStone Han | 139 | 0 | 0 | 139 | 29 |
| Chinese / Noto Sans or Serif SC | 148 | 8 | 1 | 139 | 30 |

Empty geometry, including spaces, does not represent avoided expensive visible-glyph hinting. None of these first paints clears the arena. During zoom, Korean Myeongjo clears twice in zoom-in and once in zoom-out; Chinese BabelStone clears once and twice; Chinese Noto Sans/Serif clear once in each phase. Larger outlines consume the budget sooner, but these event counts do not establish that an uncertain timing loss was caused by eviction.

All reported warm and pan phases have **zero native render, outline-request and scaler-build events** in every traced font/locale. Differences there arise outside outline hit/miss work: possible sources include PNG classification, routing and run handling, general draw cost, code generation and measurement variation. They are not evidence of arena allocation on a cache hit.

The old bitmap atlas already includes horizontal phase in its key. Full-em Han advances at the initial integer outline sizes are integral: direct default-instance `hmtx` inspection finds one-em advances for all 102 mapped ordinary Han characters in the fixed BabelStone/Noto corpus. The inspected Myeongjo Hangul characters instead have fixed 973/1024-em advances. This is consistent with repeated Han already sharing a bitmap phase while proportional Latin characters request several phases of the same outline. It is an explanation supported by requests and metrics, not a proof of variation-metric behavior at every weight or a universal rule about scripts. The fixed Korean/Chinese text also introduces more distinct glyphs than the English scene.

Master additionally calls `Font::glyph` before native atlas lookup to classify PNG content. A vacant glyph/variation key causes generic unhinted outline construction through `ttf_parser` with the benchmark's default textlayout feature; native Swash then computes its own geometry. Successful generic paths are cached, while empty/missing results can be retried. Final classifies the same largest-strike PNG metadata without constructing that path. This benefit is independent of retaining Swash outlines. The source paths and line references are recorded in [the source audit](analysis/cjk-font-search/mechanism-source-audit.txt).

## Retention ablation

The no-retention library is the final frozen source with precisely one `self.insert_scaled_outline(key)` call removed. Its initially empty map therefore never gains an outline. Classification, routing, run-scaler reuse, key/lookup code, native outline scratch, budget enforcement and bitmap rendering remain in the source. This compares the complete retention implementation, including eager admission/copying/storage and lazy-scaler effects, against the otherwise corresponding final path. Optimized code generation and residual scheduling variation also remain possible influences.

The frozen diagnostic ran eight predetermined font/locale cases, six balanced three-version orders, five trials per process and requested DPR2: **144 processes and 3,600 raw rows**. No raw attempts were excluded or retried. Each process result is the median of five trial phase means. The table reports mean paired differences across six blocks, in µs/frame. **Final − no-retention** is negative when retention helps; **master − no-retention** is positive when the remaining final changes help. Each cell shows those two differences in that order. This exploratory ablation has no confidence intervals or significance claims; exact per-block values and ranges remain in the JSON.

| Workload / font | First paint | Warm | Zoom in | Zoom out | Pan |
| --- | ---: | ---: | ---: | ---: | ---: |
| English / Rye | −2,591.64 / +56.95 | −2.83 / −3.41 | −2,522.80 / +111.76 | −1,662.20 / +46.24 | −2.02 / −1.79 |
| English / Vollkorn | −2,218.53 / +20.80 | −1.46 / −2.59 | −2,048.37 / +37.07 | −1,407.56 / +48.10 | −0.77 / +1.03 |
| English / Myeongjo Regular | −244.28 / +29.19 | +2.53 / −2.86 | −213.49 / +20.22 | −155.96 / +8.40 | −0.80 / −0.90 |
| Korean / Myeongjo Regular | −43.14 / +25.56 | +1.08 / +1.54 | −49.69 / +25.22 | −42.62 / +11.92 | −0.92 / −1.96 |
| English / Noto Serif SC | −14.41 / +64.67 | −1.98 / −0.84 | −141.77 / +19.72 | −24.11 / +9.99 | −1.64 / +0.25 |
| Chinese / Noto Serif SC | −42.40 / +116.90 | −2.51 / −3.53 | −35.71 / +39.96 | −6.47 / +17.13 | −2.84 / −1.27 |
| English / BabelStone Han | +29.16 / +18.45 | −0.89 / −0.13 | −17.96 / +32.24 | −12.98 / +17.51 | −1.82 / −1.34 |
| Chinese / BabelStone Han | +39.12 / +40.69 | +1.91 / −0.29 | +35.49 / +25.34 | +3.57 / +26.86 | +1.41 / −1.03 |

For the reported 65-frame sequence, phase means are weighted and summed **within each trial before taking its process median**, then paired across blocks. Warmup is excluded from that endpoint. Sequence differences are therefore not necessarily the sum of the separately reported phase-median differences.

| Workload / font | Final − no-retention, µs/65 frames | Master − no-retention, µs/65 frames |
| --- | ---: | ---: |
| English / Rye | −52,971.92 | +1,696.51 |
| English / Vollkorn | −43,902.43 | +1,021.07 |
| English / Myeongjo Regular | −4,657.88 | +89.77 |
| Korean / Myeongjo Regular | −1,142.66 | +481.53 |
| English / Noto Serif SC | −2,084.88 | +327.72 |
| Chinese / Noto Serif SC | −662.35 | +427.80 |
| English / BabelStone Han | −518.55 | +584.39 |
| Chinese / BabelStone Han | +344.85 | +587.79 |

Rye and Vollkorn's large improvement is predominantly retention: their first-paint retention savings are positive in all six blocks, with ranges 2,534.79–2,630.12µs and 2,109.50–2,389.21µs respectively. Myeongjo's English retention savings range 223.67–259.58µs, compared with 3.87–77.54µs in Korean. The same font can therefore supply different cache opportunities in different text.

Noto Serif's Chinese first paint preserves a mean 116.90µs improvement without retention; the additional mean retention effect is 42.40µs and changes sign across blocks (−22.38 to +96.29µs saving). In English its mean retention effect is 14.41µs, also with mixed block signs (−74.00 to +91.08µs). Those estimates do not support attributing its full original patch benefit to eight cheap cached outlines or to a large hint program. They support remaining changes as a substantial part of its cold benefit, with classification and scaler/run changes still bundled.

BabelStone's Chinese first paint has no geometry hits. Retention is slower than no-retention in all six diagnostic blocks, by 13.92–63.17µs, with a mean 39.12µs cost. The remaining changes save a mean 40.69µs, leaving a mean master-versus-final difference of only 1.57µs in this ablation. This is direct evidence of a retention downside in a low-reuse, inexpensive-outline cold workload. The English and Chinese sequence estimates are less consistent than these cold comparisons. The six-block diagnostic must not be promoted to a new confidence-rated confirmation or generalized application percentage.

The independent audit checked all 144 exact invocations, 3,600 original atlas-count matches, nine dependency/feature graphs, every source edit and all 48 three-arm phase/sequence effects using independent decimal arithmetic. The original master-versus-final confirmation campaigns remain separate evidence with their own paired-block confidence intervals.

## Scope, image evidence and preserved inputs

Requested application DPR2 does **not** double this demo's initial Swash outline sizes. Production shapes using DPR, then converts positions back; the atlas outline size comes from Paint and the quantized canvas transform. Actual traced initial sizes are 11–16px, and zoom sizes extend roughly 9.625–50px. Native DPR1 controls match those initial sizes; native DPR2 is a larger-outline-size control. A screen-average µs/glyph value is not multiplied by application hit counts as an exact prediction.

The application also uses weight overrides for several Noto labels. Native default coordinates omit those weights. The separate weighted warm-cost supplement covers weights 300 and 400; public Swash normalization gives Noto Serif weight300 `[1556]`, while production uses `[1555]`. That one case is a nearby instance differing by one 2.14 fixed-point step, not an exact request replay. The other supplemental vectors match the production trace. Default Noto Sans/Serif weights are 100/200, so “Regular” versus default cannot be assumed.

Existing application pixel evidence applies to the earlier Rye/Vollkorn controls and separately localized Korean/Chinese campaigns. The new exploratory English CJK-font cohort has no application pixel-proof campaign. The retention ablation has **no new no-retention application pixel proof**. Native kernel alpha/geometry agreement, exact source preservation, request-sequence agreement and atlas-count agreement are useful separate checks; they are not substitutes for such a pixel proof.

Production FemtoVG, the Swash checkout and Cargo registry sources were not edited for this mechanism work. Instrumentation and the no-retention deletion live in isolated copies with unique package/executable identities. Warm-cost interpretation corrections are retained as `analysis-v2`; timed inputs and raw outputs are unchanged. The failed first counter build, which used an unresolved copied relative common-module path, remains preserved; the fresh v2 corrects only that path and package identities before any count rendering. The localized collector's earlier string/Path pre-render failure and its one-line normalization proof also remain recorded separately.

The main audit and result artifacts are:

- [VM dispatch report](analysis/cjk-font-search/vm-dynamic-instructions.md) and [raw-derived VM summary](analysis/cjk-font-search/vm-count-summary.json).
- [Warm-cost corrected report](analysis/cjk-font-search/cost-summary.md) and [independent warm-cost audit](analysis/cjk-font-search/independent-cost-audit.json).
- [Production phase counts](analysis/cjk-font-search/production-counts-summary.csv), [independent counter audit](analysis/cjk-font-search/production-independent-count-audit.json) and [empty-outline/advance-width annotations](analysis/cjk-font-search/production-geometry-and-advances.json).
- [Frozen retention protocol](analysis/cjk-font-search/retention-protocol-frozen.json), [all ablation results](analysis/cjk-font-search/retention-analysis.json), [summary CSV](analysis/cjk-font-search/retention-summary.csv) and [independent ablation audit](analysis/cjk-font-search/independent-retention-audit.json).

Further font selection should target expensive **executed** outline work together with repeated geometry requests in the unchanged demo. It should retain ordinary low-cost controls and the complete master-versus-final workload evidence, rather than infer value from repertoire size or total stored hint bytes alone.


## Preserved evidence and limitations

All attempts remain. An untimed Cargo collision between identical screening
package names was caught before measurement and corrected with distinct package
identities; the original English binary remained unchanged. An initial localized
pixel preflight then failed in Python before rendering/timing due to a string/Path
argument. The original plan/collector and failed attempt remain. The successful
V2 collectors contain only an independently verified Path normalization line;
Rust workloads, executables and source/build proofs did not change.

Both localized analyzers emitted three NumPy matmul RuntimeWarnings. Logs are
retained. The independent direct-indexed checker matched all means, ratios and
intervals within 1e-6 and verified finite checked values. No trials were removed,
no losing fonts dropped, and no new measurement was labeled a rerun of old data.
Balanced launch order limits drift; it does not prove absence of background load.

Scripts, inputs, raw records, rejected attempts, stdout/stderr, source/build
bindings and reports are archived in `results/cjk-font-search`. Compiled outputs
and caches are omitted explicitly. Offline verification checks every archive
member before five independent native/English/localized/cost audits; absent binary
bytes remain bound to build hashes and are not rechecked as live executables.
See [reproduction instructions](docs/cjk-font-reproduction.md).
