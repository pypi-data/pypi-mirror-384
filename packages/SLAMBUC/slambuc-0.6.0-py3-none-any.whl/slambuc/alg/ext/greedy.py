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
import heapq
import itertools
import math

import networkx as nx

from slambuc.alg import INFEASIBLE, T_BLOCK, T_RESULTS
from slambuc.alg.app import MEMORY, RATE, DATA
from slambuc.alg.util import ibacktrack_chain, recalculate_partitioning, par_subchain_latency, par_subtree_memory

# Naming convention for state-space DAG
START, END = 's', 't'


def get_bounded_greedy_block(tree: nx.DiGraph, root: int, M: int, N: int = 1, cp_end: int = None,
                             cp_cuts: set[int] = frozenset()) -> tuple[T_BLOCK, list[int]]:
    """
    Calculate a partition block based on the memory limit *M* by iteratively merging edges with the largest weights
    started from the given *root*.

    Filter out mandatory cuts of *cp_cuts* on the cpath form merging, while merges other cpath edges.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param M:       upper memory bound of the partition blocks in MB
    :param N:       available CPU core count
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param cp_cuts: barrier nodes of mandatory cuts on the critical path
    :return:        calculated partition block and the separated neighbouring nodes
    """
    # Init
    blk, blk_mem, cp_set, neighs = {root}, tree.nodes[root][MEMORY], set(ibacktrack_chain(tree, root, cp_end)), []

    def add_neighbours(node: int):
        """Add neighbours of the given *node* while keeping the order with a heap queue"""
        for sn, d in tree[node].items():
            if sn in cp_cuts:
                continue
            # Set edge weight to -inf for cpath nodes not included in precalculated cuts for designated must-merge
            # noinspection PyUnresolvedReferences
            heapq.heappush(neighs, (-1 * (d[RATE] * d[DATA] if sn not in cp_set else math.inf), sn))

    # Collect possible cut/merge edges based on the neighbouring nodes
    # Set edge weight to inf for cpath nodes not included in precalculated cuts for designated merging
    add_neighbours(root)
    while neighs:
        # Chose the largest data transfer edge for merging -> minimize cut weights
        _, v = heapq.heappop(neighs)
        # Stop extension of the current block due to memory limit
        if par_subtree_memory(tree, root, blk | {v}, N) > M:
            break
        blk.add(v)
        add_neighbours(v)
    # Collect root nodes of cut subtrees by the given block
    succ = [sn for n in blk for sn in tree[n] if sn not in blk]
    return sorted(blk), succ


def min_weight_greedy_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, N: int = 1,
                                   delay: int = 1, metrics: bool = True, **kwargs) -> T_RESULTS:
    """
    Calculates memory-bounded tree partitioning in a greedy manner without any latency limit.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param M:       upper memory bound of the partition blocks in MB
    :param N:       available CPU core count
    :param delay:   invocation delay between blocks
    :param metrics: return calculated sum cost and critical path latency
    :return:        tuple of derived partitioning, sum cost, and the latency on the critical path (root, cp_end)
    """
    partition, succ = [], collections.deque((root,))
    # Iteratively grow partition blocks starting from root and restarting it at the neighbouring nodes
    while succ:
        blk, next_succ = get_bounded_greedy_block(tree, succ.popleft(), M, N)
        succ.extend(next_succ)
        partition.append(blk)
    sum_cost, sum_lat = recalculate_partitioning(tree, partition, root, N, None, delay) if metrics else (None, None)
    return partition, sum_cost, sum_lat


########################################################################################################################


def get_feasible_cpath_split(tree: nx.DiGraph, root: int, cp_end: int, M: int, L: int, N: int = 1,
                             delay: int = 1) -> set[int] | None:
    """
    Calculate feasible splitting of the critical path that meets given memory *M* and latency *L* limits.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param M:       upper memory bound of the partition blocks in MB
    :param L:       latency limit defined on the critical path in ms
    :param N:       available CPU core count
    :param delay:   invocation delay between blocks
    :return:        set of barrier nodes of calculated critical path blocks
    """
    cpath = list(reversed(list(ibacktrack_chain(tree, root, cp_end))))
    cp_len, cp_set = len(cpath), set(cpath)
    # Check trivial single block subcase
    if par_subchain_latency(tree, root, cp_set, cp_set, N) <= L and par_subtree_memory(tree, root, cpath, N) <= M:
        return {root}
    cuts, best_feasible_lat, best_feasible_cut = set(), math.inf, None
    while True:
        best_lat, best_cut = math.inf, None
        # Iterate over possible cut
        for c in range(1, cp_len):
            if c in cuts:
                continue
            # Calculate relevant metrics
            blk_lats, blk_mems = zip(*((par_subchain_latency(tree, cpath[i], set(cpath[i:j]), cp_set, N),
                                        par_subtree_memory(tree, cpath[i], cpath[i:j], N))
                                       for i, j in itertools.pairwise([0, *sorted(cuts | {c}), cp_len])))
            # Store better case for the new cut *c* added to prior chosen *cuts*
            if (sum_lats := sum(blk_lats) + (len(blk_lats) - 1) * delay) < best_lat:
                best_lat, best_cut = sum_lats, c
            # Track feasible splitting regarding the block memories
            if all(map(lambda _m: _m <= M, blk_mems)) and sum_lats < best_feasible_lat:
                best_feasible_lat, best_feasible_cut = sum_lats, c
        # Return the first feasible cuts
        if best_feasible_lat <= L:
            cuts |= {best_feasible_cut}
            break
        if best_cut is None:
            # No latency-limited subcase can be achieved or all iterative cut subcases are examined
            return None
        else:
            # Greedily select the locally best cut (the largest reduce in lat possibly but not necessarily in opt cuts)
            cuts.add(best_cut)
    return {root, *(cpath[c] for c in cuts)}


