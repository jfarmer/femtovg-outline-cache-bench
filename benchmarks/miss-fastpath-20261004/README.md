# Normal-miss fast-path follow-up

See [results](SUMMARY.md), [full report](REPORT.md), [exact source provenance](SOURCE_FREEZE.json),
[tests](validation/RESULTS.json), [raw records](runs/comparison/raw.jsonl), and
[independent review](INDEPENDENT_REVIEW.md).

Master is upstream `9d574e0`; Before is committed cache branch `907bb37`.
After is the measured working-tree insertion fast path based on `907bb37`;
it is not labeled as a commit. Both source patches and all frozen source
hashes are retained. The archive contains source trees, scripts, unchanged
scenes, assets and font licenses, normalized dependency locks, build logs,
validation logs, six balanced blocks, raw process output, guards and reports.
Compiled executables and compiler caches are omitted; binary identities
remain in BUILD.json and OMITTED.json.

Verify and extract with Python 3.12 or later:

```sh
python3 verify.py
python3 verify.py --extract /tmp/femtovg-miss-fastpath
```

With Rust/Cargo and the locked dependencies cached, rebuild the variants and
run a fresh no-window comparison:

```sh
cd /tmp/femtovg-miss-fastpath/bench
python3 build.py
python3 run.py --out runs/new-comparison --blocks 6
python3 analyze.py --out runs/new-comparison
python3 audit.py --out runs/new-comparison
```

The default cohort uses all seven existing cases: three demo fonts, a
non-Swash demo control, two 32-size miss controls, and Fleur de Leah stress.
The guard must inspect process names; failed inspection or compiler overlap
excludes and retains the entire interrupted block. No timing-based filtering
is performed. Demo results measure CPU drawing; miss/stress results include
Void flush. Font loading, Canvas creation and GPU work are excluded.

The verifier checks retained bytes and archive extraction. A fresh build
from the relocated archive has not been tested; original absolute provenance
paths and binary identities are retained as captured. Rebuild before a fresh
run. Earlier studies remain intact and their absolute timings are not pooled
with this dataset.
