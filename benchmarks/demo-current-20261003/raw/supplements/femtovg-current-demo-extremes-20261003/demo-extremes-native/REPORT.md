Fresh current master/final actual demo CPU comparison at DPI 2.

| Features | Font | Phase | Units | Master | Final | Paired change [exploratory 95% interval] |
|---|---|---|---|---:|---:|---:|
| default_swash | FleurDeLeah | first_paint | us/frame | 7240.271 | 4919.396 | -2358.688 [-2444.646, -2264.397] |
| default_swash | FleurDeLeah | warm | us/frame | 226.830 | 222.802 | -3.409 [-5.303, -2.106] |
| default_swash | FleurDeLeah | zoom_in | us/frame | 6456.031 | 4291.137 | -2166.634 [-2250.766, -2118.959] |
| default_swash | FleurDeLeah | zoom_out | us/frame | 4251.272 | 2786.932 | -1474.675 [-1524.382, -1417.715] |
| default_swash | FleurDeLeah | pan | us/frame | 230.683 | 225.792 | -5.177 [-7.288, -2.088] |
| default_swash | FleurDeLeah | reported_sequence | us/sequence | 144694.682 | 99667.980 | -46400.350 [-47944.209, -44850.437] |
| default_swash | DiplomataSC | first_paint | us/frame | 7318.541 | 4534.021 | -2790.604 [-2855.083, -2748.230] |
| default_swash | DiplomataSC | warm | us/frame | 244.452 | 241.244 | -3.881 [-6.749, +1.080] |
| default_swash | DiplomataSC | zoom_in | us/frame | 6697.189 | 3901.260 | -2763.380 [-2849.328, -2702.288] |
| default_swash | DiplomataSC | zoom_out | us/frame | 4629.885 | 2786.948 | -1849.175 [-1878.120, -1741.564] |
| default_swash | DiplomataSC | pan | us/frame | 247.829 | 245.840 | -1.817 [-6.106, +0.648] |
| default_swash | DiplomataSC | reported_sequence | us/sequence | 153401.227 | 94557.371 | -57838.849 [-59644.377, -56787.655] |
| default_no_swash | FleurDeLeah | first_paint | us/frame | 6963.896 | 6914.125 | -67.583 [-133.354, +118.937] |
| default_no_swash | FleurDeLeah | warm | us/frame | 225.837 | 226.055 | +0.390 [-0.282, +5.136] |
| default_no_swash | FleurDeLeah | zoom_in | us/frame | 5823.396 | 5808.891 | +16.245 [-64.554, +149.050] |
| default_no_swash | FleurDeLeah | zoom_out | us/frame | 3804.262 | 3847.453 | +38.156 [-41.694, +164.448] |
| default_no_swash | FleurDeLeah | pan | us/frame | 226.594 | 227.554 | +1.216 [-0.206, +3.146] |
| default_no_swash | FleurDeLeah | reported_sequence | us/sequence | 131502.147 | 132397.712 | +568.871 [-1397.120, +4638.710] |
| default_no_swash | DiplomataSC | first_paint | us/frame | 5855.916 | 5830.791 | +17.895 [-68.833, +201.271] |
| default_no_swash | DiplomataSC | warm | us/frame | 243.124 | 243.015 | -0.108 [-2.018, +2.542] |
| default_no_swash | DiplomataSC | zoom_in | us/frame | 5018.189 | 4999.302 | +8.686 [-72.821, +59.932] |
| default_no_swash | DiplomataSC | zoom_out | us/frame | 3529.002 | 3528.229 | -15.410 [-47.983, +28.661] |
| default_no_swash | DiplomataSC | pan | us/frame | 246.031 | 246.523 | +1.564 [-4.144, +3.123] |
| default_no_swash | DiplomataSC | reported_sequence | us/sequence | 118814.793 | 118114.523 | -741.943 [-1422.122, +760.148] |

Negative paired changes save CPU time. The complete reported sequence includes first paint, 30 warm, 12 zoom-in, 12 zoom-out and 10 pan frames (65 total). The 119 intervening warmup frames are excluded.
CPU scene drawing includes layout, other demo drawing and Canvas set_size; total adds Void flush. Font/image setup is excluded. No GPU, window, presentation or application-launch latency is measured.
Twelve independent rotating paired process blocks; each configuration has six AB and six BA orders. One trial per process. Median paired deltas/ratios; 10,000 whole-block percentile bootstrap resamples, fixed seed; exploratory intervals without multiplicity adjustment.
Environment policy: 0 whole-block retries; strict name guards before and after each process, 60 quiet seconds before start/replay; all attempted process output and guard evidence retained; no timing-value filtering.
