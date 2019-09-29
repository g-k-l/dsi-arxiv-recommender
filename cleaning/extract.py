# -*- coding: utf-8 -*-
from collections import OrderedDict
import re

from lxml import etree


FIELDS = ('content_md5sum', 'filename', 'first_item', 'last_item',
          'md5sum', 'num_items', 'seq_num', 'size', 'timestamp', 'yymm')


def pdf_metadata(file_path=None):
    """Extact metadata about chunks from pdf/src manifests"""
    if file_path is None:
        file_path = "./src-metadata/arXiv_pdf_manifest.xml"
    with open(file_path) as f:
        xmltree = etree.parse(f)
    root = xmltree.getroot()
    for chunk_metadata in root.getchildren():
        if chunk_metadata.tag == "file":
            yield get_fields(chunk_metadata, asdict=True)


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
