#!/usr/bin/env python3
"""Independent raw first/search renderer-thread CPU statistics and paired CIs.

No benchmark/analyzer imports, Rust builds, app launches or windows. Recompute CIs
only after measurements because the recorded bootstrap performs substantial CPU work.
"""
import argparse,datetime,json,math
from collections import defaultdict
from pathlib import Path
from independent_audit_math import median,close,draws,interval,token_seed,digest,pairs,declared_pairs
from benchlib import read_path_map
METRICS=('first_frame.render.thread_cpu_ms','search_frame.render.thread_cpu_ms')

def raw_frame_cpu(sample,marker):
    spans=sample['slint_internal_spans'];markers=[span for span in spans if span['name']==marker]
    assert len(markers)==1,('marker count',marker,len(markers))
    at=markers[0]['start_ns']
    frames=[span for span in spans if span['name']=='femtovg.render' and span['start_ns']<=at<=span['start_ns']+span['duration_ns']]
    assert len(frames)==1,('enclosing render frame count',marker,len(frames))
    frame=frames[0];lo=frame['start_ns'];hi=lo+frame['duration_ns']
    counters=[span for span in spans if span['name']=='femtovg.render.thread_cpu_ns' and lo<=span['start_ns'] and span['start_ns']+span['duration_ns']<=hi]
    assert len(counters)==1,('renderer CPU counter count',marker,len(counters))
    amount=counters[0]['amount'];assert math.isfinite(amount) and amount>=0
    return amount/1_000_000

