#!/usr/bin/env python3
"""Stage or install an additive, independently auditable Latin font study.

Source preparation is safe during timing. Executing staging is not: it hashes
the live proofs, compresses retained records and checks the baseline. Root
owns quiet scheduling and actual installation. No build, benchmark, download,
commit, push or historical result rewrite is performed by this driver.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile

LABEL = "aggressive-font-search"
ROLE = "exploratory-latin-font-search"
TOOLS = ("verify-results.py", "archive-study.py")
COHORTS = (("broad-29", "", 29), ("hinted-10", "hinted-supplement-v1", 10),
           ("ornate-8", "ornate-supplement-v1", 8))
REQUIRED_CAMPAIGNS = ("font-stress-search", "updated-cache-examples", "cjk-font-search")
DEMO_READER = "supporting/audit_demo_screen_effects_archive.py"
PUBLISHED_DEMO_READER = "independent_aggressive_demo_screen_audit.py"
CONFIRMATION_READER = "demo-confirmation-analysis-v1/independent_demo_confirmation_audit.py"
PUBLISHED_CONFIRMATION_READER = "independent_aggressive_demo_confirmation_audit.py"
MAX_ARCHIVE_BYTES = 104857600


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def info(path):
    path = Path(path)
    return {"sha256": sha(path), "bytes": path.stat().st_size}


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def complete(path):
    value = load(path)
    if value.get("complete") is not True:
        raise ValueError("Completed evidence required: " + str(path))
    return value


def relative(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/")):
        raise ValueError("Unsafe relative path: " + repr(value))
    return Path(path)


def cohort_root(source, value):
    return source if value == "" else source / relative(value)


def records(root):
    root = Path(root)
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("Symlink in installation stage: " + str(root))
    return {p.relative_to(root).as_posix(): info(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Expected unique baseline adaptation marker: " + repr(old))
    return text.replace(old, new)


def check_binding(binding, required):
    path = Path(binding["path"])
    if not path.is_absolute() or not path.is_file() or info(path) != {
            k: binding[k] for k in ("sha256", "bytes")}:
        raise ValueError("Completed live input changed: " + str(path))
    required.append(path)


def validate_inputs(source, repo, manifest_path):
    manifest = complete(manifest_path)
    if manifest.get("schema") != 1 or manifest.get("pending_audits"):
        raise ValueError("Final schema-1 manifest with no pending audits required")
    declared = manifest.get("cohorts", [])
    expected = [(label, root, count) for label, root, count in COHORTS]
    if [(c["label"], c["root"], c["candidate_fonts"]) for c in declared] != expected:
        raise ValueError("Exactly the independently frozen29/10/8 cohorts must be declared")
    native_reader = repo / "scripts/independent_cjk_native_audit.py"
    required = [manifest_path, native_reader, source / DEMO_READER]
    native_screens = []
    for cohort in declared:
        root = cohort_root(source, cohort["root"])
        acquired_path = root / "acquired-files.json"
        acquired = complete(acquired_path)
        if len(acquired["candidates"]) != cohort["candidate_fonts"]:
            raise ValueError("Acquired candidate count differs: " + cohort["label"])
        required.append(acquired_path)
        for asset in acquired["files"]:
            if asset.get("complete") is not True:
                raise ValueError("Unfinished acquired asset")
            check_binding(asset, required)
            raw = Path(asset["path"]).read_bytes()
            blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
            if len(raw) != asset["repository_bytes"] or blob != asset["repository_blob_sha1"]:
                raise ValueError("Acquired official Git blob differs: " + asset["path"])
        protocol_path = root / "native-prescreen-protocol-v1.json"
        protocol = complete(protocol_path)
        if not protocol["source_only_protocol"] or (protocol["trials"], protocol["repeats"], protocol["rounds"]) != (4, 3, 1):
            raise ValueError("Original native prescreen protocol required")
        if protocol["font_count_including_controls"] != cohort["candidate_fonts"] + 2:
            raise ValueError("Native Rye/Vollkorn controls missing")
        for binding in protocol["bindings"]:
            check_binding(binding, required)
        required.append(protocol_path)
        native_path = root / relative(cohort["native_live_audit"])
        native = complete(native_path)
        if native["inspector_sha256"] != sha(native_reader) or native.get("missing_binaries_explicit_archive_mode"):
            raise ValueError("Native completed live audit/source binding required")
        if len(native["screens"]) != 1 or Path(native["screens"][0]["root"]).resolve() != (root / "native-prescreen-v1").resolve():
            raise ValueError("Native audit does not cover its exact frozen cohort")
        screen = native["screens"][0]
        if len(screen["successful_launches"]) + len(screen["rejected_launches"]) != protocol["font_count_including_controls"]:
            raise ValueError("Successful or rejected native processes missing")
        for path, expected_info in native["inputs"].items():
            check_binding({"path": path, **expected_info}, required)
        required.append(native_path)
        native_screens.append([cohort["label"], (Path(cohort["root"]) / "native-prescreen-v1").as_posix()])
        demo_path = root / relative(cohort["demo_archive_audit"])
        demo = complete(demo_path)
        if demo["auditor"]["sha256"] != sha(source / DEMO_READER):
            raise ValueError("Demo audit differs from retained archive-capable reader")
        policy = demo.get("archive_policy", {})
        if policy.get("omitted_compiled_bodies") or not policy.get("font_source_build_dependency_metadata_checks_retained") or policy.get("wrapper_and_collector_imported") is not False:
            raise ValueError("Completed full live audit from archive-capable reader required")
        for field in ("wrapper", "protocol", "selection", "provenance", "analysis"):
            check_binding(demo[field], required)
        for field in ("identity_adapter", "identity_adapter_source_proof"):
            check_binding(policy[field], required)
        selection = complete(root / "demo-selection-v1/selection.json")
        expected_fonts = cohort["candidate_fonts"] + 2
        if len(selection["fonts"]) != expected_fonts or demo["processes_checked"] != expected_fonts * 4 or demo["raw_original_stdout_rows_checked"] != expected_fonts * 60:
            raise ValueError("Entire two-block/three-trial demo cohort must be audited")
        # This reader independently checks the guarded source and raw identity;
        # run it again before a reviewable stage so no stale output is trusted.
        required.append(demo_path)
    audits = manifest.get("analysis_audits", [])
    if len(audits) < 4 or audits[0].get("suite") != "aggressive-native" or audits[0].get("screens") != native_screens:
        raise ValueError("All three native cohorts must enter one explicit audit plan")
    expected_demo = [root for _, root, _ in COHORTS]
    actual_demo = [a["cohort_root"] for a in audits if a.get("suite") == "aggressive-demo-screen"]
    if actual_demo != expected_demo:
        raise ValueError("Exactly all three exploratory application cohorts must be audited")
    if any(a.get("campaign") != LABEL or a.get("suite") not in ("aggressive-native", "aggressive-demo-screen", "aggressive-demo-confirmation") for a in audits):
        raise ValueError("Unsupported analysis audit suite")
    if any(a.get("required_campaigns") != list(REQUIRED_CAMPAIGNS) for a in audits):
        raise ValueError("Exact original/font/CJK companion campaigns must be declared")
    confirmations = manifest.get("confirmations", [])
    confirmation_audits = [a for a in audits if a.get("suite") == "aggressive-demo-confirmation"]
    if not confirmations or [c["audit_plan"] for c in confirmations] != confirmation_audits:
        raise ValueError("Final selected fonts require separately declared completed confirmation audits")
    confirmation_reader = source / CONFIRMATION_READER
    required.append(confirmation_reader)
    for confirmation in confirmations:
        final = complete(source / relative(confirmation["completed_audit"]))
        if final["auditor_sha256"] != sha(confirmation_reader) or not final.get("live_source_font_binary_rgba_checks_in_completed_analysis"):
            raise ValueError("Final confirmation audit/source identity differs")
        plan = confirmation["audit_plan"]
        root = cohort_root(source, plan["audit_root"])
        analysis = source / relative(plan["analysis"]) if plan.get("analysis") else root / "analysis"
        summary = complete(analysis / "summary.json")
        raw = complete(analysis / "raw-audit.json")
        if raw.get("metadata_only") is not False or final["summary_sha256"] != sha(analysis / "summary.json"):
            raise ValueError("Full original live confirmation analysis required")
        for field in ("cpu", "gpu", "analysis", "selection", "collector_fix_proof"):
            if plan.get(field):
                path = source / relative(plan[field])
                if not path.exists():
                    raise ValueError("Declared confirmation input missing: " + str(path))
                if path.is_file():
                    required.append(path)
        required += [source / relative(confirmation["completed_audit"]), analysis / "summary.json", analysis / "raw-audit.json"]
    if set(manifest.get("reports", {})) != {"AGGRESSIVE-FONT-SEARCH.md", "SUMMARY-AGGRESSIVE-FONT-SEARCH.md"}:
        raise ValueError("Both final Latin study reports required")
    inputs_path = source / relative(manifest["report_inputs"])
    inputs = complete(inputs_path)
    if not inputs.get("files"):
        raise ValueError("Reports require exact input bindings")
    for path, expected_info in inputs["files"].items():
        actual_path = Path(path) if Path(path).is_absolute() else source / relative(path)
        if info(actual_path) != {k: expected_info[k] for k in ("sha256", "bytes")}:
            raise ValueError("Report input changed: " + path)
        required.append(actual_path)
    required.append(inputs_path)
    for original in [*manifest["reports"].values(), *manifest.get("visible", {})]:
        path = source / relative(original)
        if not path.is_file():
            raise ValueError("Declared final visible source missing: " + original)
        required.append(path)
    return manifest, required


def adapt(repo, stage, source):
    verifier = (repo / "scripts/verify-results.py").read_text()
    marker = "('cjk-font-report-inputs.json','cjk_font_report_inputs')"
    verifier = once(verifier, marker, marker + ",('aggressive-font-report-inputs.json','aggressive_font_report_inputs')")
    marker = "('cjk-native','cjk-localized','cjk-english','cjk-cost')"
    verifier = once(verifier, marker, "('cjk-native','cjk-localized','cjk-english','cjk-cost','aggressive-native','aggressive-demo-screen','aggressive-demo-confirmation')")
    verifier = once(verifier, "elif audit['suite']=='cjk-native':", "elif audit['suite'] in ('cjk-native','aggressive-native'):")
    marker = "        else:raise ValueError(f'Unknown audit suite: {audit[\"suite\"]}')"
    replacement = """        elif audit['suite']=='aggressive-demo-screen':
            cohort=root if audit['cohort_root']=='' else Path(location('cohort_root'))
            command += [str(REPO/'scripts/independent_aggressive_demo_screen_audit.py'),
                str(cohort),'--allow-missing-binaries']
        elif audit['suite']=='aggressive-demo-confirmation':
            confirmation_root=root if audit['audit_root']=='' else Path(location('audit_root'))
            command += [str(REPO/'scripts/independent_aggressive_demo_confirmation_audit.py'),
                '--root',str(confirmation_root)]
            for field,flag in (('cpu','--cpu'),('gpu','--gpu'),('analysis','--analysis'),
                               ('selection','--selection'),('collector_fix_proof','--collector-fix-proof')):
                if audit.get(field):command += [flag,location(field)]
            if audit.get('control_font'):command += ['--control-font',audit['control_font']]
