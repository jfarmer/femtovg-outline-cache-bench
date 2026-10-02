# Installed repository offline verification

The full verifier was run successfully from the installed repository at
`/Users/jesse/github/femtovg-outline-cache-bench`. It verified all **22 campaign
archives and 39,284 retained files**, including lossless tar hardlink aliases,
plus all 612 bundled source/asset files, 24 visible analysis copies and eight
report-input checksums. The complete result is
[verification.json](offline-verification/verification.json).

The four independent raw-data audits reproduced **8,328 paired point effects**
and **2,928 primary 95% bootstrap intervals** using the recorded 10,000 whole
block resamples. All selected observations were retained; Alustin's whole-block
retries were independently checked against raw query contamination.

| Cohort | Point effects | Primary intervals | Retained audit |
| --- | ---: | ---: | --- |
| Final replay, CPU/GPU phases and weighted sequences | 3,888 | 1,296 | [JSON](offline-verification/01-selection-examples-replay-audit.json) |
| Final Alustin, first/search renderer thread CPU | 72 | 72 | [JSON](offline-verification/02-selection-alustin-app-audit.json) |
| Screening replay, CPU phases and weighted sequences | 4,212 | 1,404 | [JSON](offline-verification/03-miss-screening-examples-replay-audit.json) |
| Screening Alustin, first/search renderer thread CPU | 156 | 156 | [JSON](offline-verification/04-miss-screening-alustin-app-audit.json) |

Replay point checks cover all three cumulative timing metrics; primary intervals
cover CPU draw time and GPU completion time. App checks here cover the two main
renderer thread CPU metrics. Other app metrics, including RSS, retain their full
analysis tables and original independent-audit records in the archives.
Intervals are exploratory and unadjusted for multiple comparisons.

The auditors imported no benchmark/analyzer code and read raw CSV/trace data
from checksum-verified archive materializations. A longest-prefix map resolves
historical paths; every unmapped historical path is rejected. Existing old
`/tmp` inputs cannot supply missing audit data. The successful installed-path
run proves relocation of the archive-backed analysis.

Compiled executables and compiler caches are omitted. Offline checks verify
recorded executable identities and build-provenance hashes, **not omitted binary
bytes**. Original source, locks, helpers, raw observations, pixel captures and
font-diagnostic records remain archived. Fresh portable builds and pixel/font
checks are documented in [portable validation](portable-validation.md).

To reproduce in a new output directory:

```sh
python3 scripts/verify-results.py --output runs/verification
```

The compact verification record and four audit outputs are retained here;
large temporary metadata materializations remain under ignored `runs/`.
