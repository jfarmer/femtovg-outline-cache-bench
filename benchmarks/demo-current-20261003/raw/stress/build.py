#!/usr/bin/env python3
"""Build frozen public-API specimen binaries only in a coordinated build window."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
SCENES = Path('/private/tmp/femtovg-review-fixes-scenes')
PERF = Path('/private/tmp/femtovg-review-fixes-perf')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_idle():
    probe = subprocess.run(['pgrep', '-x', r'cargo|rustc|clang|clang\+\+|ld|ld.lld|cc|cc1|swift|swiftc|swift-frontend|ninja|cmake'], capture_output=True, text=True)
    assert probe.returncode in [0, 1], probe.stderr
    if probe.returncode == 0:
        raise SystemExit(f'Waiting for unrelated build/compiler/linker processes: {probe.stdout.split()}')


def dependency_graph(meta):
    packages = {p['id']: p for p in meta['packages']}
    identity = lambda key: (packages[key]['name'], packages[key]['version'], packages[key]['source'])
    return sorted((identity(n['id']), sorted(n['features']),
        sorted((identity(d['pkg']), sorted((k['kind'] or '', str(k['target'] or '')) for k in d['dep_kinds'])) for d in n['deps']))
        for n in meta['resolve']['nodes'] if n['id'] != meta['resolve']['root'])


def verify_source(variant):
    source = SCENES / 'source' / variant
    archived = json.loads((SCENES / f'source-{variant}.json').read_text())
    actual = {str(p.relative_to(source)): sha(p) for p in source.rglob('*') if p.is_file() and p.name != 'Cargo.lock'}
    expected = {name: digest for name, digest in archived['files'].items() if Path(name).name != 'Cargo.lock'}
    assert actual == expected, f'Frozen source changed: {variant}'
    return {'source_root': str(source), 'registered_source_record': str(SCENES / f'source-{variant}.json'),
            'registered_source_record_sha256': sha(SCENES / f'source-{variant}.json'), 'all_source_files': actual}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-ready', action='store_true')
    args = parser.parse_args()
    if not args.build_ready:
        raise SystemExit('Hold: root must confirm a coordinated build window.')
    ensure_idle()
    (ROOT / 'builds').mkdir(exist_ok=True)
    (ROOT / 'bin').mkdir(exist_ok=True)
    # Shared compiled dependencies are safe only in this coordinated build window.
    environment = dict(os.environ, CARGO_TARGET_DIR=str(PERF / 'target'), CARGO_INCREMENTAL='0')
    reference_graph = None
    for variant in ['master', 'final']:
        ensure_idle()
        provenance = verify_source(variant)
        manifest = ROOT / 'harness' / variant / 'Cargo.toml'
        old_lock = SCENES / 'harness' / variant / 'Cargo.lock'
        lock = manifest.with_name('Cargo.lock')
        shutil.copy2(old_lock, lock)
        command = ['cargo', 'build', '--offline', '--locked', '--release', '--manifest-path', str(manifest),
                   '--features', 'default_swash', '--message-format=json']
        process = subprocess.run(command, env=environment, capture_output=True, text=True)
        (ROOT / 'builds' / f'{variant}.cargo.jsonl').write_text(process.stdout)
        (ROOT / 'builds' / f'{variant}.stderr').write_text(process.stderr)
        if process.returncode:
            raise SystemExit(process.stderr)
        artifacts = [json.loads(line) for line in process.stdout.splitlines() if line.startswith('{')]
        library = [r for r in artifacts if r.get('reason') == 'compiler-artifact' and r.get('target', {}).get('name') == 'femtovg']
        assert len(library) == 1 and library[0]['manifest_path'] == str(SCENES / 'source' / variant / 'Cargo.toml')
        assert 'swash' in library[0]['features'] and 'textlayout' in library[0]['features']
        executables = [r['executable'] for r in artifacts if r.get('reason') == 'compiler-artifact' and r.get('executable')]
        assert len(executables) == 1
        binary = ROOT / 'bin' / f'hinting-stress-{variant}'
        shutil.copy2(executables[0], binary)
        metadata_command = ['cargo', 'metadata', '--offline', '--locked', '--format-version', '1',
                            '--manifest-path', str(manifest), '--features', 'default_swash']
        raw_meta = subprocess.check_output(metadata_command, env=environment, text=True)
        (ROOT / 'builds' / f'{variant}.metadata.json').write_text(raw_meta)
        graph = dependency_graph(json.loads(raw_meta))
        if reference_graph is None:
            reference_graph = graph
        assert graph == reference_graph, 'Dependency/feature graph differs'
        previous = json.loads((PERF / 'scene-builds' / f'{variant}-default_swash.metadata.json').read_text())
        assert graph == dependency_graph(previous), 'Graph differs from archived public scene study'
        record = {'variant': variant, 'feature': 'default_swash', 'command': command, 'source': provenance,
                  'femtovg_artifact': library[0], 'binary_path': str(binary), 'binary_sha256': sha(binary),
                  'lock_sha256': sha(lock), 'matches_archived_lock': sha(lock) == sha(old_lock),
                  'dependency_graph_sha256': hashlib.sha256(json.dumps(graph, sort_keys=True).encode()).hexdigest(),
                  'harness_sha256': sha(ROOT / 'harness-src/main.rs'),
                  'rustc': subprocess.check_output(['rustc', '-Vv'], text=True),
                  'cargo': subprocess.check_output(['cargo', '-V'], text=True),
                  'profile': {'opt_level': 3, 'lto': False, 'codegen_units': 16, 'debug': False, 'incremental': False, 'panic': 'unwind'},
                  'build_environment': {name: environment.get(name) for name in ['RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_TARGET', 'CARGO_INCREMENTAL', 'CARGO_TARGET_DIR']}}
        (ROOT / 'builds' / f'{variant}.json').write_text(json.dumps(record, indent=2) + '\n')
        assert verify_source(variant) == provenance
        print(f'Built and verified hinting stress {variant}', flush=True)


if __name__ == '__main__':
    main()
