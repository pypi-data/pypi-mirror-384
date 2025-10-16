import torch
from torch.nn.modules.module import Module
import torch.nn.init as init
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from sklearn.metrics import confusion_matrix
from torch.nn.parameter import Parameter
import math
from dpplgngr.utils.utils_data_graph import normalize, get_embedding
# models
# GCN

class GCN(Module):
    """
    GCN layer, reference to: https://arxiv.org/abs/1609.02907
    """

    def __init__(self, input_len, output_len, bias=True):
        super(GCN, self).__init__()
        self.input_len = input_len
        self.output_len = output_len
        # print("Type of ouput_len: {}\t, value of output_len: {}".format(type(output_len), output_len))
        self.W = Parameter(torch.FloatTensor(input_len, output_len))
        if bias:
            self.b = Parameter(torch.FloatTensor(output_len))
        else:
            self.register_parameter('b', None)

    def reset_parameters(self):
        """
        reset parameters in uniform distribution
        """
        margin = 1. / math.sqrt(self.W.size(1))
        self.W.data.uniform_(-margin, margin)
        if self.b is not None:
            self.b.data.uniform_(-margin, margin)

    def forward(self, inputs, adj):
        """
        When this layer is called, execute this function.
        :param inputs:  embedded node vectors (with condition context)
        :param adj:  adjacent matrix
        :return: output of GCN layer
        """
        # print("Type of inputs: {}".format(type(inputs)))
        # print("Type of weights: {}".format(type(self.W)))
        support = torch.mm(inputs, self.W)
        # output = torch._sparse_mm(adj, support)
        output = torch.spmm(adj, support)
        if self.b is None:
            return output
        else:
            return output + self.b

    def __str__(self):
        return "Layer: {}({}->{})".format(self.__class__.__name__, self.input_len, self.output_len)

    def __repr__(self):
        return "Layer: {}({}->{})".format(self.__class__.__name__, self.input_len, self.output_len)


class GCNEncoder(nn.Module):
    def __init__(self, emb_size, hidden_dim, layer_num=2):
        super(GCNEncoder, self).__init__()
        self.act = nn.ReLU()
        self.gc_top = GCN(emb_size, hidden_dim)
        self.gc_medium = nn.ModuleList([GCN(hidden_dim, hidden_dim) for i in range(layer_num-1)])
        self.mean = nn.Sequential(nn.Linear(hidden_dim, hidden_dim//2),
                                  nn.ReLU(),
                                  nn.Linear(hidden_dim//2, hidden_dim//2))
        self.logvar = nn.Sequential(nn.Linear(hidden_dim, hidden_dim//2),
                                    nn.ReLU(),
                                    nn.Linear(hidden_dim//2, hidden_dim//2))
        for m in self.modules():
            # print(m)
            if isinstance(m, nn.Linear):
                m.weight.data = init.xavier_uniform(m.weight.data, gain=nn.init.calculate_gain('relu'))
            elif isinstance(m, GCN):
                m.reset_parameters()
                # m.W.data = init.xavier_uniform(m.W.data, gain=nn.init.calculate_gain('relu'))

    def forward(self, x, adj, normalized=True):
        """
        call this function when you use encoder
        :param normalized: whether the adjacent matrix is normalized
        :param x: node features of one graph
        :param adj: Normalized adjacency matrix of one graph.
        :return:
        """
        if not normalized:
            adj = normalize(adj)
        x = self.gc_top(x, adj)
        x = self.act(x)
        for gcn in self.gc_medium:
            x = gcn(x, adj)
            x = self.act(x)
        mean = self.mean(x)
        logvar = self.logvar(x)
        return mean, logvar


class VanillaDecoder(nn.Module):
    def __init__(self, dropout=0.5):
        """
        InnerProductDecoder definition.
        :param dropout: probability to randomly zero some of the elements from a Bernoulli distribution.
        """
        super(VanillaDecoder, self).__init__()
        self.act = nn.Sigmoid()
        self.dropout = dropout

    def forward(self, x):
        x = F.dropout(x, p=self.dropout)
        rec = torch.mm(x, x.permute(1, 0))
        return self.act(rec)


class MLPDecoder(nn.Module):
    def __init__(self, input_dim, hidden_dim=16, dropout=0.5):
        super(MLPDecoder, self).__init__()
        self.act = nn.Sigmoid()
        self.dropout = dropout
        self.decode = nn.Sequential(nn.Linear(input_dim, hidden_dim),
                                    nn.ReLU(),
                                    nn.Linear(hidden_dim, hidden_dim//2))
        for m in self.modules():
            if isinstance(m, nn.Linear):
                m.weight.data = init.xavier_uniform(m.weight.data, gain=nn.init.calculate_gain('relu'))

    def forward(self, x):
        x = F.dropout(x, p=self.dropout)
        x = self.decode(x)
        rec = torch.mm(x, x.permute(1, 0))
        return self.act(rec)


class GraphVAE(nn.Module):
    def __init__(self, emb_size, encode_dim, layer_num, decode_dim, dropout, logits):
        super(GraphVAE, self).__init__()
        self.encoder = GCNEncoder(emb_size=emb_size,
                                  hidden_dim=encode_dim,
                                  layer_num=layer_num)
        self.decoder = MLPDecoder(input_dim=encode_dim//2,
                                  hidden_dim=decode_dim,
                                  dropout=dropout)
        self.logits = logits

    @staticmethod
    def remove_eye(adj):
        adj_ = adj
        assert ((adj_ == adj_.T).all())
        adj_ -= torch.diag(torch.diag(adj_))
        return adj_

    @staticmethod
    def calc_metric(y_pred, y_true):
        eps = 1e-5
        if isinstance(y_pred, torch.Tensor):
            y_pred = (y_pred*2-eps).int()
            y_pred = y_pred.data.cpu().numpy().reshape(-1).tolist()
        if isinstance(y_true, torch.Tensor):
            y_true = y_true.int()
            y_true = y_true.data.cpu().numpy().reshape(-1).tolist()
        return confusion_matrix(y_true, y_pred)

    def forward(self, adj, x=None, normalized=True, training=True, with_logits=True):
        if x is None:
            x = get_embedding(adj, max_size=8, method='spectral')
        mean, logvar = self.encoder(x, adj, normalized)
        noise = torch.randn(mean.shape, requires_grad=True).cuda()
        std = logvar.mul(0.5).exp_()
        if training:
            pl = []
            for j in range(mean.shape[0]):
                prior_loss = 1 + logvar[j, :] - mean[j, :].pow(2) - logvar[j, :].exp()
                # torch.numel refers to the total number of elements in the tensor, instead of the sum of elements.
                prior_loss = (-0.5 * torch.sum(prior_loss)) / torch.numel(mean[j, :].data)
                # print("prior loss: {}".format(prior_loss.data))
                pl.append(prior_loss)
            loss_kl = sum(pl)
            x = mean + std * noise
            rec_adj = self.decoder(x)
            # rec_adj = self.remove_eye(rec_adj)
            if with_logits:
                neg_weight = self.logits
                binary_cross_entropy = nn.BCEWithLogitsLoss(pos_weight=torch.ones(1)*neg_weight)
            else:
                binary_cross_entropy = nn.BCELoss()
            binary_cross_entropy.cuda()
            loss_rec = binary_cross_entropy(rec_adj, adj)
            confus_m = self.calc_metric(rec_adj, adj)
            return loss_kl, loss_rec, confus_m
        else:
            x = mean
            rec_adj = self.decoder(x)
            confus_m = self.calc_metric(rec_adj, adj)
            return rec_adj, confus_m