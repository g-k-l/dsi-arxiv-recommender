import os
import csv
import numpy as np
from multiprocessing import cpu_count
from gensim.models.doc2vec import Doc2Vec
import pyspark as ps
from pyspark.mllib.linalg.distributed import RowMatrix

'''Compute the similarity of the document vectors.'''


def get_row_matrix(sc, model='adam.first'):
    model = Doc2Vec.load(model)
    docvecs = np.matrix(model.docvecs).T
    n_rows = docvecs.shape[0]
    mat_rdd = sc.parallelize(docvecs)
    mat = RowMatrix(mat_rdd, n_rows)
    return mat

def get_col_sim(rowmatrix):
    return rowmatrix.columnSimilarities()

if __name__ == '__main__':
    print 'Starting'
    sc = ps.SparkContext('local[{}]'.format(cpu_count()))
    col_sims = get_col_sim(get_row_matrix(sc))
