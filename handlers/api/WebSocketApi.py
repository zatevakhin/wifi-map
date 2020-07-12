# -*- coding: utf-8 -*-


from tornado import websocket
from core.auxiliary import classproperty
from loguru import logger

import threading
from time import sleep

import json

from queue import Queue
from core.auxiliary import md5

from core import CommandHandler
from core.commands import CmdGpsGetPosition
from enum import IntEnum, auto

class RequestMapData(IntEnum):
    POSITION = auto()
    WIFI = auto()
    VISIBLE_ACCESS_POINTS = auto()


class ConnectedClient:
    def __init__(self):
        self.new_access_points = set()
        self.visible_access_points = list()
        self.gps_position = {
            "latitude": 0,
            "longitude": 0,
            "altitude": 0
        }


class WebSocketApi(websocket.WebSocketHandler):
    connections = set()

    @classproperty
    def location(cls):
        return r"/api/websocket"

    def initialize(self, storage):
        self.storage = storage
        self.cmd = storage.get(CommandHandler.WORKER_NAME)
        self.db = storage.get("db")
        
        self.client_data = ConnectedClient()
    
    def open(self):
        logger.info(f"WebSocket connected ({self})")

        ws_clients = self.storage.get("ws-clients")
        ws_clients.update({ md5(self): self.client_data})

    def on_message(self, message):
        try:
            message = json.loads(message)
            action = int(message.get("action", None))
        except Exception:
            action = None

        if action in [int(RequestMapData.WIFI)]:
            self.send_wifi_updates()

        if action in [int(RequestMapData.POSITION)]:
            self.cmd.put(CmdGpsGetPosition(self.storage))
            self.send_current_position()

        if action in [int(RequestMapData.VISIBLE_ACCESS_POINTS)]:
            self.send_visible_access_points()

    def send_current_position(self):
        position = self.client_data.gps_position
        self.write_message({"return": int(RequestMapData.POSITION), "position": position})

    def send_visible_access_points(self):
        visible_access_points = self.client_data.visible_access_points
        self.write_message({
            "return": int(RequestMapData.VISIBLE_ACCESS_POINTS),
            "devices": visible_access_points
        })

    def send_wifi_updates(self):
        if self.client_data.new_access_points:
            with self.db.connect() as connection:
                record_id_list = ",".join(map(str, self.client_data.new_access_points))

                query = f"""select * from records where id in ({ record_id_list })"""
                records = connection.execute(query).fetchall()

                self.write_message({"return": int(RequestMapData.WIFI), "records": records})

            self.client_data.new_access_points.clear()

    def on_error(self):
        pass

    def on_close(self):
        logger.info(f"WebSocket disconnected ({self})")
        
        ws_clients = self.storage.get("ws-clients")
        ws_clients.pop(md5(self), None)
