#!/usr/bin/env python3
"""Independently audit native screening CSVs and derive exploratory medians.

Imports neither screen.py nor a campaign collector/analyzer. Does not build or
run a renderer. Live mode checks binaries; archive mode can explicitly declare
missing executables and retains their original SHA-256 build identities.

Exact native geometry/alpha equality is established by the successful guarded
Rust process's untimed assertions. This reader checks every emitted digest and
count binding; it does not reconstruct pixels from a CSV digest.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import tomllib


KERNELS = ['builder_only', 'rebuild_and_outline', 'prepared_hinted', 'prepared_unhinted', 'native_render', 'geometry_reuse']
ORDERS = [[0, 1, 5, 2, 4, 3], [1, 2, 0, 3, 5, 4], [2, 3, 1, 4, 0, 5], [3, 4, 2, 5, 1, 0], [4, 5, 3, 0, 2, 1], [5, 0, 4, 1, 3, 2]]
CSV_FIELDS = ["font_sha256", "profile", "dpr", "logical_size", "size", "trial", "kernel", "glyphs", "repeats", "total_us", "us_per_glyph", "points", "verbs", "audit_images", "audit_digest"]


def graph(metadata):
    packages = {p["id"]: p for p in metadata["packages"]}

    def identity(identifier):
        p = packages[identifier]
        return [p["name"], p["version"], p["source"] or "<screen-root>"]

    nodes = []
    for node in metadata["resolve"]["nodes"]:
        edges = [[edge["name"], identity(edge["pkg"]), sorted(json.dumps(kind, sort_keys=True) for kind in edge["dep_kinds"])] for edge in node["deps"]]
        nodes.append([identity(node["id"]), sorted(node["features"]), sorted(edges)])
    return sorted(nodes)


class Audit:
    def __init__(self, mapping, allow_missing_binaries):
        self.mapping = sorted(mapping.items(), key=lambda pair: len(pair[0]), reverse=True)
        self.allow_missing_binaries = allow_missing_binaries
        self.inputs = {}
        self.missing_binaries = []

    def path(self, value):
        raw = str(value)
        for old, new in self.mapping:
            if raw == old or raw.startswith(old.rstrip("/") + "/"):
                return Path(new + raw[len(old):])
        return Path(raw)

    def bind(self, value, expected=None, binary=False):
        path = self.path(value)
        if not path.is_file() and binary and self.allow_missing_binaries:
            assert expected and re.fullmatch(r"[0-9a-f]{64}", expected)
            self.missing_binaries.append({"original_path": str(value), "sha256": expected})
            return expected
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if expected is not None:
            assert actual == expected, (str(value), "SHA-256 mismatch", expected, actual)
        self.inputs[str(value)] = {"resolved_path": str(path), "sha256": actual, "bytes": len(raw)}
        return actual

    def read(self, value, expected=None):
        self.bind(value, expected)
        return json.loads(self.path(value).read_text())

    def source(self, built):
        command = built["commands"][0]
        manifest = Path(command[command.index("--manifest-path") + 1])
        source = manifest.parent
        inputs = self.read(source / "inputs.json", built["source_inputs_sha256"])
        for filename, expected in inputs["screen_files"].items():
            self.bind(source / filename, expected)
        self.bind(source / "screen.py", built["driver_sha256"])
        self.bind(source / "Cargo.lock", built["lock_sha256"])
        manifest_data = tomllib.loads(self.path(manifest).read_text())
        bins = manifest_data.get("bin", [{"name": manifest_data["package"]["name"]}])
        assert len(bins) == 1 and Path(built["binary"]).name == bins[0]["name"]
        metadata_path = Path(built["commands"][0][built["commands"][0].index("--manifest-path") + 1])
        assert metadata_path == manifest
        lock = tomllib.loads(self.path(source / "Cargo.lock").read_text())
        registry = {p["name"]: p for p in lock["package"] if p.get("source")}
        assert set(registry) == set(inputs["locked_packages"])
        for name, expected in inputs["locked_packages"].items():
            for field in ("version", "source", "checksum"):
                assert registry[name][field] == expected[field], (name, field)
        if "cjk_workload" in inputs:
            work = inputs["cjk_workload"]
            self.read(work["path"], work["sha256"])
        native = inputs.get("native_sources", {})
        if native.get("all_61_source_files_equal"):
            for root_name in ("local_swash_source", "registry_swash_source"):
                root = native[root_name]
                # Dependency source trees may be absent in restored archives;
                # the build metadata/lock and guarded original hashes remain.
                if self.path(root).is_dir():
                    for filename, expected in native["source_files"].items():
                        self.bind(Path(root) / filename, expected)
        rust = self.path(source / "src/main.rs").read_text()
        for fragment in ("for phase in 0..10", "assert_geometry(retained, &scratch_outline)", "assert_image(&native, &reused, &mut hash)", "left.x.to_bits(), left.y.to_bits()", "left.placement.left", "left.placement.width", "left.data, right.data", "let digest = audit_case(font, &case, &cache)"):
            assert fragment in rust, (str(source), "native exact proof assertion missing", fragment)
        assert repr(ORDERS) in rust
        assert "assert_geometry(retained, &rebuilt_outline)" in rust
        sizes = [float(x.strip()) for x in re.search(r"const SIZES: \[f32; 5\] = \[([^]]+)\]", rust).group(1).split(",") if x.strip()]
        assert sizes == [11, 12, 14, 15, 16]
        profiles = re.findall(r'profile: "([^"]+)"', rust)
        assert len(profiles) == 2 and len(set(profiles)) == 2
        cases = [(dpr, size, profile) for dpr in (1, 2) for size in sizes for profile in profiles]
        return inputs, source, cases

    def screen(self, label, root):
        root = Path(root)
        provenance_path = root / "provenance.json"
        provenance = self.read(provenance_path)
        assert provenance["complete"] and provenance["mode"] in ("timing", "audit")
        built = self.read(provenance["build"], provenance["build_sha256"])
        assert built["complete"] and built["driver_sha256"] == provenance["driver_sha256"]
        self.bind(built["binary"], built["binary_sha256"], binary=True)
        inputs, source, cases = self.source(built)
        metadata_path = Path(provenance["build"]).parent / "metadata.json"
        metadata = self.read(metadata_path, built["metadata_sha256"])
        assert graph(metadata) == built["graph"]
        nodes = {n["id"]: n for n in metadata["resolve"]["nodes"]}
        swash = next(p for p in metadata["packages"] if p["name"] == "swash")
        assert sorted(nodes[swash["id"]]["features"]) == ["default", "render", "scale", "std"]
        for package in metadata["packages"]:
            if package["source"] is not None:
                expected = inputs["locked_packages"][package["name"]]
                assert (package["version"], package["source"]) == (expected["version"], expected["source"])
        for font in provenance["fonts"].values():
            self.bind(font["path"], font["sha256"])
        trials = provenance["trials"]
        if provenance["mode"] == "timing":
            assert trials > 0 and trials % 6 == 0
        else:
            assert trials == 1
        assert provenance["repeats"] > 0 and provenance["rounds"] > 0
        labels = list(provenance["fonts"])
        order = []
        for round_index in range(provenance["rounds"]):
            rotated = labels[round_index % len(labels):] + labels[:round_index % len(labels)]
            order.extend((round_index + 1, font) for font in rotated)
        assert [(item["round"], item["font"]) for item in provenance["launches"]] == order
        checked = []
        rejected = []
        values = defaultdict(list)
        invariants = {}
        sample_count = 0
        for launch in provenance["launches"]:
            font = launch["font"]
            identity = provenance["fonts"][font]
            command = [built["binary"], provenance["mode"], identity["path"], identity["sha256"], str(trials), str(provenance["repeats"])]
            assert launch["command"] == command
            self.bind(launch["stdout"])
            self.bind(launch["stderr"])
            with self.path(launch["stdout"]).open() as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
                if reader.fieldnames is not None:
                    assert reader.fieldnames == CSV_FIELDS
            if not launch["complete"]:
                assert launch["exit_code"] != 0
                rejected.append({"font": font, "round": launch["round"], "exit_code": launch["exit_code"], "raw_partial_rows": len(rows), "stdout": launch["stdout"], "stderr": launch["stderr"]})
                continue
            assert launch["exit_code"] == 0
            expected_rows = len(cases) if provenance["mode"] == "audit" else len(cases) * trials * len(KERNELS)
            assert len(rows) == launch["rows"] == expected_rows
            expected_order = []
            for dpr, size, profile in cases:
                if provenance["mode"] == "audit":
                    expected_order.append((dpr, size, profile, 0, "audit_exact"))
                else:
                    for trial in range(trials):
                        expected_order.extend((dpr, size, profile, trial, KERNELS[kernel]) for kernel in ORDERS[trial % len(ORDERS)])
            coverage = defaultdict(set)
            for size, codepoint, glyph in re.findall(r"coverage locale=\w+ size=([\d.]+) codepoint=U\+([0-9A-F]+) glyph=(\d+)", self.path(launch["stderr"]).read_text()):
                assert int(glyph) > 0
                coverage[float(size)].add(int(glyph))
            for row, expected in zip(rows, expected_order):
                dpr, size, profile, trial, kernel = expected
                assert row["font_sha256"] == identity["sha256"]
                assert (int(row["dpr"]), float(row["logical_size"]), row["profile"], int(row["trial"]), row["kernel"]) == expected
                assert float(row["size"]) == dpr * size
                glyphs = int(row["glyphs"])
                assert glyphs > 0
                if profile in ("ascii94", "cjk94"):
                    assert glyphs == 94
                elif coverage:
                    assert glyphs == len(coverage[size]), (font, size, glyphs, coverage[size])
                points, verbs, images = map(int, (row["points"], row["verbs"], row["audit_images"]))
                assert points >= 0 and verbs >= 0 and images == glyphs * 10
                digest = row["audit_digest"]
                assert re.fullmatch(r"[0-9a-f]{16}", digest)
                key = (font, profile, dpr, size)
                identity_counts = (glyphs, points, verbs, images, digest)
                assert invariants.setdefault(key, identity_counts) == identity_counts
                total, per_glyph = float(row["total_us"]), float(row["us_per_glyph"])
                assert math.isfinite(total) and math.isfinite(per_glyph) and total >= 0 and per_glyph >= 0
                if kernel == "audit_exact":
                    assert int(row["repeats"]) == 0 and total == 0 and per_glyph == 0
                else:
                    assert int(row["repeats"]) == provenance["repeats"]
                    recomputed = total / (glyphs * provenance["repeats"])
                    # CSV rounds total_us to six and per-glyph time to nine decimals.
                    assert abs(recomputed - per_glyph) <= 0.000000501 / (glyphs * provenance["repeats"]) + 0.000000000501
                    values[key + (kernel,)].append(per_glyph)
                sample_count += 1
            checked.append({"font": font, "round": launch["round"], "rows": len(rows), "stdout": launch["stdout"], "stderr": launch["stderr"]})
        assert len(checked) == provenance["successful_launches"]
        assert len(rejected) == provenance["rejected_launches"]
        summary = []
        for key, counts in sorted(invariants.items()):
            font, profile, dpr, size = key
            item = {"screen": label, "font": font, "font_sha256": provenance["fonts"][font]["sha256"], "profile": profile, "dpr": dpr, "logical_size": size, "glyphs": counts[0], "points": counts[1], "verbs": counts[2], "audit_images": counts[3], "audit_digest": counts[4]}
            if values:
                medians = {kernel: statistics.median(values[key + (kernel,)]) for kernel in KERNELS}
                sample_counts = {kernel: len(values[key + (kernel,)]) for kernel in KERNELS}
                assert len(set(sample_counts.values())) == 1
                item.update({kernel + "_us_per_glyph": value for kernel, value in medians.items()})
                item.update(trials_per_kernel=sample_counts["prepared_hinted"], hinting_increment_us_per_glyph=medians["prepared_hinted"] - medians["prepared_unhinted"], potential_saved_us_per_glyph=medians["native_render"] - medians["geometry_reuse"])
            summary.append(item)
        return {"screen": label, "root": str(root), "provenance": str(provenance_path), "mode": provenance["mode"], "trials": trials, "repeats": provenance["repeats"], "rounds": provenance["rounds"], "cases_per_launch": len(cases), "raw_rows_checked": sample_count, "successful_launches": checked, "rejected_launches": rejected, "case_medians": summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen", action="append", nargs=2, metavar=("LABEL", "ROOT"), required=True)
    parser.add_argument("--path-map", type=Path)
    parser.add_argument("--allow-missing-binaries", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    mapping = json.loads(args.path_map.read_text()) if args.path_map else {}
    audit = Audit(mapping, args.allow_missing_binaries)
    results = [audit.screen(label, root) for label, root in args.screen]
    grouped = defaultdict(list)
    for result in results:
        for row in result["case_medians"]:
            grouped[row["screen"], row["font"], row["profile"], row["dpr"]].append(row)
    overview = []
    for (screen, font, profile, dpr), rows in sorted(grouped.items()):
        assert len(rows) == 5
        item = {"screen": screen, "font": font, "font_sha256": rows[0]["font_sha256"], "profile": profile, "dpr": dpr, "logical_sizes": [row["logical_size"] for row in rows]}
        for field in [kernel + "_us_per_glyph" for kernel in KERNELS] + ["hinting_increment_us_per_glyph", "potential_saved_us_per_glyph"]:
            if field in rows[0]:
                item[field] = statistics.median(row[field] for row in rows)
        overview.append(item)
    for original, identity in audit.inputs.items():
        assert hashlib.sha256(audit.path(original).read_bytes()).hexdigest() == identity["sha256"], (original, "changed during audit")
    output = {"complete": True, "inspector_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "method": "Independent raw CSV/launch/order/count/digest/finite-value/rounded-duration checks; source/build/metadata/lock/font guards. Per-case median over all retained successful trials and rounds; overview is the median of five logical-size medians. All native kernels and rejected attempts are retained. Exact geometry and image proof relies on guarded native assertions, not a reconstruction from a digest. Warm cost-decomposition diagnostics only; builder_only is per builder invocation. No confidence intervals, algebraic-additivity assertion, actual cache overhead, atlas hit rate, arena admission/eviction, or predicted app percentage.", "missing_binaries_explicit_archive_mode": audit.missing_binaries, "inputs": audit.inputs, "screens": results, "profile_dpr_medians": overview}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    if overview:
        fields = list(overview[0]) + sorted(set().union(*(set(row) for row in overview)) - set(overview[0]))
        with args.output.with_suffix(".csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(overview)
    print(json.dumps({"complete": True, "screens": len(results), "rows_checked": sum(result["raw_rows_checked"] for result in results), "rejected_launches_preserved": sum(len(result["rejected_launches"]) for result in results), "output": str(args.output)}))


if __name__ == "__main__":
    main()
