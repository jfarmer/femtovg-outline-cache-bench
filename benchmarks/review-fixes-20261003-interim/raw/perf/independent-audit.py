#!/usr/bin/env python3
"""Independently audit every paired process record; never import run/analyzer code.

Heavy bootstrap requires --timing-finished or a coordinated --timing-paused.
All accepted
cohorts must have exactly 12 complete paired blocks. Interrupted cohorts remain
retained and counted separately, never silently merged or filtered.
"""
import argparse
from collections import Counter, defaultdict
import csv
import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import random
import re


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values):
    ordered = sorted(values)
    middle = len(ordered) // 2
    return ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2


def near(actual, expected, label):
    if isinstance(expected, list):
        assert len(actual) == len(expected), label
        for index, value in enumerate(expected):
            near(actual[index], value, f'{label}[{index}]')
    else:
        assert math.isclose(actual, expected, rel_tol=1e-11, abs_tol=1e-8), (label, actual, expected)


def read_jsonl(path, missing_ok=False):
    if missing_ok and not path.exists():
        return []
    lines = path.read_text().splitlines()
    assert all(line.strip() for line in lines), f'Blank raw record in {path}'
    return [json.loads(line) for line in lines]


def read_records(folder):
    return read_jsonl(folder / 'raw.jsonl')


def timestamp(value):
    parsed = datetime.datetime.fromisoformat(value)
    assert parsed.tzinfo is not None, value
    return parsed


def scene_configurations():
    return [(feature, scene, font) for feature in ['default_swash', 'default_no_swash']
            for scene, font in [('demo', 'RobotoFlex'), ('demo', 'Vollkorn'),
                                ('text', 'RobotoFlex'), ('text', 'Vollkorn')]]


def scene_planned_order(configs, blocks):
    expected = []
    for block in range(blocks):
        rotated = configs[block % len(configs):] + configs[:block % len(configs)]
        for index, config in enumerate(rotated):
            variants = ['master', 'final'] if (block + index) % 2 == 0 else ['final', 'master']
            expected.extend((block, *config, variant) for variant in variants)
    return expected


