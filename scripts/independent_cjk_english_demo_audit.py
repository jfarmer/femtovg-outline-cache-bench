#!/usr/bin/env python3
"""Audit the exploratory English-demo screen directly from every raw trial.

Reads the original replay_campaign.py schema, without importing that collector
or a native/statistical analyzer. The intended cohort has two balanced blocks,
three trials, DPR2, master/final, and thirteen retained fonts. No confidence
intervals, timing exclusions, or confirmation claims are produced.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics


PHASES = {
    "demo": {"first_paint": 1, "warm": 30, "zoom_in": 12, "zoom_out": 12, "pan": 10},
    "text": {"first_paint": 1, "warm": 30, "x_advance": 10, "x_return": 10, "y_advance": 10, "size_advance": 12, "size_return": 12, "reflow": 3},
    "font_variations": {"first_paint": 1, "warm": 30, "weight_advance": 6, "weight_return": 6, "slant_advance": 10, "slant_return": 10},
    "grid_singleton": {"once": 1}, "grid_two_phases": {"first": 1, "second": 1},
    "grid_unique_sizes": {"sweep": 32}, "grid_unique_variations": {"sweep": 32},
    "grid_pollution": {"hot_first": 1, "hot_second": 1, "pollution": 64, "hot_return": 1},
}
METRICS = ("draw_us", "submit_us", "complete_us")
FIELDS = ["scene", "phase", "trial", "frames", *METRICS, "new_atlas_entries"]
RESULT_FIELDS = ["backend", "font", "dpi", "block", "version", *FIELDS]


class Reader:
    def __init__(self, mapping, archive):
        self.mapping = sorted(mapping.items(), key=lambda pair: -len(pair[0]))
        self.archive = archive
        self.checked = {}
        self.missing_binaries = []

    def path(self, original):
        raw = str(original)
        for old, new in self.mapping:
            if raw == old or raw.startswith(old.rstrip("/") + "/"):
                return Path(new + raw[len(old):])
        return Path(raw)

    def bind(self, path, expected=None, size=None, binary=False):
        resolved = self.path(path)
        if binary and self.archive and not resolved.is_file():
            assert expected and size
            self.missing_binaries.append({"path": str(path), "sha256": expected, "bytes": size})
            return expected
        with resolved.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if expected is not None:
            assert digest == expected, (str(path), "SHA-256 mismatch")
        actual_size = resolved.stat().st_size
        if size is not None:
            assert actual_size == size, (str(path), "byte length mismatch")
        self.checked[str(path)] = {"resolved_path": str(resolved), "sha256": digest, "bytes": actual_size}
        return digest

    def info(self, record, binary=False):
        return self.bind(record["path"], record["sha256"], record["bytes"], binary)

    def json(self, path):
        self.bind(path)
        return json.loads(self.path(path).read_text())

    def tree(self, path, expected):
        actual = {str(file.relative_to(self.path(path))): self.bind(Path(path) / file.relative_to(self.path(path))) for file in sorted(self.path(path).rglob("*")) if file.is_file()}
        assert actual == expected, (str(path), "source/asset tree differs")

    def identity(self, meta):
        identity = meta["identity"]
        for binary in identity["binaries"].values():
            self.info(binary, binary=True)
        self.info(identity["oracle_binary"], binary=True)
        for field in ("build_provenance", "native_build_provenance", "native_prepare_provenance", "prepare_provenance"):
            self.info(identity[field])
        for record in identity["independent_audits"]:
            self.info(record)
            assert self.json(record["path"])["complete"]
        build = self.json(identity["build_provenance"]["path"])
        assert build["complete"]
        assert build["compiler"] == identity["compiler"] and build["cargo"] == identity["cargo"]
        assert build["resolved_lock_sha256"] == identity["resolved_lock_sha256"]
        assert build["runner_source"] == identity["runner_source"]
        core = Path(identity["build_provenance"]["path"]).parent
        self.tree(core / "runner/src", identity["runner_source"])
        self.bind(core / "runner/Cargo.lock", identity["resolved_lock_sha256"])
        assert set(identity["sources"]) == set(build["variants"]) == set(identity["binaries"])
        for version, sources in identity["sources"].items():
            built = build["variants"][version]
            assert built["complete"]
            assert identity["binaries"][version]["path"] == built["binary"]
            assert identity["binaries"][version]["sha256"] == built["binary_sha256"]
            assert sources["pure_snapshot"] == built["pure_source_files"]
            assert sources["timed_source"] == built["timed_source_files"]
            self.tree(core / "snapshots" / version, sources["pure_snapshot"])
            self.tree(core / "replay-sources" / version, sources["timed_source"])
        prepare = self.json(identity["prepare_provenance"]["path"])
        assets = {name[len("assets/"):]: record["sha256"] for name, record in prepare["prepared_files"].items() if name.startswith("assets/")}
        assert assets == identity["assets"]
        self.tree(core.parent / "assets", assets)
        native_prepare = self.json(identity["native_prepare_provenance"]["path"])
        native_build = self.json(identity["native_build_provenance"]["path"])
        assert native_prepare["complete"] and native_build["complete"]
        assert identity["native_prepare_provenance"]["sha256"] == native_build["prepare_sha256"]
        assert native_prepare["original_master_files"] == identity["sources"]["master"]["timed_source"]
        self.tree(native_prepare["oracle_source"], native_prepare["oracle_files"])
        study = core.parent.parent
        self.tree(study / "native-master-offset-oracle/runner", native_prepare["runner_files"])
        self.bind(native_build["metadata"], native_build["metadata_sha256"])
        assert native_build["binary"] == identity["oracle_binary"]["path"]
        assert native_build["binary_sha256"] == identity["oracle_binary"]["sha256"]


def write_csv(path, rows):
    assert rows
    fields = list(rows[0])
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", "--root", dest="campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--path-map", type=Path)
    parser.add_argument("--archive", "--allow-missing-binaries", dest="archive", action="store_true", help="Explicitly permit absent archived executable bodies; all other inputs remain required")
    args = parser.parse_args()
    mapping = json.loads(args.path_map.read_text()) if args.path_map else {}
    reader = Reader(mapping, args.archive)
    meta_path = args.campaign / "cpu-provenance.json"
    meta = reader.json(meta_path)
    assert meta["complete"] and meta["mode"] == meta["backend"] == "cpu" and meta["exploratory"]
    assert meta["blocks"] == 2 and meta["trials_per_process"] == 3
    assert meta["versions"] == ["master", "final"] and meta["dpis"] == [2]
    assert len(meta["fonts"]) == len(set(meta["fonts"])) == 13
    assert meta["phases"] == PHASES
    assert meta["pixel_proof"] is None, "This reader is scoped to exploratory selection without a pixel campaign"
    reader.info(meta["driver"])
    if meta["selection_manifest"] is not None:
        reader.info(meta["selection_manifest"])
    reader.identity(meta)
    assert set(meta["font_files"]) == set(meta["fonts"])
    for record in meta["font_files"].values():
        reader.info(record)
    configurations = [(font, 2) for font in meta["fonts"]]
    expected_launches, expected_orders = [], []
    for block_index in range(2):
        offset = block_index % len(configurations)
        labels = []
        for font, dpi in configurations[offset:] + configurations[:offset]:
            versions = ("master", "final") if (block_index + configurations.index((font, dpi))) % 2 == 0 else ("final", "master")
            for version in versions:
                key = block_index + 1, font, dpi, version
                label = f"{block_index + 1:02}-{font}-dpi{dpi}-{version}"
                expected_launches.append((key, label))
                labels.append(label)
        expected_orders.append(labels)
    assert meta["order"] == expected_orders
    assert len(meta["launches"]) == len(expected_launches) == 52
    aggregate = []
    raw_processes = {}
    process_medians = []
    values = defaultdict(dict)
    for launch, (key, label) in zip(meta["launches"], expected_launches):
        block, font, dpi, version = key
        assert (launch["block"], launch["font"], launch["dpi"], launch["version"]) == key
        assert launch["label"] == label and launch["validated"] and launch["exit_code"] == 0
        assert launch["command"] == [meta["identity"]["binaries"][version]["path"], "cpu", "3", "2"]
        assert launch["environment"] == {"FEMTOVG_REPLAY_TEXT_FONT": meta["font_files"][font]["path"]}
        reader.info(launch["stdout_info"])
        reader.info(launch["stderr_info"])
        assert launch["stdout"] == launch["stdout_info"]["path"] and launch["stderr"] == launch["stderr_info"]["path"]
        with reader.path(launch["stdout"]).open() as stream:
            raw_reader = csv.DictReader(stream)
            assert raw_reader.fieldnames == FIELDS
            raw = list(raw_reader)
        assert len(raw) == launch["rows"] == 84
        expected_rows = {(trial, scene, phase) for trial in range(3) for scene, phases in PHASES.items() for phase in phases}
        seen = set()
        for row in raw:
            row_key = int(row["trial"]), row["scene"], row["phase"]
            assert row_key in expected_rows and row_key not in seen
            seen.add(row_key)
            frames = int(row["frames"])
            assert frames == PHASES[row_key[1]][row_key[2]]
            count = int(row["new_atlas_entries"])
            assert count >= 0
            if row_key[1].startswith("grid_"):
                assert count == 94 * frames
            timings = [float(row[metric]) for metric in METRICS]
            assert all(math.isfinite(value) and value >= 0 for value in timings)
            assert timings == sorted(timings)
            aggregate.append({"backend": "cpu", "font": font, "dpi": str(dpi), "block": str(block), "version": version, **row})
        assert seen == expected_rows
        raw_processes[key] = raw
        for scene, phases in PHASES.items():
            for metric in METRICS:
                for phase, frames in phases.items():
                    samples = [float(row[metric]) for row in raw if row["scene"] == scene and row["phase"] == phase]
                    assert len(samples) == 3
                    median = statistics.median(samples)
                    endpoint = font, dpi, scene, phase, metric
                    values[endpoint][block, version] = median
                    process_medians.append({"backend": "cpu", "font": font, "dpi": dpi, "block": block, "version": version, "scene": scene, "phase": phase, "metric": metric, "reported_frames": frames, "trial_values_us": samples, "process_median_us": median})
                if scene in ("demo", "text", "font_variations"):
                    frames = sum(phases.values())
                    assert frames == {"demo": 65, "text": 88, "font_variations": 63}[scene]
                    samples = [sum(float(row[metric]) * int(row["frames"]) for row in raw if row["scene"] == scene and int(row["trial"]) == trial) for trial in range(3)]
                    median = statistics.median(samples)
                    values[font, dpi, scene, "reported_sequence", metric][block, version] = median
                    process_medians.append({"backend": "cpu", "font": font, "dpi": dpi, "block": block, "version": version, "scene": scene, "phase": "reported_sequence", "metric": metric, "reported_frames": frames, "trial_values_us": samples, "process_median_us": median})
    reader.info(meta["results"])
    with reader.path(meta["results"]["path"]).open() as stream:
        combined = csv.DictReader(stream)
        assert combined.fieldnames == RESULT_FIELDS
        assert list(combined) == aggregate
    assert len(aggregate) == 52 * 84 == 4368
    comparisons = meta["count_comparisons"]
    assert len(comparisons) == len(configurations) * 2
    compared = set()
    for comparison in comparisons:
        factor = comparison["block"], comparison["font"], comparison["dpi"]
        assert factor in {(block, font, dpi) for block in (1, 2) for font, dpi in configurations} and factor not in compared
        compared.add(factor)
        assert comparison["validated_against_native_pixels"] is False
        assert set(comparison["counts"]) == {"master", "final"}
        for version, counts in comparison["counts"].items():
            raw = raw_processes[comparison["block"], comparison["font"], comparison["dpi"], version]
            expected = [{"scene": row["scene"], "phase": row["phase"], "trial": int(row["trial"]), "count": int(row["new_atlas_entries"])} for row in raw]
            assert counts == expected
    assert len(compared) == 26
    for font, dpi in configurations:
        orders = Counter(tuple(launch["version"] for launch in meta["launches"] if (launch["block"], launch["font"], launch["dpi"]) == (block, font, dpi)) for block in (1, 2))
        assert orders == Counter({("master", "final"): 1, ("final", "master"): 1})
    effects = []
    for endpoint, group in sorted(values.items()):
        font, dpi, scene, phase, metric = endpoint
        assert set(group) == {(block, version) for block in (1, 2) for version in ("master", "final")}
        master = [group[block, "master"] for block in (1, 2)]
        final = [group[block, "final"] for block in (1, 2)]
        paired = [a - b for a, b in zip(master, final)]
        effects.append({"backend": "cpu", "font": font, "font_sha256": meta["font_files"][font]["sha256"], "dpi": dpi, "scene": scene, "phase": phase, "metric": metric, "paired_blocks": 2, "reference_version": "master", "candidate_version": "final", "reference_mean_process_median_us": statistics.mean(master), "candidate_mean_process_median_us": statistics.mean(final), "mean_paired_savings_us": statistics.mean(paired), "block_savings_us": paired})
    assert len(effects) == 13 * (28 + 3) * 3 == 1209
    primary = sorted([row for row in effects if (row["scene"], row["phase"], row["metric"]) == ("demo", "first_paint", "draw_us")], key=lambda row: -row["mean_paired_savings_us"])
    for original, identity in reader.checked.items():
        with reader.path(original).open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == identity["sha256"], (original, "changed during audit")
    result = {"complete": True, "auditor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "campaign": str(args.campaign), "source_mode": "live" if not args.archive else "archive", "method": "All raw trials and 28 phases × 3 cumulative timing metrics retained. Phase process medians use three trials. Reported scene sequences sum frame-weighted phase times within each trial before taking the process median: 65 demo, 88 text, 63 variation frames. Paired effects are means across two balanced blocks. No confidence intervals, exclusions, or confirmation claims; regular font overrides only, fixed Roboto variation controls retained. Untimed warmup frames and setup/launch costs are outside reported sequences. No actual-demo pixel proof was required during exploratory selection.", "processes": 52, "raw_rows": len(aggregate), "font_DPR_factors": 13, "endpoint_effects": len(effects), "balanced_AB_BA_per_font": True, "missing_binaries_explicit_archive_mode": reader.missing_binaries, "inputs": reader.checked, "primary_ranking": primary, "effects": effects, "process_medians": process_medians}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    write_csv(args.output.with_suffix(".csv"), effects)
    write_csv(args.output.with_name(args.output.stem + "-process-medians.csv"), process_medians)
    print(json.dumps({"complete": True, "processes": 52, "raw_rows": len(aggregate), "endpoint_effects": len(effects), "output": str(args.output)}))


if __name__ == "__main__":
    main()
