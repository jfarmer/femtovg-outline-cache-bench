//! Public-API stress control for cache admission near the nominal 1 MiB budget.
//! Each phase gets a fresh atlas; the registered fonts and outline cache remain
//! in one shared TextContext. This is not an application-latency benchmark.
use femtovg::{renderer::Void, Canvas, Color, Paint, PositionedGlyph, TextContext};
use std::{collections::HashSet, hint::black_box, time::Instant};

struct Group {
    size: f32,
    glyphs: Vec<PositionedGlyph>,
}

fn groups(ids: &[u16], keys: usize, phase: usize) -> Vec<Group> {
    let mut remaining = keys;
    let mut size = 12.0;
    let mut result = Vec::new();
    while remaining != 0 {
        let count = remaining.min(ids.len());
        let glyphs = ids[..count]
            .iter()
            .enumerate()
            .map(|(index, &glyph_id)| PositionedGlyph {
                x: 24.0 + (index % 16) as f32 * 56.0 + phase as f32 / 10.0,
                y: 80.0 + (index / 16) as f32 * 80.0,
                glyph_id,
            })
            .collect();
        assert!(size <= 50.0, "every request remains on the atlas path");
        result.push(Group { size, glyphs });
        remaining -= count;
        size += 1.0;
    }
    result
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    assert_eq!(args.len(), 4, "usage: runner timing|audit FONT_PATH TRIALS");
    let mode = args[1].as_str();
    assert!(matches!(mode, "timing" | "audit"));
    assert_eq!(mode == "audit", cfg!(feature = "audit"));
    let trials: usize = args[3].parse().unwrap();
    assert!(trials > 0);
    let data = std::fs::read(&args[2]).unwrap();
    let font_ref = swash::FontRef::from_index(&data, 0).unwrap();
    let ids: Vec<_> = ('!'..='~')
        .map(|character| font_ref.charmap().map(character))
        .collect();
    assert_eq!(ids.len(), 94);
    assert!(!ids.contains(&0));
    assert_eq!(ids.iter().copied().collect::<HashSet<_>>().len(), 94);
    println!("keys,trial,phase,groups,glyph_requests,draw_flush_us,upload_count,upload_bytes,upload_digest,vertex_digest");

    for trial in 0..trials {
        for keys in [3300, 3440, 3600] {
            // New context per workload/trial, so population is always cold.
            let context = TextContext::default();
            let font = context.add_font_mem(&data).unwrap();
            for phase in 0..10 {
                // These have independent atlases but share the geometry cache.
                // Creation, registration, request construction and destruction
                // remain outside the reported draw+flush timing.
                let mut canvas = Canvas::new_with_text_context(Void, context.clone()).unwrap();
                canvas.set_size(1000, 600, 1.0);
                let requests = groups(&ids, keys, phase);
                #[cfg(feature = "audit")]
                Void::benchmark_start_audit();
                let start = Instant::now();
                for request in &requests {
                    let paint = Paint::color(Color::black()).with_font_size(request.size);
                    canvas
                        .fill_glyph_run(font, &[], request.glyphs.iter().cloned(), &paint)
                        .unwrap();
                    canvas.flush_to_output(());
                }
                let duration = start.elapsed().as_secs_f64() * 1e6;
                black_box(&canvas);
                #[cfg(feature = "audit")]
                {
                    let (uploads, bytes, mask_digest, vertex_digest) =
                        Void::benchmark_finish_audit();
                    assert_eq!(
                        uploads, keys,
                        "fresh canvas must upload every requested glyph"
                    );
                    println!("{keys},{trial},{phase},{},{keys},0,{uploads},{bytes},{mask_digest:016x},{vertex_digest:016x}", requests.len());
                    black_box(duration);
                }
                #[cfg(not(feature = "audit"))]
                println!(
                    "{keys},{trial},{phase},{},{keys},{duration:.6},,,,",
                    requests.len()
                );
            }
        }
    }
}
