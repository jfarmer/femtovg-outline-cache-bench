// F06 verifier probe (v-F06-reproduce). Copied to src/bin/f06probe.rs in a
// base clone (6a5f15a) and a branch clone (da26832); same source for both.
// Differs from the workloads harness: Slint-like UI frame of many SHORT runs
// (one fill_glyph_run per label, so per-call overhead counts), a variable
// font with coordinates passed on every run, per-frame timing (p10/median of
// individually timed frames) instead of median of 400-frame blocks.
//
// usage: f06probe <labels|para> <font> <coords:0|1> [frames]
// prints: RESULT <workload> <metric> <value>

use std::time::Instant;

use femtovg::{renderer::Void, Canvas, Color, FontId, Paint, PositionedGlyph, TextContext};
use swash::{tag_from_str_lossy, FontRef, Setting};

const LABELS: &[&str] = &[
    "File", "Edit", "View", "Window", "Help", "Open...", "Save", "Save As...", "Close", "Quit",
    "Settings", "General", "Appearance", "Dark mode", "Font size", "Language", "English (US)",
    "Notifications", "Enable sounds", "Do not disturb", "Account", "Sign out", "Cancel", "OK",
    "Apply", "Search", "Name", "Date modified", "Size", "Kind", "Documents", "Downloads",
    "Pictures", "Music", "Videos", "Desktop", "Recent", "Favorites", "Trash", "New Folder",
    "Volume 72%", "Brightness", "Wi-Fi: Home Network", "Bluetooth", "Battery 81%", "12:45 PM",
];

const PARA: &str = "The quick brown fox jumps over the lazy dog while five boxing wizards jump quickly; \
pack my box with five dozen liquor jugs. Sphinx of black quartz, judge my vow! 0123456789 (1,234.56)";

fn coords(f: &FontRef, on: bool) -> Vec<i16> {
    if !on || f.variations().len() == 0 {
        return Vec::new();
    }
    f.variations().normalized_coords([Setting { tag: tag_from_str_lossy("wght"), value: 450.0 }]).collect()
}

fn run(f: &FontRef, coords: &[i16], size: f32, text: &str, x0: f32, y: f32) -> Vec<PositionedGlyph> {
    let cmap = f.charmap();
    let gm = f.glyph_metrics(coords).scale(size);
    let mut x = x0;
    let mut v = Vec::new();
    for c in text.chars() {
        let g = cmap.map(c);
        if c != ' ' {
            v.push(PositionedGlyph { x, y, glyph_id: g });
        }
        x += gm.advance_width(g);
    }
    v
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    let wl = a[1].as_str();
    let data = std::fs::read(&a[2]).unwrap();
    let use_coords = a[3] == "1";
    let frames: usize = a.get(4).map(|s| s.parse().unwrap()).unwrap_or(3000);
    let f = FontRef::from_index(&data, 0).unwrap();
    let c = coords(&f, use_coords);

    let (runs, size): (Vec<Vec<PositionedGlyph>>, f32) = match wl {
        "labels" => (
            LABELS
                .iter()
                .enumerate()
                .map(|(i, t)| run(&f, &c, 14.0, t, 8.0 + (i % 4) as f32 * 220.0, 20.0 + (i / 4) as f32 * 22.0))
                .collect(),
            14.0,
        ),
        "para" => ((0..12).map(|i| run(&f, &c, 16.0, PARA, 10.3 + i as f32 * 0.37, 24.0 + i as f32 * 20.0)).collect(), 16.0),
        _ => panic!("workload"),
    };
    let glyphs: usize = runs.iter().map(|r| r.len()).sum();

    let ctx = TextContext::default();
    let font: FontId = ctx.add_shared_font_with_index(data.clone(), 0).unwrap();
    let mut canvas = Canvas::new_with_text_context(Void, ctx).unwrap();
    canvas.set_size(1280, 800, 1.0);
    let mut paint = Paint::color(Color::rgb(20, 20, 20));
    paint.set_font_size(size);

    let mut frame = |canvas: &mut Canvas<Void>| {
        for r in &runs {
            canvas.fill_glyph_run(font, &c, r.iter().cloned(), &paint).unwrap();
        }
        canvas.flush_to_output(());
    };
    for _ in 0..20 {
        frame(&mut canvas);
    }
    let mut t = Vec::with_capacity(frames);
    for _ in 0..frames {
        let s = Instant::now();
        frame(&mut canvas);
        t.push(s.elapsed().as_nanos() as f64);
    }
    t.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let p10 = t[frames / 10];
    let med = t[frames / 2];
    println!("RESULT {wl} glyphs {glyphs}");
    println!("RESULT {wl} runs {}", runs.len());
    println!("RESULT {wl} p10_ns_per_glyph {:.2}", p10 / glyphs as f64);
    println!("RESULT {wl} med_ns_per_glyph {:.2}", med / glyphs as f64);
}
