#!/usr/bin/env python3
"""Reconstruct completed proof-sheet studies from stdout; never run binaries.

This script imports neither the campaign runner nor its analysis helpers.
Bootstrap sampling is recreated from uniform indices, matching the declared
unweighted choices protocol, with a fresh seed for every reported interval.
"""
import csv
import datetime as dt
import difflib
import hashlib
import io
import json
from pathlib import Path
import random
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
REPO = Path('/Users/jesse/github/femtovg')
SCENES = Path('/private/tmp/femtovg-review-fixes-scenes')
PERF = Path('/private/tmp/femtovg-review-fixes-perf')
PIN_PATH = Path('/private/tmp/femtovg-current-demo-20261003/provenance/PIN_VERIFICATION.json')
FONTS = ['FleurDeLeah', 'RobotoFlex', 'Rye']
PHASES = [('first_paint', 1), ('warm', 30), ('new_size', 12), ('return', 1)]
HEAD = 'b87a94ddfba46ee67ca35ba240104615ac1503d8'
MASTER = '6a5f15ae55db439a4ed8b1e818c6521029c34fbd'
BENCH_ASSETS = Path('/Users/jesse/github/femtovg-outline-cache-bench/assets')


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest(path):
    return digest_bytes(Path(path).read_bytes())


def read_json(path):
    return json.loads(Path(path).read_text())


def median(values):
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2


def timestamp(value):
    return dt.datetime.fromisoformat(value)


def interval(values):
    # random.choices with no weights selects floor(random() * population_size).
    # Recreating that protocol from indices avoids importing the runner/helper.
    rng = random.Random(61432)
    n = len(values)
    medians = []
    for _ in range(10000):
        sample = [values[int(rng.random() * n)] for _ in range(n)]
        medians.append(median(sample))
    medians.sort()
    return [medians[250], medians[9750]]


def dependency_nodes(path):
    meta = read_json(path)
    packages = {p['id']: p for p in meta['packages']}
    def identity(package_id):
        p = packages[package_id]
        return (p['name'], p['version'], p['source'])
    graph = []
    for node in meta['resolve']['nodes']:
        if node['id'] == meta['resolve']['root']:
            continue
        dependencies = []
        for edge in node['deps']:
            kinds = sorted((k['kind'] or '', str(k['target'] or '')) for k in edge['dep_kinds'])
            dependencies.append((identity(edge['pkg']), kinds))
        graph.append((identity(node['id']), sorted(node['features']), sorted(dependencies)))
    return sorted(graph)


def lock_dependencies(path):
    packages = tomllib.loads(Path(path).read_text())['package']
    return sorted(json.dumps(p, sort_keys=True) for p in packages
                  if not p['name'].startswith('femtovg-review-scenes-'))


def git_file(revision, name):
    return subprocess.check_output(['git', '-C', str(REPO), 'show', f'{revision}:{name}'])


def license_supplement():
    font = BENCH_ASSETS / 'RobotoFlex-VariableFont.ttf'
    ofl = BENCH_ASSETS / 'licenses/RobotoFlex-OFL.txt'
    attribution = BENCH_ASSETS / 'ATTRIBUTION.md'
    legacy = Path('/private/tmp/femtovg-current-demo-20261003/assets/LICENSE-Roboto')
    copied_font = legacy.with_name('RobotoFlex-VariableFont.ttf')
    assert digest(font) == digest(copied_font) == '512f759e24d81543f5629b8edc99c566140a8d161fc2277ac82e64add2f26cf9'
    assert digest(ofl) == '9cbaed04b20c853f99840efe5dc96956f6f6120ed83a0ade35f9281a2b63e5d0'
    assert 'SIL Open Font License, Version 1.1' in ofl.read_text()
    mapping = next(line for line in attribution.read_text().splitlines() if line.startswith('| RobotoFlex-VariableFont.ttf |'))
    assert '[OFL 1.1](licenses/RobotoFlex-OFL.txt)' in mapping
    assert 'Apache License' in legacy.read_text()
    return {'font': {'path': str(font), 'sha256': digest(font)},
        'applicable_license': {'path': str(ofl), 'sha256': digest(ofl), 'license': 'SIL OFL 1.1'},
        'attribution': {'path': str(attribution), 'sha256': digest(attribution), 'mapping_line': mapping},
        'predeclared_legacy_file': {'path': str(legacy), 'sha256': digest(legacy), 'contents': 'Apache 2.0',
                                  'applicable_to_this_RobotoFlex_font': False},
        'original_plans_and_measurements_changed': False,
        'correction': 'The audit verifies the legacy file bytes but does not treat that file as the applicable Roboto Flex license.'}


