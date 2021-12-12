# -*- coding: utf-8 -*-

from .Command import Command
from core import GpsPoller

class CmdGpsGetPosition(Command):

    def __init__(self, storage, position):
        self.ws_clients = storage.get("ws-clients")
        self.position = position

    def execute(self):
        for _, client in self.ws_clients.items():
            client.gps_position.update({
                "latitude": self.position.latitude,
                "longitude": self.position.longitude,
                "altitude": self.position.altitude
            })
