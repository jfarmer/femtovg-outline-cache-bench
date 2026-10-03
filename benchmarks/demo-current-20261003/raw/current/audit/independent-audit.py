#!/usr/bin/env python3
"""Independent audit from original stdout and ledger; imports no study analyzer."""
import collections
import argparse
import csv
import datetime
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import random

parser = argparse.ArgumentParser()
parser.add_argument('--study', choices=['primary', 'extremes'], default='primary')
arguments = parser.parse_args()
ROOT = Path('/private/tmp/femtovg-current-demo-20261003' if arguments.study == 'primary' else '/private/tmp/femtovg-current-demo-extremes-20261003')
COHORT = ROOT / ('demo-current-native' if arguments.study == 'primary' else 'demo-extremes-native')
OUT = ROOT / 'audit'
OUT.mkdir(exist_ok=True)
PHASES = [('first_paint', 1), ('warm', 30), ('zoom_in', 12), ('zoom_out', 12), ('pan', 10)]
FEATURES = ['default_swash', 'default_no_swash']
FONTS = ['RobotoFlex', 'PTSans', 'Vollkorn', 'Rye'] if arguments.study == 'primary' else ['FleurDeLeah', 'DiplomataSC']
VARIANTS = ['master', 'final']
CONFIGURATIONS = len(FEATURES) * len(FONTS)
RECORDS_PER_BLOCK = CONFIGURATIONS * len(VARIANTS)
EXPECTED_RECORDS = 12 * RECORDS_PER_BLOCK
EXPECTED_SUMMARY_ROWS = CONFIGURATIONS * 6


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def lines(name):
    return [json.loads(line) for line in (COHORT / name).read_text().splitlines() if line.strip()]


