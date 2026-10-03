# Smaller integration: results

The simpler version removes 146 lines of production code, reducing the added production code from 439 to 293 lines relative to master. It uses the original atlas loop and a private per-glyph cache API. It keeps the arena, reusable buffers, classification shortcut and rendering fixes.

It preserves the demo gains, but is slower than master in the two 32-size workloads dominated by misses. This is a tradeoff, not a performance-neutral simplification. The current implementation is unchanged.

| CPU workload | Master | Current | Simpler |
|---|---:|---:|---:|
| Demo: RobotoFlex | 1.802 ms | 1.681 ms | 1.744 ms |
| Demo: Rye | 6.788 ms | 4.154 ms | 4.078 ms |
| Demo: Vollkorn | 6.919 ms | 4.841 ms | 4.875 ms |
| 32 unique sizes: RobotoFlex | 5.695 ms | 5.329 ms | 5.871 ms |
| 32 unique sizes: Vollkorn | 46.609 ms | 46.567 ms | 47.103 ms |

The Roboto size sweep draws 94 glyphs at each of 32 sizes (3,008 requests). Its paired slowdown versus master is 3.27%, with a 95% exploratory interval of 2.99% to 4.56%. Vollkorn is 1.38% slower, with an interval of 0.13% to 1.90%. The demo first-draw differences between the two cache versions are inconclusive in this run.

Both cache versions skip scaler construction on outline hits. The current version also reuses the scaler across misses in a compatible run; the simpler version builds one for every miss. The experiment removes both run reuse and the separate atlas loop together, so it does not establish that a second loop is needed. It supports preserving scaler reuse if avoiding the miss-heavy slowdowns is a requirement.

The no-Swash Roboto demo control shows no clear warm/zoom/pan slowdown. The warm-frame difference versus master is +2.25%, with an interval spanning zero. A faster first draw with Swash disabled cannot be attributed to the outline cache.

All 12 blocks completed, balancing all six version orders twice. There were 864 accepted measurements and no build-process matches during the timings. A sandbox process-inspection failure before timing is retained. Demo CPU drawing is measured at DPI 2; the miss controls include draw and Void flush at DPI 1. Setup, GPU work and whole-app startup are excluded.

Validation: 186 library tests passed with Swash, 169 with Swash only, 163 with default features; no-default-feature library check and formatting passed. Cached-hit context borrowing was tested red then green. The API constructs its scaler from the same arguments used for its cache key.

Master is `6a5f15ae55db439a4ed8b1e818c6521029c34fbd`. Current is `b87a94ddfba46ee67ca35ba240104615ac1503d8` plus the encapsulation edits recorded in `full-workspace.diff`. Simpler starts from exactly Current; `prototype.diff` records the experiment. Exact sources, scripts, inputs, raw outputs, source/binary hashes, line-count method and analysis are retained in the snapshot archive. Compiled binaries and compiler caches are omitted.

This is a narrow engineering comparison. It does not prove universal absence of regressions or replace the original demo and stress results. No FemtoVG PR was created.
