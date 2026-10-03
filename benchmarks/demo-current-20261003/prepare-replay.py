#!/usr/bin/env python3
"""Prepare a relocated replay copy; this command performs no build or timing."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

STUDY = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cohort-root', type=Path, default=STUDY / 'raw/current')
    args = parser.parse_args()
    original, work, out = args.cohort_root.resolve(), args.work_dir.resolve(), args.output.resolve()
    if out.exists() or out.is_symlink():
        raise SystemExit(f'Refusing to overwrite replay workspace: {out}')
    if out.is_relative_to(STUDY) or out.is_relative_to(original):
        raise SystemExit('Replay workspace must be outside immutable archived evidence.')
    plan = json.loads((original / 'PLAN.json').read_text())
    builds_path = work / 'scenes/builds.json'
    builds = json.loads(builds_path.read_text())
    records = {f'{r["variant"]}-{r["feature"]}': r for r in builds['records'] if r['kind'] == 'scenes'}
    if set(records) != set(plan['binaries']):
        raise SystemExit('Expected exactly the four rebuilt master/final scene configurations.')
    for label, record in records.items():
        if sha(record['binary']) != record['sha256']:
            raise SystemExit(f'Rebuilt executable changed: {label}')
    old_assets = Path(plan['source_and_build_provenance']['scene_setup']) / 'assets'
    rebound_assets = {}
    for original_path, expected in plan['external_scene_assets'].items():
        relative = Path(original_path).relative_to(old_assets)
        relocated = work / 'scenes/assets' / relative
        if sha(relocated) != expected:
            raise SystemExit(f'Fixed scene asset differs: {relative}')
        rebound_assets[str(relocated)] = expected
    emoji = plan['optional_host_emoji_font']
    present = Path(emoji['path']).exists()
    if present != emoji['present'] or (present and sha(emoji['path']) != emoji['sha256']):
        raise SystemExit('Host optional emoji-font state differs. Record a changed environment explicitly before attempting a different-font replay.')
    out.mkdir(parents=True)
    for file in ['run-demo.py', 'guard.py']:
        shutil.copy2(original / file, out / file)
    for directory in ['assets', 'provenance']:
        shutil.copytree(original / directory, out / directory)
    shutil.copy2(original / 'PLAN.json', out / 'provenance/original-plan.json')
    shutil.copy2(builds_path, out / 'provenance/reproduction-builds.json')
    for label, record in records.items():
        relative = f'provenance/rebuilt-{label}.json'
        (out / relative).write_text(json.dumps(record, indent=2) + '\n')
        plan['binaries'][label] = {'binary_path': record['binary'], 'binary_sha256': record['sha256'], 'build_record': relative}
    plan['external_scene_assets'] = rebound_assets
    plan['source_and_build_provenance']['scene_setup'] = str(work / 'scenes')
    plan['source_and_build_provenance']['reproduction'] = {'original_cohort_root': str(original), 'build_record': 'provenance/reproduction-builds.json', 'changes': 'Only copied PLAN paths, executable identities and prepared-file hashes rebound. Original archived PLAN/source/raw results remain unchanged; rebuilt source/dependency maps are retained separately.'}
    plan['prepared_files'] = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    (out / 'PLAN.json').write_text(json.dumps(plan, indent=2) + '\n')
    print(f'Prepared {out}; no build, smoke or timing executed. Review source maps and wait for build activity to end before a separately authorized run.')


if __name__ == '__main__':
    main()
