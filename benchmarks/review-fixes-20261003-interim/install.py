#!/usr/bin/env python3
"""Install an immutable study in one new directory; never overwrite a study."""
import argparse
import datetime
import hashlib
import json
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_DEST = Path('/Users/jesse/github/femtovg-outline-cache-bench/benchmarks/pr-final-20261003')
INPUTS = {
    'perf': Path('/private/tmp/femtovg-review-fixes-perf'),
    'containment': Path('/private/tmp/femtovg-review-fixes-containment'),
    'scenes': Path('/private/tmp/femtovg-review-fixes-scenes'),
}
CACHE_PARTS = {'target', 'bin', '__pycache__', '.git', '.cache', 'node_modules'}
UNTRAVERSED_DIRS = CACHE_PARTS - {'bin'}
BINARY_MAGICS = {b'\x7fELF', b'\xfe\xed\xfa\xce', b'\xce\xfa\xed\xfe',
                 b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe'}


def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def reason(relative, path):
    if CACHE_PARTS.intersection(relative.parts):
        return 'binary, build target, or regenerable cache directory'
    if path.suffix in {'.pyc', '.pyo', '.o', '.rlib', '.rmeta', '.dylib', '.so', '.dll', '.exe', '.a'}:
        return 'compiled artifact or interpreter cache'
    if path.name == '.DS_Store':
        return 'host filesystem metadata'
    with path.open('rb') as stream:
        if stream.read(4) in BINARY_MAGICS:
            return 'executable or native compiled artifact'
    return None


def preserve(source, destination, label, omitted):
    for directory, subdirs, files in os.walk(source, followlinks=False):
        for name in [*subdirs, *files]:
            path = Path(directory) / name
            if path.is_symlink():
                link = os.readlink(path)
                omitted.append({'path': f'{label}/{path.relative_to(source)}',
                                'reason': 'symlink omitted; target recorded without following it',
                                'target': link, 'sha256': hashlib.sha256(os.fsencode(link)).hexdigest()})
        kept = []
        for name in subdirs:
            path = Path(directory) / name
            if path.is_symlink():
                continue
            if name in UNTRAVERSED_DIRS:
                omitted.append({'path': f'{label}/{path.relative_to(source)}', 'kind': 'directory',
                                'reason': 'Regenerable compiler/interpreter cache; not traversed or hashed.',
                                'sha256': None, 'file_count': None})
            else:
                kept.append(name)
        subdirs[:] = kept
        for name in sorted(files):
            path = Path(directory) / name
            if path.is_symlink():
                continue
            relative = path.relative_to(source)
            before = path.stat()
            checksum = digest(path)
            exclusion = reason(relative, path)
            if exclusion:
                omitted.append({'path': f'{label}/{relative}', 'reason': exclusion,
                                'bytes': before.st_size, 'sha256': checksum})
            else:
                copied = destination / relative
                copied.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, copied)
                if digest(copied) != checksum:
                    raise SystemExit(f'Input changed while copying: {path}')
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                raise SystemExit(f'Input changed while inventorying: {path}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path, default=DEFAULT_DEST)
    parser.add_argument('--evidence', type=Path, action='append', default=[],
                        help='Additional retained TDD/check artifact; repeatable.')
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination.exists():
        raise SystemExit(f'Refusing to overwrite existing study: {destination}')
    for name, source in INPUTS.items():
        if not source.is_dir():
            raise SystemExit(f'Missing study source {name}: {source}')
    # Caller must wait for all measurements/builds to finish before running this.
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()  # Exclusive ownership of this previously absent directory.
    omitted = []
    for name, source in INPUTS.items():
        preserve(source, destination / 'raw' / name, name, omitted)
    fonts = Path('/Users/jesse/github/femtovg-outline-cache-bench/assets')
    for relative in ['Vollkorn-Medium.ttf', 'PTSans-Regular.ttf',
                     'licenses/Vollkorn-OFL.txt', 'licenses/PTSans-OFL.txt']:
        source = fonts / relative
        if not source.is_file():
            raise SystemExit(f'Missing licensed portable asset: {source}')
        copied = destination / 'assets' / relative
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, copied)
    insertion = Path('/private/tmp/femtovg-review-phase-regressions.rs')
    evidence = ([insertion] if insertion.is_file() else []) + args.evidence
    for index, source in enumerate(evidence):
        copied = destination / 'evidence' / 'tdd' / f'{index:02d}-{source.name}'
        if source.is_dir():
            preserve(source, copied, f'tdd/{source.name}', omitted)
        else:
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, copied)
    for name in ['reproduce.py', 'README.md', 'TDD-OBSERVATIONS.md', 'install.py']:
        shutil.copy2(HERE / name, destination / name)
    shutil.copy2(INPUTS['perf'] / 'RESULTS.md', destination / 'SUMMARY.md')
    shutil.copy2(INPUTS['perf'] / 'MANUAL-REVIEW.md', destination / 'MANUAL-REVIEW.md')
    (destination / 'OMITTED.json').write_text(json.dumps(omitted, indent=2) + '\n')
    record = {
        'installed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'destination': str(destination), 'input_roots': {k: str(v) for k, v in INPUTS.items()},
        'candidate_commit_reported_by_parent': json.loads((INPUTS['perf'] / 'final-runtime-identity.json').read_text())['final_commit'],
        'preservation': 'All retained inputs byte-identical. Original paths/metadata unchanged. No archives/compression.',
        'omissions': 'OMITTED.json records excluded bin/artifact file sizes and SHA-256; compiler-cache directories are not traversed/hashed; symlinks record target identity.',
        'checksum_scope': 'Every retained file except SHA256SUMS itself.',
        'tdd': 'Initial red/green observations were tool-output-only; no reconstructed raw logs.',
        'status': 'interim: warm/generic complete; eight-block cold reanalysis provisional; scenes and portable builds wait for the other project build to finish; no further cold run planned; no PR before manual review',
    }
    (destination / 'INSTALLATION.json').write_text(json.dumps(record, indent=2) + '\n')
    checksums = []
    for path in sorted(destination.rglob('*')):
        if path.is_file() and path.name != 'SHA256SUMS':
            checksums.append(f'{digest(path)}  {path.relative_to(destination)}')
    (destination / 'SHA256SUMS').write_text('\n'.join(checksums) + '\n')
    print(f'Installed preserved study: {destination}')
    print(f'Retained {len(checksums)} files; inventoried {len(omitted)} omitted artifacts.')


if __name__ == '__main__':
    main()
