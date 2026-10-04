"""Package completed review-fix evidence; publish only as a separate explicit step."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import shutil
import stat
import subprocess
import tarfile

STUDY = Path('/private/tmp/femtovg-feedback-20261004')
PAYLOAD = Path('/private/tmp/femtovg-feedback-publication')
REPO = Path('/Users/jesse/github/femtovg-outline-cache-bench')
DEST = 'benchmarks/review-fixes-20261004'
COMMITS = {'master': '9d574e076d3ce6006d9a21a01e3ae8a3bc649a57',
           'before': 'af989d9b617e9f424cb05974b057e4099592267a'}
SKIP = {'.git', '.serena', '__pycache__', 'target', 'bin'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def summary(bench, cohorts, commits):
    normal = json.loads((bench / f'runs/{cohorts["comparison"]}/SUMMARY.json').read_text())
    stress = json.loads((bench / f'runs/{cohorts["stress"]}/SUMMARY.json').read_text())
    rows = {(row['case'], row['phase']): row for row in normal + stress}
    lines = ['# Final cache review fixes', '',
             'This compares upstream Master `9d574e0`, the cache before these fixes',
             f'(`af989d9`), and the committed PR code (`{commits["after"][:7]}`). Earlier studies keep',
             'their original baselines and results; they are not pooled with this run.', '',
             'The cache remains behind the private Font API. Near its budget, arena',
             'growth now retains headroom instead of repeatedly reserving one outline.',
             'Variable-coordinate lookups borrow their key; coordinates are copied only',
             'when admitting an outline. Related atlas fixes preserve live layers and',
             'skip genuinely blank paths. Generic atlas target changes stay batched per',
             'run. See [scope and TDD evidence](REVIEW_FIXES.md) and the',
             '[public API review](API_REVIEW.md); no public API changed.', '',
             'CPU drawing time for the first frame of FemtoVG’s existing demo, in milliseconds:', '',
             '| Font | Master | Before fixes | PR |', '|---|---:|---:|---:|']

    def values(row):
        return ' | '.join(f'{row[variant] / 1000:.3f}' for variant in ('master', 'before', 'after'))

    for font in ('RobotoFlex', 'Vollkorn', 'Rye'):
        lines.append(f'| {font} | {values(rows[(f"demo-{font}", "first_paint")])} |')
    lines.append(f'| RobotoFlex, Swash disabled | {values(rows[("demo-RobotoFlex-no-swash", "first_paint")])} |')
    lines += ['', 'RobotoFlex’s demo first frame shows no clear change; its paired interval',
              'crosses zero. The demo savings for Vollkorn and Rye remain substantial.',
              'The non-Swash control also has an interval crossing zero.']
    lines += ['', 'The same extreme Fleur de Leah scene, in milliseconds:', '',
              '| Workload | Master | Before fixes | PR |', '|---|---:|---:|---:|']
    for phase, label in [('first_paint', 'First frame'), ('new_size', 'Mean frame while changing sizes'),
                         ('complete_sequence', 'Complete 44-frame sequence')]:
        lines.append(f'| {label} | {values(rows[("stress-FleurDeLeah", phase)])} |')
    lines += ['', 'The complete 32-size all-miss controls, in milliseconds:', '',
              '| Font | Master | Before fixes | PR |', '|---|---:|---:|---:|']
    for font in ('RobotoFlex', 'Vollkorn'):
        lines.append(f'| {font} | {values(rows[(f"grid_unique_sizes-{font}", "all_misses")])} |')
    roboto_miss = rows[('grid_unique_sizes-RobotoFlex', 'all_misses')]
    low, high = roboto_miss['after_vs_master_ci95']
    lines += ['', f'When every request misses, RobotoFlex takes {roboto_miss["after_vs_master_percent"]:.2f}% more CPU time',
              f'than Master (exploratory paired 95% interval: +{low:.2f}% to +{high:.2f}%).',
              'Vollkorn’s all-miss interval crosses zero. This is not a universal speedup.']
    lines += ['', 'These are CPU measurements with the Void renderer. They exclude application',
              'startup, font loading and GPU work. The demo has warm, pan and zoom phases',
              'in the [full report](REPORT.md), including a non-Swash control. The',
              '[stress report](STRESS-REPORT.md) retains all phases. Six balanced blocks',
              'per cohort cover all three-version orders. Paired intervals in the JSON',
              'reports are exploratory; the controls do not prove universal equivalence.', '',
              'The [separate allocation probe](PROBE-REPORT.md) exercises nonempty',
              'variation coordinates and near-budget workloads. It counts allocator',
              'calls and observed capacity changes, including shrink. Output images',
              'still allocate, and a capacity change does not prove memory physically moved.',
              'Its instrumented timings are not application-speed claims.', '',
              'Exact sources, locked dependencies, unchanged scenes, fonts/licenses,',
              'scripts, guards, raw accepted and excluded attempts, test evidence and',
              '[independent audit](AUDIT-REPORT.md) are retained. Compiled executables',
              'and target caches are omitted; their recorded identities remain available.',
              'No Alustin launch timing applies to this exact version. No FemtoVG PR',
              'has been created.']
    return '\n'.join(lines) + '\n'


def prepare(args):
    study, payload = args.study.resolve(), args.payload.resolve()
    if payload.exists():
        raise RuntimeError(f'Payload already exists: {payload}')
    bench = study / 'bench'
    if not args.after_commit or len(args.after_commit) != 40 or any(c not in '0123456789abcdef' for c in args.after_commit):
        raise RuntimeError('Provide the final full --after-commit SHA, after the batching correction')
    commits = {**COMMITS, 'after': args.after_commit}
    cohorts = {'comparison': args.comparison, 'stress': args.stress, 'probe': args.probe}
    comparison, stress, probe = [f'runs/{cohorts[key]}' for key in ('comparison', 'stress', 'probe')]
    required = ['BUILD.json', 'SOURCE_FREEZE.json', 'REVIEW_FIXES.md', 'VALIDATION.json', 'API_REVIEW.md',
                f'{comparison}/SUMMARY.json', f'{comparison}/SUMMARY.csv',
                f'{comparison}/REPORT.md', f'{comparison}/AUDIT.json',
                f'{stress}/SUMMARY.json', f'{stress}/SUMMARY.csv',
                f'{stress}/REPORT.md', f'{stress}/AUDIT.json',
                f'{probe}/SUMMARY.json', 'PROBE-REPORT.md']
    for name in required:
        if not (bench / name).is_file():
            raise RuntimeError(f'Completed evidence missing: {name}')
    if not args.audit or not args.audit.is_file() or not args.audit_report or not args.audit_report.is_file():
        raise RuntimeError('Provide completed independent --audit and --audit-report files')
    for cohort in cohorts.values():
        output = bench / 'runs' / cohort
        plan = json.loads((output / 'PLAN.json').read_text())
        statuses = [json.loads(p.read_text()) for p in (output / 'attempts').glob('*/STATUS.json')]
        if sum(record['status'] == 'accepted' for record in statuses) != plan['blocks']:
            raise RuntimeError(f'Cohort incomplete: {cohort}')

    payload.mkdir(parents=True)
    copies = {'REPORT.md': f'{comparison}/REPORT.md', 'SUMMARY.json': f'{comparison}/SUMMARY.json',
              'SUMMARY.csv': f'{comparison}/SUMMARY.csv', 'STRESS-REPORT.md': f'{stress}/REPORT.md',
              'STRESS-SUMMARY.json': f'{stress}/SUMMARY.json',
              'STRESS-SUMMARY.csv': f'{stress}/SUMMARY.csv', 'PROBE-REPORT.md': 'PROBE-REPORT.md',
              'PROBE-SUMMARY.json': f'{probe}/SUMMARY.json', 'REVIEW_FIXES.md': 'REVIEW_FIXES.md',
              'API_REVIEW.md': 'API_REVIEW.md',
              'VALIDATION.json': 'VALIDATION.json', 'after-vs-before.diff': 'after-vs-before.diff',
              'after-vs-master.diff': 'after-vs-master.diff', 'SOURCE_FREEZE.json': 'SOURCE_FREEZE.json'}
    for dest, src in copies.items():
        shutil.copy2(bench / src, payload / dest)
    shutil.copy2(args.audit, payload / 'AUDIT.json')
    # The standalone report lives beside API_REVIEW.md. Its original bytes
    # and relative link remain unchanged inside the source snapshot archive.
    (payload / 'AUDIT-REPORT.md').write_text(
        args.audit_report.read_text().replace('](../bench/API_REVIEW.md)', '](API_REVIEW.md)'))
    shutil.copy2(__file__, payload / 'publication.py')
    shutil.copy2(args.repo / 'benchmarks/font-cache-adapter-20261004/verify.py', payload / 'verify.py')
    (payload / 'SUMMARY.md').write_text(summary(bench, cohorts, commits))
    (payload / 'README.md').write_text('''# Final cache review fixes

See [results](SUMMARY.md), [review scope and TDD evidence](REVIEW_FIXES.md),
the [public API review](API_REVIEW.md),
the [demo/miss report](REPORT.md), [stress report](STRESS-REPORT.md),
[allocation probe](PROBE-REPORT.md), and [independent audit](AUDIT-REPORT.md).

Master is upstream `9d574e0`; Before is `af989d9`; PR is committed `FINAL_SHA`.
The snapshot retains exact sources, scripts, locked dependencies, scenes,
fonts/licenses, provenance, guards, raw accepted/excluded attempts and tests.
Compiled executables and compiler caches are omitted; binary hashes remain
in build records and `OMITTED.json`.

Verify and extract with Python 3.12 or later:

```sh
python3 verify.py
python3 verify.py --extract /tmp/femtovg-review-fixes
```

With Rust/Cargo and cached dependencies, rebuild all variants and run fresh
measurements. These commands open no windows:

```sh
cd /tmp/femtovg-review-fixes/bench
python3 build.py
python3 run.py --out runs/new-comparison --blocks 6
python3 analyze.py --out runs/new-comparison
python3 run.py --out runs/new-stress --blocks 6 --cases stress-FleurDeLeah
python3 analyze.py --out runs/new-stress
python3 probe.py --out runs/new-probe --blocks 6
```

The guard must inspect process names; a failed inspection or compiler/build
overlap excludes the entire block and retains the attempt. The demo measures
CPU drawing; stress and miss workloads include Void flush. No GPU performance
or application startup is measured. The probe has counter overhead.

Measured builds/runs and their audits used the original isolated directory.
The package verifier checks retained bytes and archive extraction. A fresh build
from the relocated archive has not been tested; original absolute provenance
paths and binary identities are retained as captured. Rebuild before a fresh run.
'''.replace('FINAL_SHA', commits['after'][:7]))
    omitted = {'excluded_roots': ['bench/bin', 'target caches', '__pycache__'], 'binaries': []}
    entries = {}
    for path in sorted(study.rglob('*')):
        relative = path.relative_to(study)
        if not path.is_file():
            continue
        if 'bin' in relative.parts and '__pycache__' not in relative.parts:
            omitted['binaries'].append({'path': str(relative), 'original_path': str(path),
                                        'bytes': path.stat().st_size, 'sha256': digest(path.read_bytes())})
        if any(part in SKIP for part in relative.parts):
            continue
        if path.is_symlink():
            raise RuntimeError(f'Unexpected study symlink: {path}')
        entries[str(relative)] = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
    extra = Path('/private/tmp/femtovg-cow-key-review')
    for name in ('build-allocation-test.py', 'allocation-tests.rs', 'module-tests.rs',
                 'coordinate-red.log', 'coordinate-green.log', 'arena-red.log', 'module-green.log'):
        path = extra / name
        if path.exists():
            entries[f'evidence/coordinate-cow/{name}'] = (path.read_bytes(), 0o644)
    entries['review/AUDIT.json'] = (args.audit.read_bytes(), 0o644)
    entries['review/AUDIT-REPORT.md'] = (args.audit_report.read_bytes(), 0o644)
    entries['publication/package.py'] = (Path(__file__).read_bytes(), 0o644)
    entries['OMITTED.json'] = (encoded(omitted), 0o644)
    (payload / 'OMITTED.json').write_bytes(encoded(omitted))
    provenance = {'commits': commits, 'cohorts': cohorts, 'created_utc': datetime.now(timezone.utc).isoformat(),
                  'original_study': str(study), 'independent_audit': str(args.audit),
                  'pre_run_attempts': 'runs/comparison retains failed guard checks from the superseded a6eb669 freeze; it has no accepted timings and is not used in the final statistics.',
                  'reproduction_limit': 'Relocated fresh build not tested; rebuild binaries before new runs.'}
    entries['PUBLICATION.json'] = (encoded(provenance), 0o644)
    (payload / 'PUBLICATION.json').write_bytes(encoded(provenance))
    members, canonical = {}, {}
    archive = payload / 'snapshot.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name, (data, mode) in sorted(entries.items()):
            checksum = digest(data)
            members[name] = {'bytes': len(data), 'sha256': checksum}
            info = tarfile.TarInfo(name)
            info.mode = mode
            identity = (checksum, len(data))
            if identity in canonical:
                info.type, info.linkname = tarfile.LNKTYPE, canonical[identity]
                tar.addfile(info)
            else:
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
                canonical[identity] = name
    index = {'archive': archive.name, 'bytes': archive.stat().st_size,
             'sha256': digest(archive.read_bytes()), 'members': members}
    (payload / 'snapshot-index.json').write_bytes(encoded(index))
    subprocess.run(['python3', str(payload / 'verify.py')], check=True)
    print(f'Prepared {payload}: {len(members)} members, {archive.stat().st_size} archive bytes')


def publish(args):
    repo, payload = args.repo.resolve(), args.payload.resolve()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True).strip():
        raise RuntimeError('Benchmark repository must be clean before installing new evidence')
    destination = repo / DEST
    if destination.exists():
        raise RuntimeError(f'Immutable evidence destination already exists: {destination}')
    subprocess.run(['python3', str(payload / 'verify.py')], check=True)
    readme = repo / 'README.md'
    old = readme.read_text()
    first, remainder = old.split('\n', 1)
    final_commit = json.loads((payload / 'PUBLICATION.json').read_text())['commits']['after'][:7]
    update = ('\nThe [committed review-fix comparison](benchmarks/review-fixes-20261004/SUMMARY.md) '
              f'compares upstream Master `9d574e0`, the pre-fix cache, and PR code `{final_commit}`. '
              'It retains demo, miss and Fleur stress results, plus allocation/growth probes, '
              'exact sources, raw attempts, test evidence and an independent audit.\n')
    shutil.copytree(payload, destination)
    readme.write_text(first + '\n' + update + remainder)
    print(f'Installed {destination}; review and commit the benchmark repository separately.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'publish'))
    parser.add_argument('--study', type=Path, default=STUDY)
    parser.add_argument('--payload', type=Path, default=PAYLOAD)
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--audit', type=Path)
    parser.add_argument('--audit-report', type=Path)
    parser.add_argument('--after-commit')
    parser.add_argument('--comparison', default='comparison-final')
    parser.add_argument('--stress', default='stress-final')
    parser.add_argument('--probe', default='probe-final')
    arguments = parser.parse_args()
    (prepare if arguments.action == 'prepare' else publish)(arguments)
