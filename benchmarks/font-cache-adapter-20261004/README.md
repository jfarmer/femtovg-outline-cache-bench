# Private Font cache adapter

See [results and interpretation](SUMMARY.md), the [demo/miss report](REPORT.md),
[stress report](STRESS-REPORT.md), [independent audit](AUDIT-REPORT.md) and
[production line counts](LINE-COUNTS.json).

This compares upstream Master, the previous smaller-integration prototype,
and the final private-Font adapter using six balanced blocks per cohort.
The current FemtoVG workspace adopts the smaller implementation and registers
its shared native cache handle with each font. Source is preserved here even
though the application branch has not been committed or submitted as a PR.

`snapshot.tar.gz` contains exact sources, manifests/locks, unchanged benchmark
scenes, fonts/licenses, build provenance, raw output, excluded attempts, process
guards, scripts, analysis, validation and TDD records. Compiled executables and
compiler caches are omitted; executable hashes are recorded in `OMITTED.json`.

Verify and optionally extract with Python 3.12 or later:

```sh
python3 verify.py
python3 verify.py --extract /tmp/femtovg-font-cache-adapter
```

With Rust/Cargo and cached dependencies, rebuild all versions and run fresh
CPU measurements. These commands open no windows:

```sh
cd /tmp/femtovg-font-cache-adapter/bench
python3 build.py
python3 run.py --out runs/new-comparison --blocks 6
python3 analyze.py --out runs/new-comparison
python3 run.py --out runs/new-stress --blocks 6 --cases stress-FleurDeLeah --quiet-seconds 30
python3 analyze.py --out runs/new-stress
```

The main command runs demo Roboto Flex/Vollkorn/Rye, a non-Swash Roboto control,
and all-miss Roboto/Vollkorn size sweeps. The second cohort runs Fleur de Leah
with the [unchanged extreme scene](../demo-current-20261003/raw/stress/harness-src/main.rs).
The [demo drawing source](../demo-current-20261003/raw/scenes/harness-src/demo.rs)
is unchanged as well. Both source files are also retained in the snapshot.

Measured builds/runs and the independent audit were validated in the original
isolated directory. Archive checksums, every retained member and extraction
were verified after packaging. A fresh build from the relocated archive was
not tested. The runner must be able to inspect process names; it stops on
inspection failure or a compiler/build overlap, preserving excluded attempts.

The demo excludes setup and GPU work; the size sweep includes Void flush over
32 frames; stress includes CPU layout/drawing plus Void flush. None measures
application startup. Older Alustin launch results do not apply to this exact
implementation. The small all-miss cost versus Master remains documented.
