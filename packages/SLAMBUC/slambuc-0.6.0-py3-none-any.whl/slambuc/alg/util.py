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
import itertools
import operator
from collections.abc import Generator

import networkx as nx
import pulp as lp

from slambuc.alg import T_PART, T_BARRS
from slambuc.alg.app.common import *


def verify_limits(tree: nx.DiGraph, cpath: set[int], M: int | float, L: int | float) -> tuple[bool, bool]:
    """
    Verify that given limits *M* and *L* based on the given *tree* allow feasible solution.

    :param tree:    input tree
    :param cpath:   nodes of critical path
    :param M:       memory upper bound
    :param L:       latency upper bound
    :return:        boolean values of satisfied limits M and L
    """
    return (max(tree.nodes[v][MEMORY] for v in tree if v is not PLATFORM) <= M,
            sum(tree.nodes[v][RUNTIME] for v in cpath) <= L)


def ipostorder_dfs(tree: nx.DiGraph, source: int | str, inclusive: bool = True) -> Generator[tuple[int, int]]:
    """
    Return the existing predecessor and node tuple in a DFS traversal of the given *tree* in a post/reversed order.

    :param tree:        input tree
    :param source:      starting node
    :param inclusive:   also returns the source node
    :return:            generator of tree nodes
    """
    stack = collections.deque([(source, iter(tree[source]))])
    while stack:
        v, ichildren = stack[-1]
        try:
            c = next(ichildren)
            stack.append((c, iter(tree[c])))
        except StopIteration:
            stack.pop()
            if stack:
                yield stack[-1][0], v
    if inclusive:
        yield next(tree.predecessors(source), None), source


def ipostorder_tabu_dfs(tree: nx.DiGraph, source: int, tabu: set[int] | dict[int, ...] = None,
                        inclusive: bool = True) -> Generator[tuple[int, int]]:
    """
    Return nodes of *tree* in a postorder DFS traversal excluding descendants of nodes in *tabu* set.

    :param tree:        input tree
    :param source:      starting node
    :param tabu:        tabu node set
    :param inclusive:   also returns the source node
    :return:            generator of tree nodes
    """
    stack = collections.deque([(source, iter(tree[source]))])
    while stack:
        v, ichildren = stack[-1]
        try:
            c = next(ichildren)
            if not tabu or c not in tabu:
                stack.append((c, iter(tree[c])))
        except StopIteration:
            stack.pop()
            if stack:
                yield stack[-1][0], v
    if inclusive:
        yield next(tree.predecessors(source), None), source


def ipostorder_edges(tree: nx.DiGraph, source: int,
                     data: bool = False) -> Generator[tuple[int, int] | tuple[int, int, ...]]:
    """
    Return the edges (head, tail) in a DFS traversal of the given *tree* in a post/reversed order with edge data.

    :param tree:        input tree
    :param source:      starting node
    :param data:        return edge data
    :return:            generator of edges
    """
    stack = collections.deque([(source, iter(tree[source]))])
    while stack:
        v, ichildren = stack[-1]
        try:
            c = next(ichildren)
            stack.append((c, iter(tree[c])))
        except StopIteration:
            stack.pop()
            if stack:
                p = stack[-1][0]
                if data:
                    yield p, v, tree[p][v]
                else:
                    yield p, v


def ileft_right_dfs(tree: nx.DiGraph,
                    source: int) -> Generator[tuple[tuple[int | None, int | None], int | None, tuple[int, int]]]:
    """
    Return edges in left-right traversal along with the previously visited uncle and sibling edges.

    :param tree:    input tree
    :param source:  starting node
    :return:        generator of interested nodes
    """
    # ... -> [u] -j-> [v] -i-> [v_i]  => [(u, u_j-1), v_i-1, v_succ, v, v_i]
    stack = collections.deque([[(None, None), None, iter(tree[source]), source, 0]])
    while stack:
        u_prev, v_prev, ichildren, v, v_i = stack[-1]
        yield u_prev, v_prev, (v, v_i)
        try:
            c = next(ichildren)
            stack[-1][1], stack[-1][-1] = v_i, c
            stack.append([(v, v_i), None, iter(tree[c]), c, 0])
        except StopIteration:
            stack.pop()


def ileft_right_dfs_idx(tree: nx.DiGraph, source: int) -> Generator[tuple[int, int]]:
    """
    Return nodes of the given *tree* in left-right traversal along with the index of the considered child node.

    :param tree:    input tree
    :param source:  starting node
    :return:        generator of interested node indices
    """
    # [v] -i-> [v_i]  => [v_succ, v, v_i]
    stack = collections.deque([[iter(tree[source]), source, 0]])
    while stack:
        ichildren, v, i = stack[-1]
        yield v, i
        try:
            c = next(ichildren)
            stack[-1][-1] += 1
            stack.append([iter(tree[c]), c, 0])
        except StopIteration:
            stack.pop()


