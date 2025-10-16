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
import math

import networkx as nx

from slambuc.alg import INFEASIBLE, T_BARRS_GEN, T_RESULTS
from slambuc.alg.app import PLATFORM
from slambuc.alg.util import (isubtrees, ipowerset, ibacktrack_chain, ser_subtree_memory, ser_subtree_cost,
                              ser_subchain_latency)


def isubtrees_exhaustive(tree: nx.DiGraph, root: int, M: int) -> T_BARRS_GEN:
    """
    Calculate all combinations of edge cuts and returns only if it is feasible wrt. the memory limit *M*.

    Block metrics are calculated based on serialized execution platform model.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param M:       upper memory bound in MB
    :return:        generator of chain partitions
    """
    for cuts in ipowerset(tree.edges(range(1, len(tree)))):
        barrs = {root}.union(v for _, v in cuts)
        # Check whether the subtrees meet the memory requirement M
        feasible_subtrees = [b for b, nodes in isubtrees(tree, barrs) if ser_subtree_memory(tree, nodes) <= M]
        if len(feasible_subtrees) == len(barrs):
            yield feasible_subtrees


def greedy_ser_tree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                                 cp_end: int = None, delay: int = 1) -> list[T_RESULTS]:
    """
    Calculates minimal-cost partitioning of an app graph(tree) by iterating over all possible cuttings.

    Block metrics are calculated based on serialized execution platform model.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param M:       upper memory bound of the partition blocks (in MB)
    :param L:       latency limit defined on the critical path (in ms)
    :param cp_end:  tail node of the critical path in the form of subchain[root -> c_pend]
    :param delay:   invocation delay between blocks
    :return:        tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    cp_end = cp_end if cp_end is not None else max(n for n in tree if n != PLATFORM)
    best_res, best_cost = [INFEASIBLE], math.inf
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Iterates over all possible cuttings
    for barrs in isubtrees_exhaustive(tree, root, M):
        partition = []
        sum_cost = 0
        for b, nodes in isubtrees(tree, barrs):
            partition.append(nodes)
            sum_cost += ser_subtree_cost(tree, b, nodes)
        partition.sort()
        # Calculate blocks of critical path based on the partitioning
        restricted_blk_lats = [ser_subchain_latency(tree, blk[0], set(blk), cpath) for blk in partition]
        sum_lat = sum(restricted_blk_lats) + (sum(map(bool, restricted_blk_lats)) - 1) * delay
        if sum_lat <= L:
            # Store partitioning with the same best cost for comparison
            if sum_cost == best_cost:
                best_res.append((partition, sum_cost, sum_lat))
            # Initialize new best cost partitioning
            elif sum_cost < best_cost:
                best_res, best_cost = [(partition, sum_cost, sum_lat)], sum_cost
    return best_res
