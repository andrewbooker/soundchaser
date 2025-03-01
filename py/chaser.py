#!/usr/bin/python3

import requests
import time
import sounddevice as sd
import threading
import readchar


def UsbAudioDevices():
    usable = {}

    devs = sd.query_devices()
    for d in range(len(devs)):
        dev = devs[d]
        if "USB" in dev["name"] and dev["default_samplerate"] == 44100:
            usable[d] = (dev["name"], int(dev["max_input_channels"]))

    return usable


class MovingAvg():
    def __init__(self, size):
        self.size = size
        self.clear()

    def clear(self):
        self.values = []
        self.avg = 0.0

    def add(self, v):
        self.avg += (v * 1.0 / self.size)
        self.values.append(v)
        if (len(self.values) > self.size):
            p = self.values.pop(0)
            self.avg -= (p * 1.0 / self.size)

    def first(self):
        return self.values[0]

    def value(self):
        return self.avg if (len(self.values) == self.size) else (self.avg * self.size / len(self.values))


class AbsMovingAvg(MovingAvg):
    def __init__(self, size):
        MovingAvg.__init__(self, size)

    def add(self, v):
        self.avg += (abs(v) * 1.0 / self.size)
        self.values.append(v)
        if (len(self.values) > self.size):
            p = self.values.pop(0)
            self.avg -= (abs(p) * 1.0 / self.size)


class Derivative():
    def __init__(self, width):
        self.values = []
        self.val = 0.0
        self.width = width

    def add(self, v):
        self.values.append(v)
        if (len(self.values) > self.width):
            p = self.values.pop(0)
        self.val = (self.values[-1] - self.values[0]) / len(self.values)

    def value(self):
        return self.val


class Threshold():
    def __init__(self, thesholdFn):
        self.fn = thesholdFn
        self.val = 0;

    def add(self, v):
        self.val = v

    def value(self):
        return 1.0 if self.val > self.fn() else 0

    def overshoot(self):
        if self.value() == 0:
            return 0.0
        return (self.val - self.fn()) / (1.0 - self.fn())


class Chaser():
    def __init__(self, consumer, high, low):
        self.avg = AbsMovingAvg(44)
        self.deriv = Derivative(2)
        self.thrOn = Threshold(lambda: high)
        self.thrOff = Threshold(lambda: low)
        self.state = 0
        self.consumer = consumer
        
    def add(self, v):
        self.avg.add(v)
        self.thrOn.add(self.avg.value())
        self.thrOff.add(self.avg.value())
        self.deriv.add(self.avg.value())

        if self.thrOn.value() == 1 and self.state == 0:
            self.state = 1
        elif self.deriv.value() < 0 and self.state == 1:
            self.consumer.on(self.thrOn.overshoot())
            self.state = 2
        elif self.thrOff.value() == 0 and self.state == 2:
            self.state = 0
            self.consumer.off()


class Consumer():
    def __init__(self):
        self.toggle = False

    def on(self, velocity):
        params = {}
        port = 9900 if not self.toggle else 9901
        self.toggle = not self.toggle
        requests.post("http://localhost:%d" % port, json=params)
        print("note on")

    def off(self):
        print("note off")


audioDevices = UsbAudioDevices()
aidx = [k for k in audioDevices.keys()][0]
audioDevice = audioDevices[aidx]
print("using", audioDevice)

consumer = Consumer()
chaser = Chaser(consumer, 0.04, 0.0039)

callback = lambda indata, frames, t, status: [chaser.add(v[0]) for v in indata]

def audioCapture(shouldStop, callback):
    print("starting audio capture")
    with sd.InputStream(samplerate=44100.0, device=aidx, channels=1, callback=callback, blocksize=44) as stream:
        stream.start()
        while not shouldStop.is_set():
            time.sleep(1)


shouldStop = threading.Event()
threads = []
threads.append(threading.Thread(target=audioCapture, args=(shouldStop,callback,), daemon=True))
[t.start() for t in threads]

print("press 'q' to exit")
while not shouldStop.is_set():
    c = readchar.readchar()
    if c == "q":
        print("stopping...")
        shouldStop.set()
        [t.join() for t in threads]



