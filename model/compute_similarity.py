import os
import sys
import numpy as np
import pyspark as ps
import psycopg2
from psycopg2.extras import DictCursor
from pyspark.mllib.linalg.distributed import RowMatrix
from gensim.models.doc2vec import Doc2Vec
from multiprocessing import Process, cpu_count
from threading import Thread

''' Compute the similarity of the document vectors.'''

def one_iter(sc, model, threshold=0, compute_threshold=0,test=True):
    '''
    INPUT:
        sc: SparkContext
        model: the doc2vec model
        threshold (float): below which the edge is destroyed
        compute_threshold: this is the threshold placed in columnSimilarities
        test: if True, select a subset of 1000-vectors
    OUTPUT:
        col_sims (rdd): rdd of MatrixEntries, containing the indices of the vector
            pair along with the cosine similarity of the pair
        idx_selected (np.array): an ordered list of which vectors were selected, if
            we calculated cosine similarity for only a subset of the doc vectors.
    '''
    rowmat, idx_selected = get_row_matrix(sc, model, test)
    col_sims_mat = rowmat.columnSimilarities(compute_threshold)
    col_sims = col_sims_mat.entries.filter(threshold_filter(0))
    return col_sims, idx_selected

def get_row_matrix(sc, model, test=True, subset_size=0.01):
    '''
    Called by one_iter.
    '''
    docvecs = np.array(model.docvecs).T
    n_rows = docvecs.shape[0]
    if not test:
        mat_rdd = sc.parallelize(docvecs)
	idx_selected = None
    else:
        # idx_selected = np.random.choice(np.arange(docvecs.shape[1]),size=100000,replace=False)
        idx_selected = stratified_sampling(model, subset_size)
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
    Use this for small graphs (~1000 vectors as nodes)
    For bigger graphs, use spark's write to text.

    INPUT:
        entries (list): This is a list of MatrixEntries
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


def build_subject_dict(model):
    '''
    build \{subject_id: (index location in model.docvecs, list of arxiv_id)\}
    '''
    subject_dict = {}
    for i in xrange(len(model.docvecs)):
        docvec = model.docvecs[i]
        if docvec.index_to_doctag[1] in subject_dict.keys():
            subject_dict[docvecindex_to_doctag[1]].append(tuple([i,docvec.index_to_doctag[0]))
        else:
            subject_dict[docvecindex_to_doctag[1]] = [(tuple([i,docvec.index_to_doctag[0]))]
    return subject_dict


def stratified_sampling(model, subset_size):
    '''
    connect to the database, return a sample stratified by subject_id/subject
    subset_size: float between 0 and 1, as percentage of the total count.
    '''
    total_sample_size = subset_size*len(model.docvecs)
    subject_dict = build_subject_dict(model)
    sample_indices = []
    for i in xrange(subject_dict.keys()):
        full_subset = np.array([model.docvecs[idx[0]] for idx in subject_dict[i]])
        sample_size = int(len(subset)*weight)
        if sample_size != 0:
            sample_subset = np.random.choice(subset, sample_size, replace=False)
            sample_indices+= sample_subset

    return sample_indices


if __name__ == '__main__':
    print 'Starting'
    model = Doc2Vec.load('second_model')
    sc = ps.SparkContext('local[{}]'.format(cpu_count()))
    col_sims,idx_selected=one_iter(sc, model, threshold=0.05, compute_threshold=0.1,test=True,subset_size=0.1)
    print 'Writing matrix to files'
    #output_adj_list(result)
    col_sims.saveAsTextFile('matrixentries_test')
