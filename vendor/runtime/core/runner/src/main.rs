mod demo;
mod text;
mod font_variations;
mod perf_graph;
mod controlled;
#[path = "../../snapshots/master/tests/common/mod.rs"]
mod common;

use femtovg::{Canvas, Renderer, renderer::{Void, WGPURenderer}};
use std::{time::Instant, path::PathBuf};

fn asset(file: &str) -> Vec<u8> {
    std::fs::read(PathBuf::from("/Users/jesse/github/femtovg/examples/assets").join(file)).unwrap()
}
fn regular_text_font() -> Vec<u8> {
    match std::env::var_os("FEMTOVG_REPLAY_TEXT_FONT") {
        Some(path) => std::fs::read(path).expect("read replay text font"),
        None => asset("RobotoFlex-VariableFont.ttf"),
    }
}
#[derive(Clone, Copy)]
pub struct Size { pub width: u32, pub height: u32 }
#[derive(Clone, Copy)]
pub struct Frame {
    pub index: u32, pub width: u32, pub height: u32,
    pub font_size: f32, pub x: f32, pub y: f32,
    pub mousex: f32, pub mousey: f32, pub weight: f32, pub slant: f32,
}
impl Frame {
    fn new(name: &str) -> Self {
        Self { index: 0, width: if name == "font_variations" {800} else {1000},
            height: if name == "font_variations" {700} else {600},
            font_size: 18.0, x: 5.0, y: 380.0, mousex: 500.0, mousey: 300.0,
            weight: 400.0, slant: 0.0 }
    }
}
enum Scene { Demo(demo::Scene), Text(text::Scene), Variations(font_variations::Scene) }
impl Scene {
    fn new<T: Renderer>(name: &str, c: &mut Canvas<T>) -> Self {
        match name {
            "demo" => Self::Demo(demo::Scene::new(c)),
            "text" => Self::Text(text::Scene::new(c)),
            "font_variations" => Self::Variations(font_variations::Scene::new(c)),
            _ => panic!("unknown scene")
        }
    }
    fn draw<T: Renderer>(&mut self, c: &mut Canvas<T>, f: Frame) {
        match self { Self::Demo(s) => s.draw(c,f), Self::Text(s) => s.draw(c,f), Self::Variations(s) => s.draw(c,f) }
    }
}
struct Gpu { device: wgpu::Device, queue: wgpu::Queue, targets: Vec<wgpu::Texture> }
impl Gpu {
    fn new() -> Self {
        let (device,queue) = common::headless_device().expect("a GPU is required");
        let mut targets = Vec::new();
        for (width,height) in [(1000,600),(800,600),(600,600),(800,700)] {
            targets.push(device.create_texture(&wgpu::TextureDescriptor {
                label: Some("example replay target"),
                size: wgpu::Extent3d {width,height,depth_or_array_layers:1},
                mip_level_count:1, sample_count:1, dimension:wgpu::TextureDimension::D2,
                format:wgpu::TextureFormat::Rgba8Unorm,
                usage:wgpu::TextureUsages::RENDER_ATTACHMENT | wgpu::TextureUsages::COPY_SRC,
                view_formats:&[],
            }));
        }
        Self {device,queue,targets}
    }
    fn target(&self, f: Frame) -> &wgpu::Texture {
        self.targets.iter().find(|t| t.width()==f.width && t.height()==f.height).unwrap()
    }
    fn wait(&self) {
        self.device.poll(wgpu::PollType::wait_indefinitely()).unwrap();
    }
    fn drain(&self) { self.queue.submit(std::iter::empty()); self.wait(); }
    fn pixels(&self, f: Frame) -> Vec<u8> {
        let width = f.width; let height=f.height;
        let padded=(width*4).div_ceil(wgpu::COPY_BYTES_PER_ROW_ALIGNMENT)*wgpu::COPY_BYTES_PER_ROW_ALIGNMENT;
        let buffer = self.device.create_buffer(&wgpu::BufferDescriptor {
            label:Some("outside-timing readback"),size:(padded*height) as u64,
            usage:wgpu::BufferUsages::COPY_DST|wgpu::BufferUsages::MAP_READ,mapped_at_creation:false,
        });
        let mut encoder=self.device.create_command_encoder(&wgpu::CommandEncoderDescriptor::default());
        encoder.copy_texture_to_buffer(
            wgpu::TexelCopyTextureInfo {texture:self.target(f),mip_level:0,origin:wgpu::Origin3d::ZERO,aspect:wgpu::TextureAspect::All},
            wgpu::TexelCopyBufferInfo {buffer:&buffer,layout:wgpu::TexelCopyBufferLayout {offset:0,bytes_per_row:Some(padded),rows_per_image:Some(height)}},
            wgpu::Extent3d {width,height,depth_or_array_layers:1});
        self.queue.submit([encoder.finish()]);
        let (sender,receiver)=std::sync::mpsc::channel();
        let slice=buffer.slice(..);
        slice.map_async(wgpu::MapMode::Read,move |r| sender.send(r).unwrap());
        self.wait(); receiver.recv().unwrap().unwrap();
        let mapped=slice.get_mapped_range().unwrap();
        let mut pixels=Vec::with_capacity((width*height*4) as usize);
        for row in mapped.chunks(padded as usize) {pixels.extend_from_slice(&row[..(width*4) as usize]);}
        drop(mapped);buffer.unmap();pixels
    }
}
struct Measurement { draw: f64, submit: f64, complete: f64, misses: usize }
fn frame<T: Renderer>(c: &mut Canvas<T>, s: &mut Scene, f: &mut Frame, dpi: f32,
    flush: &mut impl FnMut(&mut Canvas<T>, Frame), wait: &mut impl FnMut()) -> Measurement {
    let before=c.benchmark_atlas_entries();
    let start=Instant::now();
    c.set_size(f.width,f.height,dpi);
    s.draw(c,*f);
    let draw=start.elapsed().as_secs_f64()*1e6;
    flush(c,*f);
    let submit=start.elapsed().as_secs_f64()*1e6;
    wait();
    let complete=start.elapsed().as_secs_f64()*1e6;
    let after=c.benchmark_atlas_entries();
    f.index+=1;
    Measurement {draw,submit,complete,misses:after-before}
}
fn emit(name:&str,phase:&str,trial:usize,frames:&[Measurement]) {
    let n=frames.len() as f64;
    println!("{name},{phase},{trial},{},{:.6},{:.6},{:.6},{}",frames.len(),
        frames.iter().map(|r|r.draw).sum::<f64>()/n,
        frames.iter().map(|r|r.submit).sum::<f64>()/n,
        frames.iter().map(|r|r.complete).sum::<f64>()/n,
        frames.iter().map(|r|r.misses).sum::<usize>());
}
fn run<T: Renderer>(name:&str,trial:usize,dpi:f32,mut c:Canvas<T>,
    mut flush:impl FnMut(&mut Canvas<T>,Frame),mut wait:impl FnMut(),
    mut setup:impl FnMut(),mut snapshot:impl FnMut(Frame,&str)) {
    let mut s=Scene::new(name,&mut c);
    let mut f=Frame::new(name);
    setup();
    let first=frame(&mut c,&mut s,&mut f,dpi,&mut flush,&mut wait);
    emit(name,"first_paint",trial,&[first]);snapshot(f,"first_paint");
    for _ in 1..120 {frame(&mut c,&mut s,&mut f,dpi,&mut flush,&mut wait);}
    let steady=(0..30).map(|_|frame(&mut c,&mut s,&mut f,dpi,&mut flush,&mut wait)).collect::<Vec<_>>();
    emit(name,"warm",trial,&steady);snapshot(f,"warm");
    let phases: Vec<(&str,usize)> = match name {
        "text" => vec![("x_advance",10),("x_return",10),("y_advance",10),("size_advance",12),("size_return",12),("reflow",3)],
        "demo" => vec![("zoom_in",12),("zoom_out",12),("pan",10)],
        _ => vec![("weight_advance",6),("weight_return",6),("slant_advance",10),("slant_return",10)],
    };
    for (phase,n) in phases {
        let mut results=Vec::new();
        for i in 0..n {
            match phase {
                "x_advance"=>f.x+=0.1,"x_return"=>f.x-=0.1,"y_advance"=>f.y+=0.1,
                "size_advance"=>f.font_size=(f.font_size+0.5).max(2.0),
                "size_return"=>f.font_size=(f.font_size-0.5).max(2.0),
                "reflow"=>f.width=[800,600,1000][i],
                "weight_advance"=>f.weight=(f.weight+50.0).min(1000.0),
                "weight_return"=>f.weight=(f.weight-50.0).max(100.0),
                "slant_advance"=>f.slant=(f.slant-1.0).max(-10.0),
                "slant_return"=>f.slant=(f.slant+1.0).min(0.0),
                "zoom_in"|"zoom_out"=> {
                    let p=c.transform().inverse().transform_point(f.mousex,f.mousey);
                    let y=if phase=="zoom_in" {1.0} else {-1.0};
                    c.translate(p.0,p.1);c.scale(1.0+y/10.0,1.0+y/10.0);c.translate(-p.0,-p.1);
                },
                "pan"=> {
                    let p0=c.transform().inverse().transform_point(f.mousex,f.mousey);
                    f.mousex+=10.0;
                    let p1=c.transform().inverse().transform_point(f.mousex,f.mousey);
                    c.translate(p1.0-p0.0,p1.1-p0.1);
                },
                _=>unreachable!(),
            }
            results.push(frame(&mut c,&mut s,&mut f,dpi,&mut flush,&mut wait));
        }
        emit(name,phase,trial,&results);snapshot(f,phase);
    }
}
fn run_controlled<T: Renderer>(name:&str,trial:usize,dpi:f32,mut c:Canvas<T>,
    mut flush:impl FnMut(&mut Canvas<T>,Frame),mut wait:impl FnMut(),
    mut setup:impl FnMut(),mut snapshot:impl FnMut(Frame,&str)) {
    let scene=controlled::Scene::new(name,&mut c,dpi);
    let mut f=Frame::new(name);
    setup();
    for (phase, requests) in scene.phases() {
        let mut measurements=Vec::with_capacity(requests.len());
        for request in requests {
            let before=c.benchmark_atlas_entries();
            let start=Instant::now();
            c.set_size(f.width,f.height,dpi);
            scene.draw(&mut c,&request);
            let draw=start.elapsed().as_secs_f64()*1e6;
            flush(&mut c,f);
            let submit=start.elapsed().as_secs_f64()*1e6;
            wait();
            let complete=start.elapsed().as_secs_f64()*1e6;
            let after=c.benchmark_atlas_entries();
            measurements.push(Measurement {draw,submit,complete,misses:after-before});
            f.index+=1;
        }
        emit(name,phase,trial,&measurements);snapshot(f,phase);
    }
}
fn run_selected<T: Renderer>(name:&str,trial:usize,dpi:f32,c:Canvas<T>,
    flush:impl FnMut(&mut Canvas<T>,Frame),wait:impl FnMut(),
    setup:impl FnMut(),snapshot:impl FnMut(Frame,&str)) {
    if name.starts_with("grid_") {
        run_controlled(name,trial,dpi,c,flush,wait,setup,snapshot);
    } else {
        run(name,trial,dpi,c,flush,wait,setup,snapshot);
    }
}
fn main() {
    let args=std::env::args().collect::<Vec<_>>();
    let backend=args.get(1).map(String::as_str).unwrap_or("cpu");
    let trials:usize=args.get(2).map(|s|s.parse().unwrap()).unwrap_or(3);
    let dpi:f32=args.get(3).map(|s|s.parse().unwrap()).unwrap_or(1.0);
    let output=args.get(4).map(PathBuf::from);
    if let Some(p)=&output {std::fs::create_dir_all(p).unwrap();}
    println!("scene,phase,trial,frames,draw_us,submit_us,complete_us,new_atlas_entries");
    let gpu=if backend=="gpu" {Some(Gpu::new())} else {None};
    for trial in 0..trials {
        for name in ["demo","text","font_variations","grid_singleton","grid_two_phases","grid_unique_sizes","grid_unique_variations","grid_pollution"] {
            if let Some(g)=&gpu {
                let c=Canvas::new(WGPURenderer::new(g.device.clone(),g.queue.clone())).unwrap();
                run_selected(name,trial,dpi,c,|c:&mut Canvas<WGPURenderer>,f:Frame| {g.queue.submit(c.flush_to_output(g.target(f)));},
                    ||g.wait(),||g.drain(),|f,phase| {
                        if trial==0 {if let Some(p)=&output {
                            std::fs::write(p.join(format!("{name}-{phase}.rgba")),g.pixels(f)).unwrap();
                        }}
                    });
            } else {
                run_selected(name,trial,dpi,Canvas::new(Void).unwrap(),|c:&mut Canvas<Void>,_f:Frame| {c.flush_to_output(());},||{},||{},|_,_|{});
            }
        }
    }
}
