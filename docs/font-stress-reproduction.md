# Reproduce the favorable-font study

The report separates the exploratory 56-face search from the subsequent frozen
three-font confirmation. It uses existing font files and the unchanged FemtoVG
example scenes. It measures the already frozen `master` and `final` production
sources; the font search introduces no production patch or synthetic font.
These are deliberately favorable examples, not a sample of typical fonts.

The `font-stress-search` campaign preserves every search/confirmation attempt,
download/source/license record, font file, raw trial, selection rationale,
pixel reference, analysis and audit. Compiled executables and Cargo targets are
omitted; their identities and build logs remain recorded. The source/build
identity references resolve into the separately retained
`updated-cache-examples` campaign. Both archives are required for the offline
statistical audit. A longest-prefix map handles nested historical paths.

## Check the retained evidence without building or opening a window

From the benchmark repository, use a fresh output directory:

```sh
python3 -B scripts/verify-results.py \
  --campaign font-stress-search \
  --output /private/tmp/font-stress-offline-check
```

This checks every retained archive byte and visible input hash, then replays
the declared independent raw/statistical audit. It extracts metadata only for
the audit; archive verification still includes the font, source and RGBA bytes.
It does not claim to check absent compiled executable bytes.

## Prepare a fresh reproduction

The preparation helper verifies and extracts the frozen revised source bundle
and the new font-search archive. It checks that all four prepared pure snapshots
match the snapshots used for the confirmation. The build step then prepares the
native uncached-master reference from the instrumented replay sources; its atlas
identity uses actual raster-offset bits.
The original measured collector and analyzer remain unchanged in the archive.

```sh
python3 -B scripts/prepare-font-stress.py \
  --output /private/tmp/font-stress-fresh
```

Preparation makes no build, measurement or GUI launch. It creates
`reproduction-commands.json`, `fresh-source-identity.json`, and
`reproduction-adaptation.json`. The two generated drivers retain the original
collection/statistical code. Their identity check explicitly uses fresh build
proofs plus exact archived pure snapshots in place of historical independent
executable audits. Old executable-audit records are not relabeled as proof of
new executables. The adaptation and original/generated driver hashes are
recorded. Fresh results must be described as a reproduction with this disclosed
validation scope.

The font selection is fixed before new measurements. A separate relocated
selection manifest keeps the exact original font hashes, exploration records
and original selection hash/time; only the selected font paths and fresh freeze
time change. It uses Rye Regular, Doulos SIL Regular and Vollkorn Medium.

## Build, check pixels, then measure

Rust/Cargo and Python 3.11 or newer are required. The replay harness uses the
same locked dependency graph as the revised-cache campaign. Dependencies must
already be available locally: builds use `--offline --locked`. GPU measurements
and pixel checks require the harness's native Metal backend on macOS. Close
competing workloads before timing, and run each step serially.

```sh
python3 -B scripts/prepare-font-stress.py --output /private/tmp/font-stress-fresh --execute-step build
python3 -B scripts/prepare-font-stress.py --output /private/tmp/font-stress-fresh --execute-step pixels
python3 -B scripts/prepare-font-stress.py --output /private/tmp/font-stress-fresh --execute-step cpu
python3 -B scripts/prepare-font-stress.py --output /private/tmp/font-stress-fresh --execute-step gpu
python3 -B scripts/prepare-font-stress.py --output /private/tmp/font-stress-fresh --execute-step analyze
```

The existing verified builder builds all four frozen variants because the
identity checker binds all four. Confirmation times only `master` and `final`:
12 whole balanced blocks at DPR 1 and 2, five CPU trials or three GPU trials per
process. Pixel checks precede timing and require all 28 phase/count references
to agree exactly with native/master expectations. Report the fresh outputs;
do not replace the retained original measurements.

The generated collector can also be invoked directly for a limited smoke check
or a different openly licensed font. Use a different fresh output directory,
explicit `--study`, `--font LABEL PATH`, and `--versions master final` each time.
Small incomplete confirmation schedules require `--exploratory` and must be
reported as exploratory. A smoke run is not validation of a full new campaign.

## Native screening kernels

The `search` extraction also contains the original native screening package,
its pinned `Cargo.lock`, `inputs.json`, source guards, fonts and license records.
For example:

```sh
python3 -B /private/tmp/font-stress-fresh/search/screen.py build \
  --output /private/tmp/font-screen-fresh-build \
  --target /private/tmp/font-screen-fresh-target
python3 -B /private/tmp/font-stress-fresh/search/screen.py run \
  --build /private/tmp/font-screen-fresh-build/build.json \
  --output /private/tmp/font-screen-fresh-audit \
  --mode audit \
  --font Rye-Regular /private/tmp/font-stress-fresh/search/fonts/rye/Rye-Regular.ttf
```

Keep the original native package files and its original README unchanged so
`inputs.json` can check their measured hashes. Native kernel rankings are
screening evidence; the PR performance claim comes from fresh master/final
FemtoVG example measurements. The original acquisition scripts are historical
records; the copied font/source/license files permit reproduction without
refetching mutable upstream branches. `supporting/` retains the external font
inspection helper when supplied. FontTools is needed for that static inspection,
not for the replay measurement.

Reproduction validation is recorded separately from the original measurement
and statistical proofs in
[the installed validation record](../analysis/font-stress-reproduction-validation.json).
Archive extraction/source checks, four fresh replay builds, a fresh native
oracle build, and a four-process CPU smoke for Rye at DPR2 passed. The smoke
used two balanced blocks with one trial per process and retained all 28 phases.
The main performance claims use the original complete confirmation. No fresh
reproduction pixel capture, GPU timing, or full confirmation cohort is claimed.
