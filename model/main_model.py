import pickle
from scipy.spatial.distance import cosine
from gensim.models.doc2vec import Doc2Vec
from multiprocessing import Pool, cpu_count

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

    print 'Writing to disk...'
    with open('./assets/subject_model.pkl','wb') as f:
        pickle.dump(model_dict,f)

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


if __name__ == '__main__':
    model = Doc2Vec.load('./assets/second_model/second_model')
    model_dict = build_subject_model(model)
    
