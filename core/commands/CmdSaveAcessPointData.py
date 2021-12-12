# -*- coding: utf-8 -*-

from .Command import Command
from core import WiFiScanner
from loguru import logger
from datetime import datetime
import sqlite3
import math


CHECK_ACCESS_POINT = '''
SELECT * FROM AccessPoint WHERE bssid=? LIMIT 1;
'''

ADD_ACCESS_POINT   = '''
INSERT INTO AccessPoint (bssid) VALUES(?);
'''

ADD_ACCESS_POINT_SSID = '''
INSERT OR IGNORE INTO WithSsid (ap_id, ssid) VALUES(?, ?);
'''

ADD_ACCESS_POINT_CHANNEL = '''
INSERT OR IGNORE INTO AtChannel (ap_id, channel) VALUES(?, ?);
'''

ADD_ACCESS_POINT_ENCRYPTION = '''
INSERT OR IGNORE INTO WithEncryption (ap_id, crypto) VALUES(?, ?);
'''

ADD_ACCESS_POINT_GEOPOSITION = '''
INSERT OR IGNORE INTO AtGeoposition (ap_id, latitude, longitude) VALUES(?, ?, ?);
'''

CHECK_ACCESS_POINT_GEOPOSITION = '''
SELECT * FROM AtGeoposition WHERE ap_id=? LIMIT 1;
'''

UPDATE_ACCESS_POINT_GEOPOSITION = '''
UPDATE AtGeoposition SET latitude=?, longitude=?, t_stamp=datetime('now', 'localtime') WHERE ap_id=?;
'''

REMOVE_ACCESS_POINT_GEOPOSITION = '''
DELETE FROM AtGeoposition WHERE ap_id=?;
'''

class CmdSaveAcessPointData(Command):

    def __init__(self, storage, position, ap_list):
        Command.__init__(self, storage.get(WiFiScanner.WORKER_NAME))
        self.db = storage.get("db")
        self.ap_list = ap_list
        self.position = position

    def execute(self):
        with self.db.connect() as connection:
            self.save_results(connection)

    def save_results(self, connection):
        cursor = connection.cursor()

        added_ap_list = set()
        for item in self.ap_list:
            is_new, ap = self.add_access_point_data(cursor, item)

            if is_new and ap:
                added_ap_list.add(ap["id"])

        # for _, client in self.ws_clients.items():
        #     client.new_access_points = client.new_access_points.union(added_ap_list)


    def get_access_point(self, cursor, item):
        return cursor.execute(CHECK_ACCESS_POINT, [item.bssid]).fetchone() or {}

    def get_access_point_geoposition(self, cursor, access_point):
        return cursor.execute(CHECK_ACCESS_POINT_GEOPOSITION, [access_point["id"]]).fetchone() or {}

    def add_access_point_data(self, cursor, item):
        access_point = self.get_access_point(cursor, item)

        is_new = False

        if not access_point:
            access_point = self.save_access_point(cursor, item)
            is_new = True

        self.save_access_point_ssid(cursor, item, access_point)
        self.save_access_point_channel(cursor, item, access_point)
        self.save_access_point_encryption(cursor, item, access_point)
        self.save_access_point_geoposition(cursor, item, access_point)

        return is_new, access_point

    def save_access_point(self, cursor, item) -> int:
        cursor.execute(ADD_ACCESS_POINT, [item.bssid])
        return {"id": cursor.lastrowid, "bssid": item.bssid}

    def save_access_point_ssid(self, cursor, item, access_point):
        cursor.execute(ADD_ACCESS_POINT_SSID, [access_point["id"], item.ssid])
        return {"id": access_point["id"], "ap_id": access_point["id"], "ssid": item.ssid}

    def save_access_point_channel(self, cursor, item, access_point):
        cursor.execute(ADD_ACCESS_POINT_CHANNEL, [
            access_point["id"], item.channel
        ])

        return {
            "id": access_point["id"],
            "channel": item.channel
        }

    def save_access_point_encryption(self, cursor, item, access_point):
        cursor.execute(ADD_ACCESS_POINT_ENCRYPTION, [
            access_point["id"], int(item.crypto.value)
        ])

        return {
            "id": access_point["id"],
            "crypto": int(item.crypto.value),
        }

    def save_access_point_geoposition(self, cursor, item, access_point):

        is_latitude_close = math.isclose(self.position.latitude, 0.0, rel_tol=1e-1)
        is_longitude_close = math.isclose(self.position.longitude, 0.0, rel_tol=1e-1)
        
        if is_latitude_close and is_longitude_close:
            return None

        ap_geoposition = self.get_access_point_geoposition(cursor, access_point)

        if ap_geoposition:
            cursor.execute(UPDATE_ACCESS_POINT_GEOPOSITION, [
                    self.position.latitude,
                    self.position.longitude,
                    access_point["id"]
                ])
        else:
            cursor.execute(ADD_ACCESS_POINT_GEOPOSITION, [
                access_point["id"],
                self.position.latitude,
                self.position.longitude
            ])

        return {
            "id": access_point["id"],
            "latitude": self.position.latitude,
            "longitude": self.position.longitude,
        }
