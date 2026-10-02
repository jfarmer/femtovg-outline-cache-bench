#!/usr/bin/env python3
"""Revalidate completed multi-version blocks and bootstrap paired comparisons.

Read-only benchmark postprocessing; never launches the app. Every accepted block
is retained. Incomplete batches require an explicit documented exclusion.
"""
import argparse
from collections import defaultdict
import csv
import functools
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
import run as runner
from benchmark_helpers import digest,event_map,file_info

HERE=Path(__file__).resolve().parent
runner.validate_report.__globals__['digest']=functools.lru_cache(maxsize=None)(digest)
VERSIONS=runner.VERSIONS
COMPARISONS=tuple([('master',v) for v in VERSIONS[1:]]+[('current',v) for v in VERSIONS[2:]])+(('route','final'),)
NAMES={'observed_search_response_ms':'Launch to observed search response readiness','first_frame_since_main_ms':'First rendered frame since main',
 'search_frame_since_main_ms':'Search response rendered since main','search_after_first_frame_ms':'First frame to search response',
 'first_callback_wall_ms':'First BeforeRendering to AfterRendering interval','spawn_to_main_ms':'Spawn to main','peak_rss_mib':'Process lifetime peak RSS'}
for phase in ('first_frame','search_frame'):
    for part in ('render','component_items','final_flush'):
        for measure in ('wall','thread_cpu'):NAMES[f'{phase}.{part}.{measure}_ms']=f'{phase} femtovg.{part}, {measure}'

def read(path):return json.loads(Path(path).read_text())
def percentile(values,q):
    values=sorted(values);position=(len(values)-1)*q;lo=math.floor(position);hi=math.ceil(position)
    return values[lo]+(values[hi]-values[lo])*(position-lo)
def ci(values):return [percentile(values,.025),percentile(values,.975)]
def scalar_metrics(sample,frames,mode):
    events=event_map(sample);first=events['first_frame_rendered']['since_main_ms'];search=events['interactive_frame_rendered']['since_main_ms']
    result={'observed_search_response_ms':sample['launch_to_probe_observed_ms'],'first_frame_since_main_ms':first,'search_frame_since_main_ms':search,
      'search_after_first_frame_ms':search-first,'first_callback_wall_ms':first-events['first_render_started']['since_main_ms']}
    if sample.get('spawn_to_main_ms') is not None:result['spawn_to_main_ms']=sample['spawn_to_main_ms']
    if sample.get('peak_rss_bytes') is not None:result['peak_rss_mib']=sample['peak_rss_bytes']/2**20
    if mode=='cpu':
        for phase in ('first_frame','search_frame'):
            for part in ('render','component_items','final_flush'):
                for measure,suffix in [('wall',''),('thread_cpu','.thread_cpu_ns')]:
                    name=f'femtovg.{part}{suffix}'
                    if name not in frames[phase]:raise ValueError(f'Missing {phase} {name}')
                    result[f'{phase}.{part}.{measure}_ms']=frames[phase][name]['ms']
    if any(not math.isfinite(value) or value<0 for value in result.values()):raise ValueError('Negative/nonfinite metric')
    return result

def validate_launch(manifest,launch):
    version=launch['version'];font=manifest['fonts'][launch['font']];binary=manifest['binaries'][version]
    if version not in VERSIONS or launch.get('exit_code')!=0:raise ValueError(f'Failed/unknown-version launch: {launch["label"]}')
    report=read(launch['report'])
    sample,frames,selected,contamination=runner.validate_report(report,Path(binary['path']).resolve(),binary['sha256'],launch['backend'],font,manifest['mode'],manifest['font_event_schema']['event'])
    if frames!=launch['frames'] or selected!=launch['font_configured_event']:raise ValueError(f'Raw frame/font event mismatch: {launch["label"]}')
    if runner.extract_metrics(sample,frames)!=launch['metrics']:raise ValueError(f'Raw metric mismatch: {launch["label"]}')
    return sample,frames,contamination

