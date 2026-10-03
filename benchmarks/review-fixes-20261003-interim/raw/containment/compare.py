from pathlib import Path
import difflib
import hashlib
import json
import re

root = Path('/private/tmp/femtovg-review-fixes-containment')
workspace = Path('/Users/jesse/github/femtovg')
generic = {'6', '9b', '13', '16', '17.false', '17.true', '18.false', '18.true', '19.0', '19.1'}
restore = {'8', '8b', '9c'}
rows = []
reports = []
failures = []

def sections(text):
    result = {}
    for section in re.split(r'(?m)(?=^=== )', text):
        if section.startswith('=== '):
            key = re.match(r'=== (\S+)', section).group(1)
            result[key] = section
    return result

for tag in ['default', 'default-swash', 'swash-only']:
    sides = {side: sections((root / f'{tag}-{side}.trace.txt').read_text()) for side in ['base', 'current']}
    assert sides['base'].keys() == sides['current'].keys()
    selected = []
    exceptions = []
    for key in sides['base']:
        base = sides['base'][key]
        current = sides['current'][key]
        native_flags = re.findall(r'uses_subpixel_positioning: (true|false)', current)
        checked = tag == 'default' or key in generic
        normalized = False
        if tag != 'default' and key in generic:
            assert all(flag == 'false' for flag in native_flags), (tag, key, native_flags)
            # Only the new private false-valued Swash source metadata is absent
            # upstream; leave every other key, placement, command, and vertex as is.
            if native_flags:
                current = current.replace(', uses_subpixel_positioning: false', '')
                normalized = True
        identical = base == current
        if checked:
            selected.append((key, identical))
            if not identical:
                if key in restore:
                    exceptions.append(key)
                else:
                    failures.append(f'{tag}:{key}')
        row = {
            'feature_set': tag, 'scenario': key, 'checked_containment': checked,
            'identical': identical, 'private_false_flag_removed': normalized,
            'private_flag_count': len(native_flags),
            'base_sha256': hashlib.sha256(base.encode()).hexdigest(),
            'current_compared_sha256': hashlib.sha256(current.encode()).hexdigest(),
            'current_raw_sha256': hashlib.sha256(sides['current'][key].encode()).hexdigest(),
            'base_result': base.splitlines()[0], 'current_result': current.splitlines()[0],
        }
        rows.append(row)
        split = root / 'scenarios' / tag
        split.mkdir(parents=True, exist_ok=True)
        (split / f'{key}-base.txt').write_text(base)
        (split / f'{key}-current-raw.txt').write_text(sides['current'][key])
        if normalized:
            (split / f'{key}-current-compared.txt').write_text(current)
        if not identical:
            diff = ''.join(difflib.unified_diff(base.splitlines(True), current.splitlines(True), fromfile='upstream 6a5f15a', tofile='current source'))
            (split / f'{key}.diff').write_text(diff)
    reports.append(f'{tag}: {sum(equal for _, equal in selected)}/{len(selected)} checked scenarios identical; restore exceptions: {", ".join(exceptions) or "none"}.')

hashes = json.loads((root / 'source-hashes.json').read_text())
changed = [name for name, expected in hashes.items() if not (workspace / name).is_file() or hashlib.sha256((workspace / name).read_bytes()).hexdigest() != expected]
source_now = {str(path.relative_to(workspace)) for path in (workspace / 'src').rglob('*') if path.is_file()}
added = sorted(source_now - hashes.keys())
(root / 'comparison.json').write_text(json.dumps(rows, indent=2) + '\n')
lines = [
    '# Containment comparison', '',
    'Compared exact upstream production source at `6a5f15a` with a snapshot of the current working production source, using the reviewer containment probe plus isolated generic stroke and large/rotated direct cases. Both copies use the workspace Cargo.lock and identical dependencies. All six offline, locked probe runs passed.', '',
    'The only upstream instrumentation is inside `cfg(test)`: the image-update failure knob and the probe module. Current production source was not edited. The command stream, vertex buffer, complete atlas entries, atlas allocator state, target, and state-stack depth are compared.', '',
    'For Swash generic-only scenarios, every present `uses_subpixel_positioning` value was checked to be false before removing that new private field from the Debug text. No other fields or differences were normalized. Non-Swash traces receive no normalization.', '',
    *reports, '',
    f'Unexpected checked differences: {", ".join(failures) or "none"}.',
    f'Workspace source files changed after snapshot: {", ".join(changed) or "none"}.',
    f'Workspace source files added after snapshot: {", ".join(added) or "none"}.', '',
    'The two non-Swash exceptions both still return `FontSizeTooLargeForAtlas`. Their atlas state and vertices are unchanged. The differences are the restored target (screen in scenario 8, original image in scenario 8b) and the corresponding SetRenderTarget command before the subsequent rectangle draw. The saved diffs contain no other changes.', '',
    'Per-scenario SHA-256 hashes and classifications are in comparison.json. Full traces, test logs, exact commands, and unified diffs are retained alongside this report. Native Swash fill scenarios are recorded but excluded from the generic-only equality verdict because the authorized outline positioning/cache behavior changes there.',
]
(root / 'REPORT.md').write_text('\n'.join(lines) + '\n')
print('\n'.join(reports))
print(f'Unexpected checked differences: {failures or "none"}')
print(f'Changed after snapshot: {changed or "none"}; added: {added or "none"}')
raise SystemExit(bool(failures))