def get_min_cpath_split(tree: nx.DiGraph, root: int, cp_end: int, M: int, L: int, N: int = 1,
                        delay: int = 1) -> set[int]:
    """
    Calculate min-latency splitting of the critical path that meets given memory *M* and latency *L* limits.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param M:       upper memory bound of the partition blocks in MB
    :param L:       latency limit defined on the critical path in ms
    :param N:       available CPU core count
    :param delay:   invocation delay between blocks
    :return:        set of barrier nodes of calculated critical path blocks
    """
    cpath = list(reversed(list(ibacktrack_chain(tree, root, cp_end))))
    cp_set = set(cpath)
    # Check trivial single block subcase
    if par_subchain_latency(tree, root, cp_set, cp_set, N) <= L and par_subtree_memory(tree, root, cpath, N) <= M:
        return {root}
    # Initiate data structure for DAG
    _cache = collections.defaultdict(list)
    _cache.update({START: [START], END: [END]})
    # noinspection PyUnresolvedReferences
    dag = nx.DiGraph(directed=True, **tree.graph)
    # noinspection PyTypeChecker
    for i, (prev, b) in enumerate(itertools.pairwise(itertools.chain([START], cpath))):
        b: int
        blk = set()
        for w in cpath[i:]:
            blk.add(w)
            # Skip infeasible subcase due to memory constraint
            if par_subtree_memory(tree, b, blk, N) > M:
                break
            blk_id = f"{b}|{w}"
            _cache[w].append(blk_id)
            blk_lat = par_subchain_latency(tree, b, blk, cp_set, N)
            # Add invocation delay for inter-block invocations
            if b != root and blk_lat > 0:
                blk_lat += delay
            # Add connection between related subcases
            for p in _cache[prev]:
                dag.add_edge(p, blk_id, weight=blk_lat)
    # Add connection for ending subcases
    for p in _cache[cpath[-1]]:
        dag.add_edge(p, END, weight=0)
    min_lat, sp = nx.single_source_dijkstra(dag, source=START, target=END)
    return {int(v.split('|')[0]) for v in sp[1:-1]} if min_lat <= L else None


def min_weight_partition_heuristic(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                                   N: int = 1, cp_end: int = None, delay: int = 1, metrics: bool = True) -> T_RESULTS:
    """
    Greedy heuristic algorithm to calculate partitioning of the given *tree* regarding the given memory *M* and
    latency *L* limits.
    It uses a greedy approach to calculate a low-cost critical path cut (might miss feasible solutions).
    It may conclude the partitioning problem infeasible despite there exist one with large costs.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param M:       upper memory bound of the partition blocks in MB
    :param L:       latency limit defined on the critical path in ms
    :param N:       available CPU core count
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:   invocation delay between blocks
    :param metrics: return calculated sum cost and critical path latency
    :return:        tuple of derived partitioning, sum cost, and the latency on the critical path (root, cp_end)
    """
    # Greedy search for feasible cut of the critical path
    cpath_cuts = get_feasible_cpath_split(tree, root, cp_end, M, L, N, delay)
    # No feasible cuts are found
    if cpath_cuts is None:
        return INFEASIBLE
    partition, succ = [], collections.deque((root,))
    # Iteratively grow partition blocks starting from root and restarting it at the neighbouring nodes
    while succ:
        v = succ.popleft()
        blk, next_succ = get_bounded_greedy_block(tree, v, M, N, cp_end, cpath_cuts)
        succ.extend(next_succ)
        partition.append(blk)
    sum_cost, sum_lat = recalculate_partitioning(tree, partition, root, N, cp_end, delay) if metrics else (None, None)
    return partition, sum_cost, sum_lat


def min_lat_partition_heuristic(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                                N: int = 1, cp_end: int = None, delay: int = 1, metrics: bool = True) -> T_RESULTS:
    """
    Greedy heuristic algorithm to calculate partitioning of the given *tree* regarding the given memory *M* and
    latency *L* limits.
    It uses Dijkstra's algorithm to calculate the critical path cut with the lowest latency (might be expensive).
    It always returns a latency-feasible solution if it exists.

    :param tree:    app graph annotated with node runtime(ms), edge rate and edge data unit size
    :param root:    root node of the tree
    :param M:       upper memory bound of the partition blocks in MB
    :param L:       latency limit defined on the critical path in ms
    :param N:       available CPU core count
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:   invocation delay between blocks
    :param metrics: return calculated sum cost and critical path latency
    :return:        tuple of derived partitioning, sum cost, and the latency on the critical path (root, cp_end)
    """
    # Greedy search for min-latency cut of the critical path
    cpath_cuts = get_min_cpath_split(tree, root, cp_end, M, L, N, delay)
    # No feasible cuts are found
    if cpath_cuts is None:
        return INFEASIBLE
    partition, succ = [], collections.deque((root,))
    # Iteratively grow partition blocks starting from root and restarting it at the neighbouring nodes
    while succ:
        v = succ.popleft()
        blk, next_succ = get_bounded_greedy_block(tree, v, M, N, cp_end, cpath_cuts)
        succ.extend(next_succ)
        partition.append(blk)
    sum_cost, sum_lat = recalculate_partitioning(tree, partition, root, N, cp_end, delay) if metrics else (None, None)
    return partition, sum_cost, sum_lat
