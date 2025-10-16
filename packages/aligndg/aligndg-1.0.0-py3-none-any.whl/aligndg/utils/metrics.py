import numpy as np
import sklearn
import sklearn.metrics.pairwise
import pandas as pd


def cal_layer_based_alignment_result(alignment, labels):  # pairwise slice alignment accuracy (shift is used for DLPFC)
    res = []
    l_dict = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6}
    cnt0 = 0
    cnt1 = 0
    cnt2 = 0
    cnt3 = 0
    cnt4 = 0
    cnt5 = 0
    cnt6 = 0
    for i, elem in enumerate(alignment):
        if labels[i] == '-1' or labels[elem.argmax() + alignment.shape[0]] == '-1':
            continue
        if l_dict[labels[i]] == l_dict[labels[elem.argmax() + alignment.shape[0]]]:
            cnt0 += 1
        if abs(l_dict[labels[i]] - l_dict[labels[elem.argmax() + alignment.shape[0]]]) == 1:
            cnt1 += 1
        if abs(l_dict[labels[i]] - l_dict[labels[elem.argmax() + alignment.shape[0]]]) == 2:
            cnt2 += 1
        if abs(l_dict[labels[i]] - l_dict[labels[elem.argmax() + alignment.shape[0]]]) == 3:
            cnt3 += 1
        if abs(l_dict[labels[i]] - l_dict[labels[elem.argmax() + alignment.shape[0]]]) == 4:
            cnt4 += 1
        if abs(l_dict[labels[i]] - l_dict[labels[elem.argmax() + alignment.shape[0]]]) == 5:
            cnt5 += 1
        if abs(l_dict[labels[i]] - l_dict[labels[elem.argmax() + alignment.shape[0]]]) == 6:
            cnt6 += 1
    print(alignment.shape[0])
    print(cnt0 / alignment.shape[0], cnt1 / alignment.shape[0], cnt2 / alignment.shape[0], cnt3 / alignment.shape[0],
          cnt4 / alignment.shape[0], cnt5 / alignment.shape[0], cnt6 / alignment.shape[0])
    res.extend(
        [cnt0 / alignment.shape[0], cnt1 / alignment.shape[0], cnt2 / alignment.shape[0], cnt3 / alignment.shape[0],
         cnt4 / alignment.shape[0], cnt5 / alignment.shape[0], cnt6 / alignment.shape[0]])
    return res


# spot-to-spot
def cal_alignment_acc(alignment, gt):
    gt = gt.to_numpy()
    result = np.zeros_like(alignment)
    # alignment: mapping matrix
    for i in range(alignment.shape[0]):
        # get one-to-one result mapping matrix, save as result (for balanced alignment)
        result[i, np.argmax(alignment[i])] = 1

    s = (result * gt).sum()
    acc = s / alignment.shape[1]
    return acc, result


def get_ratio(alignment, labels):
    matched_idx_list = []
    ad1_match_label = []
    ad2_match_label = [2] * alignment.shape[1]

    for i, elem in enumerate(alignment):

        if labels[i] == labels[elem.argmax() + alignment.shape[0]]:
            ad1_match_label.append(1)
            ad2_match_label[elem.argmax()] = 1
            matched_idx_list.append(elem.argmax())
        else:
            ad1_match_label.append(0)
            ad2_match_label[elem.argmax()] = 0

    return alignment.shape[0] / len(set(matched_idx_list)), ad1_match_label