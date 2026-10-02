#!/usr/bin/env python3
"""Read-only guards for the freshly completed four-version selection campaign."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,datetime

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def files(root):return {str(p.relative_to(root)):sha(p) for p in sorted(Path(root).rglob('*')) if p.is_file()}
def require(ok,message):
 if not ok:raise ValueError(message)
def exact(root,expected):require(files(root)==expected,'Sources changed: '+str(root))
def compiler(data):
 require(subprocess.check_output(['rustc','--version'],text=True).strip()==data.get('compiler',data.get('rustc')),'Compiler changed')
 require(subprocess.check_output(['cargo','--version'],text=True).strip()==data['cargo'],'Cargo changed')
def verify_replay(root):
 from build_replay import dependency_graph,verify_baseline_reuse
 root=Path(root);d=json.loads((root/'replay-build-provenance.json').read_text());cfg=json.loads((root/'experiment.json').read_text());versions=cfg['versions']
 require(d['complete'] and set(d['variants'])==set(versions),'Incomplete replay variants');compiler(d)
 exact(root/'runner/src',d['runner_source']);require(sha(root/'runner/Cargo.lock')==d['resolved_lock_sha256'],'Runner lock changed')
 require((root/'runner/Cargo.toml').read_text()==d['initial_manifest'],'Runner manifest changed')
 frozen=json.loads((root/'snapshot-provenance.json').read_text());graphs=[]
 for v in versions:
  r=d['variants'][v];require(r['complete'] and sha(r['binary'])==r['binary_sha256'],'Replay binary changed: '+v)
  exact(root/'snapshots'/v,r['pure_source_files']);exact(root/'replay-sources'/v,r['timed_source_files']);require(frozen[v]['source_files']==r['pure_source_files'],'Snapshot record changed: '+v)
  metadata=json.loads((root/(v+'-replay-metadata.json')).read_text());graphs.append(dependency_graph(metadata))
  if r.get('reused_binary'):
   old=Path(r['previous_build_provenance']);require(sha(old)==r['previous_build_provenance_sha256'],'Archived replay provenance changed')
   verify_baseline_reuse(old.parent,v,r,{'runner_source':d['runner_source'],'initial_lock_sha256':d['resolved_lock_sha256'],'compiler':d['compiler']},metadata)
 require(all(g==graphs[0] for g in graphs),'Replay dependency graphs/features differ')
 return {'complete':True,'scope':'Four completed replay variants; sources/binaries/runner/lock/toolchain/graphs and exact baseline reuse verified','variants':versions}
def verify_app(root):
 from baseline_build_helpers import app_inputs,git,graph,digest
 root=Path(root);d=json.loads((root/'build/provenance.json').read_text());versions=json.loads((root/'experiment.json').read_text())['versions'];app=Path('/Users/jesse/github/alustin-gui-v2')
 require(d['complete'] and d['app_lock_restored'] and d['final_app_inputs_match'] and set(d['variants'])==set(versions),'Incomplete app build');compiler(d)
 require(app_inputs(app)==d['app_tracked_inputs'],'App tracked inputs changed');require(git(app,'rev-parse','HEAD').decode().strip()==d['app_commit'],'App HEAD changed')
 require(digest(git(app,'diff','--binary','HEAD'))==d['app_input_diff_sha256'],'App tracked diff changed')
 require(sha(app/'Cargo.lock')==d['initial_app_lock_sha256'],'App lock changed');require(sha(root/'build/resolved.Cargo.lock')==d['resolved_lock_sha256'],'Archived resolved lock changed')
 old_path=Path(d['previous_build_provenance']['path']);require(sha(old_path)==d['previous_build_provenance']['sha256'],'Archived app baseline provenance changed');old=json.loads(old_path.read_text());expected=json.loads((root/'build/dependency-graph.json').read_text())
 for v in versions:
  r=d['variants'][v];exact(Path(r['source_directory']),r['source_sha256']);require(digest(json.dumps(r['source_sha256'],sort_keys=True).encode())==r['source_map_sha256'],'Source map changed: '+v)
  b=r['binary'];require(sha(b['path'])==b['sha256'] and Path(b['path']).stat().st_size==b['bytes'],'App binary changed: '+v)
  require(r['resolved_lock_sha256']==d['resolved_lock_sha256'],'Variant app lock differs: '+v)
  if r['reused_binary']:
   previous_label=r['previous_label'];o=old['builds'][previous_label];require(r['source_sha256']==o['source_sha256'],'Baseline source differs: '+v)
   require(sha(old_path.parent/'bin'/previous_label/'alustin-gui')==b['sha256'],'Archived baseline executable changed: '+v)
   metadata=json.loads((old_path.parent/(previous_label+'-metadata.json')).read_text());compiled=old_path.parent/previous_label
  else:metadata=json.loads((root/'build'/(v+'-metadata.json')).read_text());compiled=Path(r['source_directory'])
  normalized,native=graph(metadata,app,compiled);require(normalized==expected,'App dependency graph differs: '+v);require(native=={k:r[k] for k in ['swash','skrifa','femtovg_features']},'Native features/versions differ: '+v)
 h=d['harness'];require(sha(h['path'])==h['sha256'],'Shared harness changed')
 return {'complete':True,'scope':'Four app variants; exact HEAD/tracked inputs/diff/locks/toolchain/source/binary/harness/dependency guards verified; no app executed','variants':versions}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('replay','app'));p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();print(json.dumps((verify_replay if a.mode=='replay' else verify_app)(a.root),indent=2))
if __name__=='__main__':main()
