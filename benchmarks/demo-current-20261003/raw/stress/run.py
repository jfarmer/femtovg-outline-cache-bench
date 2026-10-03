#!/usr/bin/env python3
"""Predeclared paired proof-sheet processes; never run during another study."""
import argparse
from collections import Counter
import csv
import datetime
import hashlib
import io
import json
from pathlib import Path
import random
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parent
FONTS = {
    'FleurDeLeah': '/private/tmp/femtovg-current-demo-extremes-20261003/assets/FleurDeLeah-Regular.ttf',
    'RobotoFlex': '/private/tmp/femtovg-current-demo-20261003/assets/RobotoFlex-VariableFont.ttf',
    'Rye': '/private/tmp/femtovg-current-demo-20261003/assets/Rye-Regular.ttf',
}
FONT_DOCS = {
    'FleurDeLeah': ['/private/tmp/femtovg-current-demo-extremes-20261003/assets/LICENSE-FleurDeLeah',
                    '/private/tmp/femtovg-current-demo-extremes-20261003/provenance/Fleur-acquisition-record.json'],
    'RobotoFlex': ['/private/tmp/femtovg-current-demo-20261003/assets/LICENSE-Roboto',
                   '/private/tmp/femtovg-current-demo-20261003/provenance/copied-control-assets.json'],
    'Rye': ['/private/tmp/femtovg-current-demo-20261003/assets/LICENSE-Rye',
            '/private/tmp/femtovg-current-demo-20261003/provenance/Rye-acquisition-record.json'],
}
PHASES = [('first_paint', 1), ('warm', 30), ('new_size', 12), ('return', 1)]
BUILD_NAMES = r'cargo|rustc|clang|clang\+\+|ld|ld.lld|cc|cc1|swift|swiftc|swift-frontend|ninja|cmake'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def idle(out):
    probe = subprocess.run(['pgrep', '-x', BUILD_NAMES], capture_output=True, text=True)
    assert probe.returncode in [0, 1], probe.stderr
    if probe.returncode == 0:
        event = {'utc': utc(), 'reason': 'compiler/build/linker process-name match', 'pids': probe.stdout.split()}
        (out / 'ABORT.json').write_text(json.dumps(event, indent=2) + '\n')
        raise SystemExit('Environment interference: cohort stopped; every record retained, no summary.')