def audit_retry_retention(folder, meta, accepted, expected_order, configuration_key, require_complete=True):
    policy = meta.get('environment_retry_policy', {})
    if not (folder / 'PLAN.json').exists():
        return None
    plan = json.loads((folder / 'PLAN.json').read_text())
    if not plan['policy']['environment_retries']:
        return None
    assert plan['logical_blocks'] == 12
    assert plan['runner_sha256'] == meta['runner_sha256']
    assert digest(Path(plan['runner_archive'])) == plan['runner_sha256']
    assert digest(Path(plan.get('guard_archive', plan['runner_archive']))) == plan['guard_sha256']
    if 'guard_sha256' in meta:
        assert meta['guard_sha256'] == plan['guard_sha256']
    assert plan['policy']['environment_retries'] is True
    assert plan['policy']['no_timing_value_filtering'] is True
    assert plan['policy']['guard'] == 'before and after EACH process'
    assert plan['policy']['discard_unit'] == ('entire attempt of a logical paired block' if configuration_key == 'workload' else 'entire attempt of logical paired block')
    assert plan['policy']['quiet_seconds_before_start_or_replay'] == 60
    assert plan['policy']['max_retries'] == 30
    assert plan['policy']['max_duration_seconds'] == 1800
    assert len(plan['blocks']) == 12
    block_order = defaultdict(list)
    for key in expected_order:
        block_order[key[0]].append(key)
    expected_per_block = len(block_order[0])
    assert plan['expected_processes_per_accepted_block'] == expected_per_block
    for block, declared in enumerate(plan['blocks']):
        assert declared['logical_block'] == block
        if configuration_key == 'workload':
            declared_order = [(block, config['feature'], config['workload'], config['font'], variant)
                              for config in declared['configurations'] for variant in declared['variant_order']]
        else:
            declared_order = [(block, config['feature'], config['scene'], config['font'], variant)
                              for config in declared['configurations'] for variant in config['variant_order']]
        assert declared_order == block_order[block], (folder.name, block, 'predeclared order')
    attempts = read_jsonl(folder / 'attempts.jsonl')
    rejected = read_jsonl(folder / 'excluded-raw.jsonl', missing_ok=True)
    ledger = read_jsonl(folder / 'ledger.jsonl')
    rejection_events = read_jsonl(folder / 'rejected-blocks.jsonl', missing_ok=True)
    quiet_events = read_jsonl(folder / 'interference-events.jsonl', missing_ok=True)
    by_attempt = defaultdict(list)
    glyph_counts = workload_counts(folder.parent) if configuration_key == 'workload' else None
    last_attempt = 0
    for record in attempts:
        assert record['attempt'] >= last_attempt
        last_attempt = record['attempt']
        by_attempt[record['attempt']].append(record)
    accepted_reconstructed, rejected_reconstructed = [], []
    next_block = 0
    rejected_ledger = []
    prior_end = timestamp(plan['written_utc'])
    quiet_required = True
    attempt_offset = accepted_offset = excluded_offset = 0
    for attempt_id, event in enumerate(ledger, start=1):
        assert event['attempt'] == attempt_id and event['block'] == next_block
        records = by_attempt.pop(attempt_id, [])
        order = [(r['block'], r['feature'], r[configuration_key], r['font'], r['variant']) for r in records]
        assert order == block_order[next_block][:len(records)], (folder.name, attempt_id, 'attempt order')
        assert len(records) <= expected_per_block
        assert event['attempt_record_offset'] == attempt_offset
        assert event['process_records'] == len(records)
        attempt_offset += len(records)
        previous = prior_end
        for index, record in enumerate(records):
            before, after = timestamp(record['guard_before_utc']), timestamp(record['guard_after_utc'])
            assert previous <= before <= after
            previous = after
            assert record['guard_after_status'] in ['idle', 'guard_matched_or_failed']
            if record['guard_after_status'] != 'idle':
                assert event['status'] == 'rejected' and index == len(records) - 1
            if configuration_key == 'workload':
                validate_process_record(record, meta, meta['suite'], glyph_counts)
            else:
                parse_scene_metrics(record, folder.name)
        start = timestamp(event['started_utc'])
        end = timestamp(event['ended_utc'])
        assert prior_end <= start <= end
        if quiet_required:
            assert (start - prior_end).total_seconds() >= 59.9, (folder.name, attempt_id, 'quiet interval shorter than predeclared')
        assert not records or start <= timestamp(records[0]['guard_before_utc'])
        assert previous <= end
        if event['status'] == 'accepted':
            assert len(records) == expected_per_block
            assert event['process_records'] == event['expected_process_records'] == expected_per_block
            assert all(r['guard_after_status'] == 'idle' for r in records)
            assert event['accepted_raw_offset'] == accepted_offset
            accepted_offset += len(records)
            accepted_reconstructed.extend(records)
            next_block += 1
            prior_end = end
            quiet_required = False
            assert previous <= prior_end
        else:
            assert event['status'] == 'rejected' and event['reason'] == 'environment_guard_match'
            assert event['rejected_process_records'] == len(records)
            assert event['excluded_raw_offset'] == excluded_offset
            excluded_offset += len(records)
            assert event['pids'] and all(str(pid).isdecimal() for pid in event['pids'])
            names = event['process_families_and_names_only']
            assert [entry['pid'] for entry in names] == event['pids']
            assert all('family' in entry and 'comm' in entry for entry in names)
            assert event.get('guard_reason', event.get('reason_detail', 'Build/compiler/linker process name guard matched')) == 'Build/compiler/linker process name guard matched'
            rejected_reconstructed.extend(records)
            rejected_ledger.append(event)
            prior_end = end
            quiet_required = True
            # The post-guard timestamp is written just after its matching guard event.
            assert not records or prior_end >= timestamp(records[-1]['guard_before_utc'])
    assert next_block <= 12 and not by_attempt
    if require_complete:
        assert next_block == 12
    assert accepted == accepted_reconstructed, (folder.name, 'accepted raw stream differs from ledger')
    assert rejected == rejected_reconstructed, (folder.name, 'excluded raw stream differs from ledger')
    assert len(attempts) == attempt_offset == len(accepted) + len(rejected)
    assert len(rejection_events) == len(rejected_ledger)
    for raw_event, ledger_event in zip(rejection_events, rejected_ledger):
        assert all(ledger_event[key] == value for key, value in raw_event.items() if key != 'reason')
        assert raw_event['reason'] == 'Build/compiler/linker process name guard matched'
    for event in quiet_events:
        assert event['reason'] == 'Build/compiler/linker process name guard matched' and event['pids']
    assert len(rejected_ledger) <= plan['policy']['max_retries']
    return {'plan_sha256': digest(folder / 'PLAN.json'), 'ledger_sha256': digest(folder / 'ledger.jsonl'),
            'all_attempt_records_retained': len(attempts), 'accepted_attempts': next_block,
            'rejected_attempts': len(rejected_ledger), 'rejected_records_retained': len(rejected),
            'attempts_raw_sha256': digest(folder / 'attempts.jsonl'),
            'excluded_raw_sha256': digest(folder / 'excluded-raw.jsonl') if (folder / 'excluded-raw.jsonl').exists() else None,
            'quiet_guard_events_retained': len(quiet_events)}


