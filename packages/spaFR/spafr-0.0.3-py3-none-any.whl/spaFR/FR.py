# from pyseat.SEAT import SEAT
# import seaborn as sns
# import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import copy



def check_tf(r_tf_graph, ggi_tf1, ok_receptor, lr_receptor):    
    '''
    Check if the receptor is a TF and if it has a TF target in the GGI network.
    Parameters
    ----------
    r_tf_graph : pd.DataFrame
        DESCRIPTION.
    ggi_tf1 : pd.DataFrame

    ok_receptor : list
        DESCRIPTION.
    lr_receptor : str   
        DESCRIPTION.

    Returns
    -------
    r_tf_graph : pd.DataFrame
        DESCRIPTION.
    ok_receptor : list
        DESCRIPTION.
    '''            
    ggi_res_yes = ggi_tf1[(ggi_tf1['src_tf'] == True) | (ggi_tf1['dest_tf'] == True)]
    # print(ggi_res_yes)
    if not ggi_res_yes.empty:
        tf_genes = set((ggi_res_yes[['src_tf', 'dest_tf']].values * ggi_res_yes[['src', 'dest']].values).flatten())
        tf_genes = [item for item in tf_genes if item != '']
        # print(lr_receptor, tf_genes)
        ok_receptor.append(lr_receptor)
        r_tf_graph.loc[lr_receptor,tf_genes] = 1
    return r_tf_graph, ok_receptor


def prior_get_ggi_res(receptor_name, ggi_tf, max_hop):
    '''
    Get the GGI network for the given receptors.
    Parameters
    ----------
    receptor_name : list
        List of receptors.
    ggi_tf : pd.DataFrame
        Knowledge of GGI network.
    max_hop : int
        Maximum hop to consider.

    Returns
    -------
    r_tf_graph : pd.DataFrame
        GGI network for the given receptors.
    ok_receptor : list
        List of receptors with TF target in the GGI network.
    '''
    r_tf_graph = pd.DataFrame()
    ok_receptor = []
    for lr_receptor in receptor_name:
        # print(lr_receptor)
        ggi_tf1 = ggi_tf[ggi_tf['src'] == lr_receptor].copy()
        r_tf_graph, ok_receptor = check_tf(r_tf_graph, ggi_tf1, ok_receptor, lr_receptor)
        n = 1
        # print('hop ',n)
        if not ggi_tf1.empty:
            ggi_tf1.loc[:,'hop'] = n
            while n < max_hop:
                n+=1 
                # print('hop', n)
                # ggi_res = pd.concat([ggi_res, ggi_tf1], ignore_index=True)
                ggi_tf1 = ggi_tf[ggi_tf['src'].isin(ggi_tf1['dest'])].drop_duplicates()
                r_tf_graph, ok_receptor = check_tf(r_tf_graph, ggi_tf1, ok_receptor, lr_receptor)
                if ggi_tf1.empty:
                    break
                ggi_tf1['hop'] = n + 2
    return r_tf_graph, set(ok_receptor)




