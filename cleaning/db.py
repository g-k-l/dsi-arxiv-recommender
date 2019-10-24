# -*- coding: utf-8 -*-

from configparser import ConfigParser
import os

import asyncpg
import psycopg2


config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
CONFIG = ConfigParser()
CONFIG.read(config_path)
DB_CONFIG = CONFIG["POSTGRES"]
DB_NAME = "arxiv"


async def pgconn_async():
    conn_payload = {
        "host": DB_CONFIG["HOST"],
        "port": DB_CONFIG["PORT"],
        "user": DB_CONFIG["USER"],
        "password": DB_CONFIG["PASSWORD"],
        "database": DB_NAME,
    }
    conn = await asyncpg.connect(**conn_payload)
    return conn



def pgconn():
    conn_payload = {
        "host": DB_CONFIG["HOST"],
        "port": DB_CONFIG["PORT"],
        "user": DB_CONFIG["USER"],
        "password": DB_CONFIG["PASSWORD"],
        "dbname": DB_NAME,
    }
    return psycopg2.connect(**conn_payload)