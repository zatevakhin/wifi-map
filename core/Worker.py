# -*- coding: utf-8 -*-

from threading import Thread
from enum import IntEnum, auto
from core.auxiliary import classproperty


class WorkerStatus(IntEnum):
    WORKING = auto()
    STOPPED = auto()
    ERROR = auto()


class Worker(Thread):

    def __init__(self, name=None):
        Thread.__init__(self, name=name)

    def stop(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError
