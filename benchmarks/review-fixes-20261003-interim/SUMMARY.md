The final cache fixes substantially remove the original warm regression, with
small measured costs remaining outside native fills. A separate post hoc
provisional analysis of the earliest cold campaign's eight complete blocks
supports broad cold benefits across all 66 configurations. Actual demo/text
scene timing remains paused until the user confirms the external project's
ongoing build has finished; a quiet gap is insufficient. Another cold run is
not planned unless a meaningful new concern appears.

The primary baseline is exact upstream 6a5f15a; da26832 is an attribution
control. Immutable finalgenericrestore production bytes match measured commit
7b42f52. Root's later single commit changes two comments inside cfg(test), with
release-prefix identity recorded separately. Frozen measured sources remain
unchanged.

The primary warm/generic cohorts use 12 rotating independent paired process blocks,
release opt-level 3, no LTO, 16 codegen units, no incremental compilation,
rustc 1.96.0 / LLVM 22.1.2 on aarch64 macOS. Dependency/feature graphs match
between candidates. Compiler artifacts prove the frozen library manifest;
source, executable, harness and font hashes are recorded. These are CPU
Canvas/Void measurements, not GPU or presented frame timing.

Representative completed measurements:

| Features and workload | Master ns/glyph | Final ns/glyph | Master µs/frame | Final µs/frame | Paired delta µs/frame [exploratory 95% interval] |
|---|---:|---:|---:|---:|---|
| default+Swash, warm Roboto Flex paragraph | 56.02 | 51.47 | 102.86 | 94.50 | −8.09 [−9.24, −7.73] |
| Swash only, warm Arial paragraph | 52.05 | 48.90 | 95.56 | 89.77 | −5.76 [−6.30, −5.37] |
| Swash only, warm Arial labels | 87.99 | 89.09 | 29.92 | 30.29 | +0.36 [−0.11, +0.85] |
| default without Swash, warm positive Arial paragraph fill | 48.61 | 50.19 | 89.25 | 92.15 | +2.42 [+1.83, +3.35] |
| default without Swash, warm positive Arial paragraph stroke | 48.64 | 50.02 | 89.31 | 91.83 | +2.35 [+1.96, +3.08] |
| default+Swash, warm centered-negative Arial label stroke | 108.94 | 111.46 | 37.04 | 37.90 | +0.83 [+0.42, +1.29] |
| default without Swash, cold positive Arial label fill | 4798.35 | 4896.07 | 1631.44 | 1664.67 | +32.19 [−0.42, +73.79] |
| Swash only, cold centered-negative Arial paragraph stroke | 493.07 | 501.97 | 905.27 | 921.60 | +16.25 [+0.94, +26.35] |

Warm native paragraphs save 4.46–8.09 µs/frame in the four measured cases;
three of four labels save 0.44–1.46 µs/frame. Swash-only Arial labels have a
small inconclusive cost. Every da26832 warm control is slower than master,
adding 2.23–13.79 µs/frame. The earlier ordinary-inline variant still regresses
in warm fills; that intervention was measured on the previous frozen candidate,
not rerun on finalgenericrestore. It supports keeping inline(always) for the
observed compiler/profile, without proving it universally necessary.

Generic warm labels without Swash are near neutral. The four non-Swash warm
paragraph controls add 1.31–2.42 µs/frame with intervals above zero. Swash
generic label strokes add 0.38–0.83 µs/frame; paragraph strokes are neutral or
faster. Generic cold controls mostly have wide intervals spanning zero, with
the displayed Swash-only negative paragraph stroke exception. Negative runs
are centered to straddle zero and can have different clipping than positive
runs; compare each final row only with the same master positions.

Intervals resample whole paired blocks 10,000 times using the median and a
fixed seed. They are exploratory and have no multiplicity adjustment. Paired
median deltas need not equal the difference of marginal master/final medians.
Full rows, raw observations and absolute intervals are in
warm-genericrestore and generic-genericrestore. An independent analyzer
verified all 288 warm records/24 summary rows and 768 generic records/64 rows.

Incomplete cold-genericrestore, cold-genericrestore-clean,
cold-genericrestore-quiet, and cold-genericrestore-final retain their original
excluded status because process-name guards detected external Cargo/build
activity. Their original EXCLUDED.md, metadata and raw records remain immutable.
No observations are merged into a replacement cohort. A later
origin check confirms actual Cargo build plus rustc compile activity; known
PIDs were inspected privately to classify command families, and only family,
PID, comm, and parent names were retained. No command arguments or environment
were persisted. Guard policy remains strict.

