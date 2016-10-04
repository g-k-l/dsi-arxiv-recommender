import os
import pickle
import numpy as np
from scipy.spatial.distance import cosine
from gensim.models.doc2vec import Doc2Vec

'''Compute the similarity of the document vectors.'''

model = Doc2Vec.load('adam.first')
doc_vecs = np.array(Doc2Vec.docvecs())
n_vecs = len(doc_vecs)

cos_dist_matrix = np.zeroes(shape=(n_vecs, n_vecs))

for i, doc_vec in enumerate(doc_vecs):
    cos_dists = np.apply_along_axis(lambda v: cosine(doc_vec, v), axis=1,arr=doc_vecs)
    cos_dist_matrix[i, ] = cos_dists

cos_sim_matrix = 1 - cos_dist_matrix

with open('cos_sim_matrix.adam.first.pkl', 'wb'):
    pickle.dump(cos_sim_matrix)
