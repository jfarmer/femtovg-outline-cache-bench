#!/usr/bin/env python3
"""Prepare, build, run, or analyze the separate public-API budget stress control."""
import argparse
import csv
import hashlib
import io
import itertools
import json
import math
import platform
import random
import shutil
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSIONS = ('master', 'prior', 'updated45', 'final')
KEYS = (3300, 3440, 3600)
FIELDS = ['keys', 'trial', 'phase', 'groups', 'glyph_requests', 'draw_flush_us',
          'upload_count', 'upload_bytes', 'upload_digest', 'vertex_digest']
ORDERS = tuple(tuple(VERSIONS[(index + rotation) % 4] for index in (0, 1, 3, 2))
               for rotation in range(4))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def files(path):
    return {str(file.relative_to(path)): sha(file) for file in sorted(path.rglob('*'))
            if file.is_file() and not any(part in ('.git', 'target', '.serena') for part in file.relative_to(path).parts)}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + '\n')


def once(code, before, after):
    if code.count(before) != 1:
        raise ValueError(f'Expected one source marker: {before!r}')
    return code.replace(before, after)


MEASURED_LOCK_RECORD_SHA256 = "c8d48d1a7672ba18fe7bc4cd9fc55f512289e1092a995efc817fe59742bb7b87"


def measured_locks():
    path = HERE / 'measured-locks/provenance.json'
    if not path.is_file() or sha(path) != MEASURED_LOCK_RECORD_SHA256:
        raise ValueError('Measured lockfile provenance missing or changed')
    record = json.loads(path.read_text())
    if not record['complete'] or record['versions'] != list(VERSIONS):
        raise ValueError('Incomplete measured lockfiles')
    if set(record['locks']) != {'timing', 'audit'}:
        raise ValueError('Both measured build kinds required')
    for kind in ('timing', 'audit'):
        if set(record['locks'][kind]) != set(VERSIONS):
            raise ValueError('All four measured version lockfiles required')
        for version in VERSIONS:
            item = record['locks'][kind][version]
            lock = HERE / item['file']
            if not lock.is_file() or sha(lock) != item['sha256']:
                raise ValueError(f'Measured lockfile missing or changed: {kind}/{version}')
    return record


