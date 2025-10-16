import pickle
from collections import defaultdict
from sklearn.manifold import SpectralEmbedding
import torch
import numpy as np
import copy
import networkx as nx
import matplotlib.pyplot as plt
from utils.utils_eval import *
import torch.nn.functional as F
import os


def get_spectral_emb(adj, max_size):
    """
    Given adj is N*N, return its feature mat N*D, D is fixed in model
    :param adj: adjacent matrix
    :param max_size: the amount of dimension to be embedded
    :return: spectral embedding of every node in this graph
    """

    adj_ = adj.data.cpu().numpy()
    emb = SpectralEmbedding(n_components=max_size)
    res = emb.fit_transform(adj_)
    x = torch.from_numpy(res).float().cuda()
    return x


def get_embedding(adj, max_size=2, method='spectral'):
    if method == 'spectral':
        return get_spectral_emb(adj, max_size)
    return adj[:, :max_size]


def normalize(adj):
    adj = adj.data.cpu().numpy()
    adj_ = adj + np.eye(adj.shape[0])
    rowsum = np.array(adj_.sum(1))
    degree_mat_inv_sqrt = np.diag(np.power(rowsum, -0.5).flatten())
    degree_mat_sqrt = np.diag(np.power(rowsum, -0.5).flatten())
    adj_normalized = degree_mat_inv_sqrt.dot(adj_).dot(degree_mat_sqrt)
    return torch.from_numpy(adj_normalized).float().cuda()


def cat_cond(x, cond_vec):
    if cond_vec is None:
        return x
    attr_mat = cond_vec.repeat(x.size()[0], 1)
    x = torch.cat([x, attr_mat], dim=1)
    return x


def show_graph(adj, base_adj=None, remove_isolated=True, show=False):
    if not isinstance(adj, np.ndarray):
        adj_ = adj.data.cpu().numpy()
    else:
        adj_ = copy.deepcopy(adj)

    adj_ -= np.diag(np.diag(adj_))

    assert ((adj_ == adj_.T).all())
    if show:
        gr = nx.from_numpy_array(adj_)
        if remove_isolated:
            gr.remove_nodes_from(list(nx.isolates(gr)))
        nx.draw(gr, node_size=10)
        plt.title('gen')
        plt.show()

    d = compute_graph_statistics(adj_)
    #pprint.pprint(d)

    if base_adj is not None:
        base_gr = nx.from_numpy_array(base_adj)
        if show:
            nx.draw(base_gr, node_size=10)
            plt.title('base')
            plt.show()
        bd = compute_graph_statistics(base_adj)
        diff_d = {}
        for k in list(d.keys()):
            diff_d[k] = round(abs(d[k] - bd[k]), 4)
        # print(diff_d.keys())
        # print(diff_d.values())
        return diff_d


def keep_topk_conns(adj, k=3):
    g = nx.from_numpy_array(adj)
    to_removes = [cp for cp in sorted(nx.connected_components(g), key=len)][:-k]
    for cp in to_removes:
        g.remove_nodes_from(cp)
    adj = nx.to_numpy_array(g)
    return adj


def top_n_indexes(arr, n):
    idx = np.argpartition(arr, arr.size - n, axis=None)[-n:]
    width = arr.shape[1]
    return [divmod(i, width) for i in idx]


