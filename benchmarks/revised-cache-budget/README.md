This additive CPU control targets admission near the nominal 1 MiB cache budget.
It preserves the existing replay and application suites unchanged. It does not
claim application latency or infer outline-cache hits from rendering requests.

Each trial and key count gets a fresh shared TextContext and font registration.
Ten fresh Canvas instances use that context, preserving the outline cache while
giving every phase a fresh outer glyph atlas. All calls use public
`Canvas::fill_glyph_run`, at DPI 1 with 94 distinct nonspace ASCII glyphs and
integer sizes beginning at 12. The final partial group gives exactly 3,300,
3,440, or 3,600 geometry keys. Sizes never exceed 50, staying on the atlas route.
The phase offsets are 0.0 through 0.9. Requests/font registration and Canvas
creation/destruction are excluded; every glyph-run draw and flush is included.
Whole-sequence totals include the population phase and all nine reuse phases.

This models cache sharing across fresh atlases or canvases, deliberately near a
budget boundary. The 3,440-key fitting condition came from a Roboto Flex observer;
it is a targeted synthetic stress case, not a claim that every application or
font has this working set. A separate untimed observer should establish actual
outline hits/clears if those mechanisms are reported.

`prepare` copies frozen sources without editing them. Timing copies differ only
in the four existing Void black_box barriers. Separate audit copies also record
padded upload-data and vertex FNV64 digests; timing copies contain no observer.
The four root packages have distinct names to avoid prior root-package reuse
mistakes. Builds are offline, fresh from the copied sources, pin Swash 0.2.10 and
require identical resolved dependency/features graphs across variants. A CPU
build never opens a window. Parent orchestration must keep builds, analysis,
compression and other benchmarks out of timed intervals.

Example sequence, substituting the four actual frozen source paths:

```sh
python3 bench.py prepare --output RUN_DIRECTORY \
  --source master MASTER_SOURCE --source prior PRIOR_SOURCE \
  --source updated45 UPDATED45_SOURCE --source final FINAL_SOURCE
python3 bench.py build --root RUN_DIRECTORY --kind timing
python3 bench.py build --root RUN_DIRECTORY --kind audit
python3 bench.py run --root RUN_DIRECTORY --kind audit --font ROBOTO_FILE --output AUDIT_DIRECTORY
python3 bench.py analyze --root AUDIT_DIRECTORY
python3 bench.py run --root RUN_DIRECTORY --kind timing --font ROBOTO_FILE --output TIMING_DIRECTORY --blocks 12 --trials 5
python3 bench.py analyze --root TIMING_DIRECTORY --bootstrap 10000
```

All four versions are freshly timed in 12 balanced Williams blocks. Each process
has five trials. Phase sums are formed within each trial before process medians;
versions are then paired within blocks. All valid raw observations remain. The
95% whole-block bootstrap intervals are exploratory, without multiplicity or
implementation-selection adjustments. Audit digests compare candidate uploads
and vertices to master, not complete GPU RGBA images or exact byte streams.

No build or benchmark was run while authoring these files.


This directory is a reproduction-only adaptation made after measurement. The
original measured driver and its provenance remain in the archive. Its scene,
timing, audit sink, launch order, and statistical code are unchanged here.

Preparation copies the exact eight measured Cargo.lock files from
`measured-locks/`, verifies their pinned hashes, and records their hashes in the
prepared manifests. Build never generates or updates lockfiles: both metadata
and compilation use `--offline --locked` and fail if an input lockfile is absent
or changed. An offline reproduction requires the measured dependency versions
to be present in the local Cargo cache; it cannot substitute newer versions.

`adaptation.json` records the original and reproduction source hashes.
`measured-locks/provenance.json` links every lockfile to its measured binary and
metadata. `validation.json` records preparation and metadata-only checks; no
new benchmark observations were collected for this adaptation.
