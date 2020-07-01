# -*- coding: utf-8 -*-

import sqlite3


CREATE_ALL_TABLES = """
CREATE TABLE IF NOT EXISTS `records` (
    `id`        INTEGER  PRIMARY KEY NOT NULL,
    `address`   CHAR(17)             NOT NULL,
    `channel`   INTEGER              NOT NULL,
    `frequency` REAL                 NOT NULL,
    `signal`    INTEGER              NOT NULL,
    `name`      TEXT                 NOT NULL,
    `latitude`  REAL                 NOT NULL,
    `longitude` REAL                 NOT NULL,
    `altitude`  REAL                 NOT NULL,

    UNIQUE(address, channel, name)
);
"""


class Database(object):
    
    def __init__(self, db_name):
        self.db_name = db_name

        with self.connect() as connection:
            c = connection.cursor()
            c.execute(CREATE_ALL_TABLES)

    def connect(self):
        connection = sqlite3.connect(self.db_name)
        connection.row_factory = Database.dict_factory

        connection.text_factory = str

        connection.execute("PRAGMA foreign_keys = ON;")
        connection.execute("PRAGMA encoding = 'UTF-8';")

        return connection

    @staticmethod
    def dict_factory(cursor, row):
        return {col[0]: row[idx] for (idx, col) in enumerate(cursor.description)}
