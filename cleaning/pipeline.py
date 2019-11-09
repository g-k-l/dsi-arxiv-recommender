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
from os.path import join, dirname
import re
import shutil
import subprocess
import tempfile
import time
import sys

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from psycopg2.extras import execute_batch

from .db import pgconn
from .extract_meta import (remove_prefix, remove_suffix,
    arxivid_from, pdf_metadata_from_db)


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(join(dirname(__file__), "logs/pipeline.log"))
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
stdinh = logging.StreamHandler(sys.stdout)
stdinh.setLevel(logging.DEBUG)
stdinh.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(stdinh)
logger.addHandler(fh)


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


def get_proc_logger(pdf_meta):
    filename = remove_prefix(pdf_meta['filename'], "pdf/")
    plogger = mp.get_logger()
    plogger.setLevel(logging.DEBUG)
    logname = "logs/proc_%s.log" % (filename)
    logf_path = join(dirname(__file__), logname)
    fh = logging.FileHandler(logf_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    plogger.addHandler(fh)
    return plogger


def measure(func, log):
    def inner(*args, **kwargs):
        start = time.perf_counter()
        ret = func(*args, **kwargs)
        log.info("%s took %s seconds" % (func.__name__, time.perf_counter() - start))
        return ret
    return inner


def proc_chunk(pdf_meta, queue):
    plogger = get_proc_logger(pdf_meta)
    plogger.info("Starting on chunk: %s" % pdf_meta['filename'])
    with mk_temp_dir() as tempdir:
        fetch_chunk(pdf_meta['filename'], tempdir)
        plogger.info("Fetched chunk: %s" % pdf_meta['filename'])
        for dirpath, file in yield_pdfs_only(tempdir):
            inpath = os.path.join(dirpath, file)
            text = measure(pdf_to_text, plogger)(inpath)
            tokens = measure(to_tokens, plogger)(text)
            # submit the paper's arxiv_id and text to postgres
            arxiv_id = arxivid_from(remove_suffix(file, ".pdf"))
            queue.put((arxiv_id, tokens))
            plogger.info("Extracted arxiv_id=%s" % (arxiv_id))
    plogger.info("Completed chunk: %s" % pdf_meta['filename'])


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
    conn.commit()

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
            conn.commit()
            del buf[:BUFFER_SIZE]

    execute_batch(cur, INSERT_STMT, buf)
    conn.commit()
    logger.info("*******Flushed Final Buffer********")
    conn.close()


def main(skip_to=None):
    manager = mp.Manager()
    queue = manager.Queue()

    consumer_p = mp.Process(target=consumer, args=(queue,))
    consumer_p.start()
    conn = pgconn()
    with mp.Pool(processes=os.cpu_count()-1) as producers:
        results = []
        for pdf_meta in pdf_metadata_from_db(conn, skip_to):
            result = producers.apply_async(proc_chunk, (pdf_meta, queue,))
            results.append(result)
        # block until producers finish all tasks
        for result in results:
            result.get()
    conn.close()
    queue.put(EXIT)
    consumer_p.join()
