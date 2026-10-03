#!/usr/bin/env python3
"""Preserve fresh demo evidence in a new directory; never build or run it."""
import argparse
import datetime
import hashlib
import json
import os
import shutil
from pathlib import Path

CURRENT = Path(__file__).resolve().parent
SCENES = Path('/private/tmp/femtovg-review-fixes-scenes')
PERF = Path('/private/tmp/femtovg-review-fixes-perf')
BENCH = Path('/Users/jesse/github/femtovg-outline-cache-bench')
INTERIM = BENCH / 'benchmarks/review-fixes-20261003-interim'
DEFAULT = BENCH / 'benchmarks/demo-current-20261003'
SKIP_DIRS = {'target', 'bin', '__pycache__', '.git', '.cache', 'node_modules'}
SKIP_SUFFIXES = {'.pyc', '.pyo', '.o', '.a', '.rlib', '.rmeta', '.dylib', '.so', '.exe'}

REPLAY = r'''#!/usr/bin/env python3
"""Prepare a relocated replay copy; this command performs no build or timing."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

STUDY = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cohort-root', type=Path, default=STUDY / 'raw/current')
    args = parser.parse_args()
    original, work, out = args.cohort_root.resolve(), args.work_dir.resolve(), args.output.resolve()
    if out.exists() or out.is_symlink():
        raise SystemExit(f'Refusing to overwrite replay workspace: {out}')
    if out.is_relative_to(STUDY) or out.is_relative_to(original):
        raise SystemExit('Replay workspace must be outside immutable archived evidence.')
    plan = json.loads((original / 'PLAN.json').read_text())
    builds_path = work / 'scenes/builds.json'
    builds = json.loads(builds_path.read_text())
    records = {f'{r["variant"]}-{r["feature"]}': r for r in builds['records'] if r['kind'] == 'scenes'}
    if set(records) != set(plan['binaries']):
        raise SystemExit('Expected exactly the four rebuilt master/final scene configurations.')
    for label, record in records.items():
        if sha(record['binary']) != record['sha256']:
            raise SystemExit(f'Rebuilt executable changed: {label}')
    old_assets = Path(plan['source_and_build_provenance']['scene_setup']) / 'assets'
    rebound_assets = {}
    for original_path, expected in plan['external_scene_assets'].items():
        relative = Path(original_path).relative_to(old_assets)
        relocated = work / 'scenes/assets' / relative
        if sha(relocated) != expected:
            raise SystemExit(f'Fixed scene asset differs: {relative}')
        rebound_assets[str(relocated)] = expected
    emoji = plan['optional_host_emoji_font']
    present = Path(emoji['path']).exists()
    if present != emoji['present'] or (present and sha(emoji['path']) != emoji['sha256']):
        raise SystemExit('Host optional emoji-font state differs. Record a changed environment explicitly before attempting a different-font replay.')
    out.mkdir(parents=True)
    for file in ['run-demo.py', 'guard.py']:
        shutil.copy2(original / file, out / file)
    for directory in ['assets', 'provenance']:
        shutil.copytree(original / directory, out / directory)
    shutil.copy2(original / 'PLAN.json', out / 'provenance/original-plan.json')
    shutil.copy2(builds_path, out / 'provenance/reproduction-builds.json')
    for label, record in records.items():
        relative = f'provenance/rebuilt-{label}.json'
        (out / relative).write_text(json.dumps(record, indent=2) + '\n')
        plan['binaries'][label] = {'binary_path': record['binary'], 'binary_sha256': record['sha256'], 'build_record': relative}
    plan['external_scene_assets'] = rebound_assets
    plan['source_and_build_provenance']['scene_setup'] = str(work / 'scenes')
    plan['source_and_build_provenance']['reproduction'] = {'original_cohort_root': str(original), 'build_record': 'provenance/reproduction-builds.json', 'changes': 'Only copied PLAN paths, executable identities and prepared-file hashes rebound. Original archived PLAN/source/raw results remain unchanged; rebuilt source/dependency maps are retained separately.'}
    plan['prepared_files'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out / 'PLAN.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(f'Prepared {out}; no build, smoke or timing executed. Review source maps and wait for build activity to end before a separately authorized run.')


if __name__ == '__main__':
    main()
'''

README = '''This directory preserves the fresh 2026-10-03 current demo study.
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
'''

