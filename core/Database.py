# -*- coding: utf-8 -*-

import sqlite3


CREATE_ACCESS_POINT_TABLE = """
    CREATE TABLE IF NOT EXISTS AccessPoint (
        id    INTEGER  PRIMARY KEY NOT NULL,
        bssid CHAR(17)             NOT NULL,

        UNIQUE(bssid)
    );
"""

CREATE_CLIENT_TABLE = """
    CREATE TABLE IF NOT EXISTS Client (
        id    INTEGER  PRIMARY KEY NOT NULL,
        mac   CHAR(17)             NOT NULL,

        UNIQUE(mac)
    );
"""

CREATE_WITH_SSID_TABLE = """
    CREATE TABLE IF NOT EXISTS WithSsid (
        id      INTEGER  PRIMARY KEY NOT NULL,
        ap_id   INTEGER              NOT NULL,
        ssid    TEXT                 NOT NULL,
        t_stamp TIMESTAMP DEFAULT    CURRENT_TIMESTAMP,

        FOREIGN KEY (ap_id) REFERENCES AccessPoint(id),
        UNIQUE(ap_id, ssid)
    );
"""

CREATE_AT_CHANNEL_TABLE = """
    CREATE TABLE IF NOT EXISTS AtChannel (
        id        INTEGER PRIMARY KEY NOT NULL,
        ap_id     INTEGER             NOT NULL,
        channel   INTEGER             NOT NULL,
        t_stamp   TIMESTAMP DEFAULT   CURRENT_TIMESTAMP,

        FOREIGN KEY (ap_id) REFERENCES AccessPoint(id),
        UNIQUE(ap_id, channel)
    );
"""

CREATE_WITH_ENCRYPTION_TABLE = """
    CREATE TABLE IF NOT EXISTS WithEncryption (
        id         INTEGER PRIMARY KEY NOT NULL,
        ap_id      INTEGER             NOT NULL,
        crypto  INTEGER             NOT NULL,
        t_stamp    TIMESTAMP DEFAULT   CURRENT_TIMESTAMP,

        FOREIGN KEY (ap_id) REFERENCES AccessPoint(id),
        UNIQUE(ap_id, crypto)
    );
"""

CREATE_AT_GEOPOSITION_TABLE = """
    CREATE TABLE IF NOT EXISTS AtGeoposition (
        id        INTEGER PRIMARY KEY NOT NULL,
        ap_id     INTEGER             NOT NULL,
        latitude  REAL                NOT NULL,
        longitude REAL                NOT NULL,
        t_stamp   TIMESTAMP DEFAULT   CURRENT_TIMESTAMP,

        FOREIGN KEY (ap_id) REFERENCES AccessPoint(id)
    );
"""

CREATE_HANDSHAKE_TABLE = """
    CREATE TABLE IF NOT EXISTS Handshake (
        id        INTEGER PRIMARY KEY NOT NULL,
        ap_id     INTEGER             NOT NULL,
        cl_id     INTEGER             NOT NULL,
        beacon    BLOB                NOT NULL,
        one       BLOB                NOT NULL,
        two       BLOB                NOT NULL,
        three     BLOB                NOT NULL,
        four      BLOB                NOT NULL,
        t_stamp   TIMESTAMP DEFAULT   CURRENT_TIMESTAMP,

        FOREIGN KEY (ap_id) REFERENCES AccessPoint(id),
        FOREIGN KEY (cl_id) REFERENCES Client(id),
        UNIQUE(ap_id, cl_id)
    );
"""


class Database(object):
    
    def __init__(self, db_name):
        self.db_name = db_name

        with self.connect() as connection:
            c = connection.cursor()
            c.execute(CREATE_ACCESS_POINT_TABLE)
            c.execute(CREATE_CLIENT_TABLE)
            c.execute(CREATE_WITH_SSID_TABLE)
            c.execute(CREATE_AT_CHANNEL_TABLE)
            c.execute(CREATE_WITH_ENCRYPTION_TABLE)
            c.execute(CREATE_AT_GEOPOSITION_TABLE)
            c.execute(CREATE_HANDSHAKE_TABLE)


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
