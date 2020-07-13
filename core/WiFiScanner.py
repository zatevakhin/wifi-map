# -*- coding: utf-8 -*-

from wifi import Cell
from wifi.exceptions import InterfaceError
from core.wifi import NetInterface
from core.Worker import Worker, WorkerStatus
from core.auxiliary import classproperty
import time
from collections import namedtuple
from loguru import logger

from core import CommandHandler
from core import GpsPoller

from core import commands


GeoPosition = namedtuple("GeoPosition", ["latitude", "longitude", "altitude"])


WORKER_NAME = "Wi-Fi Scanner"


class WiFiScanner(Worker):


    def __init__(self, storage):
        Worker.__init__(self, name=WORKER_NAME)
        self.storage = storage
        self.cmd = storage.get(CommandHandler.WORKER_NAME)
        self.gps = storage.get(GpsPoller.WORKER_NAME)

        self.status = WorkerStatus.WORKING

    def stop(self):
        if WorkerStatus.WORKING == self.status:
            logger.success("Stopping WiFi scanner thread...")
            self.status = WorkerStatus.STOPPED

    def run(self):
        while WorkerStatus.WORKING == self.status:
            position = self.gps.get_position()
            
            ap_list = self.make_all_interfaces_scan()

            cmd1 = commands.CmdGetVisibleAccessPoints(self.storage, ap_list)
            self.cmd.put(cmd1)

            if not position.latitude or not position.longitude:
                time.sleep(1)
                continue

            cmd2 = commands.CmdSaveScanningResults(self.storage, ap_list)

            self.cmd.put(cmd2)

            time.sleep(1) 

    def make_all_interfaces_scan(self) -> set:
        all_interfaces_ap = set()
        for interface in NetInterface.all():
            ap_list = self.scan_wifi_by_interface(interface)
            all_interfaces_ap = all_interfaces_ap.union(set(ap_list))
        return all_interfaces_ap

    def scan_wifi_by_interface(self, interface):
        try:
            return list(Cell.all(interface))
        except InterfaceError:
            return []