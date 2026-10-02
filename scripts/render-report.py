#!/usr/bin/env python3
"""Render review tables from the preserved final point/interval summaries."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = {"stock": "Roboto Flex", "roboto": "Roboto Flex", "vollkorn": "Vollkorn Medium", "ptsans": "PT Sans Regular"}


def load(name):
    path = ROOT / "analysis" / name / "summary.csv"
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def one(rows, **keys):
    result = [r for r in rows if all(r.get(k) == str(v) for k, v in keys.items())]
    if len(result) != 1:
        raise ValueError(f"Expected one observation for {keys}; found {len(result)}")
    return result[0]


def effect(row, app=False):
    point = float(row["median_paired_change_pct" if app else "paired_delta_pct"])
    low, high = json.loads(row["median_paired_change_pct_ci95" if app else "paired_bootstrap95"])
    delta = float(row["median_paired_delta" if app else "paired_delta_us"])
    if not app:
        delta /= 1000
    return f"{point:+.1f}% [{low:+.1f}, {high:+.1f}]<br>Δ {delta:+.3f} ms"


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |",
                      *["| " + " | ".join(map(str, r)) + " |" for r in rows]])


def main():
    selection = json.loads((ROOT / "selection.json").read_text())
    selected = selection["selected_variant"]
    if selected not in {"final", "route", "current"}:
        raise ValueError("Unknown selected variant")
    replay = load("selection-examples")
    sequences = load("selection-sequences")
    app = load("selection-alustin")
    for row in replay + sequences:
        expected_trials = 5 if row["backend"] == "cpu" else 3
        if row["backend"] not in {"cpu", "gpu"} or int(row["dpi"]) != 2 or int(row["process_blocks"]) != 12 or int(row["trials_per_process"]) != expected_trials:
            raise ValueError("Primary replay report requires complete 12-block DPR2 CPU/GPU cohorts with 5/3 trials")
    if any(row["mode"] != "cpu" or int(row["n_blocks"]) != 12 for row in app):
        raise ValueError("Primary Alustin report requires complete 12-block CPU cohorts")
    parts = ["# FemtoVG Swash outline-cache study", "", selection["report_conclusion"], "",
             "The primary comparison is the selected patch versus master. Original-cache and prototype comparisons explain the selection. Negative duration changes mean faster. Cells show median paired changes, 95% whole-block bootstrap intervals, and median paired absolute changes. Absolute medians need not reproduce the paired percentage.", "",
             "## Selected patch versus master: existing examples", ""]
    rows = []
    for backend, metric in [("cpu", "draw_us"), ("gpu", "complete_us")]:
        for font in ("stock", "vollkorn", "ptsans"):
            for scene in ("demo", "text"):
                row = one(replay, backend=backend, font=font, dpi=2, scene=scene, phase="first_paint", metric=metric,
                          reference_version="master", candidate_version=selected)
                rows.append([FONTS[font], scene, "CPU drawing" if backend == "cpu" else "GPU completion",
                             f"{float(row['reference_process_median']) / 1000:.3f} → {float(row['candidate_process_median']) / 1000:.3f}", effect(row)])
    parts += [table(["Font", "Scene", "Measurement", "Master → selected (ms)", "Selected/master"], rows), "",
              "GPU completion includes drawing and submission and is not a GPU timestamp. All original example phases remain in the complete [per-phase statistics](analysis/selection-examples/summary.csv).", "",
              "## Alustin first-render CPU", "",
              "These diagnostic spans measure renderer-thread host work, including component rendering and flush. They do not establish GPU completion, compositor latency, or diagnostics-off startup.", ""]
    rows = []
    for font in ("roboto", "vollkorn", "ptsans"):
        for backend in ("winit-femtovg-wgpu", "winit-femtovg"):
            row = one(app, mode="cpu", font=font, backend=backend, metric="first_frame.render.thread_cpu_ms", reference="master", candidate=selected)
            old = one(app, mode="cpu", font=font, backend=backend, metric="first_frame.render.thread_cpu_ms", reference="master", candidate="current")
            rows.append([FONTS[font], "WGPU" if backend.endswith("wgpu") else "OpenGL",
                         f"{float(row['reference_median']):.3f} → {float(row['candidate_median']):.3f}", effect(row, True), effect(old, True)])
    parts += [table(["Font", "Backend", "Master → selected (ms)", "Selected/master", "Original cache/master"], rows), "",
              "[All Alustin spans, first and filtered search frames](analysis/selection-alustin/summary.csv) retain gains, regressions, and uncertain effects.", "",
              "## Alustin filtered search-frame CPU", "",
              "The search update can introduce new atlas keys. It is a repeated application interaction, not a completely warm redraw.", ""]
    rows = []
    for font in ("roboto", "vollkorn", "ptsans"):
        for backend in ("winit-femtovg-wgpu", "winit-femtovg"):
            row = one(app, mode="cpu", font=font, backend=backend, metric="search_frame.render.thread_cpu_ms", reference="master", candidate=selected)
            rows.append([FONTS[font], "WGPU" if backend.endswith("wgpu") else "OpenGL",
                         f"{float(row['reference_median']):.3f} → {float(row['candidate_median']):.3f}", effect(row, True)])
    parts += [table(["Font", "Backend", "Master → selected (ms)", "Selected/master"], rows), "",
              "## Alustin process memory", "",
              "Process-lifetime high-water RSS comes from the same diagnostics-on application cohort. It includes host memory for the application, renderer, fonts, driver state, and transient work; it measures neither device VRAM nor the outline cache alone.", ""]
    rows = []
    for font in ("roboto", "vollkorn", "ptsans"):
        for backend in ("winit-femtovg-wgpu", "winit-femtovg"):
            row = one(app, mode="cpu", font=font, backend=backend, metric="peak_rss_mib", reference="master", candidate=selected)
            low, high = json.loads(row["median_paired_delta_ci95"])
            rows.append([FONTS[font], "WGPU" if backend.endswith("wgpu") else "OpenGL",
                         f"{float(row['reference_median']):.2f} → {float(row['candidate_median']):.2f}",
                         f"{float(row['median_paired_delta']):+.3f} [{low:+.3f}, {high:+.3f}]"])
    parts += [table(["Font", "Backend", "Master → selected peak RSS (MiB)", "Paired RSS Δ, 95% CI (MiB)"], rows), "",
              "## Miss downside and complete controlled sequences", "",
              "Each controlled frame introduces 94 new atlas keys. The two-phase total includes both populations; pollution includes both hot-population frames, all 64 pollution frames, and hot return. The variation grid always uses Roboto Flex, so only its stock-font factor is shown here.", ""]
    rows = []
    labels = {"grid_singleton": "94 one-use glyphs", "grid_two_phases": "First + second phase", "grid_unique_sizes": "32 unique sizes", "grid_unique_variations": "32 unique weights", "grid_pollution": "Hot + 64-size pollution + return"}
    for font in ("stock", "vollkorn", "ptsans"):
        for scene, label in labels.items():
            if scene == "grid_unique_variations" and font != "stock":
                continue
            base = dict(backend="cpu", font=font, dpi=2, scene=scene, metric="draw_us")
            old = one(sequences, **base, reference_version="master", candidate_version="current")
            route = one(sequences, **base, reference_version="master", candidate_version="route")
            arena = one(sequences, **base, reference_version="master", candidate_version="final")
            marginal = one(sequences, **base, reference_version="route", candidate_version="final")
            rows.append([FONTS[font], label, effect(old), effect(route), effect(arena), effect(marginal)])
    parts += [table(["Font", "Complete sequence", "Original/master", "Route/master", "Arena/master", "Arena/route"], rows), "",
              "## Marginal arena benefit in the examples and application", "",
              "Route combines lazy native Scaler reuse and the legacy-preserving PNG prepass. Arena adds reusable native Outline scratch and compact cached geometry. This direct pairing measures the complete added storage/accounting implementation; it cannot attribute the result solely to allocation changes.", ""]
    rows = []
    for font in ("stock", "vollkorn", "ptsans"):
        for scene in ("demo", "text"):
            row = one(replay, backend="cpu", font=font, dpi=2, scene=scene, phase="first_paint", metric="draw_us", reference_version="route", candidate_version="final")
            rows.append([FONTS[font], scene + " CPU first paint", effect(row)])
    for font in ("roboto", "vollkorn", "ptsans"):
        for backend in ("winit-femtovg-wgpu", "winit-femtovg"):
            row = one(app, mode="cpu", font=font, backend=backend, metric="first_frame.render.thread_cpu_ms", reference="route", candidate="final")
            rows.append([FONTS[font], "Alustin " + ("WGPU" if backend.endswith("wgpu") else "OpenGL") + " first CPU", effect(row, True)])
    parts += [table(["Font", "Scene", "Arena/route"], rows), "", "## Reported example sequences", "",
              "These totals include every reported phase, including movement, reflow, zoom, size, weight, and slant changes. They exclude 119 unreported warmup frames per scene and are not full launch-to-end durations.", ""]
    rows = []
    for backend, metric in [("cpu", "draw_us"), ("gpu", "complete_us")]:
        for font in ("stock", "vollkorn", "ptsans"):
            for scene in ("demo", "text", "font_variations"):
                if scene == "font_variations" and font != "stock":
                    continue
                row = one(sequences, backend=backend, font=font, dpi=2, scene=scene, metric=metric, reference_version="master", candidate_version=selected)
                rows.append([FONTS[font], scene, row["reported_frames"], "CPU" if backend == "cpu" else "GPU completion", effect(row)])
    parts += [table(["Regular-font factor", "Scene", "Reported frames", "Measurement", "Selected/master"], rows), "",
              "## Exploratory regression audit", "",
              "The following selected/master example CPU-drawing, example GPU-completion, and Alustin CPU effects have a positive 95% interval. The complete tables also retain every interval spanning zero. These are exploratory per-metric intervals without multiplicity adjustment, so isolated effects should not be treated as universal regressions.", ""]
    rows = []
    for row in replay:
        endpoint = (row["backend"], row["metric"])
        if endpoint not in {("cpu", "draw_us"), ("gpu", "complete_us")} or row["reference_version"] != "master" or row["candidate_version"] != selected or row["scene"].startswith("grid_"):
            continue
        if row["scene"] == "font_variations" and row["font"] != "stock":
            continue
        if json.loads(row["paired_bootstrap95"])[0] > 0:
            rows.append([FONTS[row["font"]], row["scene"] + "/" + row["phase"] + (" CPU" if row["backend"] == "cpu" else " GPU completion"), effect(row)])
    for row in app:
        if row["reference"] != "master" or row["candidate"] != selected or row["metric"] not in {"first_frame.render.thread_cpu_ms", "search_frame.render.thread_cpu_ms"}:
            continue
        if json.loads(row["median_paired_change_pct_ci95"])[0] > 0:
            rows.append([FONTS[row["font"]], "Alustin " + row["backend"] + "/" + row["metric"], effect(row, True)])
    parts += [table(["Font", "Observation", "Selected/master"], rows) if rows else "No selected/master effect in these primary CPU spans has a wholly positive interval.", "",
              "## Correctness, source scope, and limits", "", selection["validation_summary"], "",
              "The optimization paths are Swash-only and internal to FemtoVG. They use existing native Swash scaling/source APIs; shared atlas helper factoring also compiles outside Swash with unchanged behavior. No Swash source, version requirement, or hint interpreter changes are included. The cache remains eager; the nominal budget remains 1 MiB. There is no validated static bytecode cutoff.", "",
              "The original budget is logical accounting. Arena counts its own capacities plus public logical native-scratch high-water lengths. Neither is a total-heap limit; map spare storage, allocator overhead, native ScaleContext storage, private Swash scratch capacity, and transient allocations are excluded. See [methodology](docs/methodology.md).", "",
              "The initial prepass changed mixed PNG/COLR painter order and was replaced by the guarded version. Gray8 removes an existing path-stroke contamination of adjacent native-mask padding, causing a master pixel difference; it is excluded from this cache change. Its [causal diagnosis](docs/gray8-diagnosis.md) and incomplete cohort remain archived. The original private-allocation-estimation arena was superseded by public-only accounting.", "",
              "The original Image/RGBA pool reduced allocation requests but regressed some cold controls. Instance indexing and Entry lookup had mixed small effects and did not justify additional production changes. [Prototype evidence](docs/miss-prototypes.md) preserves those benefits and costs. Earlier admission experiments remain archived, including complete sequence penalties and excluded startup attempts.", "",
              "Final results come from complete fresh-process balanced blocks, 5 CPU or 3 GPU trials per replay process, and diagnostic Alustin render spans. Raw observations, all six comparisons, failures, scripts, snapshots, locks, and source/executable hashes remain in [the archive index](results/index.json). [Reproduction instructions](README.md) distinguish a standalone replay from the application checkout and its external fixture requirements.", "",
              "The final cohorts recorded arm64 macOS 26.6.2. Every timed GPU replay reported an Apple M4 Max integrated GPU using Metal through WGPU; Alustin exercised WGPU30 and OpenGL at 2560 × 1600 pixels with scale factor 2. Both build records identify rustc 1.96.0 (ac68faa20, 2026-05-25) and Cargo 1.96.0 (30a34c682, 2026-05-25). CPU core configuration and memory capacity were not recorded, so this report does not infer them from the current host.", "",
              "The implementation selection is exploratory and uses these same cohorts. Its intervals describe process variability; they do not adjust for choosing among prototypes, fonts, or endpoints. The study supports the measured workloads on this machine rather than a universal application speedup.", "",
              "## Source pins and report inputs", "",
              "Upstream master: `f57a2c39e9836c146556c58c98d80c5bf7899029`. Original eager cache: `7a278ca4f947658d01c355c450edc6abcdbe3958`. Alustin main: `ac35d4e0b5c52edb7defb9feccdadfd584635c14`. Locally modified candidates are identified by complete source maps and executable hashes, rather than represented as additional source commits.", ""]
    inputs = {"selection.json": hashlib.sha256((ROOT / "selection.json").read_bytes()).hexdigest(),
              "scripts/render-report.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    for name in ("selection-examples", "selection-sequences", "selection-alustin"):
        path = ROOT / "analysis" / name / "summary.csv"
        inputs[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        provenance = path.parent / "summary.json"
        if provenance.exists():
            inputs[str(provenance.relative_to(ROOT))] = hashlib.sha256(provenance.read_bytes()).hexdigest()
    parts += [table(["Preserved statistics", "SHA-256"], [[f"[{name}]({name})", f"`{checksum}`"] for name, checksum in inputs.items()]), ""]
    (ROOT / "REPORT.md").write_text("\n".join(parts))
    (ROOT / "analysis/report-inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    print(f"Rendered REPORT.md for selected variant {selected}")


if __name__ == "__main__":
    main()
