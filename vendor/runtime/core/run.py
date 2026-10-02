#!/usr/bin/env python3
"""Run fresh, balanced multi-version offscreen blocks; never opens a window.

Every frame, trial, and validated process is retained. Pixels are collected in a
separate batch and excluded from timing summaries. No source is modified here.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
VERSIONS = tuple(json.loads((ROOT/'experiment.json').read_text())['versions'])
def williams(n):
    base=[0]
    for i in range(1,n):
        base.append((i+1)//2 if i%2 else n-i//2)
    rows=[tuple((x+k)%n for x in base) for k in range(n)]
    if n%2: rows += [tuple(reversed(row)) for row in rows]
    from collections import Counter
    positions=Counter((p,v) for row in rows for p,v in enumerate(row))
    carry=Counter((a,b) for row in rows for a,b in zip(row,row[1:]))
    assert len(set(positions.values()))==1 and len(set(carry.values()))==1
    assert len(carry)==n*(n-1)
    return tuple(rows)
ORDER = williams(len(VERSIONS))
ASSETS = Path('/Users/jesse/github/femtovg/examples/assets')
FONTS = {
    'stock': ASSETS/'RobotoFlex-VariableFont.ttf',
    'vollkorn': Path('/Users/jesse/github/alustin-gui-v2/crates/alustin-gui/assets/fonts/Vollkorn-Medium.ttf'),
    'ptsans': Path('/private/tmp/femtovg-open-font-search/candidate-agent/PTSans-Regular.ttf'),
    'liberation': Path('/private/tmp/femtovg-liberation-font-review/liberation-fonts-ttf-2.1.5/LiberationSerif-Regular.ttf'),
    'arial': Path('/System/Library/Fonts/Supplemental/Arial.ttf'),
}
PHASES = {
    'demo': {'first_paint': 1, 'warm': 30, 'zoom_in': 12, 'zoom_out': 12, 'pan': 10},
    'text': {'first_paint': 1, 'warm': 30, 'x_advance': 10, 'x_return': 10, 'y_advance': 10,
             'size_advance': 12, 'size_return': 12, 'reflow': 3},
    'font_variations': {'first_paint': 1, 'warm': 30, 'weight_advance': 6, 'weight_return': 6,
                        'slant_advance': 10, 'slant_return': 10},
    'grid_singleton': {'once': 1},
    'grid_two_phases': {'first': 1, 'second': 1},
    'grid_unique_sizes': {'sweep': 32},
    'grid_unique_variations': {'sweep': 32},
    'grid_pollution': {'hot_first': 1, 'hot_second': 1, 'pollution': 64, 'hot_return': 1},
}
CSV_FIELDS = ['scene', 'phase', 'trial', 'frames', 'draw_us', 'submit_us', 'complete_us', 'new_atlas_entries']
RESULT_FIELDS = ['backend', 'font', 'dpi', 'block', 'version', *CSV_FIELDS]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def info(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def tree_info(path):
    path = Path(path).resolve(strict=True)
    files = {str(p.relative_to(path)): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}
    return {'path': str(path), 'files': files,
            'tree_sha256': hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()}


def write_provenance(path, data):
    path.write_text(json.dumps(data, indent=2)+'\n')


def parse_rows(stdout, trials):
    reader = csv.DictReader(io.StringIO(stdout))
    if reader.fieldnames != CSV_FIELDS:
        raise ValueError(f'unexpected replay CSV header: {reader.fieldnames}')
    rows = list(reader)
    expected = {(trial, scene, phase) for trial in range(trials)
                for scene, phases in PHASES.items() for phase in phases}
    seen = set()
    for row in rows:
        key = (int(row['trial']), row['scene'], row['phase'])
        if key not in expected or key in seen:
            raise ValueError(f'unexpected/duplicate replay row: {key}')
        seen.add(key)
        if int(row['frames']) != PHASES[key[1]][key[2]]:
            raise ValueError(f'unexpected frame count: {key}')
        atlas = int(row['new_atlas_entries'])
        if atlas < 0:
            raise ValueError(f'negative atlas count: {key}')
        # Every controlled frame introduces exactly 94 new atlas keys. This
        # excludes hidden atlas hits and confirms the intended fixed request
        # counts, independently of the outline admission implementation.
        if row['scene'].startswith('grid_') and atlas != 94 * int(row['frames']):
            raise ValueError(f'controlled frame must introduce 94 atlas keys: {key}: {atlas}')
        times = [float(row[name]) for name in ('draw_us', 'submit_us', 'complete_us')]
        if any(not math.isfinite(x) or x < 0 for x in times) or times != sorted(times):
            raise ValueError(f'invalid cumulative timings: {key}: {times}')
    if seen != expected:
        raise ValueError(f'missing replay rows: {sorted(expected-seen)}')
    return rows


def validate_block(rows):
    keys = lambda data: {(r['scene'], r['phase'], int(r['trial'])):
                        (int(r['frames']), int(r['new_atlas_entries'])) for r in data}
    expected = keys(rows['master'])
    for version in VERSIONS:
        if keys(rows[version]) != expected:
            raise ValueError(f'master/{version} frame or atlas-entry counts differ')


def snapshots(master, alternate, font, dpi, version):
    expected = {f'{scene}-{phase}.rgba' for scene, phases in PHASES.items() for phase in phases}
    for path in (master, alternate):
        actual = {p.name for p in path.glob('*.rgba')}
        if actual != expected:
            raise ValueError(f'unexpected snapshot set for {font}/DPR{dpi}/{version}: {actual ^ expected}')
    comparisons = []
    for name in sorted(expected):
        width, height = (800, 700) if name.startswith('font_variations-') else (1000, 600)
        a, b = master/name, alternate/name
        if a.stat().st_size != width*height*4 or b.stat().st_size != width*height*4:
            raise ValueError(f'unexpected RGBA dimensions for {name}')
        comparisons.append({'font': font, 'dpi': dpi, 'version': version, 'snapshot': name,
                            'width': width, 'height': height, 'master': info(a), 'candidate': info(b),
                            'rgba_identical': a.read_bytes() == b.read_bytes()})
    return comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('cpu', 'gpu', 'pixels'))
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--blocks', type=int, default=12)
    parser.add_argument('--trials', type=int)
    parser.add_argument('--fonts', choices=tuple(FONTS), nargs='+', default=['stock', 'vollkorn', 'ptsans'])
    parser.add_argument('--dpis', choices=(1,2), type=int, nargs='+', default=[2])
    parser.add_argument('--binary', action='append', nargs=2, metavar=('VERSION','PATH'))
    parser.add_argument('--font-file', action='append', nargs=2, metavar=('NAME','PATH'))
    parser.add_argument('--build-provenance', type=Path)
    parser.add_argument('--gpu-backend', default='metal')
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    if args.blocks < 1 or args.timeout < 1 or (args.trials is not None and args.trials < 1):
        parser.error('blocks, trials, and timeout must be positive')
    if len(set(args.fonts)) != len(args.fonts) or len(set(args.dpis)) != len(args.dpis):
        parser.error('font and DPR factors must be unique')
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    run_directory = output/f'{args.mode}-runs'
    run_directory.mkdir(exist_ok=False)
    csv_path, provenance_path = output/f'{args.mode}-results.csv', output/f'{args.mode}-provenance.json'
    if csv_path.exists() or provenance_path.exists():
        raise ValueError('result/provenance output exists; choose a new output directory')
    binaries = {version: root/f'{version}-runner' for version in VERSIONS}
    for version, path in args.binary or []:
        if version not in binaries:
            parser.error(f'unknown version: {version}')
        binaries[version] = Path(path)
    binaries = {version: path.resolve(strict=True) for version,path in binaries.items()}
    if len(set(binaries.values())) != len(VERSIONS):
        parser.error('version executables must have distinct paths')
    fonts = dict(FONTS)
    for name, path in args.font_file or []:
        if name not in fonts:
            parser.error(f'unknown font: {name}')
        fonts[name] = Path(path)
    binary_info = {version: info(path) for version,path in binaries.items()}
    font_info = {name: info(fonts[name]) for name in args.fonts}
    controls = {name: info(ASSETS/file) for name,file in (
        ('roboto_variable','RobotoFlex-VariableFont.ttf'),('amiri_fallback','amiri-regular.ttf'),('icons','entypo.ttf'))}
    sources = {version: {'pure_snapshot': tree_info(root/'snapshots'/version),
                          'replay_source': tree_info(root/'replay-sources'/version)} for version in VERSIONS}
    runner = tree_info(root/'runner')
    build_path = args.build_provenance or root/'replay-build-provenance.json'
    build = info(build_path)
    build_data = json.loads(build_path.read_text())
    if not build_data.get('complete') or set(build_data.get('variants',{})) != set(VERSIONS):
        raise ValueError('build provenance must contain all completed variants')
    for version in VERSIONS:
        record=build_data['variants'][version]
        if not record.get('complete') or record['binary_sha256'] != binary_info[version]['sha256']:
            raise ValueError(f'build provenance does not verify executable: {version}')
        if record['pure_source_files'] != sources[version]['pure_snapshot']['files'] or record['timed_source_files'] != sources[version]['replay_source']['files']:
            raise ValueError(f'build provenance source files differ: {version}')
    if build_data['runner_source'] != tree_info(root/'runner/src')['files']:
        raise ValueError('runner drawing sources differ from completed build')
    if build_data['resolved_lock_sha256'] != sha(root/'runner/Cargo.lock'):
        raise ValueError('runner lock differs from completed build')
    if build_data.get('compiler'):
        from verify_ready import verify_replay
        verify_replay(root)
    snapshot_path=root/'snapshot-provenance.json'
    snapshot_provenance=info(snapshot_path) if snapshot_path.exists() else None
    source_descriptions={}
    if snapshot_provenance:
        source_descriptions={version:{key:value for key,value in record.items() if key!='source_files'}
            for version,record in json.loads(snapshot_path.read_text()).items()}
    env = dict(os.environ)
    for name in ('FEMTOVG_REPLAY_TEXT_FONT','SLINT_FONT_PATH','SLINT_DEFAULT_FONT','MTL_SHADER_CACHE_SIZE'):
        env.pop(name,None)
    env['FEMTOVG_REQUIRE_GPU'] = args.gpu_backend
    backend = 'gpu' if args.mode == 'pixels' else args.mode
    blocks = 1 if args.mode == 'pixels' else args.blocks
    trials = 1 if args.mode == 'pixels' else args.trials or (5 if backend == 'cpu' else 3)
    provenance = {
        'mode': args.mode, 'backend': backend, 'blocks': blocks, 'trials_per_process': trials,
        'versions': list(VERSIONS), 'fonts': args.fonts, 'dpis': args.dpis, 'phases': PHASES,
        'platform': platform.platform(), 'binaries': binary_info, 'font_files': font_info,
        'control_font_files': controls, 'sources': sources, 'runner_sources': runner,
        'build_provenance': build, 'snapshot_provenance':snapshot_provenance,
        'variant_source_descriptions':source_descriptions, 'driver': info(Path(__file__)),
        'fixed_environment': {'FEMTOVG_REQUIRE_GPU': args.gpu_backend},
        'order_method': 'Williams orders repeated; configuration rotates each block; each candidate pairs to the same master observation in that block',
        'scope': 'Existing 19 example phases unchanged, plus 9 controlled public-glyph-API phases; variation example and controlled variation grid always use Roboto',
        'controlled_request_counts': 'Each controlled frame contains 94 distinct glyph IDs and creates 94 distinct atlas keys; singleton/size/variation instances occur once, two-phase instances twice, pollution hot instance three times',
        'measurement': 'Within-process trials become process medians before block pairing; draw/submit/complete are cumulative microseconds/frame and are not additive',
        'retention': 'All validated process/trial timing rows in a completed batch; no timing-based exclusions or retries',
        'order': [], 'launches': [], 'pixel_comparisons': [], 'complete': False,
    }
    write_provenance(provenance_path,provenance)
    with csv_path.open('x',newline='') as stream:
        csv.DictWriter(stream,fieldnames=RESULT_FIELDS).writeheader()
    configurations = [(font,dpi) for dpi in args.dpis for font in args.fonts]
    pixel_paths = {}
    for block_index in range(blocks):
        offset = block_index % len(configurations)
        ordered = configurations[offset:] + configurations[:offset]
        block_order=[]
        provenance['order'].append(block_order)
        for configuration_index, (font,dpi) in enumerate(ordered):
            versions = [VERSIONS[index] for index in ORDER[(block_index+configurations.index((font,dpi))) % len(ORDER)]]
            block_rows={}
            for version in versions:
                label=f'{block_index+1:02}-{font}-dpi{dpi}-{version}'
                block_order.append(label)
                launch_env=dict(env)
                font_env={} if font=='stock' else {'FEMTOVG_REPLAY_TEXT_FONT':font_info[font]['path']}
                launch_env.update(font_env)
                command=[str(binaries[version]),backend,str(trials),str(dpi)]
                if args.mode=='pixels':
                    destination=run_directory/f'{font}-dpi{dpi}-{version}-pixels'
                    command.append(str(destination))
                    pixel_paths[font,dpi,version]=destination
                launch={'label':label,'block':block_index+1,'font':font,'dpi':dpi,'version':version,
                        'command':command,'environment':font_env,'validated':False,
                        'stdout':str(run_directory/f'{label}.stdout.csv'),
                        'stderr':str(run_directory/f'{label}.stderr.txt')}
                provenance['launches'].append(launch)
                write_provenance(provenance_path,provenance)
                with Path(launch['stdout']).open('w') as stdout, Path(launch['stderr']).open('w') as stderr:
                    completed=subprocess.run(command,cwd=root,env=launch_env,stdout=stdout,stderr=stderr,timeout=args.timeout)
                launch['exit_code']=completed.returncode
                write_provenance(provenance_path,provenance)
                if completed.returncode:
                    raise RuntimeError(f'{label} exited {completed.returncode}; raw files retained')
                if sha(binaries[version]) != binary_info[version]['sha256']:
                    raise ValueError(f'executable changed: {version}')
                rows=parse_rows(Path(launch['stdout']).read_text(),trials)
                block_rows[version]=rows
                launch.update(validated=True,rows=len(rows))
                with csv_path.open('a',newline='') as stream:
                    csv.DictWriter(stream,fieldnames=RESULT_FIELDS).writerows(
                        {'backend':backend,'font':font,'dpi':dpi,'block':block_index+1,'version':version,**row} for row in rows)
                write_provenance(provenance_path,provenance)
                print(f'{args.mode} block {block_index+1}/{blocks}, {font}, DPR{dpi}, {version}: {len(rows)} rows validated',flush=True)
            validate_block(block_rows)
            if args.mode=='pixels':
                for version in VERSIONS[1:]:
                    comparisons=snapshots(pixel_paths[font,dpi,'master'],pixel_paths[font,dpi,version],font,dpi,version)
                    provenance['pixel_comparisons'].extend(comparisons)
                    write_provenance(provenance_path,provenance)
                    if not all(row['rgba_identical'] for row in comparisons):
                        raise ValueError(f'RGBA parity failed: {font}/DPR{dpi}/{version}')
    if args.mode=='pixels' and 'stock' in args.fonts and len(args.fonts)>1:
        checks=[]
        control_names=[f'font_variations-{phase}.rgba' for phase in PHASES['font_variations']]+['grid_unique_variations-sweep.rgba']
        for dpi in args.dpis:
            for version in VERSIONS:
                for font in args.fonts:
                    if font=='stock':
                        continue
                    stock,alternate=pixel_paths['stock',dpi,version],pixel_paths[font,dpi,version]
                    checks.append({'font':font,'dpi':dpi,'version':version,
                        'roboto_controls_unchanged':all(sha(stock/name)==sha(alternate/name) for name in control_names),
                        'regular_first_paint_changed':{scene:sha(stock/f'{scene}-first_paint.rgba') != sha(alternate/f'{scene}-first_paint.rgba') for scene in ('demo','text')}})
        provenance['font_override_controls']=checks
        if not all(row['roboto_controls_unchanged'] and all(row['regular_first_paint_changed'].values()) for row in checks):
            raise ValueError('font override or unchanged Roboto control parity failed')
    final_sources={version:{'pure_snapshot':tree_info(root/'snapshots'/version),'replay_source':tree_info(root/'replay-sources'/version)} for version in VERSIONS}
    if final_sources != sources or tree_info(root/'runner') != runner:
        raise ValueError('runner or frozen source snapshots changed during measurement')
    if any(sha(fonts[name])!=font_info[name]['sha256'] for name in args.fonts):
        raise ValueError('font inputs changed during measurement')
    if sha(build_path)!=build['sha256'] or (snapshot_provenance and sha(snapshot_path)!=snapshot_provenance['sha256']):
        raise ValueError('build/snapshot provenance changed during measurement')
    provenance['complete']=True
    write_provenance(provenance_path,provenance)
    print(f'Completed {len(provenance["launches"])} processes; artifacts in {output}',flush=True)


if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(f'Replay failed: {error}',file=sys.stderr)
        sys.exit(1)
