#!/usr/bin/env python3
"""Summarize multi-version process blocks, retaining all observations."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys

from run import PHASES, VERSIONS, parse_rows, validate_block

ROOT = Path(__file__).resolve().parent
METRICS = ('draw_us','submit_us','complete_us')
COMPARISONS = tuple([('master',v) for v in VERSIONS[1:]]+[('current',v) for v in VERSIONS[2:]]) + (('route','final'),)


def percentile(values,q):
    values=sorted(values)
    position=(len(values)-1)*q
    lo,hi=math.floor(position),math.ceil(position)
    return values[lo]+(values[hi]-values[lo])*(position-lo)


def interval(values):
    return [percentile(values,.025),percentile(values,.975)]


def read_mode(root,mode):
    metadata=json.loads((root/f'{mode}-provenance.json').read_text())
    if not metadata.get('complete') or metadata['versions'] != list(VERSIONS):
        raise ValueError(f'{mode} batch incomplete or not multi-version experiment')
    expected_processes=metadata['blocks']*len(metadata['fonts'])*len(metadata['dpis'])*len(VERSIONS)
    launches=metadata['launches']
    if len(launches)!=expected_processes or any(not row.get('validated') or row.get('exit_code')!=0 for row in launches):
        raise ValueError(f'{mode} contains missing/unvalidated processes')
    expected_launches={(block,font,dpi,version) for block in range(1,metadata['blocks']+1)
                       for font in metadata['fonts'] for dpi in metadata['dpis'] for version in VERSIONS}
    launch_keys=[(row['block'],row['font'],row['dpi'],row['version']) for row in launches]
    if set(launch_keys)!=expected_launches or len(set(launch_keys))!=len(launch_keys):
        raise ValueError(f'{mode} process factors are incomplete/duplicate')
    with (root/f'{mode}-results.csv').open() as stream:
        rows=list(csv.DictReader(stream))
    expected_rows=sum(row['rows'] for row in launches)
    if len(rows)!=expected_rows:
        raise ValueError(f'{mode} CSV row count differs from raw processes')
    # Re-parse every raw stdout and compare it with the indexed CSV. This is a
    # read-only validation, so invalid or incomplete batches cannot accidentally
    # become summaries after editing the aggregate CSV.
    indexed=defaultdict(list)
    for row in rows:
        indexed[int(row['block']),row['font'],int(row['dpi']),row['version']].append(row)
    blocks=defaultdict(dict)
    for launch in launches:
        key=(launch['block'],launch['font'],launch['dpi'],launch['version'])
        raw=parse_rows(Path(launch['stdout']).read_text(),metadata['trials_per_process'])
        aggregate=[{k:v for k,v in row.items() if k not in ('backend','font','dpi','block','version')} for row in indexed[key]]
        if raw!=aggregate:
            raise ValueError(f'aggregate differs from retained stdout: {key}')
        blocks[key[:3]][key[3]]=raw
    for values in blocks.values():
        validate_block(values)
    return metadata,rows


def metric_summary(rows,metric,reference,candidate,blocks,trials,resamples,indices):
    processes=defaultdict(dict)
    all_values=defaultdict(list)
    for row in rows:
        key=(int(row['block']),row['version'])
        trial=int(row['trial'])
        if trial in processes[key]:
            raise ValueError(f'duplicate trial in process: {key}')
        value=float(row[metric])
        if not math.isfinite(value) or value<=0:
            raise ValueError(f'invalid metric: {metric}/{key}/{value}')
        processes[key][trial]=value
        all_values[row['version']].append(value)
    expected={(block,version) for block in range(1,blocks+1) for version in VERSIONS}
    if set(processes)!=expected or any(set(values)!=set(range(trials)) for values in processes.values()):
        raise ValueError('missing/extra trials or process blocks')
    medians={key:statistics.median(values.values()) for key,values in processes.items()}
    pairs=[]
    for block in range(1,blocks+1):
        a,b=medians[block,reference],medians[block,candidate]
        pairs.append({'block':block,'reference':a,'candidate':b,'delta_us':b-a,
                      'candidate_over_reference_ratio':b/a,'change_pct':100*(b/a-1)})
    deltas=[row['delta_us'] for row in pairs]
    percentages=[row['change_pct'] for row in pairs]
    boot_delta=[statistics.median(deltas[i] for i in sample) for sample in indices]
    boot_pct=[statistics.median(percentages[i] for i in sample) for sample in indices]
    return {
        'reference_version':reference,'candidate_version':candidate,
        'reference_median':statistics.median(all_values[reference]),
        'candidate_median':statistics.median(all_values[candidate]),
        'reference_process_median':statistics.median(row['reference'] for row in pairs),
        'candidate_process_median':statistics.median(row['candidate'] for row in pairs),
        'paired_delta_us':statistics.median(deltas),
        'paired_delta_us_ci95':interval(boot_delta) if indices else None,
        'paired_delta_pct':statistics.median(percentages),
        'paired_bootstrap95':interval(boot_pct) if indices else None,
        'process_blocks':blocks,'trials_per_process':trials,'samples_per_version':blocks*trials,
        'bootstrap_resamples':resamples if indices else 0,'pairs':pairs,
    }


def write_csv(path,rows):
    if not rows:
        raise ValueError('cannot write an empty summary')
    with path.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True,help='completed measurement output directory')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--modes',choices=('cpu','gpu'),nargs='+',default=['cpu','gpu'])
    parser.add_argument('--bootstrap',type=int,default=10000)
    parser.add_argument('--seed',type=int,default=72531)
    args=parser.parse_args()
    if args.bootstrap<1:
        parser.error('bootstrap must be positive')
    root=args.root.resolve(strict=True)
    output=args.output.resolve() if args.output else root/'analysis'
    output.mkdir(parents=True,exist_ok=True)
    summaries=[]
    flat=[]
    pair_rows=[]
    provenance={}
    for mode in args.modes:
        if not (root/f'{mode}-provenance.json').exists():
            continue
        metadata,data=read_mode(root,mode)
        provenance[mode]=metadata
        groups=defaultdict(list)
        for row in data:
            groups[row['font'],int(row['dpi']),row['scene'],row['phase']].append(row)
        expected=len(metadata['fonts'])*len(metadata['dpis'])*sum(len(phases) for phases in PHASES.values())
        if len(groups)!=expected:
            raise ValueError(f'{mode} has missing/extra phase configurations')
        for (font,dpi,scene,phase),rows in sorted(groups.items()):
            counts={(int(row['frames']),int(row['new_atlas_entries'])) for row in rows}
            if len(counts)!=1:
                raise ValueError(f'workload counts differ across blocks/versions: {font}/{dpi}/{scene}/{phase}')
            frames,atlas=next(iter(counts))
            entry={'backend':mode,'font':font,'dpi':dpi,'scene':scene,'phase':phase,
                   'frames':frames,'new_atlas_entries':atlas,'comparisons':[]}
            token=f'{mode}/{font}/{dpi}/{scene}/{phase}'
            seed=args.seed ^ int.from_bytes(hashlib.sha256(token.encode()).digest()[:8],'big')
            rng=random.Random(seed)
            blocks=metadata['blocks']
            # A sampled index identifies the entire multi-version block. Shared
            # draws across all reference comparisons and all cumulative metrics retain
            # within-block dependence instead of treating candidates separately.
            indices=[[rng.randrange(blocks) for _ in range(blocks)] for _ in range(args.bootstrap)] if blocks>=3 else []
            for reference,candidate in COMPARISONS:
                comparison={'reference_version':reference,'candidate_version':candidate}
                for metric in METRICS:
                    values=metric_summary(rows,metric,reference,candidate,blocks,
                        metadata['trials_per_process'],args.bootstrap,indices)
                    comparison[metric]=values
                    pair_rows.extend({**{key:entry[key] for key in ('backend','font','dpi','scene','phase')},
                        'metric':metric,'reference_version':reference,'candidate_version':candidate,**pair} for pair in values['pairs'])
                    flat.append({**{key:entry[key] for key in ('backend','font','dpi','scene','phase','frames','new_atlas_entries')},
                        'metric':metric,**{key:value for key,value in values.items() if key!='pairs'}})
                entry['comparisons'].append(comparison)
            summaries.append(entry)
    if not summaries:
        raise ValueError('no completed timing batches found')
    (output/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    write_csv(output/'summary.csv',flat)
    write_csv(output/'paired-processes.csv',pair_rows)
    methodology={
        'bootstrap_resamples':args.bootstrap,'seed':args.seed,'versions':list(VERSIONS),'comparisons':COMPARISONS,
        'pairing':'Median across trials per child process, then pair all versions within block/font/DPR/phase',
        'effect':'Median paired candidate-minus-reference microseconds and median paired 100*(candidate/reference-1) percent; negative means faster',
        'intervals':'Percentile bootstrap of whole multi-version blocks, using shared block indices across comparisons and cumulative metrics; linearly interpolated 2.5/97.5 percentiles; no CI below three blocks',
        'absolute_values':'All per-trial phase averages pooled for marginal medians; process-median absolutes also recorded',
        'scope':'Exploratory intervals across 28 phases and reference comparisons, without multiplicity adjustment; Roboto control repetitions across font factors are not independent font evidence',
        'retention':'All validated processes/trials from completed batches included; retained raw stdout re-parsed and matched against aggregate CSV; no outlier removal',
        'units':'Microseconds per frame, averaged within phase/trial; draw/submit/complete cumulative and not additive',
        'provenance_files':{mode:str(root/f'{mode}-provenance.json') for mode in provenance},
    }
    if (root/'pixels-provenance.json').exists():
        pixels=json.loads((root/'pixels-provenance.json').read_text())
        methodology['pixels']={'complete':pixels.get('complete',False),'comparisons':len(pixels['pixel_comparisons']),
            'identical_comparisons':sum(row['rgba_identical'] for row in pixels['pixel_comparisons']),
            'font_override_controls':pixels.get('font_override_controls',[])}
    (output/'summary-methodology.json').write_text(json.dumps(methodology,indent=2)+'\n')
    print(f'Wrote {len(summaries)} phase configurations, {len(flat)} comparison metrics, {len(pair_rows)} block comparisons to {output}')


if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,KeyError) as error:
        print(f'Summary failed: {error}',file=sys.stderr)
        sys.exit(1)
