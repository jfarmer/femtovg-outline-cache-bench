# Outline-cache study methodology

The primary comparison is the selected FemtoVG source against upstream master,
with the original eager-cache patch retained as a third reference. Prototype
comparisons explain implementation choices; they do not replace the primary
comparison. This is a Swash-only change. Swash source and dependency requirements
are unchanged, and the measured dependency resolution uses Swash 0.2.10.

## Why an outline cache can help

A glyph-atlas hit already avoids rasterization. The additional cache helps when
an atlas miss requests an outline already hinted at the same face, exact size,
glyph ID, and normalized variation coordinates. Horizontal pixel phases can
share that geometry while keeping separate rasterized atlas entries. A new size
or variation instance cannot reuse the old hinted geometry. Color glyphs retain
native Swash source selection and bypass the outline cache.

On an outline miss, the additional work includes key creation and hashing,
retained geometry allocation or copying, and cache bookkeeping. Its benefit on
a later phase is the avoided native scaling and hinting. Font bytecode size
describes one input to scaling cost; it does not measure reuse, native hint-cache
behavior, rasterization cost, or how much of an application frame is text.
Therefore this study establishes no static bytecode admission cutoff.

The miss-cost candidates use existing APIs: reuse Swash's Scaler within a run,
avoid constructing an unused generic FemtoVG Path, use scale_outline_into with
caller-owned scratch, change cache indexing, or reuse caller-owned render/upload
buffers. No additional font parser, hint interpreter, or Swash hint cache is
implemented. The bitmap prepass uses FemtoVG's existing ttf-parser metadata API
to preserve its existing PNG draw partition.

## Workloads

The replay preserves all 19 phases from the existing demo, text, and variable-font
examples. It adds nine controlled phases through the public glyph-run API:
single-use glyphs; a complete first/second horizontal-phase pair; unique sizes;
unique variable instances; and hot-population, pollution, and hot-return phases.
Each controlled frame introduces 94 distinct atlas keys. Whole-sequence totals
include cache population and pollution, rather than reporting the hot return in
isolation. The example sequence totals exclude 119 unreported warmup frames per
scene and are explicitly described as sums of reported phases.

Alustin supplies application rendering with identical save, catalog, icon pack,
viewport, font registration, and renderer settings across variants. Roboto Flex,
Vollkorn Medium, and PT Sans Regular are used in both environments. Font changes
also change geometry, metrics, and layout; differences between fonts cannot be
attributed to bytecode size alone. Separate untimed application launches verify
the actual primary font faces and bundled Inter fallback.

The variable-font example and controlled variation grid always use Roboto Flex.
Their repeats under the other regular-font factors are repeated controls, not
independent evidence about Vollkorn or PT Sans.

## Timing and statistics

All timed jobs run serially, without concurrent benchmark jobs, builds, archive
compression, or heavy analysis. Each variant uses a fresh process. Version order
uses Williams cycles, balancing position and directed carryover; configuration
order rotates. Driver metadata records the exact order, source maps, executable
hashes, toolchain, font hashes, lockfiles, and dependency graphs. Reused historical
baseline executables require exact source, instrumentation, toolchain, lock, and
dependency checks. Portable reproduction rebuilds every variant.

Replay CPU uses the same Void-renderer black_box barriers for every variant.
GPU replay uses offscreen Metal/WGPU, with separate drawing, submission, and GPU
completion observations. These durations are cumulative and must not be added.
Pixel captures and observer traces are separate, untimed cohorts.

Within-process trials become process medians before pairing variants within a
block. Effects are median paired ratios and median paired absolute differences.
95% percentile bootstrap intervals resample whole blocks with shared indices
across versions. All valid observations remain; there is no duration trimming,
outlier filtering, or duration-based retry. Confidence intervals are exploratory
and have no multiplicity adjustment. A small selected font set and one machine
limit generalization.

Alustin's CPU diagnostics measure host renderer-thread work, including component
rendering and flush. They do not measure GPU completion, compositor presentation,
or diagnostics-off startup. Only query contamination permits a whole-block retry;
all other failures abort an incomplete cohort. The older 589-launch startup
attempts are preserved and excluded as whole incomplete cohorts.

## Correctness and storage

Every successful pixel cohort compares complete RGBA images to master. Tests
cover exact outline identity, normalized coordinates, color-source priority,
empty/invalid fallback, cache clears, oversized outlines, and PNG/COLR painter
order. The separate mixed-color GPU validator makes legacy painter order
observable with overlapping colored glyphs, not just command counts.

The original cache's 1 MiB budget is logical accounting, not total heap memory.
The arena candidate additionally counts its own vector capacities exactly and
native Outline scratch using public point/verb high-water lengths. Private Swash
capacity, private layer buffers, spare map buckets, allocator overhead, native
ScaleContext storage, and transient working memory are outside that soft budget.
The initial private-capacity-estimation prototype remains archived but is not the
final arena candidate. Changing accounting can change residency and clear timing;
arena timings therefore measure the complete policy/storage implementation.

Allocation observers count successful allocation/reallocation requests during
drawing. Requested bytes sum requests, including full reallocation sizes; they
are neither live-memory measurements nor proof of an elapsed-time improvement.
The isolated pooled-pixel prototype demonstrates why those distinctions matter.

## Preservation

Results archives preserve original raw measurements, failures, provenance,
analysis, pixel captures, source snapshots, lockfiles, and scripts without
rewriting recorded absolute paths. Each archive has a verified per-file manifest.
Compiled artifacts and compiler caches are omitted and inventoried; executable
hashes remain in build provenance. Repository tools resolve historical paths
through the archive index. Fresh runtime path relocation is separately recorded
and never changes historical evidence.

Archive retention does not mean that an incomplete or rejected cohort supports
a performance claim. Each report identifies its included cohorts and exclusions.
The earlier benchmarks remain available as historical evidence.
