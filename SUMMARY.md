# Submission case and final results

Submit this as a Swash-only optimization for workloads that create new glyph-atlas entries while reusing hinted geometry. The measured application and existing example gains justify review. It is **not an unqualified performance win**: a few warm phases regress slightly, memory is retained, and some GPU and application comparisons are inconclusive.

## Selected implementation

Keep eager caching of hinted outline geometry, keyed by font identity, glyph, exact size and variation coordinates. Subpixel placement is excluded from this key because atlas entries at different placements can reuse that geometry. The nominal cache budget remains **1 MiB**, with clearing at the soft accounting threshold; this is not a total-heap limit.

Reduce misses by creating a native Swash Scaler lazily and reusing it within a compatible glyph run, avoiding redundant generic Path construction through a guarded PNG metadata prepass, and using native `scale_outline_into` with reusable Outline scratch and compact point/verb arenas. The guarded prepass preserves master’s mixed color/bitmap ordering. These changes are internal to FemtoVG: no Swash changes or duplicated hint interpreter are required.

No font-bytecode cutoff or delayed-admission policy is selected. Static hint counts did not establish a reliable decision rule, and complete sequences expose costs that an isolated cache-hit timing can hide. The production choice remains eager caching for the Swash outline path.

## Selected patch versus master

These are median paired changes from the final balanced cohorts. Negative means faster. The full [report](REPORT.md) includes absolute times, paired 95% bootstrap intervals, complete reported sequences, uncertain comparisons and regressions.

| Font | FemtoVG demo first CPU draw | FemtoVG text first CPU draw | Alustin first-render CPU, WGPU | Alustin first-render CPU, OpenGL |
| --- | --- | --- | --- | --- |
| Roboto Flex | −5.4% | −3.8% | −0.8%, inconclusive | −2.5% |
| Vollkorn Medium | −33.0% | −24.0% | −22.6% | −20.5% |
| PT Sans Regular | −14.8% | −9.4% | −4.1%, inconclusive | −6.5% |

Vollkorn also improves first GPU completion by **15.9% in the demo** and **11.9% in the text example**. Several Roboto/PT Sans first-paint GPU intervals span zero. Alustin numbers measure diagnostic renderer-thread CPU work; they do not establish display latency or diagnostics-off startup gains.

The main miss-cost result is the Roboto Flex sequence of **32 unique sizes**: the original cache costs **13.3% more than master**, while the selected patch is **4.6% faster than master**. Directly adding the arena to lazy Scaler reuse and the guarded prepass improves this sequence by **10.4%**. Other one-use and pollution controls are included in the report. Arena’s incremental first-render effect in Alustin remains mostly inconclusive, so it is justified primarily by those directly paired miss controls rather than by an application speedup claim.

## Costs and acceptance argument

Four selected/master warm or movement phases have positive exploratory CPU intervals: **0.2–0.9%**, about **1–2 microseconds** per reported draw. Alustin Roboto/OpenGL search has an uncertain positive estimate. Most process-memory differences are inconclusive; Vollkorn/WGPU peak RSS increases by a paired **0.24 MiB** with a positive interval. The 1 MiB soft cache budget excludes map spare storage, allocator overhead and private native scratch capacities. The patch also adds implementation complexity.

The acceptance case is a substantial reduction in hinted-font outline work, demonstrated in existing FemtoVG scenes and Alustin, together with lower miss costs in controls that penalized the original patch. It preserves master pixels in **504 example**, **144 mixed-color**, and **18 Alustin** comparisons. The selected workspace passes **171 library tests**, formatting, default-without-Swash and Swash-only library checks; the frozen Swash-only suite passes **155 tests**.

This is evidence for the measured workloads and machine, not a universal speedup. The selection is exploratory, its confidence intervals have no multiplicity adjustment, and the extra storage implementation needs maintainer review. Gray8 atlas changes and other rejected prototypes are excluded but their evidence remains preserved.

## Evidence and reproduction

[README.md](README.md) describes offline verification and fresh builds. [REPORT.md](REPORT.md) contains the complete final analysis; [methodology](docs/methodology.md) defines timing, pairing, accounting and correctness checks. The [archive index](results/index.json) retains 22 campaigns, including existing benchmarks, font studies, unsuccessful alternatives, raw observations, frozen source snapshots, locks and provenance. Compiled binaries and compiler caches are explicitly omitted; their recorded identities remain archived.

Master is pinned to `f57a2c39e9836c146556c58c98d80c5bf7899029`, the original eager patch to `7a278ca4f947658d01c355c450edc6abcdbe3958`, and Alustin main to `ac35d4e0b5c52edb7defb9feccdadfd584635c14`. The selected four production Rust files match the final timed snapshot byte-for-byte. Historical cohorts are retained separately rather than pooled into the final comparison.
