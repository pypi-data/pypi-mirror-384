import torch
import numpy as np
import networkx as nx
from aligndg.uopt.problems.space import AlignmentProblem
import torch
from torch_geometric.data import Data
from aligndg.graph.model import GATAutoEncoder
from tqdm import tqdm
import torch.nn.functional as F
import pandas as pd


def train_AlignDG(adata,
                  batch_key='slice_name',
                  hidden_dims=[512, 32],
                  pre_epoch=500,
                  total_epoch=1000,
                  iter_comb=None,
                  lamb=1,
                  beta=0.1,
                  alpha1=1,
                  alpha2=1,
                  epsilon=1e-3,
                  low_rank=False):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    data = Data(
        edge_index=torch.LongTensor(np.array([adata.uns['edge_list'][0], adata.uns['edge_list'][1]])),
        prune_edge_index=torch.LongTensor(np.array([])), x=torch.FloatTensor(adata.X.todense()))
    data = data.to(device)
    section_ids = adata.obs[batch_key].unique()

    model = GATAutoEncoder(hidden_dims=[adata.shape[1], hidden_dims[0], hidden_dims[1]]).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    model.train()

    for _ in tqdm(range(0, pre_epoch)):
        optimizer.zero_grad()
        z, out = model(data.x, data.edge_index)
        loss = F.mse_loss(out, data.x)
        loss.backward()
        torch.nn.utils.clip_grad_value_(model.parameters(), 5.0)
        optimizer.step()

    with torch.no_grad():
        model.eval()
        z, _ = model(data.x, data.edge_index)
        adata.obsm['raw_latent'] = z.cpu().detach().numpy()
        adata.obsm['latent'] = z.cpu().detach().numpy()

    epoch_iter = tqdm(range(pre_epoch, total_epoch), position=0)
    for epoch in epoch_iter:
        if epoch % 100 == 0 or epoch == 500:
            print('Update spot triplet at epoch {}'.format(epoch))
            adata.obsm['latent'] = z.cpu().detach().numpy()
            spot_pairs_dict, pis = create_spot_pairs(input_adata=adata, input_iter_comb=iter_comb,
                                                     use_rep='latent', alpha=beta, tau_a=alpha1, tau_b=alpha2,
                                                     epsilon=epsilon, low_rank=low_rank)
            anchor_ind = []
            positive_ind = []
            negative_ind = []

            for slice_pair in spot_pairs_dict.keys():
                batch_name_list = adata.obs['slice_name'][spot_pairs_dict[slice_pair].keys()]
                cell_name_by_batch_dict = dict()
                for batch_id in range(len(section_ids)):
                    cell_name_by_batch_dict[section_ids[batch_id]] = adata.obs_names[
                        adata.obs[batch_key] == section_ids[batch_id]].values

                anchor_list = []
                positive_list = []
                negative_list = []

                for anchor in spot_pairs_dict[slice_pair].keys():
                    anchor_list.append(anchor)
                    positive_spot = spot_pairs_dict[slice_pair][anchor][0]
                    positive_list.append(positive_spot)
                    section_size = len(cell_name_by_batch_dict[batch_name_list[anchor]])
                    # print(section_size)
                    negative_list.append(
                        cell_name_by_batch_dict[batch_name_list[anchor]][np.random.randint(section_size)])

                batch_as_dict = dict(zip(list(adata.obs_names), range(0, adata.shape[0])))
                anchor_ind = np.append(anchor_ind, list(map(lambda _: batch_as_dict[_], anchor_list)))
                positive_ind = np.append(positive_ind, list(map(lambda _: batch_as_dict[_], positive_list)))
                negative_ind = np.append(negative_ind, list(map(lambda _: batch_as_dict[_], negative_list)))

        model.train()
        optimizer.zero_grad()

        z, out = model(data.x, data.edge_index)
        mse_loss = F.mse_loss(out, data.x)

        anchor_arr = z[anchor_ind,]
        positive_arr = z[positive_ind,]
        negative_arr = z[negative_ind,]

        triplet_loss = torch.nn.TripletMarginLoss(margin=1, p=2, reduction='mean')
        tri_output = triplet_loss(anchor_arr, positive_arr, negative_arr)

        loss = mse_loss + lamb * tri_output
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.)
        optimizer.step()
        epoch_iter.set_description(
            f"# Epoch {epoch}, loss: {loss.item():.3f}, gene_recon: {mse_loss.item():.3f}, triplet loss: {tri_output.item()}")

    with torch.no_grad():
        model.eval()

    z, out = model(data.x, data.edge_index)
    adata.obsm['latent'] = z.cpu().detach().numpy()
    return adata, pis



