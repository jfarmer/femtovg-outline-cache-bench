#!/usr/bin/env python3
"""Freeze sources and copy original example scene adapters; never build or time."""
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/jesse/github/femtovg')
BENCH = Path('/Users/jesse/github/femtovg-outline-cache-bench')
SCENES = BENCH / 'vendor/runtime/core/runner/src'
UPSTREAM = '6a5f15ae55db439a4ed8b1e818c6521029c34fbd'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])


def file_map(tree):
    return {str(p.relative_to(tree)): digest(p) for p in sorted(tree.rglob('*')) if p.is_file()}


def freeze(name, working=False):
    target = ROOT / 'source' / name
    if target.exists():
        raise SystemExit(f'Refusing to overwrite frozen source: {target}')
    target.mkdir(parents=True)
    revision = git('rev-parse', 'HEAD').decode().strip() if working else UPSTREAM
    with tarfile.open(fileobj=io.BytesIO(git('archive', revision))) as archive:
        archive.extractall(target, filter='data')
    if working:
        tracked = git('ls-files', '-z').decode().split('\0')
        for relative in filter(None, tracked):
            source, dest = REPO / relative, target / relative
            if source.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
            elif dest.exists():
                dest.unlink()
        for source in sorted((REPO / 'src').rglob('*')):
            if source.is_file():
                dest = target / source.relative_to(REPO)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
    (ROOT / f'source-{name}.json').write_text(json.dumps({
        'variant': name, 'revision': revision, 'working_tree': working,
        'diff_sha256': hashlib.sha256(git('diff', '--binary')).hexdigest() if working else None,
        'files': file_map(target), 'production_modifications': None,
    }, indent=2) + '\n')
    manifest = ROOT / 'harness' / name / 'Cargo.toml'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(f'''[package]
name = "femtovg-review-scenes-{name}"
version = "0.1.0"
edition = "2021"

[workspace]

[[bin]]
name = "scenes-{name}"
path = "../../harness-src/main.rs"

[dependencies]
femtovg = {{ path = "{target}", default-features = false }}
swash = "=0.2.10"
image = {{ version = "0.25.0", default-features = false, features = ["jpeg", "png"] }}

[features]
default_swash = ["femtovg/default", "femtovg/swash"]
default_no_swash = ["femtovg/default"]

[profile.release]
opt-level = 3
debug = false
lto = false
codegen-units = 16
incremental = false
panic = "unwind"
''')


def main():
    (ROOT / 'harness-src').mkdir(exist_ok=True)
    copies = {}
    for name in ['demo.rs', 'text.rs', 'perf_graph.rs']:
        source, dest = SCENES / name, ROOT / 'harness-src' / name
        shutil.copy2(source, dest)
        assert digest(source) == digest(dest)
        copies[name] = {'source': str(source), 'sha256': digest(dest), 'modifications': None}
    assets = ROOT / 'assets'
    shutil.copytree(REPO / 'examples/assets', assets, dirs_exist_ok=True)
    shutil.copy2(BENCH / 'assets/Vollkorn-Medium.ttf', assets / 'Vollkorn-Medium.ttf')
    shutil.copy2(BENCH / 'assets/licenses/Vollkorn-OFL.txt', assets / 'LICENSE-Vollkorn')
    (ROOT / 'provenance.json').write_text(json.dumps({
        'scene_sources': copies, 'assets': file_map(assets),
        'fonts': {
            'stock': 'RobotoFlex-VariableFont.ttf',
            'serif': 'Vollkorn-Medium.ttf',
        },
        'optional_emoji_font': '/System/Library/Fonts/Apple Color Emoji.ttc',
        'measurement': 'Canvas set_size + original scene draw; total adds Void flush; setup excluded.',
        'source_instrumentation': None,
    }, indent=2) + '\n')
    freeze('master')
    freeze('final', working=True)
    print(f'Prepared source-only harness: {ROOT}')


if __name__ == '__main__':
    main()
