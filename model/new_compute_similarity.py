import numpy as np
from scipy.spatial.distance import cosine
from multiprocessing import Pool, cpu_count
from collections import deque
from gensim.models.doc2vec import Doc2Vec

def matrix_norm(model, threshold,start=0):
    full_matrix = np.array(model.docvecs)
    pool = Pool(500)
    for i in xrange(start,full_matrix.shape[0]-1):
	print 'Computing row ', i
        pool.apply_async(compute_one_row, (full_matrix[i,:], i+1,full_matrix, threshold))
    print 'Completed'


def compute_one_row(left, start, my_copy_matrix, threshold):
    with open('./cos_sims/cos_sim_row_{}.txt'.format(start-1), 'w') as f:
        for j in xrange(start, len(my_copy_matrix)):
            sim = 1-cosine(left, my_copy_matrix[j,:])
	    if sim > threshold:
                f.write('{}, {}, {} \n'.format(start-1,j,sim))

if __name__ == '__main__':
    model = Doc2Vec.load('second_model')
    matrix_norm(model, 0.2)
