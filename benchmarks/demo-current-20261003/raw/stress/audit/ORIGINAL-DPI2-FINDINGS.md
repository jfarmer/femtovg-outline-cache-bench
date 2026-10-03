This preliminary checkpoint is superseded by the completed independent audit in REPORT.md and AUDIT.json. The findings below record the original pre-rerun checkpoint.

Original DPI 2 cohort structural audit: 72 processes, 288 phase records, 3,168 measured frames; complete 12 paired blocks and 6 AB/6 BA per font. Every reported frame has 1,980 public glyph requests, 198 glyph/size instances, 30 public draws, and 66 characters/row. No record exclusions. Statistical replication and source identity audit are pending.

At identity CTM native sizes are 14/20/28 pixels plus changing-size delta. DPR 2 rows are shifted by 0.05 native units, 0..0.45. Do not describe this run as ten distinct native phase bins or 28/40/56 native PPEM. Requested bins and native cache events were not instrumented.

The first compiler-guard abort has no timing raw file and remains separate. No measured data or original files were changed.
