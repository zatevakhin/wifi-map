# -*- coding: utf-8 -*-

from tornado import web
from core.auxiliary import classproperty


class IndexApi(web.RequestHandler):

    @classproperty
    def location(cls):
        return r"/api/index/(action_[a-z_]+)"

    def initialize(self, storage):
        self.db = storage.get("db")

    def post(self, action):
        connection = self.db.connect()

        if hasattr(self, action):
            getattr(self, action)(connection)
        else:
            self.write({"msg": 0xFF}) # replace to Errors Enum

    def action_channels(self, connection):
        records = connection.execute("SELECT * FROM `records`;").fetchall()
        channel_list = list(set(list(map(lambda item: item.get("channel"), records))))

        self.write({"channels": channel_list})

    def action_records(self, connection):
        channel = self.get_argument("channel", "all")

        where_condition = "" if channel == "all" else f"WHERE channel={channel}"
        records = connection.execute(f"SELECT * FROM `records` {where_condition};").fetchall()

        self.write({"records": records})
