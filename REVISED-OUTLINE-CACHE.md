# Measure the revised Swash outline cache against master

The complete revised patch retains substantial gains on expensive outlines and
smaller gains on Roboto, including initial population. It is **not a universal
performance improvement**: several warm text phases are 4.6–8.0 µs slower, some
GPU and application comparisons remain uncertain, and the cache retains memory.
The latest changes fix premature eviction at the budget boundary, make scaler
identity correct by construction, and fix three rendering defects that also
exist on master.

These are new measurements of the exact working tree, freshly built against
the master fetched on October 2, 2026. They do not reuse the older benchmark
numbers or executables. The shared point/verb arena remains selected; the prior
[native Outline pool comparison](NATIVE-OUTLINE-POOL.md) and
[original cache study](REPORT.md) remain available and unchanged. This follow-up
does not repeat the no-arena ablation, and does not establish that an arena wins
on every workload.

## Suggested PR presentation

Lead with the work avoided and **absolute CPU time saved**, naming the font,
scene and machine. Application percentages depend on the amount of unrelated
rendering work. Absolute savings also depend on the workload; neither is a
portable prediction for another application. Keep percentages as secondary
context for the recognizable FemtoVG scenes, and retain confidence intervals
and full results in the linked analysis.

Suggested wording:

> This caches hinted Swash outline geometry across distinct bitmap-atlas
> demands, while continuing to use native Swash scaling and rasterization.
> The default cache has a 1 MiB soft accounting budget. On an M4 Max, compared
> with master, FemtoVG demo first-paint CPU saves about 69 µs with Roboto Flex,
> 2.20 ms with Vollkorn and 302 µs with PT Sans. In Alustin's first frame,
> renderer CPU savings on WGPU are about 0.56 ms, 5.36 ms and 1.03 ms respectively.
> Some warm text phases cost an additional 5–8 µs. These are drawing/renderer
> measurements, not end-to-end launch-time savings.

| Font | FemtoVG demo first paint, CPU saved | FemtoVG text first paint, CPU saved | Alustin first frame, WGPU CPU saved | Alustin first frame, OpenGL CPU saved |
| --- | ---: | ---: | ---: | ---: |
| Roboto Flex | 69 µs | 413 µs | 0.56 ms | 0.17 ms, uncertain |
| Vollkorn | 2.20 ms | 6.64 ms | 5.36 ms | 4.74 ms |
| PT Sans | 302 µs | 892 µs | 1.03 ms | 0.86 ms |

These are paired absolute savings from the new final/master cohort. First-paint
cost includes population. The controlled two-phase 94-glyph and unique-size/
variation workloads explain the reuse and miss behavior; the complete scene
totals and application measurements show whether those effects survive useful
work. State the warm redraw and memory tradeoffs alongside the gains. The
boundary repair saves about 8.37 ms over the previous arena in the complete
3440-key, ten-pass control; label that as a targeted stress test rather than an
application improvement. An optimization that skips repeated hinting is a
credible PR case without claiming that every application becomes a fixed
percentage faster.

## What is in the final patch

The cache remains Swash-only and internal to FemtoVG. It eagerly retains hinted
outline geometry, keyed by font identity, glyph, exact size and full normalized
variation coordinates. Points and verbs live in shared append-only vectors;
map entries contain ranges. Rasterization remains necessary for each new
fractional position. Existing atlas hits still bypass this work. Native Swash
scaling, hinting and rasterization facilities do the corresponding work; this
patch does not edit Swash or add a replacement font scaler.

The cache has a 1 MiB **soft accounting budget**, not a whole-heap limit. Its
own arena capacities, logical key/range metadata and native outline scratch
high-water lengths are charged. Hash-table spare capacity, allocator overhead,
private Swash buffers and other rendering allocations are outside that figure.
True overflow still clears the cache. Oversized outlines can render without
being retained.

The budget fix first attempts ordinary geometric arena growth. If that reserve
would exceed the budget, it tests minimum combined growth **before evicting the
existing entries**. It clears only when the current working set plus the new
entry cannot fit under the accounting policy. This is a bounded-vector reserve
decision, without a new replacement policy or a chunk allocator. Exact growth
near the boundary can make more reserve requests; the measurements below
include that cost rather than assuming allocation strategies are universally
beneficial.

