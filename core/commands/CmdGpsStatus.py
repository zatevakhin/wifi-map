# -*- coding: utf-8 -*-

from .Command import Command
from core import GpsPoller

class CmdGpsStatus(Command):

    def __init__(self, storage, status):
        self.ws_clients = storage.get("ws-clients")
        self.status = status

    def execute(self):
        for _, client in self.ws_clients.items():
            client.gps_status = self.status
