from pathlib import Path
import os
import subprocess
import time

root = Path('/private/tmp/femtovg-review-fixes-containment')
features = [
    ('default', []),
    ('default-swash', ['--features', 'swash']),
    ('swash-only', ['--no-default-features', '--features', 'swash']),
]
results = []
for tag, args in features:
    for side in ['base', 'current']:
        output = root / f'{tag}-{side}.trace.txt'
        env = os.environ.copy()
        env['CARGO_TARGET_DIR'] = str(root / 'target')
        env['PROBE_OUT'] = str(output)
        command = ['cargo', 'test', '--offline', '--locked', '--lib', *args, 'containment_review_probe::containment_probe', '--', '--exact']
        start = time.monotonic()
        completed = subprocess.run(command, cwd=root / side, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log = root / f'{tag}-{side}.log'
        log.write_text(completed.stdout)
        result = {'features': tag, 'side': side, 'exit_code': completed.returncode, 'seconds': round(time.monotonic() - start, 2), 'command': command}
        results.append(result)
        print(f'{tag} {side}: exit={completed.returncode}, {result["seconds"]}s', flush=True)
        for line in completed.stdout.splitlines():
            if line.startswith('test result:') or line.startswith('error'):
                print(line, flush=True)
        if completed.returncode:
            print('\n'.join(completed.stdout.splitlines()[-35:]), flush=True)
            break
    else:
        continue
    break
import json
(root / 'run-results.json').write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(any(result['exit_code'] for result in results))