def topk_adj(adj, k):
    adj_ = adj.data.cpu().numpy()
    #print("adj prob:\n{}".format(adj_))
    assert ((adj_ == adj_.T).all())
    adj_ = (adj_ - np.min(adj_)) / np.ptp(adj_)
    adj_ -= np.diag(np.diag(adj_))
    # print("prob:\n{}".format(adj))
    tri_adj = np.triu(adj_)
    inds = top_n_indexes(tri_adj, k // 2)
    res = torch.zeros(adj.shape)
    for ind in inds:
        i = ind[0]
        j = ind[1]
        res[i, j] = 1.0
        res[j, i] = 1.0
    #print("adj:\n{}".format(res))
    return res.cuda()


def gen_graph(model, n, e, attr_vec, z_size, opt):
    fixed_noise = torch.randn((n, z_size), requires_grad=True).cuda()
    # print("the shape of attr_gen1: {}".format(fixed_noise.data.cpu().numpy().shape))
    if opt.cond_size:
        fixed_noise = cat_cond(fixed_noise, attr_vec)
    # print("the shape of attr_gen2: {}".format(fixed_noise.data.cpu().numpy().shape))
    rec_adj = model.decoder(fixed_noise)
    return topk_adj(F.sigmoid(rec_adj), e * 2)


def load_data(DATA_FILEPATH='ENZYMES_587.graphs', split=False):
    data_dict = pickle.load(open(DATA_FILEPATH, 'rb'))
    adj_mats = data_dict['adj_mats']
    attr_vecs = data_dict['attr_vecs']
    if split:
        train_adj_mats = adj_mats[:int(len(adj_mats) * .8)]
        train_attr_vecs = attr_vecs[:int(len(attr_vecs) * .8)]
    else:
        train_adj_mats = adj_mats
        train_attr_vecs = attr_vecs
    test_adj_mats = adj_mats[int(len(adj_mats) * .8):]
    test_attr_vecs = attr_vecs[int(len(attr_vecs) * .8):]
    return train_adj_mats, test_adj_mats, train_attr_vecs, test_attr_vecs


def load_dblp_data(DATA_DIR):
    # script for loading NWE dblp
    # folder structure
    # - this.ipynb
    # - $DATA_DIR - *.txt

    mat_names = []  # e.g. GSE_2304
    adj_mats = []  # essential data, type: list(np.ndarray)
    attr_vecs = []  # essential data, type: list(np.ndarray)
    id_maps = []  # map index to gene name if you need

    for f in os.listdir(DATA_DIR):
        if not f.startswith(('nodes', 'links', 'attrs')):
            continue
        else:
            mat_names.append('_'.join(f.split('.')[0].split('_')[1:]))
    mat_names = sorted([it for it in set(mat_names)])
    print('Test length', len(mat_names))
    for mat_name in mat_names:
        node_file = 'nodes_' + mat_name + '.txt'
        link_file = 'links_' + mat_name + '.txt'
        attr_file = 'attrs_' + mat_name + '.txt'
        node_file_path = os.path.join(DATA_DIR, node_file)
        link_file_path = os.path.join(DATA_DIR, link_file)
        attr_file_path = os.path.join(DATA_DIR, attr_file)

        id_to_item = {}
        with open(node_file_path, 'r') as f:
            for i, line in enumerate(f):
                author = line.rstrip('\n')
                id_to_item[i] = author
        all_ids = set(id_to_item.keys())

        with open(attr_file_path, 'r') as f:
            attr_vec = np.loadtxt(f).T.flatten()
            attr_vecs.append(attr_vec)

        links = defaultdict(set)
        with open(link_file_path, 'r') as f:
            for line in f:
                cells = line.rstrip('\n').split(',')
                from_id = int(cells[0])
                to_id = int(cells[1])
                if from_id in all_ids and to_id in all_ids:
                    links[from_id].add(to_id)

        N = len(all_ids)
        adj = np.zeros((N, N))
        for from_id in range(N):
            for to_id in links[from_id]:
                adj[from_id, to_id] = 1
                adj[to_id, from_id] = 1

        adj -= np.diag(np.diag(adj))
        id_map = [id_to_item[i] for i in range(N)]

        # Remove small component
        # adj = remove_small_conns(adj, keep_min_conn=4)

        # Keep large component
        adj = keep_topk_conns(adj, k=1)
        adj_mats.append(adj)
        id_maps.append(id_map)

        if int(np.sum(adj)) == 0:
            adj_mats.pop(-1)
            id_maps.pop(-1)
            mat_names.pop(-1)
            attr_vecs.pop(-1)

    # train_adj_mats = adj_mats[:int(len(adj_mats) * .8)]
    train_adj_mats = adj_mats[:int(len(adj_mats))]
    test_adj_mats = adj_mats[int(len(adj_mats) * .8):]
    # train_attr_vecs = attr_vecs[:int(len(attr_vecs) * .8)]
    train_attr_vecs = attr_vecs[:int(len(attr_vecs))]
    test_attr_vecs = attr_vecs[int(len(attr_vecs) * .8):]
    return train_adj_mats, test_adj_mats, train_attr_vecs, test_attr_vecs