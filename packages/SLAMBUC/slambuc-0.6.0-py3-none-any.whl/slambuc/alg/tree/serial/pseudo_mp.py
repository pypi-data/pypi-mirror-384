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
import multiprocessing
import operator
import typing
from collections.abc import Generator

import networkx as nx

from slambuc.alg import INFEASIBLE, T_RESULTS
from slambuc.alg.app import *
from slambuc.alg.tree.serial.pseudo import SubBTreePart, SubLTreePart, OPT
from slambuc.alg.util import (ipostorder_dfs, ibacktrack_chain, recreate_subtree_blocks, ipostorder_tabu_dfs,
                              ileft_right_dfs, verify_limits)


def isubtree_cutoffs(tree: nx.DiGraph, root: int = 1, lb: int = 1,
                     ub: int | float = math.inf) -> typing.Generator[tuple[tuple[int, int], int], None, None]:
    """
    Recursively return edges that cut off non-trivial subtrees from *tree* with size between *lb* and *ub*.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param lb:      lower size bound
    :param ub:      upper size bound
    :return:        cut barrier node, branches and subtree root
    """
    _tmp = {}
    for _, v in ipostorder_dfs(tree, root, inclusive=True):
        # Sum the size of descendant subtrees
        if len(brs := _tmp.setdefault(v, {s: sum(_tmp.pop(s).values(), start=1) for s in tree.successors(v)})) > 1:
            # Only consider subtrees with proper size
            for br, st in brs.items():
                if lb <= st:
                    if ub <= st:
                        _tmp[v][br] = 0
                    yield (v, br), st


def get_cpu_splits(tree: nx.DiGraph, root: int = 1, workers: int = None) -> list[tuple[int, int]]:
    """
    Calculate the cuts for parallelization based on *workers* count and subtree size heuristics.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param workers: workers count
    :return:        cut edges
    """
    ub = math.sqrt(len(tree) - 1)
    lb = ub if not workers else 1
    n = workers if workers else ub
    return [e for e, _ in heapq.nlargest(round(n),
                                         list(isubtree_cutoffs(tree, root, lb, ub)), key=operator.itemgetter(1))]


def isubtree_sync_cutoffs(tree: nx.DiGraph, root: int = 1,
                          size: int = math.inf) -> Generator[tuple[tuple[int | str, int], int | None, set[int]]]:
    """
    Recursively return edges that cut off non-trivial subtrees from *tree* with given *size*.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param size:    subtree min size
    :return:        generator of cut edge, subtree root, and related branches
    """
    _tmp, sync = {}, collections.defaultdict(set)
    for _, v in ipostorder_dfs(tree, root, inclusive=True):
        # Sum the size of descendant subtrees
        brs = _tmp.setdefault(v, {s: sum(_tmp.pop(s).values(), start=0 if s in sync else 1)
                                  for s in tree.successors(v)}).items()
        for br, st in brs:
            # Only consider subtrees with proper size
            if len(brs) > 1 and size <= st:
                # Return the cut edge, number of freely processable nodes, list of sync nodes
                yield (v, br), st, sync[br]
                # Clear nodes free to process
                _tmp[v][br] = 0
                # Cache subcase node required to be waited as a sync point
                sync[v].add(br)
            elif br in sync:
                # Mark as a dependent node and propagate sync points
                sync[v].update(sync[br])
        if v == root:
            yield (PLATFORM, root), None, sync[root]


def isubtree_splits(tree: nx.DiGraph, root: int = 1) -> Generator[tuple[tuple[int | str, int], set[int]]]:
    """
    Return the heuristic cutoff edges of given *tree* along with the mandatory synchronization points by assuming
    the subtree size equals *sqrt(n)*.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :return:        generator of cut edge, subtree root, and related branches
    """
    yield from ((c, sync) for c, _, sync in isubtree_sync_cutoffs(tree, root, math.ceil(math.sqrt(len(tree) - 1))))


########################################################################################################################


