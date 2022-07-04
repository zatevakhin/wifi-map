# -*- coding: utf-8 -*-


from tornado import websocket
from core.auxiliary import classproperty
from loguru import logger

import threading
from time import sleep

import json

from core.GpsPoller import GpsStatus
from queue import Queue
from core.auxiliary import md5

from core import CommandHandler
from enum import IntEnum, auto

from pyiw import interface as Ifc
from pyiw.types import *

class RequestMapData(IntEnum):
    POSITION = auto()
    WIFI = auto()
    VISIBLE_ACCESS_POINTS = auto()
    AVAILABLE_WIRELESS_INTERFACES = auto()

    DEVICE_ENABLE = auto()
    DEVICE_DISABLE = auto()
    DEVICE_ADD_MONITOR = auto()
    DEVICE_REMOVE_MONITOR = auto()
    DEVICE_SET_CHANNEL = auto()

    STATUS_GPS = auto()
    STATUS_SERVICES = auto()
    MOVE_UPDATE = auto()
    SHOW_ACTIVE = auto()


class ConnectedClient:
    def __init__(self):
        self.new_access_points = set()
        self.visible_access_points = list()
        self.gps_position = {
            "latitude": 0,
            "longitude": 0,
            "altitude": 0
        }

        self.gps_status = GpsStatus.DISCONNECTED

        self.ap_in_bounds = set()


