# Reproducing the Alustin comparison

The replay suite can run without an Alustin checkout. The application comparison requires the pinned Alustin source, its common benchmark patch, and the same application fixtures. The benchmark repository supplies the FemtoVG variants, open fonts, archived input manifests, scripts, and application patch; it does not silently substitute another Alustin revision or regenerate dependencies.

## Application source and common benchmark changes

The recorded Alustin revision is `ac35d4e0b5c52edb7defb9feccdadfd584635c14`. The branch name used for the measurements was `perf/femtovg-outline-master-compare`; the commit and tracked-file contents are the guards that matter for reproduction.

Use a separate checkout or worktree at that revision. Apply `vendor/app-inputs/app-input.diff` to the clean pinned source, and place `vendor/app-inputs/app-original.Cargo.lock` at the checkout's `Cargo.lock`. The build wrapper checks the full tracked-file hash map, HEAD, exact tracked diff, and initial lock before building. An already prepared checkout must match these inputs exactly; the wrapper does not apply the patch or overwrite unrelated changes for you.

The common patch affects these five files:

| File | Common change in every compared variant |
| --- | --- |
| `crates/alustin-gui/Cargo.toml` | Adds `femtovg-benchmark`, selecting the FemtoVG WGPU renderer and existing startup diagnostics. |
| `crates/alustin-gui/src/main.rs` | Sets the window font family from the benchmark configuration and records the configured family/path event. |
| `crates/alustin-gui/src/startup.rs` | Identifies WGPU 30 correctly under the narrow benchmark feature. |
| `crates/alustin-gui/ui/forge.slint` | Exposes the benchmark font-family property, preserving Vollkorn as its default. |
| `crates/alustin-gui/vendor/i-slint-renderer-femtovg/font_cache.rs` | Adds an optional dump of actual font blobs passed to FemtoVG; enabled only for separate font-validation runs. |

The SHA-256 of that exact patch is `f7f9d5555e158d6211a7de6d1ed4307aaeb35ff02b929245ed4f2262964f66a1`. These changes are shared across master, current, and every candidate. Each build overrides only the FemtoVG dependency with the relevant pinned source snapshot.

## Locks and dependency graphs

Two different lock files are intentional:

| Input | Recorded SHA-256 | Purpose |
| --- | --- | --- |
| `app-original.Cargo.lock` | `908b48c83c7e4b4c3cc27828b28dcc9e09db3b98a51665fe284a527a1c913ea3` | Exact checkout lock required before and after the build transaction. |
| `resolved.Cargo.lock` | `5f3ac225f41ca3e189ef63d5a5035bf9bddcc0c0c821a965a5801eab7e26fb24` | Archived dependency resolution used while compiling all FemtoVG overrides. |

The builder temporarily installs the resolved lock, uses `--locked --offline`, validates normalized dependencies and features, and restores the original lock conditionally on success or failure. If another process changes the lock during the transaction, the builder preserves that change and reports an incomplete build. Keep exclusive access to the checkout while building. Dependency packages for the archived locks must already be present in the Cargo cache; do not solve a missing package by regenerating either lock.

Recorded application builds used Swash `0.2.10`, Skrifa `0.40.0`, and FemtoVG features `swash` and `wgpu`, with `textlayout` absent. The standalone replay resolves a separate pinned dependency graph and must not be treated as the same application build. Slint supplies shaped glyph runs to FemtoVG, so Alustin can reach the atlas path without FemtoVG's text-layout prewarming of generic glyph paths. The example replay also exercises `fill_text`, whose layout work can already populate those paths. This affects the work avoided by the guarded prepass change; it does not imply that a larger scene alone explains the difference. Recorded toolchain: Rust/Cargo `1.96.0`; a new build records its actual toolchain and guards it throughout its campaign.

## Application fixtures

The driver records each fixture's canonical path, byte length, and SHA-256. Relocating a fixture is allowed when its bytes remain identical. The original defaults refer to the following files in the Alustin checkout:

