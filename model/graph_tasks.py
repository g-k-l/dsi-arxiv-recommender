import os
import csv
import pickle
from collections import defaultdict
from itertools import combinations
import numpy as np
from scipy.spatial.distance import cosine
import networkx as nx
import community as com
from gensim.models.doc2vec import Doc2Vec

root_path = './assets/cos_sims/'

def get_partitions(file_list, output_path='./assets/idx_community.txt'):
    '''
    Gets the dictionary where the key is the index, and the
    value is the community label. Loop through all the cos_sim files
    to load the nodes and edges
    '''
    master_g = nx.Graph()
    for i, filename in enumerate(file_list):
        if i % 20 == 0:
            print 'Current iteration: {} out of {}.'.format(i, len(file_list))
            if i == 100:
                break
        next_set = nx.read_weighted_edgelist(root_path+filename, delimiter=',')
        master_g = nx.compose(master_g, next_set)

    print 'Writing combined graph to disk...'
    nx.write_weighted_edgelist(master_g, "./assets/cos_sims_full_edgelist.txt") # write to disk
    print 'Starting Community Detection'
    partition = com.best_partition(master_g)  # partitions is a dictionary
    print 'Partition Completed, Writing to Disk... '
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
    with open('./assets/community_centroids.pkl','wb') as f:
        writer = csv.writer(f)
        for idx, comm in partition.iteritems():
            tmp[comm].append(model.docvecs[int(idx)])

        result_d = {comm: reduce(lambda x,y: x+y, vectors)/len(vectors) for comm, vectors in tmp.iteritems()}
        pickle.dump(result_d,f)
    return result_d

def get_centroid_similarities(centroids):
    '''
    Compute the pairwise cosine similarities of the community centroids
    '''
    comb = combinations(centroids.keys(), 2)
    centroid_sims = []
    with open('./assets/centroid_sims.txt', 'w') as f:
        writer = csv.writer(f)
        for c1, c2 in comb:
            centroid_sims.append([c1, c2, 1-cosine(centroids[c1],centroids[c2])])
            writer.writerow([c1,c2,1-cosine(centroids[c1],centroids[c2])])
    return centroid_sims

def get_subject_centroids(model):
    '''
    Computes the centroid of each subject by taking the average of vectors belonging
    to that subject. Loads subject_dict.pkl, which is built by compute_sample_similarity.py
    '''
    with open('./assets/subject_dict.pkl', 'rb') as f:
        subject_dict = pickle.load(f)
    subject_centroids = {}
    with open('./assets/subject_centroids.pkl','wb') as f:
        for subject_id, idx_list in subject_dict.iteritems():
            subject_centroids[subject_id] = np.mean(model.docvecs[idx_list],axis=0)
        pickle.dump(subject_centroids,f)
    return subject_centroids

def get_subject_similarities(centroids):
    comb = combinations(centroids.keys(), 2)
    centroid_sims = []
    with open('./assets/subject_sims.txt', 'w') as f:
        writer = csv.writer(f)
        for c1, c2 in comb:
            centroid_sims.append([c1, c2, 1-cosine(centroids[c1],centroids[c2])])
            writer.writerow([c1,c2,1-cosine(centroids[c1],centroids[c2])])
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


if __name__ == '__main__':
    walker = os.walk(root_path) #test
    file_list = walker.next()[2] #list of file neames in directory
    print 'Getting partitions'
    partition = get_partitions(file_list) #get the partition
    print 'Loading Model'
    model = Doc2Vec.load('./assets/second_model/second_model')
    print 'Starting centroid computations'
    centroids = get_community_centroids(model, partition)
    centroid_sims = get_centroid_similarities(centroids)
    #subject_centroids = get_subject_centroids(model)
    #subject_centroids_sims = get_subject_similarities(subject_centroids)
    print 'Completed.'