def workload_counts(study):
    # Count actual precomputed text, independently of recorded benchmark values.
    source = (study / 'harness-src/main.rs').read_text()
    label_body = re.search(r'const LABELS.*?= &\[(.*?)\];', source, re.S).group(1)
    labels = [json.loads(value) for value in re.findall(r'"(?:[^"\\]|\\.)*"', label_body)]
    paragraph = re.search(r'const PARA: &str = "(.*?)";', source, re.S).group(1)
    paragraph = re.sub(r'\\\n\s*', '', paragraph)
    paragraph = json.loads('"' + paragraph + '"')
    assert len(labels) == 46
    return {'labels': sum(sum(c != ' ' for c in text) for text in labels),
            'para': 12 * sum(c != ' ' for c in paragraph)}


def configurations(suite):
    features = ['swash_only', 'default_swash']
    fonts = ['Arial', 'RobotoFlex']
    if suite == 'warm':
        return [(feature, workload, font) for feature in features
                for workload in ['labels', 'para'] for font in fonts]
    if suite == 'generic':
        return [(feature, f'{temperature}_{layout}_{mode}_{position}', 'Arial')
                for feature in features + ['default_no_swash']
                for temperature in ['warm', 'cold'] for layout in ['labels', 'para']
                for mode in ['fill', 'stroke'] for position in ['positive', 'negative']
                if feature == 'default_no_swash' or mode == 'stroke']
    assert suite == 'cold'
    fonts += ['Vollkorn', 'PTSans']
    workloads = [f'cold_{layout}_{phase}' for layout in ['labels', 'para']
                 for phase in ['natural', 'onephase']]
    workloads += ['grid_singleton', 'grid_two_phases', 'grid_unique_sizes', 'grid_pollution']
    return ([(feature, workload, font) for feature in features for workload in workloads for font in fonts]
            + [(feature, 'grid_unique_variations', 'RobotoFlex') for feature in features])


def planned_order(configs, variants, blocks):
    order = []
    for block in range(blocks):
        rotated = configs[block % len(configs):] + configs[:block % len(configs)]
        candidate_order = variants[block % len(variants):] + variants[:block % len(variants)]
        if block % 2:
            candidate_order = candidate_order[::-1]
        for config in rotated:
            order.extend((block, *config, variant) for variant in candidate_order)
    return order


def validate_identities(study, folder, meta, records, suite):
    for font, info in meta['fonts'].items():
        assert digest(Path(info['path'])) == info['sha256'], (folder.name, font, 'font changed')
    source_root = Path('/private/tmp/femtovg-review-fixes-scenes/harness-src') if suite == 'scenes' else study / 'harness-src'
    for name, expected in meta['harness_files'].items():
        assert digest(source_root / name) == expected, (folder.name, name, 'harness changed')
    if suite == 'scenes':
        scene_root = Path('/private/tmp/femtovg-review-fixes-scenes')
        for name, expected in meta['assets'].items():
            assert digest(scene_root / 'assets' / name) == expected, (folder.name, name, 'scene asset changed')
        optional = meta['optional_host_emoji_font']
        assert Path(optional['path']).exists() == optional['present']
        if optional['present']:
            assert digest(Path(optional['path'])) == optional['sha256']
    binary_paths = {}
    for record in records:
        label = f'{record["variant"]}-{record["feature"]}'
        path = Path(record['command'][0])
        assert label in meta['binaries'], (folder.name, label)
        assert binary_paths.setdefault(label, path) == path, (folder.name, label, 'binary path changed')
    assert set(binary_paths) == set(meta['binaries']), (folder.name, 'unused/missing binary identity')
    for label, path in binary_paths.items():
        assert digest(path) == meta['binaries'][label], (folder.name, label, 'binary changed')


