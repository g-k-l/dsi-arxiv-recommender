# -*- coding: utf-8 -*-

from configparser import ConfigParser
import logging
import os
from os.path import dirname, join
import time

from gensim.models.doc2vec import (Doc2Vec, TaggedDocument, logger)
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import psycopg2
from psycopg2.extras import DictCursor


fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh = logging.FileHandler(join(dirname(__file__), 'logs/train.log'))
fh.setFormatter(fmt)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)


config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
CONFIG = ConfigParser()
CONFIG.read(config_path)
DB_CONFIG = CONFIG["POSTGRES"]


def pgconn():
    DB_NAME = "arxiv"
    conn_payload = {
        "host": DB_CONFIG["HOST"],
        "port": DB_CONFIG["PORT"],
        "user": DB_CONFIG["USER"],
        "password": DB_CONFIG["PASSWORD"],
        "dbname": DB_NAME,
    }
    return psycopg2.connect(**conn_payload)


stopwords_set = set(stopwords.words())

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


class DocIterator(object):
    """Stream the documents into gensim's doc2vec model"""
    def __init__(self, conn):
        self.conn = conn
        self.excluded_list = []

    def __iter__(self):
        cur = self.conn.cursor(cursor_factory=DictCursor)
        cur.arraysize = 100000

        cur.execute("SELECT COUNT(1) AS ct FROM articles;")
        ndocs = cur.fetchall()[0]["ct"]

        cur.execute("SELECT arxiv_id, subjects, abstract FROM articles;")

        for ct, article in enumerate(cur):
            logger.info("Processing %s" % article["arxiv_id"])
            if ct % 1000 == 0:
                logger.info("%d/%d complete." % (ct, ndocs))

            words = to_tokens(article["abstract"])

            # removed_nums = re.sub(r'[0-9.,_{}><()\-\|\$]{3,}', ' ', body)
            # removed_specials = re.sub(
            #     r'[{}><()\|\$\\\*\^\%\#\@]', '', body)
            # words = re.findall(r"[\w']+|[.,!?;]", removed_specials)
            # words = [word.lower() for word in words]
            tags = [article['arxiv_id']] + article['subjects']
            yield TaggedDocument(words, tags)


if __name__ == '__main__':
    logger.info('Starting...')

    pg_conn = pgconn()
    doc_iterator = DocIterator(pg_conn)
    hidden_layer_size = 100

    time1 = time.perf_counter()
    model = Doc2Vec(documents=doc_iterator,
                    workers=os.cpu_count(),
                    vector_size=hidden_layer_size)
    time2 = time.perf_counter()
    logger.info('Training complete. Duration: ', time2-time1)

    model.save("abstract_only_model.gensim")
    logger.info('Saved model as "abstract_only_model.gensim", exiting...')
