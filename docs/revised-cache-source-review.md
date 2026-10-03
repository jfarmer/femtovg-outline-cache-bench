# Source and build identity review

Before fixes 1–3, the exact live checkout was HEAD
`4c45270585f0fadca63d3eae61433adb8102bea2`, with two dirty tracked files:
`src/text.rs` and `src/text/swash_rasterizer.rs`. Both master refs pointed to
the pinned `f57a2c39e9836c146556c58c98d80c5bf7899029`. The independent inventory
is `independent-source-identities.json`, containing all 139 tracked file
hashes, the complete pinned-master map, and the binary diff hash. User
`.serena/`, untracked build files, and observers are excluded.

The source frozen for the updated 4/5 comparison has text hash
`4bb6b3664c35de5bd3c2ca0017f9a8d02306a3bf51039137e03f98ed5d6f2e3d`
and rasterizer hash
`fa2fc5852710952ee3122500e08bda3a1dd38d69a39cd0420604f51c9488ee92`.
Root confirmed this freeze before this agent started the later 1–3 fixes.

## Fresh build precautions

The historical `core/build_replay.py` explicitly reuses archived
master/current executables. The historical app builder also retains those
baselines. Do not run either unchanged for the new cohort. Fresh runtime
builders and their preflight already forbid historical executable reuse;
retain that policy for every measured version.

Use a distinct immutable pure-source directory for each version and separate
timed copies. Derive updated 4/5 from the exact tracked-file inventory, and
derive master from its pinned Git object. Verify all source bytes again
after building. The only replay instrumentation should remain the identical
Void `black_box` barriers and atlas-entry accessor, separately recorded as
timed-source changes. No observer or review-test module belongs in timed
production code.

Prefer a separate Cargo target directory for each variant to rule out stale
local-crate fingerprints. A shared target was the source of an earlier
invalid observation cohort, which was explicitly retained and corrected.
Different final filenames alone do not prove that the intended source was
compiled. If sharing dependency build artifacts is necessary, verify the
actual Cargo compiler-artifact message identifies the correct manifest,
package, executable and freshly compiled local dependencies. Distinct
benchmark runner/package identities can add protection, but changing the
FemtoVG package name would alter pure-source metadata and must be recorded;
it is unnecessary with independent targets.

For every binary retain the exact source map, metadata/package origins,
compiler/Cargo versions, locked dependency/features graph, command, target
directory, compiler-artifact executable path, SHA-256 and file size. Copy
that reported executable immediately to its immutable variant path. Verify
launch records against those hashes. Maintain equal dependencies, features,
optimization/debug flags and harness source for all variants; path identities
may be normalized for graph comparison but must remain visible in raw metadata.

## Later rendering correctness fixes

`fix123.patch` is the separate live-tree change from frozen updated 4/5.
No rasterizer 4/5 logic was changed by this agent.

1. `draw_glyph_run` only needs immutable access to the text context and font;
   font geometry caches and native scaler contexts already use their own
   interior mutability. Replacing its outer mutable borrow permits the
   existing lazy ephemeral-atlas constructor to obtain its immutable context
   handle safely. No constructor API change is needed.
2. Signed `i8` subpixel bins distinguish existing negative and integer phases
   while preserving the one-byte key size and current quantization/placement.
3. Each of the existing generic and Swash atlas loops is independently wrapped
   in `Canvas::with_render_target`, so an error returned from the closure still
   restores the entry target. Native scaler scope and fallback release remain
   unchanged. This helper handles returned errors, not unwinding panics.

Regression tests reuse the existing PNG font assembler and recording renderer.
They exercise first rotated/large PNG draws; negative/integer positions in
both orders against native Swash coverage and quad-placement oracles plus warm
reuse and the generic stroke keys; and actual allocation/upload errors after
atlas switches, with screen, explicit image and layer-store target restoration
and a following clear. Mask capture is opt-in and failures are test-only.

This agent formatted the edited Rust files and passed `git diff --check`.
Compilation and test execution are owned serially by the parent agent; no
build, benchmark or GUI was run by this agent during implementation.

Parent validation records subsequently completed: `final-default-tests.log`
reports 175/175 passing library tests with default features plus Swash;
`final-swash-only-tests.log` reports 159/159 passing library tests with defaults
disabled and Swash enabled. Both include the applicable new regression cases.
