#!/usr/bin/env python3
"""Audit all frozen default/explicit-weight cost cohorts without running Rust."""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

DEFAULT = {"en": ["Rye-Regular", "Vollkorn-Medium", "NanumMyeongjo-Regular",
                  "NotoSansSC-VF", "NotoSerifSC-VF", "BabelStoneHan"],
           "ko": ["NanumMyeongjo-Regular"],
           "zh": ["NotoSansSC-VF", "NotoSerifSC-VF", "BabelStoneHan"]}
WEIGHT_SCREENS = [(locale + "-w" + str(weight), locale, weight)
                  for locale in ("en", "zh") for weight in (300, 400)]

def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

class Inputs:
    def __init__(self, mapping):
        self.mapping = sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True)
        self.inputs = {}
    def path(self, value):
        raw = str(value)
        for old, new in self.mapping:
            if raw == old or raw.startswith(old.rstrip("/") + "/"):
                return Path(new + raw[len(old):])
        return Path(raw)
    def bind(self, value, identity=None):
        path = self.path(value)
        actual = {"sha256": sha(path), "bytes": path.stat().st_size}
        if identity is not None:
            assert actual == {key: identity[key] for key in actual}, (str(value), "binding mismatch")
        self.inputs[str(value)] = {"resolved_path": str(path), **actual}
        return actual
    def read(self, value, identity=None):
        self.bind(value, identity)
        return json.loads(self.path(value).read_text())

