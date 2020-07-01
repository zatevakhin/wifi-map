# -*- coding: utf-8 -*-

from tornado import web
from core.auxiliary import classproperty


class IndexApi(web.RequestHandler):

    @classproperty
    def location(cls):
        return r"/api/index"

    def initialize(self, storage):
        pass

    def post(self, domain_id):
        pass
