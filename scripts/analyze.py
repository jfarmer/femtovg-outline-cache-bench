#!/usr/bin/env python3
"""Analyze fresh runtime measurements with the bundled original methods."""
import argparse,subprocess,sys
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('suite',choices=('replay','app'))
    parser.add_argument('--runtime',type=Path,required=True);parser.add_argument('--results',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--bootstrap',type=int,default=10000)
    parser.add_argument('--seed',type=int,default=72531);parser.add_argument('--modes',choices=('cpu','gpu'),nargs='+')
    args=parser.parse_args();runtime=args.runtime.resolve(strict=True);output=args.output.resolve()
    if output.exists():parser.error('--output must be new; preserve previous analysis')
    if args.suite=='replay':
        if len(args.results)!=1:parser.error('Replay analysis accepts one combined timing directory')
        root=args.results[0].resolve(strict=True);modes=args.modes or [mode for mode in ('cpu','gpu') if (root/(mode+'-provenance.json')).exists()]
        if not modes:parser.error('No completed replay timing modes found')
        for name,folder in (('summarize.py','phase'),('sequence_totals.py','sequence')):
            subprocess.run([sys.executable,str(runtime/'core'/name),'--root',str(root),'--output',str(output/folder),
                '--modes',*modes,'--bootstrap',str(args.bootstrap),'--seed',str(args.seed)],check=True)
    else:
        subprocess.run([sys.executable,str(runtime/'app/analyze.py'),*[str(p.resolve(strict=True)) for p in args.results],
            '--output',str(output),'--bootstrap',str(args.bootstrap),'--seed',str(args.seed)],check=True)

if __name__=='__main__':main()