def ichain(tree: nx.DiGraph, start: int, leaf: int) -> Generator[int]:
    """
    Generator over the nodes of the chain from *start* node to *leaf* node.

    :param tree:    input tree
    :param start:   first node
    :param leaf:    last node
    :return:        generator of chain nodes
    """
    n = start
    while n != leaf:
        yield n
        for c in tree.successors(n):
            if leaf in tree.nodes[c][LABEL]:
                n = c
                break
    yield leaf


def ibacktrack_chain(tree: nx.DiGraph, start: int, leaf: int) -> Generator[int]:
    """
    Return the node of a chain in the *tree* in backward order from *leaf* to *start* node.

    :param tree:    input tree
    :param start:   first node
    :param leaf:    last node
    :return:        generator of chain nodes
    """
    if leaf not in tree:
        return
    last = leaf
    while last != start:
        yield last
        try:
            last = next(tree.predecessors(last))
        except StopIteration:
            break
    yield last


def isubchains(tree: nx.DiGraph, start: int,
               leaf: int = None) -> Generator[tuple[tuple[list[int], list[int]], set[int]]]:
    """
    Generator over the subchains and its branches from *start* to all reachable leaf where the subchain is bisected
    at the last node from which the specific *leaf* is still reachable.

    :param tree:    input tree
    :param start:   first node
    :param leaf:    last node
    :return:        generator of chain node parts and branches
    """
    chain = [start]
    while (deg := len(tree.succ[chain[-1]])) == 1:
        chain.append(next(tree.successors(chain[-1])))
    if deg == 0:
        yield (chain, []), set()
    else:
        for c in (children := set(tree.successors(chain[-1]))):
            nbr = children - {c}
            for (part1, part2), branches in isubchains(tree, c, leaf):
                if leaf in tree.nodes[part1[0]][LABEL]:
                    yield (chain + part1, part2), nbr | branches
                elif leaf is not None:
                    yield (chain, part1 + part2), nbr | branches
                else:
                    yield (chain + part1, []), nbr | branches


def iflattened_tree(tree: nx.DiGraph, root: int) -> Generator[list[int]]:
    """
    Generate chain decomposition of the given *tree* started from node *root*.

    :param tree:    input tree
    :param root:    root node
    :return:        generator of decomposed chains
    """
    for (head, tail), brs in isubchains(tree, root, max(tree.nodes[root][LABEL])):
        chain, brs = [head + tail], sorted(brs)
        for subchains in itertools.product(*map(functools.partial(iflattened_tree, tree), brs)):
            yield list(itertools.chain(chain, *subchains))


def isubtree_bfs(tree: nx.DiGraph, source: int, inclusive: bool = True) -> Generator[int]:
    """
    Return nodes in BFS traversal of the given *tree* started from *root*.

    :param tree:        input tree
    :param source:        root node
    :param inclusive:   also returns the source node
    :return:            generator of tree nodes
    """
    children = collections.deque((source,))
    if inclusive:
        yield source
    while children:
        u = children.popleft()
        for v in tree.successors(u):
            children.append(v)
            yield v


def isubtrees(tree: nx.DiGraph, barrs: T_BARRS) -> Generator[tuple[int, list[int]]]:
    """
    Return the barrier nodes and subtrees of the given *tree* marked by the *barr* nodes.

    :param tree:    input tree
    :param barrs:   set of barrier nodes
    :return:        generator of barrier and regarding subtree nodes
    """
    for b in barrs:
        nodes = [b]
        children = collections.deque(nodes)
        while children:
            u = children.popleft()
            for v in tree.successors(u):
                if v not in barrs:
                    nodes.append(v)
                    children.append(v)
        nodes.sort()
        yield b, nodes


def itop_subtree_nodes(tree: nx.DiGraph, root: int, barrs: T_BARRS) -> Generator[int]:
    """
    Return the nodes of the top subtree with *root* of the given *tree* cut by the *barr* nodes.

    :param tree:    input tree
    :param root:    root node
    :param barrs:   set of barrier nodes
    :return:        generator of topmost block's nodes
    """
    nodes = [root]
    children = collections.deque(nodes)
    while children:
        u = children.popleft()
        for v in tree.successors(u):
            if v not in barrs:
                children.append(v)
                yield v


def induced_subtrees(tree: nx.DiGraph, root: int,
                     only_nodes: bool = False) -> Generator[tuple[tuple[int, int], list[int | tuple[int]]]]:
    """
    Recursively generate the ingress edge of subtrees and all reachable edges / nodes in the given subtree.

    :param tree:        input tree
    :param root:        root node
    :param only_nodes:  returns only subtree nodes instead of edges
    :return:            generator of ingress and covered edges
    """
    subtrees = collections.defaultdict(list)
    for p, n in ipostorder_dfs(tree, root, inclusive=True):
        base = (n,) if only_nodes else ((n, s) for s in tree.successors(n))
        subtrees[n].extend(itertools.chain(base, *(subtrees[c] for c in tree.successors(n))))
        for c in tree.successors(n):
            del subtrees[c]
        yield (p, n), subtrees[n]


