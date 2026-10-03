#!/usr/bin/env python3
"""Run both frozen cost cohorts serially; stop on errors and preserve all output."""
import argparse
from datetime import datetime,timezone
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def info(path):
    path=path.resolve(strict=True)
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return dict(path=str(path),sha256=digest,bytes=path.stat().st_size)
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    if output.exists():raise ValueError('Fresh serial diagnostic output required')
    cohorts=[('default',ROOT/'mechanism-cost-screen/run_cost_campaign.py'),
             ('weights',ROOT/'mechanism-weight-cost-screen/run_weight_cost_campaign.py')]
    record=dict(complete=False,created_utc=datetime.now(timezone.utc).isoformat(),
        driver=info(Path(__file__)),processes_expected=18,raw_rows_expected=12960,
        scope='Two separately frozen serial warm-cost cohorts: default6fonts10processes plus Noto300/400weights8processes. No analysis, CI or app-percentage claim.',campaigns=[])
    for name,driver in cohorts:
        selection=driver.parent/'selection-frozen.json'
        assert json.loads(selection.read_text())['complete']
        record['campaigns'].append(dict(label=name,driver=info(driver),selection=info(selection),
            complete=False,command=[sys.executable,'-B',str(driver),'run','--output',str(output/name)]))
    output.mkdir(parents=True);write(output/'campaign-plan.json',record)
    for item in record['campaigns']:
        print('START',item['label'],flush=True)
        item['started_utc']=datetime.now(timezone.utc).isoformat();write(output/'campaign-plan.json',record)
        status=subprocess.run(item['command']).returncode
        item.update(complete=status==0,exit_code=status,finished_utc=datetime.now(timezone.utc).isoformat())
        write(output/'campaign-plan.json',record)
        if status:raise SystemExit(status)
    record.update(complete=True,finished_utc=datetime.now(timezone.utc).isoformat())
    write(output/'campaign-plan.json',record);print('Both serial cost cohorts complete',flush=True)
if __name__=='__main__':main()
