# Review fixes and scope

The final committed implementation is `907bb375645613b3647efab4c0efe29b50ed5b18`.
These changes remain part of the single Swash outline-cache change; no public
API or dependency changed. See [the API review](API_REVIEW.md).

PR-specific fixes:

- **4:** Restoration tests assert that the live layer survives and remains
  usable, rather than only checking an already-released target.
- **8:** Arena growth no longer repeatedly reserves one outline near the
  budget. Bounded geometric headroom and spare-capacity trimming retain
  fitting working sets while limiting allocation work.
- **9:** Cache lookups borrow normalized coordinates. Coordinates become owned
  only when admitting a new key; the larger key is budgeted.
- **11:** Remove the constructor argument left unused by Font encapsulation.

Related preexisting bugs repaired in the touched rendering path:

- **1:** Generic atlas rendering uses `Canvas::offscreen_pass` instead of
  `save/reset`, preserving open layers, transforms and canvas state. The
  debug-inspector initialization path without image-loading is covered too.
- **2:** Genuinely blank generic paths such as spaces skip atlas allocation
  and rendering. Nonempty outlines whose native bitmap is tiny or empty
  retain their generic fallback.
- **6:** Generic PNG uploads return an error instead of panicking. This does
  not repair the separate, preexisting debug image-loading initialization
  `unwrap`, which remains deferred.

The first review-fix commit, `a6eb669`, introduced a target-command regression
in generic rendering: each cold glyph's offscreen pass restored the caller's
target. Four glyphs emitted eight switches where two were expected, including
outside the Swash path. The final `907bb375` correction selects the destination
atlas before the state-isolating offscreen pass, and restores the caller once
per run. It preserves live layers and the previous batching. No accepted timing
was collected for `a6eb669`. This is separate from the preexisting layer bug.

Deferred existing atlas issues: **3** bitmap/generic positioning policy, **5**
reservation recovery after upload failure, and **7** duplicate phase entries
for phase-independent bitmaps. **10** retains a cheap handle to the same shared
ScaleContext; it is not a second scaling context.

TDD evidence in `validation/`:

- The live-layer and generic PNG checks failed against the old rendering code.
  The initial debug-inspector run had three false failures because a native
  positioning helper counted the inspector's initialization clear quad. The
  corrected helper selects the glyph draw command. Both stages' logs remain.
- The near-budget regression failed with 1,688 capacity changes across 1,858
  inserts. It now passes its bound of fewer than 64 changes, counting growth
  and shrink. All 16 isolated rasterizer module tests passed.
- For 1,000 cached renders with nonempty coordinates, allocation calls fell
  from 2,000 to 1,000, matching empty-coordinate hits. The remaining calls
  allocate image buffers. This is diagnostic evidence, not application timing.
- The generic batching regression failed with eight switches for four cold
  glyphs where two were expected. It passes with two switches on the final
  source, while asserting caller target, transform, state depth and layer
  count. It covers generic stroke with Swash and fill/stroke without Swash.
- Final `cargo nextest` library runs passed **198 / 182 / 170 tests** for
  default + Swash, Swash-only and default without Swash. The selected Swash
  debug-inspector run without image-loading passed **12 tests**. Earlier
  **197 / 181 / 169** runs are explicitly retained as prior-stage evidence.
  The no-default-feature check passed before the batching correction.

`VALIDATION.json` records log hashes, source stages and the final source-tree
identity. `SOURCE_FREEZE.json` records all three frozen source trees, commits
and patch hashes. Earlier metadata/prose are retained in `validation/prior-stage-*`.

Fresh performance measurements are complete: six balanced blocks in each of
`runs/comparison-final`, `runs/stress-final` and `runs/probe-final`. The first two
compare Master `9d574e0`, the pre-fix cache `af989d9`, and final PR code
`907bb375`; the separate mechanism probe compares Before and PR. The demo,
miss controls and Fleur stress scene are unchanged. Accepted and excluded
attempts, guards, sources, dependencies and executable hashes are retained.
The earlier `runs/comparison` contains failed pre-run checks for the superseded
freeze and no accepted timings. It is not included in the final statistics.

The large-font demo and stress savings remain. RobotoFlex's demo first frame
shows no clear change; its all-miss control is slower than Master. The detailed
reports and exploratory paired intervals describe this cost. These results
do not establish a universal performance improvement. Earlier studies retain
their own source pins and are not relabeled as this version's measurements.
