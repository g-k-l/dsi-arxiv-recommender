# -*- coding: utf-8 -*-
import asyncio

from configparser import ConfigParser
import logging
import io
import os
from os.path import join
import sys
import tarfile

import aiofiles
import asyncpg

from extract import get_fields


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
asyncio_log = logging.getLogger("asyncio")
asyncio_log.setLevel(logging.DEBUG)
asyncio_log.addHandler(handler)
logger = asyncio_log


CONFIG = ConfigParser()
CONFIG.read('config.ini')
DB_CONFIG = CONFIG["POSTGRES"]

DB_NAME = "arxiv"


async def pgconn():
    conn_payload = {
        "host": DB_CONFIG["HOST"],
        "port": DB_CONFIG["PORT"],
        "user": DB_CONFIG["USER"],
        "password": DB_CONFIG["PASSWORD"],
        "database": DB_NAME,
        "timeout": 5,
    }
    conn = await asyncpg.connect(**conn_payload)
    return conn


# Note: for performance concerns, we declare arxiv_id
# as PK after all data has been inserted
CREATE_TBL_SQL = """
    CREATE TABLE IF NOT EXISTS articles (
        arxiv_id VARCHAR(50),
        title TEXT,
        authors TEXT[],
        subjects TEXT[],
        abstract TEXT,
        last_submitted DATE
    );"""

BUILD_INDEX_SQL = """
    CREATE UNIQUE INDEX CONCURRENTLY articles_arxiv_id_index
        ON articles (arxiv_id);
    ALTER TABLE articles ADD CONSTRAINT articles_pkey PRIMARY KEY
        USING INDEX articles_arxiv_id_index;
"""

INSERT_STMT = """
    INSERT INTO articles
        (arxiv_id, title, authors, subjects, abstract, last_submitted)
    VALUES
        (?, ?, ?, ?, ?, ?);
"""


def fmt_for_insert(row):
    if row["authors"]:
        row["authors"] = "|".join(row["authors"])
    if row["subjects"]:
        row["subjects"] = "|".join(row["subjects"])
    return list(row.values())


async def prep_metadata(tgz_path):
    async with aiofiles.open(tgz_path, mode="rb") as f:
        content = await f.read()
    tgz = tarfile.open(fileobj=io.BytesIO(content))
    for member in tgz.getmembers():
        raw_xml = tgz.extractfile(member).read()
        yield list(get_fields(raw_xml, asdict=True).values())
    tgz.close()


PRODUCER_EXIT = -1


async def data_producer(queue):
    logger.info("*******Data Producer Starting********")
    for tgz in sorted(os.listdir("./metadata")):
        tgz_path = join("./metadata", tgz)
        metadata_it = prep_metadata(tgz_path)
        logger.info("*******Prepped %s********" % (tgz_path))
        async for metadata in metadata_it:
            await queue.put(metadata)
    await queue.put(PRODUCER_EXIT)


QUEUE_SIZE = 4000
BUFFER_SIZE = 2000


async def db_consumer(queue):
    logger.info("*******DB Consumer Starting********")
    conn = await pgconn()
    await conn.execute(CREATE_TBL_SQL)
    buf = []
    while True:
        msg = await queue.get()
        if msg == PRODUCER_EXIT:
            break
        buf.append(msg)
        if len(buf) >= BUFFER_SIZE:
            logger.info("*******Flushing Buffer********")
            await conn.copy_records_to_table('articles',
                                             records=buf[:BUFFER_SIZE])
            del buf[:BUFFER_SIZE]
    # send remaining items in buffer to db
    await conn.copy_records_to_table('articles', records=buf)
    await conn.close()


def main():
    logger.info("*******Main Starting********")
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    queue = asyncio.Queue(maxsize=QUEUE_SIZE, loop=loop)
    producer = data_producer(queue)
    consumer = db_consumer(queue)
    logger.info("********Event Loop Starting*********")
    loop.run_until_complete(asyncio.gather(producer, consumer))
    loop.close()


if __name__ == "__main__":
    main()
