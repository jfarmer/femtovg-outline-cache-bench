#!/usr/bin/env python3
"""Stage a reviewable revised-cache report/archive update, then optionally install.

Use only after every serial timing run, analysis and independent audit completes.
Default: write a fresh staging directory outside the benchmark repository. No
commit, publication, build, GUI launch or benchmark occurs. --install-existing
installs an already reviewed stage without recompressing it.
"""
from __future__ import annotations
import argparse, ast, hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

VERSIONS = ['master', 'prior', 'updated45', 'final']
PAIRS = [('master','prior'), ('master','updated45'), ('master','final'),
         ('prior','updated45'), ('prior','final'), ('updated45','final')]
LABELS = ['updated-cache-examples', 'updated-cache-alustin', 'updated-cache-source-bundle']
CHANGED_TOOLS = ['independent_audit_math.py', 'verify-results.py', 'archive-campaign.py', 'archive-study.py']

def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()
def load(path): return json.loads(Path(path).read_text())
def write(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def records(root):
    root=Path(root)
    if any(p.is_symlink() for p in root.rglob('*')):raise ValueError('Symlink in staged inputs: '+str(root))
    return {p.relative_to(root).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size}
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def replace_once(code, old, new, label):
    if code.count(old)!=1:raise ValueError(f'Expected exactly one adaptation marker in {label}: {old!r}')
    return code.replace(old,new)
def require_complete(path):
    value=load(path)
    if value.get('complete') is not True:raise ValueError('Completed measurement/audit required: '+str(path))
    return value

def completed_inputs(source, app):
    required=[source/'examples-validated'/f'{mode}-provenance.json' for mode in ('cpu','gpu','pixels')]
    required += [app/'cpu/summary.json',app/'pixels/summary.json',source/'final-validation.json',
                 source/'independent-source-build-audit.json',source/'independent-replay-statistics-audit.json',
                 source/'independent-identity-pixel-audit.json',source/'independent-native-offset-oracle-source-audit.json',
                 source/'independent-native-offset-oracle-build-audit.json',
                 app/'independent-app-statistics-audit.json',
                 app/'independent-order-audit.json']
    for path in required:require_complete(path)
    ledgers=[]
    for mode in ('cpu','gpu','pixels'):
        record=load(source/'examples-validated'/f'{mode}-provenance.json')['oracle_ledger'];path=Path(record['path'])
        if not path.is_relative_to(source) or sha(path)!=record['sha256'] or path.stat().st_size!=record['bytes']:
            raise ValueError('Accepted example native-oracle ledger is not unchanged retained evidence: '+str(path))
        require_complete(path);ledgers.append((path,record['sha256']))
    if len(set(ledgers))!=1:raise ValueError('Accepted example modes must use the same exact native oracle ledger')
    required.append(ledgers[0][0])
    summaries=[]
    for folder in (source/'analysis/replay/phase',source/'analysis/replay/sequence',app/'analysis'):
        summaries.extend([folder/'summary.csv',folder/'summary.json'])
        if any(not path.is_file() for path in summaries[-2:]):raise ValueError('Completed analysis missing: '+str(folder))
    if sha(source/'runtime/app/experiment.json')!=sha(app/'experiment.json'):
        raise ValueError('Alustin experiment differs from frozen runtime experiment')
    for path in (source/'runtime/core/experiment.json',app/'experiment.json'):
        experiment=load(path)
        if experiment['versions']!=VERSIONS or list(map(tuple,experiment['comparisons']))!=PAIRS:
            raise ValueError('Unexpected four-version comparison protocol: '+str(path))
    # This additional public-API workload remains inside the examples campaign.
    # Never archive an unfinished budget run as completed evidence.
    budget=[]
    if (source/'budget-timing').exists() or (source/'budget-audit').exists():
        budget=[source/'budget-timing/provenance.json',source/'budget-timing/analysis.json',
                source/'budget-audit/provenance.json',source/'budget-audit/audit.json',
                source/'budget/independent-budget-audit.json',
                source/'budget-reproduction/validation.json',
                source/'budget-reproduction/adaptation.json',
                source/'budget-reproduction/measured-locks/provenance.json']
        for path in budget:require_complete(path)
        reproduction=source/'budget-reproduction'
        validation=load(reproduction/'validation.json')
        adaptation=load(reproduction/'adaptation.json')
        lock_record=load(reproduction/'measured-locks/provenance.json')
        for field,path in (('driver_sha256',reproduction/'bench.py'),
                           ('adaptation_sha256',reproduction/'adaptation.json'),
                           ('measured_lock_record_sha256',reproduction/'measured-locks/provenance.json')):
            if validation[field]!=sha(path):raise ValueError('Validated budget reproduction changed: '+str(path))
        for name,digest in adaptation['reproduction_files'].items():
            if sha(reproduction/name)!=digest:raise ValueError('Pinned budget reproduction input changed: '+name)
        if lock_record['versions']!=VERSIONS or set(lock_record['locks'])!={'timing','audit'}:
            raise ValueError('Unexpected measured budget lock protocol')
        for kind in ('timing','audit'):
            if set(lock_record['locks'][kind])!=set(VERSIONS):raise ValueError('Missing measured budget locks: '+kind)
            for variant,record in lock_record['locks'][kind].items():
                expected='measured-locks/'+kind+'/'+variant+'/Cargo.lock'
                if record['file']!=expected or sha(reproduction/expected)!=record['sha256']:
                    raise ValueError('Measured budget lock changed: '+expected)
                budget.append(reproduction/expected)
        checks=validation['metadata_checks']
        if len(checks)!=8 or {(row['kind'],row['version']) for row in checks}!={(kind,variant) for kind in ('timing','audit') for variant in VERSIONS}:
            raise ValueError('Budget reproduction validation does not cover all eight exact builds')
        if any(row['matches_measured_graph'] is not True or row['lock_unchanged_after_metadata'] is not True for row in checks):
            raise ValueError('Budget reproduction graph/lock validation failed')
    return required+summaries+budget

def adapted_tools(repo, stage, source):
    updated={name:(repo/'scripts'/name).read_text() for name in CHANGED_TOOLS}
    name='independent_audit_math.py'
    updated[name]=replace_once(updated[name],
        "def baseline_pairs(versions):\n    assert versions[:2]==['master','current']\n",
        "def baseline_pairs(versions):\n"
        "    if versions==['master','prior','updated45','final']:\n"
        "        return [('master','prior'),('master','updated45'),('master','final'),\n"
        "                ('prior','updated45'),('prior','final'),('updated45','final')]\n"
        "    assert versions[:2]==['master','current']\n",name)
    name='verify-results.py'
    marker="('native-pool-report-inputs.json','native_pool_report_inputs')"
    updated[name]=replace_once(updated[name],marker,marker+",('revised-cache-report-inputs.json','revised_cache_report_inputs')",name)
    marker="            command += [str(REPO/'scripts/independent_raw_replay_audit.py'),'--results',location('results'),'--experiment',location('experiment')]"
    updated[name]=replace_once(updated[name],marker,
        "            protocol=audit.get('validation_protocol')\n"
        "            if protocol not in (None,'native-master-offset-oracle'):raise ValueError('Unknown replay validation protocol: '+str(protocol))\n"
        "            auditor='independent_oracle_raw_replay_audit.py' if protocol=='native-master-offset-oracle' else 'independent_raw_replay_audit.py'\n"
        "            command += [str(REPO/'scripts'/auditor),'--results',location('results'),'--experiment',location('experiment')]",name)
    name='archive-campaign.py'
    updated[name]=replace_once(updated[name],'def inventory(source):','def inventory(source, excluded_prefixes=()):',name)
    updated[name]=replace_once(updated[name],
        '        if path.is_symlink():\n            reason = "symlink; original target is recorded"',
        '        if any(relative==prefix or prefix in relative.parents for prefix in excluded_prefixes):\n'
        '            reason = "separately archived nested campaign; original bytes retained there"\n'
        '        elif path.is_symlink():\n            reason = "symlink; original target is recorded"',name)
    updated[name]=replace_once(updated[name],
        '    parser.add_argument("--label", required=True)',
        '    parser.add_argument("--label", required=True)\n'
        '    parser.add_argument("--exclude-prefix", action="append", default=[], help="Nested root retained in its own campaign archive")',name)
    updated[name]=replace_once(updated[name],
        '    kept, omitted = inventory(source)',
        '    for value in args.exclude_prefix:\n'
        '        if not value or Path(value).is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):\n'
        '            parser.error("--exclude-prefix must be a safe relative directory")\n'
        '        if not (source/value).is_dir():parser.error("--exclude-prefix must identify an existing nested campaign directory")\n'
        '    excluded_prefixes=tuple(Path(value) for value in args.exclude_prefix)\n'
        '    kept, omitted = inventory(source, excluded_prefixes)',name)
    updated[name]=replace_once(updated[name],
        '                "files": {}, "omitted": omitted, "complete": False}',
        '                "files": {}, "omitted": omitted, "excluded_nested_campaign_prefixes": args.exclude_prefix, "complete": False}',name)
    updated[name]=replace_once(updated[name],
        '    final_kept, final_omitted = inventory(source)',
        '    final_kept, final_omitted = inventory(source, excluded_prefixes)',name)
    name='archive-study.py'
    marker='    ("native-pool-source-bundle", "femtovg-outline-pool-bundle", "native-outline-reproduction"),\n'
    entries=''.join(f'    ({label!r}, {str(root)!r}, {role!r}),\n' for label,root,role in (
        (LABELS[0],source,'revised-cache-comparison'),(LABELS[1],source/'alustin','revised-cache-comparison'),
        (LABELS[2],source/'bundle','revised-cache-reproduction')))
    updated[name]=replace_once(updated[name],marker,marker+entries,name)
    # Re-archiving this cohort through archive-study uses the same nested-root
    # exclusions. Existing cohorts still use the exact old archiver interface.
    marker='        subprocess.run([sys.executable, str(REPO / "scripts/archive-campaign.py"), str(source),\n                        str(destination), "--label", label], check=True)'
    replacement='        command=[sys.executable, str(REPO / "scripts/archive-campaign.py"), str(source), str(destination), "--label", label]\n'
    replacement+='        if label=="updated-cache-examples":command += ["--exclude-prefix","alustin","--exclude-prefix","bundle"]\n'
    replacement+='        subprocess.run(command, check=True)'
    updated[name]=replace_once(updated[name],marker,replacement,name)
    for name,code in updated.items():
        ast.parse(code,filename=name);path=stage/'scripts'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(code)
    spec=importlib.util.spec_from_file_location('revised_installer_math',stage/'scripts/independent_audit_math.py')
    helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
    for versions in (['master','current','final','route'],['master','current','final','pool'],VERSIONS):
        assert len(helpers.pairs(versions))==6
        assert helpers.declared_pairs(versions,helpers.pairs(versions))==helpers.pairs(versions)
    assert helpers.pairs(VERSIONS)==PAIRS

def reproduction_wrapper():
    return '''#!/usr/bin/env python3
"""Verify/extract the revised frozen source bundle and prepare a fresh runtime."""
import argparse,subprocess,sys
from pathlib import Path
from benchlib import REPO,ArchiveStore
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--alustin-checkout',type=Path)
    parser.add_argument('--with-budget',action='store_true')
    args=parser.parse_args();output=args.output.resolve()
    if output.exists():parser.error('--output must be fresh')
    if output.is_relative_to(REPO/'results') or output.is_relative_to(REPO/'vendor'):parser.error('Output cannot replace archived inputs')
    output.mkdir(parents=True)
    ArchiveStore().inspect('updated-cache-source-bundle',output/'bundle')
    command=[sys.executable,str(output/'bundle/scripts/prepare.py'),'--output',str(output/'runtime')]
    if args.alustin_checkout:command+=['--alustin-checkout',str(args.alustin_checkout.resolve(strict=True))]
    subprocess.run(command,check=True)
    if args.with_budget:
        command=[sys.executable,str(REPO/'benchmarks/revised-cache-budget/bench.py'),'prepare','--output',str(output/'budget-runtime')]
        for variant in ('master','prior','updated45','final'):command+=['--source',variant,str(output/'runtime/core/snapshots'/variant)]
        subprocess.run(command,check=True)
    print(output)
if __name__=='__main__':main()
'''

def verify_nested_retention(main_archive, child_archives, source):
    for omitted in main_archive['omitted']:
        if not omitted['reason'].startswith('separately archived nested campaign'):continue
        relative=Path(omitted['path']);name=relative.parts[0];child=child_archives[name]
        nested=Path(*relative.parts[1:]).as_posix();expected=child['files'].get(nested)
        original=source/relative
        if expected:
            if expected!={'sha256':sha(original),'bytes':original.stat().st_size}:
                raise ValueError('Nested raw evidence differs from child archive: '+str(relative))
        else:
            child_omitted={entry['path']:entry for entry in child['omitted']}
            if nested not in child_omitted or child_omitted[nested]['bytes']!=omitted['bytes']:
                raise ValueError('Nested evidence is absent from child archive: '+str(relative))
            if child_omitted[nested]['reason'].startswith('separately archived'):
                raise ValueError('Unexpected second-level campaign exclusion: '+str(relative))

def stage_update(args):
    source=args.source.resolve(strict=True);repo=args.repository.resolve(strict=True);stage=args.stage.resolve()
    app=source/'alustin';bundle=source/'bundle'
    if stage.exists() or stage.is_relative_to(repo) or stage.is_relative_to(source):
        raise ValueError('Stage must be fresh and outside repository and all study roots')
    subprocess.run(['git','diff','--quiet'],cwd=repo,check=True);subprocess.run(['git','diff','--cached','--quiet'],cwd=repo,check=True)
    required=completed_inputs(source,app)
    report=(args.report or source/'REVISED-OUTLINE-CACHE.md').resolve(strict=True)
    if not report.is_relative_to(source):raise ValueError('Report must be inside source campaign so its bytes are archived')
    report_input_proof=source/'REVISED-OUTLINE-CACHE.inputs.json'
    if report_input_proof.is_file():
        report_inputs=load(report_input_proof)
        for original_path,expected in report_inputs.get('files',{}).items():
            path=Path(original_path)
            if not path.is_absolute():path=source/path
            if not path.is_file() or sha(path)!=expected['sha256'] or path.stat().st_size!=expected['bytes']:
                raise ValueError('Report source input changed: '+str(path))
        if report_inputs.get('script'):
            renderer=report_inputs['script'];path=Path(renderer['path'])
            if not path.is_absolute():path=source/path
            if not path.is_file() or sha(path)!=renderer['sha256']:raise ValueError('Report renderer changed: '+str(path))
    index=load(repo/'results/index.json');old_index=json.loads(json.dumps(index));copies=load(repo/'analysis/copy-manifest.json')
    if {c['label'] for c in index['campaigns']} & set(LABELS):raise ValueError('Revised-cache campaigns already indexed')
    if not {'native-pool-examples','native-pool-alustin','native-pool-source-bundle'} <= {c['label'] for c in index['campaigns']}:
        raise ValueError('Expected the existing native-pool follow-up to be preserved')
    sys.path.insert(0,str(repo/'scripts'));from benchlib import bundled_manifest
    original=bundled_manifest(repo);new_bundle=bundled_manifest(bundle)
    if new_bundle['versions']!=VERSIONS:raise ValueError('Wrong fresh source bundle variants')
    pool_entry=next(c for c in index['campaigns'] if c['label']=='native-pool-source-bundle')
    pool_manifest=load(repo/pool_entry['path']/'archive.json')['files']['vendor/manifest.json']['sha256']
    if new_bundle['comparison_origin']['manifest_sha256']!=pool_manifest:
        raise ValueError('Fresh bundle does not derive from the preserved native-pool source bundle')
    protected=['REPORT.md','SUMMARY.md','NATIVE-OUTLINE-POOL.md','README.md','results/index.json','analysis/copy-manifest.json',
        'analysis/report-inputs.json','analysis/native-pool-report-inputs.json','vendor/manifest.json']
    protected+=['scripts/'+name for name in CHANGED_TOOLS]
    baseline={name:sha(repo/name) for name in protected};stage.mkdir(parents=True)
    adapted_tools(repo,stage,source)
    wrapper=stage/'scripts/prepare-revised-cache.py';wrapper.write_text(reproduction_wrapper());ast.parse(wrapper.read_text())
    # All generated repository-facing tools have a retained study source,
    # making their visible-copy hashes independently resolvable to an archive.
    evidence=Path(tempfile.mkdtemp(prefix='repository-tools-',dir=source))
    for path in (stage/'scripts').glob('*.py'):shutil.copy2(path,evidence/path.name)
    write(evidence/'adaptation-provenance.json',{'complete':True,'repository':str(repo),
        'original_tool_sha256':{name:baseline['scripts/'+name] for name in CHANGED_TOOLS},
        'adapted_files':records(evidence),'installer_sha256':sha(__file__),
        'policy':'Preserve legacy comparisons; explicitly add the six revised pairs, one report-input manifest, and separately archived nested-root exclusions'})
    campaigns=[(LABELS[0],source,'revised-cache-comparison'),(LABELS[1],app,'revised-cache-comparison'),
               (LABELS[2],bundle,'revised-cache-reproduction')]
    archived={}
    # Archive children before their parent so excluded bytes can be checked
    # against independently verified child manifests immediately.
    for label,root,role in campaigns[1:]+campaigns[:1]:
        if (repo/'results'/label).exists():raise ValueError('Archive destination already exists: '+label)
        destination=stage/'results'/label
        command=[sys.executable,str(stage/'scripts/archive-campaign.py'),str(root),str(destination),'--label',label]
        if root==source:command+=['--exclude-prefix','alustin','--exclude-prefix','bundle']
        subprocess.run(command,check=True);archived[label]=load(destination/'archive.json')
    verify_nested_retention(archived[LABELS[0]],{'alustin':archived[LABELS[1]],'bundle':archived[LABELS[2]]},source)
    for label,root,role in campaigns:
        record=archived[label]
        index['campaigns'].append({'label':label,'path':'results/'+label,'original_root':record['original_root'],'role':role,
            'complete':record['complete'],'archive':record['archive'],'files':len(record['files']),'raw_bytes':record['raw_bytes']})
    index.setdefault('analysis_audits',[]).extend([
        {'suite':'replay','campaign':LABELS[0],'results':'examples-validated','experiment':'runtime/core/experiment.json','modes':['cpu','gpu'],
         'validation_protocol':'native-master-offset-oracle',
         'phase_summary':'analysis/replay/phase/summary.csv','sequence_summary':'analysis/replay/sequence/summary.csv'},
        {'suite':'app','campaign':LABELS[1],'batch':'cpu','analysis':'analysis','experiment':'experiment.json'}])
    visible=[]
    for origin,destination in ((source/'analysis/replay/phase','analysis/updated-cache-examples'),
        (source/'analysis/replay/sequence','analysis/updated-cache-sequences'),(app/'analysis','analysis/updated-cache-alustin')):
        visible.extend((p,Path(destination)/p.relative_to(origin)) for p in sorted(origin.rglob('*'))
                       if p.is_file() and '__pycache__' not in p.parts)
    named=[(report,'REVISED-OUTLINE-CACHE.md'),
        (source/'REVISED-OUTLINE-CACHE-TABLES.md','REVISED-OUTLINE-CACHE-TABLES.md'),
        (source/'REVISED-OUTLINE-CACHE-TABLES.inputs.json','analysis/updated-cache-original-table-inputs.json'),
        (source/'revised-cache-metrics.json','analysis/updated-cache-metrics.json'),
        (source/'revised-cache-reproduction.md','docs/revised-cache-reproduction.md'),
        (source/'final-validation.json','analysis/updated-cache-final-validation.json'),
        (source/'independent-source-identities.json','analysis/updated-cache-source-identities.json'),
        (source/'independent-source-build-audit.json','analysis/updated-cache-source-build-audit.json'),
        (source/'independent-identity-pixel-audit.json','analysis/updated-cache-identity-pixel-audit.json'),
        (source/'independent-native-offset-oracle-source-audit.json','analysis/updated-cache-native-oracle-source-audit.json'),
        (source/'independent-native-offset-oracle-build-audit.json','analysis/updated-cache-native-oracle-build-audit.json'),
        (source/'independent-replay-statistics-audit.json','analysis/updated-cache-replay-audit.json'),
        (app/'independent-app-statistics-audit.json','analysis/updated-cache-app-audit.json'),
        (app/'independent-order-audit.json','analysis/updated-cache-order-audit.json'),
        (source/'source-audit-notes.md','docs/revised-cache-source-review.md'),
        (source/'validation-overlay-v4/independent_raw_replay_audit.py','scripts/independent_oracle_raw_replay_audit.py'),
        (source/'native_offset_oracle.py','benchmarks/revised-cache-oracle/native_offset_oracle.py'),
        (source/'prepare_validation_overlay.py','benchmarks/revised-cache-oracle/prepare_validation_overlay.py'),
        (source/'check_validation_overlay.py','benchmarks/revised-cache-oracle/check_validation_overlay.py'),
        (Path(__file__),'scripts/install-revised-cache-study.py')]
    # Root authors the report only after analysis; the installer copies its
    # renderer and exact input manifest if present, without inventing results.
    for origin,destination in ((source/'revised-cache-report.py','scripts/render-revised-cache-report.py'),
        (source/'REVISED-OUTLINE-CACHE.inputs.json','analysis/updated-cache-original-report-inputs.json')):
        if origin.is_file():named.append((origin,destination))
    if (source/'budget-timing').exists():
        named += [(source/'budget-timing/analysis.json','analysis/updated-cache-budget-effects.json'),
            (source/'budget-audit/audit.json','analysis/updated-cache-budget-pixels.json'),
            (source/'budget/independent-budget-audit.json','analysis/updated-cache-budget-audit.json')]
        reproduction=source/'budget-reproduction'
        named.extend((path,'benchmarks/revised-cache-budget/'+path.relative_to(reproduction).as_posix())
                     for path in sorted(reproduction.rglob('*'))
                     if path.is_file() and '__pycache__' not in path.parts)
    visible.extend((origin,Path(destination)) for origin,destination in named)
    for origin,relative in visible:
        if not origin.is_file():raise ValueError('Required visible evidence missing: '+str(origin))
        destination=stage/relative
        if (repo/relative).exists() or destination.exists():raise ValueError('Visible evidence destination exists: '+str(relative))
        destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(origin,destination)
        if relative.as_posix() in copies:raise ValueError('Duplicate copy-manifest record: '+str(relative))
        copies[relative.as_posix()]={'source':str(origin.resolve()),'sha256':sha(origin),'bytes':origin.stat().st_size}
    # The newly adapted tools already exist in stage; record their archived
    # copies explicitly rather than creating duplicate staging destinations.
    for name in CHANGED_TOOLS+['prepare-revised-cache.py']:
        copies['scripts/'+name]={'source':str((evidence/name).resolve()),'sha256':sha(stage/'scripts'/name),
            'bytes':(stage/'scripts'/name).stat().st_size}
    write(stage/'analysis/revised-cache-report-inputs.json',{relative.as_posix():sha(stage/relative) for _,relative in visible})
    write(stage/'analysis/copy-manifest.json',copies);write(stage/'results/index.json',index)
    marker='## Verify the retained evidence offline\n'
    addition='''## Revised outline-cache follow-up

The [revised-cache comparison](REVISED-OUTLINE-CACHE.md) records a fresh four-way
master/prior/fixes-4–5/final comparison, with example and Alustin measurements
under a balanced order schedule, pixels, independent audits, and the targeted
public-API cache-boundary workload. The prior reports, source bundle, and campaign
archives remain preserved. Three added archives retain every raw attempt and
the isolated frozen reproduction bundle. See [reproduction](docs/revised-cache-reproduction.md)
and `scripts/prepare-revised-cache.py` for a fresh extraction/preparation.

'''
    (stage/'README.md').write_text(replace_once((repo/'README.md').read_text(),marker,addition+marker,'README.md'))
    assert index['campaigns'][:len(old_index['campaigns'])]==old_index['campaigns']
    assert index['analysis_audits'][:len(old_index['analysis_audits'])]==old_index['analysis_audits']
    proof={'schema':1,'complete':True,'installed':False,'repository':str(repo),'source':str(source),'stage':str(stage),
        'old_repository_file_sha256':baseline,'source_inputs':{str(p):sha(p) for p in required},
        'old_campaign_count':len(old_index['campaigns']),'old_audit_count':len(old_index['analysis_audits']),
        'new_labels':LABELS,'new_audit_count':2,'staged_files':records(stage),'installer_sha256':sha(__file__),
        'original_bundled_files_verified':len(original['files']),'fresh_bundle_manifest_sha256':sha(bundle/'vendor/manifest.json'),
        'nested_raw_evidence_verified':True,'policy':'Append evidence; preserve old reports/vendor/archive bytes; no commit or remote action'}
    write(stage/'installation-plan.json',proof)
    print('Reviewable revised-cache update staged:',stage)
    return proof

def atomic_copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.'+destination.name+'-',dir=destination.parent,delete=False) as stream:
        temporary=Path(stream.name)
        with source.open('rb') as origin:shutil.copyfileobj(origin,stream)
    shutil.copystat(source,temporary);os.replace(temporary,destination)

def install(args,proof):
    repo=args.repository.resolve(strict=True);stage=args.stage.resolve(strict=True)
    if not proof.get('complete') or proof.get('installed') or proof['repository']!=str(repo) or proof['stage']!=str(stage):
        raise ValueError('Install requires the completed, unchanged, uninstalled plan for this exact stage/repository')
    for relative,expected in proof['old_repository_file_sha256'].items():
        if sha(repo/relative)!=expected:raise ValueError('Repository changed since staging: '+relative)
    for relative,expected in proof['staged_files'].items():
        if sha(stage/relative)!=expected['sha256'] or (stage/relative).stat().st_size!=expected['bytes']:
            raise ValueError('Staged input changed: '+relative)
    allowed={'README.md','results/index.json','analysis/copy-manifest.json'}|{'scripts/'+name for name in CHANGED_TOOLS}
    for relative in proof['staged_files']:
        if (repo/relative).exists() and relative not in allowed:raise ValueError('Unexpected existing destination: '+relative)
    for label in proof['new_labels']:
        destination=repo/'results'/label;temporary=destination.with_name('.'+label+'.install-tmp')
        if destination.exists() or temporary.exists():raise ValueError('Archive destination exists: '+label)
        shutil.copytree(stage/'results'/label,temporary);os.replace(temporary,destination)
    for relative in proof['staged_files']:
        if relative=='results/index.json' or any(relative.startswith('results/'+label+'/') for label in proof['new_labels']):continue
        atomic_copy(stage/relative,repo/relative)
    atomic_copy(stage/'results/index.json',repo/'results/index.json')
    for relative in ('REPORT.md','SUMMARY.md','NATIVE-OUTLINE-POOL.md','analysis/report-inputs.json','analysis/native-pool-report-inputs.json','vendor/manifest.json'):
        if sha(repo/relative)!=proof['old_repository_file_sha256'][relative]:raise ValueError('Historical report/input changed: '+relative)
    proof.update(installed=True,installed_files=len(proof['staged_files']));write(stage/'installation-plan.json',proof)
    print('Installed revised-cache evidence; old reports, vendor bundle and index entries preserved:',repo)
    print('Next: verify the three added archives and the two new raw audit plans before recording validation or committing.')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parent)
    parser.add_argument('--repository',type=Path,default=Path('/Users/jesse/github/femtovg-outline-cache-bench'))
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--install',action='store_true')
    parser.add_argument('--install-existing',action='store_true',help='Install an already reviewed stage without recompression')
    args=parser.parse_args()
    if args.install_existing and not args.install:parser.error('--install-existing requires --install')
    proof=load(args.stage/'installation-plan.json') if args.install_existing else stage_update(args)
    if args.install:install(args,proof)

if __name__=='__main__':main()
