#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from loguru import logger

from handlers.pages import Index
from handlers.api import IndexApi, WebSocketApi
from core import AppServer, Storage, Database
from core.GpsPoller import GpsPoller, WORKER_NAME as GPS_NAME
from core.WiFiScanner import WiFiScanner, WORKER_NAME as WIFI_NAME
from core.CommandHandler import CommandHandler, WORKER_NAME as CMD_NAME

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

    storage.set(CMD_NAME, CommandHandler())
    storage.set(GPS_NAME, GpsPoller())
    storage.set(WIFI_NAME, WiFiScanner(storage))

    storage.get(CMD_NAME).start()
    storage.get(GPS_NAME).start()
    storage.get(WIFI_NAME).start()

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
        threads = map(lambda i: storage.get(i), [CMD_NAME, GPS_NAME, WIFI_NAME])

        map(lambda item: item.stop(), threads)
        map(lambda item: item.join(), threads)

        logger.info("Stopping server!")
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
