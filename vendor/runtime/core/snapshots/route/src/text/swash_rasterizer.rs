use std::{
    cell::RefCell,
    mem::{size_of, size_of_val},
    rc::Rc,
};

use fnv::FnvHashMap;
use swash::{
    scale::{
        image::{Content, Image},
        outline::Outline,
        Render, ScaleContext, Scaler, Source, StrikeWith,
    },
    zeno::{Format, Mask, Origin, Scratch, Vector},
    CacheKey, FontRef,
};

/// The color sources a glyph is rendered from before falling back to its outline.
const COLOR_SOURCES: [Source; 2] = [Source::ColorOutline(0), Source::ColorBitmap(StrikeWith::BestFit)];

/// Bytes the outline cache may hold, as `entry_bytes` counts them. An entry
/// for a Latin glyph takes a few hundred bytes, so this holds a couple of
/// thousand.
const OUTLINE_CACHE_BUDGET: usize = 1 << 20;

/// Identifies a hinted outline by everything the scaler hints it with.
#[derive(Debug, Hash, PartialEq, Eq)]
struct OutlineKey {
    font: CacheKey,
    glyph_id: u16,
    font_size: u32,
    normalized_coords: Box<[i16]>,
}

/// Renders glyphs with swash.
///
/// Swash hints an outline independently of the subpixel offset it is rasterized
/// at, so the hinted outline of a glyph is kept and reused for its other offsets.
/// Glyphs that render from a color source aren't cached, since those images
/// depend on the offset.
pub(crate) struct SwashRasterizer {
    scale_context: Rc<RefCell<ScaleContext>>,
    scratch: Scratch,
    outlines: FnvHashMap<OutlineKey, Outline>,
    outline_bytes: usize,
    outline_budget: usize,
}

impl SwashRasterizer {
    pub(crate) fn new(scale_context: Rc<RefCell<ScaleContext>>) -> Self {
        Self::with_outline_budget(scale_context, OUTLINE_CACHE_BUDGET)
    }

    fn with_outline_budget(scale_context: Rc<RefCell<ScaleContext>>, outline_budget: usize) -> Self {
        Self {
            scale_context,
            scratch: Scratch::new(),
            outlines: FnvHashMap::default(),
            outline_bytes: 0,
            outline_budget,
        }
    }

    pub(crate) fn scale_context(&self) -> Rc<RefCell<ScaleContext>> {
        Rc::clone(&self.scale_context)
    }

    /// Renders a glyph as `Render` does with color outlines, then color bitmaps,
    /// then outlines as sources, in `Format::Alpha` and offset horizontally by
    /// `subpixel_x`.
    ///
    /// `font` must be the same `FontRef` for every call with the same face, so
    /// that its cache key identifies it.
    pub(crate) fn render(
        &mut self,
        font: FontRef<'_>,
        font_size: f32,
        glyph_id: u16,
        subpixel_x: f32,
        normalized_coords: &[i16],
    ) -> Option<Image> {
        let key = OutlineKey {
            font: font.key,
            glyph_id,
            font_size: font_size.to_bits(),
            normalized_coords: normalized_coords.into(),
        };

        if let Some(outline) = self.outlines.get(&key) {
            return Some(rasterize(outline, &mut self.scratch, subpixel_x));
        }

        let context = Rc::clone(&self.scale_context);
        let mut scale_context = context.borrow_mut();
        let mut scaler = scale_context
            .builder(font)
            .size(font_size)
            .hint(true)
            .normalized_coords(normalized_coords)
            .build();

        self.render_miss(key, glyph_id, subpixel_x, &mut scaler)
    }