def child(reader, screens, output, args):
    command = [sys.executable, "-B", str(reader)]
    for label, root in screens:
        command += ["--screen", label, str(root)]
    if args.path_map:
        command += ["--path-map", str(args.path_map)]
    if args.allow_missing_binaries:
        command.append("--allow-missing-binaries")
    command += ["--output", str(output)]
    assert not output.exists(), "Fresh child audit output required"
    result = subprocess.run(command, capture_output=True, text=True)
    output.with_suffix(".stdout").write_text(result.stdout)
    output.with_suffix(".stderr").write_text(result.stderr)
    output.with_suffix(".command.json").write_text(json.dumps({"command": command,
        "exit_code": result.returncode}, indent=2) + "\n")
    if result.returncode:
        raise RuntimeError("Independent cost reader failed: " + str(output))
    value = json.loads(output.read_text())
    assert value["complete"] and value["inspector_sha256"] == sha(reader)
    return value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--default-reader", type=Path, required=True)
    parser.add_argument("--weight-reader", type=Path, required=True)
    parser.add_argument("--path-map", type=Path)
    parser.add_argument("--allow-missing-binaries", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "Fresh combined audit output required"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mapping = json.loads(args.path_map.read_text()) if args.path_map else {}
    checked = Inputs(mapping)
    top = checked.read(args.root / "campaign-plan.json")
    assert top["complete"] and (top["processes_expected"], top["raw_rows_expected"]) == (18, 12960)
    assert [item["label"] for item in top["campaigns"]] == ["default", "weights"]
    checked.bind(top["driver"]["path"], top["driver"])
    study = Path(top["driver"]["path"]).parent
    selections = {}
    for item in top["campaigns"]:
        assert item["complete"] and item["exit_code"] == 0
        checked.bind(item["driver"]["path"], item["driver"])
        selection = checked.read(item["selection"]["path"], item["selection"])
        assert selection["complete"] and selection["driver"] == item["driver"]
        assert datetime.fromisoformat(selection.get("frozen_utc", selection["created_utc"])) <= datetime.fromisoformat(item["started_utc"])
        checked.bind(selection["prepare"]["path"], selection["prepare"])
        subplan = checked.read(args.root / item["label"] / "campaign-plan.json")
        assert subplan["complete"] and subplan["selection"] == item["selection"]
        for launch in subplan["campaigns"]:
            assert launch["complete"] and launch["exit_code"] == 0
        selections[item["label"]] = selection
    default, weighted = selections["default"], selections["weights"]
    assert default["cases"] == DEFAULT and weighted["weights"] == [300, 400] and weighted["locales"] == ["en", "zh"]
    assert weighted["default_selection"] == top["campaigns"][0]["selection"]
    for selection in (default, weighted):
        assert (selection["trials"], selection["repeats"], selection["rounds"]) == (6, 20, 1)
    frozen_coords = {}
    for proof in weighted["coordinate_audits"]:
        assert proof["complete"] and proof["exit_code"] == 0
        provenance = checked.read(proof["proof"]["path"], proof["proof"])
        assert provenance["complete"] and provenance["mode"] == "audit"
        assert provenance["successful_launches"] == 2 and provenance["rejected_launches"] == 0
        for launch in provenance["launches"]:
            assert launch["complete"] and launch["exit_code"] == 0 and launch["rows"] == 20
            checked.bind(launch["stdout"]); checked.bind(launch["stderr"])
            assert launch["normalized_coords"] == proof["normalized_coords"][launch["font"]]
        frozen_coords[proof["locale"], proof["weight"]] = proof["normalized_coords"]
    assert set(frozen_coords) == {(locale, weight) for _, locale, weight in WEIGHT_SCREENS}
    correction_path = study / "supporting/cost-audit-reader-correction/proof.json"
    correction = checked.read(correction_path)
    for change in correction["readers"]:
        original = checked.path(change["original"])
        actual = checked.path(change["path"])
        checked.bind(change["original"], {"sha256": change["original_sha256"], "bytes": original.stat().st_size})
        checked.bind(change["path"], {"sha256": change["corrected_sha256"], "bytes": actual.stat().st_size})
        assert actual.read_bytes() == original.read_bytes().replace(
            b"ORDERS[trial % 4]", b"ORDERS[trial % len(ORDERS)]").replace(
            b"sample_counts[\"native_outline\"]", b"sample_counts[\"prepared_hinted\"]")
    assert [sha(args.default_reader), sha(args.weight_reader)] == [item["corrected_sha256"] for item in correction["readers"]]
    default_result = child(args.default_reader, [(label, args.root / "default" / label)
        for label in DEFAULT], args.output.with_name(args.output.stem + "-default.json"), args)
    weighted_result = child(args.weight_reader, [(label, args.root / "weights" / label)
        for label, _, _ in WEIGHT_SCREENS], args.output.with_name(args.output.stem + "-weights.json"), args)
    results = [("default", default_result), ("weights", weighted_result)]
    launches = rows = cases = 0
    for kind, result in results:
        expected = list(DEFAULT) if kind == "default" else [x[0] for x in WEIGHT_SCREENS]
        assert [screen["screen"] for screen in result["screens"]] == expected
        for screen in result["screens"]:
            locale = screen["screen"].split("-")[0]
            selection = selections[kind]
            provenance = checked.read(screen["provenance"])
            bound = selection["builds"][locale]
            assert provenance["build"] == bound["provenance"]["path"]
            assert provenance["build_sha256"] == bound["provenance"]["sha256"]
            assert provenance["driver_sha256"] == bound["driver"]["sha256"]
            fonts = DEFAULT[locale] if kind == "default" else list(weighted["fonts"])
            assert list(provenance["fonts"]) == fonts
            for font in fonts:
                assert provenance["fonts"][font] == {key: selection["fonts"][font][key] for key in ("path", "sha256")}
            assert screen["mode"] == "timing" and (screen["trials"], screen["repeats"], screen["rounds"], screen["cases_per_launch"]) == (6, 20, 1, 20)
            assert not screen["rejected_launches"]
            if kind == "weights":
                weight = int(screen["screen"].split("w")[1])
                assert provenance["weight"] == weight
                for launch in provenance["launches"]:
                    assert launch["normalized_coords"] == frozen_coords[locale, weight][launch["font"]]
            launches += len(screen["successful_launches"])
            rows += screen["raw_rows_checked"]
            cases += len(screen["case_medians"])
    assert (launches, rows, cases) == (18, 12960, 360)
    for original, identity in checked.inputs.items():
        checked.bind(original, identity)
    result = {"complete": True, "auditor_sha256": sha(__file__), "source_mode": "archive" if args.allow_missing_binaries else "live",
        "root": str(args.root), "processes": launches, "raw_rows": rows, "cases": cases,
        "timed_cohorts": 7, "frozen_untimed_coordinate_processes": 8,
        "method": "Independently check all seven frozen timing cohorts, six Williams orders, sources/builds/locks/fonts, exact Rust geometry/image assertions, launch order, duration arithmetic, coordinate normalization source and frozen per-font vectors. Child readers recompute every case median. No CIs, application-performance inference or algebraic-additivity guarantee.",
        "inputs": checked.inputs, "default_audit": default_result, "weighted_audit": weighted_result,
        "default_reader_sha256": sha(args.default_reader), "weight_reader_sha256": sha(args.weight_reader),
        "missing_binaries_explicit_archive_mode": default_result["missing_binaries_explicit_archive_mode"] + weighted_result["missing_binaries_explicit_archive_mode"]}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"complete": True, "processes": launches, "raw_rows": rows, "cases": cases, "output": str(args.output)}))

if __name__ == "__main__":
    main()
