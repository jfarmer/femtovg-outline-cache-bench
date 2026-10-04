# Smaller integration on the hinting stress demo

See [results and interpretation](SUMMARY.md) and [all measured phases](REPORT.md).
This uses the same scene and fonts as the [earlier stress comparison](../demo-current-20261003/raw/stress/paired12-dpi1/REPORT.md),
now comparing master, the current cache plus encapsulation edits, and the smaller
integration from the [previous experiment](../lower-touch-20261003/SUMMARY.md).

`snapshot.tar.gz` contains exact source snapshots, manifests and locks, the
unchanged stress scene, fonts and licenses, build provenance, plans, raw outputs,
process guards and analysis. Compiled executables and compiler caches are omitted;
their measured hashes remain in provenance and `OMITTED.json`.

With Python 3.12 or later, verify and optionally extract:

```sh
python3 verify.py
python3 verify.py --extract /tmp/femtovg-lower-touch-stress
```

Harness manifests use relative paths. With Rust/Cargo and cached dependencies,
rebuild all three versions and measure into a fresh output directory:

```sh
cd /tmp/femtovg-lower-touch-stress/bench
python3 build.py
python3 run.py --out runs/new-comparison --blocks 12
python3 analyze.py --out runs/new-comparison
```

The measured builds and runs were validated in the original isolated directory.
Archive integrity and extraction were checked after packaging. A fresh build from
the relocated archive has not been tested. The runner needs permission to inspect
process names and stops if that inspection fails or a build overlaps timing.

The [drawing source](../demo-current-20261003/raw/stress/harness-src/main.rs)
is unchanged. The scene draws the same text at three sizes in ten fractionally
shifted rows, then repeats it and changes the sizes. Measurements cover CPU
layout, drawing and Void flush at DPI 1, excluding setup, GPU work and app startup.
