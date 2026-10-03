This is the preserved 2026-10-03 final glyph-outline-cache verification study.
See [SUMMARY.md](SUMMARY.md) for the comparison and its measured tradeoffs.
This installation is an interim snapshot: warm/generic measurements are complete,
and the eight-block cold reanalysis is explicitly provisional. Demo/text timings
await the user's other build finishing; no further cold run is planned.
Portable build/smoke verification is also pending. See [MANUAL-REVIEW.md](MANUAL-REVIEW.md)
for the code state, actual validation and work remaining. No PR has been created.
The final generic-loop restoration measures the runtime code in commit
`b87a94d`; the retained source records describe the moment each candidate was
frozen. Only two comment lines inside a test module changed after measurement;
`raw/perf/final-runtime-identity.json` records the exact diff, full hashes, and
the byte-identical prefix before that test module. No test logic or released
code changed. Upstream `6a5f15a` is the primary baseline. Earlier candidates and the
ordinary-inline attribution control remain available beside the final results.

All original scripts, source snapshots, Cargo manifests/locks, build logs,
dependency graphs, raw observations, cohort reports and containment traces are
retained under `raw/perf`, `raw/containment`, and `raw/scenes`. Their paths and
metadata are preserved verbatim, including references to the original machine.
No prior benchmark directory or global index was modified. `SHA256SUMS` covers
every retained file except itself. `OMITTED.json` inventories excluded binary
files with sizes and SHA-256 hashes. Compiler/interpreter cache directories are
recorded as directory omissions without traversing or hashing their contents;
excluded symlinks record their target strings without following external files.

`TDD-OBSERVATIONS.md` distinguishes initial tool-output-only red/green evidence
from retained raw logs. No missing console transcript has been reconstructed.
Additional real check logs can be supplied to the installer with `--evidence`.

Portable reproduction uses the bundled frozen sources, never the current
FemtoVG checkout. The wrapper creates a separate fresh workspace and changes
only the copied harness Cargo dependency paths to refer to its source copies.
Rust harness/scene code remains unchanged. Historical source and result metadata
stay immutable. Each build captures Cargo logs, lock/dependency/compiler records,
actual binary hashes and source maps. Build and run are separate steps so no
compiler/linker jobs overlap timings; the runner also checks process names.

```sh
python3 reproduce.py verify
python3 reproduce.py build --group perf --work-dir /tmp/femtovg-study-reproduction
python3 reproduce.py build --group scenes --work-dir /tmp/femtovg-study-reproduction
python3 reproduce.py build --group containment --work-dir /tmp/femtovg-study-reproduction
python3 reproduce.py smoke --group perf --work-dir /tmp/femtovg-study-reproduction --output /tmp/femtovg-perf-smoke
python3 reproduce.py smoke --group scenes --work-dir /tmp/femtovg-study-reproduction --output /tmp/femtovg-scenes-smoke
python3 reproduce.py smoke --group containment --work-dir /tmp/femtovg-study-reproduction --output /tmp/femtovg-containment-smoke
python3 reproduce.py run --kind warm --work-dir /tmp/femtovg-study-reproduction --output /tmp/femtovg-warm-reproduction
python3 reproduce.py run --kind cold --work-dir /tmp/femtovg-study-reproduction --output /tmp/femtovg-cold-reproduction
python3 reproduce.py run --kind generic --work-dir /tmp/femtovg-study-reproduction --output /tmp/femtovg-generic-reproduction
python3 reproduce.py run --kind scenes --work-dir /tmp/femtovg-study-reproduction --output /tmp/femtovg-scenes-reproduction
python3 reproduce.py run --kind containment --work-dir /tmp/femtovg-study-reproduction --output /tmp/femtovg-containment-reproduction
```

Smoke runs check functional completion; any timings printed by the harnesses
are deliberately not treated as performance evidence.

Each group refuses to overwrite an existing workspace; outputs must also be
fresh. Build defaults to offline locked dependencies. On a machine without the
dependencies cached, use `build --online` explicitly. Perf defaults to master
and finalgenericrestore; `build --variants` can select other retained candidates.
Scenes use their independently frozen master/final snapshots. Containment uses
the retained probe-bearing base/current source copies.

Roboto Flex and the required scene assets are bundled. Vollkorn and PT Sans are
copied with their existing benchmark repository licenses under `assets/`; their
paths can be overridden with `run --asset-dir`. Arial is not redistributed.
Supply `run --arial /path/to/Arial.ttf` or `FEMTOVG_ARIAL_FONT` to reproduce those
historical rows, verifying its hash against retained cohort metadata. Without
Arial, warm/cold omit its rows and generic uses Roboto Flex, so those runs are
explicitly a changed font workload rather than an exact replay of Arial rows.
The original scene adapter optionally loads host Apple Color Emoji; its presence
is logged and should match across paired runs.

Run defaults use 12 independent rotating/reversing paired process blocks, 3,000
warm frames or seven cold samples. Raw stdout/stderr are retained without
outlier filtering. Original reports retain the original medians, paired ratios,
absolute costs and exploratory bootstrap intervals. Reproduction retains fresh
raw observations for independent analysis; it never rewrites original reports.

These workloads measure public glyph-run CPU costs and Void flush. Actual demo
and text adapters also include layout, paths, images, strokes, fallback text and
the FPS graph; scene setup is excluded. They measure no GPU execution, display
latency or complete application startup. Containment compares recorded commands,
vertices and atlas state. The preserved GPU check evidence, if supplied, has its
own scope. No finite corpus establishes universal absence of regressions.
