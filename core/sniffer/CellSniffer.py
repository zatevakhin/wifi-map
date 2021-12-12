# -*- coding: utf-8 -*-

from scapy.layers.dot11 import Dot11Beacon
from scapy.layers.dot11 import Dot11
from scapy.layers.eap import EAPOL
from core.util.mac import is_multicast
from functools import reduce
from .types import *

import time

ACCESS_POINT_TTL = 10 * 6
ACCESS_POINT_CLIENT_TTL = 10 * 3


class CellSniffer:

    def __init__(self, sniffer):
        self.__access_points = []
        self.__bssid_list = set()
        self.__client_list = set()
    
    @property
    def access_points(self):
        return self.__access_points

    @property
    def bssid_list(self):
        return self.__bssid_list

    @property
    def client_list(self):
        return self.__client_list

    def __call__(self, pkt):
        if pkt.haslayer(Dot11Beacon):
            beacon = pkt.getlayer(Dot11Beacon)
            bssid = pkt.getlayer(Dot11).addr2

            if bssid not in self.__bssid_list:
                self.__bssid_list.add(bssid)
                ap_stats = beacon.network_stats()
                
                if "country_desc_type" in ap_stats:
                    del ap_stats["country_desc_type"]

                if "country" in ap_stats:
                    del ap_stats["country"]

                if "rates" in ap_stats:
                    del ap_stats["rates"]

                ap_stats.update({"bssid": bssid, "clients": []})

                self.__access_points.append(AccessPoint(**ap_stats))

        
        if pkt.haslayer(Dot11) and pkt.getlayer(Dot11).type == 2 and not pkt.haslayer(EAPOL):
            d11 = pkt.getlayer(Dot11)
            s = d11.addr2
            r = d11.addr1

            tg_bssid = None
            ap_bssid = None

            if s in self.__bssid_list:
                tg_bssid, ap_bssid = r, s
            elif r in self.__bssid_list:
                tg_bssid, ap_bssid = s, r

            if tg_bssid and tg_bssid not in self.__client_list:

                expired_access_points = []

                for access_point in self.__access_points:
                    if access_point.bssid == ap_bssid and not is_multicast(tg_bssid):
                        access_point.add_client(tg_bssid)
                        access_point.update_last_seen()

                        self.__client_list.add(tg_bssid)
                    elif int(time.time()) > (access_point.last_seen + ACCESS_POINT_TTL):
                        expired_access_points.append(access_point)

                for ap in expired_access_points:
                    self.__bssid_list.remove(ap.bssid)
                    self.__access_points.remove(ap)

