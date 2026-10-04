# Smaller integration on the extreme hinting demo

The smaller cache keeps nearly all the large savings in this stress scene. It uses the original atlas loop and builds a scaler per outline miss, while retaining the arena and geometry reuse. The three source snapshots are identical to those in the preceding smaller-integration experiment.

First frame, CPU layout/drawing plus Void flush at DPI 1:

| Font | Master | Current | Simpler |
|---|---:|---:|---:|
| Fleur de Leah | 90.256 ms | 20.183 ms | 20.504 ms |
| Rye | 52.129 ms | 13.078 ms | 13.380 ms |
| Roboto Flex | 4.705 ms | 3.966 ms | 4.001 ms |

Average frame while changing the font sizes:

| Font | Master | Current | Simpler |
|---|---:|---:|---:|
| Fleur de Leah | 91.617 ms | 21.734 ms | 21.740 ms |
| Rye | 52.772 ms | 13.767 ms | 13.926 ms |
| Roboto Flex | 5.101 ms | 4.207 ms | 4.302 ms |

Compared with the current cache, the smaller version has a small first-frame penalty for Fleur de Leah and Rye: paired medians of +2.25% and +2.24%, with exploratory 95% intervals of +0.82% to +3.66% and +0.11% to +3.16%. During size changes Fleur shows no clear difference, while Rye is +0.94% slower (+0.50% to +1.98%). Roboto first-frame and size-change differences are inconclusive.

The scene draws 66 characters at three sizes in ten fractionally shifted rows. Every version and block reports the same 1,980 shaped glyph requests, 198 distinct glyph/size instances, 30 text draws, and 1,800 by 1,200 viewport. Both cache versions can reuse hinted geometry across fractional positions, so they retain the dominant benefit. The smaller version only gives up reuse of a scaler while populating uncached outlines. Exact cache-hit and scaler-build counts are not instrumented.

This differs from the previous 32-size miss control: that control requests each glyph/size only once, so cached geometry cannot help its measured requests. The smaller version was 3.27% slower than master there for Roboto and 1.38% slower for Vollkorn. The stress result preserves the favorable-case benefit; it does not remove that miss-heavy tradeoff.

All 12 balanced blocks completed using each of the six version orders twice. There were 108 successful processes, 432 directly timed phase observations and 108 derived complete-sequence totals; no interrupted blocks or build-process matches. Setup, font loading, GPU work and application startup are excluded. All 44 frames contribute to the reported complete sequence. The drawing source and font bytes are unchanged from the earlier archived stress scene.

Master is `6a5f15ae55db439a4ed8b1e818c6521029c34fbd`. Current is `b87a94ddfba46ee67ca35ba240104615ac1503d8` plus the previous encapsulation edits; Simpler is the exact prototype from the preceding experiment. Exact sources, inputs, scripts, raw outputs, licenses, build identities and analysis are retained in the snapshot archive. The FemtoVG branch remains unchanged; no PR was created.
