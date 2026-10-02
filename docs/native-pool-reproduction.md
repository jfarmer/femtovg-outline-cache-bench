# Reproduce the native Swash Outline pool comparison

The arena/native-pool follow-up has its own pinned source bundle. Existing
`vendor/` inputs and commands for the earlier arena-selection study remain
unchanged. The new bundle uses the same portable workflow, with four fresh
variants: `master`, original cache (`current`), selected arena (`final`) and
native objects (`pool`). Its analysis declares the five original baseline
comparisons plus the direct `final` → `pool` comparison.

The only production source difference between arena and pool is
`src/text/swash_rasterizer.rs`. Both use native Swash scaling/hinting, the same
cache keys, scaler/run reuse and guarded bitmap routing. Pool storage replaces
shared point/verb ranges with owned native Outline objects and bounded
recycling. Native private capacities are inaccessible; the two 1 MiB soft
budgets do not have identical admission or heap-retention behavior.

## Verify and extract the isolated bundle

From the benchmark repository, first checksum the archived bytes and their
retained file records. This command does not build Rust or open windows:

```sh
python3 scripts/verify-results.py --campaign native-pool-source-bundle --output runs/native-pool-bundle-verification --integrity-only
mkdir -p runs/native-pool-bundle
tar -xzf results/native-pool-source-bundle/records.tar.gz --strip-components 1 -C runs/native-pool-bundle
```

The extraction directory must be empty. Archive hardlinks deduplicate identical
contents while preserving every original filename and checksum. Compiled
executables and compiler caches are omitted. The bundle's own manifest guards
all pinned `vendor/` source snapshots, application inputs and open font/assets.

## Fresh replay builds and measurement

Run the following commands from the repository root. The output directories
must be fresh; never reuse an incomplete or modified preparation.

```sh
python3 runs/native-pool-bundle/scripts/prepare.py --output runs/native-pool-runtime
python3 runs/native-pool-bundle/scripts/build.py replay --runtime runs/native-pool-runtime
python3 runs/native-pool-bundle/scripts/run.py replay pixels --runtime runs/native-pool-runtime --output runs/native-pool-results --dpis 1 2
python3 runs/native-pool-bundle/scripts/run.py replay cpu --runtime runs/native-pool-runtime --output runs/native-pool-results --blocks 12
python3 runs/native-pool-bundle/scripts/run.py replay gpu --runtime runs/native-pool-runtime --output runs/native-pool-results --blocks 12
python3 runs/native-pool-bundle/scripts/analyze.py replay --runtime runs/native-pool-runtime --results runs/native-pool-results --output runs/native-pool-analysis --bootstrap 10000
```

Build all four variants afresh before any measurement. A warmed Cargo target
directory may be supplied with `--target-dir`; cached build artifacts are
allowed, historical executable reuse is forbidden. All builds use pinned
`--offline --locked` dependency resolution; prepare the dependency cache first
if reproducing on a new machine.

The GPU replay defaults to Metal and requires a working GPU; it creates an
offscreen surface. The existing demo, text and variation scene definitions and
all five controlled scenes remain intact. CPU runs use five within-process
trials; GPU runs use three. Twelve Williams blocks balance launch position and
directed predecessor counts. Run builds, pixel checks, CPU timing and GPU timing
serially on a quiet machine. Bootstrap analysis and allocation instrumentation
must run only after timed measurements have completed.

Roboto Flex, Vollkorn Medium, PT Sans and all required demo assets are bundled
with licenses. Arial and Apple Color Emoji are system inputs and are not
redistributed. The optional Apple emoji input and its hash are recorded when
available; original pixel artifacts reflect the recorded machine's inputs.

## Alustin application

Use the pinned application checkout and the common five-file benchmark diff
described in [alustin-reproduction.md](alustin-reproduction.md), including its
external save, catalog and icon-pack fixtures. The original Alustin-specific
outline fix must be absent from all variants. Prepare a new runtime with that
checkout; the application builder checks exact HEAD, tracked inputs, common
diff, lock and dependency/features graph before building each source override.

```sh
python3 runs/native-pool-bundle/scripts/prepare.py --output runs/native-pool-app-runtime --alustin-checkout /path/to/alustin-benchmark
python3 runs/native-pool-bundle/scripts/build.py all --runtime runs/native-pool-app-runtime
python3 runs/native-pool-bundle/scripts/run.py app pixels --runtime runs/native-pool-app-runtime --output runs/native-pool-app-pixels --actual-font-diagnostics
python3 runs/native-pool-bundle/scripts/run.py app cpu --runtime runs/native-pool-app-runtime --output runs/native-pool-app-cpu --rounds 12
python3 runs/native-pool-bundle/scripts/analyze.py app --runtime runs/native-pool-app-runtime --results runs/native-pool-app-cpu runs/native-pool-app-pixels --output runs/native-pool-app-analysis --bootstrap 10000
```

Application runs open windows. The controlled desktop uses 2,560 × 1,600
physical pixels, DPR 2, WGPU30 and OpenGL, no system-font discovery, explicit
primary fonts plus bundled Inter fallback, eager shaders and GPU warmup.
Untimed pixel diagnostics verify actual primary and fallback font bytes.
Renderer-thread CPU spans describe host rendering work rather than display
latency or overall startup. Peak RSS includes the whole process.

Only final-query contamination retries an entire four-version block, at most
three attempts; every raw attempt and valid partner remains preserved. No
timing-based rejection, retry or outlier trimming is permitted.

## Offline raw-data verification

The original machine's results can be verified without rebuilding, opening
windows or accessing its old `/private/tmp` directories:

```sh
python3 scripts/verify-results.py --campaign native-pool-examples --campaign native-pool-alustin --campaign native-pool-source-bundle --output runs/native-pool-offline-verification
```

The verifier checks all retained archive bytes and visible analysis copies,
then independently reconstructs primary raw effects and confidence intervals
through a verified historical-root mapping. Compiled executable bytes are
absent from archives; offline verification checks their recorded identity and
build provenance rather than claiming to hash missing binaries. Fresh runtime
preflights check actual binary bytes before every reproduced run.

The independent allocation probe is untimed and has its own isolated sources,
observer, allocator, build identities and complete prefix records. Its requested
heap measurements include actual private native buffers but exclude allocator
bookkeeping, page residency and GPU memory. That probe does not substitute for
elapsed-time measurements or complete exact RGBA comparisons.
