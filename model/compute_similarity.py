import os
from time import time
import numpy as np
from multiprocessing import Process, cpu_count
from threading import Thread
from gensim.models.doc2vec import Doc2Vec
import pyspark as ps
from pyspark.mllib.linalg.distributed import RowMatrix
import matplotlib.pyplot as plt
import seaborn

'''Compute the similarity of the document vectors.'''

def get_row_matrix(sc, model='adam.first',test=True):
    model = Doc2Vec.load(model)
    docvecs = np.array(model.docvecs).T
    n_rows = docvecs.shape[0]
    if not test:
        mat_rdd = sc.parallelize(docvecs)
    else:
        idx_selected = np.random.choice(np.arange(docvecs.shape[1]),size=1000,replace=False)
        mat_rdd = sc.parallelize(docvecs[:,idx_selected])
    mat = RowMatrix(mat_rdd, n_rows)
    return mat, idx_selected

def get_col_sim(rowmatrix, compute_threshold):
    return rowmatrix.columnSimilarities(compute_threshold)

def threshold_filter(threshold):
    def helper(entry):
        if entry.value > threshold:
            return True
        return False
    return helper

def get_stats(result):
    '''result is a list of MatrixEntries'''
    values = map(lambda entry: entry.value, result)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel = 'Cosine Similarities'
    ax.set_ylabel = 'Vectors'
    ax.hist(values, bins=20)
    plt.savefig('Similarity Historgram.jpg')
    print 'Average: ', sum(values)/len(values)
    print 'Num values: ', len(values)

def one_iter(sc):
    time_0 = time()
    rowmat, idx_selected = get_row_matrix(sc)
    col_sims_mat = get_col_sim(rowmat, 0)
    time_1 = time()
    col_sims = col_sims_mat.entries.filter(threshold_filter(0))
    time_2 = time()
    result = col_sims.collect()
    time_3 = time()

    print 'Working time to get col_sims_mat: ', time_1-time_0
    print 'Working time to filter: ', time_2-time_0
    print 'Working time to collect entries: ', time_3-time_0
    return result, idx_selected

def output_adj_list(entries):

    def adj_list_helper(limits, order):
        with open('graph_part_{}.txt'.format(order) 'w') as f:
            for idx in xrange(limits[0], limits[1]):
                f.write('{} {} {}'.format(entries[idx].i, entries[idx].j, entries[idx].value))

    parts = cpu_count()
    part_size = len(entries)/float(cpu_count())
    for order in xrange(parts):
        limits = [part_size*order, part_size*(order+1)]
        if limits[1] >= len(entries):
            limits[1] = None
        p = Process(target=adj_list_helper, limits)
        p.start()

if __name__ == '__main__':
    print 'Starting'
    sc = ps.SparkContext('local[{}]'.format(cpu_count()))
    result,idx_selected=one_iter(sc)
    get_stats(result)
    print 'Writing matrix to files'
    output_adj_list(result)
