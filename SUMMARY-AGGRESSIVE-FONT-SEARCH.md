# Aggressive Latin font search: summary

**Fleur de Leah is a stronger per-glyph hinting stress font; Diplomata SC is a modestly stronger unchanged-demo example.** We screened 47 unchanged open-source candidates and separately confirmed five selected fonts against the exact updated patch and upstream master.

| Font | Master first paint | Patch first paint | Saved time, 95% interval |
|---|---:|---:|---:|
| Diplomata SC | 6.741 ms | 3.982 ms | 2.759 ms [2.710, 2.808] |
| Rye | 6.422 ms | 3.744 ms | 2.677 ms [2.617, 2.736] |
| Water Brush | 7.516 ms | 4.866 ms | 2.650 ms [2.561, 2.745] |
| Fleur de Leah | 6.703 ms | 4.431 ms | 2.272 ms [2.209, 2.332] |
| Vollkorn Medium | 6.759 ms | 4.488 ms | 2.271 ms [2.173, 2.386] |

Diplomata SC's additional first-paint saving over fresh Rye is **81.79 µs**, with a 95% interval of **29.42–142.95 µs**. It saves **57.300 ms** across the 65 reported demo frames, versus Rye's **53.855 ms**. Warm/pan intervals all include zero. Water Brush's first-paint advantage over Rye is uncertain; Fleur demonstrably saves less than Rye in this demo.

On the fixed native ASCII94 test, Fleur's hinted outline costs **31.84 µs/glyph**, versus Rye's **18.79** and Vollkorn's **13.51** in the same cohort. Counted interpreter dispatches are about **3,985, 2,604 and 1,648** respectively, with exact native geometry/image agreement. The demo uses different glyphs and reuse frequencies, so a larger kernel cost is not a larger application saving.

Fresh confirmation retained 120 processes and 3,000 rows, 12 balanced blocks and five trials; all 75 captured images agree between master, patch and native reference. A separate audit reproduced all 90 endpoints and 184 intervals. All three exploratory cohorts, lower-benefit fonts, rejected processes and prior benchmarks remain preserved. Nothing in production FemtoVG or Swash was edited by this font search.

Read the [full analysis](AGGRESSIVE-FONT-SEARCH.md) and [reproduction notes](docs/aggressive-font-reproduction.md). These are absolute host drawing savings in one demo on an M4 Max, not a universal improvement or an application launch/FPS result.
