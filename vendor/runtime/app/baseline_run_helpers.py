#!/usr/bin/env python3
"""Pair FemtoVG master/patch in the same Alustin application for four UI fonts.

startup/cpu/pixels open application windows. --help never launches an application.
Every font uses explicit runtime registration with system discovery disabled.
Input-contaminated attempts retry the whole pair, preserving all raw attempts.
"""

import argparse
import csv
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from benchmark_helpers import digest, event_map, file_info, frame_spans, git_head, png_rgba


ROOT = Path("/Users/jesse/github/alustin-gui-v2")
HERE = Path(__file__).resolve().parent
BACKENDS = ("winit-femtovg-wgpu", "winit-femtovg")
FONT_DEFAULTS = {
    "vollkorn": ("Vollkorn", ROOT / "crates/alustin-gui/assets/fonts/Vollkorn-Medium.ttf"),
    "liberation": ("Liberation Serif", Path("/private/tmp/femtovg-liberation-font-review/liberation-fonts-ttf-2.1.5/LiberationSerif-Regular.ttf")),
    "arial": ("Arial", Path("/System/Library/Fonts/Supplemental/Arial.ttf")),
    "roboto": ("Roboto Flex", Path("/Users/jesse/github/femtovg/examples/assets/RobotoFlex-VariableFont.ttf")),
    "ptsans": ("PT Sans", Path("/private/tmp/femtovg-open-font-search/candidate-agent/PTSans-Regular.ttf")),
}


def write_csv(path, rows):
    if not rows:
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def checkpoint(output, result, accepted):
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    write_csv(output / "accepted.csv", accepted)
    attempts = []
    for record in result["launches"]:
        attempts.append({key: record.get(key) for key in (
            "label", "round", "backend", "font", "family", "attempt", "version",
            "exit_code", "validated", "included", "validation_error", "report")}
                        | record.get("metrics", {}))
    write_csv(output / "attempts.csv", attempts)


def validate_report(report, binary, expected_sha, backend, font, mode, font_event):
    if len(report.get("samples", [])) != 1:
        raise ValueError("startup_bench must return exactly one sample")
    sample = report["samples"][0]
    ran = sample.get("executable_path")
    if not ran or Path(ran).resolve() != binary:
        raise ValueError(f"ran {ran!r}, expected {str(binary)!r}")
    if digest(ran) != expected_sha:
        raise ValueError(f"running executable differs from recorded SHA-256: {ran}")
    if sample.get("backend_requested") != backend:
        raise ValueError("requested backend differs from configuration")
    if sample.get("system_fonts_disabled") is not True or report.get("system_fonts_disabled") is not True:
        raise ValueError("system font discovery must be disabled for every font")
    reported_path = report.get("font_path")
    if not reported_path or str(Path(reported_path).resolve()) != font["file"]["path"]:
        raise ValueError(f"harness font path {reported_path!r} differs from configured file")
    events = event_map(sample)
    dimensions = events["first_frame_rendered"]["details"]
    if (dimensions.get("physical_width"), dimensions.get("physical_height"), dimensions.get("scale_factor")) != (2560, 1600, 2.0):
        raise ValueError(f"unexpected first-frame dimensions/DPR: {dimensions}")
    expected_api = "WGPU30" if backend == "winit-femtovg-wgpu" else "OpenGL"
    api = events["renderer_setup"]["details"]["graphics_api"]
    if api != expected_api:
        raise ValueError(f"graphics API {api!r}, expected {expected_api!r}")
    selected = [event for event in sample["events"] if event["event"] == font_event]
    if len(selected) != 1:
        raise ValueError(f"expected exactly one {font_event} event, found {len(selected)}")
    detail = selected[0]["details"]
    if detail.get("family") != font["family"]:
        raise ValueError(f"font event family={detail.get('family')!r}, expected {font['family']!r}")
    if str(Path(detail.get("font_path", "")).resolve()) != font["file"]["path"]:
        raise ValueError("font event path differs from configured file")
    if digest(font["file"]["path"]) != font["file"]["sha256"]:
        raise ValueError("font file changed during the experiment")
    frames = {}
    if mode == "cpu":
        spans = sample.get("slint_internal_spans", [])
        for phase, marker in (("first_frame", "first_frame_rendered"), ("search_frame", "interactive_frame_rendered")):
            frames[phase] = frame_spans(spans, marker)
    query = events["interactive_frame_rendered"]["details"]["query"]
    contamination = None if query == "a" else f"search response query {query!r}, expected 'a' (possible desktop input contamination)"
    return sample, frames, selected[0], contamination


