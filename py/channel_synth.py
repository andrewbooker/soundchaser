#!/usr/bin/python3


from http.server import HTTPServer, BaseHTTPRequestHandler
import pygame as pg
import time
import sys
import threading
import readchar
import sounddevice as sd

import queue




class Player:
    def __init__(self, vol, sound):
        self.channel = pg.mixer.find_channel()
        self.channel.set_volume(vol[0], vol[1])
        self.sound = pg.mixer.Sound(sound)

    def play(self):
        self.channel.play(self.sound)


class SynthPlayer:
    def __init__(self, vol):
        sd.default.samplerate = 44100
        sd.default.channels = 2
        self.q = queue.Queue()

    def _callback(outdata, frames, time, status):
        outdata[:] = self.q.get()
    
    def play():
        blocksize = 4410
        self.q.put(self.mix.read(blocksize))
        with sd.OutputStream(blocksize=blocksize, dtype="float32", callback=callback)
            while mix.hasData():
                self.put(mix.read(blocksize))
    


class Controller(BaseHTTPRequestHandler):
    def __init__(self, vol, sound, *args):
        self.player = Player(vol, sound)
        BaseHTTPRequestHandler.__init__(self, *args)

    def _standardResponse(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self._standardResponse()
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.end_headers()

    def do_POST(self):
        self.player.play()
        self._standardResponse()
        self.end_headers()

class PG:
    def __init__(self):
        pg.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        pg.init()

    def __del__(self):
        pg.quit()

ignore = PG()

class ControllerA(Controller):
    def __init__(self, *args):
        Controller.__init__(self, (1.0, 0.0), sys.argv[1], *args)

class ControllerB(Controller):
    def __init__(self, *args):
        Controller.__init__(self, (0.0, 1.0), sys.argv[2], *args)


servers = [
    HTTPServer(("0.0.0.0", 9900), ControllerA),
    HTTPServer(("0.0.0.0", 9901), ControllerB)
]


shouldStop = threading.Event()
threads = [threading.Thread(target=s.serve_forever, args=(), daemon=True) for s in servers]
[t.start() for t in threads]

print("press 'q' to exit")
while not shouldStop.is_set():
    c = readchar.readchar()
    if c == "q":
        print("stopping...")
        shouldStop.set()
        [s.shutdown() for s in servers]
        [s.server_close() for s in servers]
        [t.join() for t in threads]


