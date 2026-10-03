#!/usr/bin/env python3
"""Prepare/record/capture an untimed uncached-master raster-offset oracle."""
import argparse
import csv
import difflib
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

PACKAGE = 'femtovg-example-outline-review-native-master-offset-oracle'
PHASES = {
    'demo': {'first_paint': 1, 'warm': 30, 'zoom_in': 12, 'zoom_out': 12, 'pan': 10},
    'text': {'first_paint': 1, 'warm': 30, 'x_advance': 10, 'x_return': 10, 'y_advance': 10,
             'size_advance': 12, 'size_return': 12, 'reflow': 3},
    'font_variations': {'first_paint': 1, 'warm': 30, 'weight_advance': 6, 'weight_return': 6,
                        'slant_advance': 10, 'slant_return': 10},
    'grid_singleton': {'once': 1}, 'grid_two_phases': {'first': 1, 'second': 1},
    'grid_unique_sizes': {'sweep': 32}, 'grid_unique_variations': {'sweep': 32},
    'grid_pollution': {'hot_first': 1, 'hot_second': 1, 'pollution': 64, 'hot_return': 1},
}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def files(path): return {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}
def write(path, value): path.write_text(json.dumps(value, indent=2) + '\n')
def once(text, old, new, count=1):
    if text.count(old) != count: raise ValueError(f'Expected {count} markers: {old!r}')
    return text.replace(old, new)

def prepare(args):
    runtime = args.runtime.resolve(strict=True)
    root = args.output.resolve()
    if root.exists(): raise ValueError('Fresh oracle output required')
    original = runtime / 'core/replay-sources/master'
    root.mkdir(parents=True)
    source = root / 'replay-sources/master'
    shutil.copytree(original, source)
    path = source / 'src/text.rs'
    before = path.read_text()
    after = once(before, 'subpixel_location: u8,', 'subpixel_location: u32,', 2)
    after = once(after, '                subpixel_location as u8,',
        '                {\n                    let raster_offset = subpixel_location / 10.0;\n'
        '                    if raster_offset == 0.0 { 0 } else { raster_offset.to_bits() }\n                },')
    path.write_text(after)
    original_files, oracle_files = files(original), files(source)
    changed = [name for name in oracle_files if oracle_files[name] != original_files[name]]
    if changed != ['src/text.rs']: raise ValueError(f'Unexpected oracle changes: {changed}')
    shutil.copytree(runtime / 'core/runner', root / 'runner')
    common = root / 'snapshots/master/tests/common'
    common.parent.mkdir(parents=True)
    shutil.copytree(original / 'tests/common', common)
    runner = root / 'runner'
    manifest = runner / 'Cargo.toml'
    manifest.write_text(once(once(manifest.read_text(),
        'name = "femtovg-example-outline-review"', f'name = "{PACKAGE}"'),
        '../replay-sources/current', '../replay-sources/master'))
    lock = runner / 'Cargo.lock'
    lock.write_text(once(lock.read_text(), 'name = "femtovg-example-outline-review"', f'name = "{PACKAGE}"'))
    if files(runner / 'src') != files(runtime / 'core/runner/src'):
        raise ValueError('Oracle runner scene source changed')
    patch = root / 'master-offset-key.patch'
    patch.write_text(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile='master/src/text.rs', tofile='oracle/src/text.rs')))
    proof = {'complete': True, 'label': 'native-master-offset-oracle', 'runtime': str(runtime),
        'original_master_source': str(original), 'original_master_files': original_files,
        'oracle_source': str(source), 'oracle_files': oracle_files, 'changed_files': changed,
        'runner_files': files(runner), 'common_files': files(common), 'package': PACKAGE,
        'driver_sha256': sha(__file__), 'patch_sha256': sha(patch),
        'semantics': 'Master native uncached Swash Render remains unchanged. Only atlas phase identity uses actual raster offset f32 bits, canonicalizing signed zero. No geometry arena/cache, bitmap-borrow fix, target-restoration fix or final signed-bin implementation is copied.'}
    write(root / 'prepare.json', proof)
    print(json.dumps({'root': str(root), 'manifest': str(manifest), 'package': PACKAGE,
        'metadata_command': ['cargo', 'metadata', '--offline', '--locked', '--format-version', '1', '--manifest-path', str(manifest)],
        'build_command': ['cargo', 'build', '--release', '--offline', '--locked', '--manifest-path', str(manifest), '--target-dir', 'TARGET_DIRECTORY']}, indent=2))

def verify(root):
    proof = json.loads((root / 'prepare.json').read_text())
    if not proof['complete'] or files(Path(proof['oracle_source'])) != proof['oracle_files']:
        raise ValueError('Oracle source changed')
    if files(root / 'runner') != proof['runner_files'] or files(root / 'snapshots/master/tests/common') != proof['common_files']:
        raise ValueError('Runner/common/lock changed')
    return proof

def record_build(args):
    root = args.root.resolve(strict=True)
    verify(root)
    binary = args.binary.resolve(strict=True)
    metadata = args.metadata.resolve(strict=True)
    packages = json.loads(metadata.read_text())['packages']
    if [p['version'] for p in packages if p['name'] == 'swash'] != ['0.2.10']:
        raise ValueError('Unexpected Swash version')
    if not any(p['name'] == PACKAGE for p in packages): raise ValueError('Wrong root package')
    write(root / 'build.json', {'complete': True, 'binary': str(binary), 'binary_sha256': sha(binary),
        'metadata': str(metadata), 'metadata_sha256': sha(metadata), 'prepare_sha256': sha(root / 'prepare.json'),
        'compiler': subprocess.check_output(['rustc', '--version'], text=True).strip(),
        'cargo': subprocess.check_output(['cargo', '--version'], text=True).strip()})