def get_ggi_res(receptor_all, ggi_tf, exp, max_hop):
    '''
    receptor_all : list
        List of all receptors.
    ggi_tf : pd.DataFrame
        GGI and if genes are TF.
        Four columns: 
        src(str)/dest(str)/src_tf(bool)/dest_tf(bool)
    exp : pd.DataFrame
        Expression dataframe with genes as rownames and cells as colnames.
    max_hop : int
        Maximum number of hops to consider.
    Returns
    -------
    r_tf_graph : pd.DataFrame
        row of receptors, col of TF, 0/1 entries.
    ok_receptor : set   
        Set of receptors that have TFs within maximum hop.
    '''
    receptor_name = list(set(receptor_all).intersection(exp.index))
    # print(receptor_name)
    r_tf_graph = pd.DataFrame()
    ok_receptor = []
    for lr_receptor in receptor_name:
        # first hop, n=1
        n = 1
        ggi_tf1 = ggi_tf[ggi_tf['src'] == lr_receptor]
        ggi_tf1 = ggi_tf1[ggi_tf1['dest'].isin(exp.index)].drop_duplicates()
        # lr_receptor: IL1RAP
        # ggi_tf1: one hop gene of receptors.
        # src    dest  src_tf  dest_tf
        # IL1RAP   MYD88   False    False
        # IL1RAP  MAPK14   False    False
        # IL1RAP    MTOR   False    False
        r_tf_graph, ok_receptor = check_tf(r_tf_graph, ggi_tf1, ok_receptor, lr_receptor)

        if not ggi_tf1.empty:
            ggi_tf1.loc[:,'hop'] = n
            while n < max_hop:
                n+=1
                ggi_tf1 = ggi_tf[ggi_tf['src'].isin(ggi_tf1['dest'])]
                ggi_tf1 = ggi_tf1[ggi_tf1['dest'].isin(exp.index)].drop_duplicates()
                # ggi_tf1:
                # src      dest  src_tf  dest_tf
                # MAPK14    FOS   False     True
                # MAPK14  MAPKAPK2   False    False
                # MTOR     IGBP1   False    False
                r_tf_graph, ok_receptor = check_tf(r_tf_graph, ggi_tf1, ok_receptor, lr_receptor)
                # r_tf_graph:
                #         ELK4  JUND  RELA  JUNB  JUN  MEF2D  ATF4  FOS  FOSB  HIF1A  FOSL2
                # IL1RAP   1.0   1.0   1.0   1.0  1.0    1.0   1.0  1.0   1.0    1.0    1.0
                if ggi_tf1.empty:
                    break
        # break
    return r_tf_graph, set(ok_receptor)



def pairwise_jaccard_distance(X):
    """
    Compute the pairwise Jaccard distance between the rows of the input matrix X.
    
    Parameters:
    X (numpy.ndarray): The input matrix, where each row represents a data point.
    
    Returns:
    numpy.ndarray: The pairwise Jaccard distance matrix.
    """
    # Compute the dot product of the input matrix
    dot_product = np.dot(X, X.T)
    
    # Compute the sum of the squares of the input matrix
    sum_squares = np.sum(X ** 2, axis=1)
    
    # Compute the pairwise Jaccard distance
    jaccard_distance = 1 - dot_product / (sum_squares[:, None] + sum_squares - dot_product)
    
    # Replace NaN values with 1 (maximum Jaccard distance)
    jaccard_distance[np.isnan(jaccard_distance)] = 1
    
    return jaccard_distance


def cal_dist(ref_GCN, distance_method='JSD'):
    '''
    ref_GCN: pandas dataframe, row_index=Receptor, col_index=Ligands. col contains things I need to compare
    distance_method: str, default is 'JSD', can be 'SORENSEN', 'COR'
    output: pandas dataframe, row_index=Ligands, col_index=Ligands, value=distance
    '''
    if distance_method == 'JSD':
        # transform .T for JSD, not typo
        jaccard_distance_matrix = pairwise_jaccard_distance(ref_GCN.T.values)
        distance_df = pd.DataFrame(jaccard_distance_matrix, index=ref_GCN.columns, columns=ref_GCN.columns)
    return distance_df



# check common
def check_common(list1, list2):
    diff = list(set(list1).difference(set(list2)))
    if len(diff) == 0:
        return True, []
    else:
        return False, diff


def fr_df_without_log_minmax(profile, distance_df):
    '''
    distance_df: pandas dataframe, row_index=Ligands, col_index=Ligands, value=distance
    profile: pandas dataframe, row_index=cell, col_index=Ligands. Exp mat, col contains things I need to compare, same as distance_df
    output: pandas dataframe, row_index=Ligands, col_index=Ligands, value=FR. Graph weighted by exp mat.
    '''
    in_ref, diff = check_common(profile.columns, distance_df.columns)
    if not in_ref:
        print("These species cannot be found in GCN Reference: {}".format(diff))
        exit(0)

    d = copy.deepcopy(distance_df[list(profile.columns)].loc[list(profile.columns)])
    sp_list = list(d.columns)
    
    distance_matrix = d.values
    n_sp = len(sp_list)
    fr_matrix = np.zeros(shape=(n_sp, n_sp))
    max_fr = -np.inf
    min_fr = np.inf
    for i in range(n_sp):
        for j in range(i+1, n_sp):
            sp1 = sp_list[i]
            sp2 = sp_list[j]
            x = np.array(profile[sp1])
            y = np.array(profile[sp2])
            FR = np.dot(x, y)*(1-distance_matrix[i][j])
            fr_matrix[i][j] = FR
            # update max and min
            if FR > max_fr:
                max_fr = FR
            if FR < min_fr:
                min_fr = FR   
    fr_df = pd.DataFrame(fr_matrix, columns=sp_list, index=sp_list)
    return fr_df


