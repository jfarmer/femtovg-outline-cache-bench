# Aggressive open-source fonts for the outline cache

Fleur de Leah is the strongest hinting stress font found in this search: on the fixed 94-character ASCII corpus, constructing a hinted outline costs **31.84 µs/glyph**, versus **18.79 for Rye** and **13.51 for Vollkorn Medium** measured alongside it. In the unchanged demo, **Diplomata SC** gives the largest confirmed first-paint saving: **2.759 ms**, versus **2.677 ms for fresh Rye**. Its additional saving is **81.79 µs [29.42, 142.95]**. These are separate findings. We found a heavier per-glyph font and a modestly stronger demo example, rather than a font that dramatically increases the demo's cache benefit.

## Fresh master-versus-patch demo confirmation

| Font | Master first paint | Patch first paint | Saved time, 95% interval |
|---|---:|---:|---:|
| Diplomata SC | 6.741 ms | 3.982 ms | 2.759 ms [2.710, 2.808] |
| Rye | 6.422 ms | 3.744 ms | 2.677 ms [2.617, 2.736] |
| Water Brush | 7.516 ms | 4.866 ms | 2.650 ms [2.561, 2.745] |
| Fleur de Leah | 6.703 ms | 4.431 ms | 2.272 ms [2.209, 2.332] |
| Vollkorn Medium | 6.759 ms | 4.488 ms | 2.271 ms [2.173, 2.386] |

Only these fresh confirmation data enter the table. The reference is frozen upstream master `f57a2c39e9836c146556c58c98d80c5bf7899029`; the patch is the exact updated cache and correctness-fix snapshot bound by the source/build records. It retains the Swash-only arena implementation, including the corrected arena-growth order. This font investigation changes no production FemtoVG or Swash source. The final renderer, original master and independent native actual-offset renderer agreed byte for byte in all five captured demo phases for all five fonts: 15 processes and 75 RGBA captures.

We selected fonts from separately completed exploration, froze their files and rationale, and then ran 12 balanced master/final blocks with five trials per process: 120 CPU processes and 3,000 original rows. Configuration order rotates by block; each font has six AB and six BA orders. The drawing is the existing English demo, with only its regular font replaced; icon, emoji, fallback fonts and all assets remain fixed. Requested DPR is 2, while its actual initial atlas outline sizes are 11, 12, 14, 15 and 16 px. The CPU timing replay opens no window.

The estimator is the mean of paired block differences between process medians. Intervals use 10,000 whole-block bootstrap resamples with shared indices across fonts. The same-block comparison against fresh Rye supports Diplomata SC's modest advantage. Water Brush's additional saving is −27.36 µs [−114.19, +79.11], so its difference from Rye remains uncertain. Fleur saves 405.44 µs less than Rye [348.56, 462.32]. These selected-font intervals describe this one machine and workload; they are conditional on selection and do not correct all endpoints as one hypothesis family. No exploratory timing is pooled into confirmation.

## Repeated drawing and costs

| Font | Saved across 65 reported frames, 95% interval | Warm saved µs/frame | Pan saved µs/frame |
|---|---:|---:|---:|
| Diplomata SC | 57.300 ms [55.575, 59.664] | -1.64 | +0.76 |
| Rye | 53.855 ms [52.769, 55.022] | +0.03 | -0.23 |
| Water Brush | 50.339 ms [48.993, 51.827] | -0.05 | +1.12 |
| Fleur de Leah | 42.830 ms [38.325, 45.503] | +0.21 | -2.37 |
| Vollkorn Medium | 46.087 ms [44.351, 48.492] | -1.10 | -0.40 |

Positive values save host drawing time. Each sequence total is constructed within a trial before taking the process median: one first paint, 30 warm, 12 zoom-in, 12 zoom-out and 10 pan frames. The 119 unreported warmup frames are excluded. Every warm and pan interval includes zero; small mean differences in the table are not established improvements or regressions. Zoom results and all three cumulative timing endpoints remain in the full tables. Sequence totals are neither application launch times nor FPS estimates. The primary confirmation measures host CPU drawing; its GPU processes verify pixels rather than establish GPU performance.

## The more expensive hinting case

| Font, same native cohort | Hinted outline | Unhinted outline | Render minus geometry reuse |
|---|---:|---:|---:|
| Fleur de Leah | 31.84 µs/glyph | 0.69 µs/glyph | 31.96 µs/glyph |
| Rye | 18.79 µs/glyph | 0.48 µs/glyph | 19.18 µs/glyph |
| Vollkorn Medium | 13.51 µs/glyph | 0.28 µs/glyph | 13.57 µs/glyph |

These native results use the same unchanged screen executable, four trials and three repeats, with a fixed ASCII94 glyph set at five sizes from 11 to 16 px. Each row is the median of five per-size trial medians. Prepared scaler creation, font preparation and cached geometry creation are excluded; this is a kernel cost, not a net application cache result. Retained hinted outlines match fresh hinted outlines exactly, and native rendering matches geometry-reuse alpha masks at ten subpixel phases per case before timing; unhinted construction is measured as a separate control. The native DPR1 profile matches the demo's initial outline sizes; native DPR2 explicitly uses doubled sizes as a separate control. No native confidence interval is claimed from this exploration.

A separately instrumented private interpreter confirms actual execution, with zero VM errors and exact native/count geometry and image agreement. For fixed ASCII94 at these sizes, Fleur executes about **3,985 dispatches/glyph**, Rye **2,604** and Vollkorn **1,648**; the count is an instruction dispatch count, not a CPU-cycle estimate. In the size-specific unique demo glyphs, these medians narrow to about **2,942, 2,848 and 2,034**. That unique glyph set also changes between sizes, so it must not be interpreted as a pure PPEM experiment. Font table bytes and total repertoire do not predict which programs are executed for the characters an application actually reuses.