def rows(path):
    result = list(csv.DictReader(path.open()))
    expected = {(scene, phase) for scene, phases in PHASES.items() for phase in phases}
    if len(result) != 28 or {(row['scene'], row['phase']) for row in result} != expected:
        raise ValueError('Wrong oracle phase coverage')
    for row in result:
        if int(row['trial']) != 0 or int(row['frames']) != PHASES[row['scene']][row['phase']]:
            raise ValueError('Wrong trial/frame count')
    return {(row['scene'], row['phase']): row for row in result}

def capture(args):
    root = args.root.resolve(strict=True)
    proof = verify(root)
    build = json.loads((root / 'build.json').read_text())
    if not build['complete'] or build['prepare_sha256'] != sha(root / 'prepare.json'):
        raise ValueError('Build/preparation mismatch')
    oracle = Path(build['binary'])
    if sha(oracle) != build['binary_sha256']: raise ValueError('Oracle executable changed')
    master = args.master_binary.resolve(strict=True)
    master_sha = sha(master)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    assets = Path(proof['runtime']) / 'assets'
    fonts = {'stock': assets / 'RobotoFlex-VariableFont.ttf', 'vollkorn': assets / 'Vollkorn-Medium.ttf',
             'ptsans': assets / 'PTSans-Regular.ttf'}
    ledger = {'schema': 1, 'complete': False, 'versions': ['master', 'prior', 'updated45', 'final'],
        'oracle_label': 'native-master-offset-oracle', 'oracle_prepare': {'path': str(root / 'prepare.json'), 'sha256': sha(root / 'prepare.json')},
        'oracle_build': {'path': str(root / 'build.json'), 'sha256': sha(root / 'build.json')},
        'master_binary': {'path': str(master), 'sha256': master_sha}, 'configurations': [], 'launches': [],
        'scope': 'Untimed native uncached-master offset-identity oracle. Final expected counts come from oracle; old-key master counts are separately captured. Prior/updated45 remain old-master parity. Phase-key semantics are an independently constructed actual-offset oracle.'}
    write(output / 'ledger.json', ledger)
    for font, font_file in fonts.items():
        for dpi in (1, 2):
            captured = {}
            for label, binary in [('master', master), ('oracle', oracle)]:
                directory = output / f'{font}-dpi{dpi}-{label}'
                directory.mkdir()
                stdout, stderr = directory / 'stdout.csv', directory / 'stderr.txt'
                env = dict(os.environ)
                env.pop('FEMTOVG_REPLAY_TEXT_FONT', None)
                env['FEMTOVG_REQUIRE_GPU'] = 'metal'
                if font != 'stock': env['FEMTOVG_REPLAY_TEXT_FONT'] = str(font_file)
                command = [str(binary), 'gpu', '1', str(dpi), str(directory / 'pixels')]
                launch = {'font': font, 'dpi': dpi, 'label': label, 'command': command,
                          'font_sha256': sha(font_file), 'stdout': str(stdout), 'stderr': str(stderr), 'complete': False}
                ledger['launches'].append(launch)
                write(output / 'ledger.json', ledger)
                with stdout.open('w') as out, stderr.open('w') as err:
                    subprocess.run(command, env=env, stdout=out, stderr=err, check=True, timeout=args.timeout)
                captured[label] = (rows(stdout), directory / 'pixels')
                launch['complete'] = True
                write(output / 'ledger.json', ledger)
            phases = []
            for scene, scene_phases in PHASES.items():
                for phase, frames in scene_phases.items():
                    old = int(captured['master'][0][scene, phase]['new_atlas_entries'])
                    new = int(captured['oracle'][0][scene, phase]['new_atlas_entries'])
                    snapshot = captured['oracle'][1] / f'{scene}-{phase}.rgba'
                    original = captured['master'][1] / f'{scene}-{phase}.rgba'
                    phases.append({'scene': scene, 'phase': phase, 'frames': frames,
                        'counts': {'master': old, 'prior': old, 'updated45': old, 'final': new},
                        'oracle_snapshot': {'path': str(snapshot), 'bytes': snapshot.stat().st_size, 'sha256': sha(snapshot)},
                        'master_snapshot': {'path': str(original), 'bytes': original.stat().st_size, 'sha256': sha(original)},
                        'oracle_matches_original_master': snapshot.read_bytes() == original.read_bytes()})
            ledger['configurations'].append({'font': font, 'dpi': dpi, 'phases': phases})
            write(output / 'ledger.json', ledger)
    if sha(oracle) != build['binary_sha256'] or sha(master) != master_sha: raise ValueError('Executable changed during capture')
    verify(root)
    ledger['complete'] = True
    write(output / 'ledger.json', ledger)
    print(output / 'ledger.json')

parser = argparse.ArgumentParser(description=__doc__)
sub = parser.add_subparsers(dest='command', required=True)
p = sub.add_parser('prepare'); p.add_argument('--runtime', type=Path, required=True); p.add_argument('--output', type=Path, required=True); p.set_defaults(function=prepare)
p = sub.add_parser('record-build'); p.add_argument('--root', type=Path, required=True); p.add_argument('--binary', type=Path, required=True); p.add_argument('--metadata', type=Path, required=True); p.set_defaults(function=record_build)
p = sub.add_parser('capture'); p.add_argument('--root', type=Path, required=True); p.add_argument('--master-binary', type=Path, required=True); p.add_argument('--output', type=Path, required=True); p.add_argument('--timeout', type=int, default=240); p.set_defaults(function=capture)
args = parser.parse_args(); args.function(args)
