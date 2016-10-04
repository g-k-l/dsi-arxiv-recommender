import os
import csv
import numpy as np
from scipy.spatial.distance import cosine
from gensim.models.doc2vec import Doc2Vec

'''Compute the similarity of the document vectors.'''

print 'Starting'

model = Doc2Vec.load('adam.first')
doc_vecs = np.array(Doc2Vec.docvecs
n_vecs = len(doc_vecs)

print 'Loaded.'

with open('cos_sim_matrix.csv','w') as f:
    csv_writer = csv.writer(f)
    print 'Current iteration: ', i
    for i, doc_vec in enumerate(doc_vecs):
        cos_sims = np.apply_along_axis(lambda v: 1-cosine(doc_vec, v), axis=1,arr=doc_vecs)
    csv_writer.writerow(cos_sims)

print 'Job Completed.'
