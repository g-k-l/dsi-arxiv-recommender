import os
import csv
import pickle
from collections import defaultdict
from itertools import combinations
from scipy.spatial.distance import cosine
import networkx as nx
import community as com
import snap
from gensim.models.doc2vec import Doc2Vec

root_path = './assets/cos_sims_tmps/'


# def get_partitions_snap(file_list,output_path='./assets/idx_community.txt'):
#     '''
#     Uses Stanford snap's implementation of CNM to do community detection
#     Note that since snap does not support weighted graphs, we simply declare
#     all edges as weight 1.
#     '''
#
#
#


def get_partitions_nx(file_list, output_path='./assets/idx_community.txt'):
    '''
    Gets the dictionary where the key is the index, and the
    value is the community label. Loop through all the cos_sim files
    to load the nodes and edges
    '''
    master_g = nx.Graph()
    for filename in file_list:
        next_set = nx.read_weighted_edgelist(root_path+filename, delimiter=',')
        master_g = nx.compose(master_g, next_set)

    nx.write_adjlist(master_g, "cos_sims_full_adj_list.txt") # write to disk
    partition = com.best_partition(master_g)  # partitions is a dictionary
    with open(output_path, 'w') as f:
        writer = csv.writer(f)
        for idx, comm in partition.iteritems():
            writer.writerow([idx,comm])
    return partition

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
    '''
    Compute the pairwise cosine similarities of the community centroids
    '''
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

    with open('./assets/arxiv_id_community.txt', 'w') as f1, \
        open('./assets/community_arxiv_id.txt','w') as f2:
        writer1, writer2 = csv_writer(f1), csv_writer(f2)

        for idx, comm in partition.iteritems():
            arxiv_id_community[model.docvecs.index_to_doctag(idx)] = comm
            community_arxiv_id[comm].append(model.docvecs.index_to_doctag(idx))
            writer1.writerow([model.docvecs.index_to_doctag(idx),comm])

        for comm, arxiv_ids in community_arxiv_id.iteritems():
            writer2.writerow([comm,arxiv_ids])

    return arxiv_id_community, community_arxiv_id


def subset_testing():
    '''
    
    '''



if __name__ == '__main__':
    walker = os.walk('./assets/cos_sims_tmps') #test
    file_list = walker.next[2] #list of file neames in directory
    partition = get_partitions(file_list) #get the partition

    model = Doc2Vec.load('./assets/second_model/second_model')
    centroids = get_community_centroids(model, partition)
    centroid_sims = get_centroid_similarities(centroids)
    subject_centroids = get_subject_centroids(model)
    subject_centroids_sims = get_subject_similarities(subject_centroids)
