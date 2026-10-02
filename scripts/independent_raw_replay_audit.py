#!/usr/bin/env python3
"""Independently audit raw replay matrices, point effects and paired-bootstrap CIs.

No runner/analyzer imports, Rust builds, font parsing, GPU or benchmark launches.
Run after measurement: CI recomputation intentionally performs substantial CPU work.
"""
import argparse,ast,csv,datetime,json,math
from collections import defaultdict
from pathlib import Path
from independent_audit_math import median,close,draws,interval,token_seed,digest,pairs,declared_pairs
from benchlib import read_path_map
resolve_path = Path

METRICS=('draw_us','submit_us','complete_us')
RAW_FIELDS=['scene','phase','trial','frames',*METRICS,'new_atlas_entries']
INDEX_FIELDS=['backend','font','dpi','block','version']
PHASES={
 'demo':{'first_paint':1,'warm':30,'zoom_in':12,'zoom_out':12,'pan':10},
 'text':{'first_paint':1,'warm':30,'x_advance':10,'x_return':10,'y_advance':10,'size_advance':12,'size_return':12,'reflow':3},
 'font_variations':{'first_paint':1,'warm':30,'weight_advance':6,'weight_return':6,'slant_advance':10,'slant_return':10},
 'grid_singleton':{'once':1},'grid_two_phases':{'first':1,'second':1},'grid_unique_sizes':{'sweep':32},
 'grid_unique_variations':{'sweep':32},'grid_pollution':{'hot_first':1,'hot_second':1,'pollution':64,'hot_return':1}}

def read_csv(path,header=None):
    with resolve_path(path).open() as stream:
        reader=csv.DictReader(stream)
        if header is not None:assert reader.fieldnames==header,('unexpected CSV header',path,reader.fieldnames)
        return list(reader)

def validate_raw(root,mode,versions):
    path=root/(mode+'-provenance.json');metadata=json.loads(path.read_text())
    assert metadata['complete'] and metadata['mode']==mode and metadata['versions']==versions
    assert metadata['phases']==PHASES and len(set(metadata['fonts']))==len(metadata['fonts'])
    assert len(set(metadata['dpis']))==len(metadata['dpis'])
    blocks,trials=metadata['blocks'],metadata['trials_per_process']
    expected={(block,font,dpi,version) for block in range(1,blocks+1) for font in metadata['fonts'] for dpi in metadata['dpis'] for version in versions}
    rows=read_csv(root/(mode+'-results.csv'),INDEX_FIELDS+RAW_FIELDS)
    indexed=defaultdict(list)
    for row in rows:
        assert row['backend']==mode
        indexed[int(row['block']),row['font'],int(row['dpi']),row['version']].append(row)
    assert set(indexed)==expected and len(metadata['launches'])==len(expected)
    assert len(rows)==len(expected)*trials*28
    expected_rows={(trial,scene,phase) for trial in range(trials) for scene,phases in PHASES.items() for phase in phases}
    factors=defaultdict(set);seen=set();sources=[path,root/(mode+'-results.csv')]
    for launch in metadata['launches']:
        assert launch['validated'] and launch['exit_code']==0
        key=(launch['block'],launch['font'],launch['dpi'],launch['version'])
        assert key in expected and key not in seen;seen.add(key)
        raw_path=resolve_path(launch['stdout']);sources.append(raw_path)
        raw=read_csv(raw_path,RAW_FIELDS)
        aggregate=[{k:v for k,v in row.items() if k not in INDEX_FIELDS} for row in indexed[key]]
        assert raw==aggregate and len(raw)==28*trials and launch['rows']==len(raw)
        row_keys=[(int(row['trial']),row['scene'],row['phase']) for row in raw]
        assert len(set(row_keys))==len(row_keys) and set(row_keys)==expected_rows
        for row in raw:
            frames,entries=int(row['frames']),int(row['new_atlas_entries'])
            assert frames==PHASES[row['scene']][row['phase']] and entries>=0
            if row['scene'].startswith('grid_'):assert entries==94*frames
            durations=[float(row[metric]) for metric in METRICS]
            assert durations==sorted(durations) and all(math.isfinite(value) and value>=0 for value in durations)
            factors[launch['font'],launch['dpi'],row['scene'],row['phase']].add((frames,entries))
    assert seen==expected and all(len(values)==1 for values in factors.values())
    return metadata,rows,sources

