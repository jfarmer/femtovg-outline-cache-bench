#!/usr/bin/env python3
"""Recompute every retained localized-confirmation effect from raw stdout.

Independent of both collection and analysis modules. Archive verification must
check all archive members first; this audit then checks raw/statistical/metadata
bindings. Compiled binaries and RGBA bodies are not required by this offline
mathematical audit. The completed live analysis audits those inputs separately.
"""
import argparse
from collections import defaultdict, Counter
import csv
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import random
import statistics

PHASES = {
    'demo': {'first_paint': 1, 'warm': 30, 'zoom_in': 12, 'zoom_out': 12, 'pan': 10},
    'text': {'first_paint': 1, 'warm': 30, 'x_advance': 10, 'x_return': 10,
             'y_advance': 10, 'size_advance': 12, 'size_return': 12, 'reflow': 3},
    'font_variations': {'first_paint': 1, 'warm': 30, 'weight_advance': 6,
                        'weight_return': 6, 'slant_advance': 10, 'slant_return': 10},
    'grid_singleton': {'once': 1}, 'grid_two_phases': {'first': 1, 'second': 1},
    'grid_unique_sizes': {'sweep': 32}, 'grid_unique_variations': {'sweep': 32},
    'grid_pollution': {'hot_first': 1, 'hot_second': 1, 'pollution': 64, 'hot_return': 1},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--cpu', type=Path)
    parser.add_argument('--gpu', type=Path)
    parser.add_argument('--analysis', type=Path)
    parser.add_argument('--selection', type=Path)
    parser.add_argument('--control-font')
    parser.add_argument('--collector-fix-proof', type=Path,
                        help='Bind an explicitly preserved Path-normalization collector correction')
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
    analysis = args.analysis.resolve() if args.analysis else root / 'analysis'
    summary = read(analysis / 'summary.json')
    assert summary['complete'] and summary['methodology']['bootstrap_resamples'] == 10000
    proof = read(analysis / 'raw-audit.json')
    assert proof['complete'] and not proof['metadata_only']
    indices_file = read(analysis / 'bootstrap-indices.json')
    modes = tuple(mode for mode in ('cpu', 'gpu') if summary['methodology']['inputs'].get(mode) is not None)
    assert 'cpu' in modes and set(proof['backends']) == set(modes)
    assert set(indices_file) == set(modes)
    mode_roots = {'cpu': args.cpu.resolve() if args.cpu else root / 'confirm-cpu',
                  'gpu': args.gpu.resolve() if args.gpu else root / 'confirm-gpu'}

    def normalized_graph(metadata):
        # Separate implementation of the source/build graph normalization.
        by_id = {package['id']: package for package in metadata['packages']}
        root_id = metadata['resolve']['root']
        labels = {identifier: ['<runner>' if identifier == root_id else package['name'], package['version'],
                              package['source'] or ('<runner>' if identifier == root_id else '<femtovg>')]
                  for identifier, package in by_id.items()}
        nodes = []
        for node in metadata['resolve']['nodes']:
            edges = [[edge['name'], labels[edge['pkg']], sorted(json.dumps(kind, sort_keys=True) for kind in edge['dep_kinds'])]
                     for edge in node['deps']]
            nodes.append([labels[node['id']], sorted(node['features']), sorted(edges)])
        return sorted(nodes)

    identities, factors = {}, {}
    def localized_identity(identity):
        check_info(identity['prepare_provenance']); check_info(identity['build_provenance'])
        prep = read(identity['prepare_provenance']['path'])
        built = read(identity['build_provenance']['path'])
        assert prep['complete'] and built['complete']
        assert built['prepare'] == identity['prepare_provenance']
        assert built['builder'] == prep['driver']
        for field in ('driver', 'collector', 'analyzer', 'workload', 'original_build', 'original_oracle_prepare'):
            check_info(prep[field])
        original = read(prep['original_build']['path'])
        native = read(prep['original_oracle_prepare']['path'])
        workload = read(prep['workload']['path'])
        assert original['complete'] and native['complete'] and workload['complete']
        assert workload['old_runner_source'] == original['runner_source']
        common = {name[len('tests/common/'):]: digest for name, digest in original['variants']['master']['pure_source_files'].items() if name.startswith('tests/common/')}
        assert prep['shared_common']['files'] == common == native['common_files']
        # These tiny external helper files are required source bytes, not binaries.
        for name, digest in common.items():
            assert sha(Path(prep['shared_common']['root']) / name) == digest
        assert identity['compiler'] == built['compiler'] and identity['cargo'] == built['cargo']
        assert identity['scope'] == prep['scope'] and identity['locale'] == prep['locale'] == workload['locale']
        assert identity['assets'] == prep['assets']
        assert set(identity['sources']) == set(prep['variants']) == set(built['variants']) == {'master','final','oracle'}
        assert set(identity['binaries']) == {'master','final'}
        for version in ('master', 'final', 'oracle'):
            p, b = prep['variants'][version], built['variants'][version]
            assert b['complete'] and b['graph'] == p['reference_graph']
            expected = native['oracle_files'] if version == 'oracle' else original['variants'][version]['timed_source_files']
            assert p['library_files'] == expected
            assert identity['sources'][version] == {'library_root':p['library'],'library_files':p['library_files'],
                                                     'runner_root':p['runner'],'runner_files':p['runner_files']}
            check_info(p['reference_metadata']); check_info(b['metadata'])
            assert normalized_graph(read(p['reference_metadata']['path'])) == normalized_graph(read(b['metadata']['path'])) == b['graph']
            binary = identity['oracle_binary'] if version == 'oracle' else identity['binaries'][version]
            assert binary == b['binary']
        assert native['original_master_files'] == original['variants']['master']['timed_source_files']
        assert native['changed_files'] == ['src/text.rs']
        return prep

    values, backend_proofs, bootstrap = {}, {}, {}
    metrics = ('draw_us','submit_us','complete_us')
    for mode in modes:
        metadata_path = mode_roots[mode] / f'{mode}-provenance.json'
        assert summary['methodology']['inputs'][mode]['sha256'] == sha(metadata_path)
        meta = read(metadata_path)
        assert meta['complete'] and not meta['exploratory']
        assert meta['blocks'] == 12 and meta['trials_per_process'] == (5 if mode == 'cpu' else 3)
        assert meta['versions'] == ['master','final']
        assert meta['phases'] == PHASES
        assert meta['backend'] == meta['mode'] == mode
        assert len(set(meta['fonts'])) == len(meta['fonts']) and len(set(meta['dpis'])) == len(meta['dpis']) and 2 in meta['dpis']
        assert set(meta['font_files']) == set(meta['fonts'])
        prep = localized_identity(meta['identity'])
        identities[mode] = meta['identity']
        factors[mode] = {field:meta[field] for field in ('fonts','dpis','versions','font_files','selection_manifest')}
        if meta['driver'] != prep['collector']:
            # Prepared Rust, binary, workload, and build proofs remain unchanged.
            # Accept only the explicitly preserved Python Path coercion, with
            # original/fixed bytes checked against its independent correction log.
            assert args.collector_fix_proof is not None, 'Changed collector requires --collector-fix-proof'
            correction = read(args.collector_fix_proof)
            assert correction['complete']
            changes = [entry for entry in correction['changes'] if entry['locale'] == prep['locale']]
            assert len(changes) == 1
            change = changes[0]
            assert change['original'] == prep['collector']['path']
            assert change['original_sha256'] == prep['collector']['sha256']
            assert change['fixed'] == meta['driver']['path']
            assert change['fixed_sha256'] == meta['driver']['sha256']
            check_info(meta['driver'])
            original_source = resolve(change['original']).read_bytes()
            fixed_source = resolve(change['fixed']).read_bytes()
            marker = b'def files(root):\n'
            assert original_source.count(marker) == 1
            assert fixed_source == original_source.replace(marker, marker + b'    root = Path(root)\n')
            checked[str(args.collector_fix_proof)] = sha(args.collector_fix_proof)
        assert meta['selection_manifest'] is not None
        check_info(meta['selection_manifest'])
        selection_path = args.selection.resolve() if args.selection else Path(meta['selection_manifest']['path'])
        assert sha(selection_path) == meta['selection_manifest']['sha256']
        selection = read(selection_path)
        assert selection['complete'] and selection['confirmation']['versions'] == meta['versions']
        assert datetime.fromisoformat(selection['frozen_utc']) <= datetime.fromisoformat(meta['created_utc'])
        selected = {font['label']:{k:v for k,v in font.items() if k != 'label'} for font in selection['fonts']}
        assert selected == meta['font_files']
        for file, digest in selection['selection_inputs'].items():
            assert sha(selection_path.parent / file) == digest, file
        phases_per_trial = sum(len(phases) for phases in meta['phases'].values())
        assert phases_per_trial == 28
        expected_processes = {(b,f,d,v) for b in range(1,13) for f in meta['fonts'] for d in meta['dpis'] for v in meta['versions']}
        process_rows = {}
        aggregate = []
        for launch in meta['launches']:
            key = launch['block'], launch['font'], launch['dpi'], launch['version']
            assert key in expected_processes and key not in process_rows
            assert launch['validated'] and launch['exit_code'] == 0
            assert launch['command'] == [meta['identity']['binaries'][key[3]]['path'],mode,str(meta['trials_per_process']),str(key[2])]
            assert launch['environment'] == {'FEMTOVG_REPLAY_TEXT_FONT':meta['font_files'][key[1]]['path']}
            assert launch['cwd'] == str(Path(meta['identity']['prepare_provenance']['path']).parent / 'runtime/core')
            check_info(launch['stdout_info']); check_info(launch['stderr_info'])
            raw = list(csv.DictReader(resolve(launch['stdout']).open()))
            assert len(raw) == phases_per_trial * meta['trials_per_process']
            seen = set()
            for row in raw:
                k = int(row['trial']), row['scene'], row['phase']
                assert k not in seen and 0 <= k[0] < meta['trials_per_process']
                seen.add(k)
                assert int(row['frames']) == meta['phases'][k[1]][k[2]]
                assert all(math.isfinite(float(row[m])) and float(row[m]) >= 0 for m in metrics)
                assert [float(row[m]) for m in metrics] == sorted(float(row[m]) for m in metrics)
                if row['scene'].startswith('grid_'):
                    assert int(row['new_atlas_entries']) == 94 * int(row['frames'])
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
        configurations = [(font,dpi) for dpi in meta['dpis'] for font in meta['fonts']]
        expected_order, expected_keys = [], []
        for block_index in range(12):
            offset = block_index % len(configurations)
            labels = []
            for font,dpi in configurations[offset:] + configurations[:offset]:
                version_order = ('master','final') if (block_index + configurations.index((font,dpi))) % 2 == 0 else ('final','master')
                for version in version_order:
                    labels.append(f'{block_index+1:02}-{font}-dpi{dpi}-{version}')
                    expected_keys.append((block_index+1,font,dpi,version))
            expected_order.append(labels)
        assert meta['order'] == expected_order
        assert [(launch['block'],launch['font'],launch['dpi'],launch['version']) for launch in meta['launches']] == expected_keys
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
        assert len(ledger) == len(meta['fonts'])*len(meta['dpis'])*phases_per_trial
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
    assert all(value == identities['cpu'] for value in identities.values())
    assert all(value == factors['cpu'] for value in factors.values())
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
    control_rows = summary['primary_control_advantage']
    if args.control_font:
        assert args.control_font in selected
        assert {(row['font'], row['control_font']) for row in control_rows} == {(font,args.control_font) for font in selected if font != args.control_font}
        assert len(control_rows) == len(selected) - 1
    for row in control_rows:
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
            'localized_source_metadata_bound':True,
            'auditor_sha256':sha(Path(__file__)),'summary_sha256':sha(analysis/'summary.json')}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('complete','endpoint_comparisons','interval_comparisons','control_advantages')}))


if __name__ == '__main__':
    main()
