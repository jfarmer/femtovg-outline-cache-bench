#!/usr/bin/env python3
"""Build Alustin against two clean FemtoVG refs without changing app inputs.

The app must already expose femtovg-benchmark. Dependencies must be cached: all
Cargo commands use --offline. Run with exclusive access to the app Cargo.lock.
This builds binaries only; it never launches them or opens windows.
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tomllib


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def command(args: list[str], cwd: Path) -> bytes:
    return subprocess.check_output(args, cwd=cwd)


def git(root: Path, *args: str) -> bytes:
    return command(["git", *args], root)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def app_inputs(root: Path) -> dict[str, str]:
    # Include tracked worktree files and staged changes; Cargo.lock is managed below.
    files = git(root, "ls-files", "-z").split(b"\0")
    return {
        raw.decode(): digest((root / raw.decode()).read_bytes())
        for raw in files
        if raw and raw != b"Cargo.lock" and (root / raw.decode()).is_file()
    }


def snapshot(repo: Path, ref: str, destination: Path) -> str:
    revision = git(repo, "rev-parse", "--verify", ref + "^{commit}").decode().strip()
    destination.mkdir()
    raw = git(repo, "archive", revision)
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(destination, filter="data")
    manifest = tomllib.loads((destination / "Cargo.toml").read_text())
    if manifest["package"]["name"] != "femtovg":
        raise ValueError("the source repository must contain the FemtoVG crate")
    for path in (destination / "src").rglob("*.rs"):
        if "alustin_startup" in path.read_text():
            raise ValueError(f"ref contains benchmark instrumentation: {ref}: {path}")
    return revision


def graph(metadata: dict, app: Path, source: Path) -> tuple[list[dict], dict]:
    packages = {p["id"]: p for p in metadata["packages"]}
    femtovg = [p for p in packages.values() if p["name"] == "femtovg"]
    if len(femtovg) != 1 or Path(femtovg[0]["manifest_path"]).resolve() != source / "Cargo.toml":
        raise ValueError("Cargo did not use precisely the archived FemtoVG override")
    nodes = {n["id"]: n for n in metadata["resolve"]["nodes"]}
    features = nodes[femtovg[0]["id"]]["features"]
    if not {"swash", "wgpu"}.issubset(features) or "textlayout" in features:
        raise ValueError(f"unexpected FemtoVG features: {features}")

    def identity(package_id: str) -> str:
        package = packages[package_id]
        origin = package["source"]
        if origin is None:
            path = Path(package["manifest_path"]).resolve()
            if package["name"] == "femtovg":
                origin = "<femtovg-archive>"
            elif path.is_relative_to(app):
                origin = str(path.relative_to(app))
            else:
                origin = str(path)
        return f'{package["name"]}@{package["version"]}|{origin}'

    normalized = []
    for node in nodes.values():
        dependencies = [
            {"name": d["name"], "package": identity(d["pkg"]),
             "kinds": sorted(d["dep_kinds"], key=lambda k: (k["kind"] or "", k["target"] or ""))}
            for d in node["deps"]
        ]
        normalized.append({"package": identity(node["id"]), "features": sorted(node["features"]),
                           "dependencies": sorted(dependencies, key=lambda d: (d["name"], d["package"]))})
    swash_id = next(d["pkg"] for d in nodes[femtovg[0]["id"]]["deps"] if d["name"] == "swash")
    skrifa_id = next(d["pkg"] for d in nodes[swash_id]["deps"] if d["name"] == "skrifa")
    versions = {"swash": packages[swash_id]["version"], "skrifa": packages[skrifa_id]["version"],
                "femtovg_features": sorted(features)}
    if versions["swash"] != "0.2.10":
        raise ValueError(f"expected Swash 0.2.10, resolved {versions['swash']}")
    return sorted(normalized, key=lambda n: n["package"]), versions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Alustin checkout (default: cwd)")
    parser.add_argument("--femtovg", type=Path, required=True, help="clean FemtoVG Git repository")
    parser.add_argument("--master-ref", default="master")
    parser.add_argument("--patch-ref", default="HEAD")
    parser.add_argument("--output", type=Path, required=True, help="new artifact directory")
    parser.add_argument("--target-dir", type=Path, help="shared Cargo target directory (default: OUTPUT/target)")
    args = parser.parse_args()
    app = args.root.resolve(strict=True)
    repo = args.femtovg.resolve(strict=True)
    output = args.output.resolve()
    if output.exists() or any(output.is_relative_to(base / ".git") for base in (app, repo)):
        parser.error("--output must be a new directory outside Git internals")
    if git(repo, "status", "--porcelain", "--untracked-files=no").strip():
        parser.error("FemtoVG has tracked source changes; commit or stash them before archiving refs")
    manifest = tomllib.loads((app / "crates/alustin-gui/Cargo.toml").read_text())
    if "femtovg-benchmark" not in manifest.get("features", {}):
        parser.error("the Alustin checkout must already define the femtovg-benchmark feature")
    output.mkdir(parents=True)
    target = (args.target_dir or output / "target").resolve()
    lock_path = app / "Cargo.lock"
    original_lock = lock_path.read_bytes()
    expected_lock = original_lock
    initial_inputs = app_inputs(app)
    (output / "app-original.Cargo.lock").write_bytes(original_lock)
    input_diff = git(app, "diff", "--binary", "HEAD")
    (output / "app-input.diff").write_bytes(input_diff)
    provenance = {
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "app_commit": git(app, "rev-parse", "HEAD").decode().strip(),
        "app_branch": git(app, "branch", "--show-current").decode().strip(),
        "app_tracked_inputs": initial_inputs,
        "app_input_diff_sha256": digest(input_diff),
        "build_helper_sha256": digest(Path(__file__).read_bytes()),
        "initial_app_lock_sha256": digest(original_lock),
        "rustc": command(["rustc", "--version"], app).decode().strip(),
        "cargo": command(["cargo", "--version"], app).decode().strip(),
        "target_dir": str(target), "builds": {},
    }
    write_json(output / "provenance.json", provenance)
    try:
        refs = [("master", args.master_ref), ("patch", args.patch_ref)]
        for label, ref in refs:
            revision = snapshot(repo, ref, output / label)
            provenance["builds"][label] = {"requested_ref": ref, "commit": revision}
        common_graph = None
        for index, (label, _) in enumerate(refs):
            source = output / label
            if app_inputs(app) != initial_inputs or lock_path.read_bytes() != expected_lock:
                raise RuntimeError("app inputs changed during the comparison; aborting")
            override = f"patch.crates-io.femtovg.path={json.dumps(str(source))}"
            metadata_command = ["cargo", "metadata", "--offline", "--format-version", "1",
                                "--features", "alustin-gui/femtovg-benchmark", "--config", override]
            if index:
                metadata_command.append("--locked")
            # Only the first metadata resolution may update Cargo.lock. Capture its
            # exact result for the conditional restoration below, including failures.
            try:
                metadata_raw = command(metadata_command, app)
            finally:
                if not index:
                    expected_lock = lock_path.read_bytes()
                    (output / "resolved.Cargo.lock").write_bytes(expected_lock)
                    (output / "Cargo.lock.diff").write_text("".join(difflib.unified_diff(
                        original_lock.decode().splitlines(keepends=True),
                        expected_lock.decode().splitlines(keepends=True),
                        fromfile="app-original.Cargo.lock", tofile="resolved.Cargo.lock")))
            (output / f"{label}-metadata.json").write_bytes(metadata_raw)
            dependency_graph, versions = graph(json.loads(metadata_raw), app, source)
            if common_graph is None:
                common_graph = dependency_graph
                write_json(output / "dependency-graph.json", common_graph)
            elif common_graph != dependency_graph:
                write_json(output / "patch-dependency-graph.json", dependency_graph)
                raise RuntimeError("master and patch dependency graphs differ")
            if lock_path.read_bytes() != expected_lock or app_inputs(app) != initial_inputs:
                raise RuntimeError("Cargo resolution changed unexpected app inputs")
            build_command = ["cargo", "build", "--release", "--locked", "--offline", "-p", "alustin-gui",
                             "--features", "femtovg-benchmark", "--bin", "alustin-gui", "--example", "startup_bench",
                             "--config", override, "--target-dir", str(target)]
            record = provenance["builds"][label]
            record.update({"build_command": build_command, "metadata_command": metadata_command,
                           "resolved_lock_sha256": digest(expected_lock), **versions})
            write_json(output / "provenance.json", provenance)
            with (output / f"{label}-build.log").open("wb") as log:
                subprocess.run(build_command, cwd=app, stdout=log, stderr=subprocess.STDOUT, check=True)
            if lock_path.read_bytes() != expected_lock or app_inputs(app) != initial_inputs:
                raise RuntimeError("build changed app inputs unexpectedly")
            destination = output / "bin" / label
            destination.mkdir(parents=True)
            # Preserve this variant before the shared target is reused for the next.
            for name, built in [("alustin-gui", target / "release/alustin-gui"),
                                ("startup_bench", target / "release/examples/startup_bench")]:
                shutil.copy2(built, destination / name)
            record["binary_sha256"] = {p.name: digest(p.read_bytes()) for p in destination.iterdir()}
            record["source_sha256"] = {
                str(p.relative_to(source)): digest(p.read_bytes())
                for p in source.rglob("*") if p.is_file()
            }
            if not index:
                shutil.copy2(destination / "startup_bench", output / "bin/startup_bench")
            write_json(output / "provenance.json", provenance)
    finally:
        current_lock = lock_path.read_bytes()
        if current_lock == expected_lock:
            if current_lock != original_lock:
                replacement = output / "restore.Cargo.lock"
                replacement.write_bytes(original_lock)
                # Copy back in place: output and the checkout can use different filesystems.
                lock_path.write_bytes(replacement.read_bytes())
            provenance["app_lock_restored"] = lock_path.read_bytes() == original_lock
        else:
            provenance["app_lock_restored"] = False
            provenance["lock_restore_error"] = "Cargo.lock changed after resolution; preserving the external edit"
            (output / "unexpected.Cargo.lock").write_bytes(current_lock)
        provenance["final_app_inputs_match"] = app_inputs(app) == initial_inputs
        write_json(output / "provenance.json", provenance)
        if not provenance["app_lock_restored"]:
            raise RuntimeError(f"lock restoration refused; compare original/resolved/unexpected locks in {output}")
    print(f"Built both variants without launching them; artifacts: {output}")


if __name__ == "__main__":
    main()