def _btree_partitioning(ready: typing.Union[multiprocessing.SimpleQueue, None],
                        sync: dict[int, multiprocessing.SimpleQueue],
                        tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                        M: int = math.inf, L: int = math.inf, cpath: set[int] = frozenset(), delay: int = 1,
                        bidirectional: bool = True) -> None | dict[int, dict[tuple[int, int], SubBTreePart]]:
    """
    Calculates minimal-cost partitioning of a subgraph with *root* using the bottom-up tree traversal approach
    while waits for subcases at sync edges.

    This function is designed for running in a separate detached subprocess and synchronizing subresults via
    *SimpleQueue* objects as an IPC method.

    :param ready:           object for signaling the end of partitioning
    :param sync:            object regarding subtrees which results need to be waited for
    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cpath:           critical path nodes
    :param delay:           invocation delay between blocks
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    # Allocate empty dict for local subcases combined with prior subcase results
    DP = {}
    # Iterate nodes in a bottom-up traversal order except the subtrees of the sync points
    for p, v in ipostorder_tabu_dfs(tree, root, tabu=sync):
        r_v, d_v, t_v, m_v = tree[p][v][RATE], tree[p][v][DATA], tree.nodes[v][RUNTIME], tree.nodes[v][MEMORY]
        # SINGLETON: calculate the default subcase of singleton partition of node v
        cost = r_v * (d_v + t_v) + sum(vs[RATE] * vs[DATA] for vs in tree.succ[v].values())
        # Only add fetching overhead for root node and omit caching to ensure lat monotonicity of upward merging
        lat = d_v + t_v if p is PLATFORM else t_v if v in cpath else 0
        DP[v] = {(lat, lat): {m_v: SubBTreePart(cost, {v})}}
        # Bottom-up propagation for considering v's descendant subcases in rearranged order (non-sync points first)
        # -->   p   ---->   v   ----[i.]---->   b
        for b in itertools.chain(filter(lambda x: x not in sync, tree.successors(v)),
                                 filter(sync.__contains__, tree.successors(v))):
            # Waiting for dependent subprocess to be finished
            if b in sync:
                DP[b] = sync[b].get()
                sync[b].close()
            # Init empty data structure of subcase T[v,b]
            _cache = collections.defaultdict(dict)
            r_b, d_b, t_b = tree[v][b][RATE], tree[v][b][DATA], tree.nodes[b][RUNTIME]
            # Calculate possible latency/memory combinations while dropping subcases of v and b from DP
            for ((lat_v, blk_lat_v), DPv), ((lat_b, blk_lat_b), DPb) in itertools.product(DP[v].items(),
                                                                                          DP.pop(b).items()):
                for (mem_v, sub_v), (mem_b, sub_b) in itertools.product(DPv.items(), DPb.items()):
                    # Latency calculation in case v -> b edge is in cpath
                    if b in cpath:
                        r_v = tree[p][v][RATE]
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
                        mem, barr, cost = mem_v, sub_v.barr | sub_b.barr, sub_v.cost + sub_b.cost
                    # MERGE: v -> b edge is marked as a merge
                    elif (mem := mem_v + mem_b) > M:
                        # Infeasible subcase due to exceeded memory constraint
                        continue
                    else:
                        # Top blocks of the two sub-partitions are merged together with root node v
                        barr, cost = sub_v.barr | sub_b.barr - {b}, sub_v.cost + sub_b.cost - 2 * r_b * d_b
                    # Store the min cost subcase
                    sub_lats = lat, top_blk_lat
                    # Check whether the current subcase is a better sub-solution for state (v, sub_lats, mem)
                    if mem not in _cache[sub_lats] or cost < _cache[sub_lats][mem].cost:
                        if bidirectional:
                            # Eliminate prior subcases that are dominated by the new subcase
                            for l, m in [(_l, _m) for _l in _cache if _l[0] >= lat and _l[1] >= top_blk_lat
                                         for _m in _cache[_l] if _m >= mem and _cache[_l][_m].cost >= cost]:
                                if len(_cache[l]) > 1:
                                    del _cache[l][m]
                                else:
                                    del _cache[l]
                        # Add superior subcase
                        _cache[sub_lats][mem] = SubBTreePart(cost, barr)
            # Store min subcases as C(v,i-1) for the next iteration of the propagation process
            DP[v] = _cache
            # Drop unnecessary subcases
        # Store the cost-opt subcases wrt. latency for node v encoded with memory value 0
        for sub_v in DP[v].values():
            sub_v[OPT] = min(sub_v.values(), key=operator.itemgetter(0))
    # Notify waiting process and push optimal subcases or return TDP locally for the main thread
    return ready.put(DP[root]) if ready else DP


def pseudo_mp_btree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf,
                                 L: int = math.inf, cp_end: int = None, delay: int = 1,
                                 bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes.

    Partitioning is calculated using the bottom-up tree traversal approach.

    Arbitrary disjoint subtrees are partitioned in separate subprocesses.

    Block metrics are calculated based on serialized execution platform model.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cp_end:          tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:           invocation delay between blocks
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    # Critical path
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    workers, events, sync = [], {}, None
    # Split tree and initiate subprocesses to calculate subcases
    try:
        for (p, v), sync in isubtree_splits(tree, root):
            # Collect event of sync points
            sync = {s: events[s] for s in sync}
            if p is not PLATFORM:
                # Add own event for signaling readiness
                ready = events.setdefault(v, multiprocessing.SimpleQueue())
                # Create and start worker process
                workers.append(multiprocessing.Process(target=_btree_partitioning, name=f"subtree_{v}",
                                                       args=(ready, sync, tree, v, M, L, cpath, delay, bidirectional),
                                                       daemon=True))
                workers[-1].start()
        # Process last/topmost subtree in the main process and get subresults locally
        DP = _btree_partitioning(None, sync, tree, root, M, L, cpath, delay, bidirectional)
    except BaseException:
        # Terminate all initiated subprocesses in case of interruption
        for w in workers:
            w.terminate()
        # Reraise exception for further handling
        raise
    finally:
        # Wait for all subprocesses to terminate for closing all used resources
        for w in workers:
            w.join(timeout=0)
            if w.is_alive():
                w.kill()
                w.join()
    # Subcases under the root node contain the feasible partitioning
    if opt_lats := min(DP[root], key=lambda _l: DP[root][_l][OPT].cost, default=None):
        opt = DP[root][opt_lats][OPT]
        return recreate_subtree_blocks(tree, opt.barr), opt.cost, opt_lats[0]
    else:
        # No feasible solution
        return INFEASIBLE


########################################################################################################################


def _ltree_partitioning(ready: typing.Union[multiprocessing.SimpleQueue, None],
                        sync: dict[int, multiprocessing.SimpleQueue],
                        tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                        M: int = math.inf, L: int = math.inf, cpath: set[int] = frozenset(), delay: int = 1,
                        bidirectional: bool = True) -> None | dict[int, dict[int, SubBTreePart]]:
    """
    Calculates minimal-cost partitioning of a subgraph with *root* using the left-right tree traversal approach
    while waits for subcases at sync edges.

    This function is designed for running in a separate detached subprocess and synchronizing subresults via
    *SimpleQueue* objects as an IPC method.

    :param ready:           object for signaling the end of partitioning
    :param sync:            object regarding subtrees which results need to be waited for
    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cpath:           critical path nodes
    :param delay:           invocation delay between blocks
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    # Allocate empty dict for local subcases combined with prior subcase results
    TDP = {}
    # Process subtrees of T in a bottom-up traversal order
    for p, n in ipostorder_tabu_dfs(tree, root, tabu=sync):
        # Init empty data structure for optimal subcases T_n[v,b]
        DP = collections.defaultdict(lambda: collections.defaultdict(dict))
        # Store sync point of the overlapped subtree
        sentinel = None
        # Traverse subtree T_n in a left-right traversal
        #       |--(j-1.)--> [v_p]   |--(i-1.)--> [b_p]                                 | left side
        # -->  [u]  ----(j.)---->  [v]  ----(i.)---->  [b]  ----(max_k.)----> [b_k]     | right side
        for e_uvp, b_p, e_vb in ileft_right_dfs(tree, n):
            v, b = e_vb
            # Merge edge u -> v
            if b == 0:
                # Cache passed sync point
                if v in sync:
                    sentinel = sync[v]
                # SINGLETON: C[n,0] - calculate the default subcase of singleton partition of root node n
                if v == n:
                    r_n, d_n, t_n = tree[p][n][RATE], tree[p][n][DATA], tree.nodes[n][RUNTIME]
                    cost = r_n * (d_n + t_n) + sum(ns[RATE] * ns[DATA] for ns in tree.succ[n].values())
                    if n in cpath:
                        nc = next(filter(lambda c: c in cpath, tree.successors(n)), None)
                        lat = d_n + t_n + (math.ceil(tree[n][nc][RATE] / r_n) * tree[n][nc][DATA] if nc else 0)
                    else:
                        lat = 0
                    DP[e_vb][lat][tree.nodes[n][MEMORY]] = SubLTreePart(cost, 1, {n})
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
                                rel_r_v = math.ceil(r_v / tree[next(tree.predecessors(u))][u][RATE])
                                n_v = rel_r_v * sub_u.mul
                                vc = next(filter(lambda c: c in cpath, tree.successors(v)), None)
                                w_v = math.ceil(tree[v][vc][RATE] / r_v) * tree[v][vc][DATA] if vc else 0
                                if (lat := lat_u + n_v * (t_v - d_v + w_v)) > L:
                                    # Infeasible subcase due to exceeded latency constraint
                                    continue
                            else:
                                lat, n_v = lat_u, sub_u.mul
                            cost = sub_u.cost + r_v * (t_v - d_v) + sum(vs[RATE] * vs[DATA]
                                                                        for vs in tree.succ[v].values())
                            DP[e_vb][lat][mem] = SubLTreePart(cost, n_v, sub_u.barr)
            # CUT: C[v,b]
            else:
                # b_k <- C[v_i, d(v_i)]
                b_k = collections.deque(tree.successors(b), 1).pop() if len(tree.succ[b]) else 0
                # Previously merged edge: v -> b  =>  [root ... -> u -> v -> b ...]   |   [b]  --(max_k.)--> [b_w]
                DP[e_vb] = DP[b, b_k]
                # Cut edge: v -> b  |  [root ... -> u -> v] - [b ...]   |   v --(i-1.)--> b_p
                for lat_v in DP[v, b_p]:
                    for mem_v in DP[v, b_p][lat_v]:
                        # Waiting for dependent subprocess to be finished and pull optimal subcases
                        if b not in TDP:
                            TDP.update(sentinel.get())
                            sentinel.close()
                        # assert b in TDP, f"proc{root} {b} not in {TDP.keys()}, {e_uvp=}, {b_p=}, {e_vb=}"
                        for lat_b, opt_b in TDP[b].items():
                            # b in cpath => v in cpath
                            if (lat := lat_v + delay + lat_b if b in cpath else lat_v) > L:
                                # Infeasible subcase due to exceeded latency constraint
                                continue
                            sub_v = DP[v, b_p][lat_v][mem_v]
                            cost, barr = sub_v.cost + opt_b.cost, sub_v.barr | opt_b.barr
                            # Check whether the current subcase is a better sub-solution for state (e_vb, lat, mem)
                            if lat not in DP[e_vb] or mem_v not in DP[e_vb][lat] or cost < DP[e_vb][lat][mem_v].cost:
                                if bidirectional:
                                    # Eliminate prior subcases that are dominated by the new subcase
                                    for l, m in [(_l, _m) for _l in DP[e_vb] if _l >= lat for _m in DP[e_vb][_l]
                                                 if _m >= mem_v and DP[e_vb][_l][_m].cost >= cost]:
                                        if len(DP[e_vb][l]) > 1:
                                            del DP[e_vb][l][m]
                                        else:
                                            del DP[e_vb][l]
                                # Add superior subcase
                                DP[e_vb][lat][mem_v] = SubLTreePart(cost, sub_v.mul, barr)
        # Cache the best subcase for subtree T_n
        n_w = collections.deque(tree.successors(n), 1).pop() if len(tree.succ[n]) else 0
        # Store the best subcases of subtree T_n
        TDP[n] = {lat_n: min(dp.values(), key=operator.itemgetter(OPT)) for lat_n, dp in DP[n, n_w].items()}
    # Notify waiting process and push optimal subcases or return TDP locally for the main thread
    return ready.put(TDP) if ready else TDP


