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
        records = connection.execute("SELECT * FROM AtChannel;").fetchall()
        channel_list = list(set(list(map(lambda item: item.get("channel"), records))))

        self.write({"channels": channel_list})

    def action_records(self, connection):
        channel = self.get_argument("channel", "all")
        where_condition = "" if channel == "all" else f"WHERE channel={channel}"

        records = connection.execute(f'''
            SELECT * FROM 
                AccessPoint AS ap

                LEFT JOIN (
                    SELECT id, ap_id, ssid FROM WithSsid GROUP BY ap_id ORDER BY id DESC
                ) s ON s.ap_id = ap.id

                LEFT JOIN (
                    SELECT id, ap_id, channel, signal, frequency FROM AtChannel GROUP BY ap_id ORDER BY id DESC
                ) c ON c.ap_id = ap.id

                LEFT JOIN (
                    SELECT id, ap_id, encrypted, encryption FROM WithEncryption GROUP BY ap_id ORDER BY id DESC
                ) e ON e.ap_id = ap.id

                LEFT JOIN (
                    SELECT id, ap_id, latitude, longitude, t_stamp FROM AtGeoposition GROUP BY ap_id ORDER BY t_stamp ASC
                ) g ON g.ap_id = ap.id
            {where_condition};
        ''').fetchall()

        self.write({"records": records})