    /// Reuses the current run's scaler, constructing it only for an outline miss.
    pub(crate) fn render_with_scaler<'borrow, 'context: 'borrow>(
        &mut self,
        font: FontRef<'_>,
        font_size: f32,
        glyph_id: u16,
        subpixel_x: f32,
        normalized_coords: &[i16],
        make_scaler: impl FnOnce() -> &'borrow mut Scaler<'context>,
    ) -> Option<Image> {
        let key = OutlineKey {
            font: font.key,
            glyph_id,
            font_size: font_size.to_bits(),
            normalized_coords: normalized_coords.into(),
        };
        if let Some(outline) = self.outlines.get(&key) {
            return Some(rasterize(outline, &mut self.scratch, subpixel_x));
        }
        self.render_miss(key, glyph_id, subpixel_x, make_scaler())
    }

    fn render_miss(
        &mut self,
        key: OutlineKey,
        glyph_id: u16,
        subpixel_x: f32,
        scaler: &mut Scaler<'_>,
    ) -> Option<Image> {
        if let Some(image) = Render::new(&COLOR_SOURCES)
            .format(Format::Alpha)
            .offset(Vector::new(subpixel_x, 0.0))
            .render(scaler, glyph_id)
        {
            return Some(image);
        }

        if !scaler.has_outlines() {
            return None;
        }
        let outline = scaler.scale_outline(glyph_id)?;
        let image = rasterize(&outline, &mut self.scratch, subpixel_x);
        self.insert_outline(key, outline);
        Some(image)
    }

    /// Caches an outline, first emptying the cache if the entry wouldn't fit
    /// in what remains of the budget. An entry larger than the whole budget
    /// isn't cached.
    fn insert_outline(&mut self, key: OutlineKey, outline: Outline) {
        let bytes = entry_bytes(&key, &outline);
        if bytes > self.outline_budget {
            return;
        }
        if self.outline_bytes + bytes > self.outline_budget {
            self.outlines.clear();
            self.outline_bytes = 0;
        }
        self.outline_bytes += bytes;
        self.outlines.insert(key, outline);
    }
}

/// Approximate bytes a cache entry holds: its key and outline, the key's
/// coordinates, and the outline's points and verbs. Unused vector capacity,
/// the outline's layer records, the map's spare buckets and allocator
/// overhead aren't counted.
fn entry_bytes(key: &OutlineKey, outline: &Outline) -> usize {
    size_of::<OutlineKey>()
        + size_of::<Outline>()
        + size_of_val(&*key.normalized_coords)
        + size_of_val(outline.points())
        + size_of_val(outline.verbs())
}

