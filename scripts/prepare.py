#!/usr/bin/env python3
"""Verify pinned bundles and prepare relocated copies in a fresh run directory."""
import argparse,datetime,json,shutil
from pathlib import Path
from benchlib import REPO,bundled_manifest,records,write_json,sha

def replace(path,old,new):
    text=path.read_text();count=text.count(old)
    if count!=1:raise ValueError(f'Expected one relocation marker in {path}: {old!r}, found {count}')
    path.write_text(text.replace(old,new))
    return {'file':str(path),'old':old,'new':new,'count':count}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--alustin-checkout',type=Path,help='Optional pinned Alustin checkout for application builds/runs')
    args=parser.parse_args();manifest=bundled_manifest();output=args.output.resolve()
    if any(character in str(output) for character in ('"', "'", '\\', '\n', '\r')):parser.error('Runtime paths must avoid quote, backslash and newline characters used by original source literals')
    if output.exists():parser.error('--output must be a fresh directory')
    if output.is_relative_to(REPO/'vendor') or output.is_relative_to(REPO/'results'):parser.error('Runtime output cannot overwrite bundled/archive inputs')
    output.mkdir(parents=True)
    shutil.copytree(REPO/'vendor/runtime/core',output/'core');shutil.copytree(REPO/'vendor/runtime/app',output/'app')
    shutil.copytree(REPO/'assets',output/'assets');shutil.copytree(REPO/'vendor/app-inputs',output/'app-inputs')
    app=args.alustin_checkout.resolve(strict=True) if args.alustin_checkout else output/'alustin-checkout-required'
    if any(character in str(app) for character in ('"', "'", '\\', '\n', '\r')):parser.error('Alustin checkout path contains an unsupported source-literal character')
    assets=output/'assets';changes=[]
    core=output/'core';app_runtime=output/'app'
    changes.append(replace(core/'runner/src/main.rs','/Users/jesse/github/femtovg/examples/assets',str(assets)))
    # Existing full-path markers are deliberate, guarded substitutions on fresh copies.
    mapping={
      '/Users/jesse/github/femtovg/examples/assets':str(assets),
      '/Users/jesse/github/alustin-gui-v2/crates/alustin-gui/assets/fonts/Vollkorn-Medium.ttf':str(assets/'Vollkorn-Medium.ttf'),
      '/private/tmp/femtovg-open-font-search/candidate-agent/PTSans-Regular.ttf':str(assets/'PTSans-Regular.ttf'),
      '/private/tmp/femtovg-liberation-font-review/liberation-fonts-ttf-2.1.5/LiberationSerif-Regular.ttf':str(assets/'LiberationSerif-Regular.ttf'),
    }
    for old,new in mapping.items():changes.append(replace(core/'run.py',old,new))
    changes.append(replace(app_runtime/'baseline_run_helpers.py','/Users/jesse/github/alustin-gui-v2',str(app)))
    # The Vollkorn expression used ROOT; relocate it to the frozen asset instead.
    changes.append(replace(app_runtime/'baseline_run_helpers.py','ROOT / "crates/alustin-gui/assets/fonts/Vollkorn-Medium.ttf"','Path('+repr(str(assets/'Vollkorn-Medium.ttf'))+')'))
    for old,new in list(mapping.items())[0:1]+list(mapping.items())[2:]:
        changes.append(replace(app_runtime/'baseline_run_helpers.py',old,new))
    for suite in (core,app_runtime):
        target=suite/'verify_ready.py';old_sha=sha(target)
        shutil.copy2(REPO/'scripts/portable_verify_ready.py',target)
        changes.append({'file':str(target),'kind':'Fresh-build preflight guard; historical verifier retained in vendor/archive',
                        'original_sha256':old_sha,'runtime_sha256':sha(target)})
    # App's Roboto expression appends a file to the original assets marker? It is a full-path literal.
    # The prefix substitution above preserves the existing basename.
    write_json(output/'prepare-provenance.json',{'schema':1,'complete':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'repository':str(REPO),'bundle_manifest_sha256':sha(REPO/'vendor/manifest.json'),'pins':manifest['pins'],'versions':manifest['versions'],
        'alustin_checkout':str(app) if args.alustin_checkout else None,'relocations':changes,'prepared_files':records(output),
        'prepare_script_sha256':sha(__file__),'policy':'Fresh runtime only; source snapshots and historical records remain unchanged; no historical binary reuse'})
    print(output)

if __name__=='__main__':main()
