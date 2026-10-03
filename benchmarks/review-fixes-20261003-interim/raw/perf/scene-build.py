#!/usr/bin/env python3
"""Build the byte-preserved scene adapters after glyph timing has stopped."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from verify import graph

ROOT = Path(__file__).resolve().parent
SCENES = Path('/private/tmp/femtovg-review-fixes-scenes')
PRODUCTION = ['src/lib.rs', 'src/text.rs', 'src/text/font.rs', 'src/text/swash_rasterizer.rs']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def verify_source(variant):
    record = json.loads((SCENES / f'source-{variant}.json').read_text())
    source = SCENES / 'source' / variant
    current = {str(p.relative_to(source)): sha(p) for p in source.rglob('*') if p.is_file() and p.name != 'Cargo.lock'}
    expected = {p: h for p, h in record['files'].items() if Path(p).name != 'Cargo.lock'}
    if current != expected:
        raise SystemExit(f'Frozen scene {variant} source changed')
    if variant == 'final':
        frozen = json.loads((ROOT / 'source-finalgenericrestore.json').read_text())['files']
        for path in PRODUCTION:
            if current[path] != frozen[path] or current[path] != sha(Path('/Users/jesse/github/femtovg') / path):
                raise SystemExit(f'Scene final source differs from timed glyph candidate: {path}')

def main():
    builds = ROOT / 'scene-builds'
    builds.mkdir(exist_ok=True)
    (ROOT / 'bin').mkdir(exist_ok=True)
    environment = dict(os.environ, CARGO_TARGET_DIR=str(ROOT / 'target'), CARGO_INCREMENTAL='0')
    graphs = {}
    for variant in ['master', 'final']:
        verify_source(variant)
        manifest = SCENES / 'harness' / variant / 'Cargo.toml'
        lock = manifest.with_name('Cargo.lock')
        if not lock.exists():
            subprocess.run(['cargo', 'generate-lockfile', '--offline', '--manifest-path', str(manifest)], env=environment, check=True)
        for feature in ['default_swash', 'default_no_swash']:
            label = f'{variant}-{feature}'
            command = ['cargo', 'build', '--offline', '--locked', '--release', '--manifest-path', str(manifest), '--features', feature, '--message-format=json']
            print(f'Building scenes {label}', flush=True)
            process = subprocess.run(command, env=environment, capture_output=True, text=True)
            (builds / f'{label}.stderr').write_text(process.stderr)
            (builds / f'{label}.cargo.jsonl').write_text(process.stdout)
            if process.returncode:
                print(process.stderr)
                raise SystemExit(process.returncode)
            artifacts = [json.loads(line) for line in process.stdout.splitlines() if line.startswith('{')]
            femtovg = [x for x in artifacts if x.get('reason') == 'compiler-artifact' and x.get('target', {}).get('name') == 'femtovg']
            expected_source = str(SCENES / 'source' / variant)
            if len(femtovg) != 1 or expected_source not in femtovg[0]['manifest_path']:
                raise SystemExit(f'Wrong scene library origin: {femtovg}')
            executables = [x['executable'] for x in artifacts if x.get('reason') == 'compiler-artifact' and x.get('executable')]
            if len(executables) != 1:
                raise SystemExit(f'Wrong scene executable count: {executables}')
            binary = ROOT / 'bin' / f'scenes-{label}'
            shutil.copy2(executables[0], binary)
            metadata = subprocess.check_output(['cargo', 'metadata', '--offline', '--locked', '--format-version', '1', '--manifest-path', str(manifest), '--features', feature], env=environment, text=True)
            (builds / f'{label}.metadata.json').write_text(metadata)
            normalized = graph(json.loads(metadata))
            if feature in graphs and normalized != graphs[feature]:
                raise SystemExit(f'Scene dependency/features graph differs: {label}')
            graphs.setdefault(feature, normalized)
            record = {'variant': variant, 'feature': feature, 'command': command,
                      'source_manifest': expected_source, 'femtovg_artifact': femtovg[0],
                      'binary_path': str(binary), 'binary_sha256': sha(binary),
                      'lock_sha256': sha(lock), 'dependency_graph_sha256': hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest(),
                      'rustc': subprocess.check_output(['rustc', '-Vv'], text=True),
                      'cargo': subprocess.check_output(['cargo', '-V'], text=True),
                      'profile': {'opt_level': 3, 'debug': False, 'lto': False, 'codegen_units': 16, 'incremental': False, 'panic': 'unwind'},
                      'build_environment': {key: environment.get(key) for key in ['RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_TARGET', 'CARGO_INCREMENTAL', 'CARGO_TARGET_DIR']}}
            (builds / f'{label}.json').write_text(json.dumps(record, indent=2) + '\n')
            verify_source(variant)
            print(f'Built scenes {label}: {record["binary_sha256"][:16]}', flush=True)

if __name__ == '__main__':
    main()
