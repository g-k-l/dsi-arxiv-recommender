from sklearn.cluster import KMeans
from gensim.models.doc2vec import Doc2Vec
from multiprocessing import Process, cpu_count
import threading
import pickle

'''DEFUNCT'''

def cluster_job():
    model = Doc2Vec.load('adam.first')
    docvecs = model.docvecs
    n_clusters = xrange(200)
    processes = []

    for i in n_clusters:
        result_list = range(200)
        def kmeans_job(n_clusters, docvecs):
            if n_clusters>4:
                result_list[i] = KMeans(n_clusters).fit(docvecs)
            print 'Completed cluster ', n_clusters

        if len(processes) == cpu_count():
            map(lambda p: p.join(), processes)
            processes = []

        p = Process(target=kmeans_job, args=(i,docvecs))
        processes.append(p)
        p.start()
    if len(processes) != 0:
        map(lambda p: p.join(), processes)

    return result_list

def pickle_dump(result_list):
    with open('kmeans_models.pkl', 'wb') as f:
        pickle.dump(result_list,f)
    print 'Job Completed.'


if __name__ == '__main__':
    pickle_dump(cluster_job())
