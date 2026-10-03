#!/usr/bin/env python3
"""Stage or install an additive, independently auditable CJK font study.

Do not run staging during renderer timing: it hashes the preserved repository,
compresses the new campaign, and reads its archive back. Installation changes
only the declared new files and six existing repository maintenance files.
It never builds, benchmarks, commits, pushes, or removes historical evidence.
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

LABEL = "cjk-font-search"
ROLE = "exploratory-cjk-font-search"
TOOLS = ("verify-results.py", "archive-study.py", "archive-campaign.py")
SCREENS = (("english", "native-english"), ("ko", "native-ko"),
           ("zh", "native-zh"), ("zh-pure-ui", "native-zh-pure-ui"))
ADDITIONAL_AUDITORS = {
    "cjk-localized": ("independent_localized_confirmation_audit_v2.py",
                      "independent_cjk_localized_confirmation_audit.py"),
    "cjk-english": ("supporting/audit_english_demo.py",
                    "independent_cjk_english_demo_audit.py"),
    "cjk-cost": ("supporting/audit_cost_decomposition.py",
                 "independent_cjk_cost_decomposition_audit.py"),
}
AUDIT_COMPANIONS = {
    "cjk-cost": (("mechanism-cost-screen/audit_cost_screens.py", "independent_cjk_cost_screen_audit.py"),
                 ("mechanism-weight-cost-screen/audit_weight_cost_screens.py", "independent_cjk_weight_cost_screen_audit.py")),
}
COST_COHORTS = [["default", locale] for locale in ("en", "ko", "zh")] + [
    ["weights", locale + "-w" + str(weight)] for locale in ("en", "zh") for weight in (300, 400)]


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


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


def info(path):
    path = Path(path)
    return {"sha256": sha(path), "bytes": path.stat().st_size}


def relative(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/")):
        raise ValueError("Unsafe relative path: " + repr(value))
    return Path(path)


def records(root):
    root = Path(root)
    if any(p.is_symlink() for p in root.rglob("*")):
        raise ValueError("Symlink in installation stage: " + str(root))
    return {p.relative_to(root).as_posix(): info(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Expected unique adaptation marker: " + repr(old))
    return text.replace(old, new)


def validate_inputs(source, manifest_path, native_audit_path):
    manifest = complete(manifest_path)
    if manifest.get("schema") != 1:
        raise ValueError("Unknown CJK persistence-manifest schema")
    plan = complete(source / "native-campaign-plan.json")
    if not plan.get("exploratory") or [c["tag"] for c in plan["campaigns"]] != [s[0] for s in SCREENS]:
        raise ValueError("Expected four explicitly exploratory native campaigns")
    if any(not c.get("complete") or c.get("exit_code") != 0 for c in plan["campaigns"]):
        raise ValueError("Every declared native campaign must have completed")
    auditor = source / "supporting/audit_native_screens.py"
    audit = complete(native_audit_path)
    if audit["inspector_sha256"] != sha(auditor):
        raise ValueError("Native audit was produced by a different auditor source")
    if audit.get("missing_binaries_explicit_archive_mode"):
        raise ValueError("Installation requires completed original live native auditing")
    observed = [(s["screen"], str(Path(s["root"]).resolve())) for s in audit["screens"]]
    expected = [(name, str((source / path).resolve())) for name, path in SCREENS]
    if observed != expected:
        raise ValueError("Native audit does not cover the exact four declared campaigns")
    required = [manifest_path, native_audit_path, auditor, source / "native-campaign-plan.json"]
    for _, path in SCREENS:
        required.append(source / path / "provenance.json")
        complete(required[-1])
    # Rebind every original file checked by the live independent auditor. It
    # checks font/source/build/lock/raw evidence, not merely copied medians.
    for original, expected_info in audit["inputs"].items():
        original_path = Path(original)
        if not original_path.is_file() or info(original_path) != {
                k: expected_info[k] for k in ("sha256", "bytes")}:
            raise ValueError("Native audit input changed: " + original)
        required.append(original_path)
    reports = manifest.get("reports", {})
    if set(reports) != {"CJK-FONT-SEARCH.md", "SUMMARY-CJK-FONT-SEARCH.md"}:
        raise ValueError("Both final CJK report documents must be declared")
    report_inputs_path = source / relative(manifest["report_inputs"])
    report_inputs = complete(report_inputs_path)
    required.append(report_inputs_path)
    if not report_inputs.get("files"):
        raise ValueError("Report input bindings are required")
    for original, expected_info in report_inputs["files"].items():
        path = Path(original)
        if not path.is_absolute():
            path = source / relative(original)
        expected_hash = expected_info["sha256"] if isinstance(expected_info, dict) else expected_info
        if sha(path) != expected_hash or (isinstance(expected_info, dict) and
                "bytes" in expected_info and path.stat().st_size != expected_info["bytes"]):
            raise ValueError("CJK report input changed: " + str(path))
        required.append(path)
    for destination, original in reports.items():
        path = source / relative(original)
        if not path.is_file():
            raise ValueError("Final CJK report missing: " + destination)
        required.append(path)
    for original, destination in manifest.get("visible", {}).items():
        path = source / relative(original)
        relative(destination)
        if not path.is_file():
            raise ValueError("Declared visible evidence missing: " + original)
        required.append(path)
    application_plan = None
    if manifest.get("application_plan"):
        application_plan_path = source / relative(manifest["application_plan"])
        application_plan = complete(application_plan_path)
        if any(not launch.get("complete") or launch.get("exit_code") != 0
               for launch in application_plan.get("launches", [])):
            raise ValueError("Every launch in the explicitly selected application plan must complete")
        driver = application_plan["driver"]
        if info(driver["path"]) != {key: driver[key] for key in ("sha256", "bytes")}:
            raise ValueError("Application plan driver changed")
        expected_launches = {"pixels-ko", "pixels-zh", "english-exploratory", "cpu-ko", "cpu-zh"}
        if {launch["label"] for launch in application_plan["launches"]} != expected_launches or len(application_plan["launches"]) != 5:
            raise ValueError("Expected exactly the five declared application launches")
        for cohort in application_plan["campaigns"]:
            selection = cohort["selection"]
            if info(selection["path"]) != {key: selection[key] for key in ("sha256", "bytes")}:
                raise ValueError("Application frozen selection changed")
        required.append(application_plan_path)
    for extra in manifest.get("additional_audits", []):
        if extra.get("campaign") != LABEL or extra.get("suite") not in ADDITIONAL_AUDITORS:
            raise ValueError("Additional audit needs a supported explicit suite for this campaign")
        audit_root = source / relative(extra["audit_root"])
        completed_path = source / relative(extra["completed_audit"])
        additional = complete(completed_path)
        original, _ = ADDITIONAL_AUDITORS[extra["suite"]]
        script = source / original
        digest = additional.get("auditor_sha256", additional.get("inspector_sha256"))
        if digest != sha(script):
            raise ValueError("Additional audit is not bound to its retained auditor source")
        if not audit_root.is_dir():
            raise ValueError("Additional audit cohort root is missing")
        if extra["suite"] == "cjk-localized" and not completed_path.is_relative_to(audit_root):
            raise ValueError("Localized audit artifact must belong to its explicit cohort root")
        if extra["suite"] != "cjk-cost" and application_plan is None:
            raise ValueError("Application audits require an explicit completed application_plan manifest pointer")
        if extra["suite"] == "cjk-localized":
            if extra.get("control_font") not in ("NotoSansSC-VF", "NanumMyeongjo-Regular"):
                raise ValueError("Explicit confirmed locale control font is required")
            for path in (audit_root / "selection-frozen.json", audit_root / "confirm-cpu/cpu-provenance.json",
                         audit_root / "analysis/summary.json", audit_root / "analysis/raw-audit.json"):
                complete(path)
                required.append(path)
            if additional.get("endpoint_comparisons") != 279 or additional.get("interval_comparisons") != 560:
                raise ValueError("Expected the completed three-font CPU/DPR2 localized confirmation")
            matches = [cohort for cohort in application_plan["campaigns"]
                       if Path(cohort["campaign"]).resolve() == audit_root.resolve()]
            if len(matches) != 1 or matches[0]["control_font"] != extra["control_font"]:
                raise ValueError("Localized audit root/control differs from the explicitly selected application plan")
            fix_path = source / relative(extra["collector_fix_proof"])
            fix = complete(fix_path)
            for change in fix["changes"]:
                original_collector, fixed_collector = Path(change["original"]), Path(change["fixed"])
                if sha(original_collector) != change["original_sha256"] or sha(fixed_collector) != change["fixed_sha256"]:
                    raise ValueError("Declared collector normalization source changed")
                old = original_collector.read_text()
                if old.count("def files(root):\n") != 1 or fixed_collector.read_text() != old.replace(
                        "def files(root):\n", "def files(root):\n    root = Path(root)\n"):
                    raise ValueError("Collector adaptation must be exactly the one-line Path normalization")
                required += [original_collector, fixed_collector]
            required.append(fix_path)
        elif extra["suite"] == "cjk-english":
            if Path(additional["campaign"]).resolve() != audit_root.resolve():
                raise ValueError("English audit artifact belongs to a different explicit cohort")
            if additional.get("source_mode") != "live" or additional.get("missing_binaries_explicit_archive_mode"):
                raise ValueError("English exploratory installation requires the completed original live audit")
            if (additional.get("processes"), additional.get("raw_rows"), additional.get("endpoint_effects")) != (52, 4368, 1209):
                raise ValueError("Expected the complete 13-font, two-block, three-trial English screen")
        else:
            if Path(additional["root"]).resolve() != audit_root.resolve() or not completed_path.is_relative_to(audit_root):
                raise ValueError("Cost audit artifact must belong to its explicit timing cohort root")
            if additional.get("source_mode") != "live" or additional.get("missing_binaries_explicit_archive_mode"):
                raise ValueError("Cost installation requires completed original live auditing")
            if (extra.get("expected_processes"), extra.get("expected_raw_rows"), extra.get("expected_cases")) != (18, 12960, 360):
                raise ValueError("The manifest must declare all 18 processes, 12960 rows and 360 cost cases")
            if extra.get("timed_cohorts") != COST_COHORTS:
                raise ValueError("All seven default and explicit-weight cost cohorts must be declared")
            if (additional.get("processes"), additional.get("raw_rows"), additional.get("cases"), additional.get("timed_cohorts")) != (18, 12960, 360, 7):
                raise ValueError("Cost audit does not cover every declared process/case")
            complete(audit_root / "campaign-plan.json")
            required.append(audit_root / "campaign-plan.json")
            children = [additional["default_audit"], additional["weighted_audit"]]
            for child, (reader, _), field in zip(children, AUDIT_COMPANIONS["cjk-cost"], ("default_reader_sha256", "weight_reader_sha256")):
                if child.get("inspector_sha256") != sha(source / reader) or additional[field] != sha(source / reader):
                    raise ValueError("Cost child audit differs from its retained reader")
                required.append(source / reader)
            for evidence in [additional, *children]:
                for original, expected_info in evidence["inputs"].items():
                    original_path = Path(original)
                    if not original_path.is_file() or info(original_path) != {key: expected_info[key] for key in ("sha256", "bytes")}:
                        raise ValueError("Cost audit input changed: " + original)
                    required.append(original_path)
        required += [completed_path, script]
        # No confirmation is inferred from a directory name. Native, English
        # exploratory, and localized confirmation suites retain distinct proofs.
    return manifest, required


def adapt(repo, stage, source):
    verifier = (repo / "scripts/verify-results.py").read_text()
    marker = "('font-stress-rerun-report-inputs.json','font_stress_rerun_report_inputs')"
    verifier = once(verifier, marker, marker + ",('cjk-font-report-inputs.json','cjk_font_report_inputs')")
    marker = "    materialize=set(campaigns) if selected else set()\n"
    replacement = marker + "    full_materialize=set()\n    for audit in selected:\n        if audit['suite'] in ('cjk-native','cjk-localized','cjk-english','cjk-cost'):\n            full_materialize.update([audit['campaign'],*audit.get('required_campaigns',[])])\n"
    verifier = once(verifier, marker, replacement)
    marker = "record=store.inspect(label,destination,metadata_only=True)"
    verifier = once(verifier, marker, "record=store.inspect(label,destination,metadata_only=label not in full_materialize)")
    marker = "        else:raise ValueError(f'Unknown audit suite: {audit[\"suite\"]}')"
    replacement = """        elif audit['suite']=='cjk-native':
            command += [str(REPO/'scripts/independent_cjk_native_audit.py'),'--allow-missing-binaries']
            for name,relative_path in audit['screens']:
                safe_relative(relative_path)
                screen=root/relative_path
                if not screen.is_dir():raise ValueError('Native screen input not retained: '+relative_path)
                command += ['--screen',name,str(screen)]
        elif audit['suite']=='cjk-localized':
            command += [str(REPO/'scripts/independent_cjk_localized_confirmation_audit.py'),
                '--root',location('audit_root'),'--control-font',audit['control_font'],
                '--collector-fix-proof',location('collector_fix_proof')]
        elif audit['suite']=='cjk-english':
            command += [str(REPO/'scripts/independent_cjk_english_demo_audit.py'),
                '--root',location('audit_root'),'--allow-missing-binaries']
        elif audit['suite']=='cjk-cost':
            if (audit.get('expected_processes'),audit.get('expected_raw_rows'),audit.get('expected_cases'))!=(18,12960,360):
                raise ValueError('Full cost-cohort dimensions must be declared')
            command += [str(REPO/'scripts/independent_cjk_cost_decomposition_audit.py'),
                '--root',location('audit_root'),'--allow-missing-binaries',
                '--default-reader',str(REPO/'scripts/independent_cjk_cost_screen_audit.py'),
                '--weight-reader',str(REPO/'scripts/independent_cjk_weight_cost_screen_audit.py')]
