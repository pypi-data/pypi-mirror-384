import numpy as np
import torch
import torch.nn.functional as F
from typing import Optional, Tuple, Union

from torch import Tensor
import torch.nn as nn
from torch.nn import Parameter
from torch.nn import init
from torch.nn import Module, Linear, ReLU, ModuleList, BatchNorm1d, Dropout
from torch_geometric.nn.conv import MessagePassing
from torch_geometric.nn.dense.linear import Linear
from torch_geometric.typing import (
    Adj,
    OptTensor,
    PairTensor,
    SparseTensor,
    torch_sparse, OptPairTensor, Size
)
from torch_geometric.utils import (
    add_self_loops,
    is_torch_sparse_tensor,
    remove_self_loops,
    softmax
)
from torch_geometric.utils.sparse import set_sparse_value


class GATConv(MessagePassing):
    r"""The graph attentional operator from the `"Graph Attention Networks"
    <https://arxiv.org/abs/1710.10903>`_ paper

    .. math::
        \mathbf{x}^{\prime}_i = \alpha_{i,i}\mathbf{\Theta}\mathbf{x}_{i} +
        \sum_{j \in \mathcal{N}(i)} \alpha_{i,j}\mathbf{\Theta}\mathbf{x}_{j},

    where the attention coefficients :math:`\alpha_{i,j}` are computed as

    .. math::
        \alpha_{i,j} =
        \frac{
        \exp\left(\mathrm{LeakyReLU}\left(\mathbf{a}^{\top}
        [\mathbf{\Theta}\mathbf{x}_i \, \Vert \, \mathbf{\Theta}\mathbf{x}_j]
        \right)\right)}
        {\sum_{k \in \mathcal{N}(i) \cup \{ i \}}
        \exp\left(\mathrm{LeakyReLU}\left(\mathbf{a}^{\top}
        [\mathbf{\Theta}\mathbf{x}_i \, \Vert \, \mathbf{\Theta}\mathbf{x}_k]
        \right)\right)}.

    Args:
        in_channels (int or tuple): Size of each input sample, or :obj:`-1` to
            derive the size from the first input(s) to the forward method.
            A tuple corresponds to the sizes of source and target
            dimensionalities.
        out_channels (int): Size of each output sample.
        heads (int, optional): Number of multi-head-attentions.
            (default: :obj:`1`)
        concat (bool, optional): If set to :obj:`False`, the multi-head
            attentions are averaged instead of concatenated.
            (default: :obj:`True`)
        negative_slope (float, optional): LeakyReLU angle of the negative
            slope. (default: :obj:`0.2`)
        dropout (float, optional): Dropout probability of the normalized
            attention coefficients which exposes each node to a stochastically
            sampled neighborhood during training. (default: :obj:`0`)
        add_self_loops (bool, optional): If set to :obj:`False`, will not add
            self-loops to the input graph. (default: :obj:`True`)
        bias (bool, optional): If set to :obj:`False`, the layer will not learn
            an additive bias. (default: :obj:`True`)
        **kwargs (optional): Additional arguments of
            :class:`torch_geometric.nn.conv.MessagePassing`.
    """
    _alpha: OptTensor

    def __init__(self, in_channels: Union[int, Tuple[int, int]],
                 out_channels: int, heads: int = 1, concat: bool = True,
                 negative_slope: float = 0.2, dropout: float = 0.0,
                 add_self_loops: bool = True, bias: bool = True,
                 prune_weight: float = 0.0, **kwargs):
        kwargs.setdefault('aggr', 'add')
        super(GATConv, self).__init__(node_dim=0, **kwargs)

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.heads = heads
        self.concat = concat
        self.negative_slope = negative_slope
        self.dropout = dropout
        self.add_self_loops = add_self_loops

        # In case we are operating in bipartite graphs, we apply separate
        # transformations 'lin_src' and 'lin_dst' to source and target nodes:
        # if isinstance(in_channels, int):
        #     self.lin_src = Linear(in_channels, heads * out_channels,
        #                           bias=False, weight_initializer='glorot')
        #     self.lin_dst = self.lin_src
        # else:
        #     self.lin_src = Linear(in_channels[0], heads * out_channels, False,
        #                           weight_initializer='glorot')
        #     self.lin_dst = Linear(in_channels[1], heads * out_channels, False,
        #                           weight_initializer='glorot')

        self.lin_src = nn.Parameter(torch.zeros(size=(in_channels, heads * out_channels)))
        nn.init.xavier_normal_(self.lin_src.data, gain=1.414)
        self.lin_dst = self.lin_src


        # The learnable parameters to compute attention coefficients:
        self.att_src = Parameter(torch.Tensor(1, heads, out_channels))
        self.att_dst = Parameter(torch.Tensor(1, heads, out_channels))
        nn.init.xavier_normal_(self.att_src.data, gain=1.414)
        nn.init.xavier_normal_(self.att_dst.data, gain=1.414)

        # if bias and concat:
        #     self.bias = Parameter(torch.Tensor(heads * out_channels))
        # elif bias and not concat:
        #     self.bias = Parameter(torch.Tensor(out_channels))
        # else:
        #     self.register_parameter('bias', None)

        self._alpha = None
        self.attentions = None

        self.prune_weight = prune_weight
        # self.reset_parameters()

    # def reset_parameters(self):
    #     self.lin_src.reset_parameters()
    #     self.lin_dst.reset_parameters()
    #     glorot(self.att_src)
    #     glorot(self.att_dst)
    #     # zeros(self.bias)

    def forward(self, x: Union[Tensor, OptPairTensor], edge_index: Adj, prune_edge_index: Adj = None,
                size: Size = None, return_attention_weights=None, attention=True, tied_attention = None):
        # type: (Union[Tensor, OptPairTensor], Tensor, Size, NoneType) -> Tensor  # noqa
        # type: (Union[Tensor, OptPairTensor], SparseTensor, Size, NoneType) -> Tensor  # noqa
        # type: (Union[Tensor, OptPairTensor], Tensor, Size, bool) -> Tuple[Tensor, Tuple[Tensor, Tensor]]  # noqa
        # type: (Union[Tensor, OptPairTensor], SparseTensor, Size, bool) -> Tuple[Tensor, SparseTensor]  # noqa
        r"""
        Args:
            return_attention_weights (bool, optional): If set to :obj:`True`,
                will additionally return the tuple
                :obj:`(edge_index, attention_weights)`, holding the computed
                attention weights for each edge. (default: :obj:`None`)
        """
        H, C = self.heads, self.out_channels

        # We first transform the input node features. If a tuple is passed, we
        # transform source and target node features via separate weights:
        if isinstance(x, Tensor):
            assert x.dim() == 2, "Static graphs not supported in 'GATConv'"
            # x_src = x_dst = self.lin_src(x).view(-1, H, C)
            x_src = x_dst = torch.mm(x, self.lin_src).view(-1, H, C)
        else:  # Tuple of source and target node features:
            x_src, x_dst = x
            assert x_src.dim() == 2, "Static graphs not supported in 'GATConv'"
            x_src = self.lin_src(x_src).view(-1, H, C)
            if x_dst is not None:
                x_dst = self.lin_dst(x_dst).view(-1, H, C)

        x = (x_src, x_dst)

        if not attention:
            return x[0].mean(dim=1)
            # return x[0].view(-1, self.heads * self.out_channels)

        if tied_attention == None:
            # Next, we compute node-level attention coefficients, both for source
            # and target nodes (if present):
            alpha_src = (x_src * self.att_src).sum(dim=-1)
            alpha_dst = None if x_dst is None else (x_dst * self.att_dst).sum(-1)
            alpha = (alpha_src, alpha_dst)
            self.attentions = alpha
        else:
            alpha = tied_attention

        if self.add_self_loops:
            if isinstance(edge_index, Tensor):
                # We only want to add self-loops for nodes that appear both as
                # source and target nodes:
                num_nodes = x_src.size(0)
                if x_dst is not None:
                    num_nodes = min(num_nodes, x_dst.size(0))
                num_nodes = min(size) if size is not None else num_nodes
                edge_index, _ = remove_self_loops(edge_index)
                edge_index, _ = add_self_loops(edge_index, num_nodes=num_nodes)
            elif isinstance(edge_index, SparseTensor):
                edge_index = set_diag(edge_index)

        if self.prune_weight == 0:
            # propagate_type: (x: OptPairTensor, alpha: OptPairTensor)
            out = self.propagate(edge_index, x=x, alpha=alpha, size=size)
        else:
            out = (1-self.prune_weight)*self.propagate(edge_index, x=x, alpha=alpha, size=size)+\
                  self.prune_weight*self.propagate(prune_edge_index, x=x, alpha=alpha, size=size)

        alpha = self._alpha
        assert alpha is not None
        self._alpha = None

        if self.concat:
            out = out.view(-1, self.heads * self.out_channels)
        else:
            out = out.mean(dim=1)

        # if self.bias is not None:
        #     out += self.bias

        if isinstance(return_attention_weights, bool):
            if isinstance(edge_index, Tensor):
                return out, (edge_index, alpha)
            elif isinstance(edge_index, SparseTensor):
                return out, edge_index.set_value(alpha, layout='coo')
        else:
            return out

    def message(self, x_j: Tensor, alpha_j: Tensor, alpha_i: OptTensor,
                index: Tensor, ptr: OptTensor,
                size_i: Optional[int]) -> Tensor:
        # Given egel-level attention coefficients for source and target nodes,
        # we simply need to sum them up to "emulate" concatenation:
        alpha = alpha_j if alpha_i is None else alpha_j + alpha_i

        # alpha = F.leaky_relu(alpha, self.negative_slope)
        alpha = torch.sigmoid(alpha)
        alpha = softmax(alpha, index, ptr, size_i)
        self._alpha = alpha  # Save for later use.
        alpha = F.dropout(alpha, p=self.dropout, training=self.training)
        return x_j * alpha.unsqueeze(-1)

    def __repr__(self):
        return '{}({}, {}, heads={})'.format(self.__class__.__name__,
                                             self.in_channels,
                                             self.out_channels, self.heads)