def create_spot_pairs(input_adata, input_iter_comb, use_rep='latent', alpha=0.1, tau_a=1, tau_b=1, epsilon=1e-3, low_rank=False):
    slice_list = input_adata.obs['slice_name']
    slices = []
    slice_features = []
    spot_names = input_adata.obs_names
    spots = []
    pis = []

    for i in slice_list.unique():
        slices.append(input_adata[slice_list == i])
        slice_features.append(input_adata[slice_list == i].obsm[use_rep])
        spots.append(spot_names[slice_list == i])

    slice_name_df = pd.DataFrame(np.array(slice_list.unique()))
    spot_pairs = dict()

    for comb in input_iter_comb:
        i = slice_name_df.loc[comb[0]].values[0]
        j = slice_name_df.loc[comb[1]].values[0]
        key_name = i + '_' + j

        print('Processing datasets {}'.format((i, j)))
        spot_pairs[key_name] = {}

        ''' for simplicity, we temporarily employ the FGW code provided in Moscot to implement optimal transport '''
        handle_adata = input_adata[(input_adata.obs['slice_name'] == i) | (input_adata.obs['slice_name'] == j)]
        
        ap = AlignmentProblem(adata=handle_adata)
        ap = ap.prepare(batch_key='slice_name', joint_attr=use_rep)

        if not low_rank:
            ap = ap.solve(alpha=alpha, tau_a=tau_a, tau_b=tau_b, epsilon=epsilon)
            pi = ap.solutions[list(ap.solutions)[0]].transport_matrix
            pis.append(pi)
            rows, cols = np.where(pi > 0)
        else:
            # todo: implement the low-rank code
            ap = ap.solve(alpha=alpha, tau_a=tau_a, tau_b=tau_b, epsilon=0, rank=500)
            ans = ap.solutions[list(ap.solutions)[0]]._output
            q = ans.q
            r = ans.r
            g = ans.g
            g_safe = np.asarray(g, dtype=float)
            g_safe = g_safe + 1e-12
            middle = np.diag(1.0 / g_safe)
            left_mat = q @ middle
            right_mat = middle @ r.T

            m = left_mat.shape[0]
            rows = np.arange(m, dtype=np.int64)
            cols = np.empty(m, dtype=np.int64)
            for r_idx in tqdm(range(m), desc=f"argmax per row (low-rank {si}->{sj})", leave=True):
                res_row = left_mat[r_idx] @ right_mat     # shape: (n,)
                max_index = int(np.argmax(res_row))
                max_value = float(res_row[max_index])
                cols[r_idx] = max_index
            # for low-rank mode, no pis matrix return
            pis.append(None)

        
        
        spot_pair = [(spots[comb[0]][row], spots[comb[1]][col]) for row, col in zip(rows, cols)]
        spot_pair = set(spot_pair)

        G = nx.Graph()
        G.add_edges_from(spot_pair)
        node_names = np.array(G.nodes)
        anchors = list(node_names)

        adj = nx.adjacency_matrix(G)
        tmp = np.split(adj.indices, adj.indptr[1: -1])

        for anchor in range(len(anchors)):
            key = anchors[anchor]
            index = tmp[anchor]
            names = list(node_names[index])

            if key in spot_pairs[key_name]:
                spot_pairs[key_name][key].extend(x for x in names if x not in spot_pairs[key_name][key])
            else:
                spot_pairs[key_name][key] = names

    return spot_pairs, pis