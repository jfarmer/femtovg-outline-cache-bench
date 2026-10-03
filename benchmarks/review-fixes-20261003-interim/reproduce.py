#!/usr/bin/env python3
"""Build bundled frozen sources, then run in a separate fresh workspace."""
import argparse
import csv
import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

STUDY = Path(__file__).resolve().parent
FEATURES = ['swash_only', 'default_swash', 'default_no_swash']
COMPILERS = {'cargo', 'rustc', 'clang', 'clang++', 'ld', 'ld.lld', 'cc', 'cc1',
             'swift', 'swiftc', 'swift-frontend', 'ninja', 'cmake'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def idle():
    names = subprocess.check_output(['ps', '-A', '-o', 'comm='], text=True).splitlines()
    active = [name for name in names if Path(name.strip()).name in COMPILERS]
    if active:
        raise SystemExit(f'Build/compiler jobs active; no timings started: {active}')


def verify():
    count = 0
    for line in (STUDY / 'SHA256SUMS').read_text().splitlines():
        expected, relative = line.split('  ', 1)
        path = (STUDY / relative).resolve()
        if not path.is_relative_to(STUDY) or not path.is_file() or sha(path) != expected:
            raise SystemExit(f'Retained checksum mismatch: {relative}')
        count += 1
    print(f'Verified {count} retained files against SHA256SUMS.')


def copy_work(kind, work):
    source, target = STUDY / 'raw' / kind, work / kind
    if target.exists():
        raise SystemExit(f'Refusing to overwrite reproduction workspace: {target}')
    target.mkdir(parents=True)
    names = ['base', 'current'] if kind == 'containment' else ['source', 'harness', 'harness-src']
    if kind == 'scenes':
        names += ['assets']
    for name in names:
        shutil.copytree(source / name, target / name)
    if kind != 'containment':
        for manifest in (target / 'harness').glob('*/Cargo.toml'):
            variant = manifest.parent.name
            content = manifest.read_text()
            content, count = re.subn(r'(femtovg\s*=\s*\{\s*path\s*=\s*)"[^"]+"',
                                    lambda match: match[1] + f'"../../source/{variant}"', content)
            if count != 1:
                raise SystemExit(f'Expected exactly one FemtoVG path in {manifest}')
            manifest.write_text(content)
    return target


def build(args):
    work = args.work_dir.resolve()
    target = copy_work(args.group, work)
    logs, binaries = target / 'builds', target / 'bin'
    logs.mkdir()
    binaries.mkdir()
    environment = dict(os.environ, CARGO_TARGET_DIR=str(work / 'target'), CARGO_INCREMENTAL='0')
    variants = args.variants or (['base', 'current'] if args.group == 'containment'
                                else ['master', 'final'] if args.group == 'scenes'
                                else ['master', 'finalgenericrestore'])
    features = ['default', 'default_swash', 'swash_only'] if args.group == 'containment' else (
        FEATURES if args.group == 'perf' else ['default_swash', 'default_no_swash'])
    records = []
    for variant in variants:
        manifest = target / variant / 'Cargo.toml' if args.group == 'containment' else target / 'harness' / variant / 'Cargo.toml'
        if not manifest.with_name('Cargo.lock').exists():
            command = ['cargo', 'generate-lockfile', '--manifest-path', str(manifest)]
            if not args.online:
                command.append('--offline')
            subprocess.run(command, env=environment, check=True)
        for feature in features:
            label = f'{variant}-{feature}'
            command = ['cargo', 'test', '--no-run', '--lib'] if args.group == 'containment' else ['cargo', 'build', '--release']
            command += ['--locked', '--manifest-path', str(manifest), '--message-format=json']
            if not args.online:
                command.append('--offline')
            if feature == 'swash_only':
                command += ['--no-default-features', '--features', 'swash'] if args.group == 'containment' else ['--features', feature]
            elif feature != 'default':
                command += ['--features', 'swash' if args.group == 'containment' else feature]
            result = subprocess.run(command, env=environment, capture_output=True, text=True)
            (logs / f'{label}.stdout.jsonl').write_text(result.stdout)
            (logs / f'{label}.stderr').write_text(result.stderr)
            if result.returncode:
                raise SystemExit(f'Build failed for {label}; full logs in {logs}')
            artifacts = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
            expected_manifest = target / variant / 'Cargo.toml' if args.group == 'containment' else target / 'source' / variant / 'Cargo.toml'
            origins = [a for a in artifacts if a.get('reason') == 'compiler-artifact'
                       and a.get('target', {}).get('name') == 'femtovg']
            if not origins or any(Path(a['manifest_path']).resolve() != expected_manifest.resolve() for a in origins):
                raise SystemExit(f'Wrong FemtoVG build origin for {label}: {origins}')
            for artifact in artifacts:
                if artifact.get('reason') != 'compiler-artifact' or not artifact.get('executable'):
                    continue
                name = artifact['target']['name']
                kind = 'containment' if args.group == 'containment' else 'scenes' if args.group == 'scenes' else (
                    'warm' if name.startswith('probe-') else 'cold' if name.startswith('cold-') else 'generic')
                binary = binaries / f'{label}-{kind}'
                shutil.copy2(artifact['executable'], binary)
                records.append({'variant': variant, 'feature': feature, 'kind': kind,
                                'binary': str(binary), 'sha256': sha(binary), 'command': command,
                                'manifest_sha256': sha(manifest), 'lock_sha256': sha(manifest.with_name('Cargo.lock'))})
            metadata = ['cargo', 'metadata', '--locked', '--format-version', '1', '--manifest-path', str(manifest)]
            if not args.online:
                metadata.append('--offline')
            if args.group != 'containment':
                metadata += ['--features', feature]
            elif feature == 'swash_only':
                metadata += ['--no-default-features', '--features', 'swash']
            elif feature == 'default_swash':
                metadata += ['--features', 'swash']
            (logs / f'{label}.metadata.json').write_text(subprocess.check_output(metadata, env=environment, text=True))
    (target / 'builds.json').write_text(json.dumps({
        'records': records, 'rustc': subprocess.check_output(['rustc', '-Vv'], text=True),
        'cargo': subprocess.check_output(['cargo', '-V'], text=True), 'platform': platform.platform(),
        'harnesses': {p.name: sha(p) for p in (target / 'harness-src').glob('*.rs')} if args.group != 'containment' else None,
        'source_maps': {variant: {str(p.relative_to(target / 'source' / variant)): sha(p)
                                 for p in (target / 'source' / variant).rglob('*') if p.is_file()}
                        for variant in variants} if args.group != 'containment' else None,
        'cargo_path_relocation': 'Only FemtoVG dependency path changed to ../../source/<variant>; original manifests remain in raw/.',
    }, indent=2) + '\n')
    print(f'Build complete: {target}; run separately once all build jobs finish.')


def smoke(args):
    root = args.work_dir.resolve() / args.group
    records = json.loads((root / 'builds.json').read_text())['records']
    out = args.output.resolve()
    if out.exists():
        raise SystemExit(f'Refusing to overwrite smoke output: {out}')
    idle()
    out.mkdir(parents=True)
    font = STUDY / 'raw/perf/source/base/examples/assets/RobotoFlex-VariableFont.ttf'
    results = []
    for record in records:
        if sha(Path(record['binary'])) != record['sha256']:
            raise SystemExit(f'Changed binary: {record["binary"]}')
        kind = record['kind']
        if kind == 'containment':
            command = [record['binary'], '--exact', 'containment_review_probe::containment_probe', '--nocapture']
        elif kind == 'scenes':
            command = [record['binary'], 'text', '1', '1']
        else:
            workload = 'labels' if kind == 'warm' else 'cold_labels_natural' if kind == 'cold' else 'warm_labels_stroke_positive'
            command = [record['binary'], workload, str(font), '0', '3' if kind == 'warm' else '1']
        label = f'{record["variant"]}-{record["feature"]}-{kind}'
        environment = dict(os.environ, FEMTOVG_REPLAY_TEXT_FONT=str(font), PROBE_OUT=str(out / f'{label}.trace.txt'))
        completed = subprocess.run(command, env=environment, capture_output=True, text=True)
        (out / f'{label}.stdout').write_text(completed.stdout)
        (out / f'{label}.stderr').write_text(completed.stderr)
        results.append({'label': label, 'command': command, 'exit_code': completed.returncode,
                        'binary_sha256': record['sha256'], 'interpretation': 'Functional smoke only; printed timings are not performance evidence.'})
    (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    raise SystemExit(any(r['exit_code'] for r in results))


def fonts(args):
    font_root = Path(args.asset_dir).resolve() if args.asset_dir else STUDY / 'assets'
    roboto = STUDY / 'raw/perf/source/base/examples/assets/RobotoFlex-VariableFont.ttf'
    result = [('RobotoFlex', roboto, '1')]
    arial = args.arial or os.environ.get('FEMTOVG_ARIAL_FONT')
    if arial:
        result.insert(0, ('Arial', Path(arial).resolve(), '0'))
    if args.kind == 'cold':
        result += [('Vollkorn', font_root / 'Vollkorn-Medium.ttf', '0'),
                   ('PTSans', font_root / 'PTSans-Regular.ttf', '0')]
    return result


def run(args):
    group = 'containment' if args.kind == 'containment' else 'scenes' if args.kind == 'scenes' else 'perf'
    root = args.work_dir.resolve() / group
    build_record = json.loads((root / 'builds.json').read_text())
    records = [r for r in build_record['records'] if r['kind'] == args.kind]
    for record in records:
        if sha(Path(record['binary'])) != record['sha256']:
            raise SystemExit(f'Changed reproduction binary: {record["binary"]}')
    out = args.output.resolve()
    if out.exists():
        raise SystemExit(f'Refusing to overwrite results: {out}')
    idle()
    out.mkdir(parents=True)
    if args.kind == 'containment':
        results = []
        for record in records:
            trace = out / f'{record["feature"]}-{record["variant"]}.trace.txt'
            command = [record['binary'], '--exact', 'containment_review_probe::containment_probe', '--nocapture']
            completed = subprocess.run(command, env=dict(os.environ, PROBE_OUT=str(trace)), capture_output=True, text=True)
            (out / f'{record["feature"]}-{record["variant"]}.log').write_text(completed.stdout + completed.stderr)
            results.append({**record, 'command': command, 'exit_code': completed.returncode})
        (out / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        raise SystemExit(any(r['exit_code'] for r in results))
    selected_fonts = fonts(args)
    features = sorted({r['feature'] for r in records})
    variants = list(dict.fromkeys(r['variant'] for r in records))
    lookup = {(r['feature'], r['variant']): r for r in records}
    if args.kind == 'scenes':
        serif = (Path(args.asset_dir).resolve() if args.asset_dir else STUDY / 'assets') / 'Vollkorn-Medium.ttf'
        configs = [(f, scene, name, path, coords) for f in features
                   for scene, name, path, coords in [('demo', *selected_fonts[-1]), ('text', *selected_fonts[-1]), ('text', 'Vollkorn', serif, '0')]]
    elif args.kind == 'warm':
        configs = [(f, workload, *font) for f in features if f != 'default_no_swash'
                   for workload in ['labels', 'para'] for font in selected_fonts]
    elif args.kind == 'generic':
        chosen = selected_fonts[:1]
        configs = [(f, f'{temperature}_{layout}_{mode}_{position}', name, path, '0')
                   for f in features for temperature in ['warm', 'cold'] for layout in ['labels', 'para']
                   for mode in ['fill', 'stroke'] for position in ['positive', 'negative']
                   for name, path, _ in chosen if f == 'default_no_swash' or mode == 'stroke']
    else:
        workloads = [f'cold_{layout}_{phase}' for layout in ['labels', 'para'] for phase in ['natural', 'onephase']]
        workloads += ['grid_singleton', 'grid_two_phases', 'grid_unique_sizes', 'grid_pollution']
        configs = [(f, workload, *font) for f in features if f != 'default_no_swash' for workload in workloads for font in selected_fonts]
        configs += [(f, 'grid_unique_variations', *font) for f in features if f != 'default_no_swash'
                    for font in selected_fonts if font[0] == 'RobotoFlex']
    (out / 'metadata.json').write_text(json.dumps({
        'kind': args.kind, 'blocks': args.blocks, 'frames': args.frames, 'samples': args.samples,
        'build': build_record, 'platform': platform.platform(),
        'fonts': {name: {'path': str(path), 'sha256': sha(path)} for _, _, name, path, _ in configs},
        'arial': 'Explicit optional unbundled input; rows omitted/substituted when absent.',
        'order': 'Configuration rotation; variant rotation and reversal on odd independent process blocks.',
    }, indent=2) + '\n')
    observations = []
    for block in range(args.blocks):
        rotation = block % len(configs)
        for feature, workload, font, path, coords in configs[rotation:] + configs[:rotation]:
            idle()
            order = variants[block % len(variants):] + variants[:block % len(variants)]
            if block % 2:
                order.reverse()
            for variant in order:
                executable = lookup[feature, variant]['binary']
                count = args.frames if args.kind == 'warm' or (args.kind == 'generic' and workload.startswith('warm_')) else args.samples
                command = [executable, workload, '1', str(args.dpi)] if args.kind == 'scenes' else [executable, workload, str(path), coords, str(count)]
                environment = dict(os.environ, FEMTOVG_REPLAY_TEXT_FONT=str(path))
                completed = subprocess.run(command, env=environment, capture_output=True, text=True, check=True)
                if args.kind == 'scenes':
                    metrics = [{key: float(value) if key.endswith('_us') else value for key, value in row.items()}
                               for row in csv.DictReader(io.StringIO(completed.stdout))]
                else:
                    metrics = {line.split()[2]: float(line.split()[3]) for line in completed.stdout.splitlines() if line.startswith('RESULT ')}
                observation = {'block': block, 'feature': feature, 'workload': workload, 'font': font,
                               'variant': variant, 'command': command, 'stdout': completed.stdout,
                               'stderr': completed.stderr, 'metrics': metrics}
                observations.append(observation)
                with (out / 'raw.jsonl').open('a') as stream:
                    stream.write(json.dumps(observation) + '\n')
        print(f'Completed block {block + 1}/{args.blocks}', flush=True)
    print(f'Raw paired observations retained in {out}; summarize without changing historical raw/.')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('verify')
    b = sub.add_parser('build')
    b.add_argument('--group', choices=['perf', 'scenes', 'containment'], required=True)
    b.add_argument('--variants', nargs='+')
    b.add_argument('--online', action='store_true', help='Allow dependency downloads; default offline.')
    r = sub.add_parser('run')
    r.add_argument('--kind', choices=['warm', 'cold', 'generic', 'scenes', 'containment'], required=True)
    r.add_argument('--output', type=Path, required=True)
    r.add_argument('--blocks', type=int, default=12)
    r.add_argument('--frames', type=int, default=3000)
    r.add_argument('--samples', type=int, default=7)
    r.add_argument('--dpi', type=float, default=1.0)
    r.add_argument('--arial', help='Optional separately licensed Arial path; or FEMTOVG_ARIAL_FONT.')
    r.add_argument('--asset-dir', help='Override Vollkorn/PTSans asset directory.')
    s = sub.add_parser('smoke')
    s.add_argument('--group', choices=['perf', 'scenes', 'containment'], required=True)
    s.add_argument('--output', type=Path, required=True)
    for command in [b, r, s]:
        command.add_argument('--work-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'build':
        build(args)
    elif args.action == 'verify':
        verify()
    elif args.action == 'smoke':
        smoke(args)
    else:
        run(args)


if __name__ == '__main__':
    main()
