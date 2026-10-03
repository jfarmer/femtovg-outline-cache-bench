#!/usr/bin/env python3
"""Serial paired public demo/text scene timings; invoke only after source GO."""
import argparse
import csv
import datetime
import hashlib
import io
import json
import os
import random
import statistics
import subprocess
import time
from pathlib import Path
from run import ensure_idle, wait_idle

ROOT = Path(__file__).resolve().parent
SCENES = Path('/private/tmp/femtovg-review-fixes-scenes')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--blocks', type=int, default=12)
    parser.add_argument('--code-ready', action='store_true')
    parser.add_argument('--external-build-finished', action='store_true')
    parser.add_argument('--retry-interference', action='store_true')
    parser.add_argument('--quiet-seconds', type=int, default=60)
    parser.add_argument('--max-retries', type=int, default=30)
    parser.add_argument('--max-duration', type=int, default=1800)
    args = parser.parse_args()
    archive = ROOT / 'runners' / 'block-retry-v1' / 'scene-run.py'
    guard_archive = archive.with_name('run.py')
    if args.retry_interference and (sha(archive) != sha(Path(__file__)) or sha(guard_archive) != sha(ROOT / 'run.py')):
        raise SystemExit('Scene runner/guard archives differ from the predeclared live files.')
    if not args.code_ready:
        raise SystemExit('Wait for final source and build-idle GO')
    if not args.external_build_finished:
        raise SystemExit('Scene timing is held until the user confirms the external project build has finished.')
    out = ROOT / args.output
    if out.exists():
        raise SystemExit(f'Refusing to overwrite scene cohort {out}')
    provenance = json.loads((SCENES / 'provenance.json').read_text())
    for name, record in provenance['scene_sources'].items():
        if sha(SCENES / 'harness-src' / name) != record['sha256']:
            raise SystemExit(f'Archived scene adapter changed: {name}')
    for name, expected in provenance['assets'].items():
        if sha(SCENES / 'assets' / name) != expected:
            raise SystemExit(f'Scene asset changed: {name}')
    emoji = Path(provenance['optional_emoji_font'])
    fonts = {'RobotoFlex': SCENES / 'assets/RobotoFlex-VariableFont.ttf', 'Vollkorn': SCENES / 'assets/Vollkorn-Medium.ttf'}
    configs = [(feature, scene, font) for feature in ['default_swash', 'default_no_swash'] for scene, font in [('demo', 'RobotoFlex'), ('demo', 'Vollkorn'), ('text', 'RobotoFlex'), ('text', 'Vollkorn')]]
    identities = {}
    for feature in ['default_swash', 'default_no_swash']:
        for variant in ['master', 'final']:
            label = f'{variant}-{feature}'
            build = json.loads((ROOT / 'scene-builds' / f'{label}.json').read_text())
            if sha(Path(build['binary_path'])) != build['binary_sha256']:
                raise SystemExit(f'Scene binary changed: {label}')
            identities[label] = build['binary_sha256']
    if not args.retry_interference:
        ensure_idle()
    out.mkdir()
    (out / 'metadata.json').write_text(json.dumps({'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'blocks': args.blocks, 'binaries': identities, 'runner_sha256': sha(Path(__file__)), 'guard_sha256': sha(ROOT / 'run.py'),
        'fonts': {name: {'path': str(path), 'sha256': sha(path)} for name, path in fonts.items()}, 'assets': provenance['assets'],
        'optional_host_emoji_font': {'path': str(emoji), 'present': emoji.exists(), 'sha256': sha(emoji) if emoji.exists() else None},
        'harness_files': {p.name: sha(p) for p in (SCENES / 'harness-src').glob('*.rs')},
        'order': 'Configuration order rotates; paired variant order alternates per block/configuration.',
        'metrics': 'CPU actual archived scene adapters through public Canvas+Void flush; includes layout and other scene draw work; setup/font/image registration excluded; phase means; no GPU/window/pixels.',
        'platform': subprocess.check_output(['sw_vers'], text=True)}, indent=2) + '\n')
    plan = {'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'runner_sha256': sha(Path(__file__)), 'runner_archive': str(archive), 'guard_sha256': sha(ROOT / 'run.py'), 'guard_archive': str(guard_archive), 'logical_blocks': args.blocks,
            'expected_processes_per_accepted_block': len(configs) * 2, 'expected_summary_rows': 52,
            'policy': {'environment_retries': args.retry_interference, 'discard_unit': 'entire attempt of logical paired block', 'guard': 'before and after EACH process',
                       'trigger': 'compiler/build/linker process-name match', 'no_timing_value_filtering': True, 'quiet_seconds_before_start_or_replay': args.quiet_seconds,
                       'max_retries': args.max_retries, 'max_duration_seconds': args.max_duration},
            'blocks': [{'logical_block': b, 'configurations': [{'feature': f, 'scene': s, 'font': n, 'variant_order': ['master', 'final'] if (b + i) % 2 == 0 else ['final', 'master']} for i, (f, s, n) in enumerate(configs[b % len(configs):] + configs[:b % len(configs)])]} for b in range(args.blocks)]}
    (out / 'PLAN.json').write_text(json.dumps(plan, indent=2) + '\n')
    deadline = time.monotonic() + args.max_duration
    observations = []
    if args.retry_interference:
        print(f'Waiting for {args.quiet_seconds} quiet seconds before scene timing.', flush=True)
        wait_idle(out, args.quiet_seconds, max(1, deadline - time.monotonic()))
    block = retries = attempt = total_attempt_records = total_excluded_records = 0
    while block < args.blocks:
        if args.retry_interference and time.monotonic() > deadline:
            raise SystemExit('Scene environment duration limit reached; no completed-cohort report written.')
        attempt += 1
        attempt_start_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        attempt_offset = total_attempt_records
        block_records = []
        order = configs[block % len(configs):] + configs[:block % len(configs)]
        try:
            for index, (feature, scene, font) in enumerate(order):
                ensure_idle(out)
                for variant in (['master', 'final'] if (block + index) % 2 == 0 else ['final', 'master']):
                    if args.retry_interference:
                        ensure_idle(out)
                    before_guard_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    command = [str(ROOT / 'bin' / f'scenes-{variant}-{feature}'), scene, '1', '1']
                    env = dict(os.environ, FEMTOVG_REPLAY_TEXT_FONT=str(fonts[font]))
                    process = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
                    rows = list(csv.DictReader(io.StringIO(process.stdout)))
                    parsed = [{**r, **{k: float(r[k]) for k in ['draw_us', 'flush_us', 'total_us']}, 'frames': int(r['frames'])} for r in rows]
                    record = {'block': block, 'attempt': attempt, 'feature': feature, 'scene': scene, 'font': font, 'variant': variant, 'command': command, 'stdout': process.stdout, 'stderr': process.stderr, 'metrics': parsed,
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
            print(f'Environment interrupted scene block {block + 1}; replaying whole block after {args.quiet_seconds} quiet seconds (retry {retries}/{args.max_retries}).', flush=True)
            if retries > args.max_retries:
                raise SystemExit('Scene environment retry limit reached; no completed-cohort report written.')
            wait_idle(out, args.quiet_seconds, max(1, deadline - time.monotonic()))
            continue
        observations.extend(block_records)
        with (out / 'raw.jsonl').open('a') as stream:
            for record in block_records:
                stream.write(json.dumps(record) + '\n')
        with (out / 'ledger.jsonl').open('a') as stream:
            stream.write(json.dumps({'block': block, 'attempt': attempt, 'status': 'accepted', 'process_records': len(block_records), 'expected_process_records': len(configs) * 2,
                                     'started_utc': attempt_start_utc, 'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'attempt_record_offset': attempt_offset,
                                     'accepted_raw_offset': len(observations) - len(block_records)}) + '\n')
        print(f'Completed scene paired block {block + 1}/{args.blocks}', flush=True)
        block += 1
    summary = []
    report = ['Actual demo/text adapter CPU comparison against upstream 6a5f15a.', '', '| Features | Scene/font | Phase | Master us/frame | Final us/frame | Paired ratio | 95% interval | Paired delta us/frame |', '|---|---|---|---:|---:|---:|---|---:|']
    for feature, scene, font in configs:
        selected = [r for r in observations if (r['feature'], r['scene'], r['font']) == (feature, scene, font)]
        phases = [r['phase'] for r in selected[0]['metrics']]
        for phase in phases:
            values = {variant: {r['block']: next(m['total_us'] for m in r['metrics'] if m['phase'] == phase) for r in selected if r['variant'] == variant} for variant in ['master', 'final']}
            ratios = [values['final'][b] / values['master'][b] for b in range(args.blocks)]
            deltas = [values['final'][b] - values['master'][b] for b in range(args.blocks)]
            rng = random.Random(61432)
            bootstrap = sorted(statistics.median(rng.choices(ratios, k=len(ratios))) for _ in range(10000))
            row = {'feature': feature, 'scene': scene, 'font': font, 'phase': phase,
                   'master_median_us_per_frame': statistics.median(values['master'].values()), 'final_median_us_per_frame': statistics.median(values['final'].values()),
                   'median_paired_ratio': statistics.median(ratios), 'paired_ratio_ci95': [bootstrap[250], bootstrap[9750]],
                   'median_paired_delta_us_per_frame': statistics.median(deltas), 'paired_ratios': ratios, 'paired_deltas': deltas}
            summary.append(row)
            report.append(f'| {feature} | {scene}/{font} | {phase} | {row["master_median_us_per_frame"]:.2f} | {row["final_median_us_per_frame"]:.2f} | {row["median_paired_ratio"]:.3f} | {bootstrap[250]:.3f}–{bootstrap[9750]:.3f} | {row["median_paired_delta_us_per_frame"]:+.2f} |')
    report.extend(['', 'Intervals are exploratory 95% percentile bootstraps of independent paired blocks (10,000 resamples; no multiplicity correction). First-paint is a single frame per process; other phases report phase means. Void covers CPU scene drawing and flush only. One machine, release opt-level 3, no LTO.'])
    if args.retry_interference:
        report.extend(['', f'Predeclared environment policy: {retries} whole-block replays on process-name guard matches; every accepted process has before/after guards. Attempts, rejected whole blocks, ledger, and family/name evidence are retained; no timing-value filtering.'])
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (out / 'REPORT.md').write_text('\n'.join(report) + '\n')
    print('\n'.join(report), flush=True)

if __name__ == '__main__':
    main()