def audit(args):
    root=args.results.resolve(strict=True)
    experiment=json.loads(args.experiment.read_text());versions=experiment['versions'];comparisons=pairs(versions)
    modes=args.modes or [mode for mode in ('cpu','gpu') if (root/(mode+'-provenance.json')).exists()]
    assert modes
    data={};phase_values=defaultdict(dict);sequence_values=defaultdict(dict);fingerprints={};raw_checks=[]
    for mode in modes:
        metadata,rows,sources=validate_raw(root,mode,versions);data[mode]=metadata
        raw_checks.append({'mode':mode,'blocks':metadata['blocks'],'processes':len(metadata['launches']),'phase_rows':len(rows),'trials':metadata['trials_per_process']})
        for path in sources:fingerprints[str(path)]=digest(path)
        for row in rows:
            key=int(row['block']),row['version'],int(row['trial'])
            config=mode,row['font'],int(row['dpi']),row['scene']
            for metric in METRICS:
                phase_values[(*config,row['phase'],metric)][key]=float(row[metric])
                total_key=(*config,metric)
                sequence_values[total_key][key]=sequence_values[total_key].get(key,0)+int(row['frames'])*float(row[metric])
    phase_path=args.phase_summary or root/'analysis/summary.csv'
    sequence_path=args.sequence_summary or root/'sequence-analysis/summary.csv'
    phase_method=phase_path.parent/'summary-methodology.json'
    sequence_method=sequence_path.parent/'methodology.json'
    summaries=[('phase',phase_path,phase_method,phase_values)]
    if sequence_path.exists():summaries.append(('sequence',sequence_path,sequence_method,sequence_values))
    audited=[];point_count=0;ci_count=0
    for kind,path,method_path,values_by_group in summaries:
        method=json.loads(method_path.read_text())
        assert method['versions']==versions
        comparisons=declared_pairs(versions,method['comparisons'])
        ci_pairs=set(map(tuple,args.ci_pair)) if args.ci_pair else set(comparisons)
        assert ci_pairs<=set(comparisons)
        fingerprint_paths=[path,method_path]
        for p in fingerprint_paths:fingerprints[str(p)]=digest(p)
        grouped=defaultdict(list);seen=set()
        for row in read_csv(path):
            mode=row['backend']
            if mode not in modes:continue
            config=mode,row['font'],int(row['dpi']),row['scene']
            phase=row.get('phase');identity=(*config,phase,row['metric'],row['reference_version'],row['candidate_version'])
            assert identity not in seen;seen.add(identity)
            assert (row['reference_version'],row['candidate_version']) in comparisons and row['metric'] in METRICS
            grouped[(*config,phase)].append(row)
        expected_groups=sum(len(m['fonts'])*len(m['dpis'])*(28 if kind=='phase' else len(PHASES)) for m in data.values())
        assert len(grouped)==expected_groups and len(seen)==expected_groups*len(comparisons)*len(METRICS)
        for count,(config,rows) in enumerate(sorted(grouped.items()),1):
            mode,font,dpi,scene,phase=config;metadata=data[mode];n=metadata['blocks'];trials=metadata['trials_per_process']
            token=f'{mode}/{font}/{dpi}/{scene}/{phase}' if kind=='phase' else f'sequence/{mode}/{font}/{dpi}/{scene}'
            seed=token_seed(method['seed'],token)
            samples=draws(n,method['bootstrap_resamples'],seed) if args.ci=='primary' and n>=3 else None
            for row in rows:
                metric=row['metric'];reference,candidate=row['reference_version'],row['candidate_version']
                key=(mode,font,dpi,scene,phase,metric) if kind=='phase' else (mode,font,dpi,scene,metric)
                values=values_by_group[key]
                expected_keys={(block,version,trial) for block in range(1,n+1) for version in versions for trial in range(trials)}
                assert set(values)==expected_keys
                a=[median(values[block,reference,trial] for trial in range(trials)) for block in range(1,n+1)]
                b=[median(values[block,candidate,trial] for trial in range(trials)) for block in range(1,n+1)]
                differences=[new-old for old,new in zip(a,b)];percentages=[100*(new/old-1) for old,new in zip(a,b)]
                expected={'reference_median':median(values[block,reference,trial] for block in range(1,n+1) for trial in range(trials)),
                    'candidate_median':median(values[block,candidate,trial] for block in range(1,n+1) for trial in range(trials)),
                    'reference_process_median':median(a),'candidate_process_median':median(b),
                    'paired_delta_us':median(differences),'paired_delta_pct':median(percentages)}
                for name,value in expected.items():close(row[name],value)
                assert int(row['process_blocks'])==n and int(row['trials_per_process'])==trials
                point_count+=1
                record={'kind':kind,'backend':mode,'font':font,'dpi':dpi,'scene':scene,'phase':phase,'metric':metric,
                    'reference':reference,'candidate':candidate,'n_blocks':n,**expected,'ci_independently_checked':False}
                primary=metric==('draw_us' if mode=='cpu' else 'complete_us')
                if primary and (reference,candidate) in ci_pairs and samples is not None:
                    ci_pct,ci_us=interval(percentages,samples),interval(differences,samples)
                    reported_pct,reported_us=ast.literal_eval(row['paired_bootstrap95']),ast.literal_eval(row['paired_delta_us_ci95'])
                    for actual,computed in zip(reported_pct,ci_pct):close(actual,computed)
                    for actual,computed in zip(reported_us,ci_us):close(actual,computed)
                    ci_count+=1;record.update(ci_independently_checked=True,paired_bootstrap95=ci_pct,paired_delta_us_ci95=ci_us,bootstrap_seed=seed)
                audited.append(record)
            if count%10==0:print(f'Audited {kind} groups {count}/{len(grouped)}',flush=True)
    report={'complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'versions':versions,
        'raw_checks':raw_checks,'point_rows_recomputed':point_count,'primary_ci_rows_recomputed':ci_count,
        'primary_metrics':{'cpu':'draw_us','gpu':'complete_us'},'audited':audited,'input_sha256':fingerprints,
        'auditor_sha256':digest(__file__),'math_helper_sha256':digest(Path(__file__).with_name('independent_audit_math.py')),
        'scope':'Independent raw CSV parsing, complete variant/block/trial matrices, weighted trial sums before process medians, and recorded whole-block percentile bootstrap; no runner/analyzer imports. Intervals exploratory/unadjusted; original scene totals omit unreported warmups.'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Independent replay audit passed: {point_count} point effects, {ci_count} primary CIs: {args.output}')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results',type=Path,required=True)
    parser.add_argument('--experiment',type=Path,default=Path(__file__).with_name('experiment.json'))
    parser.add_argument('--modes',choices=('cpu','gpu'),nargs='+')
    parser.add_argument('--phase-summary',type=Path);parser.add_argument('--sequence-summary',type=Path)
    parser.add_argument('--ci',choices=('none','primary'),default='primary')
    parser.add_argument('--ci-pair',nargs=2,action='append',metavar=('REFERENCE','CANDIDATE'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--path-map',type=Path,help='Verified historical-root to materialized-root map')
    args=parser.parse_args()
    global resolve_path
    resolve_path=read_path_map(args.path_map)
    audit(args)
if __name__=='__main__':main()
