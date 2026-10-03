#!/usr/bin/env python3
"""Build/run native Swash font screening, separately from real replay results."""
import argparse
import csv
import io
import json
import hashlib
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def guard():
    inputs = json.loads((HERE / "inputs.json").read_text())
    for name, expected in inputs["screen_files"].items():
        if sha(HERE / name) != expected:
            raise ValueError(f"Screen source changed: {name}")
    return inputs


def graph(metadata):
    packages = {package["id"]: package for package in metadata["packages"]}
    root_id = metadata["resolve"]["root"]
    def identity(identifier):
        package = packages[identifier]
        return (package["name"], package["version"], package["source"] or "<screen-root>")
    return sorted((identity(node["id"]), sorted(node["features"]),
                   sorted((edge["name"], identity(edge["pkg"]),
                           sorted(json.dumps(kind, sort_keys=True) for kind in edge["dep_kinds"]))
                          for edge in node["deps"])) for node in metadata["resolve"]["nodes"])


def build(args):
    inputs = guard()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = HERE / "Cargo.toml"
    commands = [
        ["cargo", "metadata", "--offline", "--locked", "--format-version", "1", "--manifest-path", str(manifest)],
        ["cargo", "build", "--release", "--offline", "--locked", "--manifest-path", str(manifest), "--target-dir", str(args.target.resolve())],
    ]
    record = {"complete": False, "source_inputs_sha256": sha(HERE / "inputs.json"),
              "driver_sha256": sha(__file__), "commands": commands,
              "compiler": subprocess.check_output(["rustc", "--version"], text=True).strip(),
              "cargo": subprocess.check_output(["cargo", "--version"], text=True).strip()}
    write(output / "build.json", record)
    with (output / "build.log").open("w") as log:
        raw = subprocess.check_output(commands[0], stderr=log)
        (output / "metadata.json").write_bytes(raw)
        metadata = json.loads(raw)
        for package in metadata["packages"]:
            if package["source"] is not None:
                expected = inputs["locked_packages"][package["name"]]
                if (package["version"], package["source"]) != (expected["version"], expected["source"]):
                    raise ValueError("Package version or source differs from pinned measured dependency graph")
        nodes = {node["id"]: node for node in metadata["resolve"]["nodes"]}
        swash = next(package for package in metadata["packages"] if package["name"] == "swash")
        if sorted(nodes[swash["id"]]["features"]) != ["default", "render", "scale", "std"]:
            raise ValueError("Swash features differ from actual measured replay")
        subprocess.run(commands[1], stdout=log, stderr=subprocess.STDOUT, check=True)
    guard()
    binary = args.target.resolve() / "release/femtovg-font-cost-screen"
    record.update(complete=True, binary=str(binary), binary_sha256=sha(binary),
                  metadata_sha256=sha(output / "metadata.json"), graph=graph(metadata),
                  lock_sha256=sha(HERE / "Cargo.lock"))
    write(output / "build.json", record)
    print(output / "build.json")


