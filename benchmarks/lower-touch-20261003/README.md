# Smaller integration experiment

See [results and interpretation](SUMMARY.md), [all measured phases](REPORT.md),
and the [production line-count records](LINE-COUNTS.json).

This compares master, the current implementation plus its encapsulation edits,
and a prototype that restores the single atlas loop and builds a scaler per miss.
The prototype and all measurements are preserved; the FemtoVG branch was not replaced.

`snapshot.tar.gz` contains exact source snapshots, manifests and locks, benchmark
scripts, assets and licenses, plans, raw output, process guards, and analysis.
Compiled executables and compiler caches are omitted. Binary hashes are retained
in build provenance and `OMITTED.json`. Every retained file is indexed and hashed.

Verify and optionally extract with Python 3.12 or later:

```sh
python3 verify.py
python3 verify.py --extract /tmp/femtovg-lower-touch
```

The extracted harness manifests use relative paths. With Rust/Cargo and cached
dependencies, rebuild all versions and measure into a fresh output directory:

```sh
cd /tmp/femtovg-lower-touch/bench
python3 build.py
python3 run.py --out runs/new-comparison --blocks 12
python3 analyze.py --out runs/new-comparison
```

The measured builds and runs were validated in the original isolated directory.
Archive integrity and extraction were checked after packaging. A fresh build from
the relocated archive has not been tested. The runner needs permission to inspect
process names and stops if that inspection fails or a build overlaps timing.

The demo drawing source is the same as the [existing archived adapter](../demo-current-20261003/raw/scenes/harness-src/demo.rs).
The complete one-use/size-sweep drawing source is retained at
`bench/harness-src/cold/controlled.rs` inside the snapshot. These CPU measurements
exclude setup, GPU rendering and application startup.
