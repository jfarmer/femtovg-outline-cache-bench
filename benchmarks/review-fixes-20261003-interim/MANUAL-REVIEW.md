The review branch is one commit, `b87a94ddfba46ee67ca35ba240104615ac1503d8`,
on upstream `6a5f15ae55db439a4ed8b1e818c6521029c34fbd`. It is pushed to
`jfarmer/femtovg:glyph-outline-cache`. No PR exists; the user requires a final
manual review before one is created.

[Compare against upstream master](https://github.com/femtovg/femtovg/compare/master...jfarmer:glyph-outline-cache).
The full previous history is saved in local branch
`backup/glyph-outline-cache-before-squash-20261003` at `7b42f52`.

Plain hinted outlines are cached by face, glyph, exact floating-point size and
normalized variation coordinates. Cache identity and scaler construction use
the same private immutable run settings. Swash supplies hinting and color-source
rendering; Zeno rasterizes retained geometry using Swash's outline render steps.
Shared point/verb arenas and reusable native scratch amortize miss allocations.
Exact arena growth is attempted before eviction. The 1 MiB per-context budget
is soft accounting, excluding private Swash buffers, spare map buckets,
allocator overhead and transient working memory.

The cache is Swash-only. No exported API, dependency, feature definition, error
variant, renderer backend, layer, filter, clip, shadow or budget module changes.
New RecordingRenderer controls exist only in tests. The generic atlas retains
master's unsigned phase keys and quad arithmetic. Native outline masks use ten
canonical phases and an integer carry; bitmap and generic placement remain
truncated. The only observed non-Swash behavioral change restores the original
render target after atlas errors. PNG initialization borrowing is fixed as well.

TDD exposed a duplicate generic negative-position atlas entry and incorrect
native negative-position coverage before the fixes. Independent Swash Render
oracles now cover outline, COLR and bitmap positioning on cold and warm draws,
integer translations, ties, variations and budget boundaries. Initial red/green
console output was observed through tools and was not archived as a raw log;
do not mistake the narrative for an independently retained transcript.

Completed validation:

- Default cargo test: 163 library, 54 integration and 10 documentation tests.
- Library suites: 184 with defaults plus Swash; 168 with Swash only.
- Offscreen Apple M4 Max Metal: three text tests in each configuration, plus
  two stroke tests without Swash.
- All-feature clippy passed with 12 warnings in unchanged upstream code.
  Formatting and whitespace checks passed.
- Six isolated containment probes passed. Successful default traces match
  master (28/30 checked cases); two error cases differ only in target restoration.
  Generic stroke/direct traces match in all 10 default-plus-Swash and all nine
  Swash-only cases. Atlas state, vertices and commands were compared; only the
  new private source flag was normalized after checking it was false.

Performance is an interim result. The completed 12-block paired warm/generic
cohorts compare the measured runtime to exact current upstream master; the
independent auditor reproduced all 288 warm and 768 generic process records.
Warm native paragraphs save 4.46–8.09 microseconds per frame. Swash-only Arial
labels show an inconclusive 0.36 microsecond cost. Four non-Swash warm paragraph
controls add 1.31–2.42 microseconds per frame, with exploratory intervals above
zero. Generic Swash label strokes add 0.38–0.83 microseconds. These are measured
small costs, so an unqualified performance-win claim is unsupported.

Cold native/cache-miss evidence is a separate post hoc provisional analysis of
the earliest interrupted campaign's eight complete paired blocks. The selection
rule was saved before calculating cold effects. All 66 configurations and three
variants form a complete 1,584-process matrix; partial block 8's 174 records are
excluded. All 66 final/master point ratios favor final, with 63 exploratory
intervals below one and three crossing one. The largest permitted cost is the
default-plus-Swash Vollkorn 32-size sequence: paired ratio 0.99470, interval
[0.99236, 1.01068], complete-sequence delta −252.021 microseconds, interval
[−365.917, +507.625]. This is not the planned 12-block primary cold cohort.
The earlier guard could miss brief activity during a process. All four original
campaigns' raw files and exclusion notes remain unchanged; no campaigns were
merged. See `provisional-cold-audit/PLAN.json`, `REPORT.md` and `CONCLUSION.md`.
No cold rerun is needed unless a meaningful new concern arises.

Actual demo/text scene results remain pending. The user confirmed another
project is still building. Further timing waits for explicit confirmation that
it has finished. Scene sources and binaries are prepared, including Roboto Flex
and Vollkorn in both examples and non-Swash controls.
Historical Alustin/GPU/font studies remain preserved elsewhere in the benchmark
repository; their older source results are not measurements of this final branch.

The source freeze predates the squash and two corrected test-comment lines.
`final-runtime-identity.json` records full hashes, the exact comment-only diff,
and byte identity before the test module. No test logic or released code changed.

Before considering submission, finish the demo/text scene cohort, audit
all accepted/rejected records, verify portable reproduction, and update the
performance summary. The user then reviews the final diff and evidence. No PR
creation is authorized until that manual review is approved.
