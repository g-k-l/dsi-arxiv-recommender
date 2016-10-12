import csv
import pickle
from collections import defaultdict
from itertools import combinations
from scipy.spatial.distance import cosine
import networkx as nx
import community as com
from gensim.models.doc2vec import Doc2Vec


def get_partitions(filename, output_path='./assets/idx_community.txt'):
    '''
    Gets the dictionary where the key is the index, and the
    value is the community label.
    '''
    g = read_weighted_edgelist(filename, delimiter=',')
    partition = com.best_partition(g)  # partitions is a dictionary
    with open(output_path, 'w') as f:
        writer = csv.writer(f)
        for idx, comm in partition:
            writer.writerow([idx,comm])
    return partitions

def get_community_centroids(model, partition):
    '''
    Computes the centroid for each community in the partition by averaging taking
    the average of all the vectors in that community.
    '''
    tmp = defaultdict(list)
    for idx, comm in partition:
        tmp[comm].append(model.docvecs[idx])
    return {comm: reduce(lambda x,y: x+y, vectors)/len(vectors) for comm, vectors in tmp.iteritems()}

def get_centroid_similarities(centroids):
    comb = combinations(centroids.keys(), 2)
    centroid_sims = []
    with open('./assets/centroid_sims.txt', 'w') as f:
        writer = csv.writer(f)
        for c1, c2 in comb:
            centroid_sims.append([c1, c2, cosine(c1,c2)])
            writer.writerow([c1,c2,cosine(c1,c2)])
    return centroid_sims

def get_subject_centroids(model):
    '''
    Computes the centroid of each subject by taking the average of vectors belonging
    to that subject. Loads subject_dict.pkl, which is built by compute_sample_similarity.py
    '''
    with open('./assets/subject_dict.pkl', 'rb') as f:
        subject_dict = pickle.load(f)
    subject_centroids = {}
    for subject_id, idx_list in subject_dict.iteritems():
        subject_centroids[subject_id] = np.mean(model.docvecs[idx_list])
    return subject_centroids

def get_subject_similarities(centroids):
    comb = combinations(centroids.keys(), 2)
    centroid_sims = []
    with open('./assets/subject_sims.txt', 'w') as f:
        writer = csv.writer(f)
        for c1, c2 in comb:
            centroid_sims.append([c1, c2, cosine(c1,c2)])
            writer.writerow([c1,c2,cosine(c1,c2)])
    return centroid_sims

def build_arxiv_id_to_community(model, partition):
    '''
    Takes the partition dictionary, feed its keys to doc2vec.docvecs.index_to_doctag
    to obtain a dictionary containing arxiv_id (str): community (int) and the inverse
    community (int): arxiv_ids (list)
    '''
    arxiv_id_community = {}
    community_arxiv_id = defaultdict(list)

    with open('./assets/arxiv_id_community.txt', 'w') as f1,
        open('./assets/community_arxiv_id.txt','w') as f2:
        writer1, writer2 = csv_writer(f1), csv_writer(f2)

        for idx, comm in partition.iteritems():
            arxiv_id_community[model.docvecs.index_to_doctag(idx)] = comm
            community_arxiv_id[comm].append(model.docvecs.index_to_doctag(idx))
            writer1.writerow([model.docvecs.index_to_doctag(idx),comm])

        for comm, arxiv_ids in community_arxiv_id.iteritems():
            writer2.writerow([comm,arxiv_ids])

    return arxiv_id_community, community_arxiv_id
