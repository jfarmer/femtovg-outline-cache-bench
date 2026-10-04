# Normal-miss fast path

This compares Master `9d574e0`, the cache before these changes (`907bb375`),
and the frozen updated implementation. Only `src/text/swash_rasterizer.rs`
changes, adding 11 net lines. The scaler borrows its context only while
extracting the outline, removing an `Rc` clone on misses. When both arenas
have capacity and the full budget including new metadata fits, insertion
skips growth calculations. Both paths use the same insertion tail; existing
growth, trimming and eviction behavior remains.

FemtoVG demo first-frame CPU drawing time, in milliseconds:

| Font | Master | Before | Updated |
|---|---:|---:|---:|
| Roboto Flex | 1.832 | 1.785 | 1.767 |
| Vollkorn | 7.201 | 5.002 | 5.097 |
| Rye | 7.013 | 4.231 | 4.242 |

Complete 32-frame all-miss workloads, in milliseconds:

| Font | Master | Before | Updated |
|---|---:|---:|---:|
| Roboto Flex | 5.895 | 5.984 | 5.962 |
| Vollkorn | 47.703 | 47.883 | 47.695 |

Fleur de Leah stress scene, in milliseconds:

| Workload | Master | Before | Updated |
|---|---:|---:|---:|
| First frame | 94.841 | 20.822 | 21.430 |
| Complete 44-frame sequence | 1257.525 | 303.075 | 301.262 |

Roboto's all-miss paired change is **−1.48% versus Before**, with an exploratory
95% interval of **−2.79% to +0.93%**. Versus Master it is **+1.21%**, with an
interval of **−1.59% to +1.77%**. These are medians of within-block changes,
not ratios of the table's independent medians. The small gain is suggestive;
the intervals cross zero. Comparing the earlier run's roughly 3% overhead
with this run's roughly 1% estimate would not establish a causal improvement.

The substantial Vollkorn, Rye and Fleur savings versus Master remain.
No Updated-versus-Before interval lies wholly above zero, but six blocks
cannot establish universal equivalence or improvement. The [full report](REPORT.md)
and [statistics](SUMMARY.json) include every phase and the non-Swash control.

All **198 / 182 / 170** library tests passed with default + Swash, Swash-only
and default without Swash; formatting passed. See [test evidence](validation/RESULTS.json).
The benchmark accepted six balanced blocks, **126 processes and 486 records**,
with no excluded attempts or matched build-process guards. CPU drawing uses
the Void renderer; miss and stress timings include Void flush. Font loading,
canvas creation and GPU work are excluded. No GPU or Alustin timings were added.

[Reproduction](README.md), [source freeze](SOURCE_FREEZE.json),
[source diff](after-vs-before.diff) and [raw records](runs/comparison/raw.jsonl)
retain the exact implementation and unchanged scenes. Earlier studies remain
intact and are not pooled with this run.
