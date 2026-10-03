#!/usr/bin/env python3
"""Verify compressed records offline and independently recompute selected effects.

Original historical paths remain untouched. Only verified metadata is extracted
into a fresh output directory. No old /tmp checkout, Rust build or GUI is needed.
"""
import argparse,datetime,json,subprocess,sys
from pathlib import Path
from benchlib import REPO,ArchiveStore,write_json,sha,safe_relative,bundled_manifest

def verify_visible_inputs(store):
    bundle=bundled_manifest();checks={'bundled_files':len(bundle['files']),'bundle_manifest_sha256':sha(REPO/'vendor/manifest.json')}
    path=REPO/'analysis/copy-manifest.json'
    if path.exists():
        copies=json.loads(path.read_text())
        for relative,expected in copies.items():
            safe_relative(relative);copy=REPO/relative
            if not copy.is_file() or copy.stat().st_size!=expected['bytes'] or sha(copy)!=expected['sha256']:raise ValueError(f'Visible analysis copy differs: {relative}')
            campaign,source_relative=store.original(expected['source'])
            archived=json.loads((REPO/campaign['path']/'archive.json').read_text())
            if archived['files'].get(source_relative)!={key:expected[key] for key in ('sha256','bytes')}:raise ValueError(f'Analysis copy differs from archived source record: {relative}')
        checks['analysis_copies']=len(copies);checks['copy_manifest_sha256']=sha(path)
    for filename,prefix in (('report-inputs.json','report_inputs'),('native-pool-report-inputs.json','native_pool_report_inputs'),('revised-cache-report-inputs.json','revised_cache_report_inputs'),('font-stress-report-inputs.json','font_stress_report_inputs'),('font-stress-rerun-report-inputs.json','font_stress_rerun_report_inputs'),('cjk-font-report-inputs.json','cjk_font_report_inputs'),('aggressive-font-report-inputs.json','aggressive_font_report_inputs')):
        path=REPO/'analysis'/filename
        if path.exists():
            inputs=json.loads(path.read_text())
            for relative,expected in inputs.items():
                safe_relative(relative)
                if not (REPO/relative).is_file() or sha(REPO/relative)!=expected:raise ValueError(f'Report input checksum differs: {relative}')
            checks[prefix]=len(inputs);checks[prefix+'_manifest_sha256']=sha(path)
    return checks

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True,help='Fresh verification artifact directory')
    parser.add_argument('--campaign',action='append',help='Verify only listed labels (default: all archives)')
    parser.add_argument('--integrity-only',action='store_true',help='Verify archive bytes without statistical recomputation')
    parser.add_argument('--ci',choices=('none','primary'),default='primary')
    parser.add_argument('--audit-plan',type=Path,help='Optional JSON list of explicit analysis_audits; default: results/index.json')
    args=parser.parse_args();store=ArchiveStore();index=json.loads(store.index.read_text());output=args.output.resolve()
    if output.exists():parser.error('--output must be new')
    if output.is_relative_to(REPO/'results') or output.is_relative_to(REPO/'vendor'):parser.error('Verification output cannot overwrite archives/sources')
    output.mkdir(parents=True)
    audits=json.loads(args.audit_plan.read_text()) if args.audit_plan else index.get('analysis_audits',[])
    campaigns=args.campaign or [entry['label'] for entry in store.campaigns]
    if len(set(campaigns))!=len(campaigns):parser.error('Duplicate campaign labels')
    selected=[audit for audit in audits if audit['campaign'] in campaigns] if not args.integrity_only else []
    # Cross-campaign historical references, including nested validators, resolve
    # through one verified longest-prefix map. Materialize each selected archive.
    # Audit companions are verified/extracted without selecting their other audit plans.
    for audit in selected:
        for label in audit.get('required_campaigns',[]):
            store.campaign(label)
            if label not in campaigns:campaigns.append(label)
    materialize=set(campaigns) if selected else set()
    full_materialize=set()
    for audit in selected:
        if audit['suite'] in ('cjk-native','cjk-localized','cjk-english','cjk-cost','aggressive-native','aggressive-demo-screen','aggressive-demo-confirmation'):
            full_materialize.update([audit['campaign'],*audit.get('required_campaigns',[])])
    report={'schema':1,'complete':False,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'index_sha256':sha(store.index),'archives':[],'audits':[],'binary_policy':'Compiled executables are omitted; provenance hashes retained. Offline audits verify their recorded identity, not absent binary bytes.',
        'verification_script_sha256':sha(__file__)}
    report['visible_inputs']=verify_visible_inputs(store)
    write_json(output/'verification.json',report)
    for label in campaigns:
        destination=output/'metadata'/label if label in materialize else None
        record=store.inspect(label,destination,metadata_only=label not in full_materialize);report['archives'].append(record)
        write_json(output/'verification.json',report);print(f'Archive verified: {label}',flush=True)
    path_map=output/'historical-path-map.json';write_json(path_map,store.path_map())
    for number,audit in enumerate(selected,1):
        campaign=store.campaign(audit['campaign']);root=store.materialized[audit['campaign']]
        def location(field):
            value=audit[field];safe_relative(value);path=root/value
            if not path.exists():raise ValueError(f'Audit input not retained: {audit["campaign"]}/{value}')
            return str(path)
        artifact=output/f'{number:02}-{audit["campaign"]}-{audit["suite"]}-audit.json'
        command=[sys.executable]
        if audit['suite']=='replay':
            protocol=audit.get('validation_protocol')
            if protocol not in (None,'native-master-offset-oracle'):raise ValueError('Unknown replay validation protocol: '+str(protocol))
            auditor='independent_oracle_raw_replay_audit.py' if protocol=='native-master-offset-oracle' else 'independent_raw_replay_audit.py'
            command += [str(REPO/'scripts'/auditor),'--results',location('results'),'--experiment',location('experiment')]
            if audit.get('modes'):command += ['--modes',*audit['modes']]
            for field,flag in (('phase_summary','--phase-summary'),('sequence_summary','--sequence-summary')):
                if audit.get(field):command += [flag,location(field)]
            command += ['--ci',args.ci]
        elif audit['suite']=='app':
            command += [str(REPO/'scripts/independent_raw_app_audit.py'),'--batch',location('batch'),'--analysis',location('analysis'),
                '--experiment',location('experiment'),'--archived-binaries','--ci','all' if args.ci=='primary' else 'none']
        elif audit['suite']=='font-confirmation':
            command += [str(REPO/'scripts/independent_font_confirmation_audit.py'),'--root',str(root)]
        elif audit['suite'] in ('cjk-native','aggressive-native'):
            command += [str(REPO/'scripts/independent_cjk_native_audit.py'),'--allow-missing-binaries']
            for name,relative_path in audit['screens']:
                safe_relative(relative_path)
                screen=root/relative_path
                if not screen.is_dir():raise ValueError('Native screen input not retained: '+relative_path)
                command += ['--screen',name,str(screen)]
        elif audit['suite']=='cjk-localized':
            command += [str(REPO/'scripts/independent_cjk_localized_confirmation_audit.py'),
                '--root',location('audit_root'),'--control-font',audit['control_font'],
                '--collector-fix-proof',location('collector_fix_proof')]
        elif audit['suite']=='cjk-english':
            command += [str(REPO/'scripts/independent_cjk_english_demo_audit.py'),
                '--root',location('audit_root'),'--allow-missing-binaries']
        elif audit['suite']=='cjk-cost':
            if (audit.get('expected_processes'),audit.get('expected_raw_rows'),audit.get('expected_cases'))!=(18,12960,360):
                raise ValueError('Full cost-cohort dimensions must be declared')
            command += [str(REPO/'scripts/independent_cjk_cost_decomposition_audit.py'),
                '--root',location('audit_root'),'--allow-missing-binaries',
                '--default-reader',str(REPO/'scripts/independent_cjk_cost_screen_audit.py'),
                '--weight-reader',str(REPO/'scripts/independent_cjk_weight_cost_screen_audit.py')]
        elif audit['suite']=='aggressive-demo-screen':
            cohort=root if audit['cohort_root']=='' else Path(location('cohort_root'))
            command += [str(REPO/'scripts/independent_aggressive_demo_screen_audit.py'),
                str(cohort),'--allow-missing-binaries']
        elif audit['suite']=='aggressive-demo-confirmation':
            confirmation_root=root if audit['audit_root']=='' else Path(location('audit_root'))
            command += [str(REPO/'scripts/independent_aggressive_demo_confirmation_audit.py'),
                '--root',str(confirmation_root)]
            for field,flag in (('cpu','--cpu'),('gpu','--gpu'),('analysis','--analysis'),
                               ('selection','--selection'),('collector_fix_proof','--collector-fix-proof')):
                if audit.get(field):command += [flag,location(field)]
            if audit.get('control_font'):command += ['--control-font',audit['control_font']]
        else:raise ValueError(f'Unknown audit suite: {audit["suite"]}')
        command += ['--path-map',str(path_map),'--output',str(artifact)]
        subprocess.run(command,check=True)
        report['audits'].append({'plan':audit,'artifact':artifact.name,'sha256':sha(artifact),'complete':True});write_json(output/'verification.json',report)
    report.update(complete=True,statistical_audits=len(selected),integrity_only=args.integrity_only,
                  statistical_scope='Selected replay/app/font-confirmation cohorts, exploratory CJK native/English/cost screens, and separately labeled localized CPU confirmations declared in analysis_audits; historical campaigns retain exact records and are checksum verified')
    write_json(output/'verification.json',report)
    print(f'Verified {len(campaigns)} campaign archives and {len(selected)} independent raw statistical audits: {output}')

if __name__=='__main__':main()