def prepare(args):
    locks = measured_locks()
    sources = {name: Path(path).resolve(strict=True) for name, path in args.source}
    if len(args.source) != 4 or set(sources) != set(VERSIONS):
        raise ValueError('Exactly master, prior, updated45, final source paths required')
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Prepared output must be fresh')
    output.mkdir(parents=True)
    provenance = {'complete': False, 'versions': list(VERSIONS), 'driver_sha256': sha(__file__),
                  'runner_sha256': sha(HERE / 'main.rs'), 'audit_tail_sha256': sha(HERE / 'audit_void_tail.rs'),
                  'sources': {}, 'variants': {},
                  'reproduction_only': True,
                  'measured_lock_record_sha256': MEASURED_LOCK_RECORD_SHA256}
    for version, source in sources.items():
        provenance['sources'][version] = {'path': str(source), 'files': files(source)}
    for kind in ('timing', 'audit'):
        provenance['variants'][kind] = {}
        for version in VERSIONS:
            source = sources[version]
            copied = output / kind / version / 'femtovg'
            shutil.copytree(source, copied, ignore=shutil.ignore_patterns('.git', 'target', '.serena'))
            if files(copied) != provenance['sources'][version]['files']:
                raise ValueError(f'Copy mismatch: {version}')
            void = copied / 'src/renderer/void.rs'
            original = void.read_text()
            render = ('    ) {\n        std::hint::black_box(images);\n'
                      '        std::hint::black_box(verts);\n        std::hint::black_box(&commands);\n')
            if kind == 'audit':
                render += '        benchmark_vertices(verts);\n'
            render += '    }\n\n    fn alloc_image'
            code = once(original, '    ) {\n    }\n\n    fn alloc_image', render)
            update = '        std::hint::black_box(&data);\n'
            if kind == 'audit':
                update += '        benchmark_image(&data);\n'
            code = once(code, '        data.check_update(&image.info, x, y)',
                        update + '        data.check_update(&image.info, x, y)')
            if kind == 'audit':
                code += (HERE / 'audit_void_tail.rs').read_text()
            void.write_text(code)
            instrumented_files = files(copied)
            changed = {name for name, digest in instrumented_files.items()
                       if digest != provenance['sources'][version]['files'].get(name)}
            if changed != {'src/renderer/void.rs'}:
                raise ValueError(f'Unexpected instrumentation: {changed}')
            wrapper = output / kind / version / 'wrapper'
            (wrapper / 'src').mkdir(parents=True)
            shutil.copy2(HERE / 'main.rs', wrapper / 'src/main.rs')
            package = f'femtovg-budget-{kind}-{version}'
            manifest = ('[package]\n' + f'name = "{package}"\n' +
                        'version = "0.0.0"\nedition = "2021"\n\n'
                        '[dependencies]\nfemtovg = { path = "../femtovg", features = ["swash"] }\n'
                        'swash = "=0.2.10"\n\n[features]\naudit = []\n\n'
                        '[profile.release]\ndebug = true\n')
            (wrapper / 'Cargo.toml').write_text(manifest)
            lock = locks['locks'][kind][version]
            shutil.copy2(HERE / lock['file'], wrapper / 'Cargo.lock')
            if sha(wrapper / 'Cargo.lock') != lock['sha256']:
                raise ValueError('Measured lockfile copy differs')
            provenance['variants'][kind][version] = {'source': str(copied), 'source_files': instrumented_files,
                'wrapper': str(wrapper), 'wrapper_files': files(wrapper), 'package': package,
                'measured_lockfile': {'input': lock['file'], 'sha256': lock['sha256']}}
    provenance['complete'] = True
    write(output / 'prepare.json', provenance)
    print(output)


def verify_prepared(root):
    locks = measured_locks()
    provenance = json.loads((root / 'prepare.json').read_text())
    if not provenance.get('reproduction_only') or provenance.get('measured_lock_record_sha256') != MEASURED_LOCK_RECORD_SHA256:
        raise ValueError('Preparation does not pin measured lockfiles')
    if not provenance['complete'] or provenance['versions'] != list(VERSIONS):
        raise ValueError('Incomplete preparation')
    for kind in ('timing', 'audit'):
        for version, record in provenance['variants'][kind].items():
            expected = locks['locks'][kind][version]
            if record['measured_lockfile'] != {'input': expected['file'], 'sha256': expected['sha256']}:
                raise ValueError('Prepared lockfile record changed')
            lock = Path(record['wrapper']) / 'Cargo.lock'
            if not lock.is_file() or sha(lock) != expected['sha256']:
                raise ValueError(f'Prepared measured lockfile missing or changed: {kind}/{version}')
            if files(Path(record['source'])) != record['source_files']:
                raise ValueError('Instrumented source changed')
            for name, digest in record['wrapper_files'].items():
                if sha(Path(record['wrapper']) / name) != digest:
                    raise ValueError('Runner/manifest changed')
    return provenance


def graph(metadata):
    packages = {package['id']: package for package in metadata['packages']}
    result = []
    for node in metadata['resolve']['nodes']:
        package = packages[node['id']]
        if package['name'].startswith('femtovg-budget-'):
            continue
        dependencies = []
        for edge in node['deps']:
            dependency = packages[edge['pkg']]
            kinds = sorted(json.dumps(kind, sort_keys=True) for kind in edge['dep_kinds'])
            dependencies.append((edge['name'], dependency['name'], dependency['version'],
                                 dependency.get('source') or '<femtovg-path>', kinds))
        result.append((package['name'], package['version'], package.get('source') or '<femtovg-path>',
                       sorted(node['features']), sorted(dependencies)))
    return sorted(result)


