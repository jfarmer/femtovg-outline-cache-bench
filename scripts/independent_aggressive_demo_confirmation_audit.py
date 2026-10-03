#!/usr/bin/env python3
"""Recompute every retained demo-confirmation effect from raw stdout.

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

PHASES = {'demo': {'first_paint': 1, 'warm': 30, 'zoom_in': 12, 'zoom_out': 12, 'pan': 10}}


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
    class IdentityReader:
        metadata_only = True
        skipped_live = []
        def resolve(self,path): return resolve(path)
        def load(self,path): return read(path)
        def check_info(self,record,live=False):
            if not live: check_info(record)
        def info(self,path):
            return {'path':str(path),'bytes':resolve(path).stat().st_size,'sha256':sha(path)}
    def require(ok,message):
        assert ok,message
    def audit_identity(reader, identity):
        for name in ('demo_prepare', 'demo_build', 'active_collector', 'collector_correction_proof'):
            reader.check_info(identity[name])
        prep = reader.load(identity['demo_prepare']['path'])
        build = reader.load(identity['demo_build']['path'])
        require(prep['complete'] and build['complete'] and build['prepare'] == identity['demo_prepare'], 'Demo prepare/build binding differs')
        require(build['compiler'] == identity['compiler'] and build['cargo'] == identity['cargo'], 'Compiler differs')
        require(build['builder'] == prep['driver'], 'Demo preparation/build source differs')
        for field in ('driver','collector','original_collector','ablation_prepare','ablation_build','ablation_independent_audit','native_oracle_prepare','native_oracle_build'):
            reader.check_info(prep[field])
        require(reader.load(prep['ablation_independent_audit']['path'])['complete'], 'Reused runner independent proof incomplete')
        require(set(identity['binaries']) == {'master','final','no_retention'}, 'Reused demo executable set differs')
        require(set(identity['sources']) == {'master','final','no_retention','oracle'}, 'Frozen library set differs')
        def source_infos(root, expected):
            if reader.metadata_only:
                reader.skipped_live.append({'source_root':root,'files':len(expected)})
                return
            real = reader.resolve(root)
            actual = {str(path.relative_to(real)) for path in real.rglob('*') if path.is_file() and 'target' not in path.parts}
            require(actual == set(expected), 'Source file set differs: ' + str(root))
            for name,record in expected.items():
                require(record['path'] == str(Path(root)/name), 'Source record path differs')
                reader.check_info(record)
        for version,entry in prep['libraries'].items():
            require(identity['sources'][version] == entry['files'], 'Library identity differs: '+version)
            source_infos(entry['root'],entry['files'])
        for version,entry in prep['reused'].items():
            require(identity['binaries'][version] == entry['binary'], 'Reused binary binding differs: '+version)
            reader.check_info(entry['binary'],live=True)
            reader.check_info(entry['metadata'])
            source_infos(entry['runner_root'],entry['runner_files'])
        oracle = build['oracle']
        require(oracle['dependency_feature_graph_matches'] is True and identity['oracle_binary'] == oracle['binary'], 'Oracle binding differs')
        for field in ('metadata','reference_metadata','lockfile'):
            reader.check_info(oracle[field])
        reader.check_info(oracle['binary'],live=True)
        require(identity['runner_source'] == {name:record['sha256'] for name,record in prep['demo_source'].items()}, 'Drawing source differs')
        require(identity['shared_common'] == prep['shared_common'], 'Shared common binding differs')
        require(identity['assets'] == {name:record['sha256'] for name,record in prep['assets'].items()}, 'Assets differ')
        source_infos(prep['original_runner_root'],prep['original_runner_files'])
        source_infos(prep['shared_common_root'],prep['shared_common'])
        source_infos(prep['assets_root'],prep['assets'])
        # Cargo.lock is populated at build; its exact bytes are bound separately.
        oracle_source = dict(prep['oracle_runner_files'])
        oracle_source['Cargo.lock'] = oracle['lockfile']
        source_infos(prep['oracle_runner_root'],oracle_source)
        correction = reader.load(identity['collector_correction_proof']['path'])
        require(correction['complete'] and correction['before'] == prep['collector'] and correction['after'] == identity['active_collector'], 'Collector correction binding differs')
        for field in ('before','after','patcher'):
            reader.check_info(correction[field])
        source = reader.resolve(correction['before']['path']).read_text()
        for change in correction['changes']:
            require(source.count(change['old']) == 1, 'Collector correction source no longer applies')
            source = source.replace(change['old'],change['new'])
        require(source == reader.resolve(correction['after']['path']).read_text(), 'Collector changed beyond narrow correction')
        def graph(path):
            metadata = reader.load(path)
            root = metadata['resolve']['root']
            labels = {}
            for package in metadata['packages']:
                name = '<runner>' if package['id']==root else ('femtovg' if package['name']=='femtovg-mechanism-no-retention' else package['name'])
                labels[package['id']] = [name,package['version'],package['source'] or ('<runner>' if package['id']==root else '<femtovg>')]
            nodes = []
            for node in metadata['resolve']['nodes']:
                edges = [[edge['name'],labels[edge['pkg']],sorted(json.dumps(kind,sort_keys=True) for kind in edge['dep_kinds'])] for edge in node['deps']]
                nodes.append([labels[node['id']],sorted(node['features']),sorted(edges)])
            return sorted(nodes)
        baseline = graph(oracle['reference_metadata']['path'])
        require(graph(oracle['metadata']['path']) == baseline, 'Oracle dependency/feature graph differs')
        for entry in prep['reused'].values():
            require(graph(entry['metadata']['path']) == baseline, 'Reused dependency/feature graph differs')
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
        prep = audit_identity(IdentityReader(),meta['identity'])
        identities[mode] = meta['identity']
        factors[mode] = {field:meta[field] for field in ('fonts','dpis','versions','font_files','selection_manifest')}
        assert meta['driver'] == meta['identity']['active_collector']
        check_info(meta['driver'])
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
        assert phases_per_trial == 5
        expected_processes = {(b,f,d,v) for b in range(1,13) for f in meta['fonts'] for d in meta['dpis'] for v in meta['versions']}
        process_rows = {}
        aggregate = []
        for launch in meta['launches']:
            key = launch['block'], launch['font'], launch['dpi'], launch['version']
            assert key in expected_processes and key not in process_rows
            assert launch['validated'] and launch['exit_code'] == 0
            assert launch['command'] == [meta['identity']['binaries'][key[3]]['path'],mode,str(meta['trials_per_process']),str(key[2])]
            assert launch['environment'] == {'FEMTOVG_REPLAY_TEXT_FONT':meta['font_files'][key[1]]['path']}
            assert launch['cwd'] == str(Path(meta['identity']['demo_prepare']['path']).parent)
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
            'demo_source_metadata_bound':True, 'live_source_font_binary_rgba_checks_in_completed_analysis':True,
            'auditor_sha256':sha(Path(__file__)),'summary_sha256':sha(analysis/'summary.json')}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('complete','endpoint_comparisons','interval_comparisons','control_advantages')}))


if __name__ == '__main__':
    main()