def parse_metrics(record):
    emitted = {}
    for line in record['stdout'].splitlines():
        parts = line.split()
        assert len(parts) == 4 and parts[:2] == ['RESULT', record['workload']], line
        assert parts[2] not in emitted, (record['workload'], 'duplicate metric')
        emitted[parts[2]] = float(parts[3])
    assert emitted
    assert all(math.isfinite(value) and value > 0 for value in emitted.values()), emitted
    emitted['med_us_per_frame'] = emitted.get('med_ns_per_frame', emitted['med_ns_per_glyph'] * emitted['glyphs']) / 1000
    emitted['med_us_total'] = emitted.get('ns_total', emitted['med_us_per_frame'] * 1000) / 1000
    assert set(record['metrics']) == set(emitted), (record['workload'], 'stored metric set')
    for key, value in emitted.items():
        near(record['metrics'][key], value, f'raw/{record["workload"]}/{key}')
    return emitted


def validate_process_record(record, meta, suite, glyph_counts):
    workload, font = record['workload'], record['font']
    metrics = parse_metrics(record)
    command = record['command']
    assert len(command) == 5 and command[1] == workload
    assert command[2] == meta['fonts'][font]['path']
    assert command[3] == ('1' if font == 'RobotoFlex' else '0')
    warm = suite == 'warm' or (suite == 'generic' and workload.startswith('warm_'))
    assert int(command[4]) == (meta['frames'] if warm else meta['cold_samples_per_process'])
    if workload.startswith('grid_'):
        expected_frames = {'grid_singleton': 1, 'grid_two_phases': 2, 'grid_unique_sizes': 32,
                           'grid_unique_variations': 32, 'grid_pollution': 67}[workload]
        assert metrics['frames'] == expected_frames and metrics['glyphs'] == expected_frames * 94
        assert abs(metrics['med_ns_per_glyph'] * metrics['glyphs'] - metrics['ns_total']) <= .005 * metrics['glyphs'] + .500001
        assert abs(metrics['med_ns_per_frame'] * metrics['frames'] - metrics['ns_total']) <= .005 * metrics['frames'] + .500001
    else:
        layout = workload if suite == 'warm' else workload.split('_')[1]
        assert metrics['glyphs'] == glyph_counts[layout], (workload, metrics['glyphs'], glyph_counts[layout])
        if suite == 'warm':
            assert metrics['runs'] == (46 if workload == 'labels' else 12)
            assert metrics['p10_ns_per_glyph'] <= metrics['med_ns_per_glyph']
        if suite == 'cold':
            assert metrics['frames'] == 1
    return metrics


SCENE_PHASES = {'demo': [('first_paint', 1), ('warm', 30), ('zoom_in', 12), ('zoom_out', 12), ('pan', 10)],
                'text': [('first_paint', 1), ('warm', 30), ('x_advance', 10), ('x_return', 10), ('y_advance', 10),
                         ('size_advance', 12), ('size_return', 12), ('reflow', 3)]}


