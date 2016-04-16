#!/usr/bin/env python3
import os
import time
import datetime
import threading
import requests
import socket
import base64
import json
import argparse
import sys
import os
from Tail import Tail

class Config:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Terminal real-time recorder backend.")
        self.parser.add_argument("-l", "--lines", dest='lines', default="25")
        self.parser.add_argument("-c", "--cols", dest='cols', default="80")
        self.parser.add_argument("-e", "--env", dest='env', default="")
        self.parser.add_argument("-p", "--pid-file", dest='pid_file', default="/tmp/terminal-dup.pid")
        self.parser.add_argument("-u", "--url-prefix", dest='url_prefix', default="https://jamesits-terminal-duplicator.wilddogio.com")
        self.config = vars(self.parser.parse_args())

class TerminalStream (threading.Thread):
    def __init__(self, path, qd=None):
        threading.Thread.__init__(self)
        self.tail_interval = None
        self.monitor_path = path
        self.wait_for_file()
        self.tail = Tail(self.monitor_path)
        self.tail.register_callback(self.__tail_callback)
        self.tuQueue = []
        self.last_update = time.time()
        self.query = QueueDispatcher(self.tuQueue)

    def __tail_callback(self, content):
        #content = content.strip().strip('\n')
        #print(content)
        # print(len(result), result)
        self.last_update = time.time()
        u = TerminalUpdate(content.rstrip("\n"), self.last_update)
        self.tuQueue.append(u)

    def wait_for_file(self):
        print("<waiting for recorder>")
        while not os.path.exists(self.monitor_path):
            time.sleep(1)
        print("<connected to recorder>")

    def run(self):
        try:
            print("<starting query dispatcher>")
            self.query.start()
            print("<starting output monitor>")
            if self.tail_interval:
                self.tail.follow(self.tail_interval)
            else:
                self.tail.follow()
        except FileNotFoundError:
            print("<recorder quit>")
        except KeyboardInterrupt:
            print("<user abort>")

class TerminalUpdate:
    def __init__(self, content, timestamp=None):
        self.timestamp = timestamp or time.time()
        self.content = content.encode()

    def __str__(self):
        return "\n".join(["[{0}]{1}".format(self.timestamp, x) for x in self.content.decode().split("\n")]).rstrip("\n")

class QueueDispatcher (threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.callbacks = []
        self.seq = 0
        self.idle_interval = 0.1
        self.queue = queue
        #self.exit_flag = threading.Event()

    def registerCallback(self, cb):
        self.callbacks.append(cb)

    def removeCallback(self, cb):
        self.callbacks.remove(cb)

    def run(self):
        while True:
            if len(self.queue) == 0:
                #print("<got no news>")
                time.sleep(self.idle_interval)
            else:
                #print("<got some updates>")
                current_tu = self.queue.pop(0)
                for cb in self.callbacks:
                    cb(current_tu, self.seq)
                self.seq += 1

class Previewer:
    def __init__(self, qd):
        qd.registerCallback(self.callback)

    def callback(self, update, seq):
        print(update)

class RawPreviewer:
    def __init__(self, qd):
        qd.registerCallback(self.callback)

    def callback(self, update, seq):
        print(update.content.decode())

class Duplicator:
    def __init__(self, qd, file):
        qd.registerCallback(self.callback)
        self.file = file
        target = open(self.file, "w")
        target.close

    def callback(self, update, seq):
        with open(self.file, "ab") as target:
            target.write(update.content.decode())

class WilddogUploader:
    def __init__(self, qd, device_name="", config={}):
        self.device_name = device_name
        self.init_url = config["url_prefix"] + "/sessions.json"
        self.update_url = config["url_prefix"] + "/sessions/{}/{}.json"
        data = {
            "config": config
        }
        data["config"]["device_name"] = device_name
        data["config"]["timestamp"] = time.time()
        data = json.dumps(data)
        print("<connecting to web service>")
        req = requests.post(self.init_url,data=data)
        self.name = req.json()['name']
        if req.status_code != 200:
            print("Request error " + str(r.status_code) + ": " + r.text)
        print("<Session ID: {}>".format(self.name))
        qd.registerCallback(self.callback)

    def callback(self, update, seq):
        data={
                "seq": seq,
                "timestamp": update.timestamp,
                "raw_content": update.content.decode(),
                "content": base64.b64encode(update.content).decode()
            }
        data = json.dumps(data)
        req = requests.put(self.update_url.format(self.name, seq), data=data)
        if req.status_code != 200:
            print("Request error " + str(req.status_code) + ": " + req.text)

if __name__ == "__main__":
    config = Config().config
    #print(config)
    with open(config['pid_file'], "w") as target:
        target.write(str(os.getpid()))
    ts = TerminalStream("/tmp/terminal-rec")
    #pr = Previewer(ts.query)
    up = WilddogUploader(ts.query, device_name=socket.gethostname(), config=config)
    ts.start()
    import atexit
    @atexit.register
    def exit_handler():
        print("<program terminating>")
        os.remove(config['pid_file'])
