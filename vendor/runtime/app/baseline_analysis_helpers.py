#!/usr/bin/env python3
"""Analyze completed, raw-validated Alustin font master/patch process pairs.

No application is launched. Incomplete batches are never analyzed. Contaminated
whole-pair attempts remain in retention metadata, with the runner's first valid
attempt accepted independently of performance. All accepted processes remain.
"""

import argparse
from collections import defaultdict
import csv
import functools
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import statistics
import sys

from benchmark_helpers import digest, event_map, file_info


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("font_pair_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
# Hash identical retained executable/font files once, outside measured processes.
runner.digest = functools.lru_cache(maxsize=None)(digest)

NAMES = {
    "observed_search_response_ms": "Launch to observed search-response readiness",
    "first_frame_since_main_ms": "First rendered frame since main",
    "search_frame_since_main_ms": "Search response rendered since main",
    "search_after_first_frame_ms": "First frame to rendered search response",
    "first_callback_wall_ms": "First BeforeRendering to AfterRendering callback interval",
    "spawn_to_main_ms": "Spawn to main",
    "peak_rss_mib": "Process lifetime peak RSS",
}
for phase in ("first_frame", "search_frame"):
    for part in ("render", "component_items", "final_flush"):
        for measure in ("wall", "thread_cpu"):
            NAMES[f"{phase}.{part}.{measure}_ms"] = f"{phase} femtovg.{part}, {measure}"


def resolve(path):
    path = Path(path)
    return path.resolve() if path.is_absolute() else (HERE / path).resolve()


def read(path):
    return json.loads(Path(path).read_text())


def percentile(values, q):
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    lo, hi = math.floor(position), math.ceil(position)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)


def ci(values):
    return [percentile(values, 0.025), percentile(values, 0.975)]


def scalar_metrics(sample):
    events = event_map(sample)
    first = events["first_frame_rendered"]["since_main_ms"]
    search = events["interactive_frame_rendered"]["since_main_ms"]
    values = {
        "observed_search_response_ms": sample["launch_to_probe_observed_ms"],
        "first_frame_since_main_ms": first,
        "search_frame_since_main_ms": search,
        "search_after_first_frame_ms": search - first,
        "first_callback_wall_ms": first - events["first_render_started"]["since_main_ms"],
    }
    if sample.get("spawn_to_main_ms") is not None:
        values["spawn_to_main_ms"] = sample["spawn_to_main_ms"]
    if sample.get("peak_rss_bytes") is not None:
        values["peak_rss_mib"] = sample["peak_rss_bytes"] / 2**20
    return values


