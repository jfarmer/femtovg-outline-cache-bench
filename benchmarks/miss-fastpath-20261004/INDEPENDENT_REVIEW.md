# Independent miss-fast-path review

PASS: the six clean permutation blocks contain 126 processes, 486 records and
27 complete groups. All 81 reported paired point estimates, median deltas and
5,000-resample bootstrap intervals were independently reproduced from raw
values without importing the runner or analyzer. Six accepted attempts and idle
guard statuses were also checked; there are no excluded attempts.

The check is reproducible with
`python3 bench/independent-numeric-audit.py` from the study root. Computed values,
input hashes, seeds and tolerances are in `INDEPENDENT_NUMERIC_AUDIT.json`.
The prepared audit separately verifies source/binary identities.

## Interpretation

| All-miss sequence | Master | Before (907bb37) | Fast path | Paired fast path / before (95% exploratory CI) |
|---|---:|---:|---:|---:|
| Roboto, 32 frames / 3,008 requests | 5.895 ms | 5.984 ms | 5.962 ms | −1.478% [−2.794%, +0.927%] |
| Vollkorn, 32 frames / 3,008 requests | 47.703 ms | 47.883 ms | 47.695 ms | −0.905% [−1.261%, +0.797%] |

Paired absolute changes versus 907bb37 are −88.83 µs and −433.29 µs per
sequence. Against master, Roboto is +1.212% [−1.589%, +1.769%] and Vollkorn is
−0.353% [−0.760%, +0.798%]. These directions favor the fast path, but do not
demonstrate an all-miss speedup or prove that the miss penalty disappeared.
The earlier run's roughly 3% Roboto result is separate evidence: comparing it
with this run's 1.2% estimate is not a causal measurement of this edit.

Large native benefits remain. First-paint marginal medians are Rye
7.013→4.242 ms, Vollkorn 7.201→5.097 ms and Fleur de Leah
94.841→21.430 ms (master→fast path). Fleur's 44-frame sequence is
1,257.525→301.262 ms. Its new-size and full-sequence paired intervals versus
907bb37 favor the fast path. Its first-paint point is slower by 369 µs paired
(+1.514%, CI [−0.133%, +4.173%]), leaving a possible small cost.

No after/before interval is wholly positive in these data. Six exploratory
blocks do not prove zero cost, and the intervals have no multiplicity
correction. All no-Swash control intervals cross zero. Before/after frozen
source maps differ only in `src/text/swash_rasterizer.rs`; `text.rs` declares
that module under `#[cfg(feature = "swash")]`, so this edit is excluded when
Swash is disabled. CPU/Void results do not measure GPU/backend performance.

The table uses marginal medians for absolute times and medians of paired ratios
for percentages. Those statistics need not agree algebraically: Roboto's
after/before ratio of marginal medians is −0.364%, while its median paired
change is −1.478%. Neither is an arithmetic error. Paired deltas likewise
differ from subtracting marginal medians.

The code review found no necessary issue: admission checks current capacities,
existing plus new metadata and scratch high-water; the rare growth/eviction
body and owned-key insertion tail remain unchanged. Scoped borrowing releases
the scaler/context before accounting and removes the per-miss `Rc` clone.
Keeping the edit is reasonable without a universal performance claim.
