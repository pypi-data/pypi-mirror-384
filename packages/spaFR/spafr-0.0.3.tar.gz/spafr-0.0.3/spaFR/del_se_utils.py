import copy 
import numpy as np
# calculate the SE
def se_sum(se_dict, children_list, node):
    value = 0
    for c in children_list:
        if c in se_dict.keys():
            value += se_dict[c]
    if node in children_list:
        return value
    value += se_dict[node]
    return value

def node_se(edge_df, sp_list, parent_list):
    degree = edge_df.sum()
    #print(degree)
    v_g = degree.sum()
    v_parent = degree[parent_list].sum()
    v_node = degree[sp_list].sum()
    v_outside = v_node - edge_df.loc[sp_list, sp_list].sum().sum()
    if v_parent*v_node == 0:
        return 0, v_outside
    value = - v_outside/v_g*np.log2(v_node/v_parent)
    return value, v_outside


def all_node_se(edge_df, parent_dict, node_leaves):
    se_dict = {'root': 0}
    outside_dict = {'root': 0}
    valid_leaves = set(edge_df.index)
    for l in valid_leaves:
        sp_list = [l]
        parent = parent_dict[l]
        if parent not in parent_dict.keys():
            parent_list = list(valid_leaves)
        else:
            parent_list = list(set(node_leaves[parent]).intersection(valid_leaves))
        value, out_v = node_se(edge_df, sp_list, parent_list)
        se_dict[l] = value
        outside_dict[l] = out_v

    for node, sp_list in node_leaves.items():
        sp_list = list(set(sp_list).intersection(valid_leaves))
        if node not in parent_dict.keys():
            continue
        parent = parent_dict[node]
        if parent not in parent_dict:
            parent_list = list(valid_leaves)
        else:
            parent_list = list(set(node_leaves[parent]).intersection(valid_leaves))
        value, out_v = node_se(edge_df, sp_list, parent_list)
        se_dict[node] = value
        outside_dict[node] = out_v
    return copy.deepcopy(se_dict), copy.deepcopy(outside_dict)


def subtree_se(edge_df, parent_dict, node_leaves, child_dict):
    '''
    Calculate the SE for each node in the tree
    :param edge_df: similarity dataframe 1- gene_dist
    :param parent_dict: parent node dictionary {node:parent}
    :param node_leaves: node leaves dictionary {node:[leaves]}
    :param child_dict: child node dictionary {node:[direct children]}
    '''
    se_dict, _ = all_node_se(edge_df, parent_dict, node_leaves)
    result = {}
    for node in se_dict.keys():
        children_list = child_dict[node]
        value = se_sum(se_dict, children_list, node)
        result[node] = value
    return copy.deepcopy(result)