class GraphSAGE(Module):
    def __init__(self, in_channels, hidden_dims, agg_class, dropout=0., num_samples=25, BN=False):
        super(GraphSAGE, self).__init__()
        self.in_channels = in_channels
        self.hidden_dims = hidden_dims
        self.agg_class = agg_class
        self.aggregators = ModuleList([agg_class(in_channels, in_channels)])
        self.aggregators.extend([agg_class(dim, dim) for dim in hidden_dims])

        self.dropout = dropout
        self.num_samples = num_samples
        self.BN = BN

        self.fcs = ModuleList([Linear(2 * in_channels, hidden_dims[0])])
        self.fcs.extend([Linear(2 * hidden_dims[i - 1], hidden_dims[i]) for i in range(1, len(hidden_dims))])

        if self.BN:
            self.bns = ModuleList([BatchNorm1d(hidden_dim) for hidden_dim in hidden_dims])
        else:
            self.bns = None

        self.dropout = Dropout(dropout)
        self.relu = ReLU()
        self.init_weights()

    def init_weights(self):
        for m in self.modules():
            if isinstance(m, Linear):
                init.xavier_normal_(m.weight.data)
                if m.bias is not None:
                    m.bias.data.zero_()

    def forward(self, features, node_layers, mapping, rows):
        out = features
        for k in range(len(self.hidden_dims)):
            nodes = node_layers[k + 1]
            mapping = mapping[k]
            init_mapped_nodes = np.array([mapping[0][v] for v in nodes], dtype=np.int64)
            cur_rows = rows[init_mapped_nodes]
            aggregate = self.aggregators[k](out, nodes, mapping, cur_rows, self.num_samples)
            cur_mapped_nodes = np.array([mapping[v] for v in nodes], dtype=np.int64)

            out = torch.cat((out[cur_mapped_nodes, :], aggregate), dim=1)
            out = self.fcs[k](out)
            if k + 1 < len(self.hidden_dims):
                if self.BN:
                    out = self.bns[k](out)
                else:
                    out = self.relu(out)
                    out = self.dropout(out)
        return out


