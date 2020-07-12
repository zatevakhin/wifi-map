# -*- coding: utf-8 -*-

from .Command import Command
from core import GpsPoller

class CmdGpsGetPosition(Command):

    def __init__(self, storage):
        Command.__init__(self, storage.get(GpsPoller.WORKER_NAME))
        self.ws_clients = storage.get("ws-clients")

    def execute(self):
        position = self.receiver.get_position()

        for _, client in self.ws_clients.items():
            client.gps_position.update({
                "latitude": position.latitude,
                "longitude": position.longitude,
                "altitude": position.altitude
            })
