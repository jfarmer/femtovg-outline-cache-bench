#!/usr/bin/env python3
"""Stage an additive favorable-font evidence update, then install a reviewed stage.

Run only after timing, analysis and independent audits finish. Existing dirty
repository content is the baseline: no clean-tree requirement, resets, commits
or remote writes. Archive compression and integrity checks happen during staging.
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

LABEL = 'font-stress-search'
CHANGED_TOOLS = ('verify-results.py', 'archive-study.py')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def load(path): return json.loads(Path(path).read_text())

def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def records(root):
    root = Path(root)
    if any(p.is_symlink() for p in root.rglob('*')):
        raise ValueError('Symlink in staged inputs: ' + str(root))
    return {p.relative_to(root).as_posix(): {'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def once(code, old, new):
    if code.count(old) != 1: raise ValueError('Expected unique adaptation marker: ' + repr(old))
    return code.replace(old, new)

def complete(path):
    record = load(path)
    if record.get('complete') is not True: raise ValueError('Completed evidence required: ' + str(path))
    return record

def inputs(source):
    required = [source/'confirm-cpu/cpu-provenance.json', source/'confirm-gpu/gpu-provenance.json',
        source/'pixels/pixels-provenance.json', source/'selection-frozen.json',
        source/'analysis/summary.json', source/'analysis/raw-audit.json', source/'analysis/analysis-inputs.json',
        source/'independent-confirmation-audit.json', source/'FONT-STRESS-SEARCH.inputs.json']
    for path in required: complete(path)
    selection = load(source/'selection-frozen.json')
    if selection['confirmation']['versions'] != ['master', 'final']:
        raise ValueError('Confirmation must compare frozen master and final')
    reference = None
    for mode, trials in (('cpu', 5), ('gpu', 3)):
        data = load(source/f'confirm-{mode}/{mode}-provenance.json')
        if data['versions'] != ['master', 'final'] or data['blocks'] != 12 or data['trials_per_process'] != trials or data['exploratory']:
            raise ValueError('Unexpected complete confirmation protocol: ' + mode)
        if set(data['dpis']) != {1, 2} or len(data['fonts']) != 3:
            raise ValueError('Expected three selected fonts and both DPRs')
        proof = data['pixel_proof']
        if Path(proof['path']) != source/'pixels/pixels-provenance.json' or sha(proof['path']) != proof['sha256']:
            raise ValueError('Confirmation pixel proof changed')
        if reference is not None and reference != data['identity']:
            raise ValueError('CPU/GPU source/build identities differ')
        reference = data['identity']
    if load(source/'pixels/pixels-provenance.json')['identity'] != reference:
        raise ValueError('Pixel/timing identities differ')
    analysis = load(source/'analysis/analysis-inputs.json')
    for record in [*analysis['inputs'].values(), *analysis['outputs'].values()]:
        if isinstance(record, dict) and {'path', 'sha256'} <= record.keys():
            if sha(record['path']) != record['sha256'] or ('bytes' in record and Path(record['path']).stat().st_size != record['bytes']):
                raise ValueError('Analysis input/output changed: ' + record['path'])
    report = load(source/'FONT-STRESS-SEARCH.inputs.json')
    for original, record in report['files'].items():
        path = Path(original)
        if not path.is_absolute(): path = source/path
        expected = record['sha256'] if isinstance(record, dict) else record
        if sha(path) != expected or (isinstance(record, dict) and 'bytes' in record and path.stat().st_size != record['bytes']):
            raise ValueError('Report input changed: ' + str(path))
    return required

def adapt(repo, stage, source):
    code = (repo/'scripts/verify-results.py').read_text()
    code = once(code, "('revised-cache-report-inputs.json','revised_cache_report_inputs')",
        "('revised-cache-report-inputs.json','revised_cache_report_inputs'),('font-stress-report-inputs.json','font_stress_report_inputs')")
    code = once(code, '    materialize=set(campaigns) if selected else set()\n',
        '    # Audit companions are verified/extracted without selecting their other audit plans.\n'
        '    for audit in selected:\n'
        "        for label in audit.get('required_campaigns',[]):\n"
        '            store.campaign(label)\n'
        '            if label not in campaigns:campaigns.append(label)\n'
        '    materialize=set(campaigns) if selected else set()\n')
    marker = '        else:raise ValueError(f\'Unknown audit suite: {audit["suite"]}\')'
    code = once(code, marker,
        "        elif audit['suite']=='font-confirmation':\n"
        "            command += [str(REPO/'scripts/independent_font_confirmation_audit.py'),'--root',str(root)]\n" + marker)
    code = once(code,
        "statistical_scope='Selected modern replay/app cohorts declared in analysis_audits; historical campaigns retain exact records and are checksum verified'",
        "statistical_scope='Selected replay/app/font-confirmation cohorts declared in analysis_audits; historical campaigns retain exact records and are checksum verified'")
    archive = (repo/'scripts/archive-study.py').read_text()
    marker = "]\n\n\ndef main():"
    archive = once(archive, marker,
        f"    ({LABEL!r}, {str(source)!r}, 'favorable-font-confirmation'),\n" + marker)
    for name, text in (('verify-results.py', code), ('archive-study.py', archive)):
        ast.parse(text, filename=name)
        (stage/'scripts'/name).write_text(text)

def stage_update(args):
    source = args.source.resolve(strict=True); repo = args.repository.resolve(strict=True); stage = args.stage.resolve()
    if stage.exists() or stage.is_relative_to(repo) or stage.is_relative_to(source):
        raise ValueError('Stage must be fresh and outside the repository and source campaign')
    required = inputs(source)
    index = load(repo/'results/index.json'); old_index = json.loads(json.dumps(index))
    labels = {entry['label'] for entry in index['campaigns']}
    if LABEL in labels or not {'updated-cache-examples', 'updated-cache-source-bundle'} <= labels:
        raise ValueError('Expected preserved revised archives and no prior font-stress archive')
    sys.path.insert(0, str(repo/'scripts'))
    from benchlib import bundled_manifest
    bundled_manifest(repo)
    # Freeze all existing visible files and archive manifests, including dirty
    # additions. Compressed historical archives are never destinations of this
    # installer; their index records are preserved verbatim and verified later.
    protected = [p for p in repo.rglob('*') if p.is_file()
        and '.git' not in p.relative_to(repo).parts and '__pycache__' not in p.parts
        and not (p.name.endswith(('.tar.gz', '.tgz')) and 'results' in p.relative_to(repo).parts)]
    baseline = {p.relative_to(repo).as_posix(): sha(p) for p in sorted(protected)}
    stage.mkdir(parents=True); (stage/'scripts').mkdir()
    adapt(repo, stage, source)
    helper = args.helper.resolve(strict=True); doc = args.docs.resolve(strict=True)
    auditor = source/'independent_font_confirmation_audit.py'
    ast.parse(helper.read_text()); ast.parse(auditor.read_text())
    shutil.copy2(helper, stage/'scripts/prepare-font-stress.py')
    # Retain generated tools in the new campaign before archiving so the visible
    # copy manifest resolves every installed byte to independently checked input.
    evidence = Path(tempfile.mkdtemp(prefix='repository-tools-', dir=source))
    for name in (*CHANGED_TOOLS, 'prepare-font-stress.py'):
        shutil.copy2(stage/'scripts'/name, evidence/name)
    shutil.copy2(Path(__file__), evidence/'install-font-stress.py')
    shutil.copy2(doc, evidence/'font-stress-reproduction.md')
    write(evidence/'adaptation-provenance.json', {'complete': True,
        'original_tool_sha256': {name: baseline['scripts/'+name] for name in CHANGED_TOOLS},
        'files': records(evidence), 'installer_sha256': sha(__file__),
        'scope': 'One additive campaign/audit, required verified cross-campaign identity references, fresh reproduction helper; all historical audit behavior retained.'})
    destination = stage/'results'/LABEL
    subprocess.run([sys.executable, str(repo/'scripts/archive-campaign.py'), str(source), str(destination), '--label', LABEL], check=True)
    archive = complete(destination/'archive.json')
    index['campaigns'].append({'label': LABEL, 'path': 'results/'+LABEL, 'original_root': archive['original_root'],
        'role': 'favorable-font-confirmation', 'complete': True, 'archive': archive['archive'],
        'files': len(archive['files']), 'raw_bytes': archive['raw_bytes']})
    index.setdefault('analysis_audits', []).append({'suite': 'font-confirmation', 'campaign': LABEL,
        'required_campaigns': ['updated-cache-examples'],
        'cpu': 'confirm-cpu', 'gpu': 'confirm-gpu', 'analysis': 'analysis',
        'scope': 'Independent raw/stdout effects and intervals; every archive byte checked first; omitted executable bytes represented by preserved provenance.'})
    copies = load(repo/'analysis/copy-manifest.json')
    visible = [(source/'FONT-STRESS-SEARCH.md', Path('FONT-STRESS-SEARCH.md')),
        (source/'SUMMARY-FONT-STRESS.md', Path('SUMMARY-FONT-STRESS.md')),
        (source/'FONT-STRESS-SEARCH.inputs.json', Path('analysis/font-stress-original-report-inputs.json')),
        (source/'selection-frozen.json', Path('analysis/font-stress-selection.json')),
        (source/'independent-confirmation-audit.json', Path('analysis/font-stress-independent-confirmation-audit.json')),
        (source/'reproduction-validation/validation.json', Path('analysis/font-stress-reproduction-validation.json')),
        (source/'analyze_font_confirm.py', Path('benchmarks/font-stress/analyze_font_confirm.py')),
        (source/'replay_campaign.py', Path('benchmarks/font-stress/replay_campaign.py')),
        (source/'screen.py', Path('benchmarks/font-stress/screen.py')),
        (auditor, Path('scripts/independent_font_confirmation_audit.py')),
        (evidence/'install-font-stress.py', Path('scripts/install-font-stress.py')),
        (evidence/'font-stress-reproduction.md', Path('docs/font-stress-reproduction.md'))]
    visible += [(p, Path('analysis/font-stress-confirmation')/p.relative_to(source/'analysis'))
                for p in sorted((source/'analysis').rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    visible += [(source/'supporting'/name, Path('analysis/font-stress-confirmation')/name)
                for name in ('font-inspection.csv', 'font-inspection.json', 'search-metrics.csv')]
    visible.append((source/'hardware.json', Path('analysis/font-stress-confirmation/hardware.json')))
    for original, relative in visible:
        destination = stage/relative
        if not original.is_file() or destination.exists() or (repo/relative).exists():
            raise ValueError('New visible evidence missing or destination exists: ' + str(relative))
        destination.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(original, destination)
        copies[relative.as_posix()] = {'source': str(original), 'sha256': sha(original), 'bytes': original.stat().st_size}
    for name in (*CHANGED_TOOLS, 'prepare-font-stress.py'):
        original = evidence/name
        copies['scripts/'+name] = {'source': str(original), 'sha256': sha(original), 'bytes': original.stat().st_size}
    write(stage/'analysis/font-stress-report-inputs.json', {r.as_posix(): sha(stage/r) for _, r in visible})
    write(stage/'analysis/copy-manifest.json', copies); write(stage/'results/index.json', index)
    addition = '''## Favorable-font confirmation

The [font study](FONT-STRESS-SEARCH.md) records a retained 56-face exploratory
search followed by fresh frozen master/final measurements of Rye, Doulos SIL
and Vollkorn in the existing example scenes. [Summary](SUMMARY-FONT-STRESS.md),
all raw attempts, native pixels, font licenses, and independent statistical
checks are preserved. These are selected favorable examples. See
[reproduction](docs/font-stress-reproduction.md) for checked extraction and fresh
locked builds, and the report for the actual reproduction validation scope.

'''
    marker = '## Verify the retained evidence offline\n'
    (stage/'README.md').write_text(once((repo/'README.md').read_text(), marker, addition+marker))
    assert index['campaigns'][:-1] == old_index['campaigns']
    assert index['analysis_audits'][:-1] == old_index['analysis_audits']
    proof = {'schema': 1, 'complete': True, 'installed': False, 'source': str(source),
        'repository': str(repo), 'stage': str(stage), 'installer_sha256': sha(__file__),
        'old_repository_file_sha256': baseline, 'old_campaign_count': len(old_index['campaigns']),
        'old_audit_count': len(old_index['analysis_audits']), 'new_labels': [LABEL],
        'staged_files': records(stage), 'completed_inputs': {str(p): sha(p) for p in required},
        'policy': 'Freeze the current dirty repository as baseline; append one campaign/audit; preserve historical archive/index records and all other files; no commit or remote action.'}
    write(stage/'installation-plan.json', proof)
    print('Reviewable additive font-stress update staged:', stage)
    return proof

def atomic_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.'+destination.name+'-', dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
        with source.open('rb') as origin: shutil.copyfileobj(origin, stream)
    shutil.copystat(source, temporary); os.replace(temporary, destination)

def install(args, proof):
    repo = args.repository.resolve(strict=True); stage = args.stage.resolve(strict=True)
    if not proof.get('complete') or proof.get('installed') or proof['repository'] != str(repo) or proof['stage'] != str(stage):
        raise ValueError('Completed unchanged uninstalled plan required for this exact repository/stage')
    for relative, digest in proof['old_repository_file_sha256'].items():
        if sha(repo/relative) != digest: raise ValueError('Repository changed after staging: ' + relative)
    for relative, expected in proof['staged_files'].items():
        if sha(stage/relative) != expected['sha256'] or (stage/relative).stat().st_size != expected['bytes']:
            raise ValueError('Stage changed after review: ' + relative)
    allowed = {'README.md', 'results/index.json', 'analysis/copy-manifest.json'} | {'scripts/'+n for n in CHANGED_TOOLS}
    for relative in proof['staged_files']:
        if (repo/relative).exists() and relative not in allowed: raise ValueError('Existing destination: ' + relative)
    destination = repo/'results'/LABEL; temporary = destination.with_name('.'+LABEL+'.install-tmp')
    if destination.exists() or temporary.exists(): raise ValueError('New archive destination exists')
    shutil.copytree(stage/'results'/LABEL, temporary); os.replace(temporary, destination)
    for relative in proof['staged_files']:
        if relative == 'results/index.json' or relative.startswith('results/'+LABEL+'/'): continue
        atomic_copy(stage/relative, repo/relative)
    atomic_copy(stage/'results/index.json', repo/'results/index.json')
    for relative, digest in proof['old_repository_file_sha256'].items():
        if relative not in allowed and sha(repo/relative) != digest: raise ValueError('Historical input changed: ' + relative)
    proof['installed'] = True; write(stage/'installation-plan.json', proof)
    print('Installed one font-stress campaign/audit; previous evidence preserved:', repo)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/private/tmp/femtovg-font-stress-search-20261002'))
    parser.add_argument('--repository', type=Path, default=Path('/Users/jesse/github/femtovg-outline-cache-bench'))
    parser.add_argument('--stage', type=Path, required=True)
    installed_helper = Path(__file__).resolve().with_name('prepare-font-stress.py')
    installed_docs = Path(__file__).resolve().parent.parent/'docs/font-stress-reproduction.md'
    parser.add_argument('--helper', type=Path, default=installed_helper if installed_helper.exists() else Path('/private/tmp/femtovg-prepare-font-stress.py'))
    parser.add_argument('--docs', type=Path, default=installed_docs if installed_docs.exists() else Path('/private/tmp/femtovg-font-stress-reproduction.md'))
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--install-existing', action='store_true')
    args = parser.parse_args()
    if args.install_existing and not args.install: parser.error('--install-existing requires --install')
    proof = load(args.stage/'installation-plan.json') if args.install_existing else stage_update(args)
    if args.install: install(args, proof)

if __name__ == '__main__': main()
