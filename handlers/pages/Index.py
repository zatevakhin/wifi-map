# -*- coding: utf-8 -*-

import os
from tornado import web

from core.auxiliary import classproperty


class Index(web.RequestHandler):

    @classproperty
    def location(cls):
        return r"/"

    def initialize(self, storage):
        self.db = storage.get("db")

    def get(self):
        self.render("index.tt")