def ihierarchical_edges(dag: nx.DiGraph, source: int) -> Generator[list[int]]:
    """
    Generate subgraph edges based on the hierarchical levels of BFS traversal.

    :param dag:     input DAG graph
    :param source:  source node
    :return:        generator of subgraph edges
    """
    level = collections.deque((source,))
    visited = set()
    while level:
        children = []
        while level:
            u = level.popleft()
            if u in visited:
                continue
            visited.add(u)
            for v in dag.successors(u):
                children.append((u, v))
        if children:
            yield children
        level.extend({v for _, v in children})


def ihierarchical_nodes(dag: nx.DiGraph, source: int | str) -> Generator[tuple[int, ...]]:
    """
    Generate subgraph nodes based on the hierarchical levels of BFS traversal.

    :param dag:     input DAG graph
    :param source:  source node
    :return:        generator of subgraph nodes
    """
    level = collections.deque((source,))
    visited = set()
    while level:
        children = set()
        yield tuple(level)
        while level:
            u = level.popleft()
            for v in dag.succ[u]:
                if v not in visited:
                    children.add(v)
        level.extend(children)
        visited.update(children)


def isubgraph_bfs(dag: nx.DiGraph, source: int, inclusive: bool = True) -> Generator[int]:
    """
    Return nodes in BFS traversal of the given *DAG* graph started from *root* without node revisiting.

    :param dag:         input tree
    :param source:      root node
    :param inclusive:   also returns the source node
    :return:            generator of tree nodes
    """
    children = collections.deque((source,))
    visited = set()
    if inclusive:
        yield source
    while children:
        u = children.popleft()
        for v in dag.successors(u):
            if v not in visited:
                children.append(v)
                yield v
        visited.update(children)


def iclosed_subgraph(dag: nx.DiGraph, source: int, inclusive: bool = True) -> Generator[int]:
    """
    Generate subgraph nodes that have ingress edges from inside the subgraph.

    :param dag:         input DAG graph
    :param source:      source node
    :param inclusive:   also returns the source node
    :return:            generator of subgraph nodes
    """
    children = collections.deque((source,))
    visited = {source}
    if inclusive:
        yield source
    while children:
        u = children.popleft()
        for v in dag.successors(u):
            if v not in visited and set(dag.predecessors(v)) <= visited:
                children.append(v)
                visited.add(v)
                yield v


def ipowerset(data: typing.Iterable[int] | typing.Sized, start: int = 0) -> Generator[list[int]]:
    """
    Generate the powerset of the given *data* beginning to count the sets from size *start*.

    :param data:    list of data values
    :param start:   lower bound of set size
    :return:        generator of subsets
    """
    return itertools.chain.from_iterable(itertools.combinations(data, i) for i in range(start, len(data) + 1))


def iser_mul_factor(rate: typing.Iterable[int]) -> itertools.accumulate:
    """
    Generator over the **pessimistic** number of function instances inside a block assuming a serialized execution
     model.

    :param rate:    list of rate values
    :return:        generator of accumulated function instance counts
    """
    return itertools.accumulate((math.ceil(j / i) for i, j in itertools.pairwise(rate)), operator.mul, initial=1)


def ipar_mul_factor(rate: typing.Iterable[int], N: int = 1) -> itertools.accumulate:
    """
    Generator over the **pessimistic** number of function instances inside a block assuming a parallelized execution
     model.

    :param rate:    list of rate values
    :param N:       CPU count
    :return:        generator of accumulated function instance counts
    """
    return itertools.accumulate((math.ceil(j / (i * N)) for i, j in itertools.pairwise(rate)), operator.mul, initial=1)


def igen_mul_factor(rate: list[int], ncores: list[int]) -> itertools.accumulate:
    """
    Generator over the **pessimistic** number of function instances using separate relative CPU cores.

    :param rate:    list of rate values
    :param ncores:  list of CPU cores
    """
    return itertools.accumulate((math.ceil(j / (i * nc)) for (i, j), nc in zip(itertools.pairwise(rate), ncores)),
                                operator.mul, initial=1)


########################################################################################################################


def leaf_label_nodes(tree: nx.DiGraph) -> nx.DiGraph:
    """
    Label each node *n* with the set of leafs that can be reached from *n*.

    :param tree:    input tree
    :return:        labeled tree
    """
    for _, v in ipostorder_dfs(tree, PLATFORM, inclusive=False):
        tree.nodes[v][LABEL] = set().union(*(tree.nodes[s][LABEL] for s in tree.succ[v])) if len(tree.succ[v]) else {v}
    return tree


def ith_child(tree: nx.DiGraph, v: int, i: int) -> int:
    """
    Returns the *i*-th child of the node *v* started to count from 1.

    E.g.:
    >>> v_i = ith_child(tree, v, i) # [v] -i-> [v_i]

    :param tree:    input tree
    :param v:       node ID
    :param i:       number of given child
    :return:        i-th node
    """
    return next(itertools.islice(tree.successors(v), i - 1, None)) if i > 0 else 0


