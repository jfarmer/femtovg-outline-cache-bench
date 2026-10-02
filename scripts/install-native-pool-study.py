#!/usr/bin/env python3
"""Stage and optionally install the completed arena/native-Outline comparison.

Run only after all serial benchmarks and independent audits finish. The default
stages a reviewable update outside the repository. --install also copies it to
the existing benchmark repository; no commit, publication, build or GUI occurs.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CORE = Path('/private/tmp/femtovg-outline-pool-review')
APP = Path('/private/tmp/alustin-outline-pool-review')
BUNDLE = Path('/private/tmp/femtovg-outline-pool-bundle')
REPO = Path('/Users/jesse/github/femtovg-outline-cache-bench')
CAMPAIGNS = [
    ('native-pool-examples', CORE, 'native-outline-comparison'),
    ('native-pool-alustin', APP, 'native-outline-comparison'),
    ('native-pool-source-bundle', BUNDLE, 'native-outline-reproduction'),
]
AUDITS = [
    {'suite':'replay','campaign':'native-pool-examples','results':'results','experiment':'runtime/core/experiment.json',
     'modes':['cpu','gpu'],'phase_summary':'analysis/phase/summary.csv','sequence_summary':'analysis/sequence/summary.csv'},
    {'suite':'app','campaign':'native-pool-alustin','batch':'cpu-12','analysis':'analysis','experiment':'experiment.json'},
]

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def write(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def load(path):
    return json.loads(Path(path).read_text())

def records(root):
    return {p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size}
        for p in sorted(Path(root).rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    loaded=importlib.util.module_from_spec(spec);spec.loader.exec_module(loaded)
    return loaded

def replace_once(code, old, new, label):
    if code.count(old)!=1:raise ValueError(f'Expected one adaptation marker in {label}: {old}')
    return code.replace(old,new)

def completed_inputs():
    required = [CORE/'results/cpu-provenance.json',CORE/'results/gpu-provenance.json',CORE/'results/pixels-provenance.json',
        APP/'cpu-12/summary.json',APP/'pixels/summary.json',CORE/'source-review.json',CORE/'probe/results.json',
        CORE/'independent-replay-statistics-audit.json',CORE/'independent-identity-pixel-audit.json',APP/'independent-app-statistics-audit.json']
    for path in required:
        if not load(path).get('complete'):raise ValueError(f'Completed measurement/audit required before archiving: {path}')
    for folder in (CORE/'analysis/phase',CORE/'analysis/sequence',APP/'analysis'):
        if not (folder/'summary.csv').is_file() or not (folder/'summary.json').is_file():
            raise ValueError(f'Completed statistics missing: {folder}')
    if sha(CORE/'runtime/app/experiment.json')!=sha(APP/'experiment.json'):
        raise ValueError('App campaign experiment differs from the exact runtime copy')
    return required

def adapted_scripts(repo, stage):
    names=('independent_audit_math.py','verify-results.py','archive-campaign.py','archive-study.py')
    original={name:(repo/'scripts'/name).read_text() for name in names}
    updated=dict(original)
    updated['independent_audit_math.py']=replace_once(updated['independent_audit_math.py'],
        "    if 'route' in versions and 'final' in versions:comparisons.append(('route','final'))\n",
        "    if 'route' in versions and 'final' in versions:comparisons.append(('route','final'))\n    if 'pool' in versions and 'final' in versions:comparisons.append(('final','pool'))\n",names[0])
    updated['independent_audit_math.py']=replace_once(updated['independent_audit_math.py'],
        "    if 'route' in versions and 'final' in versions:allowed.append(baseline+[('route','final')])\n",
        "    if 'route' in versions and 'final' in versions:allowed.append(baseline+[('route','final')])\n    if 'pool' in versions and 'final' in versions:allowed.append(baseline+[('final','pool')])\n",names[0])
    old="""    path=REPO/'analysis/report-inputs.json'
    if path.exists():
        inputs=json.loads(path.read_text())
        for relative,expected in inputs.items():
            safe_relative(relative)
            if not (REPO/relative).is_file() or sha(REPO/relative)!=expected:raise ValueError(f'Report input checksum differs: {relative}')
        checks['report_inputs']=len(inputs);checks['report_inputs_manifest_sha256']=sha(path)