def parse_scene_metrics(record, name):
    assert record['command'][1:] == [record['scene'], '1', '1']
    emitted = list(csv.DictReader(io.StringIO(record['stdout'])))
    assert list(emitted[0]) == ['scene', 'phase', 'trial', 'frames', 'draw_us', 'flush_us', 'total_us']
    assert [(p['phase'], int(p['frames'])) for p in emitted] == SCENE_PHASES[record['scene']]
    assert len(emitted) == len(record['metrics'])
    parsed = {}
    for raw, stored in zip(emitted, record['metrics']):
        assert raw['scene'] == record['scene'] and raw['trial'] == '0'
        assert set(raw) == set(stored)
        for key in ['scene', 'phase', 'trial']:
            assert raw[key] == stored[key]
        assert int(raw['frames']) == stored['frames']
        values = {key: float(raw[key]) for key in ['draw_us', 'flush_us', 'total_us']}
        assert all(math.isfinite(value) and value >= 0 for value in values.values())
        assert values['total_us'] > 0
        assert abs(values['draw_us'] + values['flush_us'] - values['total_us']) <= .00000151
        for key, value in values.items():
            near(stored[key], value, f'{name}/{record["scene"]}/{raw["phase"]}/{key}')
        parsed[raw['phase']] = values['total_us']
    # Sum phase means weighted by all measured frames in this process/block.
    parsed['measured_sequence'] = sum(parsed[phase] * frames for phase, frames in SCENE_PHASES[record['scene']])
    return parsed


def bootstrap_indices(blocks):
    generator = random.Random(61432)
    return [generator.choices(range(blocks), k=blocks) for _ in range(10000)]


def interval(values, draws):
    if all(value == values[0] for value in values):
        return [values[0], values[0]]
    replicates = sorted(median([values[index] for index in sample]) for sample in draws)
    return [replicates[250], replicates[9750]]


def paired_statistics(reference, selected, draws):
    assert len(reference) == len(selected) == 12
    ratios = [candidate / base for candidate, base in zip(selected, reference)]
    deltas = [candidate - base for candidate, base in zip(selected, reference)]
    return {'reference_median': median(reference), 'selected_median': median(selected),
            'median_paired_ratio': median(ratios), 'paired_ratio_ci95': interval(ratios, draws),
            'median_paired_delta': median(deltas), 'paired_delta_ci95': interval(deltas, draws),
            'paired_ratios': ratios, 'paired_deltas': deltas, 'paired_ratio_range': [min(ratios), max(ratios)]}


def audit_process_cohort(study, name, draws, glyph_counts):
    folder = study / name
    meta = json.loads((folder / 'metadata.json').read_text())
    suite = meta['suite']
    assert meta['blocks'] == 12
    configs = configurations(suite)
    variants = meta['variants']
    assert variants == (['master', 'finalgenericrestore'] if suite == 'generic' else ['master', 'base', 'finalgenericrestore'])
    records = read_records(folder)
    expected_order = planned_order(configs, variants, 12)
    actual_order = [(r['block'], r['feature'], r['workload'], r['font'], r['variant']) for r in records]
    assert actual_order == expected_order, (name, '12-block full matrix/order')
    retry_check = audit_retry_retention(folder, meta, records, expected_order, 'workload')
    validate_identities(study, folder, meta, records, suite)
    by_key = {}
    counts = Counter()
    for record in records:
        block, feature, workload, font, variant = (record[key] for key in ['block', 'feature', 'workload', 'font', 'variant'])
        metrics = validate_process_record(record, meta, suite, glyph_counts)
        key = (feature, workload, font, variant, block)
        assert key not in by_key
        by_key[key] = metrics
        counts[variant] += 1
    original = json.loads((folder / 'summary.json').read_text())
    assert [(r['feature'], r['workload'], r['font'], r['variant']) for r in original] == [(*config, variant) for config in configs for variant in variants]
    audited = []
    for row in original:
        config = (row['feature'], row['workload'], row['font'])
        reference = [by_key[(*config, 'master', b)] for b in range(12)]
        candidate = [by_key[(*config, row['variant'], b)] for b in range(12)]
        ratio = paired_statistics([m['med_ns_per_glyph'] for m in reference], [m['med_ns_per_glyph'] for m in candidate], draws)
        frame = paired_statistics([m['med_us_per_frame'] for m in reference], [m['med_us_per_frame'] for m in candidate], draws)
        sequence = paired_statistics([m['med_us_total'] for m in reference], [m['med_us_total'] for m in candidate], draws)
        expected = {'median_ns_per_glyph': median(m['med_ns_per_glyph'] for m in candidate),
                    'median_us_per_frame': frame['selected_median'], 'median_us_total': sequence['selected_median'],
                    'median_paired_ratio': ratio['median_paired_ratio'], 'paired_ratio_ci95': ratio['paired_ratio_ci95'],
                    'paired_ratio_range': ratio['paired_ratio_range'], 'paired_ratios': ratio['paired_ratios'],
                    'median_paired_delta_us_per_frame': frame['median_paired_delta'], 'paired_deltas': frame['paired_deltas']}
        for key, value in expected.items():
            near(row[key], value, f'{name}/{config}/{row["variant"]}/{key}')
        audited.append({'cohort': name, 'suite': suite, **{k: row[k] for k in ['feature', 'workload', 'font', 'variant']},
                        **expected, 'master_median_us_per_frame': frame['reference_median'],
                        'master_median_us_total': sequence['reference_median'],
                        'paired_delta_us_per_frame_ci95': frame['paired_delta_ci95'],
                        'median_paired_sequence_ratio': sequence['median_paired_ratio'], 'paired_sequence_ratio_ci95': sequence['paired_ratio_ci95'],
                        'median_paired_delta_us_total': sequence['median_paired_delta'], 'paired_delta_us_total_ci95': sequence['paired_delta_ci95']})
    return {'cohort': name, 'raw_records_used': len(records), 'raw_sha256': digest(folder / 'raw.jsonl'),
            'configurations': len(configs), 'blocks': 12, 'per_variant_counts': dict(counts), 'summary_rows_verified': len(original),
            'whole_block_environment_retry_audit': retry_check}, audited