def provenance():
    pin = read_json(PIN_PATH)
    assert pin['head'] == HEAD and pin['upstream_master'] == MASTER
    identity = read_json(PERF / 'final-runtime-identity.json')
    assert identity['final_commit'] == HEAD
    result = {'pin_sha256': digest(PIN_PATH), 'final_runtime_identity_sha256': digest(PERF / 'final-runtime-identity.json'),
              'master_commit': MASTER, 'final_commit': HEAD, 'variants': {}, 'commit_file_identity': {}}
    builds = {}
    graphs = []
    locks = []
    for variant in ['master', 'final']:
        build = read_json(ROOT / 'builds' / f'{variant}.json')
        builds[variant] = build
        source = build['source']
        directory = Path(source['source_root'])
        assert directory == SCENES / 'source' / variant
        registered = read_json(source['registered_source_record'])
        assert digest(source['registered_source_record']) == source['registered_source_record_sha256']
        expected = {n: h for n, h in registered['files'].items() if Path(n).name != 'Cargo.lock'}
        actual = {str(p.relative_to(directory)): digest(p) for p in directory.rglob('*')
                  if p.is_file() and p.name != 'Cargo.lock'}
        assert actual == expected == source['all_source_files']
        if variant == 'master':
            assert registered['revision'] == MASTER and not registered['working_tree']
        assert digest(build['binary_path']) == build['binary_sha256']
        assert digest(ROOT / 'harness-src/main.rs') == build['harness_sha256']
        assert digest(ROOT / 'harness' / variant / 'Cargo.lock') == build['lock_sha256']
        assert build['lock_sha256'] == digest(SCENES / 'harness' / variant / 'Cargo.lock')
        graph = dependency_nodes(ROOT / 'builds' / f'{variant}.metadata.json')
        assert digest_bytes(json.dumps(graph, sort_keys=True).encode()) == build['dependency_graph_sha256']
        assert graph == dependency_nodes(PERF / 'scene-builds' / f'{variant}-default_swash.metadata.json')
        graphs.append(graph)
        locks.append(lock_dependencies(ROOT / 'harness' / variant / 'Cargo.lock'))
        artifact = build['femtovg_artifact']
        assert artifact['manifest_path'] == str(directory / 'Cargo.toml')
        assert artifact['features'] == ['default', 'image', 'image-loading', 'swash', 'textlayout']
        assert artifact['profile']['opt_level'] == '3' and not artifact['profile']['debug_assertions']
        records = [json.loads(line) for line in (ROOT / 'builds' / f'{variant}.cargo.jsonl').read_text().splitlines()
                   if line.startswith('{')]
        libraries = [r for r in records if r.get('reason') == 'compiler-artifact'
                     and r.get('target', {}).get('name') == 'femtovg']
        assert libraries == [artifact]
        assert records[-1]['reason'] == 'build-finished' and records[-1]['success']
        executables = [r['executable'] for r in records if r.get('reason') == 'compiler-artifact' and r.get('executable')]
        assert len(executables) == 1 and digest(executables[0]) == build['binary_sha256']
        result['variants'][variant] = {'build_record_sha256': digest(ROOT / 'builds' / f'{variant}.json'),
            'binary_sha256': build['binary_sha256'], 'source_files_verified': len(actual),
            'registered_snapshot_revision': registered['revision'], 'snapshot_is_working_tree': registered['working_tree'],
            'compiler_artifact_manifest': artifact['manifest_path'], 'features': artifact['features'],
            'dependency_graph_sha256': build['dependency_graph_sha256'], 'harness_sha256': build['harness_sha256'],
            'lock_sha256': build['lock_sha256']}
    assert graphs[0] == graphs[1] and locks[0] == locks[1]
    for field in ['rustc', 'cargo', 'profile', 'build_environment']:
        assert builds['master'][field] == builds['final'][field]
        result[field] = builds['master'][field]
    for name, entry in pin['production_identity'].items():
        final = (SCENES / 'source/final' / name).read_bytes()
        committed = git_file(HEAD, name)
        assert digest_bytes(final) == entry['frozen_sha256']
        assert digest_bytes(committed) == entry['current_sha256']
        baseline_path = SCENES / 'source/master' / name
        if baseline_path.exists():
            assert baseline_path.read_bytes() == git_file(MASTER, name)
            baseline_identity = 'file bytes match'
        else:
            assert subprocess.check_output(['git', '-C', str(REPO), 'ls-tree', MASTER, '--', name]) == b''
            baseline_identity = 'absent from both baseline and upstream commit'
        whole = final == committed
        if name == 'src/text/swash_rasterizer.rs':
            marker = b'#[cfg(test)]\nmod tests'
            assert marker in final and marker in committed
            before_tests = final.split(marker)[0]
            assert before_tests == committed.split(marker)[0]
            assert digest_bytes(before_tests) == identity['files'][name]['before_test_module_sha256']
            changes = [opcode for opcode in difflib.SequenceMatcher(None, final.splitlines(), committed.splitlines()).get_opcodes()
                       if opcode[0] != 'equal']
            assert len(changes) == 1
            tag, i, j, k, l = changes[0]
            assert tag == 'replace' and j - i == l - k == 2
            assert all(line.strip().startswith(b'///') for line in final.splitlines()[i:j] + committed.splitlines()[k:l])
        else:
            assert whole
        result['commit_file_identity'][name] = {'master_file_identity_6a': baseline_identity, 'final_whole_file_matches_b87': whole,
            'final_released_code_matches_b87': True, 'frozen_sha256': digest_bytes(final), 'committed_sha256': digest_bytes(committed)}
    result['source_revision_label_caveat'] = ('The final snapshot registration predates the squash and says da26832 working tree; '
        'its file hashes, not that stale label, establish released-code identity with b87a94d.')
    result['same_dependencies_features_and_build_conditions'] = True
    return result, builds


