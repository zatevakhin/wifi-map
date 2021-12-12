# -*- coding: utf-8 -*-

from threading import Thread
from enum import Enum, auto
from core.auxiliary import classproperty


class WorkerStatus(Enum):
    WORKING = auto()
    STOPPED = auto()
    ERROR = auto()
    IDLE = auto()


class Worker(Thread):

    def __init__(self, name=None):
        Thread.__init__(self, name=name)
        self.status = WorkerStatus.STOPPED

    def set_status(self, status):
        self.status = status

    def get_status(self):
        return self.status

    def stop(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError
