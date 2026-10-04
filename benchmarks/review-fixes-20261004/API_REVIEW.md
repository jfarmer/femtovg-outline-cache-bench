# Public API review

Read-only source comparison: `a6eb66900b10cf28e95fe042d07039302af1c043`
against upstream `9d574e076d3ce6006d9a21a01e3ae8a3bc649a57`.
Also reviewed the subsequent batching fix and regression test, committed as
`907bb375645613b3647efab4c0efe29b50ed5b18` on 2026-10-04. Public declarations
remain identical to upstream. The recorded library runs passed 198 tests with
default + Swash, 182 Swash-only tests, and 170 default tests; the selected debug
inspector run passed 12 tests (`../tdd/nextest-batched-*.txt`).
No builds or API extraction tools were run for this review.

No externally callable signature, visibility, export, public field, enum variant,
or dependency change was found. The unrestricted `pub fn` declarations in the
three modified production integration files are identical after whitespace
normalization: `lib.rs` 66, `text.rs` 17, and `text/font.rs` 34. Reachability was
also inspected; declaration equality alone was not used as the API conclusion.

- **Internal `GlyphAtlas::new`** loses its text-context argument. Its constructor
  was and remains `pub(crate)`. `lib.rs` declares `mod text`, imports
  `GlyphAtlas` privately, and does not reexport that type.
- **Public `femtovg::Atlas::new(width, height)`** is a different type: the packing
  atlas reexported from `text::atlas`. Its source file has no branch changes.
- **Public `Canvas::new` and `Canvas::new_with_text_context`** retain their
  signatures. Their changed calls to the internal atlas constructor do not
  change the public constructors.
- **Public `Canvas::with_render_target`** and internal `Canvas::offscreen_pass`
  retain their existing upstream definitions; `layers.rs` has no branch diff.
- `Font`, `TextContextImpl`, and the new rasterizer handle remain unreachable
  through the public exports. `TextContext` does not expose its inner field or
  return those private types. Internal adapter/accessor changes are not public
  API changes. New recording-renderer fields in `lib.rs` are under `cfg(test)`.

## Observable behavior

An unchanged source API does not imply unchanged behavior. This branch changes
Swash outline reuse, memory/performance policy, and native fractional placement.
It also fixes externally observable failures: first rotated/oversized PNG glyph
rendering no longer triggers an internal context-borrow panic; cold generic atlas
rendering preserves caller layers/state/target; generic PNG upload failure returns
the existing `Result::Err` instead of panicking; truly empty generic paths avoid
blank atlas cells. Nonempty tiny glyphs whose native mask is empty retain generic
fallback. These should be described as intentional behavior fixes, without a
universal performance or compatibility claim.

## Generic target batching: fixed before final performance measurement

The a6eb669 version restored the target per cold generic glyph: N nonempty
glyphs fitting one atlas could emit 2N switches instead of the prior two,
excluding initialization/debug switches. The recorded red regression test
(`../tdd/atlas-batching-red.txt`) demonstrates eight switches for four glyphs
where two were expected. This was a command-count regression, with no measured
GPU slowdown claim. OpenGL executes framebuffer binding, viewport and
view-uniform work for each switch; wgpu recreates its render pass.

The subsequent source fix restores the run-level
`with_render_target(initial, ...)` and explicitly selects each destination atlas
before its `offscreen_pass`. The nested target guard therefore selects and
restores the same atlas, adding no switch. The offscreen pass still isolates
state and bypasses caller layer suppression; the outer guard restores the caller
on ordinary return and `Result::Err`. It does not add panic-unwind guarantees.

The new test primes texture initialization, then requests four cold glyphs and
asserts two switches, one texture, caller target/transform/state-depth/layer-count
preservation, across screen, image and layer targets. It covers generic stroke
with Swash and generic fill/stroke without Swash. Existing allocation-error
coverage checks restoration after switching to an atlas before a later failure.
No glyph keys, geometry, cache ownership or public signatures changed in this
batching correction. Its source was reviewed; validation logs record test runs
separately.

Void benchmarks still do not measure GPU/backend performance. The final source
does, however, preserve the prior generic target batching rather than relying on
Void timings to dismiss the added-switch concern.
