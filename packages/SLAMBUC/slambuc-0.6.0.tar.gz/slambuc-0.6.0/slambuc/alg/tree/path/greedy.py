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
import itertools
import math
from collections.abc import Generator

import networkx as nx

from slambuc.alg import INFEASIBLE, T_RESULTS
from slambuc.alg.app import *
from slambuc.alg.util import (isubtrees, ibacktrack_chain, ipowerset, path_blocks, chain_cost, chain_latency,
                              chain_cpu, chain_memory_opt)


def ichains_exhaustive(tree: nx.DiGraph, root: int, M: int, N: int) -> Generator[set[int]]:
    """
    Calculate all combinations of edge cuts and returns only if it is feasible wrt. the chain connectivity, M, and N.

    Calculation is improved compared to brute force to only start calculating cuts from c_min.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param M:       upper memory bound in MB
    :param N:       upper CPU core bound
    :return:        generator of chain partitions
    """
    c_min = math.ceil(sum(nx.get_node_attributes(tree, MEMORY).values()) / M) - 1
    for cuts in ipowerset(tree.edges(range(1, len(tree))), start=c_min):
        barr = {root}.union(v for _, v in cuts)
        # Check whether the subtrees are chains and meet the memory requirement M and N
        for b, nodes in isubtrees(tree, barr):
            # noinspection PyUnresolvedReferences
            if max(d for _, d in tree.subgraph(nodes).out_degree) > 1:
                break
            memory, rate = zip(*[(tree.nodes[v][MEMORY], tree[u][v][RATE]) for u, v in
                                 itertools.pairwise([next(tree.predecessors(b)), *nodes])])
            if chain_memory_opt(memory, rate, 0, len(nodes) - 1) > M or chain_cpu(rate, 0, len(nodes) - 1) > N:
                break
        else:
            yield barr


def ifeasible_chains(tree: nx.DiGraph, root: int, M: int, N: int) -> Generator[set[int]]:
    """
    Calculate only feasible chain partitions and returns the one which meets the limits M and N.

    Calculation is improved compared to brute force to only calculate chain partitions based on the branching nodes.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param M:       upper memory bound in MB
    :param N:       upper CPU core bound
    :return:        generator of chain partitions
    """
    branch_edges = [itertools.chain(itertools.combinations(tree.succ[b], len(tree.succ[b]) - 1),
                                    [tuple(tree.successors(b))]) for b in (v for v, d in tree.out_degree if d > 1)]
    single_edges = ipowerset([v for v in tree.nodes
                              if v is not PLATFORM and tree.degree(next(tree.predecessors(v))) == 2])
    for chain_cuts in itertools.product(*branch_edges, single_edges):
        barr = {root}.union(itertools.chain.from_iterable(chain_cuts))
        # Check whether the subtrees are chains and meet the memory requirement M and N
        for b, nodes in isubtrees(tree, barr):
            memory, rate = zip(*[(tree.nodes[v][MEMORY], tree[u][v][RATE]) for u, v in
                                 itertools.pairwise([next(tree.predecessors(b)), *nodes])])
            if chain_memory_opt(memory, rate, 0, len(nodes) - 1) > M or chain_cpu(rate, 0, len(nodes) - 1) > N:
                break
        else:
            yield barr


def greedy_tree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, N: int = math.inf,
                             L: int = math.inf, cp_end: int = None, delay: int = 1, unit: int = 1,
                             ichains=ifeasible_chains, only_cuts: bool = False) -> list[T_RESULTS]:
    """
    Calculates minimal-cost partitioning of an app graph(tree) by iterating over all possible cuttings.

    :param tree:        app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:        root node of the graph
    :param M:           upper memory bound of the partition blocks (in MB)
    :param N:           upper CPU core bound of the partition blocks
    :param L:           latency limit defined on the critical path (in ms)
    :param cp_end:      tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:       invocation delay between blocks
    :param unit:        rounding unit for the cost calculation (default: 100 ms)
    :param ichains:     generator of chain partitions
    :param only_cuts:   return the number of cuts instead of the calculated latency
    :return:            tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    best_res, best_cost = [INFEASIBLE], math.inf
    # Iterates over all possible cuttings
    for barr in ichains(tree, root, M, N):
        partition = []
        sum_cost = 0
        for b, nodes in isubtrees(tree, barr):
            partition.append(nodes)
            runtime, rate = zip(*[(tree.nodes[v][RUNTIME], tree[u][v][RATE])
                                  for u, v in itertools.pairwise([next(tree.predecessors(b)), *partition[-1]])])
            sum_cost += chain_cost(runtime, rate, 0, len(partition[-1]) - 1, unit)
        # Calculate blocks of the critical path based on the partitioning
        cp_block = path_blocks(partition, reversed(list(ibacktrack_chain(tree, root, cp_end))))
        sum_lat = sum(chain_latency([tree.nodes[v][RUNTIME] for v in blk], 0, len(blk) - 1, delay, 0, len(blk) - 1)
                      for blk in cp_block) + (len(cp_block) - 1) * delay
        partition.sort()
        if sum_lat <= L:
            if only_cuts:
                sum_lat = len(cp_block) - 1
            # Store partitioning with the same best cost for comparison
            if sum_cost == best_cost:
                best_res.append((partition, sum_cost, sum_lat))
            # Initialize new best cost partitioning
            elif sum_cost < best_cost:
                best_res, best_cost = [(partition, sum_cost, sum_lat)], sum_cost
    return best_res
