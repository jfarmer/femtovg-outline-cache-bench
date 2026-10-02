# Portable execution validation

The portable bundle was prepared in a fresh runtime directory and **all four
variants were rebuilt for both suites**. Cached Cargo dependency outputs were
used to reduce rebuild time; historical campaign executables were not reused.
The exact sources, resolved locks, dependency/features metadata, build logs,
commands and newly produced executable hashes were recorded. Alustin's original
Cargo.lock was restored and its tracked inputs remained unchanged.

The subsequent functional checks passed:

- Replay CPU: one block and one trial, stock font at DPR 2; all four processes
  validated 28 phase rows each.
- Untimed GPU replay pixels: stock font at DPR 1 and 2; all 168 candidate/master
  phase-image comparisons were byte identical.
- Untimed Alustin pixels: Vollkorn on `winit-femtovg-wgpu`; all three
  candidate/master comparisons were byte identical.
- Actual renderer-font diagnostics passed for all four Alustin processes,
  validating the explicitly registered primary face and Inter fallback.
- A copied prepared runtime passed its checksum guard, then a synthetic source
  mutation was rejected. The frozen vendor bundle was unchanged.
- All seven small synthetic source/archive/path/build guards passed, including
  hardlink aliases and rejection of unmapped historical paths.

These small batches verify portability and behavior. Their recorded CPU
durations are **not performance evidence**; the measured experiment cohorts and
their paired statistics provide that evidence.

[portable-real-validation.json](portable-real-validation.json) records the
outcomes, source pins and hashes of all build/run provenance. The original
runtime root was `runs/portable-validation`; its retained inputs, logs,
provenance and pixel/font records are preserved as a validation campaign in the
result archive inventory. Compiled binaries are omitted under the ordinary
archive policy, with their hashes retained.

Commands used:

```sh
python3 scripts/bundle-runtime.py --core /private/tmp/femtovg-miss-selection-v2-review --app /private/tmp/alustin-miss-selection-v2-review
python3 scripts/prepare.py --output runs/portable-validation --alustin-checkout /Users/jesse/github/alustin-gui-v2
python3 scripts/build.py all --runtime runs/portable-validation --replay-target-dir /private/tmp/femtovg-cache-bench/target --app-target-dir /private/tmp/slint-wgpu-evidence/target
python3 scripts/run.py replay cpu --runtime runs/portable-validation --output runs/portable-validation/functional-replay-cpu --blocks 1 --trials 1 --fonts stock --dpis 2
python3 scripts/run.py replay pixels --runtime runs/portable-validation --output runs/portable-validation/functional-replay-pixels --fonts stock --dpis 1 2
python3 scripts/run.py app pixels --runtime runs/portable-validation --output runs/portable-validation/functional-app-pixels --fonts vollkorn --backends winit-femtovg-wgpu --actual-font-diagnostics
```

New users choose their own output and checkout paths; `prepare.py` records every
guarded runtime relocation. No historical `/tmp` path needs to exist for offline
archive verification.