def load_batch(directory):
    manifest = read(directory / "summary.json")
    if manifest.get("complete") is not True:
        raise ValueError(f"{directory} is incomplete; exclude the entire batch explicitly")
    if manifest["mode"] not in ("cpu", "startup", "pixels"):
        raise ValueError(f"unknown batch mode in {directory}")
    fonts = manifest["fonts"]
    backends = manifest["backends"]
    if not fonts or not backends or len(backends) != len(set(backends)):
        raise ValueError(f"invalid configured matrix in {directory}")
    expected = {(backend, font, round_number)
                for backend in backends for font in fonts
                for round_number in range(1, manifest["rounds"] + 1)}
    pairs = manifest["accepted_pairs"]
    if len(pairs) != len(expected):
        raise ValueError(f"accepted-pair count differs from configured matrix in {directory}")
    launches = manifest["launches"]
    if len({row["label"] for row in launches}) != len(launches):
        raise ValueError(f"duplicate launch labels in {directory}")
    by_label = {row["label"]: row for row in launches}
    accepted_labels = [label for pair in pairs for label in pair["labels"]]
    if len(accepted_labels) != 2 * len(expected) or len(set(accepted_labels)) != len(accepted_labels):
        raise ValueError(f"invalid accepted-pair labels in {directory}")
    if set(accepted_labels) != {row["label"] for row in launches if row.get("included")}:
        raise ValueError(f"included launch flags differ from accepted pairs in {directory}")
    for row in launches:
        if not row.get("included") and not row.get("exclusion_reason"):
            raise ValueError(f"unexplained excluded attempt: {row['label']}")
    groups, raw_rows = {}, []
    for accepted in pairs:
        key = accepted["backend"], accepted["font"], accepted["round"]
        if key not in expected or key in groups:
            raise ValueError(f"duplicate or unconfigured accepted pair {key}")
        if not 1 <= accepted["attempt"] <= manifest["max_attempts"]:
            raise ValueError(f"invalid pair attempt for {key}")
        group = {}
        for label in accepted["labels"]:
            launch = by_label[label]
            version, backend, font_name = launch["version"], launch["backend"], launch["font"]
            if version not in ("master", "patch") or version in group:
                raise ValueError(f"duplicate/unknown version in pair {key}")
            if (backend, font_name, launch["round"]) != key or launch["attempt"] != accepted["attempt"]:
                raise ValueError(f"launch does not belong to its accepted pair: {label}")
            if launch.get("validated") is not True or launch.get("exit_code") != 0:
                raise ValueError(f"failed or unvalidated included launch: {label}")
            font = fonts[font_name]
            binary = manifest["binaries"][version]
            report = read(launch["report"])
            sample, frames, selected, contamination = runner.validate_report(
                report, Path(binary["path"]).resolve(), binary["sha256"], backend,
                font, manifest["mode"], manifest["font_event_schema"]["event"])
            if contamination:
                raise ValueError(f"contaminated included launch: {label}")
            if frames != launch["frames"] or selected != launch["font_configured_event"]:
                raise ValueError(f"raw report aggregation differs from retained launch: {label}")
            if runner.extract_metrics(sample, frames) != launch["metrics"]:
                raise ValueError(f"raw metric extraction differs from retained launch: {label}")
            metrics = scalar_metrics(sample)
            if manifest["mode"] == "cpu":
                for phase in ("first_frame", "search_frame"):
                    for part in ("render", "component_items", "final_flush"):
                        for measure, suffix in (("wall", ""), ("thread_cpu", ".thread_cpu_ns")):
                            name = f"femtovg.{part}{suffix}"
                            if name not in frames[phase]:
                                raise ValueError(f"missing {phase} {name}: {label}")
                            metrics[f"{phase}.{part}.{measure}_ms"] = frames[phase][name]["ms"]
            if any(not math.isfinite(value) or value < 0 for value in metrics.values()):
                raise ValueError(f"negative or nonfinite metric: {label}")
            row = {"batch": directory.name, "mode": manifest["mode"], "backend": backend,
                   "font": font_name, "family": font["family"], "round": launch["round"],
                   "attempt": launch["attempt"], "version": version, "label": label,
                   "report": launch["report"], "metrics": metrics}
            group[version] = row
            raw_rows.append(row)
        if set(group) != {"master", "patch"}:
            raise ValueError(f"unmatched accepted pair {key}")
        groups[key] = group
    if set(groups) != expected:
        raise ValueError(f"missing accepted matrix entries in {directory}")
    if manifest["mode"] == "pixels":
        comparisons = manifest["pixel_comparisons"]
        if len(comparisons) != len(expected):
            raise ValueError(f"pixel comparison count differs in {directory}")
        seen = set()
        for comparison in comparisons:
            key = comparison["backend"], comparison["font"], 1
            if key not in expected or key in seen:
                raise ValueError(f"duplicate/unconfigured pixel comparison {key}")
            seen.add(key)
            rebuilt = runner.pixel_comparison(Path(comparison["master_png"]["path"]),
                                             Path(comparison["patch_png"]["path"]), key[0], key[1])
            if rebuilt != comparison or comparison["rgba_identical"] is not True:
                raise ValueError(f"raw pixel comparison differs for {key}")
    return manifest, groups, raw_rows


