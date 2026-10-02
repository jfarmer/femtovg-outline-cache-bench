#!/usr/bin/env python3
"""Render arena/pool comparisons from completed, preserved statistics only.

This renderer does not compute estimates, confidence intervals, or run workloads.
Run it only after the serial measurement campaign and statistical audits finish.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = Path('/private/tmp/alustin-outline-pool-review')
FONTS = {'stock':'Roboto Flex', 'roboto':'Roboto Flex', 'vollkorn':'Vollkorn Medium', 'ptsans':'PT Sans Regular'}
COMPARISONS = [('master','final'), ('master','pool'), ('final','pool')]
LABELS = {'grid_singleton':'94 one-use glyphs', 'grid_two_phases':'First + second phase',
    'grid_unique_sizes':'32 unique sizes', 'grid_unique_variations':'32 unique weights',
    'grid_pollution':'Hot + 64-size pollution + return'}
ENDPOINTS = {'grid_singleton':'once', 'grid_two_phases':'second', 'grid_unique_sizes':'sweep',
    'grid_unique_variations':'sweep', 'grid_pollution':'hot_return'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def load(path):
    with Path(path).open(newline='') as stream:
        return list(csv.DictReader(stream))

def one(rows, **keys):
    matches = [row for row in rows if all(row.get(key) == str(value) for key,value in keys.items())]
    if len(matches) != 1:
        raise ValueError(f'Expected one observation for {keys}; found {len(matches)}')
    return matches[0]

def interval(row, key):
    value = json.loads(row[key])
    if not isinstance(value,list) or len(value)!=2 or any(not math.isfinite(float(x)) for x in value) or value[0]>value[1]:
        raise ValueError(f'Invalid preserved interval {key}: {value}')
    return value

def pct_number(value):
    return f'{value:+.3f}' if 0 < abs(value) < .05 else f'{value:+.2f}'

def effect(row, app=False):
    point = float(row['median_paired_change_pct' if app else 'paired_delta_pct'])
    low,high = interval(row,'median_paired_change_pct_ci95' if app else 'paired_bootstrap95')
    delta = float(row['median_paired_delta' if app else 'paired_delta_us']) / (1 if app else 1000)
    return f'{pct_number(point)}% [{pct_number(low)}, {pct_number(high)}]<br>Δ {delta:+.3f} ms'

def rss_effect(row):
    low,high = interval(row,'median_paired_delta_ci95')
    return f"{float(row['median_paired_delta']):+.3f} [{low:+.3f}, {high:+.3f}] MiB"

def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |',
        *['| '+' | '.join(map(str,row))+' |' for row in rows]])

def trio(rows, base, app=False, rss=False):
    values=[]
    for reference,candidate in COMPARISONS:
        names={'reference':reference,'candidate':candidate} if app else {'reference_version':reference,'candidate_version':candidate}
        row=one(rows,**base,**names)
        values.append(rss_effect(row) if rss else effect(row,app))
    return values

def validate(core, app, replay, sequences, application):
    for mode in ('cpu','gpu','pixels'):
        record=read(core/'results'/f'{mode}-provenance.json')
        if not record.get('complete') or record['versions']!=['master','current','final','pool']:
            raise ValueError(f'Incomplete or wrong-variant replay batch: {mode}')
        if mode!='pixels' and (record['blocks']!=12 or record['dpis']!=[2] or record['fonts']!=['stock','vollkorn','ptsans']):
            raise ValueError(f'Unexpected replay timing matrix: {mode}')
        if mode=='pixels' and (len(record['pixel_comparisons'])!=504 or not all(row['rgba_identical'] for row in record['pixel_comparisons'])):
            raise ValueError('Incomplete or mismatching replay pixel campaign')
    for name in ('cpu-12','pixels'):
        record=read(app/name/'summary.json')
        if not record.get('complete') or record['versions']!=['master','current','final','pool']:
            raise ValueError(f'Incomplete or wrong-variant application batch: {name}')
        if name=='cpu-12' and (record['rounds']!=12 or len(record['accepted_blocks'])!=72):
            raise ValueError('Unexpected Alustin timing matrix')
        if name=='pixels' and (len(record['pixel_comparisons'])!=18 or not all(row['rgba_identical'] for row in record['pixel_comparisons'])):
            raise ValueError('Incomplete or mismatching Alustin pixel campaign')
        if name=='pixels':
            included=[launch for launch in record['launches'] if launch.get('included')]
            if not record['actual_font_diagnostics'].get('enabled') or len(included)!=24 or any(launch.get('font_verification_exit_code')!=0 or not launch.get('actual_fonts') for launch in included):
                raise ValueError('Accepted Alustin pixels require actual primary/fallback font verification')
    if len(replay)!=3024 or len(sequences)!=864 or len(application)!=684:
        raise ValueError('Expected all six comparisons and complete phase/sequence/application tables')
    for row in replay+sequences:
        expected_trials=5 if row['backend']=='cpu' else 3
        if row['backend'] not in {'cpu','gpu'} or int(row['dpi'])!=2 or int(row['process_blocks'])!=12 or int(row['trials_per_process'])!=expected_trials:
            raise ValueError('Primary replay report requires 12-block DPR2 CPU/GPU cohorts with 5/3 trials')
    if any(row['mode']!='cpu' or int(row['n_blocks'])!=12 for row in application):
        raise ValueError('Primary Alustin report requires complete 12-round CPU cohorts')

def probe_tables(path):
    probe=read(path)
    if not probe.get('complete') or len(probe['records'])!=54 or len(probe['executions'])!=6:
        raise ValueError('Incomplete allocation/residency probe')
    indexed={tuple(row[key] for key in ('version','font','scene','phase')):row for row in probe['records']}
    if len(indexed)!=54:
        raise ValueError('Duplicate allocation probe record')
    residency=[];allocation=[]
    for font in ('stock','vollkorn','ptsans'):
        for scene,phase in ENDPOINTS.items():
            if scene=='grid_unique_variations' and font!='stock': continue
            a=indexed['final',font,scene,phase];b=indexed['pool',font,scene,phase]
            for key in ('prefix_frames','prefix_glyphs','dpi','pixel_digest_fnv64','actual_font'):
                if a[key]!=b[key]:raise ValueError(f'Probe mechanism parity differs: {font}/{scene}/{key}')
            def pair(field,group=None,scale=1):
                old=a[group][field] if group else a[field]
                new=b[group][field] if group else b[field]
                return f'{old/scale:.1f} → {new/scale:.1f}' if scale!=1 else f'{old} → {new}'
            residency.append([FONTS[font],LABELS[scene],pair('hits','counters'),pair('nonempty_clears','counters'),
                pair('cached_entries','state'),b['state']['pooled_entries'],pair('accounted_retained_bytes','state',1024),
                pair('rasterizer_owned_requested_bytes',scale=1024)])
            allocation.append([FONTS[font],LABELS[scene],a['prefix_glyphs'],pair('allocation_calls'),
                pair('allocation_requested_bytes',scale=1024),pair('peak_live_requested_growth',scale=1024),
                b['counters']['fresh_native_outlines'],b['counters']['pool_acquires']])
    return probe,residency,allocation

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core',type=Path,default=ROOT)
    parser.add_argument('--app',type=Path,default=APP)
    parser.add_argument('--phase-summary',type=Path)
    parser.add_argument('--sequence-summary',type=Path)
    parser.add_argument('--app-summary',type=Path)
    parser.add_argument('--probe',type=Path)
    parser.add_argument('--source-review',type=Path)
    parser.add_argument('--conclusion',type=Path,help='Optional maintainer assessment written after independent audits')
    parser.add_argument('--output',type=Path,default=ROOT/'NATIVE-OUTLINE-POOL.md')
    args=parser.parse_args();core=args.core.resolve(strict=True);app=args.app.resolve(strict=True)
    phase_path=args.phase_summary or core/'analysis/phase/summary.csv'
    sequence_path=args.sequence_summary or core/'analysis/sequence/summary.csv'
    app_path=args.app_summary or app/'analysis/summary.csv'
    replay,sequences,application=map(load,(phase_path,sequence_path,app_path))
    validate(core,app,replay,sequences,application)
    review_path=args.source_review or core/'source-review.json';review=read(review_path)
    if not review.get('complete') or review['different_production_source_files']!=['src/text/swash_rasterizer.rs']:
        raise ValueError('Source identity review missing or comparison scope differs')
    parts=['# Shared geometry arena versus pooled native Swash Outline','']
    if args.conclusion:parts += [args.conclusion.read_text().strip(),'']
    parts += ['This follow-up compares the previously selected shared geometry arena (`final`) with cached, recycled native Swash `Outline` objects (`pool`). Master and the original cache (`current`) remain in the same fresh four-version campaign. The prior [REPORT.md](REPORT.md) and every earlier benchmark remain preserved; these new observations are not pooled with earlier cohorts.','',
        'Each cell shows median paired change, an exploratory 95% whole-block bootstrap interval, and paired absolute change. Negative duration changes mean faster. **Pool/arena is the direct storage comparison**; arena/master and pool/master show whether either complete patch merits inclusion. Absolute medians need not reproduce a median paired percentage.','',
        '## Existing example first paint','']
    rows=[]
    for backend,metric in [('cpu','draw_us'),('gpu','complete_us')]:
        for font in ('stock','vollkorn','ptsans'):
            for scene in ('demo','text'):
                base=dict(backend=backend,font=font,dpi=2,scene=scene,phase='first_paint',metric=metric)
                rows.append([FONTS[font],scene,'CPU drawing' if backend=='cpu' else 'GPU completion',*trio(replay,base)])
    parts += [table(['Font','Scene','Measurement','Arena/master','Pool/master','Pool/arena'],rows),'',
        'GPU completion includes CPU drawing, submission and waiting for completion; it is not a GPU timestamp. All 28 phases remain in the [per-phase statistics](analysis/native-pool-examples/summary.csv).','',
        '## Complete controlled sequences','',
        'Each controlled frame introduces 94 distinct atlas keys. Size and variation sweeps deliberately provide no cross-instance outline reuse. The two-phase total includes population and reuse. Pollution includes both hot frames, all 64 pollution frames and hot return. Variation controls always use Roboto Flex and are shown once.','']
    rows=[]
    for backend,metric in [('cpu','draw_us'),('gpu','complete_us')]:
        for font in ('stock','vollkorn','ptsans'):
            for scene,label in LABELS.items():
                if scene=='grid_unique_variations' and font!='stock':continue
                rows.append([FONTS[font],label,'CPU' if backend=='cpu' else 'GPU completion',
                    *trio(sequences,dict(backend=backend,font=font,dpi=2,scene=scene,metric=metric))])
    parts += [table(['Font','Complete sequence','Measurement','Arena/master','Pool/master','Pool/arena'],rows),'',
        '## Every reported example sequence','',
        'These sums include every reported phase: movement, reflow, zoom and font-instance changes. They exclude 119 unreported warmup frames per scene and are not launch-to-end durations. Each trial is summed before process medians and block pairing.','']
    rows=[]
    for backend,metric in [('cpu','draw_us'),('gpu','complete_us')]:
        for font in ('stock','vollkorn','ptsans'):
            for scene in ('demo','text','font_variations'):
                if scene=='font_variations' and font!='stock':continue
                base=dict(backend=backend,font=font,dpi=2,scene=scene,metric=metric)
                exemplar=one(sequences,**base,reference_version='final',candidate_version='pool')
                rows.append([FONTS[font],scene,exemplar['reported_frames'],'CPU' if backend=='cpu' else 'GPU completion',*trio(sequences,base)])
    parts += [table(['Font factor','Scene','Reported frames','Measurement','Arena/master','Pool/master','Pool/arena'],rows),'',
        '## Alustin first and filtered search renderer-thread CPU','',
        'These diagnostics measure renderer-thread host work; they do not measure GPU completion, compositor scanout or diagnostics-off startup. The filtered search can introduce new atlas entries and is not necessarily a completely warm redraw.','']
    rows=[]
    for metric,label in [('first_frame.render.thread_cpu_ms','First'),('search_frame.render.thread_cpu_ms','Search')]:
        for font in ('roboto','vollkorn','ptsans'):
            for backend in ('winit-femtovg-wgpu','winit-femtovg'):
                rows.append([FONTS[font],'WGPU' if backend.endswith('wgpu') else 'OpenGL',label,
                    *trio(application,dict(mode='cpu',font=font,backend=backend,metric=metric),app=True)])
    parts += [table(['Font','Backend','Frame','Arena/master','Pool/master','Pool/arena'],rows),'',
        '## Alustin process high-water RSS','',
        'RSS includes the application, renderer, fonts, driver and transient host work. It is neither device VRAM nor the outline cache alone. The following effects are absolute MiB changes rather than percentages.','']
    rows=[]
    for font in ('roboto','vollkorn','ptsans'):
        for backend in ('winit-femtovg-wgpu','winit-femtovg'):
            rows.append([FONTS[font],'WGPU' if backend.endswith('wgpu') else 'OpenGL',
                *trio(application,dict(mode='cpu',font=font,backend=backend,metric='peak_rss_mib'),app=True,rss=True)])
    parts += [table(['Font','Backend','Arena−master, 95% CI','Pool−master, 95% CI','Pool−arena, 95% CI'],rows),'',
        '## Warm redraws','',
        'All warm example phases are shown, including intervals crossing zero. Variation-scene repetitions under other regular-font factors are duplicate Roboto control workloads.','']
    rows=[]
    for backend,metric in [('cpu','draw_us'),('gpu','complete_us')]:
        for font in ('stock','vollkorn','ptsans'):
            for scene in ('demo','text','font_variations'):
                if scene=='font_variations' and font!='stock':continue
                rows.append([FONTS[font],scene,'CPU' if backend=='cpu' else 'GPU completion',
                    *trio(replay,dict(backend=backend,font=font,dpi=2,scene=scene,phase='warm',metric=metric))])
    parts += [table(['Font factor','Scene','Measurement','Arena/master','Pool/master','Pool/arena'],rows),'',
        '## Exploratory regression audit','',
        'This lists primary example drawing/completion and Alustin first/search renderer-thread CPU effects whose preserved 95% interval lies entirely above zero. Intervals are per-metric and unadjusted for multiple comparisons. Small isolated differences do not establish a general regression. All uncertain effects remain in the full statistics.','']
    rows=[]
    for row in replay:
        pair=row['reference_version'],row['candidate_version']
        if pair not in COMPARISONS or (row['backend'],row['metric']) not in {('cpu','draw_us'),('gpu','complete_us')} or row['scene'].startswith('grid_'):
            continue
        if row['scene']=='font_variations' and row['font']!='stock':continue
        if interval(row,'paired_bootstrap95')[0]>0:
            rows.append([FONTS[row['font']],f"{row['scene']}/{row['phase']} {row['backend']}",
                {('master','final'):'Arena/master',('master','pool'):'Pool/master',('final','pool'):'Pool/arena'}[pair],effect(row)])
    for row in application:
        pair=row['reference'],row['candidate']
        if pair not in COMPARISONS or row['metric'] not in {'first_frame.render.thread_cpu_ms','search_frame.render.thread_cpu_ms'}:continue
        if interval(row,'median_paired_change_pct_ci95')[0]>0:
            rows.append([FONTS[row['font']],f"Alustin {row['backend']}/{row['metric']}",
                {('master','final'):'Arena/master',('master','pool'):'Pool/master',('final','pool'):'Pool/arena'}[pair],effect(row,True)])
    parts += [table(['Font','Observation','Comparison','Duration change'],rows) if rows else 'No effect in this declared regression-audit scope has an entirely positive interval.','',
        '## Storage, reuse and code volume','',
        f"The arena stores point/verb ranges in shared vectors and uses one native Outline scratch object. The pool stores native Outline objects directly, removing range management and scratch-to-cache geometry copying. It adds object acquisition, recycling, per-object high-water tracking and free-pool trimming. The production rasterizer is **{review['arena']['production_lines']} → {review['pool']['production_lines']} lines**, {review['arena']['production_lines']-review['pool']['production_lines']} fewer; this describes source volume, not a demonstrated maintainability improvement.",'',
        'Both candidates are internal to FemtoVG and Swash-only, with identical cache keys, eager admission, native scaling/hinting and bitmap/scaler routing. No Swash or transitive dependency changes are included.','',
        '**The equal 1 MiB nominal targets do not impose equal heap limits or cache residency.** The arena charges its shared-vector capacities exactly plus logical key/range metadata and native scratch public length high-water. The pool charges logical point/verb length high-water separately for each native object, cached metadata and the free-pool wrapper vector capacity. Neither can account for inaccessible native spare capacities/layers; map capacity, allocator overhead, shared ScaleContext and transient work are excluded. Differences in eviction or retained private capacity are part of this implementation comparison.','']
    probe_path=args.probe or core/'probe/results.json';probe,residency,allocation=probe_tables(probe_path)
    parts += ['### Untimed residency and requested heap','',
        'Values are **arena → pool** at the end of each complete control. Hits and clears are cumulative through the same replay prefix. Owned requested heap is measured by dropping only the rasterizer while fonts and its external ScaleContext remain alive and every output Image has already been dropped. It includes native private buffers, map buckets and Zeno scratch; it is requested Rust heap memory, not RSS or allocator bookkeeping.','',
        table(['Font','Complete control','Hits','Nonempty clears','Cached entries','Free pool entries','Accounted KiB','Owned requested KiB'],residency),'',
        '### Untimed allocation traffic','',
        'Every endpoint is replayed from a fresh rasterizer/context through the whole prefix. Allocation traffic and peak growth include temporary images and shared-context preparation. Allocation counts do not predict elapsed time; timed binaries contain none of this instrumentation. Values are arena → pool; fresh/pool-acquired native object counts apply to the pool only.','',
        table(['Font','Complete control','Glyph requests','Allocation calls','Requested KiB','Peak live growth KiB','Fresh native objects','Pool acquisitions'],allocation),'',
        f"The [full probe](analysis/native-pool-probe.json) retains all {len(probe['records'])} prefix records and all {len(probe['executions'])} executions. Pixel FNV digests are a mechanism sanity check; the independent complete RGBA campaign is the visual correctness evidence.",'',
        '## Validation and study limits','',
        'The native pool passed 173 library tests and formatting. Final rendering validation contains 504 exact replay comparisons at DPR 1/2 and 18 exact Alustin comparisons, with actual primary/fallback font bytes checked in untimed application diagnostics. Source review verifies that only the Swash rasterizer storage/accounting file differs. Initial invalid allocation-probe root-package reuse is preserved separately and excluded from the valid probe; corrected unique package/executable guards are recorded.','',
        'Timing uses 12 balanced Williams blocks per font/DPR, five CPU or three GPU replay trials per process, and a balanced Williams schedule for 12 Alustin rounds per font/backend. Three input-contaminated queries caused whole-block retries: the accepted PT Sans cohorts have order counts 2/3/3/4 on both backends, while the other four cohorts retain 3/3/3/3. All valid observations are retained; no duration-based exclusions or retries are permitted. These are exploratory intervals without multiplicity adjustment or adjustment for implementation selection. They describe these workloads and this machine, not a universal speedup.','',
        'The raw replay and application independent audits reconstruct primary point effects and confidence intervals from retained records. Source, lock, feature-graph, executable identity, ordering and exact pixel audits are separate evidence. All six original-cache/master/candidate comparisons remain in the complete CSV/JSON statistics even though the report highlights three.','',
        '## Reproduction and preserved inputs','',
        'The three new campaign archives are `native-pool-examples`, `native-pool-alustin`, and `native-pool-source-bundle` in [results/index.json](results/index.json). The source-bundle archive contains the isolated portable wrappers and pinned native-pool source snapshots; extract it into a fresh directory, then use its prepare/build/run/analyze commands as described in [native pool reproduction](docs/native-pool-reproduction.md). Existing repository vendor inputs remain unchanged.','']
    inputs={'script':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'files':{}}
    for path in (phase_path,sequence_path,app_path,probe_path,review_path,core/'candidate-proof.json',core/'runtime/core/experiment.json'):
        inputs['files'][str(path.resolve())]={'sha256':sha(path),'bytes':path.stat().st_size}
    for path in (core/'independent-replay-statistics-audit.json',core/'independent-identity-pixel-audit.json',app/'independent-app-statistics-audit.json'):
        record=read(path)
        if not record.get('complete'):raise ValueError(f'Incomplete independent audit: {path}')
        inputs['files'][str(path.resolve())]={'sha256':sha(path),'bytes':path.stat().st_size}
    if args.conclusion:inputs['files'][str(args.conclusion.resolve())]={'sha256':sha(args.conclusion),'bytes':args.conclusion.stat().st_size}
    def label(path):
        path=Path(path)
        if path.is_relative_to(core):return 'core/'+path.relative_to(core).as_posix()
        if path.is_relative_to(app):return 'app/'+path.relative_to(app).as_posix()
        return str(path)
    rows=[[label(path),f"`{record['sha256']}`"] for path,record in inputs['files'].items()]
    parts += [table(['Preserved input','SHA-256'],rows),'']
    output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('\n'.join(parts))
    output.with_suffix('.inputs.json').write_text(json.dumps(inputs,indent=2,sort_keys=True)+'\n')
    print('Rendered completed arena/pool report:',output)

if __name__=='__main__':main()