def child_idx(tree: nx.DiGraph, v: int) -> int:
    """
    Returns the index of *v* among its sibling nodes or return 0.

    E.g.:
    >>> j = child_idx(tree, v) # [u] -j-> [v]

    :param tree:    input tree
    :param v:       node ID
    :return:        index of node *v*
    """
    return next((i for i, v_i in enumerate(tree.succ[next(tree.predecessors(v))], 1) if v_i == v)) if v else 0


def top_subtree_block(tree: nx.DiGraph, barr: T_BARRS) -> nx.Graph:
    """
    Return the first/top subtree of the given *tree* separated by the given *barr* nodes.

    :param tree:    input tree
    :param barr:    set of barrier nodes
    :return:        top subtree
    """
    return tree.subgraph(next(isubtrees(tree, sorted(barr)))[1])


def path_blocks(partition: T_PART, path: typing.Iterable[int]) -> T_PART:
    """
    Calculate the blocks of separated critical path based on the original partitioning.

    :param partition:   given tree partitioning
    :param path:        path of specific nodes
    :return:            calculated path blocks
    """
    parts = []
    current_blk = None
    for v in path:
        for blk in partition:
            if v in blk:
                if blk == current_blk:
                    parts[-1].append(v)
                else:
                    parts.append([v])
                    current_blk = blk
    return parts


def recreate_subchain_blocks(tree: nx.DiGraph, barr: T_BARRS) -> T_PART:
    """
    Recreate chain blocks from barrier nodes of the given partitioning.

    :param tree:    input tree
    :param barr:    set of barrier nodes
    :return:        list of chain blocks
    """
    n = list(tree.nodes)
    p = []
    if not barr:
        return []
    for w in reversed(range(1, len(n))):
        if n[w] == 0:
            continue
        n[w], blk, v = 0, [w], w
        while v not in barr:
            v = next(tree.predecessors(v))
            if n[v]:
                n[v] = 0
                blk.append(v)
        blk.reverse()
        p.append(blk)
    return sorted(p)


def recreate_subtree_blocks(tree: nx.DiGraph, barr: T_BARRS) -> T_PART:
    """
    Return the partition blocks of the given *tree* cut by the *barr* nodes.

    :param tree:    input tree
    :param barr:    set of barrier nodes
    :return:        list of partition blocks
    """
    p = []
    for b in barr:
        blk = [b]
        c = collections.deque(blk)
        while c:
            u = c.popleft()
            for v in tree.successors(u):
                if v not in barr:
                    blk.append(v)
                    c.append(v)
        p.append(blk)
    return sorted(p)


def split_chain(barr: T_BARRS, n: int, full: bool = True) -> T_PART:
    """
    Recreate partition blocks from barrier nodes for an *n*-size chain := [0, n-1].

    :param barr:    set of barrier nodes
    :param n:       chain size
    :param full:    recreate all block nodes instead of just fist/last nodes
    :return:        created partitioning
    """
    return [list(range(b, w)) if full else [b, w - 1] if b < w - 1 else [b]
            for b, w in itertools.pairwise(barr + [n])]


def split_path(path: list[int], barr: T_BARRS) -> T_PART:
    """
    Recreate partition blocks of a chain from barrier nodes for an *n*-size chain := [0, n-1].

    :param path:    list of nodes
    :param barr:    set of barrier nodes
    :return:        created partitioning
    """
    return [path[b: w] for b, w in itertools.pairwise(barr + [len(path)])]


def x_eval(x: int | None | lp.LpVariable) -> bool:
    """
    Evaluate *x* from a decision variable matrix based on its solution value.

    :param x:   decision variable
    :return:    whether it is a solution or not
    """
    return bool(round(x.varValue) if isinstance(x, lp.LpVariable) else x)


def recalculate_ser_partitioning(tree: nx.DiGraph, partition: T_PART, root: int = 1, cp_end: int = None,
                                 delay: int = 1) -> tuple[int, int]:
    """
    Calculate the sum cost and sum latency on the critical path based on the given *partition* assuming a serialized
    execution model.

    :param tree:        input tree
    :param partition:   given partitioning
    :param root:        root node
    :param cp_end:      end node of critical path
    :param delay:       platform invocation delay
    :return:            sum cost nad latency of the given partitioning
    """
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    c_blks = [blk for blk in partition if blk[0] in cpath]
    return (sum(ser_subtree_cost(tree, blk[0], blk) for blk in partition),
            sum(ser_subchain_latency(tree, blk[0], set(blk), cpath) for blk in c_blks) + (len(c_blks) - 1) * delay)


def recalculate_partitioning(tree: nx.DiGraph, partition: T_PART, root: int = 1, N: int = 1, cp_end: int = None,
                             delay: int = 1) -> tuple[int, int]:
    """
    Calculate sum cost and sum latency on the critical path based on the given *partition* assuming a parallelized
    execution model.

    :param tree:        input tree
    :param partition:   given partitioning
    :param root:        root node
    :param N:           CPU count
    :param cp_end:      end node of critical path
    :param delay:       platform invocation delay
    :return:            sum cost nad latency of the given partitioning
    """
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    c_blks = [blk for blk in partition if blk[0] in cpath]
    return (sum(par_subtree_cost(tree, min(blk), blk, N) for blk in partition),
            sum(par_subchain_latency(tree, blk[0], set(blk), cpath, N) for blk in c_blks) + (len(c_blks) - 1) * delay
            if cpath else None)


