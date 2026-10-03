# Independent final-study audit

Status: partial_passed; audited cohorts: ['warm-genericrestore', 'generic-genericrestore'].

Independent stdout parsing, full 12-block matrix/order and identity checks, all accepted raw processes used; paired-block median bootstrap with 10000 draws, seed 61432, percentile indices 250/9750. Summary tolerances rel=1e-11 abs=1e-8.

| Cohort | Raw process records used | Verified summary rows | Blocks |
|---|---:|---:|---:|
| warm-genericrestore | 288 | 24 | 12 |
| generic-genericrestore | 768 | 64 | 12 |

Expected glyph counts: {'labels': 340, 'para': 1836}.
Interrupted raw cohorts retained separately: [('cold-genericrestore', 1758), ('cold-genericrestore-clean', 564), ('cold-genericrestore-final', 1176), ('cold-genericrestore-quiet', 972)].

Process stdout contains its aggregate timing metrics, not every individually timed frame/sample. Scene sequence sums include all emitted measured phases (65 demo/88 text frames) and exclude 119 unreported priming frames. Intervals are exploratory, without multiplicity correction; one machine, CPU drawing/flush only.

Full independently recomputed ratios, absolute delta confidence intervals, complete controlled-sequence costs, scene phase-weighted sums computed before medians, all final rows, and worst-cost selections are in RESULT.json. No selected-cohort raw process records were omitted.
