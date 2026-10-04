"""Create a scratch publication bundle and reviewable git patch; no repo writes."""
import gzip
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

STUDY = Path('/private/tmp/femtovg-miss-fastpath-20261004')
BENCH = STUDY / 'bench'
REPO = Path('/Users/jesse/github/femtovg-outline-cache-bench')
PAYLOAD = Path('/private/tmp/femtovg-miss-fastpath-publication')
PATCH_ROOT = Path('/private/tmp/femtovg-miss-fastpath-publication-patch')
PATCH = Path('/private/tmp/femtovg-miss-fastpath-publication.patch')
DESTINATION = 'benchmarks/miss-fastpath-20261004'
EXCLUDE = {'.git', '.serena', 'bin', 'target', '__pycache__'}
sha = lambda data: hashlib.sha256(data).hexdigest()

for required in ('SUMMARY.md', 'INDEPENDENT_REVIEW.md', 'SOURCE_FREEZE.json',
                 'runs/comparison/SUMMARY.json', 'runs/comparison/AUDIT.json',
                 'validation/RESULTS.json'):
    if not (BENCH / required).is_file():
        raise RuntimeError(f'Required final artifact missing: {required}')
status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO)
if status:
    raise RuntimeError('Public benchmark repository changed; inspect before preparing publication patch')
if (REPO / DESTINATION).exists() or PAYLOAD.exists() or PATCH_ROOT.exists():
    raise RuntimeError('Publication destination already exists; do not overwrite immutable artifacts')
base_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO, text=True).strip()
base_readme = (REPO / 'README.md').read_bytes()

sys.path.insert(0, str(BENCH))
from common import files, source_snapshot
build = json.loads((BENCH / 'BUILD.json').read_text())
freeze = json.loads((BENCH / 'SOURCE_FREEZE.json').read_text())
assert freeze['after_commit'] is None
assert build['harness'] == files(BENCH / 'harness-src')
assert build['harness_packages'] == files(BENCH / 'harness')
assert build['assets'] == files(BENCH / 'assets')
for variant in ('master', 'before', 'after'):
    assert source_snapshot(variant) == build['variants'][variant]['source'] == freeze['sources'][variant]
audit = json.loads((BENCH / 'runs/comparison/AUDIT.json').read_text())
assert (audit['complete_blocks'], audit['accepted_processes'], audit['measurement_rows']) == (6, 126, 486)
assert not audit['excluded_attempts'] and audit['matched_guard_checks'] == 0
validation = json.loads((BENCH / 'validation/RESULTS.json').read_text())
assert all(record['exit_code'] == 0 for record in validation['results'])

PAYLOAD.mkdir()
# Keep the familiar top-level summaries alongside their exact archived copies.
for source, destination in [
    ('SUMMARY.md', 'SUMMARY.md'), ('INDEPENDENT_REVIEW.md', 'INDEPENDENT_REVIEW.md'),
    ('runs/comparison/REPORT.md', 'REPORT.md'), ('runs/comparison/SUMMARY.json', 'SUMMARY.json'),
    ('runs/comparison/SUMMARY.csv', 'SUMMARY.csv'), ('runs/comparison/AUDIT.json', 'AUDIT.json'),
    ('SOURCE_FREEZE.json', 'SOURCE_FREEZE.json'), ('after-vs-before.diff', 'after-vs-before.diff'),
    ('after-vs-master.diff', 'after-vs-master.diff'), ('runs/comparison/raw.jsonl', 'runs/comparison/raw.jsonl'),
]:
    target = PAYLOAD / destination
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BENCH / source, target)
shutil.copytree(BENCH / 'validation', PAYLOAD / 'validation')
for source in sorted(BENCH.iterdir()):
    if source.is_file() and source.name != 'INDEPENDENT_REVIEW.md' and any(
            token in source.name.lower() for token in ('independent', 'numeric')):
        shutil.copy2(source, PAYLOAD / source.name)

