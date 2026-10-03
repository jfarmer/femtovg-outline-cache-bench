# Proposed single PR

Title: Reuse hinted outlines in the Swash glyph atlas

## Draft description

Swash atlas misses repeatedly hint the same glyph outline for different
subpixel positions. Retain hinted geometry per font face, glyph, exact size,
and variation coordinates, then rasterize each position with the same outline
path as Swash's `Render`. Reuse a working outline and a lazy scaler within each
run segment, and avoid constructing generic paths for native atlas fills.

Color sources retain Swash's precedence and bypass the plain-outline cache.
The shared PNG metadata lookup preserves COLR-before-PNG batch order. Native
outline phases use a nonnegative fraction and integer carry so translated
positions share masks; color bitmaps and generic glyphs retain their integer
placement. The generic atlas loop keeps its upstream quad construction inline;
the native helper deliberately duplicates that code to protect generic renderer
code generation and is explicitly inlined for native runs.

The cache uses a 1 MiB soft accounting budget per shared text context, covering
its arena capacities, entry metadata, and logical outline scratch. Private Swash
storage, spare map capacity, allocator overhead, and transient memory are
excluded. Arena storage reduces repeated allocations; exact growth avoids
clearing a working set that still fits this budget.

The integration also fixes the existing rotated/oversized PNG initialization
borrow panic and restores the caller's target after glyph-atlas errors. The
panic fix applies with `swash` plus `textlayout`; target restoration applies to
all font-rendering configurations. Public APIs, error kinds, dependencies, and
feature definitions are unchanged.

Validation:

- Final library suites: 184 default-plus-Swash tests and 168 Swash-only tests
  passed, as reported by the main agent. Add the exact default-only total and
  any other completed checks before publishing.
- Independent Swash `Render` oracles cover keys, coverage, placement, color
  selection, and variation coordinates. New integration regressions cover
  translated outline masks, COLR/PNG source order, bitmap placement, generic
  atlas reuse, fallback borrowing, and target restoration.
- Final-source containment probes passed in all six upstream/current runs.
  Non-Swash traces match in 28/30 cases; the other two differ only by the
  intended error-target restoration. Generic stroke/direct traces match in
  all 10 default-plus-Swash and all 9 Swash-only cases. The new private source
  flag was removed from Debug comparison only after checking every relevant
  value was false. Atlas state, vertices, and commands otherwise remain exact.
- [Insert the final paired release timing table here: hardware, compiler,
  sample count, medians, and both cold and warm public-path results. Include
  generic/non-Swash controls and any losing rows. Distinguish CPU measurements
  from GPU correctness checks; do not reuse the original 20-offset microbench
  figures as measurements of this final tree.]

## Suggested final commit message

The following is a draft for the final squashed tree. Replace or remove the
timing placeholder before committing, and retain only checks actually completed
on that tree. No history change has been performed by this agent.

```text
Reuse hinted outlines in the Swash glyph atlas

Swash atlas misses repeatedly hinted the same glyph for different
subpixel positions. Cache hinted geometry by face, glyph, exact size,
and variation coordinates, and rasterize it as Swash's outline renderer
does. Reuse a working outline and lazy scaler per run segment while
retaining native color-source precedence and COLR-before-PNG batch order.

Store geometry in shared arenas and try exact growth before evicting a
working set that fits. The 1 MiB soft budget counts arena capacities,
entry metadata, and logical scratch; private Swash storage, spare map
capacity, allocator overhead, and transient memory remain excluded.

Canonicalize native outline phases so integer translations reuse masks,
preserving bitmap and generic placement. Fix PNG atlas initialization
borrowing and restore the caller's render target after atlas errors.
Keep upstream quad construction in the generic loop; the separate native
helper is explicitly inlined to avoid per-glyph call overhead. Public
APIs, error kinds, dependencies, and feature definitions are unchanged.

Validation: 184 default-plus-Swash and 168 Swash-only library tests passed.
Six isolated upstream/current containment probes passed; generic command,
vertex, and atlas traces match, with only the intended target-restoration
differences after non-Swash atlas errors.

[Insert the final paired benchmark result, hardware, and method; remove
this placeholder before committing. Add other checks only once complete.]

Built with assistance from Claude Code and OpenAI Codex.
```

## Scope and history review notes

- Use one PR. One final commit is a reasonable presentation of this coherent
  atlas integration; the user did not request multiple PRs. Keep a backup of
  the original history for provenance before squashing it.
- No repository CONTRIBUTING file, AGENTS.md, commit-message template,
  pull-request template, or configured commit.template was found. The supplied
  user policy therefore applies: imperative subject, meaningful body, and
  actual validation. Existing history alone is not an official convention.
- The final commit should describe the final code and fresh measurements.
  Historical validation was real: `050d77b` passed 175/159 on the old base;
  rebasing retained that body while adding four base tests. Do not recast the
  stale post-rebase wording as fabricated original validation.
- The plain generic phase key remains u8, and its quad arithmetic matches
  upstream. New cache/scaler/source metadata is Swash-gated. The read-only
  containment comparison tests both default and Swash generic paths.
- `font_mut`, `GlyphAtlas`, `RenderedGlyph`, and `TextContextImpl` remain inside
  the private `text` module. No externally reachable function signatures,
  exported error variants, dependency declarations, or CI feature settings
  change. New RecordingRenderer knobs are test-only.
- Test gates now reflect behavior: native tests require Swash; shared generic
  tests run with either font backend. PNG initialization needs textlayout but
  no longer unnecessarily requires image-loading. Glyph-cache inspection is
  test-plus-Swash gated. The synthetic bitmap fixture adds no dependency.
- README honestly describes the soft budget and exclusions. CHANGELOG scopes
  the three fixes correctly, including native color outlines as filled outline
  glyphs and the preservation of bitmap/generic placement. Its performance
  sentence describes the aggregate improvement, not an unmeasured arena-only
  speedup. The existing font credit already identifies Bungee as test-only.
- Include the new `src/text/glyph_atlas_fallback_tests.rs` when staging: it is
  currently untracked and omitted from ordinary diff stats. The unrelated
  untracked `.serena/` directory is outside this change.
- Final timing still determines the performance claim. Source and trace
  equivalence establish containment; they do not by themselves establish
  performance equivalence across compilers or hardware.
