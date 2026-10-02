# Native Outline pool: installed offline verification

Passed from the installed repository with no Rust builds, windows, historical
temporary source trees or executable bytes required:

```sh
python3 scripts/verify-results.py --campaign native-pool-examples --campaign native-pool-alustin --campaign native-pool-source-bundle --output runs/native-pool-offline-verification
```

All 5,485 retained files in the three new archives were rehashed, including
hardlink-deduplicated pixel captures and sources. The original 612-file bundle,
49 visible analysis copies, eight original report inputs and 25 native report
inputs also passed their guards. The 22 previous campaigns and original reports
remain preserved; this command selected the three new campaigns.

Independent archive-backed recomputation reproduced 3,888 replay point effects
and 1,296 primary confidence intervals, plus 72 Alustin first/search renderer
CPU effects and intervals. It revalidated all 72 accepted application blocks
and the three query-only whole-block retries from raw records. Separate live
source/pixel and all-metric audits are retained in the campaign archives and
visible analysis; this offline check does not claim to rerun those live audits.

Exact verification outputs are in [native-pool-offline-verification/](native-pool-offline-verification/),
with a checksum manifest identifying the original outputs. Compiled executables
and compiler caches are excluded from archives. Offline checks validate recorded
binary/build identities; fresh reproduction builds and checks actual executable
bytes. Intervals are exploratory and unadjusted for multiple comparisons.