def extract_metrics(sample, frames):
    events = event_map(sample)
    metrics = {
        "startup_ms": sample["launch_to_probe_observed_ms"],
        "first_frame_since_main_ms": events["first_frame_rendered"]["since_main_ms"],
        "search_frame_since_main_ms": events["interactive_frame_rendered"]["since_main_ms"],
        "first_callback_ms": events["first_frame_rendered"]["since_main_ms"] - events["first_render_started"]["since_main_ms"],
        "spawn_to_main_ms": sample.get("spawn_to_main_ms"),
        "peak_rss_bytes": sample.get("peak_rss_bytes"),
    }
    for phase, spans in frames.items():
        for name in ("femtovg.render", "femtovg.render.thread_cpu_ns", "femtovg.component_items",
                     "femtovg.component_items.thread_cpu_ns", "femtovg.final_flush", "femtovg.final_flush.thread_cpu_ns"):
            if name in spans:
                metrics[f"{phase}.{name}.ms"] = spans[name]["ms"]
    return metrics


def pixel_comparison(master, patch, backend, font):
    import hashlib
    a, b = png_rgba(master), png_rgba(patch)
    if a[:2] != (2560, 1600) or b[:2] != (2560, 1600):
        raise ValueError(f"unexpected screenshot dimensions: master={a[:2]}, patch={b[:2]}")
    return {"backend": backend, "font": font, "master_png": file_info(master), "patch_png": file_info(patch),
            "master_dimensions": list(a[:2]), "patch_dimensions": list(b[:2]),
            "master_rgba_sha256": hashlib.sha256(a[2]).hexdigest(),
            "patch_rgba_sha256": hashlib.sha256(b[2]).hexdigest(), "rgba_identical": a == b}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("startup", "cpu", "pixels"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--harness", type=Path)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=12)
    parser.add_argument("--max-attempts", type=int, default=3, help="Maximum whole-pair attempts for query contamination")
    parser.add_argument("--backends", nargs="+", choices=BACKENDS, default=list(BACKENDS))
    parser.add_argument("--fonts", nargs="+", choices=tuple(FONT_DEFAULTS), default=["vollkorn", "liberation", "arial", "roboto"])
    parser.add_argument("--font", action="append", nargs=3, metavar=("NAME", "FAMILY", "FILE"),
                        help="Override a named font's family and single-face font file; repeat as needed")
    parser.add_argument("--font-event", default="benchmark_font_configured", help="Required app event with configured family and canonical font_path; actual used faces verified separately")
    parser.add_argument("--actual-font-diagnostics", action="store_true", help="Pixels only: request actual font dumps and verify them after each launch")
    parser.add_argument("--font-verifier", type=Path, default=HERE / "verify_actual_fonts.py")
    parser.add_argument("--fallback-font", type=Path, default=ROOT / "crates/alustin-gui/vendor/i-slint-common/sharedfontique/Inter-VariableFont.ttf")
    parser.add_argument("--save", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--icon-pack", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if args.rounds < 1 or args.timeout < 1 or not 1 <= args.max_attempts <= 3:
        parser.error("rounds/timeout must be positive; max-attempts must be between 1 and 3")
    if args.actual_font_diagnostics and args.mode != "pixels":
        parser.error("actual font diagnostics belong only to separate untimed pixels runs")
    if len(set(args.backends)) != len(args.backends) or len(set(args.fonts)) != len(args.fonts):
        parser.error("backends and fonts must be unique")
    definitions = dict(FONT_DEFAULTS)
    for name, family, path in args.font or []:
        if name not in definitions or not family.strip():
            parser.error("--font requires a configured name and nonempty family")
        definitions[name] = family, Path(path)
    root = args.root.resolve(strict=True)
    harness = (args.harness or root / "target/release/examples/startup_bench").resolve(strict=True)
    binaries = {"master": args.master.resolve(strict=True), "patch": args.patch.resolve(strict=True)}
    if binaries["master"] == binaries["patch"]:
        parser.error("master and patch must be distinct executable paths")
    paths = {"save": args.save or root / "fixtures/sample_save_large.save", "catalog": args.catalog or root / "item_names.json",
             "icon_pack": args.icon_pack or root / "logs/slint-startup/icon-pack/icons-128-raw.pack"}
    inputs = {name: file_info(path) for name, path in paths.items()}
    fonts = {name: {"family": definitions[name][0], "file": file_info(definitions[name][1])} for name in args.fonts}
    binary_info = {name: file_info(path) for name, path in binaries.items()}
    diagnostics = {"enabled": args.actual_font_diagnostics}
    if args.actual_font_diagnostics:
        diagnostics.update(verifier=file_info(args.font_verifier), fallback=file_info(args.fallback_font))
    env = dict(os.environ)
    cleared = ("SLINT_FONT_PATH", "SLINT_DEFAULT_FONT", "ALUSTIN_BENCH_FONT_FAMILY", "ALUSTIN_FONT_DIAGNOSTICS_DIR", "ALUSTIN_TEST_SAVE", "ALUSTIN_ICONS",
               "MTL_SHADER_CACHE_SIZE", "SLINT_TRACE_RENDERER_STARTUP", "SLINT_MCP_PORT", "SLINT_DEBUG_PERFORMANCE",
               "SLINT_SLOW_ANIMATIONS", "FEMTOVG_REQUIRE_GPU", "SLINT_REVEAL_DELAY_MS", "SLINT_PRESENT_WITH_TRANSACTION",
               "SLINT_MACOS_MATCH_BACKGROUND", "SLINT_GPU_WARMUP_PIPELINE_HANDOFF", "SLINT_WINDOW_ID")
    for name in cleared:
        env.pop(name, None)
    fixed_env = {"SLINT_SCALE_FACTOR": "2", "SLINT_LAZY_SHADERS": "0", "SLINT_GPU_WARMUP": "1",
                 "SLINT_NO_SYSTEM_FONTS": "1", "WINIT_MACOS_WINDOW_ANIMATION": "0", "WGPU_METAL_INITIAL_DRAWABLE": "1",
                 "ALUSTIN_ITEM_NAMES": inputs["catalog"]["path"],
                 "ALUSTIN_FEMTOVG_DIAGNOSTICS": "1" if args.mode == "cpu" else "0",
                 "SLINT_STARTUP_DIAGNOSTICS": "1" if args.mode == "cpu" else "0"}
    env.update(fixed_env)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    rounds = 1 if args.mode == "pixels" else args.rounds
    result = {
        "mode": args.mode, "app_commit": git_head(root), "root": str(root),
        "source_revisions": {"master": "f57a2c39e9836c146556c58c98d80c5bf7899029", "patch": "7a278ca4f947658d01c355c450edc6abcdbe3958"},
        "harness": file_info(harness), "binaries": binary_info, "inputs": inputs, "fonts": fonts,
        "runner": file_info(Path(__file__)), "helpers": file_info(HERE / "benchmark_helpers.py"),
        "platform": platform.platform(), "environment": fixed_env, "rounds": rounds, "max_attempts": args.max_attempts,
        "backends": list(args.backends),
        "font_event_schema": {"event": args.font_event, "fields": ["family", "font_path"]},
        "font_validation_scope": "Primary app event verifies configured family/file, not actual renderer-selected faces; actual primary/fallback face validation belongs to separate untimed diagnostic run",
        "actual_font_diagnostics": diagnostics,
        "font_policy": "All selected font files explicitly runtime registered, including Vollkorn despite its retained embedded import; system discovery off; embedded Inter fallback remains",
        "cache_policy": "Fresh processes; OS and Metal shader caches uncontrolled; retain every attempt",
        "pairing": "Adjacent master/patch launches per backend/font/round; alternate version order; rotate configuration order",
        "retry_policy": "Only final query != a retries both sides of the whole pair, up to max_attempts; select the first structurally valid uncontaminated pair without inspecting durations; failed attempts and valid partners excluded together and retained raw",
        "metrics": "Readiness includes report/IPC, excludes compositor scanout; CPU spans measure host wall/thread CPU, not GPU completion; nested spans overlap; pixels excluded from timing",
        "order": [], "launches": [], "accepted_pairs": [], "pixel_comparisons": [], "complete": False,
    }
    accepted = []
    groups = [(backend, name) for name in args.fonts for backend in args.backends]
    checkpoint(output, result, accepted)
    for round_index in range(rounds):
        offset = round_index % len(groups)
        ordered = groups[offset:] + groups[:offset]
        round_order = []
        result["order"].append(round_order)
        for backend, name in ordered:
            success = False
            for attempt in range(1, args.max_attempts + 1):
                versions = ["master", "patch"] if (round_index + attempt - 1) % 2 == 0 else ["patch", "master"]
                pair_records, contamination = [], []
                for version in versions:
                    label = f"{round_index + 1:02}-{backend}-{name}-attempt{attempt}-{version}"
                    round_order.append(label)
                    child_output = output / label
                    font = fonts[name]
                    launch_env = dict(env, SLINT_FONT_PATH=font["file"]["path"], ALUSTIN_BENCH_FONT_FAMILY=font["family"])
                    diagnostic_directory = child_output / "actual-fonts"
                    if args.actual_font_diagnostics:
                        launch_env["ALUSTIN_FONT_DIAGNOSTICS_DIR"] = str(diagnostic_directory)
                    command = [str(harness), "--runs", "1", "--timeout", str(args.timeout), "--backend", backend,
                               "--binary", str(binaries[version]), "--save", inputs["save"]["path"],
                               "--icon-pack", inputs["icon_pack"]["path"], "--font-path", font["file"]["path"],
                               "--no-system-fonts", "--output", str(child_output)]
                    if args.mode == "cpu":
                        command.append("--slint-internals")
                    if args.mode == "pixels":
                        command.append("--screenshot")
                    record = {"label": label, "round": round_index + 1, "backend": backend, "font": name,
                              "family": font["family"], "attempt": attempt, "version": version, "command": command,
                              "environment": {"SLINT_FONT_PATH": font["file"]["path"], "ALUSTIN_BENCH_FONT_FAMILY": font["family"]},
                              "report": str(child_output / "summary.json"), "validated": False, "included": False}
                    if args.actual_font_diagnostics:
                        record["environment"]["ALUSTIN_FONT_DIAGNOSTICS_DIR"] = str(diagnostic_directory)
                    result["launches"].append(record)
                    pair_records.append(record)
                    checkpoint(output, result, accepted)
                    with (output / f"{label}.harness.stdout").open("w") as stdout, (output / f"{label}.harness.stderr").open("w") as stderr:
                        completed = subprocess.run(command, cwd=root, env=launch_env, stdout=stdout, stderr=stderr, timeout=args.timeout + 30)
                    record["exit_code"] = completed.returncode
                    checkpoint(output, result, accepted)
                    if completed.returncode:
                        record["validation_error"] = f"harness exited {completed.returncode}"
                        checkpoint(output, result, accepted)
                        raise RuntimeError(f"{label} harness failed; raw outputs retained")
                    report = json.loads((child_output / "summary.json").read_text())
                    try:
                        sample, frames, selected, reason = validate_report(report, binaries[version], binary_info[version]["sha256"], backend, font, args.mode, args.font_event)
                    except (OSError, ValueError, KeyError) as error:
                        record["validation_error"] = str(error)
                        checkpoint(output, result, accepted)
                        raise
                    record.update(frames=frames, font_configured_event=selected, metrics=extract_metrics(sample, frames))
                    if reason:
                        record["validation_error"] = reason
                        contamination.append(f"{version}: {reason}")
                    else:
                        if args.actual_font_diagnostics:
                            verify = [sys.executable, diagnostics["verifier"]["path"], str(diagnostic_directory),
                                      "--primary", font["file"]["path"], "--family", font["family"],
                                      "--allow-fallback", diagnostics["fallback"]["path"], "--require-fallback"]
                            record["font_verification_command"] = verify
                            checkpoint(output, result, accepted)
                            with (output / f"{label}.font-verify.stdout").open("w") as stdout, (output / f"{label}.font-verify.stderr").open("w") as stderr:
                                verified = subprocess.run(verify, stdout=stdout, stderr=stderr, timeout=30)
                            record["font_verification_exit_code"] = verified.returncode
                            if verified.returncode:
                                record["validation_error"] = "Actual renderer-font verification failed"
                                checkpoint(output, result, accepted)
                                raise ValueError(f"{label}: actual renderer-font verification failed; raw dumps retained")
                            record["actual_fonts"] = json.loads((diagnostic_directory / "actual-fonts.json").read_text())
                        record["validated"] = True
                    checkpoint(output, result, accepted)
                    print(f"{label}: {'validated' if not reason else reason}", flush=True)
                if contamination:
                    excluded = "; ".join(contamination)
                    for record in pair_records:
                        record["exclusion_reason"] = f"Whole pair excluded: {excluded}"
                    checkpoint(output, result, accepted)
                    print(f"Discarded whole pair {round_index + 1}/{backend}/{name}, attempt {attempt}; raw outputs retained", flush=True)
                    continue
                if args.mode == "pixels":
                    by_version = {record["version"]: record for record in pair_records}
                    comparison = pixel_comparison(Path(by_version["master"]["report"]).parent / "run-1.png", Path(by_version["patch"]["report"]).parent / "run-1.png", backend, name)
                    result["pixel_comparisons"].append(comparison)
                    checkpoint(output, result, accepted)
                    if not comparison["rgba_identical"]:
                        raise RuntimeError(f"Screenshot pixel mismatch: {backend}/{name}; raw comparisons retained")
                for record in pair_records:
                    record["included"] = True
                    accepted.append({key: record[key] for key in ("round", "backend", "font", "family", "attempt", "version", "report")} | record["metrics"])
                result["accepted_pairs"].append({"round": round_index + 1, "backend": backend, "font": name,
                                                  "attempt": attempt, "labels": [record["label"] for record in pair_records]})
                checkpoint(output, result, accepted)
                success = True
                break
            if not success:
                raise RuntimeError(f"No valid pair for round {round_index + 1}/{backend}/{name} after {args.max_attempts} attempts; all attempts retained")
    expected_pairs = rounds * len(groups)
    if len(result["accepted_pairs"]) != expected_pairs or len(accepted) != expected_pairs * 2:
        raise ValueError("accepted pair/launch count mismatch")
    if args.mode == "pixels" and "vollkorn" in args.fonts:
        controls = []
        for backend in args.backends:
            for name in args.fonts:
                if name == "vollkorn":
                    continue
                by_font = {row["font"]: row for row in result["pixel_comparisons"] if row["backend"] == backend}
                for version in ("master", "patch"):
                    changed = by_font[name][f"{version}_rgba_sha256"] != by_font["vollkorn"][f"{version}_rgba_sha256"]
                    controls.append({"backend": backend, "font": name, "version": version, "pixels_differ_from_vollkorn": changed})
        result["font_override_controls"] = controls
        checkpoint(output, result, accepted)
        if not all(row["pixels_differ_from_vollkorn"] for row in controls):
            raise ValueError("Font override pixel control did not change screenshot; raw outputs retained")
    result["complete"] = True
    checkpoint(output, result, accepted)
    print(f"Completed {len(result['accepted_pairs'])} valid pairs from {len(result['launches'])} total launches; {output}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        print(f"Benchmark failed: {error}", file=sys.stderr)
        sys.exit(1)
