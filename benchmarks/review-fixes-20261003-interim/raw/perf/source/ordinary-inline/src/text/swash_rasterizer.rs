use std::{
    cell::RefCell,
    mem::{size_of, size_of_val},
    ops::Range,
    rc::Rc,
};

use fnv::FnvHashMap;
use swash::{
    scale::{
        image::{Content, Image},
        outline::Outline,
        Render, ScaleContext, Scaler, Source, StrikeWith,
    },
    zeno::{Format, Mask, Origin, Point, Scratch, Vector, Verb},
    CacheKey, FontRef,
};

const COLOR_SOURCES: [Source; 2] = [Source::ColorOutline(0), Source::ColorBitmap(StrikeWith::BestFit)];
const OUTLINE_CACHE_BUDGET: usize = 1 << 20;

#[derive(Debug, Hash, PartialEq, Eq)]
struct OutlineKey {
    font: CacheKey,
    glyph_id: u16,
    font_size: u32,
    normalized_coords: Box<[i16]>,
}

struct CachedPath {
    points: Range<usize>,
    verbs: Range<usize>,
}

/// Keeps cache identity and native scaler settings together for one run segment.
/// The scaler is built lazily from these private, immutable settings on a miss.
pub(super) struct HintedGlyphRun<'a> {
    font: FontRef<'a>,
    font_size: f32,
    normalized_coords: &'a [i16],
    context: Option<&'a mut ScaleContext>,
    scaler: Option<Scaler<'a>>,
}

impl<'a> HintedGlyphRun<'a> {
    pub(super) fn new(
        context: &'a mut ScaleContext,
        font: FontRef<'a>,
        font_size: f32,
        normalized_coords: &'a [i16],
    ) -> Self {
        Self {
            font,
            font_size,
            normalized_coords,
            context: Some(context),
            scaler: None,
        }
    }

    fn outline_key(&self, glyph_id: u16) -> OutlineKey {
        OutlineKey {
            font: self.font.key,
            glyph_id,
            font_size: self.font_size.to_bits(),
            normalized_coords: self.normalized_coords.into(),
        }
    }

    fn scaler(&mut self) -> &mut Scaler<'a> {
        self.scaler.get_or_insert_with(|| {
            self.context
                .take()
                .expect("a run initializes its scaler once")
                .builder(self.font)
                .size(self.font_size)
                .hint(true)
                .normalized_coords(self.normalized_coords)
                .build()
        })
    }
}

/// Renders glyphs using Swash, retaining hinted geometry in compact arenas.
/// Swash hints outlines before applying the raster offset, so each outline can
/// serve every subpixel position. Color sources bypass the outline cache.
///
/// The 1 MiB soft budget counts own arena capacities, logical metadata and
/// logical native outline scratch. Swash spare capacity, private layer buffers,
/// map buckets and allocator overhead are outside this accounting.
pub(crate) struct SwashRasterizer {
    scale_context: Rc<RefCell<ScaleContext>>,
    scratch: Scratch,
    scaled_outline: Outline,
    outlines: FnvHashMap<OutlineKey, CachedPath>,
    points: Vec<Point>,
    verbs: Vec<Verb>,
    metadata_bytes: usize,
    outline_bytes: usize,
    outline_budget: usize,
    scratch_points_high_water: usize,
    scratch_verbs_high_water: usize,
}

impl SwashRasterizer {
    pub(crate) fn new(scale_context: Rc<RefCell<ScaleContext>>) -> Self {
        Self::with_outline_budget(scale_context, OUTLINE_CACHE_BUDGET)
    }

    fn with_outline_budget(scale_context: Rc<RefCell<ScaleContext>>, outline_budget: usize) -> Self {
        Self {
            scale_context,
            scratch: Scratch::new(),
            scaled_outline: Outline::new(),
            outlines: FnvHashMap::default(),
            points: Vec::new(),
            verbs: Vec::new(),
            metadata_bytes: 0,
            outline_bytes: 0,
            outline_budget,
            scratch_points_high_water: 0,
            scratch_verbs_high_water: 0,
        }
    }

    pub(crate) fn scale_context(&self) -> Rc<RefCell<ScaleContext>> {
        Rc::clone(&self.scale_context)
    }

    /// Exercises the production run path for one glyph in cache tests.
    #[cfg(test)]
    fn render(
        &mut self,
        font: FontRef<'_>,
        font_size: f32,
        glyph_id: u16,
        subpixel_x: f32,
        normalized_coords: &[i16],
    ) -> Option<Image> {
        let context = Rc::clone(&self.scale_context);
        let mut context_borrow = context.borrow_mut();
        let mut run = HintedGlyphRun::new(&mut context_borrow, font, font_size, normalized_coords);
        self.render_glyph(&mut run, glyph_id, subpixel_x)
    }

