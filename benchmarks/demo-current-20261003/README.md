This directory preserves the fresh 2026-10-03 current demo study.
Read SUMMARY.md if supplied by the study owner, then raw/current/demo-current-native/REPORT.md
and its raw records. Supplemental studies, if supplied, remain separate under
raw/supplements; their cohorts and statistics are never pooled by this installer.

The original runner, plans, process outputs, guard failures, analysis, font licenses,
source identities and build records are copied byte-for-byte. The unsuccessful
initial sandbox guard attempt is preserved beside the completed native cohort.
Historical absolute paths remain unchanged in raw evidence. raw/scenes contains
the exact frozen master/final source trees, scene adapters, Cargo manifests/locks
and fixed assets used by the four measured binaries. raw/scene-builds retains
the original build outputs and dependency graphs. PIN_VERIFICATION and
final-runtime-identity distinguish the frozen candidate's full-file hashes from
the current commit's identical released code and its two test-comment changes.

SHA256SUMS covers every retained file except itself. OMITTED.json lists pruned
cache/binary directories without scanning them and the four measured executables
with their already-recorded hashes; executable bytes are not redistributed.
No global index or historical study was changed. PR drafts are review documents,
not evidence of a published PR. Historical route/arena and font-selection evidence
already preserved elsewhere in this repository remains illustrative, with its own
revisions and workloads; it is not pooled with this current cohort.
PACKAGING-NOTES.md identifies the applicable Roboto Flex OFL license separately
from the legacy Apache file preserved in the original preparation records.

Reproduction starts from bundled frozen sources, not a live FemtoVG checkout.
reproduce.py is the byte-preserved builder from the prior interim study. In this
archive use its verify and build --group scenes commands only; its other study
groups and generic smoke/run commands are not supplied here. The builder changes
only copied Cargo dependency paths, captures compiler/dependency/source/binary
records, and defaults to locked offline dependencies. --online is an explicit
option on machines lacking dependencies. prepare-replay.py then makes a fresh
copy of the current runner/plan and rebinds paths and hashes to those rebuilt
binaries and assets. The archived raw files remain immutable.

Example preparation, run from this directory:

    python3 reproduce.py verify
    python3 reproduce.py build --group scenes --work-dir /tmp/femtovg-demo-rebuild
    python3 prepare-replay.py --work-dir /tmp/femtovg-demo-rebuild --output /tmp/femtovg-demo-replay

No portable build, smoke or replay has been performed by this installer. Check
the new build's source/dependency maps against the recorded originals, ensure all
build/compiler/linker activity has ended, and obtain current authorization before
running the prepared runner separately. For a supplied supplemental cohort pass
its raw/supplements/<directory> as --cohort-root to prepare-replay.py. Fresh outputs
must remain outside this immutable archive.

The runner retains its macOS environment query and strict process guards. Host
Apple Color Emoji is optional but unbundled; matching its recorded presence and
hash is required by the relocation helper. Other platforms/font states require
an explicitly documented environment change, not an exact replay claim.
This is actual demo CPU/layout drawing plus Void flush at DPI2; font/image setup,
119 warmup frames, GPU execution, windows, presentation and application startup
are outside the reported timing. Bootstrap intervals remain exploratory.
If stress evidence was supplied, see STRESS-REPRODUCTION.md for its distinct
workload, source/font bindings and offline build preparation.
