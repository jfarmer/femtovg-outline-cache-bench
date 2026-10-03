#!/usr/bin/env python3
"""Build frozen, distinct harness packages and record actual Cargo artifacts."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source(variant):
    record = json.loads((ROOT / f'source-{variant}.json').read_text())
    source = ROOT / 'source' / variant
    current = {str(p.relative_to(source)): sha(p) for p in source.rglob('*') if p.is_file() and p.name != 'Cargo.lock'}
    expected = {p: h for p, h in record['files'].items() if Path(p).name != 'Cargo.lock'}
    if current != expected:
        raise SystemExit(f'Frozen {variant} source changed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('variants', nargs='+', choices=['master', 'base', 'final', 'ordinary-inline', 'finalgenericrestore'])
    args = parser.parse_args()
    (ROOT / 'builds').mkdir(exist_ok=True)
    (ROOT / 'bin').mkdir(exist_ok=True)
    environment = dict(os.environ, CARGO_TARGET_DIR=str(ROOT / 'target'), CARGO_INCREMENTAL='0')
    for variant in args.variants:
        verify_source(variant)
        manifest = ROOT / 'harness' / variant / 'Cargo.toml'
        lock = manifest.with_name('Cargo.lock')
        if not lock.exists():
            subprocess.run(['cargo', 'generate-lockfile', '--offline', '--manifest-path', str(manifest)], env=environment, check=True)
        for feature in ['swash_only', 'default_swash', 'default_no_swash']:
            label = f'{variant}-{feature}'
            command = ['cargo', 'build', '--offline', '--locked', '--release', '--manifest-path', str(manifest), '--features', feature, '--message-format=json']
            print(f'Building {label}', flush=True)
            process = subprocess.run(command, env=environment, capture_output=True, text=True)
            (ROOT / 'builds' / f'{label}.stderr').write_text(process.stderr)
            (ROOT / 'builds' / f'{label}.cargo.jsonl').write_text(process.stdout)
            if process.returncode:
                print(process.stderr)
                raise SystemExit(process.returncode)
            artifacts = [json.loads(line) for line in process.stdout.splitlines() if line.startswith('{')]
            femtovg = [x for x in artifacts if x.get('reason') == 'compiler-artifact' and x.get('target', {}).get('name') == 'femtovg']
            expected_source = str(ROOT / 'source' / variant)
            if len(femtovg) != 1 or expected_source not in femtovg[0]['manifest_path']:
                raise SystemExit(f'Unexpected local FemtoVG origin for {label}: {femtovg}')
            executables = [(x['target']['name'], x['executable']) for x in artifacts if x.get('reason') == 'compiler-artifact' and x.get('executable')]
            if len(executables) != 3:
                raise SystemExit(f'Unexpected executable count {executables}')
            executable_map = {}
            for name, executable in executables:
                kind = 'warm' if name.startswith('probe-') else ('cold' if name.startswith('cold-') else 'generic')
                binary = ROOT / 'bin' / f'{label}-{kind}'
                shutil.copy2(executable, binary)
                executable_map[kind] = {'artifact_path': executable, 'binary_path': str(binary), 'binary_sha256': sha(binary), 'binary_size': binary.stat().st_size}
            metadata_command = ['cargo', 'metadata', '--offline', '--locked', '--format-version', '1', '--manifest-path', str(manifest), '--features', feature]
            metadata = subprocess.check_output(metadata_command, env=environment, text=True)
            (ROOT / 'builds' / f'{label}.metadata.json').write_text(metadata)
            record = {
                'variant': variant, 'feature': feature, 'command': command,
                'source_manifest': expected_source, 'femtovg_artifact': femtovg[0],
                'executables': executable_map, 'lock_sha256': sha(lock),
                'harness_sha256': sha(ROOT / 'harness-src/main.rs'),
                'rustc': subprocess.check_output(['rustc', '-Vv'], text=True),
                'cargo': subprocess.check_output(['cargo', '-V'], text=True),
                'profile': {'opt_level': 3, 'debug': False, 'lto': False, 'codegen_units': 16, 'incremental': False, 'panic': 'unwind'},
                'build_environment': {key: environment.get(key) for key in ['RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'CARGO_BUILD_TARGET', 'CARGO_INCREMENTAL', 'CARGO_TARGET_DIR']},
            }
            (ROOT / 'builds' / f'{label}.json').write_text(json.dumps(record, indent=2) + '\n')
            verify_source(variant)
            print(f'Built {label}: ' + ', '.join(f'{kind}={entry["binary_sha256"][:16]}' for kind, entry in executable_map.items()), flush=True)


if __name__ == '__main__':
    main()