def williams(versions):
    n=len(versions);base=[0]+[(i+1)//2 if i%2 else n-i//2 for i in range(1,n)]
    rows=[tuple(versions[(value+rotation)%n] for value in base) for rotation in range(n)]
    if n%2:rows += [tuple(reversed(row)) for row in rows]
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',type=Path,required=True)
    parser.add_argument('--analysis',type=Path,required=True,help='analyzer output directory or summary.json')
    parser.add_argument('--experiment',type=Path,required=True)
    parser.add_argument('--ci',choices=('none','all'),default='all')
    parser.add_argument('--ci-pair',nargs=2,action='append',metavar=('REFERENCE','CANDIDATE'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--path-map',type=Path,help='Verified historical-root to materialized-root map')
    parser.add_argument('--archived-binaries',action='store_true',help='Validate recorded executable identity; compressed records omit compiled binaries')
    args=parser.parse_args();batch=args.batch.resolve(strict=True);resolve_path=read_path_map(args.path_map)
    manifest_path=batch/'summary.json';manifest=json.loads(manifest_path.read_text())
    analysis_path=args.analysis/'summary.json' if args.analysis.is_dir() else args.analysis
    analysis=json.loads(analysis_path.read_text());experiment=json.loads(args.experiment.read_text())
    versions=experiment['versions'];comparisons=pairs(versions);orders=williams(versions)
    assert manifest['complete'] and manifest['mode']=='cpu' and manifest['versions']==versions
    comparisons=declared_pairs(versions,analysis['statistics']['comparisons'])
    expected={(backend,font,round_) for backend in manifest['backends'] for font in manifest['fonts'] for round_ in range(1,manifest['rounds']+1)}
    assert len(manifest['accepted_blocks'])==len(expected)
    seen=set();launches=manifest['launches'];by_label={launch['label']:launch for launch in launches}
    assert len(by_label)==len(launches)
    fingerprints={str(manifest_path):digest(manifest_path),str(analysis_path):digest(analysis_path)}
    if args.archived_binaries:
        build=json.loads(resolve_path(manifest['build_provenance']['path']).read_text())
        assert build['complete'] and set(build['variants'])==set(versions)
        binary_hashes={version:build['variants'][version]['binary']['sha256'] for version in versions}
        assert all(build['variants'][v]['binary']['path']==manifest['binaries'][v]['path'] for v in versions)
    else:
        binary_hashes={version:digest(info['path']) for version,info in manifest['binaries'].items()}
    assert all(binary_hashes[v]==manifest['binaries'][v]['sha256'] for v in versions)
    source_values={};queries={}
    for launch in launches:
        assert launch['version'] in versions and launch['exit_code']==0
        path=resolve_path(launch['report']);report=json.loads(path.read_text());fingerprints[str(path)]=digest(path)
        assert len(report['samples'])==1
        sample=report['samples'][0]
        assert Path(sample['executable_path']).resolve()==Path(manifest['binaries'][launch['version']]['path']).resolve()
        assert sample['backend_requested']==launch['backend']
        events=[event for event in sample['events'] if event['event']=='interactive_frame_rendered']
        assert len(events)==1;queries[launch['label']]=events[0]['details']['query']
        source_values[launch['label']]={METRICS[0]:raw_frame_cpu(sample,'first_frame_rendered'),METRICS[1]:raw_frame_cpu(sample,'interactive_frame_rendered')}
    grouped=defaultdict(list);accepted_labels=set();retry_count=0
    for block in manifest['accepted_blocks']:
        key=block['backend'],block['font'],block['round']
        assert key in expected and key not in seen;seen.add(key)
        assert 1<=block['attempt']<=manifest['max_attempts']
        all_attempts=[launch for launch in launches if (launch['backend'],launch['font'],launch['round'])==key]
        assert len(all_attempts)==len(versions)*block['attempt']
        for attempt in range(1,block['attempt']+1):
            raw=[launch for launch in all_attempts if launch['attempt']==attempt]
            assert len(raw)==len(versions) and tuple(launch['version'] for launch in raw)==orders[(block['round']+attempt-2)%len(orders)]
            contaminated=[launch for launch in raw if queries[launch['label']]!='a']
            if attempt<block['attempt']:
                retry_count+=1;assert contaminated
                assert all(not launch.get('included') and launch.get('exclusion_reason','').startswith('Whole block excluded: ') for launch in raw)
            else:
                assert not contaminated and set(block['labels'])=={launch['label'] for launch in raw}
                assert all(launch['included'] and launch['validated'] for launch in raw)
                group={launch['version']:{'round':block['round'],'attempt':attempt,'values':source_values[launch['label']],'label':launch['label']} for launch in raw}
                grouped[key[:2]].append(group);accepted_labels.update(block['labels'])
    assert seen==expected and accepted_labels=={launch['label'] for launch in launches if launch.get('included')}
    selected=[row for row in analysis['results'] if row['mode']=='cpu' and row['batch']==batch.name and row['metric'] in METRICS]
    index={tuple(row[k] for k in ('backend','font','reference','candidate','metric')):row for row in selected}
    assert len(index)==len(selected)==len(grouped)*len(comparisons)*len(METRICS)
    ci_pairs=set(map(tuple,args.ci_pair)) if args.ci_pair else set(comparisons)
    assert ci_pairs<=set(comparisons)
    records=[];ci_count=0
    for (backend,font),blocks in sorted(grouped.items()):
        blocks.sort(key=lambda group:group['master']['round']);n=len(blocks)
        assert n==manifest['rounds'] and [block['master']['round'] for block in blocks]==list(range(1,n+1))
        seed=token_seed(analysis['statistics']['seed'],f'{batch.name}/{backend}/{font}')
        samples=draws(n,analysis['statistics']['bootstrap_resamples'],seed) if args.ci=='all' and n>=3 else None
        for metric in METRICS:
            for reference,candidate in comparisons:
                a=[block[reference]['values'][metric] for block in blocks];b=[block[candidate]['values'][metric] for block in blocks]
                assert all(value>0 for value in a)
                delta=[new-old for old,new in zip(a,b)];ratios=[new/old for old,new in zip(a,b)]
                row=index[backend,font,reference,candidate,metric]
                expected_values={'reference_median':median(a),'candidate_median':median(b),'median_paired_delta':median(delta),
                    'median_paired_ratio':median(ratios),'median_paired_change_pct':100*(median(ratios)-1)}
                for name,value in expected_values.items():close(row[name],value)
                assert row['n_blocks']==n and len(row['pairs'])==n
                for pair,block,old,new in zip(row['pairs'],blocks,a,b):
                    assert pair['round']==block['master']['round'] and pair['attempt']==block['master']['attempt']
                    for name,value in [('reference',old),('candidate',new),('delta',new-old),('candidate_over_reference_ratio',new/old)]:close(pair[name],value)
                record={'backend':backend,'font':font,'metric':metric,'reference':reference,'candidate':candidate,'n_blocks':n,
                    **expected_values,'ci_independently_checked':False}
                if samples is not None and (reference,candidate) in ci_pairs:
                    pct_interval=[100*(value-1) for value in interval(ratios,samples)];delta_interval=interval(delta,samples)
                    for actual,computed in zip(row['median_paired_change_pct_ci95'],pct_interval):close(actual,computed)
                    for actual,computed in zip(row['median_paired_delta_ci95'],delta_interval):close(actual,computed)
                    ci_count+=1;record.update(ci_independently_checked=True,pct_ci95=pct_interval,delta_ci95=delta_interval,bootstrap_seed=seed)
                records.append(record)
        print(f'Audited {backend}/{font}, {n} whole accepted blocks',flush=True)
    report={'complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'versions':versions,
        'raw_launches':len(launches),'accepted_launches':len(accepted_labels),'accepted_blocks':len(expected),'retry_attempts_revalidated':retry_count,
        'point_effects_recomputed':len(records),'cpu_ci_rows_recomputed':ci_count,'results':records,'input_sha256':fingerprints,
        'binary_verification':'Recorded identity and build-provenance hashes only; compiled executable bytes omitted from archive' if args.archived_binaries else 'Executable bytes independently hashed',
        'auditor_sha256':digest(__file__),'math_helper_sha256':digest(Path(__file__).with_name('independent_audit_math.py')),
        'scope':'Unique raw renderer frames enclosing first/search markers and their unique renderer-thread CPU amount counters; all accepted variants paired within the same round/attempt; retries independently require raw query contamination. Deterministic whole-block percentile bootstrap; exploratory/unadjusted intervals. No runner/analyzer imports.'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Independent raw app CPU audit passed: {len(records)} effects and {ci_count} CIs: {args.output}')
if __name__=='__main__':main()