/// Rasterizes an outline as `Render` does for `Source::Outline` in `Format::Alpha`.
fn rasterize(outline: &Outline, scratch: &mut Scratch, subpixel_x: f32) -> Image {
    let offset = Vector::new(subpixel_x, 0.0);
    let mut image = Image::new();
    image.placement = Mask::with_scratch(outline.path(), scratch)
        .format(Format::Alpha)
        .origin(Origin::BottomLeft)
        .offset(offset)
        .render_offset(offset)
        .inspect(|format, width, height| image.data.resize(format.buffer_size(width, height), 0))
        .render_into(&mut image.data[..], None);
    image.content = Content::Mask;
    image.source = Source::Outline;
    image
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn run_scaler_matches_native_render_for_outlines_color_invalid_and_variations() {
        for face in faces() {
            let font = FontRef::from_index(&face.data, 0).unwrap();
            for coords in &face.instances {
                for size in [9.0, 16.5, 40.0] {
                    let mut rasterizer = rasterizer();
                    let context = rasterizer.scale_context();
                    let mut reference = ScaleContext::new();
                    for offset in subpixel_offsets() {
                        let mut context_borrow = context.borrow_mut();
                        let mut context_ref = Some(&mut *context_borrow);
                        let mut scaler = None;
                        let mut setups = 0;
                        for glyph_id in face.glyph_ids.clone() {
                            let actual = rasterizer.render_with_scaler(font, size, glyph_id, offset, coords, || {
                                scaler.get_or_insert_with(|| {
                                    setups += 1;
                                    context_ref
                                        .take()
                                        .unwrap()
                                        .builder(font)
                                        .size(size)
                                        .hint(true)
                                        .normalized_coords(coords)
                                        .build()
                                })
                            });
                            let expected = render_uncached(&mut reference, font, size, glyph_id, offset, coords);
                            assert_same_image(
                                actual.as_ref(),
                                expected.as_ref(),
                                &format!("{} {coords:?} {size} glyph {glyph_id} phase {offset}", face.name),
                            );
                        }
                        assert!(setups <= 1, "one setup per run segment");
                    }
                }
            }
        }
    }

    #[test]
    fn run_scaler_is_lazy_and_second_phase_hits_never_request_it() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let mut rasterizer = rasterizer();
        let context = rasterizer.scale_context();
        let glyph_ids = ['A', 'g', 'W'].map(|ch| font.charmap().map(ch));
        {
            let mut context_borrow = context.borrow_mut();
            let mut context_ref = Some(&mut *context_borrow);
            let mut scaler = None;
            let mut setups = 0;
            for glyph_id in glyph_ids {
                rasterizer
                    .render_with_scaler(font, 24.0, glyph_id, 0.0, &[], || {
                        scaler.get_or_insert_with(|| {
                            setups += 1;
                            context_ref.take().unwrap().builder(font).size(24.0).hint(true).build()
                        })
                    })
                    .unwrap();
            }
            assert_eq!(setups, 1);
        }
        for glyph_id in glyph_ids {
            rasterizer
                .render_with_scaler(font, 24.0, glyph_id, 0.3, &[], || {
                    panic!("a cached outline must not request the run scaler")
                })
                .unwrap();
        }
    }

    fn read_font(file: &str) -> Vec<u8> {
        let path = format!("{}/examples/assets/{file}", env!("CARGO_MANIFEST_DIR"));
        std::fs::read(&path).unwrap_or_else(|err| panic!("{path}: {err}"))
    }

    /// The offsets `GlyphAtlas::render_atlas` passes: the fractional part of a
    /// glyph's position, quantized to tenths.
    fn subpixel_offsets() -> impl Iterator<Item = f32> {
        (-9..=10).map(|tenths| tenths as f32 / 10.0)
    }

    /// Renders through swash's `Render` alone, with no outline cache: the
    /// reference `SwashRasterizer::render` must match.
    fn render_uncached(
        context: &mut ScaleContext,
        font: FontRef<'_>,
        font_size: f32,
        glyph_id: u16,
        subpixel_x: f32,
        normalized_coords: &[i16],
    ) -> Option<Image> {
        let mut scaler = context
            .builder(font)
            .size(font_size)
            .hint(true)
            .normalized_coords(normalized_coords)
            .build();
        Render::new(&[
            Source::ColorOutline(0),
            Source::ColorBitmap(StrikeWith::BestFit),
            Source::Outline,
        ])
        .format(Format::Alpha)
        .offset(Vector::new(subpixel_x, 0.0))
        .render(&mut scaler, glyph_id)
    }

    /// What caching the glyph's hinted outline charges against the budget.
    fn cached_bytes(font: FontRef<'_>, font_size: f32, glyph_id: u16, normalized_coords: &[i16]) -> usize {
        let mut context = ScaleContext::new();
        let mut scaler = context
            .builder(font)
            .size(font_size)
            .hint(true)
            .normalized_coords(normalized_coords)
            .build();
        let key = OutlineKey {
            font: font.key,
            glyph_id,
            font_size: font_size.to_bits(),
            normalized_coords: normalized_coords.into(),
        };
        entry_bytes(&key, &scaler.scale_outline(glyph_id).unwrap())
    }

    fn placement(image: &Image) -> (i32, i32, u32, u32) {
        let p = image.placement;
        (p.left, p.top, p.width, p.height)
    }

    fn rasterizer() -> SwashRasterizer {
        SwashRasterizer::new(Rc::default())
    }

    fn assert_same_image(actual: Option<&Image>, expected: Option<&Image>, case: &str) {
        let (actual, expected) = match (actual, expected) {
            (Some(actual), Some(expected)) => (actual, expected),
            (None, None) => return,
            (actual, expected) => panic!("{case}: rendered {}, expected {}", actual.is_some(), expected.is_some()),
        };
        assert_eq!(placement(actual), placement(expected), "{case}: placement");
        assert_eq!(actual.content, expected.content, "{case}: content");
        assert_eq!(
            format!("{:?}", actual.source),
            format!("{:?}", expected.source),
            "{case}: source"
        );
        assert!(actual.data == expected.data, "{case}: coverage differs");
    }

    struct Face {
        name: &'static str,
        data: Vec<u8>,
        glyph_ids: std::ops::Range<u16>,
        /// Normalized coordinates to render at; the face's default instance is empty.
        instances: Vec<Vec<i16>>,
    }

    fn faces() -> Vec<Face> {
        let roboto = read_font("RobotoFlex-VariableFont.ttf");
        let axis_count = FontRef::from_index(&roboto, 0).unwrap().variations().len();
        // F2Dot14: halfway along the first axis, a quarter back along the last.
        let mut roboto_instance = vec![0; axis_count];
        roboto_instance[0] = 0x2000;
        roboto_instance[axis_count - 1] = -0x1000;

        vec![
            Face {
                name: "Roboto Flex",
                data: roboto,
                glyph_ids: 0..80,
                instances: vec![Vec::new(), roboto_instance],
            },
            Face {
                name: "Amiri",
                data: read_font("amiri-regular.ttf"),
                glyph_ids: 0..80,
                instances: vec![Vec::new()],
            },
            Face {
                name: "Entypo",
                data: read_font("entypo.ttf"),
                glyph_ids: 0..40,
                instances: vec![Vec::new()],
            },
            Face {
                name: "Bungee Color subset",
                data: read_font("BungeeColor-Subset.ttf"),
                // Glyph 9 is past the last glyph, 8.
                glyph_ids: 0..10,
                instances: vec![Vec::new()],
            },
        ]
    }

    // One rasterizer serves every face, instance and size, so an outline cached
    // under a key that left out the face, the size or the coordinates, or that
    // rounded the size, would be reused for another glyph and fail the
    // comparison.
    #[test]
    fn renders_like_swash_render_at_every_subpixel_offset() {
        let faces = faces();
        let mut rasterizer = rasterizer();
        let mut context = ScaleContext::new();

        for face in &faces {
            let font = FontRef::from_index(&face.data, 0).unwrap();
            for coords in &face.instances {
                for font_size in [9.0, 12.0, 16.1, 16.5, 16.9, 40.0] {
                    for glyph_id in face.glyph_ids.clone() {
                        for subpixel_x in subpixel_offsets() {
                            let actual = rasterizer.render(font, font_size, glyph_id, subpixel_x, coords);
                            let expected = render_uncached(&mut context, font, font_size, glyph_id, subpixel_x, coords);
                            let case = format!(
                                "{} {coords:?} glyph {glyph_id} at {font_size}px, offset {subpixel_x}",
                                face.name
                            );
                            assert_same_image(actual.as_ref(), expected.as_ref(), &case);
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn color_glyphs_render_from_color_sources_and_are_not_cached() {
        // BungeeColor-Subset.ttf is Bungee Color Regular, Version 1.000, from
        // google/fonts ofl/bungeecolor, SHA-256
        // cf21a786e54f43694f4edbb51a38f81331a4c3414217c524c8cb2d091aa7fd63,
        // subset with fontTools 4.59.1:
        //   pyftsubset BungeeColor-Regular.ttf --unicodes=U+0020,U+0041 \
        //     --layout-features='' --drop-tables+=DSIG,GSUB,GPOS --name-IDs='*'
        // Glyph 2 is A, whose COLR layers are glyphs 7 and 8.
        const COLOR_A: u16 = 2;
        const LAYER_OF_A: u16 = 7;

        let data = read_font("BungeeColor-Subset.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let mut rasterizer = rasterizer();

        let color = rasterizer.render(font, 24.0, COLOR_A, 0.3, &[]).unwrap();
        assert_eq!(color.content, Content::Color);
        assert!(matches!(color.source, Source::ColorOutline(0)));
        assert!(rasterizer.outlines.is_empty());

        // A layer glyph has no color layers of its own, so even in a color
        // face it renders from, and caches, its plain outline.
        let layer = rasterizer.render(font, 24.0, LAYER_OF_A, 0.3, &[]).unwrap();
        assert_eq!(layer.content, Content::Mask);
        assert!(matches!(layer.source, Source::Outline));
        assert_eq!(rasterizer.outlines.len(), 1);
    }

    #[test]
    fn subpixel_offsets_reuse_the_cached_outline() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let glyph_id = font.charmap().map('g');
        let mut rasterizer = rasterizer();

        let first = rasterizer.render(font, 16.0, glyph_id, 0.0, &[]).unwrap();
        assert!(first.data.iter().any(|&coverage| coverage > 0));

        // Swap the cached outline for an empty one: renders at every offset must
        // then cover nothing, which they only do if they skip hinting.
        assert_eq!(rasterizer.outlines.len(), 1);
        for cached in rasterizer.outlines.values_mut() {
            *cached = Outline::new();
        }

        for subpixel_x in subpixel_offsets() {
            let image = rasterizer.render(font, 16.0, glyph_id, subpixel_x, &[]).unwrap();
            assert!(image.data.iter().all(|&coverage| coverage == 0), "offset {subpixel_x}");
        }
    }

    #[test]
    fn cache_empties_when_an_outline_would_exceed_the_budget() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let [a, b, c] = ['a', 'b', 'c'].map(|ch| font.charmap().map(ch));
        let [a_bytes, b_bytes, c_bytes] = [a, b, c].map(|id| cached_bytes(font, 16.0, id, &[]));

        let mut rasterizer = SwashRasterizer::with_outline_budget(Rc::default(), a_bytes + b_bytes);
        rasterizer.render(font, 16.0, a, 0.0, &[]);
        rasterizer.render(font, 16.0, b, 0.0, &[]);
        assert_eq!(rasterizer.outlines.len(), 2, "a and b fill the budget exactly");
        assert_eq!(rasterizer.outline_bytes, a_bytes + b_bytes);

        rasterizer.render(font, 16.0, c, 0.0, &[]);
        assert_eq!(
            rasterizer.outlines.len(),
            1,
            "c doesn't fit, so the cache empties first"
        );
        assert_eq!(rasterizer.outline_bytes, c_bytes);
    }

    // A whitespace glyph's outline has no points or verbs, but its entry still
    // takes memory, so it must count toward the budget like any other.
    #[test]
    fn empty_outlines_count_toward_the_budget() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let space = font.charmap().map(' ');
        let mut coords = vec![0; font.variations().len()];
        let space_bytes = cached_bytes(font, 16.0, space, &coords);
        assert!(space_bytes > 0);
        assert_eq!(
            space_bytes - cached_bytes(font, 16.0, space, &[]),
            size_of_val(&coords[..]),
            "coordinates are charged by their length"
        );

        let mut rasterizer = SwashRasterizer::with_outline_budget(Rc::default(), 4 * space_bytes);
        let mut context = ScaleContext::new();
        for first_axis in 0..20 {
            coords[0] = first_axis * 0x100;
            let actual = rasterizer.render(font, 16.0, space, 0.0, &coords);
            let expected = render_uncached(&mut context, font, 16.0, space, 0.0, &coords);
            assert_same_image(actual.as_ref(), expected.as_ref(), &format!("space at {coords:?}"));
            assert!(rasterizer.outlines.len() <= 4, "{} entries", rasterizer.outlines.len());
            assert_eq!(rasterizer.outline_bytes, rasterizer.outlines.len() * space_bytes);
        }
    }

    #[test]
    fn outlines_larger_than_the_budget_are_not_cached() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let glyph_id = font.charmap().map('g');

        let mut rasterizer = SwashRasterizer::with_outline_budget(Rc::default(), 1);
        let image = rasterizer.render(font, 16.0, glyph_id, 0.0, &[]).unwrap();
        assert!(image.placement.width > 0);
        assert!(rasterizer.outlines.is_empty());
        assert_eq!(rasterizer.outline_bytes, 0);
    }
}
