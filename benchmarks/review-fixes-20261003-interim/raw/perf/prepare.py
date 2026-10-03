#!/usr/bin/env python3
"""Freeze exact source trees and prepare the preserved public Void harness."""
import argparse
import hashlib
import io
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = Path('/Users/jesse/github/femtovg')
REVIEW = Path('/Users/jesse/github/femtovg-glyph-outline-cache-review')
BASE = 'da268321ec2b53cdd188e8c07f853897121c3767'
MASTER = '6a5f15ae55db439a4ed8b1e818c6521029c34fbd'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args])


def source_map(tree):
    return {str(p.relative_to(tree)): sha(p) for p in sorted(tree.rglob('*')) if p.is_file()}


def freeze(name, working=False, ordinary_inline=False):
    tree = ROOT / 'source' / name
    if tree.exists():
        raise SystemExit(f'Refusing to overwrite frozen source {tree}')
    tree.mkdir(parents=True)
    revision = MASTER if name == 'master' else BASE
    with tarfile.open(fileobj=io.BytesIO(git('archive', revision))) as archive:
        archive.extractall(tree, filter='data')
    if working:
        tracked = git('ls-files', '-z').decode().split('\0')
        for rel in filter(None, tracked):
            original, copied = REPO / rel, tree / rel
            if original.is_file():
                copied.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, copied)
            elif copied.exists():
                copied.unlink()
        # Include newly created source tests/modules; exclude unrelated user files.
        for original in sorted((REPO / 'src').rglob('*')):
            if original.is_file():
                copied = tree / original.relative_to(REPO)
                copied.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(original, copied)
    changes = None
    if ordinary_inline:
        path = tree / 'src/text.rs'
        before = path.read_text()
        marker = '#[inline(always)]\n    fn add_glyph_quad('
        if before.count(marker) != 1:
            raise SystemExit('Expected one inline(always) attribute on add_glyph_quad')
        path.write_text(before.replace(marker, '#[inline]\n    fn add_glyph_quad(', 1))
        changes = 'Only add_glyph_quad attribute changed from inline(always) to inline.'
    (ROOT / f'source-{name}.json').write_text(json.dumps({
        'variant': name, 'base_commit': revision,
        'working_head': git('rev-parse', 'HEAD').decode().strip() if working else None,
        'working_diff_sha256': hashlib.sha256(git('diff', BASE, '--binary')).hexdigest() if working else None,
        'prototype_change': changes, 'files': source_map(tree),
    }, indent=2) + '\n')
    manifest = ROOT / 'harness' / name / 'Cargo.toml'
    manifest.parent.mkdir(parents=True)
    manifest.write_text(f'''[package]
name = "femtovg-review-fixes-{name}"
version = "0.1.0"
edition = "2021"

[workspace]

[[bin]]
name = "probe-{name}"
path = "../../harness-src/main.rs"

[[bin]]
name = "cold-{name}"
path = "../../harness-src/cold.rs"

[[bin]]
name = "generic-{name}"
path = "../../harness-src/generic.rs"

[dependencies]
femtovg = {{ path = "{tree}", default-features = false }}
swash = "=0.2.10"

[features]
swash_only = ["femtovg/swash"]
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
    print(f'Frozen {name}: {tree}', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['base', 'master', 'final', 'finalgenericrestore'])
    args = parser.parse_args()
    (ROOT / 'harness-src').mkdir(exist_ok=True)
    source = REVIEW / 'review/evidence/v-F06-reproduce/f06probe.rs'
    target = ROOT / 'harness-src/main.rs'
    if target.exists() and target.read_bytes() != source.read_bytes():
        raise SystemExit('Harness differs from preserved review source')
    shutil.copy2(source, target)
    (ROOT / 'harness-source.json').write_text(json.dumps({
        'source': str(source), 'sha256': sha(target), 'modifications': None,
    }, indent=2) + '\n')
    archived_controls = Path('/Users/jesse/github/femtovg-outline-cache-bench/vendor/runtime/core/runner/src/controlled.rs')
    original = archived_controls.read_text()
    adapted = original.replace('pub fn new<T: Renderer>(name: &str, canvas: &mut Canvas<T>, dpi: f32) -> Self {',
                               'pub fn new<T: Renderer>(name: &str, _canvas: &mut Canvas<T>, dpi: f32, font: FontId) -> Self {')
    adapted = adapted.replace('        let font = canvas.add_font_mem(&data).expect("register controlled font");\n', '')
    if adapted == original or 'canvas.add_font_mem' in adapted:
        raise SystemExit('Expected archived font-registration adapter markers')
    (ROOT / 'harness-src/controlled.rs').write_text(adapted)
    (ROOT / 'controlled-source.json').write_text(json.dumps({
        'source': str(archived_controls), 'original_sha256': sha(archived_controls),
        'sha256': sha(ROOT / 'harness-src/controlled.rs'),
        'modifications': 'Scene::new takes an already registered FontId, because Canvas::add_font_mem is unavailable without textlayout. Cold runner registers through public TextContext outside timing. Request construction, phases and draw method unchanged.',
    }, indent=2) + '\n')
    if args.stage in ['base', 'master']:
        freeze(args.stage)
    elif args.stage == 'final':
        freeze('final', working=True)
        freeze('ordinary-inline', working=True, ordinary_inline=True)
    else:
        freeze(args.stage, working=True)


if __name__ == '__main__':
    main()
