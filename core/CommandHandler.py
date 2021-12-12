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
        self.set_status(WorkerStatus.WORKING)

    def put(self, cmd):
        if isinstance(cmd, Command):
            self.commands.put_nowait(cmd)
        else:
            logger.warning(f"Object ({cmd}) not a command!")

    def stop(self):
        status = self.get_status()
        if status in [WorkerStatus.WORKING, WorkerStatus.IDLE]:
            logger.success("Stopping CMD handler thread...")
            self.set_status(WorkerStatus.STOPPED)

    def run(self):
        status = self.get_status()

        while status in [WorkerStatus.WORKING, WorkerStatus.IDLE]:
            try:
                cmd = self.commands.get(timeout=1)
                cmd.execute()
            except Empty:
                self.set_status(WorkerStatus.IDLE)
                sleep(1)
            except Exception:
                self.set_status(WorkerStatus.ERROR)
            # finally:
            #     self.set_status(WorkerStatus.STOPPED)
