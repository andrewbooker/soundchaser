use std::time::SystemTime;


struct HitDetector {
    in_hit: bool,
    max_val: i16,
    hit_started: Option<SystemTime>
}

trait AudioStreamListener {
    fn listen(&mut self, stream: &mut soundio::InStreamReader);
}

impl HitDetector {
    pub fn new() -> HitDetector {
        HitDetector {
            in_hit: false,
            max_val: 0,
            hit_started: None
        }
    }
}

impl AudioStreamListener for HitDetector {
    fn listen(&mut self, stream: &mut soundio::InStreamReader) {
        let frame_count_max = stream.frame_count_max();
        if let Err(e) = stream.begin_read(frame_count_max) {
            println!("Error reading from stream: {}", e);
            return;
        }

        for f in 0..stream.frame_count() {
            let s = stream.sample::<i16>(0, f);
            if s > self.max_val {
                self.max_val = s
            } else if self.max_val > 256 {
                self.in_hit = true;
                self.hit_started = Some(SystemTime::now());
                println!("in hit from {} after max val {}", s, self.max_val);
            }
        }
    }
}


fn main() {
    let mut ctx = soundio::Context::new();
    println!("Available backends: {:?}", ctx.available_backends());
    match ctx.connect() {
    	Ok(()) => println!("Connected to {}", ctx.current_backend()),
	    Err(e) => println!("Could not connect: {}", e),
    }


    ctx.flush_events();
    println!("{} input device(s)", ctx.input_device_count());
    let devs = ctx.input_devices().expect("Error getting devices");
    let dev = &devs[0];
    println!("Device {} ", dev.name());
    println!("Device is raw: {}", dev.is_raw());

    let mut hit_detector = HitDetector::new();
    let read_callback = |stream: &mut soundio::InStreamReader| hit_detector.listen(stream);

    let mut input_stream = dev.open_instream(
        44100,
        soundio::Format::S16LE,
        soundio::ChannelLayout::get_builtin(soundio::ChannelLayoutId::Mono),
        0.02,
        read_callback,
        None::<fn()>,
        None::<fn(soundio::Error)>,
    ).expect("Could not open input stream");
    input_stream.start().expect("could not start stream"); 
    println!("{} started", input_stream.name());

    let g = getch::Getch::new();
    loop {
        let c: u8 = g.getch().unwrap();
        match c as char {
            'q' => {
                break;
            },
            _ => {}
        }
    }
    println!("done");
}
