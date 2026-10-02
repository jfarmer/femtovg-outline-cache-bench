#!/usr/bin/env python3
"""Hash and validate font blobs emitted by an untimed Alustin screenshot run.

Only exact selected-font bytes and explicitly allowed fallback bytes are accepted.
This is postprocessing, not a timing tool or font parser. Actual font names came
from Slint's existing Skrifa API in the diagnostic path.
"""

import argparse
import hashlib
import json
from pathlib import Path


def file_info(path):
    path = path.resolve(strict=True)
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--family", required=True)
    parser.add_argument("--allow-fallback", type=Path, action="append", default=[])
    parser.add_argument("--require-fallback", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    directory = args.directory.resolve(strict=True)
    primary = file_info(args.primary)
    fallbacks = [file_info(path) for path in args.allow_fallback]
    allowed = {info["sha256"]: info for info in fallbacks}
    records = []
    for metadata_path in sorted(directory.glob("*.font.json")):
        metadata = json.loads(metadata_path.read_text())
        if metadata["schema"] != 1 or Path(metadata["blob_file"]).name != metadata["blob_file"]:
            raise ValueError(f"invalid actual-font metadata: {metadata_path}")
        blob = file_info(directory / metadata["blob_file"])
        if blob["bytes"] != metadata["bytes"]:
            raise ValueError(f"actual-font blob length differs: {metadata_path}")
        family = bytes.fromhex(metadata.pop("family_utf8_hex")).decode("utf-8")
        postscript = bytes.fromhex(metadata.pop("postscript_utf8_hex")).decode("utf-8")
        if blob["sha256"] == primary["sha256"]:
            role, source = "primary", primary
            if family != args.family or metadata["face_index"] != 0 or not metadata["has_ascii"]:
                raise ValueError(f"selected actual face has unexpected family/index/coverage: {family}, {metadata}")
        elif blob["sha256"] in allowed:
            role, source = "fallback", allowed[blob["sha256"]]
        else:
            raise ValueError(f"unexpected actual font: {family}, SHA-256 {blob['sha256']}")
        records.append({**metadata, "family": family, "postscript_name": postscript,
                        "role": role, "sha256": blob["sha256"], "source": source["path"],
                        "metadata_file": str(metadata_path)})
    if not records or not any(record["role"] == "primary" for record in records):
        raise ValueError("the selected primary font was never passed to the renderer")
    if args.require_fallback and not any(record["role"] == "fallback" for record in records):
        raise ValueError("the expected controlled fallback was never passed to the renderer")
    report = {"mode": "untimed actual-font validation", "complete": True,
              "configured_family": args.family, "primary": primary, "allowed_fallbacks": fallbacks,
              "actual_fonts": records,
              "scope": "Distinct actual renderer faces, with exact blob-byte identity; not a character-to-font routing trace"}
    output = args.output or directory / "actual-fonts.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Validated {len(records)} actual font blobs; wrote {output}")


if __name__ == "__main__":
    main()
