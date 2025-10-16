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
import math
import multiprocessing
import operator
import typing

import networkx as nx

from slambuc.alg import INFEASIBLE, T_RESULTS
from slambuc.alg.app import *
from slambuc.alg.tree.serial.pseudo import SubBTreePart, SubLTreePart, OPT
from slambuc.alg.tree.serial.pseudo_mp import isubtree_splits
from slambuc.alg.util import (ipostorder_dfs, ibacktrack_chain, recreate_subtree_blocks, ileft_right_dfs,
                              par_inst_count, verify_limits)


def _par_ltree_partitioning(ready: typing.Union[multiprocessing.SimpleQueue, None],
                            sync: dict[int, multiprocessing.SimpleQueue],
                            tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                            M: int = math.inf, L: int = math.inf, N: int = 1, cpath: set[int] = frozenset(),
                            delay: int = 1, bidirectional: bool = True) -> None | dict[int, SubBTreePart]:
    """
    Calculates minimal-cost partitioning of a subgraph with *root* node using the left-right tree traversal approach
    while waits for subcases at *sync* edges.

    This function is designed for running in a separate detached subprocess and synchronizing subresults via
    *SimpleQueue* objects as an IPC method.

    :param ready:           object for signaling the end of partitioning
    :param sync:            object regarding subtrees which results need to be waited for
    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param N:               available CPU core count
    :param cpath:           critical path nodes
    :param delay:           invocation delay between blocks
    :param bidirectional:   use bidirectional subcase elimination (may introduce quadratic increase in the worst case)
    :return:                tuple of optimal partitioning, reached sum cost and latency on the critical path
    """
    # Allocate empty dict for local subcases combined with prior subcase results
    TDP = {}
    # Process subtrees of T in a bottom-up traversal order
    for p, n in ipostorder_dfs(tree, root):
        # Init empty data structure for optimal subcases T_n[v,b]
        DP = collections.defaultdict(lambda: collections.defaultdict(dict))
        # Store sync point of the overlapped subtree
        sentinel = None
        r_n, d_n, t_n, m_n = tree[p][n][RATE], tree[p][n][DATA], tree.nodes[n][RUNTIME], tree.nodes[n][MEMORY]
        # Traverse subtree T_n in a left-right traversal
        #       |--(j-1.)--> [v_p]   |--(i-1.)--> [b_p]                                 | left side
        # -->  [u]  ----(j.)---->  [v]  ----(i.)---->  [b]  ----(max_k.)----> [b_k]     | right side
        for e_uvp, b_p, e_vb in ileft_right_dfs(tree, n):
            v, b = e_vb
            # Merge edge u -> v as consider node v and all its first 0 child (b=0)
            if b == 0:
                # Cache passed sync point
                if v in sync:
                    sentinel = sync[v]
                # SINGLETON: C[n,0] - calculate the default subcase of singleton partition of root node n
                if v == n:
                    cost = r_n * (d_n + t_n) + sum(par_inst_count(r_n, ns[RATE], N) * ns[DATA]
                                                   for ns in tree.succ[n].values())
                    if n in cpath:
                        nc = next(filter(lambda c: c in cpath, tree.successors(n)), None)
                        # n_v = 1 for root node n; add caching overhead on critical path here
                        lat = d_n + t_n + (math.ceil(tree[n][nc][RATE] / (r_n * N)) * tree[n][nc][DATA] if nc else 0)
                    else:
                        lat = 0
                    DP[e_vb][lat][m_n, m_n] = SubLTreePart(cost, 1, {n})
                # MERGE: C[v,0] - subcase of merging single node v into the n-rooted block containing node u
                else:
                    u, v_p = e_uvp
                    r_v, d_v = tree[u][v][RATE], tree[u][v][DATA]
                    t_v, m_v = tree.nodes[v][RUNTIME], tree.nodes[v][MEMORY]
                    # v_p = 0 => no prior sibling node, C[v,0] = C[u,j-1] + delta(u,v)
                    for lat_u in DP[e_uvp]:
                        for mem_u in DP[e_uvp][lat_u]:
                            sub_u = DP[e_uvp][lat_u][mem_u]
                            # Calculate memory prefetch and operative memory demands separately
                            mem = mem_u[0] + m_v, max(mem_u[1], min(math.ceil(r_v / r_n), N) * m_v)
                            if max(mem) > M:
                                # Infeasible subcase due to exceeded memory constraint
                                continue
                            # v in cpath => u in cpath
                            if v in cpath:
                                rel_r_v = math.ceil(r_v / (tree[next(tree.predecessors(u))][u][RATE] * N))
                                n_v = rel_r_v * sub_u.mul
                                vc = next(filter(lambda c: c in cpath, tree.successors(v)), None)
                                w_v = math.ceil(tree[v][vc][RATE] / (r_v * N)) * tree[v][vc][DATA] if vc else 0
                                # Recalculate caching overhead (remove prior block's write out from E2E latency)
                                if (lat := lat_u + n_v * (t_v - d_v + w_v)) > L:
                                    # Infeasible subcase due to exceeded latency constraint
                                    continue
                            else:
                                lat, n_v = lat_u, sub_u.mul
                            # Calculate sum cost by adding merged node runtime and caching
                            cost = (sub_u.cost + par_inst_count(r_n, r_v, N) * (t_v - d_v) +
                                    sum(par_inst_count(r_n, vs[RATE], N) * vs[DATA] for vs in tree.succ[v].values()))
                            # Check whether the current subcase is a better sub-solution for state (e_vb, lat, mem)
                            if lat not in DP[e_vb] or mem not in DP[e_vb][lat] or cost < DP[e_vb][lat][mem].cost:
                                # Eliminate prior subcases that are dominated by the new subcase
                                for l, m in tuple((_l, _m) for _l in DP[e_vb] if _l >= lat
                                                  for _m in DP[e_vb][_l] if (_m[0] >= mem[0] and _m[0] >= mem[0]
                                                                             and DP[e_vb][_l][_m].cost >= cost)):
                                    if len(DP[e_vb][l]) > 1:
                                        del DP[e_vb][l][m]
                                    else:
                                        del DP[e_vb][l]
                                # Add superior subcase
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
                        for lat_b, opt_b in TDP[b].items():
                            # b in cpath => v in cpath
                            if (lat := lat_v + delay + lat_b if b in cpath else lat_v) > L:
                                # Infeasible subcase due to exceeded latency constraint
                                continue
                            sub_v = DP[v, b_p][lat_v][mem_v]
                            # Only concatenate blocks
                            cost, barr = sub_v.cost + opt_b.cost, sub_v.barr | opt_b.barr
                            # Check whether the current subcase is a better sub-solution for state (e_vb, lat, mem)
                            if lat not in DP[e_vb] or mem_v not in DP[e_vb][lat] or cost < DP[e_vb][lat][mem_v].cost:
                                if bidirectional:
                                    # Eliminate prior subcases that are dominated by the new subcase
                                    for l, m in tuple((_l, _m) for _l in DP[e_vb] if _l >= lat
                                                      for _m in DP[e_vb][_l] if (_m[0] >= mem_v[0] and _m[0] >= mem_v[0]
                                                                                 and DP[e_vb][_l][_m].cost >= cost)):
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


def pseudo_par_mp_ltree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                                     N: int = 1, cp_end: int = None, delay: int = 1,
                                     bidirectional: bool = True) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes.

    Partitioning is calculated using the left-right tree traversal approach.

    Arbitrary disjoint subtrees are partitioned in separate subprocesses.

    Block metrics are calculated based on parallelized execution platform model.

    :param tree:            app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:            root node of the graph
    :param M:               upper memory bound of the partition blocks in MB
    :param L:               latency limit defined on the critical path in ms
    :param N:               available CPU core count
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
                workers.append(multiprocessing.Process(target=_par_ltree_partitioning, name=f"subtree_{v}",
                                                       args=(ready, sync, tree, v, M, L, N, cpath, delay,
                                                             bidirectional), daemon=False))
                workers[-1].start()
        # Process last/topmost subtree in the main process and get subresults locally
        TDP = _par_ltree_partitioning(None, sync, tree, root, M, L, N, cpath, delay, bidirectional)
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
