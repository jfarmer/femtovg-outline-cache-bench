# Final cache review fixes

See [results](SUMMARY.md), [review scope and TDD evidence](REVIEW_FIXES.md),
the [public API review](API_REVIEW.md),
the [demo/miss report](REPORT.md), [stress report](STRESS-REPORT.md),
[allocation probe](PROBE-REPORT.md), and [independent audit](AUDIT-REPORT.md).

Master is upstream `9d574e0`; Before is `af989d9`; PR is committed `907bb37`.
The snapshot retains exact sources, scripts, locked dependencies, scenes,
fonts/licenses, provenance, guards, raw accepted/excluded attempts and tests.
Compiled executables and compiler caches are omitted; binary hashes remain
in build records and `OMITTED.json`.

Verify and extract with Python 3.12 or later:

```sh
python3 verify.py
python3 verify.py --extract /tmp/femtovg-review-fixes
```

With Rust/Cargo and cached dependencies, rebuild all variants and run fresh
measurements. These commands open no windows:

```sh
cd /tmp/femtovg-review-fixes/bench
python3 build.py
python3 run.py --out runs/new-comparison --blocks 6
python3 analyze.py --out runs/new-comparison
python3 run.py --out runs/new-stress --blocks 6 --cases stress-FleurDeLeah
python3 analyze.py --out runs/new-stress
python3 probe.py --out runs/new-probe --blocks 6
```

The guard must inspect process names; a failed inspection or compiler/build
overlap excludes the entire block and retains the attempt. The demo measures
CPU drawing; stress and miss workloads include Void flush. No GPU performance
or application startup is measured. The probe has counter overhead.

Measured builds/runs and their audits used the original isolated directory.
The package verifier checks retained bytes and archive extraction. A fresh build
from the relocated archive has not been tested; original absolute provenance
paths and binary identities are retained as captured. Rebuild before a fresh run.
