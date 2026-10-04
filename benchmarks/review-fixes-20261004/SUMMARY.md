# Final cache review fixes

This compares upstream Master `9d574e0`, the cache before these fixes
(`af989d9`), and the committed PR code (`907bb37`). Earlier studies keep
their original baselines and results; they are not pooled with this run.

The cache remains behind the private Font API. Near its budget, arena
growth now retains headroom instead of repeatedly reserving one outline.
Variable-coordinate lookups borrow their key; coordinates are copied only
when admitting an outline. Related atlas fixes preserve live layers and
skip genuinely blank paths. Generic atlas target changes stay batched per
run. See [scope and TDD evidence](REVIEW_FIXES.md) and the
[public API review](API_REVIEW.md); no public API changed.

CPU drawing time for the first frame of FemtoVG’s existing demo, in milliseconds:

| Font | Master | Before fixes | PR |
|---|---:|---:|---:|
| RobotoFlex | 1.711 | 1.722 | 1.712 |
| Vollkorn | 7.170 | 4.996 | 4.983 |
| Rye | 7.004 | 4.269 | 4.288 |
| RobotoFlex, Swash disabled | 4.217 | 4.389 | 4.059 |

RobotoFlex’s demo first frame shows no clear change; its paired interval
crosses zero. The demo savings for Vollkorn and Rye remain substantial.
The non-Swash control also has an interval crossing zero.

The same extreme Fleur de Leah scene, in milliseconds:

| Workload | Master | Before fixes | PR |
|---|---:|---:|---:|
| First frame | 94.627 | 21.632 | 21.572 |
| Mean frame while changing sizes | 95.099 | 22.775 | 22.757 |
| Complete 44-frame sequence | 1240.644 | 302.261 | 299.714 |

The complete 32-size all-miss controls, in milliseconds:

| Font | Master | Before fixes | PR |
|---|---:|---:|---:|
| RobotoFlex | 5.998 | 6.161 | 6.178 |
| Vollkorn | 48.637 | 48.806 | 49.034 |

When every request misses, RobotoFlex takes 3.27% more CPU time
than Master (exploratory paired 95% interval: +2.60% to +7.03%).
Vollkorn’s all-miss interval crosses zero. This is not a universal speedup.

These are CPU measurements with the Void renderer. They exclude application
startup, font loading and GPU work. The demo has warm, pan and zoom phases
in the [full report](REPORT.md), including a non-Swash control. The
[stress report](STRESS-REPORT.md) retains all phases. Six balanced blocks
per cohort cover all three-version orders. Paired intervals in the JSON
reports are exploratory; the controls do not prove universal equivalence.

The [separate allocation probe](PROBE-REPORT.md) exercises nonempty
variation coordinates and near-budget workloads. It counts allocator
calls and observed capacity changes, including shrink. Output images
still allocate, and a capacity change does not prove memory physically moved.
Its instrumented timings are not application-speed claims.

Exact sources, locked dependencies, unchanged scenes, fonts/licenses,
scripts, guards, raw accepted and excluded attempts, test evidence and
[independent audit](AUDIT-REPORT.md) are retained. Compiled executables
and target caches are omitted; their recorded identities remain available.
No Alustin launch timing applies to this exact version. No FemtoVG PR
has been created.
