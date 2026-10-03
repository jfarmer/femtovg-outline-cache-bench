// Append this module to src/text.rs. It runs generic fill coverage without
// Swash and stroke coverage with either font backend.
#[cfg(all(test, any(feature = "textlayout", feature = "swash")))]
mod review_phase_regressions {
    use super::*;
    use crate::RecordingRenderer;

    const FONT: &[u8] = include_bytes!(concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/examples/assets/RobotoFlex-VariableFont.ttf"
    ));

    fn setup() -> (Canvas<RecordingRenderer>, FontId, u16) {
        let mut canvas = Canvas::new(RecordingRenderer::default()).unwrap();
        canvas.set_size(400, 200, 1.0);
        let font = canvas.text_context.borrow_mut().add_font_mem(FONT).unwrap();
        let glyph_id = swash::FontRef::from_index(FONT, 0)
            .unwrap()
            .charmap()
            .map('g');
        (canvas, font, glyph_id)
    }

    #[test]
    fn review_generic_negative_position_reuses_the_integer_bitmap() {
        #[cfg(feature = "swash")]
        let modes = [RenderMode::Stroke];
        #[cfg(not(feature = "swash"))]
        let modes = [RenderMode::Fill, RenderMode::Stroke];
        for mode in modes {
            for positions in [[-0.4, 10.0], [10.0, -0.4]] {
                let (mut canvas, font, glyph_id) = setup();
                let paint = Paint::color(Color::black())
                    .with_font_size(24.0)
                    .with_line_width(1.25);
                let draw = |canvas: &mut Canvas<RecordingRenderer>, x| {
                    let glyph = [PositionedGlyph {
                        glyph_id,
                        x,
                        y: 70.0,
                    }];
                    match mode {
                        RenderMode::Fill => canvas.fill_glyph_run(font, &[], glyph, &paint),
                        RenderMode::Stroke => canvas.stroke_glyph_run(font, &[], glyph, &paint),
                    }
                    .unwrap();
                };
                draw(&mut canvas, positions[0]);
                let first = canvas.verts[canvas.verts.len() - 6..].to_vec();
                let commands_before = canvas.commands.len();
                draw(&mut canvas, positions[1]);
                assert_eq!(canvas.glyph_atlas.rendered_glyphs.borrow().len(), 1,
                    "a phase-insensitive {mode:?} rasterizer must reuse its bitmap in either draw order");
                assert_eq!(
                    canvas.commands.len() - commands_before,
                    1,
                    "the second draw must append only its screen quad, without rerasterizing"
                );
                let second = &canvas.verts[canvas.verts.len() - 6..];
                for (a, b) in first.iter().zip(second) {
                    assert_eq!(
                        (a.u, a.v),
                        (b.u, b.v),
                        "both quads must sample the same atlas cell"
                    );
                }
            }
        }
    }

    #[cfg(feature = "swash")]
    #[test]
    fn review_native_negative_position_matches_its_integer_translation() {
        use swash::{
            scale::{Render, ScaleContext, Source},
            zeno::{Format, Vector},
        };
        let face = swash::FontRef::from_index(FONT, 0).unwrap();
        let glyph_id = face.charmap().map('g');
        let mut context = ScaleContext::new();
        let mut scaler = context.builder(face).size(24.0).hint(true).build();
        // -0.4 is independently decomposed as origin -1 and phase 0.6.
        let expected = Render::new(&[Source::Outline])
            .format(Format::Alpha)
            .offset(Vector::new(0.6, 0.0))
            .render(&mut scaler, glyph_id)
            .unwrap();
        let mut recorded = Vec::new();
        for (x, expected_origin) in [(-0.4, -1.0), (19.6, 19.0)] {
            let (mut canvas, font, _) = setup();
            canvas.renderer.record_image_masks = true;
            canvas
                .fill_glyph_run(
                    font,
                    &[],
                    [PositionedGlyph {
                        glyph_id,
                        x,
                        y: 70.0,
                    }],
                    &Paint::color(Color::black()).with_font_size(24.0),
                )
                .unwrap();
            assert_eq!(canvas.renderer.image_masks.len(), 1);
            let (width, height, pixels) = canvas.renderer.image_masks.last().unwrap();
            let padding = GLYPH_PADDING as usize;
            assert_eq!(
                (*width, *height),
                (
                    expected.placement.width as usize + 2 * padding,
                    expected.placement.height as usize + 2 * padding
                )
            );
            let coverage: Vec<u8> = (0..expected.placement.height as usize)
                .flat_map(|row| {
                    pixels[(row + padding) * width + padding
                        ..(row + padding) * width + padding + expected.placement.width as usize]
                        .iter()
                        .copied()
                })
                .collect();
            assert_eq!(coverage, expected.data, "native coverage at x={x}");
            let vertices = &canvas.verts[canvas.verts.len() - 6..];
            let left = vertices
                .iter()
                .map(|vertex| vertex.x)
                .fold(f32::INFINITY, f32::min);
            assert_eq!(
                left,
                expected_origin + expected.placement.left as f32 - GLYPH_PADDING as f32
            );
            recorded.push((left, (*width, *height, pixels.clone())));
        }
        assert_eq!(
            recorded[0].1, recorded[1].1,
            "integer translation must preserve the mask"
        );
        assert_eq!(
            recorded[0].0 + 20.0,
            recorded[1].0,
            "the quad must translate by exactly 20 pixels"
        );
    }
}
