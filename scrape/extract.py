# -*- coding: utf-8 -*-
"""
This module is ported from arXiv-doc2vec-recommender
Credits go to https://github.com/sepehr125
"""

from xml.etree import ElementTree as ET
from datetime import datetime


XMLNS = '{http://purl.org/dc/elements/1.1/}'


def get_fields(body):
    """
    Args:
        body (str): the body of the file
    Returns:
        tuple: (title, authors, subject, abstract, last_submitted, arxiv_id)
    """
    root = ET.fromstring(body)
    return (get_title(root),
            get_authors(root),
            get_subject(root),
            get_abstract(root),
            get_date(root),
            get_arxivid(root))


'''
INPUT:
    root (Element): ElementTree root element

OUTPUT:
    str: URL of abstract on arxiv.org
    None: if no identifier looking like an arxiv URL exists
'''


def get_title(root):
    tag = XMLNS + "title"
    title = root.find(tag)
    if title is not None:
        return title.text


def get_authors(root):
    """OUTPUT: List of string of authors"""
    tag = XMLNS + "creator"
    authors = root.findall(tag)
    if authors:
        return [el.text for el in authors]


def get_subject(root):
    tag = XMLNS + "subject"
    subjects = root.findall(tag)
    if subjects:
        return [sub.text for sub in subjects]


def get_abstract(root):
    """
    There are two elements with the `description` tag name.
    The longer one is the abstract.
    """
    tag = XMLNS + "description"
    descriptions = root.findall(tag)
    if descriptions:
        abstract = max([el.text for el in descriptions], key=len)
        return abstract


def get_arxivid(root):
    """
    The arxiv id is hidden among several fields all with the
    tag name "identifier". Fortunately, the arxiv id is the full
    URL at arxiv.org for the abstract, so we can identify them
    checking if they contain 'arxiv.org'
    """
    tag = XMLNS + "identifier"
    ids = root.findall(tag)
    if ids:
        for el in ids:
            if el.text.startswith('http://arxiv.org/abs/'):
                return el.text


def get_date(root):
    """
    OUTPUT: datetime: last submitted date in %Y-%m-%d format
    """
    tag = XMLNS + "date"
    date_list = root.findall(tag)
    if date_list:
        dates = [datetime.strptime(el.text, "%Y-%m-%d").date()
                 for el in date_list]
        return (max(dates))

