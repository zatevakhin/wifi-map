# -*- coding: utf-8 -*-

from tornado import web
from core.auxiliary import classproperty

import folium
from folium.plugins import HeatMap
import os


class Index(web.RequestHandler):

    @classproperty
    def location(cls):
        return r"/"

    def initialize(self, storage):
        self.db = storage.get("db")

    def get(self):
        connection = self.db.connect()
        
        records = connection.execute("SELECT * FROM `records` LIMIT 1000;").fetchall()
        
        longitude_list = list(map(lambda item: item.get("longitude"), records))
        latitude_list = list(map(lambda item: item.get("latitude"), records))
        signal_list = list(map(lambda item: item.get("signal"), records))

        channel_list = list(set(list(map(lambda item: item.get("channel"), records))))
        print(channel_list)

        center = [sum(latitude_list) / len(latitude_list), sum(longitude_list) / len(longitude_list)]

        heat_map_data = list(map(lambda item: (item.get("latitude"), item.get("longitude"), item.get("signal")), records))

        heat_map = folium.Map(location=center, zoom_start=12)

        hm_wide = HeatMap(heat_map_data,
               min_opacity=0.2,
               max_val=(max(signal_list)),
               radius=17, blur=15, 
               max_zoom=1, 
             )

        heat_map.add_child(hm_wide)
        heat_map.save('www/static/data/index_map_all.html')

        self.render("index.tt", channels=channel_list)

    def post(self):
        channel = self.get_argument("channel", "all")

        connection = self.db.connect()
        
        where_condition = "" if channel == "all" else f"WHERE channel={channel}"

        records = connection.execute(f"SELECT * FROM `records` {where_condition} LIMIT 1000;").fetchall()
        
        longitude_list = list(map(lambda item: item.get("longitude"), records))
        latitude_list = list(map(lambda item: item.get("latitude"), records))
        signal_list = list(map(lambda item: item.get("signal"), records))

        channel_list = list(set(list(map(lambda item: item.get("channel"), records))))
        print(channel_list)

        center = [sum(latitude_list) / len(latitude_list), sum(longitude_list) / len(longitude_list)]

        heat_map_data = list(map(lambda item: (item.get("latitude"), item.get("longitude"), item.get("signal")), records))

        heat_map = folium.Map(location=center, zoom_start=12)

        hm_wide = HeatMap(heat_map_data,
               min_opacity=0.2,
               max_val=(max(signal_list)),
               radius=17, blur=15, 
               max_zoom=1, 
             )

        heat_map.add_child(hm_wide)
        heat_map.save(f"www/static/data/index_map_{channel}.html")
