import networkx as nx
import community as com
from gensim.models.doc2vec import Doc2Vec

def get_partitions(filename,output_name='communities.pkl'):
    '''
    Gets the dictionary where the key is the index, and the
    value is the community label
    '''
    g = read_weighted_edgelist('graph.txt')
    partitions = com.best_partition(g) #partitions is a dictionary
    with open(output_name, 'wb') as f:
        pickle.dump(partitions, f)
    return partitions

def build_idx_to_community(idx_selected, partitions):
    '''
    Takes the idx_selected (from compute_similarity), partitions (community labels)
    and form a dictionary mapping between the two.
    '''
    return {idx_selected[key]: value for key, value in partitions.iteritems()}

def build_arxiv_id_to_community(modelname, idx_to_community):
    '''
    Takes the idx_to_community dictionary, feed its keys to doc2vec.docvecs
    index_to_doctag to obtain a dictionary containing arxiv_id (str): community (int).
    '''
    model = Doc2Vec.load(modelname)
    return {model.docvecs.index_to_doctag(key):value for key, value in idx_to_community.iteritems()}
