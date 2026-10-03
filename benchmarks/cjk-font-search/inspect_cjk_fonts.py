#!/usr/bin/env python3
"""Read font metadata and stored programs by script/corpus; no rendering or timing.

Usage: --font LABEL PATH [--font LABEL PATH ...] --output JSON
       [--all-faces | --face N] [--text-file LABEL UTF8_PATH ...]

All input fonts remain untouched. TTC faces are inspected in their original
collection. Geometry uses default-instance FontTools getCoordinates, which
expands TrueType composite components. CFF/CFF2 is reported separately rather
than treating a missing glyf instruction stream as missing hint work.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import statistics
import sys
import unicodedata

import fontTools
from fontTools.ttLib import TTCollection, TTFont


RANGES = {
    "ascii95": [(0x20, 0x7E)],
    "cjk_unified_bmp": [(0x4E00, 0x9FFF)],
    "cjk_extension_a": [(0x3400, 0x4DBF)],
    # Deliberately a declared numeric interval, not a claim of Unicode assignment.
    "han_supplementary_interval": [(0x20000, 0x323AF)],
    "hiragana": [(0x3040, 0x309F)],
    "katakana": [(0x30A0, 0x30FF)],
    "hangul_syllables": [(0xAC00, 0xD7AF)],
}


def summarize(values):
    values = list(values)
    nonzero = [v for v in values if v]
    return {
        "count": len(values), "nonzero_count": len(nonzero),
        "total": sum(values), "max": max(values, default=0),
        "median": statistics.median(values) if values else 0,
        "median_nonzero": statistics.median(nonzero) if nonzero else 0,
    }


def inspect_face(path, label, face, file_hash, corpora):
    with TTFont(path, fontNumber=face, lazy=False) as font:
        names = font["name"]
        order = font.getGlyphOrder()
        cmap = font.getBestCmap() or {}
        glyph_sizes = {}
        glyph_kinds = Counter()
        if "glyf" in font:
            glyf = font["glyf"]
            for name in order:
                glyph = glyf[name]
                program = getattr(glyph, "program", None)
                glyph_sizes[name] = len(program.getBytecode()) if program else 0
                glyph_kinds["composite" if glyph.isComposite() else "simple_or_empty"] += 1
        table_programs = {}
        for tag in ("fpgm", "prep", "cvt ", "glyf", "gvar", "CFF ", "CFF2"):
            data = {"present": tag in font, "table_bytes": len(font.getTableData(tag)) if tag in font else 0}
            if tag in font and tag in ("fpgm", "prep"):
                data["program_bytes"] = len(font[tag].program.getBytecode())
            table_programs[tag] = data
        point_cache = {}

        def points(name):
            if name not in point_cache:
                point_cache[name] = len(font["glyf"][name].getCoordinates(font["glyf"])[0])
            return point_cache[name]

        def mapped_summary(code_counts, geometry):
            mapped = {cp: cmap[cp] for cp in code_counts if cp in cmap and cmap[cp] != ".notdef"}
            unique_glyphs = sorted(set(mapped.values()))
            entry = {
                "requested_distinct_characters": len(code_counts),
                "requested_character_occurrences": sum(code_counts.values()),
                "mapped_distinct_characters": len(mapped),
                "mapped_character_occurrences": sum(code_counts[cp] for cp in mapped),
                "mapped_unique_glyphs": len(unique_glyphs),
                "missing_codepoints": ["U+%04X" % cp for cp in code_counts if cp not in mapped],
            }
            if "glyf" in font:
                entry["direct_glyf_program_bytes_unique_glyphs"] = summarize(glyph_sizes[name] for name in unique_glyphs)
                entry["direct_glyf_program_bytes_per_mapped_character"] = summarize(glyph_sizes[name] for name in mapped.values())
                entry["direct_glyf_program_bytes_weighted_occurrences"] = sum(glyph_sizes[name] * code_counts[cp] for cp, name in mapped.items())
                if geometry:
                    entry["expanded_points_unique_glyphs"] = summarize(points(name) for name in unique_glyphs)
                    entry["expanded_points_weighted_occurrences"] = sum(points(name) * code_counts[cp] for cp, name in mapped.items())
                    entry["per_codepoint"] = {
                        "U+%04X" % cp: {"glyph_name": name, "glyph_id": font.getGlyphID(name), "occurrences": code_counts[cp], "direct_program_bytes": glyph_sizes[name], "expanded_points": points(name)}
                        for cp, name in mapped.items()
                    }
            else:
                entry["geometry_unavailable"] = "No glyf table; CFF/CFF2 points and programs are not equivalent to TrueType measurements."
            return entry

        scripts = {}
        for name, ranges in RANGES.items():
            # Script summaries inspect only mapped characters, avoiding huge missing arrays.
            cps = {cp: 1 for cp in cmap if any(lo <= cp <= hi for lo, hi in ranges)}
            if name == "ascii95":
                cps = {cp: 1 for lo, hi in ranges for cp in range(lo, hi + 1)}
            scripts[name] = mapped_summary(cps, name == "ascii95")
            scripts[name]["declared_ranges_hex"] = [[hex(lo), hex(hi)] for lo, hi in ranges]
            scripts[name]["range_positions"] = sum(hi - lo + 1 for lo, hi in ranges)
        corpus_data = {}
        for name, record in corpora.items():
            counts = Counter(map(ord, record["text"]))
            corpus_data[name] = mapped_summary(counts, True)
            corpus_data[name]["input"] = {k: v for k, v in record.items() if k != "text"}
            controls = {cp: n for cp, n in counts.items() if unicodedata.category(chr(cp)) == "Cc"}
            corpus_data[name]["layout_control_codepoints"] = {"U+%04X" % cp: n for cp, n in controls.items()}
            corpus_data[name]["renderable_excluding_only_cc_controls"] = mapped_summary({cp: n for cp, n in counts.items() if cp not in controls}, True)
        maxp_fields = ("maxPoints", "maxContours", "maxCompositePoints", "maxCompositeContours", "maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions", "maxComponentElements", "maxComponentDepth")
        return {
            "label": label, "path": str(path.resolve()), "face_index": face,
            "sha256": file_hash, "file_bytes": path.stat().st_size,
            "family": names.getDebugName(1), "subfamily": names.getDebugName(2),
            "full_name": names.getDebugName(4), "version": names.getDebugName(5),
            "license_description": names.getDebugName(13), "license_url": names.getDebugName(14),
            "tables": sorted(t for t in font.keys() if t != "GlyphOrder"),
            "glyph_count": len(order), "mapped_codepoints": len(cmap),
            "units_per_em": font["head"].unitsPerEm,
            "variable_axes": [{"tag": a.axisTag, "min": a.minValue, "default": a.defaultValue, "max": a.maxValue} for a in font["fvar"].axes] if "fvar" in font else [],
            "embedded_program_tables": table_programs,
            "direct_glyf_program_bytes_all_glyphs": summarize(glyph_sizes.values()),
            "glyph_kinds": dict(glyph_kinds),
            "maxp": {k: getattr(font["maxp"], k) for k in maxp_fields if hasattr(font["maxp"], k)},
            "scripts": scripts, "corpora": corpus_data,
        }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--font", nargs=2, action="append", metavar=("LABEL", "PATH"), required=True)
    p.add_argument("--text-file", nargs=2, action="append", metavar=("LABEL", "PATH"), default=[])
    faces = p.add_mutually_exclusive_group()
    faces.add_argument("--all-faces", action="store_true")
    faces.add_argument("--face", type=int, default=0)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    corpora = {}
    for label, raw_path in args.text_file:
        path = Path(raw_path)
        raw = path.read_bytes()
        if label in corpora:
            p.error("Duplicate text label: " + label)
        corpora[label] = {"path": str(path.resolve()), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "text": raw.decode("utf-8")}
    records = []
    for label, raw_path in args.font:
        path = Path(raw_path)
        raw = path.read_bytes()
        file_hash = hashlib.sha256(raw).hexdigest()
        if raw[:4] == b"ttcf":
            with TTCollection(path, lazy=True) as collection:
                face_count = len(collection.fonts)
        else:
            face_count = 1
        selected = range(face_count) if args.all_faces else [args.face]
        for face in selected:
            if not 0 <= face < face_count:
                p.error("Face %d out of range for %s (%d faces)" % (face, path, face_count))
            records.append(inspect_face(path, label, face, file_hash, corpora))
    output = {
        "complete": True, "fonttools_version": fontTools.__version__, "python": sys.version,
        "inspector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "method": "Unmodified font SFNT/TTC metadata, direct stored glyf/fpgm/prep byte lengths, mapped script coverage and exact UTF-8 corpus statistics. Composite-expanded points are unscaled and unhinted at the default instance. Direct glyph bytes omit instructions executed by component glyphs and all runtime function/loop execution. Stored byte counts, maxp declarations, file size and glyph coverage are not executed instruction counts or performance predictions. CFF/CFF2 has a different hinting model and is not classified by TrueType program bytes.",
        "fonts": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    flat = []
    for font in records:
        row = {"label": font["label"], "face_index": font["face_index"], "sha256": font["sha256"], "file_bytes": font["file_bytes"], "full_name": font["full_name"], "version": font["version"], "glyph_count": font["glyph_count"], "glyf_program_bytes_total": font["direct_glyf_program_bytes_all_glyphs"]["total"], "fpgm_program_bytes": font["embedded_program_tables"]["fpgm"].get("program_bytes", 0), "prep_program_bytes": font["embedded_program_tables"]["prep"].get("program_bytes", 0)}
        row.update({"maxp_" + key: value for key, value in font["maxp"].items()})
        for name, corpus in font["corpora"].items():
            rendering = corpus["renderable_excluding_only_cc_controls"]
            row[name + "_mapped_distinct"] = rendering["mapped_distinct_characters"]
            row[name + "_requested_distinct"] = rendering["requested_distinct_characters"]
            row[name + "_direct_program_bytes_weighted"] = rendering.get("direct_glyf_program_bytes_weighted_occurrences")
            row[name + "_expanded_points_weighted"] = rendering.get("expanded_points_weighted_occurrences")
        flat.append(row)
    fields = list(flat[0]) + sorted(set().union(*(set(row) for row in flat)) - set(flat[0]))
    with args.output.with_suffix(".csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flat)
    print(json.dumps({"complete": True, "faces": len(records), "output": str(args.output)}))


if __name__ == "__main__":
    main()
