#![allow(unused)]
use femtovg::{Align, Baseline, Canvas, Color, FillRule, FontId, ImageFlags, ImageId, LineCap, LineJoin, Paint, Path, Renderer, Solidity};
use std::f32::consts::PI;
use crate::{asset, Frame, Size};
use crate::perf_graph::PerfGraph;
fn draw_baselines<T: Renderer>(
    canvas: &mut Canvas<T>,
    font: FontId,
    x: f32,
    y: f32,
    font_size: f32,
    supports_emojis: bool,
) {
    let baselines = [Baseline::Top, Baseline::Middle, Baseline::Alphabetic, Baseline::Bottom];

    let mut paint = Paint::color(Color::black())
        .with_font(&[font])
        .with_font_size(font_size);

    let mut base_text = "AbcpKjgF".to_string();
    if supports_emojis {
        base_text.push_str("🚀🌳");
    }

    for (i, baseline) in baselines.iter().enumerate() {
        let y = y + i as f32 * 40.0;

        let mut path = Path::new();
        path.move_to(x, y + 0.5);
        path.line_to(x + 250., y + 0.5);
        canvas.stroke_path(&path, &Paint::color(Color::rgba(255, 32, 32, 128)));

        paint.set_text_baseline(*baseline);

        if let Ok(res) = canvas.fill_text(x, y, format!("{base_text} Baseline::{baseline:?}"), &paint) {
            //let res = canvas.fill_text(10.0, y, format!("d النص العربي جميل جدا {:?}", baseline), &paint);

            let mut path = Path::new();
            path.rect(res.x, res.y, res.width(), res.height());
            canvas.stroke_path(&path, &Paint::color(Color::rgba(100, 100, 100, 64)));
        }
    }
}

fn draw_alignments<T: Renderer>(canvas: &mut Canvas<T>, font: FontId, x: f32, y: f32, font_size: f32) {
    let alignments = [Align::Left, Align::Center, Align::Right];

    let mut path = Path::new();
    path.move_to(x + 0.5, y - 20.);
    path.line_to(x + 0.5, y + 80.);
    canvas.stroke_path(&path, &Paint::color(Color::rgba(255, 32, 32, 128)));

    let mut paint = Paint::color(Color::black())
        .with_font(&[font])
        .with_font_size(font_size);

    for (i, alignment) in alignments.iter().enumerate() {
        paint.set_text_align(*alignment);

        if let Ok(res) = canvas.fill_text(x, y + i as f32 * 30.0, format!("Align::{alignment:?}"), &paint) {
            let mut path = Path::new();
            path.rect(res.x, res.y, res.width(), res.height());
            canvas.stroke_path(&path, &Paint::color(Color::rgba(100, 100, 100, 64)));
        }
    }
}

fn draw_paragraph<T: Renderer>(canvas: &mut Canvas<T>, font: FontId, x: f32, y: f32, font_size: f32, text: &str) {
    let paint = Paint::color(Color::black())
        .with_font(&[font])
        .with_font_weight(Paint::FONT_WEIGHT_LIGHT)
        //.with_text_align(Align::Right)
        .with_font_size(font_size);

    let font_metrics = canvas.measure_font(&paint).expect("Error measuring font");

    let width = canvas.width() as f32;
    let mut y = y;

    let lines = canvas
        .break_text_vec(width, text, &paint)
        .expect("Error while breaking text");

    for line_range in lines {
        if let Ok(_res) = canvas.fill_text(x, y, &text[line_range], &paint) {
            y += font_metrics.height();
        }
    }

    // let mut start = 0;

    // while start < text.len() {
    //     let substr = &text[start..];

    //     if let Ok(index) = canvas.break_text(width, substr, &paint) {
    //         if let Ok(res) = canvas.fill_text(x, y, &substr[0..index], &paint) {
    //             y += res.height;
    //         }

    //         start += &substr[0..index].len();
    //     } else {
    //         break;
    //     }
    // }
}

fn draw_inc_size<T: Renderer>(canvas: &mut Canvas<T>, font: FontId, x: f32, y: f32) {
    let mut cursor_y = y;

    for i in 4..23 {
        let paint = Paint::color(Color::black()).with_font(&[font]).with_font_size(i as f32);

        let font_metrics = canvas.measure_font(&paint).expect("Error measuring font");

        if let Ok(_res) = canvas.fill_text(x, cursor_y, "The quick brown fox jumps over the lazy dog", &paint) {
            cursor_y += font_metrics.height();
        }
    }
}

