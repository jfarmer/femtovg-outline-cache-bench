#!/usr/bin/env python3
"""Extract checked font-search/source archives and prepare an honest fresh rerun.

No build, GUI launch or measurement occurs. Generated drivers retain the measured
collection/statistical logic and replace historical executable audit matching
with explicitly recorded fresh frozen-source validation. Historical proofs are
retained; they are never rewritten to describe a new executable.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

VERSIONS = ('master', 'prior', 'updated45', 'final')

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Fresh reproduction adaptation marker changed: ' + repr(old))
    return text.replace(old, new)

def between(text, start, end, replacement):
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError('Fresh reproduction adaptation boundaries changed')
    a, b = text.index(start), text.index(end)
    if a >= b:
        raise ValueError('Reversed adaptation boundaries')
    return text[:a] + replacement + text[b:]

def adapt(search, output, expected):
    collector_source = search / 'replay_campaign.py'
    analyzer_source = search / 'analyze_font_confirm.py'
    collector = between(collector_source.read_text(),
        '    proof_paths = [study / name for name in (',
        '    assets = files(study / \'runtime/assets\')',
        "    frozen_path = study / 'fresh-source-identity.json'\n"
        "    frozen = load(frozen_path)\n"
        "    require(frozen.get('complete') is True and frozen['versions'] == list(ALL_VERSIONS),\n"
        "            'Fresh frozen-source validation is incomplete')\n"
        "    require({v: sources[v]['pure_snapshot'] for v in ALL_VERSIONS} == frozen['pure_sources'],\n"
        "            'Fresh source differs from the archived measured source')\n"
        "    proof_paths = []\n")
    collector = once(collector,
        "            'independent_audits': [info(p) for p in proof_paths],",
        "            'independent_audits': [], 'fresh_source_validation': info(frozen_path),\n"
        "            'validation_scope': 'Fresh locked builds/assets/native oracle and archived pure-source identity; historical independent executable audits are not relabeled',")
    analyzer = between(analyzer_source.read_text(),
        "    independent_native = reader.load(identity['independent_audits'][-1]['path'])",
        '\n\ndef audit_processes(',
        "    require(reader.sha(native['metadata']) == native['metadata_sha256'],\n"
        "            'Fresh native resolved dependency metadata changed')\n"
        "    require(identity['independent_audits'] == [], 'Fresh reproduction must not relabel old independent audits')\n"
        "    reader.check_info(identity['fresh_source_validation'])\n"
        "    frozen = reader.load(identity['fresh_source_validation']['path'])\n"
        "    require(frozen.get('complete') is True and frozen['versions'] == list(VERSIONS),\n"
        "            'Fresh frozen-source validation incomplete')\n"
        "    require({v: identity['sources'][v]['pure_snapshot'] for v in VERSIONS} == frozen['pure_sources'],\n"
        "            'Fresh pure source differs from the archived measured source')\n")
    generated = {'replay_reproduction.py': collector, 'analyze_reproduction.py': analyzer}
    for name, text in generated.items():
        ast.parse(text, filename=name)
        (output / name).write_text(text)
    write(output / 'reproduction-adaptation.json', {
        'complete': True, 'generated_utc': datetime.now(timezone.utc).isoformat(),
        'original_drivers': {p.name: sha(p) for p in (collector_source, analyzer_source)},
        'generated_drivers': {name: sha(output / name) for name in generated},
        'pure_sources': expected,
        'changes': 'Only executable identity validation is adapted: historical independent executable proofs are replaced with explicitly labeled archived pure-source validation; all raw collection, phase/count/pixel checks, schedule and statistics remain unchanged.',
        'validated_scope': 'Preparation and Python syntax only; no fresh build or rerun is implied.'})

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repository', type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--execute-step', choices=('build', 'pixels', 'cpu', 'gpu', 'analyze'),
                        help='Execute previously prepared commands in this output; never recreate preparation')
    args = parser.parse_args()
    repo = args.repository.resolve(strict=True)
    sys.path.insert(0, str(repo / 'scripts'))
    from benchlib import ArchiveStore
    output = args.output.resolve()
    if args.execute_step:
        if not output.is_dir() or output.is_relative_to(repo):
            parser.error('Execution requires an existing preparation outside the repository')
        command_record = json.loads((output / 'reproduction-commands.json').read_text())
        if command_record.get('complete') is not True:
            raise ValueError('Incomplete prepared commands')
        commands = command_record['commands']
        if args.execute_step == 'build':
            subprocess.run(commands['replay_build'], check=True)
            subprocess.run(commands['native_prepare'], check=True)
            with (output / 'native-master-offset-oracle/metadata.json').open('w') as stream:
                subprocess.run(commands['native_metadata'], stdout=stream, check=True)
            subprocess.run(commands['native_build'], check=True)
            subprocess.run(commands['native_record'], check=True)
        else:
            subprocess.run(commands[args.execute_step], check=True)
        return
    if output.exists() or output.is_relative_to(repo):
        parser.error('--output must be fresh and outside the benchmark repository')
    output.mkdir(parents=True)
    store = ArchiveStore(repo)
    verified = [store.inspect('updated-cache-source-bundle', output / 'bundle'),
                store.inspect('font-stress-search', output / 'search')]
    subprocess.run([sys.executable, str(output / 'bundle/scripts/prepare.py'),
                    '--output', str(output / 'runtime')], check=True)
    search = output / 'search'
    measured = json.loads((search / 'pixels/pixels-provenance.json').read_text())
    if measured.get('complete') is not True:
        raise ValueError('Retained measured pixel/source identity is incomplete')
    expected = {v: measured['identity']['sources'][v]['pure_snapshot'] for v in VERSIONS}
    observed = {v: {str(p.relative_to(output / 'runtime/core/snapshots' / v)): sha(p)
                   for p in sorted((output / 'runtime/core/snapshots' / v).rglob('*')) if p.is_file()}
                for v in VERSIONS}
    if expected != observed:
        raise ValueError('Fresh prepared pure sources differ from original measured sources')
    write(output / 'fresh-source-identity.json', {
        'complete': True, 'versions': list(VERSIONS), 'pure_sources': expected,
        'reference': {'path': str(search / 'pixels/pixels-provenance.json'),
                      'sha256': sha(search / 'pixels/pixels-provenance.json')},
        'archive_verification': verified,
        'scope': 'Exact archived four pure snapshots, validated at preparation; this is not an independent audit of future executables.'})
    original_selection = search / 'selection-frozen.json'
    selection = json.loads(original_selection.read_text())
    original_root = Path(store.campaign('font-stress-search')['original_root'])
    for record in selection['fonts']:
        record['path'] = str(search / Path(record['path']).relative_to(original_root))
        if sha(record['path']) != record['sha256'] or Path(record['path']).stat().st_size != record['bytes']:
            raise ValueError('Selected archived font changed: ' + record['label'])
    selection['original_frozen_utc'] = selection['frozen_utc']
    selection['frozen_utc'] = datetime.now(timezone.utc).isoformat()
    selection['relocation_only'] = {'original_sha256': sha(original_selection),
        'scope': 'The same preselected three fonts; only absolute paths and reproduction freeze time are changed.'}
    selection_path = search / 'selection-reproduction.json'
    write(selection_path, selection)
    adapt(search, output, expected)
    oracle = repo / 'benchmarks/revised-cache-oracle/native_offset_oracle.py'
    fonts = [item for record in selection['fonts'] for item in ('--font', record['label'], record['path'])]
    collector = output / 'replay_reproduction.py'
    common = [sys.executable, str(collector), '--study', str(output), '--versions', 'master', 'final',
              '--dpi', '1', '2', '--selection-manifest', str(selection_path), *fonts]
    build = [sys.executable, str(output / 'bundle/scripts/build.py'), 'replay',
             '--runtime', str(output / 'runtime')]
    oracle_root = output / 'native-master-offset-oracle'
    native_manifest = oracle_root / 'runner/Cargo.toml'
    target = output / 'target/native-oracle'
    commands = {'replay_build': build,
        'native_prepare': [sys.executable, str(oracle), 'prepare', '--runtime', str(output / 'runtime'),
                           '--output', str(oracle_root)],
        'native_metadata': ['cargo', 'metadata', '--offline', '--locked', '--format-version', '1',
                            '--manifest-path', str(native_manifest)],
        'native_build': ['cargo', 'build', '--release', '--offline', '--locked',
                        '--manifest-path', str(native_manifest), '--target-dir', str(target)],
        'native_record': [sys.executable, str(oracle), 'record-build', '--root', str(oracle_root),
                          '--binary', str(target / 'release/femtovg-example-outline-review-native-master-offset-oracle'),
                          '--metadata', str(oracle_root / 'metadata.json')],
        'pixels': [*common, '--mode', 'pixels', '--output', str(output / 'rerun-pixels')],
        'cpu': [*common, '--mode', 'cpu', '--blocks', '12', '--trials', '5', '--pixel-proof',
                str(output / 'rerun-pixels/pixels-provenance.json'), '--output', str(output / 'rerun-cpu')],
        'gpu': [*common, '--mode', 'gpu', '--blocks', '12', '--trials', '3', '--pixel-proof',
                str(output / 'rerun-pixels/pixels-provenance.json'), '--output', str(output / 'rerun-gpu')],
        'analyze': [sys.executable, str(output / 'analyze_reproduction.py'), '--cpu', str(output / 'rerun-cpu'),
                    '--gpu', str(output / 'rerun-gpu'), '--control-font', 'Vollkorn-Medium',
                    '--output', str(output / 'rerun-analysis')]}
    write(output / 'reproduction-commands.json', {'complete': True, 'commands': commands,
        'native_metadata_note': 'Save native_metadata stdout verbatim to the native_record --metadata path before recording the build.',
        'scope': 'Commands are prepared, not executed. Build/cache dependencies must be available locally for --offline --locked.'})
    print(output)

if __name__ == '__main__':
    main()
