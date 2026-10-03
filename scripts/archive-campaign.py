#!/usr/bin/env python3
"""Preserve a completed experiment, including failures, in a verified archive.

Compiled executables, compiler output trees, and Python caches are omitted.
Every omitted file is listed. Original scripts, sources, locks, logs, timings,
provenance, analysis and pixel captures are preserved without rewriting paths.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile

PRUNE = {"target", "targets", "target-native", "target-counted", "test-target", "test-targets", "probe-target", "__pycache__", ".git", ".serena"}
EXECUTABLE_MAGIC = {
    b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf",
    b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce", b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca", b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca",
}


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inventory(source, excluded_prefixes=()):
    kept, omitted = [], []
    for path in sorted(source.rglob("*")):
        if not path.is_file() and not path.is_symlink():
            continue
        relative = path.relative_to(source)
        reason = None
        if any(relative==prefix or prefix in relative.parents for prefix in excluded_prefixes):
            reason = "separately archived nested campaign; original bytes retained there"
        elif path.is_symlink():
            reason = "symlink; original target is recorded"
        elif any(part in PRUNE for part in relative.parts):
            reason = "compiler or local cache"
        elif path.suffix in {".rlib", ".rmeta", ".o", ".dylib", ".so", ".pyc", ".exe"}:
            reason = "compiled output"
        else:
            with path.open("rb") as stream:
                magic = stream.read(4)
            if magic in EXECUTABLE_MAGIC:
                reason = "compiled executable; build provenance retains its hash"
        if reason:
            record = {"path": relative.as_posix(), "bytes": path.lstat().st_size if path.is_symlink() else path.stat().st_size, "reason": reason}
            if path.is_symlink():
                record["target"] = str(path.readlink())
            omitted.append(record)
        else:
            kept.append(path)
    return kept, omitted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--exclude-prefix", action="append", default=[], help="Nested root retained in its own campaign archive")
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    destination = args.destination.resolve()
    if not source.is_dir() or destination.is_relative_to(source):
        parser.error("source must be a directory and destination must be outside it")
    if destination.exists():
        parser.error("destination exists; use a fresh archive directory")
    if not args.label or "/" in args.label or args.label in {".", ".."}:
        parser.error("label must be one safe path component")
    for value in args.exclude_prefix:
        if not value or Path(value).is_absolute() or any(part in ("", ".", "..") for part in value.split("/")):
            parser.error("--exclude-prefix must be a safe relative directory")
        if not (source/value).is_dir():parser.error("--exclude-prefix must identify an existing nested campaign directory")
    excluded_prefixes=tuple(Path(value) for value in args.exclude_prefix)
    kept, omitted = inventory(source, excluded_prefixes)
    destination.mkdir(parents=True)
    archive = destination / "records.tar.gz"
    manifest = {"schema": 1, "label": args.label, "original_root": str(source),
                "retention": "All noncompiled files, including incomplete/rejected cohorts; inclusion in the archive does not imply inclusion in a timing analysis",
                "storage": "Lossless tar hardlinks deduplicate identical file contents; every original path and byte checksum is retained",
                "files": {}, "omitted": omitted, "excluded_nested_campaign_prefixes": args.exclude_prefix, "complete": False}
    manifest_path = destination / "archive.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    canonical = {}
    with archive.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|") as bundle:
                for path in kept:
                    before = path.stat()
                    checksum = sha(path)
                    relative = path.relative_to(source).as_posix()
                    entry = bundle.gettarinfo(str(path), arcname=f"{args.label}/{relative}")
                    entry.uid = entry.gid = entry.mtime = 0
                    entry.uname = entry.gname = ""
                    content_key = (checksum, before.st_size)
                    if content_key in canonical:
                        entry.type = tarfile.LNKTYPE
                        entry.linkname = canonical[content_key]
                        entry.size = 0
                        bundle.addfile(entry)
                    else:
                        canonical[content_key] = entry.name
                        with path.open("rb") as stream:
                            bundle.addfile(entry, stream)
                    after = path.stat()
                    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                        raise RuntimeError(f"Source changed while archiving: {path}")
                    manifest["files"][relative] = {"sha256": checksum, "bytes": before.st_size}
    # Read the compressed copy independently; never trust a successful write.
    observed, regular = {}, set()
    with tarfile.open(archive, "r|gz") as bundle:
        for entry in bundle:
            if not entry.isfile() and not entry.islnk():
                raise RuntimeError(f"Unexpected archive member: {entry.name}")
            relative = Path(entry.name).relative_to(args.label).as_posix()
            if relative in observed:
                raise RuntimeError(f"Duplicate archive member: {entry.name}")
            if entry.islnk():
                target = Path(entry.linkname).relative_to(args.label).as_posix()
                if target not in regular or manifest["files"][relative] != observed[target]:
                    raise RuntimeError(f"Invalid deduplicated file reference: {entry.name}")
                observed[relative] = dict(observed[target])
            else:
                with bundle.extractfile(entry) as stream:
                    observed[relative] = {"sha256": hashlib.file_digest(stream, "sha256").hexdigest(), "bytes": entry.size}
                regular.add(relative)
    if observed != manifest["files"]:
        raise RuntimeError("Archive content differs from original files")
    final_kept, final_omitted = inventory(source, excluded_prefixes)
    if final_kept != kept or final_omitted != omitted:
        raise RuntimeError("Source inventory changed while archiving")
    manifest.update(archive={"path": archive.name, "sha256": sha(archive), "bytes": archive.stat().st_size},
                    raw_bytes=sum(r["bytes"] for r in observed.values()),
                    unique_content_bytes=sum(size for _, size in canonical), complete=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Archived and verified {args.label}: {len(observed)} files, {archive.stat().st_size} compressed bytes; {len(omitted)} compiled/cache files omitted")


if __name__ == "__main__":
    main()
