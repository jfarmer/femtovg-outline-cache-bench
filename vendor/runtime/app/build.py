#!/usr/bin/env python3
"""Verify existing app inputs, retain verified baselines, and build configured candidates.

Does not launch the app. --check-only is read-only. Normal builds temporarily use
an archived resolved Cargo.lock, restore it conditionally even on failure, and
reject any tracked application/source/dependency changes.
"""
from __future__ import annotations
import argparse
import datetime
import json
from pathlib import Path
import shutil
import subprocess
import sys
from baseline_build_helpers import app_inputs, command, digest, git, graph, write_json

HERE=Path(__file__).resolve().parent
OLD=Path('/private/tmp/alustin-font-outline-review/build')
APP=Path('/Users/jesse/github/alustin-gui-v2')
SOURCES=Path('/private/tmp/femtovg-miss-selection-v2-review/snapshots')
VARIANTS=tuple(json.loads((HERE/'experiment.json').read_text())['versions'])
CACHE_SOURCE='src/text/swash_rasterizer.rs'

def hashes(root):
    return {str(p.relative_to(root)):digest(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and p.relative_to(root)!=Path('Cargo.lock')}

def verify(app, previous, sources):
    old=json.loads((previous/'provenance.json').read_text())
    inputs=app_inputs(app)
    if inputs != old['app_tracked_inputs']:
        changed=sorted(k for k in set(inputs)|set(old['app_tracked_inputs']) if inputs.get(k)!=old['app_tracked_inputs'].get(k))
        raise ValueError(f'Application inputs differ from the archived master/current build: {changed}')
    if digest((app/'Cargo.lock').read_bytes())!=old['initial_app_lock_sha256']:
        raise ValueError('Current app Cargo.lock differs from the original archived/restored app lock')
    if git(app,'rev-parse','HEAD').decode().strip()!=old['app_commit']:
        raise ValueError('Application HEAD differs from archived build')
    diff=git(app,'diff','--binary','HEAD')
    if digest(diff)!=old['app_input_diff_sha256'] or diff!=(previous/'app-input.diff').read_bytes():
        raise ValueError('Application tracked diff differs from archived build')
    if command(['rustc','--version'],app).decode().strip()!=old['rustc'] or command(['cargo','--version'],app).decode().strip()!=old['cargo']:
        raise ValueError('Rust/Cargo toolchain differs from archived binaries')
    sources_map={variant:hashes(sources/variant) for variant in VARIANTS}
    for variant,old_label in [('master','master'),('current','patch')]:
        if sources_map[variant]!=old['builds'][old_label]['source_sha256']:
            raise ValueError(f'{variant} source snapshot differs from archived binary inputs')
        for name,sha in old['builds'][old_label]['binary_sha256'].items():
            if digest((previous/'bin'/old_label/name).read_bytes())!=sha:
                raise ValueError(f'Archived binary changed: {old_label}/{name}')
    archived_graph=json.loads((previous/'dependency-graph.json').read_text())
    for old_label in ['master','patch']:
        normalized,versions=graph(json.loads((previous/f'{old_label}-metadata.json').read_text()),app,previous/old_label)
        if normalized!=archived_graph:
            raise ValueError(f'Archived {old_label} metadata differs from archived normalized graph')
        if versions!={key:old['builds'][old_label][key] for key in ['swash','skrifa','femtovg_features']}:
            raise ValueError(f'Archived {old_label} metadata differs from recorded Swash/features')
    harness=previous/'bin/startup_bench'
    if digest(harness.read_bytes())!=old['builds']['master']['binary_sha256']['startup_bench']:
        raise ValueError('Shared startup_bench differs from archived master harness')
    lock=(previous/'resolved.Cargo.lock').read_bytes()
    if any(digest(lock)!=old['builds'][label]['resolved_lock_sha256'] for label in ['master','patch']):
        raise ValueError('Archived resolved Cargo.lock changed')
    for variant in VARIANTS[2:]:
        changed={k for k in set(sources_map[variant])|set(sources_map['current']) if sources_map[variant].get(k)!=sources_map['current'].get(k)}
        if not changed or not changed <= {'src/text/swash_rasterizer.rs','src/text.rs','src/lib.rs','src/text/font.rs'}:
            raise ValueError(f'{variant} changes unexpected files: {sorted(changed)}')
        if 'alustin_startup' in (sources/variant/CACHE_SOURCE).read_text():
            raise ValueError('Benchmark instrumentation in cache source')
    return old,inputs,diff,sources_map,lock

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=APP)
    parser.add_argument('--previous-build',type=Path,default=OLD)
    parser.add_argument('--sources',type=Path,default=SOURCES)
    parser.add_argument('--target-dir',type=Path,default=Path('/private/tmp/slint-wgpu-evidence/target'))
    parser.add_argument('--output',type=Path,default=HERE/'build')
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    app=args.root.resolve(strict=True); previous=args.previous_build.resolve(strict=True); sources=args.sources.resolve(strict=True)
    old,inputs,diff,source_maps,resolved_lock=verify(app,previous,sources)
    if args.check_only:
        print('Verified exact app tracked inputs, previous binaries/toolchain/lock, and pure variant sources; no build performed')
        return
    output=args.output.resolve();target=args.target_dir.resolve()
    if output.exists():parser.error('--output must be a new directory')
    output.mkdir(parents=True)
    original_lock=(app/'Cargo.lock').read_bytes();lock_path=app/'Cargo.lock';expected_lock=original_lock
    (output/'app-original.Cargo.lock').write_bytes(original_lock)
    (output/'resolved.Cargo.lock').write_bytes(resolved_lock)
    (output/'app-input.diff').write_bytes(diff)
    provenance={
      'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'app_commit':old['app_commit'],'app_branch':git(app,'branch','--show-current').decode().strip(),
      'app_tracked_inputs':inputs,'app_input_diff_sha256':digest(diff),
      'initial_app_lock_sha256':digest(original_lock),'resolved_lock_sha256':digest(resolved_lock),
      'build_helper_sha256':digest(Path(__file__).read_bytes()),
      'previous_build_provenance':{'path':str(previous/'provenance.json'),'sha256':digest((previous/'provenance.json').read_bytes())},
      'rustc':old['rustc'],'cargo':old['cargo'],'target_dir':str(target),
      'source_constraint':'Prototype changes restricted to Swash rasterizer and existing text/atlas routing; generated crate lock omitted, archived app lock governs resolution',
      'variants':{},'complete':False,
    }
    expected_graph=json.loads((previous/'dependency-graph.json').read_text())
    write_json(output/'dependency-graph.json',expected_graph)
    for variant,old_label in [('master','master'),('current','patch')]:
        destination=output/'bin'/variant;destination.mkdir(parents=True)
        binary=destination/'alustin-gui';shutil.copy2(previous/'bin'/old_label/'alustin-gui',binary)
        provenance['variants'][variant]={
          'label':variant,'base_ref':old['builds'][old_label]['commit'],'source_directory':str(sources/variant),
          'source_sha256':source_maps[variant],'source_map_sha256':digest(json.dumps(source_maps[variant],sort_keys=True).encode()),
          'binary':{'path':str(binary),'sha256':digest(binary.read_bytes()),'bytes':binary.stat().st_size},
          'reused_binary':True,'previous_label':old_label,
          'resolved_lock_sha256':digest(resolved_lock),'swash':old['builds'][old_label]['swash'],'skrifa':old['builds'][old_label]['skrifa'],
          'femtovg_features':old['builds'][old_label]['femtovg_features'],
        }
    (output/'bin').mkdir(exist_ok=True)
    shutil.copy2(previous/'bin/startup_bench',output/'bin/startup_bench')
    harness=output/'bin/startup_bench'
    provenance['harness']={'path':str(harness),'sha256':digest(harness.read_bytes()),'bytes':harness.stat().st_size}
    for variant in VARIANTS[2:]:
        frozen=output/'sources'/variant
        frozen.mkdir(parents=True)
        for relative in source_maps[variant]:
            destination=frozen/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(sources/variant/relative,destination)
        if hashes(frozen)!=source_maps[variant]:raise RuntimeError(f'{variant} changed while snapshotting')
    write_json(output/'provenance.json',provenance)
    try:
        if app_inputs(app)!=inputs or lock_path.read_bytes()!=original_lock:
            raise RuntimeError('Application inputs/lock changed before build transaction')
        lock_path.write_bytes(resolved_lock);expected_lock=resolved_lock
        for variant in VARIANTS[2:]:
            frozen=output/'sources'/variant
            if app_inputs(app)!=inputs or lock_path.read_bytes()!=expected_lock or hashes(frozen)!=source_maps[variant]:
                raise RuntimeError('Application or frozen source changed during build transaction')
            override=f'patch.crates-io.femtovg.path={json.dumps(str(frozen))}'
            metadata_command=['cargo','metadata','--offline','--locked','--format-version','1','--features','alustin-gui/femtovg-benchmark','--config',override]
            raw=command(metadata_command,app);(output/f'{variant}-metadata.json').write_bytes(raw)
            dependency_graph,versions=graph(json.loads(raw),app,frozen)
            if dependency_graph!=expected_graph:
                write_json(output/f'{variant}-dependency-graph.json',dependency_graph)
                raise RuntimeError(f'{variant} dependencies differ from archived master/current')
            if versions != {k:old['builds']['master'][k] for k in ['swash','skrifa','femtovg_features']}:
                raise RuntimeError('FemtoVG dependency versions/features changed')
            build_command=['cargo','build','--release','--locked','--offline','-p','alustin-gui','--features','femtovg-benchmark','--bin','alustin-gui','--config',override,'--target-dir',str(target)]
            record={'label':variant,'base_ref':old['builds']['patch']['commit'],'source_directory':str(frozen),
              'source_sha256':source_maps[variant],'source_map_sha256':digest(json.dumps(source_maps[variant],sort_keys=True).encode()),
              'resolved_lock_sha256':digest(resolved_lock),'reused_binary':False,
              'build_command':build_command,'metadata_command':metadata_command,**versions}
            provenance['variants'][variant]=record;write_json(output/'provenance.json',provenance)
            with (output/f'{variant}-build.log').open('wb') as log:
                subprocess.run(build_command,cwd=app,stdout=log,stderr=subprocess.STDOUT,check=True)
            if app_inputs(app)!=inputs or lock_path.read_bytes()!=expected_lock or hashes(frozen)!=source_maps[variant]:
                raise RuntimeError('Application or frozen source changed during build')
            destination=output/'bin'/variant;destination.mkdir(parents=True)
            binary=destination/'alustin-gui';shutil.copy2(target/'release/alustin-gui',binary)
            record['binary']={'path':str(binary),'sha256':digest(binary.read_bytes()),'bytes':binary.stat().st_size}
            write_json(output/'provenance.json',provenance)
    finally:
        current_lock=lock_path.read_bytes()
        if current_lock==expected_lock:
            if current_lock!=original_lock:lock_path.write_bytes(original_lock)
            provenance['app_lock_restored']=lock_path.read_bytes()==original_lock
        else:
            provenance['app_lock_restored']=False
            provenance['lock_restore_error']='Cargo.lock changed externally; refusing restoration'
            (output/'unexpected.Cargo.lock').write_bytes(current_lock)
        provenance['final_app_inputs_match']=app_inputs(app)==inputs
        write_json(output/'provenance.json',provenance)
        if not provenance['app_lock_restored']:raise RuntimeError('Cargo.lock restoration refused; see archived locks')
    if not provenance['final_app_inputs_match']:raise RuntimeError('App inputs changed during build')
    provenance['complete']=True;write_json(output/'provenance.json',provenance)
    print(f'Built prototypes and verified retained master/current; no windows launched: {output}')

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        print(f'Build failed: {error}',file=sys.stderr);sys.exit(1)
