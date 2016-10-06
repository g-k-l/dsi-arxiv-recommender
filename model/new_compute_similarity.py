import numpy as np
from multiprocessing import Pool, cpu_count
from gensim.models.doc2vec import Doc2Vec

def matrix_norm(model, threshold):
    full_matrix = np.array(Doc2Vec.docvecs)

    def compute_one_row(left, start):
        with open('./cos_sims/cos_sim_row_{}.txt'.format(start), 'w') as f:
            for j in xrange(start, len(full_matrix)):
                sim = left.dot(full_matrix[:,j])
                f.write('{}, {}, {} \n'.format(start,j,sim))
        print 'Completed row ', start

    processes = []
    for i in xrange(full_matrix.size[1]-1):
        print 'Computing row ', i
        p = Process(target=compute_one_row(full_matrix[:,i], i+1))
        processes.append(p)
        p.start()

    print 'Completed'

if __name__ == '__main__':
    model = Doc2Vec.load('second_model')
    matrix_norm(model, 0.1)