retained = []
omitted = []
for source in sorted(STUDY.rglob('*')):
    if not source.is_file():
        continue
    relative = source.relative_to(STUDY)
    if any(part in EXCLUDE for part in relative.parts):
        if 'bin' in relative.parts:
            data = source.read_bytes()
            omitted.append({'path': relative.as_posix(), 'bytes': len(data), 'sha256': sha(data),
                            'reason': 'compiled executable; identity retained, bytes omitted'})
        continue
    if source.is_symlink():
        raise RuntimeError(f'Unexpected source symlink: {relative}')
    retained.append((relative.as_posix(), source.read_bytes(), source.stat().st_mode & 0o777))

members = {}
canonical = {}
archive_path = PAYLOAD / 'snapshot.tar.gz'
with archive_path.open('wb') as raw:
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as tar:
            for name, data, mode in retained:
                digest = sha(data)
                info = tarfile.TarInfo(name)
                info.mode = mode
                info.mtime = info.uid = info.gid = 0
                key = (len(data), digest)
                record = {'bytes': len(data), 'sha256': digest}
                if key in canonical:
                    info.type = tarfile.LNKTYPE
                    info.linkname = canonical[key]
                    tar.addfile(info)
                    record['linkname'] = info.linkname
                else:
                    canonical[key] = name
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
                members[name] = record
index = {'archive': archive_path.name, 'bytes': archive_path.stat().st_size,
         'sha256': sha(archive_path.read_bytes()), 'members': members}
(PAYLOAD / 'snapshot-index.json').write_text(json.dumps(index, indent=2) + '\n')
(PAYLOAD / 'OMITTED.json').write_text(json.dumps({'files': omitted,
    'excluded_directory_names': sorted(EXCLUDE),
    'compiler_caches': 'Outside the study and not archived; build metadata retains the original target path.'}, indent=2) + '\n')
shutil.copy2(REPO / 'benchmarks/review-fixes-20261004/verify.py', PAYLOAD / 'verify.py')
(PAYLOAD / 'README.md').write_text('''# Normal-miss fast-path follow-up\n\nSee [results](SUMMARY.md), [full report](REPORT.md), [exact source provenance](SOURCE_FREEZE.json),\n[tests](validation/RESULTS.json), [raw records](runs/comparison/raw.jsonl), and\n[independent review](INDEPENDENT_REVIEW.md).\n\nMaster is upstream `9d574e0`; Before is committed cache branch `907bb37`.\nAfter is the measured working-tree insertion fast path based on `907bb37`;\nit is not labeled as a commit. Both source patches and all frozen source\nhashes are retained. The archive contains source trees, scripts, unchanged\nscenes, assets and font licenses, normalized dependency locks, build logs,\nvalidation logs, six balanced blocks, raw process output, guards and reports.\nCompiled executables and compiler caches are omitted; binary identities\nremain in BUILD.json and OMITTED.json.\n\nVerify and extract with Python 3.12 or later:\n\n```sh\npython3 verify.py\npython3 verify.py --extract /tmp/femtovg-miss-fastpath\n```\n\nWith Rust/Cargo and the locked dependencies cached, rebuild the variants and\nrun a fresh no-window comparison:\n\n```sh\ncd /tmp/femtovg-miss-fastpath/bench\npython3 build.py\npython3 run.py --out runs/new-comparison --blocks 6\npython3 analyze.py --out runs/new-comparison\npython3 audit.py --out runs/new-comparison\n```\n\nThe default cohort uses all seven existing cases: three demo fonts, a\nnon-Swash demo control, two 32-size miss controls, and Fleur de Leah stress.\nThe guard must inspect process names; failed inspection or compiler overlap\nexcludes and retains the entire interrupted block. No timing-based filtering\nis performed. Demo results measure CPU drawing; miss/stress results include\nVoid flush. Font loading, Canvas creation and GPU work are excluded.\n\nThe verifier checks retained bytes and archive extraction. A fresh build\nfrom the relocated archive has not been tested; original absolute provenance\npaths and binary identities are retained as captured. Rebuild before a fresh\nrun. Earlier studies remain intact and their absolute timings are not pooled\nwith this dataset.\n''')
(PAYLOAD / 'PUBLICATION.json').write_text(json.dumps({
    'public_repository_base_commit': base_commit,
    'public_repository_base_readme_sha256': sha(base_readme),
    'destination': DESTINATION, 'study_source_after': 'measured working tree based on 907bb37',
    'snapshot_bytes': index['bytes'], 'snapshot_members': len(members),
    'snapshot_sha256': index['sha256'], 'packaging_script': str(Path(__file__).resolve()),
}, indent=2) + '\n')
shutil.copy2(__file__, PAYLOAD / 'publication.py')

