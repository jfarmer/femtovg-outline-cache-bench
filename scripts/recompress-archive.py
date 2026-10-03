#!/usr/bin/env python3
"""Recompress the preserved tar stream without altering a single decoded byte."""
import argparse
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import time

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--format', choices=['gzip9', 'xz'], required=True)
args = parser.parse_args()
source = args.source.resolve(strict=True)
args.output.mkdir(parents=True, exist_ok=False)
out = args.output / ('records.tar.gz' if args.format == 'gzip9' else 'records.tar.xz')
started = time.monotonic()
plain = hashlib.sha256()
plain_bytes = 0
with source.open('rb') as raw_in, gzip.GzipFile(fileobj=raw_in, mode='rb') as decoded, out.open('xb') as raw_out:
    encoded = (gzip.GzipFile(filename='', fileobj=raw_out, mode='wb', mtime=0, compresslevel=9)
               if args.format == 'gzip9' else lzma.LZMAFile(raw_out, mode='wb', preset=6))
    with encoded:
        while chunk := decoded.read(1024 * 1024):
            plain.update(chunk)
            plain_bytes += len(chunk)
            encoded.write(chunk)
reader = gzip.open if args.format == 'gzip9' else lzma.open
check = hashlib.sha256()
checked_bytes = 0
with reader(out, 'rb') as stream:
    while chunk := stream.read(1024 * 1024):
        check.update(chunk)
        checked_bytes += len(chunk)
assert check.digest() == plain.digest() and checked_bytes == plain_bytes
record = {'complete': True, 'format': args.format, 'source': str(source),
          'source_sha256': digest(source), 'source_bytes': source.stat().st_size,
          'output': str(out), 'output_sha256': digest(out), 'output_bytes': out.stat().st_size,
          'decoded_tar_sha256': plain.hexdigest(), 'decoded_tar_bytes': plain_bytes,
          'decoded_tar_byte_equivalence_verified': True,
          'elapsed_seconds': time.monotonic() - started,
          'script_sha256': digest(Path(__file__)),
          'scope': 'Storage-only recompression. Original archive, manifests, paths, font bytes and measurements remain unchanged.'}
(args.output / 'recompression.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record))