def audit_scenes(study, name, draws):
    folder = study / name
    meta = json.loads((folder / 'metadata.json').read_text())
    assert meta['blocks'] == 12
    configs = scene_configurations()
    expected = scene_planned_order(configs, 12)
    records = read_records(folder)
    assert [(r['block'], r['feature'], r['scene'], r['font'], r['variant']) for r in records] == expected
    retry_check = audit_retry_retention(folder, meta, records, expected, 'scene')
    validate_identities(study, folder, meta, records, 'scenes')
    phases = SCENE_PHASES
    by_key = {}
    phase_records = 0
    for record in records:
        parsed = parse_scene_metrics(record, name)
        key = (record['feature'], record['scene'], record['font'], record['variant'], record['block'])
        assert key not in by_key
        by_key[key] = parsed
        phase_records += len(record['metrics'])
    original = json.loads((folder / 'summary.json').read_text())
    assert [(r['feature'], r['scene'], r['font'], r['phase']) for r in original] == [(*config, phase) for config in configs for phase, _ in phases[config[1]]]
    audited = []
    lookup = {(r['feature'], r['scene'], r['font'], r['phase']): r for r in original}
    for config in configs:
        for phase in [name for name, _ in phases[config[1]]] + ['measured_sequence']:
            reference = [by_key[(*config, 'master', block)][phase] for block in range(12)]
            candidate = [by_key[(*config, 'final', block)][phase] for block in range(12)]
            stats = paired_statistics(reference, candidate, draws)
            if phase != 'measured_sequence':
                row = lookup[(*config, phase)]
                expected = {'master_median_us_per_frame': stats['reference_median'], 'final_median_us_per_frame': stats['selected_median'],
                            'median_paired_ratio': stats['median_paired_ratio'], 'paired_ratio_ci95': stats['paired_ratio_ci95'],
                            'median_paired_delta_us_per_frame': stats['median_paired_delta'], 'paired_ratios': stats['paired_ratios'], 'paired_deltas': stats['paired_deltas']}
                for key, value in expected.items():
                    near(row[key], value, f'{name}/{config}/{phase}/{key}')
            audited.append({'cohort': name, 'suite': 'scenes', 'feature': config[0], 'scene': config[1], 'font': config[2],
                            'phase': phase, 'units': 'us/sequence' if phase == 'measured_sequence' else 'us/frame',
                            'measured_frames': sum(count for _, count in phases[config[1]]) if phase == 'measured_sequence' else dict(phases[config[1]])[phase], **stats})
    return {'cohort': name, 'raw_records_used': len(records), 'phase_records_used': phase_records,
            'raw_sha256': digest(folder / 'raw.jsonl'), 'blocks': 12, 'configurations': len(configs),
            'per_variant_counts': dict(Counter(r['variant'] for r in records)), 'summary_rows_verified': len(original),
            'whole_block_environment_retry_audit': retry_check}, audited


