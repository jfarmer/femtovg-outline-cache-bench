# Reproduce the repeat cohort

This repeat was requested because of a concern about another desktop workload.
The available chronology did not establish overlap with the original cohort.
Both cohorts remain retained; the repeat report compares them explicitly rather
than replacing the earlier measurements or selecting individual favorable runs.

The repeat uses the exact original collector, compiled master/final executables,
font files, selection manifest, 28 phases, native pixel proof and balanced
12-block schedule at DPR 1 and 2. It collects five CPU or three GPU trials per
process in a fresh directory. Its identity/proof paths refer to the unchanged
original study. The new archive therefore declares two verified companions:
`font-stress-search` and `updated-cache-examples`.

The original selection manifest and its six small selection-input files are
copied byte-identically into the repeat archive. This permits reuse of the
unchanged independent raw/statistical checker. The original absolute proof
bindings in the collection records remain unchanged. The verifier authenticates
all retained bytes first, then resolves historical references through its
verified longest-prefix path map. Compiled executables are omitted from archives;
offline verification checks their preserved metadata bindings, not absent bytes.

```sh
python3 -B scripts/verify-results.py \
  --campaign font-stress-rerun \
  --output /private/tmp/font-stress-rerun-offline-check
```

For a fresh source build and new measurements, follow
[the original reproduction instructions](font-stress-reproduction.md). The
frozen fonts/sources and measurement schedule are the same. Freshly built
executables require the disclosed reproduction identity adaptation; historical
independent executable proofs are not relabeled as new build proofs. Use fresh
output paths and retain the new pixel preflight and every timing attempt.

Keep all benchmark/build/download activity serial during timing. Record the
observed background processes and the actual scope of any preparation/smoke
validation. A process snapshot is evidence of observed activity at that instant,
not proof that the entire interval had no competing work.
