import hashlib
import json
import pathlib
import subprocess

repo = pathlib.Path('/Users/jesse/github/femtovg')
study = pathlib.Path('/private/tmp/femtovg-review-fixes-perf')
snapshot = study / 'source/finalgenericrestore'
sha = lambda data: hashlib.sha256(data).hexdigest()
files = ['src/lib.rs', 'src/text.rs', 'src/text/font.rs', 'src/text/swash_rasterizer.rs']
records = {}
for rel in files:
    recorded, committed = (snapshot / rel).read_bytes(), (repo / rel).read_bytes()
    record = {'measured_sha256': sha(recorded), 'committed_sha256': sha(committed), 'whole_file_equal': recorded == committed}
    if rel.endswith('swash_rasterizer.rs'):
        marker = b'#[cfg(test)]\nmod tests {'
        assert recorded.count(marker) == committed.count(marker) == 1
        before_recorded, before_committed = recorded.split(marker)[0], committed.split(marker)[0]
        assert before_recorded == before_committed
        record['before_test_module_sha256'] = sha(before_committed)
        record['before_test_module_equal'] = True
        expected = recorded.replace(
            b"    /// The offsets `GlyphAtlas::render_atlas` passes: the fractional part of a\n    /// glyph's position, quantized to tenths.\n",
            b"    /// Cover the native atlas's ten phases plus signed offsets and the upper\n    /// endpoint accepted by the lower-level rasterizer.\n",
        )
        assert expected == committed, 'Only the two documented test-comment lines may differ'
    else:
        assert recorded == committed, rel
    records[rel] = record
commit = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
delta = subprocess.check_output(['git', '-C', str(repo), 'diff', '7b42f524b0f357ad535e54ac0aad6ab22ab71aae', 'HEAD'], text=True)
result = {
    'final_commit': commit,
    'measured_variant': 'finalgenericrestore',
    'measured_runtime_matches_final_commit': True,
    'post_measurement_change': 'Only two comment lines inside cfg(test) clarify the lower-level test offset superset; no test logic or released code changed.',
    'post_measurement_diff': delta,
    'files': records,
}
(study / 'final-runtime-identity.json').write_text(json.dumps(result, indent=2) + '\n')
print(commit + ': measured runtime matches final commit; only documented test comments differ.')
