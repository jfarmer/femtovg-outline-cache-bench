// Public generic-path fill/stroke checks. Layout is the preserved F06 code;
// centred-negative positions shift that same precomputed run across zero.
use std::time::Instant;
use femtovg::{renderer::Void, Canvas, Color, FontId, Paint, PositionedGlyph, TextContext};
use swash::FontRef;

#[allow(dead_code)]
mod f06 {
    include!("main.rs");
    pub fn plan(font: &FontRef<'_>, use_coords: bool, workload: &str) -> (Vec<Vec<PositionedGlyph>>, Vec<i16>, f32) {
        let c = coords(font, use_coords);
        let (runs, size): (Vec<Vec<PositionedGlyph>>, f32) = match workload {
            "labels" => (LABELS.iter().enumerate().map(|(i, text)| run(font, &c, 14.0, text, 8.0 + (i % 4) as f32 * 220.0, 20.0 + (i / 4) as f32 * 22.0)).collect(), 14.0),
            "para" => ((0..12).map(|i| run(font, &c, 16.0, PARA, 10.3 + i as f32 * 0.37, 24.0 + i as f32 * 20.0)).collect(), 16.0),
            _ => panic!("workload"),
        };
        (runs, c, size)
    }
}

fn new_canvas(data: &[u8]) -> (Canvas<Void>, FontId) {
    let tc = TextContext::default();
    let id = tc.add_shared_font_with_index(data.to_vec(), 0).unwrap();
    let mut canvas = Canvas::new_with_text_context(Void, tc).unwrap();
    canvas.set_size(1280, 800, 1.0);
    (canvas, id)
}

fn frame(canvas: &mut Canvas<Void>, id: FontId, coords: &[i16], runs: &[Vec<PositionedGlyph>], paint: &Paint, stroke: bool) {
    for row in runs {
        if stroke {
            canvas.stroke_glyph_run(id, coords, row.iter().cloned(), paint).unwrap();
        } else {
            canvas.fill_glyph_run(id, coords, row.iter().cloned(), paint).unwrap();
        }
    }
    canvas.flush_to_output(());
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let workload = &args[1];
    let parts: Vec<_> = workload.split('_').collect();
    let data = std::fs::read(&args[2]).unwrap();
    let font = FontRef::from_index(&data, 0).unwrap();
    let (mut runs, coords, size) = f06::plan(&font, args[3] == "1", parts[1]);
    let stroke = parts[2] == "stroke";
    if parts[3] == "negative" {
        for row in &mut runs {
            let center = (row.first().unwrap().x + row.last().unwrap().x) / 2.0;
            for glyph in row {
                glyph.x -= center;
            }
        }
    }
    let glyphs: usize = runs.iter().map(Vec::len).sum();
    let paint = Paint::color(Color::black()).with_font_size(size).with_line_width(1.25);
    let count: usize = args[4].parse().unwrap();
    let mut samples = Vec::with_capacity(count);
    if parts[0] == "warm" {
        let (mut canvas, id) = new_canvas(&data);
        for _ in 0..20 {
            frame(&mut canvas, id, &coords, &runs, &paint, stroke);
        }
        for _ in 0..count {
            let start = Instant::now();
            frame(&mut canvas, id, &coords, &runs, &paint, stroke);
            samples.push(start.elapsed().as_nanos() as f64);
        }
        std::hint::black_box(&mut canvas);
    } else {
        for _ in 0..count {
            let (mut canvas, id) = new_canvas(&data);
            let start = Instant::now();
            frame(&mut canvas, id, &coords, &runs, &paint, stroke);
            samples.push(start.elapsed().as_nanos() as f64);
            std::hint::black_box(&mut canvas);
        }
    }
    samples.sort_by(f64::total_cmp);
    let median = samples[count / 2];
    println!("RESULT {workload} glyphs {glyphs}");
    println!("RESULT {workload} med_ns_per_glyph {:.2}", median / glyphs as f64);
    println!("RESULT {workload} med_ns_per_frame {median:.2}");
}
