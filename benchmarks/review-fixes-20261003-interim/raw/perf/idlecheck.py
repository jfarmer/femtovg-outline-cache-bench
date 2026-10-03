#!/usr/bin/env python3
"""Confirm a sustained quiet interval using names only before timing resumes."""
import argparse
import json
import time
from pathlib import Path
from run import ensure_idle

parser = argparse.ArgumentParser()
parser.add_argument('--seconds', type=int, default=45)
parser.add_argument('--report')
parser.add_argument('--wait', action='store_true', help='Reset the quiet interval while known build activity remains.')
parser.add_argument('--max-wait', type=int, default=600)
args = parser.parse_args()
report = None
if args.report:
    report = Path(__file__).resolve().parent / args.report
    report.mkdir(exist_ok=False)
started = start = time.monotonic()
active = False
last_pids = None
while time.monotonic() - start < args.seconds:
    if time.monotonic() - started > args.max_wait:
        raise SystemExit('Sustained idle interval not reached within the monitoring limit.')
    try:
        ensure_idle(report)
    except SystemExit:
        if not args.wait or report is None or not (report / 'ABORT.json').exists():
            raise
        record = json.loads((report / 'ABORT.json').read_text())
        if record['pids'] != last_pids:
            with (report / 'events.jsonl').open('a') as stream:
                stream.write(json.dumps(record) + '\n')
        last_pids = record['pids']
        start = time.monotonic()
        if not active:
            print('Build activity observed; waiting for the full quiet interval.', flush=True)
        active = True
    else:
        if active:
            print('Build names are idle; quiet interval started.', flush=True)
        active = False
    time.sleep(1)
print(f'Build process names stayed idle for {args.seconds} seconds.', flush=True)
