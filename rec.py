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
import shutil
from Tail import Tail

class Config:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Terminal real-time recorder backend.")
        self.parser.add_argument("-l", "--lines", dest='lines', default="25")
        self.parser.add_argument("-c", "--cols", dest='cols', default="80")
        self.parser.add_argument("-e", "--env", dest='env', default="")
        self.parser.add_argument("-p", "--pid-file", dest='pid_file', default="/tmp/terminal-dup.pid")
        self.parser.add_argument("-u", "--url-prefix", dest='url_prefix', default="https://jamesits-terminal-duplicator.wilddogio.com")
        self.parser.add_argument("-i", "--identifier", dest='identifier', default=None)
        self.config = vars(self.parser.parse_args())

class TerminalStream (threading.Thread):
    def __init__(self, path, qd=None):
        threading.Thread.__init__(self)
        self.tail_interval = 0.2
        self.monitor_path = path
        self.wait_for_file()
        self.tail = Tail(self.monitor_path)
        self.tail.register_callback(self.__tail_callback)
        self.tuQueue = []
        self.last_update = time.time()
        self.query = QueueDispatcher(self.tuQueue)

    def __tail_callback(self, content):
        #content = content.strip().strip('\n')
        #print(content, file=sys.stderr)
        # print(len(result), result, file=sys.stderr)
        self.last_update = time.time()
        u = TerminalUpdate(content.rstrip("\n"), self.last_update)
        self.tuQueue.append(u)

    def wait_for_file(self):
        print("<waiting for recorder>", file=sys.stderr)
        while not os.path.exists(self.monitor_path):
            time.sleep(1)
        print("<connected to recorder>", file=sys.stderr)

    def run(self):
        try:
            print("<starting query dispatcher>", file=sys.stderr)
            self.query.start()
            print("<starting output monitor>", file=sys.stderr)
            if self.tail_interval:
                self.tail.follow(self.tail_interval)
            else:
                self.tail.follow()
        except FileNotFoundError:
            print("<recorder quit>", file=sys.stderr)
        except KeyboardInterrupt:
            print("<user abort>", file=sys.stderr)

class TerminalUpdate:
    def __init__(self, content="", timestamp=None):
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
                # print("<got no news>", file=sys.stderr)
                time.sleep(self.idle_interval)
            else:
                # print("<got some updates>", file=sys.stderr)
                current_tu = self.queue.pop(0)
                for cb in self.callbacks:
                    cb(self.seq, current_tu)
                self.seq += 1

    def control(self, control_data):
        # print("<got control frame>", file=sys.stderr)
        for cb in self.callbacks:
            cb(self.seq, TerminalUpdate(), control=True, control_data=control_data)
        self.seq += 1

class Previewer:
    def __init__(self, qd):
        qd.registerCallback(self.callback)

    def callback(self, seq, update, control=False, control_data={}):
        if not control:
            print(update, file=sys.stderr)

class RawPreviewer:
    def __init__(self, qd):
        qd.registerCallback(self.callback)

    def callback(self, seq, update, control=False, control_data={}):
        if not control:
            print(update.content.decode(), file=sys.stderr)

class Duplicator:
    def __init__(self, qd, file):
        qd.registerCallback(self.callback)
        self.file = file
        target = open(self.file, "w")
        target.close

    def callback(self, seq, update, control=False, control_data={}):
        if not control:
            with open(self.file, "ab") as target:
                target.write(update.content.decode())

class WilddogUploader:
    def __init__(self, qd, device_name="", config={}):
        self.device_name = device_name
        self.identifier = config['identifier']
        self.init_url = config["url_prefix"] + "/sessions.json"
        # self.init_history_url = config["url_prefix"] + "/sessions/{}/history.json"
        self.update_url = config["url_prefix"] + "/sessions/{0}/history/{1}.json"
        self.setidentifier_url = config["url_prefix"] + "/ids/{0}.json"
        data = {
            "config": config
        }
        data["config"]["device_name"] = device_name
        data["config"]["timestamp"] = time.time()
        data = json.dumps(data)
        print("<connecting to web service>", file=sys.stderr)

        req = requests.post(self.init_url, data=data)
        self.name = req.json()['name']
        if req.status_code != 200:
            print("Request error " + str(req.status_code) + ": " + req.url + req.text, file=sys.stderr)
        # req = requests.post(self.init_history_url.format(self.name), data="{[]}")
        # if req.status_code != 200:
        #     print("Request error " + str(req.status_code) + ": " + req.url + req.text, file=sys.stderr)
        print("<Session ID: {}>".format(self.name), file=sys.stderr)

        if self.identifier:
            data = {
                "name": self.name
            }
            data = json.dumps(data)
            req = requests.put(self.setidentifier_url.format(self.identifier),data=data)
            if req.status_code != 200:
                print("Request error " + str(req.status_code) + ": " + req.url + req.text, file=sys.stderr)
            print("<Session name: {}>".format(self.identifier), file=sys.stderr)
        qd.registerCallback(self.callback)

    def callback(self, seq, update, control=False, control_data={}):
        data={
                "seq": seq,
                "timestamp": update.timestamp,
                # "recv_timestamp": {".sv": "timestamp"},
                "is_control_frame": control,
            }
        if control:
            data['control_data'] = control_data
        else:
            data["raw_content"] = update.content.decode()
            #data["encoded_content"] = base64.b64encode(update.content).decode()
        data = json.dumps(data)
        #print("Sending: " + update.content.decode(), file=sys.stderr)
        req = requests.put(self.update_url.format(self.name, seq), data=data)
        if req.status_code != 200:
            print("Request error " + str(req.status_code) + ": " + req.url + req.text, file=sys.stderr)

if __name__ == "__main__":
    # Quitting handler
    #import atexit
    #@atexit.register
    def exit_handler(signal=None, frame=None):
        print("<program terminating>", file=sys.stderr)
        os.remove(config['pid_file'])
    import signal
    signal.signal(signal.SIGINT, exit_handler)

    config = Config().config
    #print(config, file=sys.stderr)
    with open(config['pid_file'], "w") as target:
        target.write(str(os.getpid()))
    ts = TerminalStream("/tmp/terminal-rec")
    #pr = RawPreviewer(ts.query)
    up = WilddogUploader(ts.query, device_name=socket.gethostname(), config=config)
    ts.start()

    # Handle terminal size change
    def winch_handler(signal, frame):
        # print("Got WINCH", file=sys.stderr)
        time.sleep(1)
        (cols, lines) = shutil.get_terminal_size((80, 25))
        ts.query.control({
            "type": "WINCH",
            "data": {
                "cols": cols,
                "lines": lines,
            },
        })
    signal.signal(signal.SIGWINCH, winch_handler)
