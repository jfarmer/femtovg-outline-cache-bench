#!/usr/bin/env python3
"""Package frozen cohort inputs once, without changing historical records."""
import argparse, datetime, json, shutil
from pathlib import Path
from benchlib import REPO, records, hashes, write_json

CORE_HELPERS=('run.py','summarize.py','sequence_totals.py','build_replay.py','experiment.json','snapshot-provenance.json','verify_ready.py')
APP_HELPERS=('run.py','analyze.py','build.py','experiment.json','benchmark_helpers.py','baseline_build_helpers.py','baseline_run_helpers.py','baseline_analysis_helpers.py','verify_actual_fonts.py','verify_ready.py')

def copy(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    if source.is_dir():shutil.copytree(source,destination)
    else:shutil.copy2(source,destination)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core',type=Path,required=True)
    parser.add_argument('--app',type=Path,required=True)
    parser.add_argument('--app-baseline',type=Path,default=Path('/private/tmp/alustin-font-outline-review/build'))
    parser.add_argument('--vollkorn',type=Path,default=Path('/Users/jesse/github/alustin-gui-v2/crates/alustin-gui/assets/fonts/Vollkorn-Medium.ttf'))
    parser.add_argument('--ptsans',type=Path,default=Path('/private/tmp/femtovg-open-font-search/candidate-agent/PTSans-Regular.ttf'))
    parser.add_argument('--liberation',type=Path,default=Path('/private/tmp/femtovg-liberation-font-review/liberation-fonts-ttf-2.1.5/LiberationSerif-Regular.ttf'))
    args=parser.parse_args();core=args.core.resolve(strict=True);app=args.app.resolve(strict=True)
    vendor=REPO/'vendor';runtime=vendor/'runtime'
    if runtime.exists() or (vendor/'manifest.json').exists():parser.error('Runtime bundle already exists; never overwrite frozen inputs')
    experiment=json.loads((core/'experiment.json').read_text())
    if json.loads((app/'experiment.json').read_text())['versions']!=experiment['versions']:raise ValueError('Core/app versions differ')
    frozen=json.loads((core/'snapshot-provenance.json').read_text())
    for variant in experiment['versions']:
        if hashes(core/'snapshots'/variant)!=frozen[variant]['source_files']:raise ValueError(f'Changed frozen source: {variant}')
        copy(core/'snapshots'/variant,runtime/'core/snapshots'/variant)
    for name in CORE_HELPERS:copy(core/name,runtime/'core'/name)
    for name in ('runner','instrumentation'):copy(core/name,runtime/'core'/name)
    for cache in (runtime/'core').rglob('__pycache__'):shutil.rmtree(cache)
    for name in APP_HELPERS:copy(app/name,runtime/'app'/name)
    baseline=args.app_baseline.resolve(strict=True)
    for name in ('provenance.json','app-original.Cargo.lock','resolved.Cargo.lock','app-input.diff','dependency-graph.json'):
        copy(baseline/name,vendor/'app-inputs'/name)
    assets=REPO/'assets';base=core/'snapshots/current/examples/assets'
    for name in ('RobotoFlex-VariableFont.ttf','amiri-regular.ttf','entypo.ttf','BungeeColor-Subset.ttf','pattern.jpg','images'):
        copy(base/name,assets/name)
    for source,name in ((args.vollkorn,'Vollkorn-Medium.ttf'),(args.ptsans,'PTSans-Regular.ttf'),(args.liberation,'LiberationSerif-Regular.ttf')):copy(source,assets/name)
    for source,name in ((args.vollkorn.parent/'OFL.txt','Vollkorn-OFL.txt'),(args.ptsans.parent/'PTSans-OFL.txt','PTSans-OFL.txt'),(args.liberation.parent/'LICENSE','Liberation-LICENSE.txt'),(base/'LICENSE-BungeeColor','BungeeColor-OFL.txt')):
        copy(source,assets/'licenses'/name)
    required=('RobotoFlex-OFL.txt','Amiri-OFL.txt','Entypo-CC-BY-SA-4.0.txt','Vollkorn-OFL.txt','PTSans-OFL.txt','Liberation-LICENSE.txt','BungeeColor-OFL.txt')
    if any(not (assets/'licenses'/name).is_file() for name in required):raise ValueError('Font license missing; do not freeze an incomplete bundle')
    inventory={}
    for name in ('vendor','assets'):inventory.update({name+'/'+k:v for k,v in records(REPO/name).items()})
    write_json(vendor/'manifest.json',{'schema':1,'complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'versions':experiment['versions'],'pins':{'femtovg_master':experiment['baseline_master'],'femtovg_current':experiment['baseline_current'],
        'alustin':json.loads((baseline/'provenance.json').read_text())['app_commit']},'original_core_root':str(core),'original_app_root':str(app),
        'files':inventory,'policy':'Historical helpers unaltered; runtime relocation occurs only in new prepare output; compiled executables excluded'})
    print('Bundled frozen runtime inputs; every version must be rebuilt for a fresh run')

if __name__=='__main__':main()
