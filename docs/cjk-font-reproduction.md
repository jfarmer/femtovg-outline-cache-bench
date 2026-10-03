# Reproducing the CJK font investigation

Native glyph screening, the unchanged English demo, and any localized demo
measurements are separate workloads. A font replacement does not translate an
English demo. Read `CJK-FONT-SEARCH.md` for which cohorts actually completed,
their recorded font/source identities, and the limits of each comparison.

The campaign retains original font assets and licenses, font inspection,
prepared Rust/Python sources, locks, metadata, compiler/build provenance,
stdout/stderr, successful and rejected attempts, and the final reports.
Compiled executables and compiler caches are omitted explicitly. Historical
absolute paths remain intact; offline verification resolves them through
verified archive mappings.

From the dedicated benchmark repository, independently check the retained
native CSVs without a Rust build, renderer execution, GUI, or font installation:

```sh
python3 -B scripts/verify-results.py \
  --campaign cjk-font-search \
  --output /private/tmp/femtovg-cjk-offline-verification-fresh
```

The output directory must be new. The verifier first reads and checks every
archive member. It then materializes the CJK archive and the declared companion
campaigns, including the original fonts and Rust sources needed by the native
auditor. Existing statistical suites retain their original extraction policy.

The native auditor independently checks launch order, all raw durations, rounded
per-glyph arithmetic, glyph coverage/counts, geometry/image digest consistency,
finite values, driver/source/build/dependency/lock/font identities, and retained
rejected attempts. It recomputes medians from stdout. The native Rust process
performed exact geometry and image assertions before timing; an offline CSV
audit checks their source and emitted bindings, and does not reconstruct pixels
from a digest. Missing original binaries are declared explicitly in archive mode
and remain bound to their recorded build hashes.

The default verification plan also declares the unchanged English demo screen
and each localized confirmation separately. The explicit optional `cjk-cost`
plan independently recomputes all seven cost-decomposition cohorts: ten default
font processes and eight Noto weight-300/400 processes, 12,960 rows and 360
exact-size cases. It checks the frozen weight coordinate vectors and the
retained reader-only correction, and does not assign confidence intervals or an
application effect to those native kernels. The cost reader and its two child
readers are installed as separate retained sources. See
`docs/cjk-cost-diagnostic-reproduction.md` for the six kernels, their timing
boundaries, and the one-step Noto Serif weight-300 coordinate difference.

The English screen uses its own
independent raw/order/aggregate/source auditor and retains exploratory medians
without an application pixel campaign or confirmation confidence intervals.
Each localized CPU confirmation uses
its own nested cohort root, frozen selection, freshly prepared runner identity,
native oracle proof, and independent paired-effects/bootstrap auditor. Chinese
and Korean controls are explicit plan fields. The verifier does not apply the
historical font-confirmation identity schema to a translated runner.

The initial localized pixel preflight failed in Python before rendering because
a source-tree reader received a string rather than a `Path`. That failed plan,
wrapper and original collectors remain retained. The completed application plan
is an explicit persistence-manifest pointer, not the first plan by filename.
The corrected collectors normalize only that argument; original/fixed byte
identities and the exact one-line change are independently checked through
`collector-path-normalization.json`. Rust sources, binaries, workloads and build
proofs did not change. The localized audit requires this proof explicitly.

For new timing, restore the original source/asset layout or prepare fresh driver
paths, build each distinct screen package from its retained locked source, and
write to new output directories. Keep package and executable names distinct
from the original screen and from each other. A new build needs its own build
identity; its results are a new cohort rather than a replacement for historical
records. Preserve the collected protocol in `native-campaign-plan.json`: four
balanced kernel orders, both DPRs, the five recorded sizes, and the actual
declared text profiles. Run renderer timing serially without builds, downloads,
compression, or analysis competing with it.

Any localized demo reproduction additionally needs exact font coverage of all
translated strings, digits and punctuation, new master/patch/native-oracle
pixel captures, and its own source/build/font/protocol proof. The English demo
proof does not establish correctness for translated text. Follow the retained
`LOCALIZED-REPLAY.md` and the completed cohort provenance rather than assuming
that native scaling cost predicts application savings.

## Installing an additive archive

`install_cjk_study.py` prepares the repository update only after timing, native
auditing, final reports and report-input bindings complete. Its persistence
manifest describes explicit visible artifacts and any supplementary audit plans.
It refuses the wrong baseline, duplicate campaign destinations, missing proofs,
changed evidence, or an existing staging directory. Staging includes compression
and must run after timing finishes.

```sh
python3 -B install_cjk_study.py \
  --stage /private/tmp/femtovg-cjk-install-stage-fresh \
  --native-audit supporting/native-audit.json
```

Review the staged files and `installation-plan.json`, then use the same arguments
with `--install --install-existing` to install that exact checked stage. The
installer adds one campaign, its independently auditable evidence, and reports.
Every previous campaign, audit, source asset and numerical report remains
preserved. Installation does not commit or publish the repository.
