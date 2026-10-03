#!/usr/bin/env python3
"""Derive paired absolute intervals from retained raw data without retiming."""
import argparse
import json
import random
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def interval(values):
    rng = random.Random(61432)
    samples = sorted(statistics.median(rng.choices(values, k=len(values))) for _ in range(10000))
    return [samples[250], samples[9750]]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cohorts', nargs='+')
    args = parser.parse_args()
    for cohort in args.cohorts:
        folder = ROOT / cohort
        raw = [json.loads(line) for line in (folder / 'raw.jsonl').read_text().splitlines()]
        scene = isinstance(raw[0]['metrics'], list)
        expanded = []
        for record in raw:
            if scene:
                for metric in record['metrics']:
                    expanded.append({**record, 'workload': f'{record["scene"]}/{metric["phase"]}', 'metrics': {'med_us_per_frame': metric['total_us'], 'med_us_total': metric['total_us'] * metric['frames'], 'frames': metric['frames']}})
            else:
                expanded.append(record)
        keys = sorted({(r['feature'], r['workload'], r['font']) for r in expanded})
        results = []
        report = ['Paired absolute CPU costs derived from retained process blocks.', '', '| Features | Workload | Font | Variant | Master us/frame | Candidate us/frame | Paired delta us/frame [95% interval] | Master us/sequence | Candidate us/sequence | Paired delta us/sequence [95% interval] |', '|---|---|---|---|---:|---:|---|---:|---:|---|']
        for key in keys:
            selected = [r for r in expanded if (r['feature'], r['workload'], r['font']) == key]
            reference = {r['block']: r['metrics'] for r in selected if r['variant'] == 'master'}
            for variant in sorted({r['variant'] for r in selected} - {'master'}):
                records = sorted((r for r in selected if r['variant'] == variant), key=lambda r: r['block'])
                deltas = [r['metrics']['med_us_per_frame'] - reference[r['block']]['med_us_per_frame'] for r in records]
                total_deltas = [r['metrics']['med_us_total'] - reference[r['block']]['med_us_total'] for r in records]
                row = {'feature': key[0], 'workload': key[1], 'font': key[2], 'variant': variant,
                       'master_median_us_per_frame': statistics.median(m['med_us_per_frame'] for m in reference.values()),
                       'candidate_median_us_per_frame': statistics.median(r['metrics']['med_us_per_frame'] for r in records),
                       'median_paired_delta_us_per_frame': statistics.median(deltas), 'paired_delta_us_per_frame_ci95': interval(deltas), 'paired_deltas_us_per_frame': deltas,
                       'master_median_us_total': statistics.median(m['med_us_total'] for m in reference.values()),
                       'candidate_median_us_total': statistics.median(r['metrics']['med_us_total'] for r in records),
                       'median_paired_delta_us_total': statistics.median(total_deltas), 'paired_delta_us_total_ci95': interval(total_deltas), 'paired_deltas_us_total': total_deltas}
                results.append(row)
                d = row['median_paired_delta_us_per_frame']; lo, hi = row['paired_delta_us_per_frame_ci95']
                td = row['median_paired_delta_us_total']; tl, th = row['paired_delta_us_total_ci95']
                report.append(f'| {key[0]} | {key[1]} | {key[2]} | {variant} | {row["master_median_us_per_frame"]:.2f} | {row["candidate_median_us_per_frame"]:.2f} | {d:+.2f} [{lo:+.2f}, {hi:+.2f}] | {row["master_median_us_total"]:.2f} | {row["candidate_median_us_total"]:.2f} | {td:+.2f} [{tl:+.2f}, {th:+.2f}] |')
        report.extend(['', 'Paired deltas compare each candidate process with the master process from the same rotating block; therefore the median paired delta need not equal the difference between marginal medians. Intervals resample complete paired blocks (10,000 median percentile bootstrap draws, seed 61432, indices 250/9750); exploratory, without multiplicity correction. Sequence totals are complete controlled sequences or the actual scene phase frame count; single-frame glyph workloads use the same per-frame/sequence value. CPU Canvas/Void only, no GPU or presented-frame timing.'])
        (folder / 'ABSOLUTE.json').write_text(json.dumps(results, indent=2) + '\n')
        (folder / 'ABSOLUTE.md').write_text('\n'.join(report) + '\n')
        print(f'Derived {len(results)} absolute rows: {cohort}', flush=True)

if __name__ == '__main__':
    main()
