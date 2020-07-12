# -*- coding: utf-8 -*-

from abc import ABC


class Command(ABC):

    def __init__(self, receiver):
        self.receiver = receiver

    def execute(self):
        pass