"""
    new="""    for filename,prefix in (('report-inputs.json','report_inputs'),('native-pool-report-inputs.json','native_pool_report_inputs')):
        path=REPO/'analysis'/filename
        if path.exists():
            inputs=json.loads(path.read_text())
            for relative,expected in inputs.items():
                safe_relative(relative)
                if not (REPO/relative).is_file() or sha(REPO/relative)!=expected:raise ValueError(f'Report input checksum differs: {relative}')
            checks[prefix]=len(inputs);checks[prefix+'_manifest_sha256']=sha(path)
"""
    updated['verify-results.py']=replace_once(updated['verify-results.py'],old,new,names[1])
    updated['archive-campaign.py']=replace_once(updated['archive-campaign.py'],
        'PRUNE = {"target", "test-targets", "__pycache__", ".git", ".serena"}',
        'PRUNE = {"target", "test-target", "test-targets", "probe-target", "__pycache__", ".git", ".serena"}',names[2])
    marker='    ("portable-validation", "femtovg-outline-cache-bench/runs/portable-validation", "functional-validation"),\n'
    updated['archive-study.py']=replace_once(updated['archive-study.py'],marker,marker+
        '    ("native-pool-examples", "femtovg-outline-pool-review", "native-outline-comparison"),\n'
        '    ("native-pool-alustin", "alustin-outline-pool-review", "native-outline-comparison"),\n'
        '    ("native-pool-source-bundle", "femtovg-outline-pool-bundle", "native-outline-reproduction"),\n',names[3])
    for name,code in updated.items():
        ast.parse(code,filename=name)
        destination=stage/'scripts'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(code)
    math_helpers=module(stage/'scripts/independent_audit_math.py','native_install_math_guard')
    old_versions=['master','current','final','route'];new_versions=['master','current','final','pool']
    assert math_helpers.pairs(old_versions)[-1]==('route','final') and len(math_helpers.pairs(old_versions))==6
    assert math_helpers.pairs(new_versions)[-1]==('final','pool') and len(math_helpers.pairs(new_versions))==6
    assert len(math_helpers.declared_pairs(old_versions,math_helpers.baseline_pairs(old_versions)))==5
    assert len(math_helpers.declared_pairs(new_versions,math_helpers.pairs(new_versions)))==6
    return original

def stage_update(args):
    repo=args.repo.resolve(strict=True);stage=args.stage.resolve()
    if stage.exists() or stage.is_relative_to(repo) or any(stage.is_relative_to(source) for _,source,_ in CAMPAIGNS):
        raise ValueError('Stage must be fresh and outside repository/campaign roots')
    subprocess.run(['git','diff','--quiet'],cwd=repo,check=True)
    subprocess.run(['git','diff','--cached','--quiet'],cwd=repo,check=True)
    required=completed_inputs()
    index=load(repo/'results/index.json');copy_manifest=load(repo/'analysis/copy-manifest.json')
    if len(index['campaigns'])!=22 or len(index['analysis_audits'])!=4:
        raise ValueError('Expected unchanged original 22-campaign/four-audit repository; avoid duplicate or unexpected updates')
    labels={record['label'] for record in index['campaigns']}
    if labels&{label for label,_,_ in CAMPAIGNS}:raise ValueError('Native pool campaigns already indexed')
    sys.path.insert(0,str(repo/'scripts'));from benchlib import bundled_manifest
    bundle=bundled_manifest(repo)
    if sha(repo/'vendor/manifest.json')!=load(BUNDLE/'vendor/manifest.json')['comparison_origin']['manifest_sha256']:
        raise ValueError('Original source bundle changed since follow-up preparation')
    baseline_names=['REPORT.md','SUMMARY.md','README.md','results/index.json','analysis/copy-manifest.json',
        'analysis/report-inputs.json','vendor/manifest.json','scripts/independent_audit_math.py','scripts/verify-results.py',
        'scripts/archive-campaign.py','scripts/archive-study.py']
    baseline_hashes={name:sha(repo/name) for name in baseline_names}
    stage.mkdir(parents=True)
    adapted_scripts(repo,stage)
    # Retain exact adapted tools in the study before creating its archive.
    evidence=CORE/'repository-tools';evidence.mkdir(exist_ok=True)
    for source in sorted((stage/'scripts').glob('*.py')):shutil.copy2(source,evidence/source.name)
    write(evidence/'adaptation-provenance.json',{'complete':True,'repository':str(repo),'original_file_sha256':
        {name:checksum for name,checksum in baseline_hashes.items() if name.startswith('scripts/')},
        'adapted_files':{name:value for name,value in records(evidence).items() if name!='adaptation-provenance.json'},
        'policy':'Legacy archive/audit plans retained; add final/pool and singular compiler cache pruning'})
    # Render only after raw cohorts and independent audits have completed.
    command=[sys.executable,str(CORE/'native-pool-report.py')]
    if args.conclusion:command+=['--conclusion',str(args.conclusion.resolve(strict=True))]
    subprocess.run(command,check=True)
    for label,source,role in CAMPAIGNS:
        if (repo/'results'/label).exists():raise ValueError(f'New archive destination already exists: {label}')
        destination=stage/'results'/label
        subprocess.run([sys.executable,str(stage/'scripts/archive-campaign.py'),str(source),str(destination),'--label',label],check=True)
        archive=load(destination/'archive.json')
        index['campaigns'].append({'label':label,'path':'results/'+label,'original_root':archive['original_root'],'role':role,
            'complete':archive['complete'],'archive':archive['archive'],'files':len(archive['files']),'raw_bytes':archive['raw_bytes']})
    index['analysis_audits'].extend(AUDITS)
    copies=[]
    for source,destination in ((CORE/'analysis/phase','analysis/native-pool-examples'),
        (CORE/'analysis/sequence','analysis/native-pool-sequences'),(APP/'analysis','analysis/native-pool-alustin')):
        for file in sorted(source.rglob('*')):
            if file.is_file() and '__pycache__' not in file.parts:copies.append((file,Path(destination)/file.relative_to(source)))
    copies.extend((source,Path(destination)) for source,destination in [
        (CORE/'probe/results.json','analysis/native-pool-probe.json'),
        (CORE/'probe/summary.csv','analysis/native-pool-probe.csv'),
        (CORE/'probe/SUMMARY.md','docs/native-pool-probe.md'),
        (CORE/'source-review.json','analysis/native-pool-source-review.json'),
        (CORE/'candidate-proof.json','analysis/native-pool-candidate-proof.json'),
        (CORE/'independent-replay-statistics-audit.json','analysis/native-pool-replay-audit.json'),
        (CORE/'independent-identity-pixel-audit.json','analysis/native-pool-identity-pixel-audit.json'),
        (APP/'independent-app-statistics-audit.json','analysis/native-pool-app-audit.json'),
        (CORE/'native-pool-report.py','scripts/render-native-pool-report.py'),
        (CORE/'native-pool-reproduction.md','docs/native-pool-reproduction.md'),
        (Path(__file__),'scripts/install-native-pool-study.py'),
        (CORE/'NATIVE-OUTLINE-POOL.md','NATIVE-OUTLINE-POOL.md'),
        (CORE/'NATIVE-OUTLINE-POOL.inputs.json','analysis/native-pool-original-report-inputs.json')])
    for source,relative in copies:
        destination=stage/relative
        if (repo/relative).exists() or destination.exists():raise ValueError(f'Visible follow-up destination exists: {relative}')
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination)
        entry={'source':str(source.resolve()),'sha256':sha(source),'bytes':source.stat().st_size}
        if relative.as_posix() in copy_manifest:raise ValueError(f'Duplicate visible-copy record: {relative}')
        copy_manifest[relative.as_posix()]=entry
    native_report_inputs={relative.as_posix():sha(stage/relative) for _,relative in copies if relative.suffix in {'.csv','.json','.py','.md'}}
    write(stage/'analysis/native-pool-report-inputs.json',native_report_inputs)
    write(stage/'analysis/copy-manifest.json',copy_manifest)
    write(stage/'results/index.json',index)
    readme=(repo/'README.md').read_text()
    marker='## Verify the retained evidence offline\n'
    addition="""## Native Swash Outline pool follow-up