def median(values):
    values = sorted(values)
    count = len(values)
    return values[count // 2] if count % 2 else (values[count // 2 - 1] + values[count // 2]) / 2.0


comparisons = 0
maximum_error = 0.0


def equal(actual, expected, label):
    global comparisons, maximum_error
    comparisons += 1
    if isinstance(expected, (float, int)):
        error = abs(actual - expected)
        maximum_error = max(maximum_error, error)
        assert error <= max(1e-8, abs(expected) * 1e-12), (label, actual, expected, error)
    elif isinstance(expected, list):
        assert len(actual) == len(expected), label
        for index, (a, e) in enumerate(zip(actual, expected)):
            equal(a, e, f'{label}[{index}]')
    else:
        assert actual == expected, (label, actual, expected)


plan = json.loads((COHORT / 'PLAN.json').read_text())
metadata = json.loads((COHORT / 'metadata.json').read_text())
stored = json.loads((COHORT / 'summary.json').read_text())
complete = json.loads((COHORT / 'COMPLETE.json').read_text())
raw = lines('raw.jsonl')
attempts = lines('attempts.jsonl')
excluded = lines('excluded-raw.jsonl')
ledger = lines('ledger.jsonl')
guards = lines('guard-checks.jsonl')
quiet = lines('quiet-intervals.jsonl')
interference = lines('interference-events.jsonl')
assert digest(COHORT / 'PLAN.json') == metadata['plan_sha256']
assert (ROOT / 'PLAN.json').read_bytes() == (COHORT / 'PLAN.json').read_bytes()
assert plan['logical_blocks'] == 12 and plan['dpi'] == 2 and plan['trials_per_process'] == 1
assert plan['authorization']['exact_user_instruction'] == 'Anyways, do what you need to do to get the current demo cdata'
assert len(raw) == len(attempts) == EXPECTED_RECORDS and len(excluded) == 0 and raw == attempts
assert len(ledger) == 12 and len(stored) == EXPECTED_SUMMARY_ROWS and complete['environment_retries'] == 0
assert not (COHORT / 'STOPPED.json').exists()

configs = [(feature, font) for feature in FEATURES for font in FONTS]
order_counts = {f'{feature}-{font}': collections.Counter() for feature, font in configs}
parsed_by_key = {}
phase_observations = 0
verified_guard_records = 0
process_ids = set()
all_phase_counts = collections.Counter()

for block in range(12):
    entries = raw[block * RECORDS_PER_BLOCK:(block + 1) * RECORDS_PER_BLOCK]
    schedule = configs[block % CONFIGURATIONS:] + configs[:block % CONFIGURATIONS]
    planned = plan['blocks'][block]
    assert planned['logical_block'] == block
    expected = []
    for position, (feature, font) in enumerate(schedule):
        stable_index = configs.index((feature, font))
        variants = ['master', 'final'] if (block + stable_index) % 2 == 0 else ['final', 'master']
        config_id = f'{feature}-{font}'
        order_counts[config_id][tuple(variants)] += 1
        declaration = planned['configurations'][position]
        assert (declaration['feature'], declaration['font'], declaration['variant_order']) == (feature, font, variants)
        expected.extend((feature, font, variant) for variant in variants)
    assert [(r['feature'], r['font'], r['variant']) for r in entries] == expected
    entry = ledger[block]
    assert entry['block'] == block and entry['attempt'] == block + 1 and entry['status'] == 'accepted'
    assert entry['process_records'] == RECORDS_PER_BLOCK and entry['accepted_raw_offset'] == entry['attempt_record_offset'] == block * RECORDS_PER_BLOCK
    assert entry['attempt_id'] == f'block-{block:02d}-attempt-{block + 1:03d}'
    for record in entries:
        assert record['block'] == block and record['attempt_id'] == entry['attempt_id']
        assert record['returncode'] == 0 and record['scene'] == 'demo' and record['stderr'] == ''
        assert record['command'] == [plan['binaries'][f'{record["variant"]}-{record["feature"]}']['binary_path'], 'demo', '1', '2']
        assert record['selected_font_path'] == str(ROOT / plan['fonts'][record['font']]['file'])
        assert entry['started_utc'] <= record['started_utc'] <= record['ended_utc'] <= entry['ended_utc']
        for stage in ['before', 'after']:
            guard = record[f'guard_{stage}']
            assert guard['status'] == 'idle' and not guard['pids'] and not guard['process_families_and_names_only']
            assert guard['context'] == {'stage': f'{stage}_process', 'block': block, 'attempt_id': record['attempt_id'],
                    'configuration_id': record['configuration_id'], 'variant': record['variant']}
            assert guard in guards
            if stage == 'before':
                assert guard['checked_utc'] <= record['started_utc']
            else:
                assert guard['checked_utc'] >= record['ended_utc']
            verified_guard_records += 1
        original_rows = list(csv.DictReader(io.StringIO(record['stdout'])))
        assert [(r['phase'], int(r['frames'])) for r in original_rows] == PHASES
        measurements = {}
        totals = {metric: 0.0 for metric in ['draw_us', 'flush_us', 'total_us']}
        for index, row in enumerate(original_rows):
            assert row['scene'] == 'demo' and row['trial'] == '0'
            decoded = {**row, 'trial': 0, 'frames': int(row['frames']),
                       **{key: float(row[key]) for key in totals}}
            assert decoded == record['metrics'][index]
            decimal_values = [Decimal(row[key]) for key in totals]
            assert all(value.is_finite() and value >= 0 for value in decimal_values)
            assert abs(decimal_values[0] + decimal_values[1] - decimal_values[2]) <= Decimal('0.00001')
            for metric in totals:
                totals[metric] += decoded[metric] * decoded['frames']
            measurements[row['phase']] = decoded['total_us']
            phase_observations += 1
            all_phase_counts[row['phase']] += 1
        assert sum(int(r['frames']) for r in original_rows) == 65
        for metric in totals:
            equal(record['reported_sequence_totals_us'][metric], totals[metric], 'weighted sequence total')
        measurements['reported_sequence'] = totals['total_us']
        key = (record['feature'], record['font'], record['variant'], block)
        assert key not in parsed_by_key
        parsed_by_key[key] = measurements
        process_ids.add((record['attempt_id'], record['configuration_id'], record['variant']))

assert len(process_ids) == EXPECTED_RECORDS and phase_observations == EXPECTED_RECORDS * 5 and verified_guard_records == EXPECTED_RECORDS * 2
for count in order_counts.values():
    assert count == {('master', 'final'): 6, ('final', 'master'): 6}
assert quiet and quiet[0]['required_quiet_seconds'] == 60
before_start = [g for g in guards if g['context']['stage'] == 'quiet_interval']
last_match = max((g['checked_utc'] for g in before_start if g['status'] == 'matched'), default=metadata['started_utc'])
first_process_utc = min(r['guard_before']['checked_utc'] for r in raw)
assert (datetime.datetime.fromisoformat(first_process_utc) - datetime.datetime.fromisoformat(last_match)).total_seconds() >= 60
process_guard_rows = [g for g in guards if g['context']['stage'] in ['before_process', 'after_process']]
assert len(process_guard_rows) == EXPECTED_RECORDS * 2 and all(g['status'] == 'idle' for g in process_guard_rows)

random_source = random.Random(61432)
resamples = [[random_source.randrange(12) for _ in range(12)] for _ in range(10000)]
recalculated = []
for feature, font in configs:
    for phase in [p for p, _ in PHASES] + ['reported_sequence']:
        frames = 65 if phase == 'reported_sequence' else dict(PHASES)[phase]
        master = [parsed_by_key[feature, font, 'master', block][phase] for block in range(12)]
        final = [parsed_by_key[feature, font, 'final', block][phase] for block in range(12)]
        differences = [f - m for m, f in zip(master, final)]
        ratios = [f / m for m, f in zip(master, final)]
        differences_bootstrap = sorted(median(differences[i] for i in indexes) for indexes in resamples)
        ratios_bootstrap = sorted(median(ratios[i] for i in indexes) for indexes in resamples)
        expected = {'configuration_id': f'{feature}-{font}', 'feature': feature, 'font': font, 'scene': 'demo', 'phase': phase,
                    'units': 'us/sequence' if phase == 'reported_sequence' else 'us/frame', 'frames': frames,
                    'master_median_us': median(master), 'final_median_us': median(final),
                    'median_paired_delta_us': median(differences), 'paired_delta_ci95_us': [differences_bootstrap[250], differences_bootstrap[9750]],
                    'median_paired_ratio': median(ratios), 'paired_ratio_ci95': [ratios_bootstrap[250], ratios_bootstrap[9750]],
                    'paired_deltas_us': differences, 'paired_ratios': ratios, 'master_values_us': master, 'final_values_us': final}
        if phase == 'reported_sequence':
            expected['median_paired_delta_us_per_reported_frame'] = expected['median_paired_delta_us'] / 65
            expected['paired_delta_ci95_us_per_reported_frame'] = [value / 65 for value in expected['paired_delta_ci95_us']]
        recorded = next(r for r in stored if (r['feature'], r['font'], r['phase']) == (feature, font, phase))
        assert set(recorded) == set(expected)
        for field, value in expected.items():
            equal(recorded[field], value, f'{feature}/{font}/{phase}/{field}')
        recalculated.append(expected)

prepared_hashes = {}
for path, expected in plan['prepared_files'].items():
    assert digest(ROOT / path) == expected, path
    prepared_hashes[path] = expected
for record in plan['binaries'].values():
    assert digest(record['binary_path']) == record['binary_sha256']
for path, expected in plan['external_scene_assets'].items():
    assert digest(path) == expected
emoji = plan['optional_host_emoji_font']
assert Path(emoji['path']).exists() == emoji['present']
if emoji['present']:
    assert digest(emoji['path']) == emoji['sha256']
pin_path = ROOT / 'provenance/PIN_VERIFICATION.json'
pins = json.loads(pin_path.read_text())
assert pins['head'] == plan['candidate_commit'] and pins['upstream_master'] == plan['baseline_commit']
assert pins['binaries'] == {label: record['binary_sha256'] for label, record in plan['binaries'].items()}
for name, identity in pins['production_identity'].items():
    current = Path('/Users/jesse/github/femtovg') / name
    frozen = Path('/private/tmp/femtovg-review-fixes-scenes/source/final') / name
    assert digest(current) == identity['current_sha256'] and digest(frozen) == identity['frozen_sha256']
    if name.endswith('swash_rasterizer.rs'):
        marker = b'#[cfg(test)]\nmod tests'
        assert current.read_bytes().split(marker)[0] == frozen.read_bytes().split(marker)[0]
    else:
        assert current.read_bytes() == frozen.read_bytes()
    assert identity['released_code_equal'] is True

non_swash = [row for row in recalculated if row['feature'] == 'default_no_swash']
assert len(non_swash) == len(FONTS) * 6
non_swash_crossing = sum(row['paired_delta_ci95_us'][0] < 0 < row['paired_delta_ci95_us'][1] for row in non_swash)
swash = [row for row in recalculated if row['feature'] == 'default_swash']
signs = collections.Counter('saving' if row['paired_delta_ci95_us'][1] < 0 else 'cost' if row['paired_delta_ci95_us'][0] > 0 else 'inconclusive' for row in swash)
result = {'status': 'PASS', 'independent_analyzer_sha256': digest(__file__), 'cohort': str(COHORT),
          'logical_blocks': 12, 'accepted_process_records': EXPECTED_RECORDS, 'attempt_process_records': EXPECTED_RECORDS, 'excluded_process_records': 0,
          'environment_retries': 0, 'phase_observations': phase_observations, 'reported_frames_per_process': 65,
          'summary_rows_independently_recomputed': EXPECTED_SUMMARY_ROWS, 'before_after_idle_guards': verified_guard_records,
          'prestart_guard_matches': sum(g['status'] == 'matched' for g in before_start),
          'configuration_order_counts': {key: {'master_final': value[('master', 'final')], 'final_master': value[('final', 'master')]} for key, value in order_counts.items()},
          'numeric_comparisons': comparisons, 'maximum_absolute_reproduction_error': maximum_error,
          'prepared_file_hashes_checked': len(prepared_hashes), 'pin_verification_sha256': digest(pin_path),
          'non_swash_intervals_crossing_zero': non_swash_crossing, 'non_swash_summary_rows': len(non_swash), 'swash_interval_classification': dict(signs),
          'raw_hashes': {name: digest(COHORT / name) for name in ['raw.jsonl', 'attempts.jsonl', 'excluded-raw.jsonl', 'ledger.jsonl', 'guard-checks.jsonl', 'summary.json', 'PLAN.json']},
          'all_recomputed_rows': recalculated,
          'limits': ['One trial per process and one machine; exploratory intervals without multiplicity adjustment.',
                     'Process guards establish sampled before/after name checks, not continuous absence of background activity.',
                     'Non-Swash intervals crossing zero is not an equivalence test; prior synthetic paragraph costs remain evidence.',
                     'CPU actual demo drawing/layout/Void flush; setup, GPU, presentation and application startup excluded.',
                     'Complete patch comparison does not isolate hinted-cache, arena, prepass or code generation effects.']}
(OUT / 'AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
report = ['Independent current-demo audit: PASS.', '',
          f'Reconstructed all {EXPECTED_RECORDS} process records from original CSV stdout, all {phase_observations} phase observations, all 65-frame sequence totals, and all {EXPECTED_SUMMARY_ROWS} summary rows/paired bootstrap intervals. No study analyzer was imported. All numeric results reproduced within tolerance.',
          f'Twelve complete chronological blocks match the independently generated rotation. Every configuration has six AB and six BA orders. Attempts equal accepted raw records, excluded raw is empty, and all {verified_guard_records} before/after process guards are idle. Initial quiet checks may contain observed activity; these precede the verified 60-second quiet interval and no timing record is filtered.',
          f'Maximum absolute numeric reproduction error: {maximum_error:.12g}. Swash exploratory interval classification: {dict(signs)}. {non_swash_crossing}/{len(non_swash)} non-Swash intervals cross zero; this does not establish equivalence.', '',
          '| Font, default+Swash | Master first paint ms | Final first paint ms | Paired saving ms [exploratory95% interval] | Median paired reduction |',
          '|---|---:|---:|---:|---:|']
for font in FONTS:
    row = next(r for r in swash if r['font'] == font and r['phase'] == 'first_paint')
    lo, hi = row['paired_delta_ci95_us']
    report.append(f'| {font} | {row["master_median_us"]/1000:.3f} | {row["final_median_us"]/1000:.3f} | {-row["median_paired_delta_us"]/1000:.3f} [{-hi/1000:.3f}, {-lo/1000:.3f}] | {(1-row["median_paired_ratio"])*100:.2f}% |')
report.extend(['', 'Paired differences and ratios need not equal arithmetic using the marginal medians. The comparison includes the complete patch. Warm/pan differences cannot be assigned directly to geometry-cache hits when the bitmap atlas is already warm.',
               'Current-source six-file identities, released Swash prefix, four binary hashes, all prepared files/fonts/licenses, fixed assets and optional emoji font checked. Original sandbox-guard failure is a separate zero-timing attempt and was not altered.',
               'Prior synthetic non-Swash paragraph costs of 1.3–2.4µs/frame remain disclosed. This demo cannot erase those observations. No GPU/application startup improvement or universal benefit is established.'])
(OUT / 'REPORT.md').write_text('\n'.join(report) + '\n')
print(json.dumps({key: value for key, value in result.items() if key not in ['all_recomputed_rows', 'raw_hashes', 'configuration_order_counts', 'limits']}, indent=2))
