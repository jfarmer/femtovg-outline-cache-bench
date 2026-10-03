# CJK font search summary

Rye remains the most convincing expensive font from this search. Thirteen new
CJK font files, including Nanum, D2Coding, Droid, WenQuanYi, Noto SC and BabelStone
Han, produced no larger measured per-glyph or demo savings. A larger font-wide
hinting program total does not establish more work per glyph.

On the unchanged English demo at DPR2, Rye saved 2.507 ms on first paint,
Vollkorn 2.177 ms and the best CJK-family Latin result, Nanum Myeongjo Regular,
0.304 ms. These are two-block exploratory comparisons; the existing Rye
12-block confirmation remains retained separately.

The independently checked localized first-paint confirmations were:

| Locale | Font | Master ms | Patch ms | Saved µs [95% CI] |
| --- | --- | --- | --- | --- |
| ko | NanumGothic-ExtraBold | 2.093 | 2.013 | +79.750 [+52.239, +105.132] |
| ko | NanumMyeongjo-ExtraBold | 2.074 | 1.977 | +96.913 [+69.514, +130.248] |
| ko | NanumMyeongjo-Regular | 2.059 | 2.003 | +55.358 [+19.246, +88.706] |
| zh | BabelStoneHan | 1.896 | 1.896 | +0.719 [-18.184, +16.407] |
| zh | NotoSansSC-VF | 2.899 | 2.740 | +159.371 [+101.753, +210.081] |
| zh | NotoSerifSC-VF | 6.864 | 6.636 | +227.879 [+168.823, +287.605] |

The patch is not a universal performance improvement. Warm and some other
phases cost more; all phase/sequence effects and intervals remain visible in
the [full report](CJK-FONT-SEARCH.md). Both localized pixel preflights passed,
and independent analysis checked every retained effect/interval.

The mechanism investigation separates dynamic glyph hint execution, repeated
scaler construction, rasterization, and actual atlas/outline reuse. Count-only
instrumentation does not supply performance numbers. The full report states
what was observed, what was inferred, and what remains unexplained.
