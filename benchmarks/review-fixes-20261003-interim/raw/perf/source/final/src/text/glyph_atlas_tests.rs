#[cfg(not(feature = "textlayout"))]
use crate::ErrorKind;
use crate::{renderer, Canvas, Color, FontId, Paint, PositionedGlyph, RecordingRenderer};

#[test]
fn run_scaler_releases_shared_context_at_empty_and_invalid_fallback_boundaries() {
    let data = include_bytes!("../../examples/assets/RobotoFlex-VariableFont.ttf");
    let font_ref = swash::FontRef::from_index(data, 0).unwrap();
    let mut canvas = Canvas::new(RecordingRenderer::default()).unwrap();
    canvas.set_size(400, 200, 1.0);
    let font_id = canvas.text_context.borrow_mut().add_font_mem(data).unwrap();
    let ids = ['A', ' ', 'g'].map(|ch| font_ref.charmap().map(ch));
    let paint = Paint::color(Color::black()).with_font_size(24.0);
    for phase in [0.0, 0.3] {
        let glyphs = [ids[0], u16::MAX, ids[1], ids[2]]
            .into_iter()
            .enumerate()
            .map(|(index, glyph_id)| PositionedGlyph {
                x: 10.0 + index as f32 * 30.0 + phase,
                y: 70.0,
                glyph_id,
            });
        canvas.fill_glyph_run(font_id, &[], glyphs, &paint).unwrap();
    }
    let atlas = canvas.glyph_atlas.rendered_glyphs.borrow();
    // The existing Swash-only fallback represents an empty outline as an
    // empty padded atlas glyph, whereas textlayout has no generic space path.
    let expected_rendered = if cfg!(feature = "textlayout") { 4 } else { 6 };
    assert_eq!(
        atlas.values().filter(|glyph| glyph.is_some()).count(),
        expected_rendered
    );
    assert_eq!(
        atlas.values().filter(|glyph| glyph.is_none()).count(),
        8 - expected_rendered
    );
}

#[test]
fn swash_atlas_fills_defer_generic_paths_but_direct_and_strokes_keep_them() {
    let data = include_bytes!("../../examples/assets/RobotoFlex-VariableFont.ttf");
    let glyph_id = swash::FontRef::from_index(data, 0).unwrap().charmap().map('A');
    let glyphs = || {
        [PositionedGlyph {
            x: 10.3,
            y: 70.0,
            glyph_id,
        }]
    };
    for route in 0..4 {
        let mut canvas = Canvas::new(RecordingRenderer::default()).unwrap();
        canvas.set_size(300, 200, 1.0);
        let font_id = canvas.text_context.borrow_mut().add_font_mem(data).unwrap();
        let paint = Paint::color(Color::black()).with_font_size(if route == 3 { 96.0 } else { 24.0 });
        if route == 2 {
            canvas.rotate(0.2);
        }
        if route == 1 {
            canvas.stroke_glyph_run(font_id, &[], glyphs(), &paint).unwrap();
        } else {
            canvas.fill_glyph_run(font_id, &[], glyphs(), &paint).unwrap();
        }
        let text_context = canvas.text_context.borrow();
        let paths = text_context.font(font_id).unwrap().glyph_cache_len();
        assert_eq!(paths, usize::from(route != 0), "route {route}");
        assert!(!canvas.commands.is_empty(), "route {route} draws");
    }
}

#[test]
fn swash_prepass_bypass_routes_colr_and_plain_layer_glyphs_to_their_atlas_draws() {
    let mut canvas = Canvas::new(RecordingRenderer::default()).unwrap();
    canvas.set_size(300, 200, 1.0);
    let font_id = canvas
        .text_context
        .borrow_mut()
        .add_font_mem(include_bytes!("../../examples/assets/BungeeColor-Subset.ttf"))
        .unwrap();
    let paint = Paint::color(Color::black()).with_font_size(24.0);
    let glyphs = [2, 7, u16::MAX]
        .into_iter()
        .enumerate()
        .map(|(index, glyph_id)| PositionedGlyph {
            x: 10.0 + index as f32 * 40.0,
            y: 70.0,
            glyph_id,
        });
    canvas.fill_glyph_run(font_id, &[], glyphs, &paint).unwrap();
    let atlas = canvas.glyph_atlas.rendered_glyphs.borrow();
    assert_eq!(atlas.values().filter(|glyph| glyph.is_some()).count(), 2);
    assert_eq!(atlas.values().filter(|glyph| glyph.is_none()).count(), 1);
    let commands = &canvas.commands;
    let mask_draws = commands
        .iter()
        .filter(|command| match &command.cmd_type {
            renderer::CommandType::Triangles { params } => params.glyph_texture_type == 1,
            _ => false,
        })
        .count();
    let color_draws = commands
        .iter()
        .filter(|command| match &command.cmd_type {
            renderer::CommandType::Triangles { params } => params.glyph_texture_type == 2,
            _ => false,
        })
        .count();
    assert_eq!(mask_draws, 1);
    assert_eq!(color_draws, 1);
    let text_context = canvas.text_context.borrow();
    assert_eq!(text_context.font(font_id).unwrap().glyph_cache_len(), 0);
}