The separate provisional-cold-audit selected the chronologically earliest
campaign and all of its complete blocks 0–7, after the campaign had stopped
and before that numerical reanalysis. It uses the full 66-configuration ×
three-variant × eight-block matrix: 1,584 process records. The 174 records from
partial block 8 and every later interrupted campaign are excluded from this
analysis. No records were selected or combined using their measured effects.
The original planned twelve-block cold campaign remains incomplete; this is
explicitly post hoc provisional evidence, not the planned primary cohort.

The independent analyzer verified all 198 rows and all six executable/four
font/four harness hashes, emitted metric identities and command arguments.
The separate provisional-cold-provenance check also verified the full matrix
and chronological rotation, source origins, production file hashes, matching
dependency/feature graphs and compiler/profile, complete-sequence totals, and
the unchanged original artifacts. All 66 final/master paired point estimates
favor the candidate; 63 exploratory intervals lie below parity and three cross
it. This supports the broad cold benefit on the measured corpus, without
claiming every row has a conclusive win.

Representative provisional cold results below use default+Swash and complete
sequence costs. Pure-miss controls retain all population work; the pollution
sequence includes two hot population frames, 64 size changes and the hot
return. It measures pressure and return together, without proving that cache
eviction occurred.

| Cold workload/font | Frames/sequence | Master µs/sequence | Final µs/sequence | Paired delta µs/sequence [exploratory 95% interval] |
|---|---:|---:|---:|---|
| Natural labels, Roboto Flex | 1 | 335.000 | 230.562 | −102.021 [−125.875, −91.750] |
| Rounded single-phase labels, Roboto Flex | 1 | 166.500 | 119.291 | −45.980 [−52.417, −20.084] |
| 94 unique glyphs, one phase, Roboto Flex | 1 | 189.646 | 127.292 | −55.354 [−64.333, −50.374] |
| 32 unique sizes, Roboto Flex | 32 | 5,855.500 | 5,495.020 | −350.291 [−427.334, −324.833] |
| 32 unique sizes, Vollkorn | 32 | 47,537.146 | 47,552.688 | −252.021 [−365.917, +507.625] |
| 32 unique normalized weights, Roboto Flex | 32 | 7,894.812 | 5,487.709 | −2,443.854 [−2,479.667, −2,332.958] |
| Complete pollution/return, PT Sans | 67 | 26,397.041 | 25,372.021 | −964.021 [−1,748.000, −947.749] |
| Complete pollution/return, Arial | 67 | 31,693.104 | 30,767.979 | −858.645 [−1,404.459, −782.917] |

The most uncertain row is default+Swash/Vollkorn's 32-size sweep: its paired
per-frame delta is −7.876 µs [−11.435, +15.863], while its marginal median final
total is slightly larger. Paired statistics compare within each block and
need not equal differences between marginal medians. The other two
inconclusive rows are default+Swash/Arial rounded labels and paragraphs,
with per-frame intervals −34.167 to +9.042 µs and −39.708 to +4.750 µs.

Provisional intervals resample eight whole paired blocks 10,000 times. The
original guard checked before configurations, not continuously or after every
process, so a later detected build neither establishes earlier idle conditions
nor invalidates every earlier observation. The user later confirmed that the
external build remained running. Individual seven-sample observations were
not emitted. One machine, exploratory intervals without multiplicity
adjustment, CPU public glyph drawing and Void flush only; layout/GPU/window
work is excluded. These limits justify the provisional label and retaining
the actual-scene check, rather than requiring another whole cold cohort.

No retry cohort or actual-scene timing has started. Four feature-specific
scene binaries are built and their source origins, dependency graphs,
compiler/profile, binary and asset hashes are prepared. The remaining planned
timing covers Roboto Flex and Vollkorn in both demo and text scenes, including
first paint, warm drawing, movement, resizing and reflow. RETRY_PLAN.json and
the archived runners retain a future cold reproduction option, while the
next planned cohort is scenes only: 12 complete accepted logical blocks,
guards around every process, all attempts retained, and whole-block replay
after 60 quiet seconds on environmental guard matches. Replay is bounded
by 30 retries/30 minutes and excludes no observation based on its timing value.
