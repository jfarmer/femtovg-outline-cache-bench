"""Name-only build guard; inspect arguments only for already matched PIDs.

Adapted from the earlier study's run.py. Arguments and environment are never
printed or persisted. Cargo metadata/version probes remain guard matches.
"""
import datetime
import json
import shlex
import subprocess
import time
from pathlib import Path

BUILD_NAMES = r'cargo|rustc|clang|clang\+\+|ld|ld.lld|cc|cc1|swift|swiftc|swift-frontend|ninja|cmake'


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def append(path, record):
    with path.open('a') as stream:
        stream.write(json.dumps(record) + '\n')


class GuardMatched(Exception):
    def __init__(self, evidence):
        self.evidence = evidence
        super().__init__('Build/compiler/linker process-name guard matched')


def process_family(pid):
    names = subprocess.run(['ps', '-o', 'ppid=,comm=', '-p', pid], capture_output=True, text=True)
    fields = names.stdout.strip().split(maxsplit=1)
    if len(fields) != 2 or not fields[0].isdecimal():
        return {'pid': pid, 'comm': None, 'family': 'exited-before-inspection'}
    parent, comm = fields
    parent_comm = subprocess.run(['ps', '-o', 'comm=', '-p', parent], capture_output=True, text=True).stdout.strip()
    family = 'build/compiler/linker'
    if Path(comm).name in ['cargo', 'rustc']:
        inspected = subprocess.run(['ps', '-o', 'args=', '-p', pid], capture_output=True, text=True)
        try:
            tail = shlex.split(inspected.stdout)[1:]
        except ValueError:
            tail = []
        if any(word in ['-V', '-vV', '--version'] for word in tail):
            family = 'version'
        elif Path(comm).name == 'cargo':
            families = ['metadata', 'check', 'build', 'test', 'clippy', 'run', 'bench', 'rustc', 'rustdoc', 'fetch', 'fmt', 'locate-project', 'generate-lockfile']
            family = next((word for word in tail if word in families), 'unknown-cargo')
        else:
            family = 'compile'
    return {'pid': pid, 'comm': comm, 'family': family, 'parent_pid': parent, 'parent_comm': parent_comm}


def ensure_idle(out, context):
    checked_utc = utc()
    process = subprocess.run(['pgrep', '-x', BUILD_NAMES], capture_output=True, text=True)
    if process.returncode not in [0, 1]:
        record = {'checked_utc': checked_utc, 'status': 'guard_failed', 'context': context,
                  'returncode': process.returncode, 'stderr': process.stderr}
        append(out / 'guard-checks.jsonl', record)
        raise RuntimeError('Cannot check build process names; stopping')
    pids = [pid for pid in process.stdout.split() if pid.isdecimal()]
    record = {'checked_utc': checked_utc, 'status': 'matched' if pids else 'idle', 'context': context,
              'pids': pids, 'process_families_and_names_only': [process_family(pid) for pid in pids]}
    append(out / 'guard-checks.jsonl', record)
    if pids:
        append(out / 'interference-events.jsonl', record)
        raise GuardMatched(record)
    return record


def wait_idle(out, seconds, deadline, context):
    quiet_start = time.monotonic()
    started_utc = utc()
    while time.monotonic() - quiet_start < seconds:
        if time.monotonic() >= deadline:
            raise TimeoutError('Quiet interval not reached within the predeclared deadline')
        try:
            ensure_idle(out, {'stage': 'quiet_interval', **context})
        except GuardMatched:
            quiet_start = time.monotonic()
        time.sleep(1)
    append(out / 'quiet-intervals.jsonl', {'started_utc': started_utc, 'ended_utc': utc(),
           'required_quiet_seconds': seconds, 'context': context})
