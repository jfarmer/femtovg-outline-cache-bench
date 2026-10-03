#!/usr/bin/env python3
"""Rotate paired process trials; retain every raw result and absolute costs."""
import argparse
import datetime
import hashlib
import json
import os
import random
import shlex
import statistics
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_NAMES = 'cargo|rustc|clang|clang\\+\\+|ld|ld.lld|cc|cc1|swift|swiftc|swift-frontend|ninja|cmake'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def process_family(pid):
    # Inspect only this known guard PID. Never print/persist command arguments;
    # retain only the command family and process/parent names authorized by root.
    named = subprocess.run(['ps', '-o', 'ppid=,comm=', '-p', pid], capture_output=True, text=True)
    fields = named.stdout.strip().split(maxsplit=1)
    if len(fields) != 2 or not fields[0].isdecimal():
        return {'pid': pid, 'comm': None, 'family': 'exited-before-inspection'}
    parent, comm = fields
    parent_name = subprocess.run(['ps', '-o', 'comm=', '-p', parent], capture_output=True, text=True).stdout.strip()
    family = 'build/compiler/linker'
    if Path(comm).name in ['cargo', 'rustc']:
        inspected = subprocess.run(['ps', '-o', 'args=', '-p', pid], capture_output=True, text=True)
        try:
            words = shlex.split(inspected.stdout)
        except ValueError:
            words = []
        tail = words[1:]
        if any(word in ['-V', '-vV', '--version'] for word in tail):
            family = 'version'
        elif Path(comm).name == 'cargo':
            families = ['metadata', 'check', 'build', 'test', 'clippy', 'run', 'bench', 'rustc', 'rustdoc', 'fetch', 'fmt', 'locate-project', 'generate-lockfile']
            family = next((word for word in tail if word in families), 'unknown-cargo')
        else:
            family = 'compile'
    return {'pid': pid, 'comm': comm, 'family': family, 'parent_pid': parent, 'parent_comm': parent_name}


def ensure_idle(out=None):
    process = subprocess.run(['pgrep', '-x', BUILD_NAMES], capture_output=True, text=True)
    if process.returncode not in [0, 1]:
        raise SystemExit(f'Cannot check build process names: {process.stderr}')
    if process.returncode == 0:
        pids = [pid for pid in process.stdout.split() if pid.isdecimal()]
        families = [process_family(pid) for pid in pids]
        abort = {'aborted_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'reason': 'Build/compiler/linker process name guard matched', 'pids': pids,
                 'process_families_and_names_only': families}
        if out is not None:
            (out / 'ABORT.json').write_text(json.dumps(abort, indent=2) + '\n')
        raise SystemExit(f'Build/compiler/linker processes active; no timing started: {json.dumps(abort)}')


