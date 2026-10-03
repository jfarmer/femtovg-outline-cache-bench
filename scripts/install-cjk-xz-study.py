#!/usr/bin/env python3
"""Stage/install the reviewed CJK evidence using a byte-identical XZ tar stream."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil

ORIGINAL = Path('/private/tmp/femtovg-cjk-font-search-20261002/install_cjk_study.py')
spec = importlib.util.spec_from_file_location('reviewed_cjk_installer', ORIGINAL)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)

def stage(args):
    old = args.original_stage.resolve(strict=True)
    proof = installer.load(old / 'installation-plan.json')
    assert proof['complete'] and not proof['installed'] and proof['stage'] == str(old)
    for name, expected in proof['staged_files'].items():
        assert installer.info(old / name) == expected, name
    compressed = installer.complete(args.recompression.resolve(strict=True))
    original_archive = old / 'results/cjk-font-search/records.tar.gz'
    assert compressed['format'] == 'xz' and compressed['decoded_tar_byte_equivalence_verified']
    assert compressed['source_sha256'] == installer.sha(original_archive)
    new_archive = Path(compressed['output']).resolve(strict=True)
    assert installer.sha(new_archive) == compressed['output_sha256']
    assert new_archive.stat().st_size == compressed['output_bytes'] < 100 * 1024 * 1024
    destination = args.stage.resolve()
    assert not destination.exists() and not destination.is_relative_to(old)
    shutil.copytree(old, destination)
    (destination / 'installation-plan.json').unlink()
    archive_dir = destination / 'results/cjk-font-search'
    (archive_dir / 'records.tar.gz').unlink()
    shutil.copy2(new_archive, archive_dir / 'records.tar.xz')
    metadata = installer.load(archive_dir / 'archive.json')
    previous_archive = dict(metadata['archive'])
    metadata['archive'] = {**previous_archive, 'path': 'records.tar.xz',
                           'bytes': compressed['output_bytes'], 'sha256': compressed['output_sha256']}
    installer.write(archive_dir / 'archive.json', metadata)
    index = installer.load(destination / 'results/index.json')
    campaign = next(c for c in index['campaigns'] if c['label'] == 'cjk-font-search')
    assert campaign['archive'] == previous_archive
    campaign['archive'] = metadata['archive']
    installer.write(destination / 'results/index.json', index)
    repo = Path(proof['repository'])
    reader = (repo / 'scripts/benchlib.py').read_text()
    assert reader.count("tarfile.open(archive, 'r|gz')") == 1
    (destination / 'scripts/benchlib.py').write_text(reader.replace(
        "tarfile.open(archive, 'r|gz')", "tarfile.open(archive, 'r|*')"))
    shutil.copy2(__file__, destination / 'scripts/install-cjk-xz-study.py')
    shutil.copy2('/private/tmp/femtovg-cjk-recompress.py', destination / 'scripts/recompress-archive.py')
    installer.write(destination / 'analysis/cjk-archive-recompression.json', compressed)
    proof.update(stage=str(destination), installer_sha256=installer.sha(__file__),
                 original_installer_sha256=installer.sha(ORIGINAL),
                 previous_stage=str(old), recompression=compressed,
                 additional_existing_update='scripts/benchlib.py: autodetect standard tar compression',
                 policy=proof['policy'] + ' Use standard XZ with identical decoded tar bytes; accept gzip and XZ via tarfile auto-detection.')
    proof['completed_inputs'][str(ORIGINAL)] = installer.sha(ORIGINAL)
    proof['completed_inputs'][str(args.recompression.resolve())] = installer.sha(args.recompression)
    proof['staged_files'] = installer.records(destination)
    installer.write(destination / 'installation-plan.json', proof)
    print('Reviewable XZ stage:', destination)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--original-stage', type=Path)
parser.add_argument('--recompression', type=Path)
parser.add_argument('--stage', type=Path, required=True)
parser.add_argument('--repository', type=Path, default=Path('/Users/jesse/github/femtovg-outline-cache-bench'))
parser.add_argument('--install-existing', action='store_true')
args = parser.parse_args()
if args.install_existing:
    proof = installer.load(args.stage / 'installation-plan.json')
    assert proof['installer_sha256'] == installer.sha(__file__)
    assert proof['additional_existing_update'] == 'scripts/benchlib.py: autodetect standard tar compression'
    for path, expected in proof['completed_inputs'].items():
        assert installer.sha(path) == expected, path
    installer.TOOLS = (*installer.TOOLS, 'benchlib.py')
    installer.install(args, proof)
else:
    assert args.original_stage and args.recompression
    stage(args)
