# -*- coding: utf-8 -*-

from loguru import logger
import time

from core.Worker import Worker, WorkerStatus

from core import CommandHandler
from core import commands


WORKER_NAME = "Data Manager"


class DataManager(Worker):

    def __init__(self, storage):
        Worker.__init__(self, name=WORKER_NAME)
        self.set_status(WorkerStatus.WORKING)
        self.storage = storage
        self.current_position = None
        self.current_scanner_result = []
        self.current_sniffer_result = []

    def set_current_gps_state(self, state):
        self.current_gps_state = state

    def set_current_position(self, position):
        self.current_position = position

    def set_current_scanner_result(self, scanner_result):
        self.current_scanner_result = scanner_result

    def set_current_sniffer_result(self, sniffer_result):
        self.current_sniffer_result = sniffer_result

    def stop(self):
        status = self.get_status()
        if status in [WorkerStatus.WORKING, WorkerStatus.IDLE]:
            logger.success(f"Stopping {WORKER_NAME} thread...")
            self.set_status(WorkerStatus.STOPPED)

    def run(self):
        status = self.get_status()

        mgr = self.storage.get(CommandHandler.WORKER_NAME)

        while status in [WorkerStatus.WORKING, WorkerStatus.IDLE]:
            time.sleep(1)

            if self.current_position: # todo: make pos with TTL
                mgr.put(commands.CmdGpsGetPosition(self.storage, self.current_position))

                if self.current_scanner_result:
                    self.handle_scanner_result()
                    # self.current_scanner_result = []

                if self.current_sniffer_result:
                    self.handle_sniffer_result()
                    self.current_sniffer_result = []

    def handle_scanner_result(self):
        mgr = self.storage.get(CommandHandler.WORKER_NAME)
        bssid_list = list(map(lambda  x: str(x.bssid).upper(), self.current_scanner_result + self.current_sniffer_result))
        mgr.put(commands.CmdGetVisibleAccessPoints(self.storage, list(set(bssid_list))))

        mgr.put(commands.CmdSaveAcessPointData(self.storage, self.current_position, self.current_scanner_result))

    def handle_sniffer_result(self):
        mgr = self.storage.get(CommandHandler.WORKER_NAME)
        bssid_list = list(map(lambda  x: str(x.bssid).upper(), self.current_scanner_result + self.current_sniffer_result))
        mgr.put(commands.CmdGetVisibleAccessPoints(self.storage, list(set(bssid_list))))

        mgr.put(commands.CmdSaveAcessPointData(self.storage, self.current_position, self.current_sniffer_result))
