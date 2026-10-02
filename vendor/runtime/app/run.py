#!/usr/bin/env python3
"""Fresh balanced multi-version Alustin blocks for cache policy comparisons.

cpu/startup/pixels open windows. CPU diagnostics and actual-font dump diagnostics
are mutually exclusive; actual faces are verified in untimed pixels runs only.
Only a contaminated final query retries a whole block. All raw attempts remain.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from benchmark_helpers import digest,event_map,file_info,git_head
from baseline_run_helpers import BACKENDS,FONT_DEFAULTS,ROOT,extract_metrics,pixel_comparison,validate_report,write_csv

HERE=Path(__file__).resolve().parent
VERSIONS=tuple(json.loads((HERE/'experiment.json').read_text())['versions'])
def williams(n):
    base=[0]+[(i+1)//2 if i%2 else n-i//2 for i in range(1,n)]
    rows=[tuple(VERSIONS[(x+k)%n] for x in base) for k in range(n)]
    if n%2:rows += [tuple(reversed(row)) for row in rows]
    from collections import Counter
    positions=Counter((p,v) for row in rows for p,v in enumerate(row))
    carry=Counter((a,b) for row in rows for a,b in zip(row,row[1:]))
    assert len(set(positions.values()))==1 and len(set(carry.values()))==1 and len(carry)==n*(n-1)
    return tuple(rows)
ORDERS=williams(len(VERSIONS))

def checkpoint(output,result,accepted):
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    write_csv(output/'accepted.csv',accepted)
    write_csv(output/'attempts.csv',[
      {key:r.get(key) for key in ('label','round','backend','font','family','attempt','version','exit_code','validated','included','validation_error','report')}|r.get('metrics',{})
      for r in result['launches']])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('cpu','startup','pixels'))
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--build-provenance',type=Path,default=HERE/'build/provenance.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--rounds',type=int,default=12)
    parser.add_argument('--max-attempts',type=int,default=3)
    parser.add_argument('--timeout',type=int,default=120)
    parser.add_argument('--backends',nargs='+',choices=BACKENDS,default=list(BACKENDS))
    parser.add_argument('--fonts',nargs='+',choices=tuple(FONT_DEFAULTS),default=['vollkorn','ptsans','roboto'])
    parser.add_argument('--font',action='append',nargs=3,metavar=('NAME','FAMILY','FILE'))
    parser.add_argument('--font-event',default='benchmark_font_configured')
    parser.add_argument('--actual-font-diagnostics',action='store_true')
    parser.add_argument('--font-verifier',type=Path,default=HERE/'verify_actual_fonts.py')
    parser.add_argument('--fallback-font',type=Path,default=ROOT/'crates/alustin-gui/vendor/i-slint-common/sharedfontique/Inter-VariableFont.ttf')
    parser.add_argument('--save',type=Path)
    parser.add_argument('--catalog',type=Path)
    parser.add_argument('--icon-pack',type=Path)
    args=parser.parse_args()
    if args.rounds<1 or args.timeout<1 or not 1<=args.max_attempts<=3:parser.error('rounds/timeout positive; max-attempts 1–3')
    if args.actual_font_diagnostics and args.mode!='pixels':parser.error('Actual font diagnostics are untimed pixels-only')
    if len(set(args.backends))!=len(args.backends) or len(set(args.fonts))!=len(args.fonts):parser.error('Fonts/backends must be unique')
    definitions=dict(FONT_DEFAULTS)
    for name,family,path in args.font or []:
        if name not in definitions or not family.strip():parser.error('--font requires a known name and nonempty family')
        definitions[name]=(family,Path(path))
    root=args.root.resolve(strict=True)
    build=json.loads(args.build_provenance.read_text())
    if not build.get('complete') or not build.get('app_lock_restored') or not build.get('final_app_inputs_match'):
        parser.error('Build provenance must be complete with restored lock and unchanged app inputs')
    if set(build['variants'])!=set(VERSIONS):parser.error('Build must contain the configured variants')
    if git_head(root)!=build['app_commit']:parser.error('Application HEAD differs from build provenance')
    if build.get('app_tracked_inputs'):
        from verify_ready import verify_app
        verify_app(HERE)
    binary_info={version:file_info(build['variants'][version]['binary']['path']) for version in VERSIONS}
    for version,info in binary_info.items():
        if info!=build['variants'][version]['binary']:parser.error(f'{version} binary differs from build provenance')
    harness_info=file_info(build['harness']['path'])
    if harness_info!=build['harness']:parser.error('Shared harness differs from build provenance')
    if len({info['path'] for info in binary_info.values()})!=len(VERSIONS):parser.error('Distinct executable paths required')
    binaries={version:Path(info['path']) for version,info in binary_info.items()}
    paths={'save':args.save or root/'fixtures/sample_save_large.save','catalog':args.catalog or root/'item_names.json',
           'icon_pack':args.icon_pack or root/'logs/slint-startup/icon-pack/icons-128-raw.pack'}
    inputs={name:file_info(path) for name,path in paths.items()}
    fonts={name:{'family':definitions[name][0],'file':file_info(definitions[name][1])} for name in args.fonts}
    diagnostics={'enabled':args.actual_font_diagnostics}
    if args.actual_font_diagnostics:diagnostics.update(verifier=file_info(args.font_verifier),fallback=file_info(args.fallback_font))
    env=dict(os.environ)
    for name in ('SLINT_FONT_PATH','SLINT_DEFAULT_FONT','ALUSTIN_BENCH_FONT_FAMILY','ALUSTIN_FONT_DIAGNOSTICS_DIR','ALUSTIN_TEST_SAVE','ALUSTIN_ICONS',
                 'MTL_SHADER_CACHE_SIZE','SLINT_TRACE_RENDERER_STARTUP','SLINT_MCP_PORT','SLINT_DEBUG_PERFORMANCE','SLINT_SLOW_ANIMATIONS',
                 'FEMTOVG_REQUIRE_GPU','SLINT_REVEAL_DELAY_MS','SLINT_PRESENT_WITH_TRANSACTION','SLINT_MACOS_MATCH_BACKGROUND',
                 'SLINT_GPU_WARMUP_PIPELINE_HANDOFF','SLINT_WINDOW_ID'):
        env.pop(name,None)
    fixed_env={'SLINT_SCALE_FACTOR':'2','SLINT_LAZY_SHADERS':'0','SLINT_GPU_WARMUP':'1','SLINT_NO_SYSTEM_FONTS':'1',
      'WINIT_MACOS_WINDOW_ANIMATION':'0','WGPU_METAL_INITIAL_DRAWABLE':'1','ALUSTIN_ITEM_NAMES':inputs['catalog']['path'],
      'ALUSTIN_FEMTOVG_DIAGNOSTICS':'1' if args.mode=='cpu' else '0','SLINT_STARTUP_DIAGNOSTICS':'1' if args.mode=='cpu' else '0'}
    env.update(fixed_env)
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    rounds=1 if args.mode=='pixels' else args.rounds
    result={'mode':args.mode,'root':str(root),'app_commit':build['app_commit'],
      'build_provenance':file_info(args.build_provenance),'source_variants':{version:{key:record[key] for key in ('label','base_ref','source_directory','source_map_sha256','source_sha256')} for version,record in build['variants'].items()},
      'versions':list(VERSIONS),'harness':harness_info,'binaries':binary_info,'inputs':inputs,'fonts':fonts,
      'runner':file_info(Path(__file__)),'helpers':file_info(HERE/'benchmark_helpers.py'),'validation_helpers':file_info(HERE/'baseline_run_helpers.py'),
      'platform':platform.platform(),'environment':fixed_env,'rounds':rounds,'max_attempts':args.max_attempts,'backends':list(args.backends),
      'font_event_schema':{'event':args.font_event,'fields':['family','font_path']},'actual_font_diagnostics':diagnostics,
      'font_policy':'All selected font files explicitly registered; system discovery disabled; bundled Inter fallback retained',
      'cache_policy':'Fresh processes; uncontrolled OS/Metal shader caches; all raw attempts retained',
      'pairing':'Adjacent variant launches per font/backend/round; Williams order balances position and directed carryover; rotate configuration order',
      'version_orders':[list(order) for order in ORDERS],
      'retry_policy':'Only final query != a retries all variants, maximum three whole-block attempts; first valid block accepted without inspecting durations; every other failure aborts incomplete batch',
      'metrics':'Host wall/thread CPU and harness/IPC readiness; excludes GPU completion/compositor scanout; nested spans overlap; pixels untimed',
      'order':[],'launches':[],'accepted_blocks':[],'pixel_comparisons':[],'complete':False}
    accepted=[];groups=[(backend,font) for font in args.fonts for backend in args.backends]
    checkpoint(output,result,accepted)
    for round_index in range(rounds):
        offset=round_index%len(groups);ordered=groups[offset:]+groups[:offset];round_order=[];result['order'].append(round_order)
        for backend,name in ordered:
            success=False
            for attempt in range(1,args.max_attempts+1):
                versions=ORDERS[(round_index+attempt-1)%len(ORDERS)]
                block_records=[];contamination=[]
                for version in versions:
                    label=f'{round_index+1:02}-{backend}-{name}-attempt{attempt}-{version}'
                    round_order.append(label);child_output=output/label;font=fonts[name]
                    launch_env=dict(env,SLINT_FONT_PATH=font['file']['path'],ALUSTIN_BENCH_FONT_FAMILY=font['family'])
                    diagnostic_directory=child_output/'actual-fonts'
                    if args.actual_font_diagnostics:launch_env['ALUSTIN_FONT_DIAGNOSTICS_DIR']=str(diagnostic_directory)
                    command=[harness_info['path'],'--runs','1','--timeout',str(args.timeout),'--backend',backend,'--binary',str(binaries[version]),
                      '--save',inputs['save']['path'],'--icon-pack',inputs['icon_pack']['path'],'--font-path',font['file']['path'],
                      '--no-system-fonts','--output',str(child_output)]
                    if args.mode=='cpu':command.append('--slint-internals')
                    if args.mode=='pixels':command.append('--screenshot')
                    record={'label':label,'round':round_index+1,'backend':backend,'font':name,'family':font['family'],'attempt':attempt,'version':version,
                      'command':command,'environment':{'SLINT_FONT_PATH':font['file']['path'],'ALUSTIN_BENCH_FONT_FAMILY':font['family']},
                      'report':str(child_output/'summary.json'),'validated':False,'included':False}
                    if args.actual_font_diagnostics:record['environment']['ALUSTIN_FONT_DIAGNOSTICS_DIR']=str(diagnostic_directory)
                    result['launches'].append(record);block_records.append(record);checkpoint(output,result,accepted)
                    try:
                        with (output/f'{label}.harness.stdout').open('w') as stdout,(output/f'{label}.harness.stderr').open('w') as stderr:
                            completed=subprocess.run(command,cwd=root,env=launch_env,stdout=stdout,stderr=stderr,timeout=args.timeout+30)
                        record['exit_code']=completed.returncode
                        if completed.returncode:raise RuntimeError(f'Harness exited {completed.returncode}')
                        report=json.loads((child_output/'summary.json').read_text())
                        sample,frames,selected,reason=validate_report(report,binaries[version],binary_info[version]['sha256'],backend,font,args.mode,args.font_event)
                        record.update(frames=frames,font_configured_event=selected,metrics=extract_metrics(sample,frames))
                        if reason:
                            record['validation_error']=reason;contamination.append(f'{version}: {reason}')
                        else:
                            if args.actual_font_diagnostics:
                                verify=[sys.executable,diagnostics['verifier']['path'],str(diagnostic_directory),'--primary',font['file']['path'],'--family',font['family'],
                                  '--allow-fallback',diagnostics['fallback']['path'],'--require-fallback']
                                record['font_verification_command']=verify;checkpoint(output,result,accepted)
                                with (output/f'{label}.font-verify.stdout').open('w') as stdout,(output/f'{label}.font-verify.stderr').open('w') as stderr:
                                    verified=subprocess.run(verify,stdout=stdout,stderr=stderr,timeout=30)
                                record['font_verification_exit_code']=verified.returncode
                                if verified.returncode:raise ValueError('Actual renderer-font verification failed')
                                record['actual_fonts']=json.loads((diagnostic_directory/'actual-fonts.json').read_text())
                            record['validated']=True
                    except (OSError,ValueError,RuntimeError,KeyError,subprocess.SubprocessError) as error:
                        record['validation_error']=str(error);result['failure']=f'{label}: {error}';checkpoint(output,result,accepted);raise
                    checkpoint(output,result,accepted);print(f'{label}: '+('validated' if not reason else reason),flush=True)
                if contamination:
                    reason='; '.join(contamination)
                    for record in block_records:record['exclusion_reason']=f'Whole block excluded: {reason}'
                    checkpoint(output,result,accepted)
                    print(f'Retrying entire block {round_index+1}/{backend}/{name}, attempt {attempt}; all raw reports retained',flush=True)
                    continue
                if args.mode=='pixels':
                    by_version={record['version']:record for record in block_records}
                    for version in VERSIONS[1:]:
                        comparison=pixel_comparison(Path(by_version['master']['report']).parent/'run-1.png',Path(by_version[version]['report']).parent/'run-1.png',backend,name)
                        comparison.update(reference='master',candidate=version)
                        result['pixel_comparisons'].append(comparison);checkpoint(output,result,accepted)
                        if not comparison['rgba_identical']:raise RuntimeError(f'Pixel mismatch {backend}/{name}/{version}; batch incomplete')
                for record in block_records:
                    record['included']=True
                    accepted.append({key:record[key] for key in ('round','backend','font','family','attempt','version','report')}|record['metrics'])
                result['accepted_blocks'].append({'round':round_index+1,'backend':backend,'font':name,'attempt':attempt,'labels':[record['label'] for record in block_records]})
                checkpoint(output,result,accepted);success=True;break
            if not success:raise RuntimeError(f'No valid whole block {round_index+1}/{backend}/{name} after {args.max_attempts} attempts')
    expected=rounds*len(groups)
    if len(result['accepted_blocks'])!=expected or len(accepted)!=len(VERSIONS)*expected:raise ValueError('Accepted matrix count mismatch')
    if args.mode=='pixels' and 'vollkorn' in args.fonts:
        controls=[]
        for backend in args.backends:
            by_font={name:{} for name in args.fonts}
            for record in result['pixel_comparisons']:
                if record['backend']==backend:
                    by_font[record['font']]['master']=record['master_rgba_sha256']
                    by_font[record['font']][record['candidate']]=record['patch_rgba_sha256']
            for name in args.fonts:
                if name!='vollkorn':
                    for version in VERSIONS:
                        controls.append({'backend':backend,'font':name,'version':version,'pixels_differ_from_vollkorn':by_font[name][version]!=by_font['vollkorn'][version]})
        result['font_override_controls']=controls;checkpoint(output,result,accepted)
        if not all(row['pixels_differ_from_vollkorn'] for row in controls):raise ValueError('Font override did not change pixels')
    result['complete']=True;checkpoint(output,result,accepted)
    print(f'Completed {len(result["accepted_blocks"])} multi-version blocks; {len(result["launches"])} total launches: {output}',flush=True)

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,KeyError,subprocess.SubprocessError) as error:
        print(f'Benchmark failed: {error}',file=sys.stderr);sys.exit(1)