// Add a real PNG strike to the existing COLR fixture. The synthetic sfnt table
// assembly is confined to this test; both production classifiers use the
// existing font APIs. Glyph 7 has a glyf outline too, so source precedence is
// exercised rather than treating bitmap presence as the absence of an outline.
fn mixed_colr_png_font() -> Vec<u8> {
    let original = include_bytes!("../../examples/assets/BungeeColor-Subset.ttf");
    let glyph_count = swash::FontRef::from_index(original, 0)
        .unwrap()
        .metrics(&[])
        .glyph_count;
    let bitmap_glyph = 7;
    assert!(glyph_count > bitmap_glyph);

    let bitmap = ::image::RgbaImage::from_pixel(24, 24, ::image::Rgba([255, 0, 64, 255]));
    let mut png = std::io::Cursor::new(Vec::new());
    bitmap.write_to(&mut png, ::image::ImageFormat::Png).unwrap();
    let png = png.into_inner();
    let mut payload = Vec::new();
    payload.extend_from_slice(&0i16.to_be_bytes()); // originOffsetX
    payload.extend_from_slice(&0i16.to_be_bytes()); // originOffsetY
    payload.extend_from_slice(b"png ");
    payload.extend_from_slice(&png);

    let mut sbix = Vec::new();
    sbix.extend_from_slice(&1u16.to_be_bytes()); // version
    sbix.extend_from_slice(&1u16.to_be_bytes()); // required flag bit 0
    sbix.extend_from_slice(&1u32.to_be_bytes()); // one strike
    sbix.extend_from_slice(&12u32.to_be_bytes()); // strike offset
    sbix.extend_from_slice(&24u16.to_be_bytes()); // pixels per em
    sbix.extend_from_slice(&72u16.to_be_bytes()); // resolution
    let payload_start = 4 + 4 * (u32::from(glyph_count) + 1);
    for glyph in 0..=glyph_count {
        let offset = payload_start + if glyph > bitmap_glyph { payload.len() as u32 } else { 0 };
        sbix.extend_from_slice(&offset.to_be_bytes());
    }
    sbix.extend_from_slice(&payload);

    let u16_at = |offset| u16::from_be_bytes(original[offset..offset + 2].try_into().unwrap());
    let u32_at = |offset| u32::from_be_bytes(original[offset..offset + 4].try_into().unwrap()) as usize;
    let mut tables = Vec::new();
    for index in 0..usize::from(u16_at(4)) {
        let record = 12 + index * 16;
        let tag: [u8; 4] = original[record..record + 4].try_into().unwrap();
        assert_ne!(&tag, b"sbix");
        let start = u32_at(record + 8);
        let length = u32_at(record + 12);
        tables.push((tag, original[start..start + length].to_vec()));
    }
    tables.push((*b"sbix", sbix));
    tables.sort_by_key(|(tag, _)| *tag);

    let table_count = tables.len() as u16;
    let entry_selector = table_count.ilog2() as u16;
    let search_range = (1u16 << entry_selector) * 16;
    let mut font = original[..4].to_vec();
    font.extend_from_slice(&table_count.to_be_bytes());
    font.extend_from_slice(&search_range.to_be_bytes());
    font.extend_from_slice(&entry_selector.to_be_bytes());
    font.extend_from_slice(&(table_count * 16 - search_range).to_be_bytes());
    let body_start = 12 + tables.len() * 16;
    let mut body = Vec::new();
    for (tag, table) in tables {
        font.extend_from_slice(&tag);
        // As in the other minimal sfnt fixtures, parsers do not verify checksums.
        font.extend_from_slice(&0u32.to_be_bytes());
        font.extend_from_slice(&((body_start + body.len()) as u32).to_be_bytes());
        font.extend_from_slice(&(table.len() as u32).to_be_bytes());
        body.extend_from_slice(&table);
        while !body.len().is_multiple_of(4) {
            body.push(0);
        }
    }
    font.extend_from_slice(&body);
    font
}

