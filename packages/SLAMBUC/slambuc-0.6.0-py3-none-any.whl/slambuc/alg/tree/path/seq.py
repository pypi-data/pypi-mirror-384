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
import functools
import math
import typing

import networkx as nx

from slambuc.alg import INFEASIBLE, T_RESULTS, T_PART
from slambuc.alg.app import *
from slambuc.alg.util import ipostorder_dfs, ibacktrack_chain, verify_limits


class TBlock(typing.NamedTuple):
    """Store subtree attributes for a given seq subcase."""
    w: int = None  # Tailing node of the first block of the subtree partitioning
    sum_cost: int = math.inf  # Sum cost of the subtree partitioning
    cumsum: int = 0  # Sum (cumulative) runtime of the first block (with tail node w) in the partitioning
    sum_mem: int = math.inf  # Sum memory of the first block
    par_mem: int = math.inf  # Parallel memory of the first block
    max_rate: int = 0  # Maximum rate value of internal edge in the first block
    cpu: int = 1  # Sum CPU core need of the first block

    def __repr__(self):
        return repr(tuple(self))


def seq_tree_partitioning(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                          M: int = math.inf, N: int = math.inf, L: int = math.inf, cp_end: int = None, delay: int = 1,
                          unit: int = 1, full: bool = True) -> T_RESULTS | tuple[list, float | None, int]:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes leveraging
    a bottom-up tree traversal approach.

    Cost calculation relies on the rounding *unit* and number of vCPU cores *N*, whereas platform invocation *delay*
    is used for latency calculations.

    Details in: J. Czentye, I. Pelle and B. Sonkoly, "Cost-optimal Operation of Latency Constrained Serverless
    Applications: From Theory to Practice," NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium,
    Miami, FL, USA, 2023, pp. 1-10, doi: 10.1109/NOMS56928.2023.10154412.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param M:       upper memory bound of the partition blocks (in MB)
    :param N:       upper CPU core bound of the partition blocks
    :param L:       latency limit defined on the critical path (in ms)
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:   invocation delay between blocks
    :param unit:    rounding unit for the cost calculation (default: 100 ms)
    :param full:    return full blocks or just their ending nodes
    :return:        tuple of optimal partition, sum cost of the partitioning, and optimal number of cuts
    """
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    if cpath:
        # c_max is the number of cuts allowed by L or at most the number of edges on cpath
        c_max = math.floor(min((L - sum(tree.nodes[_v][RUNTIME] for _v in cpath)) / delay, len(cpath) - 1))
    else:
        # if cpath is undefined c_max = tree depth / number of possible edge cuts on the longest root-leaf chain
        c_max = max(len(list(ibacktrack_chain(tree, root, v))) - 1 for v in tree if not tree.succ[v])
    # Check lower bound for latency limit
    if c_max < 0:
        return [], None, c_max
    DP = [collections.defaultdict(collections.deque) for _ in range(len(tree))]
    for i in range(len(DP)):
        DP[i][0].append(TBlock())

    @functools.lru_cache(maxsize=(len(tree) - 1))
    def block_cost(pred: int, barr: int, cumsum: int, expand: bool = True) -> tuple[int, int]:
        """Calculate the sum cost of subtree: T_barr and return the cumulative sum runtime of the block[barr, w]."""
        if expand:
            cumsum += tree.nodes[barr][RUNTIME]
        return tree[pred][barr][RATE] * (math.ceil(cumsum / unit) * unit), cumsum

    @functools.lru_cache(maxsize=(len(tree) - 1))
    def block_par_mem(pred: int, barr: int, w: int) -> int:
        """Calculate memory of block: p -> [barr -> w]."""
        _pred = next(tree.predecessors(w))
        mem_par = math.ceil(tree[_pred][w][RATE] / tree[pred][barr][RATE]) * tree.nodes[w][MEMORY]
        while w > barr:
            w, _pred = _pred, next(tree.predecessors(_pred))
            mem_par = max(mem_par, math.ceil(tree[_pred][w][RATE] / tree[pred][barr][RATE]) * tree.nodes[w][MEMORY])
        return mem_par

    @functools.lru_cache(maxsize=(len(tree) - 1))
    def block_cpu(pred: int, node: int, max_rate: int, cpu: int) -> tuple[int, int]:
        """Calculate the nex CPU core need of the block[barr, w] and also return the max internal rate."""
        blk_max_rate = max(max_rate, tree[pred][node][RATE])
        return max(cpu, math.ceil(blk_max_rate / tree[pred][node][RATE])), blk_max_rate

    def qmin(node: int, c_n: int) -> int:
        """Return the sum cost of best/min subcase for *node* with *c_n* cuts."""
        return DP[node][c_n][0].sum_cost

    def qinsert(node: int, c_n: int, blk: TBlock):
        """Insert given block subcase *block* into *DP* for the *node* with *c_n* cuts."""
        if blk.sum_cost < math.inf and max(blk.sum_mem, blk.par_mem) <= M and blk.cpu <= N:
            if len(DP[node][c_n]) and blk.sum_cost <= qmin(node, c_n):
                DP[node][c_n].appendleft(blk)
            else:
                DP[node][c_n].append(blk)

    def qmerge(pred: int, node: int, c_n: int, barr: int, c_b: int, m_cost: int):
        """
        Copy DP entries from queue of node *barr* with *c_b* cuts into queue of node *node* with *c_n* cuts
        while leaving the best subcase in the original queue.
        """
        for blk in DP[barr][c_b]:
            # Ignore infeasible subcases
            if blk.sum_cost < math.inf:
                # Calculate the original cost of the block[barr, w]
                b_blk_cost, _ = block_cost(node, barr, blk.cumsum, expand=False)
                # Calculate the cost of the expanded block[node, w], n -> barr
                n_blk_cost, n_blk_cumsum = block_cost(pred, node, blk.cumsum)
                # Calculate the new sum_cost
                n_sum_cost = blk.sum_cost + (n_blk_cost - b_blk_cost) + m_cost
                # Calculate the new memory values
                n_sum_blk_mem = blk.sum_mem + tree.nodes[node][MEMORY]
                n_par_blk_mem = block_par_mem(pred, node, blk.w)
                # Calculate the new CPU need
                blk_cpu, blk_max_rate = block_cpu(pred, node, blk.max_rate, blk.cpu)
                qinsert(node, c_n, TBlock(blk.w, n_sum_cost, n_blk_cumsum, n_sum_blk_mem, n_par_blk_mem,
                                          blk_max_rate, blk_cpu))
        # If no feasible solution exists with c cuts -> add default with infinity cost
        if not DP[node][c_n]:
            DP[node][c_n].append(TBlock())

    def qclear(node: int, c_n: int):
        """Leave only the best/min subcase in the queue as the first element"""
        best_blk = DP[node][c_n][0]
        DP[node][c_n].clear()
        DP[node][c_n].append(best_blk)

    for p, n in ipostorder_dfs(tree, root):
        n_mem, n_rate = tree.nodes[n][MEMORY], tree[p][n][RATE]
        # Subcases of leaves can be precalculated to store the single block -> [n]
        if len(tree.succ[n]) < 1:
            sum_n_cost, n_cumsum = block_cost(p, n, 0)
            qinsert(n, 0, TBlock(n, sum_n_cost, n_cumsum, n_mem, n_rate, 1))
            continue
        # Sum best subcases of n's successors not involved in cpath
        sum_m_cost = sum(qmin(m, 0) for m in tree.succ[n] if m not in cpath)
        if n not in cpath:
            # Single block subcase -> [n] + sum(m): n -> m
            n_cost, n_cumsum = block_cost(p, n, 0)
            sum_n_cost = n_cost + sum_m_cost
            qinsert(n, 0, TBlock(n, sum_n_cost, n_cumsum, n_mem, n_rate, 1))
            # Merged subcases -> [n] U [b -> w] + sum(m): n -> b, n -> m, m != b
            for b in tree.succ[n]:
                qmerge(p, n, 0, b, 0, m_cost=sum_m_cost - qmin(b, 0))
                qclear(b, 0)
        else:
            # Cut subcase -> [n] + m_cp + sum(m\m_cp): n -> m, m != m_cp
            n_cost, n_cumsum = block_cost(p, n, 0)
            m_cp = next(m for m in tree.succ[n] if m in cpath)
            # Since n -> b is a cut, at most c_max-1 subcases should be referenced
            for c in range(1, min(len(DP[m_cp]), c_max) + 1):
                sum_n_cost = n_cost + sum_m_cost + qmin(m_cp, c - 1)
                qinsert(n, c, TBlock(n, sum_n_cost, n_cumsum, n_mem, n_rate, 1))
            # Merged subcases -> [n] U [b -> w] + sum(m\m_cp) + m_cp: n -> b, n -> m, m != b != m_cp
            for b in tree.succ[n]:
                if b == m_cp:
                    for c in range(0, min(len(DP[m_cp]), c_max + 1)):
                        qmerge(p, n, c, b, c, m_cost=sum_m_cost)
                        qclear(b, c)
                else:
                    m_res_cost = sum_m_cost - qmin(b, 0)
                    # Subcases of node b with 0 cut is reused to calculate subcases with different number of cuts
                    for c in range(1, min(len(DP[m_cp]), c_max) + 1):
                        qmerge(p, n, c, b, 0, m_cost=m_res_cost + qmin(m_cp, c - 1))
                    qclear(b, 0)
    c_opt = min(DP[root], key=lambda _c: qmin(root, _c))
    if qmin(root, c_opt) < math.inf:
        return extract_blocks(tree, DP, root, cp_end, c_opt, full), qmin(root, c_opt), c_opt
    else:
        return [], math.inf, c_opt


def extract_blocks(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                   DP: list[collections.defaultdict[int, collections.deque[TBlock]]],
                   root: int, cp_end: int, c_opt: int, full: bool = True) -> T_PART:
    """
    Extract subtree roots of partitioning from the tailing nodes stored in the *DP* matrix.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param DP:      dynamic programming structure storing intermediate *TBlock* subcases
    :param root:    root node of the graph
    :param cp_end:  tail node of the critical path
    :param c_opt:   calculated optimal cut size
    :param full:    calculate full blocks
    :return:        partitioning blocks
    """
    n = set(filter(lambda v: v is not PLATFORM, tree))
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    p = []
    barr = {(root, c_opt)}
    while len(n):
        b, c = barr.pop()
        w = DP[b][c][0].w
        blk, prior = [], None
        while prior != b:
            for m in tree.successors(w):
                if m != prior:
                    barr.add((m, c - 1) if m in cpath else (m, 0))
            if full:
                blk.append(w)
            n.remove(w)
            prior = w
            w = next(tree.predecessors(w))
        if blk[-1] != b:
            blk.append(b)
        blk.reverse()
        p.append(blk)
    return sorted(p)
