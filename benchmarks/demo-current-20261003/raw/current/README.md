Fresh current-demo preparation only; no builds or timings executed.

Run only after root source/build verification and guarded timing GO:

    python3 /private/tmp/femtovg-current-demo-20261003/run-demo.py --timing-authorized --code-ready --output demo-current

The runner waits for 60 quiet seconds, then executes demo only at DPI2: four fonts, default+Swash and default without Swash, twelve rotating paired process blocks (192 processes). Each configuration receives six AB and six BA orders. Any name-guard match rejects the entire logical attempt; every attempt and output is retained. Maximum eight environment retries or thirty minutes. No timing-based filtering.

Output includes original stdout/stderr, parsed five-phase frame counts, complete65-frame totals, before/after guard records, ledger offsets, absolute paired exploratory95% intervals, and source/build/font/license identities.119 warmup frames are excluded. This is actual-demo CPU+layout+Voidflush, with font/image setup excluded; noGPU/window/presentation timing.

The exact new user authorization is recorded in PLAN.json and is not a claim that the external build finished. Existing frozen runners and earlier archives are unchanged.