The scaler fix introduces a run object with private, immutable font, size and
variation settings. Those same fields create both the cache key and the native
hinted scaler. The scaler is initialized lazily on the first outline miss and
shared within that compatible run segment. A caller cannot supply a scaler and
an independently specified cache identity. Cache hits avoid scaler construction.

The three additional fixes are:

- Use immutable text-context access while drawing a run, allowing the lazy PNG
  atlas constructor to borrow that context without a `RefCell` panic. Regression
  cases cover the first rotated PNG draw and the first large PNG draw.
- Preserve negative fractional-position bins with a signed one-byte atlas key.
  Previously, casting a negative phase to `u8` aliased it with integer phase zero.
  Tests check both draw orders, native coverage and the actual glyph position.
- Wrap both atlas loops in `Canvas::with_render_target`, restoring their entry
  target after successful rendering and returned errors. Tests inject failures
  after an earlier glyph switched to the atlas, then check subsequent drawing
  for screen, image and layer-store targets. The helper does not catch panics.

## Four freshly built versions

| Version | Source | Purpose |
| --- | --- | --- |
| master | `f57a2c39e9836c146556c58c98d80c5bf7899029` | Primary acceptance baseline |
| prior | `4c45270585f0fadca63d3eae61433adb8102bea2` | Previously selected arena implementation |
| updated45 | Exact frozen prior tree plus fixes 4 and 5 | Isolate budget/scaler changes |
| final | Exact frozen working tree plus fixes 1–5 | Patch to submit |

Final source SHA-256 values are
`ae79b1702bb44fcef401b47dda0b38458160a57876f74b10cbb445d4d97c8798`
for `src/lib.rs`,
`6ec9215f1ab17cad624fca578ef327af2bf842554d322a06887fc26b8204ca5f`
for `src/text.rs`, and
`fa2fc5852710952ee3122500e08bda3a1dd38d69a39cd0420604f51c9488ee92`
for `src/text/swash_rasterizer.rs`. The complete inventories and build origins
are retained in the [source/build audit](analysis/updated-cache-source-build-audit.json).
The source snapshots include uncommitted changes; a Git HEAD alone is not the
identity of either updated version.

All suites use 12 four-version Williams blocks, three balanced order cycles.
The machine is an Apple M4 Max with 128 GiB RAM and 16 logical CPUs, using
Rust/Cargo 1.96.0. Every version uses the same dependency graph within its suite
and Swash 0.2.10. The replay and application graphs are distinct (including
different Skrifa versions); effects are compared within each suite. This is
evidence from one machine, not a cross-platform guarantee.
The completed timing cohort contains 144 example CPU processes, 144 example GPU
processes, 288 Alustin launches and 48 boundary-control processes. CPU replays
and boundary processes have five internal trials; GPU processes have three.
No timing-based exclusions were made. All Alustin blocks succeeded on their
first attempt, so no query retry altered the schedule.

Effects are medians of within-block candidate/reference ratios, not ratios of
the displayed marginal medians. Complete sequences are summed within each
trial before process medians and block pairing. Brackets below are 95%
whole-block bootstrap intervals with 10,000 resamples. They are exploratory,
with no adjustment for multiple comparisons or implementation selection.
Negative percentages mean less elapsed time. The [complete tables](REVISED-OUTLINE-CACHE-TABLES.md)
and raw analyses retain all six version comparisons and the original controls.

## Final versus master: existing example scenes

The CPU replay measures host drawing work through the Void renderer with the
same black-box barriers in every version. The original demo, text and variation
scenes, motion/reflow/zoom phases, and unique-size/variation/pollution controls
are retained. The GPU replay draws offscreen through Metal and measures drawing,
submission and completion waiting together; it is not a GPU timestamp measure.

| Font | Demo first paint, CPU | Text first paint, CPU | Demo reported sequence, CPU | Text reported sequence, CPU |
| --- | ---: | ---: | ---: | ---: |
| Roboto Flex | −4.69% [−7.04, −3.84] | −5.38% [−6.55, −4.38] | −2.30% [−4.06, −1.89] | −2.51% [−3.06, −1.69] |
| Vollkorn | −32.61% [−33.61, −31.83] | −24.10% [−24.95, −23.57] | −32.68% [−33.05, −32.45] | −27.33% [−27.51, −27.20] |
| PT Sans | −14.89% [−15.63, −13.13] | −9.58% [−9.78, −8.90] | −13.47% [−14.26, −13.29] | −7.00% [−7.31, −6.76] |