def analyze_group(directory, mode, backend, font, family, pairs, bootstrap, seed):
    metrics = set(pairs[0]["master"]["metrics"])
    if any(set(pair[version]["metrics"]) != metrics for pair in pairs for version in ("master", "patch")):
        raise ValueError(f"metric set changed within {directory.name}/{backend}/{font}")
    rng = random.Random(seed)
    n = len(pairs)
    # Same resampled pair indices for all metrics within each configuration.
    samples = [[rng.randrange(n) for _ in range(n)] for _ in range(bootstrap)] if n >= 3 else []
    rows = []
    for name in sorted(metrics):
        master = [pair["master"]["metrics"][name] for pair in pairs]
        patch = [pair["patch"]["metrics"][name] for pair in pairs]
        differences = [new - old for old, new in zip(master, patch)]
        ratios = [new / old for old, new in zip(master, patch)] if all(value > 0 for value in master) else None
        delta_ci = ci([statistics.median([differences[i] for i in indices]) for indices in samples]) if samples else None
        ratio_ci = ci([statistics.median([ratios[i] for i in indices]) for indices in samples]) if samples and ratios else None
        rows.append({
            "batch": directory.name, "mode": mode, "backend": backend, "font": font, "family": family,
            "metric": name, "description": NAMES[name], "units": "MiB" if name == "peak_rss_mib" else "ms",
            "n_pairs": n, "master_median": statistics.median(master), "patch_median": statistics.median(patch),
            "master_min": min(master), "master_max": max(master), "patch_min": min(patch), "patch_max": max(patch),
            "median_paired_delta": statistics.median(differences), "median_paired_delta_ci95": delta_ci,
            "median_paired_ratio": statistics.median(ratios) if ratios else None,
            "median_paired_change_pct": 100 * (statistics.median(ratios) - 1) if ratios else None,
            "median_paired_change_pct_ci95": [100 * (value - 1) for value in ratio_ci] if ratio_ci else None,
            "pairs": [{"round": pair["master"]["round"], "attempt": pair["master"]["attempt"],
                       "master": old, "patch": new, "delta": new - old,
                       "patch_over_master_ratio": new / old if old > 0 else None}
                      for pair, old, new in zip(pairs, master, patch)],
        })
    return rows


