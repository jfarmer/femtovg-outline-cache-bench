#!/usr/bin/env python3
"""Render preserved revised-cache estimates; compute no statistics or CIs."""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
VERSIONS=['master','prior','updated45','final']
PAIRS=[('master','final'),('prior','updated45'),('updated45','final')]
PAIR_NAMES=['Final/master','Fixes 4–5/prior','Final/fixes 4–5']
FONTS={'stock':'Roboto Flex','roboto':'Roboto Flex','vollkorn':'Vollkorn','ptsans':'PT Sans'}
SCENES={'grid_singleton':'94 one-use glyphs','grid_two_phases':'Population + second phase',
        'grid_unique_sizes':'32 unique sizes','grid_unique_variations':'32 unique weights',
        'grid_pollution':'Hot + 64-size pollution + return'}
APP_METRICS={'first_frame.render.thread_cpu_ms':'First paint','search_frame.render.thread_cpu_ms':'Filtered search'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def csv_rows(path):
    with Path(path).open(newline='') as stream:return list(csv.DictReader(stream))
def one(rows,**keys):
    matches=[row for row in rows if all(str(row.get(key))==str(value) for key,value in keys.items())]
    if len(matches)!=1:raise ValueError(f'Expected one preserved row for {keys}; found {len(matches)}')
    return matches[0]
def ci(value):
    values=json.loads(value) if isinstance(value,str) else value
    if not isinstance(values,list) or len(values)!=2 or any(not math.isfinite(float(x)) for x in values) or values[0]>values[1]:
        raise ValueError('Invalid preserved 95% interval: '+str(value))
    return list(map(float,values))
def number(value,signed=False):
    value=float(value);precision=3 if 0<abs(value)<.05 else 2
    return f'{value:+.{precision}f}' if signed else f'{value:.{precision}f}'
def milliseconds(value):
    value=float(value);return f'{value:.6f}' if abs(value)<.01 else f'{value:.3f}'
def normalized(row,kind):
    if kind=='app':
        return {'reference':row['reference'],'candidate':row['candidate'],
            'reference_ms':float(row['reference_median']),'candidate_ms':float(row['candidate_median']),
            'delta_ms':float(row['median_paired_delta']),'change_pct':float(row['median_paired_change_pct']),
            'ci95_pct':ci(row['median_paired_change_pct_ci95'])}
    if kind=='budget':
        return {'reference':row['reference'],'candidate':row['candidate'],
            'reference_ms':float(row['reference_median_us'])/1000,'candidate_ms':float(row['candidate_median_us'])/1000,
            'delta_ms':float(row['paired_delta_us'])/1000,'change_pct':float(row['paired_change_pct']),
            'ci95_pct':ci(row['paired_change_pct_ci95'])}
    return {'reference':row['reference_version'],'candidate':row['candidate_version'],
        'reference_ms':float(row['reference_process_median'])/1000,'candidate_ms':float(row['candidate_process_median'])/1000,
        'delta_ms':float(row['paired_delta_us'])/1000,'change_pct':float(row['paired_delta_pct']),
        'ci95_pct':ci(row['paired_bootstrap95'])}
def effect(row,kind):
    value=normalized(row,kind);low,high=value['ci95_pct'];delta=value['delta_ms']
    absolute=f'Δ {delta*1000:+.3f} µs' if abs(delta)<.01 else f'Δ {delta:+.3f} ms'
    return f"{number(value['change_pct'],True)}% [{number(low,True)}, {number(high,True)}]<br>{absolute}"
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |',
                      *['| '+' | '.join(map(str,row))+' |' for row in rows]])
def values(rows,base,kind):
    keys=('reference','candidate') if kind in ('app','budget') else ('reference_version','candidate_version')
    selected=[one(rows,**base,**dict(zip(keys,pair))) for pair in PAIRS]
    primary=normalized(selected[0],kind)
    return [milliseconds(primary['reference_ms']),milliseconds(primary['candidate_ms']),
            *[effect(row,kind) for row in selected]]
