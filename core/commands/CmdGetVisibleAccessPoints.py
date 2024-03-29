# -*- coding: utf-8 -*-

from .Command import Command
from core import WiFiScanner


class CmdGetVisibleAccessPoints(Command):

    def __init__(self, storage, ap_list):
        Command.__init__(self, storage.get(WiFiScanner.WORKER_NAME))
        self.ws_clients = storage.get("ws-clients")
        self.ap_list = ap_list

    def execute(self):
        for _, client in self.ws_clients.items():
            client.visible_access_points = self.ap_list