def cohort(name, dpi, builds):
    directory = ROOT / name
    plan = read_json(directory / 'PLAN.json')
    complete = read_json(directory / 'COMPLETE.json')
    raw = [json.loads(line) for line in (directory / 'raw.jsonl').read_text().splitlines()]
    stored_summary = read_json(directory / 'summary.json')
    assert plan['blocks'] == 12 and plan['fonts'] == FONTS and plan['dpi'] == dpi
    assert plan['builds'] == builds
    assert plan['runner_sha256'] == digest(ROOT / 'run.py')
    assert plan['phases'] == [list(p) for p in PHASES]
    for field, filename in [('plan_sha256', 'PLAN.json'), ('raw_sha256', 'raw.jsonl'),
                            ('summary_sha256', 'summary.json'), ('report_sha256', 'REPORT.md')]:
        assert complete[field] == digest(directory / filename)
    assert not (directory / 'ABORT.json').exists()
    expected = []
    for block in range(12):
        fonts = FONTS[block % 3:] + FONTS[:block % 3]
        for index, font in enumerate(fonts):
            variants = ['master', 'final'] if (block + index) % 2 == 0 else ['final', 'master']
            expected.extend({'block': block, 'font': font, 'variant': variant} for variant in variants)
    observed = [{k: r[k] for k in ['block', 'font', 'variant']} for r in raw]
    assert observed == expected == plan['process_order'] and len(raw) == 72
    orders = {}
    for font in FONTS:
        pairs = [[r['variant'] for r in raw if r['font'] == font and r['block'] == block] for block in range(12)]
        assert pairs.count(['master', 'final']) == pairs.count(['final', 'master']) == 6
        orders[font] = {'master_then_final': 6, 'final_then_master': 6}
    assert plan['pair_order_counts'] == orders
    assets = {}
    for font in FONTS:
        entry = plan['font_assets'][font]
        assert digest(entry['path']) == entry['sha256']
        for document in plan['font_license_and_acquisition_records'][font]:
            assert digest(document['path']) == document['sha256']
        license_path = plan['font_license_and_acquisition_records'][font][0]['path']
        license_text = Path(license_path).read_text()
        license_name = 'SIL OFL 1.1'
        assert ('Apache License' in license_text) if font == 'RobotoFlex' else ('SIL Open Font License, Version 1.1' in license_text)
        acquired = read_json(plan['font_license_and_acquisition_records'][font][1]['path'])
        if font == 'FleurDeLeah':
            candidate = next(c for c in acquired['candidates'] if c['family'] == 'fleurdeleah')
            asset = next(a for a in candidate['assets'] if a['repository_path'] == candidate['font_repository_path'])
            license_asset = next(a for a in candidate['assets'] if a['repository_path'].endswith('/OFL.txt'))
            assert asset['complete'] and license_asset['complete'] and asset['sha256'] == entry['sha256']
            assert license_asset['sha256'] == digest(license_path)
            origin = {'repository': candidate['source_repository'], 'commit': candidate['source_commit'],
                      'path': candidate['font_repository_path']}
        elif font == 'Rye':
            candidate = next(c for c in acquired['results'] if c['family_directory'] == 'rye')
            asset = next(a for a in candidate['downloads'] if a['source_path'].endswith('/Rye-Regular.ttf'))
            license_asset = next(a for a in candidate['downloads'] if a['source_path'].endswith('/OFL.txt'))
            assert asset['returncode'] == license_asset['returncode'] == 0 and asset['sha256'] == entry['sha256']
            assert license_asset['sha256'] == digest(license_path)
            origin = {'repository': candidate['repository'], 'commit': candidate['commit'], 'path': asset['source_path']}
        else:
            asset = acquired['RobotoFlex-VariableFont.ttf']
            license_asset = acquired['LICENSE-Roboto']
            assert asset['sha256'] == entry['sha256'] and digest(asset['source_path']) == entry['sha256']
            assert license_asset['sha256'] == digest(license_path) == digest(license_asset['source_path'])
            assert digest(SCENES / 'source/master/examples/assets/RobotoFlex-VariableFont.ttf') == entry['sha256']
            origin = {'repository': 'femtovg', 'commit': MASTER, 'path': 'examples/assets/RobotoFlex-VariableFont.ttf'}
        assets[font] = {'font_sha256': entry['sha256'], 'license': license_name,
            'recorded_origin': origin, 'documents': plan['font_license_and_acquisition_records'][font]}
        if font == 'RobotoFlex':
            assets[font]['predeclared_license_file_is_legacy_Apache_not_applicable_RobotoFlex_license'] = True
            assets[font]['applicable_license_supplement'] = 'LICENSE-SUPPLEMENT.json'
    previous_after = timestamp(plan['declared_utc'])
    observations = {}
    weighted_sequences = []
    for r in raw:
        assert r['returncode'] == 0 and r['stderr'] == '' and r['guard_after_status'] == 'idle'
        before, after = timestamp(r['guard_before_utc']), timestamp(r['guard_after_utc'])
        assert previous_after <= before <= after
        previous_after = after
        command = [builds[r['variant']]['binary_path'], plan['font_assets'][r['font']]['path'], 'proofsheet', str(dpi), '1']
        assert r['command'] == command
        rows = list(csv.DictReader(io.StringIO(r['stdout'])))
        assert len(rows) == 4 and [(row['phase'], int(row['frames'])) for row in rows] == PHASES
        for row in rows:
            assert row['scene'] == 'proofsheet' and row['trial'] == '0'
            for key, number in [('glyph_requests_per_frame', 1980), ('distinct_glyph_size_instances_per_frame', 198),
                                ('text_draw_calls_per_frame', 30), ('nominal_characters_per_row', 66)]:
                assert int(row[key]) == number
            assert int(row['logical_width']) == 1800 and int(row['logical_height']) == 1200
            times = [float(row[k]) for k in ['draw_us', 'flush_us', 'total_us']]
            assert times[0] > 0 and times[1] >= 0 and abs(times[0] + times[1] - times[2]) < 0.000002
        key = (r['block'], r['font'], r['variant'])
        assert key not in observations
        observations[key] = rows
        contributions = {row['phase']: int(row['frames']) * float(row['total_us']) for row in rows}
        weighted_sequences.append({'block': r['block'], 'font': r['font'], 'variant': r['variant'],
            'frames': 44, 'phase_contributions_us': contributions, 'total_us': sum(contributions.values())})
    assert (timestamp(raw[0]['guard_before_utc']) - timestamp(plan['declared_utc'])).total_seconds() >= 59
    assert timestamp(complete['completed_utc']) >= previous_after
    for block in range(12):
        for font in FONTS:
            baseline, final = observations[(block, font, 'master')], observations[(block, font, 'final')]
            fields = ['phase', 'frames', 'glyph_requests_per_frame', 'distinct_glyph_size_instances_per_frame',
                      'text_draw_calls_per_frame', 'logical_width', 'logical_height', 'nominal_characters_per_row']
            assert [[r[k] for k in fields] for r in baseline] == [[r[k] for k in fields] for r in final]
    reconstructed = []
    largest_error = 0.0
    for font in FONTS:
        for phase in [p for p, _ in PHASES] + ['complete_sequence']:
            values = {}
            for variant in ['master', 'final']:
                values[variant] = []
                for block in range(12):
                    rows = observations[(block, font, variant)]
                    value = sum(int(r['frames']) * float(r['total_us']) for r in rows) if phase == 'complete_sequence' else next(float(r['total_us']) for r in rows if r['phase'] == phase)
                    values[variant].append(value)
            ratios = [final / master for master, final in zip(values['master'], values['final'])]
            deltas = [final - master for master, final in zip(values['master'], values['final'])]
            row = {'font': font, 'phase': phase, 'units': 'us/sequence' if phase == 'complete_sequence' else 'us/frame',
                'master_median': median(values['master']), 'final_median': median(values['final']),
                'median_paired_ratio': median(ratios), 'paired_ratio_ci95': interval(ratios),
                'median_paired_delta': median(deltas), 'paired_delta_ci95': interval(deltas),
                'paired_ratios': ratios, 'paired_deltas': deltas}
            expected_row = stored_summary[len(reconstructed)]
            assert row.keys() == expected_row.keys()
            for k, value in row.items():
                if isinstance(value, str):
                    assert value == expected_row[k]
                else:
                    pairs = zip(value, expected_row[k]) if isinstance(value, list) else [(value, expected_row[k])]
                    for a, b in pairs:
                        error = abs(a - b)
                        largest_error = max(largest_error, error)
                        assert error <= max(1e-8, abs(b) * 1e-11), (font, phase, k, a, b)
            reconstructed.append(row)
    assert len(stored_summary) == len(reconstructed) == 15
    assert complete['completed_processes'] == complete['expected_processes'] == 72
    assert complete['summary_rows'] == 15 and complete['phase_observations'] == 288 and complete['measured_frames'] == 3168
    assert complete['interference_events'] == 0
    counts = {'saving_ci_below_zero': sum(r['paired_delta_ci95'][1] < 0 for r in reconstructed),
              'loss_ci_above_zero': sum(r['paired_delta_ci95'][0] > 0 for r in reconstructed),
              'inconclusive_ci_crosses_zero': sum(r['paired_delta_ci95'][0] <= 0 <= r['paired_delta_ci95'][1] for r in reconstructed)}
    return {'cohort': name, 'dpi': dpi, 'processes': 72, 'phase_records': 288, 'measured_frames': 3168,
        'accepted_complete_blocks': 12, 'excluded_measured_records': 0, 'pair_orders': orders,
        'all_workload_dimensions_equal_between_variants': True, 'per_frame_reported_requests': 1980,
        'per_frame_reported_distinct_instances': 198, 'phase_weights': dict(PHASES), 'total_sequence_frames': 44,
        'bootstrap': {'resamples': 10000, 'seed': 61432, 'method': 'paired median, percentile order indices250/9750; unweighted choices protocol',
                      'multiplicity_adjustment': False},
        'largest_summary_absolute_error': largest_error, 'summary_rows_reproduced': 15, 'ci_classification': counts,
        'font_assets': assets, 'file_hashes': {f: digest(directory / f) for f in ['PLAN.json', 'raw.jsonl', 'summary.json', 'REPORT.md', 'COMPLETE.json']},
        'reconstructed_rows': reconstructed, 'all_weighted_sequences': weighted_sequences}


