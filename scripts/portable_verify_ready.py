"""Preflight for freshly rebuilt portable cohorts; historical reuse is forbidden."""
import hashlib,json,subprocess
from pathlib import Path

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def files(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(Path(root).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def require(condition,message):
    if not condition:raise ValueError(message)
def exact(root,expected):require(files(root)==expected,'Frozen inputs changed: '+str(root))
def compiler(data):
    require(subprocess.check_output(['rustc','--version'],text=True).strip()==data.get('compiler',data.get('rustc')),'Compiler changed since fresh build')
    require(subprocess.check_output(['cargo','--version'],text=True).strip()==data['cargo'],'Cargo changed since fresh build')
def preparation(root,data):
    path=root.parent/'prepare-provenance.json';prep=json.loads(path.read_text())
    require(prep['complete'] and sha(path)==data['prepared_provenance_sha256'],'Preparation provenance changed')
    require(data.get('historical_binary_reuse') is False,'Fresh build record required')
    for relative,expected in prep['prepared_files'].items():
        path=root.parent/relative
        require(path.is_file() and path.stat().st_size==expected['bytes'] and sha(path)==expected['sha256'],'Prepared runtime input changed: '+relative)
    return prep
def verify_replay(root):
    from build_replay import dependency_graph
    root=Path(root);data=json.loads((root/'replay-build-provenance.json').read_text());prep=preparation(root,data);versions=prep['versions']
    require(data['complete'] and set(data['variants'])==set(versions),'Incomplete replay cohort');compiler(data)
    exact(root/'runner/src',data['runner_source']);require(sha(root/'runner/Cargo.lock')==data['resolved_lock_sha256'],'Runner lock changed')
    require((root/'runner/Cargo.toml').read_text()==data['initial_manifest'],'Runner manifest changed')
    frozen=json.loads((root/'snapshot-provenance.json').read_text());graphs=[]
    for version in versions:
        record=data['variants'][version];require(record['complete'] and record['reused_binary'] is False,'Incomplete/reused replay binary')
        require(sha(record['binary'])==record['binary_sha256'],'Replay binary changed: '+version)
        exact(root/'snapshots'/version,record['pure_source_files']);exact(root/'replay-sources'/version,record['timed_source_files'])
        require(frozen[version]['source_files']==record['pure_source_files'],'Pure snapshot record changed: '+version)
        graphs.append(dependency_graph(json.loads((root/(version+'-replay-metadata.json')).read_text())))
    require(all(graph==graphs[0] for graph in graphs),'Replay dependency/features graphs differ')
    return {'complete':True,'variants':versions,'scope':'Fresh sources, binaries, preparation, toolchain, lock and dependency/features graphs verified'}
def verify_app(root):
    from baseline_build_helpers import app_inputs,git,graph,digest
    root=Path(root);data=json.loads((root/'build/provenance.json').read_text());prep=preparation(root,data);versions=prep['versions'];app=Path(prep['alustin_checkout'])
    require(data['complete'] and data['app_lock_restored'] and data['final_app_inputs_match'] and set(data['variants'])==set(versions),'Incomplete app cohort');compiler(data)
    require(app_inputs(app)==data['app_tracked_inputs'],'App tracked inputs changed');require(git(app,'rev-parse','HEAD').decode().strip()==data['app_commit'],'App HEAD changed')
    require(digest(git(app,'diff','--binary','HEAD'))==data['app_input_diff_sha256'],'App tracked diff changed')
    require(sha(app/'Cargo.lock')==data['initial_app_lock_sha256'],'App original lock changed');require(sha(root/'build/resolved.Cargo.lock')==data['resolved_lock_sha256'],'Resolved app lock changed')
    expected=json.loads((root/'build/dependency-graph.json').read_text())
    for version in versions:
        record=data['variants'][version];require(record['reused_binary'] is False,'Historical app binary reuse is forbidden')
        source=Path(record['source_directory']);exact(source,record['source_sha256'])
        require(digest(json.dumps(record['source_sha256'],sort_keys=True).encode())==record['source_map_sha256'],'Source map changed: '+version)
        binary=record['binary'];require(sha(binary['path'])==binary['sha256'] and Path(binary['path']).stat().st_size==binary['bytes'],'App binary changed: '+version)
        require(record['resolved_lock_sha256']==data['resolved_lock_sha256'],'Variant app lock differs: '+version)
        normalized,native=graph(json.loads((root/'build'/(version+'-metadata.json')).read_text()),app,source)
        require(normalized==expected and native=={key:record[key] for key in ('swash','skrifa','femtovg_features')},'App dependency/features graph differs: '+version)
    harness=data['harness'];require(sha(harness['path'])==harness['sha256'] and Path(harness['path']).stat().st_size==harness['bytes'],'Harness changed')
    return {'complete':True,'variants':versions,'scope':'Fresh app source/binaries, exact tracked inputs, locks, toolchain and dependency/features graph verified'}
