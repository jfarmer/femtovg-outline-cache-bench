Performance verification for the complete glyph-outline cache fix

Primary baseline: upstream `6a5f15ae55db439a4ed8b1e818c6521029c34fbd` (`master`).
Attribution control: cache branch `da268321ec2b53cdd188e8c07f853897121c3767` (`base`).
Current candidate: frozen working tree (`finalgenericrestore`), production bytes
matching commit `7b42f524b0f357ad535e54ac0aad6ab22ab71aae`. Earlier `final` and
`ordinary-inline` snapshots remain historical controls: the latter replaces only
the earlier `add_glyph_quad`'s `#[inline(always)]` with ordinary `#[inline]`.

All writes remain under this directory. No GUI is used. Timings must start only
after the parent confirms the code is ready and other builds have completed.
The runner checks compiler/build/linker process names before each configuration.
It preserves every observation and aborts if a build is detected; there is no
timing-based rejection or filtering.

The warm harness is byte-for-byte `review/evidence/v-F06-reproduce/f06probe.rs`.
Cold labels and paragraphs reuse its layout implementation, with natural and
rounded single-phase positions. Controlled misses reuse the archived study's
`controlled.rs`, changing only font registration outside timing to support
swash-only: a public `TextContext` registers the font and passes its ID to the
scene. Control requests, phases and drawing remain unchanged. Sequence totals
include population, pollution and hot return.

Generic validation covers public fill/stroke in a default build without swash,
and strokes in both swash configurations. The same precomputed labels/paragraph
are measured at positive positions and shifted to straddle zero.

After the final-source signal:

```sh
python3 /private/tmp/femtovg-review-fixes-perf/prepare.py finalgenericrestore
python3 /private/tmp/femtovg-review-fixes-perf/build.py finalgenericrestore
python3 /private/tmp/femtovg-review-fixes-perf/verify.py --candidate finalgenericrestore
python3 /private/tmp/femtovg-review-fixes-perf/run.py --suite warm --output warm-rerun --blocks 12 --frames 3000 --variants master base finalgenericrestore --code-ready --external-build-finished
python3 /private/tmp/femtovg-review-fixes-perf/run.py --suite generic --output generic-rerun --blocks 12 --frames 3000 --samples 7 --variants master finalgenericrestore --code-ready --external-build-finished
python3 /private/tmp/femtovg-review-fixes-perf/run.py --suite cold --output cold-rerun --blocks 12 --samples 7 --variants master base finalgenericrestore --code-ready --external-build-finished --retry-interference --quiet-seconds 60 --max-retries 30 --max-duration 1800
```

Preparation and build commands refuse to overwrite frozen sources. Runner output
directories must be fresh. Cargo builds use offline locked resolution, distinct
package identities, and captured compiler artifacts proving the local FemtoVG
manifest. Production source maps, harness hashes, dependency metadata, toolchain,
profile, executable hashes and font hashes are retained. Release uses opt-level 3,
no LTO, 16 codegen units, no incremental compilation, no debug info, and unwind.

Paired process order rotates and reverses; configuration order rotates across
blocks. Within-process cold medians use seven fresh Canvas/atlas/context samples;
warm results use individually timed frames after 20 warm frames. Reports include
absolute ns/glyph, us/frame, complete sequence cost, paired ratios and absolute
deltas. Exploratory 95% intervals bootstrap paired blocks 10,000 times without
multiplicity adjustment. All layout, font registration and control setup occurs
outside timing. Results measure CPU public drawing and Void flush, not GPU or
whole-application/display latency. A finite workload set cannot prove universal
absence of regressions.

The actual demo/text scene adapters are prepared separately under
`/private/tmp/femtovg-review-fixes-scenes`; their demo.rs, text.rs and perf_graph.rs
are byte-preserved archived adapters. `scene-build.py` verifies their final
production hashes equal this candidate and builds four binaries with both
default feature configurations. `scene-run.py --output scenes-rerun --blocks 12
--code-ready --external-build-finished --retry-interference --quiet-seconds 60
--max-retries 30 --max-duration 1800` compares both Roboto Flex/Vollkorn demo
and text scenes. Scene timing includes layout and other scene drawing; font/image
loading remains outside first-paint timing. Scene phase means and complete
phase costs cover CPU Canvas drawing and Void flush, without GPU execution.

`absolute.py COHORT ...` derives paired absolute per-frame and complete-sequence
95% intervals from retained raw blocks without new measurements. Run it only
after timing has stopped. Marginal candidate and master medians need not differ
by the median paired delta.

`cold-genericrestore`, `cold-genericrestore-clean`,
`cold-genericrestore-quiet`, and `cold-genericrestore-final` are incomplete
excluded cohorts: the process-name guard detected Cargo/build activity after
eight, two, four, and five reported complete
blocks respectively. Their EXCLUDED.md files preserve exact PIDs and reasons;
their observations are not merged into the replacement cohort. The earlier
runner is preserved in run-before-nameguard.py (SHA-256
681dc3b7e67e5d1f4b629379d0fa61933e3c3fa0cbc4a11c2038bf52f4d35a0b).
The subsequent guard adds immediate PID+comm recording on abort; measurement
code and harness hashes are unchanged. `idlecheck.py` requires 45 consecutive
seconds without compiler/build/linker process-name matches before timing.

The user confirmed that the external project build is still running. All
further timing is held until the user explicitly indicates it has finished;
a quiet gap is insufficient. No retry cohort has started. RETRY_PLAN.json
predeclares a new whole-logical-block retry policy: every process receives
before/after guards, matched builds reject an entire attempt, 60 quiet seconds
precede its replay, all attempted records remain available, and timing values
never drive exclusions. The archived runners under runners/block-retry-v1
must hash-match the live scripts before this mode starts. The auditor verifies
accepted/excluded streams against the attempt ledger and deterministic plan.

After the user's question about another cold run, a separately declared post
hoc provisional analysis uses all eight complete blocks 0–7 from the earliest
cold-genericrestore campaign only. All 66 configurations and three variants
are included, with 174 partial block8 records and every later campaign omitted.
Original EXCLUDED.md, metadata and raw files remain unchanged; no records are
merged into a primary twelve-block cohort. Independent numerical analysis is
in provisional-cold-audit; matrix/source/metric provenance is separately checked
in provisional-cold-provenance by cold-provenance.py, without another bootstrap
or measurement. RESULTS.md reports representative complete-sequence costs and
the three inconclusive rows. No additional cold timing is planned unless a
meaningful new concern appears. The remaining planned timing is actual scenes,
after explicit user confirmation of external-build completion.
