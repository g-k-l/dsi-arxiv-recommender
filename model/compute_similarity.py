import os
import numpy as np
import pyspark as ps
from pyspark.mllib.linalg.distributed import RowMatrix
from gensim.models.doc2vec import Doc2Vec
from multiprocessing import Process, cpu_count
from threading import Thread

'''Compute the similarity of the document vectors.'''

def one_iter(sc, model, threshold=0, compute_threshold=0,test=True):
    '''
    INPUT:
        sc: SparkContext
        model: the doc2vec model
        threshold (float): below which the edge is destroyed
        compute_threshold: this is the threshold placed in columnSimilarities
        test: if True, select a subset of 1000-vectors
    OUTPUT:
        result (list): list of MatrixEntries, containing the indices of the vector
            pair along with the cosine similarity of the pair
        idx_selected (np.array): an ordered list of which vectors were selected, if
            we calculated cosine similarity for only a subset of the doc vectors.
    '''
    rowmat, idx_selected = get_row_matrix(sc, modelname, test)
    col_sims_mat = rowmat.columnSimilarities(compute_threshold)
    col_sims = col_sims_mat.entries.filter(threshold_filter(0))
    result = col_sims.collect()
    return result, idx_selected

def get_row_matrix(sc, model, test):
    '''
    Called by one_iter.
    '''
    docvecs = np.array(model.docvecs).T
    n_rows = docvecs.shape[0]
    if not test:
        mat_rdd = sc.parallelize(docvecs)
    else:
        idx_selected = np.random.choice(np.arange(docvecs.shape[1]),size=1000,replace=False)
        mat_rdd = sc.parallelize(docvecs[:,idx_selected])
    mat = RowMatrix(mat_rdd, n_rows)
    return mat, idx_selected

def threshold_filter(threshold):
    '''
    Called by one_iter
    '''
    def helper(entry):
        if entry.value > threshold:
            return True
        return False
    return helper

def output_adj_list(entries):
    '''
    INPUT:
        entries (list): This is a list of spark MatrixEntries
    OUTPUT:
        None. But writes out the matrix entries as text files in format readable
        by networkx (as a weighted adjacency list)
    '''
    def adj_list_helper(limits, order):
        with open('graph_part_{}.txt'.format(order), 'w') as f:
            print limits
            for idx in xrange(limits[0], limits[1]):
                f.write('{} {} {}\n'.format(entries[idx].i, entries[idx].j, entries[idx].value))

    parts = cpu_count()
    part_size = len(entries)/parts
    for order in xrange(parts):
        limits = [part_size*order, part_size*(order+1)]
        if limits[1] >= len(entries):
            limits[1] = len(entries)
        p = Process(target=adj_list_helper, args=(limits,order))
        p.start()

def get_arxiv_id(model, index, idx_selected=None):
    if idx_selected:
        return model.docvecs.index_to_doctag(idx_selected[index])
    return model.docvecs.index_to_doctag(index)

if __name__ == '__main__':
    print 'Starting'
    model = Doc2Vec.load(model)
    sc = ps.SparkContext('local[{}]'.format(cpu_count()))
    result,idx_selected=one_iter(sc, model)
    print 'Writing matrix to files'
    output_adj_list(result)