    /// Reuses the native run scaler only when the eager arena cache misses.
    pub(super) fn render_glyph(
        &mut self,
        run: &mut HintedGlyphRun<'_>,
        glyph_id: u16,
        subpixel_x: f32,
    ) -> Option<Image> {
        let key = run.outline_key(glyph_id);
        if let Some(path) = self.outlines.get(&key) {
            return Some(rasterize_path(
                &self.points[path.points.clone()],
                &self.verbs[path.verbs.clone()],
                &mut self.scratch,
                subpixel_x,
            ));
        }
        let scaler = run.scaler();
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
        let success = scaler.scale_outline_into(glyph_id, &mut self.scaled_outline);
        // Include failed draws too: a failed pen can already have grown buffers.
        self.observe_scratch_lengths();
        if !success {
            self.enforce_retained_budget();
            return None;
        }
        let image = rasterize_path(
            self.scaled_outline.points(),
            self.scaled_outline.verbs(),
            &mut self.scratch,
            subpixel_x,
        );
        self.insert_scaled_outline(key);
        self.enforce_retained_budget();
        Some(image)
    }

    // This is a soft accounting budget, not a bound on total heap retention.
    // Swash exposes outline lengths, not capacities or private layer storage.
    // Charge a high-water logical point/verb count plus the Outline value;
    // own arena capacities and key/range metadata are counted separately.
    fn observe_scratch_lengths(&mut self) {
        self.scratch_points_high_water = self.scratch_points_high_water.max(self.scaled_outline.points().len());
        self.scratch_verbs_high_water = self.scratch_verbs_high_water.max(self.scaled_outline.verbs().len());
        self.refresh_bytes();
    }

    fn scratch_logical_bytes(&self) -> usize {
        size_of::<Outline>()
            + self.scratch_points_high_water * size_of::<Point>()
            + self.scratch_verbs_high_water * size_of::<Verb>()
    }

    fn refresh_bytes(&mut self) {
        self.outline_bytes = self.metadata_bytes
            + self.points.capacity() * size_of::<Point>()
            + self.verbs.capacity() * size_of::<Verb>()
            + self.scratch_logical_bytes();
    }

    fn clear_cached_paths(&mut self) {
        self.outlines.clear();
        self.points.clear();
        self.verbs.clear();
        self.metadata_bytes = 0;
        self.refresh_bytes();
    }

    fn enforce_retained_budget(&mut self) {
        self.refresh_bytes();
        if self.outline_bytes > self.outline_budget {
            self.clear_cached_paths();
        }
        if self.outline_bytes > self.outline_budget {
            // An oversized glyph may use temporary working memory, but must
            // not make the retained scratch high-water state unbounded.
            self.scaled_outline = Outline::new();
            self.scratch_points_high_water = 0;
            self.scratch_verbs_high_water = 0;
            self.refresh_bytes();
        }
    }

    fn insert_scaled_outline(&mut self, key: OutlineKey) {
        let metadata = size_of::<OutlineKey>() + size_of::<CachedPath>() + size_of_val(&*key.normalized_coords);
        let points_len = self.scaled_outline.points().len();
        let verbs_len = self.scaled_outline.verbs().len();
        let scratch_bytes = self.scratch_logical_bytes();
        let budget = self.outline_budget;
        let fits = |point_capacity: usize, verb_capacity: usize, metadata_bytes: usize| {
            metadata_bytes + point_capacity * size_of::<Point>() + verb_capacity * size_of::<Verb>() + scratch_bytes
                <= budget
        };
        if !fits(points_len, verbs_len, metadata) {
            return;
        }
        fn grow(capacity: usize, required: usize) -> usize {
            if required <= capacity {
                capacity
            } else {
                required.max(capacity.saturating_mul(2)).max(8)
            }
        }
        let mut point_capacity = grow(self.points.capacity(), self.points.len() + points_len);
        let mut verb_capacity = grow(self.verbs.capacity(), self.verbs.len() + verbs_len);
        if !fits(point_capacity, verb_capacity, self.metadata_bytes + metadata) {
            // Keep the current working set when exact growth fits but the
            // preferred geometric growth would exceed the soft budget.
            point_capacity = self.points.capacity().max(self.points.len() + points_len);
            verb_capacity = self.verbs.capacity().max(self.verbs.len() + verbs_len);
        }
        if !fits(point_capacity, verb_capacity, self.metadata_bytes + metadata) {
            self.clear_cached_paths();
            point_capacity = grow(self.points.capacity(), points_len);
            verb_capacity = grow(self.verbs.capacity(), verbs_len);
            // Near the capacity ceiling, an exact growth may fit when a
            // doubling does not. Geometry remains eagerly admitted.
            if !fits(point_capacity, verb_capacity, metadata) {
                point_capacity = self.points.capacity().max(points_len);
                verb_capacity = self.verbs.capacity().max(verbs_len);
            }
            if !fits(point_capacity, verb_capacity, metadata) {
                return;
            }
        }
        if point_capacity > self.points.capacity() {
            self.points.reserve_exact(point_capacity - self.points.len());
        }
        if verb_capacity > self.verbs.capacity() {
            self.verbs.reserve_exact(verb_capacity - self.verbs.len());
        }
        let points_start = self.points.len();
        let verbs_start = self.verbs.len();
        self.points.extend_from_slice(self.scaled_outline.points());
        self.verbs.extend_from_slice(self.scaled_outline.verbs());
        self.outlines.insert(
            key,
            CachedPath {
                points: points_start..self.points.len(),
                verbs: verbs_start..self.verbs.len(),
            },
        );
        self.metadata_bytes += metadata;
        self.refresh_bytes();
    }
}

