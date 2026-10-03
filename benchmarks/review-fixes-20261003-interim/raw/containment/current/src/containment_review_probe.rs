// Containment probe: records, for the same text draws, the RecordingRenderer
// command stream, vertex buffer, glyph-atlas entries and atlas texture count,
// so base (6a5f15a) and branch (da26832) can be diffed per feature set.
// Output goes to the file named by PROBE_OUT.
use std::fmt::Write as _;

use crate::*;

const FONT: &[u8] = include_bytes!("../examples/assets/RobotoFlex-VariableFont.ttf");

fn gid(c: char) -> u16 {
    swash::FontRef::from_index(FONT, 0).unwrap().charmap().map(c)
}

fn glyphs(c: char, xs: &[f32], y: f32) -> Vec<PositionedGlyph> {
    xs.iter()
        .map(|&x| PositionedGlyph {
            x,
            y,
            glyph_id: gid(c),
        })
        .collect()
}

struct Probe {
    canvas: Canvas<RecordingRenderer>,
    cmds: Rc<RefCell<Vec<renderer::Command>>>,
    verts: Rc<RefCell<Vec<renderer::Vertex>>>,
    font: FontId,
}

fn probe_with(renderer: RecordingRenderer) -> Probe {
    let cmds = renderer.last_commands.clone();
    let verts = renderer.last_verts.clone();
    // Slint's shape: a TextContext, a shared font, Canvas::new_with_text_context.
    let text_context = TextContext::default();
    let font = text_context.add_shared_font_with_index(FONT, 0).unwrap();
    let mut canvas = Canvas::new_with_text_context(renderer, text_context).unwrap();
    canvas.set_size(1000, 1000, 1.0);
    Probe {
        canvas,
        cmds,
        verts,
        font,
    }
}

fn probe() -> Probe {
    probe_with(RecordingRenderer::default())
}

fn atlas_state(p: &Probe, out: &mut String) {
    let rg = p.canvas.glyph_atlas.rendered_glyphs.borrow();
    let mut keys: Vec<String> = rg.iter().map(|(k, v)| format!("{k:?} => {v:?}")).collect();
    keys.sort();
    writeln!(out, "rendered_glyphs.len = {}", rg.len()).unwrap();
    for k in keys {
        writeln!(out, "  {k}").unwrap();
    }
    writeln!(
        out,
        "glyph_textures.len = {}",
        p.canvas.glyph_atlas.glyph_textures.borrow().len()
    )
    .unwrap();
    writeln!(out, "glyph_textures = {:?}", p.canvas.glyph_atlas.glyph_textures.borrow()).unwrap();
}

fn snapshot(p: &mut Probe, out: &mut String, label: &str) {
    writeln!(out, "--- {label}").unwrap();
    writeln!(out, "current_render_target(before flush) = {:?}", p.canvas.current_render_target).unwrap();
    writeln!(out, "state_stack.len = {}", p.canvas.state_stack.len()).unwrap();
    atlas_state(p, out);
    p.canvas.flush_to_output(());
    writeln!(out, "commands = {:#?}", p.cmds.borrow()).unwrap();
    writeln!(out, "verts.len = {}", p.verts.borrow().len()).unwrap();
    writeln!(out, "verts = {:?}", p.verts.borrow()).unwrap();
}

fn screen_rect(p: &mut Probe) {
    let mut path = Path::new();
    path.rect(0.0, 0.0, 10.0, 10.0);
    p.canvas.fill_path(&path, &Paint::color(Color::white()));
}

