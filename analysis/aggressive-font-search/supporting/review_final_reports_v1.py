#!/usr/bin/env python3
"""Bind the final prose review to already completed, immutable analyses.

This checks report transcription and scope. It does not rerun renderers,
timings, interpreter collection, or the already completed raw-result audits.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path('/private/tmp/femtovg-aggressive-font-search-20261002')
OUT = ROOT / 'supporting/final-report-review-v1.json'


def read(name):
    return json.loads((ROOT / name).read_text())


def info(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def main():
    assert not OUT.exists(), 'Preserve the earlier review; create a new version.'
    main_path = ROOT / 'AGGRESSIVE-FONT-SEARCH.md'
    summary_path = ROOT / 'SUMMARY-AGGRESSIVE-FONT-SEARCH.md'
    main_text = main_path.read_text()
    summary_text = summary_path.read_text()
    results = read('primary-analysis-v1/absolute-results.json')
    audit = read('primary-analysis-v1/independent-audit.json')
    raw = read('primary-analysis-v1/raw-audit.json')
    pixels = read('primary-pixels-v1/pixels-provenance.json')
    mechanism = read('supporting/selected-mechanism-report.json')
    trace = read('mechanism-production-trace-v1/counts-analysis.json')
    assert all(item['complete'] for item in [results, audit, raw, pixels, mechanism, trace])
    assert audit['endpoint_comparisons'] == 90
    assert audit['interval_comparisons'] == 184
    assert audit['control_advantages'] == 4
    names = {'WaterBrush-Regular': 'Water Brush', 'DiplomataSC-Regular': 'Diplomata SC',
             'FleurDeLeah-Regular': 'Fleur de Leah', 'Rye-Regular': 'Rye',
             'Vollkorn-Medium': 'Vollkorn Medium'}
    checked_rows = []
    for record in results['fonts']:
        first = record['first_paint']
        row = '| ' + ' | '.join([names[record['font']],
            f"{first['master_us'] / 1000:.3f} ms", f"{first['final_us'] / 1000:.3f} ms",
            f"{first['saved_us'] / 1000:.3f} ms [{first['saved_ci95_us'][0] / 1000:.3f}, {first['saved_ci95_us'][1] / 1000:.3f}]"]) + ' |'
        assert row in main_text and row in summary_text, record['font']
        seq = record['reported_sequence']
        seq_text = f"{seq['saved_us'] / 1000:.3f} ms [{seq['saved_ci95_us'][0] / 1000:.3f}, {seq['saved_ci95_us'][1] / 1000:.3f}]"
        assert seq_text in main_text
        for phase in ['warm', 'pan']:
            low, high = record[phase]['saved_ci95_us']
            assert low <= 0 <= high, (record['font'], phase)
        checked_rows.append({'font': record['font'], 'first_paint_table_matches': True,
                             'sequence_table_matches': True, 'warm_pan_intervals_include_zero': True})
    assert len(checked_rows) == 5
    configurations = pixels['pixel_configurations']
    assert len(pixels['launches']) == 15 and len(configurations) == 5
    checked_captures = 0
    for config in configurations:
        assert len(config['phases']) == 5
        for phase in config['phases']:
            assert phase['native_matches_original_master']
            assert phase['original_master_changed_pixels'] == 0
            assert set(phase['snapshots']) == {'master', 'final', 'oracle'}
            assert len({item['sha256'] for item in phase['snapshots'].values()}) == 1
            checked_captures += 3
    assert checked_captures == 75
    assert mechanism['proof']['duplicate_ASCII_demo_glyph_rows_exact'] == 588
    assert mechanism['proof']['vm_execution_errors'] == 0
    assert 'These counts are for the replaced regular font' in main_text
    assert 'matching point/verb counts' in main_text
    assert 'unhinted construction is measured as a separate control' in main_text
    assert 'conditional on selection' in main_text
    assert 'not a CPU-cycle estimate' in main_text
    weighted_expected = {'Rye-Regular': (137, 365278), 'DiplomataSC-Regular': (134, 351692),
                         'WaterBrush-Regular': (141, 316957), 'Vollkorn-Medium': (132, 273091),
                         'FleurDeLeah-Regular': (134, 271951)}
    for item in mechanism['first_paint_hit_weighted_partial_join']:
        font = item['font']
        if font in weighted_expected:
            assert (item['mapped_graphic_hits'], item['sum_dispatches_on_mapped_graphic_hits']) == weighted_expected[font]
            expected = f"| {names[font]} | {item['mapped_graphic_hits']} | {item['sum_dispatches_on_mapped_graphic_hits']:,} |"
            assert expected in main_text
    bound_names = ['write_final_report.py', 'primary-analysis-v1/absolute-results.json',
        'primary-analysis-v1/summary.json', 'primary-analysis-v1/summary.csv',
        'primary-analysis-v1/independent-audit.json', 'primary-analysis-v1/raw-audit.json',
        'primary-selection-v1/selection.json', 'primary-selection-v1/protocol.json',
        'primary-pixels-v1/pixels-provenance.json', 'supporting/selected-mechanism-report.json',
        'supporting/selected-mechanism-report.md', 'supporting/selected-mechanism-input-bindings.json',
        'supporting/selected-mechanism-hit-weighted-first-paint.csv',
        'mechanism-production-trace-v1/counts-analysis.json',
        'mechanism-production-trace-v1/independent-count-audit.json',
        'mechanism-vm-supplement-v1/analysis/count-overview.csv',
        'mechanism-vm-ornate-v1/analysis/combined-six-font-counts.json',
        'hinted-supplement-v1/supporting/native-prescreen-ranking.json',
        'supporting/native-prescreen-ranking.json', 'ornate-supplement-v1/supporting/native-prescreen-ranking.json']
    result = {'complete': True, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'reviewer_source': info(Path(__file__)), 'reports': [info(main_path), info(summary_path)],
        'inputs': [info(ROOT / name) for name in bound_names],
        'checked_primary_rows': checked_rows, 'pixel_captures_with_equal_recorded_hashes': checked_captures,
        'scope': 'Prose/source-scope review and transcription checks against completed independent analyses. Existing live raw/source/font/binary/RGBA guards and bootstrap audits are bound, not rerun.',
        'manual_source_review': [
            {'finding': 'Native screen validates freshly hinted geometry against retained hinted geometry, plus bounds and alpha bytes at ten phases; unhinted outlines are a separate timed control.',
             'source': info('/private/tmp/femtovg-font-stress-search-20261002/src/main.rs'), 'lines': '146-200'},
            {'finding': 'CPU replay is headless; common GPU helper also requests no compatible surface and renders to offscreen textures.',
             'source': info('/private/tmp/femtovg-updated-cache-bench-20261002/runtime/core/snapshots/master/tests/common/mod.rs')},
            {'finding': 'First-paint 268/156/112/39-style request counts refer to the regular font role; fixed fonts are recorded separately.',
             'source': info(ROOT / 'mechanism-production-trace-v1/counts-analysis.json')},
            {'finding': 'The partial production/VM join checks mapped miss point/verb counts; full native/count geometry and duplicate glyph digests are separate checks.',
             'source': info(ROOT / 'supporting/report_selected_mechanism.py')}
        ],
        'limits': ['Selection-conditional, unadjusted intervals on one machine/workload.',
                   'Warm/pan zero-inclusive intervals do not establish equivalence or zero overhead.',
                   'Glyph dispatches exclude preparation/rasterization and are not CPU cycles or attributed elapsed savings.',
                   'No new rendering, timing, or production source changes occurred in this review.'],
        'result': 'Report data and methodological scope match bound completed evidence after the noted prose corrections.'}
    OUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'complete': True, 'output': info(OUT), 'primary_rows': len(checked_rows),
                      'recorded_pixel_capture_hashes': checked_captures, 'bound_inputs': len(bound_names)}))


if __name__ == '__main__':
    main()