class WebSocketApi(websocket.WebSocketHandler):

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

        # Send initial data
        self.send_all_acess_points()
        self.send_current_gps_status()
        self.send_current_position()
        self.send_available_wireless_interfaces()


    def on_message(self, message):
        try:
            message = json.loads(message)
            action = int(message.get("action", None))
        except Exception:
            action = None

        if action in [int(RequestMapData.WIFI)]:
            self.send_wifi_updates()
        elif action in [int(RequestMapData.POSITION)]:
            self.send_current_position()
        elif action in [int(RequestMapData.VISIBLE_ACCESS_POINTS)]:
            self.send_visible_access_points()
        elif action in [int(RequestMapData.AVAILABLE_WIRELESS_INTERFACES)]:
            self.send_available_wireless_interfaces()
        elif action in [int(RequestMapData.DEVICE_ENABLE)]:
            Ifc.set_state(message["device"], InterfaceState.UP)
        elif action in [int(RequestMapData.DEVICE_DISABLE)]:
            Ifc.set_state(message["device"], InterfaceState.DOWN)
        elif action in [int(RequestMapData.DEVICE_ADD_MONITOR)]:
            Ifc.add_monitor(message["device"], f"{message['device']}_mon")
        elif action in [int(RequestMapData.STATUS_GPS)]:
            self.send_current_gps_status()
        elif action in [int(RequestMapData.STATUS_SERVICES)]:
            self.send_services_status()
        elif action in [int(RequestMapData.MOVE_UPDATE)]:
            self.send_select_from_bounds(message.get("bounds", []))
        elif action in [int(RequestMapData.SHOW_ACTIVE)]:
            self.send_active_access_points()
        else:
            logger.error(message)

    def send_available_wireless_interfaces(self):

        interfaces = {}

        for ifc in Ifc.all_wireless():
            flags = Ifc.get_flags(ifc)

            interfaces.update({
                ifc: {
                    "enabled": InterfaceFlags.UP in flags,
                    "monitor": Ifc.is_monitor(ifc),
                    "monitor_available": Ifc.is_support_monitor(ifc)
                }
            })

        self.write_message({
            "return": int(RequestMapData.AVAILABLE_WIRELESS_INTERFACES),
            "interfaces": interfaces
            })

    def send_current_gps_status(self):
        status = self.client_data.gps_status
        self.write_message({"return": int(RequestMapData.STATUS_GPS), "status": status})

    def send_current_position(self):
        position = self.client_data.gps_position
        self.write_message({"return": int(RequestMapData.POSITION), "position": position})

    def send_visible_access_points(self):
        visible_access_points = self.client_data.visible_access_points
        self.write_message({
            "return": int(RequestMapData.VISIBLE_ACCESS_POINTS),
            "devices": visible_access_points
        })

    def send_all_acess_points(self):
        with self.db.connect() as connection:
            records = connection.execute(f'''
                SELECT * FROM
                    AccessPoint AS ap

                    LEFT JOIN (
                        SELECT id, ap_id, ssid FROM WithSsid GROUP BY ap_id ORDER BY id DESC
                    ) s ON s.ap_id = ap.id

                    LEFT JOIN (
                        SELECT id, ap_id, channel FROM AtChannel GROUP BY ap_id ORDER BY id DESC
                    ) c ON c.ap_id = ap.id

                    LEFT JOIN (
                        SELECT id, ap_id, crypto FROM WithEncryption GROUP BY ap_id ORDER BY id DESC
                    ) e ON e.ap_id = ap.id

                    LEFT JOIN (
                        SELECT id, ap_id, latitude, longitude, t_stamp FROM AtGeoposition GROUP BY ap_id ORDER BY t_stamp ASC
                    ) g ON g.ap_id = ap.id;
            ''').fetchall()

            self.write_message({"return": int(RequestMapData.WIFI), "records": records})

    def send_wifi_updates(self):
        if self.client_data.new_access_points:
            with self.db.connect() as connection:
                record_id_list = ",".join(map(str, self.client_data.new_access_points))

                records = connection.execute(f'''
                    SELECT * FROM
                        AccessPoint AS ap

                        LEFT JOIN (
                            SELECT ap_id, ssid FROM WithSsid GROUP BY ap_id ORDER BY id DESC
                        ) s ON s.ap_id = ap.id

                        LEFT JOIN (
                            SELECT ap_id, channel FROM AtChannel GROUP BY ap_id ORDER BY id DESC
                        ) c ON c.ap_id = ap.id

                        LEFT JOIN (
                            SELECT ap_id, crypto FROM WithEncryption GROUP BY ap_id ORDER BY id DESC
                        ) e ON e.ap_id = ap.id

                        LEFT JOIN (
                            SELECT ap_id, latitude, longitude FROM AtGeoposition GROUP BY ap_id ORDER BY t_stamp ASC
                        ) g ON g.ap_id = ap.id

                    WHERE id IN ({ record_id_list });
                ''').fetchall()

                self.write_message({"return": int(RequestMapData.WIFI), "records": records})

            self.client_data.new_access_points.clear()

    def send_services_status(self):
        services = self.storage.get("services")
        services_list = list(map(lambda service: (service[0], int(service[1].get_status().value)), services))

        self.write_message({"return": int(RequestMapData.STATUS_SERVICES), "services": services_list})

    def send_select_from_bounds(self, bounds):

        with self.db.connect() as connection:
            records = connection.execute(f'''
            SELECT bssid,latitude,longitude,ssid,channel,crypto FROM
                AccessPoint AS ap
                JOIN AtGeoposition as g ON g.ap_id = ap.id
                JOIN WithSsid as s ON s.ap_id = ap.id
                JOIN AtChannel as c ON c.ap_id = ap.id
                JOIN WithEncryption as e ON e.ap_id = ap.id
            WHERE latitude <= ? AND longitude <= ? AND latitude >= ? AND longitude >= ?
            ''', bounds).fetchall()

            in_bounds = self.client_data.ap_in_bounds
            new_in_bounds = set(map(lambda item: item.get("bssid"), records))

            removed = in_bounds - new_in_bounds
            added = new_in_bounds - in_bounds

            for item in removed:
                in_bounds.remove(item)

            for item in added:
                in_bounds.add(item)

            self.client_data.ap_in_bounds = in_bounds

            data = []
            for item in records:
                bssid = item.get("bssid")
                if bssid in added:
                    data.append(item)


            self.write_message({"return": int(RequestMapData.MOVE_UPDATE), "removed": list(removed), "added": data, "count": len(data)})

    def send_active_access_points(self):
        visible_access_points = self.client_data.visible_access_points
        self.write_message({"return": int(RequestMapData.SHOW_ACTIVE), "active": visible_access_points})

    def on_error(self):
        pass

    def on_close(self):
        logger.info(f"WebSocket disconnected ({self})")

        ws_clients = self.storage.get("ws-clients")
        ws_clients.pop(md5(self), None)
