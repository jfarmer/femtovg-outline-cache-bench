#!/usr/bin/env python3
"""Rotate paired process trials; retain every raw result and absolute costs."""
import argparse
import datetime
import hashlib
import json
import os
import random
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_NAMES = 'cargo|rustc|clang|clang\\+\\+|ld|ld.lld|cc|cc1|swift|swiftc|swift-frontend|ninja|cmake'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ensure_idle(out=None):
    process = subprocess.run(['pgrep', '-x', BUILD_NAMES], capture_output=True, text=True)
    if process.returncode not in [0, 1]:
        raise SystemExit(f'Cannot check build process names: {process.stderr}')
    if process.returncode == 0:
        pids = [pid for pid in process.stdout.split() if pid.isdecimal()]
        names = subprocess.run(['ps', '-o', 'pid=,comm=', '-p', ','.join(pids)], capture_output=True, text=True)
        abort = {'aborted_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reason': 'Build/compiler/linker process name guard matched', 'pids': pids,
                 'names_only_ps_stdout': names.stdout, 'names_only_ps_stderr': names.stderr, 'names_only_ps_returncode': names.returncode}
        if out is not None:
            (out / 'ABORT.json').write_text(json.dumps(abort, indent=2) + '\n')
        raise SystemExit(f'Build/compiler/linker processes active; no timing started: {json.dumps(abort)}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--blocks', type=int, default=12)
    parser.add_argument('--frames', type=int, default=3000)
    parser.add_argument('--samples', type=int, default=7)
    parser.add_argument('--suite', choices=['warm', 'cold', 'generic'], default='warm')
    parser.add_argument('--code-ready', action='store_true', help='Required only after root confirms final source ready.')
    parser.add_argument('--variants', nargs='+')
    args = parser.parse_args()
    if not args.code_ready:
        raise SystemExit('Wait for root code-ready signal before timing')
    out = ROOT / args.output
    if out.exists():
        raise SystemExit(f'Refusing to overwrite existing cohort {out}')
    variants = args.variants or (['master', 'base', 'final', 'ordinary-inline'] if args.suite == 'warm' else ['master', 'base', 'final'] if args.suite == 'cold' else ['master', 'final'])
    fonts = [('Arial', Path('/System/Library/Fonts/Supplemental/Arial.ttf'), '0'),
             ('RobotoFlex', ROOT / 'source/base/examples/assets/RobotoFlex-VariableFont.ttf', '1')]
    features = ['swash_only', 'default_swash']
    if args.suite == 'warm':
        workloads = ['labels', 'para']
        configs = [(feature, workload, font, path, coords) for feature in features for workload in workloads for font, path, coords in fonts]
    elif args.suite == 'cold':
        fonts += [('Vollkorn', Path('/Users/jesse/github/femtovg-outline-cache-bench/assets/Vollkorn-Medium.ttf'), '0'),
                  ('PTSans', Path('/Users/jesse/github/femtovg-outline-cache-bench/assets/PTSans-Regular.ttf'), '0')]
        workloads = [f'cold_{layout}_{phase}' for layout in ['labels', 'para'] for phase in ['natural', 'onephase']]
        workloads += ['grid_singleton', 'grid_two_phases', 'grid_unique_sizes', 'grid_pollution']
        configs = [(feature, workload, font, path, coords) for feature in features for workload in workloads for font, path, coords in fonts]
        configs += [(feature, 'grid_unique_variations', font, path, coords) for feature in features for font, path, coords in fonts if font == 'RobotoFlex']
    else:
        features += ['default_no_swash']
        fonts = fonts[:1]
        configs = [(feature, f'{temperature}_{layout}_{mode}_{position}', font, path, coords)
                   for feature in features for temperature in ['warm', 'cold']
                   for layout in ['labels', 'para'] for mode in ['fill', 'stroke']
                   for position in ['positive', 'negative'] for font, path, coords in fonts
                   if feature == 'default_no_swash' or mode == 'stroke']
    identities = {}
    for feature, _, _, _, _ in configs:
        for variant in variants:
            label = f'{variant}-{feature}'
            record = json.loads((ROOT / 'builds' / f'{label}.json').read_text())
            executable = record['executables'][args.suite]
            binary = Path(executable['binary_path'])
            if sha(binary) != executable['binary_sha256']:
                raise SystemExit(f'Binary changed: {label}')
            identities[label] = executable['binary_sha256']
    ensure_idle()
    out.mkdir()
    (out / 'metadata.json').write_text(json.dumps({
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'runner_sha256': sha(Path(__file__)),
        'suite': args.suite, 'blocks': args.blocks, 'frames': args.frames, 'cold_samples_per_process': args.samples, 'variants': variants,
        'binaries': identities, 'fonts': {font: {'path': str(path), 'sha256': sha(path)} for font, path, _ in fonts},
        'harness_files': {p.name: sha(p) for p in (ROOT / 'harness-src').glob('*.rs')},
        'order': 'Configuration order rotates per block; variant order rotates and reverses on odd blocks.',
        'metrics': 'CPU public glyph draw+Void flush; warm has 20 initial frames excluded, cold uses a new Canvas/atlas/context per sample; all layout, registration and control construction outside timing. Complete controlled sequences include population and pollution. No GPU/layout timing.',
        'platform': subprocess.check_output(['sw_vers'], text=True),
    }, indent=2) + '\n')
    observations = []
    for block in range(args.blocks):
        order_configs = configs[block % len(configs):] + configs[:block % len(configs)]
        for feature, workload, font, path, coords in order_configs:
            ensure_idle(out)
            order = variants[block % len(variants):] + variants[:block % len(variants)]
            if block % 2:
                order = list(reversed(order))
            for variant in order:
                count = args.frames if args.suite == 'warm' or (args.suite == 'generic' and workload.startswith('warm_')) else args.samples
                command = [str(ROOT / 'bin' / f'{variant}-{feature}-{args.suite}'), workload, str(path), coords, str(count)]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                metrics = {}
                for line in result.stdout.splitlines():
                    if line.startswith('RESULT '):
                        _, _, name, value = line.split()
                        metrics[name] = float(value)
                metrics['med_us_per_frame'] = metrics.get('med_ns_per_frame', metrics['med_ns_per_glyph'] * metrics['glyphs']) / 1000
                metrics['med_us_total'] = metrics.get('ns_total', metrics['med_us_per_frame'] * 1000) / 1000
                record = {'block': block, 'feature': feature, 'workload': workload, 'font': font, 'variant': variant,
                          'command': command, 'stdout': result.stdout, 'stderr': result.stderr, 'metrics': metrics}
                observations.append(record)
                with (out / 'raw.jsonl').open('a') as stream:
                    stream.write(json.dumps(record) + '\n')
        print(f'Completed paired block {block + 1}/{args.blocks}', flush=True)
    rows = []
    text = [f'{args.suite.title()} public glyph-run CPU comparison; primary baseline is exact upstream 6a5f15a.', '',
            '| Features | Workload | Font | Variant | ns/glyph | us/frame | us/sequence | Paired ratio | 95% interval | Paired delta us/frame |',
            '|---|---|---|---|---:|---:|---:|---:|---|---:|']
    for feature, workload, font, _, _ in configs:
        selected = [r for r in observations if (r['feature'], r['workload'], r['font']) == (feature, workload, font)]
        reference = {r['block']: r['metrics'] for r in selected if r['variant'] == variants[0]}
        for variant in variants:
            records = [r for r in selected if r['variant'] == variant]
            ratios = [r['metrics']['med_ns_per_glyph'] / reference[r['block']]['med_ns_per_glyph'] for r in records]
            deltas = [r['metrics']['med_us_per_frame'] - reference[r['block']]['med_us_per_frame'] for r in records]
            bootstrap_rng = random.Random(61432)
            bootstrap = sorted(statistics.median(bootstrap_rng.choices(ratios, k=len(ratios))) for _ in range(10000))
            interval = [bootstrap[250], bootstrap[9750]]
            row = {'feature': feature, 'workload': workload, 'font': font, 'variant': variant,
                   'median_ns_per_glyph': statistics.median(r['metrics']['med_ns_per_glyph'] for r in records),
                   'median_us_per_frame': statistics.median(r['metrics']['med_us_per_frame'] for r in records),
                   'median_us_total': statistics.median(r['metrics']['med_us_total'] for r in records),
                   'median_paired_ratio': statistics.median(ratios), 'median_paired_delta_us_per_frame': statistics.median(deltas),
                   'paired_ratio_ci95': interval,
                   'paired_ratio_range': [min(ratios), max(ratios)], 'paired_ratios': ratios, 'paired_deltas': deltas}
            rows.append(row)
            text.append(f'| {feature} | {workload} | {font} | {variant} | {row["median_ns_per_glyph"]:.2f} | {row["median_us_per_frame"]:.2f} | {row["median_us_total"]:.2f} | {row["median_paired_ratio"]:.3f} | {interval[0]:.3f}–{interval[1]:.3f} | {row["median_paired_delta_us_per_frame"]:+.2f} |')
    text.extend(['', 'Ratios are paired per process block. 95% percentile bootstrap intervals resample paired blocks (10,000 draws); exploratory, without multiplicity adjustment.',
                 'One machine, the recorded precomputed glyph runs, release profile, no LTO. These measurements cover CPU glyph drawing and Void flush; they do not measure full application or GPU frame latency.'])
    (out / 'summary.json').write_text(json.dumps(rows, indent=2) + '\n')
    (out / 'REPORT.md').write_text('\n'.join(text) + '\n')
    print('\n'.join(text), flush=True)


if __name__ == '__main__':
    main()