########################################################################################################################


def chain_memory(memory: list[int], b: int, w: int) -> int:
    """
    Calculate cumulative memory of block [b, w].

    :param memory:  list of memory values
    :param b:       barrier node
    :param w:       end node of block
    :return:        memory value
    """
    return sum(itertools.islice(memory, b, w + 1))


def chain_memory_opt(memory: list[int], rate: list[int], b: int, w: int) -> int:
    """
    Calculate cumulative memory of block [b, w] based on the **optimistic** number of parallel function instances.

    :param memory:  list of memory values
    :param rate:    list of rate values
    :param b:       barrier node
    :param w:       end node of block
    :return:        memory value
    """
    return max(sum(itertools.islice(memory, b, w + 1)),
               functools.reduce(lambda pre, i: max(pre, max(math.ceil(rate[j] / rate[i]) * memory[j]
                                                            for j in range(i, w + 1))), reversed(range(b, w + 1)), 0))


def chain_cpu(rate: list[int], b: int, w: int) -> int:
    """
    Calculate CPU core need of block [b, w] with multiprocessing.

    :param rate:    list of rate values
    :param b:       barrier node
    :param w:       end node of block
    :return:        CPU count
    """
    # noinspection PyTypeChecker
    r_max = itertools.chain((1,), enumerate(itertools.accumulate(reversed(rate[b: w + 1]), max)))
    return functools.reduce(lambda pre, max_i: max(pre, math.ceil(max_i[1] / rate[w - max_i[0]])), r_max)


def chain_cost(runtime: list[int], rate: list[int], b: int, w: int, unit: int = 1) -> int:
    """
    Calculate running time of block [b, w] with multiprocessing.

    :param runtime: list of runtime values
    :param rate:    list of rate values
    :param b:       barrier node
    :param w:       end node of block
    :param unit:    rounding unit
    :return:        calculated cost
    """
    return rate[b] * (math.ceil(sum(runtime[b: w + 1]) / unit) * unit)


def chain_latency(runtime: list[int], b: int, w: int, delay: int | float, start: int, end: int) -> int:
    """
    Calculate relevant latency for block [b, w] with multiprocessing.

    :param runtime: list of runtime values
    :param b:       barrier node
    :param w:       end node of block
    :param delay:   platform delay
    :param start:   fist node to consider
    :param end:     last node to consider
    :return:        calculated latency value
    """
    if end < b or w < start:
        # Do not consider latency if no intersection
        return 0
    blk_lat = sum(runtime[max(b, start): min(w, end) + 1])
    # Ignore delay if the latency path starts within the subchain
    return delay + blk_lat if start < b else blk_lat


########################################################################################################################


def pblock_memory(memory: list[int]) -> int:
    """
    Calculate cumulative memory of block [b, w] with serialization.

    :param memory:  list of memory values
    :return:        memory value
    """
    return sum(memory)


def pblock_memory_opt(memory: list[int], rate: list[int], b: int, w: int) -> int:
    """
    Calculate memory of block [b, w] recursively based on the **optimistic** number of parallel function instances.

    :param memory:  list of memory values
    :param rate:    list of rate values
    :param b:       barrier node
    :param w:       end node of block
    :return:        calculated memory value
    """
    return functools.reduce(lambda pre, i: max(pre, max(math.ceil(rate[j] / rate[i]) * memory[j]
                                                        for j in range(i, w + 1))), reversed(range(b, w + 1)), 0)


def pblock_memory_pes(memory: list[int], rate: list[int], b: int, w: int) -> int:
    """
    Calculate memory of block [b, w] recursively based on the **pessimistic** number of parallel function instances.

    :param memory:  list of memory values
    :param rate:    list of rate values
    :param b:       barrier node
    :param w:       end node of block
    :return:        calculated memory value
    """
    return functools.reduce(lambda pre, i: max(memory[i], math.ceil(rate[i + 1] / rate[i]) * pre),
                            reversed(range(b, w)), memory[w])


def pblock_memory_pes2(memory: list[int], rate: list[int], b: int, w: int) -> int:
    """
    Calculate memory of block [b, w] directly based on the **pessimistic** number of parallel function instances.

    :param memory:  list of memory values
    :param rate:    list of rate values
    :param b:       barrier node
    :param w:       end node of block
    :return:        calculated memory value
    """
    n_k = itertools.accumulate((math.ceil(rate[i + 1] / rate[i]) for i in range(b, w)), operator.mul, initial=1)
    return max(n * memory[b + k] for k, n in enumerate(n_k))


def pblock_cost(runtime: list[int], rate: list[int], data: list[int]) -> int:
    """
    Calculate running time of a subtree block with serialization.

    :param runtime: list of runtime values
    :param rate:    list of rate values
    :param data:    list of data values
    :return:        calculated cost
    """
    # return rate[b] * (data[b] + sum([(rate[i] / rate[b]) * runtime[i] for i in range(b, w + 1)]))
    return sum((r * t for r, t in zip(rate, runtime)), start=rate[0] * data[0])