// Match the Source::Outline arm of Swash's Render::render_into, including both
// offset and render_offset. The independent Render oracle tests guard this copy.
fn rasterize_path(points: &[Point], verbs: &[Verb], scratch: &mut Scratch, subpixel_x: f32) -> Image {
    let offset = Vector::new(subpixel_x, 0.0);
    let mut image = Image::new();
    image.placement = Mask::with_scratch((points, verbs), scratch)
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
                        let mut run = HintedGlyphRun::new(&mut context_borrow, font, size, coords);
                        for glyph_id in face.glyph_ids.clone() {
                            let actual = rasterizer.render_glyph(&mut run, glyph_id, offset);
                            let expected = render_uncached(&mut reference, font, size, glyph_id, offset, coords);
                            assert_same_image(
                                actual.as_ref(),
                                expected.as_ref(),
                                &format!("{} {coords:?} {size} glyph {glyph_id} phase {offset}", face.name),
                            );
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn run_scaler_is_lazy_and_second_phase_hits_do_not_build_it() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let mut rasterizer = rasterizer();
        let context = rasterizer.scale_context();
        let glyph_ids = ['A', 'g', 'W'].map(|ch| font.charmap().map(ch));
        {
            let mut context_borrow = context.borrow_mut();
            let mut run = HintedGlyphRun::new(&mut context_borrow, font, 24.0, &[]);
            assert!(run.scaler.is_none());
            for glyph_id in glyph_ids {
                rasterizer.render_glyph(&mut run, glyph_id, 0.0).unwrap();
                assert!(run.scaler.is_some());
                assert!(run.context.is_none(), "the context is consumed once for this run");
            }
        }
        let mut context_borrow = context.borrow_mut();
        let mut run = HintedGlyphRun::new(&mut context_borrow, font, 24.0, &[]);
        for glyph_id in glyph_ids {
            rasterizer.render_glyph(&mut run, glyph_id, 0.3).unwrap();
            assert!(run.scaler.is_none(), "a cached outline must not build the run scaler");
        }
        let cold_glyph = font.charmap().map('O');
        rasterizer.render_glyph(&mut run, cold_glyph, 0.3).unwrap();
        assert!(
            run.scaler.is_some(),
            "a later miss initializes the previously unused scaler"
        );
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
    /// reference the production run renderer must match.
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
            cached.points = 0..0;
            cached.verbs = 0..0;
        }

        for subpixel_x in subpixel_offsets() {
            let image = rasterizer.render(font, 16.0, glyph_id, subpixel_x, &[]).unwrap();
            assert!(image.data.iter().all(|&coverage| coverage == 0), "offset {subpixel_x}");
        }
    }

    #[test]
    fn exact_budget_boundary_controls_admission_and_rehinting() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let glyph = font.charmap().map('g');
        let mut probe = rasterizer();
        probe.render(font, 16.0, glyph, 0.0, &[]).unwrap();
        let entry_cost = probe.outline_bytes;
        let mut reference = ScaleContext::new();
        for (budget, admitted) in [(entry_cost - 1, false), (entry_cost, true), (entry_cost + 1, true)] {
            let mut rasterizer = SwashRasterizer::with_outline_budget(Rc::default(), budget);
            rasterizer.render(font, 16.0, glyph, 0.0, &[]).unwrap();
            assert_eq!(rasterizer.outlines.len(), usize::from(admitted), "budget {budget}");
            let context = rasterizer.scale_context();
            let actual = {
                let mut context = context.borrow_mut();
                let mut run = HintedGlyphRun::new(&mut context, font, 16.0, &[]);
                let image = rasterizer.render_glyph(&mut run, glyph, 0.3);
                assert_eq!(run.scaler.is_none(), admitted, "a retained outline avoids rehinting");
                image
            };
            let expected = render_uncached(&mut reference, font, 16.0, glyph, 0.3, &[]);
            assert_same_image(actual.as_ref(), expected.as_ref(), "budget boundary");
        }
    }

    #[test]
    fn an_unadmittable_outline_preserves_a_working_set_that_still_fits() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let small = font.charmap().map('.');
        let large = font.charmap().map('@');
        let mut rasterizer = rasterizer();
        rasterizer.render(font, 16.0, small, 0.0, &[]).unwrap();
        let mut reference = ScaleContext::new();
        let mut large_outline = Outline::new();
        assert!(reference
            .builder(font)
            .size(16.0)
            .hint(true)
            .build()
            .scale_outline_into(large, &mut large_outline));
        let scratch_bytes = size_of::<Outline>()
            + large_outline.points().len().max(rasterizer.scratch_points_high_water) * size_of::<Point>()
            + large_outline.verbs().len().max(rasterizer.scratch_verbs_high_water) * size_of::<Verb>();
        // Allow the retained small entry and the larger temporary scratch,
        // but not a cached copy of the larger outline.
        rasterizer.outline_budget = rasterizer.metadata_bytes
            + rasterizer.points.capacity() * size_of::<Point>()
            + rasterizer.verbs.capacity() * size_of::<Verb>()
            + scratch_bytes;
        let actual = rasterizer.render(font, 16.0, large, 0.3, &[]);
        let expected = render_uncached(&mut reference, font, 16.0, large, 0.3, &[]);
        assert_same_image(actual.as_ref(), expected.as_ref(), "unadmittable outline");
        assert_eq!(rasterizer.outlines.len(), 1);
        let context = rasterizer.scale_context();
        let mut context = context.borrow_mut();
        let mut run = HintedGlyphRun::new(&mut context, font, 16.0, &[]);
        assert!(rasterizer.render_glyph(&mut run, small, 0.3).is_some());
        assert!(run.scaler.is_none(), "the retained working set still hits");
    }

    #[test]
    fn exact_arena_growth_preserves_a_working_set_that_fits_the_budget() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let glyph_id = font.charmap().map('@');
        let sizes = [24.0, 25.0, 26.0];
        let mut rasterizer = rasterizer();
        rasterizer.render(font, sizes[0], glyph_id, 0.0, &[]).unwrap();
        let geometry_bytes = rasterizer.points.len() * size_of::<Point>() + rasterizer.verbs.len() * size_of::<Verb>();
        let metadata = rasterizer.metadata_bytes;
        let scratch = rasterizer.scratch_logical_bytes();
        // Three entries fit, but doubling the two-entry arena for the third
        // would exceed the budget.
        rasterizer.outline_budget = 4 * geometry_bytes + 3 * metadata + scratch - 1;
        assert!(3 * geometry_bytes + 3 * metadata + scratch <= rasterizer.outline_budget);
        for size in &sizes[1..] {
            rasterizer.render(font, *size, glyph_id, 0.0, &[]).unwrap();
        }
        assert_eq!(rasterizer.outlines.len(), sizes.len());
        assert!(rasterizer.outline_bytes <= rasterizer.outline_budget);

        let mut reference = ScaleContext::new();
        let context = rasterizer.scale_context();
        for size in sizes.into_iter().cycle().take(9) {
            let actual = {
                let mut context_borrow = context.borrow_mut();
                let mut run = HintedGlyphRun::new(&mut context_borrow, font, size, &[]);
                let image = rasterizer.render_glyph(&mut run, glyph_id, 0.3);
                assert!(run.scaler.is_none(), "the entire working set must remain cached");
                image
            };
            let expected = render_uncached(&mut reference, font, size, glyph_id, 0.3, &[]);
            assert_same_image(actual.as_ref(), expected.as_ref(), "retained near-budget outline");
            assert_eq!(rasterizer.outlines.len(), sizes.len());
        }
        // A fourth size really exceeds the budget, so eviction is still needed.
        let actual = rasterizer.render(font, 27.0, glyph_id, 0.3, &[]);
        let expected = render_uncached(&mut reference, font, 27.0, glyph_id, 0.3, &[]);
        assert_same_image(actual.as_ref(), expected.as_ref(), "over-budget outline");
        assert_eq!(rasterizer.outlines.len(), 1);
        assert!(rasterizer.outline_bytes <= rasterizer.outline_budget);
    }

    #[test]
    fn arena_capacity_and_logical_scratch_are_charged_and_reused_after_clears() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let mut rasterizer = SwashRasterizer::with_outline_budget(Rc::default(), 4096);
        let mut context = ScaleContext::new();
        let mut cleared = false;
        let mut prior_entries = 0;
        let mut scratch_peak = size_of::<Outline>();
        for (i, ch) in ('!'..='~').cycle().take(400).enumerate() {
            let glyph = font.charmap().map(ch);
            let size = 16.0 + (i / 94) as f32;
            let actual = rasterizer.render(font, size, glyph, 0.3, &[]);
            let expected = render_uncached(&mut context, font, size, glyph, 0.3, &[]);
            assert_same_image(actual.as_ref(), expected.as_ref(), "bounded arena churn");
            assert!(rasterizer.outline_bytes <= 4096);
            assert_eq!(
                rasterizer.outline_bytes,
                rasterizer.metadata_bytes
                    + rasterizer.points.capacity() * size_of::<Point>()
                    + rasterizer.verbs.capacity() * size_of::<Verb>()
                    + rasterizer.scratch_logical_bytes()
            );
            scratch_peak = scratch_peak.max(rasterizer.scratch_logical_bytes());
            cleared |= rasterizer.outlines.len() < prior_entries;
            prior_entries = rasterizer.outlines.len();
        }
        assert!(cleared);
        assert!(scratch_peak > size_of::<Outline>());
    }

    #[test]
    fn empty_outlines_still_charge_metadata_and_coordinates() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let space = font.charmap().map(' ');
        let mut coords = vec![0; font.variations().len()];
        let mut rasterizer = SwashRasterizer::with_outline_budget(Rc::default(), 1024);
        for first_axis in 0..20 {
            coords[0] = first_axis * 0x100;
            rasterizer.render(font, 16.0, space, 0.0, &coords);
            assert!(rasterizer.outline_bytes <= 1024);
            assert_eq!(
                rasterizer.metadata_bytes,
                rasterizer.outlines.len()
                    * (size_of::<OutlineKey>() + size_of::<CachedPath>() + size_of_val(&coords[..]))
            );
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
        assert!(rasterizer.outline_bytes <= size_of::<Outline>());
        assert!(rasterizer.scaled_outline.points().is_empty());
    }
    #[test]
    fn native_scratch_uses_public_length_high_water_and_resets_when_oversized() {
        let data = read_font("RobotoFlex-VariableFont.ttf");
        let font = FontRef::from_index(&data, 0).unwrap();
        let mut rasterizer = rasterizer();
        let wide = font.charmap().map('W');
        rasterizer.render(font, 24.0, wide, 0.0, &[]).unwrap();
        let points = rasterizer.scaled_outline.points().len();
        let verbs = rasterizer.scaled_outline.verbs().len();
        assert!(points > 0 && verbs > 0);
        assert_eq!(rasterizer.scratch_points_high_water, points);
        assert_eq!(rasterizer.scratch_verbs_high_water, verbs);
        assert_eq!(
            rasterizer.scratch_logical_bytes(),
            size_of::<Outline>() + points * size_of::<Point>() + verbs * size_of::<Verb>()
        );
        rasterizer
            .render(font, 24.0, font.charmap().map(' '), 0.0, &[])
            .unwrap();
        assert!(rasterizer.scaled_outline.points().is_empty());
        assert_eq!(rasterizer.scratch_points_high_water, points);
        assert_eq!(rasterizer.scratch_verbs_high_water, verbs);
        // Give the scratch alone insufficient logical budget and render a miss.
        rasterizer.outline_budget = size_of::<Outline>() + 1;
        rasterizer.render(font, 25.0, wide, 0.0, &[]).unwrap();
        assert!(rasterizer.outlines.is_empty());
        assert!(rasterizer.scaled_outline.points().is_empty());
        assert_eq!(rasterizer.scratch_points_high_water, 0);
        assert_eq!(rasterizer.scratch_verbs_high_water, 0);
        assert_eq!(rasterizer.scratch_logical_bytes(), size_of::<Outline>());
    }
}
