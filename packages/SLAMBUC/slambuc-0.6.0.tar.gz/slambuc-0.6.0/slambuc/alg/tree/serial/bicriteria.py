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
import typing

import networkx as nx

from slambuc.alg import INFEASIBLE, T_RESULTS
from slambuc.alg.app import *
from slambuc.alg.app.common import WEIGHT
from slambuc.alg.util import (ipostorder_dfs, ileft_right_dfs, ibacktrack_chain, recreate_subtree_blocks,
                              recalculate_ser_partitioning, ipostorder_edges, verify_limits)

# Constants for attribute index
OPT = 0


class WeightedSubBTreePart(typing.NamedTuple):
    """Store subtree partitioning attributes for a given edge-weighted subcase."""
    weight: int = 0  # Cumulative weights of covered edges in the subtree partitioning
    barr: set[int] = set()  # Barrier/heading nodes of the given subtree partitioning

    def __repr__(self):
        return repr(tuple(self))


def biheuristic_btree_partitioning(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                                   M: int = math.inf, L: int = math.inf, cp_end: int = None, delay: int = 1,
                                   Epsilon: float = 0.0, Lambda: float = 0.0, bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes, while
    applying the bottom-up tree traversal approach.

    Cost approximation ratio *Epsilon* controls the maximum deviation from the cost-optimal partitioning
    (Epsilon=0.0 enforces the algorithm to calculate exact solution) in exchange for reduces subcase calculations.

    Latency approximation ratio (*Lambda*) controls the maximum deviation with respect to the latency limit $L$
    (Lambda=0.0 enforces no rounding) in exchange for reduces subcase calculations.
    
    Block metrics are calculated based on serialized execution platform model.

    Provide suboptimal partitioning due to the simplified and inaccurate latency rounding.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cp_end:          tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:           invocation delay between blocks
    :param Epsilon:         weight factor for state space trimming (0 <= Eps < 1, Eps = 0 falls back to exact calc.)
    :param Lambda:          latency factor for state space trimming (0 <= Lambda, Lambda = 0 falls back to exact calc.)
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    # Set of critical path's nodes
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    # Init empty data structure for optimal results of subtrees T_v
    DP = {_v: collections.defaultdict(dict) for _v in tree if _v is not PLATFORM}
    # Number of nodes
    t_size = len(DP)
    # Iterate nodes in a bottom-up traversal order
    for p, v in ipostorder_dfs(tree, root):
        # SINGLETON: calculate the default subcase of singleton partition of node v
        r_v, d_v, t_v, m_v = tree[p][v][RATE], tree[p][v][DATA], tree.nodes[v][RUNTIME], tree.nodes[v][MEMORY]
        # Only add fetching overhead for root node and omit caching to ensure lat monotonicity of upward merging
        lat = d_v + t_v if v == root else t_v if v in cpath else 0
        # For singleton blocks weight is 0 by default
        DP[v][lat, lat][m_v] = WeightedSubBTreePart(0, {v})
        w_max = 0
        # Bottom-up propagation for considering v's descendant subcases in sequential order (v is not leaf)
        # -->   p   ---->   v   ----[i.]---->   b
        for b in tree.successors(v):
            # Init empty data structure of subcase T[v,b]
            _cache = collections.defaultdict(dict)
            r_b, d_b, t_b = tree[v][b][RATE], tree[v][b][DATA], tree.nodes[b][RUNTIME]
            # Calculate possible latency/memory combinations while dropping subcases of v and b from DP
            for ((lat_v, blk_lat_v), DPv), ((lat_b, blk_lat_b), DPb) in itertools.product(DP[v].items(),
                                                                                          DP.pop(b).items()):
                for (mem_v, sub_v), (mem_b, sub_b) in itertools.product(DPv.items(), DPb.items()):
                    # Latency calculation in case v -> b edge is in cpath
                    if b in cpath:
                        # CUT: v -> b edge is marked as a cut (opt subcases of b have the dedicated memory value 0)
                        if mem_b == OPT:
                            # Add caching overhead of inter-block call
                            top_blk_lat = blk_lat_v + math.ceil(r_b / r_v) * d_b
                            # Add invocation delay and fetch overhead of inter-block call
                            if (lat := top_blk_lat + delay + d_b + lat_b) > L:
                                # Infeasible subcase due to exceeded latency constraint
                                continue
                        # MERGE: v -> b edge is marked as a merge
                        else:
                            # Top block's latency comes for only the single cp node v, hence n_v = 1
                            top_blk_lat = blk_lat_v + math.ceil(r_b / r_v) * blk_lat_b
                            # Calculate new latency based on the recalculated top block's latency
                            if (lat := lat_b - blk_lat_b + top_blk_lat) > L:
                                # Infeasible subcase due to exceeded latency constraint
                                continue
                    else:
                        # Top block's attributes remain the same, either v in cpath or not
                        top_blk_lat, lat = blk_lat_v, lat_v
                    # CUT: v -> b edge is marked as a cut
                    if mem_b == OPT:
                        # Sub-partitions are just concatenated
                        mem, weight, barr = mem_v, sub_v.weight + sub_b.weight, sub_v.barr | sub_b.barr
                    # MERGE: v -> b edge is marked as a merge
                    elif (mem := mem_v + mem_b) > M:
                        # Infeasible subcase due to exceeded memory constraint
                        continue
                    else:
                        # Top blocks of the two sub-partitions are merged together with root node v
                        weight, barr = sub_v.weight + sub_b.weight + r_b * d_b, sub_v.barr | sub_b.barr - {b}
                    # Store the max-weight subcase
                    sub_lats = lat, top_blk_lat
                    # Check whether the current subcase is a better sub-solution for state (v, sub_lats, mem)
                    if mem not in _cache[sub_lats] or weight > _cache[sub_lats][mem].weight:
                        if bidirectional:
                            # Eliminate prior subcases that are dominated by the new subcase
                            for l, m in tuple((_l, _m) for _l in _cache if _l[0] >= lat and _l[1] >= top_blk_lat
                                              for _m in _cache[_l] if _m >= mem and _cache[_l][_m].weight <= weight):
                                if len(_cache[l]) > 1:
                                    del _cache[l][m]
                                else:
                                    del _cache[l]
                        # Add superior subcase
                        _cache[sub_lats][mem] = WeightedSubBTreePart(weight, barr)
                        w_max = max(w_max, weight)
            # Store max subcases as C(v,i-1) for the next iteration of the propagation process
            DP[v] = _cache
        # Trim state space based on given bi-criteria parameters
        if len(tree.succ[v]) > 0:
            # Calculate trim interval sizes
            l_max = L if L < math.inf else max((_l[0] for _l in DP[v]), default=0)
            l_scale = ((Lambda * l_max) / t_size) if Lambda > 0.0 and l_max > 0 else 1.0
            w_scale = ((Epsilon * w_max) / t_size) if Epsilon > 0.0 and w_max > 0 else 1.0
            # print(f"w int size: {w_scale}, l int size: {l_scale}")
            _kept_subcases = {}
            # Search for dominated subcases
            for (lat, top_blk_lat), dpv in tuple(DP[v].items()):
                for mem, subcase in tuple(dpv.items()):
                    # Track states as a tuple of interval sequence numbers
                    if (lw_state := (math.ceil(lat / l_scale),
                                     math.ceil(top_blk_lat / l_scale),
                                     math.ceil(subcase.weight / w_scale))) in _kept_subcases:
                        kept_lats, kept_mem = _kept_subcases[lw_state]
                        # Evaluate dominance relation between visited and current subcase
                        if kept_mem > mem:
                            # Drop dominated subcase
                            del DP[v][kept_lats][kept_mem]
                            if not len(DP[v][kept_lats]):
                                del DP[v][kept_lats]
                        else:
                            continue
                    # Add subcase as kept state
                    _kept_subcases[lw_state] = (lat, top_blk_lat), mem
        # Store the weight-opt subcases wrt. latency for node v encoded with memory value 0
        for sub_v in DP[v].values():
            sub_v[OPT] = max(sub_v.values(), key=operator.itemgetter(0))
    # Subcases under the root node contain the feasible partitioning
    if opt_lats := max(DP[root], key=lambda _l: DP[root][_l][OPT].weight, default=None):
        opt = DP[root][opt_lats][OPT]
        return recreate_subtree_blocks(tree, opt.barr), opt.weight, opt_lats[0]
    else:
        # No feasible solution
        return INFEASIBLE


def biheuristic_tree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                                  cp_end: int = None, delay: int = 1, Epsilon: float = 0.0, Lambda: float = 0.0,
                                  bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes, while
    applying the bottom-up tree traversal approach.

    Provide suboptimal partitioning due to the simplified and inaccurate latency rounding.

    Recalculates original sum cost and latency metrics.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cp_end:          tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:           invocation delay between blocks
    :param Epsilon:         weight factor for state space trimming (0 <= Eps < 1, Eps = 0 falls back to exact calc.)
    :param Lambda:          latency factor for state space trimming (0 <= Lambda, Lambda = 0 falls back to exact calc.)
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    partition, *_ = biheuristic_btree_partitioning(tree, root, M, L, cp_end, delay, Epsilon, Lambda, bidirectional)
    if partition:
        # noinspection PyTypeChecker
        return partition, *recalculate_ser_partitioning(tree, partition, root, cp_end, delay)
    else:
        # No feasible solution
        return INFEASIBLE


########################################################################################################################


class WeightedSubLTreePart(typing.NamedTuple):
    """Store subtree partitioning attributes for a given edge-weighted subcase."""
    weight: int = 0  # Cumulative weights of covered edges in the subtree partitioning
    top_lat: int = 0  # Calculated latency for the topmost partition block
    mul: int = 1  # Last serialization multiplier of the top/first block of the subtree partitioning
    barr: set[int] = set()  # Barrier/heading nodes of the given subtree partitioning

    def __repr__(self):
        return repr(tuple(self))


def bifptas_ltree_partitioning(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                               M: int = math.inf, L: int = math.inf, cp_end: int = None, delay: int = 1,
                               Epsilon: float = 0.0, Lambda: float = 0.0, bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes, while
    applying the left-right tree traversal approach.

    Cost approximation ratio *Epsilon* controls the maximum deviation from the cost-optimal partitioning
    (Epsilon=0.0 enforces the algorithm to calculate exact solution) in exchange for reduces subcase calculations.

    Latency violation ratio (*Lambda*) controls the maximum violating deviation from the latency limit $L$
    (Lambda=0.0 enforces no violation)  in exchange for reduces subcase calculations.

    Block metrics are calculated based on serialized execution platform model.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cp_end:          tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:           invocation delay between blocks
    :param Epsilon:         weight factor for state space trimming (0 <= Eps < 1, Eps = 0 falls back to exact calc.)
    :param Lambda:          latency factor for state space trimming (0 <= Lambda, Lambda = 0 falls back to exact calc.)
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    # Set of critical path's nodes
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    # Init empty data structure for optimal results of subtrees
    TDP = {n: {} for n in tree if n is not PLATFORM}
    t_size = len(TDP)
    # Calculate latency rounding interval and scaled latency upper bound
    if Lambda > 0.0 and L < math.inf:
        l_scale = ((Lambda * L) / t_size)
        L_hat = math.floor(L / l_scale) + t_size
    else:
        l_scale, L_hat = 1.0, L
    # Process subtrees of T in a bottom-up traversal order
    for p, n in ipostorder_dfs(tree, root):
        # Init empty data structure for optimal subcases T_n[v,b]
        DP = collections.defaultdict(lambda: collections.defaultdict(dict))
        # Traverse subtree T_n in a left-right traversal
        #       |--(j-1.)--> [v_p]   |--(i-1.)--> [b_p]                                 | left side
        # -->  [u]  ----(j.)---->  [v]  ----(i.)---->  [b]  ----(max_k.)----> [b_k]     | right side
        w_max = 0
        for e_uvp, b_p, e_vb in ileft_right_dfs(tree, n):
            v, b = e_vb
            # Merge edge u -> v
            if b == 0:
                # SINGLETON: C[n,0] - calculate the default subcase of singleton partition of root node n
                if v == n:
                    r_n, d_n, t_n = tree[p][n][RATE], tree[p][n][DATA], tree.nodes[n][RUNTIME]
                    if n in cpath:
                        nc = next(filter(lambda c: c in cpath, tree.successors(n)), None)
                        lat_n = d_n + t_n + (math.ceil(tree[n][nc][RATE] / r_n) * tree[n][nc][DATA] if nc else 0)
                    else:
                        lat_n = 0
                    # Rounding latency value for singleton block
                    lat = math.ceil(lat_n / l_scale)
                    # For singleton blocks weight is 0 by default
                    DP[e_vb][lat][tree.nodes[n][MEMORY]] = WeightedSubLTreePart(0, lat_n, 1, {n})
                # MERGE: C[v,0] - subcase of merging single node v into the n-rooted block containing node u
                else:
                    u, v_p = e_uvp
                    r_v, d_v, t_v = tree[u][v][RATE], tree[u][v][DATA], tree.nodes[v][RUNTIME]
                    # v_p = 0 => no prior sibling node, C[v,0] = C[u,j-1] + delta(u,v)
                    for lat_u in DP[e_uvp]:
                        for mem_u in DP[e_uvp][lat_u]:
                            if (mem := mem_u + tree.nodes[v][MEMORY]) > M:
                                # Infeasible subcase due to exceeded memory constraint
                                continue
                            sub_u = DP[e_uvp][lat_u][mem_u]
                            # v in cpath => u in cpath
                            if v in cpath:
                                n_v = math.ceil(r_v / tree[next(tree.predecessors(u))][u][RATE]) * sub_u.mul
                                vc = next(filter(lambda c: c in cpath, tree.successors(v)), None)
                                o_v = math.ceil(tree[v][vc][RATE] / r_v) * tree[v][vc][DATA] if vc else 0
                                # Calculate latency of merged node v and add rounded value to top block
                                top_lat = sub_u.top_lat + n_v * (t_v - d_v + o_v)
                                if (lat := math.ceil(top_lat / l_scale)) > L_hat:
                                    # Infeasible subcase due to exceeded latency constraint
                                    continue
                            else:
                                # Top block's latency attributes remains the same
                                lat, top_lat, n_v = lat_u, sub_u.top_lat, sub_u.mul
                            # Store subcase with weight increased by the merged/covered edge weight
                            weight = sub_u.weight + r_v * d_v
                            DP[e_vb][lat][mem] = WeightedSubLTreePart(weight, top_lat, n_v, sub_u.barr)
            # CUT: C[v,b]
            else:
                # b_k <- C[v_i, d(v_i)]
                b_k = collections.deque(tree.successors(b), 1).pop() if len(tree.succ[b]) else 0
                # Previously merged edge: v -> b  =>  [root ... -> u -> v -> b ...]   |   [b]  --(max_k.)--> [b_w]
                DP[e_vb] = DP[b, b_k]
                # Cut edge: v -> b  |  [root ... -> u -> v] - [b ...]   |   v --(i-1.)--> b_p
                for lat_v in DP[v, b_p]:
                    for mem_v in DP[v, b_p][lat_v]:
                        for lat_b, opt_b in TDP[b].items():
                            # add delay for cut and round b in cpath => v in cpath
                            # lat_b_hat = math.ceil((delay + opt_b.lat) / l_scale) if b in cpath else 0
                            lat_b_hat = (lat_b - math.ceil(opt_b.top_lat / l_scale)
                                         + math.ceil((opt_b.top_lat + delay) / l_scale)) if b in cpath else 0
                            if (lat := lat_v + lat_b_hat) > L_hat:
                                # Infeasible subcase due to exceeded latency constraint
                                continue
                            sub_v = DP[v, b_p][lat_v][mem_v]
                            # Sub-partitions are just concatenated
                            top_lat, weight, barr = sub_v.top_lat, sub_v.weight + opt_b.weight, sub_v.barr | opt_b.barr
                            # Check whether the current subcase is a better sub-solution for state (e_vb, lat, mem)
                            if (lat not in DP[e_vb] or mem_v not in DP[e_vb][lat]
                                    or weight > DP[e_vb][lat][mem_v].weight):
                                if bidirectional:
                                    # Eliminate prior subcases that are dominated by the new subcase
                                    for l, m in tuple((_l, _m) for _l in DP[e_vb] if _l >= lat for _m in DP[e_vb][_l]
                                                      if _m >= mem_v and DP[e_vb][_l][_m].weight <= weight):
                                        if len(DP[e_vb][l]) > 1:
                                            del DP[e_vb][l][m]
                                        else:
                                            del DP[e_vb][l]
                                # Add superior subcase
                                DP[e_vb][lat][mem_v] = WeightedSubLTreePart(weight, top_lat, sub_v.mul, barr)
                                # Accumulate max calculated weight for subcases of n
                                w_max = max(w_max, weight)
        # Cache the best subcase for subtree T_n getting from the last successor of node n
        sn_last = collections.deque(tree.successors(n), 1).pop() if len(tree.succ[n]) else 0
        # Trim state space based on given bi-criteria parameters
        if len(tree.succ[n]) > 0:
            # Calculate trim interval size for weights
            w_scale = ((Epsilon * w_max) / t_size) if Epsilon > 0.0 and w_max > 0 else 1.0
            _kept_subcases = {}
            # Search for dominated subcases
            for lat, dpn in tuple(DP[n, sn_last].items()):
                for mem, subcase in tuple(dpn.items()):
                    # Track states as a tuple of interval sequence numbers
                    if (lw_state := (lat, math.ceil(subcase.weight / w_scale))) in _kept_subcases:
                        kept_mem = _kept_subcases[lw_state]
                        # Evaluate dominance relation between visited and current subcase
                        if kept_mem > mem:
                            # Drop dominated subcase
                            if len(DP[n, sn_last][lat]) > 1:
                                del DP[n, sn_last][lat][kept_mem]
                            else:
                                del DP[n, sn_last][lat]
                        else:
                            continue
                    # Add subcase as kept state
                    _kept_subcases[lw_state] = mem
        # Store the max-weight subcases of subtree T_n
        for lat_n, dp in DP[n, sn_last].items():
            TDP[n][lat_n] = max(dp.values(), key=operator.itemgetter(0))
    # Subcases under the root node contain the feasible partitioning
    if (opt_lat := max(TDP[root], key=lambda _l: TDP[root][_l].weight, default=None)) is not None:
        opt = TDP[root][opt_lat]
        return recreate_subtree_blocks(tree, opt.barr), opt.weight, opt_lat
    else:
        # No feasible solution
        return INFEASIBLE


def bifptas_tree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                              cp_end: int = None, delay: int = 1, Epsilon: float = 0.0, Lambda: float = 0.0,
                              bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes, while
    applying the left-right tree traversal approach.

    Recalculates original sum cost and latency metrics.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cp_end:          tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:           invocation delay between blocks
    :param Epsilon:         weight factor for state space trimming (0 <= Eps < 1, Eps = 0 falls back to exact calc.)
    :param Lambda:          latency factor for state space trimming (0 <= Lambda, Lambda = 0 falls back to exact calc.)
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    partition, *_ = bifptas_ltree_partitioning(tree, root, M, L, cp_end, delay, Epsilon, Lambda, bidirectional)
    if partition:
        # noinspection PyTypeChecker
        return partition, *recalculate_ser_partitioning(tree, partition, root, cp_end, delay)
    else:
        # No feasible solution
        return INFEASIBLE


########################################################################################################################


class WeightedDualSubLTreePart(typing.NamedTuple):
    """Store subtree partitioning attributes for a given edge-weighted subcase."""
    mem: int = 0  # Memory demand of the topmost block in the subtree partitioning
    top_lat: int = 0  # Calculated latency for the topmost partition block
    mul: int = 1  # Last serialization multiplier of the top/first block of the subtree partitioning
    barr: set[int] = set()  # Barrier/heading nodes of the given subtree partitioning

    def __repr__(self):
        return repr(tuple(self))


def bifptas_dual_ltree_partitioning(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                                    M: int = math.inf, L: int = math.inf, cp_end: int = None, delay: int = 1,
                                    Epsilon: float = 0.0, Lambda: float = 0.0, bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes, while
    applying the left-right tree traversal approach.

    Cost approximation ratio *Epsilon* controls the maximum deviation from the cost-optimal partitioning
    (Epsilon=0.0 enforces the algorithm to calculate exact solution) in exchange for reduces subcase calculations.

    Latency violation ratio (*Lambda*) controls the maximum violating deviation from the latency limit $L$
    (Lambda=0.0 enforces no violation)  in exchange for reduces subcase calculations.

    Instead of direct cost calculations, the cumulative overheads of externalized states are subject to minimization
    as a different formalization of the same optimization problem.

    Block metrics are calculated based on serialized execution platform model.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cp_end:          tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:           invocation delay between blocks
    :param Epsilon:         weight factor for state space trimming (0 <= Eps < 1, Eps = 0 falls back to exact calc.)
    :param Lambda:          latency factor for state space trimming (0 <= Lambda, Lambda = 0 falls back to exact calc.)
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    # Set of critical path's nodes
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    # Init empty data structure for optimal results of subtrees
    TDP = {n: {} for n in tree if n is not PLATFORM}
    t_size = len(TDP)
    # Calculate latency rounding interval and scaled latency upper bound
    if Lambda > 0.0 and L < math.inf:
        l_scale = ((Lambda * L) / t_size)
        L_hat = math.floor(L / l_scale) + t_size
    else:
        l_scale, L_hat = 1.0, L
    w_max = max(d[WEIGHT] for u, v, d in ipostorder_edges(tree, root, data=True)
                if d.setdefault(WEIGHT, d[RATE] * d[DATA]) and tree.nodes[u][MEMORY] + tree.nodes[v][MEMORY] <= M)
    w_scale = ((Epsilon * w_max) / t_size) if Epsilon > 0.0 and w_max > 0 else 1.0
    # Process subtrees of T in a bottom-up traversal order
    for p, n in ipostorder_dfs(tree, root):
        # Init empty data structure for optimal subcases T_n[v,b]
        DP = collections.defaultdict(lambda: collections.defaultdict(dict))
        # Traverse subtree T_n in a left-right traversal
        #       |--(j-1.)--> [v_p]   |--(i-1.)--> [b_p]                                 | left side
        # -->  [u]  ----(j.)---->  [v]  ----(i.)---->  [b]  ----(max_k.)----> [b_k]     | right side
        for e_uvp, b_p, e_vb in ileft_right_dfs(tree, n):
            v, b = e_vb
            # Merge edge u -> v
            if b == 0:
                # SINGLETON: C[n,0] - calculate the default subcase of singleton partition of root node n
                if v == n:
                    t_n, m_n = tree.nodes[n][RUNTIME], tree.nodes[n][MEMORY]
                    r_n, d_n = tree[p][n][RATE], tree[p][n][DATA]
                    if n in cpath:
                        nc = next(filter(lambda c: c in cpath, tree.successors(n)), None)
                        lat_n = d_n + t_n + (math.ceil(tree[n][nc][RATE] / r_n) * tree[n][nc][DATA] if nc else 0)
                    else:
                        lat_n = 0
                    # Rounding latency value for singleton block
                    lat = math.ceil(lat_n / l_scale)
                    # For singleton blocks weight is 0 by default
                    DP[e_vb][lat][0] = WeightedDualSubLTreePart(m_n, lat_n, 1, {n})
                # MERGE: C[v,0] - subcase of merging single node v into the n-rooted block containing node u
                else:
                    u, _ = e_uvp
                    t_v, m_v = tree.nodes[v][RUNTIME], tree.nodes[v][MEMORY]
                    r_v, d_v, w_v = tree[u][v][RATE], tree[u][v][DATA], tree[u][v][WEIGHT]
                    # v_p = 0 => no prior sibling node, C[v,0] = C[u,j-1] + delta(u,v)
                    for lat_u in DP[e_uvp]:
                        for weight_u in DP[e_uvp][lat_u]:
                            sub_u = DP[e_uvp][lat_u][weight_u]
                            if (mem := sub_u.mem + m_v) > M:
                                # Infeasible subcase due to exceeded memory constraint
                                continue
                            # v in cpath => u in cpath
                            if v in cpath:
                                n_v = math.ceil(r_v / tree[next(tree.predecessors(u))][u][RATE]) * sub_u.mul
                                vc = next(filter(lambda c: c in cpath, tree.successors(v)), None)
                                o_v = math.ceil(tree[v][vc][RATE] / r_v) * tree[v][vc][DATA] if vc else 0
                                # Calculate latency of merged node v and add rounded value to top block
                                top_lat = sub_u.top_lat + n_v * (t_v - d_v + o_v)
                                if (lat := math.ceil(top_lat / l_scale)) > L_hat:
                                    # Infeasible subcase due to exceeded latency constraint
                                    continue
                            else:
                                # Top block's latency attributes remains the same
                                lat, top_lat, n_v = lat_u, sub_u.top_lat, sub_u.mul
                            # Store subcase with weight increased by the merged/covered edge weight
                            weight = weight_u + math.ceil(w_v / w_scale)
                            DP[e_vb][lat][weight] = WeightedDualSubLTreePart(mem, top_lat, n_v, sub_u.barr)
            # CUT: C[v,b]
            else:
                # b_k <- C[v_i, d(v_i)]
                b_k = collections.deque(tree.successors(b), 1).pop() if len(tree.succ[b]) else 0
                # Previously merged edge: v -> b  =>  [root ... -> u -> v -> b ...]   |   [b]  --(max_k.)--> [b_w]
                DP[e_vb] = DP[b, b_k]
                # Cut edge: v -> b  |  [root ... -> u -> v] - [b ...]   |   v --(i-1.)--> b_p
                for lat_v in DP[v, b_p]:
                    for weight_v in DP[v, b_p][lat_v]:
                        sub_v = DP[v, b_p][lat_v][weight_v]
                        for (weight_b, lat_b), opt_b in TDP[b].items():
                            # add delay for cut and round b in cpath => v in cpath
                            lat_b_hat = (lat_b - math.ceil(opt_b.top_lat / l_scale)
                                         + math.ceil((opt_b.top_lat + delay) / l_scale)) if b in cpath else 0
                            if (lat := lat_v + lat_b_hat) > L_hat:
                                # Infeasible subcase due to exceeded latency constraint
                                continue
                            # Sub-partitions are just concatenated
                            top_lat, mem = sub_v.top_lat, sub_v.mem
                            weight, barr = weight_v + weight_b, sub_v.barr | opt_b.barr
                            # Check whether the current subcase is a better sub-solution for state (e_vb, lat, mem)
                            if lat not in DP[e_vb] or weight not in DP[e_vb][lat] or mem < DP[e_vb][lat][weight].mem:
                                if bidirectional:
                                    # Eliminate prior subcases that are dominated by the new subcase
                                    for l, w in tuple((_l, _w) for _l in DP[e_vb] if _l >= lat for _w in DP[e_vb][_l]
                                                      if _w <= weight and DP[e_vb][_l][_w].mem >= mem):
                                        if len(DP[e_vb][l]) > 1:
                                            del DP[e_vb][l][w]
                                        else:
                                            del DP[e_vb][l]
                                # Add superior subcase
                                DP[e_vb][lat][weight] = WeightedDualSubLTreePart(mem, top_lat, sub_v.mul, barr)
        # Cache the best subcase for subtree T_n getting from the last successor of node n
        sn_last = collections.deque(tree.successors(n), 1).pop() if len(tree.succ[n]) else 0
        # Store the max-weight subcases of subtree T_n
        for lat_n, dp in DP[n, sn_last].items():
            weight_n_max = max(dp)
            TDP[n][weight_n_max, lat_n] = dp[weight_n_max]
    # Subcases under the root node contain the feasible partitioning
    if opt_wl := max(TDP[root], key=operator.itemgetter(0), default=None):
        # noinspection PyTypeChecker
        return recreate_subtree_blocks(tree, TDP[root][opt_wl].barr), *opt_wl
    else:
        # No feasible solution
        return INFEASIBLE


def bifptas_dual_tree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                                   cp_end: int = None, delay: int = 1, Epsilon: float = 0.0, Lambda: float = 0.0,
                                   bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes, while
    applying a different formalization of the optimal partitioning problem.

    Cost approximation ratio *Epsilon* controls the maximum deviation from the cost-optimal partitioning
    (Epsilon=0.0 enforces the algorithm to calculate exact solution) in exchange for reduces subcase calculations.

    Latency violation ratio (*Lambda*) controls the maximum violating deviation from the latency limit $L$
    (Lambda=0.0 enforces no violation)  in exchange for reduces subcase calculations.

    Block metrics are calculated based on serialized execution platform model.

    Recalculates original sum cost and latency metrics.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cp_end:          tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:           invocation delay between blocks
    :param Epsilon:         weight factor for state space trimming (0 <= Eps < 1, Eps = 0 falls back to exact calc.)
    :param Lambda:          latency factor for state space trimming (0 <= Lambda, Lambda = 0 falls back to exact calc.)
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    partition, *_ = bifptas_dual_ltree_partitioning(tree, root, M, L, cp_end, delay, Epsilon, Lambda, bidirectional)
    if partition:
        # noinspection PyTypeChecker
        return partition, *recalculate_ser_partitioning(tree, partition, root, cp_end, delay)
    else:
        # No feasible solution
        return INFEASIBLE