def main():
    parser = argparse.ArgumentParser()
    timing = parser.add_mutually_exclusive_group()
    timing.add_argument('--timing-finished', action='store_true')
    timing.add_argument('--timing-paused', action='store_true')
    parser.add_argument('--cohorts', nargs='+')
    parser.add_argument('--cold-cohort')
    parser.add_argument('--scene-cohort', default='scenes-genericrestore')
    args = parser.parse_args()
    if not (args.timing_finished or args.timing_paused):
        raise SystemExit('Heavy audit held during timing; require --timing-finished or a coordinated --timing-paused.')
    study = Path(__file__).resolve().parent
    if args.cold_cohort is None:
        completed = [folder.name for folder in sorted(study.glob('cold-genericrestore*'))
                     if (folder / 'summary.json').exists() and not (folder / 'EXCLUDED.md').exists()]
        assert len(completed) <= 1, 'Specify --cold-cohort when more than one completed cold cohort exists.'
        args.cold_cohort = completed[0] if completed else 'cold-not-yet-complete'
    out = study / 'independent-audit'
    out.mkdir(exist_ok=True)
    glyphs = workload_counts(study)
    draws = bootstrap_indices(12)
    cohorts, audited = [], []
    names = args.cohorts or ['warm-genericrestore', 'generic-genericrestore', args.cold_cohort, args.scene_cohort]
    for name in names:
        if name == args.scene_cohort:
            continue
        checks, rows = audit_process_cohort(study, name, draws, glyphs)
        cohorts.append(checks)
        audited.extend(rows)
        print(f'{name}: {checks["raw_records_used"]} raw records, {checks["summary_rows_verified"]} summary rows verified', flush=True)
    scenes = []
    if args.scene_cohort in names:
        scene_checks, scenes = audit_scenes(study, args.scene_cohort, draws)
        cohorts.append(scene_checks)
        print(f'{args.scene_cohort}: {scene_checks["raw_records_used"]} processes, {scene_checks["phase_records_used"]} raw phase rows verified', flush=True)
    excluded = []
    for folder in sorted(study.glob('cold-genericrestore*')):
        if folder.name == args.cold_cohort or not (folder / 'raw.jsonl').exists():
            continue
        records = read_records(folder)
        meta = json.loads((folder / 'metadata.json').read_text())
        expected = planned_order(configurations('cold'), meta['variants'], meta['blocks'])
        actual = [(r['block'], r['feature'], r['workload'], r['font'], r['variant']) for r in records]
        assert actual == expected[:len(actual)], (folder.name, 'interrupted cohort prefix')
        for record in records:
            validate_process_record(record, meta, 'cold', glyphs)
        retry_check = audit_retry_retention(folder, meta, records, expected, 'workload', require_complete=False)
        note = folder / 'EXCLUDED.md'
        excluded.append({'cohort': folder.name, 'raw_records_retained': len(records), 'raw_sha256': digest(folder / 'raw.jsonl'),
                         'records_by_block': dict(Counter(r['block'] for r in records)), 'excluded_note': note.read_text() if note.exists() else 'Incomplete cohort: retained separately, never merged.'})
        excluded[-1]['whole_block_environment_retry_audit'] = retry_check
    selected = [r for r in audited if r['variant'] == 'finalgenericrestore']
    worst = {}
    for suite in ['warm', 'generic', 'cold']:
        subset = [r for r in selected if r['suite'] == suite]
        if not subset:
            continue
        worst[suite] = {'largest_absolute_frame_delta': max(subset, key=lambda r: r['median_paired_delta_us_per_frame']),
                        'largest_absolute_sequence_delta': max(subset, key=lambda r: r['median_paired_delta_us_total']),
                        'largest_upper_ci_frame_delta': max(subset, key=lambda r: r['paired_delta_us_per_frame_ci95'][1]),
                        'largest_upper_ci_sequence_delta': max(subset, key=lambda r: r['paired_delta_us_total_ci95'][1]),
                        'largest_ratio': max(subset, key=lambda r: r['median_paired_ratio'])}
    if scenes:
        worst['scenes'] = {'largest_absolute_frame_delta': max((r for r in scenes if r['phase'] != 'measured_sequence'), key=lambda r: r['median_paired_delta']),
                           'largest_absolute_sequence_delta': max((r for r in scenes if r['phase'] == 'measured_sequence'), key=lambda r: r['median_paired_delta'])}
    complete = len(cohorts) == 4
    result = {'status': 'passed' if complete else 'partial_passed', 'method': 'Independent stdout parsing, full 12-block matrix/order and identity checks, all accepted raw processes used; paired-block median bootstrap with 10000 draws, seed 61432, percentile indices 250/9750. Summary tolerances rel=1e-11 abs=1e-8.',
              'glyph_counts': glyphs, 'cohorts': cohorts, 'excluded_retained_cohorts': excluded,
              'all_rows': audited, 'scene_rows': scenes, 'pr_selected_all_final_rows': selected, 'worst_costs': worst,
              'limitations': 'Process stdout contains its aggregate timing metrics, not every individually timed frame/sample. Scene sequence sums include all emitted measured phases (65 demo/88 text frames) and exclude 119 unreported priming frames. Intervals are exploratory, without multiplicity correction; one machine, CPU drawing/flush only.'}
    (out / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    lines = ['# Independent final-study audit', '', f'Status: {result["status"]}; audited cohorts: {names}.', '', result['method'], '', '| Cohort | Raw process records used | Verified summary rows | Blocks |', '|---|---:|---:|---:|']
    lines += [f'| {c["cohort"]} | {c["raw_records_used"]} | {c["summary_rows_verified"]} | {c["blocks"]} |' for c in cohorts]
    lines += ['', f'Expected glyph counts: {glyphs}.', f'Interrupted raw cohorts retained separately: {[(e["cohort"], e["raw_records_retained"]) for e in excluded]}.', '', result['limitations'], '',
              'Full independently recomputed ratios, absolute delta confidence intervals, complete controlled-sequence costs, scene phase-weighted sums computed before medians, all final rows, and worst-cost selections are in RESULT.json. No selected-cohort raw process records were omitted.']
    (out / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    cost_lines = ['# Independently recomputed absolute costs', '',
                  'All final candidate rows are retained. Confidence intervals are exploratory paired-block percentile bootstraps; a positive point estimate whose interval crosses zero is inconclusive.', '',
                  '| Suite/features | Workload/font | Master us/frame | Final us/frame | Paired ratio | Paired delta us/frame (95% CI) | Paired delta us/sequence (95% CI) |',
                  '|---|---|---:|---:|---:|---:|---:|']
    for row in selected:
        frame_ci = row['paired_delta_us_per_frame_ci95']
        sequence_ci = row['paired_delta_us_total_ci95']
        cost_lines.append(f'| {row["suite"]}/{row["feature"]} | {row["workload"]}/{row["font"]} | {row["master_median_us_per_frame"]:.3f} | {row["median_us_per_frame"]:.3f} | {row["median_paired_ratio"]:.5f} | {row["median_paired_delta_us_per_frame"]:+.3f} [{frame_ci[0]:+.3f}, {frame_ci[1]:+.3f}] | {row["median_paired_delta_us_total"]:+.3f} [{sequence_ci[0]:+.3f}, {sequence_ci[1]:+.3f}] |')
    if scenes:
        cost_lines += ['', 'Scene sequence totals weight every emitted phase by its measured frame count within each block before computing paired ratios, deltas, medians, and intervals.', '',
                       '| Features | Scene/font | Phase | Master us | Final us | Paired ratio | Paired delta us (95% CI) |', '|---|---|---|---:|---:|---:|---:|']
        for row in scenes:
            delta_ci = row['paired_delta_ci95']
            cost_lines.append(f'| {row["feature"]} | {row["scene"]}/{row["font"]} | {row["phase"]} ({row["units"]}) | {row["reference_median"]:.3f} | {row["selected_median"]:.3f} | {row["median_paired_ratio"]:.5f} | {row["median_paired_delta"]:+.3f} [{delta_ci[0]:+.3f}, {delta_ci[1]:+.3f}] |')
    (out / 'ABSOLUTE-COSTS.md').write_text('\n'.join(cost_lines) + '\n')
    print(f'Audit passed; saved {out / "RESULT.json"}', flush=True)


if __name__ == '__main__':
    main()
