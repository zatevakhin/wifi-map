# -*- coding: utf-8 -*-

import threading
import time
from gps import *


class GpsPoller(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.session = gps(mode=WATCH_ENABLE)
        self.current_value = None
        self.working = True

    def stop_it(self):
        self.working = False

    def get_current_value(self):
       return self.current_value

    def run(self):
        try:
            while self.working:
                self.current_value = self.session.next()
                time.sleep(0.2) 
        except StopIteration:
            pass
