#!/usr/bin/env python3
"""Post hoc chronological-prefix analysis; independent of original analyzer.

Do not run benchmark binaries. Preserve all original interrupted-cohort files.
The selection rule is written before accessing any numerical timing metrics.
"""
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import runpy


ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'provisional-cold-audit'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paired(reference, candidate, audit, draws):
    assert len(reference) == len(candidate) == 8
    ratios = [c / r for r, c in zip(reference, candidate)]
    deltas = [c - r for r, c in zip(reference, candidate)]
    return {'master_median': audit['median'](reference), 'candidate_median': audit['median'](candidate),
            'median_paired_ratio': audit['median'](ratios), 'paired_ratio_ci95': audit['interval'](ratios, draws),
            'median_paired_delta': audit['median'](deltas), 'paired_delta_ci95': audit['interval'](deltas, draws),
            'ratios': ratios, 'deltas': deltas}


def main():
    audit = runpy.run_path(str(ROOT / 'independent-audit.py'))
    folders = [p for p in ROOT.glob('cold-genericrestore*') if (p / 'EXCLUDED.md').exists()]
    starts = {p.name: json.loads((p / 'metadata.json').read_text())['started_utc'] for p in folders}
    first = min(folders, key=lambda p: audit['timestamp'](starts[p.name]))
    assert first.name == 'cold-genericrestore'
    meta = json.loads((first / 'metadata.json').read_text())
    assert meta['suite'] == 'cold' and meta['blocks'] == 12
    assert meta['variants'] == ['master', 'base', 'finalgenericrestore']
    originals = {name: sha(first / name) for name in ['raw.jsonl', 'metadata.json', 'EXCLUDED.md']}
    plan = {'status': 'explicit post hoc provisional reanalysis; not the planned 12-block primary cold cohort',
            'selection_rule': 'Choose the chronologically earliest interrupted finalgenericrestore cold campaign and its first eight complete logical blocks 0 through 7; exclude its partial block 8 and all other campaigns. Never choose or combine records using timing effects.',
            'source_cohort': first.name, 'candidate_cohort_start_times': starts,
            'selected_blocks': list(range(8)), 'expected_configurations': 66,
            'expected_variants': meta['variants'], 'expected_selected_records': 1584,
            'excluded_partial_block': 8, 'expected_excluded_partial_records': 174,
            'bootstrap': {'draws': 10000, 'seed': 61432, 'paired_blocks': 8, 'percentile_indices': [250, 9750]},
            'original_artifact_sha256': originals,
            'limitations': 'Selection was declared after the campaign stopped, before this cold numerical analysis. The original guard checked before configurations, not continuously or after each process; later detected interference neither establishes earlier idle conditions nor invalidates every earlier record. Individual seven-sample values were not emitted. Intervals are exploratory, without multiplicity adjustment, on one machine; CPU glyph drawing and Void flush only, excluding layout and GPU work.'}
    OUT.mkdir(exist_ok=True)
    plan_path = OUT / 'PLAN.json'
    if plan_path.exists():
        existing = json.loads(plan_path.read_text())
        assert {k: v for k, v in existing.items() if k != 'declared_utc'} == plan
        plan = existing
    else:
        plan['declared_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        plan_path.write_text(json.dumps(plan, indent=2) + '\n')
    # Numerical timing access begins only after the selection rule is persisted.
    records = audit['read_records'](first)
    configs = audit['configurations']('cold')
    variants = meta['variants']
    selected = [r for r in records if r['block'] in plan['selected_blocks']]
    omitted = [r for r in records if r['block'] not in plan['selected_blocks']]
    key = lambda r: (r['block'], r['feature'], r['workload'], r['font'], r['variant'])
    expected_order = audit['planned_order'](configs, variants, 8)
    assert [key(r) for r in selected] == expected_order
    assert len(configs) == 66 and len(selected) == 1584 and len(omitted) == 174
    assert [key(r) for r in omitted] == audit['planned_order'](configs, variants, 12)[1584:1758]
    assert all(r['block'] == 8 for r in omitted)
    audit['validate_identities'](ROOT, first, meta, selected, 'cold')
    glyph_counts = audit['workload_counts'](ROOT)
    by_key = {}
    for record in records:
        metrics = audit['validate_process_record'](record, meta, 'cold', glyph_counts)
        if record['block'] < 8:
            by_key[(record['feature'], record['workload'], record['font'], record['variant'], record['block'])] = metrics
    assert len(by_key) == 1584
    # Store exact selected/omitted records without modifying the original file.
    raw_lines = (first / 'raw.jsonl').read_text().splitlines(keepends=True)
    (OUT / 'selected-raw.jsonl').write_text(''.join(raw_lines[:1584]))
    (OUT / 'excluded-partial-raw.jsonl').write_text(''.join(raw_lines[1584:]))
    draws = audit['bootstrap_indices'](8)
    rows = []
    for feature, workload, font in configs:
        config = (feature, workload, font)
        master = [by_key[(*config, 'master', b)] for b in range(8)]
        for variant in variants:
            candidate = [by_key[(*config, variant, b)] for b in range(8)]
            glyph = paired([r['med_ns_per_glyph'] for r in master], [r['med_ns_per_glyph'] for r in candidate], audit, draws)
            frame = paired([r['med_us_per_frame'] for r in master], [r['med_us_per_frame'] for r in candidate], audit, draws)
            sequence = paired([r['med_us_total'] for r in master], [r['med_us_total'] for r in candidate], audit, draws)
            rows.append({'feature': feature, 'workload': workload, 'font': font, 'variant': variant, 'paired_blocks': 8,
                         'glyphs': candidate[0]['glyphs'], 'measured_frames': candidate[0]['frames'],
                         'master_median_ns_per_glyph': glyph['master_median'], 'candidate_median_ns_per_glyph': glyph['candidate_median'],
                         'median_paired_ratio': glyph['median_paired_ratio'], 'paired_ratio_ci95': glyph['paired_ratio_ci95'],
                         'master_median_us_per_frame': frame['master_median'], 'candidate_median_us_per_frame': frame['candidate_median'],
                         'median_paired_delta_us_per_frame': frame['median_paired_delta'], 'paired_delta_us_per_frame_ci95': frame['paired_delta_ci95'],
                         'master_median_us_total': sequence['master_median'], 'candidate_median_us_total': sequence['candidate_median'],
                         'median_paired_sequence_ratio': sequence['median_paired_ratio'], 'paired_sequence_ratio_ci95': sequence['paired_ratio_ci95'],
                         'median_paired_delta_us_total': sequence['median_paired_delta'], 'paired_delta_us_total_ci95': sequence['paired_delta_ci95'],
                         'paired_ratios': glyph['ratios'], 'paired_frame_deltas': frame['deltas'], 'paired_sequence_deltas': sequence['deltas']})
    final = [r for r in rows if r['variant'] == 'finalgenericrestore']
    assert len(rows) == 198 and len(final) == 66
    worst = {'largest_frame_delta': max(final, key=lambda r: r['median_paired_delta_us_per_frame']),
             'largest_sequence_delta': max(final, key=lambda r: r['median_paired_delta_us_total']),
             'largest_frame_upper_ci': max(final, key=lambda r: r['paired_delta_us_per_frame_ci95'][1]),
             'largest_sequence_upper_ci': max(final, key=lambda r: r['paired_delta_us_total_ci95'][1]),
             'largest_paired_ratio': max(final, key=lambda r: r['median_paired_ratio'])}
    classifications = {'interval_below_one': [r for r in final if r['paired_ratio_ci95'][1] < 1],
                       'interval_above_one': [r for r in final if r['paired_ratio_ci95'][0] > 1],
                       'interval_crosses_one': [r for r in final if r['paired_ratio_ci95'][0] <= 1 <= r['paired_ratio_ci95'][1]]}
    result = {'status': 'provisional_audit_passed; not primary planned 12-block data', 'plan': plan,
              'source_raw_records_retained': len(records), 'complete_records_used': len(selected),
              'partial_records_excluded': len(omitted), 'blocks_used': 8, 'configurations': len(configs),
              'per_variant_records_used': dict(Counter(r['variant'] for r in selected)),
              'glyph_counts': glyph_counts, 'all_198_rows': rows, 'all_66_final_rows': final,
              'worst_costs': worst, 'exploratory_ratio_classifications': classifications,
              'selected_raw_sha256': sha(OUT / 'selected-raw.jsonl'), 'excluded_partial_raw_sha256': sha(OUT / 'excluded-partial-raw.jsonl')}
    for name, expected in originals.items():
        assert sha(first / name) == expected, ('Original artifact changed', name)
    (OUT / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
    report = ['# Provisional eight-block cold reanalysis', '', plan['status'] + '.', '', plan['selection_rule'], '',
              f'Used all {len(selected)} records in the complete 66-configuration × 3-variant × 8-block matrix; excluded the {len(omitted)} records from partial block 8. All font, executable and harness hashes, command arguments, glyph/frame counts, and emitted/stored timing identities passed independent checks. Original campaign files were unchanged.', '',
              'Paired-block medians and exploratory 95% percentile bootstrap intervals: 10,000 resamples of eight whole paired blocks, seed 61432; endpoints 250/9750. All 198 rows and 66 final-versus-master rows are in RESULT.json.', '',
              'Controlled sequence costs include every measured frame: singleton 1, two phases 2, distinct sizes 32, distinct normalized variable instances 32, pollution 67 (hot population + 64 pollution frames + return). Costs are compared per complete sequence before calculating paired statistics. The 64-size pollution workload measures pressure and return together; it has no instrumentation proving actual eviction. Roboto Flex natural/one-phase text uses weight 450; the controlled instance sweep uses weights 100 through 875.', '',
              plan['limitations'], '',
              f'Exploratory final/master ratio intervals: {len(classifications["interval_below_one"])} wholly below one, {len(classifications["interval_above_one"])} wholly above one, {len(classifications["interval_crosses_one"])} crossing one.', '',
              '| Features | Workload/font | Frames | Master us/frame | Final us/frame | Paired ratio (95% CI) | Paired delta us/frame (95% CI) | Master us/sequence | Final us/sequence | Paired delta us/sequence (95% CI) |',
              '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in final:
        ratio_ci, frame_ci, total_ci = (row[key] for key in ['paired_ratio_ci95', 'paired_delta_us_per_frame_ci95', 'paired_delta_us_total_ci95'])
        report.append(f'| {row["feature"]} | {row["workload"]}/{row["font"]} | {int(row["measured_frames"])} | {row["master_median_us_per_frame"]:.3f} | {row["candidate_median_us_per_frame"]:.3f} | {row["median_paired_ratio"]:.4f} [{ratio_ci[0]:.4f}, {ratio_ci[1]:.4f}] | {row["median_paired_delta_us_per_frame"]:+.3f} [{frame_ci[0]:+.3f}, {frame_ci[1]:+.3f}] | {row["master_median_us_total"]:.3f} | {row["candidate_median_us_total"]:.3f} | {row["median_paired_delta_us_total"]:+.3f} [{total_ci[0]:+.3f}, {total_ci[1]:+.3f}] |')
    (OUT / 'REPORT.md').write_text('\n'.join(report) + '\n')
    print(f'Provisional audit passed: {len(selected)} complete records, {len(rows)} comparison rows; {len(omitted)} partial records excluded. Saved {OUT}', flush=True)


if __name__ == '__main__':
    main()