def report(result):
    lines = ['# Independent proof-sheet audit', '',
        'PASS: both complete cohorts were reconstructed from their original CSV stdout without importing the runner. The DPI 1 cohort is primary; DPI 2 remains a separate control. The DPI 1 plan was declared for a fresh campaign after the DPI 2 units error was identified. No measured records were excluded or merged.', '',
        'Each cohort has 72 processes, 288 phase records, 12 complete paired blocks, and 6 master-first/6 final-first pairs per font. Each process reports a 44-frame sequence: first paint1, warm30, changing size12, return1. Every reported frame requests 1,980 glyphs through30 public text calls, with198 distinct glyph/font/size instances and66 characters per row. Workload counts and finite1800×1200 logical dimensions match between variants.', '',
        'All15 summary rows per cohort reproduce within the stated numerical tolerance. Intervals are exploratory paired median bootstraps with10,000 resamples, seed61432, percentile order positions250/9750, and no multiplicity correction. Complete sequence totals are formed inside each process before pairing; they include all44 measured frames. Marginal medians can differ from the paired median difference.', '',
        'Frozen binaries, all frozen source files, compiler artifact manifests/features, dependency graphs, lock dependency records, harness digest and build conditions pass. Five existing baseline files match upstream6a5f15a, and the new Swash module is absent from both baseline and upstream. Six final files match the primary source pin and released code atb87a94d. The only whole-file difference is two comment lines inside the Swash test module. Its entire prefix before the test module is identical. The final snapshot registration retains an old working-tree revision label; full hashes and commit comparisons establish the actual identity.', '',
        'Font files and supplied license/acquisition records match their predeclared digests. All three fonts use SIL OFL 1.1. The predeclared LICENSE-Roboto is a preserved legacy Apache 2.0 file: verifying its hash does not establish applicability to this Roboto Flex font. The exact Roboto Flex font bytes match the benchmark asset whose ATTRIBUTION.md maps it to licenses/RobotoFlex-OFL.txt; that applicable OFL file and mapping were verified separately in LICENSE-SUPPLEMENT.json. Original plans and measurements remain unchanged. The original compiler-guard prestart abort remains separate with zero timing records. Six API/count smoke processes are excluded from both cohorts.', '']
    for data in result['cohorts']:
        lines.extend([f'## {data["cohort"]} (DPI {data["dpi"]:g})', '',
            '| Font | Phase | Master ms | Final ms | Paired delta ms [95% CI] | Paired reduction % [95% CI] |',
            '|---|---|---:|---:|---:|---:|'])
        for row in data['reconstructed_rows']:
            d, r = row['paired_delta_ci95'], row['paired_ratio_ci95']
            lines.append(f'| {row["font"]} | {row["phase"]} | {row["master_median"]/1000:.3f} | {row["final_median"]/1000:.3f} | {row["median_paired_delta"]/1000:+.3f} [{d[0]/1000:+.3f}, {d[1]/1000:+.3f}] | {(1-row["median_paired_ratio"])*100:.2f} [{(1-r[1])*100:.2f}, {(1-r[0])*100:.2f}] |')
        lines.extend(['', f'Largest absolute discrepancy from stored statistics: {data["largest_summary_absolute_error"]:.3g}. CI classification: {data["ci_classification"]}.', ''])
    lines.extend(['## Interpretation limits', '',
        '- At identity canvas transform, native atlas font sizes are 14/20/28 pixels plus the changing-size delta, independent of layout DPR. DPI 1 requests row shifts 0..0.9 in 0.1 native units; DPI 2 requests 0..0.45 in 0.05 units. Individual glyph advances and floating-point quantization mean the defensible claim is **up to ten requested canonical phase bins**, rather than a verified ten bins for every glyph.',
        '- Returned public TextMetrics positions are the invscaled positions passed to the identity-transform atlas path. They could diagnose requested canonical bins, but this unchanged harness stores counts rather than every glyph position. Request counts are not instrumented bitmap or outline cache hits, misses, admissions, or evictions.',
        '- Changing-size frames avoid previous-size bitmap reuse but retain repeated same-frame geometry opportunities across rows. They are not a pure miss-only control. A fast return can reuse the outer bitmap atlas; it does not independently prove outline-cache retention.',
        '- The three-typeface dense proof sheet demonstrates a large bounded public-API CPU cost and patch saving. It does not establish a globally maximal font/workload, isolate hinting alone, isolate the arena, or prove eviction. It is not an application/GPU/window frame-time claim. Void produces no captured proof-sheet pixels.',
        '- Timings retain only phase means, not every individual frame time. Public count assertions in the harness enforce the reported count across each phase. Process-name checks before/after cannot prove continuous machine isolation or absence of unrelated CPU load; successful before checks are inferred from the hash-bound runner control flow, whereas after status and timestamps are explicit in raw records.',
        '- DPI1 and DPI2 are separate chronological studies, not paired cross-DPI experiments. Their difference cannot be assigned solely to phase coverage because shaping/layout scale also changes.',
        '- Existing synthetic non-Swash warm-paragraph costs of about1.3–2.4 microseconds per frame remain part of the broader patch assessment; this Swash-only stress comparison does not erase or measure them.', ''])
    return '\n'.join(lines).replace('paint1', 'paint 1').replace('warm30', 'warm 30').replace('size12', 'size 12').replace('return1', 'return 1').replace('through30', 'through 30').replace('with198', 'with 198').replace('and66', 'and 66').replace('finite1800', 'finite 1800').replace('All15', 'All 15').replace('with10,000', 'with 10,000').replace('seed61432', 'seed 61432').replace('positions250', 'positions 250').replace('all44', 'all 44').replace('upstream6a', 'upstream 6a').replace('atb87', 'at b87').replace('OFL1.1', 'OFL 1.1').replace('Apache2.0', 'Apache 2.0').replace('are14', 'are 14').replace('DPI1', 'DPI 1').replace('DPI2', 'DPI 2').replace('shifts0', 'shifts 0').replace('in0.', 'in 0.').replace('about1.3', 'about 1.3') + '\n'