STRESS_README = '''The optional public font proof-sheet stress study is preserved separately
under raw/stress. Its original README describes the visible workload, selected
fonts, phases and limits. It is a designed stress case, not a demonstrated global
maximum of hinting cost. Its raw processes and statistics are not pooled with
the demo cohorts. Original run/build scripts, harness Rust, Cargo manifests/locks,
build logs, dependency graphs, source identities, raw stdout/stderr, plans and
analysis remain byte-for-byte copies. Binary/cache bytes are omitted.

External fonts actually named in the completed stress PLAN are additionally
bundled with licenses under assets/stress/<font-name>. The generated
STRESS-FONT-ASSETS.json records original paths, hashes and retained archive paths;
thin acquisition provenance is retained where available. This does not rewrite
the original PLAN or its external-path metadata. raw/scenes supplies the same
frozen master/final library source trees against which the stress harness built.

Offline relocation and build preparation, outside this immutable archive:

1. Create a fresh work directory and copy raw/scenes to work/scenes, raw/stress
   to work/stress, raw/scene-builds to work/perf/scene-builds, and assets/stress to
   work/stress/font-assets. Refuse existing work directories. Keep a diff of each
   changed copied script/manifest.
2. In the copied stress build.py, change only SCENES to work/scenes and PERF to
   work/perf. In its two copied harness Cargo.toml files, rebind only the femtovg
   dependency paths to work/scenes/source/master and work/scenes/source/final.
   The frozen library Rust source and stress harness Rust remain unchanged.
3. After all timing jobs have stopped, run the copied builder with
   `python3 work/stress/build.py --build-ready`. Its build is locked and offline,
   copies the original matching locks, uses the original release profile, and
   records actual library origins, source maps, metadata/feature graphs,
   compiler identities and fresh binary hashes under work/stress/builds.
   The copied original scene metadata is its dependency-graph reference; it is
   historical evidence, not a claim that the new executable hash must match.
4. Inspect those new build/source/dependency identities before any later run.
   To relocate a separately authorized replay, rebind the copied run.py FONTS
   and FONT_DOCS paths using STRESS-FONT-ASSETS.json: fonts and every recorded
   license/acquisition document have explicit retained archive paths. Choose a
   fresh output and pass the desired original cohort's explicit --dpi value;
   paired12-native (DPI2) and paired12-dpi1 (DPI1) remain distinct campaigns.
   Preserve that script diff and new PLAN. The original runner's macOS process
   guards and original campaign ordering/phase definitions remain in effect.

No stress relocation, rebuild, smoke or replay was performed by the installer.
The public API proof sheet times layout, panel paths, text atlas work and Void
flush; font registration is outside timing. It does not isolate native hinting,
establish eviction, measure GPU/display latency, or compare arena-only storage.
'''

PACKAGING_NOTES = '''The measured RobotoFlex-VariableFont.ttf has SHA256
512f759e24d81543f5629b8edc99c566140a8d161fc2277ac82e64add2f26cf9,
matching the benchmark repository's asset byte-for-byte. The benchmark asset
attribution maps this font to SIL OFL 1.1, Copyright 2017 The Roboto Flex Project
Authors. Its applicable license is bundled at
raw/scenes/assets/licenses/RobotoFlex-OFL.txt (SHA256
9cbaed04b20c853f99840efe5dc96956f6f6120ed83a0ade35f9281a2b63e5d0).

The original plans recorded LICENSE-Roboto, a legacy Apache license file
(SHA256 c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4).
That historical file and every original path/hash/document remain preserved
verbatim. The extra OFL copy corrects packaging without rewriting provenance.
When stress assets are supplied, the applicable OFL is also placed beside the
font at assets/stress/RobotoFlex/RobotoFlex-OFL.txt. STRESS-FONT-ASSETS.json
annotates its applicable_license and preserved_legacy_license separately.
'''


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def inventory(root, target, omitted):
    """Enumerate retained files without following links or traversing caches."""
    retained = []
    for base, directories, files in os.walk(root, followlinks=False):
        base = Path(base)
        for name in list(directories):
            source = base / name
            if name in SKIP_DIRS or source.is_symlink():
                directories.remove(name)
                omitted.append({'source': str(source), 'archive_path': str(target / source.relative_to(root)), 'reason': 'symlink' if source.is_symlink() else 'cache or compiled-binary directory; contents not traversed', **({'link_target': os.readlink(source)} if source.is_symlink() else {})})
        for name in sorted(files):
            source = base / name
            relative = target / source.relative_to(root)
            if source.is_symlink():
                omitted.append({'source': str(source), 'archive_path': str(relative), 'reason': 'symlink', 'link_target': os.readlink(source)})
            elif source.suffix in SKIP_SUFFIXES:
                omitted.append({'source': str(source), 'archive_path': str(relative), 'reason': 'compiled/interpreter artifact', 'bytes': source.stat().st_size, 'sha256': sha(source)})
            else:
                retained.append((source, relative))
    return retained


