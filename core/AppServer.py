# -*- coding: utf-8 -*-

from tornado import ioloop, web
from loguru import logger


class AppServer(object):

    def __init__(self, arguments):
        self.__arguments = arguments
        self.__handlers = []
        self.__settings = {}

    @property
    def port(self):
        return int(self.__arguments.port)

    @property
    def address(self):
        return self.__arguments.address

    def add_handler(self, handler: tuple):
        if type(handler) != tuple:
            raise AssertionError("Handler must be tuple!")

        self.__handlers.append(handler)

    def add_setting(self, setting: dict):
        if type(setting) != dict:
            raise AssertionError("Setting must be dict!")

        self.__settings.update(setting)

    def add_async_service(self, service: object):
        self.__services.append(service)

    def run(self):
        application = web.Application(self.__handlers, **self.__settings)
        logger.info("Server started at {}:{}", self.address, self.port)
        application.listen(self.port, address=self.address)
        io_loop = ioloop.IOLoop.instance()
        io_loop.start()