def main():
    original = ROOT / 'paired12'
    before = {p.name: digest(p) for p in original.iterdir() if p.is_file()}
    assert set(before) == {'PLAN.json', 'ABORT.json'} and not (original / 'raw.jsonl').exists()
    origin, builds = provenance()
    licensing = license_supplement()
    data = [cohort('paired12-dpi1', 1.0, builds), cohort('paired12-native', 2.0, builds)]
    smoke = read_json(ROOT / 'smoke.json')
    assert len(smoke) == 6 and all(r['returncode'] == 0 for r in smoke)
    assert {p.name: digest(p) for p in original.iterdir() if p.is_file()} == before
    result = {'status': 'PASS', 'completed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'audit_script_sha256': digest(Path(__file__)), 'provenance': origin, 'cohorts': data,
        'failed_prestart_attempt': {'path': str(original), 'file_hashes': before, 'timing_records': 0, 'unchanged': True,
                                  'abort': read_json(original / 'ABORT.json')},
        'smoke': {'records': 6, 'sha256': digest(ROOT / 'smoke.json'), 'included_in_timings': False},
        'RobotoFlex_license_correction': licensing,
        'no_binaries_builds_or_timings_executed_by_audit': True}
    (ROOT / 'audit/LICENSE-SUPPLEMENT.json').write_text(json.dumps(licensing, indent=2) + '\n')
    (ROOT / 'audit/AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
    (ROOT / 'audit/REPORT.md').write_text(report(result))
    print(json.dumps({'status': 'PASS', 'cohorts': [{k: c[k] for k in ['cohort', 'processes', 'summary_rows_reproduced', 'largest_summary_absolute_error', 'ci_classification']} for c in data]}))


if __name__ == '__main__':
    main()