def write_csv(path, rows, fields):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batches", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=HERE / "analysis")
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=72531)
    parser.add_argument("--exclude", nargs=2, action="append", default=[], metavar=("BATCH", "REASON"))
    args = parser.parse_args()
    if args.bootstrap < 1:
        parser.error("bootstrap must be positive")
    directories = [resolve(path) for path in args.batches]
    exclusions = [(resolve(path), reason) for path, reason in args.exclude]
    if len(set(directories)) != len(directories) or set(directories) & {path for path, _ in exclusions}:
        parser.error("included paths must be unique and separate from excluded batches")
    summary = {
        "statistics": {
            "observation": "One fresh process; master/patch paired within backend, font, round, and accepted attempt",
            "absolute": "Independent medians across all accepted processes",
            "effect": "Median within-pair patch-minus-master delta and patch/master ratio; percentage=100*(median paired ratio-1)",
            "ci": "Percentile bootstrap of paired median effects; resample pairs with replacement; no CI with fewer than three pairs",
            "bootstrap_resamples": args.bootstrap, "seed": args.seed,
            "percentiles": "Linear interpolation between sorted bootstrap order statistics at 2.5% and 97.5%",
            "scope": "Exploratory per-metric intervals without multiplicity adjustment; host/IPC, not GPU completion or compositor latency",
            "retention": "Every accepted process retained; first valid whole-pair retry chosen by query alone; all excluded raw attempts retained; no duration/outlier filtering",
            "validation": "Revalidate raw harness reports, configured font event, binary/font hashes, matrix completeness, and recorded frame/metric aggregations; decode screenshot pixels again",
        },
        "analyzer": file_info(Path(__file__)), "batches": [], "excluded_batches": [],
        "results": [], "pixels": [],
    }
    raw_rows, pair_rows = [], []
    timing_identity = None
    for directory, reason in exclusions:
        manifest = read(directory / "summary.json")
        summary["excluded_batches"].append({"path": str(directory), "reason": reason, "mode": manifest["mode"],
                                            "complete": manifest.get("complete", False), "raw_launches": len(manifest["launches"]),
                                            "validated_launches": sum(bool(row.get("validated")) for row in manifest["launches"])})
    for directory in directories:
        manifest, groups, raw = load_batch(directory)
        if manifest["mode"] != "pixels":
            identity = {key: manifest[key] for key in ("app_commit", "source_revisions", "binaries", "harness", "inputs", "fonts", "backends")}
            if timing_identity is not None and identity != timing_identity:
                raise ValueError("CPU/startup timing batches have different application/font/input provenance")
            timing_identity = identity
        kept = {"path": str(directory), **{key: manifest[key] for key in (
            "mode", "rounds", "app_commit", "source_revisions", "binaries", "inputs", "fonts", "backends",
            "environment", "harness", "actual_font_diagnostics", "runner", "helpers")}}
        kept.update(raw_launches=len(manifest["launches"]), accepted_launches=len(raw),
                    excluded_attempt_launches=len(manifest["launches"]) - len(raw), accepted_pairs=len(groups),
                    excluded_attempts=[row for row in manifest["launches"] if not row.get("included")])
        summary["batches"].append(kept)
        if manifest["mode"] == "pixels":
            summary["pixels"].extend({"batch": directory.name, **row} for row in manifest["pixel_comparisons"])
            continue
        raw_rows.extend(raw)
        for backend, font in sorted({key[:2] for key in groups}):
            pairs = [groups[key] for key in sorted(groups) if key[:2] == (backend, font)]
            token = f"{directory.name}/{backend}/{font}"
            seed = args.seed ^ int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
            rows = analyze_group(directory, manifest["mode"], backend, font, manifest["fonts"][font]["family"], pairs, args.bootstrap, seed)
            summary["results"].extend(rows)
            for row in rows:
                pair_rows.extend({"batch": row["batch"], "mode": row["mode"], "backend": backend,
                                  "font": font, "family": row["family"], "metric": row["metric"], "units": row["units"], **pair}
                                 for pair in row["pairs"])
    output = resolve(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    fields = ("batch", "mode", "backend", "font", "family", "metric", "units", "n_pairs", "master_median", "patch_median",
              "median_paired_delta", "median_paired_delta_ci95", "median_paired_ratio",
              "median_paired_change_pct", "median_paired_change_pct_ci95")
    write_csv(output / "summary.csv", [{key: row[key] for key in fields} for row in summary["results"]], fields)
    pair_fields = ("batch", "mode", "backend", "font", "family", "metric", "units", "round", "attempt", "master", "patch", "delta", "patch_over_master_ratio")
    write_csv(output / "pairs.csv", pair_rows, pair_fields)
    (output / "launches.json").write_text(json.dumps(raw_rows, indent=2) + "\n")
    print(f"Wrote {len(summary['results'])} metric summaries, {len(raw_rows)} timed launches, {len(summary['pixels'])} pixel comparisons to {output}")
    primary = {"observed_search_response_ms", "peak_rss_mib", "first_frame.render.thread_cpu_ms", "search_frame.render.thread_cpu_ms"}
    for row in summary["results"]:
        if row["metric"] in primary:
            interval, change = row["median_paired_change_pct_ci95"], row["median_paired_change_pct"]
            effect = f"{change:+.2f}%" if change is not None else "ratio unavailable"
            bounds = f" [{interval[0]:+.2f}, {interval[1]:+.2f}]" if interval else " [CI unavailable]"
            print(f"{row['batch']} {row['backend']} {row['family']} {row['metric']}: "
                  f"{row['master_median']:.3f} -> {row['patch_median']:.3f} {row['units']}; paired {effect}{bounds}; n={row['n_pairs']}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        print(f"Analysis failed: {error}", file=sys.stderr)
        sys.exit(1)
