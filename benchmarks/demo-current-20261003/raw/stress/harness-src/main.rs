use femtovg::{renderer::Void, Baseline, Canvas, Color, FontId, Paint, Path};
use std::{collections::HashSet, time::Instant};

const SPECIMEN: &str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789&@%$";
const SIZES: [f32; 3] = [14.0, 20.0, 28.0];
const PHASE_ROWS: usize = 10;
const LEFT: f32 = 128.0;

struct Scene {
    font: FontId,
}

struct Measurement {
    draw_us: f64,
    flush_us: f64,
    total_us: f64,
    glyph_requests: usize,
    distinct_instances: usize,
    logical_width: u32,
    logical_height: u32,
}

impl Scene {
    fn draw(&self, canvas: &mut Canvas<Void>, dpi: f32, size_delta: f32) -> Measurement {
        let start = Instant::now();
        let paints: Vec<_> = SIZES.iter().map(|size| {
            Paint::color(Color::rgb(32, 37, 42))
                .with_font(&[self.font])
                .with_font_size(size + size_delta)
                .with_font_weight(450.0)
                .with_text_baseline(Baseline::Alphabetic)
        }).collect();
        // Layout is included in drawing. Measure all bands before fixing the
        // viewport so even a wide typeface remains fully visible on the page.
        let mut max_width: f32 = 0.0;
        for paint in &paints {
            let metrics = canvas.measure_text(LEFT, 0.0, SPECIMEN, paint).unwrap();
            max_width = max_width.max(metrics.width());
        }
        let width = (max_width + 2.0 * LEFT).ceil().max(1800.0) as u32;
        let height = (96.0 + SIZES.iter().map(|size| {
            PHASE_ROWS as f32 * (size + size_delta + 8.0) + 24.0
        }).sum::<f32>()).ceil().max(1200.0) as u32;
        assert!(width < 100_000 && height < 100_000);
        let physical_width = (width as f32 * dpi).ceil() as u32;
        let physical_height = (height as f32 * dpi).ceil() as u32;
        canvas.set_size(physical_width, physical_height, dpi);
        canvas.clear_rect(0, 0, physical_width, physical_height, Color::rgb(245, 244, 239));
        let mut glyph_requests = 0;
        // Keep the returned public glyph IDs until after timing, so specimen
        // counting does not add a hash operation for every glyph to drawing.
        let mut first_row_ids = Vec::with_capacity(SIZES.len());
        let mut top = 96.0;
        for (band, paint) in paints.iter().enumerate() {
            let size = SIZES[band] + size_delta;
            let band_height = PHASE_ROWS as f32 * (size + 8.0);
            let mut panel = Path::new();
            panel.rect(LEFT - 24.0, top - size - 8.0, width as f32 - 2.0 * LEFT + 48.0, band_height + 16.0);
            canvas.fill_path(&panel, &Paint::color(Color::rgb(255, 255, 255)));
            let mut rule = Path::new();
            rule.rect(LEFT - 24.0, top + band_height + 10.0, width as f32 - 2.0 * LEFT + 48.0, 1.0);
            canvas.fill_path(&rule, &Paint::color(Color::rgb(196, 199, 201)));
            for phase in 0..PHASE_ROWS {
                // fill_text lays out at device scale. These logical offsets
                // request horizontal shifts of 0.0 through 0.9 device pixels.
                let x = LEFT + phase as f32 * 0.1 / dpi;
                let y = top + phase as f32 * (size + 8.0);
                let metrics = canvas.fill_text(x, y, SPECIMEN, paint).unwrap();
                glyph_requests += metrics.glyphs.len();
                if phase == 0 {
                    first_row_ids.push((size.to_bits(), metrics.glyphs));
                }
            }
            top += band_height + 24.0;
        }
        let draw_us = start.elapsed().as_secs_f64() * 1e6;
        canvas.flush_to_output(());
        let total_us = start.elapsed().as_secs_f64() * 1e6;
        let distinct: HashSet<_> = first_row_ids.iter().flat_map(|(size, glyphs)| {
            glyphs.iter().map(move |glyph| (glyph.font_id, glyph.glyph_id, *size))
        }).collect();
        assert!(first_row_ids.iter().all(|(_, glyphs)| glyphs.iter().all(|glyph| glyph.glyph_id != 0)));
        Measurement { draw_us, flush_us: total_us - draw_us, total_us, glyph_requests,
                      distinct_instances: distinct.len(), logical_width: width, logical_height: height }
    }
}

fn emit(phase: &str, trial: usize, measured: &[Measurement]) {
    let first = &measured[0];
    assert!(measured.iter().all(|m| m.glyph_requests == first.glyph_requests && m.distinct_instances == first.distinct_instances));
    let frames = measured.len();
    let average = |f: fn(&Measurement) -> f64| measured.iter().map(f).sum::<f64>() / frames as f64;
    println!("proofsheet,{phase},{trial},{frames},{:.6},{:.6},{:.6},{},{},{},{},{},{}",
        average(|m| m.draw_us), average(|m| m.flush_us), average(|m| m.total_us),
        first.glyph_requests, first.distinct_instances, PHASE_ROWS * SIZES.len(),
        measured.iter().map(|m| m.logical_width).max().unwrap(),
        measured.iter().map(|m| m.logical_height).max().unwrap(), SPECIMEN.chars().count());
}

fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(args.len(), 5, "usage: hinting-stress FONT_PATH proofsheet DPI TRIALS");
    assert_eq!(args[2], "proofsheet");
    let dpi: f32 = args[3].parse().unwrap();
    let trials: usize = args[4].parse().unwrap();
    assert!(dpi.is_finite() && dpi > 0.0 && dpi <= 3.0 && trials > 0);
    let data = std::fs::read(&args[1]).expect("read font specimen");
    println!("scene,phase,trial,frames,draw_us,flush_us,total_us,glyph_requests_per_frame,distinct_glyph_size_instances_per_frame,text_draw_calls_per_frame,logical_width,logical_height,nominal_characters_per_row");
    for trial in 0..trials {
        // Font I/O/registration and Canvas creation are outside frame timing.
        // Every trial owns a fresh text context and bitmap atlas.
        let mut canvas = Canvas::new(Void).unwrap();
        let font = canvas.add_font_mem(&data).unwrap();
        canvas.set_size((1800.0 * dpi) as u32, (1200.0 * dpi) as u32, dpi);
        let scene = Scene { font };
        emit("first_paint", trial, &[scene.draw(&mut canvas, dpi, 0.0)]);
        let warm: Vec<_> = (0..30).map(|_| scene.draw(&mut canvas, dpi, 0.0)).collect();
        emit("warm", trial, &warm);
        let new_size: Vec<_> = (1..=12).map(|step| scene.draw(&mut canvas, dpi, step as f32 * 0.1)).collect();
        emit("new_size", trial, &new_size);
        emit("return", trial, &[scene.draw(&mut canvas, dpi, 0.0)]);
        std::hint::black_box(canvas);
    }
}
