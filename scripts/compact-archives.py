#!/usr/bin/env python3
"""Losslessly repack local campaign sources; retain every original archive."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", type=Path, required=True)
    args = parser.parse_args()
    backup = args.backup.resolve()
    if backup.is_relative_to(ROOT):
        parser.error("backup must be outside the repository")
    backup.mkdir(parents=True, exist_ok=True)
    index_path = ROOT / "results/index.json"
    index = json.loads(index_path.read_text())
    for campaign in index["campaigns"]:
        label = campaign["label"]
        directory = ROOT / campaign["path"]
        old = json.loads((directory / "archive.json").read_text())
        if "unique_content_bytes" in old:
            continue
        source = Path(old["original_root"]).resolve(strict=True)
        destination = directory.with_name(label + "-dedup-in-progress")
        if destination.exists() or (backup / label).exists():
            raise RuntimeError(f"Prior repack/backup exists: {label}")
        with (directory / old["archive"]["path"]).open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != old["archive"]["sha256"]:
                raise RuntimeError(f"Original archive checksum differs: {label}")
        subprocess.run([sys.executable, str(ROOT / "scripts/archive-campaign.py"), str(source),
                        str(destination), "--label", label], check=True)
        new = json.loads((destination / "archive.json").read_text())
        if old["files"] != new["files"]:
            raise RuntimeError(f"Repack changed original path/content manifest: {label}")
        directory.rename(backup / label)
        destination.rename(directory)
        campaign.update(archive=new["archive"], raw_bytes=new["raw_bytes"], files=len(new["files"]))
        index_path.write_text(json.dumps(index, indent=2) + "\n")
        print(f"Lossless repack {label}: {old['archive']['bytes']} → {new['archive']['bytes']} bytes; original retained at {backup / label}", flush=True)


if __name__ == "__main__":
    main()