#[cfg(feature = "textlayout")]
#[test]
fn swash_prepass_preserves_overlapping_colr_then_png_batches_on_cold_and_warm_atlas() {
    let data = mixed_colr_png_font();
    let face = ttf_parser::Face::parse(&data, 0).unwrap();
    let bitmap = face.glyph_raster_image(ttf_parser::GlyphId(7), u16::MAX).unwrap();
    assert_eq!(bitmap.format, ttf_parser::RasterImageFormat::PNG);
    assert_eq!((bitmap.width, bitmap.height), (24, 24));
    assert!(face.glyph_raster_image(ttf_parser::GlyphId(2), u16::MAX).is_none());

    let prepare = || {
        let mut canvas = Canvas::new(RecordingRenderer::default()).unwrap();
        canvas.set_size(100, 100, 1.0);
        let font_id = canvas.text_context.borrow_mut().add_font_mem(&data).unwrap();
        (canvas, font_id)
    };
    let paint = Paint::color(Color::black()).with_font_size(24.0);
    let glyph = |glyph_id| PositionedGlyph {
        x: 20.0,
        y: 70.0,
        glyph_id,
    };
    let signature = |canvas: &Canvas<RecordingRenderer>| {
        canvas
            .commands
            .iter()
            .filter_map(|command| match &command.cmd_type {
                renderer::CommandType::Triangles { params } if params.glyph_texture_type == 2 => {
                    let (start, count) = command.triangles_verts.unwrap();
                    Some(canvas.verts[start..start + count].to_vec())
                }
                _ => None,
            })
            .collect::<Vec<_>>()
    };
    let (mut reference, reference_font) = prepare();
    // The existing classifier puts the COLR glyph in the first atlas batch and
    // the generic PNG in the second, even if the caller supplies PNG first.
    reference
        .fill_glyph_run(reference_font, &[], [glyph(2)], &paint)
        .unwrap();
    reference
        .fill_glyph_run(reference_font, &[], [glyph(7)], &paint)
        .unwrap();
    let expected = signature(&reference);
    assert_eq!(expected.len(), 2, "fixture must rasterize both color sources");
    assert!(expected.iter().all(|vertices| vertices.len() == 6));
    let bounds = |vertices: &[renderer::Vertex]| {
        vertices.iter().fold(
            (f32::INFINITY, f32::INFINITY, f32::NEG_INFINITY, f32::NEG_INFINITY),
            |(x0, y0, x1, y1), v| (x0.min(v.x), y0.min(v.y), x1.max(v.x), y1.max(v.y)),
        )
    };
    let (ax0, ay0, ax1, ay1) = bounds(&expected[0]);
    let (bx0, by0, bx1, by1) = bounds(&expected[1]);
    assert!(
        ax0.max(bx0) < ax1.min(bx1) && ay0.max(by0) < ay1.min(by1),
        "the two color quads overlap, so their painter order matters"
    );

    let (mut canvas, font_id) = prepare();
    for warm in [false, true] {
        canvas.commands.clear();
        canvas.verts.clear();
        canvas
            .fill_glyph_run(font_id, &[], [glyph(7), glyph(2)], &paint)
            .unwrap();
        assert_eq!(signature(&canvas), expected, "warm atlas: {warm}");
        assert_eq!(
            canvas.glyph_atlas.glyph_textures.borrow().len(),
            1,
            "both sources share a texture; combining batches would reverse their painter order"
        );
        assert_eq!(canvas.text_context.borrow().font(font_id).unwrap().glyph_cache_len(), 0);
    }
}

mod glyph_atlas_regressions {
    use super::*;
    #[cfg(not(feature = "textlayout"))]
    use crate::text::glyph_atlas_fallback_tests::{assert_target_and_following_clear, select_target};

    fn canvas(data: &[u8]) -> (Canvas<RecordingRenderer>, FontId) {
        let mut canvas = Canvas::new(RecordingRenderer::default()).unwrap();
        canvas.set_size(400, 200, 1.0);
        let font = canvas.text_context.borrow_mut().add_font_mem(data).unwrap();
        (canvas, font)
    }

