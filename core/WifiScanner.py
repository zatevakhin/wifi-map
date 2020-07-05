# -*- coding: utf-8 -*-

from wifi import Cell
from wifi.exceptions import InterfaceError
from core.wifi import NetInterface
import threading
import time
from collections import namedtuple
from loguru import logger


GeoPosition = namedtuple("GeoPosition", ["latitude", "longitude", "altitude"])


class WifiScanner(threading.Thread):

    def __init__(self, database, gps):
        threading.Thread.__init__(self)
        self.database = database
        self.gps = gps
        self.working = True

    def stop_it(self):
        if self.working:
            logger.success("Stopping WiFi scanner thread...")
            self.working = False

    def add_ap(self, connection, ap, position):
        query = """INSERT OR IGNORE INTO `records` (
            address, channel, frequency, signal, name, latitude, longitude, altitude
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""

        query_data = [
            ap.address,
            ap.channel,
            float(ap.frequency.split(" ")[0]),
            ap.signal,
            ap.ssid,
            position.latitude,
            position.longitude,
            position.altitude
        ]

        connection.execute(query, query_data)


    def run(self):
        try:
            connection = self.database.connect()
            
            position = None
            while self.working:
                gps = self.gps.get_current_value()

                if not gps:
                    logger.critical("GPS is not available!")
                    self.stop_it()
                    return

                longitude = gps.get("lon", None)
                latitude = gps.get("lat", None)
                altitude = gps.get("alt", None)

                if longitude and latitude and altitude:
                    position = GeoPosition(latitude=latitude, longitude=longitude, altitude=altitude)

                if not position:
                    continue
                
                for interface in NetInterface.all():
                    try:
                        for ap in Cell.all(interface):
                            self.add_ap(connection, ap, position)
                    except InterfaceError:
                        pass

                connection.commit()

                time.sleep(1) 
        except StopIteration:
                pass
