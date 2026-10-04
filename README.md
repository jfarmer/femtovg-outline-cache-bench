# FemtoVG Swash outline cache experiments

The current PR measurements compare upstream master `6a5f15a` with proposed code `b87a94dd`. See the [combined results and analysis](benchmarks/demo-current-20261003/SUMMARY.md).

| Scene | What it draws | Source and results |
|---|---|---|
| FemtoVG demo, DPI 2 | The existing demo: text, controls, images, paths, strokes and performance graph, followed by warm, zoom and pan frames. | [Drawing source](benchmarks/demo-current-20261003/raw/scenes/harness-src/demo.rs), [adapter](benchmarks/demo-current-20261003/raw/scenes/harness-src/main.rs), [four-font plan](benchmarks/demo-current-20261003/raw/current/demo-current-native/PLAN.json), [results](benchmarks/demo-current-20261003/raw/current/demo-current-native/REPORT.md), [two-font supplement](benchmarks/demo-current-20261003/raw/supplements/femtovg-current-demo-extremes-20261003/demo-extremes-native/REPORT.md) |
| Font specimen, DPI 1 | A finite page with 1,980 glyph requests: three sizes, ten fractionally shifted rows per size, then warm frames and size changes. | [Drawing source](benchmarks/demo-current-20261003/raw/stress/harness-src/main.rs), [plan](benchmarks/demo-current-20261003/raw/stress/paired12-dpi1/PLAN.json), [results](benchmarks/demo-current-20261003/raw/stress/paired12-dpi1/REPORT.md) |

Both measure CPU layout/drawing plus Void flush, excluding font/image loading, GPU work, window creation and startup. Each comparison uses twelve paired blocks on M4 Max/macOS. Plans, raw process output, provenance, font licenses and independent audits are retained alongside the reports. [Reproduction instructions](benchmarks/demo-current-20261003/README.md) describe the archived scripts and their validation scope.

A [smaller-integration experiment](benchmarks/lower-touch-20261003/SUMMARY.md) compares master, the current cache plus encapsulation edits, and a prototype using the original atlas loop. It removes 146 production lines and preserves the demo gains, but loses some protection against repeated size changes when every request misses. The current FemtoVG implementation is unchanged.

The [same comparison on the extreme hinting demo](benchmarks/lower-touch-stress-20261003/SUMMARY.md) shows that the smaller integration retains nearly all the savings there: Fleur de Leah goes from 90.26 ms on master to 20.18 ms with the current cache and 20.50 ms with the smaller version on the first frame.

The earlier studies below retain their own source pins and baselines. They are not pooled with these current-master comparisons.

Original evidence documents are preserved as captured. Statements that the repository had no public remote describe the capture date; the current [PR draft](pr-draft/PR_BODY.md) links the published source and results.

This repository preserves the outline-cache investigation: original benchmarks,
font/hinting studies, rejected alternatives, native Swash miss-cost prototypes,
FemtoVG demo/text/variation replays, and Alustin application comparisons.
See the earlier [SUMMARY.md](SUMMARY.md) and [REPORT.md](REPORT.md) for
those findings, and [results/index.json](results/index.json)
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

## Native Swash Outline pool follow-up

The [arena/native-object comparison](NATIVE-OUTLINE-POOL.md) adds fresh example
and Alustin measurements under a balanced order schedule, exact pixels, and
independent allocation/residency evidence. The original reports and 22 campaign archives
remain preserved. Three new archives retain this comparison and its isolated
portable source bundle; see [reproduction](docs/native-pool-reproduction.md).
The default verifier now includes the new audit plans in the full archive index.
The [installed offline check](docs/native-pool-offline-verification.md) verified
all new retained files and independently reproduced the primary statistics.

## Revised outline-cache follow-up

The [revised-cache comparison](REVISED-OUTLINE-CACHE.md) records a fresh four-way
master/prior/fixes-4–5/final comparison, with example and Alustin measurements
under a balanced order schedule, pixels, independent audits, and the targeted
public-API cache-boundary workload. The prior reports, source bundle, and campaign
archives remain preserved. Three added archives retain every raw attempt and
the isolated frozen reproduction bundle. See [reproduction](docs/revised-cache-reproduction.md)
and `scripts/prepare-revised-cache.py` for a fresh extraction/preparation.

## Repeated favorable-font measurements

A [fresh repeat](FONT-STRESS-RERUN.md) measures the same frozen master/final
sources, example scenes, three fonts, native pixel proof and balanced schedule.
It was requested because of a background-load concern; overlap with the original
measurement was not established. The original [font study](FONT-STRESS-SEARCH.md),
its numerical report, and its archive remain preserved. See the
[repeat summary](SUMMARY-FONT-STRESS-RERUN.md) and
[reproduction notes](docs/font-stress-rerun-reproduction.md).

## Favorable-font confirmation

The [font study](FONT-STRESS-SEARCH.md) records a retained 56-face exploratory
search followed by fresh frozen master/final measurements of Rye, Doulos SIL
and Vollkorn in the existing example scenes. [Summary](SUMMARY-FONT-STRESS.md),
all raw attempts, native pixels, font licenses, and independent statistical
checks are preserved. These are selected favorable examples. See
[reproduction](docs/font-stress-reproduction.md) for checked extraction and fresh
locked builds, and the report for the actual reproduction validation scope.

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

## CJK font investigation

The [CJK font study](CJK-FONT-SEARCH.md) preserves the original English demo,
adds explicitly labeled localized workloads where measured, and reports native
glyph screening separately from application/cache comparisons. All earlier
font studies and their raw cohorts remain retained. See the
[summary](SUMMARY-CJK-FONT-SEARCH.md) and
[reproduction notes](docs/cjk-font-reproduction.md).

## Aggressive Latin font investigation

The [Latin font study](AGGRESSIVE-FONT-SEARCH.md) preserves three separately frozen exploration cohorts and all original failed or rejected attempts. Native hinting/geometry costs remain distinct from unchanged-demo cache comparisons. See the [summary](SUMMARY-AGGRESSIVE-FONT-SEARCH.md) and [reproduction notes](docs/aggressive-font-reproduction.md).
