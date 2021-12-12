# -*- coding: utf-8 -*-

from enum import IntEnum, Enum, auto
from multimethod import multimethod
from time import time

def map_encryption_to_enum(crypto):
    if not crypto: crypto = "OPN"
    crypto = ".".join([crypto, [crypto]][isinstance(crypto, str)])

    if crypto in ["OPN"]:
        return AccessPointEncryption.OPEN
    elif crypto in ["wep"]:
        return AccessPointEncryption.WEP
    elif crypto in ["WPA/PSK", "wpa"]:
        return AccessPointEncryption.WPA
    elif crypto in ["WPA2/PSK", "wpa2"]:
        return AccessPointEncryption.WPA2
    elif crypto in ["WPA2/PSK.WPA/PSK", "WPA/PSK.WPA2/PSK"]:
        return AccessPointEncryption.WPA_WPA2
    else:
        assert True, "Should not happend!"

    return crypto

class AccessPoint:
    def __init__(self, ssid, bssid, channel, crypto, **argv):
        self.ssid = ssid
        self.bssid = bssid
        self.channel = channel
        self.crypto = map_encryption_to_enum(crypto)

        self.clients = []

        self.first_seen = int(time())
        self.last_seen = int(time())

    def update_last_seen(self):
        self.last_seen = int(time())

    def add_client(self, client_mac):
        self.clients.append(AccessPointClient(client_mac))

    def __repr__(self):
        return f"<AccessPoint {self.bssid}/{self.channel} ({self.ssid}) {self.crypto}, clients:{len(self.clients)}>"

class AccessPointClient:
    def __init__(self, mac):
        self.mac = mac

    def __eq__(self, other):
        return self.mac == other.mac

    def __repr__(self):
        return f"<Client {self.mac}>"

class AccessPointEncryption(Enum):
    OPEN = auto()
    WEP = auto()
    WPA = auto()
    WPA2 = auto()
    WPA_WPA2 = auto()


class PacketFiled(IntEnum):
    SSID = 0
    CHANNEL = 3


class CellClientPair:
    def __init__(self, cell: str, client: str):
        self.client = client.lower()
        self.cell = cell.lower()

    def __eq__(self, other):
        return self.cell == other.cell and self.client == other.client

    def __repr__(self):
        return f"<{self.cell} / {self.client}>"


class FourSidedHandshake:
    def __init__(self):
        self.one = None
        self.two = None
        self.three = None
        self.four = None
    
    @property
    def packets(self):
        return [self.one, self.two, self.three, self.four]

    def __repr__(self):
        handshakes = tuple(map(lambda x: int(bool(x)), self.packets))
        return f"<{handshakes}>"


class HandshakeCapture:

    @multimethod
    def __init__(self):
        self.beacon = None
        self.handshake = FourSidedHandshake()

    @multimethod
    def __init__(self, cell: str, client: str):
        self.__init__(CellClientPair(cell, client))
    
    @multimethod
    def __init__(self, pair: CellClientPair):
        self.__init__()
        self.pair = pair

    def __eq__(self, other):
        return self.pair.cell == other.pair.cell and self.pair.client == other.pair.client

    @property
    def complete(self):
        return None not in (self.beacon, *self.handshake.packets)

    def __repr__(self):
        packets = self.handshake.packets
        packets.insert(0, self.beacon)

        packets = tuple(map(lambda x: int(bool(x)), packets))

        return f"<{self.pair.cell} -> {self.pair.client}, {packets}>"