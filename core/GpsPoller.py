# -*- coding: utf-8 -*-

from collections import namedtuple
from core.auxiliary import classproperty
from core.Worker import Worker, WorkerStatus
from time import sleep

import gpsd # make own gpsd adapter or find better
from loguru import logger
from enum import IntEnum, auto

from core import commands
from core import CommandHandler


GeoPosition = namedtuple("GeoPosition", ["latitude", "longitude", "altitude"])


WORKER_NAME = "GPS Poller"
DEFAULT_POSITION = GeoPosition(0, 0, 0)


class GpsStatus(IntEnum):
    DISCONNECTED = auto()
    ZERO_DATA = auto()
    NO_2D_FIX = auto()
    NO_3D_FIX = auto()
    FULL_DATA = auto()


class GpsPoller(Worker):

    def __init__(self, storage):
        Worker.__init__(self, name=WORKER_NAME)
        self.storage = storage
        self.current = None

    def __try_connect(self):
        mgr = self.storage.get(CommandHandler.WORKER_NAME)

        try:
            gpsd.connect()
            self.set_status(WorkerStatus.WORKING)

            mgr.put(commands.CmdGpsStatus(self.storage, GpsStatus.ZERO_DATA))
        except ConnectionRefusedError:
            logger.exception("GPS not connected!")
            self.set_status(WorkerStatus.ERROR)

            mgr.put(commands.CmdGpsStatus(self.storage, GpsStatus.DISCONNECTED))


    def stop(self):
        status = self.get_status()
        if status in [WorkerStatus.WORKING]:
            logger.success("Stopping GPS poller thread...")
            self.set_status(WorkerStatus.STOPPED)

    def get_position(self):
        status = GpsStatus.ZERO_DATA
        position = DEFAULT_POSITION

        if self.current:
            try:
                position = GeoPosition(*self.current.position(), self.current.altitude())
                status = GpsStatus.FULL_DATA
            except gpsd.NoFixError as e:
                if f"{e}" in ["Needs at least 3D fix"]:
                    position = GeoPosition(*self.current.position(), 0)
                    status = GpsStatus.NO_3D_FIX

            if position != DEFAULT_POSITION:
                try:
                    position = GeoPosition(*self.current.position(), 0)
                    status = GpsStatus.FULL_DATA
                except gpsd.NoFixError as e:
                    if f"{e}" in ["Needs at least 2D fix"]:
                        position = GeoPosition(*self.current.position(), 0)
                        status = GpsStatus.NO_2D_FIX

        return status, position

    def run(self):
        status = self.get_status()
        self.__try_connect()

        while status in [WorkerStatus.ERROR]:
            self.__try_connect()
            if status in [WorkerStatus.ERROR]:
                logger.warning("Trying reconnect to GPSd server...")
                sleep(10)

        status = self.get_status()
        print(f"status: {status}")

        while status in [WorkerStatus.WORKING]:
            try:
                self.current = gpsd.get_current()
            except UserWarning as e:
                logger.warning(f"{e}")

            gps_status, position = self.get_position()

            mgr = self.storage.get(CommandHandler.WORKER_NAME)

            if position != DEFAULT_POSITION:
                mgr.put(commands.CmdSetPositionToDataManager(self.storage, position))
            else:
                logger.warning("No correct geo position.")

            mgr.put(commands.CmdGpsStatus(self.storage, gps_status))

            sleep(1)
