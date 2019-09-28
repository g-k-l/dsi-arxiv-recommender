# -*- coding: utf-8 -*-
from collections import deque
import os
from os.path import join
import sqlite3
from sqlite3 import IntegrityError
import tarfile

from extract import get_fields


DB_NAME = "arxiv.db"

CREATE_TBL_SQL = """
    CREATE TABLE IF NOT EXISTS articles (
        arxiv_id TEXT PRIMARY KEY NOT NULL,
        title TEXT,
        authors TEXT,
        subjects TEXT,
        abstract TEXT,
        last_submitted DATE
    );"""

INSERT_STMT = """
    INSERT INTO articles
        (arxiv_id, title, authors, subjects, abstract, last_submitted)
    VALUES
        (?, ?, ?, ?, ?, ?);
"""


# Note: sqlite3 connection defaults to autocommit
class DBWrapper(object):
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()

    def create_arxiv_tbl(self):
        return self.execute(CREATE_TBL_SQL)

    def insert_into_articles(self, row):
        return self.execute(INSERT_STMT, row)

    def insert_many_into_articles(self, rows):
        return self.executemany(INSERT_STMT, rows)

    def execute(self, *args, **kwargs):
        return self.cursor.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):
        return self.cursor.executemany(*args, **kwargs)


def fmt_for_insert(row):
    if row["authors"]:
        row["authors"] = "|".join(row["authors"])
    if row["subjects"]:
        row["subjects"] = "|".join(row["subjects"])
    return list(row.values())


def raw_xml_from(tgz_path):
    tgz = tarfile.open(tgz_path)
    for member in tgz.getmembers():
        raw_xml = tgz.extractfile(member).read()
        yield fmt_for_insert(get_fields(raw_xml, asdict=True))
    tgz.close()


def proc_metadata_batch(cur, tgz_path):
    metadata_iter = raw_xml_from(tgz_path)
    for row in metadata_iter:
        print("Inserting %s" % row)
        try:
            cur.insert_into_articles(row)
        except IntegrityError as ex:
            # usually caused by duplicated arxiv_id in metadata
            # retry using 1 row at a time, ignoring failed rows
            print("failed to insert row: %s" % (row))
            print(ex)
        finally:
            # exhause iterator to ensure file is closed
            deque(metadata_iter, maxlen=0)


def main():
    conn = sqlite3.connect(DB_NAME)
    cur = DBWrapper(conn)
    cur.create_arxiv_tbl()

    os.makedirs("./temp", exist_ok=True)

    for tgz in sorted(os.listdir("./metadata")):
        tgz_path = join("./metadata", tgz)
        proc_metadata_batch(cur, tgz_path)


if __name__ == "__main__":
    main()
