#!/usr/bin/env python3
"""Derive absolute warm-cost tables and matched weight comparisons; no CIs."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import statistics

KERNELS = ["builder_only", "rebuild_and_outline", "prepared_hinted", "prepared_unhinted", "native_render", "geometry_reuse"]

def identity(path):
    path = Path(path).resolve(strict=True)
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}

def csv_write(path, rows):
    fields = list(rows[0]) + sorted(set().union(*(set(row) for row in rows)) - set(rows[0]))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)

def key(row):
    return row["locale"], row["font"], row["profile"], row["dpr"], row["logical_size"]

def table(rows):
    text = ["| Workload | Font / weight | Builder | Rebuild + outline | Hinted | Unhinted | Native render | Geometry reuse |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        label = row["font"] + (" / " + str(row["weight"]) if row["weight"] != "default" else "")
        text.append("| " + " | ".join([row["locale"], label] +
            [f'{row[kernel + "_us_per_glyph"]:.3f}' for kernel in KERNELS]) + " |")
    return "\n".join(text)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--weight-selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    selection = json.loads(args.weight_selection.read_text())
    assert audit["complete"] and (audit["processes"], audit["raw_rows"], audit["cases"]) == (18, 12960, 360)
    assert selection["complete"]
    coordinates = {(row["locale"], row["weight"], font): coords
        for row in selection["coordinate_audits"] for font, coords in row["normalized_coords"].items()}
    cases = []
    for cohort, source in (("default", audit["default_audit"]), ("weights", audit["weighted_audit"])):
        for screen in source["screens"]:
            assert screen["mode"] == "timing"
            for original in screen["case_medians"]:
                row = dict(original)
                locale = row["screen"].split("-")[0]
                weight = row.get("weight", "default")
                row.update(cohort=cohort, locale=locale, weight=weight,
                    normalized_coords=coordinates[locale, weight, row["font"]] if cohort == "weights" else [],
                    nominal_default_weight={"NotoSansSC-VF": 100, "NotoSerifSC-VF": 200}.get(row["font"]))
                row["rebuild_increment_us_per_glyph"] = row["rebuild_and_outline_us_per_glyph"] - row["prepared_hinted_us_per_glyph"]
                cases.append(row)
    assert len(cases) == 360 and all(row["trials_per_kernel"] == 6 for row in cases)
    defaults = {key(row): row for row in cases if row["cohort"] == "default"}
    variation_cases = []
    for row in cases:
        if row["cohort"] == "weights":
            base = defaults[key(row)]
            assert base["font_sha256"] == row["font_sha256"] and base["glyphs"] == row["glyphs"]
            comparison = {field: row[field] for field in ("locale", "font", "font_sha256", "profile", "dpr", "logical_size", "weight", "normalized_coords", "nominal_default_weight")}
            for kernel in KERNELS:
                field = kernel + "_us_per_glyph"
                comparison[kernel + "_default_us_per_glyph"] = base[field]
                comparison[kernel + "_weighted_us_per_glyph"] = row[field]
                comparison[kernel + "_increment_us_per_glyph"] = row[field] - base[field]
                comparison[kernel + "_ratio_to_default"] = row[field] / base[field]
            variation_cases.append(comparison)
    assert len(variation_cases) == 160
    groups = {}
    for row in cases:
        groups.setdefault((row["locale"], row["font"], row["profile"], row["dpr"], str(row["weight"])), []).append(row)
    profiles = []
    for _, rows in sorted(groups.items()):
        assert len(rows) == 5
        first = rows[0]
        result = {field: first[field] for field in ("cohort", "locale", "font", "font_sha256", "profile", "dpr", "weight", "normalized_coords", "nominal_default_weight")}
        result.update(logical_sizes=sorted(row["logical_size"] for row in rows), cases=5, trials_per_case_per_kernel=6)
        for field in [kernel + "_us_per_glyph" for kernel in KERNELS] + ["hinting_increment_us_per_glyph", "potential_saved_us_per_glyph", "rebuild_increment_us_per_glyph"]:
            result[field] = statistics.median(row[field] for row in rows)
        profiles.append(result)
    vargroups = {}
    for row in variation_cases:
        vargroups.setdefault((row["locale"], row["font"], row["profile"], row["dpr"], row["weight"]), []).append(row)
    variation_profiles = []
    for _, rows in sorted(vargroups.items()):
        assert len(rows) == 5
        result = {field: rows[0][field] for field in ("locale", "font", "font_sha256", "profile", "dpr", "weight", "normalized_coords", "nominal_default_weight")}
        result.update(logical_sizes=sorted(row["logical_size"] for row in rows), cases=5)
        for kernel in KERNELS:
            for suffix in ("default_us_per_glyph", "weighted_us_per_glyph", "increment_us_per_glyph", "ratio_to_default"):
                result[kernel + "_" + suffix] = statistics.median(row[kernel + "_" + suffix] for row in rows)
        variation_profiles.append(result)
    assert (len(profiles), len(variation_profiles)) == (72, 32)
    args.output.mkdir(parents=True, exist_ok=True)
    expected = [args.output / name for name in ("summary.json", "summary.csv", "summary.md", "case-medians.csv", "variation-case-comparisons.csv", "variation-profile-comparisons.csv")]
    assert not any(path.exists() for path in expected), "Fresh report outputs required"
    result = {"complete": True, "generator": identity(__file__), "inputs": [identity(args.audit), identity(args.weight_selection)],
        "processes": 18, "raw_rows": 12960, "case_medians": 360, "profile_dpr_medians": 72,
        "method": "Median of six retained trial us/glyph values per exact font/profile/DPR/logical-size/kernel case; overview median of five size medians. Variation ratios and differences are first matched per case to the same font SHA/profile/DPR/size at default coordinates, then summarized across five sizes. Builder-only is per build/drop iteration. Default and weighted cohorts ran separately; estimates have no confidence interval and no algebraic-additivity guarantee.",
        "application_scope": "Warm native diagnostics only: no cache admission/eviction, per-hit key/coordinate work, atlas traversal, scene traversal, raster GPU time or claimed app effect. DPR1 corresponds to the demo's initial 11–16px text-atlas sizes; DPR2 is a separately reported larger-size control. Unique glyph profiles are unshaped charmap glyphs, not the actual ordered production atlas-miss trace. NotoSerifSC weight300 uses Swash public normalization [1556], whereas the production trace uses [1555]; that instance is nearby, not an exact replay. Other supplemental coordinate vectors match the production trace.",
        "production_coordinate_difference": {"font": "NotoSerifSC-VF", "weight": 300, "screen_normalized_coords": [1556], "production_trace_normalized_coords": [1555], "scope": "Both locales; one 2.14 fixed-point step. Nearby-instance diagnostic, not exact production replay."},
        "profiles": profiles, "variation_profiles": variation_profiles}
    (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    csv_write(args.output / "summary.csv", profiles)
    csv_write(args.output / "case-medians.csv", cases)
    csv_write(args.output / "variation-case-comparisons.csv", variation_cases)
    csv_write(args.output / "variation-profile-comparisons.csv", variation_profiles)
    paragraphs = ["# Warm Swash cost decomposition", "",
        "All 18 timing processes and 12,960 rows passed independent live source/build/font/order/arithmetic checks. Each timing case retained exact native/rebuilt geometry and ten-offset native/reused alpha-image agreement. The reader-only correction is preserved separately; timed inputs and outputs were unchanged.", "",
        "Values below are **µs per glyph iteration**, with builder-only measured per scaler build/drop. Each table entry is the median of the five logical-size medians (11, 12, 14, 15, 16 px); each size has six balanced trials of twenty repeats. ASCII94 controls and all 360 exact-size cases remain in the JSON and CSV outputs. These are exploratory warm-cost diagnostics, without confidence intervals or application-percentage claims.", ""]
    for dpr in (1, 2):
        paragraphs += [f"## DPR {dpr}: " + ("initial-atlas size controls" if dpr == 1 else "larger-size controls"), ""]
        for kind, title in (("default", "Default coordinates"), ("weights", "Explicit demo weights")):
            selected = [row for row in profiles if row["dpr"] == dpr and row["cohort"] == kind and row["profile"] != "ascii94"]
            paragraphs += ["### " + title, "", table(selected), ""]
    paragraphs += ["## Matched variation cost at DPR 1", "",
        "Each ratio is the median of five ratios matched at identical font SHA, text profile and logical size. The default weight is 100 for Noto Sans SC and 200 for Noto Serif SC; normalized coordinates are computed once outside every timer. The public Swash API yields `[1556]` for Noto Serif SC weight 300, while the production trace uses `[1555]`: this one case is a nearby instance, one 2.14 fixed-point step apart. All other supplemental coordinate vectors match the production trace.", "",
        "| Workload | Font / weight | Hinted increment (µs) | Hinted ratio | Render increment (µs) | Render ratio |",
        "| --- | --- | ---: | ---: | ---: | ---: |"]
    for row in variation_profiles:
        if row["dpr"] == 1 and row["profile"] != "ascii94":
            paragraphs.append(f'| {row["locale"]} | {row["font"]} / {row["weight"]} | {row["prepared_hinted_increment_us_per_glyph"]:.3f} | {row["prepared_hinted_ratio_to_default"]:.2f}× | {row["native_render_increment_us_per_glyph"]:.3f} | {row["native_render_ratio_to_default"]:.2f}× |')
    paragraphs += ["", "## What these measurements establish", "",
        "Warm scaler construction is small and similar across these fonts. Rye and Vollkorn instead have a large difference between prepared hinted and unhinted outline cost. Nanum Myeongjo's hinted outline work is smaller but remains material, including its Korean glyphs. Noto default and nondefault instances have closely matched hinted/unhinted costs; requesting nondefault weights increases outline and raster work without creating a large hinting-specific cost.", "",
        "These observations distinguish expensive hinted outline work from scaler setup and raster complexity. They do not by themselves explain the application's cache overhead or its miss sequence. The production counter traces establish those separate facts. Rebuild, outline and rendering timings are independent kernels; subtracting medians is an estimate, not a strict sum of isolated pipeline stages.", "",
        "All six kernels exclude cold context creation and perform their own warmup. Geometry reuse includes a standalone hash lookup and rasterizes retained native outlines; it excludes FemtoVG's real cache-key allocation, arena budget/admission, atlas and rendering loop. Noto normalization is performed once outside every timer. Application benchmarks remain the evidence for the patch's overall performance.", ""]
    (args.output / "summary.md").write_text("\n".join(paragraphs))
    print(json.dumps({"complete": True, "profiles": len(profiles), "cases": len(cases), "variation_cases": len(variation_cases), "output": str(args.output)}))

if __name__ == "__main__":
    main()