fn draw_stroked<T: Renderer>(canvas: &mut Canvas<T>, font: FontId, x: f32, y: f32) {
    let paint = Paint::color(Color::rgba(0, 0, 0, 128))
        .with_font(&[font])
        .with_font_weight(Paint::FONT_WEIGHT_BOLD)
        .with_line_width(12.0)
        .with_font_size(72.0);
    let _ = canvas.stroke_text(x + 5.0, y + 5.0, "RUST", &paint);

    let paint = paint.with_color(Color::black()).with_line_width(10.0);
    let _ = canvas.stroke_text(x, y, "RUST", &paint);

    let paint = paint.with_line_width(6.0).with_color(Color::hex("#B7410E"));
    let _ = canvas.stroke_text(x, y, "RUST", &paint);

    let paint = paint.with_color(Color::white());
    let _ = canvas.fill_text(x, y, "RUST", &paint);
}

fn draw_gradient_fill<T: Renderer>(canvas: &mut Canvas<T>, font: FontId, x: f32, y: f32) {
    let paint = Paint::color(Color::rgba(0, 0, 0, 255))
        .with_font(&[font])
        .with_font_weight(Paint::FONT_WEIGHT_BOLD)
        .with_line_width(6.0)
        .with_font_size(72.0);
    let _ = canvas.stroke_text(x, y, "RUST", &paint);

    let paint = Paint::linear_gradient(
        x,
        y - 60.0,
        x,
        y,
        Color::rgba(225, 133, 82, 255),
        Color::rgba(93, 55, 70, 255),
    )
    .with_font(&[font])
    .with_font_weight(Paint::FONT_WEIGHT_BOLD)
    .with_font_size(72.0);
    let _ = canvas.fill_text(x, y, "RUST", &paint);
}

fn draw_image_fill<T: Renderer>(canvas: &mut Canvas<T>, font: FontId, x: f32, y: f32, image_id: ImageId, t: f32) {
    let paint = Paint::color(Color::hex("#7300AB")).with_line_width(3.0);
    let mut path = Path::new();
    path.move_to(x, y - 2.0);
    path.line_to(x + 180.0, y - 2.0);
    canvas.stroke_path(&path, &paint);

    let text = "RUST";

    let paint = Paint::color(Color::rgba(0, 0, 0, 128))
        .with_font(&[font])
        .with_font_weight(Paint::FONT_WEIGHT_BOLD)
        .with_line_width(4.0)
        .with_font_size(72.0);
    let _ = canvas.stroke_text(x, y, text, &paint);

    //let mut paint = Paint::image(image_id, x + 50.0, y - t*10.0, 120.0, 120.0, t.sin() / 10.0, 0.70);
    let paint = Paint::image(image_id, x, y - t * 10.0, 120.0, 120.0, 0.0, 0.50)
        .with_font(&[font])
        .with_font_weight(Paint::FONT_WEIGHT_BOLD)
        .with_font_size(72.0);
    let _ = canvas.fill_text(x, y, text, &paint);
}

fn draw_complex<T: Renderer>(canvas: &mut Canvas<T>, x: f32, y: f32, font_size: f32) {
    let paint = Paint::color(Color::rgb(34, 34, 34)).with_font_size(font_size);

    let _ = canvas.fill_text(
        x,
        y,
        "Latin اللغة العربية Кирилица тест iiiiiiiiiiiiiiiiiiiiiiiiiiiii\nasdasd",
        &paint,
    );
    //let _ = canvas.fill_text(x, y, "اللغة العربية", &paint);
    //canvas.fill_text(x, y, "Traditionally, text is composed to create a readable, coherent, and visually satisfying", &paint);
}

const LOREM_TEXT: &str = r"
Traditionally, text is composed to create a readable, coherent, and visually satisfying typeface
that works invisibly, without the awareness of the reader. Even distribution of typeset material,
with a minimum of distractions and anomalies, is aimed at producing clarity and transparency.
Choice of typeface(s) is the primary aspect of text typography—prose fiction, non-fiction,
editorial, educational, religious, scientific, spiritual, and commercial writing all have differing
characteristics and requirements of appropriate typefaces and their fonts or styles.

مرئية وسهلة قراءة وجذابة. ترتيب الحروف يشمل كل من اختيار عائلة الخط وحجم وطول الخط والمسافة بين السطور

