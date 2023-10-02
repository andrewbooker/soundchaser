#!/usr/bin/python3


from http.server import HTTPServer, BaseHTTPRequestHandler
import pygame as pg
import time
import sys


class Player:
    def __init__(self):
        pg.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        pg.init()
        self.channel = pg.mixer.find_channel()
        self.channel.set_volume(1.0)
        self.sound = pg.mixer.Sound(sys.argv[1])

    def __del__(self):
        pg.quit()

    def play(self):
        self.channel.play(self.sound)


player = Player()


class Controller(BaseHTTPRequestHandler):
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
        player.play()
        self._standardResponse()


HTTPServer(("0.0.0.0", 9900), Controller).serve_forever()

