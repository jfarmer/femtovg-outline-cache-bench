// Public cold/miss controls using the unchanged F06 layout helpers and the
// unchanged archived study controlled scene. No production observer changes.
use std::time::Instant;
use femtovg::{renderer::Void, Canvas, Color, FontId, Paint, PositionedGlyph, TextContext};
use swash::FontRef;

mod controlled;

#[allow(dead_code)]
mod f06 {
    include!("main.rs");

    pub fn plan(font: &FontRef<'_>, use_coords: bool, workload: &str, onephase: bool) -> (Vec<Vec<PositionedGlyph>>, Vec<i16>, f32) {
        let c = coords(font, use_coords);
        let (mut runs, size): (Vec<Vec<PositionedGlyph>>, f32) = match workload {
            "labels" => (LABELS.iter().enumerate().map(|(i, text)| run(font, &c, 14.0, text, 8.0 + (i % 4) as f32 * 220.0, 20.0 + (i / 4) as f32 * 22.0)).collect(), 14.0),
            "para" => ((0..12).map(|i| run(font, &c, 16.0, PARA, 10.3 + i as f32 * 0.37, 24.0 + i as f32 * 20.0)).collect(), 16.0),
            _ => panic!("workload"),
        };
        if onephase {
            for row in &mut runs {
                for glyph in row {
                    glyph.x = glyph.x.round();
                }
            }
        }
        (runs, c, size)
    }
}

// These callbacks satisfy the archived controlled module unchanged. Arguments
// always specify the intended regular font; variation uses bundled Roboto Flex.
pub fn asset(file: &str) -> Vec<u8> {
    let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../source/base/examples/assets").join(file);
    std::fs::read(path).unwrap()
}

pub fn regular_text_font() -> Vec<u8> {
    std::fs::read(std::env::args().nth(2).unwrap()).unwrap()
}

fn new_canvas(data: &[u8]) -> (Canvas<Void>, FontId) {
    let tc = TextContext::default();
    let id = tc.add_shared_font_with_index(data.to_vec(), 0).unwrap();
    let mut canvas = Canvas::new_with_text_context(Void, tc).unwrap();
    canvas.set_size(1280, 800, 1.0);
    (canvas, id)
}

fn med(values: &mut [f64]) -> f64 {
    values.sort_by(f64::total_cmp);
    values[values.len() / 2]
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let workload = &args[1];
    let data = std::fs::read(&args[2]).unwrap();
    let use_coords = args[3] == "1";
    let samples: usize = args.get(4).map(|x| x.parse().unwrap()).unwrap_or(7);
    let mut observations = Vec::new();
    let (glyphs, frames);
    if workload.starts_with("cold_") {
        let font = FontRef::from_index(&data, 0).unwrap();
        let parts: Vec<_> = workload.split('_').collect();
        let (runs, coords, size) = f06::plan(&font, use_coords, parts[1], parts[2] == "onephase");
        glyphs = runs.iter().map(Vec::len).sum::<usize>();
        frames = 1;
        let paint = Paint::color(Color::black()).with_font_size(size);
        for _ in 0..samples {
            let (mut canvas, id) = new_canvas(&data);
            let start = Instant::now();
            for row in &runs {
                canvas.fill_glyph_run(id, &coords, row.iter().cloned(), &paint).unwrap();
            }
            canvas.flush_to_output(());
            observations.push(start.elapsed().as_nanos() as f64);
            std::hint::black_box(&mut canvas);
        }
    } else {
        frames = match workload.as_str() {
            "grid_singleton" => 1, "grid_two_phases" => 2,
            "grid_unique_sizes" | "grid_unique_variations" => 32,
            "grid_pollution" => 67, _ => panic!("workload"),
        };
        glyphs = frames * 94;
        for _ in 0..samples {
            let (mut canvas, id) = new_canvas(&data);
            canvas.set_size(1000, 600, 1.0);
            let scene = controlled::Scene::new(workload, &mut canvas, 1.0, id);
            let phases = scene.phases();
            let start = Instant::now();
            for (_, requests) in phases {
                for request in requests {
                    scene.draw(&mut canvas, &request);
                    canvas.flush_to_output(());
                }
            }
            observations.push(start.elapsed().as_nanos() as f64);
            std::hint::black_box(&mut canvas);
        }
    }
    let total = med(&mut observations);
    println!("RESULT {workload} glyphs {glyphs}");
    println!("RESULT {workload} frames {frames}");
    println!("RESULT {workload} ns_total {total:.0}");
    println!("RESULT {workload} med_ns_per_glyph {:.2}", total / glyphs as f64);
    println!("RESULT {workload} med_ns_per_frame {:.2}", total / frames as f64);
}
