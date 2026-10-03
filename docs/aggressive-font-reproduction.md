# Reproducing the aggressive Latin font investigation

This investigation appends to the existing benchmark repository; it does not
replace the Latin or CJK studies. Shipped regular fonts are acquired unchanged
from Google Fonts commit `9710da1eacb3be272583c3224dcb70f9da6eadbb`.
Each acquisition manifest binds every font, license, metadata and retained
upstream description to its official Git blob identity and SHA256. No font is
subsetted, rehinted or transformed to manufacture an expensive case.

The original29-font cohort, ten-font hinted supplement and eight-font ornate
supplement have separate frozen manifests, static inspection, native
protocols and demo protocols. Each native prescreen reuses the original
frozen executable and driver with four trials and three repeats. Its DPR1
demo profile uses logical11/12/14/15/16px sizes, matching the actual first
paint atlas requests; its DPR2 profile is a separate larger-size control.
Exact outline/image assertions run before timing. Native per-glyph costs do
not establish application cache hits or net benefit.

Exploratory application screens keep the unchanged FemtoVG demo, regular
font replacement and fixed icon/emoji/fallback assets. All font processes use
two balanced blocks and three trials. Their results preserve every phase,
within-trial65-frame reported sequence and all three cumulative endpoints.
The exact rational independent audit checks original process stdout, paired
blocks, aggregate agreement, order, source/font/build identities and atlas
annotations. It supplies no confidence intervals from those two blocks.

The final selected-font confirmation has its own selection frozen before
collection, fresh Rye/Vollkorn controls, balanced12-block collection and
independent raw/bootstrap audit. Its actual fonts, versions, pixels, timing
and estimator scope are bound by the final manifest. Read the final report
and selection protocol for the measured dimensions. Selection intervals are
conditional on this search and machine, not a representative font sample.

Static engine audits and privately counted hint-interpreter traces are
supporting causal evidence. Their original programs, sources, failure logs,
raw counts and live equality proofs are retained separately. They are not
renderer performance measurements.

## Offline verification

After installation, verify the new archive and its declared independent
audits with the standard repository interface:

```sh
python3 -B scripts/verify-results.py \
  --campaign aggressive-font-search \
  --output /private/tmp/femtovg-aggressive-installed-verification-fresh
```

The output path must be new. Required original/font/CJK companion archives
are verified and fully materialized through the existing longest-prefix
historical path map. Every retained archive member, including fonts/source
and RGBA captures, is checksum-verified before an audit. Compiled bodies are
omitted explicitly: recorded live identity checks remain preserved, the
native/exploratory readers require an explicit missing-binary option, and
any executable present during such an audit must still match its digest.

The native reader is shared with CJK because its implementation supports
arbitrary screen labels. The exploratory demo reader does not import or
execute collectors/wrappers. The confirmation reader independently recomputes
raw medians, weighted trial sequences, paired means and supplied bootstrap
intervals; it checks the source/preflight metadata from the original complete
live analysis. Offline statistical auditing cannot establish the absence of
background load during original measurements.

## Preparing an additive review stage

Only prepare a final manifest after the report, all three exploratory audits
and the selected-font confirmation actually pass. The helper derives the
actual confirmation paths and control directly from the frozen selection
protocol's recorded independent-audit command. Alternatively, a completed
confirmation-plan JSON can declare `completed_audit`, `audit_plan` and optional
visible pixel/source/mechanism bindings. The finalized helper includes the native/static tables,
all three exploratory results, engine audits, VM count summaries and complete
primary analysis/bootstrap inputs.

```sh
python3 -B finalize_aggressive_manifest.py \
  --confirmation-protocol primary-selection-v1/protocol.json

python3 -B install_aggressive_study.py \
  --repository /Users/jesse/github/femtovg-outline-cache-bench \
  --stage /private/tmp/femtovg-aggressive-install-stage-fresh
```

Manifest finalization/staging performs hashes, numerical audits and archive
compression. Do not run it during renderer timing. The installer expects the
reviewed installed CJK baseline of31 campaigns and15 audits. It appends one
archive and only the explicitly declared new audits, preserving every old
index entry and numerical report. Existing file updates are limited to the
README, index, visible copy manifest, verifier and archive registry. It reuses
the existing archive helper and lossless decoding support.

Review the complete installation plan and create a disposable baseline-plus-
stage view. Run the new archive's offline verifier in that view before root
installs the concrete result. The actual repository write needs its normal
filesystem approval; no commit or remote publication is implied.

Native collection entry points are `run_native_prescreen.py collect` in each
cohort; demo screens use each frozen `run_aggressive_demo_screen.py collect`.
Root must coordinate builds/downloads/analysis and desktop access before any
such renderer run. All original failed, rejected and superseded attempts are
kept under their original names. Do not rerun a collector into an existing
campaign or replace frozen protocol inputs.
