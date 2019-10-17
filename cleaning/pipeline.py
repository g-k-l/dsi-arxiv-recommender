# -*- coding: utf-8 -*-

"""
1. Read metadata for a pdf chunk
2. Pull the pdf chunk from arXiv's s3 bucket
3. perform checksum, untar the chunk
4. for each pdf file in the chunk:
    a. use pdf2txt to convert the file to plain text
    b. lower-case all, tokenize, drop stopwords,
       drop punctuation and symbols such as '[', '('.
       Drop numbers as well to reduce noise.
    c. Join the words by space, store in the database,
       along with it's arxiv_id as identifier
"""

import contextlib
import logging
import multiprocessing as mp
import os
import re
import shutil
import subprocess
import tempfile
import time
import random
import sys

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from psycopg2.extras import execute_batch

from .db import pgconn
from .extract_meta import (remove_prefix, remove_suffix,
    arxivid_from, pdf_metadata_from_db)


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


stopwords_set = set(stopwords.words())
num_regex = re.compile(r'^[0-9]+$')


def to_tokens(raw_content):
    lemmatizer = WordNetLemmatizer()
    words = word_tokenize(raw_content)
    ret = []
    for word in words:
        word = word.lower()
        if (word in stopwords_set or len(word) == 1):
            continue
        try:
            # eliminate all numbers
            float(word)
        except ValueError:
            ret.append(lemmatizer.lemmatize(word))
    return ret


def pdf_to_text(inpath):
    p = subprocess.Popen(['pdf2txt.py', inpath], stdout=subprocess.PIPE)
    output, __ = p.communicate()
    return output.decode('utf-8')


@contextlib.contextmanager
def mk_temp_dir():
    tempdir = tempfile.mkdtemp()
    try:
        yield tempdir
    finally:
        shutil.rmtree(tempdir)


def fetch_chunk(key, tempdir):
    filename = remove_prefix(key, "pdf/")
    filepath = os.path.join(tempdir, filename)
    subprocess.run(["aws", "s3api", "get-object", "--request-payer",
        "requester", "--bucket", "arxiv", "--key", key, filepath])
    subprocess.run(["tar", "xvfz", filepath, "-C", tempdir])


def yield_pdfs_only(directory):
    for dirpath, __, files in os.walk(directory):
        for file in files:
            if not file.endswith(".pdf"):
                continue
            yield dirpath, file


def proc_chunk(pdf_meta, queue):
    logger.info("Starting on chunk: %s" % pdf_meta['filename'])
    with mk_temp_dir() as tempdir:
        fetch_chunk(pdf_meta['filename'], tempdir)
        logger.info("Fetched chunk: %s" % pdf_meta['filename'])
        for dirpath, file in yield_pdfs_only(tempdir):
            inpath = os.path.join(dirpath, file)
            tokens = to_tokens(pdf_to_text(inpath))
            # submit the paper's arxiv_id and text to postgres
            arxiv_id = arxivid_from(remove_suffix(file, ".pdf"))
            queue.put((arxiv_id, tokens))
    logger.info("Completed chunk: %s" % pdf_meta['filename'])


BUFFER_SIZE = 5000
EXIT = -1

CONTENT_TBL_SQL = """
    CREATE TABLE IF NOT EXISTS content (
        arxiv_id VARCHAR(50),
        text_content TEXT[]
    );"""

INSERT_STMT = """
    INSERT INTO content
        (arxiv_id, text_content)
    VALUES
        (%s, %s);"""


def consumer(queue):
    logger.info("*******DB Consumer Starting********")
    conn = pgconn()
    cur = conn.cursor()
    cur.execute(CONTENT_TBL_SQL)

    buf = []
    while True:
        msg = queue.get()
        if msg == EXIT:
            logger.info("*******Received EXIT********")
            break
        buf.append(queue.get())
        if len(buf) >= BUFFER_SIZE:
            logger.info("*******Flushing Buffer********")
            execute_batch(cur, INSERT_STMT, buf[:BUFFER_SIZE])
            del buf[:BUFFER_SIZE]

    execute_batch(cur, INSERT_STMT, buf)
    logger.info("*******Flushed Final Buffer********")
    conn.close()


def main():
    manager = mp.Manager()
    queue = manager.Queue()

    consumer_p = mp.Process(target=consumer, args=(queue,))
    consumer_p.start()
    conn = pgconn()
    with mp.Pool(processes=4) as producers:
        results = []
        for pdf_meta in pdf_metadata_from_db(conn):
            result = producers.apply_async(proc_chunk, (pdf_meta, queue,))
            results.append(result)
        # block until producers finish all tasks
        for result in results:
            result.get()
    conn.close()
    queue.put(EXIT)
    consumer_p.join()
