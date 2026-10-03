// Added only to separate untimed audit copies, never to timing copies.
#[derive(Default)]
struct BenchmarkAudit {
    uploads: usize,
    bytes: usize,
    mask: u64,
    vertices: u64,
}
std::thread_local! {
    static BENCHMARK_AUDIT: std::cell::RefCell<BenchmarkAudit> = std::cell::RefCell::new(BenchmarkAudit::default());
}
fn benchmark_hash(state: &mut u64, bytes: &[u8]) {
    for &byte in bytes {
        *state = (*state ^ byte as u64).wrapping_mul(1099511628211);
    }
}
fn benchmark_image(data: &ImageSource<'_>) {
    BENCHMARK_AUDIT.with(|cell| {
        let mut state = cell.borrow_mut();
        state.uploads += 1;
        let size = data.dimensions();
        benchmark_hash(&mut state.mask, &(size.width as u64).to_le_bytes());
        benchmark_hash(&mut state.mask, &(size.height as u64).to_le_bytes());
        match data {
            ImageSource::Rgb(image) => {
                for row in image.rows() {
                    for pixel in row {
                        benchmark_hash(&mut state.mask, &[pixel.r, pixel.g, pixel.b]);
                        state.bytes += 3;
                    }
                }
            }
            ImageSource::Rgba(image) => {
                for row in image.rows() {
                    for pixel in row {
                        benchmark_hash(&mut state.mask, &[pixel.r, pixel.g, pixel.b, pixel.a]);
                        state.bytes += 4;
                    }
                }
            }
            ImageSource::Gray(image) => {
                for row in image.rows() {
                    for pixel in row {
                        benchmark_hash(&mut state.mask, &[pixel.value()]);
                        state.bytes += 1;
                    }
                }
            }
        }
    });
}
fn benchmark_vertices(vertices: &[Vertex]) {
    BENCHMARK_AUDIT.with(|cell| {
        let mut state = cell.borrow_mut();
        benchmark_hash(&mut state.vertices, &(vertices.len() as u64).to_le_bytes());
        for vertex in vertices {
            for value in [vertex.x, vertex.y, vertex.u, vertex.v] {
                benchmark_hash(&mut state.vertices, &value.to_bits().to_le_bytes());
            }
        }
    });
}
impl Void {
    /// Starts an untimed upload and vertex digest capture.
    pub fn benchmark_start_audit() {
        BENCHMARK_AUDIT.with(|cell| {
            *cell.borrow_mut() = BenchmarkAudit {
                mask: 14695981039346656037,
                vertices: 14695981039346656037,
                ..BenchmarkAudit::default()
            }
        });
    }
    /// Returns the captured upload counts and upload/vertex digests.
    pub fn benchmark_finish_audit() -> (usize, usize, u64, u64) {
        BENCHMARK_AUDIT.with(|cell| {
            let state = cell.borrow();
            (state.uploads, state.bytes, state.mask, state.vertices)
        })
    }
}