Fleur's unhinted outline costs under 1 µs/glyph, so its much higher hinted cost is chiefly hint evaluation rather than outline decoding alone. Native ASCII94 cost makes it a useful stress font for the existing controlled glyph workloads. Its lower unchanged-demo benefit prevents us from advertising it as a stronger demo win.

## Why a larger font cost does not ensure larger savings

The separately captured production traces preserve the exact request stream between uncached master and the final cache. First-paint outline requests/hits/misses/scaler builds are: Rye 268/156/112/39, Water Brush 272/160/112/37, Fleur 264/152/112/36, Diplomata SC 263/151/112/40, and Vollkorn 263/151/112/37. Initial caches do not clear. These counts are for the replaced regular font; the traces also record the fixed fonts separately. Actual benefit weights the particular repeated glyphs and sizes, rather than the uniform native unique-glyph average.

Joining the actual first-paint graphic cache hits to the sealed per-glyph interpreter records gives a more direct explanation:

| Regular font | Mapped graphic cache hits | Glyph instruction dispatches avoided on those hits |
|---|---:|---:|
| Rye | 137 | 365,278 |
| Diplomata SC | 134 | 351,692 |
| Water Brush | 141 | 316,957 |
| Vollkorn Medium | 132 | 273,091 |
| Fleur de Leah | 134 | 271,951 |

All mapped production misses have matching point/verb counts against the sealed native records, and 588 duplicate ASCII/demo glyph records agree exactly. This is a partial coverage count: empty spaces and the unsupported non-ASCII join entries are explicitly excluded, rather than assigned zero work. It counts glyph VM dispatches, not preparation, rasterization, total CPU work or time. Fleur's actual reused graphic glyphs avoid less executed work than Rye's, despite Fleur's much higher fixed-ASCII mean. The weighted glyph mix explains why the unique-glyph proxy does not predict the demo ranking; it does not claim that instruction count alone predicts exact CPU savings.

Water Brush retains 39,848 points on first paint, versus Rye's 15,000, Fleur's 17,961, Diplomata SC's 8,228 and Vollkorn's 8,658. During the reported zoom sequence Water Brush clears six times, Rye and Fleur twice, and Diplomata SC and Vollkorn once. More retained geometry and more clearing provide evidence of additional memory work; these traces do not independently time its causal contribution. Every measured warm and pan phase has zero native outline requests, cache lookups, misses and scaler builds. Small warm timing differences therefore cannot be assigned to per-glyph arena lookup work.

This extends the earlier CJK finding: even a large font's repertoire and hint tables can accompany cheap glyph execution or few useful outline hits. Admission based only on total hint bytes, outline points or the presence of TrueType instructions would not reproduce the observed ranking. The [mechanism report](analysis/aggressive-font-search/supporting/selected-mechanism-report.md) preserves full counts and their scope.

## Search scope and retained evidence

We evaluated **47 candidates** in three independently frozen cohorts: 29 decorative/geometry fonts, ten hinted or calligraphic fonts, and eight modern script/brush fonts, each with fresh Rye and Vollkorn controls. All are unchanged shipped open-source files from Google Fonts commit `9710da1eacb3be272583c3224dcb70f9da6eadbb`; official font, license, metadata and description bytes and their Git blob identities are retained. No rehinting, subsetting or artificial program inflation was used. Fleur de Leah and the other new fonts carry their shipped SIL Open Font License files. Primary sources: [Fleur de Leah](https://github.com/google/fonts/tree/main/ofl/fleurdeleah), [Diplomata SC](https://github.com/google/fonts/tree/main/ofl/diplomatasc), [Water Brush](https://github.com/google/fonts/tree/main/ofl/waterbrush).

The native collection keeps 53 processes: 52 successes, 16,640 raw rows, and one retained Herr von Muellerhoff rejection because its native ASCII94 test requires an unused caret. Herr covers the actual demo text and was included in that separate replay. The three demo screens keep 212 processes and 3,180 rows, with all 954 phase/sequence endpoints independently checked using exact rational arithmetic. They use two paired blocks and three trials for selection only. The original historical font and CJK benchmarks, including losing cases, remain preserved.

Rubik Pixels demonstrates the limit of geometry alone: expensive unhinted outlines do not guarantee a larger demo win. Fleur is the strongest newly found hinting stress case, Diplomata SC is the best confirmed selected demo first-paint result, and Water Brush is a useful mixture of hinting and larger geometry without established savings beyond Rye. This search supplies no universal font threshold and no unqualified performance claim.

## Results and reproduction

The [primary table](analysis/aggressive-font-search/confirmation/primary-table.md), [all phase results](analysis/aggressive-font-search/confirmation/summary.csv), [independent confirmation audit](analysis/aggressive-font-search/confirmation/independent-audit.json), and per-cohort exploratory/static/native tables are published beside the retained archive. The independent confirmation audit recomputed 90 endpoints and 184 intervals directly from original process stdout and regenerated bootstrap indices, with no disagreement. Full live font, source, binary, dependency-graph and RGBA identity checks passed. The archive retains original failures, corrected source adapters, all raw trials, counted VM traces, pixels, manifests, and source/build proofs; compiled artifacts are explicitly omitted for portable offline verification.

See [reproduction instructions](docs/aggressive-font-reproduction.md). Run `python3 -B scripts/verify-results.py --campaign aggressive-font-search --output FRESH_DIRECTORY` to verify every retained member and independently recompute the declared raw-result audits without building Rust or opening a window. A successful source/order/raw audit does not establish the absence of background load or thermal drift during collection; fresh same-block controls and retained variability constrain that inference.