def build(args):
    root = args.root.resolve(strict=True)
    prep = verify_prepared(root)
    destination = root / f'{args.kind}-build.json'
    if destination.exists():
        raise ValueError('Build record already exists')
    provenance = {'complete': False, 'kind': args.kind, 'prepare_sha256': sha(root / 'prepare.json'),
                  'compiler': subprocess.check_output(['rustc', '--version'], text=True).strip(),
                  'cargo': subprocess.check_output(['cargo', '--version'], text=True).strip(), 'variants': {}}
    target = (args.target_dir or root / 'target' / args.kind).resolve()
    expected = None
    for version in VERSIONS:
        record = prep['variants'][args.kind][version]
        wrapper = Path(record['wrapper'])
        manifest = wrapper / 'Cargo.toml'
        commands = [['cargo', 'metadata', '--offline', '--locked', '--format-version', '1', '--manifest-path', str(manifest)],
                    ['cargo', 'build', '--release', '--offline', '--locked', '--manifest-path', str(manifest), '--target-dir', str(target)]]
        if args.kind == 'audit':
            commands[0] += ['--features', 'audit']
            commands[1] += ['--features', 'audit']
        result = {'commands': commands, 'complete': False}
        provenance['variants'][version] = result
        write(destination, provenance)
        with (root / f'{args.kind}-{version}-build.log').open('w') as log:
            raw = subprocess.check_output(commands[0], stderr=log)
            (root / f'{args.kind}-{version}-metadata.json').write_bytes(raw)
            normalized = graph(json.loads(raw))
            if expected is None:
                expected = normalized
            if normalized != expected:
                raise ValueError('Resolved dependency/features graph differs across variants')
            if [p['version'] for p in json.loads(raw)['packages'] if p['name'] == 'swash'] != ['0.2.10']:
                raise ValueError('Unexpected Swash version')
            subprocess.run(commands[1], stdout=log, stderr=subprocess.STDOUT, check=True)
        binary = root / 'bin' / args.kind / version
        binary.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target / 'release' / record['package'], binary)
        result.update(complete=True, binary=str(binary), binary_sha256=sha(binary),
                      lock_sha256=sha(wrapper / 'Cargo.lock'), graph=normalized)
        write(destination, provenance)
    verify_prepared(root)
    provenance['complete'] = True
    write(destination, provenance)
    print(destination)


def parse_rows(stdout, kind, trials):
    reader = csv.DictReader(io.StringIO(stdout))
    if reader.fieldnames != FIELDS:
        raise ValueError('Unexpected CSV header')
    rows = list(reader)
    expected = set(itertools.product(KEYS, range(trials), range(10)))
    indexed = {}
    for row in rows:
        key = tuple(int(row[name]) for name in ('keys', 'trial', 'phase'))
        if key not in expected or key in indexed:
            raise ValueError(f'Unexpected/duplicate row: {key}')
        if int(row['groups']) != math.ceil(key[0] / 94) or int(row['glyph_requests']) != key[0]:
            raise ValueError('Request accounting mismatch')
        if kind == 'timing':
            if not math.isfinite(float(row['draw_flush_us'])) or float(row['draw_flush_us']) <= 0:
                raise ValueError('Invalid timing')
            if any(row[field] for field in FIELDS[6:]):
                raise ValueError('Audit instrumentation in timing result')
        elif int(row['upload_count']) != key[0] or int(row['upload_bytes']) <= 0:
            raise ValueError('Every requested glyph must upload in a fresh atlas')
        indexed[key] = row
    if set(indexed) != expected:
        raise ValueError('Incomplete process')
    return rows


