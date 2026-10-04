"""Persist the independent arithmetic check previously run inline.

No imports from the runner or analyzer; no builds or benchmark executions.
"""
import hashlib
import itertools
import json
import math
import random
import statistics
from pathlib import Path

BENCH = Path(__file__).resolve().parent
OUT = BENCH / 'runs' / 'comparison'
plan = json.loads((OUT / 'PLAN.json').read_text())
raw = [json.loads(line) for line in (OUT / 'raw.jsonl').read_text().splitlines()]
reported = json.loads((OUT / 'SUMMARY.json').read_text())
variants = ('master', 'before', 'after')
assert plan['orders'] == list(map(list, itertools.permutations(variants)))
assert len(raw) == 486
assert len(set((r['block'], r['variant'], r['case']) for r in raw)) == 126
groups = {}
for row in raw:
    assert row['order'] == plan['orders'][row['block']]
    key = row['case'], row['phase']
    pair = row['block'], row['variant']
    assert pair not in groups.setdefault(key, {})
    groups[key][pair] = row['draw_us' if row['case'].startswith('demo-') else 'total_us']
assert len(groups) == 27
assert all(set(group) == set(itertools.product(range(6), variants)) for group in groups.values())
assert len(reported) == 27
recomputed = []
for index, (key, values) in enumerate(sorted(groups.items())):
    report = reported[index]
    assert key == (report['case'], report['phase'])
    result = {'case': key[0], 'phase': key[1], 'blocks': 6}
    for variant in variants:
        result[variant] = statistics.median(values[block, variant] for block in range(6))
        assert math.isclose(report[variant], result[variant], rel_tol=1e-11, abs_tol=1e-8)
    for candidate, baseline in [('before', 'master'), ('after', 'master'), ('after', 'before')]:
        percentages = [100 * (values[block, candidate] / values[block, baseline] - 1) for block in range(6)]
        delta = statistics.median(values[block, candidate] - values[block, baseline] for block in range(6))
        rng = random.Random(20261004 + index)
        bootstrap = sorted(statistics.median(rng.choices(percentages, k=6)) for _ in range(5000))
        label = f'{candidate}_vs_{baseline}'
        expected = [statistics.median(percentages), bootstrap[125], bootstrap[4874], delta]
        actual = [report[label + '_percent'], *report[label + '_ci95'], report[label + '_delta_us']]
        assert all(math.isclose(a, e, rel_tol=1e-11, abs_tol=1e-8) for a, e in zip(actual, expected))
        result[label + '_percent'] = expected[0]
        result[label + '_ci95'] = expected[1:3]
        result[label + '_delta_us'] = expected[3]
        result[label + '_ratio_of_medians_percent'] = 100 * (result[candidate] / result[baseline] - 1)
    recomputed.append(result)

build = json.loads((BENCH / 'BUILD.json').read_text())
before_files = build['variants']['before']['source']['files']
after_files = build['variants']['after']['source']['files']
changed = [file for file in sorted(set(before_files) | set(after_files))
           if before_files.get(file) != after_files.get(file)]
assert changed == ['src/text/swash_rasterizer.rs']
attempts = [(path.name, json.loads((path / 'STATUS.json').read_text())['status'])
            for path in sorted((OUT / 'attempts').iterdir())]
assert attempts == [(f'block-{block:02d}-00', 'accepted') for block in range(6)]
guard_statuses = sorted(set(json.loads(line)['status'] for line in (OUT / 'guard-checks.jsonl').read_text().splitlines()))
assert guard_statuses == ['idle']
result = {
    'status': 'PASS',
    'scope': 'Independent raw matrix and numerical reconstruction; source/binary hashing is covered by the separate prepared audit.',
    'accepted_records': len(raw), 'accepted_processes': 126,
    'complete_groups': len(groups), 'verified_paired_contrasts': 81,
    'bootstrap': {'resamples': 5000, 'seed': '20261004 + sorted group index', 'percentile_indices': [125, 4874]},
    'tolerance': {'relative': 1e-11, 'absolute': 1e-8},
    'input_sha256': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
                     for name in ('PLAN.json', 'raw.jsonl', 'SUMMARY.json')},
    'before_after_snapshot_changed_files': changed,
    'accepted_attempts': attempts, 'guard_statuses': guard_statuses,
    'wholly_positive_after_before_intervals': [f'{r["case"]}/{r["phase"]}' for r in recomputed if r['after_vs_before_ci95'][0] > 0],
    'wholly_positive_after_master_intervals': [f'{r["case"]}/{r["phase"]}' for r in recomputed if r['after_vs_master_ci95'][0] > 0],
    'recomputed_summary': recomputed,
    'limits': [
        'Six exploratory blocks do not prove zero cost or equivalence; no multiplicity correction.',
        'Medians of paired ratios and deltas differ from ratios and differences of marginal medians.',
        'These CPU/Void workloads do not measure GPU/backend performance.',
        'Earlier runs are separate evidence and are not pooled into causal estimates here.',
    ],
}
(BENCH / 'INDEPENDENT_NUMERIC_AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS: 486 records,126 processes,27 complete groups,81 paired contrasts; no wholly positive after/before interval.')