def load_batch(directory):
    manifest=read(directory/'summary.json')
    if not manifest.get('complete'):raise ValueError(f'Incomplete batch: {directory}')
    if manifest['versions']!=list(VERSIONS):raise ValueError('Unexpected variants/order')
    if file_info(manifest['build_provenance']['path'])!=manifest['build_provenance']:raise ValueError('Build provenance changed')
    for info in [manifest['harness'],*manifest['binaries'].values(),*manifest['inputs'].values(),*[font['file'] for font in manifest['fonts'].values()]]:
        if file_info(info['path'])!=info:raise ValueError(f'Input/binary changed: {info["path"]}')
    if manifest['mode'] not in ('cpu','startup','pixels'):raise ValueError('Unknown mode')
    expected={(backend,font,round_) for backend in manifest['backends'] for font in manifest['fonts'] for round_ in range(1,manifest['rounds']+1)}
    if len(expected)!=len(manifest['accepted_blocks']):raise ValueError('Accepted matrix count mismatch')
    launches=manifest['launches'];by_label={row['label']:row for row in launches}
    if len(by_label)!=len(launches):raise ValueError('Duplicate launch labels')
    accepted_labels=[label for block in manifest['accepted_blocks'] for label in block['labels']]
    if len(accepted_labels)!=len(VERSIONS)*len(expected) or len(set(accepted_labels))!=len(accepted_labels):raise ValueError('Accepted labels invalid')
    if set(accepted_labels)!={r['label'] for r in launches if r.get('included')}:raise ValueError('Included flags differ from blocks')
    groups={};raw=[]
    for block in manifest['accepted_blocks']:
        key=block['backend'],block['font'],block['round']
        if key not in expected or key in groups:raise ValueError('Duplicate/unconfigured block')
        if not 1<=block['attempt']<=manifest['max_attempts']:raise ValueError('Invalid attempt')
        accepted_group={}
        all_attempts=[row for row in launches if (row['backend'],row['font'],row['round'])==key]
        for attempt in range(1,block['attempt']+1):
            rows=[row for row in all_attempts if row['attempt']==attempt]
            if len(rows)!=len(VERSIONS) or {r['version'] for r in rows}!=set(VERSIONS):raise ValueError('Partial/invalid whole attempt')
            actual_order=tuple(row['version'] for row in rows)
            if actual_order!=runner.ORDERS[(block['round']+attempt-2)%len(runner.ORDERS)]:raise ValueError('Version order differs from balanced design')
            contaminated=[]
            for launch in rows:
                sample,frames,contamination=validate_launch(manifest,launch)
                if contamination:contaminated.append(launch['version'])
                if attempt<block['attempt']:
                    if launch.get('included') or not launch.get('exclusion_reason','').startswith('Whole block excluded: '):raise ValueError('Unexplained previous-attempt exclusion')
                else:
                    if launch['label'] not in block['labels'] or launch.get('validated') is not True or contamination:raise ValueError('Invalid accepted block launch')
                    metrics=scalar_metrics(sample,frames,manifest['mode'])
                    row={'batch':directory.name,'mode':manifest['mode'],'backend':key[0],'font':key[1],'family':manifest['fonts'][key[1]]['family'],
                      'round':key[2],'attempt':attempt,'version':launch['version'],'label':launch['label'],'report':launch['report'],'metrics':metrics}
                    accepted_group[launch['version']]=row;raw.append(row)
            if attempt<block['attempt'] and not contaminated:raise ValueError('Excluded an uncontaminated whole block')
        if len(all_attempts)!=len(VERSIONS)*block['attempt']:raise ValueError('Unexpected post-acceptance/raw attempts')
        if set(accepted_group)!=set(VERSIONS):raise ValueError('Incomplete accepted group')
        groups[key]=accepted_group
    if set(groups)!=expected:raise ValueError('Accepted matrix incomplete')
    if manifest['mode']=='pixels':
        seen=set()
        if len(manifest['pixel_comparisons'])!=(len(VERSIONS)-1)*len(expected):raise ValueError('Pixel comparison count mismatch')
        for comparison in manifest['pixel_comparisons']:
            key=comparison['backend'],comparison['font'],1
            pair=key+(comparison['candidate'],)
            if key not in expected or pair in seen or comparison['reference']!='master' or comparison['candidate'] not in VERSIONS[1:]:raise ValueError('Invalid pixel comparison')
            seen.add(pair)
            rebuilt=runner.pixel_comparison(Path(comparison['master_png']['path']),Path(comparison['patch_png']['path']),key[0],key[1])
            rebuilt.update(reference='master',candidate=comparison['candidate'])
            if rebuilt!=comparison or not comparison['rgba_identical']:raise ValueError('Raw pixel comparison mismatch')
    return manifest,groups,raw

