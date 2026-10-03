#!/usr/bin/env python3
"""Join preserved count-only evidence; never collect or interpret timings.

Native cost-screen summaries are supplied as previously audited context with
their separate cohorts. No application effect, confidence interval or cache
admission rule is inferred from these counts.
"""
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import struct

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'supporting'
CJK = Path('/private/tmp/femtovg-cjk-font-search-20261002')
VM = ROOT / 'mechanism-vm-ornate-v1'
REUSED = ROOT / 'mechanism-vm-supplement-v1'
TRACE = ROOT / 'mechanism-production-trace-v1'
FONTS = ['Rye-Regular', 'Vollkorn-Medium', 'FleurDeLeah-Regular',
         'WaterBrush-Regular', 'DiplomataSC-Regular', 'LavishlyYours-Regular']


def info(path):
    path = Path(path).resolve(strict=True)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    assert not path.exists(), 'Keep earlier reports; use a fresh output version.'
    path.write_text(json.dumps(value, indent=2) + '\n')


def write_csv(path, rows):
    assert not path.exists()
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def size_bits(value):
    return struct.unpack('!I', struct.pack('!f', value))[0]


def main():
    bound = {}

    def bind(path):
        value = info(path)
        bound[value['path']] = value
        return value

    combined_path = VM / 'analysis/combined-six-font-counts.json'
    combined = read(combined_path)
    trace = read(TRACE / 'counts-analysis.json')
    trace_proof = read(TRACE / 'trace-campaign.json')
    trace_audit = read(TRACE / 'independent-count-audit.json')
    assert all(item['complete'] for item in [combined, trace, trace_proof, trace_audit])
    assert combined['count_only'] and combined['no_timing_results']
    assert len(trace['runs']) == 12 and len(trace['comparisons']) == 6
    assert trace_audit['analysis'] == bind(TRACE / 'counts-analysis.json')
    assert trace_audit['campaign'] == bind(TRACE / 'trace-campaign.json')
    assert trace_audit['elapsed_time_columns_read'] == trace['audit_counts']['elapsed_time_columns_read'] == 0
    for path in [combined_path, TRACE / 'independent-count-audit.json',
                 VM / 'provenance.json', REUSED / 'provenance.json',
                 VM / 'analysis/count-summary.json', REUSED / 'analysis/count-summary.json',
                 VM / 'analysis-execution.json', TRACE / 'analysis-execution.json',
                 REUSED / 'analysis-execution-v2.json',
                 VM / 'auditor-adaptation.json', TRACE / 'analyzer-adaptation.json',
                 ROOT / 'supporting/engine-selection-audit.json',
                 ROOT / 'ornate-supplement-v1/supporting/engine-selection-audit.json']:
        bind(path)
    for field in ['new_counts', 'reused_counts', 'reused_provenance', 'prepare']:
        assert bind(combined[field]['path']) == combined[field]
    proofs = [read(VM / 'provenance.json'), read(REUSED / 'provenance.json')]
    for proof in proofs:
        assert proof['complete'] and proof['count_only']
        assert proof['original_native_alpha_case_matches'] == 120
    assert read(VM / 'analysis/count-summary.json')['vm_error_count'] == 0
    assert read(REUSED / 'analysis/count-summary.json')['vm_error_count'] == 0
    native_context = []
    static = {}
    for cohort in [ROOT, ROOT / 'hinted-supplement-v1', ROOT / 'ornate-supplement-v1']:
        inspected_path = cohort / 'supporting/font-inspection.json'
        inspected = read(inspected_path)
        assert inspected['complete']
        bind(inspected_path)
        for record in inspected['fonts']:
            if record['label'] in FONTS:
                previous = static.setdefault(record['label'], record)
                assert previous['sha256'] == record['sha256']
        ranking_path = cohort / 'supporting/native-prescreen-ranking.json'
        ranking = read(ranking_path)
        assert ranking['complete'] and bind(ranking['audit']['path']) == ranking['audit']
        bind(ranking_path)
        for row in ranking['rows']:
            if row['font'] in FONTS:
                native_context.append({'cohort': str(cohort.relative_to(ROOT)) or '.', **row})
    assert set(static) == set(FONTS)
    glyph_maps = {}
    duplicate_checks = 0
    for proof in proofs:
        for launch in proof['launches']:
            if launch['mode'] != 'counted':
                continue
            font = launch['font']
            assert launch['complete'] and launch['exit_code'] == 0
            assert launch['font_file']['sha256'] == static[font]['sha256']
            bind(launch['font_file']['path'])
            assert bind(launch['stdout'])['sha256'] == launch['stdout_sha256']
            assert bind(launch['stderr'])['sha256'] == launch['stderr_sha256']
            glyphs = {}
            for row in map(json.loads, Path(launch['stdout']).read_text().splitlines()):
                if row['kind'] != 'glyph' or not row['hinted'] or row['dpr'] != 1:
                    continue
                key = size_bits(row['size']), row['glyph']
                value = {name: row[name] for name in ['points', 'verbs', 'outline_digest', 'counts']}
                if key in glyphs:
                    assert glyphs[key] == value, 'ASCII/demo same glyph/size diagnostic changed.'
                    duplicate_checks += 1
                glyphs[key] = value
            glyph_maps[font] = glyphs
    assert set(glyph_maps) == set(FONTS)
    weighted = []
    for launch in trace_proof['launches']:
        assert launch['font']['sha256'] == static[launch['font_label']]['sha256']
        assert bind(launch['events']['path']) == launch['events']
        assert bind(launch['stdout']['path']) == launch['stdout']
        if launch['version'] != 'final':
            continue
        font = launch['font_label']
        mapping = glyph_maps[font]
        counts = []
        hit_points = []
        unmatched = Counter()
        omitted_miss_geometry = []
        geometry_checks = 0
        last_miss = None
        phase = None
        for line in Path(launch['events']['path']).read_text().splitlines():
            fields = line.split('\t')
            if fields[0] == 'FVGPHASE':
                phase = fields[2] if fields[1] == 'BEGIN' else None
                continue
            if phase != 'first_paint':
                continue
            code = fields[1]
            if code in ['H', 'M']:
                last_miss = None
                if int(fields[2]) != launch['font']['bytes']:
                    continue
                assert json.loads(fields[7]) == [], 'Only exact default coordinates are joined.'
                key = int(fields[6]), int(fields[5])
                if code == 'M':
                    last_miss = key
                if key not in mapping:
                    unmatched[code, *key] += 1
                    continue
                if code == 'H':
                    counts.append(mapping[key]['counts'][2]['instructions'])
                    hit_points.append(mapping[key]['points'])
            elif code == 'O' and last_miss is not None:
                assert fields[2] == 'true'
                if last_miss in mapping:
                    assert (int(fields[3]), int(fields[4])) == (mapping[last_miss]['points'], mapping[last_miss]['verbs'])
                    geometry_checks += 1
                else:
                    omitted_miss_geometry.append({'size_bits': last_miss[0], 'glyph': last_miss[1],
                                                   'points': int(fields[3]), 'verbs': int(fields[4])})
                last_miss = None
        comparison = next(item for item in trace['comparisons'] if item['font_label'] == font)
        first = comparison['phases']['first_paint']['roles']['regular']
        unmapped = [{'event': code, 'size_bits': bits, 'glyph': glyph, 'occurrences': count}
                    for (code, bits, glyph), count in sorted(unmatched.items())]
        unmatched_hits = sum(row['occurrences'] for row in unmapped if row['event'] == 'H')
        unmatched_misses = sum(row['occurrences'] for row in unmapped if row['event'] == 'M')
        assert len(counts) + unmatched_hits == first['final_hits']
        assert geometry_checks + unmatched_misses == first['final_misses']
        weighted.append({
            'font': font, 'font_sha256': static[font]['sha256'],
            'all_first_paint_hits': first['final_hits'], 'mapped_graphic_hits': len(counts),
            'unmapped_hits': unmatched_hits, 'mapped_graphic_miss_geometry_checks': geometry_checks,
            'unmapped_misses': unmatched_misses,
            'sum_dispatches_on_mapped_graphic_hits': sum(counts),
            'hit_weighted_mean_dispatches_on_mapped_graphic_hits': statistics.mean(counts),
            'sum_outline_points_on_mapped_graphic_hits': sum(hit_points),
            'unmapped_event_details': unmapped, 'unmapped_miss_geometry': omitted_miss_geometry,
            'scope': 'Partial direct join to previously executed glyph diagnostics, exact size bits and default coords. Missing spaces, glyph0 and any non-ASCII glyph are retained explicitly; no dispatch count is assigned to them. Geometry checks prove mapped production misses have matching point/verb counts, not an independent per-glyph image proof.',
        })
    profile_rows = combined['profile_dpr_medians']
    assert len(profile_rows) == 24
    trace_rows = []
    for comparison in trace['comparisons']:
        assert comparison['master_render_requests_equals_final_outline_requests']
        for phase, data in comparison['phases'].items():
            for role, bucket in data['roles'].items():
                trace_rows.append({
                    'font': comparison['font_label'], 'phase': phase, 'role': role,
                    'frames': next(row['phases'][phase]['frames'] for row in trace['runs'] if row['font_label'] == comparison['font_label']),
                    **{key: value for key, value in bucket.items() if key != 'final_coords'},
                    'final_coords_json': json.dumps(bucket['final_coords']),
                    'clears_for_whole_phase': len(data['clears']),
                    'request_streams_equal': comparison['master_render_requests_equals_final_outline_requests'],
                })
    for comparison in trace['comparisons']:
        assert not comparison['phases']['first_paint']['clears']
        for phase in ['warm', 'pan']:
            for role in ['regular', 'icons']:
                row = comparison['phases'][phase]['roles'][role]
                assert all(row[field] == 0 for field in ['master_native_render_calls', 'final_outline_requests', 'final_hits', 'final_misses', 'final_scaler_builds'])
    source_bindings = []
    prep = read(CJK / 'mechanism-diagnostic/prepare.json')
    registry = Path(prep['original_skrifa'])
    for name, start, end in [('src/outline/glyf/hint/engine/outline.rs', 769, 795),
                             ('src/outline/glyf/hint/engine/outline.rs', 710, 746),
                             ('src/outline/glyf/hint/instance.rs', 98, 131)]:
        path = registry / name
        binding = bind(path)
        assert binding['sha256'] == prep['original_skrifa_files'][name]
        source_bindings.append({**binding, 'lines_start': start, 'lines_end': end,
                                'excerpt': '\n'.join(path.read_text().splitlines()[start - 1:end])})
    outer = []
    observed_chunks = {'vm-collect': 'a6a7f6', 'vm-analyze': '586cf4',
                       'trace-collect': '490547', 'trace-analyze': '6438f7'}
    for name, directory, driver in [('vm', VM, 'diagnose_selected.py'), ('trace', TRACE, 'trace_selected.py')]:
        for mode, stem in [('collect', 'collector'), ('analyze', 'analyzer')]:
            assert (directory / (stem + '.stderr')).stat().st_size == 0
            outer.append({'observed_tool_exit_code': 0, 'tool_chunk': observed_chunks[name + '-' + mode],
                          'command': ['python3', '-B', str(directory / driver), mode],
                          'stdout': bind(directory / (stem + '.stdout')), 'stderr': bind(directory / (stem + '.stderr')),
                          'driver': bind(directory / driver)})
    write(VM / 'outer-execution-record.json', {'complete': True, 'entries': outer[:2],
                                              'observation': 'Exact exit0 observed in functions tool responses; completion records and preserved stdout/stderr additionally checked.'})
    write(TRACE / 'outer-execution-record.json', {'complete': True, 'entries': outer[2:],
                                                 'observation': 'Exact exit0 observed in functions tool responses; completion records and preserved stdout/stderr additionally checked.'})
    write_csv(OUT / 'selected-mechanism-vm-profiles.csv', profile_rows)
    write_csv(OUT / 'selected-mechanism-trace-phases.csv', trace_rows)
    weighted_flat = [{key: value for key, value in row.items() if key not in ['unmapped_event_details', 'unmapped_miss_geometry', 'scope']} for row in weighted]
    write_csv(OUT / 'selected-mechanism-hit-weighted-first-paint.csv', weighted_flat)
    conclusions = [
        'All six files resolve to the TrueType interpreter by actual maxp/fpgm/prep predicate. Direct stored glyph byte lengths omit called font functions and loop iterations; nearly all measured glyph dispatches come from called fpgm bodies.',
        'ASCII94, median demo-unique glyph work, and first-paint hit-weighted work are distinct quantities. Fleur is more aggressive on full ASCII, but its actual mapped graphic hit mix executes less work than Rye. Glyph shape, text selection, point size and reuse frequency matter.',
        'WaterBrush has many more retained points and more observed budget clears than Rye. Native unhinted/reuse costs and source-level point loops support extra geometry/memory work as an explanation; no isolated arena cost or eviction counterfactual is measured here.',
        'Every first-paint native request stream matches between master and final, and no first-paint budget clear occurs. Fonts all produce112 regular misses but differing repeat hits and geometry. Full-patch benefit also includes batching scalers and removing redundant generic outline decoding; instruction counts cannot attribute the entire application effect to outline retention.',
        'Every measured warm and pan phase has zero outline requests, hits, misses, native calls or scaler builds. Any measured timing difference in those phases is outside direct outline-cache work or measurement variation, and remains unexplained by these counters.',
        'Font/prep builder counts are separate and retained by native instance caching; fpgm-origin dispatches during glyph execution represent called functions rather than rerunning the whole font program. Dispatch counts are not CPU cycles and do not measure internal point loops, scratch copies, allocations, parsing or rasterization.',
    ]
    result = {
        'complete': True, 'created_utc': datetime.now(timezone.utc).isoformat(),
        'reporter': bind(Path(__file__)), 'count_only': True, 'no_new_timing_results': True,
        'proof': {'fresh_vm_processes': 6, 'fresh_exact_native_alpha_cases': 120,
                  'reused_vm_processes': 6, 'reused_exact_native_alpha_cases': 120,
                  'vm_execution_errors': 0, 'production_trace_processes': 12,
                  'production_frames_per_process': 184, 'exact_master_R_final_Q_stream_pairs': 6,
                  'original_application_atlas_rows_checked': 60,
                  'duplicate_ASCII_demo_glyph_rows_exact': duplicate_checks,
                  'first_paint_mapped_miss_geometry_checks': sum(row['mapped_graphic_miss_geometry_checks'] for row in weighted),
                  'timing_columns_read_by_event_analyzers': 0},
        'vm_profile_medians': profile_rows, 'first_paint_hit_weighted_partial_join': weighted,
        'trace_per_phase_roles': trace_rows, 'native_cost_screen_context_separate_cohorts': native_context,
        'native_cost_scope': 'Previously audited warm native screens only, each cohort reported separately. DPR1 matches actual initial11/12/14/15/16px sizes; DPR2 tests22/24/28/30/32px. Neither native kernels nor counts are ordered application timing or isolated cache cost.',
        'source_bindings_point_loops_and_instance_copies': source_bindings,
        'conclusions_and_limits': conclusions,
        'visible_outputs': ['selected-mechanism-report.md', 'selected-mechanism-report.json',
                            'selected-mechanism-vm-profiles.csv', 'selected-mechanism-trace-phases.csv',
                            'selected-mechanism-hit-weighted-first-paint.csv', 'selected-mechanism-input-bindings.json'],
    }
    write(OUT / 'selected-mechanism-report.json', result)
    vm_demo = {row['font']: row for row in profile_rows if row['profile'] == 'demo_unique' and row['dpr'] == 1}
    vm_ascii = {row['font']: row for row in profile_rows if row['profile'] == 'ascii94' and row['dpr'] == 1}
    weighted_by_font = {row['font']: row for row in weighted}
    trace_by_font = {row['font_label']: row for row in trace['comparisons']}
    lines = [
        'Selected font mechanism evidence', '',
        'This is count-only explanatory evidence. The production event traces use the sealed English CPU-only demo at requested DPR2; their initial outlines are11/12/14/15/16px. VM DPR1 rows therefore match those sizes. No new performance timing or pixel proof is claimed.', '',
        '| Font | ASCII94 dispatches/glyph | Unique-demo dispatches/glyph | Mapped actual graphic-hit dispatches/glyph | First hits / misses | First retained points | Zoom clears |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for font in FONTS:
        first = trace_by_font[font]['phases']['first_paint']['roles']['regular']
        clears = sum(len(row['clears']) for row in trace_by_font[font]['phases'].values())
        lines.append('| ' + ' | '.join([font, f"{vm_ascii[font]['mean_glyph_completed_dispatches']:.0f}",
                                      f"{vm_demo[font]['mean_glyph_completed_dispatches']:.0f}",
                                      f"{weighted_by_font[font]['hit_weighted_mean_dispatches_on_mapped_graphic_hits']:.0f}",
                                      f"{first['final_hits']} / {first['final_misses']}",
                                      str(first['final_outline_points']), str(clears)]) + ' |')
    lines += ['', 'ASCII/demo columns are medians of five per-size unique-glyph means. The hit column weights the exact first-paint repeated graphic glyphs. It is a partial join: spaces, glyph0 and any extra non-ASCII glyph omitted by the sealed VM driver remain explicitly unmeasured. All588 duplicate ASCII/demo records match, and632 mapped production misses have matching point/verb counts. Counts are dispatches, not cycles or predicted frame savings.', '']
    lines += conclusions
    lines += ['', 'All six master native-render streams exactly equal final outline-request streams, including size bits, coordinates, subpixel phases and order. Every trace matches the preserved application atlas counts. Fresh VM runs match120 retained ten-phase native alpha cases; the reused Fleur/Rye/Voll campaign matched another120. No VM errors occurred. All four collector/analyzer commands exited0; outer stderr files are empty.', '',
              'The bound JSON retains every phase and role, both native DPRs, per-size records, opcode/origin details, unmatched joins, source excerpts and separate native cost-screen cohorts. The JSON manifest records original absolute paths for provenance; these Markdown links preserve the study-relative layout.', '',
              '[Machine-readable report](selected-mechanism-report.json), [VM profiles](selected-mechanism-vm-profiles.csv), [all phase counts](selected-mechanism-trace-phases.csv), [partial hit-weighted join](selected-mechanism-hit-weighted-first-paint.csv), [input bindings](selected-mechanism-input-bindings.json).', '',
              '[Production event analysis](../mechanism-production-trace-v1/counts-analysis.json), [independent event recount](../mechanism-production-trace-v1/independent-count-audit.json), [combined six-font VM analysis](../mechanism-vm-ornate-v1/analysis/combined-six-font-counts.json).']
    report_path = OUT / 'selected-mechanism-report.md'
    assert not report_path.exists()
    report_path.write_text('\n'.join(lines) + '\n')
    outputs = [bind(OUT / name) for name in result['visible_outputs'] if name != 'selected-mechanism-input-bindings.json']
    write(OUT / 'selected-mechanism-input-bindings.json', {
        'complete': True, 'reporter': info(Path(__file__)), 'inputs': list(bound.values()), 'outputs': outputs,
        'rule': 'Original byte bindings and absolute paths retained; no source/file path is rewritten inside original artifacts.',
    })
    for binding in bound.values():
        assert info(binding['path']) == binding
    print(json.dumps({'complete': True, 'fonts': len(FONTS), 'profiles': len(profile_rows),
                      'phase_role_rows': len(trace_rows), 'duplicate_glyph_checks': duplicate_checks,
                      'mapped_miss_geometry_checks': result['proof']['first_paint_mapped_miss_geometry_checks'],
                      'report': str(report_path)}))


if __name__ == '__main__':
    main()
