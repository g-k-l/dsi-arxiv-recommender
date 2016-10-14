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
        subject_centroids = picke.load(f)

    model_dict = {}
    pool = Pool(cpu_count())
    async_results = []

    for idx, doc_vec in enumerate(model.docvecs):
        async_results.append(pool.apply_async(idx, doc_vec, subject_centroids)
        if idx % 3000 == 0 : #take 3000 as the batch size
            for result in async_results:
                if not result.ready():
                    result.wait()
                if result.successful():
                    vec_idx, subject_doc_sims = result.get()
                    arxiv_id = model.docvecs.index_to_doctag[vec_idx]
                    model_dict[arxiv_id] = subject_doc_sims
            async_results=[]

    with open('./assets/subject_model.pkl') as f:
        pickle.dump(model_dict,f)

    return model_dict

def build_single_doc_dict(idx, doc_vec, subject_centroids):
    '''
    Separated from build_subject_model for multiprocessing.
    This function multithreads to build the dictionary
    '''
    subject_doc_sims = {}
    for subject_id, centroid in subject_centroids.iteritems():
        subject_doc_sims[subject_id] = 1-cos(docvec,centroid)
    return idx, subject_doc_sims


if __name__ == '__main__':
    model = Doc2Vec.load('./assets/second_model/second_model')
    model_dict = build_subject_model(model)
    