def cal_nFR(profile, distance_df):
    '''
    profile: pandas dataframe, row_index=cell, col_index=Ligands. Exp mat, col contains things I need to compare, same as distance_df
    distance_df: pandas dataframe, row_index=Ligands, col_index=Ligands, value=distance
    output: 
        fr_df: pandas dataframe, row_index=Ligands, col_index=Ligands, value=nFR. Graph weighted by exp mat.
        fr: sum of nFR
        nFR: normalized FR
    '''
    gene_list = profile.columns
    simi = 1 - distance_df.loc[gene_list, gene_list].values
    np.fill_diagonal(simi, 0)
    
    a = profile[gene_list].values
    # a = a.T  # Transpose for easier broadcasting
    inter_matrix = np.dot(a.T, a)
    np.fill_diagonal(inter_matrix, 0)
    
    td = np.sum(inter_matrix) / 2
    if td == 0:
        # print("The total expression is 0, please check the input data")
        return None, 0, 0
    fr_df = inter_matrix * simi
    fr = np.sum(fr_df) / 2
    fr_df = pd.DataFrame(fr_df, index=gene_list, columns=gene_list)
    nFR = fr / td
    return fr_df, fr, nFR



def cal_TD(profile):
    '''
    profile: pandas dataframe, row_index=cell, col_index=Ligands. Exp mat, col contains things I need to compare, same as distance_df
    distance_df: pandas dataframe, row_index=Ligands, col_index=Ligands, value=distance
    output: 
        fr_df: pandas dataframe, row_index=Ligands, col_index=Ligands, value=nFR. Graph weighted by exp mat.
        fr: sum of nFR
        nFR: normalized FR
    '''
    gene_list = profile.columns    
    a = profile[gene_list].values
    # a = a.T  # Transpose for easier broadcasting
    inter_matrix = np.dot(a.T, a)
    np.fill_diagonal(inter_matrix, 0)
    
    td = np.sum(inter_matrix) / 2
    if td == 0:
        print("The total expression is 0, please check the input data")
        return 0
    return td



def filter_lr_pathway(exp, pathways, lrpairs, species):
    # Filter the lrpairs DataFrame to only include the specified species
    lrpair = lrpairs[lrpairs['species'] == species]
    # Filter the lrpair DataFrame to only include ligands and receptors that are present in the exp DataFrame
    lrpair = lrpair[(lrpair['ligand'].isin(exp.index)) & (lrpair['receptor'].isin(exp.index))]
    # Check if there are any ligand-receptor pairs found in exp
    if len(lrpair) == 0:
        raise ValueError("No ligand-receptor pairs found in exp!")
    # Filter the pathways DataFrame to only include the specified species
    pathways = pathways[pathways['species'] == species]
    # Filter the pathways DataFrame to only include src and dest values that are present in the exp DataFrame
    pathways = pathways[(pathways['src'].isin(exp.index)) & (pathways['dest'].isin(exp.index))]
    # Create the ggi_tf DataFrame from the filtered pathways DataFrame
    ggi_tf = pathways[['src', 'dest', 'src_tf', 'dest_tf']]
    ggi_tf = ggi_tf.drop_duplicates()
    # Filter the lrpair DataFrame to only include receptors that are present in the ggi_tf DataFrame
    lrpair = lrpair[lrpair['receptor'].isin(ggi_tf['src'])]
    # Filter the lrpair DataFrame to only include ligands that are present in the ggi_tf DataFrame
    return pathways, lrpair