The demo and text sequence totals cover 65 and 88 reported frames respectively;
they exclude 119 unreported warmup frames. They are not an entire application
session. Paired CPU savings over those reported sequences are about 0.87/2.38 ms
for Roboto, 44.93/53.33 ms for Vollkorn and 6.45/7.06 ms for PT Sans.

Roboto's complete 32-size, 32-weight and pollution/return controls improve
5.72%, 30.53% and 4.61% respectively, with intervals below zero. Vollkorn's
32-size result is uncertain (−0.97%, interval [−1.61, +0.19]); the arena does
not make all churn patterns materially faster. Font-variation controls always
use Roboto and repeat under the other font factors, so those repetitions must
not be presented as independent Vollkorn or PT Sans variation evidence.

GPU reported-sequence changes for demo/text are:

| Font | Demo, draw/submit/wait | Text, draw/submit/wait |
| --- | ---: | ---: |
| Roboto Flex | −0.17% [−5.31, +2.35], uncertain | −1.26% [−8.60, −0.63] |
| Vollkorn | −19.07% [−21.85, −16.04] | −17.01% [−18.97, −15.52] |
| PT Sans | −5.77% [−10.43, −2.51] | −4.29% [−10.49, +4.84], uncertain |

The full phase results show small real tradeoffs. Warm text CPU increases
2.88%/7.16 µs with Vollkorn and 3.15%/7.76 µs with PT Sans; both intervals are
above zero. Several text return/movement phases cost 4.6–8.0 µs more, including
Roboto's x-return at +2.44%/+6.40 µs. These measurements identify costs, without
establishing a particular source-level cause. No final/master complete sequence
in this study has an interval wholly above zero, but that observation is not
proof that every future workload benefits.

## Final versus master: Alustin

The same pinned Alustin scene runs with explicitly selected Roboto Flex,
Vollkorn or PT Sans and an Inter fallback. Untimed diagnostics verify the actual
font bytes. Both backends use the controlled desktop, eager shaders and GPU
warmup. These values measure renderer-thread CPU; they are not end-to-end
startup, compositor or GPU latency.

| Font | First frame, WGPU | First frame, OpenGL | Search frame, WGPU | Search frame, OpenGL |
| --- | ---: | ---: | ---: | ---: |
| Roboto Flex | −3.74% [−5.86, −0.25] | −0.99% [−2.68, +0.02], uncertain | +0.83% [−3.55, +6.47], uncertain | −0.29% [−2.88, +2.12], uncertain |
| Vollkorn | −23.96% [−24.80, −21.45] | −18.19% [−20.25, −17.27] | −5.04% [−12.79, −0.79] | −8.00% [−10.10, −4.56] |
| PT Sans | −6.80% [−7.88, −4.78] | −4.63% [−6.96, −2.49] | −5.39% [−10.72, +1.66], uncertain | −0.85% [−5.21, +3.65], uncertain |

Paired first-frame CPU savings are about 0.56/0.17 ms for Roboto, 5.36/4.74 ms
for Vollkorn and 1.03/0.86 ms for PT Sans on WGPU/OpenGL. Only Vollkorn provides
supported search-frame gains on both backends. Whole-process peak RSS paired
changes range from −0.68 to +0.50 MiB across these six configurations; five
intervals include zero. PT Sans WGPU is −0.66 MiB [−1.52, −0.20]. These noisy
whole-process peaks cannot establish the cache's allocation cost or memory
neutrality.

## What the budget fix buys, and what the later fixes cost

An additive public-API control shares a TextContext across ten fresh canvases
with fresh outer atlases. Each pass draws exactly 3300, 3440 or 3600 Roboto
geometry keys at integer sizes below the atlas routing threshold. This creates
repeated demand for the same hinted geometry near the cache budget, rather than
letting an already-warm bitmap atlas conceal it. Draw and flush costs are timed;
font/request preparation and canvas creation/destruction are excluded.

| Geometry keys | Final/master, all ten passes | Fixes 4–5/prior, all ten passes | Fixes 1–3/updated45, all ten passes |
| --- | ---: | ---: | ---: |
| 3300 | −14.22% [−14.56, −13.77] | −11.12% [−11.41, −10.65] | +0.86% [+0.25, +1.04] |
| 3440 | −13.80% [−14.35, −13.59] | −11.13% [−11.53, −10.72] | +0.81% [+0.46, +1.21] |
| 3600 | −3.86% [−4.29, −3.53] | −0.55% [−0.88, −0.37] | +0.70% [+0.17, +1.07] |