""" + marker
    verifier = once(verifier, marker, replacement)
    study = (repo / "scripts/archive-study.py").read_text()
    marker = "]\n\n\ndef main():"
    study = once(study, marker, f"    ({LABEL!r}, {str(source)!r}, {ROLE!r}),\n" + marker)
    for name, text in (("verify-results.py", verifier), ("archive-study.py", study)):
        ast.parse(text, filename=name)
        (stage / "scripts" / name).write_text(text)


def stage_update(args):
    source = args.source.resolve(strict=True)
    repo = args.repository.resolve(strict=True)
    stage = args.stage.resolve()
    if stage.exists() or stage.is_relative_to(repo) or stage.is_relative_to(source):
        raise ValueError("Fresh stage outside source and repository required")
    manifest_path = (args.manifest or source / "aggressive-persistence-manifest.json").resolve(strict=True)
    manifest, required = validate_inputs(source, repo, manifest_path)
    index = load(repo / "results/index.json")
    old = json.loads(json.dumps(index))
    labels = {entry["label"] for entry in index["campaigns"]}
    if LABEL in labels or not set(REQUIRED_CAMPAIGNS) <= labels or (len(index["campaigns"]), len(index["analysis_audits"])) != (31, 15):
        raise ValueError("Reviewed installed CJK baseline of31 campaigns/15 audits required")
    sys.path.insert(0, str(repo / "scripts"))
    from benchlib import bundled_manifest
    bundled_manifest(repo)
    # Archive bodies have their independent manifest digests. Protect every
    # other historical file without redundantly hashing all large bodies here.
    archive_paths = {entry["path"] + "/" + entry["archive"]["path"] for entry in index["campaigns"]}
    protected = [p for p in repo.rglob("*") if p.is_file() and ".git" not in p.relative_to(repo).parts
                 and "__pycache__" not in p.parts and p.relative_to(repo).as_posix() not in archive_paths]
    baseline = {p.relative_to(repo).as_posix(): sha(p) for p in sorted(protected)}
    stage.mkdir(parents=True)
    (stage / "scripts").mkdir()
    adapt(repo, stage, source)
    evidence = Path(tempfile.mkdtemp(prefix="repository-tools-", dir=source))
    for name in TOOLS:
        shutil.copy2(stage / "scripts" / name, evidence / name)
    shutil.copy2(__file__, evidence / "install-aggressive-study.py")
    shutil.copy2(source / DEMO_READER, evidence / PUBLISHED_DEMO_READER)
    shutil.copy2(source / CONFIRMATION_READER, evidence / PUBLISHED_CONFIRMATION_READER)
    docs = args.docs.resolve(strict=True)
    shutil.copy2(docs, evidence / "aggressive-font-reproduction.md")
    # Re-run source-bound live exploratory proofs at the staging boundary. This
    # invokes no renderer or timing kernel and retains fresh outputs in evidence.
    for label, root, _ in COHORTS:
        subprocess.run([sys.executable, "-B", str(source / DEMO_READER),
                        str(cohort_root(source, root)), "--output", str(evidence / (label + "-demo-live-audit.json"))], check=True)
    for number, confirmation in enumerate(manifest["confirmations"], 1):
        plan = confirmation["audit_plan"]
        command = [sys.executable, "-B", str(source / CONFIRMATION_READER), "--root", str(cohort_root(source, plan["audit_root"]))]
        for field, flag in (("cpu", "--cpu"), ("gpu", "--gpu"), ("analysis", "--analysis"), ("selection", "--selection"), ("collector_fix_proof", "--collector-fix-proof")):
            if plan.get(field):
                command += [flag, str(source / relative(plan[field]))]
        if plan.get("control_font"):
            command += ["--control-font", plan["control_font"]]
        command += ["--output", str(evidence / ("confirmation-" + str(number) + "-live-audit.json"))]
        subprocess.run(command, check=True)
    write(evidence / "adaptation-provenance.json", {"complete": True,
        "installer_sha256": sha(__file__), "original_tool_sha256": {name: baseline["scripts/" + name] for name in TOOLS},
        "files": records(evidence), "scope": "Append three frozen Latin exploration cohorts in one lossless archive, reuse existing native auditor/storage helpers, and add separately declared raw application audits. Preserve every historical result."})
    destination = stage / "results" / LABEL
    subprocess.run([sys.executable, "-B", str(repo / "scripts/archive-campaign.py"),
                    str(source), str(destination), "--label", LABEL], check=True)
    archived = complete(destination / "archive.json")
    if archived["archive"]["bytes"] >= MAX_ARCHIVE_BYTES:
        raise ValueError("Lossless archive exceeds hosting limit; preserve this stage and prepare a separately proven storage remedy")
    index["campaigns"].append({"label": LABEL, "path": "results/" + LABEL,
        "original_root": archived["original_root"], "role": ROLE, "complete": True,
        "archive": archived["archive"], "files": len(archived["files"]), "raw_bytes": archived["raw_bytes"]})
    index["analysis_audits"].extend(manifest["analysis_audits"])
    visible = [(source / relative(original), relative(destination)) for destination, original in manifest["reports"].items()]
    visible += [(source / relative(manifest["report_inputs"]), Path("analysis/aggressive-font-original-report-inputs.json")),
                (evidence / PUBLISHED_DEMO_READER, Path("scripts") / PUBLISHED_DEMO_READER),
                (evidence / PUBLISHED_CONFIRMATION_READER, Path("scripts") / PUBLISHED_CONFIRMATION_READER),
                (evidence / "install-aggressive-study.py", Path("scripts/install-aggressive-study.py")),
                (evidence / "aggressive-font-reproduction.md", Path("docs/aggressive-font-reproduction.md"))]
    visible += [(source / relative(original), relative(destination)) for original, destination in manifest.get("visible", {}).items()]
    names = [p.as_posix() for _, p in visible]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate new visible destinations")
    copies = load(repo / "analysis/copy-manifest.json")
    for original, path in visible:
        if not original.is_file() or (stage / path).exists() or (repo / path).exists():
            raise ValueError("New visible source missing or destination exists: " + str(path))
        (stage / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, stage / path)
        copies[path.as_posix()] = {"source": str(original), **info(original)}
    for name in TOOLS:
        copies["scripts/" + name] = {"source": str(evidence / name), **info(evidence / name)}
    write(stage / "analysis/aggressive-font-report-inputs.json", {path.as_posix(): sha(stage / path) for _, path in visible})
    write(stage / "analysis/copy-manifest.json", copies)
    write(stage / "results/index.json", index)
    addition = "\n## Aggressive Latin font investigation\n\nThe [Latin font study](AGGRESSIVE-FONT-SEARCH.md) preserves three separately frozen exploration cohorts and all original failed or rejected attempts. Native hinting/geometry costs remain distinct from unchanged-demo cache comparisons. See the [summary](SUMMARY-AGGRESSIVE-FONT-SEARCH.md) and [reproduction notes](docs/aggressive-font-reproduction.md).\n"
    (stage / "README.md").write_text((repo / "README.md").read_text().rstrip() + "\n" + addition)
    if index["campaigns"][:-1] != old["campaigns"] or index["analysis_audits"][:15] != old["analysis_audits"]:
        raise ValueError("Historical index entries changed")
    proof = {"schema": 1, "complete": True, "installed": False,
        "repository": str(repo), "source": str(source), "stage": str(stage),
        "installer_sha256": sha(__file__), "old_repository_file_sha256": baseline,
        "old_archive_records": [entry["archive"] for entry in old["campaigns"]],
        "old_campaign_count": 31, "old_audit_count": 15, "new_labels": [LABEL],
        "staged_files": records(stage), "completed_inputs": {str(path): sha(path) for path in required},
        "policy": "Add auditable Latin records and summaries without changing old result reports or performing commit/remote operations."}
    write(stage / "installation-plan.json", proof)
    print("Reviewable additive Latin font update staged:", stage)
    return proof


def atomic_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="." + destination.name + "-", dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name)
        with source.open("rb") as original:
            shutil.copyfileobj(original, stream)
    shutil.copystat(source, temporary)
    os.replace(temporary, destination)


def install(args, proof):
    repo = args.repository.resolve(strict=True)
    stage = args.stage.resolve(strict=True)
    if not proof.get("complete") or proof.get("installed") or proof["repository"] != str(repo) or proof["stage"] != str(stage):
        raise ValueError("Completed unchanged uninstalled plan required")
    for path, digest in proof["old_repository_file_sha256"].items():
        if sha(repo / path) != digest:
            raise ValueError("Repository changed after staging: " + path)
    for path, expected in proof["staged_files"].items():
        if info(stage / path) != expected:
            raise ValueError("Stage changed after review: " + path)
    allowed = {"README.md", "results/index.json", "analysis/copy-manifest.json"} | {"scripts/" + name for name in TOOLS}
    for path in proof["staged_files"]:
        if (repo / path).exists() and path not in allowed:
            raise ValueError("Existing destination: " + path)
    destination = repo / "results" / LABEL
    temporary = destination.with_name("." + LABEL + ".install-tmp")
    if destination.exists() or temporary.exists():
        raise ValueError("Latin archive destination already exists")
    shutil.copytree(stage / "results" / LABEL, temporary)
    os.replace(temporary, destination)
    for path in proof["staged_files"]:
        if path == "results/index.json" or path.startswith("results/" + LABEL + "/"):
            continue
        atomic_copy(stage / path, repo / path)
    atomic_copy(stage / "results/index.json", repo / "results/index.json")
    for path, digest in proof["old_repository_file_sha256"].items():
        if path not in allowed and sha(repo / path) != digest:
            raise ValueError("Historical evidence changed: " + path)
    proof["installed"] = True
    write(stage / "installation-plan.json", proof)
    print("Installed additive Latin campaign; historical records preserved:", repo)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--repository", type=Path, default=Path("/Users/jesse/github/femtovg-outline-cache-bench"))
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--docs", type=Path, default=Path(__file__).resolve().parent / "AGGRESSIVE-REPRODUCTION.md")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--install-existing", action="store_true")
    args = parser.parse_args()
    if args.install_existing and not args.install:
        parser.error("--install-existing requires --install")
    proof = load(args.stage / "installation-plan.json") if args.install_existing else stage_update(args)
    if args.install:
        install(args, proof)


if __name__ == "__main__":
    main()
