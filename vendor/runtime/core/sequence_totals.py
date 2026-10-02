#!/usr/bin/env python3
"""Compare whole reported sequences, summing phase duration before medians.

Controlled scenes are complete sequences. Original examples exclude their 119
unreported warmup frames and are explicitly labelled sums of reported phases.
The script reads retained data only and never launches a benchmark or window.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys

from run import PHASES, VERSIONS
from summarize import COMPARISONS, METRICS, metric_summary, read_mode, write_csv


def totals(rows):
    """Sum frames times per-frame phase duration within each original trial."""
    grouped=defaultdict(dict)
    for row in rows:
        key=(row['font'],int(row['dpi']),row['scene'],int(row['block']),row['version'],int(row['trial']))
        phase=row['phase']
        if phase in grouped[key]:
            raise ValueError(f'duplicate phase in sequence: {key}/{phase}')
        grouped[key][phase]=row
    results=defaultdict(list)
    for (font,dpi,scene,block,version,trial),phases in grouped.items():
        if set(phases)!=set(PHASES[scene]):
            raise ValueError(f'incomplete reported sequence: {font}/{dpi}/{scene}/{block}/{version}/{trial}')
        frames=sum(int(row['frames']) for row in phases.values())
        atlas=sum(int(row['new_atlas_entries']) for row in phases.values())
        expected_frames=sum(PHASES[scene].values())
        if frames!=expected_frames:
            raise ValueError(f'wrong sequence frame count: {scene}/{frames}/{expected_frames}')
        results[font,dpi,scene].append({'block':str(block),'version':version,'trial':str(trial),
            'frames':frames,'new_atlas_entries':atlas,
            **{metric:sum(int(row['frames'])*float(row[metric]) for row in phases.values()) for metric in METRICS}})
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True,help='completed timing output directory')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--modes',choices=('cpu','gpu'),nargs='+',default=['cpu','gpu'])
    parser.add_argument('--bootstrap',type=int,default=10000)
    parser.add_argument('--seed',type=int,default=72531)
    args=parser.parse_args()
    if args.bootstrap<1:
        parser.error('bootstrap must be positive')
    root=args.root.resolve(strict=True)
    output=args.output.resolve() if args.output else root/'sequence-analysis'
    output.mkdir(parents=True,exist_ok=True)
    summary=[]
    flat=[]
    paired=[]
    provenance={}
    for mode in args.modes:
        if not (root/f'{mode}-provenance.json').exists():
            continue
        metadata,rows=read_mode(root,mode)
        provenance[mode]=str(root/f'{mode}-provenance.json')
        sequences=totals(rows)
        if len(sequences)!=len(metadata['fonts'])*len(metadata['dpis'])*len(PHASES):
            raise ValueError(f'{mode}: incomplete sequence/font/DPR factors')
        for (font,dpi,scene),data in sorted(sequences.items()):
            counts={(row['frames'],row['new_atlas_entries']) for row in data}
            if len(counts)!=1:
                raise ValueError(f'frame or atlas counts vary across complete sequences: {font}/{dpi}/{scene}')
            frames,atlas=next(iter(counts))
            scope='complete controlled sequence' if scene.startswith('grid_') else 'sum of reported phases; excludes 119 unreported warmup frames'
            entry={'backend':mode,'font':font,'dpi':dpi,'scene':scene,'scope':scope,
                   'reported_frames':frames,'new_atlas_entries':atlas,'phases':PHASES[scene],
                   'comparisons':[]}
            blocks=metadata['blocks']
            token=f'sequence/{mode}/{font}/{dpi}/{scene}'
            seed=args.seed ^ int.from_bytes(hashlib.sha256(token.encode()).digest()[:8],'big')
            rng=random.Random(seed)
            indices=[[rng.randrange(blocks) for _ in range(blocks)] for _ in range(args.bootstrap)] if blocks>=3 else []
            for reference,candidate in COMPARISONS:
                comparison={'reference_version':reference,'candidate_version':candidate}
                for metric in METRICS:
                    # Values entering metric_summary are already sums within
                    # each trial. It then takes one process median per block.
                    # Taking phase medians first would produce a different and
                    # generally invalid estimate of complete-sequence duration.
                    values=metric_summary(data,metric,reference,candidate,blocks,
                        metadata['trials_per_process'],args.bootstrap,indices)
                    comparison[metric]=values
                    common={key:entry[key] for key in ('backend','font','dpi','scene','scope','reported_frames','new_atlas_entries')}
                    flat.append({**common,'metric':metric,**{key:value for key,value in values.items() if key!='pairs'}})
                    paired.extend({**common,'metric':metric,'reference_version':reference,'candidate_version':candidate,**pair} for pair in values['pairs'])
                entry['comparisons'].append(comparison)
            summary.append(entry)
    if not summary:
        raise ValueError('no complete timing batches found')
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    write_csv(output/'summary.csv',flat)
    write_csv(output/'paired-processes.csv',paired)
    methodology={
        'bootstrap_resamples':args.bootstrap,'seed':args.seed,'versions':list(VERSIONS),'comparisons':COMPARISONS,
        'sequence_aggregation':'For each trial and scene, sum frames*draw_us, frames*submit_us, and frames*complete_us over every reported phase. Then take the median of complete trial sums within each child process, then pair version process medians within blocks.',
        'whole_sequences':'All five controlled scenes are complete sequences. grid_two_phases includes first and second; grid_pollution includes both hot-population phases, all 64 pollution frames, and the hot-return frame.',
        'original_examples':'Labelled sum of reported phases: all 19 original phase rows are included, but each original scene has 119 unreported warmup frames that cannot be reconstructed from retained timing rows. These totals are not complete startup-to-end durations.',
        'interpretation':'Whole-sequence totals include all cache population and pollution work, so an isolated hot-return speedup is not mistaken for a net speedup over the preceding work.',
        'pairing':'All reference comparisons use the same multi-version block. Each process median is computed after trial sums, never by summing phase medians.',
        'intervals':'Percentile bootstrap of whole multi-version blocks, shared indices across all reference comparisons and all three cumulative metrics; no CI below three blocks; exploratory with no multiplicity adjustment.',
        'units':'Microseconds for the entire reported sequence. Draw/submit/complete are cumulative and must not be added. For readability divide totals by 1000 to display milliseconds.',
        'retention':'read_mode revalidates every retained raw stdout against aggregate CSV; all trials/processes in each complete batch retained; no exclusions or timing launches.',
        'provenance_files':provenance,
    }
    (output/'methodology.json').write_text(json.dumps(methodology,indent=2)+'\n')
    print(f'Wrote {len(summary)} sequence configurations, {len(flat)} comparison metrics, {len(paired)} block observations to {output}')


if __name__=='__main__':
    try:
        main()
    except (OSError,ValueError,KeyError) as error:
        print(f'Sequence analysis failed: {error}',file=sys.stderr)
        sys.exit(1)
