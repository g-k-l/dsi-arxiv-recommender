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
    def __init__(self, conn, content=False):
        self.conn = conn
        self.content = content

    def __iter__(self):
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM articles;")
            excluded_list = []
            for article in cur:
                body = ''
                try:
                    body += article['abstract'].replace('\n', ' ').strip()
                except:
                    print 'Missing Abstract for ', article['abstract']
                try:
		            body += str(' ' + article['title'] + '. ')
                except:
                    print 'Title missing for ', article['arxiv_id']
                if self.content:
                    try:
                        body += str(article['content'] + '. ')
                    except:
                        print 'Content missing for ', article['arxiv_id']

                if len(body) < 250: #exclude articles which have too little content (heuristically)
                    exclude_list.append(article['arxiv_id'])

                removed_nums = re.sub(r'[0-9.,_{}><()\-\|\$]{3,}',' ', body)
                removed_specials = re.sub(r'[{}><()\|\$\\\*\^\%\#\@]', '', removed_nums)
                words = re.findall(r"[\w']+|[.,!?;]", removed_nums)
                words = [word.lower() for word in words]
                tags = [article['arxiv_id'], article['subject_id']]

                yield TaggedDocument(words, tags)


if __name__ == '__main__':

    full_content = True
    hidden_layer_size = 200

    n_cpus = multiprocessing.cpu_count()
    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
                        user='root', password='1873', database='arxivpsql') as conn:
        doc_iterator = DocIterator(conn, full_content)
        model = Doc2Vec(
            documents=doc_iterator,
            workers=n_cpus,
            size=hidden_layer_size)
    if full_content:
        model.save('full_model')
    else:
        model.save('abstract_model')