def analyze_group(directory,manifest,backend,font,blocks,bootstrap,seed):
    names=set(blocks[0]['master']['metrics'])
    if any(set(block[version]['metrics'])!=names for block in blocks for version in VERSIONS):raise ValueError('Metric sets differ within block matrix')
    rng=random.Random(seed);n=len(blocks);samples=[[rng.randrange(n) for _ in range(n)] for _ in range(bootstrap)] if n>=3 else []
    results=[]
    for reference,candidate in COMPARISONS:
        for name in sorted(names):
            a=[block[reference]['metrics'][name] for block in blocks];b=[block[candidate]['metrics'][name] for block in blocks]
            deltas=[new-old for old,new in zip(a,b)];ratios=[new/old for old,new in zip(a,b)] if all(old>0 for old in a) else None
            delta_ci=ci([statistics.median([deltas[i] for i in indices]) for indices in samples]) if samples else None
            ratio_ci=ci([statistics.median([ratios[i] for i in indices]) for indices in samples]) if samples and ratios else None
            results.append({'batch':directory.name,'mode':manifest['mode'],'backend':backend,'font':font,'family':manifest['fonts'][font]['family'],
              'reference':reference,'candidate':candidate,'metric':name,'description':NAMES[name],'units':'MiB' if name=='peak_rss_mib' else 'ms','n_blocks':n,
              'reference_median':statistics.median(a),'candidate_median':statistics.median(b),'reference_min':min(a),'reference_max':max(a),'candidate_min':min(b),'candidate_max':max(b),
              'median_paired_delta':statistics.median(deltas),'median_paired_delta_ci95':delta_ci,
              'median_paired_ratio':statistics.median(ratios) if ratios else None,'median_paired_change_pct':100*(statistics.median(ratios)-1) if ratios else None,
              'median_paired_change_pct_ci95':[100*(value-1) for value in ratio_ci] if ratio_ci else None,
              'pairs':[{'round':block['master']['round'],'attempt':block['master']['attempt'],'reference':old,'candidate':new,'delta':new-old,'candidate_over_reference_ratio':new/old if old>0 else None} for block,old,new in zip(blocks,a,b)]})
    return results

