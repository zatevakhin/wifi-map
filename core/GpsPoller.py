# -*- coding: utf-8 -*-

import threading
import time
from gps import *

from loguru import logger

class GpsPoller(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        try:
            self.session = gps(mode=WATCH_ENABLE)
        except ConnectionError:
            logger.exception("Can't connect to GPSd daemon.")
            self.session = None
            self.working = False

        self.current_value = None
        self.working = True

    def stop_it(self):
        if self.working:
            logger.success("Stopping GPS poller thread...")
            self.working = False

    def get_current_value(self):
       return self.current_value

    def run(self):
        try:
            if not self.session:
                logger.critical("GPSd session is not available!")
                self.stop_it()
                return

            while self.working:
                self.current_value = self.session.next()
                time.sleep(0.2) 
        except StopIteration:
            pass
