#!/usr/bin/env python3
"""Build every pinned variant afresh; no GUI and no historical binary reuse."""
import argparse,datetime,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
from benchlib import REPO,bundled_manifest,hashes,records,sha,write_json

def command(args,cwd=None):return subprocess.check_output(args,cwd=cwd)

def checkpoint(path,value):write_json(path,value)

def verify_prepared(runtime):
    bundled_manifest()
    prep=json.loads((runtime/'prepare-provenance.json').read_text())
    if not prep.get('complete') or prep['bundle_manifest_sha256']!=sha(REPO/'vendor/manifest.json'):raise ValueError('Prepared bundle differs from source manifest')
    # Verify each prepared input; build outputs are allowed only outside these trees.
    for relative,expected in prep['prepared_files'].items():
        path=runtime/relative
        if not path.is_file() or path.is_symlink() or path.stat().st_size!=expected['bytes'] or sha(path)!=expected['sha256']:raise ValueError(f'Prepared input changed: {relative}')
    return prep

def build_replay(runtime,prep,target=None):
    root=runtime/'core';runner=root/'runner';manifest=runner/'Cargo.toml';before=manifest.read_text();lock=runner/'Cargo.lock';locked=lock.read_bytes()
    target=Path(target or runtime/'target/replay').resolve();destination=root/'replay-build-provenance.json'
    if destination.exists() or (root/'replay-sources').exists():raise ValueError('Replay build outputs already exist; use a fresh prepared run')
    frozen=json.loads((root/'snapshot-provenance.json').read_text());void=(root/'instrumentation/void.rs').read_bytes();raw=(root/'snapshots/master/src/renderer/void.rs').read_bytes();stripped=void
    for line in (b'        std::hint::black_box(images);\n',b'        std::hint::black_box(verts);\n',b'        std::hint::black_box(&commands);\n',b'        std::hint::black_box(&data);\n'):
        if stripped.count(line)!=1:raise ValueError('Unexpected Void instrumentation')
        stripped=stripped.replace(line,b'')
    if stripped!=raw:raise ValueError('Unexpected renderer instrumentation changes')
    provenance={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'variants':{},'runner_source':hashes(runner/'src'),
        'initial_lock_sha256':sha(lock),'resolved_lock_sha256':sha(lock),'initial_manifest':before,'compiler':command(['rustc','--version']).decode().strip(),
        'cargo':command(['cargo','--version']).decode().strip(),'builder_sha256':sha(__file__),'target_dir':str(target),
        'prepared_provenance_sha256':sha(runtime/'prepare-provenance.json'),'historical_binary_reuse':False,'complete':False}
    checkpoint(destination,provenance)
    try:
        for variant in prep['versions']:
            pure=root/'snapshots'/variant;source=root/'replay-sources'/variant
            if hashes(pure)!=frozen[variant]['source_files']:raise ValueError(f'Frozen snapshot changed: {variant}')
            shutil.copytree(pure,source)
            if (source/'src/renderer/void.rs').read_bytes()!=raw:raise ValueError('Variant renderer differs before common instrumentation')
            (source/'src/renderer/void.rs').write_bytes(void)
            path=source/'src/lib.rs';code=path.read_text();marker='    pub fn set_size(&mut self, width: u32, height: u32, dpi: f32) {'
            if code.count(marker)!=1 or 'pub fn benchmark_atlas_entries' in code:raise ValueError('Unexpected atlas accessor marker')
            position=code.index(marker);doc_start=code.rfind('\n\n',0,position)+2
            if not code[doc_start:position].lstrip().startswith('///'):raise ValueError('Unexpected set_size documentation')
            method='    #[doc(hidden)]\n    /// Counts glyph-atlas entries for benchmark validation.\n    pub fn benchmark_atlas_entries(&self) -> usize { self.glyph_atlas.rendered_glyphs.borrow().len() }\n\n'
            path.write_text(code[:doc_start]+method+code[doc_start:])
            if before.count('../replay-sources/current')!=1:raise ValueError('Unexpected runner dependency marker')
            text=before.replace('../replay-sources/current','../replay-sources/'+variant);manifest.write_text(text)
            metadata_cmd=['cargo','metadata','--offline','--locked','--format-version','1','--manifest-path',str(manifest)]
            metadata=command(metadata_cmd);(root/(variant+'-replay-metadata.json')).write_bytes(metadata);packages=json.loads(metadata)['packages']
            if [p['version'] for p in packages if p['name']=='swash']!=['0.2.10']:raise ValueError('Unexpected Swash version')
            build_cmd=['cargo','build','--release','--locked','--offline','--manifest-path',str(manifest),'--target-dir',str(target)]
            record={'pure_source_files':hashes(pure),'timed_source_files':hashes(source),'metadata_command':metadata_cmd,'build_command':build_cmd,
                'manifest':text,'swash':[p['version'] for p in packages if p['name']=='swash'],'skrifa':[p['version'] for p in packages if p['name']=='skrifa'],
                'reused_binary':False,'complete':False}
            provenance['variants'][variant]=record;checkpoint(destination,provenance)
            with (root/(variant+'-replay-build.log')).open('wb') as log:subprocess.run(build_cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            if lock.read_bytes()!=locked:raise ValueError('Locked replay dependency resolution changed')
            binary=root/(variant+'-runner');shutil.copy2(target/'release/femtovg-example-outline-review',binary)
            record.update(binary=str(binary),binary_sha256=sha(binary),complete=True);checkpoint(destination,provenance)
        provenance['complete']=True
    finally:
        manifest.write_text(before);checkpoint(destination,provenance)

def build_app(runtime,prep,target=None):
    root=runtime/'app';app=prep['alustin_checkout']
    if not app:raise ValueError('Prepare with --alustin-checkout for an app build')
    app=Path(app).resolve(strict=True);inputs_root=runtime/'app-inputs';old=json.loads((inputs_root/'provenance.json').read_text())
    sys.path.insert(0,str(root));from baseline_build_helpers import app_inputs,git,graph,digest
    inputs=app_inputs(app);diff=git(app,'diff','--binary','HEAD');lock_path=app/'Cargo.lock';original_lock=lock_path.read_bytes()
    if inputs!=old['app_tracked_inputs'] or git(app,'rev-parse','HEAD').decode().strip()!=old['app_commit'] or diff!=(inputs_root/'app-input.diff').read_bytes():raise ValueError('Alustin tracked inputs/commit/diff differ from pinned application')
    if digest(original_lock)!=old['initial_app_lock_sha256']:raise ValueError('Alustin Cargo.lock differs from archived original input')
    locked=(inputs_root/'resolved.Cargo.lock').read_bytes();expected_graph=json.loads((inputs_root/'dependency-graph.json').read_text())
    target=Path(target or runtime/'target/app').resolve();output=root/'build'
    if output.exists():raise ValueError('App build outputs already exist; use a fresh prepared run')
    output.mkdir();(output/'resolved.Cargo.lock').write_bytes(locked);(output/'app-original.Cargo.lock').write_bytes(original_lock);(output/'app-input.diff').write_bytes(diff)
    write_json(output/'dependency-graph.json',expected_graph)
    provenance={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'app_commit':old['app_commit'],'app_tracked_inputs':inputs,
        'app_input_diff_sha256':digest(diff),'initial_app_lock_sha256':digest(original_lock),'resolved_lock_sha256':digest(locked),
        'rustc':command(['rustc','--version']).decode().strip(),'cargo':command(['cargo','--version']).decode().strip(),'target_dir':str(target),
        'build_helper_sha256':sha(__file__),'prepared_provenance_sha256':sha(runtime/'prepare-provenance.json'),'historical_binary_reuse':False,'variants':{},'complete':False}
    path=output/'provenance.json';checkpoint(path,provenance);expected_lock=original_lock
    try:
        lock_path.write_bytes(locked);expected_lock=locked
        for variant in prep['versions']:
            source=runtime/'core/snapshots'/variant;source_hashes=hashes(source)
            if app_inputs(app)!=inputs or lock_path.read_bytes()!=locked:raise ValueError('Alustin changed during build transaction')
            override='patch.crates-io.femtovg.path='+json.dumps(str(source))
            metadata_cmd=['cargo','metadata','--offline','--locked','--format-version','1','--features','alustin-gui/femtovg-benchmark','--config',override]
            raw=command(metadata_cmd,app);(output/(variant+'-metadata.json')).write_bytes(raw);normalized,versions=graph(json.loads(raw),app,source)
            if normalized!=expected_graph:raise ValueError('App dependency/features graph differs from archived inputs')
            build_cmd=['cargo','build','--release','--locked','--offline','-p','alustin-gui','--features','femtovg-benchmark','--bin','alustin-gui','--example','startup_bench','--config',override,'--target-dir',str(target)]
            record={'label':variant,'base_ref':prep['pins']['femtovg_master'] if variant=='master' else prep['pins']['femtovg_current'],
                'source_directory':str(source),'source_sha256':source_hashes,'source_map_sha256':digest(json.dumps(source_hashes,sort_keys=True).encode()),
                'reused_binary':False,'resolved_lock_sha256':digest(locked),'build_command':build_cmd,'metadata_command':metadata_cmd,**versions}
            provenance['variants'][variant]=record;checkpoint(path,provenance)
            with (output/(variant+'-build.log')).open('wb') as log:subprocess.run(build_cmd,cwd=app,stdout=log,stderr=subprocess.STDOUT,check=True)
            if app_inputs(app)!=inputs or lock_path.read_bytes()!=locked or hashes(source)!=source_hashes:raise ValueError('Pinned app/source/lock changed during build')
            destination=output/'bin'/variant;destination.mkdir(parents=True);binary=destination/'alustin-gui';shutil.copy2(target/'release/alustin-gui',binary)
            record['binary']={'path':str(binary),'sha256':sha(binary),'bytes':binary.stat().st_size}
            if variant==prep['versions'][0]:
                harness=output/'bin/startup_bench';shutil.copy2(target/'release/examples/startup_bench',harness)
                provenance['harness']={'path':str(harness),'sha256':sha(harness),'bytes':harness.stat().st_size}
            checkpoint(path,provenance)
    finally:
        if lock_path.read_bytes()==expected_lock:
            if expected_lock!=original_lock:lock_path.write_bytes(original_lock)
            provenance['app_lock_restored']=True
        else:provenance['app_lock_restored']=False;(output/'unexpected.Cargo.lock').write_bytes(lock_path.read_bytes())
        provenance['final_app_inputs_match']=app_inputs(app)==inputs;checkpoint(path,provenance)
    if not provenance['app_lock_restored'] or not provenance['final_app_inputs_match']:raise ValueError('App lock restoration/input validation failed')
    provenance['complete']=True;checkpoint(path,provenance)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('suite',choices=('replay','app','all'));parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--target-dir',type=Path,help='Cargo cache for one suite; fresh snapshots and resulting binaries are still recorded')
    parser.add_argument('--replay-target-dir',type=Path);parser.add_argument('--app-target-dir',type=Path)
    args=parser.parse_args();runtime=args.runtime.resolve(strict=True);prep=verify_prepared(runtime)
    if args.target_dir and (args.suite=='all' or args.replay_target_dir or args.app_target_dir):parser.error('--target-dir is for one suite; use separate target overrides for all')
    if args.suite in ('replay','all'):build_replay(runtime,prep,args.target_dir or args.replay_target_dir)
    if args.suite in ('app','all'):build_app(runtime,prep,args.target_dir or args.app_target_dir)
    print('All requested variants freshly built; no windows opened')

if __name__=='__main__':main()