def primary(row):return (row['backend'],row['metric']) in {('cpu','draw_us'),('gpu','complete_us')}
def unique_font(row):
    return row['font']=='stock' or row['scene'] not in ('font_variations','grid_unique_variations')
def complete(path):
    value=read(path)
    if value.get('complete') is not True:raise ValueError('Completed evidence required: '+str(path))
    return value

def validate(root,phases,sequences,application,budget):
    for mode in ('cpu','gpu','pixels'):
        record=complete(root/'examples-validated'/f'{mode}-provenance.json')
        if record['versions']!=VERSIONS:raise ValueError('Wrong replay versions')
        if mode!='pixels' and (record['blocks']!=12 or record['dpis']!=[2] or record['fonts']!=['stock','vollkorn','ptsans']):
            raise ValueError('Unexpected primary replay matrix')
        if mode=='pixels' and (len(record['pixel_comparisons'])!=504 or not all(row['rgba_identical'] for row in record['pixel_comparisons'])):
            raise ValueError('Complete native-oracle/legacy pixel validation missing')
    for name in ('cpu','pixels'):
        record=complete(root/'alustin'/name/'summary.json')
        if record['versions']!=VERSIONS:raise ValueError('Wrong Alustin versions')
        if name=='cpu' and (record['rounds']!=12 or len(record['accepted_blocks'])!=72):raise ValueError('Unexpected Alustin timing matrix')
        if name=='pixels' and (len(record['pixel_comparisons'])!=18 or not all(row['rgba_identical'] for row in record['pixel_comparisons'])):
            raise ValueError('Alustin exact pixel validation missing')
        if name=='pixels':
            accepted=[launch for launch in record['launches'] if launch.get('included')]
            if not record['actual_font_diagnostics']['enabled'] or len(accepted)!=24 or any(launch.get('font_verification_exit_code')!=0 or not launch.get('actual_fonts') for launch in accepted):
                raise ValueError('Accepted Alustin actual-font diagnostics missing')
    if len(phases)!=3024 or len(sequences)!=864 or len(application)!=684 or len(budget)!=54:
        raise ValueError('Incomplete six-comparison phase/sequence/application/budget statistics')
    for row in phases+sequences:
        if not primary(row) and row['metric'] not in ('draw_us','submit_us','complete_us'):raise ValueError('Unknown replay metric')
        if int(row['dpi'])!=2 or int(row['process_blocks'])!=12 or int(row['trials_per_process'])!=(5 if row['backend']=='cpu' else 3):
            raise ValueError('Unexpected primary replay block/trial factors')
    if any(row['mode']!='cpu' or int(row['n_blocks'])!=12 for row in application):raise ValueError('Unexpected Alustin statistics factors')
    if any(row['process_blocks']!=12 or row['trials_per_process']!=5 for row in budget):raise ValueError('Unexpected boundary statistics factors')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--lead',type=Path,help='Editorial assessment authored after reviewing preserved estimates and audits')
    parser.add_argument('--tables-only',action='store_true',help='Collect descriptive estimates while independent audits are pending')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();root=args.root.resolve(strict=True)
    phase_path=root/'analysis/replay/phase/summary.csv';sequence_path=root/'analysis/replay/sequence/summary.csv'
    app_path=root/'alustin/analysis/summary.csv';budget_path=root/'budget-timing/analysis.json'
    phases=csv_rows(phase_path);sequences=csv_rows(sequence_path);application=csv_rows(app_path);budget=complete(budget_path)['effects']
    validate(root,phases,sequences,application,budget)
    audits=[root/'independent-source-build-audit.json',root/'independent-native-offset-oracle-source-audit.json',
        root/'independent-native-offset-oracle-build-audit.json',root/'independent-identity-pixel-audit.json',
        root/'independent-replay-statistics-audit.json',root/'alustin/independent-app-statistics-audit.json',
        root/'alustin/independent-order-audit.json',root/'budget/independent-budget-audit.json']
    audit_state={str(path):path.exists() and read(path).get('complete') is True for path in audits}
    if not args.tables_only and not all(audit_state.values()):raise ValueError('Final report requires all completed independent audits; use --tables-only for descriptive collection')
    parts=['# Revised Swash outline-cache measurements','']
    if args.lead:parts.extend([args.lead.read_text().strip(),''])
    if args.tables_only:parts.extend(['These are descriptive tables from completed preserved estimates. Independent-audit status is recorded in the metrics JSON; this collection does not supply an editorial acceptance conclusion.',''])
    parts.extend(['Four freshly built versions share one campaign: master, the committed selected arena (`prior`), the captured fixes 4–5 tree (`updated45`), and the complete revised tree (`final`). Historical observations remain preserved and are not pooled here. **Final/master is the primary acceptance comparison.** The other columns isolate the minimum-growth/typed-run changes and then the routing/key/target fixes. All six pairings remain in the complete statistics.','',
        'Cells show median paired duration change, an exploratory 95% whole-block bootstrap interval, and paired absolute change. Negative durations mean faster. Absolute columns are process-median ms; median paired percentages need not equal ratios of those absolute medians. Small differences are shown in µs. Intervals have no multiplicity or selection adjustment.',''])
    headers=['Font','Scene / phase','Measurement','Master ms','Final ms',*PAIR_NAMES]
    for title,predicate in [('First reported paint',lambda r:r['phase']=='first_paint' and not r['scene'].startswith('grid_')),
        ('Warm example redraws',lambda r:r['phase']=='warm' and not r['scene'].startswith('grid_')),
        ('Every other reported example phase',lambda r:r['phase'] not in ('first_paint','warm') and not r['scene'].startswith('grid_')),
        ('Controlled population, reuse and miss-churn phases',lambda r:r['scene'].startswith('grid_'))]:
        rows=[]
        selected=[row for row in phases if primary(row) and unique_font(row) and predicate(row) and
                  (row['reference_version'],row['candidate_version'])==PAIRS[0]]
        for row in sorted(selected,key=lambda r:(r['backend'],r['font'],r['scene'],r['phase'])):
            base={key:row[key] for key in ('backend','font','dpi','scene','phase','metric')}
            rows.append([FONTS[row['font']],f"{row['scene']}/{row['phase']}",'CPU draw' if row['backend']=='cpu' else 'GPU completion',*values(phases,base,'phase')])
        parts.extend(['## '+title,'',table(headers,rows),''])
    parts.extend(['GPU completion includes CPU drawing, submission and waiting; it is not a GPU timestamp. Variation-scene/unique-weight repeats under other regular-font factors are the same Roboto control, so tables show them once. Every controlled frame retains exactly 94 fresh atlas keys. Unique sizes/weights expose low reuse; pollution includes the hot frames, 64-size sweep and hot return.','',
        '## Complete reported sequences','',
        'Each controlled sequence includes its population and churn. Example totals include every reported phase, but exclude 119 unreported warmup frames and are not launch-to-end durations. Each trial is summed before process medians and pairing.',''])
    rows=[]
    for row in sorted([r for r in sequences if primary(r) and unique_font(r) and (r['reference_version'],r['candidate_version'])==PAIRS[0]],
                      key=lambda r:(r['backend'],r['font'],r['scene'])):
        base={key:row[key] for key in ('backend','font','dpi','scene','metric')}
        rows.append([FONTS[row['font']],SCENES.get(row['scene'],row['scene']),row['reported_frames'],
                     'CPU draw' if row['backend']=='cpu' else 'GPU completion',*values(sequences,base,'sequence')])
    parts.extend([table(['Font','Reported sequence','Frames','Measurement','Master ms','Final ms',*PAIR_NAMES],rows),'',
        '## Alustin renderer-thread CPU','',
        'First paint and filtered-search spans measure renderer-thread host work, not GPU-completion or display latency. Search can populate new atlas entries; it is not necessarily a fully warm redraw.',''])
    rows=[]
    for font in ('roboto','vollkorn','ptsans'):
        for backend in ('winit-femtovg-wgpu','winit-femtovg'):
            for metric,label in APP_METRICS.items():
                rows.append([FONTS[font],'WGPU' if backend.endswith('wgpu') else 'OpenGL',label,
                    *values(application,dict(mode='cpu',font=font,backend=backend,metric=metric),'app')])
    parts.extend([table(['Font','Backend','Frame','Master ms','Final ms',*PAIR_NAMES],rows),'',
        '## Process high-water RSS','',
        'RSS includes the application, renderer, fonts, driver and transient work. It is not the outline cache alone or device VRAM. These cells show absolute paired MiB change and its preserved 95% interval.',''])
    rows=[]
    for font in ('roboto','vollkorn','ptsans'):
        for backend in ('winit-femtovg-wgpu','winit-femtovg'):
            selected=[one(application,mode='cpu',font=font,backend=backend,metric='peak_rss_mib',reference=a,candidate=b) for a,b in PAIRS]
            def rss(row):
                low,high=ci(row['median_paired_delta_ci95'])
                return f"{float(row['median_paired_delta']):+.3f} [{low:+.3f}, {high:+.3f}] MiB"
            rows.append([FONTS[font],'WGPU' if backend.endswith('wgpu') else 'OpenGL',*map(rss,selected)])
    parts.extend([table(['Font','Backend',*PAIR_NAMES],rows),'','## Targeted public-API cache boundary','',
        'Roboto working sets contain 3300/3440/3600 geometry keys across ten phase-specific fresh Canvas/atlas instances sharing one TextContext. Population is shown separately, reuse contains all nine later phases, and complete10 includes both. This targeted synthetic test models retained geometry across fresh atlases; it does not establish application latency or infer outline hits from atlas counts. Timing excludes font registration and Canvas creation/destruction. Every phase still rasterizes masks.',''])
    rows=[]
    for keys in (3300,3440,3600):
        for scope in ('population','reuse9','complete10'):
            rows.append([keys,scope,*values(budget,dict(keys=keys,scope=scope),'budget')])
    parts.extend([table(['Keys','Scope','Master ms','Final ms',*PAIR_NAMES],rows),'',
        '## Exploratory positive-interval audit','',
        'The following preserved intervals lie entirely above zero for a displayed comparison. This lists tiny absolute effects as well as larger ones. It is an exploratory selection of correlated phase/sequence/application/boundary observations, not an adjusted test of universal regression. Every uncertain or negative effect remains in the full tables/statistics.',''])
    increases=[];metrics=[]
    for kind,source in [('phase',phases),('sequence',sequences),('app',application),('budget',budget)]:
        for row in source:
            if kind in ('phase','sequence'):
                if not primary(row) or not unique_font(row):continue
                pair=row['reference_version'],row['candidate_version']
                label=f"{FONTS[row['font']]} {row['backend']} {row['scene']}"+(('/'+row['phase']) if kind=='phase' else ' total')
            elif kind=='app':
                if row['metric'] not in APP_METRICS:continue
                pair=row['reference'],row['candidate'];label=f"Alustin {FONTS[row['font']]} {row['backend']} {APP_METRICS[row['metric']]}"
            else:pair=row['reference'],row['candidate'];label=f"Boundary {row['keys']} keys {row['scope']}"
            if pair not in PAIRS:continue
            value=normalized(row,kind);record={'kind':kind,'label':label,**value,'source_row':row};metrics.append(record)
            if value['ci95_pct'][0]>0:increases.append([label,PAIR_NAMES[PAIRS.index(pair)],effect(row,kind)])
    parts.extend([table(['Observation','Comparison','Duration increase'],increases) if increases else 'No preserved interval in this declared scope lies entirely above zero.','',
        '## Correctness and limits','',
        'Final is validated against a separately built uncached-master native renderer whose atlas identity is constructed from actual raster-offset f32 bits, with signed zero normalized. Only master text.rs changes for the oracle; none of the arena, signed-bin implementation or other fixes are copied. All 168 final captures match that oracle. Prior/updated45 remain legacy-master parity. The original-master difference is retained; `rgba_identical` in accepted final rows means oracle parity, not unchanged legacy output. The rejected original equality cohort remains preserved. Alustin retains all 18 exact master comparisons and actual primary/fallback font byte diagnostics.','',
        '**The 1 MiB cache target is soft accounting, not a bound on total heap or RSS.** It charges shared-vector capacities, logical key/range metadata and public scratch length high-water. Inaccessible native spare capacities, hash-map spare capacity, allocator overhead, shared ScaleContext and transient work are excluded. Cache residency and allocator growth behavior matter; allocation requests are not proof that all old capacities were physically copied. A cache hit avoids native outline scaling/hinting while masks remain phase-specific.','',
        'The study uses 12 planned Williams blocks/rounds with five CPU or three GPU example trials per process and five boundary trials. No timing-based trimming or retries are used. Alustin retries only whole query-contaminated blocks and preserves attempts; the independent order proof records accepted counts. These results describe this machine and these workloads, with exploratory unadjusted intervals. Swash and transitive dependencies are unchanged. The implementation remains internal to FemtoVG and Swash-only.','',
        '## Preserved evidence and reproduction','',
        'Three added archives retain all accepted/rejected raw records, frozen sources, native-oracle captures, validation overlays, actual-font evidence and targeted boundary data: `updated-cache-examples`, `updated-cache-alustin`, `updated-cache-source-bundle`. Prior reports/archives and the original vendor bundle remain unchanged. See [reproduction](docs/revised-cache-reproduction.md), [phase statistics](analysis/updated-cache-examples/summary.csv), [sequence statistics](analysis/updated-cache-sequences/summary.csv), and [Alustin statistics](analysis/updated-cache-alustin/summary.csv). All six comparisons remain available even though these tables highlight three.',''])
    destination=args.output or root/'REVISED-OUTLINE-CACHE-TABLES.md'
    destination.write_text('\n'.join(parts).rstrip()+'\n')
    inputs={'script':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'files':{}}
    paths=[phase_path,sequence_path,app_path,budget_path,root/'runtime/core/experiment.json',root/'machine.json',root/'final-validation.json',
           root/'analysis/replay/phase/summary-methodology.json',root/'analysis/replay/sequence/methodology.json',
           root/'budget-timing/provenance.json',root/'alustin/cpu/summary.json',root/'examples-validated/pixels-provenance.json']
    paths += [path for path in audits if audit_state[str(path)]]
    if args.lead:paths.append(args.lead)
    for path in paths:inputs['files'][str(path.resolve())]={'sha256':sha(path),'bytes':path.stat().st_size}
    destination.with_suffix('.inputs.json').write_text(json.dumps(inputs,indent=2,sort_keys=True)+'\n')
    (root/'revised-cache-metrics.json').write_text(json.dumps({'complete':True,'descriptive_only':True,'versions':VERSIONS,
        'displayed_pairs':PAIRS,'all_comparisons_preserved':True,'independent_audits':audit_state,'primary_observations':metrics,
        'positive_interval_observations':increases,'source_inputs':inputs,'report':str(destination)},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'report':str(destination),'primary_observations':len(metrics),'positive_interval_observations':len(increases),
        'all_independent_audits_complete':all(audit_state.values()),'computed_statistics_or_intervals':False}))

if __name__=='__main__':main()
