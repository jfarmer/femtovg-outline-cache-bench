#!/usr/bin/env python3
"""Append a completed repeat cohort without replacing the original font study.

Stage only after serial timing, analysis and independent audits finish. Existing
dirty repository files are the baseline. No build, benchmark, GUI, commit or
remote action occurs; archive compression/verification happens while staging.
"""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

LABEL = 'font-stress-rerun'
TOOLS = ('verify-results.py', 'archive-study.py')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def load(path): return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def complete(path):
    value = load(path)
    if value.get('complete') is not True: raise ValueError('Completed evidence required: ' + str(path))
    return value

def info(path):
    path = Path(path)
    return {'sha256': sha(path), 'bytes': path.stat().st_size}

def check(record):
    if info(record['path']) != {k: record[k] for k in ('sha256', 'bytes')}:
        raise ValueError('Bound evidence changed: ' + record['path'])

def records(root):
    root = Path(root)
    if any(p.is_symlink() for p in root.rglob('*')): raise ValueError('Symlink in stage: ' + str(root))
    return {p.relative_to(root).as_posix(): info(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts}

def once(text, old, new):
    if text.count(old) != 1: raise ValueError('Expected unique adaptation marker: ' + repr(old))
    return text.replace(old, new)

def inputs(source):
    required = [source/'confirm-cpu/cpu-provenance.json', source/'confirm-gpu/gpu-provenance.json',
        source/'selection-frozen.json', source/'analysis/summary.json', source/'analysis/raw-audit.json',
        source/'analysis/analysis-inputs.json', source/'independent-rerun-audit.json',
        source/'FONT-STRESS-RERUN.inputs.json']
    for path in required: complete(path)
    selection = load(source/'selection-frozen.json')
    if selection['confirmation']['versions'] != ['master', 'final']:
        raise ValueError('Expected the original frozen master/final selection')
    # Seven small immutable aliases permit reuse of the unchanged direct audit.
    # Their original absolute bindings in collection provenance stay untouched.
    for relative, digest in selection['selection_inputs'].items():
        if sha(source/relative) != digest: raise ValueError('Selection alias changed: ' + relative)
        required.append(source/relative)
    reference = None
    for mode, trials in (('cpu', 5), ('gpu', 3)):
        data = load(source/f'confirm-{mode}/{mode}-provenance.json')
        if data['versions'] != ['master', 'final'] or data['blocks'] != 12 or data['trials_per_process'] != trials or data['exploratory']:
            raise ValueError('Unexpected complete repeat protocol: ' + mode)
        if set(data['dpis']) != {1, 2} or len(data['fonts']) != 3:
            raise ValueError('Expected three selected fonts and both DPRs')
        check(data['pixel_proof']); check(data['selection_manifest']); check(data['driver'])
        if sha(source/'selection-frozen.json') != data['selection_manifest']['sha256']:
            raise ValueError('Local selection alias differs from the original bound manifest')
        pixels = complete(data['pixel_proof']['path'])
        if pixels['identity'] != data['identity'] or pixels['font_files'] != data['font_files']:
            raise ValueError('Repeat changed original executable/source/font identities')
        if reference is not None and reference != data['identity']:
            raise ValueError('CPU/GPU source/build identities differ')
        reference = data['identity']
    analysis = load(source/'analysis/analysis-inputs.json')
    for record in [*analysis['inputs'].values(), *analysis['outputs'].values()]:
        if isinstance(record, dict) and {'path', 'sha256', 'bytes'} <= record.keys(): check(record)
    if load(source/'analysis/raw-audit.json')['metadata_only']:
        raise ValueError('Repeat requires completed live source/font/pixel validation')
    audit = load(source/'independent-rerun-audit.json')
    if audit['summary_sha256'] != sha(source/'analysis/summary.json'):
        raise ValueError('Independent repeat audit is not bound to the current summary')
    report = load(source/'FONT-STRESS-RERUN.inputs.json')
    for original, record in report['files'].items():
        path = Path(original)
        if not path.is_absolute(): path = source/path
        expected = record['sha256'] if isinstance(record, dict) else record
        if sha(path) != expected or (isinstance(record, dict) and 'bytes' in record and path.stat().st_size != record['bytes']):
            raise ValueError('Repeat report input changed: ' + str(path))
    return required

def adapt(repo, stage, source):
    verifier = (repo/'scripts/verify-results.py').read_text()
    marker = "('font-stress-report-inputs.json','font_stress_report_inputs')"
    verifier = once(verifier, marker, marker + ",('font-stress-rerun-report-inputs.json','font_stress_rerun_report_inputs')")
    archive = (repo/'scripts/archive-study.py').read_text()
    marker = ']\n\n\ndef main():'
    archive = once(archive, marker, f"    ({LABEL!r}, {str(source)!r}, 'font-confirmation-repeat'),\n" + marker)
    for name, text in (('verify-results.py', verifier), ('archive-study.py', archive)):
        ast.parse(text, filename=name); (stage/'scripts'/name).write_text(text)

def stage_update(args):
    source = args.source.resolve(strict=True); repo = args.repository.resolve(strict=True); stage = args.stage.resolve()
    if stage.exists() or stage.is_relative_to(repo) or stage.is_relative_to(source):
        raise ValueError('Fresh stage outside the repository and repeat campaign required')
    required = inputs(source)
    index = load(repo/'results/index.json'); old = json.loads(json.dumps(index))
    labels = {c['label'] for c in index['campaigns']}
    if LABEL in labels or not {'font-stress-search', 'updated-cache-examples'} <= labels:
        raise ValueError('Expected preserved original font/revised archives and no prior repeat archive')
    sys.path.insert(0, str(repo/'scripts'))
    from benchlib import bundled_manifest
    bundled_manifest(repo)
    protected = [p for p in repo.rglob('*') if p.is_file()
        and '.git' not in p.relative_to(repo).parts and '__pycache__' not in p.parts
        and not (p.name.endswith(('.tar.gz', '.tgz')) and 'results' in p.relative_to(repo).parts)]
    baseline = {p.relative_to(repo).as_posix(): sha(p) for p in sorted(protected)}
    stage.mkdir(parents=True); (stage/'scripts').mkdir(); adapt(repo, stage, source)
    evidence = Path(tempfile.mkdtemp(prefix='repository-tools-', dir=source))
    for name in TOOLS: shutil.copy2(stage/'scripts'/name, evidence/name)
    shutil.copy2(__file__, evidence/'install-font-stress-rerun.py')
    shutil.copy2(args.docs.resolve(strict=True), evidence/'font-stress-rerun-reproduction.md')
    write(evidence/'adaptation-provenance.json', {'complete': True,
        'original_tool_sha256': {n: baseline['scripts/'+n] for n in TOOLS},
        'files': records(evidence), 'installer_sha256': sha(__file__),
        'scope': 'Append a repeat archive and reuse the unchanged font-confirmation audit with two verified companion campaigns; preserve previous reports and archive records.'})
    destination = stage/'results'/LABEL
    subprocess.run([sys.executable, str(repo/'scripts/archive-campaign.py'), str(source), str(destination), '--label', LABEL], check=True)
    archived = complete(destination/'archive.json')
    index['campaigns'].append({'label': LABEL, 'path': 'results/'+LABEL, 'original_root': archived['original_root'],
        'role': 'font-confirmation-repeat', 'complete': True, 'archive': archived['archive'],
        'files': len(archived['files']), 'raw_bytes': archived['raw_bytes']})
    index.setdefault('analysis_audits', []).append({'suite': 'font-confirmation', 'campaign': LABEL,
        'required_campaigns': ['font-stress-search', 'updated-cache-examples'],
        'cpu': 'confirm-cpu', 'gpu': 'confirm-gpu', 'analysis': 'analysis',
        'scope': 'Repeat of fixed selection, collector, binaries and native pixel proof; independent raw/stdout effects and intervals, all-member integrity required first.'})
    visible = [(source/'FONT-STRESS-RERUN.md', Path('FONT-STRESS-RERUN.md')),
        (source/'SUMMARY-FONT-STRESS-RERUN.md', Path('SUMMARY-FONT-STRESS-RERUN.md')),
        (source/'FONT-STRESS-RERUN.inputs.json', Path('analysis/font-stress-rerun-original-report-inputs.json')),
        (source/'independent-rerun-audit.json', Path('analysis/font-stress-rerun-independent-audit.json')),
        (evidence/'install-font-stress-rerun.py', Path('scripts/install-font-stress-rerun.py')),
        (evidence/'font-stress-rerun-reproduction.md', Path('docs/font-stress-rerun-reproduction.md'))]
    visible += [(p, Path('analysis/font-stress-rerun')/p.relative_to(source/'analysis'))
                for p in sorted((source/'analysis').rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    if (source/'comparison').is_dir():
        visible += [(p, Path('analysis/font-stress-rerun/comparison')/p.relative_to(source/'comparison'))
                    for p in sorted((source/'comparison').rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    for name in ('hardware.json', 'current-workspace-identity.json', 'alias-provenance.json', 'rerun-provenance.json', 'quiet-provenance.json'):
        if (source/name).is_file(): visible.append((source/name, Path('analysis/font-stress-rerun')/name))
    if (source/'rerun-context.md').is_file():
        visible.append((source/'rerun-context.md', Path('analysis/font-stress-rerun/rerun-context.md')))
    visible += [(p, Path('analysis/font-stress-rerun/logs')/p.name)
                for p in sorted(source.iterdir()) if p.is_file()
                and (p.suffix in ('.stdout', '.stderr', '.log') or p.name in
                     ('analyzer-stdout.txt', 'analyzer-stderr.txt', 'analysis-stdout.txt', 'analysis-stderr.txt'))]
    copies = load(repo/'analysis/copy-manifest.json')
    for original, relative in visible:
        if not original.is_file() or (stage/relative).exists() or (repo/relative).exists():
            raise ValueError('New repeat evidence missing or destination exists: ' + str(relative))
        (stage/relative).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(original, stage/relative)
        copies[relative.as_posix()] = {'source': str(original), **info(original)}
    for name in TOOLS: copies['scripts/'+name] = {'source': str(evidence/name), **info(evidence/name)}
    write(stage/'analysis/font-stress-rerun-report-inputs.json', {r.as_posix(): sha(stage/r) for _, r in visible})
    write(stage/'analysis/copy-manifest.json', copies); write(stage/'results/index.json', index)
    addition = '''## Repeated favorable-font measurements

A [fresh repeat](FONT-STRESS-RERUN.md) measures the same frozen master/final
sources, example scenes, three fonts, native pixel proof and balanced schedule.
It was requested because of a background-load concern; overlap with the original
measurement was not established. The original [font study](FONT-STRESS-SEARCH.md),
its numerical report, and its archive remain preserved. See the
[repeat summary](SUMMARY-FONT-STRESS-RERUN.md) and
[reproduction notes](docs/font-stress-rerun-reproduction.md).

'''
    marker = '## Favorable-font confirmation\n'
    (stage/'README.md').write_text(once((repo/'README.md').read_text(), marker, addition+marker))
    assert index['campaigns'][:-1] == old['campaigns']
    assert index['analysis_audits'][:-1] == old['analysis_audits']
    proof = {'schema': 1, 'complete': True, 'installed': False, 'repository': str(repo), 'source': str(source),
        'stage': str(stage), 'installer_sha256': sha(__file__), 'old_repository_file_sha256': baseline,
        'old_campaign_count': len(old['campaigns']), 'old_audit_count': len(old['analysis_audits']),
        'new_labels': [LABEL], 'staged_files': records(stage), 'completed_inputs': {str(p): sha(p) for p in required},
        'policy': 'Preserve original numerical reports/archive/index entries; append one independently auditable repeat; no commit or remote action.'}
    write(stage/'installation-plan.json', proof); print('Reviewable repeat update staged:', stage)
    return proof

def atomic_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.'+destination.name+'-', dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
        with source.open('rb') as original: shutil.copyfileobj(original, stream)
    shutil.copystat(source, temporary); os.replace(temporary, destination)

def install(args, proof):
    repo = args.repository.resolve(strict=True); stage = args.stage.resolve(strict=True)
    if not proof.get('complete') or proof.get('installed') or proof['repository'] != str(repo) or proof['stage'] != str(stage):
        raise ValueError('Completed unchanged uninstalled plan required for this exact repository/stage')
    for relative, digest in proof['old_repository_file_sha256'].items():
        if sha(repo/relative) != digest: raise ValueError('Repository changed after staging: ' + relative)
    for relative, expected in proof['staged_files'].items():
        if info(stage/relative) != expected: raise ValueError('Stage changed after review: ' + relative)
    allowed = {'README.md', 'results/index.json', 'analysis/copy-manifest.json'} | {'scripts/'+n for n in TOOLS}
    for relative in proof['staged_files']:
        if (repo/relative).exists() and relative not in allowed: raise ValueError('Existing destination: ' + relative)
    destination = repo/'results'/LABEL; temporary = destination.with_name('.'+LABEL+'.install-tmp')
    if destination.exists() or temporary.exists(): raise ValueError('Repeat archive destination exists')
    shutil.copytree(stage/'results'/LABEL, temporary); os.replace(temporary, destination)
    for relative in proof['staged_files']:
        if relative == 'results/index.json' or relative.startswith('results/'+LABEL+'/'): continue
        atomic_copy(stage/relative, repo/relative)
    atomic_copy(stage/'results/index.json', repo/'results/index.json')
    for relative, digest in proof['old_repository_file_sha256'].items():
        if relative not in allowed and sha(repo/relative) != digest: raise ValueError('Historical evidence changed: ' + relative)
    proof['installed'] = True; write(stage/'installation-plan.json', proof)
    print('Installed additive font repeat; original reports/archive entries preserved:', repo)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/private/tmp/femtovg-font-stress-rerun-20261002'))
    parser.add_argument('--repository', type=Path, default=Path('/Users/jesse/github/femtovg-outline-cache-bench'))
    parser.add_argument('--stage', type=Path, required=True)
    installed_docs = Path(__file__).resolve().parent.parent/'docs/font-stress-rerun-reproduction.md'
    parser.add_argument('--docs', type=Path, default=installed_docs if installed_docs.exists() else Path('/private/tmp/femtovg-font-stress-rerun-reproduction.md'))
    parser.add_argument('--install', action='store_true'); parser.add_argument('--install-existing', action='store_true')
    args = parser.parse_args()
    if args.install_existing and not args.install: parser.error('--install-existing requires --install')
    proof = load(args.stage/'installation-plan.json') if args.install_existing else stage_update(args)
    if args.install: install(args, proof)

if __name__ == '__main__': main()