def pblock_latency(runtime: list[int], rate: list[int], data: list[int]) -> int:
    """
    Calculate the relevant latency of a subtree block with serialization.

    :param runtime: list of runtime values
    :param rate:    list of rate values
    :param data:    list of data values
    :return:        calculated latency
    """
    return sum((n * t for n, t in zip(iser_mul_factor(rate), runtime)), start=data[0])


########################################################################################################################


def ser_chain_submemory(memory: list[int], b: int, w: int) -> int:
    """
    Calculate cumulative memory of **chain block** [b, w] with serialization and data fetching/caching.

    :param memory:  list of memory values
    :param b:       barrier node
    :param w:       end node of block
    :return:        calculated memory value
    """
    return sum(itertools.islice(memory, b, w + 1))


def ser_chain_subcost(runtime: list[int], rate: list[int], data: list[int], b: int, w: int) -> int:
    """
    Calculate running time of a **chain block** [b, w] with serialization and data fetching/caching.

    :param runtime: list of runtime values
    :param rate:    list of rate values
    :param data:    list of data values
    :param b:       barrier node
    :param w:       end node of block
    :return:        calculated cost
    """
    cost = sum((r * t for r, t in zip(itertools.islice(rate, b, w + 1),
                                      itertools.islice(runtime, b, w + 1))), start=rate[b] * data[b])
    return cost + rate[w + 1] * data[w + 1] if w < len(data) - 1 else cost


def ser_chain_sublatency(runtime: list[int], rate: list[int], data: list[int], b: int, w: int, delay: int | float,
                         start: int, end: int) -> int:
    """
    Calculate relevant latency for **chain block** [b,w] with serialization and data fetching/caching.

    :param runtime: list of runtime values
    :param rate:    list of rate values
    :param data:    list of data values
    :param b:       barrier node
    :param w:       end node of block
    :param delay:   platform delay
    :param start:   first node to consider
    :param end:     last node to consider
    :return:        calculated latency
    """
    if end < b or w < start:
        # Do not consider latency if there is no intersection
        return 0
    # Calculate data fetching and caching
    rw_data = [0] * len(range(b, w + 1))
    rw_data[0] += data[b]
    # w is no leaf
    rw_data[-1] += data[w + 1] if w != len(data) - 1 else 0
    e = min(w, end) + 1
    blk_lat = sum(n * (t + d) for i, n, t, d in zip(range(b, e),
                                                    iser_mul_factor(itertools.islice(rate, b, e)),
                                                    itertools.islice(runtime, b, e),
                                                    rw_data)
                  if start <= i)
    # Ignore delay if the latency path starts within the subchain
    return delay + blk_lat if start < b else blk_lat


########################################################################################################################


def ser_subtree_memory(tree: nx.DiGraph, nodes: typing.Iterable[int]) -> int:
    """
    Calculate cumulative memory of a subtree.

    :param tree:    input tree
    :param nodes:   set of block nodes
    :return:        calculated memory
    """
    return sum(tree.nodes[v][MEMORY] for v in nodes)


def ser_subtree_cost(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                     barr: int, nodes: typing.Iterable[int]) -> int:
    """
    Calculate the running time of a **subtree** with serialization and data fetching/caching.

    :param tree:    input tree
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :return:        calculated cost
    """
    p = next(tree.predecessors(barr))
    return sum((tree[next(tree.predecessors(v))][v][RATE] * tree.nodes[v][RUNTIME] +
                sum(vs[RATE] * vs[DATA] for s, vs in tree.succ[v].items() if s not in nodes)
                for v in nodes), start=tree[p][barr][RATE] * tree[p][barr][DATA])


def ser_pes_subchain_latency(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                             barr: int, nodes: set[int], cpath: set[int]) -> int:
    """
    Calculate relevant latency of **chain** in a group of **nodes** with serialization and **pessimistic** caching.

    :param tree:    input tree
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param cpath:   critical path nodes
    :return:        calculated latency
    """
    if not (subchain := sorted(nodes & cpath)):
        return 0
    p = next(tree.predecessors(barr))
    # Sum the instance number * runtime execution time + caching overhead of all block-egress edges
    return sum((n_v * (tree.nodes[v][RUNTIME] + sum(math.ceil(vs[RATE] / tree[u][v][RATE]) * vs[DATA]
                                                    for s, vs in tree.succ[v].items() if s not in nodes))
                for n_v, (u, v) in zip(iser_mul_factor(tree[i][j][RATE] for i, j in itertools.pairwise([p, *subchain])),
                                       itertools.pairwise([p, *subchain]))), start=tree[p][barr][DATA])


