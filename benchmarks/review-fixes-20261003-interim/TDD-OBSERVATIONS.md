The initial scratch regressions were observed through tool outputs. The generic
negative-position reuse test failed because the atlas held two entries where
one was expected. The native x = -0.4 comparison failed its independent coverage
oracle (Swash offset 0.6 and origin -1). Those observations preceded production
fixes; subsequent targeted tests were reported green after the source-aware
placement/key changes. The final tests also cover ties, integer translations,
cold/warm reuse, phase-10 carry, color bitmaps and COLR outlines.

No raw logfile of the initial red/green console output was retained. This is an
honest narrative of the observed tool-output evidence, not a reconstructed raw
transcript. The original scratch regression insertion text is preserved when
available; final test source is in the frozen snapshots. Exact final library
check counts likewise require the original tool output unless an independently
retained log records them. Actual containment logs and any supplied check logs
remain raw files with checksums; this narrative does not replace them.
