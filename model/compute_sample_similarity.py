import os
import csv
import pickle
import numpy as np
import psycopg2
from collections import defaultdict
from psycopg2.extras import DictCursor
from scipy.spatial.distance import cosine
from multiprocessing import Pool, cpu_count
from gensim.models.doc2vec import Doc2Vec

def cos_sims_single_pass(model,subset_size=0.1,threshold=0.0):
    sample_indices_dict = stratified_sampling(model, subset_size)
    sample_indices_list=[]
    for subject_id, idx_list in sample_indices_dict.iteritems():
        sample_indices_list+=idx_list
    matrix_norm(model, sample_indices_list, threshold)

def matrix_norm(model,sample_indices=[],threshold=0.0):
    '''
    Computes the pairwise cosine similarity of the selected vectors.
    Ignore similarities below threshold.
    Sample_indices keeps track of which vectors are selected from model.docvecs
    '''
    full_matrix = np.array(model.docvecs)
    if len(sample_indices) == 0:
        sample_indices = xrange(len(full_matrix)-1)
    pool = Pool(cpu_count())
    r = []
    for i, sample_idx in enumerate(sample_indices):
        left_vec = full_matrix[sample_idx,:]
        r.append(pool.apply_async(func=compute_one_row, args=(left_vec, sample_idx, sample_indices[i+1:],full_matrix, threshold)))
	if i % 50==0 and i!=0:
	    for result in r:
		if not result.ready():
		    result.wait()
	    r=[]
    pool.close()
    pool.join()
    print 'Completed'

def compute_one_row(left_vec, left_vec_idx, sample_indices, full_matrix, threshold):
    '''
    Called by matrix_norm as a parallel process.
    left_vec is the vector we keep fixed, and its similarity with all other vectors in the sample.
    '''
    print 'Computing row ', left_vec_idx
    with open('./assets/cos_sims/sample_cos_sims_{}.txt'.format(left_vec_idx), 'w') as f:
        writer = csv.writer(f)
        for j in sample_indices:
            sim = 1-cosine(left_vec,full_matrix[j,:])
            if sim > threshold:
                writer.writerow([left_vec_idx,j,sim])
    print 'Row ', left_vec_idx, ' completed'

def stratified_sampling(model, subset_size):
    '''
    Samples the document vectors. Stratify by subject/subject_id.
    Subset is a float between 0 and 1, as a fraction of the total number of vectors.
    '''
    total_sample_size = subset_size*len(model.docvecs)
    if os.path.isfile('./assets/subject_dict.pkl'):
        print 'subject_dict exists...'
        with open('./assets/subject_dict.pkl', 'rb') as f:
            subject_dict = pickle.load(f)
    else:
        print 'building subject_dict'
        subject_dict = build_subject_dict(model)
    sample_indices = defaultdict(list)
    for subject_id in subject_dict.keys(): #for each subject
        full_subset = np.array([idx for idx, _ in subject_dict[subject_id]]) #all article indices of a particular subject
        sample_size = int(len(full_subset)*subset_size) # number of samples to draw from the subject
        if sample_size != 0:
            sample_subset = np.random.choice(full_subset, sample_size, replace=False)
            sample_indices[subject_id] =  sample_subset.tolist()
    print 'Writing sample_indices to disk'
    with open('./assets/sample_indices.txt', 'w') as f:
        writer = csv.writer(f)
        for key, value in sample_indices.iteritems():
            writer.writerow([key,value])
    print 'Done sampling'
    return sample_indices

def build_lookups(model):
    '''
    Create mappings which are useful.
    '''
    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
                          user='root', password='1873', database='arxivpsql') as conn:

        idx_arxiv_id = {}
        arxiv_id_idx = {}
        arxiv_id_subject_id = {}
        subject_id_arxiv_id = defaultdict(list)
        subject_id_subject = {}

        cur = conn.cursor(cursor_factory = DictCursor)

        # make the subject_id to subject mapping
        cur.execute('SELECT DISTINCT subject_id, subject FROM articles ORDER BY subject_id')
        with open('./assets/subject_id_subject.csv', 'w') as f:
            writer = csv.writer(f)
            for item in cur:
                writer.writerow([item['subject_id'], item['subject']])
                subject_id_subject[item['subject_id']] = item['subject']

        # open up the files to write the mappings
        with open('./assets/arxiv_id_idx.csv', 'w') as f0, open('./assets/idx_arxiv_id.csv', 'w') as f1, \
            open('./assets/arxiv_id_subject_id.csv', 'w') as f2, open('./assets/subject_id_arxiv_id.csv','w') as f3:
            csv_writers = [csv.writer(f) for f in [f0, f1,f2,f3]]

            # loop through the document vectors
            for i in xrange(len(model.docvecs)):
                arxiv_id = model.docvecs.index_to_doctag(i)

                # make arxiv_id to idx mappings
                arxiv_id_idx[arxiv_id] = i
                csv_writers[0].writerow([arxiv_id, i])
                idx_arxiv_id[i] = arxiv_id
                csv_writers[1].writerow([i, arxiv_id])

                # make subject_id to arxiv_id mappings
                cur.execute('SELECT subject_id FROM articles WHERE arxiv_id=\'{}\''.format(arxiv_id))
                try:
                    subject_id = cur.fetchone()['subject_id']
                except:
                    print 'No result for arxiv_id: ', arxiv_id
                    continue
                arxiv_id_subject_id[arxiv_id] = subject_id
                csv_writers[2].writerow([arxiv_id, subject_id])
                subject_id_arxiv_id[subject_id].append(arxiv_id)
                csv_writers[3].writerow([subject_id, arxiv_id])

    return idx_arxiv_id, arxiv_id_idx, arxiv_id_subject_id, subject_id_arxiv_id, subject_id_subject


def build_subject_dict(model):
    '''
    build {subject_id: list of (index location in model.docvecs, arxiv_id)}
    '''
    with psycopg2.connect(host='arxivpsql.cctwpem6z3bt.us-east-1.rds.amazonaws.com',
                          user='root', password='1873', database='arxivpsql') as conn:
        cur = conn.cursor(cursor_factory = DictCursor)
        subject_dict = defaultdict(list)
        for i in xrange(len(model.docvecs)):
            arxiv_id = model.docvecs.index_to_doctag(i)
            cur.execute("SELECT subject_id FROM articles WHERE arxiv_id=\'{}\'".format(arxiv_id))
            try:
                subject_id = cur.fetchone()['subject_id']
            except:
                print 'No result for arxiv_id: ', arxiv_id
            subject_dict[subject_id].append(tuple([i, arxiv_id]))

        with open('./assets/subject_dict.pkl','wb') as f:
            pickle.dump(subject_dict,f)
    return subject_dict

def get_subject_centroids(model, subject_dict):
    '''
    Computes the centroid of each subject by taking the average of vectors belonging
    to that subject.
    '''
    subject_centroids = {}
    for subject_id, idx_list in subject_dict.iteritems():
        subject_centroids[subject_id] = np.mean(model.docvecs[idx_list])
    return subject_centroids


if __name__ == '__main__':
    model = Doc2Vec.load('second_model')
    #build_lookups(model)
    cos_sims_single_pass(model)
