# -*- coding:utf-8 -*-
import make_mfcc
from scikits.talkbox.features import mfcc
import numpy as np
import audioop
import time
import threading
import json


class Analyzer(object):

    CHUNK = 512
    RMS_THRESHOLD = 50
    KNOCK_LENGTH_RANGE = (10, 50)
    DISTANCE_THRESHOLD = 1.6
    AUTO_CLEAR_SEC = 2
    AUTO_UNREGISTER_SEC = 10
    EUCLIDEAN_WEIGHT = 2
    EXPECT_PATTERN = [1,1,1,0,0,0]

    knocking = []       # ノック音発生中のサンプルを保存しておく
    knock_list = []     # ノック判定した音の中央MFCC値と検知時間を保存
    registered_mfcc = None # (mfcc, mfcc) でつかう
    stream = None
    socket = None
    clear_timer = None
    last_registered_knock_time = None

    def __init__(self, stream, socket):
        self.stream = stream
        self.socket = socket
        self.clear_timer = self.set_interval(self.auto_clear_knocklist, 1)

    def start_detection(self):
        while self.stream.is_active():
            data = self.stream.read(self.CHUNK)
            rms = audioop.rms(data, 2)
            sig = np.frombuffer(data, dtype="int16")
            ceps, mspec, spec = mfcc(sig)

            if rms > self.RMS_THRESHOLD:
                self.knocking.extend(ceps)
            else:
                if self.knocking and len(self.knocking) in range(self.KNOCK_LENGTH_RANGE[0], self.KNOCK_LENGTH_RANGE[1]):
                    # ここでKnockのMFCCを算出する
                    center_mfcc = make_mfcc.convert_center_mfcc(self.knocking)
                    # KnockListに追加する
                    self.append_knock_list((center_mfcc, time.time()))
                    # Knock event
                    self.on_knock()
                    print len(self.knock_list)
                    self.check_pattern()


                self.knocking = []

    def check_pattern(self):
        if len(self.knock_list) < len(self.EXPECT_PATTERN):
            return
        exp_btw = self.pattern2between(self.EXPECT_PATTERN)
        btw = list()
        btw_log = list()
        for i, v in enumerate(self.knock_list):
            if i is not 0:
                dis = self.calc_mfcc_distance(self.knock_list[i-1][0], v[0])
                print self.knock_list[i-1][0], v[0]
                print dis
                btw.append(0 if dis < self.DISTANCE_THRESHOLD else 1)
                btw_log.append((0 if dis < self.DISTANCE_THRESHOLD else 1, dis))
        if exp_btw == btw:
            self.register()
        self.knock_list = []

    def register(self):
        calc = ([],[])
        for i, v in enumerate(self.EXPECT_PATTERN):
            if v is 0:
                calc[0].append(self.knock_list[i][0])
            elif v is 1:
                calc[1].append(self.knock_list[i][0])
        self.registered_mfcc = (make_mfcc.convert_center_mfcc(calc[0]), make_mfcc.convert_center_mfcc(calc[1]))
        self.last_registered_knock_time = time.time()
        msg = {
            'event': 'register'
        }
        msg = json.dumps(msg)
        self.socket.send(msg)

    def on_knock(self):
        msg = {
            'event': 'knock',
            'type': self.compare_registered_knock(self.knock_list[-1][0])
            # 'mfcc': self.knock_list[-1][0].tolist()
        }
        print msg['type']
        msg = json.dumps(msg)
        self.socket.send(msg)

    def compare_registered_knock(self, knock):
        if self.registered_mfcc is None:
            return False
        diff = self.calc_mfcc_distance(self.registered_mfcc[0], knock)
        if diff < self.DISTANCE_THRESHOLD:
            self.last_registered_knock_time = time.time()
            return 'A'
        diff = self.calc_mfcc_distance(self.registered_mfcc[1], knock)
        if diff < self.DISTANCE_THRESHOLD:
            self.last_registered_knock_time = time.time()
            return 'B'
        return False

    def auto_clear_knocklist(self):
        if self.knock_list:
            diff = time.time() - self.knock_list[-1][1]
            if diff > self.AUTO_CLEAR_SEC:
                print 'clear_knock_list'
                self.knock_list = []
                msg = {
                    'event': 'clear_knock_list'
                }
                msg = json.dumps(msg)
                self.socket.send(msg)
        if self.last_registered_knock_time is not None:
            diff = time.time() - self.last_registered_knock_time
            if diff > self.AUTO_UNREGISTER_SEC and self.registered_mfcc is not None:
                self.last_registered_knock_time = None
                self.registered_mfcc = None
                print 'unregister_knock'
                msg = {
                    'event': 'unregister'
                }
                msg = json.dumps(msg)
                self.socket.send(msg)

    def set_interval(self, func, sec):
        def func_wrapper():
            self.set_interval(func, sec)
            func()
        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t

    def append_knock_list(self, knock):
        self.knock_list.append(knock)
        self.knock_list = self.knock_list[-len(self.EXPECT_PATTERN):]

    def pattern2between(self, pattern):
        h = list()
        for i,v in enumerate(pattern):
            if i is 0: continue
            h.append(0 if v is pattern[i-1] else 1)
        return h

    def calc_mfcc_distance(self, a, b):
        return np.sqrt(np.abs(np.power(a-b, self.EUCLIDEAN_WEIGHT)).sum())
