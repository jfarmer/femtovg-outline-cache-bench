//! Controlled glyph-atlas workloads, separate from unchanged example scenes.
//! Glyph IDs and variable-font normalization use Swash, outside frame timing.
use femtovg::{Canvas, Color, FontId, Paint, PositionedGlyph, Renderer};
use std::collections::HashSet;

#[derive(Clone)]
pub struct Request {
    size: f32,
    positions: Vec<PositionedGlyph>,
    coords: Vec<i16>,
}

pub struct Scene {
    font: FontId,
    phases: Vec<(&'static str, Vec<Request>)>,
}

impl Scene {
    pub fn new<T: Renderer>(name: &str, canvas: &mut Canvas<T>, dpi: f32) -> Self {
        let data = if name == "grid_unique_variations" {
            crate::asset("RobotoFlex-VariableFont.ttf")
        } else {
            crate::regular_text_font()
        };
        let face = swash::FontRef::from_index(&data, 0).expect("read controlled font");
        let map = face.charmap();
        let ids: Vec<u16> = (33u8..=126).map(|ch| map.map(ch as char)).collect();
        assert_eq!(ids.len(), 94);
        assert!(!ids.contains(&0), "every nonspace ASCII character must map");
        assert_eq!(ids.iter().copied().collect::<HashSet<_>>().len(), 94,
            "controlled grid must contain 94 distinct glyph IDs");
        let request = |size: f32, phase: u32, coords: Vec<i16>| {
            // The public glyph API accepts canvas coordinates; atlas subpixel
            // keys use their fractional part before renderer DPR handling.
            // Integer grid origins make the intended 0.0/0.1/0.2 keys explicit.
            let positions = ids.iter().enumerate().map(|(i, &glyph_id)| PositionedGlyph {
                x: 24.0 + (i % 16) as f32 * 56.0 + phase as f32 * 0.1,
                y: 80.0 + (i / 16) as f32 * 80.0,
                glyph_id,
            }).collect();
            Request { size, positions, coords }
        };
        let phases = match name {
            "grid_singleton" => vec![("once", vec![request(20.0, 0, vec![])])],
            "grid_two_phases" => vec![
                ("first", vec![request(20.0, 0, vec![])]),
                ("second", vec![request(20.0, 1, vec![])]),
            ],
            "grid_unique_sizes" => vec![("sweep", (0..32)
                .map(|i| request(16.0 + i as f32 * 0.5, 0, vec![])).collect())],
            "grid_unique_variations" => {
                let requests: Vec<_> = (0..32).map(|i| {
                    let weight = 100.0 + i as f32 * 25.0;
                    let coords = face.variations().normalized_coords([("wght", weight)]).collect();
                    request(20.0, 0, coords)
                }).collect();
                assert_eq!(requests.iter().map(|r| &r.coords).collect::<HashSet<_>>().len(), 32,
                    "variation sweep must have 32 distinct normalized instances");
                vec![("sweep", requests)]
            },
            "grid_pollution" => vec![
                ("hot_first", vec![request(20.0, 0, vec![])]),
                ("hot_second", vec![request(20.0, 1, vec![])]),
                ("pollution", (0..64).map(|i| {
                    // Avoid the hot size itself. Sizes remain below FemtoVG's
                    // direct-path threshold at both measured DPR factors.
                    request(12.25 + i as f32 * 0.5, 0, vec![])
                }).collect()),
                ("hot_return", vec![request(20.0, 2, vec![])]),
            ],
            _ => panic!("unknown controlled scene: {name}"),
        };
        eprintln!("controlled scene={name} glyphs={} distinct_keys_per_new_instance={} dpi={dpi}", ids.len(), ids.len());
        let font = canvas.add_font_mem(&data).expect("register controlled font");
        Self { font, phases }
    }

    pub fn phases(&self) -> Vec<(&'static str, Vec<Request>)> {
        self.phases.clone()
    }

    pub fn draw<T: Renderer>(&self, canvas: &mut Canvas<T>, request: &Request) {
        canvas.clear_rect(0, 0, 1000, 600, Color::rgbf(0.95, 0.95, 0.95));
        let paint = Paint::color(Color::black()).with_font_size(request.size);
        canvas.fill_glyph_run(self.font, &request.coords,
            request.positions.iter().cloned(), &paint).expect("draw controlled grid");
    }
}