    fn glyph(glyph_id: u16, x: f32) -> PositionedGlyph {
        PositionedGlyph { glyph_id, x, y: 70.0 }
    }

    #[cfg(feature = "textlayout")]
    #[test]
    fn first_rotated_and_large_png_draws_initialize_the_ephemeral_atlas() {
        let data = mixed_colr_png_font();
        for (rotation, size) in [(0.2, 24.0), (0.0, 96.0)] {
            let (mut canvas, font) = canvas(&data);
            canvas.rotate(rotation);
            canvas
                .fill_glyph_run(
                    font,
                    &[],
                    [glyph(7, 20.0)],
                    &Paint::color(Color::black()).with_font_size(size),
                )
                .unwrap();
            assert!(canvas.ephemeral_glyph_atlas.is_some());
            assert!(canvas.commands.iter().any(|command| matches!(
                &command.cmd_type,
                renderer::CommandType::Triangles { params } if params.glyph_texture_type == 2
            )));
        }
    }

    fn assert_native_draw(
        canvas: &mut Canvas<RecordingRenderer>,
        font: FontId,
        id: u16,
        x: f32,
        origin: f32,
        expected: &swash::scale::image::Image,
    ) {
        let padding = super::super::GLYPH_PADDING as usize;
        let start = canvas.verts.len();
        canvas
            .fill_glyph_run(
                font,
                &[],
                [glyph(id, x)],
                &Paint::color(Color::black()).with_font_size(24.0),
            )
            .unwrap();
        let (width, height, pixels) = canvas.renderer.image_masks.last().unwrap();
        assert_eq!(
            (*width, *height),
            (
                expected.placement.width as usize + 2 * padding,
                expected.placement.height as usize + 2 * padding
            )
        );
        let mask = (0..expected.placement.height as usize)
            .flat_map(|y| {
                pixels[(y + padding) * width + padding
                    ..(y + padding) * width + padding + expected.placement.width as usize]
                    .iter()
                    .copied()
            })
            .collect::<Vec<_>>();
        let expected_mask = if expected.content == swash::scale::image::Content::Color {
            expected.data.chunks_exact(4).map(|pixel| pixel[0]).collect::<Vec<_>>()
        } else {
            expected.data.clone()
        };
        assert_eq!(mask, expected_mask, "native coverage at x={x}");
        let vertices = &canvas.verts[start..];
        assert_eq!(vertices.len(), 6);
        assert_eq!(
            vertices.iter().map(|vertex| vertex.x).fold(f32::INFINITY, f32::min),
            origin + expected.placement.left as f32 - padding as f32,
            "native placement at x={x}"
        );
        assert_eq!(
            vertices.iter().map(|vertex| vertex.y).fold(f32::INFINITY, f32::min),
            70.0 - expected.placement.top as f32 - padding as f32
        );
    }

    #[test]
    fn native_subpixel_masks_reuse_integer_translations_in_either_order() {
        use swash::{
            scale::{Render, ScaleContext, Source},
            zeno::{Format, Vector},
        };
        let data = include_bytes!("../../examples/assets/RobotoFlex-VariableFont.ttf");
        let face = swash::FontRef::from_index(data, 0).unwrap();
        let id = face.charmap().map('g');
        let mut native_context = ScaleContext::new();
        let mut scaler = native_context.builder(face).size(24.0).hint(true).build();
        let integer = Render::new(&[Source::Outline])
            .format(Format::Alpha)
            .render(&mut scaler, id)
            .unwrap();
        // Explicit origins and offsets keep the oracle independent of the binning formula.
        for (phase, positions) in [
            (0.6, [(-0.4, -1.0), (19.6, 19.0)]),
            (0.8, [(-0.25, -1.0), (19.75, 19.0)]),
            (0.0, [(-0.04, 0.0), (19.96, 20.0)]),
        ] {
            let expected = Render::new(&[Source::Outline])
                .format(Format::Alpha)
                .offset(Vector::new(phase, 0.0))
                .render(&mut scaler, id)
                .unwrap();
            for reverse in [false, true] {
                let mut positions = positions;
                if reverse {
                    positions.reverse();
                }
                let (mut canvas, font) = canvas(data);
                canvas.renderer.record_image_masks = true;
                for _ in 0..2 {
                    for (x, origin) in positions {
                        assert_native_draw(&mut canvas, font, id, x, origin, &expected);
                    }
                    assert_eq!(canvas.renderer.image_masks.len(), 1, "translated masks upload once");
                    assert_eq!(canvas.glyph_atlas.rendered_glyphs.borrow().len(), 1);
                }
                for x in [0.0, 20.0] {
                    assert_native_draw(&mut canvas, font, id, x, x, &integer);
                }
                let distinct_phases = if phase == 0.0 { 1 } else { 2 };
                assert_eq!(canvas.renderer.image_masks.len(), distinct_phases);
                assert_eq!(canvas.glyph_atlas.rendered_glyphs.borrow().len(), distinct_phases);
            }
        }
    }

