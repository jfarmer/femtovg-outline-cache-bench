# Allocation and arena-growth probes

Six alternating Before/PR blocks use the exact frozen production rasterizer
module. Before is `af989d9`; PR is `907bb37`. These are diagnostic workloads,
with allocator-counter overhead, rather than application-speed measurements.

| Workload | Requests | Before allocations | PR allocations |
|---|---:|---:|---:|
| Cached outlines, nonempty variation coordinates | 4096 | 8192 | 4096 |
| Cached outlines, default coordinates | 4096 | 4096 | 4096 |

Borrowing coordinates removes one key allocation per nonempty-coordinate
hit. Each call still allocates its raster image. This did not produce a
clear speedup in the recorded diagnostic timings.

| Near-budget workload | Requests | Capacity changes, Before / PR | Reallocations, Before / PR | Peak entries, Before / PR |
|---|---:|---:|---:|---:|
| Roboto Flex | 4000 | 552 / 38 | 568 / 54 | 3417 / 3331 |
| Vollkorn | 4000 | 636 / 50 | 654 / 68 | 1681 / 1661 |

Capacity changes count both growth and shrink, observed before and after
each render. Intermediate changes inside a render are not individually
observed. Allocator totals include native working and image buffers too.
A reallocation or capacity change does not prove that physical storage moved.

Both versions stayed within the modeled 1 MiB budget. The PR holds slightly
fewer peak entries in these workloads. The borrowed/owned key is eight bytes
larger and its metadata is charged; this combined growth-policy/key comparison
does not isolate the contribution of each change to retention.

The probe shows much less repeated arena allocation, not a CPU speedup from
that policy alone. Raw diagnostic timings and cumulative allocator requested
bytes remain in the results; requested bytes are not retained memory or RSS.

See `runs/probe-final/{PLAN.json,METADATA.json,raw.jsonl,SUMMARY.json}` for
workload settings, source/binary identities, all six blocks, and full counts.