# Diff isolated trees so root can review/apply one patch using git apply.
old_tree = PATCH_ROOT / 'old'
new_tree = PATCH_ROOT / 'new'
old_tree.mkdir(parents=True)
new_tree.mkdir(parents=True)
(old_tree / 'README.md').write_bytes(base_readme)
readme = base_readme.decode()
paragraph = ('The [normal-miss fast-path follow-up](benchmarks/miss-fastpath-20261004/SUMMARY.md) '
             'compares upstream Master `9d574e0`, committed cache branch `907bb37`, and an additional '
             'working-tree optimization. It retains the same seven scenes, six balanced blocks, '
             'exact sources, tests, raw records and independent review.\n\n')
head, rest = readme.split('\n\n', 1)
(new_tree / 'README.md').write_text(head + '\n\n' + paragraph + rest)
shutil.copytree(PAYLOAD, new_tree / DESTINATION)
process = subprocess.run(['git', 'diff', '--no-index', '--binary', '--no-renames',
                          '--src-prefix=a/', '--dst-prefix=b/', 'old', 'new'],
                         cwd=PATCH_ROOT, capture_output=True)
assert process.returncode == 1, process.stderr.decode()
normalized = []
for line in process.stdout.splitlines(keepends=True):
    if line.startswith((b'diff --git ', b'--- ', b'+++ ')):
        for old, new in [(b'a/old/', b'a/'), (b'a/new/', b'a/'), (b'b/old/', b'b/'), (b'b/new/', b'b/')]:
            line = line.replace(old, new)
    normalized.append(line)
patch = b''.join(normalized)
paths = re.findall(rb'^diff --git a/(\S+) b/(\S+)$', patch, re.M)
assert paths and all(left == right and (right == b'README.md' or
                       right.startswith(DESTINATION.encode()+b'/')) for left, right in paths)
PATCH.write_bytes(patch)
subprocess.run(['git', 'apply', '--check', str(PATCH)], cwd=old_tree, check=True)
subprocess.run(['git', 'apply', str(PATCH)], cwd=old_tree, check=True)
expected = {p.relative_to(new_tree).as_posix():sha(p.read_bytes()) for p in new_tree.rglob('*') if p.is_file()}
actual = {p.relative_to(old_tree).as_posix():sha(p.read_bytes()) for p in old_tree.rglob('*') if p.is_file()}
assert actual == expected
subprocess.run([sys.executable, str(PAYLOAD / 'verify.py')], check=True)
extracted = PATCH_ROOT / 'extracted'
subprocess.run([sys.executable, str(PAYLOAD / 'verify.py'), '--extract', str(extracted)], check=True)
assert all((extracted/name).read_bytes()==data for name,data,_ in retained)
assert subprocess.check_output(['git', 'status', '--porcelain'], cwd=REPO) == status
print(json.dumps({'payload':str(PAYLOAD), 'patch':str(PATCH), 'patch_bytes':len(patch),
                  'patch_paths':len(paths), 'members':len(members), 'archive_bytes':index['bytes'],
                  'verified':'all member hashes, extraction bytes, patch apply/check and tree identity'},indent=2))