    #[test]
    fn native_color_outlines_use_subpixel_origins_on_cold_and_warm_draws() {
        use swash::{
            scale::{Render, ScaleContext, Source},
            zeno::Vector,
        };

        let data = include_bytes!("../../examples/assets/BungeeColor-Subset.ttf");
        let face = swash::FontRef::from_index(data, 0).unwrap();
        let mut context = ScaleContext::new();
        let mut scaler = context.builder(face).size(24.0).hint(true).build();
        for reverse in [false, true] {
            let mut cases = [(-0.4, -1.0, 0.6), (0.95, 1.0, 0.0)];
            if reverse {
                cases.reverse();
            }
            let (mut canvas, font) = canvas(data);
            canvas.renderer.record_image_masks = true;
            for (x, origin, phase) in cases {
                let expected = Render::new(&[Source::ColorOutline(0)])
                    .offset(Vector::new(phase, 0.0))
                    .render(&mut scaler, 2)
                    .unwrap();
                assert!(matches!(expected.source, Source::ColorOutline(0)));
                for _ in 0..2 {
                    assert_native_draw(&mut canvas, font, 2, x, origin, &expected);
                }
            }
            assert_eq!(
                canvas.renderer.image_masks.len(),
                2,
                "each color-outline phase uploads once"
            );
            assert_eq!(canvas.glyph_atlas.rendered_glyphs.borrow().len(), 2);
        }
    }

    #[test]
    fn native_color_bitmaps_preserve_truncated_origins_on_cold_and_warm_draws() {
        use swash::scale::{Render, ScaleContext, Source, StrikeWith};

        let data = mixed_colr_png_font();
        let face = swash::FontRef::from_index(&data, 0).unwrap();
        let mut context = ScaleContext::new();
        let mut scaler = context.builder(face).size(24.0).hint(true).build();
        let expected = Render::new(&[Source::ColorBitmap(StrikeWith::BestFit)])
            .render(&mut scaler, 7)
            .unwrap();
        assert!(matches!(expected.source, Source::ColorBitmap(_)));
        for reverse in [false, true] {
            let mut positions = [(-0.4, 0.0), (-0.95, 0.0), (0.95, 0.0), (19.95, 19.0), (-1.05, -1.0)];
            if reverse {
                positions.reverse();
            }
            let (mut canvas, font) = canvas(&data);
            canvas.renderer.record_image_masks = true;
            for (x, origin) in positions {
                assert_native_draw(&mut canvas, font, 7, x, origin, &expected);
            }
            let uploads = canvas.renderer.image_masks.len();
            for (x, origin) in positions {
                assert_native_draw(&mut canvas, font, 7, x, origin, &expected);
            }
            assert_eq!(
                canvas.renderer.image_masks.len(),
                uploads,
                "warm bitmap draws reuse the atlas"
            );
        }
    }

    #[cfg(not(feature = "textlayout"))]
    #[test]
    fn fallback_then_native_upload_error_restores_screen_image_and_layer_targets() {
        let data = include_bytes!("../../examples/assets/RobotoFlex-VariableFont.ttf");
        let face = swash::FontRef::from_index(data, 0).unwrap();
        for kind in 0..3 {
            let (mut canvas, font) = canvas(data);
            let initial = select_target(&mut canvas, kind);
            canvas.commands.clear();
            canvas.renderer.fail_image_updates = true;
            let result = canvas.fill_glyph_run(
                font,
                &[],
                [
                    glyph(face.charmap().map(' '), 10.0),
                    glyph(face.charmap().map('A'), 30.0),
                ],
                &Paint::color(Color::black()).with_font_size(24.0),
            );
            assert!(matches!(result, Err(ErrorKind::UnknownError)), "{result:?}");
            assert_target_and_following_clear(&mut canvas, initial);
        }
    }
}
