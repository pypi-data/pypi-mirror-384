import re
import copy

# covert newick to json tree structure
def parse(newick):
    tokens = re.finditer(r"([^:;,()\s]*)(?:\s*:\s*([\d.]+)\s*)?([,);])|(\S)", newick+";")

    def recurse(nextid = 0, parentid = -1): # one node
        thisid = nextid;
        children = []

        name, length, delim, ch = next(tokens).groups(0)
        if ch == "(":
            while ch in "(,":
                node, ch, nextid = recurse(nextid+1, thisid)
                children.append(node)
            name, length, delim, ch = next(tokens).groups(0)
        node = {"id": thisid, "name": name, "length": float(length) if length else None, 
                "parentid": parentid, "children": children, "taken": False}
        return copy.deepcopy(node), delim, nextid

    return recurse()[0]


# compute the leaves and level of each node, and clade deepth
def recu_compute(node, level=0, largest = {'largest': 0}):
    node['leaves'] = []
    node['level'] = level
    if len(node['children']) == 0:
        node['clade_depth'] = 0
        if level > largest['largest']:
            largest['largest'] = level
        node['leaves'] = [node['name']]
        return [node['name']], largest
    else:
        largest_children_depth = 0
        for n in node['children']:
            plus_leaves, largest = recu_compute(n, level+1, largest)
            node['leaves'] += plus_leaves
            if n['clade_depth'] > largest_children_depth:
                largest_children_depth = n['clade_depth']
        node['clade_depth'] = largest_children_depth + 1
        return node['leaves'], largest
    


def make_layer_dict(nlayer):

    result_dict = {}
    for i in range(1, nlayer):
        
        result_dict[i] = {}
    return result_dict

# find layer node:leaves
def recu_layer(node, result_dict):
    depth = node['clade_depth']
    if depth in result_dict.keys():
        result_dict[depth][node['name']] = node['leaves']
    for child in node['children']:
        recu_layer(child, result_dict)


def parents(node, parent_dict):
    for child in node['children']:
        node_name = child['name']
        parent_dict[node_name] = node['name']
        parents(child, parent_dict)

############################################################################################################
def to_layer_leaves(result_dict, nlayer):
    for i in range(1, nlayer-1):
        top_id = i + 1
        top_large_list = to_large_list(result_dict[top_id])
        for k, v in result_dict[i].items():
            if not has_common(v, top_large_list):
                # print("add node : {} from level {} to level {}".format(k, i, top_id))
                result_dict[top_id][k] = v

# check if belongs to upper level
def has_common(lower, upper):
    if len(list(set(upper).intersection(set(lower))))>0:
        return True
    else:
        return False

# check the leaves in the level
def to_large_list(level2_json):
    large_list = []
    for k, v in level2_json.items():
        large_list += v
    return large_list

############################################################################################################