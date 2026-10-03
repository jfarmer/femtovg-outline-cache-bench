#!/usr/bin/env python3
"""Run unchanged, verified replay binaries with arbitrary font files.

Exploratory timing is explicitly separate from balanced confirmation. Pixels are
captured separately, including the independent native actual-offset reference.
No builds, source changes, downloads, windows, statistics or retries are made.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

DEFAULT_STUDY = Path('/private/tmp/femtovg-updated-cache-bench-20261002')
ALL_VERSIONS = ('master', 'prior', 'updated45', 'final')
PHASES = {
    'demo': {'first_paint': 1, 'warm': 30, 'zoom_in': 12, 'zoom_out': 12, 'pan': 10},
    'text': {'first_paint': 1, 'warm': 30, 'x_advance': 10, 'x_return': 10,
             'y_advance': 10, 'size_advance': 12, 'size_return': 12, 'reflow': 3},
    'font_variations': {'first_paint': 1, 'warm': 30, 'weight_advance': 6,
                        'weight_return': 6, 'slant_advance': 10, 'slant_return': 10},
    'grid_singleton': {'once': 1}, 'grid_two_phases': {'first': 1, 'second': 1},
    'grid_unique_sizes': {'sweep': 32}, 'grid_unique_variations': {'sweep': 32},
    'grid_pollution': {'hot_first': 1, 'hot_second': 1, 'pollution': 64, 'hot_return': 1},
}
FIELDS = ['scene', 'phase', 'trial', 'frames', 'draw_us', 'submit_us',
          'complete_us', 'new_atlas_entries']
RESULT_FIELDS = ['backend', 'font', 'dpi', 'block', 'version', *FIELDS]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def info(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}


def write(path, data):
    # Persist an incomplete record before each process and an accepted record
    # afterward. Failed/timeout attempts keep their raw stdout and stderr.
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2) + '\n')
    temporary.replace(path)


def williams(n):
    base = [0]
    for i in range(1, n):
        base.append((i + 1) // 2 if i % 2 else n - i // 2)
    rows = [tuple((v + shift) % n for v in base) for shift in range(n)]
    if n % 2:
        rows += [tuple(reversed(row)) for row in rows]
    positions = Counter((p, v) for row in rows for p, v in enumerate(row))
    predecessors = Counter((a, b) for row in rows for a, b in zip(row, row[1:]))
    require(len(set(positions.values())) == 1, 'Unbalanced Williams positions')
    require(len(predecessors) == n * (n - 1) and len(set(predecessors.values())) == 1,
            'Unbalanced Williams directed predecessors')
    return rows


def parse_rows(stdout, trials):
    reader = csv.DictReader(io.StringIO(stdout))
    require(reader.fieldnames == FIELDS, 'Unexpected replay CSV fields')
    rows = list(reader)
    expected = {(t, s, p) for t in range(trials) for s, phases in PHASES.items() for p in phases}
    seen = set()
    for row in rows:
        key = (int(row['trial']), row['scene'], row['phase'])
        require(key in expected and key not in seen, f'Unexpected/duplicate replay row: {key}')
        seen.add(key)
        frames = int(row['frames'])
        require(frames == PHASES[key[1]][key[2]], f'Unexpected frame count: {key}')
        count = int(row['new_atlas_entries'])
        require(count >= 0, f'Negative atlas count: {key}')
        if key[1].startswith('grid_'):
            require(count == 94 * frames, f'Controlled grid lost distinct atlas keys: {key}: {count}')
        values = [float(row[name]) for name in ('draw_us', 'submit_us', 'complete_us')]
        require(all(math.isfinite(v) and v >= 0 for v in values) and values == sorted(values),
                f'Invalid cumulative timing: {key}')
    require(seen == expected, f'Missing replay rows: {expected - seen}')
    return rows


def counts(rows):
    return {(r['scene'], r['phase'], int(r['trial'])): int(r['new_atlas_entries']) for r in rows}


def input_identity(study):
    core = study / 'runtime/core'
    build_path = core / 'replay-build-provenance.json'
    build = load(build_path)
    require(build.get('complete') is True and set(build['variants']) == set(ALL_VERSIONS),
            'Original four-version build is incomplete')
    require(files(core / 'runner/src') == build['runner_source'], 'Original drawing source changed')
    require(sha(core / 'runner/Cargo.lock') == build['resolved_lock_sha256'], 'Original locked graph changed')
    binaries, sources = {}, {}
    for version in ALL_VERSIONS:
        record = build['variants'][version]
        require(record.get('complete') is True, f'Build incomplete: {version}')
        binary = info(Path(record['binary']))
        require(binary['sha256'] == record['binary_sha256'], f'Wrong existing binary: {version}')
        pure, timed = files(core / 'snapshots' / version), files(core / 'replay-sources' / version)
        require(pure == record['pure_source_files'] and timed == record['timed_source_files'],
                f'Original frozen source changed: {version}')
        binaries[version] = binary
        sources[version] = {'pure_snapshot': pure, 'timed_source': timed}
    prep_path = study / 'native-master-offset-oracle/prepare.json'
    native_build_path = study / 'native-master-offset-oracle/build.json'
    prep, native_build = load(prep_path), load(native_build_path)
    require(prep.get('complete') is True and native_build.get('complete') is True,
            'Native oracle prepare/build incomplete')
    require(sha(prep_path) == native_build['prepare_sha256'], 'Native oracle preparation changed')
    require(files(Path(prep['oracle_source'])) == prep['oracle_files'], 'Native oracle source changed')
    require(prep['original_master_files'] == sources['master']['timed_source'], 'Native oracle master differs')
    require(files(study / 'native-master-offset-oracle/runner') == prep['runner_files'],
            'Native oracle runner source/lock changed')
    require(sha(Path(native_build['metadata'])) == native_build['metadata_sha256'],
            'Native oracle resolved metadata changed')
    oracle = info(Path(native_build['binary']))
    require(oracle['sha256'] == native_build['binary_sha256'], 'Wrong native oracle binary')
    proof_paths = [study / name for name in (
        'independent-source-build-audit.json', 'independent-native-offset-oracle-source-audit.json',
        'independent-native-offset-oracle-build-audit.json')]
    for path in proof_paths:
        require(load(path).get('complete') is True, f'Incomplete prior independent audit: {path}')
    independent_native = load(proof_paths[-1])
    require(independent_native['binary'] == oracle and
            independent_native['build_proof_sha256'] == sha(native_build_path) and
            independent_native['prepare_sha256'] == sha(prep_path), 'Native independent build proof changed')
    assets = files(study / 'runtime/assets')
    preparation_path = study / 'runtime/prepare-provenance.json'
    preparation = load(preparation_path)
    expected_assets = {name[len('assets/'):]: r['sha256'] for name, r in preparation['prepared_files'].items()
                       if name.startswith('assets/')}
    require(assets == expected_assets, 'Compiled-in scene asset files differ from frozen preparation')
    return {'binaries': binaries, 'oracle_binary': oracle, 'sources': sources,
            'assets': assets, 'compiler': build['compiler'], 'cargo': build['cargo'],
            'build_provenance': info(build_path), 'native_build_provenance': info(native_build_path),
            'native_prepare_provenance': info(prep_path), 'prepare_provenance': info(preparation_path),
            'independent_audits': [info(p) for p in proof_paths],
            'runner_source': build['runner_source'], 'resolved_lock_sha256': build['resolved_lock_sha256']}


def pixel_phase_records(captured, font, dpi, versions):
    records = []
    snapshot_names = {f'{s}-{p}.rgba' for s, phases in PHASES.items() for p in phases}
    for version, (_, directory) in captured.items():
        require({p.name for p in directory.iterdir()} == snapshot_names, f'Wrong snapshots: {version}')
    for scene, phases in PHASES.items():
        for phase, frames in phases.items():
            name = f'{scene}-{phase}.rgba'
            width, height = (800, 700) if scene == 'font_variations' else (1000, 600)
            snapshots, phase_counts = {}, {}
            for version, (rows, directory) in captured.items():
                path = directory / name
                require(path.stat().st_size == width * height * 4, f'Wrong RGBA dimensions: {path}')
                snapshots[version] = info(path)
                phase_counts[version] = counts(rows)[scene, phase, 0]
            for version in versions:
                reference = 'oracle' if version == 'final' else 'master'
                require(snapshots[version]['sha256'] == snapshots[reference]['sha256'],
                        f'Native/reference RGBA mismatch: {font}/DPR{dpi}/{version}/{name}')
                require(phase_counts[version] == phase_counts[reference],
                        f'Native/reference atlas mismatch: {font}/DPR{dpi}/{version}/{name}')
            a = Path(snapshots['master']['path']).read_bytes()
            b = Path(snapshots['oracle']['path']).read_bytes()
            changed = [i for i in range(width * height) if a[i * 4:i * 4 + 4] != b[i * 4:i * 4 + 4]]
            records.append({'scene': scene, 'phase': phase, 'frames': frames,
                            'counts': phase_counts, 'snapshots': snapshots,
                            'native_matches_original_master': not changed,
                            'original_master_changed_pixels': len(changed),
                            'original_master_change_bounds': None if not changed else
                            [min(i % width for i in changed), min(i // width for i in changed),
                             max(i % width for i in changed), max(i // width for i in changed)]})
    return records


def pixel_expectations(path, identity, fonts, dpis, versions):
    proof = load(path)
    require(proof.get('complete') is True and proof['mode'] == 'pixels', 'Completed pixel campaign required')
    require(proof['identity'] == identity, 'Pixel campaign source/build identities differ')
    require(set(versions) <= set(proof['versions']), 'Pixel campaign did not check every selected version')
    for font, record in fonts.items():
        require(proof['font_files'].get(font) == record, f'Pixel campaign font differs: {font}')
    selected = {}
    for config in proof['pixel_configurations']:
        key = (config['font'], config['dpi'])
        require(key not in selected, f'Duplicate pixel configuration: {key}')
        selected[key] = {(r['scene'], r['phase']): r['counts'] for r in config['phases']}
        # Reverify the retained bytes once before timing, outside measurements.
        for row in config['phases']:
            for record in row['snapshots'].values():
                require(info(record['path']) == record, 'Retained pixel proof bytes changed')
    require(all((font, dpi) in selected for font in fonts for dpi in dpis), 'Missing selected font/DPR pixels')
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('cpu', 'gpu', 'pixels'), required=True)
    parser.add_argument('--study', type=Path, default=DEFAULT_STUDY)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--font', action='append', nargs=2, metavar=('LABEL', 'PATH'), required=True)
    parser.add_argument('--versions', nargs='+', choices=ALL_VERSIONS, default=list(ALL_VERSIONS))
    parser.add_argument('--dpi', '--dpis', dest='dpis', nargs='+', type=int, choices=(1, 2), default=[2])
    parser.add_argument('--blocks', type=int, default=12)
    parser.add_argument('--trials', type=int)
    parser.add_argument('--exploratory', action='store_true', help='Allow small timing batches without a pixel proof')
    parser.add_argument('--pixel-proof', type=Path, help='Completed pixels-provenance.json, required for confirmation')
    parser.add_argument('--selection-manifest', type=Path, help='Retained preconfirmation font selection/rationale')
    parser.add_argument('--gpu-backend', default='metal')
    parser.add_argument('--timeout', type=int, default=240)
    args = parser.parse_args()
    require(len(args.versions) >= 2 and len(set(args.versions)) == len(args.versions), 'Choose distinct versions')
    require(args.blocks > 0 and args.timeout > 0 and (args.trials is None or args.trials > 0), 'Positive counts required')
    require(len(set(args.dpis)) == len(args.dpis), 'Duplicate DPR factors')
    labels = [label for label, _ in args.font]
    require(len(set(labels)) == len(labels) and all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', x) for x in labels),
            'Use unique safe font labels')
    orders = williams(len(args.versions))
    if args.mode != 'pixels' and not args.exploratory:
        require(args.blocks % len(orders) == 0, 'Confirmation must include whole Williams cycles')
        require(args.pixel_proof is not None, 'Confirmation requires --pixel-proof from a separate pixel campaign')
    study = args.study.resolve(strict=True)
    identity = input_identity(study)
    fonts = {label: info(Path(path)) for label, path in args.font}
    expected = pixel_expectations(args.pixel_proof, identity, fonts, args.dpis, args.versions) if args.pixel_proof else None
    pixel_proof_info = info(args.pixel_proof) if args.pixel_proof else None
    selection_info = info(args.selection_manifest) if args.selection_manifest else None
    output = args.output.resolve()
    require(not output.exists(), 'Fresh output directory required; failed attempts are retained, never retried in place')
    output.mkdir(parents=True)
    run_directory = output / f'{args.mode}-runs'
    run_directory.mkdir()
    provenance_path = output / f'{args.mode}-provenance.json'
    csv_path = output / f'{args.mode}-results.csv'
    backend = 'gpu' if args.mode == 'pixels' else args.mode
    blocks = 1 if args.mode == 'pixels' else args.blocks
    trials = 1 if args.mode == 'pixels' else args.trials or (5 if backend == 'cpu' else 3)
    provenance = {'complete': False, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'mode': args.mode, 'backend': backend, 'exploratory': args.exploratory,
        'blocks': blocks, 'trials_per_process': trials, 'versions': args.versions,
        'fonts': labels, 'dpis': args.dpis, 'font_files': fonts, 'identity': identity,
        'driver': info(Path(__file__)), 'platform': platform.platform(), 'phases': PHASES,
        'pixel_proof': pixel_proof_info, 'selection_manifest': selection_info,
        'primary_outcome': 'Absolute demo first_paint draw_us difference final versus master; other phases/backend endpoints retained',
        'scope': 'Unchanged 19 example phases and nine controlled phases; regular font override only; variation controls always Roboto',
        'measurement': 'All raw trials retained; draw/submit/complete cumulative microseconds/frame; use process medians then paired block effects',
        'retention': 'No retries, timing exclusions, winsorization, or automatic font selection; incomplete failures retained',
        'order_method': 'Williams version orders; font/DPR configuration rotates by block; independent confirmation after exploration',
        'fixed_environment': {'FEMTOVG_REQUIRE_GPU': args.gpu_backend},
        'order': [], 'launches': [], 'count_comparisons': [], 'pixel_configurations': []}
    write(provenance_path, provenance)
    with csv_path.open('x', newline='') as stream:
        csv.DictWriter(stream, fieldnames=RESULT_FIELDS).writeheader()
    env = dict(os.environ)
    for name in ('FEMTOVG_REPLAY_TEXT_FONT', 'SLINT_FONT_PATH', 'SLINT_DEFAULT_FONT', 'MTL_SHADER_CACHE_SIZE'):
        env.pop(name, None)
    env['FEMTOVG_REQUIRE_GPU'] = args.gpu_backend
    configurations = [(font, dpi) for dpi in args.dpis for font in labels]
    for block_index in range(blocks):
        offset = block_index % len(configurations)
        block_order = []
        provenance['order'].append(block_order)
        for font, dpi in configurations[offset:] + configurations[:offset]:
            order = [args.versions[i] for i in orders[(block_index + configurations.index((font, dpi))) % len(orders)]]
            if args.mode == 'pixels':
                order = ['master'] + [v for v in order if v != 'master'] + ['oracle']
            captured = {}
            for version in order:
                label = f'{block_index + 1:02}-{font}-dpi{dpi}-{version}'
                block_order.append(label)
                binary = identity['oracle_binary'] if version == 'oracle' else identity['binaries'][version]
                launch_env = dict(env, FEMTOVG_REPLAY_TEXT_FONT=fonts[font]['path'])
                command = [binary['path'], backend, str(trials), str(dpi)]
                destination = run_directory / f'{label}-pixels'
                if args.mode == 'pixels':
                    command.append(str(destination))
                launch = {'label': label, 'block': block_index + 1, 'font': font, 'dpi': dpi, 'version': version,
                          'command': command, 'environment': {'FEMTOVG_REPLAY_TEXT_FONT': fonts[font]['path']},
                          'cwd': str(study / 'runtime/core'), 'validated': False,
                          'stdout': str(run_directory / f'{label}.stdout.csv'),
                          'stderr': str(run_directory / f'{label}.stderr.txt')}
                provenance['launches'].append(launch)
                write(provenance_path, provenance)
                try:
                    with Path(launch['stdout']).open('x') as out, Path(launch['stderr']).open('x') as err:
                        completed = subprocess.run(command, cwd=launch['cwd'], env=launch_env,
                                                   stdout=out, stderr=err, timeout=args.timeout)
                    launch['exit_code'] = completed.returncode
                    require(completed.returncode == 0, f'Process failed: {label}: {completed.returncode}')
                    require(info(binary['path']) == binary, f'Executable changed: {version}')
                    rows = parse_rows(Path(launch['stdout']).read_text(), trials)
                    captured[version] = (rows, destination)
                    launch.update(validated=True, rows=len(rows), stdout_info=info(launch['stdout']), stderr_info=info(launch['stderr']))
                    with csv_path.open('a', newline='') as stream:
                        csv.DictWriter(stream, fieldnames=RESULT_FIELDS).writerows(
                            {'backend': backend, 'font': font, 'dpi': dpi, 'block': block_index + 1,
                             'version': version, **row} for row in rows)
                    print(f'{args.mode} block {block_index + 1}/{blocks} {font} DPR{dpi} {version}: {len(rows)} rows', flush=True)
                except Exception as error:
                    launch['failure'] = f'{type(error).__name__}: {error}'
                    raise
                finally:
                    write(provenance_path, provenance)
            if args.mode == 'pixels':
                records = pixel_phase_records(captured, font, dpi, args.versions)
                provenance['pixel_configurations'].append({'font': font, 'dpi': dpi, 'phases': records})
            else:
                reference = next((v for v in order if v != 'final'), None)
                for version, (rows, _) in captured.items():
                    for key, count in counts(rows).items():
                        if expected is not None:
                            require(count == expected[font, dpi][key[:2]][version],
                                    f'Atlas count differs from native pixel preflight: {font}/DPR{dpi}/{version}/{key}')
                        elif version != 'final' and reference is not None:
                            require(count == counts(captured[reference][0])[key], 'Old atlas counts differ during exploration')
                provenance['count_comparisons'].append({'block': block_index + 1, 'font': font, 'dpi': dpi,
                    'validated_against_native_pixels': expected is not None,
                    'counts': {v: [{'scene': k[0], 'phase': k[1], 'trial': k[2], 'count': n}
                                   for k, n in counts(data[0]).items()] for v, data in captured.items()}})
            write(provenance_path, provenance)
    if args.mode == 'pixels':
        controls = {(s, p) for s, phases in PHASES.items() for p in phases
                    if s in ('font_variations', 'grid_unique_variations')}
        by_config = {(r['font'], r['dpi']): {(p['scene'], p['phase']): p for p in r['phases']}
                     for r in provenance['pixel_configurations']}
        override_checks = []
        for dpi in args.dpis:
            baseline = by_config[labels[0], dpi]
            for font in labels[1:]:
                other = by_config[font, dpi]
                unchanged = all(baseline[key]['snapshots'][version]['sha256'] ==
                                other[key]['snapshots'][version]['sha256']
                                for key in controls for version in ('master', *args.versions, 'oracle'))
                require(unchanged, 'Fixed Roboto variation control changed under regular-font substitution')
                override_checks.append({'font': font, 'reference_font': labels[0], 'dpi': dpi,
                    'fixed_roboto_controls_unchanged': unchanged,
                    'regular_first_paint_changed': {scene:
                        baseline[scene, 'first_paint']['snapshots']['master']['sha256'] !=
                        other[scene, 'first_paint']['snapshots']['master']['sha256'] for scene in ('demo', 'text')}})
        provenance['font_override_controls'] = override_checks
    require(input_identity(study) == identity, 'Original source/build/assets changed during campaign')
    require(all(info(record['path']) == record for record in fonts.values()), 'Font input changed during campaign')
    require(info(Path(__file__)) == provenance['driver'], 'Campaign driver changed while running')
    if pixel_proof_info:
        require(info(pixel_proof_info['path']) == pixel_proof_info, 'Pixel proof changed during campaign')
    if selection_info:
        require(info(selection_info['path']) == selection_info, 'Selection manifest changed during campaign')
    provenance['results'] = info(csv_path)
    provenance['complete'] = True
    write(provenance_path, provenance)
    print(f'Completed {len(provenance["launches"])} processes: {output}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'Campaign failed: {error}', file=sys.stderr)
        sys.exit(1)
