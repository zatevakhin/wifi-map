#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from loguru import logger

from handlers.pages import Index
from handlers.api import IndexApi, WebSocketApi
from core import AppServer, Storage, Database
from core.GpsPoller import GpsPoller, WORKER_NAME as GPS_POLLER
from core.WiFiScanner import WiFiScanner, WORKER_NAME as WIFI_SCANNER
from core.WiFiSniffer import WiFiSniffer, WORKER_NAME as WIFI_SNIFFER
from core.CommandHandler import CommandHandler, WORKER_NAME as CMD_HANDLER
from core.DataManager import DataManager, WORKER_NAME as DATA_MANAGER

from queue import Queue


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', '-p', nargs='?', default='8002')
    p.add_argument('--address', '-a', nargs='?', default='0.0.0.0')

    arguments = p.parse_args()

    app = AppServer(arguments)

    storage = Storage()
    storage.set("ws-clients", dict())
    storage.set("db", Database("app.db"))

    services = [
        (CMD_HANDLER, CommandHandler()),
        (DATA_MANAGER, DataManager(storage)),
        (GPS_POLLER, GpsPoller(storage)),
        (WIFI_SCANNER, WiFiScanner(storage)),
        (WIFI_SNIFFER, WiFiSniffer(storage))
    ]

    storage.set("services", services)

    tuple(map(lambda i: storage.set(*i), services))
    tuple(map(lambda i: i[-1].start(), services))

    # Settings
    app.add_setting({"debug": True})
    app.add_setting({"template_path": "www/templates/"})
    app.add_setting({"static_path": "www/static"})

    # Handlers
    app.add_handler((Index.location, Index, {'storage': storage}))
    app.add_handler((IndexApi.location, IndexApi, {'storage': storage}))
    app.add_handler((WebSocketApi.location, WebSocketApi, {'storage': storage}))

    try:
        app.run()
    except KeyboardInterrupt:
        threads = map(lambda i: storage.get(i), [CMD_HANDLER, DATA_MANAGER, GPS_POLLER, WIFI_SCANNER, WIFI_SNIFFER])

        tuple(map(lambda item: item.stop(), threads))
        tuple(map(lambda item: item.join(), threads))

        logger.info("Stopping server!")
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
