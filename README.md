# FemtoVG Swash outline cache experiments

This repository preserves the outline-cache investigation: original benchmarks,
font/hinting studies, rejected alternatives, native Swash miss-cost prototypes,
FemtoVG demo/text/variation replays, and Alustin application comparisons.
See [SUMMARY.md](SUMMARY.md) for the submission case, [REPORT.md](REPORT.md) for
the full findings, and [results/index.json](results/index.json)
for the full campaign inventory. An archived experiment can be incomplete or
rejected; inclusion here does not make it a valid performance result.

The runtime source bundle pins FemtoVG master and the original cache patch by
commit, plus the measured candidate source snapshots and the Alustin inputs.
Every fresh run builds **all** configured variants. It does not reuse the
historical benchmark executables. Python 3.11+ is sufficient to verify results;
Rust/Cargo and cached dependencies are needed to build. Measured GPU and Alustin
runs used macOS/Metal and the two Alustin FemtoVG backends. Fresh numbers depend
on the machine, toolchain and desktop workload.

The portable wrappers were exercised with real fresh builds and untimed pixel
and actual-font checks; see [portable execution validation](docs/portable-validation.md).

## Verify the retained evidence offline

The installed repository passed all 22 archive checks and four independent raw
statistical audits; see the [offline verification outcome](docs/offline-verification.md).

```sh
python3 scripts/verify-results.py --output runs/verification
```

This checks compressed-archive checksums and every retained member, then audits
the raw CSV/trace records declared in the index. The independent auditors
recompute complete process/block matrices, paired effects and primary paired
block bootstrap intervals. They do not import the benchmark analyzers. Whole
Alustin attempts excluded for a contaminated query remain in the archive and
are independently rechecked. For a faster integrity-only pass:

```sh
python3 scripts/verify-results.py --integrity-only --output runs/integrity
```

No original `/tmp` paths need to exist. Original scripts and absolute-path
provenance remain unchanged inside the archives; a verified longest-prefix path
map resolves their retained data. Compiled executables and compiler caches are
omitted and listed explicitly. Their historical hashes remain in provenance;
offline verification does not claim to inspect omitted executable bytes.

Repeated identical files are stored as ordinary tar hardlinks to an earlier
regular member. Each original path still has its own byte-count/SHA record.
The verifier rejects escaping, forward and chained links, checks every alias
against its canonical member, and materializes selected metadata under the
original paths. This reduces archive size without dropping source or pixel data.

## Rebuild and rerun the selected cohort

```sh
python3 scripts/prepare.py --output runs/reproduce
python3 scripts/build.py replay --runtime runs/reproduce
python3 scripts/run.py replay pixels --runtime runs/reproduce --output runs/reproduce/pixels --dpis 1 2
python3 scripts/run.py replay cpu --runtime runs/reproduce --output runs/reproduce/timing --blocks 12
python3 scripts/run.py replay gpu --runtime runs/reproduce --output runs/reproduce/timing --blocks 12
python3 scripts/analyze.py replay --runtime runs/reproduce --results runs/reproduce/timing --output runs/reproduce/analysis
```

The replay copies the original FemtoVG demo, text and font-variation scenes and
adds controlled atlas-miss cases. Pixels are collected in an untimed batch;
timing drivers validate identical frame/atlas-entry counts. Default primary font
factors are Roboto Flex, Vollkorn and PT Sans. The benchmark reports each phase
and weighted scene totals, summing phases within each trial before taking process
medians. Balanced launch order controls position and immediate carryover.

The original text example optionally loads the macOS Apple Color Emoji face.
That behavior is preserved; its availability and checksum are recorded by the
portable run wrapper. The proprietary system font is not bundled, so other
platforms can have different emoji fallback coverage.

For Alustin, provide a checkout at the exact pinned commit and tracked-input
hashes in `vendor/app-inputs/provenance.json`; all of its vendored dependencies,
fixtures, icon pack and benchmark feature must be present. Preparation reads
that checkout; the build temporarily uses the archived resolved Cargo.lock and
restores the original lock only if it still has the expected bytes.

```sh
python3 scripts/prepare.py --output runs/alustin --alustin-checkout /path/to/alustin-gui-v2
python3 scripts/build.py app --runtime runs/alustin
python3 scripts/run.py app pixels --runtime runs/alustin --output runs/alustin/pixels
python3 scripts/run.py app cpu --runtime runs/alustin --output runs/alustin/cpu --rounds 12
python3 scripts/analyze.py app --runtime runs/alustin --results runs/alustin/cpu --output runs/alustin/analysis
```

Alustin commands open application windows and exercise the large save plus a
search update. Keep desktop input idle during them; only the predeclared
contaminated-query rule retries a whole block. Thread CPU spans measure renderer
work; they do not measure GPU completion or display scanout. System font
discovery is disabled and selected open fonts are explicitly registered. Arial
is an optional user-supplied/system font and is not bundled.

`prepare.py` verifies every bundled source/asset checksum, creates a fresh runtime
copy and records each path substitution. Pure source snapshots and historical
records are untouched. Fresh builds record compiler/Cargo versions, exact lock,
dependency/features metadata, drawing sources, timed instrumentation, build
commands and resulting executable hashes. Shared benchmark-only atlas counters
and identical Void renderer barriers are applied to every replay variant.

## Files and licenses

- `results/*/records.tar.gz`: exact original noncompiled experiment records.
- `results/*/archive.json`: retained-member checksums and omitted-file inventory.
- `vendor/runtime/`: pinned pure snapshots and unaltered original helper templates.
- `vendor/app-inputs/`: application input provenance, exact locks and dependency graph.
- `vendor/manifest.json`: complete bundled source/asset checksums and source pins.
- `assets/`: runtime fixtures and font license texts; see [ATTRIBUTION.md](assets/ATTRIBUTION.md).
- `scripts/`: portable wrappers, archive reader and independent raw-data auditors.
- `runs/`: ignored fresh artifacts; never overwrite archived results.

The harness code is MIT licensed. Bundled FemtoVG source retains its MIT/Apache
license files. Font assets retain their separate licenses, including OFL 1.1 and
Entypo CC BY-SA 4.0. The Roboto Flex OFL text is included separately from the
older Apache-licensed Roboto font notice in the upstream asset directory.
