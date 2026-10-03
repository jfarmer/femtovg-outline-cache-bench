#!/usr/bin/env python3
"""Verify/extract the revised frozen source bundle and prepare a fresh runtime."""
import argparse,subprocess,sys
from pathlib import Path
from benchlib import REPO,ArchiveStore
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--alustin-checkout',type=Path)
    parser.add_argument('--with-budget',action='store_true')
    args=parser.parse_args();output=args.output.resolve()
    if output.exists():parser.error('--output must be fresh')
    if output.is_relative_to(REPO/'results') or output.is_relative_to(REPO/'vendor'):parser.error('Output cannot replace archived inputs')
    output.mkdir(parents=True)
    ArchiveStore().inspect('updated-cache-source-bundle',output/'bundle')
    command=[sys.executable,str(output/'bundle/scripts/prepare.py'),'--output',str(output/'runtime')]
    if args.alustin_checkout:command+=['--alustin-checkout',str(args.alustin_checkout.resolve(strict=True))]
    subprocess.run(command,check=True)
    if args.with_budget:
        command=[sys.executable,str(REPO/'benchmarks/revised-cache-budget/bench.py'),'prepare','--output',str(output/'budget-runtime')]
        for variant in ('master','prior','updated45','final'):command+=['--source',variant,str(output/'runtime/core/snapshots'/variant)]
        subprocess.run(command,check=True)
    print(output)
if __name__=='__main__':main()
