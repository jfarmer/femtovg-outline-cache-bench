The optional public font proof-sheet stress study is preserved separately
under raw/stress. Its original README describes the visible workload, selected
fonts, phases and limits. It is a designed stress case, not a demonstrated global
maximum of hinting cost. Its raw processes and statistics are not pooled with
the demo cohorts. Original run/build scripts, harness Rust, Cargo manifests/locks,
build logs, dependency graphs, source identities, raw stdout/stderr, plans and
analysis remain byte-for-byte copies. Binary/cache bytes are omitted.

External fonts actually named in the completed stress PLAN are additionally
bundled with licenses under assets/stress/<font-name>. The generated
STRESS-FONT-ASSETS.json records original paths, hashes and retained archive paths;
thin acquisition provenance is retained where available. This does not rewrite
the original PLAN or its external-path metadata. raw/scenes supplies the same
frozen master/final library source trees against which the stress harness built.

Offline relocation and build preparation, outside this immutable archive:

1. Create a fresh work directory and copy raw/scenes to work/scenes, raw/stress
   to work/stress, raw/scene-builds to work/perf/scene-builds, and assets/stress to
   work/stress/font-assets. Refuse existing work directories. Keep a diff of each
   changed copied script/manifest.
2. In the copied stress build.py, change only SCENES to work/scenes and PERF to
   work/perf. In its two copied harness Cargo.toml files, rebind only the femtovg
   dependency paths to work/scenes/source/master and work/scenes/source/final.
   The frozen library Rust source and stress harness Rust remain unchanged.
3. After all timing jobs have stopped, run the copied builder with
   `python3 work/stress/build.py --build-ready`. Its build is locked and offline,
   copies the original matching locks, uses the original release profile, and
   records actual library origins, source maps, metadata/feature graphs,
   compiler identities and fresh binary hashes under work/stress/builds.
   The copied original scene metadata is its dependency-graph reference; it is
   historical evidence, not a claim that the new executable hash must match.
4. Inspect those new build/source/dependency identities before any later run.
   To relocate a separately authorized replay, rebind the copied run.py FONTS
   and FONT_DOCS paths using STRESS-FONT-ASSETS.json: fonts and every recorded
   license/acquisition document have explicit retained archive paths. Choose a
   fresh output and pass the desired original cohort's explicit --dpi value;
   paired12-native (DPI2) and paired12-dpi1 (DPI1) remain distinct campaigns.
   Preserve that script diff and new PLAN. The original runner's macOS process
   guards and original campaign ordering/phase definitions remain in effect.

No stress relocation, rebuild, smoke or replay was performed by the installer.
The public API proof sheet times layout, panel paths, text atlas work and Void
flush; font registration is outside timing. It does not isolate native hinting,
establish eviction, measure GPU/display latency, or compare arena-only storage.