def ser_subchain_latency(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                         barr: int, nodes: set[int], cpath: set[int]) -> int:
    """
    Calculate relevant latency of **chain** in a group of **nodes** with serialization and data fetching/caching.

    :param tree:    input tree
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param cpath:   critical path nodes
    :return:        calculated latency
    """
    if barr not in cpath:
        return 0
    chain = sorted(nodes & cpath)
    # Get next cpath node following the given group
    cb = next(filter(lambda v: v in cpath, tree.successors(chain[-1])), None)
    p = next(tree.predecessors(barr))
    return sum(((n_v * tree.nodes[v][RUNTIME] +
                 (n_v * math.ceil(tree[v][cb][RATE] / tree[u][v][RATE]) * tree[v][cb][DATA]
                  if v == chain[-1] and cb is not None else 0))
                for n_v, (u, v) in zip(iser_mul_factor(tree[i][j][RATE] for i, j in itertools.pairwise([p, *chain])),
                                       itertools.pairwise([p, *chain]))), start=tree[p][barr][DATA])


########################################################################################################################


def par_inst_count(r_barr: int, r_v: int, N: int = 1) -> int:
    """
    Calculate instance number of a function considering the function/barrier rates and CPU count *N*.

    :param r_barr:  barrier node's ingress rate
    :param r_v:     call rate of node v
    :param N:       CPU count
    :return:        calculated instance count of node v
    """
    rel_r_v, sat_insts = r_v / r_barr, r_v % r_barr
    return sat_insts * math.ceil(math.ceil(rel_r_v) / N) + (r_barr - sat_insts) * math.ceil(math.floor(rel_r_v) / N)


def par_subtree_memory(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                       barr: int, nodes: list[int] | set[int], N: int = 1) -> int:
    """
    Calculate memory demand of a subtree as the sum of cumulative and parallel execution components.

    :param tree:    input tree
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param N:       CPU count
    :return:        calculated memory value
    """
    r_b = tree[next(tree.predecessors(barr))][barr][RATE]
    return max(sum(tree.nodes[v][MEMORY] for v in nodes),
               max((min(math.ceil(tree[next(tree.predecessors(v))][v][RATE] / r_b), N) * tree.nodes[v][MEMORY]
                    for v in nodes), default=0))


def par_subtree_cost(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                     barr: int, nodes: typing.Iterable[int], N: int = 1) -> int:
    """
    Calculate the running time of a **subtree** with multiprocessing and data fetching/caching.

    :param tree:    input tree
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param N:       CPU count
    :return:        calculated cost
    """
    p = next(tree.predecessors(barr))
    r_b = tree[p][barr][RATE]
    return sum((par_inst_count(r_b, tree[next(tree.predecessors(v))][v][RATE], N) * tree.nodes[v][RUNTIME] +
                sum(par_inst_count(r_b, vs[RATE], N) * vs[DATA] for s, vs in tree.succ[v].items() if s not in nodes)
                for v in nodes), start=r_b * tree[p][barr][DATA])


def par_subchain_latency(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                         barr: int, nodes: set[int], cpath: set[int], N: int = 1) -> int:
    """
    Calculate relevant latency of **chain** in a group of **nodes** with serialization and data fetching/caching.

    :param tree:    input tree
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param cpath:   critical path nodes
    :param N:       CPU count
    :return:        calculated latency
    """
    if barr not in cpath:
        return 0
    chain = sorted(nodes & cpath)
    # Get the next cpath node following the given group
    cb = next(filter(lambda v: v in cpath, tree.successors(chain[-1])), None)
    p = next(tree.predecessors(barr))
    return sum(((n_v * tree.nodes[v][RUNTIME] +
                 (n_v * math.ceil(tree[v][cb][RATE] / (tree[u][v][RATE] * N)) * tree[v][cb][DATA]
                  if v == chain[-1] and cb is not None else 0))
                for n_v, (u, v) in zip(ipar_mul_factor((tree[i][j][RATE]
                                                        for i, j in itertools.pairwise([p, *chain])), N),
                                       itertools.pairwise([p, *chain]))), start=tree[p][barr][DATA])


########################################################################################################################


def gen_subtree_memory(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                       barr: int, nodes: set[int], N: int = 1) -> int:
    """
    Calculate memory demand of a subtree as the sum of cumulative and parallel execution components.

    :param tree:    input tree
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param N:       CPU count
    :return:        calculated memory value
    """
    r_b = tree[next(tree.predecessors(barr))][barr][RATE]
    return max(sum(tree.nodes[v][MEMORY] for v in nodes),
               max(min(math.ceil(tree[next(tree.predecessors(v))][v][RATE] / r_b),
                       # In general, the max number of running instance can be bounded in threadpools
                       math.ceil(N / tree.nodes[v].get(CPU, 1))) * tree.nodes[v][MEMORY] for v in nodes))


