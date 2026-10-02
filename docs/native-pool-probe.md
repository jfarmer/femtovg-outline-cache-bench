# Untimed native-outline pool comparison

Six isolated CPU-only launches produced 54 endpoint observations. Each endpoint starts from a fresh rasterizer and shared ScaleContext, then replays all requests through the named phase. There are no clocks or GPU work. All 27 arena/pool prefix coverage digests agree; full RGBA preflight is separate.

The owned-heap figure is the requested Rust heap released when the rasterizer alone is dropped, after each output image has been dropped and while font data and the external shared ScaleContext remain alive. It includes hash-map buckets, Zeno scratch, and native Outline private buffers; it excludes shared font preparation, allocator metadata and physical memory/RSS.

Both implementations use a 1 MiB soft budget, with different accounting rules. Actual heap retention and admission are therefore measured rather than assumed equivalent.

| Font | Endpoint | Prefix frames | Alloc calls arena → pool | Rasterizer-owned requested bytes arena → pool | Cached entries arena → pool | Free outlines pool | Cache clears arena → pool |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| stock | grid_singleton/once | 1 | 144 → 799 | 41,432 → 72,192 | 94 → 94 | 0 | 0 → 0 |
| stock | grid_two_phases/second | 2 | 238 → 893 | 41,432 → 72,192 | 94 → 94 | 0 | 0 → 0 |
| stock | grid_unique_sizes/sweep | 32 | 3,135 → 24,022 | 1,033,832 → 2,273,456 | 3,008 → 147 | 2,470 | 0 → 1 |
| stock | grid_pollution/hot_return | 67 | 6,459 → 37,433 | 1,033,928 → 2,005,216 | 3,064 → 842 | 856 | 1 → 2 |
| vollkorn | grid_singleton/once | 1 | 245 → 1,139 | 113,432 → 115,992 | 94 → 94 | 0 | 0 → 0 |
| vollkorn | grid_two_phases/second | 2 | 339 → 1,233 | 113,432 → 115,992 | 94 → 94 | 0 | 0 → 0 |
| vollkorn | grid_unique_sizes/sweep | 32 | 6,166 → 24,947 | 906,920 → 1,847,808 | 317 → 170 | 1,045 | 2 → 2 |
| vollkorn | grid_pollution/hot_return | 67 | 12,686 → 38,045 | 907,016 → 1,628,200 | 817 → 903 | 22 | 4 → 4 |
| ptsans | grid_singleton/once | 1 | 149 → 850 | 68,360 → 81,424 | 94 → 94 | 0 | 0 → 0 |
| ptsans | grid_two_phases/second | 2 | 243 → 944 | 68,360 → 81,424 | 94 → 94 | 0 | 0 → 0 |
| ptsans | grid_unique_sizes/sweep | 32 | 3,153 → 22,816 | 1,108,632 → 2,068,504 | 306 → 568 | 1,133 | 1 → 1 |
| ptsans | grid_pollution/hot_return | 67 | 6,477 → 39,964 | 1,108,712 → 1,851,952 | 800 → 1,687 | 0 | 2 → 2 |

The 32-weight Roboto Flex control has 6,158 → 26,914 allocation calls, 1,037,528 → 2,252,576 owned requested bytes, and 3,008 → 178 cached entries. As in the main replay, the variation control always uses Roboto Flex; the Vollkorn and PT Sans configurations repeat this same control.

All two-phase controls preserve 94 second-phase hits and request no second-phase Scaler setup. Size and weight sweeps are zero-hit workloads; the pool begins recycling only after a cache clear. Every retained accounting snapshot and its peak is at most 1 MiB.

The first attempted probe build used separate source directories with the same root package name and shared Cargo target. Cargo reused the first executable. Those observations are explicitly invalid and retained under `*.invalid-root-package-reuse`. Valid builds use distinct package/binary names and reject identical executable hashes.

## Limits

- Untimed direct rasterizer probes do not predict elapsed time and omit generic font/layout/atlas/backend work.
- GlobalAlloc live and drop deltas are requested Rust heap bytes; allocator bookkeeping, page residency, GPU memory and RSS are excluded.
- Rasterizer-owned bytes are live requested bytes released by dropping only the rasterizer after every Image is dropped, while external ScaleContext and fonts remain alive. This includes Zeno scratch and hash-map buckets, and actual private native Outline allocations.
- Heap high-water includes temporary images and shared-context preparation during the replay prefix; it is not cache-only memory.
- Every endpoint is replayed from a fresh rasterizer/context through the same phase prefix; counters/traffic are cumulative, not just the named last phase.
- grid_unique_variations always uses Roboto Flex, matching the synthetic replay; the three font-config repetitions are duplicate control workloads.
- Counter arrays and snapshots exist only in isolated copied modules; timed/pure snapshots are verified unchanged.
- Pixel FNV64 digests are a mechanism sanity check, not a substitute for the independent full RGBA comparison campaign.
