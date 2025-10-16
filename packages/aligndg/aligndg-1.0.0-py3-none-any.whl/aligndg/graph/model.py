from aligndg.graph.layer import GATConv

import torch.nn.functional as F
import torch.nn as nn


def full_block(in_features, out_features, bias=True, p_drop=0.2):
    return nn.Sequential(
        nn.Linear(in_features, out_features, bias=bias),
        nn.BatchNorm1d(out_features, momentum=0.01, eps=0.001),
        nn.ELU(),
        nn.Dropout(p=p_drop),
    )


class GATAutoEncoder(nn.Module):
    def __init__(self, hidden_dims):
        super(GATAutoEncoder, self).__init__()
        [in_dim, num_hidden, out_dim] = hidden_dims
        self.conv1 = GATConv(in_dim, num_hidden, heads=1, concat=False,
                             dropout=0, add_self_loops=False, bias=False)
        self.conv2 = GATConv(num_hidden, out_dim, heads=1, concat=False,
                             dropout=0, add_self_loops=False, bias=False)
        self.conv3 = GATConv(out_dim, num_hidden, heads=1, concat=False,
                             dropout=0, add_self_loops=False, bias=False)
        self.conv4 = GATConv(num_hidden, in_dim, heads=1, concat=False,
                             dropout=0, add_self_loops=False, bias=False)

    def forward(self, features, edge_index):
        h1 = F.elu(self.conv1(features, edge_index))
        h2 = self.conv2(h1, edge_index, attention=False)
        self.conv3.lin_src.data = self.conv2.lin_src.transpose(0, 1)
        self.conv3.lin_dst.data = self.conv2.lin_dst.transpose(0, 1)
        self.conv4.lin_src.data = self.conv1.lin_src.transpose(0, 1)
        self.conv4.lin_dst.data = self.conv1.lin_dst.transpose(0, 1)

        h3 = F.elu(self.conv3(h2, edge_index, attention=True, tied_attention=self.conv1.attentions))
        h4 = self.conv4(h3, edge_index, attention=False)
        return h2, h4