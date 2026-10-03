#!/usr/bin/env python3
"""Tiny synthetic acceptance/rejection checks, without builds or benchmarks."""
import csv, hashlib, importlib, json, sys, tempfile
from pathlib import Path

overlay=Path(sys.argv[1]).resolve(strict=True)
sys.path.insert(0,str(overlay))
run=importlib.import_module('run');helpers=importlib.import_module('oracle_ledger')
summary=importlib.import_module('summarize');sequence=importlib.import_module('sequence_totals')
audit=importlib.import_module('independent_raw_replay_audit')
fixture=Path(tempfile.mkdtemp(prefix='native-oracle-ledger-guard-',dir='/private/tmp'))
def write(name,value):
    path=fixture/name;path.write_text(json.dumps(value));return path
def info(path):return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
proof=write('prepare.json',{'complete':True,'label':'native-master-offset-oracle','changed_files':['src/text.rs']})
build=write('build.json',{'complete':True,'prepare_sha256':info(proof)['sha256']})
ledger={'schema':1,'complete':True,'versions':list(run.VERSIONS),'oracle_label':'native-master-offset-oracle',
    'oracle_prepare':info(proof),'oracle_build':info(build),'master_binary':{'path':'synthetic-master','sha256':'0'*64},
    'launches':[],'configurations':[]}
for font in ('stock','vollkorn','ptsans'):
    for dpi in (1,2):
        phases=[]
        for scene,items in run.PHASES.items():
            for phase,frames in items.items():
                count=94*frames if scene.startswith('grid_') else 100
                counts={version:count for version in run.VERSIONS}
                if (font,dpi,scene,phase)==('stock',1,'text','size_advance'):counts['final']+=2
                width,height=(800,700) if scene=='font_variations' else (1000,600)
                phases.append({'scene':scene,'phase':phase,'frames':frames,'counts':counts,
                    'oracle_snapshot':{'path':'synthetic-image-not-opened','bytes':width*height*4,'sha256':'0'*64}})
        ledger['configurations'].append({'font':font,'dpi':dpi,'phases':phases})
        ledger['launches'].extend({'font':font,'dpi':dpi,'label':label,'complete':True,'font_sha256':'0'*64}
                                  for label in ('master','oracle'))
ledger_path=write('ledger.json',ledger);expected=helpers.verify_record(info(ledger_path),run.PHASES,run.VERSIONS)
rows={};indexed=[];launches=[]
for version in run.VERSIONS:
    values=[]
    for trial in range(2):
        for (scene,phase),entry in expected['stock',1].items():
            values.append({'scene':scene,'phase':phase,'trial':str(trial),'frames':str(entry['frames']),
                'draw_us':'1.0','submit_us':'2.0','complete_us':'3.0','new_atlas_entries':str(entry['counts'][version])})
    rows[version]=values;stdout=fixture/(version+'.csv')
    with stdout.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=run.CSV_FIELDS);writer.writeheader();writer.writerows(values)
    launches.append({'block':1,'font':'stock','dpi':1,'version':version,'validated':True,'exit_code':0,
                     'stdout':str(stdout),'rows':len(values)})
    indexed.extend({'backend':'cpu','font':'stock','dpi':'1','block':'1','version':version,**row} for row in values)
run.validate_block(rows,'stock',1,expected)
bad={version:[dict(row) for row in values] for version,values in rows.items()}
target=next(row for row in bad['final'] if (row['scene'],row['phase'],row['trial'])==('text','size_advance','0'))
target['new_atlas_entries']='104'
try:run.validate_block(bad,'stock',1,expected)
except ValueError:pass
else:raise AssertionError('Undeclared final count accepted')
target=next(row for row in bad['prior'] if (row['scene'],row['phase'],row['trial'])==('text','size_advance','0'))
target['new_atlas_entries']='102'
try:run.validate_block(bad,'stock',1,expected)
except ValueError:pass
else:raise AssertionError('Legacy count drift accepted')
selected=[row for row in indexed if (row['scene'],row['phase'])==('text','size_advance')]
frames,counts=helpers.phase_counts(selected,run.VERSIONS)
assert frames==12 and counts=={'master':100,'prior':100,'updated45':100,'final':102}
sequences=sequence.totals(indexed);_,total_counts=helpers.phase_counts(sequences['stock',1,'text'],run.VERSIONS)
assert total_counts=={'master':800,'prior':800,'updated45':800,'final':802}
summary.write_csv(fixture/'counts.csv',[{'new_atlas_entries':counts}])
assert json.loads(next(csv.DictReader((fixture/'counts.csv').open()))['new_atlas_entries'])==counts
metadata={'complete':True,'mode':'cpu','versions':list(run.VERSIONS),'blocks':1,'trials_per_process':2,
    'fonts':['stock'],'dpis':[1],'phases':run.PHASES,'launches':launches,'oracle_ledger':info(ledger_path),
    'binaries':{'master':{'sha256':'0'*64}},'font_files':{'stock':{'sha256':'0'*64}}}
write('cpu-provenance.json',metadata)
with (fixture/'cpu-results.csv').open('w',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=run.RESULT_FIELDS);writer.writeheader();writer.writerows(indexed)
assert len(summary.read_mode(fixture,'cpu')[1])==224
assert len(audit.validate_raw(fixture,'cpu',list(run.VERSIONS))[1])==224
print(json.dumps({'complete':True,'synthetic_only':True,'builds_or_benchmarks':False,
    'fixture':str(fixture),'checks':['declared per-version count difference accepted','undeclared final count rejected',
    'legacy count drift rejected','per-version phase/sequence counts preserved','CSV version maps are JSON',
    'analyzer retained stdout validation passes','independent exact-ledger raw validation passes']}))