def wait_idle(out, seconds, limit=600):
    started = quiet = time.monotonic()
    last_pids = None
    while time.monotonic() - quiet < seconds:
        if time.monotonic() - started > limit:
            raise SystemExit(f'Sustained quiet interval not reached within {limit:.0f} seconds; timing remains paused.')
        try:
            ensure_idle(out)
        except SystemExit as error:
            if not str(error).startswith('Build/compiler/linker processes active;'):
                raise
            event = json.loads((out / 'ABORT.json').read_text())
            if event['pids'] != last_pids:
                with (out / 'interference-events.jsonl').open('a') as stream:
                    stream.write(json.dumps(event) + '\n')
            last_pids = event['pids']
            quiet = time.monotonic()
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--blocks', type=int, default=12)
    parser.add_argument('--frames', type=int, default=3000)
    parser.add_argument('--samples', type=int, default=7)
    parser.add_argument('--suite', choices=['warm', 'cold', 'generic'], default='warm')
    parser.add_argument('--code-ready', action='store_true', help='Required only after root confirms final source ready.')
    parser.add_argument('--external-build-finished', action='store_true', help='Required only after the user confirms the external project build has finished.')
    parser.add_argument('--variants', nargs='+')
    parser.add_argument('--retry-interference', action='store_true', help='Predeclare whole-block replay after external build-name matches; retain every attempted record.')
    parser.add_argument('--quiet-seconds', type=int, default=60)
    parser.add_argument('--max-retries', type=int, default=30)
    parser.add_argument('--max-duration', type=int, default=1800)
    args = parser.parse_args()
    if args.retry_interference and args.suite != 'cold':
        raise SystemExit('Whole-block environment retries are enabled only for the new cold cohort.')
    if not args.code_ready:
        raise SystemExit('Wait for root code-ready signal before timing')
    if not args.external_build_finished:
        raise SystemExit('Timing is held until the user confirms the external project build has finished.')
    out = ROOT / args.output
    if out.exists():
        raise SystemExit(f'Refusing to overwrite existing cohort {out}')
    variants = args.variants or (['master', 'base', 'final', 'ordinary-inline'] if args.suite == 'warm' else ['master', 'base', 'final'] if args.suite == 'cold' else ['master', 'final'])
    archive = ROOT / 'runners' / 'block-retry-v1' / 'run.py'
    if args.retry_interference and sha(archive) != sha(Path(__file__)):
        raise SystemExit('Runner archive does not match the predeclared live runner.')
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
    if not args.retry_interference:
        ensure_idle()
    out.mkdir()
    (out / 'metadata.json').write_text(json.dumps({
        'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'runner_sha256': sha(Path(__file__)),
        'suite': args.suite, 'blocks': args.blocks, 'frames': args.frames, 'cold_samples_per_process': args.samples, 'variants': variants,
        'binaries': identities, 'fonts': {font: {'path': str(path), 'sha256': sha(path)} for font, path, _ in fonts},
        'harness_files': {p.name: sha(p) for p in (ROOT / 'harness-src').glob('*.rs')},
        'order': 'Configuration order rotates per block; variant order rotates and reverses on odd blocks.',
        'environment_retry_policy': {'enabled': args.retry_interference, 'unit': 'whole paired block', 'trigger': 'compiler/build/linker process name matches before or after EACH process; no timing-based filtering',
                                     'quiet_seconds_before_start_or_replay': args.quiet_seconds, 'max_retries': args.max_retries,
                                     'retention': 'All process records in attempts.jsonl; accepted whole blocks also in raw.jsonl; rejected block records in excluded-raw.jsonl.'},
        'metrics': 'CPU public glyph draw+Void flush; warm has 20 initial frames excluded, cold uses a new Canvas/atlas/context per sample; all layout, registration and control construction outside timing. Complete controlled sequences include population and pollution. No GPU/layout timing.',
        'platform': subprocess.check_output(['sw_vers'], text=True),
    }, indent=2) + '\n')
    plan = {'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'runner_sha256': sha(Path(__file__)), 'runner_archive': str(archive), 'guard_sha256': sha(Path(__file__)), 'suite': args.suite,
            'logical_blocks': args.blocks, 'variants': variants, 'expected_processes_per_accepted_block': len(configs) * len(variants),
            'policy': {'environment_retries': args.retry_interference, 'discard_unit': 'entire attempt of a logical paired block',
                       'guard': 'before and after EACH process', 'trigger': 'compiler/build/linker process-name match; all known Cargo/rustc PID family inspection retained as names/families only',
                       'no_timing_value_filtering': True, 'quiet_seconds_before_start_or_replay': args.quiet_seconds, 'max_retries': args.max_retries, 'max_duration_seconds': args.max_duration},
            'blocks': [{'logical_block': b, 'configurations': [{'feature': f, 'workload': w, 'font': n, 'font_path': str(p), 'coords': c} for f, w, n, p, c in configs[b % len(configs):] + configs[:b % len(configs)]],
                        'variant_order': (list(reversed(variants[b % len(variants):] + variants[:b % len(variants)])) if b % 2 else variants[b % len(variants):] + variants[:b % len(variants)])} for b in range(args.blocks)]}
    (out / 'PLAN.json').write_text(json.dumps(plan, indent=2) + '\n')
    deadline = time.monotonic() + args.max_duration
    observations = []
    if args.retry_interference:
        print(f'Waiting for {args.quiet_seconds} quiet seconds before timing.', flush=True)
        wait_idle(out, args.quiet_seconds, max(1, deadline - time.monotonic()))
    block = retries = attempt = total_attempt_records = total_excluded_records = 0
    while block < args.blocks:
        if args.retry_interference and time.monotonic() > deadline:
            raise SystemExit('Environment cohort duration limit reached; no completed-cohort report written.')
        attempt += 1
        attempt_start_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        attempt_offset = total_attempt_records
        block_records = []
        order_configs = configs[block % len(configs):] + configs[:block % len(configs)]
        try:
            for feature, workload, font, path, coords in order_configs:
                ensure_idle(out)
                order = variants[block % len(variants):] + variants[:block % len(variants)]
                if block % 2:
                    order = list(reversed(order))
                for variant in order:
                    if args.retry_interference:
                        ensure_idle(out)
                    before_guard_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
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
                    record = {'block': block, 'attempt': attempt, 'feature': feature, 'workload': workload, 'font': font, 'variant': variant,
                              'command': command, 'stdout': result.stdout, 'stderr': result.stderr, 'metrics': metrics,
                              'guard_before_utc': before_guard_utc, 'guard_after_utc': None, 'guard_after_status': 'unchecked'}
                    block_records.append(record)
                    try:
                        if args.retry_interference:
                            ensure_idle(out)
                            record['guard_after_status'] = 'idle'
                    except SystemExit:
                        record['guard_after_status'] = 'guard_matched_or_failed'
                        raise
                    finally:
                        record['guard_after_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                        with (out / 'attempts.jsonl').open('a') as stream:
                            stream.write(json.dumps(record) + '\n')
                        total_attempt_records += 1
        except SystemExit as error:
            if not args.retry_interference or not str(error).startswith('Build/compiler/linker processes active;'):
                raise
            with (out / 'excluded-raw.jsonl').open('a') as stream:
                for record in block_records:
                    stream.write(json.dumps(record) + '\n')
            event = {**json.loads((out / 'ABORT.json').read_text()), 'block': block, 'attempt': attempt, 'rejected_process_records': len(block_records)}
            with (out / 'rejected-blocks.jsonl').open('a') as stream:
                stream.write(json.dumps(event) + '\n')
            with (out / 'ledger.jsonl').open('a') as stream:
                stream.write(json.dumps({**event, 'status': 'rejected', 'reason': 'environment_guard_match', 'started_utc': attempt_start_utc, 'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                         'attempt_record_offset': attempt_offset, 'process_records': len(block_records), 'excluded_raw_offset': total_excluded_records}) + '\n')
            total_excluded_records += len(block_records)
            retries += 1
            print(f'Environment interrupted block {block + 1}; replaying the entire block after {args.quiet_seconds} quiet seconds (retry {retries}/{args.max_retries}).', flush=True)
            if retries > args.max_retries:
                raise SystemExit('Environment retry limit reached; no completed-cohort report written.')
            wait_idle(out, args.quiet_seconds, max(1, deadline - time.monotonic()))
            continue
        observations.extend(block_records)
        with (out / 'raw.jsonl').open('a') as stream:
            for record in block_records:
                stream.write(json.dumps(record) + '\n')
        with (out / 'ledger.jsonl').open('a') as stream:
            stream.write(json.dumps({'block': block, 'attempt': attempt, 'status': 'accepted', 'process_records': len(block_records), 'expected_process_records': len(configs) * len(variants),
                                     'started_utc': attempt_start_utc, 'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'attempt_record_offset': attempt_offset,
                                     'accepted_raw_offset': len(observations) - len(block_records)}) + '\n')
        print(f'Completed paired block {block + 1}/{args.blocks}', flush=True)
        block += 1
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
    if args.retry_interference:
        text.extend(['', f'Predeclared environment policy: {retries} whole-block replays after process-name guard matches; no filtering based on timing values. All attempted/excluded process records and guard events are retained separately. Accepted blocks have a process-name check before and after every process.'])
    (out / 'summary.json').write_text(json.dumps(rows, indent=2) + '\n')
    (out / 'REPORT.md').write_text('\n'.join(text) + '\n')
    print('\n'.join(text), flush=True)


if __name__ == '__main__':
    main()
