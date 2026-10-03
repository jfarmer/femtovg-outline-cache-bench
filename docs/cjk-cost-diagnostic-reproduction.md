# Swash cost decomposition

This is a separate causal diagnostic, not another application-performance
confirmation. Its inputs and protocol were frozen before measurement. The
default-font cohort remains unchanged, and the explicit-weight cohort has its
own source, binaries, selection, and untimed coordinate/correctness proof.

The serial driver runs ten default-font processes, followed by eight Noto
weight-300/400 processes. Each process measures twenty cases (two text profiles,
five logical sizes, and DPR 1/2), with six complete Williams-order trials and
twenty repeats. The diagnostic emits 12,960 raw timing rows in total. These are
protocol counts, not a statement that a particular run completed.

```sh
python3 -B /private/tmp/femtovg-cjk-font-search-20261002/run_cost_decomposition.py \
  --output /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1
```

The output must be fresh. `campaign-plan.json` records both serial cohorts and
their actual exit status. Failed attempts remain preserved. The driver does not
run analysis or silently resume partial outputs.

| Kernel | Timed work |
| --- | --- |
| `builder_only` | Build and drop one hinted scaler per glyph iteration using a warm, shared `ScaleContext`; do not decode an outline. |
| `rebuild_and_outline` | Build and drop one hinted scaler per glyph iteration, then decode into a reused `Outline`. |
| `prepared_hinted` | Decode hinted outlines using one scaler prepared before the timer. |
| `prepared_unhinted` | Decode unhinted outlines using one scaler prepared before the timer. |
| `native_render` | Render alpha images with a prepared hinted scaler, cycling ten x offsets. |
| `geometry_reuse` | Look up retained hinted outlines and rasterize alpha images, cycling the same offsets. |

Every kernel creates its context and performs its own warmup outside the timer.
The prepared kernels exclude scaler construction. Outline buffers and raster
scratch are reused. Before measurement, each case checks rebuilt/prepared
geometry exactly and compares native/reused placement and alpha bytes at all ten
x offsets. Thus `geometry_reuse` measures the standalone retained-outline
operation; it does not include FemtoVG's cache keys, budget checks, atlas, or
scene traversal. The kernels are separate measurements, so subtracting their
medians provides an estimate rather than an exact additive accounting.

The default cohort passes `normalized_coords(&[])`. The explicit-weight cohort
uses Swash's public `font.variations().normalized_coords` API once before every
case and timer, and passes the resulting slice to every scaler and correctness
check. It retains the actual weight and normalized coordinates in all raw rows
and provenance. The separately frozen untimed checks established:

| Font | Weight 300 | Weight 400 |
| --- | --- | --- |
| Noto Sans SC | `[2621]` | `[6390]` |
| Noto Serif SC | `[1556]` | `[3441]` |

These supplement the default Noto instances because the demo uses explicit
weight requests. They isolate construction, outline, and raster costs at those
instances; they do not reproduce the application's entire sequence of sizes,
glyphs, variation changes, or cache outcomes. Production counter traces are the
separate evidence for that sequence. Noto Serif SC weight 300 differs by one
2.14 fixed-point coordinate step: this screen's public Swash normalization is
`[1556]`, whereas the production trace has `[1555]`. That case is a nearby
instance, not an exact production replay. The other supplemental vectors match
the production trace.

After timing ends, independent source readers can check the original live
binary, source, dependencies, launch order, raw rows, normalization fields,
geometry/image assertion bindings, and arithmetic, and derive per-case medians:

```sh
python3 -B /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-screen/audit_cost_screens.py \
  --screen en /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/default/en \
  --screen ko /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/default/ko \
  --screen zh /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/default/zh \
  --output /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/default/independent-audit.json
python3 -B /private/tmp/femtovg-cjk-font-search-20261002/mechanism-weight-cost-screen/audit_weight_cost_screens.py \
  --screen en-w300 /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/weights/en-w300 \
  --screen en-w400 /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/weights/en-w400 \
  --screen zh-w300 /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/weights/zh-w300 \
  --screen zh-w400 /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/weights/zh-w400 \
  --output /private/tmp/femtovg-cjk-font-search-20261002/mechanism-cost-timing-v1/weights/independent-audit.json
```

Use distinct weighted screen labels as above, so weights cannot be pooled. The
readers never run a renderer. `--path-map` and explicit
`--allow-missing-binaries` support restored archives while reporting omitted
executables and their original SHA-256 identities. Digest checks bind the
successful Rust assertions; the readers do not regenerate pixels from a digest.
There are no bootstrap confidence intervals or application-percentage claims
in this diagnostic.
