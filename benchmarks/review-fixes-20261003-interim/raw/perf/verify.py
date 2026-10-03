#!/usr/bin/env python3
"""Untimed provenance checks before comparing frozen binaries."""
import argparse
import datetime
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRODUCTION = ['src/lib.rs', 'src/text.rs', 'src/text/font.rs', 'src/text/swash_rasterizer.rs']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def graph(metadata):
    package = {p['id']: p for p in metadata['packages']}
    root = metadata['resolve']['root']
    identity = lambda item: (package[item]['name'], package[item]['version'], package[item]['source'])
    nodes = []
    for node in metadata['resolve']['nodes']:
        if node['id'] == root:
            continue
        dependencies = sorted((identity(dep['pkg']), sorted((edge['kind'] or '', str(edge['target'] or '')) for edge in dep['dep_kinds'])) for dep in node['deps'])
        nodes.append((identity(node['id']), sorted(node['features']), dependencies))
    return sorted(nodes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', default='final')
    args = parser.parse_args()
    reference = {}
    records = []
    variants = ['master', 'base', 'final', 'ordinary-inline']
    if args.candidate not in variants:
        variants.append(args.candidate)
    for variant in variants:
        for feature in ['swash_only', 'default_swash', 'default_no_swash']:
            name = f'{variant}-{feature}'
            build = json.loads((ROOT / 'builds' / f'{name}.json').read_text())
            metadata = json.loads((ROOT / 'builds' / f'{name}.metadata.json').read_text())
            normalized = graph(metadata)
            if feature in reference and normalized != reference[feature]:
                raise SystemExit(f'Dependency/features graph differs: {name}')
            reference.setdefault(feature, normalized)
            artifact_features = build['femtovg_artifact']['features']
            if ('swash' in artifact_features) != (feature != 'default_no_swash'):
                raise SystemExit(f'Wrong FemtoVG feature configuration: {name} {artifact_features}')
            for kind, executable in build['executables'].items():
                if sha(Path(executable['binary_path'])) != executable['binary_sha256']:
                    raise SystemExit(f'Binary changed: {name}-{kind}')
            records.append({'variant': variant, 'feature': feature, 'dependency_graph_sha256': hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest(), 'femtovg_features': artifact_features})
    frozen = json.loads((ROOT / f'source-{args.candidate}.json').read_text())['files']
    live_root = Path('/Users/jesse/github/femtovg')
    for path in PRODUCTION:
        if sha(live_root / path) != frozen[path]:
            raise SystemExit(f'Final production source no longer matches working tree: {path}')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=live_root, text=True).strip()
    head_matches = all(hashlib.sha256(subprocess.check_output(['git', 'show', f'{head}:{path}'], cwd=live_root)).hexdigest() == frozen[path] for path in PRODUCTION)
    result = {'candidate': args.candidate, 'dependency_graphs_equal_per_feature': True, 'binary_hashes_verified': True,
              'verified_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'live_head': head,
              'head_production_matches_snapshot': head_matches,
              'final_production_matches_working_tree': True, 'production_files': {path: frozen[path] for path in PRODUCTION}, 'builds': records}
    (ROOT / f'provenance-verification-{args.candidate}.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Verified matching dependency/features graphs, all binary hashes, and exact final production source.')


if __name__ == '__main__':
    main()
