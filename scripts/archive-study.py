#!/usr/bin/env python3
"""Archive the completed local study roots; keep existing verified archives."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parent.parent
CAMPAIGNS = [
    ("original-alustin", "alustin-femtovg-outline-review", "historical"),
    ("original-examples", "femtovg-example-outline-review", "historical"),
    ("original-e2e", "femtovg-outline-e2e-review", "historical"),
    ("font-alustin", "alustin-font-outline-review", "historical"),
    ("liberation-examples", "femtovg-liberation-example-review", "historical"),
    ("pt-sans-font-study", "pt-sans-outline-review", "historical"),
    ("font-hint-search", "femtovg-open-font-search", "historical"),
    ("liberation-font-inspection", "femtovg-liberation-font-review", "historical"),
    ("pt-sans-examples", "femtovg-pt-sans-outline-review", "historical"),
    ("pt-sans-alustin", "alustin-pt-sans-outline-review", "historical"),
    ("admission-examples", "femtovg-admission-review", "historical"),
    ("admission-alustin", "alustin-admission-review", "historical"),
    ("miss-screening-examples", "femtovg-miss-review", "screening"),
    ("miss-screening-alustin", "alustin-miss-review", "screening"),
    ("draft-final-examples", "femtovg-miss-final-review", "superseded"),
    ("draft-final-alustin", "alustin-miss-final-review", "superseded"),
    ("draft-selection-examples", "femtovg-miss-selection-review", "superseded"),
    ("draft-selection-alustin", "alustin-miss-selection-review", "superseded"),
    ("gray8-diagnosis", "femtovg-gray8-diagnose", "correctness-diagnosis"),
    ("selection-examples", "femtovg-miss-selection-v2-review", "final-selection"),
    ("selection-alustin", "alustin-miss-selection-v2-review", "final-selection"),
    ("portable-validation", "femtovg-outline-cache-bench/runs/portable-validation", "functional-validation"),
    ("native-pool-examples", "femtovg-outline-pool-review", "native-outline-comparison"),
    ("native-pool-alustin", "alustin-outline-pool-review", "native-outline-comparison"),
    ("native-pool-source-bundle", "femtovg-outline-pool-bundle", "native-outline-reproduction"),
    ('updated-cache-examples', '/private/tmp/femtovg-updated-cache-bench-20261002', 'revised-cache-comparison'),
    ('updated-cache-alustin', '/private/tmp/femtovg-updated-cache-bench-20261002/alustin', 'revised-cache-comparison'),
    ('updated-cache-source-bundle', '/private/tmp/femtovg-updated-cache-bench-20261002/bundle', 'revised-cache-reproduction'),
    ('font-stress-search', '/private/tmp/femtovg-font-stress-search-20261002', 'favorable-font-confirmation'),
    ('font-stress-rerun', '/private/tmp/femtovg-font-stress-rerun-20261002', 'font-confirmation-repeat'),
    ('cjk-font-search', '/private/tmp/femtovg-cjk-font-search-20261002', 'exploratory-cjk-font-search'),
    ('aggressive-font-search', '/private/tmp/femtovg-aggressive-font-search-20261002', 'exploratory-latin-font-search'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roles", nargs="+", choices=sorted({r for _, _, r in CAMPAIGNS}))
    args = parser.parse_args()
    for label, name, role in CAMPAIGNS:
        if args.roles and role not in args.roles:
            continue
        source = Path("/private/tmp") / name
        if not source.exists():
            raise RuntimeError(f"Expected study root missing: {source}")
        destination = REPO / "results" / label
        if destination.exists():
            record = json.loads((destination / "archive.json").read_text())
            if not record.get("complete"):
                raise RuntimeError(f"Existing archive is incomplete: {destination}")
            print(f"Retained existing archive: {label}", flush=True)
            continue
        command=[sys.executable, str(REPO / "scripts/archive-campaign.py"), str(source), str(destination), "--label", label]
        if label=="updated-cache-examples":command += ["--exclude-prefix","alustin","--exclude-prefix","bundle"]
        subprocess.run(command, check=True)
    index = []
    for label, name, role in CAMPAIGNS:
        destination = REPO / "results" / label
        if not destination.exists():
            continue
        record = json.loads((destination / "archive.json").read_text())
        index.append({"label": label, "path": f"results/{label}", "original_root": record["original_root"],
                      "role": role, "complete": record["complete"], "archive": record["archive"],
                      "files": len(record["files"]), "raw_bytes": record["raw_bytes"]})
    index_path = REPO / "results/index.json"
    previous = json.loads(index_path.read_text()) if index_path.exists() else {}
    previous.update(schema=1, campaigns=index)
    index_path.write_text(json.dumps(previous, indent=2) + "\n")


if __name__ == "__main__":
    main()
