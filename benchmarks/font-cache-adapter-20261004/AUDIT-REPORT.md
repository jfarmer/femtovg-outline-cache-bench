The narrow Font-adapter comparison passed independent stdout, matrix and source-identity checks.

All phase values and complete stress-sequence values agree with preserved stdout; accepted raw records and every reported median, paired delta, percentage and bootstrap interval were reconstructed without importing the benchmark runner/analyzer.

| Cohort | Processes | Raw rows | Summary rows | Excluded attempts |
|---|---:|---:|---:|---:|
| comparison | 108 | 396 | 22 | 0 |
| stress | 18 | 90 | 5 | 3 |

Six permutations balance each comparison 3 AB/3 BA and each version twice in each position. The same locked dependencies, profile, harness and assets are used; source, manifest, lock and binary hashes match BUILD.json and each cohort metadata. Master and Simple match the earlier frozen lower-touch source identities. Build logs identify the intended source paths. No fresh build was performed by this audit.

The documented LOC count reproduces: Adapter adds 334 production code lines over Master and 41 over Simple, leaving 105 fewer than the previous Full integration. This excludes tests/comments/blanks and includes braces/attributes and all feature branches; it measures physical lines, not semantic complexity.

| Case | Phase | Master ms | Simple ms | Adapter ms | Paired Adapter−Simple ms | Adapter/Simple % (exploratory 95% interval) |
|---|---|---:|---:|---:|---:|---|
| demo-RobotoFlex | first_paint | 1.965 | 1.922 | 1.839 | -0.096 | -5.07% [-12.12, +13.61] |
| demo-RobotoFlex-no-swash | first_paint | 4.305 | 4.236 | 4.263 | -0.101 | -2.43% [-7.38, +1.42] |
| demo-Rye | first_paint | 6.963 | 4.262 | 4.287 | +0.076 | +1.79% [-4.37, +3.23] |
| demo-Vollkorn | first_paint | 7.368 | 5.136 | 4.969 | -0.295 | -5.52% [-10.50, +2.76] |
| grid_unique_sizes-RobotoFlex | all_misses | 6.074 | 6.162 | 6.175 | -0.054 | -0.88% [-8.14, +3.34] |
| grid_unique_sizes-Vollkorn | all_misses | 48.260 | 49.083 | 50.111 | +0.422 | +0.86% [-0.70, +3.38] |
| stress-FleurDeLeah | complete_sequence | 1268.191 | 301.101 | 301.649 | +0.028 | +0.01% [-1.05, +1.61] |
| stress-FleurDeLeah | first_paint | 95.422 | 21.084 | 20.786 | -0.439 | -2.07% [-10.14, +1.84] |
| stress-FleurDeLeah | new_size | 96.885 | 22.894 | 23.025 | +0.043 | +0.19% [-0.85, +2.40] |

Six complete blocks; each pair 3 AB/3 BA. Absolute values are marginal medians; deltas and percentages are medians of within-block differences/ratios. 5,000 paired-block resamples; seed 20261004+alphabetical group index; percentile indices 125 and 4874. Exploratory intervals, no multiplicity correction.

CPU benchmark with Void, no GPU/window/application performance claim.
Demo uses draw_us; cold/stress use total_us including Void flush. Do not mix these metrics.
Only default+Swash and a default-without-Swash Roboto demo control are timed; Swash-only/direct/stroke correctness depends on separate functional checks.
The seven cold samples are collapsed to one per-process median; individual sample times are not retained.
Name-based 0.1-second polling cannot prove absence of all transient/background load.
Prior non-Swash synthetic paragraph losses remain relevant; this limited demo control does not erase them.

The source review found no cache-policy or rasterization changes from Simple: ownership moved behind Font and an opaque shared handle. Cache hits still allocate their existing variation-key storage when nonempty; the wrapper adds no handle clone per render. The measured effects belong to the complete integration, not an isolated wrapper instruction cost.
