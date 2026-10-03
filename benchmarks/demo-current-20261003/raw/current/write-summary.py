#!/usr/bin/env python3
"""Render the independently audited current demo results without pooling cohorts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SUPPLEMENT = Path('/private/tmp/femtovg-current-demo-extremes-20261003')
STRESS = Path('/private/tmp/femtovg-hinting-stress-scene-20261003')
NAMES = {'RobotoFlex': 'Roboto Flex', 'PTSans': 'PT Sans', 'Vollkorn': 'Vollkorn',
         'Rye': 'Rye', 'FleurDeLeah': 'Fleur de Leah', 'DiplomataSC': 'Diplomata SC'}


def main():
    studies = [(ROOT, 'demo-current-native'), (SUPPLEMENT, 'demo-extremes-native')]
    rows = []
    for study, cohort in studies:
        assert (study / cohort / 'COMPLETE.json').exists()
        rows.extend(json.loads((study / cohort / 'summary.json').read_text()))
    lines = [
        '# Current Swash hinted-outline cache: demo and stress results', '',
        'Comparison: proposed released code at `b87a94ddfba46ee67ca35ba240104615ac1503d8` '
        'against upstream master `6a5f15ae55db439a4ed8b1e818c6521029c34fbd`. '
        'The frozen candidate differs from that commit only in two test comments. '
        'Source, compiler, feature/dependency graph and executable identities are retained in provenance.', '',
        'The current demo saves milliseconds when expensive hinting must be repeated for different atlas positions. '
        'Roboto Flex is close to unchanged; PT Sans improves modestly. '
        'The more expensive open-source typefaces save roughly 2–2.8 ms on first paint. '
        'Warm bitmap-atlas frames have little such work left to avoid.', '',
        '## Actual demo scene', '',
        'This adapter preserves FemtoVG’s demo drawing and performance graph, using the public Canvas API '
        'with a Void renderer at DPI 2. The drawing includes text layout, paths, images, strokes and the graph. '
        'Font/image loading and Canvas construction are outside timing. CPU frame drawing plus Void flush '
        'is measured; GPU, presentation, window creation and application startup are not.', '',
        '| Typeface, default + Swash | First paint master → proposed (ms/frame) '
        '| Paired first-paint saving (ms, exploratory 95% interval) '
        '| All 65 reported frames master → proposed (ms/sequence) |',
        '|---|---:|---:|---:|',
    ]
    for font, name in NAMES.items():
        first = next(r for r in rows if r['font'] == font and r['feature'] == 'default_swash' and r['phase'] == 'first_paint')
        sequence = next(r for r in rows if r['font'] == font and r['feature'] == 'default_swash' and r['phase'] == 'reported_sequence')
        lo, hi = [-x / 1000 for x in reversed(first['paired_delta_ci95_us'])]
        lines.append(f'| {name} | {first["master_median_us"] / 1000:.3f} → {first["final_median_us"] / 1000:.3f} '
                     f'| {-first["median_paired_delta_us"] / 1000:.3f} [{lo:.3f}, {hi:.3f}] '
                     f'| {sequence["master_median_us"] / 1000:.3f} → {sequence["final_median_us"] / 1000:.3f} |')
    lines.extend([
        '', 'Each font/configuration has twelve independent paired process blocks with six AB and six BA orders. '
        'The primary four fonts and later two-font supplement are separate chronological cohorts, not pooled trials. '
        'Marginal medians and medians of paired differences need not subtract to the same number. '
        'Each reported sequence includes first paint, 30 warm, 12 zoom-in, 12 zoom-out and 10 pan frames; '
        'the 119 intervening warmup frames are excluded.', '',
        'All 288 demo processes were retained, with no process retries or timing-value exclusions. '
        'Compiler/build/linker checks bracket every process after a 60-second quiet interval. '
        'Initial pre-timing activity and the unsuccessful zero-timing sandbox guard attempt are preserved. '
        'Independent audits reconstructed 1,440 phase observations, all 72 summaries and their intervals. '
        'All 36 non-Swash demo phase/sequence intervals cross zero. This is no resolved demo difference, '
        'rather than proof of equivalence or an override of the earlier generic microbenchmarks.', '',
        'Apple M4 Max, macOS, release opt-level 3, no LTO, 16 codegen units, rustc 1.96/LLVM 22.1.2. '
        'Intervals use 10,000 paired-block percentile bootstrap resamples with a fixed seed, without '
        'multiplicity adjustment; they describe this host/workload.', '',
        '## Why typeface matters', '',
        'The reusable result is the hinted geometry for one face, glyph, exact size and variation. '
        'Different subpixel positions need different atlas bitmaps, but can reuse that geometry. '
        'The gain depends on glyphs used, sizes, repeated phase requests and executed hinting cost. '
        'A font’s total bytecode bytes alone do not predict the saving. Earlier native hinting probes '
        'found Fleur de Leah more expensive per selected glyph than Rye, yet this demo saves less '
        'with Fleur. Large CJK font programs also did not automatically produce the slowest individual glyphs.', '',
    ])
    cohort = STRESS / 'paired12-dpi1'
    if (cohort / 'COMPLETE.json').exists():
        stress = json.loads((cohort / 'summary.json').read_text())
        lines.extend(['## Phase-repeated font proof sheet', '',
            'A finite page repeats 66 Latin letters, digits and symbols in ten rows at each of three '
            'logical sizes (14, 20, 28 at DPI 1). Row origins differ by 0.1 native atlas units, requesting '
            'up to ten atlas positions for the same hinted geometry. All text lies within the page; '
            'public layout, panel drawing, glyph drawing and Void flush are timed. Font registration '
            'is excluded. This is a deliberately favorable reuse stress case, not a typical application '
            'or a proved global maximum.', '',
            '| Typeface | First paint master → proposed (ms/frame) '
            '| Twelve new sizes master → proposed (ms/frame, average) '
            '| All 44 frames master → proposed (ms/sequence) |', '|---|---:|---:|---:|'])
        for font in ['FleurDeLeah', 'RobotoFlex', 'Rye']:
            chosen = [next(r for r in stress if r['font'] == font and r['phase'] == phase)
                      for phase in ['first_paint', 'new_size', 'complete_sequence']]
            cells = [f'{r["master_median"] / 1000:.3f} → {r["final_median"] / 1000:.3f}' for r in chosen]
            lines.append(f'| {NAMES[font]} | ' + ' | '.join(cells) + ' |')
        lines.extend(['', 'Twelve paired blocks per font with six AB/six BA orders. All 44 frames are included: '
            'first paint, 30 warm, twelve distinct size changes, and one return to the original sizes. '
            'The size-change pass still repeats each new glyph-size instance across phase rows; it is '
            'not an all-miss workload. Actual shaped glyph counts and page dimensions are retained '
            'from public TextMetrics. Totals neither establish eviction nor isolate cache hits or arena allocation. '
            'The separate raw record and report retain warm/return timing, paired effects and intervals. '
            'The earlier DPI 2 proof-sheet cohort is preserved as a control: its 0.1/DPI row spacing '
            'covers roughly five native phase bins, since DPI affects shaping but does not by itself '
            'double the atlas rasterizer size or position. It is not pooled with the full-phase DPI 1 cohort.', ''])
    lines.extend([
        '## Protecting the miss path', '',
        'The final implementation shares points/commands in two append-only vectors and reuses a native '
        'working Outline plus rasterizer scratch. Misses lazily share a Swash scaler within a run; '
        'native PNG routing also avoids constructing an unrelated generic outline. Whole-patch results '
        'therefore include more than geometry-cache hits.', '',
        'The existing development comparison is illustrative rather than another current-master result. '
        'For 32 unique-size glyph populations, the earlier cache with run reuse but without the final '
        'arena/working-buffer reuse cost 0.373 ms more than its master baseline for Roboto Flex and '
        '0.301 ms more for PT Sans. Adding the arena and reused working buffers changed those to '
        '0.266 ms and 0.297 ms savings. These paired comparisons use their own older source pins '
        'and jointly test compact storage and buffer reuse; they are not a pure allocator ablation. '
        'See the existing repository REPORT.md, “CPU controls: one-use glyphs, reuse and churn” '
        'and “Marginal arena benefit in the examples and application”.', '',
        'The arenas have a 1 MiB soft accounting budget and whole-cache clearing. Exact growth is tried '
        'before eviction when geometric capacity would exceed the budget. Accounted arena capacity, '
        'logical entry metadata and logical working-outline high water do not cover all heap memory. '
        'Map spare capacity, Zeno/Swash internals, allocator overhead and transient storage remain outside '
        'that budget. This is a private retention policy, not a hard process-memory bound.', '',
        '## Scope and remaining costs', '',
        'The cache is private and Swash-only in the shared text context, with no public API, dependency '
        'or backend changes. Swash supplies hinting and color rendering. Retained plain geometry uses '
        'its existing Zeno dependency because Swash Render accepts a scaler and glyph ID, not a retained '
        'scaled Outline. Generic unhinted paths and phase-specific bitmap storage remain separate.', '',
        'The atlas integration fixes three existing bugs: PNG initialization borrow panic, native negative '
        'outline phase placement, and restoration of the caller’s target on a glyph error. The shared '
        'target-restoration fix applies outside Swash. Successful generic traces match master in the '
        'checked corpus; default, default+Swash, Swash-only and selected real Metal checks pass.', '',
        'Earlier current-runtime isolated controls remain disclosed: non-Swash warm paragraphs add '
        '1.3–2.4 µs/frame; generic Swash label strokes add 0.4–0.8 µs/frame; one Swash-only negative-position '
        'cold paragraph stroke adds 16.3 µs with an interval above zero. Cold synthetic eight-block '
        'results are a provisional post hoc analysis of the first interrupted campaign. Those studies '
        'are preserved separately in review-fixes-20261003-interim, not pooled into these fresh demo '
        'or proof-sheet cohorts. The evidence supports meaningful font-dependent savings with small '
        'remaining costs, not an unqualified universal speedup.', '',
        'No PR or comment has been posted. PR_BODY.md and FOLLOW_UP.md, when present, are local '
        'drafts awaiting the user’s final manual review. The dedicated benchmark repository currently '
        'has no published remote; no public artifact URL is invented.', '',
    ])
    (ROOT / 'SUMMARY.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
