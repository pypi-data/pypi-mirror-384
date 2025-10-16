# Copyright 2025 Janos Czentye
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import collections
import itertools
import math
import operator

import networkx as nx

from slambuc.alg import INFEASIBLE, T_RESULTS
from slambuc.alg.app import RATE, DATA, PLATFORM
from slambuc.alg.util import recreate_subtree_blocks, recalculate_partitioning


# noinspection PyUnresolvedReferences
def min_weight_subchain_split(tree: nx.DiGraph, root: int = 1) -> set[int]:
    """
    Return chain-based edge cuts with the minimal edge weight (amount of transferred data).

    The splitting marks the edge with the largest weight at each branching nodes to be a must-merge edge.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :return:        set of barrier nodes
    """
    return {root}.union(*(set(tree.successors(v)) -
                          {max(tree.successors(v), key=lambda s: tree[v][s][RATE] * tree[v][s][DATA])}
                          for v in tree if v is not PLATFORM and len(tree.succ[v]) > 1))


def min_weight_chain_decomposition(tree: nx.DiGraph, root: int = 1, N: int = 1, cp_end: int = None,
                                   delay: int = 1, metrics: bool = True, **kwargs) -> T_RESULTS:
    """
    Minimal edge-weight chain-based tree partitioning (O(n)) without memory and latency constraints.

    Although latency is not considered on the critical path the algorithm reports it with the sum cost.

    :param tree:    app graph annotated with node runtime(ms) and edge rate
    :param root:    root node of the tree
    :param N:       available CPU core count
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:   invocation delay between blocks
    :param metrics: return calculated sum cost and critical path latency
    :return:        tuple of derived partitioning, sum cost, and the latency on the critical path (root, cp_end)
    """
    partition = recreate_subtree_blocks(tree, barr=min_weight_subchain_split(tree, root))
    sum_cost, sum_lat = recalculate_partitioning(tree, partition, root, N, cp_end, delay) if metrics else (None,) * 2
    return partition, sum_cost, sum_lat


########################################################################################################################


def min_weight_ksplit(tree: nx.DiGraph, root: int, k: int) -> set[int]:
    """
    Minimal data-transfer tree clustering into *k* clusters with k-1 cuts without memory and latency constraints.

    The clustering algorithm is based on the maximum split clustering algorithm(O(n^3)) which ranks the edges (paths)
    based on the amount of transferred data.

    Details in: M. Maravalle et al.: “Clustering on trees,” Computational Statistics & Data Analysis, vol. 24, no. 2,
    pp. 217–234, Apr. 1997, doi: 10.1016/S0167-9473(96)00062-X.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param k:       number of clusters
    :return:        set of barrier nodes
    """
    dist_tree = nx.to_undirected(tree)
    # Define distance of two nodes as the reciprocal of the sum transferred data between the nodes
    D = {(u, v): sum(1 / (attr[RATE] * attr[DATA]) if attr[RATE] and attr[DATA] else 0
                     for i, j, attr in tree.edges(next(nx.all_simple_paths(dist_tree, u, v)), data=True))
         for u, v in itertools.combinations(filter(lambda n: n is not PLATFORM, tree), 2)}
    edges, rank = set(tree.edges(filter(lambda n: n is not PLATFORM, tree))), 1
    labeled = collections.deque(maxlen=k - 1)
    # Iterate paths from the min distant element
    for (i, j), _ in sorted(list(D.items()), key=operator.itemgetter(1)):
        path_edges = set(e for e in tree.edges(next(nx.all_simple_paths(dist_tree, i, j))))
        # If there is unlabelled edge on the given path
        if unlabeled := path_edges & edges:
            labeled.extend((rank, b) for _, b in unlabeled)
            edges -= unlabeled
            # If all edges are labeled -> stop
            if not edges:
                break
            rank += 1
    return {root}.union(b for _, b in labeled)


def min_weight_ksplit_clustering(tree: nx.DiGraph, root: int = 1, k: int = None, N: int = 1, cp_end: int = None,
                                 delay: int = 1, metrics: bool = True, **kwargs) -> T_RESULTS:
    """
    Minimal data-transfer tree clustering into *k* clusters (with k-1 cuts) without memory and latency constraints.

    Although latency is not considered on the critical path the algorithm reports it along with the sum cost.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param k:       number of clusters
    :param N:       available CPU core count
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:   invocation delay between blocks
    :param metrics: return calculated sum cost and critical path latency
    :return:        tuple of derived partitioning, sum cost, and the latency on the critical path (root, cp_end)
    """
    k = k if k is not None else math.ceil(math.sqrt(len(tree) - 1))
    partition = recreate_subtree_blocks(tree, barr=min_weight_ksplit(tree, root, k))
    sum_cost, sum_lat = recalculate_partitioning(tree, partition, root, N, cp_end, delay) if metrics else (None, None)
    return partition, sum_cost, sum_lat


def min_weight_tree_clustering(tree: nx.DiGraph, root: int = 1, L: int = math.inf, N: int = 1, cp_end: int = None,
                               delay: int = 1, metrics: bool = True, **kwargs) -> T_RESULTS:
    """
    Minimal data-transfer tree clustering without memory constraints.

    Iteratively calculates *k-1* different ksplit clustering in reverse order until an L-feasible solution is found.

    Although latency is not considered on the critical path the algorithm reports it with the sum cost.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param L:       latency limit defined on the critical path in ms
    :param N:       available CPU core count
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:   invocation delay between blocks
    :param metrics: return calculated sum cost and critical path latency
    :return:        tuple of derived partitioning, sum cost, and the latency on the critical path (root, cp_end)
    """
    best_result = INFEASIBLE
    for k in reversed(range(1, len(tree) + 1)):
        partition = recreate_subtree_blocks(tree, barr=min_weight_ksplit(tree, root, k))
        cost, lat = recalculate_partitioning(tree, partition, root, N, cp_end, delay) if metrics else (math.inf,) * 2
        if cost <= best_result[1] and (lat is None or lat <= L):
            best_result = partition, cost, lat
    return best_result
