#!/usr/bin/env python3
"""Fresh current-master/final actual demo replay; no source edits or builds.

Derived from the unexecuted earlier scene-run.py, with a new authorization gate,
four fonts, DPI2, balanced stable-configuration AB/BA order, absolute intervals,
complete reported sequence totals, and lossless process/guard failure retention.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
import random
import statistics
import subprocess
import time
from pathlib import Path

from guard import GuardMatched, append, ensure_idle, utc, wait_idle

ROOT = Path(__file__).resolve().parent
PHASE_FRAMES = {'first_paint': 1, 'warm': 30, 'zoom_in': 12, 'zoom_out': 12, 'pan': 10}
AUTHORIZATION = 'Anyways, do what you need to do to get the current demo cdata'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def parse_output(stdout):
    rows = list(csv.DictReader(io.StringIO(stdout)))
    if [row['phase'] for row in rows] != list(PHASE_FRAMES):
        raise ValueError('Demo phase sequence differs from the predeclared five phases')
    result = []
    for row in rows:
        if row['scene'] != 'demo' or int(row['trial']) != 0 or int(row['frames']) != PHASE_FRAMES[row['phase']]:
            raise ValueError('Demo scene/trial/frame count mismatch')
        parsed = {**row, 'trial': 0, 'frames': int(row['frames'])}
        for key in ['draw_us', 'flush_us', 'total_us']:
            parsed[key] = float(row[key])
            if not math.isfinite(parsed[key]) or parsed[key] < 0:
                raise ValueError('Nonfinite or negative timing value')
        if abs(parsed['draw_us'] + parsed['flush_us'] - parsed['total_us']) > 0.00001:
            raise ValueError('Draw/flush/total arithmetic mismatch')
        result.append(parsed)
    totals = {key: sum(row[key] * row['frames'] for row in result) for key in ['draw_us', 'flush_us', 'total_us']}
    return result, totals


def summarize(records, plan):
    summary = []
    blocks = plan['logical_blocks']
    rng = random.Random(plan['statistics']['bootstrap_seed'])
    indices = [[rng.randrange(blocks) for _ in range(blocks)] for _ in range(plan['statistics']['bootstrap_resamples'])]
    for config in plan['configurations']:
        selected = [r for r in records if r['configuration_id'] == config['configuration_id']]
        for phase in [*PHASE_FRAMES, 'reported_sequence']:
            frames = sum(PHASE_FRAMES.values()) if phase == 'reported_sequence' else PHASE_FRAMES[phase]
            values = {}
            for variant in ['master', 'final']:
                values[variant] = {}
                for record in selected:
                    if record['variant'] != variant:
                        continue
                    value = record['reported_sequence_totals_us']['total_us'] if phase == 'reported_sequence' else next(row['total_us'] for row in record['metrics'] if row['phase'] == phase)
                    values[variant][record['block']] = value
                if set(values[variant]) != set(range(blocks)):
                    raise ValueError('Missing or duplicate paired blocks')
            ratios = [values['final'][b] / values['master'][b] for b in range(blocks)]
            deltas = [values['final'][b] - values['master'][b] for b in range(blocks)]
            boot_ratios = sorted(statistics.median(ratios[i] for i in sample) for sample in indices)
            boot_deltas = sorted(statistics.median(deltas[i] for i in sample) for sample in indices)
            lo, hi = 250, 9750
            row = {'configuration_id': config['configuration_id'], 'feature': config['feature'], 'font': config['font'], 'scene': 'demo', 'phase': phase,
                   'units': 'us/sequence' if phase == 'reported_sequence' else 'us/frame', 'frames': frames,
                   'master_median_us': statistics.median(values['master'].values()), 'final_median_us': statistics.median(values['final'].values()),
                   'median_paired_delta_us': statistics.median(deltas), 'paired_delta_ci95_us': [boot_deltas[lo], boot_deltas[hi]],
                   'median_paired_ratio': statistics.median(ratios), 'paired_ratio_ci95': [boot_ratios[lo], boot_ratios[hi]],
                   'paired_deltas_us': deltas, 'paired_ratios': ratios,
                   'master_values_us': [values['master'][b] for b in range(blocks)], 'final_values_us': [values['final'][b] for b in range(blocks)]}
            if phase == 'reported_sequence':
                row['median_paired_delta_us_per_reported_frame'] = row['median_paired_delta_us'] / frames
                row['paired_delta_ci95_us_per_reported_frame'] = [value / frames for value in row['paired_delta_ci95_us']]
            summary.append(row)
    return summary


def verify_prepared(plan):
    for file, expected in plan['prepared_files'].items():
        if sha(ROOT / file) != expected:
            raise ValueError(f'Prepared file changed: {file}')
    for record in plan['binaries'].values():
        if sha(record['binary_path']) != record['binary_sha256']:
            raise ValueError('Scene binary changed')
    for path, expected in plan['external_scene_assets'].items():
        if sha(path) != expected:
            raise ValueError(f'External fixed scene asset changed: {path}')
    emoji = plan['optional_host_emoji_font']
    if Path(emoji['path']).exists() != emoji['present']:
        raise ValueError('Optional emoji-font presence changed')
    if emoji['present'] and sha(emoji['path']) != emoji['sha256']:
        raise ValueError('Optional emoji-font bytes changed')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='demo-current')
    parser.add_argument('--timing-authorized', action='store_true')
    parser.add_argument('--code-ready', action='store_true', help='Root has verified the current source/build identity')
    args = parser.parse_args()
    if not args.timing_authorized:
        raise SystemExit('Latest user instruction authorizes a guarded current-demo measurement; pass --timing-authorized only under that instruction.')
    if not args.code_ready:
        raise SystemExit('Root source/build verification and code-ready GO are required.')
    plan = json.loads((ROOT / 'PLAN.json').read_text())
    if plan['authorization']['exact_user_instruction'] != AUTHORIZATION:
        raise SystemExit('Authorization record mismatch')
    verify_prepared(plan)
    out = ROOT / args.output
    if out.exists():
        raise SystemExit(f'Refusing to overwrite cohort {out}')
    out.mkdir()
    (out / 'PLAN.json').write_text(json.dumps(plan, indent=2) + '\n')
    for file in ['attempts.jsonl', 'raw.jsonl', 'excluded-raw.jsonl', 'ledger.jsonl', 'guard-checks.jsonl', 'interference-events.jsonl', 'quiet-intervals.jsonl']:
        (out / file).touch()
    (out / 'metadata.json').write_text(json.dumps({'started_utc': utc(), 'plan_sha256': sha(ROOT / 'PLAN.json'),
         'authorization': plan['authorization'], 'source_and_build_provenance': plan['source_and_build_provenance'],
         'metrics': plan['metrics'], 'statistics': plan['statistics'], 'policy': plan['policy'],
         'platform': subprocess.check_output(['sw_vers'], text=True)}, indent=2) + '\n')
    deadline = time.monotonic() + plan['policy']['max_duration_seconds']
    observations = []
    retries = attempt = attempts_count = excluded_count = 0
    active_attempt = None
    try:
        print('Waiting for 60 quiet seconds before current-demo timing.', flush=True)
        wait_idle(out, plan['policy']['quiet_seconds_before_start_or_replay'], deadline, {'reason': 'initial_start'})
        for schedule in plan['blocks']:
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError('Cohort deadline reached')
                attempt += 1
                block = schedule['logical_block']
                attempt_id = f'block-{block:02d}-attempt-{attempt:03d}'
                block_records = []
                active_attempt = {'block': block, 'attempt': attempt, 'attempt_id': attempt_id, 'started_utc': utc(), 'attempt_record_offset': attempts_count}
                guard_evidence = None
                fatal_error = None
                try:
                    for config in schedule['configurations']:
                        for variant in config['variant_order']:
                            context = {'block': block, 'attempt_id': attempt_id, 'configuration_id': config['configuration_id'], 'variant': variant}
                            before = ensure_idle(out, {'stage': 'before_process', **context})
                            label = f'{variant}-{config["feature"]}'
                            command = [plan['binaries'][label]['binary_path'], 'demo', '1', str(plan['dpi'])]
                            env = dict(os.environ, FEMTOVG_REPLAY_TEXT_FONT=str(ROOT / plan['fonts'][config['font']]['file']))
                            record = {'block': block, 'attempt': attempt, 'attempt_id': attempt_id, 'configuration_id': config['configuration_id'],
                                      'feature': config['feature'], 'font': config['font'], 'scene': 'demo', 'variant': variant, 'command': command,
                                      'selected_font_path': env['FEMTOVG_REPLAY_TEXT_FONT'], 'started_utc': utc(), 'guard_before': before,
                                      'guard_after': None, 'stdout': '', 'stderr': '', 'returncode': None, 'metrics': None, 'reported_sequence_totals_us': None}
                            try:
                                completed = subprocess.run(command, env=env, capture_output=True, text=True,
                                                           timeout=min(plan['policy']['process_timeout_seconds'], max(0.01, deadline - time.monotonic())))
                                record.update(stdout=completed.stdout, stderr=completed.stderr, returncode=completed.returncode)
                            except subprocess.TimeoutExpired as error:
                                record['stdout'] = error.stdout.decode(errors='replace') if isinstance(error.stdout, bytes) else error.stdout or ''
                                record['stderr'] = error.stderr.decode(errors='replace') if isinstance(error.stderr, bytes) else error.stderr or ''
                                record['process_error'] = 'timeout'
                                fatal_error = 'Benchmark process timeout'
                            except OSError as error:
                                record['process_error'] = type(error).__name__
                                fatal_error = f'Cannot launch benchmark: {error}'
                            record['ended_utc'] = utc()
                            try:
                                record['guard_after'] = ensure_idle(out, {'stage': 'after_process', **context})
                            except GuardMatched as error:
                                record['guard_after'] = error.evidence
                                guard_evidence = error.evidence
                            except Exception as error:
                                record['guard_after_error'] = type(error).__name__
                                fatal_error = str(error)
                            if record['returncode'] == 0:
                                try:
                                    record['metrics'], record['reported_sequence_totals_us'] = parse_output(record['stdout'])
                                except Exception as error:
                                    record['parse_error'] = str(error)
                                    fatal_error = f'Invalid benchmark output: {error}'
                            elif not fatal_error:
                                fatal_error = f'Benchmark returned {record["returncode"]}'
                            block_records.append(record)
                            append(out / 'attempts.jsonl', record)
                            attempts_count += 1
                            if fatal_error:
                                raise RuntimeError(fatal_error)
                            if guard_evidence:
                                raise GuardMatched(guard_evidence)
                except GuardMatched as error:
                    guard_evidence = error.evidence
                except BaseException:
                    for record in block_records:
                        append(out / 'excluded-raw.jsonl', record)
                    append(out / 'ledger.jsonl', {**active_attempt, 'ended_utc': utc(), 'status': 'failed', 'reason': 'process_or_guard_failure',
                           'process_records': len(block_records), 'excluded_raw_offset': excluded_count})
                    excluded_count += len(block_records)
                    active_attempt = None
                    raise
                if guard_evidence:
                    for record in block_records:
                        append(out / 'excluded-raw.jsonl', record)
                    append(out / 'ledger.jsonl', {**active_attempt, 'ended_utc': utc(), 'status': 'rejected', 'reason': 'environment_guard_match',
                           'guard_evidence': guard_evidence, 'process_records': len(block_records), 'excluded_raw_offset': excluded_count})
                    excluded_count += len(block_records)
                    active_attempt = None
                    retries += 1
                    if retries > plan['policy']['max_retries']:
                        raise RuntimeError('Environment retry limit reached')
                    print(f'Guard interrupted logical block {block + 1}; replaying its entire predetermined order after 60 quiet seconds.', flush=True)
                    wait_idle(out, plan['policy']['quiet_seconds_before_start_or_replay'], deadline, {'reason': 'whole_block_replay', 'block': block})
                    continue
                if len(block_records) != plan['expected_processes_per_accepted_block']:
                    raise RuntimeError('Incomplete logical block')
                for record in block_records:
                    append(out / 'raw.jsonl', record)
                append(out / 'ledger.jsonl', {**active_attempt, 'ended_utc': utc(), 'status': 'accepted', 'process_records': len(block_records),
                       'accepted_raw_offset': len(observations)})
                observations.extend(block_records)
                active_attempt = None
                print(f'Completed current-demo logical block {block + 1}/{plan["logical_blocks"]}.', flush=True)
                break
    except BaseException as error:
        (out / 'STOPPED.json').write_text(json.dumps({'ended_utc': utc(), 'status': 'incomplete', 'error_type': type(error).__name__,
              'reason': str(error), 'active_attempt': active_attempt, 'accepted_process_records': len(observations),
              'attempt_process_records': attempts_count, 'excluded_process_records': excluded_count}, indent=2) + '\n')
        raise
    summary = summarize(observations, plan)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    report = ['Fresh current master/final actual demo CPU comparison at DPI 2.', '',
              '| Features | Font | Phase | Units | Master | Final | Paired change [exploratory 95% interval] |',
              '|---|---|---|---|---:|---:|---:|']
    for row in summary:
        lo, hi = row['paired_delta_ci95_us']
        report.append(f'| {row["feature"]} | {row["font"]} | {row["phase"]} | {row["units"]} | {row["master_median_us"]:.3f} | {row["final_median_us"]:.3f} | {row["median_paired_delta_us"]:+.3f} [{lo:+.3f}, {hi:+.3f}] |')
    report.extend(['', 'Negative paired changes save CPU time. The complete reported sequence includes first paint, 30 warm, 12 zoom-in, 12 zoom-out and 10 pan frames (65 total). The 119 intervening warmup frames are excluded.',
                   'CPU scene drawing includes layout, other demo drawing and Canvas set_size; total adds Void flush. Font/image setup is excluded. No GPU, window, presentation or application-launch latency is measured.',
                   'Twelve independent rotating paired process blocks; each configuration has six AB and six BA orders. One trial per process. Median paired deltas/ratios; 10,000 whole-block percentile bootstrap resamples, fixed seed; exploratory intervals without multiplicity adjustment.',
                   f'Environment policy: {retries} whole-block retries; strict name guards before and after each process, 60 quiet seconds before start/replay; all attempted process output and guard evidence retained; no timing-value filtering.'])
    (out / 'REPORT.md').write_text('\n'.join(report) + '\n')
    (out / 'COMPLETE.json').write_text(json.dumps({'ended_utc': utc(), 'logical_blocks': plan['logical_blocks'], 'accepted_process_records': len(observations),
           'attempt_process_records': attempts_count, 'excluded_process_records': excluded_count, 'environment_retries': retries,
           'summary_rows': len(summary)}, indent=2) + '\n')
    print('\n'.join(report), flush=True)


if __name__ == '__main__':
    main()
