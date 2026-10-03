#!/usr/bin/env python3
"""Recompute every retained font-confirmation effect directly from raw stdout.

Independent of both collection and analysis modules. Archive verification must
check all archive members first; this audit then checks raw/statistical/metadata
bindings. Compiled binaries and RGBA bodies are not required by this offline
mathematical audit. The completed live analysis audits those inputs separately.
"""
import argparse
from collections import defaultdict, Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import statistics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--path-map', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    mappings = json.loads(args.path_map.read_text()) if args.path_map else {}
    mappings = sorted(mappings.items(), key=lambda x: -len(x[0]))
    checked = {}
    def resolve(path):
        text = str(path)
        for old, new in mappings:
            if text == old or text.startswith(old.rstrip('/') + '/'):
                return Path(new + text[len(old):])
        return Path(text)
    def sha(path):
        with resolve(path).open('rb') as stream:
            return hashlib.file_digest(stream, 'sha256').hexdigest()
    def check_info(record):
        assert resolve(record['path']).stat().st_size == record['bytes']
        assert sha(record['path']) == record['sha256'], record['path']
        checked[record['path']] = record['sha256']
    def read(path):
        return json.loads(resolve(path).read_text())
    def near(a, b):
        assert math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-6), (a,b)
    root = args.root.resolve()
    summary = read(root / 'analysis/summary.json')
    assert summary['complete'] and summary['methodology']['bootstrap_resamples'] == 10000
    proof = read(root / 'analysis/raw-audit.json')
    assert proof['complete'] and not proof['metadata_only']
    selection = read(root / 'selection-frozen.json')
    assert selection['complete'] and selection['confirmation']['versions'] == ['master','final']
    for file, digest in selection['selection_inputs'].items():
        assert sha(root / file) == digest, file
    indices_file = read(root / 'analysis/bootstrap-indices.json')
    values, backend_proofs, bootstrap = {}, {}, {}
    metrics = ('draw_us','submit_us','complete_us')
    for mode in ('cpu','gpu'):
        meta = read(root / f'confirm-{mode}/{mode}-provenance.json')
        assert meta['complete'] and not meta['exploratory']
        assert meta['blocks'] == 12 and meta['trials_per_process'] == (5 if mode == 'cpu' else 3)
        assert meta['versions'] == ['master','final']
        expected_processes = {(b,f,d,v) for b in range(1,13) for f in meta['fonts'] for d in meta['dpis'] for v in meta['versions']}
        process_rows = {}
        aggregate = []
        for launch in meta['launches']:
            key = launch['block'], launch['font'], launch['dpi'], launch['version']
            assert key in expected_processes and key not in process_rows
            assert launch['validated'] and launch['exit_code'] == 0
            check_info(launch['stdout_info']); check_info(launch['stderr_info'])
            raw = list(csv.DictReader(resolve(launch['stdout']).open()))
            assert len(raw) == 28 * meta['trials_per_process']
            seen = set()
            for row in raw:
                k = int(row['trial']), row['scene'], row['phase']
                assert k not in seen and 0 <= k[0] < meta['trials_per_process']
                seen.add(k)
                assert int(row['frames']) == meta['phases'][k[1]][k[2]]
                assert all(math.isfinite(float(row[m])) and float(row[m]) >= 0 for m in metrics)
                aggregate.append({'backend':mode,'font':key[1],'dpi':str(key[2]),'block':str(key[0]),'version':key[3],**row})
            assert seen == {(t,s,p) for t in range(meta['trials_per_process']) for s,ps in meta['phases'].items() for p in ps}
            process_rows[key] = raw
            for scene, phases in meta['phases'].items():
                for metric in metrics:
                    for phase, frames in phases.items():
                        sample = [float(r[metric]) for r in raw if r['scene']==scene and r['phase']==phase]
                        endpoint = mode,key[1],key[2],scene,phase,metric
                        values.setdefault(endpoint,{})[key[0],key[3]] = statistics.median(sample)
                    if scene in ('demo','text','font_variations'):
                        totals = [sum(float(r[metric])*int(r['frames']) for r in raw if r['scene']==scene and int(r['trial'])==t)
                                  for t in range(meta['trials_per_process'])]
                        endpoint = mode,key[1],key[2],scene,'reported_sequence',metric
                        values.setdefault(endpoint,{})[key[0],key[3]] = statistics.median(totals)
        assert set(process_rows) == expected_processes
        check_info(meta['results'])
        assert aggregate == list(csv.DictReader(resolve(meta['results']['path']).open()))
        # Two-version crossover must contain six AB and six BA pairs per factor.
        for font in meta['fonts']:
            for dpi in meta['dpis']:
                orders = Counter(tuple(l['version'] for l in meta['launches'] if (l['block'],l['font'],l['dpi'])==(b,font,dpi)) for b in range(1,13))
                assert orders == Counter({('master','final'):6,('final','master'):6})
        # Reference counts and hashes were captured before timing, independently
        # of the master/final performance comparison.
        check_info(meta['pixel_proof'])
        pixels = read(meta['pixel_proof']['path'])
        assert pixels['complete'] and pixels['identity']==meta['identity'] and pixels['font_files']==meta['font_files']
        ledger = {}
        for cfg in pixels['pixel_configurations']:
            for phase in cfg['phases']:
                assert phase['snapshots']['final']['sha256'] == phase['snapshots']['oracle']['sha256']
                assert phase['counts']['final'] == phase['counts']['oracle']
                ledger[cfg['font'],cfg['dpi'],phase['scene'],phase['phase']] = phase['counts']
        assert len(ledger) == len(meta['fonts'])*len(meta['dpis'])*28
        for (block,font,dpi,version), raw in process_rows.items():
            assert all(int(r['new_atlas_entries'])==ledger[font,dpi,r['scene'],r['phase']][version] for r in raw)
        ind = indices_file[mode]
        token = 'font-confirmation/' + mode + '/whole-block/12'
        seed = summary['methodology']['seed'] ^ int.from_bytes(hashlib.sha256(token.encode()).digest()[:8],'big')
        generator = random.Random(seed)
        generated = [[generator.randrange(12) for _ in range(12)] for _ in range(10000)]
        assert ind['token']==token and ind['seed']==seed and generated==ind['indices']
        assert hashlib.sha256(json.dumps(generated,separators=(',',':')).encode()).hexdigest()==ind['indices_sha256']
        bootstrap[mode] = generated
        backend_proofs[mode] = {'processes':len(process_rows),'rows':len(aggregate),'font_DPR_factors':len(meta['fonts'])*len(meta['dpis']),
                                'balanced_AB_BA_orders':True,'native_reference_counts':True,'regenerated_bootstrap_indices':True}
    try:
        import numpy as np
    except ImportError:
        np = None
    def resampled(sample, mode):
        indices = bootstrap[mode]
        if np is not None:
            # Direct indexed averaging, independently of the analyzer's count-
            # weight matrix multiplication.
            return np.asarray(sample)[np.asarray(indices)].mean(axis=1).tolist()
        return [sum(sample[j] for j in row)/12 for row in indices]
    def ci(sample):
        s = sorted(sample)
        result = []
        for fraction in (.025,.975):
            index = fraction*(len(s)-1); low=int(index); alpha=index-low
            result.append((1-alpha)*s[low] + alpha*s[min(low+1,len(s)-1)])
        return result
    visited = set()
    for row in summary['results']:
        key = tuple(row[k] for k in ('backend','font','dpi','scene','phase','metric'))
        assert key in values and key not in visited and row['candidate_version']=='final' and row['reference_version']=='master'
        visited.add(key)
        group=values[key]
        master=[group[b,'master'] for b in range(1,13)]
        final=[group[b,'final'] for b in range(1,13)]
        m,f=statistics.mean(master),statistics.mean(final)
        near(m,row['reference_mean_process_median_us']);near(f,row['candidate_mean_process_median_us'])
        near(m-f,row['mean_paired_savings_us']);near(100*(f/m-1),row['ratio_of_means_change_pct'])
        bm,bf=resampled(master,key[0]),resampled(final,key[0])
        bounds=ci([x-y for x,y in zip(bm,bf)])
        for x,name in zip(bounds,('savings_ci95_low_us','savings_ci95_high_us')):near(x,row[name])
        for x,name in zip(ci([100*(y/x-1) for x,y in zip(bm,bf)]),('ratio_change_ci95_low_pct','ratio_change_ci95_high_pct')):near(x,row[name])
        assert row['classification']==('improvement' if bounds[0]>0 else 'regression' if bounds[1]<0 else 'uncertain')
    assert visited==set(values)
    for row in summary['primary_control_advantage']:
        a=values['cpu',row['font'],2,'demo','first_paint','draw_us']
        b=values['cpu',row['control_font'],2,'demo','first_paint','draw_us']
        differences=[a[n,'master']-a[n,'final']-b[n,'master']+b[n,'final'] for n in range(1,13)]
        near(statistics.mean(differences),row['mean_additional_paired_savings_us'])
        bounds=ci(resampled(differences,'cpu'))
        for x,y in zip(bounds,row['additional_savings_ci95_us']):near(x,y)
        assert row['classification']==('larger_savings' if bounds[0]>0 else 'smaller_savings' if bounds[1]<0 else 'uncertain')
    result={'complete':True,'scope':'Independent direct raw/stdout process medians, weighted trial sequences, paired mean effects, direct-indexed bootstrap intervals and control advantages; no collector/analyzer imports.',
            'backends':backend_proofs,'endpoint_comparisons':len(visited),'interval_comparisons':2*len(visited)+len(summary['primary_control_advantage']),
            'control_advantages':len(summary['primary_control_advantage']),'checked_raw_metadata_files':len(checked),
            'compiled_binaries_not_required':True,'archive_integrity_prerequisite':'Offline caller verifies every retained member (including RGBA/font/source bytes) before this audit.',
            'auditor_sha256':sha(Path(__file__)),'summary_sha256':sha(root/'analysis/summary.json')}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('complete','endpoint_comparisons','interval_comparisons','control_advantages')}))


if __name__ == '__main__':
    main()
