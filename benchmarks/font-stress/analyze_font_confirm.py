#!/usr/bin/env python3
"""Audit and summarize a completed, balanced font-confirmation campaign.

The raw reader is independent of replay_campaign.py. It never launches a
renderer, executable, build, download or benchmark. Default audit includes live
binary/source/font/pixel hashes; --metadata-only permits archived raw-statistics
replay while explicitly narrowing that identity check.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import random
import statistics
import sys

VERSIONS = ('master', 'prior', 'updated45', 'final')
METRICS = ('draw_us', 'submit_us', 'complete_us')
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
SEQUENCE_FRAMES = {'demo': 65, 'text': 88, 'font_variations': 63}
RAW_FIELDS = ['scene', 'phase', 'trial', 'frames', *METRICS, 'new_atlas_entries']
RESULT_FIELDS = ['backend', 'font', 'dpi', 'block', 'version', *RAW_FIELDS]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def dump(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


class Reader:
    def __init__(self, path_map, metadata_only):
        self.path_map = sorted((path_map or {}).items(), key=lambda pair: len(pair[0]), reverse=True)
        self.metadata_only = metadata_only
        self.checked = {}
        self.skipped_live = []

    def resolve(self, path):
        value = str(path)
        for before, after in self.path_map:
            if value == before or value.startswith(before.rstrip('/') + '/'):
                return Path(after + value[len(before):])
        return Path(value)

    def sha(self, path):
        path = self.resolve(path)
        st = path.stat()
        key = (str(path), st.st_size, st.st_mtime_ns)
        if key not in self.checked:
            with path.open('rb') as stream:
                self.checked[key] = hashlib.file_digest(stream, 'sha256').hexdigest()
        return self.checked[key]

    def info(self, path):
        resolved = self.resolve(path)
        return {'path': str(path), 'bytes': resolved.stat().st_size, 'sha256': self.sha(path)}

    def check_info(self, record, live=False):
        if live and self.metadata_only:
            self.skipped_live.append(record)
            return
        require(self.info(record['path']) == record, f'Input bytes changed: {record["path"]}')

    def load(self, path):
        return json.loads(self.resolve(path).read_text())

    def source_map(self, root, expected):
        if self.metadata_only:
            self.skipped_live.append({'source_root': str(root), 'files': len(expected)})
            return
        real = self.resolve(root)
        actual_names = {str(p.relative_to(real)) for p in real.rglob('*') if p.is_file()}
        require(actual_names == set(expected), f'Source file set changed: {root}')
        for name, digest in expected.items():
            require(self.sha(Path(root) / name) == digest, f'Source changed: {root}/{name}')


def independent_orders(n):
    first = [0]
    first.extend((i + 1) // 2 if i % 2 else n - i // 2 for i in range(1, n))
    answer = [tuple((x + k) % n for x in first) for k in range(n)]
    if n % 2:
        answer.extend(tuple(reversed(row)) for row in list(answer))
    return answer


def raw_rows(text, trials):
    parser = csv.DictReader(io.StringIO(text))
    require(parser.fieldnames == RAW_FIELDS, 'Wrong retained raw CSV header')
    rows = list(parser)
    expected = {(trial, scene, phase) for trial in range(trials)
                for scene, phases in PHASES.items() for phase in phases}
    seen = set()
    for row in rows:
        key = (int(row['trial']), row['scene'], row['phase'])
        require(key in expected and key not in seen, f'Duplicate/unexpected raw row: {key}')
        seen.add(key)
        require(int(row['frames']) == PHASES[key[1]][key[2]], f'Wrong raw frame count: {key}')
        count = int(row['new_atlas_entries'])
        require(count >= 0, 'Negative raw atlas count')
        if key[1].startswith('grid_'):
            require(count == 94 * int(row['frames']), f'Controlled grid lost atlas requests: {key}')
        values = [float(row[m]) for m in METRICS]
        require(all(math.isfinite(x) and x >= 0 for x in values) and values == sorted(values),
                f'Invalid cumulative raw timing: {key}')
    require(seen == expected, 'Incomplete retained raw trials/phases')
    return rows


def audit_identity(reader, identity):
    for name in ('build_provenance', 'native_build_provenance', 'native_prepare_provenance', 'prepare_provenance'):
        reader.check_info(identity[name])
    for record in identity['independent_audits']:
        reader.check_info(record)
        require(reader.load(record['path']).get('complete') is True, 'Original independent identity audit incomplete')
    build = reader.load(identity['build_provenance']['path'])
    require(build.get('complete') is True and set(build['variants']) == set(VERSIONS), 'Original build is incomplete')
    require(identity['compiler'] == build['compiler'] and identity['cargo'] == build['cargo'], 'Compiler identity changed')
    core = Path(identity['build_provenance']['path']).parent
    for version in VERSIONS:
        binary, source = identity['binaries'][version], identity['sources'][version]
        record = build['variants'][version]
        require(record.get('complete') is True and record['binary_sha256'] == binary['sha256'], 'Binary build binding changed')
        require(source['pure_snapshot'] == record['pure_source_files'] and source['timed_source'] == record['timed_source_files'],
                'Source identity differs from original build')
        reader.check_info(binary, live=True)
        reader.source_map(core / 'snapshots' / version, source['pure_snapshot'])
        reader.source_map(core / 'replay-sources' / version, source['timed_source'])
    require(build['runner_source'] == identity['runner_source'], 'Compiled drawing source binding changed')
    reader.source_map(core / 'runner/src', identity['runner_source'])
    if not reader.metadata_only:
        require(reader.sha(core / 'runner/Cargo.lock') == identity['resolved_lock_sha256'] == build['resolved_lock_sha256'],
                'Locked dependency graph changed')
    prep = reader.load(identity['prepare_provenance']['path'])
    expected_assets = {k[7:]: v['sha256'] for k, v in prep['prepared_files'].items() if k.startswith('assets/')}
    require(expected_assets == identity['assets'], 'Fixed asset preparation binding changed')
    reader.source_map(core.parent / 'assets', identity['assets'])
    native = reader.load(identity['native_build_provenance']['path'])
    native_prep = reader.load(identity['native_prepare_provenance']['path'])
    require(native.get('complete') is True and native_prep.get('complete') is True, 'Native oracle build incomplete')
    require(native['prepare_sha256'] == identity['native_prepare_provenance']['sha256'], 'Native preparation changed')
    require(native['binary_sha256'] == identity['oracle_binary']['sha256'], 'Native executable binding changed')
    reader.check_info(identity['oracle_binary'], live=True)
    reader.source_map(Path(native_prep['oracle_source']), native_prep['oracle_files'])
    reader.source_map(Path(identity['native_prepare_provenance']['path']).parent / 'runner', native_prep['runner_files'])
    require(native_prep['original_master_files'] == identity['sources']['master']['timed_source'], 'Native reference master changed')
    independent_native = reader.load(identity['independent_audits'][-1]['path'])
    require(independent_native['binary'] == identity['oracle_binary'] and
            independent_native['build_proof_sha256'] == identity['native_build_provenance']['sha256'] and
            independent_native['prepare_sha256'] == identity['native_prepare_provenance']['sha256'],
            'Native independent source/build proof binding changed')
    require(reader.sha(native['metadata']) == native['metadata_sha256'] == independent_native['native_metadata_sha256'],
            'Native resolved dependency/feature metadata changed')
    independent_source = reader.load(identity['independent_audits'][0]['path'])
    require(independent_source['input_proof_hashes']['runtime/core/replay-build-provenance.json'] == identity['build_provenance']['sha256'] and
            independent_source['input_proof_hashes']['runtime/prepare-provenance.json'] == identity['prepare_provenance']['sha256'],
            'Original independent build proof binding changed')
    for version in VERSIONS:
        require(independent_source['builds'][version]['replay_binary'] == identity['binaries'][version] and
                independent_source['builds'][version]['replay_swash'] == ['0.2.10'] and
                independent_source['builds'][version]['replay_skrifa'] == ['0.44.0'], 'Original executable/features identity changed')


def audit_processes(reader, root, metadata, pixel=False):
    mode = metadata['mode']
    trials = metadata['trials_per_process']
    with reader.resolve(Path(root) / f'{mode}-results.csv').open() as stream:
        parser = csv.DictReader(stream)
        require(parser.fieldnames == RESULT_FIELDS, 'Wrong aggregate CSV fields')
        aggregate = list(parser)
    reader.check_info(metadata['results'])
    require(Path(metadata['results']['path']).name == f'{mode}-results.csv', 'Unexpected results record')
    indexed = defaultdict(list)
    for row in aggregate:
        require(row['backend'] == metadata['backend'], 'Aggregate backend changed')
        indexed[int(row['block']), row['font'], int(row['dpi']), row['version']].append(row)
    processes = {}
    for launch in metadata['launches']:
        key = (launch['block'], launch['font'], launch['dpi'], launch['version'])
        require(key not in processes and launch.get('validated') is True and launch.get('exit_code') == 0,
                f'Duplicate/failed process: {key}')
        for field in ('stdout_info', 'stderr_info'):
            reader.check_info(launch[field])
        require(launch['stdout_info']['path'] == launch['stdout'] and launch['stderr_info']['path'] == launch['stderr'],
                'Raw process path binding changed')
        binary = metadata['identity']['oracle_binary'] if key[3] == 'oracle' else metadata['identity']['binaries'][key[3]]
        expected_command = [binary['path'], metadata['backend'], str(trials), str(key[2])]
        if pixel:
            require(len(launch['command']) == 5, 'Pixel capture command missing destination')
            expected_command.append(launch['command'][4])
        require(launch['command'] == expected_command, f'Process command changed: {key}')
        require(launch['environment'] == {'FEMTOVG_REPLAY_TEXT_FONT': metadata['font_files'][key[1]]['path']},
                f'Actual font override changed: {key}')
        rows = raw_rows(reader.resolve(launch['stdout']).read_text(), trials)
        require(launch['rows'] == len(rows), 'Retained raw row count changed')
        copied = [{k: v for k, v in row.items() if k in RAW_FIELDS} for row in indexed[key]]
        require(copied == rows, f'Aggregate rows differ from retained stdout: {key}')
        processes[key] = rows
    require(set(indexed) == set(processes) and sum(len(x) for x in processes.values()) == len(aggregate),
            'Aggregate contains missing/extra process rows')
    return processes


def audit_pixels(reader, record, identity, fonts, dpis, versions):
    reader.check_info(record)
    metadata = reader.load(record['path'])
    require(metadata.get('complete') is True and metadata['mode'] == 'pixels' and metadata['backend'] == 'gpu',
            'Separate native pixel preflight is incomplete')
    pixel_versions = metadata['versions']
    require(metadata['identity'] == identity and set(versions) <= set(pixel_versions) <= set(VERSIONS) and
            pixel_versions[0] == 'master', 'Pixel source/version protocol differs')
    require(metadata['phases'] == PHASES and metadata['blocks'] == 1 and metadata['trials_per_process'] == 1, 'Pixel phase protocol differs')
    for label, font in fonts.items():
        require(metadata['font_files'][label] == font, f'Pixel font identity differs: {label}')
    processes = audit_processes(reader, Path(record['path']).parent, metadata, pixel=True)
    required = {(1, f, d, v) for f in metadata['fonts'] for d in metadata['dpis'] for v in (*pixel_versions, 'oracle')}
    require(set(processes) == required, 'Pixel reference/candidate matrix incomplete')
    expected = {}
    for config in metadata['pixel_configurations']:
        key = (config['font'], config['dpi'])
        require(key not in expected, 'Duplicate native pixel configuration')
        phases = {}
        for row in config['phases']:
            phase = (row['scene'], row['phase'])
            require(phase not in phases and row['frames'] == PHASES[phase[0]][phase[1]], 'Pixel phase duplicate/wrong')
            require(set(row['counts']) == set((*pixel_versions, 'oracle')) and set(row['snapshots']) == set((*pixel_versions, 'oracle')),
                    'Pixel versions are incomplete')
            for version in (*pixel_versions, 'oracle'):
                raw = next(r for r in processes[1, key[0], key[1], version] if (r['scene'], r['phase']) == phase)
                require(int(raw['new_atlas_entries']) == row['counts'][version], 'Native count ledger differs from raw capture')
                snapshot = row['snapshots'][version]
                width, height = (800, 700) if phase[0] == 'font_variations' else (1000, 600)
                require(snapshot['bytes'] == width * height * 4 and Path(snapshot['path']).name == f'{phase[0]}-{phase[1]}.rgba',
                        'Pixel dimensions/name differ')
                reader.check_info(snapshot, live=True)
                reference = 'oracle' if version == 'final' else 'master'
                if version != 'oracle':
                    require(snapshot['sha256'] == row['snapshots'][reference]['sha256'] and
                            row['counts'][version] == row['counts'][reference], 'Native/reference mask or count parity fails')
            phases[phase] = row['counts']
        require(set(phases) == {(s, p) for s, names in PHASES.items() for p in names}, 'Native pixel phases incomplete')
        expected[key] = phases
    require(set(expected) == {(f, d) for f in metadata['fonts'] for d in metadata['dpis']}, 'Native pixel factor matrix incomplete')
    require(all((f, d) in expected for f in fonts for d in dpis), 'Missing requested font/DPR pixel preflight')
    return expected, {'proof': record, 'configurations': len(expected), 'processes': len(processes),
                      'phase_comparisons': len(expected) * 28 * (len(pixel_versions) - 1), 'all_raw_native_counts_verified': True,
                      'live_rgba_bytes_verified': not reader.metadata_only}


def audit_timing(reader, root, mode):
    path = Path(root) / f'{mode}-provenance.json'
    metadata = reader.load(path)
    require(metadata.get('complete') is True and metadata.get('exploratory') is False, 'Confirmation must be complete and independent of exploratory raw data')
    versions = metadata['versions']
    require(metadata['mode'] == metadata['backend'] == mode and versions[0] == 'master' and
            'final' in versions and len(set(versions)) == len(versions) and set(versions) <= set(VERSIONS),
            'Wrong confirmation version/backend protocol')
    require(metadata['blocks'] == 12 and metadata['trials_per_process'] == (5 if mode == 'cpu' else 3), 'Expected 12 blocks with five CPU/three GPU trials')
    require(metadata['phases'] == PHASES and len(set(metadata['fonts'])) == len(metadata['fonts']) and
            len(set(metadata['dpis'])) == len(metadata['dpis']), 'Confirmation factor/phase protocol changed')
    require(set(metadata['font_files']) == set(metadata['fonts']) and metadata['pixel_proof'] is not None, 'Font or native preflight proof missing')
    reader.check_info(metadata['driver'])
    for record in metadata['font_files'].values():
        reader.check_info(record, live=True)
    if metadata.get('selection_manifest'):
        reader.check_info(metadata['selection_manifest'])
        selection = reader.load(metadata['selection_manifest']['path'])
        require(selection.get('complete') is True and
                datetime.fromisoformat(selection['frozen_utc']) <= datetime.fromisoformat(metadata['created_utc']),
                'Selected fonts were not frozen before this confirmation campaign')
        selected_fonts = {row['label']: {k: v for k, v in row.items() if k != 'label'} for row in selection['fonts']}
        require(selected_fonts == metadata['font_files'] and selection['confirmation']['versions'] == versions,
                'Confirmation differs from the frozen font/version selection')
        for name, digest in selection['selection_inputs'].items():
            require(reader.sha(Path(metadata['selection_manifest']['path']).parent / name) == digest,
                    'Exploratory selection evidence changed after freezing')
    audit_identity(reader, metadata['identity'])
    expected_counts, pixel_audit = audit_pixels(reader, metadata['pixel_proof'], metadata['identity'], metadata['font_files'], metadata['dpis'], versions)
    processes = audit_processes(reader, root, metadata)
    require(set(processes) == {(b, f, d, v) for b in range(1, 13) for f in metadata['fonts'] for d in metadata['dpis'] for v in versions},
            'Confirmation process matrix incomplete')
    for (block, font, dpi, version), rows in processes.items():
        for row in rows:
            require(int(row['new_atlas_entries']) == expected_counts[font, dpi][row['scene'], row['phase']][version],
                    'Confirmation atlas work differs from native preflight')
    configs = [(f, d) for d in metadata['dpis'] for f in metadata['fonts']]
    schedules = independent_orders(len(versions))
    require(12 % len(schedules) == 0, 'Confirmation does not contain whole Williams cycles')
    expected_order, expected_launch_keys = [], []
    balances = {}
    for block_index in range(12):
        rotate = block_index % len(configs)
        labels = []
        for font, dpi in configs[rotate:] + configs[:rotate]:
            order = [versions[i] for i in schedules[(block_index + configs.index((font, dpi))) % len(schedules)]]
            for version in order:
                labels.append(f'{block_index + 1:02}-{font}-dpi{dpi}-{version}')
                expected_launch_keys.append((block_index + 1, font, dpi, version))
        expected_order.append(labels)
    require(metadata['order'] == expected_order and
            [(r['block'], r['font'], r['dpi'], r['version']) for r in metadata['launches']] == expected_launch_keys,
            'Actual raw launch order differs from the prespecified balanced schedule')
    for font, dpi in configs:
        cohort_orders = [tuple(k[3] for k in expected_launch_keys if k[:3] == (b, font, dpi)) for b in range(1, 13)]
        positions = Counter((i, v) for order in cohort_orders for i, v in enumerate(order))
        predecessors = Counter((a, b) for order in cohort_orders for a, b in zip(order, order[1:]))
        orders = Counter(cohort_orders)
        order_frequency, position_frequency = 12 // len(schedules), 12 // len(versions)
        require(set(orders.values()) == {order_frequency} and set(positions.values()) == {position_frequency} and
                len(predecessors) == len(versions) * (len(versions) - 1) and set(predecessors.values()) == {position_frequency},
                'Williams order/position/predecessor imbalance')
        balances[f'{font}/DPR{dpi}'] = {'order_counts': {','.join(k): v for k, v in orders.items()},
                                     'positions_each': position_frequency, 'directed_predecessors_each': position_frequency}
    return metadata, processes, {'provenance': reader.info(path), 'results': metadata['results'],
        'processes': len(processes), 'raw_rows': sum(len(v) for v in processes.values()),
        'all_aggregate_rows_match_raw_stdout': True, 'all_native_work_counts_match': True,
        'williams_balance': balances, 'pixel_preflight': pixel_audit}


def endpoint_values(processes, metadata):
    endpoints = {}
    versions = metadata['versions']
    for font in metadata['fonts']:
        for dpi in metadata['dpis']:
            for scene, phases in PHASES.items():
                for phase, frames in phases.items():
                    for metric in METRICS:
                        endpoint = (font, dpi, scene, phase, metric, frames)
                        endpoints[endpoint] = {v: [] for v in versions}
                        for v in versions:
                            for block in range(1, 13):
                                values = [float(r[metric]) for r in processes[block, font, dpi, v]
                                          if r['scene'] == scene and r['phase'] == phase]
                                require(len(values) == metadata['trials_per_process'], 'Missing phase values before process median')
                                endpoints[endpoint][v].append(statistics.median(values))
                if scene in SEQUENCE_FRAMES:
                    frames = sum(phases.values())
                    require(frames == SEQUENCE_FRAMES[scene], 'Reported sequence weight changed')
                    for metric in METRICS:
                        endpoint = (font, dpi, scene, 'reported_sequence', metric, frames)
                        endpoints[endpoint] = {v: [] for v in versions}
                        for v in versions:
                            for block in range(1, 13):
                                trial_sums = [math.fsum(float(r[metric]) * int(r['frames'])
                                    for r in processes[block, font, dpi, v] if r['scene'] == scene and int(r['trial']) == t)
                                    for t in range(metadata['trials_per_process'])]
                                endpoints[endpoint][v].append(statistics.median(trial_sums))
    return endpoints


def percentile(values, quantile):
    ordered = sorted(values)
    point = (len(ordered) - 1) * quantile
    low, high = math.floor(point), math.ceil(point)
    return ordered[low] + (ordered[high] - ordered[low]) * (point - low)


def interval(values):
    return [percentile(values, .025), percentile(values, .975)]


def boot_means(values, weights, numpy):
    if numpy is not None:
        return (weights @ numpy.asarray(values, dtype=numpy.float64) / len(values)).tolist()
    return [math.fsum(v * n for v, n in zip(values, counts)) / len(values) for counts in weights]


def write_csv(path, rows):
    require(bool(rows), 'No analysis rows to write')
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cpu', type=Path, required=True)
    parser.add_argument('--gpu', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=72531)
    parser.add_argument('--bootstrap', type=int, default=10000)
    parser.add_argument('--control-font', default='vollkorn')
    parser.add_argument('--path-map', type=Path)
    parser.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--quiet-evidence', type=Path, action='append', default=[])
    args = parser.parse_args()
    require(args.bootstrap == 10000, 'Confirmation protocol fixes bootstrap at 10,000 resamples')
    output = args.output.resolve()
    require(not output.exists(), 'Use a fresh analysis output directory')
    output.mkdir(parents=True)
    reader = Reader(json.loads(args.path_map.read_text()) if args.path_map else {}, args.metadata_only)
    audit = {'complete': False, 'scope': 'Independent raw reader/order/source/native-preflight audits; no collector imports',
             'metadata_only': args.metadata_only, 'errors': [], 'backends': {}}
    dump(output / 'raw-audit.json', audit)
    try:
        datasets = {}
        for mode, root in (('cpu', args.cpu), ('gpu', args.gpu)):
            if root is None:
                continue
            metadata, processes, proof = audit_timing(reader, root, mode)
            datasets[mode] = (metadata, endpoint_values(processes, metadata))
            audit['backends'][mode] = proof
        if 'gpu' in datasets:
            cpu, gpu = datasets['cpu'][0], datasets['gpu'][0]
            require(cpu['identity'] == gpu['identity'] and cpu['font_files'] == gpu['font_files'] and
                    cpu['fonts'] == gpu['fonts'] and cpu['dpis'] == gpu['dpis'] and
                    cpu['versions'] == gpu['versions'] and
                    cpu.get('selection_manifest') == gpu.get('selection_manifest'), 'CPU/GPU confirmation inputs differ')
        require(2 in datasets['cpu'][0]['dpis'], 'Prespecified primary DPR2 is missing')
        audit['checked_files'] = [{'path': k[0], 'bytes': k[1], 'sha256': v} for k, v in reader.checked.items()]
        audit['skipped_live_identities'] = reader.skipped_live
        audit['complete'] = True
        dump(output / 'raw-audit.json', audit)
        try:
            import numpy as np
        except ImportError:
            np = None
        flat, pairs, indices_record, control_advantages = [], [], {}, []
        for mode, (metadata, endpoints) in datasets.items():
            token = f'font-confirmation/{mode}/whole-block/12'
            seed = args.seed ^ int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], 'big')
            rng = random.Random(seed)
            indices = [[rng.randrange(12) for _ in range(12)] for _ in range(args.bootstrap)]
            weights = [[sample.count(i) for i in range(12)] for sample in indices]
            if np is not None:
                weights = np.asarray(weights, dtype=np.float64)
            indices_record[mode] = {'token': token, 'seed': seed, 'indices': indices,
                'indices_sha256': hashlib.sha256(json.dumps(indices, separators=(',', ':')).encode()).hexdigest()}
            for endpoint, values in sorted(endpoints.items()):
                font, dpi, scene, phase, metric, frames = endpoint
                require(all(x > 0 for x in values['master']), 'Positive reference process median required for ratio')
                boot = {v: boot_means(values[v], weights, np) for v in metadata['versions']}
                for candidate in metadata['versions'][1:]:
                    reference_mean = statistics.mean(values['master'])
                    candidate_mean = statistics.mean(values[candidate])
                    saving = reference_mean - candidate_mean
                    savings_ci = interval([a - b for a, b in zip(boot['master'], boot[candidate])])
                    pct = 100 * (candidate_mean / reference_mean - 1)
                    pct_ci = interval([100 * (b / a - 1) for a, b in zip(boot['master'], boot[candidate])])
                    outcome = 'improvement' if savings_ci[0] > 0 else 'regression' if savings_ci[1] < 0 else 'uncertain'
                    point = {'backend': mode, 'font': font, 'dpi': dpi, 'scene': scene, 'phase': phase,
                        'metric': metric, 'frames': frames, 'unit': 'us/sequence' if phase == 'reported_sequence' else 'us/frame',
                        'reference_version': 'master', 'candidate_version': candidate,
                        'reference_mean_process_median_us': reference_mean, 'candidate_mean_process_median_us': candidate_mean,
                        'mean_paired_savings_us': saving, 'savings_ci95_low_us': savings_ci[0], 'savings_ci95_high_us': savings_ci[1],
                        'ratio_of_means_change_pct': pct, 'ratio_change_ci95_low_pct': pct_ci[0], 'ratio_change_ci95_high_pct': pct_ci[1],
                        'classification': outcome, 'blocks': 12, 'trials_per_process': metadata['trials_per_process'],
                        'bootstrap_resamples': args.bootstrap, 'bootstrap_seed': seed}
                    flat.append(point)
                    for b in range(12):
                        pairs.append({k: point[k] for k in ('backend', 'font', 'dpi', 'scene', 'phase', 'metric', 'frames',
                                                          'reference_version', 'candidate_version')} | {
                            'block': b + 1, 'reference_process_median_us': values['master'][b],
                            'candidate_process_median_us': values[candidate][b],
                            'paired_savings_us': values['master'][b] - values[candidate][b]})
            control_font = args.control_font if args.control_font in metadata['fonts'] else next(
                (font for font in metadata['fonts'] if font.lower().startswith('vollkorn')), None)
            if mode == 'cpu' and control_font is not None:
                control = endpoints[control_font, 2, 'demo', 'first_paint', 'draw_us', 1]
                control_savings = [a - b for a, b in zip(control['master'], control['final'])]
                for font in metadata['fonts']:
                    if font == control_font:
                        continue
                    observed = endpoints[font, 2, 'demo', 'first_paint', 'draw_us', 1]
                    extra = [a - b - c for a, b, c in zip(observed['master'], observed['final'], control_savings)]
                    ci = interval(boot_means(extra, weights, np))
                    control_advantages.append({'font': font, 'control_font': control_font, 'backend': 'cpu', 'dpi': 2,
                        'scene': 'demo', 'phase': 'first_paint', 'metric': 'draw_us',
                        'mean_additional_paired_savings_us': statistics.mean(extra),
                        'additional_savings_ci95_us': ci,
                        'classification': 'larger_savings' if ci[0] > 0 else 'smaller_savings' if ci[1] < 0 else 'uncertain',
                        'paired_block_differences_us': extra})
        write_csv(output / 'summary.csv', flat)
        write_csv(output / 'paired-processes.csv', pairs)
        dump(output / 'bootstrap-indices.json', indices_record)
        quiet = [reader.info(path) for path in args.quiet_evidence]
        methodology = {'complete': True, 'created_utc': datetime.now(timezone.utc).isoformat(),
            'versions': datasets['cpu'][0]['versions'], 'comparisons': [['master', v] for v in datasets['cpu'][0]['versions'][1:]],
            'process_estimator': 'Median of five CPU or three GPU raw trial values per phase and process',
            'sequence_estimator': 'For each trial sum reported phase mean × recorded frames, then median of trial totals per process; demo65/text88/variations63 frames',
            'absolute_effect': 'Arithmetic mean of 12 paired master-minus-candidate process medians; positive saves time',
            'secondary_ratio_effect': '100 × (mean candidate process median / mean master process median − 1); negative is faster; differs from median paired percentages',
            'intervals': '10,000 percentile bootstrap resamples of whole 12-block backend campaigns; shared indices across fonts, DPRs, phases, metrics and candidate versions; linear 2.5/97.5 percentiles',
            'seed': args.seed, 'bootstrap_resamples': args.bootstrap,
            'numeric_engine': 'numpy acceleration of weighted arithmetic means' if np is not None else 'Python stdlib weighted arithmetic means',
            'numpy_version': np.__version__ if np is not None else None, 'python': sys.version, 'platform': platform.platform(),
            'primary_endpoint': 'CPU demo first_paint draw_us final versus master at DPR2; selected-font improvement and additional savings versus Vollkorn are separate claims',
            'control_advantage': 'Same-block difference between selected font master−final savings and control font master−final savings',
            'sequence_scope': 'Only recorded phase frames; excludes119 unreported warm-up frames between first paint and warm measurement; cumulative draw/submit/complete are separate endpoints, never added',
            'selection_scope': 'Only confirmation raw files enter these estimates. Fonts were selected using separate exploratory data; intervals are conditional on chosen fonts, unadjusted for multiple endpoints, not a representative font population estimate. When supplied, selected font/version hashes and retained selection-input hashes are verified against the selection manifest, whose recorded frozen UTC precedes each recorded campaign start UTC; chronology is not inferred from file mtimes.',
            'controls_scope': 'Roboto variation controls remain fixed across regular-font factors and are not independent evidence for each selected font',
            'quiet_evidence': quiet,
            'machine_quiet_caveat': 'Source/order/raw audits do not establish absence of background load, thermal drift or DVFS. Attached quiet records need their own interpretation; nominal intervals capture observed block variability on this one machine.',
            'retention': 'Every validated process and raw trial retained; no exclusions, retries, winsorization or baseline substitutions',
            'identity_scope': 'Archived metadata/count/raw statistical replay; live binary/source/font/RGBA checks skipped and explicitly recorded' if args.metadata_only else 'Live executable/source/font/RGBA bytes and retained raw statistical identities verified',
            'inputs': {'cpu': audit['backends']['cpu']['provenance'],
                       'gpu': audit['backends'].get('gpu', {}).get('provenance'),
                       'analyzer': reader.info(Path(__file__)), 'raw_audit': reader.info(output / 'raw-audit.json')},
        }
        dump(output / 'summary.json', {'complete': True, 'methodology': methodology,
            'results': flat, 'primary_control_advantage': control_advantages})
        primary = [r for r in flat if r['backend'] == 'cpu' and r['dpi'] == 2 and r['scene'] == 'demo' and
                   r['phase'] == 'first_paint' and r['metric'] == 'draw_us' and r['candidate_version'] == 'final']
        report = ['Absolute first-paint host CPU savings in the unchanged demo, final versus master, DPR2. Positive values save time. Fonts were chosen by an exploratory search, then measured in a separate 12-block confirmation.', '',
                  '| Font | Master | Final | Paired savings (95% CI) | Secondary ratio change | Evidence |',
                  '|---|---:|---:|---:|---:|---|']
        for r in primary:
            report.append(f'| {r["font"]} | {r["reference_mean_process_median_us"]/1000:.3f} ms | {r["candidate_mean_process_median_us"]/1000:.3f} ms | '
                          f'{r["mean_paired_savings_us"]/1000:+.3f} ms [{r["savings_ci95_low_us"]/1000:+.3f}, {r["savings_ci95_high_us"]/1000:+.3f}] | '
                          f'{r["ratio_of_means_change_pct"]:+.2f}% | {r["classification"]} |')
        if control_advantages:
            report.extend(['', '| Selected font | Additional savings versus control (95% CI) | Evidence |', '|---|---:|---|'])
            for r in control_advantages:
                lo, hi = r['additional_savings_ci95_us']
                report.append(f'| {r["font"]} versus {r["control_font"]} | {r["mean_additional_paired_savings_us"]/1000:+.3f} ms '
                              f'[{lo/1000:+.3f}, {hi/1000:+.3f}] | {r["classification"]} |')
        report.extend(['', 'All phase/metric and weighted reported-sequence results, including warm costs, uncertain intervals and regressions, remain in [summary.csv](summary.csv). '
                       'Paired raw-derived process values are in [paired-processes.csv](paired-processes.csv); the independent preflight/order/count audit is [raw-audit.json](raw-audit.json). '
                       'See [summary.json](summary.json) for estimator definitions, exact resample seeds, conditional selection scope and machine quiet caveats. '
                       'These host drawing measurements are not end-to-end launch or FPS estimates. GPU completion is separately retained when supplied.'])
        (output / 'primary-table.md').write_text('\n'.join(report) + '\n')
        dump(output / 'analysis-inputs.json', {'complete': True, 'inputs': methodology['inputs'],
            'outputs': {name: reader.info(output / name) for name in ('summary.csv', 'summary.json', 'paired-processes.csv',
                       'bootstrap-indices.json', 'raw-audit.json', 'primary-table.md')}})
        print(f'Completed independent audit and {len(flat)} endpoint comparisons: {output}')
    except Exception as error:
        if not audit['complete']:
            audit['errors'].append(f'{type(error).__name__}: {error}')
            dump(output / 'raw-audit.json', audit)
        raise


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f'Confirmation analysis failed: {error}', file=sys.stderr)
        sys.exit(1)
