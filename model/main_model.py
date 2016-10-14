import cPickle as pickle
import csv
from itertools import combinations
from collections import defaultdict
from scipy.spatial.distance import cosine
from gensim.models.doc2vec import Doc2Vec
from multiprocessing import Pool, cpu_count

'''
This module builds the main_model, which is a dictionary of the form:

{ subject_id: { arxiv_id: { subject_id: cos_sim \} } }
'''

def build_subject_model(model):
    '''
    computes the similarity between each subject centroid and document vectors
    and stores the information as a dictionary of dictionaries.

    \{arxiv_id: \{ subject_id: cos_sims \}\}
    '''
    #load subject_centroids
    with open('./assets/subject_centroids.pkl', 'rb') as f:
        subject_centroids = pickle.load(f)

    model_dict = {}
    pool = Pool()
    async_results = []

    for idx, doc_vec in enumerate(model.docvecs):
        async_results.append(pool.apply_async(build_single_doc_dict, (idx, doc_vec, subject_centroids,)))
        if idx % 10000 == 0 and idx != 0: #take 10000 as the batch size
            for result in async_results:
                if result.ready():
                    vec_idx, subject_doc_sims = result.get()
                    arxiv_id = model.docvecs.index_to_doctag(vec_idx)
                    model_dict[arxiv_id] = subject_doc_sims
            print 'batch {} complete'.format(idx/10000)

    print 'Items in async_results: ', len(async_results)
    for result in async_results:
	if not result.ready():
	    result.wait()
	vec_idx, subject_doc_sims = result.get()
	arxiv_id = model.docvecs.index_to_doctag(vec_idx)
	if arxiv_id not in model_dict:
	    model_dict[arxiv_id] = subject_doc_sims

    return model_dict

def build_single_doc_dict(idx, doc_vec, subject_centroids):
    '''
    Separated from build_subject_model for multiprocessing.
    This function multithreads to build the dictionary
    '''
    subject_doc_sims = {}
    for subject_id, centroid in subject_centroids.iteritems():
        subject_doc_sims[subject_id] = 1-cosine(doc_vec,centroid)
    return idx, subject_doc_sims


def bin_by_subject_id(model_dict):
    '''
    Builds the following dictionary:
    { subject_id: \{arxiv_id: \{ subject_id: cos_sims \}\}}
    the list contains the similarities of the articles with the cosine sims, organized
    by subject_id for easy lookup.
    '''
    print 'Binning by subject_id...'
    result_d = {}
    with open('./assets/subject_id_arxiv_id.csv', 'r') as f:
        csv_file = csv.reader(f)
        for i, line in enumerate(csv_file):
            if i % 10000==0:
                print 'Currently on iteration: ', i
            subject_id, arxiv_id = int(line[0]), line[1]
            if subject_id in result_d:
                result_d[subject_id][arxiv_id] = model_dict[arxiv_id]
            else:
                result_d[subject_id] = {arxiv_id: model_dict[arxiv_id]}

    return result_d

def compute_product_scores(result_d):
    '''
    Takes the result from bin_by_subject_id and compute the recommendation based
    on the following: if the user selects subjects 1 and 2, then for each article
    in subject 1 and 2, compute the product of the article's similarity of subject 1
    to that of subject 2. Then sort the resulting list in descending order and take
    the top 100 results.
    '''
    pool = Pool()
    scores_dict = {} #keys are subject_id pairs and value is the list of top 100 scores
    comb = combinations(result_d.keys(), 2) #there are 10731 such combinations
    async_results = []
    for subject_id_1, subject_id_2 in comb:
        print 'Starting process for {}, {}'.format(subject_id_1, subject_id_2)
        async_results.append(pool.apply_async(compute_pair_scores, (subject_id_1, subject_id_2,
                                            result_d[subject_id_1], result_d[subject_id_2], )))
        break #testing
    write_results = []
    for result in async_results:
        if not result.ready():
            result.wait()
        subject_id_1, subject_id_2, scores_list = result.get()
        scores_dict[(min(subject_id_1, subject_id_2), max(subject_id_1, subject_id_2))]=scores_list
        write_results.append(pool.apply_async(pickle_dump_precompute, (subject_id_1,subject_id_2,scores_list,)))

    for result in write_results:
        if not result.ready():
            result.wait()

    return scores_dict

def pickle_dump_precompute(subject_id_1, subject_id_2, scores_list):
    print 'Dumping scores for {}, {}'.format(subject_id_1, subject_id_2)
    with open('./assets/precompute/{}_{}_scores_list.pkl'.format(
        min(subject_id_1, subject_id_2), max(subject_id_1, subject_id_2)), 'wb') as f:
        pickle.dump(scores_list, f)
    return True

def compute_pair_scores(subject_id_1, subject_id_2, dict_1, dict_2):
    '''
    This is a helper called by compute_product_scores. The dictionaries have the
    following format: \{ arxiv_id: \{ subject_id: cos_sim \} \}. We refer to the
    inner dictionary as cos_sim_dict
    '''
    i=0
    scores_list = []
    for d in [dict_1,dict_2]:
        for arxiv_id, cos_sim_dict in d.iteritems():
            if i % 100 == 0 & i !=0:
                print 'Current iteration for {}, {}: {}'.format(subject_id_1, subject_id_2, i)
            # ignore two negatives, whose product will be a misleading positive
            if cos_sim_dict[subject_id_1] < 0 and cos_sim_dict[subject_id_2] < 0:
                continue
            score = cos_sim_dict[subject_id_1] * cos_sim_dict[subject_id_2]
            if len(scores_list) < 100:
                scores_list.append(tuple([arxiv_id, score]))
                continue
            #otherwise, check to see if the score belongs in the list
            minimum = min(scores_list,key=lambda x: x[1])
            if score > minimum :
                scores_list.remove(minimum)
                scores_list.append(tuple([arxiv_id, score]))
            i+=1

    scores_list = sorted(scores_list, key=lambda x: x[1])
    return subject_id_1, subject_id_2, scores_list


if __name__ == '__main__':
    model = Doc2Vec.load('./assets/second_model/second_model')
    model_dict = build_subject_model(model)
    result_d = bin_by_subject_id(model_dict)
    scores_dict = compute_product_scores(result_d)

    pool = Pool()
    print 'Writing to disk...'
    with open('./assets/subject_model.pkl','wb') as f1:
        with open('./assets/complete_model_test.pkl', 'wb') as f2:
            r1=pool.apply_async(pickle.dump, (model_dict,f1,))
            r2=pool.apply_async(pickle.dump, (result_d, f2, ))
    r1.wait()
    r2.wait()
