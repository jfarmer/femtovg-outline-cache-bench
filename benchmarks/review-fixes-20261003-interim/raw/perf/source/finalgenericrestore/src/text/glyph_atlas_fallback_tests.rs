use super::*;
use crate::{LayerEffects, RecordingRenderer};

const FONT: &[u8] = include_bytes!("../../examples/assets/RobotoFlex-VariableFont.ttf");

fn canvas() -> (Canvas<RecordingRenderer>, FontId) {
    let mut canvas = Canvas::new(RecordingRenderer::default()).unwrap();
    canvas.set_size(400, 200, 1.0);
    let font = canvas.text_context.borrow_mut().add_font_mem(FONT).unwrap();
    (canvas, font)
}

fn glyph(glyph_id: u16, x: f32) -> PositionedGlyph {
    PositionedGlyph { glyph_id, x, y: 70.0 }
}

#[test]
fn generic_negative_positions_reuse_the_integer_bitmap() {
    let glyph_id = swash::FontRef::from_index(FONT, 0).unwrap().charmap().map('g');
    #[cfg(feature = "swash")]
    let modes = [RenderMode::Stroke];
    #[cfg(not(feature = "swash"))]
    let modes = [RenderMode::Fill, RenderMode::Stroke];
    for mode in modes {
        for positions in [[-0.4, 10.0], [10.0, -0.4]] {
            let (mut canvas, font) = canvas();
            let paint = Paint::color(Color::black()).with_font_size(24.0).with_line_width(1.25);
            let draw = |canvas: &mut Canvas<RecordingRenderer>, x| match mode {
                RenderMode::Fill => canvas.fill_glyph_run(font, &[], [glyph(glyph_id, x)], &paint),
                RenderMode::Stroke => canvas.stroke_glyph_run(font, &[], [glyph(glyph_id, x)], &paint),
            };
            draw(&mut canvas, positions[0]).unwrap();
            let first = canvas.verts[canvas.verts.len() - 6..].to_vec();
            let commands_before = canvas.commands.len();
            draw(&mut canvas, positions[1]).unwrap();
            assert_eq!(
                canvas.glyph_atlas.rendered_glyphs.borrow().len(),
                1,
                "{mode:?}, {positions:?}"
            );
            assert_eq!(
                canvas.commands.len() - commands_before,
                1,
                "the second draw only emits its quad"
            );
            let second = &canvas.verts[canvas.verts.len() - 6..];
            for (a, b) in first.iter().zip(second) {
                assert_eq!((a.u, a.v), (b.u, b.v), "both quads sample the same atlas cell");
            }
        }
    }
}

pub(super) fn select_target(canvas: &mut Canvas<RecordingRenderer>, kind: u8) -> RenderTarget {
    match kind {
        1 => {
            let image = canvas
                .create_image_empty(400, 200, PixelFormat::Rgba8, ImageFlags::empty())
                .unwrap();
            canvas.set_render_target(RenderTarget::Image(image));
        }
        2 => assert!(canvas.begin_layer(&LayerEffects::new())),
        _ => {}
    }
    canvas.current_render_target
}

pub(super) fn assert_target_and_following_clear(canvas: &mut Canvas<RecordingRenderer>, expected: RenderTarget) {
    use crate::renderer::CommandType;
    assert_eq!(canvas.current_render_target, expected);
    assert!(
        canvas.commands.iter().any(|command| matches!(
            &command.cmd_type,
            CommandType::SetRenderTarget(RenderTarget::Image(target)) if RenderTarget::Image(*target) != expected
        )),
        "the failed run switched to an atlas target"
    );
    let last_target = canvas.commands.iter().rev().find_map(|command| match command.cmd_type {
        CommandType::SetRenderTarget(target) => Some(target),
        _ => None,
    });
    assert_eq!(last_target, Some(expected));
    let count = canvas.commands.len();
    canvas.clear_rect(0, 0, 4, 4, Color::white());
    assert_eq!(canvas.commands.len(), count + 1);
    assert!(matches!(
        &canvas.commands.last().unwrap().cmd_type,
        CommandType::ClearRect { .. }
    ));
    assert_eq!(canvas.current_render_target, expected);
}

#[test]
fn stroke_atlas_allocation_error_restores_screen_image_and_layer_targets() {
    let face = swash::FontRef::from_index(FONT, 0).unwrap();
    let paint = Paint::color(Color::black()).with_font_size(90.0).with_line_width(30.0);
    for kind in 0..3 {
        let (mut canvas, font) = canvas();
        let initial = select_target(&mut canvas, kind);
        canvas
            .stroke_glyph_run(font, &[], [glyph(face.charmap().map('A'), 10.0)], &paint)
            .unwrap();
        canvas.commands.clear();
        canvas.verts.clear();
        canvas.renderer.fail_image_allocations = true;
        let glyphs = ('!'..='~')
            .enumerate()
            .map(|(index, ch)| glyph(face.charmap().map(ch), 10.0 + index as f32 * 20.0));
        let result = canvas.stroke_glyph_run(font, &[], glyphs, &paint);
        assert!(matches!(result, Err(ErrorKind::UnknownError)), "{result:?}");
        assert_target_and_following_clear(&mut canvas, initial);
    }
}
