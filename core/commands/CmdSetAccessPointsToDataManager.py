# -*- coding: utf-8 -*-

from .Command import Command
from core import DataManager


class CmdSetAccessPointsToDataManager(Command):

    def __init__(self, storage, access_points):
        Command.__init__(self, storage.get(DataManager.WORKER_NAME))
        self.access_points = access_points

    def execute(self):
        self.receiver.set_current_scanner_result(self.access_points)
