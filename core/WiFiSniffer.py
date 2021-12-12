# -*- coding: utf-8 -*-

from wifi import Cell
from wifi.exceptions import InterfaceError
from pyiw import interface as Ifc
from pyiw.exceptions import *
from pyiw.types import *

from core import CommandHandler
from core import commands


from core.Worker import Worker, WorkerStatus
from core.sniffer.Sniffer import Sniffer
from core.sniffer.CellSniffer import CellSniffer
from core.sniffer.HandshakeSniffer import HandshakeSniffer

from loguru import logger
import time
from random import randint as rand



WORKER_NAME = "Wi-Fi Sniffer"


class WiFiSniffer(Worker):

    def __init__(self, storage):
        Worker.__init__(self, name=WORKER_NAME)
        self.status = WorkerStatus.WORKING
        self.storage = storage

    def stop(self):
        if WorkerStatus.WORKING == self.status:
            logger.success(f"Stopping {WORKER_NAME} thread...")
            self.status = WorkerStatus.STOPPED
    
    def initialize_monitor_interface(self):

        def get_monitor_device():
            while True:
                interfaces = list(filter(Ifc.is_support_monitor, Ifc.all_wireless()))
                if not len(interfaces) > 0:
                    logger.warning("Waiting device which support monitor mode.")
                    time.sleep(10)
                else:
                    return interfaces[0]

        interface = get_monitor_device()
        flags = Ifc.get_flags(interface)

        if InterfaceFlags.UP in flags:
            Ifc.set_state(interface, InterfaceState.DOWN)

        monitors = Ifc.all_monitor()

        if len(monitors):
            return monitors[0]
        else:
            mon_name = f"{interface}_mon"

            Ifc.add_monitor(interface, mon_name)
            Ifc.set_state(mon_name, InterfaceState.UP)

            return mon_name

    def run(self):
        mgr = self.storage.get(CommandHandler.WORKER_NAME)

        while WorkerStatus.WORKING == self.status:
            mon = self.initialize_monitor_interface()

            if not mon:
                logger.warning("Waiting for monitor interface.")
                time.sleep(5)
                continue

            flags = Ifc.get_flags(mon)

            while WorkerStatus.WORKING == self.status:
                if InterfaceFlags.DOWN in flags:
                    flags = Ifc.get_flags(mon)
                    logger.warning(f"Device '{mon}' disabled.")
                    time.sleep(5)
                else:
                    break

            sniffer = Sniffer(mon)
            
            cell_sniffer = CellSniffer(sniffer)
            handshake_sniffer = HandshakeSniffer(sniffer)
            sniffer.add_packet_handler(cell_sniffer)
            sniffer.add_packet_handler(handshake_sniffer)
            
            sniffer.start()
            
            while (WorkerStatus.WORKING == self.status) and (mon in Ifc.all_monitor()):
                channel = rand(1, 14) # TODO: add time to monitor channel
                try:
                    Ifc.set_channel(mon, channel)
                except IncorrectInterfaceError:
                    logger.warning("Device disconnected.")
                    break
                except DeviceBusyError:
                    logger.warning("Seems device disabled.")
                    break
                except ChannelBlockedError:
                    logger.error(f"For '{mon}' channel '{channel}' is disabled.")
                    continue
                
                if (access_points := cell_sniffer.access_points):
                    mgr.put(commands.CmdSetSnifferResultToDataManager(self.storage, access_points))

                time.sleep(1)

            sniffer.stop()