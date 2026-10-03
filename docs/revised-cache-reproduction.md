# Reproduce the revised outline-cache comparison

The revised study has a separate frozen source bundle. It preserves the earlier
benchmark repository's vendor inputs, reports and archived campaigns. Its four
versions are `master`, committed selected arena (`prior`), the pre-fixes-1–3
snapshot (`updated45`), and the complete revised patch (`final`). All six pairs
are declared; `final/master` is the acceptance comparison. The source bundle
contains exact committed archives and verified dirty snapshots. Reproduction
uses those frozen snapshots and never reads the developer's current FemtoVG tree.

From the benchmark repository, extract and verify every source-bundle byte into
a fresh directory and prepare relocated runtime inputs:

```sh
python3 scripts/prepare-revised-cache.py --output runs/revised-cache --alustin-checkout /path/to/alustin-benchmark --with-budget
```

The Alustin checkout must match the archived application commit, tracked input
hashes, benchmark diff and original lock. See [Alustin setup](alustin-reproduction.md)
for the saved application inputs and external save/catalog/icon-pack fixtures.
Omit `--alustin-checkout` for replay-only builds and use the `replay` build command
below. The optional `--with-budget` also prepares the separately retained
public-API boundary workload.

All four variants must be freshly built before measurement. Builds are offline
and use pinned locked dependency resolution; populate the dependency cache on
a fresh machine first. A warmed target directory may be supplied, but historical
executables are not reused. Replay variants have distinct Cargo root package and
executable names; only that intentional local identity is normalized for graph
comparison. All other dependency identities/features and per-variant source,
lock and executable hashes are checked. Build logs and raw metadata are retained.

With the validated Alustin checkout, build both suites and retain its experiment:

```sh
python3 runs/revised-cache/bundle/scripts/build.py all --runtime runs/revised-cache/runtime
mkdir -p runs/revised-cache/alustin
cp runs/revised-cache/runtime/app/experiment.json runs/revised-cache/alustin/experiment.json
```

For replay-only preparation, build the example runners instead:

```sh
python3 runs/revised-cache/bundle/scripts/build.py replay --runtime runs/revised-cache/runtime
```

Skip subsequent `app` commands when using replay-only preparation.

The ordinary master pixel precheck exposed its legacy negative-position phase
key defect. The accepted revised study uses a separate untimed native-master
oracle: master rendering stays unchanged, while its atlas phase identity uses
the actual raster offset's f32 bits, canonicalizing signed zero. It does not
copy the revised cache or its signed-bin implementation. Only text.rs changes.
Build and capture the native oracle before constructing the separate validation
overlay. The frozen source bundle and prepared runtime remain untouched:

```sh
python3 benchmarks/revised-cache-oracle/native_offset_oracle.py prepare --runtime runs/revised-cache/runtime --output runs/revised-cache/native-master-offset-oracle
cargo metadata --offline --locked --format-version 1 --manifest-path runs/revised-cache/native-master-offset-oracle/runner/Cargo.toml > runs/revised-cache/native-master-offset-oracle/metadata.json
cargo build --release --offline --locked --manifest-path runs/revised-cache/native-master-offset-oracle/runner/Cargo.toml --target-dir runs/revised-cache/native-oracle-target
python3 benchmarks/revised-cache-oracle/native_offset_oracle.py record-build --root runs/revised-cache/native-master-offset-oracle --metadata runs/revised-cache/native-master-offset-oracle/metadata.json --binary runs/revised-cache/native-oracle-target/release/femtovg-example-outline-review-native-master-offset-oracle
python3 benchmarks/revised-cache-oracle/native_offset_oracle.py capture --root runs/revised-cache/native-master-offset-oracle --master-binary runs/revised-cache/runtime/core/master-runner --output runs/revised-cache/oracle-pixels
python3 benchmarks/revised-cache-oracle/prepare_validation_overlay.py --runtime runs/revised-cache/runtime --bundle runs/revised-cache/bundle --output runs/revised-cache/validation-overlay
python3 runs/revised-cache/validation-overlay/run.py pixels --root runs/revised-cache/runtime/core --oracle-ledger runs/revised-cache/oracle-pixels/ledger.json --output runs/revised-cache/examples-validated --dpis 1 2
python3 runs/revised-cache/bundle/scripts/run.py app pixels --runtime runs/revised-cache/runtime --output runs/revised-cache/alustin/pixels --actual-font-diagnostics
```

The ledger covers all 28 phases for all three fonts at both DPRs. Master, prior
and updated45 retain exact legacy counts and pixels. Final must match exact
native-oracle counts and RGBA; its original-master differences remain recorded.
Every controlled grid frame still requires 94 new atlas keys. Preserve any
failed cohort and diagnose it before timing. Existing negative-position
correctness tests also compare with an independent native expectation.