def median_interval(values):
    rng = random.Random(61432)
    resampled = sorted(statistics.median(rng.choices(values, k=len(values))) for _ in range(10000))
    return [resampled[250], resampled[9750]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--blocks', type=int, choices=[8, 12], default=12)
    parser.add_argument('--fonts', nargs='+', choices=list(FONTS), default=list(FONTS))
    parser.add_argument('--dpi', type=float, default=2.0)
    parser.add_argument('--code-ready', action='store_true')
    args = parser.parse_args()
    if not args.code_ready:
        raise SystemExit('Hold: root must confirm source/build readiness and a coordinated timing window.')
    assert len(args.fonts) == len(set(args.fonts)) and 0 < args.dpi <= 3
    out = ROOT / args.output
    assert not out.exists(), 'Refusing to overwrite a cohort'
    out.mkdir()
    identities = {variant: json.loads((ROOT / 'builds' / f'{variant}.json').read_text()) for variant in ['master', 'final']}
    for build in identities.values():
        assert sha(Path(build['binary_path'])) == build['binary_sha256']
        assert sha(ROOT / 'harness-src/main.rs') == build['harness_sha256']
    order = []
    for block in range(args.blocks):
        rotated = args.fonts[block % len(args.fonts):] + args.fonts[:block % len(args.fonts)]
        for index, font in enumerate(rotated):
            variants = ['master', 'final'] if (block + index) % 2 == 0 else ['final', 'master']
            order.extend({'block': block, 'font': font, 'variant': variant} for variant in variants)
    pair_orders = {font: Counter(tuple(e['variant'] for e in order if e['font'] == font and e['block'] == block)
                                for block in range(args.blocks)) for font in args.fonts}
    if args.blocks == 12:
        assert all(counts == Counter({('master', 'final'): 6, ('final', 'master'): 6}) for counts in pair_orders.values())
    plan = {'declared_utc': utc(), 'blocks': args.blocks, 'fonts': args.fonts, 'dpi': args.dpi,
            'font_assets': {name: {'path': FONTS[name], 'sha256': sha(Path(FONTS[name]))} for name in args.fonts},
            'font_license_and_acquisition_records': {name: [{'path': path, 'sha256': sha(Path(path))} for path in FONT_DOCS[name]] for name in args.fonts},
            'builds': identities, 'runner_sha256': sha(Path(__file__)), 'phases': PHASES,
            'pair_order_counts': {font: {'master_then_final': counts[('master', 'final')], 'final_then_master': counts[('final', 'master')]} for font, counts in pair_orders.items()},
            'process_order': order, 'nominal_glyph_requests_per_frame': 1980,
            'nominal_distinct_glyph_size_instances_per_frame': 198,
            'actual_counts': 'Public TextMetrics determine actual shaped requests and distinct glyph/font/size instances; ligatures may alter nominal counts.',
            'policy': 'Fixed complete paired matrix; guard before and after EACH process; abort whole cohort on environment interference; no timing-value filtering.',
            'timed_work': 'Public fill_text layout and atlas drawing, adaptive page layout, simple panel paths and Void flush. Fresh Canvas/font registration outside timing; all44frames included in weighted sequence.',
            'limits': 'Designed stress case, not a representative application or a proved globally worst font. No GPU/window/pixel timing; font cost attribution not isolated to hinting. Pressure does not prove eviction.'}
    (out / 'PLAN.json').write_text(json.dumps(plan, indent=2) + '\n')
    quiet = time.monotonic()
    while time.monotonic() - quiet < 60:
        idle(out)
        time.sleep(1)
    observations = []
    for entry in order:
        idle(out)
        before = utc()
        command = [identities[entry['variant']]['binary_path'], FONTS[entry['font']], 'proofsheet', str(args.dpi), '1']
        process = subprocess.run(command, capture_output=True, text=True)
        record = {**entry, 'command': command, 'stdout': process.stdout, 'stderr': process.stderr,
                  'returncode': process.returncode, 'guard_before_utc': before, 'guard_after_utc': None, 'guard_after_status': 'unchecked'}
        try:
            idle(out)
            record['guard_after_status'] = 'idle'
        except SystemExit:
            record['guard_after_status'] = 'matched'
            raise
        finally:
            record['guard_after_utc'] = utc()
            with (out / 'raw.jsonl').open('a') as stream:
                stream.write(json.dumps(record) + '\n')
        if process.returncode != 0:
            event = {'utc': utc(), 'reason': 'benchmark process failed', **entry, 'returncode': process.returncode,
                     'stdout_stderr_retained_in': 'raw.jsonl', 'command': command}
            (out / 'ABORT.json').write_text(json.dumps(event, indent=2) + '\n')
            raise SystemExit(f'Benchmark process failed: {process.stderr}')
        parsed = list(csv.DictReader(io.StringIO(process.stdout)))
        assert [(row['phase'], int(row['frames'])) for row in parsed] == PHASES
        for row in parsed:
            assert row['scene'] == 'proofsheet' and row['trial'] == '0'
            assert int(row['text_draw_calls_per_frame']) == 30 and int(row['nominal_characters_per_row']) == 66
            assert int(row['glyph_requests_per_frame']) > 0 and int(row['distinct_glyph_size_instances_per_frame']) > 0
        record['metrics'] = [{**r, **{key: float(r[key]) for key in ['draw_us', 'flush_us', 'total_us']},
                              **{key: int(r[key]) for key in ['frames', 'glyph_requests_per_frame', 'distinct_glyph_size_instances_per_frame', 'text_draw_calls_per_frame', 'logical_width', 'logical_height', 'nominal_characters_per_row']}} for r in parsed]
        # The raw record includes the entire stdout, preserving these phase metrics.
        observations.append(record)
        print(f'Completed block{entry["block"] + 1}/{args.blocks} {entry["font"]} {entry["variant"]}', flush=True)
    # Bootstrap is deferred until all timing processes have finished.
    summary = []
    for font in args.fonts:
        for phase in [name for name, _ in PHASES] + ['complete_sequence']:
            values = {}
            counts = {}
            for variant in ['master', 'final']:
                rows = [r for r in observations if r['font'] == font and r['variant'] == variant]
                assert [r['block'] for r in rows] == list(range(args.blocks))
                values[variant] = [sum(m['frames'] * m['total_us'] for m in r['metrics']) if phase == 'complete_sequence'
                                   else next(m['total_us'] for m in r['metrics'] if m['phase'] == phase) for r in rows]
                counts[variant] = [[(m['phase'], m['glyph_requests_per_frame'], m['distinct_glyph_size_instances_per_frame'], m['logical_width'], m['logical_height']) for m in r['metrics']] for r in rows]
            assert counts['master'] == counts['final'], 'Visible workload/counts differ between variants'
            ratios = [candidate / reference for candidate, reference in zip(values['final'], values['master'])]
            deltas = [candidate - reference for candidate, reference in zip(values['final'], values['master'])]
            summary.append({'font': font, 'phase': phase, 'units': 'us/sequence' if phase == 'complete_sequence' else 'us/frame',
                'master_median': statistics.median(values['master']), 'final_median': statistics.median(values['final']),
                'median_paired_ratio': statistics.median(ratios), 'paired_ratio_ci95': median_interval(ratios),
                'median_paired_delta': statistics.median(deltas), 'paired_delta_ci95': median_interval(deltas),
                'paired_ratios': ratios, 'paired_deltas': deltas})
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    lines = ['# Paired public font proof-sheet stress scene', '', plan['limits'], '',
             '| Font | Phase | Master us | Final us | Paired ratio [95% CI] | Paired delta us [95% CI] |', '|---|---|---:|---:|---|---|']
    for row in summary:
        rci, dci = row['paired_ratio_ci95'], row['paired_delta_ci95']
        lines.append(f'| {row["font"]} | {row["phase"]} ({row["units"]}) | {row["master_median"]:.3f} | {row["final_median"]:.3f} | {row["median_paired_ratio"]:.4f} [{rci[0]:.4f}, {rci[1]:.4f}] | {row["median_paired_delta"]:+.3f} [{dci[0]:+.3f}, {dci[1]:+.3f}] |')
    (out / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    complete = {'completed_utc': utc(), 'completed_processes': len(observations), 'expected_processes': len(order),
                'summary_rows': len(summary), 'phase_observations': sum(len(r['metrics']) for r in observations),
                'measured_frames': sum(m['frames'] for r in observations for m in r['metrics']),
                'interference_events': 0, 'all_processes_returned_zero': True,
                'all_before_after_process_guards_idle': True,
                'plan_sha256': sha(out / 'PLAN.json'), 'raw_sha256': sha(out / 'raw.jsonl'),
                'summary_sha256': sha(out / 'summary.json'), 'report_sha256': sha(out / 'REPORT.md')}
    assert len(observations) == len(order) and not (out / 'ABORT.json').exists()
    (out / 'COMPLETE.json').write_text(json.dumps(complete, indent=2) + '\n')


if __name__ == '__main__':
    main()
