# -*- coding: utf-8 -*-

from .Command import Command
from core import DataManager


class CmdSetSnifferResultToDataManager(Command):

    def __init__(self, storage, sniffer_result):
        Command.__init__(self, storage.get(DataManager.WORKER_NAME))
        self.sniffer_result = sniffer_result

    def execute(self):
        self.receiver.set_current_sniffer_result(self.sniffer_result)