The [arena/native-object comparison](NATIVE-OUTLINE-POOL.md) adds fresh example
and Alustin measurements under a balanced order schedule, exact pixels, and
independent allocation/residency evidence. The original reports and 22 campaign archives
remain preserved. Three new archives retain this comparison and its isolated
portable source bundle; see [reproduction](docs/native-pool-reproduction.md).
The default verifier now includes the new audit plans in the full archive index.

"""
    readme=replace_once(readme,marker,addition+marker,'README.md')
    (stage/'README.md').write_text(readme)
    # Protect historical reports/source bundle and exact old index entries.
    old_index=load(repo/'results/index.json')
    assert index['campaigns'][:22]==old_index['campaigns'] and index['analysis_audits'][:4]==old_index['analysis_audits']
    staged=records(stage)
    proof={'schema':1,'complete':True,'repository':str(repo),'stage':str(stage),
        'source_inputs':{str(path):sha(path) for path in required},'old_repository_file_sha256':baseline_hashes,
        'old_campaigns':22,'old_audits':4,'new_campaigns':len(CAMPAIGNS),'new_audits':len(AUDITS),
        'bundled_original_files_verified':len(bundle['files']),'staged_files':staged,
        'helper_sha256':sha(__file__),'installed':False,
        'policy':'Preserve historical reports/vendor/archives; append campaigns, exact visible copies and follow-up audit support; no commit or publication'}
    write(stage/'installation-plan.json',proof)
    print('Reviewable native Outline pool update staged:',stage,flush=True)
    return proof

def atomic_copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.'+destination.name+'-',dir=destination.parent,delete=False) as temporary:
        name=Path(temporary.name)
        with source.open('rb') as stream:shutil.copyfileobj(stream,temporary)
    shutil.copystat(source,name)
    os.replace(name,destination)

def install(args,proof):
    repo=args.repo.resolve(strict=True);stage=args.stage.resolve(strict=True)
    if proof['repository']!=str(repo) or proof['stage']!=str(stage) or not proof.get('complete') or proof.get('installed'):
        raise ValueError('Installation requires the completed, uninstalled plan for these exact repository/stage paths')
    for relative,expected in proof['old_repository_file_sha256'].items():
        if sha(repo/relative)!=expected:raise ValueError(f'Repository changed while staging: {relative}')
    for relative,expected in proof['staged_files'].items():
        if sha(stage/relative)!=expected['sha256'] or (stage/relative).stat().st_size!=expected['bytes']:
            raise ValueError(f'Staged content changed: {relative}')
    allowed_overwrites={'README.md','analysis/copy-manifest.json','results/index.json',
        'scripts/independent_audit_math.py','scripts/verify-results.py','scripts/archive-campaign.py','scripts/archive-study.py'}
    for relative in proof['staged_files']:
        if (repo/relative).exists() and relative not in allowed_overwrites:
            raise ValueError(f'Unexpected existing destination: {relative}')
    for label,_,_ in CAMPAIGNS:
        source=stage/'results'/label;destination=repo/'results'/label
        temporary=repo/'results'/('.'+label+'.install-tmp')
        if destination.exists() or temporary.exists():raise ValueError(f'Archive destination already exists: {label}')
        shutil.copytree(source,temporary);os.replace(temporary,destination)
    for relative in proof['staged_files']:
        if relative.startswith('results/native-pool-') or relative=='results/index.json':continue
        atomic_copy(stage/relative,repo/relative)
    # Publish the index only after all linked archive/copy inputs are installed.
    atomic_copy(stage/'results/index.json',repo/'results/index.json')
    for relative in ('REPORT.md','SUMMARY.md','analysis/report-inputs.json','vendor/manifest.json'):
        if sha(repo/relative)!=proof['old_repository_file_sha256'][relative]:raise ValueError(f'Historical input changed: {relative}')
    proof.update(installed=True,installed_files=len(proof['staged_files']))
    write(stage/'installation-plan.json',proof)
    print('Installed native Outline pool follow-up; historical reports/vendor and all 22 prior index entries preserved:',repo,flush=True)
    print('Next: verify the three new archives and two raw audit plans before recording any validation outcome or committing.',flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=REPO)
    parser.add_argument('--stage',type=Path,required=True,help='Fresh directory outside repository and experiment roots')
    parser.add_argument('--conclusion',type=Path)
    parser.add_argument('--install',action='store_true',help='Also install the staged update; no commit or remote action')
    parser.add_argument('--install-existing-stage',action='store_true',help='Install an already staged, reviewed update without recompressing')
    args=parser.parse_args()
    if args.install_existing_stage and not args.install:parser.error('--install-existing-stage requires --install')
    proof=load(args.stage/'installation-plan.json') if args.install_existing_stage else stage_update(args)
    if args.install:install(args,proof)

if __name__=='__main__':main()
