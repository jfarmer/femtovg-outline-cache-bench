#!/usr/bin/env python3
"""Run a freshly built replay or Alustin cohort, retaining every raw attempt."""
import argparse,datetime,json,platform,subprocess,sys
from pathlib import Path
from benchlib import sha,write_json

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite',choices=('replay','app'));parser.add_argument('mode',choices=('cpu','gpu','pixels','startup'))
    parser.add_argument('--runtime',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args,extra=parser.parse_known_args();runtime=args.runtime.resolve(strict=True)
    prep=json.loads((runtime/'prepare-provenance.json').read_text())
    if args.suite=='replay':
        if args.mode=='startup':parser.error('startup belongs to the app suite')
        command=[sys.executable,str(runtime/'core/run.py'),args.mode,'--root',str(runtime/'core'),'--output',str(args.output.resolve())]
    else:
        if args.mode=='gpu':parser.error('App CPU/startup/pixels use the configured real GPU backends')
        if not prep['alustin_checkout']:parser.error('Prepare with --alustin-checkout for app runs')
        command=[sys.executable,str(runtime/'app/run.py'),args.mode,'--root',prep['alustin_checkout'],'--output',str(args.output.resolve())]
    # Drivers independently verify completed build records, binaries, sources and factors.
    emoji=Path('/System/Library/Fonts/Apple Color Emoji.ttc')
    provenance={'schema':1,'suite':args.suite,'mode':args.mode,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'platform':platform.platform(),'command':command+extra,'wrapper_sha256':sha(__file__),
        'prepare_provenance_sha256':sha(runtime/'prepare-provenance.json'),
        'optional_replay_apple_emoji':{'path':str(emoji),'available':emoji.is_file(),
            'sha256':sha(emoji) if args.suite=='replay' and emoji.is_file() else None},'complete':False}
    try:
        subprocess.run(command+extra,check=True);provenance['complete']=True
    finally:
        write_json(args.output.resolve()/(args.mode+'-portable-run-provenance.json'),provenance)

if __name__=='__main__':main()
