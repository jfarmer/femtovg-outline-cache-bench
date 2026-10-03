#!/usr/bin/env python3
"""Check provenance and the complete chronological cold matrix; no bootstrap."""
import collections
import hashlib
import json
from pathlib import Path
from verify import graph

ROOT = Path(__file__).resolve().parent
CAMPAIGN = ROOT / 'cold-genericrestore'
OUT = ROOT / 'provisional-cold-provenance'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if (OUT / 'PROVENANCE.json').exists():
        raise SystemExit('Refusing to overwrite completed provenance results.')
    OUT.mkdir(exist_ok=True)
    immutable = {name: sha(CAMPAIGN / name) for name in ['metadata.json', 'raw.jsonl', 'EXCLUDED.md']}
    meta = json.loads((CAMPAIGN / 'metadata.json').read_text())
    raw_lines = (CAMPAIGN / 'raw.jsonl').read_text().splitlines(keepends=True)
    records = [json.loads(line) for line in raw_lines]
    selected = [r for r in records if 0 <= r['block'] <= 7]
    excluded = [r for r in records if r['block'] > 7]
    fonts = ['Arial', 'RobotoFlex', 'Vollkorn', 'PTSans']
    features = ['swash_only', 'default_swash']
    variants = ['master', 'base', 'finalgenericrestore']
    workloads = [f'cold_{layout}_{phase}' for layout in ['labels', 'para'] for phase in ['natural', 'onephase']]
    workloads += ['grid_singleton', 'grid_two_phases', 'grid_unique_sizes', 'grid_pollution']
    configs = [(f, w, n) for f in features for w in workloads for n in fonts]
    configs += [(f, 'grid_unique_variations', 'RobotoFlex') for f in features]
    assert len(configs) == 66 and len(selected) == 1584
    expected = []
    for block in range(8):
        config_order = configs[block % len(configs):] + configs[:block % len(configs)]
        variant_order = variants[block % len(variants):] + variants[:block % len(variants)]
        if block % 2:
            variant_order = list(reversed(variant_order))
        expected.extend((block, f, w, n, v) for f, w, n in config_order for v in variant_order)
    actual = [(r['block'], r['feature'], r['workload'], r['font'], r['variant']) for r in selected]
    assert actual == expected, 'Incomplete, duplicate or reordered selected matrix'
    assert all(r['block'] == 8 for r in excluded), 'Unexpected additional chronology'
    assert records[:1584] == selected, 'Selected records are not the full chronological prefix'
    assert meta['cold_samples_per_process'] == 7 and meta['variants'] == variants
    for name, record in meta['fonts'].items():
        assert sha(Path(record['path'])) == record['sha256'], f'Changed font {name}'
    for name, digest in meta['harness_files'].items():
        assert sha(ROOT / 'harness-src' / name) == digest, f'Changed harness {name}'
    builds = []
    graphs = {}
    for feature in features:
        for variant in variants:
            label = f'{variant}-{feature}'
            record = json.loads((ROOT / 'builds' / f'{label}.json').read_text())
            executable = record['executables']['cold']
            assert sha(Path(executable['binary_path'])) == executable['binary_sha256'] == meta['binaries'][label]
            expected_origin = str(ROOT / 'source' / variant)
            assert record['source_manifest'] == expected_origin
            assert record['femtovg_artifact']['manifest_path'] == expected_origin + '/Cargo.toml'
            normalized = graph(json.loads((ROOT / 'builds' / f'{label}.metadata.json').read_text()))
            assert feature not in graphs or normalized == graphs[feature], 'Different resolved dependency/features graph'
            graphs.setdefault(feature, normalized)
            frozen = json.loads((ROOT / f'source-{variant}.json').read_text())['files']
            for path in ['src/lib.rs', 'src/text.rs', 'src/text/font.rs', 'src/text/swash_rasterizer.rs']:
                if path in frozen:
                    assert sha(ROOT / 'source' / variant / path) == frozen[path]
                else:
                    assert not (ROOT / 'source' / variant / path).exists()
            builds.append({'label': label, 'binary_sha256': executable['binary_sha256'], 'source_manifest': expected_origin,
                           'source_manifest_sha256': sha(ROOT / f'source-{variant}.json'), 'production_files': {path: frozen.get(path) for path in ['src/lib.rs', 'src/text.rs', 'src/text/font.rs', 'src/text/swash_rasterizer.rs']},
                           'rustc': record['rustc'], 'profile': record['profile'], 'features': record['femtovg_artifact']['features'],
                           'dependency_graph_sha256': hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()})
    assert len({json.dumps(b['profile'], sort_keys=True) for b in builds}) == 1
    assert len({b['rustc'] for b in builds}) == 1
    metric_rows = []
    for feature, workload, font in configs:
        rows = [r for r in selected if (r['feature'], r['workload'], r['font']) == (feature, workload, font)]
        frames = {r['metrics']['frames'] for r in rows}
        glyphs = {r['metrics']['glyphs'] for r in rows}
        assert len(frames) == len(glyphs) == 1
        frame_count = int(next(iter(frames)))
        glyph_count = int(next(iter(glyphs)))
        expected_frames = {'grid_singleton': 1, 'grid_two_phases': 2, 'grid_unique_sizes': 32, 'grid_unique_variations': 32, 'grid_pollution': 67}.get(workload, 1)
        assert frame_count == expected_frames
        if workload.startswith('grid_'):
            assert glyph_count == frame_count * 94
        for record in rows:
            metric = record['metrics']
            assert abs(metric['med_ns_per_glyph'] - metric['ns_total'] / glyph_count) <= 0.00501
            assert abs(metric['med_ns_per_frame'] - metric['ns_total'] / frame_count) <= 0.00501
            assert abs(metric['med_us_per_frame'] - metric['med_ns_per_frame'] / 1000) < 1e-9
            assert abs(metric['med_us_total'] - metric['ns_total'] / 1000) < 1e-9
            expected_binary = str(ROOT / 'bin' / f'{record["variant"]}-{feature}-cold')
            assert record['command'] == [expected_binary, workload, meta['fonts'][font]['path'], '1' if font == 'RobotoFlex' else '0', '7']
        metric_rows.append({'feature': feature, 'workload': workload, 'font': font, 'complete_blocks': list(range(8)), 'variants': variants,
                            'process_records': len(rows), 'frames_per_complete_sequence': frame_count, 'glyph_requests_per_complete_sequence': glyph_count,
                            'metric_identity': 'ns_total is median complete-sequence time across seven fresh samples; per-frame and per-glyph costs divide that total, rounded to0.01ns; totals remain unrounded integer ns'})
    result = {'status': 'post hoc provisional provenance check; not a new measurement or bootstrap',
              'selection': 'All complete chronological blocks0..7 of earliest cold-genericrestore only; partial block8 excluded; no other campaigns merged; no selection by measured effect.',
              'selected_process_records': len(selected), 'excluded_partial_process_records': len(excluded), 'total_original_process_records': len(records),
              'selected_original_line_range_zero_based': [0, 1583], 'selected_original_bytes_sha256': hashlib.sha256(''.join(raw_lines[:1584]).encode()).hexdigest(),
              'selected_complete_configurations': len(configs), 'blocks': list(range(8)), 'samples_per_process': 7,
              'immutable_original_files_sha256': immutable, 'fonts': meta['fonts'], 'harness_files': meta['harness_files'], 'builds': builds, 'configurations': metric_rows,
              'limits': 'Original guard checked process names before each configuration, not continuously or after every process. Background activity may have occurred between checks. User later confirmed external build still running. Chronological-prefix analysis is explicitly post hoc/provisional; eight blocks rather than planned twelve; no GPU, layout or window timing. Original EXCLUDED status is preserved.'}
    for name, digest in immutable.items():
        assert sha(CAMPAIGN / name) == digest, f'Original campaign artifact changed: {name}'
    (OUT / 'PROVENANCE.json').write_text(json.dumps(result, indent=2) + '\n')
    report = ['Provisional chronological cold-prefix provenance; no bootstrap or new measurements.', '',
              'All66configurations ×8completeblocks ×3variants are present exactly once, in the original planned rotating/reversing order:1,584 selected process records. The174 partial block8 records remain excluded. No other campaign is merged and original EXCLUDED.md/metadata/raw hashes are unchanged.', '',
              'All six frozen cold executable hashes, four font hashes, four harness hashes, source origins and production hashes match their retained manifests. Resolved dependency/features graphs match per feature configuration; compiler/profile is identical. Complete-sequence and per-frame/per-glyph metric identities were checked for every selected process.', '',
              '| Features | Workload | Font | Samples/process | Frames/sequence | Glyph requests/sequence | Complete paired blocks |', '|---|---|---|---:|---:|---:|---|']
    report.extend(f'| {r["feature"]} | {r["workload"]} | {r["font"]} |7|{r["frames_per_complete_sequence"]}|{r["glyph_requests_per_complete_sequence"]}|0–7|' for r in metric_rows)
    report.extend(['', result['limits']])
    (OUT / 'REPORT.md').write_text('\n'.join(report) + '\n')
    print('Verified all66 configurations/8 complete blocks/3 variants, metrics, frozen binaries/fonts/harnesses, source origins and original-artifact immutability. No bootstrap performed.')

if __name__ == '__main__':
    main()
