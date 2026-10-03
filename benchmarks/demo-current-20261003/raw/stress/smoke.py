#!/usr/bin/env python3
"""Check public API workload/counts; observations are not campaign data."""
import csv
import io
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
FONTS = {
    'FleurDeLeah': '/private/tmp/femtovg-current-demo-extremes-20261003/assets/FleurDeLeah-Regular.ttf',
    'RobotoFlex': '/private/tmp/femtovg-current-demo-20261003/assets/RobotoFlex-VariableFont.ttf',
    'Rye': '/private/tmp/femtovg-current-demo-20261003/assets/Rye-Regular.ttf',
}
records = []
for font, path in FONTS.items():
    counts = []
    for variant in ['master', 'final']:
        command = [str(ROOT / 'bin' / f'hinting-stress-{variant}'), path, 'proofsheet', '2', '1']
        process = subprocess.run(command, capture_output=True, text=True)
        record = {'font': font, 'variant': variant, 'command': command, 'returncode': process.returncode,
                  'stdout': process.stdout, 'stderr': process.stderr, 'purpose': 'API/count smoke only; excluded from timed cohort'}
        records.append(record)
        (ROOT / 'smoke.json').write_text(json.dumps(records, indent=2) + '\n')
        assert process.returncode == 0, process.stderr
        rows = list(csv.DictReader(io.StringIO(process.stdout)))
        assert [(r['phase'], int(r['frames'])) for r in rows] == [('first_paint', 1), ('warm', 30), ('new_size', 12), ('return', 1)]
        counts.append([(r['phase'], r['glyph_requests_per_frame'], r['distinct_glyph_size_instances_per_frame'],
                        r['logical_width'], r['logical_height']) for r in rows])
    assert counts[0] == counts[1]
    print(f'{font}: master/final public glyph counts and page dimensions agree: {counts[0]}', flush=True)