The example suite retains the demo, text and font-variation scenes and all
existing unique-size, unique-variation and pollution controls. Open fonts/assets
and licenses are bundled. Roboto Flex, Vollkorn and PT Sans are the reported
font factors; the variable-font controls retain their native Roboto font.
Apple emoji is an optional recorded system input and is not redistributed.

Run suites serially on a quiet machine. Run no builds, observer probes,
compression or statistical analysis during timing. Twelve planned Williams
blocks/rounds complete three four-version cycles. Example CPU processes have
five internal trials, GPU processes three. The GPU replay defaults to Metal and
uses an offscreen surface.

Application runs open windows. Its controlled desktop is 2560 × 1600 physical
pixels at DPR 2, with WGPU30 and OpenGL, explicit primary fonts and Inter fallback,
no system-font discovery, eager shaders and GPU warmup. Untimed diagnostics verify
the actual font bytes. Renderer-thread CPU is host rendering work; RSS includes
the whole process. The only retry trigger is a contaminated final query, which
retries the whole four-variant block at most three times. Retain every attempt;
accepted order counts are audited separately because retries can unbalance them.

The additive boundary workload uses public `Canvas::fill_glyph_run` calls with
fresh atlases/canvases sharing one TextContext across ten phases. It targets
3300, 3440 and 3600 Roboto geometry keys near the 1 MiB soft-accounting boundary,
including the first population in complete-sequence totals. It is a targeted
synthetic workload, not an application latency claim. Separate untimed copies
compare upload/vertex digests; this is distinct from full RGBA pixel comparison.
The installed budget helper is a validated reproduction adaptation of the
retained measurement driver. It copies the eight exact measured Cargo locks
before preparation and uses offline locked metadata/build commands without
regenerating dependency resolution. Its scene and statistics code are unchanged;
the measured driver, adaptation and validation proofs remain archived.

```sh
python3 benchmarks/revised-cache-budget/bench.py build --root runs/revised-cache/budget-runtime --kind timing
python3 benchmarks/revised-cache-budget/bench.py build --root runs/revised-cache/budget-runtime --kind audit
python3 benchmarks/revised-cache-budget/bench.py run --root runs/revised-cache/budget-runtime --kind audit --font runs/revised-cache/runtime/assets/RobotoFlex-VariableFont.ttf --output runs/revised-cache/budget-audit
python3 benchmarks/revised-cache-budget/bench.py analyze --root runs/revised-cache/budget-audit
```

After all builds and pixel/audit checks, run the four timed suites serially:

```sh
python3 runs/revised-cache/validation-overlay/run.py cpu --root runs/revised-cache/runtime/core --oracle-ledger runs/revised-cache/oracle-pixels/ledger.json --output runs/revised-cache/examples-validated --blocks 12
python3 runs/revised-cache/validation-overlay/run.py gpu --root runs/revised-cache/runtime/core --oracle-ledger runs/revised-cache/oracle-pixels/ledger.json --output runs/revised-cache/examples-validated --blocks 12
python3 runs/revised-cache/bundle/scripts/run.py app cpu --runtime runs/revised-cache/runtime --output runs/revised-cache/alustin/cpu --rounds 12
python3 benchmarks/revised-cache-budget/bench.py run --root runs/revised-cache/budget-runtime --kind timing --font runs/revised-cache/runtime/assets/RobotoFlex-VariableFont.ttf --output runs/revised-cache/budget-timing --blocks 12 --trials 5
```

Build both budget kinds and complete the untimed audit before any timed suite.
After all serial timed suites finish, compute statistics. Each complete sequence
is summed within a trial before process medians and block pairing. Intervals are
whole-block bootstrap intervals, without multiplicity or selection adjustment.

```sh
python3 runs/revised-cache/validation-overlay/summarize.py --root runs/revised-cache/examples-validated --output runs/revised-cache/analysis/replay/phase --bootstrap 10000
python3 runs/revised-cache/validation-overlay/sequence_totals.py --root runs/revised-cache/examples-validated --output runs/revised-cache/analysis/replay/sequence --bootstrap 10000
python3 runs/revised-cache/bundle/scripts/analyze.py app --runtime runs/revised-cache/runtime --results runs/revised-cache/alustin/cpu runs/revised-cache/alustin/pixels --output runs/revised-cache/alustin/analysis --bootstrap 10000
python3 benchmarks/revised-cache-budget/bench.py analyze --root runs/revised-cache/budget-timing --bootstrap 10000
```

The original completed measurements can be verified offline without the old
temporary directories, builds or windows:

```sh
python3 scripts/verify-results.py --campaign updated-cache-examples --campaign updated-cache-alustin --campaign updated-cache-source-bundle --output runs/revised-cache-offline-verification
```

The verifier checks every retained archive byte and visible-copy checksum, then
independently reconstructs the two declared replay/application raw statistical
plans through a verified longest-prefix path map. Boundary raw trials, source,
method and independent audit are retained within the examples archive and visible
budget analysis copies. Compiled executables are omitted; their recorded build
identity is verified offline, and actual bytes are checked in every fresh run.
