mod demo;
mod perf_graph;
mod text;

use femtovg::{renderer::Void, Canvas, Renderer};
use std::{path::PathBuf, time::Instant};

fn asset(file: &str) -> Vec<u8> {
    std::fs::read(
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("../../assets")
            .join(file),
    )
    .unwrap()
}

fn regular_text_font() -> Vec<u8> {
    match std::env::var_os("FEMTOVG_REPLAY_TEXT_FONT") {
        Some(path) => std::fs::read(path).expect("read selected text font"),
        None => asset("RobotoFlex-VariableFont.ttf"),
    }
}

#[derive(Clone, Copy)]
pub struct Size {
    pub width: u32,
    pub height: u32,
}

#[derive(Clone, Copy)]
pub struct Frame {
    pub index: u32,
    pub width: u32,
    pub height: u32,
    pub font_size: f32,
    pub x: f32,
    pub y: f32,
    pub mousex: f32,
    pub mousey: f32,
    pub weight: f32,
    pub slant: f32,
}

impl Frame {
    fn new() -> Self {
        Self {
            index: 0,
            width: 1000,
            height: 600,
            font_size: 18.0,
            x: 5.0,
            y: 380.0,
            mousex: 500.0,
            mousey: 300.0,
            weight: 400.0,
            slant: 0.0,
        }
    }
}

enum Scene {
    Demo(demo::Scene),
    Text(text::Scene),
}

impl Scene {
    fn new<T: Renderer>(name: &str, canvas: &mut Canvas<T>) -> Self {
        match name {
            "demo" => Self::Demo(demo::Scene::new(canvas)),
            "text" => Self::Text(text::Scene::new(canvas)),
            _ => panic!("unknown scene: {name}"),
        }
    }

    fn draw<T: Renderer>(&mut self, canvas: &mut Canvas<T>, frame: Frame) {
        match self {
            Self::Demo(scene) => scene.draw(canvas, frame),
            Self::Text(scene) => scene.draw(canvas, frame),
        }
    }
}

struct Measurement {
    draw_us: f64,
    flush_us: f64,
    total_us: f64,
}

fn frame(canvas: &mut Canvas<Void>, scene: &mut Scene, state: &mut Frame, dpi: f32) -> Measurement {
    let start = Instant::now();
    canvas.set_size(state.width, state.height, dpi);
    scene.draw(canvas, *state);
    let draw_us = start.elapsed().as_secs_f64() * 1e6;
    canvas.flush_to_output(());
    let total_us = start.elapsed().as_secs_f64() * 1e6;
    state.index += 1;
    Measurement {
        draw_us,
        flush_us: total_us - draw_us,
        total_us,
    }
}

fn emit(name: &str, phase: &str, trial: usize, measurements: &[Measurement]) {
    let frames = measurements.len();
    let divisor = frames as f64;
    println!(
        "{name},{phase},{trial},{frames},{:.6},{:.6},{:.6}",
        measurements.iter().map(|m| m.draw_us).sum::<f64>() / divisor,
        measurements.iter().map(|m| m.flush_us).sum::<f64>() / divisor,
        measurements.iter().map(|m| m.total_us).sum::<f64>() / divisor
    );
}

fn run(name: &str, trial: usize, dpi: f32) {
    let mut canvas = Canvas::new(Void).unwrap();
    let mut scene = Scene::new(name, &mut canvas);
    let mut state = Frame::new();
    // Scene constructors load fonts and images outside the first-paint timing.
    emit(
        name,
        "first_paint",
        trial,
        &[frame(&mut canvas, &mut scene, &mut state, dpi)],
    );
    for _ in 1..120 {
        frame(&mut canvas, &mut scene, &mut state, dpi);
    }
    let warm = (0..30)
        .map(|_| frame(&mut canvas, &mut scene, &mut state, dpi))
        .collect::<Vec<_>>();
    emit(name, "warm", trial, &warm);
    let phases: &[(&str, usize)] = match name {
        "text" => &[
            ("x_advance", 10),
            ("x_return", 10),
            ("y_advance", 10),
            ("size_advance", 12),
            ("size_return", 12),
            ("reflow", 3),
        ],
        "demo" => &[("zoom_in", 12), ("zoom_out", 12), ("pan", 10)],
        _ => unreachable!(),
    };
    for &(phase, count) in phases {
        let mut measured = Vec::with_capacity(count);
        for index in 0..count {
            match phase {
                "x_advance" => state.x += 0.1,
                "x_return" => state.x -= 0.1,
                "y_advance" => state.y += 0.1,
                "size_advance" => state.font_size = (state.font_size + 0.5).max(2.0),
                "size_return" => state.font_size = (state.font_size - 0.5).max(2.0),
                "reflow" => state.width = [800, 600, 1000][index],
                "zoom_in" | "zoom_out" => {
                    let point = canvas
                        .transform()
                        .inverse()
                        .transform_point(state.mousex, state.mousey);
                    let direction = if phase == "zoom_in" { 1.0 } else { -1.0 };
                    canvas.translate(point.0, point.1);
                    canvas.scale(1.0 + direction / 10.0, 1.0 + direction / 10.0);
                    canvas.translate(-point.0, -point.1);
                }
                "pan" => {
                    let before = canvas
                        .transform()
                        .inverse()
                        .transform_point(state.mousex, state.mousey);
                    state.mousex += 10.0;
                    let after = canvas
                        .transform()
                        .inverse()
                        .transform_point(state.mousex, state.mousey);
                    canvas.translate(after.0 - before.0, after.1 - before.1);
                }
                _ => unreachable!(),
            }
            measured.push(frame(&mut canvas, &mut scene, &mut state, dpi));
        }
        emit(name, phase, trial, &measured);
    }
}

fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    let scene = args.get(1).map(String::as_str).unwrap_or("all");
    let trials: usize = args.get(2).map(|s| s.parse().unwrap()).unwrap_or(1);
    let dpi: f32 = args.get(3).map(|s| s.parse().unwrap()).unwrap_or(1.0);
    println!("scene,phase,trial,frames,draw_us,flush_us,total_us");
    for trial in 0..trials {
        for name in ["demo", "text"] {
            if scene == "all" || scene == name {
                run(name, trial, dpi);
            }
        }
    }
}
