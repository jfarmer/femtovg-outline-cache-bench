This harness runs the preserved FemtoVG demo and text example scene adapters
through the public Canvas API with the Void renderer. It measures CPU command
construction and flush cost; it does not measure GPU execution, application
startup, window presentation, or pixels.

`prepare.py` performs source and asset copies only. `harness-src/demo.rs`,
`text.rs`, and `perf_graph.rs` are byte-identical to the archived scene adapters
under `femtovg-outline-cache-bench/vendor/runtime/core/runner/src`. Their original
paths and SHA-256 hashes are in `provenance.json`. These adapters were already
extracted from the interactive examples by that benchmark; this harness does not
claim to execute the window or event-loop code byte-for-byte.

`source/master` is upstream 6a5f15a. `source/final` is the working tree captured
when prepare.py runs. Neither source tree receives production instrumentation.
Per-file hashes and working diff identity are in `source-*.json`. If the working
tree changes later, freeze a new final snapshot and update its manifest and
provenance before building. Do not silently benchmark a stale snapshot.

The default main font is the stock bundled Roboto Flex. Set
`FEMTOVG_REPLAY_TEXT_FONT` to the copied `assets/Vollkorn-Medium.ttf` for the serif
case. Amiri remains the Arabic fallback and Entypo remains the demo icon font.
The unmodified text adapter conditionally loads the host Apple Color Emoji font;
its presence is reported on stderr and must match across paired runs.

Once other timing cohorts have stopped, build each manifest for both
`default_swash` and `default_no_swash`, using the same toolchain and profile.
The scene code requires textlayout and image-loading, so a Swash-only build is
not an appropriate control. JPEG/PNG decoding features are enabled as in the
original runner; font/image loading occurs outside measured frames.

```sh
CARGO_TARGET_DIR=/private/tmp/femtovg-review-fixes-perf/target cargo build --offline --release --manifest-path harness/master/Cargo.toml --features default_swash
CARGO_TARGET_DIR=/private/tmp/femtovg-review-fixes-perf/target cargo build --offline --release --manifest-path harness/final/Cargo.toml --features default_swash
```

Copy each produced binary to a feature-specific filename before rebuilding it
with the other feature configuration. CLI arguments are scene (`all`, `demo`,
or `text`), trials per process (default 1), and DPI (default 1). For example:

```sh
FEMTOVG_REPLAY_TEXT_FONT=/private/tmp/femtovg-review-fixes-scenes/assets/Vollkorn-Medium.ttf ./scenes-final-default_swash all 1 1
```

CSV columns are `scene,phase,trial,frames,draw_us,flush_us,total_us`. Durations
are mean microseconds per frame within that phase. Draw includes set_size and
the original scene.draw; total includes Void flush. First paint is one frame;
warm is 30 frames after 120 initial frames. Text then advances/returns x,
advances y, advances/returns font size, and reflows. Demo zooms in/out and pans.
Those requests match the archived runner's frame trace. These animated phases
retain the original scene's other draw work, including paths, images, strokes,
fallback text and the FPS graph.

For comparisons, use independent rotating/reversing paired process blocks and
retain raw CSV/stdout/stderr plus compiler, source, binary and font hashes. The
shared Cargo target above is only a cache; do not build while a timing cohort is
running. No builds or timings were performed during preparation.