def run(args):
    root = args.root.resolve(strict=True)
    verify_prepared(root)
    build_path = root / f'{args.kind}-build.json'
    build = json.loads(build_path.read_text())
    if not build['complete'] or build['prepare_sha256'] != sha(root / 'prepare.json'):
        raise ValueError('Build incomplete or preparation changed')
    if args.blocks < 1 or args.trials < 1 or args.timeout < 1:
        raise ValueError('Blocks, trials, and timeout must be positive')
    if args.blocks % 4 != 0 and args.kind == 'timing':
        raise ValueError('Timing block count must complete Williams cycles')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    trials = args.trials if args.kind == 'timing' else 1
    blocks = args.blocks if args.kind == 'timing' else 1
    font = args.font.resolve(strict=True)
    provenance = {'complete': False, 'kind': args.kind, 'versions': list(VERSIONS), 'keys': list(KEYS),
        'blocks': blocks, 'trials': trials, 'font': {'path': str(font), 'sha256': sha(font)},
        'build': {'path': str(build_path), 'sha256': sha(build_path)}, 'driver_sha256': sha(__file__),
        'platform': platform.platform(), 'orders': [list(order) for order in ORDERS], 'launches': [],
        'scope': 'Public fill_glyph_run and flush; fresh Canvas/atlas per phase; shared TextContext per workload/trial. Context/font/Canvas creation and destruction excluded. Population included in complete10 totals. No outline hit counts inferred.',
        'retention': 'All completed processes and all trials retained; no duration exclusions or retries.'}
    write(output / 'provenance.json', provenance)
    with (output / 'results.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['block', 'version', *FIELDS])
        writer.writeheader()
        for block in range(1, blocks + 1):
            for version in ORDERS[(block - 1) % 4]:
                record = build['variants'][version]
                binary = Path(record['binary'])
                if sha(binary) != record['binary_sha256']:
                    raise ValueError('Executable changed')
                label = f'{block:02}-{version}'
                command = [str(binary), args.kind, str(font), str(trials)]
                launch = {'label': label, 'block': block, 'version': version, 'command': command,
                          'stdout': str(output / f'{label}.csv'), 'stderr': str(output / f'{label}.stderr'), 'complete': False}
                provenance['launches'].append(launch)
                write(output / 'provenance.json', provenance)
                with Path(launch['stdout']).open('w') as stdout, Path(launch['stderr']).open('w') as stderr:
                    subprocess.run(command, stdout=stdout, stderr=stderr, check=True, timeout=args.timeout)
                rows = parse_rows(Path(launch['stdout']).read_text(), args.kind, trials)
                if sha(binary) != record['binary_sha256']:
                    raise ValueError('Executable changed during process')
                writer.writerows({'block': block, 'version': version, **row} for row in rows)
                stream.flush()
                launch.update(complete=True, rows=len(rows), binary_sha256=sha(binary))
                write(output / 'provenance.json', provenance)
                print(f'{args.kind}: {label}, {len(rows)} rows', flush=True)
    if sha(font) != provenance['font']['sha256'] or sha(build_path) != provenance['build']['sha256']:
        raise ValueError('Input changed during run')
    verify_prepared(root)
    provenance['complete'] = True
    write(output / 'provenance.json', provenance)


def percentile(values, probability):
    values = sorted(values)
    position = probability * (len(values) - 1)
    lower, upper = math.floor(position), math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def analyze(args):
    root = args.root.resolve(strict=True)
    provenance = json.loads((root / 'provenance.json').read_text())
    if not provenance['complete']:
        raise ValueError('Incomplete run')
    if args.bootstrap < 1:
        raise ValueError('Bootstrap count must be positive')
    rows = []
    for launch in provenance['launches']:
        if not launch['complete']:
            raise ValueError('Incomplete process')
        rows.extend({'block': str(launch['block']), 'version': launch['version'], **row}
                    for row in parse_rows(Path(launch['stdout']).read_text(), provenance['kind'], provenance['trials']))
    if rows != list(csv.DictReader((root / 'results.csv').open())):
        raise ValueError('Aggregate differs from raw observations')
    if provenance['kind'] == 'audit':
        indexed = {(int(row['keys']), int(row['phase']), row['version']): row for row in rows}
        checks = []
        for keys in KEYS:
            for phase in range(10):
                reference = indexed[keys, phase, 'master']
                for version in VERSIONS[1:]:
                    fields = FIELDS[6:]
                    equal = all(indexed[keys, phase, version][field] == reference[field] for field in fields)
                    checks.append({'keys': keys, 'phase': phase, 'candidate': version, 'upload_mask_and_vertices_match_master': equal})
        write(root / 'audit.json', {'complete': all(row['upload_mask_and_vertices_match_master'] for row in checks),
              'checks': checks, 'scope': 'Untimed padded upload and vertex FNV64 digests plus upload counts/bytes; not GPU RGBA or exact byte comparisons; no outline-cache hits inferred.'})
        if not all(row['upload_mask_and_vertices_match_master'] for row in checks):
            raise ValueError('Upload/vertex digest comparison differs')
        print(root / 'audit.json')
        return
    processes = {}
    for keys in KEYS:
        for scope, phases in [('population', [0]), ('reuse9', list(range(1, 10))), ('complete10', list(range(10)))]:
            for block in range(1, provenance['blocks'] + 1):
                for version in VERSIONS:
                    values = []
                    for trial in range(provenance['trials']):
                        selected = [row for row in rows if int(row['keys']) == keys and int(row['block']) == block
                                    and row['version'] == version and int(row['trial']) == trial and int(row['phase']) in phases]
                        if len(selected) != len(phases):
                            raise ValueError('Incomplete sequence')
                        values.append(sum(float(row['draw_flush_us']) for row in selected))
                    processes[keys, scope, block, version] = statistics.median(values)
    effects = []
    n = provenance['blocks']
    for keys in KEYS:
        for scope in ('population', 'reuse9', 'complete10'):
            generator = random.Random(20261002 + keys + sum(map(ord, scope)))
            indices = [[generator.randrange(n) for _ in range(n)] for _ in range(args.bootstrap)]
            for reference, candidate in itertools.combinations(VERSIONS, 2):
                a = [processes[keys, scope, block, reference] for block in range(1, n + 1)]
                b = [processes[keys, scope, block, candidate] for block in range(1, n + 1)]
                deltas = [right - left for left, right in zip(a, b)]
                changes = [100 * (right / left - 1) for left, right in zip(a, b)]
                boot = [statistics.median(changes[index] for index in sample) for sample in indices]
                effects.append({'keys': keys, 'scope': scope, 'reference': reference, 'candidate': candidate,
                    'reference_median_us': statistics.median(a), 'candidate_median_us': statistics.median(b),
                    'paired_delta_us': statistics.median(deltas), 'paired_change_pct': statistics.median(changes),
                    'paired_change_pct_ci95': [percentile(boot, .025), percentile(boot, .975)],
                    'process_blocks': n, 'trials_per_process': provenance['trials']})
    write(root / 'analysis.json', {'complete': True, 'effects': effects, 'bootstrap': args.bootstrap,
          'method': 'Sum phase durations within each trial before the process median, then pair versions in whole Williams blocks. Percentile whole-block bootstrap; all valid observations retained; exploratory intervals.'})
    print(root / 'analysis.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    sub = commands.add_parser('prepare')
    sub.add_argument('--source', action='append', nargs=2, metavar=('VERSION', 'PATH'), required=True)
    sub.add_argument('--output', type=Path, required=True)
    sub.set_defaults(function=prepare)
    sub = commands.add_parser('build')
    sub.add_argument('--root', type=Path, required=True)
    sub.add_argument('--kind', choices=('timing', 'audit'), required=True)
    sub.add_argument('--target-dir', type=Path)
    sub.set_defaults(function=build)
    sub = commands.add_parser('run')
    sub.add_argument('--root', type=Path, required=True)
    sub.add_argument('--kind', choices=('timing', 'audit'), required=True)
    sub.add_argument('--font', type=Path, required=True)
    sub.add_argument('--output', type=Path, required=True)
    sub.add_argument('--blocks', type=int, default=12)
    sub.add_argument('--trials', type=int, default=5)
    sub.add_argument('--timeout', type=int, default=240)
    sub.set_defaults(function=run)
    sub = commands.add_parser('analyze')
    sub.add_argument('--root', type=Path, required=True)
    sub.add_argument('--bootstrap', type=int, default=10000)
    sub.set_defaults(function=analyze)
    args = parser.parse_args()
    args.function(args)


if __name__ == '__main__':
    main()
