"""Verify the retained snapshot, optionally extracting it for a fresh build."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--extract', type=Path)
args = parser.parse_args()
index = json.loads((root / 'snapshot-index.json').read_text())
archive = root / index['archive']
assert archive.stat().st_size == index['bytes']
assert hashlib.sha256(archive.read_bytes()).hexdigest() == index['sha256']
with tarfile.open(archive, 'r:gz') as tar:
    seen = set()
    regular = set()
    for member in tar:
        name = PurePosixPath(member.name)
        assert not name.is_absolute() and '..' not in name.parts
        assert member.name not in seen and member.name in index['members']
        assert member.isfile() or member.islnk()
        if member.islnk():
            assert member.linkname in regular
        else:
            regular.add(member.name)
        record = index['members'][member.name]
        data = tar.extractfile(member).read()
        assert len(data) == record['bytes']
        assert hashlib.sha256(data).hexdigest() == record['sha256']
        seen.add(member.name)
    assert seen == set(index['members'])
    if args.extract:
        tar.extractall(args.extract, filter='data')
print(f'Verified {len(seen)} snapshot members and the archive checksum.')