مرئية وسهلة قراءة وجذابة. ترتيب الحروف يشمل كل من اختيار (asdasdasdasdasdasd) عائلة الخط وحجم وطول الخط والمسافة بين السطور

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur in nisi at ligula lobortis pretium. Sed vel eros tincidunt, fermentum metus sit amet, accumsan massa. Vestibulum sed elit et purus suscipit
Sed at gravida lectus. Duis eu nisl non sem lobortis rutrum. Sed non mauris urna. Pellentesque suscipit nec odio eu varius. Quisque lobortis elit in finibus vulputate. Mauris quis gravida libero.
Etiam non malesuada felis, nec fringilla quam.
";

// const LOREM_TEXT: &str = r#"
// مرئية وسهلة قراءة وجذابة. ترتيب الحروف يشمل كل من اختيار (asdasdasdasdasdasd) عائلة الخط وحجم وطول الخط والمسافة بين السطور
// "#;


pub struct Scene { font: FontId, image: ImageId, perf: PerfGraph, supports_emojis: bool }
impl Scene {
    pub fn new<T: Renderer>(canvas: &mut Canvas<T>) -> Self {
        let font = canvas.add_font_mem(&crate::regular_text_font()).unwrap();
        canvas.add_font_mem(&asset("amiri-regular.ttf")).unwrap();
        let supports_emojis = canvas.add_font("/System/Library/Fonts/Apple Color Emoji.ttc").is_ok();
        eprintln!("text example optional Apple Color Emoji: {supports_emojis}");
        let flags = ImageFlags::GENERATE_MIPMAPS | ImageFlags::REPEAT_X | ImageFlags::REPEAT_Y;
        let image = canvas.load_image_mem(&asset("pattern.jpg"), flags).unwrap();
        Self { font, image, perf: PerfGraph::new(), supports_emojis }
    }
    pub fn draw<T: Renderer>(&mut self, canvas: &mut Canvas<T>, f: Frame) {
        let mut canvas = canvas;
        let size = Size { width: f.width, height: f.height };
        let font = self.font;
        let image_id = self.image;
        let perf = &mut self.perf;
        perf.update(1.0 / 60.0);
        let elapsed = f.index as f32 / 60.0;
        let font_size = f.font_size;
        let x = f.x;
        let y = f.y;
        let supports_emojis = self.supports_emojis;
        canvas.clear_rect(0, 0, size.width, size.height, Color::rgbf(0.9, 0.9, 0.9));
                draw_baselines(&mut canvas, font, 5.0, 50.0, font_size, supports_emojis);
                draw_alignments(&mut canvas, font, 120.0, 200.0, font_size);
                draw_paragraph(&mut canvas, font, x, y, font_size, LOREM_TEXT);
                draw_inc_size(&mut canvas, font, 300.0, 10.0);

                draw_complex(&mut canvas, 300.0, 340.0, font_size);

                draw_stroked(&mut canvas, font, size.width as f32 - 200.0, 100.0);
                draw_gradient_fill(&mut canvas, font, size.width as f32 - 200.0, 180.0);
                draw_image_fill(&mut canvas, font, size.width as f32 - 200.0, 260.0, image_id, elapsed);

                let paint = Paint::color(Color::hex("B7410E"))
                    .with_font(&[font])
                    .with_font_weight(Paint::FONT_WEIGHT_BOLD)
                    .with_text_baseline(Baseline::Top)
                    .with_text_align(Align::Right);
                let _ = canvas.fill_text(
                    size.width as f32 - 10.0,
                    10.0,
                    format!("Scroll to increase / decrease font size. Current: {font_size}"),
                    &paint,
                );
                #[cfg(feature = "debug_inspector")]
                let _ = canvas.fill_text(
                    size.width as f32 - 10.0,
                    24.0,
                    format!("Click to show font atlas texture. Current: {font_texture_to_show:?}"),
                    &paint,
                );

                canvas.save();
                canvas.reset();
                perf.render(&mut canvas, 5.0, 5.0);
                canvas.restore();

                #[cfg(feature = "debug_inspector")]
                if let Some(index) = font_texture_to_show {
                    canvas.save();
                    canvas.reset();
                    let textures = canvas.debug_inspector_get_font_textures();
                    if let Some(&id) = textures.get(index) {
                        canvas.debug_inspector_draw_image(id);
                    }
                    canvas.restore();
                }


    }
}
