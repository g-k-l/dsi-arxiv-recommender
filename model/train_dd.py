from deepdist import DeepDist
from gensim.models.doc2vec import Doc2Vec
from pyspark import SparkContext
from multiprocessing import cpu_count
from train import DocIterator
import psycopg2

sc = SparkContext('local[{}]'.format(cpu_count()))

def gradient(model, sentences):  # executes on workers
    syn0, syn1 = model.syn0.copy(), model.syn1.copy()
    model.train(sentences)
    return {'syn0': model.syn0 - syn0, 'syn1': model.syn1 - syn1}


def descent(model, update):      # executes on master
    model.syn0 += update['syn0']
    model.syn1 += update['syn1']

with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
                      user='root', password='1873', database='arxivpsql') as conn:
    print 'Building doc_iterator'
    doc_iterator = DocIterator(conn, False)
    with DeepDist(Doc2Vec(documents=doc_iterator, workers=cpu_count(), size=200, min_count=20)) as dd:
        print 'Begin Training'
        dd.train(corpus, gradient, descent)
        dd.model.save('dd_model')
        # print dd.model.most_similar(positive=['woman', 'king'],
        # negative=['man'])