class Aggregator(Module):
    def __init__(self, in_channels: int=None, out_channels: int=None):
        super().__init__()
        self.input_dim = in_channels
        self.output_dim = out_channels

    def forward(self, features, nodes, mapping, rows, num_samples):
        mapped_rows = [np.array([mapping[v] for v in row], dtype=np.int64) for row in rows]
        if num_samples == -1:
            sampled_rows = mapped_rows
        else:
            sampled_rows = [np.random.choice(row, min(len(row), num_samples), len(row) < num_samples) for row in mapped_rows]

        n = len(nodes)
        out = torch.zeros(n, self.output_dim)
        for i in range(n):
            if len(sampled_rows[i]) != 0:
                out[i, :] = self._aggregate(features[sampled_rows[i], :])
        return out

    def _aggregate(self, features):
        raise NotImplementedError


class PoolAggregator(Aggregator):

    def __init__(self, input_dim, output_dim):
        super(PoolAggregator, self).__init__(input_dim, output_dim)

        self.fc1 = Linear(input_dim, output_dim)
        self.relu = ReLU()

    def _aggregate(self, features):
        out = self.relu(self.fc1(features))
        return self._pool_fn(out)

    def _pool_fn(self, features):
        raise NotImplementedError


class MaxPoolAggregator(PoolAggregator):
    def _pool_fn(self, features):
        return torch.max(features, dim=0)[0]


class MeanPoolAggregator(PoolAggregator):
    def _pool_fn(self, features):
        return torch.mean(features, dim=0)