""" + marker
    verifier = once(verifier, marker, replacement)
    marker = "Selected replay/app/font-confirmation cohorts declared in analysis_audits; historical campaigns retain exact records and are checksum verified"
    verifier = once(verifier, marker, "Selected replay/app/font-confirmation cohorts, exploratory CJK native/English/cost screens, and separately labeled localized CPU confirmations declared in analysis_audits; historical campaigns retain exact records and are checksum verified")
    archive_study = (repo / "scripts/archive-study.py").read_text()
    marker = "]\n\n\ndef main():"
    archive_study = once(archive_study, marker,
                         f"    ({LABEL!r}, {str(source)!r}, {ROLE!r}),\n" + marker)
    archive_campaign = (repo / "scripts/archive-campaign.py").read_text()
    marker = 'PRUNE = {"target", '
    archive_campaign = once(archive_campaign, marker,
                            'PRUNE = {"target", "targets", "target-native", "target-counted", ')
    for name, text in (("verify-results.py", verifier), ("archive-study.py", archive_study),
                       ("archive-campaign.py", archive_campaign)):
        ast.parse(text, filename=name)
        (stage / "scripts" / name).write_text(text)


def stage_update(args):
    source = args.source.resolve(strict=True)
    repo = args.repository.resolve(strict=True)
    stage = args.stage.resolve()
    if stage.exists() or stage.is_relative_to(repo) or stage.is_relative_to(source):
        raise ValueError("Fresh stage outside repository and campaign required")
    manifest_path = (args.manifest or source / "cjk-persistence-manifest.json").resolve(strict=True)
    native_audit_path = args.native_audit.resolve(strict=True)
    manifest, required = validate_inputs(source, manifest_path, native_audit_path)
    index = load(repo / "results/index.json")
    old = json.loads(json.dumps(index))
    labels = {entry["label"] for entry in index["campaigns"]}
    if LABEL in labels or not {"font-stress-search", "font-stress-rerun", "updated-cache-examples"} <= labels:
        raise ValueError("Preserved original and repeat font campaigns required; no previous CJK archive allowed")
    if (len(old["campaigns"]), len(old["analysis_audits"])) != (30, 10):
        raise ValueError("Expected the reviewed baseline of 30 campaigns and 10 audits")
    sys.path.insert(0, str(repo / "scripts"))
    from benchlib import bundled_manifest
    bundled_manifest(repo)
    protected = [path for path in repo.rglob("*") if path.is_file()
                 and ".git" not in path.relative_to(repo).parts
                 and "__pycache__" not in path.parts
                 and not (path.name.endswith((".tar.gz", ".tgz"))
                          and "results" in path.relative_to(repo).parts)]
    baseline = {path.relative_to(repo).as_posix(): sha(path) for path in sorted(protected)}
    stage.mkdir(parents=True)
    (stage / "scripts").mkdir()
    adapt(repo, stage, source)
    evidence = Path(tempfile.mkdtemp(prefix="repository-tools-", dir=source))
    for name in TOOLS:
        shutil.copy2(stage / "scripts" / name, evidence / name)
    shutil.copy2(__file__, evidence / "install-cjk-study.py")
    shutil.copy2(source / "supporting/audit_native_screens.py", evidence / "independent_cjk_native_audit.py")
    additional_sources = {}
    for extra in manifest.get("additional_audits", []):
        original, published = ADDITIONAL_AUDITORS[extra["suite"]]
        if published not in additional_sources:
            shutil.copy2(source / original, evidence / published)
            additional_sources[published] = evidence / published
        for original, published in AUDIT_COMPANIONS.get(extra["suite"], []):
            if published not in additional_sources:
                shutil.copy2(source / original, evidence / published)
                additional_sources[published] = evidence / published
    docs = args.docs.resolve(strict=True)
    shutil.copy2(docs, evidence / "cjk-font-reproduction.md")
    write(evidence / "adaptation-provenance.json", {
        "complete": True, "installer_sha256": sha(__file__),
        "original_tool_sha256": {name: baseline["scripts/" + name] for name in TOOLS},
        "files": records(evidence),
        "scope": "Append one CJK archive, exploratory native/English/cost audits and separately declared localized confirmation audits; retain every historical campaign, audit and report; fully verify/materialize font/source inputs for independent auditing."})
    destination = stage / "results" / LABEL
    subprocess.run([sys.executable, "-B", str(stage / "scripts/archive-campaign.py"),
                    str(source), str(destination), "--label", LABEL], check=True)
    archived = complete(destination / "archive.json")
    index["campaigns"].append({"label": LABEL, "path": "results/" + LABEL,
        "original_root": archived["original_root"], "role": ROLE, "complete": True,
        "archive": archived["archive"], "files": len(archived["files"]), "raw_bytes": archived["raw_bytes"]})
    index["analysis_audits"].append({"suite": "cjk-native", "campaign": LABEL,
        "required_campaigns": ["font-stress-search", "updated-cache-examples"],
        "screens": [list(screen) for screen in SCREENS],
        "scope": "Exploratory independent native raw/order/duration/coverage/count/digest/source/build/lock/font audit. Native exact image/geometry assertions; no application/cache gain or confidence interval inferred."})
    index["analysis_audits"].extend(manifest.get("additional_audits", []))
    visible = [(source / relative(original), Path(destination))
               for destination, original in manifest["reports"].items()]
    visible += [(source / relative(manifest["report_inputs"]), Path("analysis/cjk-font-original-report-inputs.json")),
                (native_audit_path, Path("analysis/cjk-font-search/independent-native-audit.json")),
                (evidence / "independent_cjk_native_audit.py", Path("scripts/independent_cjk_native_audit.py")),
                (evidence / "install-cjk-study.py", Path("scripts/install-cjk-study.py")),
                (evidence / "cjk-font-reproduction.md", Path("docs/cjk-font-reproduction.md"))]
    visible += [(source / relative(original), relative(destination))
                for original, destination in manifest.get("visible", {}).items()]
    visible += [(original, Path("scripts") / published)
                for published, original in additional_sources.items()]
    names = [path.as_posix() for _, path in visible]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate new visible destination")
    copies = load(repo / "analysis/copy-manifest.json")
    for original, path in visible:
        if not original.is_file() or (stage / path).exists() or (repo / path).exists():
            raise ValueError("New CJK source missing or destination exists: " + str(path))
        (stage / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, stage / path)
        copies[path.as_posix()] = {"source": str(original), **info(original)}
    for name in TOOLS:
        copies["scripts/" + name] = {"source": str(evidence / name), **info(evidence / name)}
    write(stage / "analysis/cjk-font-report-inputs.json",
          {path.as_posix(): sha(stage / path) for _, path in visible})
    write(stage / "analysis/copy-manifest.json", copies)
    write(stage / "results/index.json", index)
    addition = "\n## CJK font investigation\n\nThe [CJK font study](CJK-FONT-SEARCH.md) preserves the original English demo,\nadds explicitly labeled localized workloads where measured, and reports native\nglyph screening separately from application/cache comparisons. All earlier\nfont studies and their raw cohorts remain retained. See the\n[summary](SUMMARY-CJK-FONT-SEARCH.md) and\n[reproduction notes](docs/cjk-font-reproduction.md).\n"
    (stage / "README.md").write_text((repo / "README.md").read_text().rstrip() + "\n" + addition)
    assert index["campaigns"][:-1] == old["campaigns"]
    assert index["analysis_audits"][:len(old["analysis_audits"])] == old["analysis_audits"]
    proof = {"schema": 1, "complete": True, "installed": False,
        "repository": str(repo), "source": str(source), "stage": str(stage),
        "installer_sha256": sha(__file__), "old_repository_file_sha256": baseline,
        "old_campaign_count": len(old["campaigns"]), "old_audit_count": len(old["analysis_audits"]),
        "new_labels": [LABEL], "staged_files": records(stage),
        "completed_inputs": {str(path): sha(path) for path in required},
        "policy": "Append auditable CJK records and summaries; preserve every previous numerical report/archive/index entry; no commit or remote action."}
    write(stage / "installation-plan.json", proof)
    print("Reviewable additive CJK update staged:", stage)
    return proof


def atomic_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="." + destination.name + "-", dir=destination.parent,
                                     delete=False) as stream:
        temporary = Path(stream.name)
        with source.open("rb") as original:
            shutil.copyfileobj(original, stream)
    shutil.copystat(source, temporary)
    os.replace(temporary, destination)


def install(args, proof):
    repo = args.repository.resolve(strict=True)
    stage = args.stage.resolve(strict=True)
    if not proof.get("complete") or proof.get("installed") or proof["repository"] != str(repo) or proof["stage"] != str(stage):
        raise ValueError("Completed unchanged uninstalled plan required for this repository/stage")
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
        raise ValueError("CJK archive destination already exists")
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
    print("Installed additive CJK campaign; historical records preserved:", repo)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--repository", type=Path, default=Path("/Users/jesse/github/femtovg-outline-cache-bench"))
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--native-audit", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--docs", type=Path, default=Path(__file__).resolve().parent / "CJK-REPRODUCTION.md")
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