def pseudo_mp_ltree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf,
                                 L: int = math.inf, cp_end: int = None, delay: int = 1,
                                 bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes.

    Partitioning is calculated using the left-right tree traversal approach.

    Arbitrary disjoint subtrees are partitioned in separate subprocesses.

    Block metrics are calculated based on serialized execution platform model.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param cp_end:          tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:           invocation delay between blocks
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    # Critical path
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    workers, events, sync = [], {}, None
    try:
        # Split tree and initiate subprocesses to calculate subcases
        for (p, v), sync in isubtree_splits(tree, root):
            # Collect event of sync points
            sync = {s: events[s] for s in sync}
            if p is not PLATFORM:
                # Add own event for signaling readiness
                ready = events.setdefault(v, multiprocessing.SimpleQueue())
                # Create and start worker process
                workers.append(multiprocessing.Process(target=_ltree_partitioning, name=f"subtree_{v}",
                                                       args=(ready, sync, tree, v, M, L, cpath, delay, bidirectional),
                                                       daemon=True))
                workers[-1].start()
        # Process last/topmost subtree in the main process and get subresults locally
        TDP = _ltree_partitioning(None, sync, tree, root, M, L, cpath, delay, bidirectional)
    except BaseException:
        # Terminate all initiated subprocesses in case of interruption
        for w in workers:
            w.terminate()
        # Reraise exception for further handling
        raise
    finally:
        # Wait for all subprocesses to terminate for closing all used resources
        for w in workers:
            w.join(timeout=0)
            if w.is_alive():
                w.kill()
                w.join()
    # Subcases under the root node contain the feasible partitioning
    if (opt_lat := min(TDP[root], key=lambda _l: TDP[root][_l].cost, default=None)) is not None:
        opt = TDP[root][opt_lat]
        return recreate_subtree_blocks(tree, opt.barr), opt.cost, opt_lat
    else:
        # No feasible solution
        return INFEASIBLE
