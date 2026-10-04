# Independent feedback performance audit

PASS: accepted stdout, complete block matrices, guard windows, source/harness/assets/binary hashes and reported summaries agree.

- `comparison-final`: 6 accepted blocks, 108 processes, 396 records, 22 summary rows; 0 excluded attempts retained.
- `stress-final`: 6 accepted blocks, 18 processes, 90 records, 5 summary rows; 1 excluded attempts retained.
- `probe-final`: 6 accepted blocks, 12 processes, 48 records, 8 summary rows; 0 excluded attempts retained.

Each three-way pair is balanced 3 AB / 3 BA. Six permutations also balance positions. Absolute medians, median paired deltas/percentages and every 5,000-resample seed/percentile interval were reconstructed without importing the analyzer.

## Limits

- CPU/Void measurements do not measure backend/GPU render-target switch cost.
- Six balanced blocks; exploratory percentile intervals, no multiplicity correction.
- Probe is a combined review-fix comparison with counters; capacity observations are net per request.
- Cumulative allocator requested bytes are not retained memory or RSS.

Public API and per-glyph target-switch review: [API_REVIEW.md](API_REVIEW.md).

## Source and exclusions

Final source: `907bb375645613b3647efab4c0efe29b50ed5b18`; frozen 150-file tree `3ee2ca6404e212efc1cee6c92db38dfa6b366f9761889a3b8c62c5288bbba601`. Upstream is `9d574e0`; the before-fixes cache control is `af989d9`. Dependency locks match after normalizing the harness package name; feature wiring and release profiles match. Build metadata records rustc 1.96.0, opt-level 3, no LTO, 16 codegen units.

The interrupted stress block `block-02-00` retains five partial records and the Cargo-nextest PID evidence (12113/12114). Its entire block was excluded; the accepted replacement used the same logical order. No comparison/probe blocks were excluded. The old `comparison` directory contains 55 pre-start guard checks (53 matched, one failed, one idle), with no attempts or timing samples; it was not reused.

## Representative final results

Absolute values below are marginal medians in milliseconds. Percentages and intervals are medians of paired block differences in relative time; they need not equal the ratio of marginal medians. Demo measures drawing/layout at DPI 2; stress measures drawing plus Void flush at DPI 1. Font/canvas setup and GPU rendering are excluded.

| Workload | Master ms | Final ms | Paired change (95% exploratory CI) |
|---|---:|---:|---:|
| demo-RobotoFlex / first_paint | 1.711 | 1.712 | -0.24% [-1.43, +11.46] |
| demo-Vollkorn / first_paint | 7.170 | 4.983 | -31.35% [-33.34, -29.59] |
| demo-Rye / first_paint | 7.004 | 4.288 | -38.65% [-40.04, -37.23] |
| grid_unique_sizes-RobotoFlex / all_misses | 5.998 | 6.178 | +3.27% [+2.60, +7.03] |
| grid_unique_sizes-Vollkorn / all_misses | 48.637 | 49.034 | +0.48% [-0.27, +1.70] |
| stress-FleurDeLeah / first_paint | 94.627 | 21.572 | -77.14% [-77.58, -74.88] |
| stress-FleurDeLeah / complete_sequence | 1240.644 | 299.714 | -75.84% [-76.00, -75.55] |

The all-miss rows are complete 32-frame/3,008-request sequences. Roboto has a measured cost: paired +195.52 µs/sequence (+6.11 µs/frame); Vollkorn is +231.71 µs/sequence, with its relative interval crossing zero. All five no-Swash demo intervals cross zero; this does not prove equivalence or cover every generic stroke workload. Warm Roboto is also +3.676 µs/frame versus the before-fixes cache control (paired +1.653%, CI [+1.003%, +2.463%]); versus master, that warm interval crosses zero. No blanket zero-regression claim is supported.

## Mechanism counts

Across 4,096 warmed requests with two normalized coordinates, allocations fall from 8,192 to 4,096: one allocation removed per hit. Empty-coordinate requests remain at 4,096 allocations. Remaining allocations include the rendered image buffer, so this is not an allocation-free rasterizer.

Across 4,000 near-budget requests, observed point/verb capacity changes including trims fall from 552 to 38 (Roboto) and 636 to 50 (Vollkorn). Peak cached entries are 3,417→3,331 and 1,681→1,661, respectively; modeled high-water values remain at most 1 MiB. This combined growth/key comparison does not isolate how much retention difference comes from Cow key metadata versus arena spare capacity. Private native buffers and map spare capacity are outside the soft accounting budget.

Probe timings include allocation-counter overhead and are diagnostic. The counts support removal of hit-side coordinate allocation and amortized arena growth; they do not establish an application speedup from each fix in isolation.