def check_inputs(root):
    plan = json.loads((root / 'PLAN.json').read_text())
    for relative, expected in plan['prepared_files'].items():
        if sha(root / relative) != expected:
            raise SystemExit(f'Prepared asset/provenance changed: {root / relative}')
    for path, expected in plan['external_scene_assets'].items():
        if sha(path) != expected:
            raise SystemExit(f'Fixed scene asset changed: {path}')
    return plan


def stress_inputs(root):
    """Require an explicitly completed, full paired matrix before preservation."""
    completed = []
    for marker in sorted(root.glob('*/COMPLETE.json')):
        cohort = marker.parent
        if (cohort / 'ABORT.json').exists():
            continue
        required = ['PLAN.json', 'raw.jsonl', 'summary.json', 'REPORT.md']
        if not all((cohort / name).is_file() for name in required):
            continue
        plan = json.loads((cohort / 'PLAN.json').read_text())
        records = [json.loads(line) for line in (cohort / 'raw.jsonl').read_text().splitlines() if line]
        order = plan['process_order']
        if not order or len(records) != len(order):
            continue
        keys = ['block', 'font', 'variant']
        if any(tuple(record.get(k) for k in keys) != tuple(entry[k] for k in keys)
               or record.get('returncode') != 0 or record.get('guard_after_status') != 'idle'
               for record, entry in zip(records, order)):
            continue
        summary = json.loads((cohort / 'summary.json').read_text())
        expected = {(font, phase) for font in plan['fonts']
                    for phase in [*[p[0] for p in plan['phases']], 'complete_sequence']}
        if len(summary) != len(expected) or {(r['font'], r['phase']) for r in summary} != expected:
            continue
        completed.append({'cohort': str(cohort), 'marker': json.loads(marker.read_text()),
                          'process_records': len(records), 'summary_rows': len(summary), 'plan': plan})
    if not completed:
        raise SystemExit(f'Stress study has no matching explicitly complete paired cohort yet: {root}')
    return completed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, default=DEFAULT)
    parser.add_argument('--supplement', type=Path, action='append', default=[])
    parser.add_argument('--stress', type=Path, help='Optional completed public proof-sheet stress study')
    parser.add_argument('--evidence', type=Path, action='append', default=[])
    parser.add_argument('--check', action='store_true', help='Read-only preflight; do not install')
    args = parser.parse_args()
    destination = args.destination.expanduser().absolute()
    if destination.exists() or destination.is_symlink():
        raise SystemExit(f'Refusing to overwrite destination: {destination}')
    if not destination.parent.is_dir():
        raise SystemExit(f'Destination parent must already exist: {destination.parent}')
    roots = [(CURRENT, Path('raw/current')), (SCENES, Path('raw/scenes')), (PERF / 'scene-builds', Path('raw/scene-builds'))]
    for source in args.supplement:
        roots.append((source.resolve(), Path('raw/supplements') / source.name))
    if args.stress:
        roots.append((args.stress.resolve(), Path('raw/stress')))
    if len({str(target) for _, target in roots}) != len(roots):
        raise SystemExit('Supplement directory names must be distinct.')
    omitted, files, plans, supplemental_completions, stress_completions = [], [], [], [], []
    plans.append(check_inputs(CURRENT))
    complete = json.loads((CURRENT / 'demo-current-native/COMPLETE.json').read_text())
    if complete['accepted_process_records'] != 192 or complete['summary_rows'] != 48:
        raise SystemExit('Current native cohort completion identity differs.')
    for source, target in roots:
        if not source.is_dir() or destination.resolve().is_relative_to(source.resolve()):
            raise SystemExit(f'Invalid source/destination relationship: {source}')
        if target.parts[:2] == ('raw', 'supplements'):
            supplemental_plan = check_inputs(source)
            plans.append(supplemental_plan)
            complete_files = list(source.glob('*/COMPLETE.json'))
            matching = []
            for complete_file in complete_files:
                result = json.loads(complete_file.read_text())
                if (result['accepted_process_records'] == supplemental_plan['expected_accepted_processes']
                        and result['summary_rows'] == supplemental_plan['expected_summary_rows']):
                    matching.append({'path': str(complete_file), 'complete': result})
            if not matching:
                raise SystemExit(f'Supplement has no matching complete cohort yet: {source}')
            supplemental_completions.extend(matching)
        elif target == Path('raw/stress'):
            stress_completions = stress_inputs(source)
        files.extend(inventory(source, target, omitted))
    for variant in ['master', 'final']:
        source_map = json.loads((SCENES / f'source-{variant}.json').read_text())['files']
        for relative, expected in source_map.items():
            if sha(SCENES / 'source' / variant / relative) != expected:
                raise SystemExit(f'Frozen source changed: {variant}/{relative}')
    files.extend([(PERF / 'scene-build.py', Path('raw/historical-scripts/scene-build.py')),
                  (PERF / 'scene-run.py', Path('raw/historical-scripts/scene-run.py')),
                  (INTERIM / 'reproduce.py', Path('reproduce.py'))])
    for name in ['Amiri-OFL.txt', 'Entypo-CC-BY-SA-4.0.txt', 'RobotoFlex-OFL.txt']:
        files.append((BENCH / 'assets/licenses' / name, Path('raw/scenes/assets/licenses') / name))
    files.append((BENCH / 'assets/ATTRIBUTION.md', Path('raw/scenes/assets/ATTRIBUTION-benchmark.md')))
    draft = Path('/private/tmp/femtovg-review-fixes-single-pr-draft.md')
    optional = ([draft] if draft.exists() else []) + args.evidence
    files.extend((p.resolve(), Path('review-documents') / p.name) for p in optional)
    for name in ['SUMMARY.md', 'MANUAL-REVIEW.md']:
        if (CURRENT / name).is_file():
            files.append((CURRENT / name, Path(name)))
    targets = [str(relative) for _, relative in files]
    if len(targets) != len(set(targets)):
        raise SystemExit('Evidence archive paths collide; choose distinct evidence filenames.')
    for plan in plans:
        for label, record in plan['binaries'].items():
            binary = Path(record['binary_path'])
            entry = {'source': str(binary), 'label': label, 'reason': 'measured executable omitted', 'recorded_sha256': record['binary_sha256'], 'sha256_origin': 'retained cohort PLAN; not rehashed by installer', 'bytes_at_installation': binary.stat().st_size if binary.exists() else None}
            if entry not in omitted:
                omitted.append(entry)
    stress_font_assets = {}
    for completed in stress_completions:
        stress_plan = completed['plan']
        for variant, record in stress_plan['builds'].items():
            binary = Path(record['binary_path'])
            entry = {'source': str(binary), 'label': f'stress-{variant}', 'reason': 'measured executable omitted', 'recorded_sha256': record['binary_sha256'], 'sha256_origin': 'retained stress PLAN/build record; not rehashed by installer', 'bytes_at_installation': binary.stat().st_size if binary.exists() else None}
            if entry not in omitted:
                omitted.append(entry)
        for name, record in stress_plan['font_assets'].items():
            font = Path(record['path'])
            if sha(font) != record['sha256']:
                raise SystemExit(f'Stress font changed: {font}')
            font_target = Path('assets/stress') / name / font.name
            documents = stress_plan['font_license_and_acquisition_records'].get(name, [])
            if not documents:
                raise SystemExit(f'Stress font has no recorded license/acquisition paths: {name}')
            retained_documents = []
            document_files = []
            for document in documents:
                source = Path(document['path'])
                if not source.is_file() or sha(source) != document['sha256']:
                    raise SystemExit(f'Stress font license/acquisition record missing or changed: {source}')
                target = font_target.parent / source.name
                document_files.append((source, target))
                retained_documents.append({'original_path': str(source), 'sha256': document['sha256'], 'archive_path': str(target)})
            identity = {'original_font': str(font), 'font_sha256': record['sha256'],
                        'archive_font': str(font_target), 'font_documents': retained_documents}
            applicable_license = None
            if name == 'RobotoFlex':
                licensed_font = BENCH / 'assets/RobotoFlex-VariableFont.ttf'
                if sha(licensed_font) != record['sha256']:
                    raise SystemExit('Stress Roboto Flex differs from the benchmark asset/license mapping.')
                applicable_license = BENCH / 'assets/licenses/RobotoFlex-OFL.txt'
                identity['applicable_license'] = {
                    'original_path': str(applicable_license), 'sha256': sha(applicable_license),
                    'archive_path': str(font_target.parent / applicable_license.name),
                    'basis': 'Font bytes match benchmark assets/RobotoFlex-VariableFont.ttf; benchmark assets/ATTRIBUTION.md maps those bytes to RobotoFlex-OFL.txt.'}
                identity['preserved_legacy_license'] = [
                    document for document in retained_documents
                    if Path(document['original_path']).name == 'LICENSE-Roboto']
                identity['packaging_note'] = 'Recorded LICENSE-Roboto is legacy Apache text. The measured Roboto Flex font uses the separately bundled OFL 1.1 license; original PLAN/documents remain verbatim.'
            if name in stress_font_assets:
                if identity != stress_font_assets[name]:
                    raise SystemExit(f'Stress cohorts disagree on font identity: {name}')
            else:
                files.append((font, font_target))
                files.extend(document_files)
                if applicable_license:
                    files.append((applicable_license, font_target.parent / applicable_license.name))
                stress_font_assets[name] = identity
    targets = [str(relative) for _, relative in files]
    if len(targets) != len(set(targets)):
        raise SystemExit('Evidence/font archive paths collide; choose distinct evidence filenames.')
    checks = [(source, relative, sha(source)) for source, relative in files]
    if args.check:
        print(json.dumps({'read_only_preflight': True, 'retained_files': len(checks), 'retained_bytes': sum(p.stat().st_size for p, _, _ in checks), 'destination': str(destination), 'supplements': [str(p) for p in args.supplement], 'completed_current_cohort': complete, 'supplemental_completions': supplemental_completions, 'stress_completions': [{k: v for k, v in r.items() if k != 'plan'} for r in stress_completions]}, indent=2))
        return
    destination.mkdir(exist_ok=False)
    for source, relative, expected in checks:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if sha(target) != expected:
            raise SystemExit(f'Copy checksum mismatch: {relative}; partial destination retained for inspection.')
    (destination / 'README.md').write_text(README)
    (destination / 'prepare-replay.py').write_text(REPLAY)
    (destination / 'PACKAGING-NOTES.md').write_text(PACKAGING_NOTES)
    if stress_completions:
        (destination / 'STRESS-REPRODUCTION.md').write_text(STRESS_README)
        (destination / 'STRESS-FONT-ASSETS.json').write_text(json.dumps(stress_font_assets, indent=2) + '\n')
    (destination / 'OMITTED.json').write_text(json.dumps(omitted, indent=2) + '\n')
    installation = {'installed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'status': 'current demo cohort complete; supplemental and stress cohorts retained separately if supplied', 'current_cohort_complete': complete, 'supplemental_completions': supplemental_completions, 'stress_completions': [{k: v for k, v in r.items() if k != 'plan'} for r in stress_completions], 'destination': str(destination), 'source_roots': [str(p) for p, _ in roots], 'baseline_commit': plans[0]['baseline_commit'], 'candidate_commit': plans[0]['candidate_commit'], 'builder_source': str(INTERIM / 'reproduce.py'), 'portable_build_smoke_or_timing_executed_by_installer': False, 'copy_policy': 'Raw metadata/source/manifests/locks retained verbatim. No global indexes or historical destinations modified. Every copied file verified against its pre-copy checksum.'}
    (destination / 'INSTALLATION.json').write_text(json.dumps(installation, indent=2) + '\n')
    retained = sorted(p for p in destination.rglob('*') if p.is_file() and p.name != 'SHA256SUMS')
    sums = '\n'.join(f'{sha(p)}  {p.relative_to(destination)}' for p in retained) + '\n'
    (destination / 'SHA256SUMS').write_text(sums)
    for line in sums.splitlines():
        expected, relative = line.split('  ', 1)
        if sha(destination / relative) != expected:
            raise SystemExit(f'Retained checksum verification failed: {relative}')
    print(f'Installed and checksum-verified {len(retained)} files in {destination}; no build or timing executed.')


if __name__ == '__main__':
    main()
