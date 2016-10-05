import multiprocessing
import psycopg2
from psycopg2.extras import DictCursor
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import re
import argparse

class DocIterator(object):
    """
    gensim documentation calls this "streaming a corpus", which
    lets us train without holding entire corpus in memory.
    It needs to be an object so gensim can make multiple passes over data.
    Here, we stream from a postgres database.
    """
    def __init__(self, conn):
        self.conn = conn

    def __iter__(self):
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM articles;")
            for article in cur:
                try:
                    abstract = article['abstract'].replace('\n', ' ').strip()
                    try:
		                body = article['title'] + '. '
                    except:
                        print 'Title missing for', article['arxiv_id']
                    body = abstract
                    words = re.findall(r"[\w']+|[.,!?;]", body)
                    words = [word.lower() for word in words]
                    tags = [article['arxiv_id']]
                except TypeError:
                    print 'Missing values and nones'
                    continue

                yield TaggedDocument(words, tags)


if __name__ == '__main__':

    n_cpus = multiprocessing.cpu_count()
    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
                        user='root', password='1873', database='arxivpsql') as conn:
        doc_iterator = DocIterator(conn)
        model = Doc2Vec(
            documents=doc_iterator,
            workers=n_cpus,
            size=300)

    model.save('second_model')
