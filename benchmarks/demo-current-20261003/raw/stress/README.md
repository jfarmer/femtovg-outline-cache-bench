# Public font proof-sheet stress scene

Built and measured on 2026-10-03. The harness calls frozen upstream master `6a5f15a` and proposed released code `b87a94dd` without production instrumentation.

The page draws 66 Latin letters/digits/symbols at logical sizes 14, 20, 28, ten rows per size. The source spaces rows by `0.1 / DPI` logical units.
The headline cohort `paired12-dpi1` uses DPI 1, so shifts 0.0 through 0.9 request up to ten native atlas phase bins. Atlas rasterization with an identity transform uses sizes 14, 20, 28: the DPI shaping scale is divided out of the glyph positions before atlas drawing.
The earlier `paired12-native` cohort uses DPI 2 and therefore roughly five native phase bins. It is retained as a separate control, not pooled into the full-phase results. DPI 2 does not make these native rasterizer sizes 28, 40, 56; the original source comment's device-pixel interpretation only holds at DPI 1.
Both variants and all three fonts report 1,980 glyph requests and 198 glyph-size instances per frame through public TextMetrics. The finite page is 1800 × 1200 logical units.
Public shaping can create ligatures or share glyph IDs, so these actual counts are retained in stdout rather than inferred from the string alone.
No claim of ten actual cache hits per instance is made; the offsets provide up to ten phase-specific bitmap requests sharing post-hint geometry.

Each fresh process registers one font outside timing.
Measured phases are first paint1, warm30, twelve unique size increments of0.1, and return1.
All44frames enter a weighted complete sequence before paired statistics.
The layout, adaptive page width, positive origins, simple paper/panel paths and public fill_text calls are timed along with Void flush.
The framebuffer uses logical page dimensions multiplied by DPR, so wide fonts remain inside a finite visible page.
There are no clips, offscreen culling tricks, GPU measurements or private glyph-cache counters.

Fleur de Leah is the intended high-cost candidate; Roboto Flex and Rye are controls.
These names indicate a selected font range, not proof of maximal hinting cost or a bytecode-complexity correlation.
The workload may create cache pressure; its totals neither isolate hinting nor prove eviction or arena-only benefits.

Build after explicit GO with `python3 build.py --build-ready`.
The builder copies the archived matching Cargo locks and verifies frozen source files, actual library artifacts, feature/dependency graphs and profile.
It uses offline locked opt-level3/no-LTO/16-codegen-unit release builds and the existing dependency cache.
The headline campaign is twelve paired blocks with Fleur de Leah, Roboto Flex and Rye at DPI 1. All 72 processes completed without measured interference; first paint was Fleur 89.304 → 19.936 ms, Rye 51.453 → 12.771 ms, Roboto 4.551 → 3.766 ms.
Reproduce in a coordinated timing window with a fresh output: `python3 run.py --output new-full-phase --blocks 12 --dpi 1 --code-ready`.
The runner rotates font order and alternates variant order, writes PLAN.json before timing, retains every process stdout/stderr, and checks compiler/build/linker names before and after every process.
It aborts rather than filtering timing values on interference.
Intervals are exploratory paired-block percentile bootstraps, 10,000 draws/seed61432, without multiplicity adjustment.

The initial paired12 directory preserves a compiler match during the prestart quiet interval. No benchmark process ran in that attempt. Both completed cohorts retain every measured process with no retries or exclusions. The six-process smoke is separately marked and excluded from campaign statistics.
