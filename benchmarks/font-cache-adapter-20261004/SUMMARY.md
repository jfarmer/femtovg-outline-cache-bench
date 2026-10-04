# Private Font cache adapter

The smaller cache is now integrated behind FemtoVG's existing private `Font` API.
Font registration attaches an optional native face identity and an opaque handle
to the text context's shared rasterizer. The atlas asks the font for an owned image;
it no longer obtains or borrows the cache itself. Swash-only generic paths use the
same native scaling context. No public API, dependency or Swash change is required.

One cache and its 1 MiB soft accounting budget remain shared per text context.
The arena, admission/growth policy, working buffers, source routing, bitmap uploads,
negative-position fixes and error restoration are preserved. Cache hits do not
construct a scaler, clone a handle or allocate a new cache. Different sizes and
variation coordinates remain distinct keys; subpixel phases reuse hinted geometry.

This adopts the previously measured simpler implementation: one existing atlas
loop and a scaler built per cache miss, rather than native run segmentation.
The Font adapter is 41 additional physical production lines compared with that
prototype. The final implementation adds 334 net production lines over Master,
105 fewer than the larger implementation. Counts exclude tests, comments and
blank lines; attributes and braces count. See [line counts](LINE-COUNTS.json).

## Exact-version CPU measurements

Master is upstream `6a5f15a`. Simple is the frozen prototype from the
[previous smaller-integration study](../lower-touch-20261003/SUMMARY.md).
PR is the exact uncommitted private-Font adapter snapshot preserved here.
Each cohort uses six blocks containing all six permutations of the three variants.
The stress cohort uses the same Fleur de Leah scene as the prior stress study.
These are fresh comparisons, not pooled with earlier measurements.

Demo first-paint CPU drawing, in milliseconds, from FemtoVG's existing demo:

| Font | Master | Previous simple | PR |
|---|---:|---:|---:|
| RobotoFlex | 1.965 | 1.922 | 1.839 |
| Vollkorn | 7.368 | 5.136 | 4.969 |
| Rye | 6.963 | 4.262 | 4.287 |

Fleur de Leah stress demo, in milliseconds:

| Workload | Master | Previous simple | PR |
|---|---:|---:|---:|
| First frame | 95.422 | 21.084 | 20.786 |
| Mean frame while changing sizes | 96.885 | 22.894 | 23.025 |
| Complete 44-frame sequence | 1268.191 | 301.101 | 301.649 |

The stress scene requests 1,980 glyphs per frame: 66 characters at three sizes,
with ten rows at different fractional horizontal positions for each size.
It then draws warm frames and changes sizes. Every version has the same actual
request counts and visible scene. The cache avoids repeating the hinting work
when a glyph at one size needs another subpixel mask. It still rasterizes each mask.

The wrapper showed no clear added cost over the previously measured simple
implementation in this matrix. For the full Fleur sequence, its paired change
was +0.013%, with an exploratory 95% block-bootstrap interval of -1.05% to +1.61%.
This is a narrow check of the ownership change, not proof of universal equivalence.

## Miss costs and scope

When every glyph/size request misses, the smaller implementation still pays a
small cost relative to Master. The complete 32-size workloads, in milliseconds:

| Font | Master | Previous simple | PR |
|---|---:|---:|---:|
| RobotoFlex | 6.074 | 6.162 | 6.175 |
| Vollkorn | 48.260 | 49.083 | 50.111 |

Vollkorn's paired PR-versus-Master increase is +2.21%, with an exploratory
95% interval of +1.38% to +4.29%; Roboto's interval crosses zero. Paired statistics
summarize changes within each block and need not equal the ratio of independent
column medians. The PR cannot claim that nothing becomes slower. This tradeoff
was present in the smaller implementation before moving ownership into Font.

The non-Swash Roboto first-paint control is 4.305 ms on Master and 4.263 ms with
the PR; its paired interval crosses zero. Tests cover strokes, direct paths,
generic fallback, color sources, placements and render-target error recovery.
No Alustin launch timing was collected for this smaller implementation or wrapper;
older launch measurements must not be described as this exact patch's results.
The earlier PR drafts describe the larger version and need revision before use.

## Validation and retained evidence

The main cohort contains 108 accepted processes and no interrupted attempts.
The stress cohort contains 18 accepted processes; three compiler-interrupted
attempts were excluded in full and retained. Process-name checks run before,
every 0.1 seconds during, and after each process. A 30-second quiet interval was
used after recurring short compiler runs. No window was opened.

These are CPU measurements on M4 Max/macOS. Demo numbers cover drawing at DPI 2;
miss-workload numbers include Void flush across 32 frames; stress numbers cover
layout/drawing plus Void flush at DPI 1. Setup, asset loading, GPU rendering and
application startup are excluded. Warm and other phases remain in the detailed
reports. Six-block intervals are exploratory.

The independent audit reconstructed all 486 accepted rows, 27 summaries and 81
contrasts from retained stdout with exact agreement, and checked source, harness,
assets, manifests, locks, binaries, ordering, exclusions and production counts.
See [audit](AUDIT.json), [demo/miss report](REPORT.md) and
[stress report](STRESS-REPORT.md). The snapshot includes exact source trees,
raw output, guards, scripts, assets/licenses, TDD records and validation metadata.

Library tests passed: 187 with default features plus Swash, 171 with Swash alone,
and 163 with defaults without Swash. The no-default-feature library check,
formatting and diff checks passed. New ownership tests were written before their
APIs, failed to compile for the missing APIs, and passed after implementation.
Existing rendering and cache-policy regression coverage is retained.

The FemtoVG source remains uncommitted for manual review. No PR was created.