def findCellKNN(coordinates, k=6):
    """
    Find k-nearest neighbors for each point in coordinates.
    
    Parameters:
    -----------
    coordinates : DataFrame
        Coordinates of points for which to find neighbors.
    ids : list, optional
        Identifiers for each point. If None, uses coordinates.index.
    k : int, default=6
        Number of nearest neighbors to find for each point.
        
    Returns:
    --------
    dict
        Dictionary mapping each point ID to a list of its k-nearest neighbor IDs.
    """
    from scipy.spatial import KDTree
    # check if coordinates is a DataFrame, if not, raise error
    if not isinstance(coordinates, pd.DataFrame):
        raise TypeError("Coordinates must be a DataFrame")

    # Convert coordinates to numpy array for KDTree if it's a DataFrame
    coord_values = np.array(coordinates) if not isinstance(coordinates, np.ndarray) else coordinates
    n_samples = len(coord_values)
    ids = coordinates.index.tolist()
    
    # Create a mapping from array indices to ids for lookups
    idx_to_id = {i: id_val for i, id_val in enumerate(ids)}
    
    kdtree = KDTree(coord_values)
    _, indices = kdtree.query(coord_values, k+1)
    knn_dict = {}
    
    for i, nearest_indices in enumerate(indices):
        point_id = idx_to_id[i]  # Use the id corresponding to this point
        # Get the ids of neighbors (excluding self)
        knn = [idx_to_id[idx] for idx in nearest_indices[1:].tolist() if idx < n_samples]
        if knn:  # Only add if there are neighbors
            knn_dict[point_id] = knn
            
    return knn_dict





############################################################################################################
# itol utils
def write_itol_color_tree(cut, my_outDir):
    with open(f'{my_outDir}/itol_{cut}_color_tree.txt', 'w') as file:
        print("TREE_COLORS", file=file)
        print("     SEPARATOR COMMA", file=file)
        print("     DATA", file=file)
    for gene in y.index:
        with open(f'{my_outDir}/itol_{cut}_color_tree.txt', 'a') as file:
            c = y.loc[gene][f'cut_{cut}_label']
            print(f'{gene},range,{c},{c}', file=file)

############################################################################################################
# plot
from typing import List
from scipy.cluster.hierarchy import to_tree, ClusterNode

def rgb_to_hex(rgb):
    # Ensure RGB values are in the range [0, 1]
    r, g, b = rgb
    # Convert to 0-255 range and round to nearest integer
    r = round(r * 255)
    g = round(g * 255)
    b = round(b * 255)
    # Convert to hex and format
    return f'#{r:02x}{g:02x}{b:02x}'


def _scipy_tree_to_newick_list(node: ClusterNode, newick: List[str], parentdist: float, leaf_names: List[str]) -> List[str]:
    """Construct Newick tree from SciPy hierarchical clustering ClusterNode

    This is a recursive function to help build a Newick output string from a scipy.cluster.hierarchy.to_tree input with
    user specified leaf node names.

    Notes:
        This function is meant to be used with `to_newick`

    Args:
        node (scipy.cluster.hierarchy.ClusterNode): Root node is output of scipy.cluster.hierarchy.to_tree from hierarchical clustering linkage matrix
        parentdist (float): Distance of parent node of `node`
        newick (list of string): Newick string output accumulator list which needs to be reversed and concatenated (i.e. `''.join(newick)`) for final output
        leaf_names (list of string): Leaf node names

    Returns:
        (list of string): Returns `newick` list of Newick output strings
    """
    if node.is_leaf():
        return newick + [f'{leaf_names[node.id]}:{parentdist - node.dist}']

    if len(newick) > 0:
        newick.append(f'):{parentdist - node.dist}')
    else:
        newick.append(');')
    newick = _scipy_tree_to_newick_list(node.get_left(), newick, node.dist, leaf_names)
    newick.append(',')
    newick = _scipy_tree_to_newick_list(node.get_right(), newick, node.dist, leaf_names)
    newick.append('(')
    return newick


def to_newick(tree: ClusterNode, leaf_names: List[str]) -> str:
    """Newick tree output string from SciPy hierarchical clustering tree

    Convert a SciPy ClusterNode tree to a Newick format string.
    Use scipy.cluster.hierarchy.to_tree on a hierarchical clustering linkage matrix to create the root ClusterNode for the `tree` input of this function.

    Args:
        tree (scipy.cluster.hierarchy.ClusterNode): Output of scipy.cluster.hierarchy.to_tree from hierarchical clustering linkage matrix
        leaf_names (list of string): Leaf node names

    Returns:
        (string): Newick output string
    """
    newick_list = _scipy_tree_to_newick_list(tree, [], tree.dist, leaf_names)
    return ''.join(newick_list[::-1])

############################################################################################################