#[test]
fn containment_probe() {
    let mut out = String::new();
    let fill = |size: f32| Paint::color(Color::black()).with_font_size(size);

    // 1. Positive fractional x.
    {
        let mut p = probe();
        p.canvas.translate(100.0, 100.0);
        let r = p.canvas.fill_glyph_run(p.font, &[], glyphs('A', &[10.0, 30.3, 50.7, 70.96, 90.04], 20.0), &fill(20.0));
        writeln!(out, "=== 1 fill positive: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 2. Negative fractional x (only), each in a different phase.
    {
        let mut p = probe();
        p.canvas.translate(200.0, 100.0);
        let r = p.canvas.fill_glyph_run(
            p.font,
            &[],
            glyphs('A', &[-0.3, -10.7, -20.04, -30.96, -40.5, -50.14, -60.16], 20.0),
            &fill(20.0),
        );
        writeln!(out, "=== 2 fill negative: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 3. Zero and positive first, then the same glyph at negative x in a second run.
    {
        let mut p = probe();
        p.canvas.translate(200.0, 100.0);
        let r1 = p.canvas.fill_glyph_run(p.font, &[], glyphs('A', &[0.0, 20.3, 40.7], 20.0), &fill(20.0));
        writeln!(out, "=== 3 fill zero/positive then negative: {r1:?}").unwrap();
        snapshot(&mut p, &mut out, "first run");
        let r2 = p.canvas.fill_glyph_run(p.font, &[], glyphs('A', &[-0.3, -20.7, -40.04, -60.5], 20.0), &fill(20.0));
        writeln!(out, "second run: {r2:?}").unwrap();
        snapshot(&mut p, &mut out, "second run");
    }
    // 4. Every phase: x = k / 20 for k in -40..=40.
    {
        let mut p = probe();
        p.canvas.translate(300.0, 100.0);
        let xs: Vec<f32> = (-40..=40).map(|k| k as f32 / 20.0).collect();
        let r = p.canvas.fill_glyph_run(p.font, &[], glyphs('A', &xs, 20.0), &fill(20.0));
        writeln!(out, "=== 4 fill every phase: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
        // Same with fine x steps to reach every reachable key.
        let xs: Vec<f32> = (-2000..=2000).map(|k| k as f32 / 1000.0).collect();
        let r = p.canvas.fill_glyph_run(p.font, &[], glyphs('A', &xs, 40.0), &fill(20.0));
        writeln!(out, "=== 4b fill fine phases: {r:?}").unwrap();
        atlas_state(&p, &mut out);
        p.canvas.flush_to_output(());
    }
    // 5. Large glyphs in the atlas (font 90) at negative, zero and positive x.
    {
        let mut p = probe();
        p.canvas.translate(300.0, 300.0);
        let r = p.canvas.fill_glyph_run(p.font, &[], glyphs('W', &[-103.4, 0.0, 103.4], 90.0), &fill(90.0));
        writeln!(out, "=== 5 fill large: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 6. Stroked text at negative, zero and positive x.
    {
        let mut p = probe();
        p.canvas.translate(200.0, 100.0);
        let stroke = Paint::color(Color::black()).with_font_size(20.0).with_line_width(2.0);
        let r = p.canvas.stroke_glyph_run(
            p.font,
            &[],
            glyphs('A', &[-0.3, 0.0, 20.3, -20.7, 40.0], 20.0),
            &stroke,
        );
        writeln!(out, "=== 6 stroke: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 7. Scaled atlas (uniform scale 2, solid colour) with negative and positive x.
    {
        let mut p = probe();
        p.canvas.translate(300.0, 100.0);
        p.canvas.scale(2.0, 2.0);
        let r = p.canvas.fill_glyph_run(p.font, &[], glyphs('A', &[-0.3, 0.3, 10.0], 10.0), &fill(10.0));
        writeln!(out, "=== 7 scaled atlas: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 8. Glyph larger than an atlas on the generic (stroke) path, after a glyph
    //    that fits: a '.' is rasterized first and switches to the atlas.
    {
        let mut p = probe();
        let stroke = Paint::color(Color::black()).with_font_size(40.0).with_line_width(476.0);
        let run = vec![
            PositionedGlyph {
                x: 10.0,
                y: 20.0,
                glyph_id: gid('.'),
            },
            PositionedGlyph {
                x: 30.0,
                y: 20.0,
                glyph_id: gid('W'),
            },
        ];
        let r = p.canvas.stroke_glyph_run(p.font, &[], run, &stroke);
        writeln!(out, "=== 8 stroke larger than atlas after a fitting glyph: {r:?}").unwrap();
        writeln!(out, "target right after = {:?}", p.canvas.current_render_target).unwrap();
        screen_rect(&mut p);
        snapshot(&mut p, &mut out, "after error and a screen rect");
    }
    // 8b. Same inside an image render target.
    {
        let mut p = probe();
        let img = p
            .canvas
            .create_image_empty(64, 64, PixelFormat::Rgba8, ImageFlags::empty())
            .unwrap();
        p.canvas.set_render_target(RenderTarget::Image(img));
        let stroke = Paint::color(Color::black()).with_font_size(40.0).with_line_width(476.0);
        let run = vec![
            PositionedGlyph {
                x: 10.0,
                y: 20.0,
                glyph_id: gid('.'),
            },
            PositionedGlyph {
                x: 30.0,
                y: 20.0,
                glyph_id: gid('W'),
            },
        ];
        let r = p.canvas.stroke_glyph_run(p.font, &[], run, &stroke);
        writeln!(out, "=== 8b stroke too large inside an image target: {r:?}").unwrap();
        writeln!(out, "target right after = {:?}", p.canvas.current_render_target).unwrap();
        screen_rect(&mut p);
        snapshot(&mut p, &mut out, "after");
    }
    // 9. Atlas allocation failure on the first glyph.
    {
        let mut p = probe_with(RecordingRenderer {
            fail_image_allocations: true,
            ..Default::default()
        });
        let r = p.canvas.fill_glyph_run(p.font, &[], glyphs('A', &[10.0, 20.5], 20.0), &fill(20.0));
        writeln!(out, "=== 9 atlas allocation failure: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
        let r = p.canvas.stroke_glyph_run(
            p.font,
            &[],
            glyphs('A', &[10.0], 20.0),
            &Paint::color(Color::black()).with_font_size(20.0).with_line_width(2.0),
        );
        writeln!(out, "=== 9b stroke atlas allocation failure: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 9c. Atlas allocation failure after a space was rasterized into an existing
    //     atlas on the generic path, by filling the first atlas with large strokes.
    {
        let mut p = probe();
        let stroke = Paint::color(Color::black()).with_font_size(20.0).with_line_width(200.0);
        // Each stroked glyph needs about 220 x 230: four fill one 512 atlas.
        let first: Vec<PositionedGlyph> = "ABCD"
            .chars()
            .map(|c| PositionedGlyph {
                x: 10.0,
                y: 20.0,
                glyph_id: gid(c),
            })
            .collect();
        let r = p.canvas.stroke_glyph_run(p.font, &[], first, &stroke);
        writeln!(out, "=== 9c fill first atlas: {r:?}").unwrap();
        writeln!(out, "textures = {}", p.canvas.glyph_atlas.glyph_textures.borrow().len()).unwrap();
        p.canvas.flush_to_output(());
        p.canvas.renderer.fail_image_allocations = true;
        let second: Vec<PositionedGlyph> = " EFGH"
            .chars()
            .map(|c| PositionedGlyph {
                x: 10.0,
                y: 20.0,
                glyph_id: gid(c),
            })
            .collect();
        let r = p.canvas.stroke_glyph_run(p.font, &[], second, &stroke);
        writeln!(out, "second run with allocation failing: {r:?}").unwrap();
        writeln!(out, "target right after = {:?}", p.canvas.current_render_target).unwrap();
        screen_rect(&mut p);
        snapshot(&mut p, &mut out, "after");
    }
    // 10. Missing font: a font id from another canvas that this one does not have.
    {
        let other = TextContext::default();
        let _ = other.add_shared_font_with_index(FONT, 0).unwrap();
        let foreign = other.add_shared_font_with_index(FONT, 0).unwrap();
        let mut p = probe();
        let r = p.canvas.fill_glyph_run(foreign, &[], glyphs('A', &[10.0], 20.0), &fill(20.0));
        writeln!(out, "=== 10 missing font: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 11. Missing glyph id.
    {
        let mut p = probe();
        let run = vec![
            PositionedGlyph {
                x: 10.0,
                y: 20.0,
                glyph_id: 65000,
            },
            PositionedGlyph {
                x: -10.5,
                y: 20.0,
                glyph_id: 65000,
            },
        ];
        let r = p.canvas.fill_glyph_run(p.font, &[], run.clone(), &fill(20.0));
        writeln!(out, "=== 11 missing glyph fill: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
        let r = p.canvas.stroke_glyph_run(
            p.font,
            &[],
            run,
            &Paint::color(Color::black()).with_font_size(20.0).with_line_width(2.0),
        );
        writeln!(out, "=== 11b missing glyph stroke: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 12. Image update failure (swash upload path; generic paths never update).
    {
        let mut p = probe_with(RecordingRenderer {
            fail_image_updates: true,
            ..Default::default()
        });
        let r = p.canvas.fill_glyph_run(p.font, &[], glyphs('A', &[10.0], 20.0), &fill(20.0));
        writeln!(out, "=== 12 image update failure, fill: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
        let run = vec![
            PositionedGlyph {
                x: 10.0,
                y: 20.0,
                glyph_id: gid(' '),
            },
            PositionedGlyph {
                x: 30.0,
                y: 20.0,
                glyph_id: gid('B'),
            },
        ];
        let r = p.canvas.fill_glyph_run(p.font, &[], run, &fill(20.0));
        writeln!(out, "=== 12b image update failure after a fallback space: {r:?}").unwrap();
        writeln!(out, "target right after = {:?}", p.canvas.current_render_target).unwrap();
        screen_rect(&mut p);
        snapshot(&mut p, &mut out, "after");
    }
    // 13. Current target is an image pending deletion.
    {
        let mut p = probe();
        let img = p
            .canvas
            .create_image_empty(64, 64, PixelFormat::Rgba8, ImageFlags::empty())
            .unwrap();
        p.canvas.set_render_target(RenderTarget::Image(img));
        p.canvas.delete_image(img);
        let stroke = Paint::color(Color::black()).with_font_size(20.0).with_line_width(2.0);
        let r = p.canvas.stroke_glyph_run(p.font, &[], glyphs('A', &[10.0], 20.0), &stroke);
        writeln!(out, "=== 13 pending-deletion target, stroke: {r:?}").unwrap();
        writeln!(out, "target right after = {:?}", p.canvas.current_render_target).unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    // 14. fill_text through textlayout, mixed negative and positive.
    #[cfg(feature = "textlayout")]
    {
        let mut p = probe();
        p.canvas.translate(100.0, 100.0);
        let r = p.canvas.fill_text(-7.3, 20.0, "Hello, world", &fill(18.0));
        writeln!(out, "=== 14 fill_text at -7.3: {:?}", r.map(|m| (m.x, m.y, m.width(), m.height()))).unwrap();
        snapshot(&mut p, &mut out, "after");
        let r = p.canvas.stroke_text(-7.3, 50.0, "Hello, world", &fill(18.0).with_line_width(1.5));
        writeln!(out, "=== 14b stroke_text at -7.3: {:?}", r.map(|m| (m.x, m.y, m.width(), m.height()))).unwrap();
        snapshot(&mut p, &mut out, "after");
    }

    // 15. Success inside an open layer and inside an image target: fill and
    //     stroke at negative and positive x, then a screen rect.
    for kind in 0..2 {
        let mut p = probe();
        if kind == 0 {
            assert!(p.canvas.begin_layer(&LayerEffects::new()));
        } else {
            let img = p
                .canvas
                .create_image_empty(256, 256, PixelFormat::Rgba8, ImageFlags::empty())
                .unwrap();
            p.canvas.set_render_target(RenderTarget::Image(img));
        }
        p.canvas.translate(100.0, 100.0);
        let r1 = p.canvas.fill_glyph_run(p.font, &[], glyphs('B', &[-0.3, 10.0, 20.5], 20.0), &fill(20.0));
        let r2 = p.canvas.stroke_glyph_run(
            p.font,
            &[],
            glyphs('B', &[-0.3, 10.0, 20.5], 50.0),
            &fill(20.0).with_line_width(2.0),
        );
        writeln!(out, "=== 15.{kind} inside layer(0)/image(1): {r1:?} {r2:?}").unwrap();
        writeln!(out, "target right after = {:?}", p.canvas.current_render_target).unwrap();
        if kind == 0 {
            p.canvas.end_layer();
        }
        screen_rect(&mut p);
        snapshot(&mut p, &mut out, "after");
    }


    // Additional isolated generic scenarios avoid native fills contaminating
    // atlas state in a stroke snapshot and cover the direct rendering routes.
    #[cfg(feature = "textlayout")]
    {
        let mut p = probe();
        p.canvas.translate(100.0, 100.0);
        let r = p.canvas.stroke_text(-7.3, 50.0, "Hello, world", &fill(18.0).with_line_width(1.5));
        writeln!(out, "=== 16 stroke_text isolated: {:?}", r.map(|m| (m.x, m.y, m.width(), m.height()))).unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    for stroked in [false, true] {
        let mut p = probe();
        p.canvas.translate(200.0, 200.0);
        let paint = fill(96.0).with_line_width(2.0);
        let run = glyphs('A', &[-10.3, 0.0, 110.7], 96.0);
        let r = if stroked {
            p.canvas.stroke_glyph_run(p.font, &[], run, &paint)
        } else {
            p.canvas.fill_glyph_run(p.font, &[], run, &paint)
        };
        writeln!(out, "=== 17.{stroked} large direct: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    for stroked in [false, true] {
        let mut p = probe();
        p.canvas.translate(200.0, 200.0);
        p.canvas.rotate(0.2);
        let paint = fill(20.0).with_line_width(2.0);
        let run = glyphs('A', &[-10.3, 0.0, 30.7], 20.0);
        let r = if stroked {
            p.canvas.stroke_glyph_run(p.font, &[], run, &paint)
        } else {
            p.canvas.fill_glyph_run(p.font, &[], run, &paint)
        };
        writeln!(out, "=== 18.{stroked} rotated direct: {r:?}").unwrap();
        snapshot(&mut p, &mut out, "after");
    }
    for kind in 0..2 {
        let mut p = probe();
        if kind == 0 {
            assert!(p.canvas.begin_layer(&LayerEffects::new()));
        } else {
            let img = p.canvas.create_image_empty(256, 256, PixelFormat::Rgba8, ImageFlags::empty()).unwrap();
            p.canvas.set_render_target(RenderTarget::Image(img));
        }
        p.canvas.translate(100.0, 100.0);
        let r = p.canvas.stroke_glyph_run(p.font, &[], glyphs('B', &[-0.3, 10.0, 20.5], 50.0), &fill(20.0).with_line_width(2.0));
        writeln!(out, "=== 19.{kind} isolated stroke inside layer(0)/image(1): {r:?}").unwrap();
        if kind == 0 {
            p.canvas.end_layer();
        }
        screen_rect(&mut p);
        snapshot(&mut p, &mut out, "after");
    }

    let path = std::env::var("PROBE_OUT").expect("PROBE_OUT");
    std::fs::write(path, out).unwrap();
}
