

fn read_callback(stream: &mut soundio::InStreamReader) {
    let frame_count_max = stream.frame_count_max();
    if let Err(e) = stream.begin_read(frame_count_max) {
        println!("Error reading from stream: {}", e);
        return;
    }
    println!("{} frames out of {}", stream.frame_count(), frame_count_max);
    
    //for f in 0..stream.frame_count() {
    //    do_something_with(stream.sample::<i16>(c, f));
    //}
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

    let mut input_stream = dev.open_instream(
        44100,
        soundio::Format::S16LE,
        soundio::ChannelLayout::get_builtin(soundio::ChannelLayoutId::Stereo),
        0.02,
        read_callback,
        None::<fn()>,
        None::<fn(soundio::Error)>,
    ).expect("Could not open input stream");
    input_stream.start().expect("could not start stream"); 
    println!("stream started");

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
