import numpy as np
from scipy.spatial.distance import cosine
from multiprocessing import Pool, cpu_count
from collections import deque
from gensim.models.doc2vec import Doc2Vec
import psycopg2
from psycopg2.extras import DictCursor

def make_cos_sims_tables(model):
    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
            user='root', password='1873', database='arxivpsql') as conn:
        cur = conn.cursor()
        for i in xrange(len(model.docvecs)/10000):
            cur.execute('CREATE TABLE cos_sims{} (docvec_idx1 int, docvec_idx2 int, cos_sim numeric)'.format(i))
        conn.commit()

def matrix_norm(model, threshold,start=0):
    full_matrix = np.array(model.docvecs)
    pool = Pool()
    for i in xrange(start,full_matrix.shape[0]-1):
	print 'Computing row ', i
        pool.apply_async(compute_one_row, (full_matrix[i,:], i+1,full_matrix, threshold))
    print 'Completed'

def compute_one_row(left, start, my_copy_matrix, threshold):
    rows = []
    for j in xrange(start, len(my_copy_matrix)):
        sim = 1-cosine(left, my_copy_matrix[j,:])
        if sim > threshold:
            rows.append(tuple([start-1,j,sim]))

    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
            user='root', password='1873', database='arxivpsql') as conn:
        cur = conn.cursor()
        args_str = ','.join(cur.mogrify("(%s,%s,%s)", row) for row in rows)
        cur.execute("INSERT INTO cos_sims{} VALUES ".format((start-1)/10000) + args_str)
        conn.commit()

    print 'Row ', start, ' completed'

def build_arxiv_id_docvec_idx_table(model):
    '''
    Creates a lookup table in postgres: arxiv_id to docvec_idx
    '''
    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
            user='root', password='1873', database='arxivpsql') as conn:

        cur = conn.cursor(cursor_factory=DictCursor)
        build_tab = '''CREATE TABLE IF NOT EXISTS arxiv_id_lookup
                    (arxiv_id text UNIQUE, docvec_idx int UNIQUE)'''
        cur.execute(build_tab)

        def insert_helper(cur, arxiv_id, docvec_idx):
            try:
                cur.execute('''INSERT INTO arxiv_id_lookup (arxiv_id, docvec_idx)
                        VALUES (%s, %s)''', (arxiv_id, docvec_idx))
                print 'Inserted one'
            except psycopg2.IntegrityError:
                print 'Duplicates for: {}, {}'.format(arxiv_id, docvec_id)

        for i in xrange(len(model.docvecs)):
            pool = Pool()
            pool.apply_async(insert_helper,(cur,model.docvecs.index_to_doctag(i), i))
        conn.commit()

def build_arxiv_id_docvec_idx_dicts(model):
    '''
    Get the (invertible) mapping from arxiv_id to docvec index as a dict
    '''
    to_arxiv_id = {i: model.docvecs.index_to_doctag[0] for i in xrange(len(model.docvecs))}
    to_index = {model.docvecs.index_to_doctag[0]: i for i in xrange(len(model.docvecs))}
    return to_arxiv_id, to_index


if __name__ == '__main__':
    print 'Loading Model'
    model = Doc2Vec.load('second_model')
    print 'Building DB Tables'
    build_arxiv_id_docvec_idx_table(model)
    make_cos_sims_table()
    print 'Computing Similarities'
    matrix_norm(model, 0.2)