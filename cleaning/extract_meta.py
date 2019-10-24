# -*- coding: utf-8 -*-

"""Parses the arXiv pdf files manifest to obtain
information about each chunk of pdf files.
"""
import asyncio
from collections import OrderedDict
import logging
from os.path import join, dirname
import re
import sys

from dateutil.parser import parse
from lxml import etree
from schema import Schema, Use, Or

from .db import pgconn_async


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger = logging.getLogger("asyncio")
logger.addHandler(handler)

FIELDS = ('content_md5sum', 'filename', 'first_item', 'last_item',
          'md5sum', 'num_items', 'seq_num', 'size', 'timestamp', 'yymm')

_schema_spec = {
    'content_md5sum': str,
    'filename': str,
    'first_item': str,
    'last_item': str,
    'md5sum': str,
    'num_items': Use(int),
    'seq_num': Use(int),
    'size': Use(int),
    'timestamp': Use(parse),
    'yymm': str
}
SCHEMA = Schema({
    k: Or(None, v) for k, v in _schema_spec.items()
})


def pdf_metadata(file_path=None):
    """Extact metadata about chunks from pdf/src manifests"""
    if file_path is None:
        file_path = join(dirname(__file__), "src-metadata/arXiv_pdf_manifest.xml")
    with open(file_path) as f:
        xmltree = etree.parse(f)
    root = xmltree.getroot()
    for chunk_metadata in root.getchildren():
        if chunk_metadata.tag == "file":
            yield SCHEMA.validate(get_fields(chunk_metadata, asdict=True))


def get_fields(root, asdict=False):
    """root is a subtree (i.e. an lxml.etree._Element)
        containing information about one src/pdf chunk."""
    data = [getattr(root.find(field), 'text', None) for field in FIELDS]
    if asdict:
        return OrderedDict(zip(FIELDS, data))
    return tuple(data)


ARXIV_ABS_URL = 'http://arxiv.org/abs/'
FNAME_REGEX = re.compile(r'^(?P<subject>[a-z-]*)(?P<id>[0-9.]+)$')


def remove_prefix(text, prefix):
    """useful since chunk filename are prefixed with 'pdf/'"""
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def remove_suffix(text, suffix):
    if text.endswith(suffix):
        return text[:-len(suffix)]
    return text


def arxivid_from(filename):
    """Parses the filename and format the result with the
        arXiv abs url to produce arxivid for the paper"""
    match = FNAME_REGEX.match(filename)
    if match is None:
        raise ValueError("Unrecognized filename pattern: %s" % (filename))
    subject = match.group("subject")
    paper_id = match.group("id")
    if not paper_id:
        raise ValueError("filename missing id segment: %s" % (filename))
    if not subject:
        return ARXIV_ABS_URL + paper_id
    return ARXIV_ABS_URL + "%s/%s" % (subject, paper_id)


CHUNK_META_TBL = """
    CREATE TABLE IF NOT EXISTS pdf_chunks_meta (
        content_md5sum VARCHAR(32),
        filename TEXT,
        first_item TEXT,
        last_item TEXT,
        md5_sum TEXT,
        num_items INT,
        seq_num INT,
        size INT,
        timestamp TIMESTAMP,
        yymm VARCHAR(4)
    );"""

TBL_EXISTS_CHECK = """
    SELECT * FROM information_schema.tables
    WHERE table_name = 'pdf_chunks_meta';
"""

TRUNCATE_META_TBL = "TRUNCATE pdf_chunks_meta;"

PDF_META_INSERT_STMT = ("INSERT INTO pdf_chunks_meta (%s) VALUES (%s);" % (
    ", ".join(FIELDS), ", ".join("?"*len(FIELDS))))


async def pdf_metadata_to_db(trunc=True):
    """Insert parsed XML data in db"""
    logger.info("Started...")

    conn = await pgconn_async()
    logger.info("Connection established.")

    await conn.execute(CHUNK_META_TBL)
    logger.info(CHUNK_META_TBL)

    if trunc:
        await conn.execute(TRUNCATE_META_TBL)
        logger.info(TRUNCATE_META_TBL)

    all_metadata = [tuple(pdf_meta.values()) for pdf_meta in pdf_metadata()]
    logger.info("Extracted %d metadata" % (len(all_metadata)))

    await conn.copy_records_to_table("pdf_chunks_meta", records=all_metadata)
    logger.info("Finished: loaded %d records" % (len(all_metadata)))



def pdf_metadata_from_db(conn):
    """Fetches the metadata inserted in previous step"""
    cur = conn.cursor()
    cur.execute("SELECT * FROM pdf_chunks_meta;")
    for row in cur.fetchall():
        yield dict(zip(FIELDS, row))


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pdf_metadata_to_db())