def write_csv(path,rows,fields):
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('batches',nargs='+',type=Path)
    parser.add_argument('--output',type=Path,default=HERE/'analysis')
    parser.add_argument('--bootstrap',type=int,default=10000)
    parser.add_argument('--seed',type=int,default=72531)
    parser.add_argument('--exclude',nargs=2,action='append',default=[],metavar=('BATCH','REASON'))
    args=parser.parse_args()
    if args.bootstrap<1:parser.error('bootstrap must be positive')
    directories=[path.resolve(strict=True) for path in args.batches];exclusions=[(Path(path).resolve(strict=True),reason) for path,reason in args.exclude]
    if len(set(directories))!=len(directories) or set(directories)&{path for path,_ in exclusions}:parser.error('Included batches must be unique and separate from excluded')
    summary={'statistics':{'observation':'Variant processes in balanced adjacent font/backend/round blocks',
      'effect':'Median within-block candidate-minus-reference delta and candidate/reference ratio; percent=100*(median ratio-1)',
      'ci':'Percentile bootstrap of block median effects; shared resampled block indices across variants and metrics; linear quantile interpolation; no CI for fewer than three blocks',
      'comparisons':[list(pair) for pair in COMPARISONS],'bootstrap_resamples':args.bootstrap,'seed':args.seed,
      'scope':'Exploratory per-metric confidence intervals without multiplicity adjustment; host CPU and observed IPC readiness, not GPU completion/compositor scanout',
      'retention':'All accepted processes; whole-block retry only for contaminated query; revalidate excluded query attempts; no duration/outlier filtering'},
      'analyzer':file_info(Path(__file__)),'batches':[],'excluded_batches':[],'results':[],'pixels':[]}
    raw_rows=[];pair_rows=[];identity=None
    for directory,reason in exclusions:
        manifest=read(directory/'summary.json');summary['excluded_batches'].append({'path':str(directory),'reason':reason,'mode':manifest['mode'],'complete':manifest.get('complete',False),'raw_launches':len(manifest['launches'])})
    for directory in directories:
        manifest,groups,raw=load_batch(directory)
        this_identity={key:manifest[key] for key in ('app_commit','source_variants','binaries','harness','inputs','fonts','backends','build_provenance')}
        if identity is not None and this_identity!=identity:raise ValueError('Application, variant, binary, input, font, or backend identity differs across batches')
        identity=this_identity
        summary['batches'].append({'path':str(directory),**{key:manifest[key] for key in ('mode','rounds','app_commit','source_variants','binaries','harness','inputs','fonts','backends','environment','actual_font_diagnostics','runner','helpers','build_provenance')},
          'raw_launches':len(manifest['launches']),'accepted_launches':len(raw),'accepted_blocks':len(groups),'excluded_attempts':[r for r in manifest['launches'] if not r.get('included')]})
        if manifest['mode']=='pixels':summary['pixels'].extend({'batch':directory.name,**comparison} for comparison in manifest['pixel_comparisons']);continue
        raw_rows.extend(raw)
        for backend,font in sorted({key[:2] for key in groups}):
            blocks=[groups[key] for key in sorted(groups) if key[:2]==(backend,font)]
            seed=args.seed^int.from_bytes(hashlib.sha256(f'{directory.name}/{backend}/{font}'.encode()).digest()[:8],'big')
            rows=analyze_group(directory,manifest,backend,font,blocks,args.bootstrap,seed);summary['results'].extend(rows)
            for row in rows:
                pair_rows.extend({key:row[key] for key in ('batch','mode','backend','font','family','reference','candidate','metric','units')}|{'round':pair['round'],'attempt':pair['attempt'],'reference_value':pair['reference'],'candidate_value':pair['candidate'],'delta':pair['delta'],'candidate_over_reference_ratio':pair['candidate_over_reference_ratio']} for pair in row['pairs'])
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');(output/'launches.json').write_text(json.dumps(raw_rows,indent=2)+'\n')
    fields=('batch','mode','backend','font','family','reference','candidate','metric','units','n_blocks','reference_median','candidate_median','median_paired_delta','median_paired_delta_ci95','median_paired_ratio','median_paired_change_pct','median_paired_change_pct_ci95')
    write_csv(output/'summary.csv',[{key:row[key] for key in fields} for row in summary['results']],fields)
    write_csv(output/'pairs.csv',pair_rows,('batch','mode','backend','font','family','reference','candidate','metric','units','round','attempt','reference_value','candidate_value','delta','candidate_over_reference_ratio'))
    print(f'Wrote {len(summary["results"])} comparisons, {len(raw_rows)} timed launches, {len(summary["pixels"])} pixel comparisons to {output}')
    for row in summary['results']:
        if row['metric'] in ('first_frame.render.thread_cpu_ms','observed_search_response_ms'):
            print(f'{row["mode"]} {row["backend"]} {row["font"]} {row["candidate"]}/{row["reference"]}: {row["metric"]} {row["median_paired_change_pct"]:+.2f}% CI {row["median_paired_change_pct_ci95"]}')

if __name__=='__main__':
    try:main()
    except (OSError,ValueError,RuntimeError,KeyError) as error:
        print(f'Analysis failed: {error}',file=sys.stderr);sys.exit(1)
