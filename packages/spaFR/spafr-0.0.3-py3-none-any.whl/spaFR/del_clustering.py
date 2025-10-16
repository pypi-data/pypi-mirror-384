from typing import List
from scipy.cluster.hierarchy import to_tree

def rgb_to_hex(rgb):
    # Ensure RGB values are in the range [0, 1]
    r, g, b = rgb
    # Convert to 0-255 range and round to nearest integer
    r = round(r * 255)
    g = round(g * 255)
    b = round(b * 255)
    # Convert to hex and format
    return f'#{r:02x}{g:02x}{b:02x}'


def linkage_to_newick(Z, labels):
    """
    Input :  Z = linkage matrix, labels = leaf labels
    Output:  Newick formatted tree string
    Edit: 2018-June-28
    https://github.com/biocore/scikit-bio/issues/1579
    """
    tree = to_tree(Z, False) #scipy.sp_hierarchy.to_tree
    def build_newick(node, newick, parentdist, leaf_names):
        if node.is_leaf(): # This is for SciPy not for ete or skbio so `is_leaf` utility function does not apply
            return f"{leaf_names[node.id]}:{(parentdist - node.dist)/2}{newick}"
        else:
            if len(newick) > 0:
                newick = f")n{node.id}:{(parentdist - node.dist)/2}{newick}"
            else:
                newick = ");"
            newick = build_newick(node.get_left(), newick, node.dist, leaf_names)
            newick = build_newick(node.get_right(), f",{newick}", node.dist, leaf_names)
            newick = f"({newick}"
            return newick
    return build_newick(tree, "", tree.dist, labels)



def write_itol_color_tree(y, cut, my_outDir):
    with open(f'{my_outDir}/itol_{cut}_color_tree.txt', 'w') as file:
        print("TREE_COLORS", file=file)
        print("     SEPARATOR COMMA", file=file)
        print("     DATA", file=file)
    for gene in y.index:
        with open(f'{my_outDir}/itol_{cut}_color_tree.txt', 'a') as file:
            c = y.loc[gene][f'cut_{cut}_label']
            print(f'{gene},range,{c},{c}', file=file)