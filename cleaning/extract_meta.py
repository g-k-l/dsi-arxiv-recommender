# -*- coding: utf-8 -*-

"""Parses the arXiv pdf files manifest to obtain
information about each chunk of pdf files.
"""
from collections import OrderedDict
import re

from dateutil.parser import parse
from lxml import etree
from schema import Schema, Use, Or


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
        file_path = "./src-metadata/arXiv_pdf_manifest.xml"
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
