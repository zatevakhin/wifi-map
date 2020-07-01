# -*- coding: utf-8 -*-


class Storage(object):

    def __init__(self):
        self.__data = {}

    def set(self, name, obj):
        self.__data[name] = obj

    def get(self, name, default=None):
        return self.__data.get(name, default)
