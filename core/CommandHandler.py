# -*- coding: utf-8 -*-

from core.auxiliary import classproperty
from core.Worker import Worker, WorkerStatus
from loguru import logger
from time import sleep
from queue import Queue, Empty
from .commands import Command


WORKER_NAME = "Command Handler"


class CommandHandler(Worker):

    def __init__(self):
        Worker.__init__(self, name=WORKER_NAME)

        self.commands = Queue()
        self.status = WorkerStatus.WORKING

    def put(self, cmd):
        if isinstance(cmd, Command):
            self.commands.put_nowait(cmd)
        else:
            logger.warning(f"Object ({cmd}) not a command!")

    def stop(self):
        if WorkerStatus.WORKING == self.status:
            logger.success("Stopping CMD handler thread...")
            self.status = False

    def run(self):
        while WorkerStatus.WORKING == self.status:
            try:
                cmd = self.commands.get(timeout=1)
                cmd.execute()
            except Empty:
                sleep(1)