These totals include the population pass. Final saves approximately
10.56/10.84/3.23 ms relative to master over the complete ten passes. The 4–5
changes have uncertain population-pass effects against prior, but improve the
nine reuse passes about 12.2–12.4% at 3300/3440 keys. The much smaller effect
at 3600 is consistent with a fitting-working-set repair rather than a general
miss-speed breakthrough. This is a targeted synthetic stress case, not a claim
that ordinary applications have these exact working sets. Upload/vertex
digests validate this control; they do not measure cache hits or constitute a
full RGBA oracle.

The earlier untimed mechanism probe separately showed why the admission change
matters: a 1 MiB cache discarded 3140 outlines although adding the next outline
with minimum growth would have accounted for only 951,683 bytes. The new code
keeps that fitting set. A synthetic 3440-key, ten-pass probe recorded 90% hits
and no clears with the exact-growth policy, while a tested bounded-headroom
alternative lost residency. Those observations explain the policy choice;
they are distinct from this follow-up's elapsed-time measurements.

Outside that targeted case, fixes 4–5 do not provide a universal incremental
speedup over prior. Complete CPU text replay changes are +0.44% for PT Sans and
+1.12% for Vollkorn with intervals above zero; Roboto's +0.61% is uncertain.
The final patch still retains the much larger master-relative benefits.

Fixes 1–3 add roughly 0.7–0.9% to the ten-pass boundary control, about
0.54–0.56 ms in total. They also add 1.44%/20 µs to Roboto demo first paint and
1.24%/55 µs to Vollkorn demo first paint. Other increments vary: Vollkorn text
first paint improves 1.85%/0.39 ms. All twelve Alustin first-frame/search-frame
increments across six cohorts against updated45 are uncertain. These are
combined patch effects;
the campaign does not isolate the render-target wrapper from the other fixes.

## Correctness and evidence

The first strict master-parity pixel precheck failed and is retained. Fixing
master's negative-phase collision necessarily changes its broken output. The
accepted suite therefore uses an independent untimed native-master oracle:
master's native Swash rendering is unchanged, while its atlas key uses the
actual raster offset's float bits, with signed zero canonicalized. It does not
copy the new signed-bin key or the outline cache.

Final matches all 168 native-oracle phase captures exactly; prior and updated45
match all 168 master captures exactly. Only four final/master captures differ:
text/size-advance with Roboto and Vollkorn at both DPRs. The Roboto difference
is 112 pixels and two additional atlas keys; Vollkorn is 21 pixels and four
keys. Aliasing can poison later positive-position requests, so the corrected
pixels are not all confined to negative screen positions. All 18 Alustin
candidate/master RGBA comparisons remain exact. No complete glyph-trace probe
was run or used to infer more specific attribution.

Validation passes: **175/175** library tests with default features plus Swash,
**159/159** with defaults disabled plus Swash, the default non-Swash library
check, formatting and diff checks. Independent audits verify exact frozen and
live source hashes, build origins, locked graphs, binary launch identities,
actual fonts, pixel comparisons and accepted order balance. Independent raw
statistics recompute 3888 replay point effects and 1296 primary intervals, and
72 Alustin CPU effects and intervals. The boundary workload has its own raw,
source, graph and statistics audit.

The case for accepting the PR is a bounded additional geometry cache that
avoids repeated native hinting across distinct bitmap-atlas demands, with
repeatable full-sequence gains and application evidence for expensive fonts,
plus smaller measured Roboto gains. The latest admission repair preserves
useful residency instead of flushing on an oversized reserve request, and
scaler/key consistency is enforced by construction. The case is conditional on
these workload benefits being worth the added code and retained memory; it is
not a promise of universal speedup, memory neutrality or lower end-to-end
latency in every application.

See [reproduction instructions](docs/revised-cache-reproduction.md) for the
frozen four-way sources and offline archive verification. All old reports and
benchmarks, the failed pixel cohort, all raw attempts, and the unsuccessful
first audit-helper compilation are preserved. Compiled artifacts are omitted
with inventories; their measured binary identities remain recorded.