| Fixture | Bytes | SHA-256 |
| --- | ---: | --- |
| `fixtures/sample_save_large.save` | 2,559,348 | `8006550510d1555d5f9c42a77f9e6b3b668d7b38cf931c4d09135214787ba1a6` |
| `item_names.json` | 1,195,171 | `19e3230416c760f0633b744d9c0d1ce89bcf623750110c8691d04b4ba5cd3b98` |
| `logs/slint-startup/icon-pack/icons-128-raw.pack` | 95,719,946 | `4f31c714d779059ec5c941a2681d7a5568bda5f5bc62f3bc236394cf2f5f7788` |

The icon pack is generated application input, so a source checkout alone may not contain it. Supply a pack matching the recorded checksum to reproduce the recorded workload. A different pack, save, or catalog creates a new workload and must be reported as such. The wrapper forwards the driver's `--save`, `--catalog`, and `--icon-pack` options for fixture relocation. Fixture availability is separate from the tracked-source/lock guard.

The controlled fallback font is the checkout's `crates/alustin-gui/vendor/i-slint-common/sharedfontique/Inter-VariableFont.ttf` (503,796 bytes, SHA-256 `c333e1de6d6241530a473f480cd1f59a2578cd509825828b89a751c09fb9b61c`). Primary fonts are the bundled exact Vollkorn Medium, Roboto Flex, and PT Sans files and their license notices. Family selection and file identity are both recorded.

## Fresh build and execution

From the benchmark repository, after preparing the pinned application checkout and fixtures:

```sh
python3 scripts/prepare.py --output runs/app-runtime --alustin-checkout /path/to/alustin-benchmark
python3 scripts/build.py app --runtime runs/app-runtime

# Untimed screenshots and actual renderer-font identity checks.
python3 scripts/run.py app pixels --runtime runs/app-runtime --output runs/app-pixels --actual-font-diagnostics

# Separate timing campaigns; these open desktop windows.
python3 scripts/run.py app cpu --runtime runs/app-runtime --output runs/app-cpu
python3 scripts/run.py app startup --runtime runs/app-runtime --output runs/app-startup
```

Pass relocated fixtures to each run when necessary, for example `--save /path/sample_save_large.save --catalog /path/item_names.json --icon-pack /path/icons-128-raw.pack`. Build and run outputs must use fresh directories. The portable builder rebuilds every configured variant and the shared startup harness; it does not rely on archived executables.

The app runs require an interactive desktop. The validated window is 2,560 × 1,600 physical pixels at scale factor 2.0. The driver checks the reported dimensions and renderer API: OpenGL for `winit-femtovg`, WGPU 30 for `winit-femtovg-wgpu`. System font discovery is disabled; the configured primary font and bundled Inter fallback are controlled inputs. The current selection uses four versions and four Williams orders, with 12 rounds by default, giving three complete order cycles. Position and directed carryover are balanced within each cycle.

## Validation and measurement scope

The font-family/path event confirms the requested configuration. Actual-font diagnostics separately dump distinct font blobs reaching Slint's FemtoVG font cache and check their exact bytes against the selected primary font and allowed Inter fallback. They require the primary face at index zero with ASCII coverage, and require the controlled fallback to have been observed. This establishes the actual renderer faces, not a character-by-character font-routing trace. The diagnostics do not measure font hinting cost.

Actual-font dumps are enabled only by `--actual-font-diagnostics` in `pixels` mode. CPU and startup timing campaigns leave `ALUSTIN_FONT_DIAGNOSTICS_DIR` unset. CPU mode enables existing host rendering spans; the dump path and screenshots are excluded from primary timing. Pixel checks compare decoded RGBA across variants within each backend and font configuration. They also check that changing the primary font changes the screenshot.

CPU results describe host wall/thread CPU for first and search rendering. Startup results include the harness/IPC readiness path. They do not measure GPU completion or compositor scanout, and nested spans must not be added together. The standalone offscreen replay reports a different draw/submit/GPU-completion measurement.

The harness submits the controlled search query `a`. Only a different final query causes a whole version block to be excluded and retried, up to three attempts; every raw attempt is retained. Other failures abort an incomplete campaign. No duration-based exclusions or retries are allowed. Use the desktop carefully during a campaign because keyboard input can contaminate the search query.

Archived raw reports and their original absolute paths remain historical evidence. Portable archive validation resolves those paths through the checksum-verified archive mapping. It should validate and recompute the archived statistics without changing the original reports or running the application.

The icon pack is an external fixture and is not included in this repository; its recorded identity is retained in the run provenance.
