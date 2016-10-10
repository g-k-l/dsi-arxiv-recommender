import numpy as np
from scipy.spatial.distance import cosine
from multiprocessing import Pool, cpu_count
from gensim.models.doc2vec import Doc2Vec

def cos_sims_single_pass(model,subset_size=0.1,threshold=0.1):
    sample_indices = stratified_sampling(model, subset_size)
    matrix_norm(model,sample_indices, threshold)

def matrix_norm(model,sample_indices=None,threshold=0.1):
    '''
    Computes the pairwise cosine similarity of the selected vectors.
    Ignore similarities below threshold.
    Sample_indices keeps track of which vectors are selected from model.docvecs
    '''
    full_matrix = np.array(model.docvecs)
    if sample_indices == None:
        sample_indices = xrange(len(full_matrix)-1)
    pool = Pool()
    for i, sample_idx in enumerate(sample_indices):
        left_vec = full_matrix[sample_idx,:]
        pool.apply_async(compute_one_row, (left_vec, i, sample_indices[i+1:],full_matrix, threshold))
    pool.close()
    pool.join()
    print 'Completed'

def compute_one_row(left_vec, left_vec_idx, sample_indices, full_matrix, threshold):
    '''
    Called by matrix_norm as a parallel process.
    left_vec is the vector we keep fixed, and its similarity with all other vectors in the sample.
    '''
    print 'Computing row ', left_vec_idx
    with open('./cos_sim_results/records/sample_cos_sims_{}.txt'.format(left_vec_idx), 'w') as f:
        for j in sample_indices:
            sim = 1-cosine(left,full_matrix[j,:])
            if sim > threshold:
                f.write('{}, {}, {} \n'.format(left_vec_idx,j,sim))
    print 'Row ', left_vec_idx, ' completed'

def stratified_sampling(model, subset_size):
    '''
    Samples the document vectors. Stratify by subject/subject_id.
    Subset is a float between 0 and 1, as a fraction of the total number of vectors.
    '''
    total_sample_size = subset_size*len(model.docvecs)
    subject_dict = build_subject_dict(model)
    sample_indices = []
    for i in xrange(subject_dict.keys()):
        full_subset = np.array([model.docvecs[idx[0]] for idx, _ in subject_dict[i]])
        sample_size = int(len(subset)*weight)
        if sample_size != 0:
            sample_subset = np.random.choice(subset, sample_size, replace=False)
            sample_indices+= sample_subset
    print 'Writing sample_indices to disk'
    with open('./cos_sim_results/sample_indices.txt', 'w') as f:
        f.write(str(sample_indices))
    print 'Done sampling'
    return sample_indices

def build_subject_dict(model):
    '''
    build \{subject_id: (index location in model.docvecs, list of arxiv_id)\}
    '''
    subject_dict = {}
    for i in xrange(len(model.docvecs)):
        docvec = model.docvecs[i]
        if model.docvecs.index_to_doctag(i)[1] in subject_dict.keys():
            subject_dict[model.docvecs.index_to_doctag(i)[1]].append(tuple([i,model.docvecs.index_to_doctag(i)[0]]))
        else:
            subject_dict[model.docvecs.index_to_doctag(i)[1]] = [(tuple([i,model.docvecs.index_to_doctag(i)[0]]))]
    with open('./cos_sim_results/subject_dict.pkl', 'wb') as f:
        pickle.dump(subject_dict, f)
    return subject_dict

if __name__ == '__main__':
    model = Doc2Vec.load('second_model')
    cos_sims_single_pass(model)
