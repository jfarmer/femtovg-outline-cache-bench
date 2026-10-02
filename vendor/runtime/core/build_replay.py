#!/usr/bin/env python3
"""Build frozen cache variants with identical replay instrumentation."""
from pathlib import Path
import datetime, hashlib, json, shutil, subprocess, tomllib

ROOT = Path(__file__).resolve().parent
VARIANTS = tuple(json.loads((ROOT/'experiment.json').read_text())['versions'])
TARGET = Path('/private/tmp/femtovg-cache-bench/target')
PREVIOUS = Path('/private/tmp/femtovg-miss-review')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def files(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*')) if p.is_file()}

def normalized_command(command):
    command=list(command)
    for flag in ('--manifest-path','--target-dir'):
        if flag in command: command[command.index(flag)+1]='<'+flag[2:]+'>'
    return command

def dependency_graph(metadata):
    packages={p['id']:p for p in metadata['packages']}
    def identity(package_id):
        p=packages[package_id]
        origin=p['source']
        if origin is None:
            origin='<femtovg>' if p['name']=='femtovg' else '<runner>' if p['name']=='femtovg-example-outline-review' else str(Path(p['manifest_path']).resolve())
        return (p['name'],p['version'],origin)
    return sorted((identity(node['id']),tuple(sorted(node['features'])),
        tuple(sorted((d['name'],identity(d['pkg']),json.dumps(d['dep_kinds'],sort_keys=True)) for d in node['deps'])))
        for node in metadata['resolve']['nodes'])

def verify_baseline_reuse(previous, variant, record, provenance, metadata):
    """Verify code, drawing, graph, toolchain, lock and flags before binary reuse."""
    prior_path=previous/'replay-build-provenance.json'
    prior=json.loads(prior_path.read_text())
    def require(condition, message):
        if not condition: raise ValueError(f'Refusing {variant} binary reuse: {message}')
    require(prior.get('complete'), 'previous build incomplete')
    prior_record=prior['variants'][variant]
    require(prior_record.get('complete'), 'previous variant incomplete')
    require(prior['runner_source']==provenance['runner_source'], 'drawing sources changed')
    require(prior['resolved_lock_sha256']==provenance['initial_lock_sha256'], 'resolved lock changed')
    require(prior['compiler']==provenance['compiler'], 'Rust compiler changed')
    for field in ('pure_source_files','timed_source_files','manifest','swash','skrifa'):
        require(prior_record[field]==record[field], field+' changed')
    require(normalized_command(prior_record['build_command'])==normalized_command(record['build_command']), 'build flags changed')
    prior_metadata=json.loads((previous/(variant+'-replay-metadata.json')).read_text())
    require(dependency_graph(prior_metadata)==dependency_graph(metadata), 'resolved dependency/features graph changed')
    binary=previous/(variant+'-runner')
    require(prior_record['binary_sha256']==sha(binary), 'archived executable changed')
    return binary,prior_path

def main():
    runner = ROOT/'runner'
    manifest = runner/'Cargo.toml'
    before = manifest.read_text()
    assert '../replay-sources/current' in before
    lock = runner/'Cargo.lock'
    initial_lock = lock.read_bytes()
    (ROOT/'replay-build.initial.Cargo.lock').write_bytes(initial_lock)
    void_source = (ROOT/'instrumentation/void.rs').read_bytes()
    raw_void = (ROOT/'snapshots/master/src/renderer/void.rs').read_bytes()
    stripped = void_source
    for line in (b'        std::hint::black_box(images);\n', b'        std::hint::black_box(verts);\n',
                 b'        std::hint::black_box(&commands);\n', b'        std::hint::black_box(&data);\n'):
        assert stripped.count(line)==1
        stripped = stripped.replace(line,b'')
    assert stripped==raw_void
    provenance={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'variants':{}, 'target_dir':str(TARGET),'runner_source':files(runner/'src'),
        'initial_lock_sha256':sha(ROOT/'replay-build.initial.Cargo.lock'),
        'initial_manifest':before,'common_instrumentation':'Atlas entry count accessor and identical Void black_box barriers; no outline observer in timed binaries',
        'compiler':subprocess.check_output(['rustc','--version'],text=True).strip(),
        'builder_sha256':sha(__file__),'cargo':subprocess.check_output(['cargo','--version'],text=True).strip(),'baseline_reuse_policy':'Exact source/drawing/manifest, Rust compiler, flags, resolved lock and normalized dependency/features graph; refuse reuse if any archived input differs','complete':False}
    provenance_path=ROOT/'replay-build-provenance.json'
    def checkpoint(): provenance_path.write_text(json.dumps(provenance,indent=2)+'\n')
    checkpoint()
    expected_lock=initial_lock
    (ROOT/'replay-build.Cargo.lock').write_bytes(expected_lock)
    try:
        for variant in VARIANTS:
            pure=ROOT/'snapshots'/variant
            source=ROOT/'replay-sources'/variant
            frozen=json.loads((ROOT/'snapshot-provenance.json').read_text())
            if variant not in frozen or files(pure)!=frozen[variant]['source_files']:
                raise ValueError(f'{variant} pure snapshot differs from frozen source provenance')
            shutil.copytree(pure,source)
            assert (source/'src/renderer/void.rs').read_bytes()==raw_void
            (source/'src/renderer/void.rs').write_bytes(void_source)
            path=source/'src/lib.rs'
            code=path.read_text()
            marker='    pub fn set_size(&mut self, width: u32, height: u32, dpi: f32) {'
            assert code.count(marker)==1 and 'pub fn benchmark_atlas_entries' not in code
            method='    #[doc(hidden)]\n    /// Counts glyph-atlas entries for benchmark validation.\n    pub fn benchmark_atlas_entries(&self) -> usize { self.glyph_atlas.rendered_glyphs.borrow().len() }\n\n'
            position=code.index(marker)
            doc_start=code.rfind('\n\n',0,position)+2
            assert code[doc_start:position].lstrip().startswith('///')
            path.write_text(code[:doc_start]+method+code[doc_start:])
            text=before.replace('../replay-sources/current','../replay-sources/'+variant)
            manifest.write_text(text)
            # A direct Swash dependency was added to the replay, with no new package.
            metadata_cmd=['cargo','metadata','--offline','--format-version','1','--manifest-path',str(manifest)]
            if expected_lock is not None: metadata_cmd.append('--locked')
            metadata=subprocess.check_output(metadata_cmd)
            (ROOT/(variant+'-replay-metadata.json')).write_bytes(metadata)
            if expected_lock is None:
                expected_lock=lock.read_bytes()
                (ROOT/'replay-build.Cargo.lock').write_bytes(expected_lock)
                old=tomllib.loads(initial_lock.decode())['package']
                new=tomllib.loads(expected_lock.decode())['package']
                identities=lambda ps:sorted((p['name'],p['version'],p.get('source')) for p in ps)
                assert identities(old)==identities(new), 'Package versions changed'
            assert lock.read_bytes()==expected_lock
            packages=json.loads(metadata)['packages']
            assert len([p for p in packages if p['name']=='swash' and p['version']=='0.2.10'])==1
            command=['cargo','build','--release','--locked','--offline','--manifest-path',str(manifest),'--target-dir',str(TARGET)]
            record={'pure_source_files':files(pure),'timed_source_files':files(source),
                'metadata_command':metadata_cmd,'build_command':command,'manifest':text,
                'swash':[p['version'] for p in packages if p['name']=='swash'],
                'skrifa':[p['version'] for p in packages if p['name']=='skrifa']}
            provenance['variants'][variant]=record
            checkpoint()
            binary=ROOT/(variant+'-runner')
            if variant in ('master','current'):
                previous=PREVIOUS
                previous_binary,previous_provenance=verify_baseline_reuse(previous,variant,record,provenance,json.loads(metadata))
                shutil.copy2(previous_binary,binary)
                record.update(reused_binary=True,previous_build_provenance=str(previous_provenance),previous_build_provenance_sha256=sha(previous_provenance))
            else:
                with (ROOT/(variant+'-replay-build.log')).open('wb') as log:
                    subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
                shutil.copy2(TARGET/'release/femtovg-example-outline-review',binary)
            assert lock.read_bytes()==expected_lock
            record.update(binary=str(binary),binary_sha256=sha(binary),complete=True)
            checkpoint()
            print(variant+' replay built',flush=True)
        provenance['resolved_lock_sha256']=sha(lock)
        provenance['complete']=True
    finally:
        manifest.write_text(before)
        checkpoint()
    print('Replay binaries ready; all sources and dependency versions recorded.',flush=True)

if __name__=='__main__': main()