def gen_subtree_cost(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                     barr: int, nodes: set[int], N: int = 1,
                     exec_calc: collections.abc.Callable[[int, int, int], int] = lambda i, t, n: t) -> int:
    """
    Calculate running time of a **subtree** with multiprocessing and data fetching/caching while using *exec_calc*
    callable to recalculate function execution time based on the function's id (i), reference runtime (t) and available
    CPU cores (n).

    :param tree:        input tree
    :param barr:        barrier node
    :param nodes:       set of block nodes
    :param N:           CPU count
    :param exec_calc:   calculator function
    :return:            calculated cost
    """
    p = next(tree.predecessors(barr))
    r_b = tree[p][barr][RATE]
    return sum((par_inst_count(r_b, tree[next(tree.predecessors(v))][v][RATE], int(N / tree.nodes[v].get(CPU, 1))) *
                exec_calc(v, tree.nodes[v][RUNTIME], N) +
                sum(par_inst_count(r_b, vs[RATE], N) * vs[DATA] for s, vs in tree.succ[v].items() if s not in nodes)
                for v in nodes), start=r_b * tree[p][barr][DATA])


def gen_subchain_latency(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                         barr: int, nodes: set[int], cpath: set[int], N: int = 1,
                         exec_calc: collections.abc.Callable[[int, int, int], int] = lambda i, t, n: t) -> int:
    """
    Calculate relevant latency of **chain** in a group of **nodes** with serialization and data fetching/caching while
    using *exec_calc* callable to recalculate function execution time based on the function's id (i), reference runtime
    (t) and available CPU cores (n).

    :param tree:        input tree
    :param barr:        barrier node
    :param nodes:       set of block nodes
    :param cpath:       critical path nodes
    :param N:           CPU count
    :param exec_calc:   calculator function
    :return:            calculated latency
    """
    if barr not in cpath:
        return 0
    chain = sorted(nodes & cpath)
    # Get the next cpath node following the given group
    cb = next(filter(lambda _v: _v in cpath, tree.successors(chain[-1])), None)
    p = next(tree.predecessors(barr))
    return sum(((n_v * exec_calc(v, tree.nodes[v][RUNTIME], int(N / tree.nodes[v].get(CPU, 1))) +
                 (n_v * math.ceil(tree[v][cb][RATE] / (tree[u][v][RATE] * N)) * tree[v][cb][DATA]
                  if v == chain[-1] and cb is not None else 0))
                for n_v, (u, v) in zip(igen_mul_factor(*zip(*((tree[i][j][RATE], int(N / tree.nodes[j].get(CPU, 1)))
                                                              for i, j in itertools.pairwise([p, *chain])))),
                                       itertools.pairwise([p, *chain]))), start=tree[p][barr][DATA])


########################################################################################################################

def par_subgraph_cost(dag: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                      barr: int, nodes: typing.Iterable[int], N: int = 1) -> int:
    """
    Calculate the running time of a **subgraph** with multiprocessing and data fetching/caching.

    :param dag:     input DAG graph
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param N:       CPU count
    :return:        calculated cost
    """
    R_b = sum(dag[p][barr][RATE] for p in dag.predecessors(barr))
    return sum((par_inst_count(R_b, sum(dag[p][v][RATE] for p in dag.predecessors(v)), N) * dag.nodes[v][RUNTIME] +
                sum(par_inst_count(R_b, dag[v][vs][RATE], N) * dag[v][vs][DATA]
                    for vs in dag.successors(v) if vs not in nodes)
                for v in nodes),
               start=sum(dag[p][barr][RATE] * dag[p][barr][DATA] for p in dag.predecessors(barr)))


def par_subgraph_latency(dag: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                         barr: int, nodes: set[int], cpath: set[int], N: int = 1) -> int:
    """
    Calculate relevant latency of **chain** in a group of **nodes** with serialization and data fetching/caching.

    :param dag:     input tree
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param cpath:   critical path nodes
    :param N:       CPU count
    :return:        calculated latency
    """
    if barr not in cpath:
        return 0
    chain = sorted(nodes & cpath)
    # Get the next cpath node following the given group
    cb = next(filter(lambda _v: _v in cpath, dag.successors(chain[-1])), None)
    pb = next(filter(lambda _p: _p in cpath or _p is PLATFORM, dag.predecessors(barr)), None)
    return sum(((n_v * dag.nodes[v][RUNTIME] +
                 (n_v * math.ceil(dag[v][cb][RATE] / (dag[u][v][RATE] * N)) * dag[v][cb][DATA]
                  if v == chain[-1] and cb is not None else 0))
                for n_v, (u, v) in zip(ipar_mul_factor((dag[i][j][RATE]
                                                        for i, j in itertools.pairwise([pb, *chain])), N),
                                       itertools.pairwise([pb, *chain]))),
               start=dag[pb][barr][DATA])


def par_subgraph_memory(dag: nx.DiGraph, barr: int, nodes: list[int] | set[int], N: int = 1) -> int:
    """
    Calculate memory demand of a **subgraph** as the sum of cumulative and parallel execution components.

    :param dag:     input DAG graph
    :param barr:    barrier node
    :param nodes:   set of block nodes
    :param N:       CPU count
    :return:        calculated memory value
    """
    R_b = sum(dag[p][barr][RATE] for p in dag.pred[barr])
    return max(sum(dag.nodes[v][MEMORY] for v in nodes),
               max(min(math.ceil(sum(dag[p][v][RATE] for p in dag.predecessors(v)) / R_b), N) * dag.nodes[v][MEMORY]
                   for v in nodes))
