All values are microseconds of CPU drawing (demo), the complete miss workload (cold), or CPU drawing plus Void flush (stress).
Demo setup/font loading and GPU rendering are excluded. Cold canvas/font setup is excluded.

| Case | Phase | Master | Simple | Adapter | Adapter / Master | Adapter / Simple |
|---|---|---:|---:|---:|---:|---:|
| stress-FleurDeLeah | complete_sequence | 1268190.836 | 301101.020 | 301649.064 | -76.22% | +0.01% |
| stress-FleurDeLeah | first_paint | 95421.563 | 21083.584 | 20785.730 | -78.21% | -2.07% |
| stress-FleurDeLeah | new_size | 96885.498 | 22894.470 | 23025.059 | -76.34% | +0.19% |
| stress-FleurDeLeah | return | 251.729 | 227.688 | 222.771 | -10.53% | -1.28% |
| stress-FleurDeLeah | warm | 166.006 | 151.476 | 144.761 | -12.26% | -3.93% |

Negative percentages mean lower CPU time. Paired block bootstrap intervals are in SUMMARY.json.
Master is frozen upstream 6a5f15a; Simple is the previous measured lower-touch integration; Adapter is the private Font cache adapter. See METADATA.json for exact source and binary identities.