def run(args):
    guard()
    build_record = args.build.resolve(strict=True)
    built = json.loads(build_record.read_text())
    if not built["complete"] or built["source_inputs_sha256"] != sha(HERE / "inputs.json"):
        raise ValueError("Incomplete build or changed source inputs")
    if built["driver_sha256"] != sha(__file__) or sha(built["binary"]) != built["binary_sha256"]:
        raise ValueError("Built driver or executable changed")
    if args.trials < 1 or args.repeats < 1 or args.rounds < 1:
        raise ValueError("Trials, repeats and rounds must be positive")
    if args.mode == "timing" and args.trials % 4:
        raise ValueError("Use complete four-order cycles for four timing kernels")
    fonts = {label: Path(path).resolve(strict=True) for label, path in args.font}
    if len(fonts) != len(args.font):
        raise ValueError("Font labels must be unique")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    trials = args.trials if args.mode == "timing" else 1
    provenance = {"complete": False, "mode": args.mode, "build": str(build_record),
        "build_sha256": sha(build_record), "driver_sha256": sha(__file__),
        "trials": trials, "repeats": args.repeats, "rounds": args.rounds,
        "fonts": {label: {"path": str(path), "sha256": sha(path)} for label, path in fonts.items()},
        "launches": [], "scope": "Font-selection microkernels only. Not measured FemtoVG master/final or application speedup. Each case validates exact geometry and alpha image bytes before timing. Prepared native scaler and scratch warm-up, geometry creation and destruction excluded."}
    write(output / "provenance.json", provenance)
    for round_index in range(args.rounds):
        labels = list(fonts)
        labels = labels[round_index % len(labels):] + labels[:round_index % len(labels)]
        for label in labels:
            font = provenance["fonts"][label]
            stem = f"{round_index + 1:02d}-{label}"
            command = [built["binary"], args.mode, font["path"], font["sha256"], str(trials), str(args.repeats)]
            launch = {"round": round_index + 1, "font": label, "command": command,
                "complete": False, "stdout": str(output / f"{stem}.csv"), "stderr": str(output / f"{stem}.stderr")}
            provenance["launches"].append(launch)
            write(output / "provenance.json", provenance)
            with Path(launch["stdout"]).open("w") as stdout, Path(launch["stderr"]).open("w") as stderr:
                completed = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=args.timeout)
            launch["exit_code"] = completed.returncode
            launch["complete"] = completed.returncode == 0
            if sha(font["path"]) != font["sha256"] or sha(built["binary"]) != built["binary_sha256"]:
                raise ValueError("Font or executable changed during screening")
            if launch["complete"]:
                rows = list(csv.DictReader(Path(launch["stdout"]).open()))
                expected = 20 if args.mode == "audit" else 20 * trials * 4
                if len(rows) != expected or any(row["font_sha256"] != font["sha256"] for row in rows):
                    raise ValueError("Incomplete screening rows")
                launch["rows"] = len(rows)
            write(output / "provenance.json", provenance)
            print(f"{stem}: {'complete' if launch['complete'] else 'rejected; stderr retained'}", flush=True)
    provenance["complete"] = True
    provenance["successful_launches"] = sum(launch["complete"] for launch in provenance["launches"])
    provenance["rejected_launches"] = sum(not launch["complete"] for launch in provenance["launches"])
    write(output / "provenance.json", provenance)


def analyze(args):
    root = args.root.resolve(strict=True)
    provenance = json.loads((root / "provenance.json").read_text())
    if not provenance["complete"] or provenance["mode"] != "timing":
        raise ValueError("Completed timing screen required")
    values = {}
    for launch in provenance["launches"]:
        if not launch["complete"]:
            continue
        rows = list(csv.DictReader(Path(launch["stdout"]).open()))
        for row in rows:
            key = (launch["font"], row["profile"], int(row["dpr"]), float(row["logical_size"]), row["kernel"])
            values.setdefault(key, []).append(float(row["us_per_glyph"]))
    output = []
    for (font, profile, dpr, size) in sorted({key[:4] for key in values}):
        native = statistics.median(values[font, profile, dpr, size, "native_render"])
        reuse = statistics.median(values[font, profile, dpr, size, "geometry_reuse"])
        scale = statistics.median(values[font, profile, dpr, size, "native_outline"])
        unhinted = statistics.median(values[font, profile, dpr, size, "native_outline_unhinted"])
        output.append({"font": font, "font_sha256": provenance["fonts"][font]["sha256"],
            "profile": profile, "dpr": dpr, "logical_size": size,
            "native_outline_us_per_glyph": scale, "native_render_us_per_glyph": native,
            "native_outline_unhinted_us_per_glyph": unhinted,
            "hinting_increment_us_per_glyph": scale - unhinted,
            "geometry_reuse_us_per_glyph": reuse, "potential_saved_us_per_glyph": native - reuse,
            "microkernel_change_pct": 100 * (reuse / native - 1)})
    write(root / "screen-summary.json", {"complete": True, "rows": output,
        "scope": "Exploratory per-glyph kernel medians for candidate ranking; no confidence intervals or predicted app percentages. Validate selected fonts in unchanged master/final demo replays."})
    print(root / "screen-summary.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    item = sub.add_parser("build")
    item.add_argument("--output", type=Path, required=True)
    item.add_argument("--target", type=Path, required=True)
    item.set_defaults(function=build)
    item = sub.add_parser("run")
    item.add_argument("--build", type=Path, required=True)
    item.add_argument("--output", type=Path, required=True)
    item.add_argument("--font", action="append", nargs=2, metavar=("LABEL", "PATH"), required=True)
    item.add_argument("--mode", choices=("audit", "timing"), default="audit")
    item.add_argument("--trials", type=int, default=4)
    item.add_argument("--repeats", type=int, default=50)
    item.add_argument("--rounds", type=int, default=1)
    item.add_argument("--timeout", type=int, default=180)
    item.set_defaults(function=run)
    item = sub.add_parser("analyze")
    item.add_argument("--root", type=Path, required=True)
    item.set_defaults(function=analyze)
    args = parser.parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
