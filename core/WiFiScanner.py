# -*- coding: utf-8 -*-

from wifi import Cell
from wifi.exceptions import InterfaceError
from pyiw import interface as Ifc
from core.Worker import Worker, WorkerStatus
from core.auxiliary import classproperty
import time
from collections import namedtuple
from loguru import logger
from core.sniffer.types import AccessPoint
from core import CommandHandler
from core import GpsPoller

from core import commands


GeoPosition = namedtuple("GeoPosition", ["latitude", "longitude", "altitude"])


WORKER_NAME = "Wi-Fi Scanner"


class WiFiScanner(Worker):
    def __init__(self, storage):
        Worker.__init__(self, name=WORKER_NAME)
        self.storage = storage
        self.status = WorkerStatus.WORKING

    def stop(self):
        if WorkerStatus.WORKING == self.status:
            logger.success(f"Stopping {WORKER_NAME} thread...")
            self.status = WorkerStatus.STOPPED

    def run(self):
        mgr = self.storage.get(CommandHandler.WORKER_NAME)

        while WorkerStatus.WORKING == self.status:

            access_points = self.make_all_interfaces_scan()

            if access_points:
                access_points = list(map(lambda x: AccessPoint(x.ssid, x.address, x.channel, x.encryption_type), access_points))
                mgr.put(commands.CmdSetAccessPointsToDataManager(self.storage, access_points))

            time.sleep(1) 

    def make_all_interfaces_scan(self) -> set:
        all_interfaces_ap = set()
        for interface in Ifc.all_wireless(filter_enabled=True, filter_monitor=True):

            ap_list = self.scan_wifi_by_interface(interface)
            all_interfaces_ap = all_interfaces_ap.union(set(ap_list))
        return all_interfaces_ap

    def scan_wifi_by_interface(self, interface):
        try:
            return list(Cell.all(interface))
        except InterfaceError:
            return []