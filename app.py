#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from loguru import logger

from handlers.pages import Index
from handlers.api import IndexApi
from core import AppServer, Storage, GpsPoller, WifiScanner, Database



def main():
    p = argparse.ArgumentParser()
    p.add_argument('--port', '-p', nargs='?', default='8002')
    p.add_argument('--address', '-a', nargs='?', default='0.0.0.0')

    arguments = p.parse_args()

    app = AppServer(arguments)

    storage = Storage()
    storage.set("db", Database("app.db"))

    storage.set("gps", GpsPoller())
    storage.get("gps").start()

    storage.set("wifi", WifiScanner(storage.get("db"), storage.get("gps")))
    storage.get("wifi").start()

    # Settings
    app.add_setting({"debug": True})
    app.add_setting({"template_path": "www/templates/"})
    app.add_setting({"static_path": "www/static"})

    # Handlers
    app.add_handler((Index.location, Index, {'storage': storage}))
    app.add_handler((IndexApi.location, IndexApi, {'storage': storage}))

    try:
        app.run()
    except KeyboardInterrupt:
        gps = storage.get("gps")
        wifi = storage.get("wifi")

        gps.stop_it()
        wifi.stop_it()

        gps.join()
        wifi.join()

        logger.info("Stopping server!")
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
