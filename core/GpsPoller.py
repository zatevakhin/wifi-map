# -*- coding: utf-8 -*-

from collections import namedtuple
from core.auxiliary import classproperty
from core.Worker import Worker, WorkerStatus
from time import sleep

import gpsd # make own gpsd adapter or find better
from loguru import logger
from enum import IntEnum, auto


GeoPosition = namedtuple("GeoPosition", ["latitude", "longitude", "altitude"])


WORKER_NAME = "GPS Poller"


class GpsPoller(Worker):

    def __init__(self):
        Worker.__init__(self, name=WORKER_NAME)
        self.current = None
        self.__try_connect()

    def __try_connect(self):
        try:
            gpsd.connect()
            self.status = WorkerStatus.WORKING
        except ConnectionRefusedError:
            logger.exception("GPS not connected!")
            self.status = WorkerStatus.ERROR

    def stop(self):
        if WorkerStatus.WORKING == self.status:
            logger.success("Stopping GPS poller thread...")
            self.status = WorkerStatus.STOPPED

    def get_position(self):
        if not self.current:
            return GeoPosition(0, 0, 0)

        try:
            (latitude, longitude, altitude) = *self.current.position(), self.current.altitude()
        except Exception as e:
            if f"{e}" in ["Needs at least 3D fix"]:
                (latitude, longitude, altitude) = *self.current.position(), 0
            else:
                return GeoPosition(0, 0, 0)

        return GeoPosition(latitude=latitude, longitude=longitude, altitude=altitude)

    def run(self):
        # if WorkerStatus.ERROR == self.status:
        #     self.stop()

        while WorkerStatus.ERROR == self.status:
            self.__try_connect()
            if WorkerStatus.ERROR == self.status:
                logger.warning("Trying reconnect to GPSd server...")
                sleep(10) # every 10s.

        while WorkerStatus.WORKING == self.status:
            try:
                self.current = gpsd.get_current()
            except UserWarning as e:
                logger.warning(f"{e}")

            sleep(0.5) 
