# -*- coding: utf-8 -*-

from scapy.sendrecv import AsyncSniffer
from scapy.error import Scapy_Exception
from loguru import logger


class Sniffer:

    def __init__(self, interface):
        self.interface = interface
        self.sniffer = AsyncSniffer(iface=interface, prn=self.__packet_handler, store=False)
        self.handlers = dict()
        self.channel = None

    def add_packet_handler(self, handler):
        self.handlers[type(handler).__name__] = handler
    
    def remove_packet_handler(self, handler):
        del self.handlers[type(handler).__name__]

    def start(self):
        self.sniffer.start()

    def stop(self):
        try:
            self.sniffer.stop()
        except Scapy_Exception as e:
            logger.exception(e)

        self.sniffer.join()

    def __packet_handler(self, pkt):
        for _, handler in self.handlers.items():
            handler(pkt)
