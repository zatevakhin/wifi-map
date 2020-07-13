# -*- coding: utf-8 -*-

from .Command import Command
from core import GpsPoller
from core import WiFiScanner
from random import uniform as float_rand


QUERY_CHECK = """SELECT * FROM `records` WHERE address=? AND channel=? AND name=? LIMIT 1;"""
QUERY_ADD = """INSERT INTO `records` (
    address, channel, frequency, signal, name, latitude, longitude, altitude
) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""


class CmdSaveScanningResults(Command):

    def __init__(self, storage, ap_list):
        Command.__init__(self, storage.get(WiFiScanner.WORKER_NAME))
        self.db = storage.get("db")
        self.gps = storage.get(GpsPoller.WORKER_NAME)
        self.ws_clients = storage.get("ws-clients")
        self.ap_list = ap_list

    def execute(self):
        with self.db.connect() as connection:
            self.save_results(connection)

    def save_results(self, connection):
        cursor = connection.cursor()

        added_ap_list = set()
        for ap in self.ap_list:
            if not self.is_item_exists(cursor, ap):
                record_id = self.save_one_item(cursor, ap)
                added_ap_list.add(record_id)

        connection.commit()

        for _, client in self.ws_clients.items():
            client.new_access_points = client.new_access_points.union(added_ap_list)

    def is_item_exists(self, cursor, item) -> bool:
        record_unique = [item.address, item.channel, item.ssid]
        return cursor.execute(QUERY_CHECK, record_unique).fetchone()

    def save_one_item(self, cursor, item) -> int:
        position = self.gps.get_position()

        query_data = [
            item.address,
            item.channel,
            float(item.frequency.split(" ")[0]),
            item.signal,
            item.ssid,
            position.latitude + float_rand(-0.0005, 0.0005),
            position.longitude + float_rand(-0.0005, 0.0005),
            position.altitude
        ]

        cursor.execute(QUERY_ADD, query_data)
        return cursor.lastrowid

