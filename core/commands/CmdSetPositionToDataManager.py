# -*- coding: utf-8 -*-

from .Command import Command
from core import DataManager


class CmdSetPositionToDataManager(Command):

    def __init__(self, storage, position):
        Command.__init__(self, storage.get(DataManager.WORKER_NAME))
        self.position = position

    def execute(self):
        self.receiver.set_current_position(self.position)
