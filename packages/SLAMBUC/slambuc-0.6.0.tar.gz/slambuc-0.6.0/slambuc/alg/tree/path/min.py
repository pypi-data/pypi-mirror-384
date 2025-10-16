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
import typing

import networkx as nx

from slambuc.alg import INFEASIBLE, T_RESULTS, T_PART
from slambuc.alg.app import *
from slambuc.alg.util import ipostorder_dfs, ibacktrack_chain


class MinTBlock(typing.NamedTuple):
    """Store subtree attributes for a given min subcase."""
    w: int = None  # Tailing node of the first block of the subtree partitioning
    c: int = 0  # Number of cuts the given subtree partitioning introduce on the critical path
    sum_cost: int = math.inf  # Sum cost of the subtree partitioning
    cost: int = math.inf  # Cost of the first block (with tail node w) in the subtree partitioning
    sum_mem: int = math.inf  # Sum memory of the first block
    par_mem: int = math.inf  # Parallel memory of the first block
    max_rate: int = 0  # Maximum rate value of internal edge in the first block
    cpu: int = 1  # Sum CPU core need of the first block

    def __repr__(self):
        return repr(tuple(self))


def min_tree_partitioning(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                          M: int = math.inf, N: int = math.inf, L: int = math.inf, cp_end: int = None, delay: int = 1,
                          unit: int = 1, full: bool = True) -> T_RESULTS | tuple[list, None, int]:
    """
    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound **M** on the total
    memory of blocks and a latency constraint **L** defined on the subchain between *root* and *cp_end* nodes.

    Cost calculation relies on the rounding *unit* and number of vCPU cores *N*, whereas platform invocation *delay*
    is used for latency calculations.

    It gives an optimal result only in case the cost function regarding the chain attributes is subadditive,
    that is k_opt = k_min is guaranteed for each case.

    Instead of full partitioning, it only returns the list of barrier nodes.

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
    if cpath:
        # c_max is the number of cuts allowed by L or at most the number of edges on cpath
        c_max = math.floor(min((L - sum(tree.nodes[_v][RUNTIME] for _v in cpath)) / delay, len(cpath) - 1))
    else:
        # if cpath is undefined c_max = tree depth / number of possible edge cuts on the longest root-leaf chain
        c_max = max(len(list(ibacktrack_chain(tree, root, v))) - 1 for v in tree if not tree.succ[v])
    # Check lower bound for latency limit
    if c_max < 0:
        return [], None, c_max
    DP = [collections.deque((MinTBlock(),)) for _ in range(len(tree))]

    def qmin(node: int) -> MinTBlock:
        """Return the sum cost of best/min subcase for *node* with *c_n* cuts."""
        return DP[node][0]

    def qinsert(node: int, blk: MinTBlock):
        """Insert given block subcase *block* into *DP* for the *node* with *c_n* cuts."""
        if blk.sum_cost < math.inf and max(blk.sum_mem, blk.par_mem) <= M and blk.cpu <= N and blk.c <= c_max:
            if blk.sum_cost <= qmin(node).sum_cost:
                DP[node].appendleft(blk)
            else:
                DP[node].append(blk)

    def qmerge(pred: int, node: int, barr: int, m_cost: int, add_cut: bool = False):
        """
        Copy DP entries from queue of node *barr* with *c_b* cuts into queue of node *node* with *c_n* cuts
        while leaving the best subcase in the original queue.
        """
        blk = None
        while len(DP[barr]):
            blk = DP[barr].pop()
            # Ignore infeasible subcases
            if blk.sum_cost < math.inf:
                blk_cost = block_cost(pred, node, blk.w)
                sum_blk_cost = blk.sum_cost + (blk_cost - blk.cost) + m_cost
                sum_blk_cut = blk.c + 1 if add_cut else blk.c
                sum_blk_mem = blk.sum_mem + tree.nodes[node][MEMORY]
                par_blk_mem = block_par_mem(pred, node, blk.w)
                blk_max_rate = max(blk.max_rate, tree[pred][node][RATE])
                blk_cpu = max(blk.cpu, math.ceil(blk_max_rate / tree[pred][node][RATE]))
                qinsert(node, MinTBlock(blk.w, sum_blk_cut, sum_blk_cost, blk_cost, sum_blk_mem, par_blk_mem,
                                        blk_max_rate, blk_cpu))
        # Leave only the best/min subcase in the queue as the first element
        DP[barr].append(blk)

    def block_cost(pred: int, barr: int, w: int) -> int:
        """Calculate running time of block: p -> [barr -> w]."""
        sum_time = tree.nodes[w][RUNTIME]
        while w > barr:
            w = next(tree.predecessors(w))
            sum_time += tree.nodes[w][RUNTIME]
        return tree[pred][barr][RATE] * (math.ceil(sum_time / unit) * unit)

    def block_par_mem(pred: int, barr: int, w: int) -> int:
        """Calculate memory of block: p -> [barr -> w]."""
        _pred = next(tree.predecessors(w))
        mem_par = math.ceil(tree[_pred][w][RATE] / tree[pred][barr][RATE]) * tree.nodes[w][MEMORY]
        while w > barr:
            w, _pred = _pred, next(tree.predecessors(_pred))
            mem_par = max(mem_par, math.ceil(tree[_pred][w][RATE] / tree[pred][barr][RATE]) * tree.nodes[w][MEMORY])
        return mem_par

    for p, n in ipostorder_dfs(tree, root):
        n_mem, n_rate = tree.nodes[n][MEMORY], tree[p][n][RATE]
        # Subcases of leaves can be precalculated to store the single block -> [n]
        if len(tree.succ[n]) < 1:
            n_cost = block_cost(p, n, n)
            qinsert(n, MinTBlock(n, 0, n_cost, n_cost, n_mem, n_rate, 1))
            continue
        # Sum best subcases of n's successors not involved in cpath
        sum_m_cost = sum(qmin(m).sum_cost for m in tree.succ[n])
        if n not in cpath:
            # Single block subcase -> [n] + sum(m): n -> m
            n_cost = block_cost(p, n, n)
            qinsert(n, MinTBlock(n, 0, n_cost + sum_m_cost, n_cost, n_mem, n_rate, 1))
            # Merged subcases -> [n] U [b -> w] + sum(m): n -> b, n -> m, m != b
            for b in tree.succ[n]:
                qmerge(p, n, b, sum_m_cost - qmin(b).sum_cost, add_cut=False)
        else:
            # Cut subcase -> [n] + m_cp + sum(m\m_cp): n -> m, m != m_cp
            n_cost = block_cost(p, n, n)
            m_cp = next(m for m in tree.succ[n] if m in cpath)
            # Since n -> b is a cut, at most c_max-1 subcases should be referenced
            qinsert(n, MinTBlock(n, qmin(m_cp).c + 1, n_cost + sum_m_cost, n_cost, n_mem, n_rate, 1))
            # Merged subcases -> [n] U [b -> w] + sum(m\m_cp) + m_cp: n -> b, n -> m, m != b != m_cp
            for b in tree.succ[n]:
                qmerge(p, n, b, sum_m_cost - qmin(b).sum_cost, add_cut=True if b != m_cp else False)
    if qmin(root).sum_cost < math.inf:
        return extract_min_blocks(tree, DP, root, full), qmin(root).sum_cost, qmin(root).c
    else:
        return INFEASIBLE


def extract_min_blocks(tree: nx.DiGraph, DP: list[collections.deque[MinTBlock]],
                       root: int, full: bool = True) -> T_PART:
    """
    Extract subtree roots of partitioning from the tailing nodes stored in the *DP* matrix.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param DP:      dynamic programming structure storing intermediate *MinTBlock* subcases
    :param root:    root node of the graph
    :param full:    calculate full blocks
    :return:        partitioning blocks
    """
    n = set(filter(lambda v: v is not PLATFORM, tree))
    p = []
    barr = {root}
    while len(n):
        b = barr.pop()
        w = DP[b][0].w
        blk, prior = [], None
        while prior != b:
            for m in tree.succ[w]:
                if m != prior:
                    barr.add(m)
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
