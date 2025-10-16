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
import os
import pathlib
import subprocess
import tempfile

import networkx as nx
import pulp
import tabulate

from slambuc.alg import LP_LAT, T_PART, T_BARRS, T_FPART
from slambuc.alg.app.common import *
from slambuc.alg.util import (ichain, path_blocks, chain_memory, chain_cost, chain_latency, leaf_label_nodes,
                              chain_cpu, ser_chain_subcost, ser_chain_sublatency, ser_subtree_cost,
                              ser_subchain_latency, par_subtree_cost, par_subchain_latency,
                              chain_memory_opt, ser_chain_submemory, par_subgraph_cost, par_subgraph_latency,
                              par_subgraph_memory, ibacktrack_chain)


def get_cplex_path() -> str:
    """
    Return local CPLEX path.

    :return: path
    """
    if cplex_path := subprocess.run(['which', 'cplex'], stdout=subprocess.PIPE).stdout.decode().strip():
        return cplex_path
    cplex_path = pathlib.Path(os.environ.get('CPLEX_HOME', '~/Programs/ibm/ILOG/CPLEX_Studio2211/cplex'),
                              'bin/x86-64_linux/cplex').expanduser()
    return str(cplex_path) if cplex_path.exists() else None


def get_cpo_path() -> str:
    """
    Return local CPO path.

    :return: path
    """
    if cpo_path := subprocess.run(['which', 'cpoptimizer'], stdout=subprocess.PIPE).stdout.decode().strip():
        return cpo_path
    cpo_path = pathlib.Path(os.environ.get('CPO_HOME', '~/Programs/ibm/ILOG/CPLEX_Studio2211/cpoptimizer'),
                            'bin/x86-64_linux/cpoptimizer').expanduser()
    return str(cpo_path) if cpo_path.exists() else None


def get_glpk_path() -> str | None:
    """
    Return local GLPK path.

    :return: path
    """
    if glpk_path := subprocess.run(['which', 'glpsol'], stdout=subprocess.PIPE).stdout.decode().strip():
        return glpk_path
    else:
        return None


def is_compatible(tree1: nx.DiGraph, tree2: nx.DiGraph) -> bool:
    """
    Return true if given second *tree2* has the same structure and edge/node attributes as the first *tree1*.

    :param tree1:   first tree
    :param tree2:   second tree
    :return:        similarity result
    """
    return (nx.is_isomorphic(tree1, tree2) and
            all(all(tree1[u][v][a] == tree2[u][v][a] for a in tree1[u][v]) and
                all(tree1.nodes[v][a] == tree2.nodes[v][a] for a in tree1.nodes[v]) for u, v in tree1.edges))


def get_chain_k_min(memory: list[int], M: int, rate: list[int], N: int, start: int = 0, end: int = None) -> int:
    """
    Return minimal number of blocks due to constraints *M* and *N*.

    :param memory:  list of memory values
    :param M:       memory upper bound
    :param rate:    list of rate values
    :param N:       CPU count
    :param start:   fist node to consider
    :param end:     last node to consider
    :return:        minimal number of blocks
    """
    end = end if end is not None else len(memory) - 1
    return max(math.ceil(chain_memory(memory, start, end) / M),
               sum(1 for i, j in itertools.pairwise(rate[start: end + 1]) if math.ceil(j / i) > N))


def get_chain_c_min(memory: list[int], M: int, rate: list[int], N: int, start: int = 0, end: int = None) -> int:
    """
    Return minimal number of cuts due to constraints *M* and *N*.

    :param memory:  list of memory values
    :param M:       memory upper bound
    :param rate:    list of rate values
    :param N:       CPU count
    :param start:   fist node to consider
    :param end:     last node to consider
    :return:        minimal number of cuts
    """
    return get_chain_k_min(memory, M, rate, N, start, end) - 1


def get_chain_c_max(runtime: list[int], L: int, b: int, w: int, delay: int, start: int = 0, end: int = None) -> int:
    """
    Return maximal number of cuts due to constraint *L*.

    :param runtime: list of runtime values
    :param L:       upper latency limit
    :param b:       barrier node
    :param w:       end node of chain block
    :param delay:   platform delay
    :param start:   fist node to consider
    :param end:     last node to consider
    :return:        maximum number of cuts
    """
    end = end if end is not None else len(runtime) - 1
    return math.floor(min((L - chain_latency(runtime, b, w, delay, start, end)) / delay, len(runtime) - 1))


def get_chain_k_max(runtime: list[int], L: int, b: int, w: int, delay: int, start: int = 0, end: int = None) -> int:
    """
    Return maximal number of blocks due to constraint *L*.

    :param runtime: list of runtime values
    :param L:       upper latency limit
    :param b:       barrier node
    :param w:       end node of chain block
    :param delay:   platform delay
    :param start:   fist node to consider
    :param end:     last node to consider
    :return:        maximum number of blocks
    """
    return get_chain_c_max(runtime, L, b, w, delay, start, end) + 1


def get_chain_k_opt(partition: T_PART, start: int = 0, end: int = None) -> int:
    """
    Return the number of blocks included by the [*start*, *end*] interval in partitioning.

    :param partition:   chain partitioning
    :param start:       fist node to consider
    :param end:         last node to consider
    :return:            number of blocks
    """
    end = end if end is not None else partition[-1][-1]
    cntr = 0
    in_chain = False
    for blk in partition:
        b, w = blk[0], blk[-1]
        if not in_chain and b <= start:
            in_chain = True
        if in_chain:
            cntr += 1
        if in_chain and end <= w:
            in_chain = False
    return cntr


def get_chain_c_opt(partition: T_PART, start: int = 0, end: int = None) -> int:
    """
    Return the number of cuts included by the [*start*, *end*] interval in partitioning.

    :param partition:   chain partitioning
    :param start:       fist node to consider
    :param end:         last node to consider
    :return:            number of cuts
    """
    return get_chain_k_opt(partition, start, end) - 1


def prune_chain(tree: nx.DiGraph, node: int, leaf: int) -> tuple[list[int], list[int]]:
    """
    Return the nodes of chain [*node*, *leaf*] and the branching nodes.

    :param tree:    app tree
    :param node:    chain's barrier node
    :param leaf:    end node of chain
    :return:        nodes of the chain and its branches
    """
    chain = [node]
    branches = []
    u = node
    while u != leaf:
        for _, v in tree.out_edges(u):
            if leaf in tree.nodes[v][LABEL]:
                chain.append(v)
            else:
                branches.append(v)
        u = chain[-1]
    return chain, branches


########################################################################################################################


def print_chain_summary(runtime: list[int], memory: list[int], rate: list[int]):
    """
    Print chain summary.

    :param runtime: list of runtime values
    :param memory:  list of memory values
    :param rate:    list of rate values
    """
    print("Chain:", "[", *(f"-{r}-> F({t}|M{m})" for t, m, r in zip(runtime, memory, rate)), "]")


def evaluate_chain_partitioning(partition: T_PART, opt_cost: int, opt_lat: int, runtime: list, memory: list, rate: list,
                                M: int = math.inf, N: int = math.inf, L: int = math.inf, start: int = 0,
                                end: int = None, delay: int = 1, unit: int = 1, **params):
    """
    Evaluate chain partitioning and print its characteristics.

    :param partition:   chain partitioning
    :param opt_cost:    optimal cost of the partitioning
    :param opt_lat:     latency of the partitioning
    :param runtime:     list of runtime values
    :param memory:      list of memory values
    :param rate:        list of rate values
    :param M:           memory upper bound
    :param N:           CPU count
    :param L:           upper latency limit
    :param start:       fist node to consider
    :param end:         last node to consider
    :param delay:       platform delay
    :param unit:        rounding unit
    """
    print('#' * 80)
    print(f"Chain partitioning [M={M}, N={N}, L={L}:{(start, end)}] => "
          f"{partition} - opt_cost: {opt_cost}, opt_lat: {opt_lat}")
    print(f"k_min={get_chain_k_min(memory, M, rate, N, start, end)}, "
          f"k_opt[L]={len(path_blocks(partition, range(start, end + 1)))}, "
          f"k_max={get_chain_k_max(runtime, L, 0, len(runtime), delay, start, end)}")
    print_block_stat(partition, runtime, memory, rate, delay, start, end, unit)
    print('#' * 80)


def print_block_stat(partition: T_PART, runtime: list[int], memory: list[int], rate: list[int], delay: float,
                     start: int = 0, end: int = None, unit: int = 1):
    """
    Print block statistics.

    :param partition:   chain partitioning
    :param runtime:     list of runtime values
    :param memory:      list of memory values
    :param rate:        list of rate values
    :param start:       fist node to consider
    :param end:         last node to consider
    :param delay:       platform delay
    :param unit:        rounding unit
    """
    end = end if end is not None else len(runtime) - 1
    stat = [[str([blk[0], blk[-1]]),
             chain_cost(runtime, rate, blk[0], blk[-1], unit),
             chain_memory_opt(memory, rate, blk[0], blk[-1]),
             chain_cpu(rate, blk[0], blk[-1]),
             chain_latency(runtime, blk[0], blk[-1], delay, start, end)] for blk in partition]
    print(tabulate.tabulate(stat, ['Block', 'Cost', 'Memory', 'CPU', 'Latency'],
                            numalign='decimal', stralign='center', tablefmt='pretty'))


def print_chain_partition_result(barr: T_BARRS, cost: int, lat: int):
    """
    Decode and print chain partitioning result.

    :param barr:    barrier nodes
    :param cost:    optimal cost
    :param lat:     latency values
    """
    if barr is not None:  # [], cost, lat
        print("Minimal-cost solution is calculated.")
    elif cost is not None and lat is None:  # None, inf, None
        print("Feasible latency-fitting solution cannot be generated due to memory constraint M.")
    elif cost is None and lat is not None:  # None, None, lat
        print("Solution does not exist due to too strict latency constraint L.")
    else:  # None, None, None
        print("Feasible solution does not exist due to non-overlapping constrains L and M.")


def print_tree_summary(tree: nx.DiGraph):
    """
    Print summary of app graphs.

    :param tree:    input tree
    """
    print(tree)
    for n, nd in tree.nodes(data=True):
        print(f"\t{n}: {nd}")
        for i, j, ed in tree.out_edges(n, data=True):
            print(f"\t\t{i} -> {j}: {ed}")


def print_tree_block_stat(tree: nx.DiGraph, partition: T_PART, unit: int = 1):
    """
    Print cost memory and latency values of partition blocks in tabulated format.

    :param tree:        input tree
    :param partition:   given partitioning
    :param unit:        rounding unit
    """
    stat = []
    for blk in partition:
        pred = next(tree.predecessors(blk[0]))
        runtime, memory, rate = zip(*[(tree.nodes[v][RUNTIME], tree.nodes[v][MEMORY], tree[u][v][RATE])
                                      for u, v in itertools.pairwise([pred] + blk)])
        b, w = 0, len(blk) - 1
        stat.append([str([blk[b], blk[w]]),
                     chain_cost(runtime, rate, b, w, unit),
                     chain_memory_opt(memory, rate, b, w),
                     chain_cpu(rate, b, w),
                     chain_latency(runtime, b, w, 0, b, w)])
    print(tabulate.tabulate(stat, ['Block', 'Cost', 'Memory', 'CPU', 'Latency'], numalign='decimal', stralign='center'))


def print_cpath_stat(tree: nx.DiGraph, partition: T_PART, cpath: list[int] = None, delay: int = 10):
    """
    Print the related block of the critical path.

    :param tree:        input tree
    :param partition:   given partitioning
    :param cpath:       critical path
    :param delay:       platform delay value
    """
    if len(partition) > 0:
        c_blocks = path_blocks(partition, cpath)
        opt_cut = len(c_blocks) - 1
        sum_lat = sum(chain_latency([tree.nodes[v][RUNTIME] for v in blk], 0, len(blk) - 1, delay, 0, len(blk) - 1)
                      for blk in c_blocks) + opt_cut * delay
        print("Critical blocks of cpath", [cpath[0], cpath[-1]], "=>", c_blocks, "-", "opt_cut:", opt_cut, "-",
              "opt_lat:", sum_lat)


def evaluate_tree_partitioning(tree: nx.DiGraph, partition: T_PART, opt_cost: int, root: int, cp_end: int, M: int,
                               N: int, L: int, delay: int, unit: int, **params):
    """
    Evaluate tree partitioning and print its characteristics.

    :param tree:        input tree
    :param partition:   given partitioning
    :param opt_cost:    optimal partitioning cost
    :param root:        root node
    :param cp_end:      end node of critical path
    :param M:           upper memory limit
    :param N:           CPU count
    :param L:           latency limit
    :param delay:       platform invocation delay
    :param unit:        rounding unit
    """
    tree = leaf_label_nodes(tree)
    # noinspection PyUnresolvedReferences
    print(tree.graph.get(NAME, "tree").center(80, '#'))
    print("Runtime:", [tree.nodes[v][RUNTIME] for v in tree.nodes if v is not PLATFORM])
    print("Memory:", [tree.nodes[v][MEMORY] for v in tree.nodes if v is not PLATFORM])
    print("Rate:", [tree[next(tree.predecessors(v))][v][RATE] for v in tree.nodes if v is not PLATFORM])
    print(f"Tree partitioning [M={M}, N={N}, L={L}:{(root, cp_end)}] => {partition} - opt_cost: {opt_cost}")
    if partition:
        print_cpath_stat(tree, partition, list(ichain(tree, root, cp_end)), delay)
        print_tree_block_stat(tree, partition, unit)
        # draw_tree(tree, partition, draw_blocks=True, draw_weights=False)
    print('#' * 80)


########################################################################################################################


def print_ser_tree_block_stat(tree: nx.DiGraph, partition: T_PART, cpath: typing.Iterable[int]):
    """
    Print cost memory and latency values of partition blocks in tabulated format.

    :param tree:        input tree
    :param partition:   given partitioning
    :param cpath:       critical path
    """
    stat = []
    for blk in partition:
        blk_cost = ser_subtree_cost(tree, blk[0], blk)
        blk_lat = ser_subchain_latency(tree, blk[0], set(blk), set(cpath))
        stat.append([str([blk[0], blk[-1]]), blk_cost, sum(tree.nodes[v][MEMORY] for v in blk), blk_lat])
    print(tabulate.tabulate(stat, ['Block', 'Cost', 'Memory', 'Latency'], numalign='decimal', stralign='center'))


def print_ser_cpath_stat(tree: nx.DiGraph, partition: T_PART, cpath: list[int] = None, delay: int = 10):
    """
    Print the related block of the critical path.

    :param tree:        input tree
    :param partition:   given partitioning
    :param cpath:       critical path
    :param delay:       platform delay value
    """
    cpath = set(cpath)
    if len(partition) > 0:
        restricted_blk = [blk for blk in partition if blk[0] in cpath]
        blk_lats = [ser_subchain_latency(tree, blk[0], set(blk), cpath) for blk in restricted_blk]
        sum_lat = sum(blk_lats) + (len(restricted_blk) - 1) * delay
        print("Critical blocks wrt. cpath:", sorted(cpath), "=>", restricted_blk, "-", "opt_lat:", sum_lat)


def evaluate_ser_tree_partitioning(tree: nx.DiGraph, partition: T_PART, opt_cost: int, opt_lat: int, root: int,
                                   cp_end: int, M: int, L: int, delay: int, draw: bool = True, **params):
    """
    Evaluate tree partitioning and print its characteristics assuming serialized platform execution model.

    :param tree:        input tree
    :param partition:   given partitioning
    :param opt_cost:    optimal partitioning cost
    :param opt_lat:     latency value of the partitioning
    :param root:        root node
    :param cp_end:      end node of critical path
    :param M:           upper memory limit
    :param L:           latency limit
    :param delay:       platform invocation delay
    :param draw:        draw tree
    """
    tree = leaf_label_nodes(tree)
    # noinspection PyUnresolvedReferences
    print(tree.graph.get(NAME, "tree").center(80, '#'))
    print("Runtime:", [tree.nodes[v][RUNTIME] for v in tree.nodes if v is not PLATFORM])
    print("Memory:", [tree.nodes[v][MEMORY] for v in tree.nodes if v is not PLATFORM])
    print("Data:", [tree[next(tree.predecessors(v))][v][DATA] for v in tree.nodes if v is not PLATFORM])
    print("Rate:", [tree[next(tree.predecessors(v))][v][RATE] for v in tree.nodes if v is not PLATFORM])
    print(f"Tree partitioning [M={M}, L={L}:{(root, cp_end)}] => {partition} - opt_cost: {opt_cost},"
          f" opt_lat: {opt_lat}")
    if partition:
        print_ser_cpath_stat(tree, partition, list(ichain(tree, root, cp_end)), delay)
        print(f"Recalculated partition cost: {sum(ser_subtree_cost(tree, blk[0], blk) for blk in partition)}")
        print_ser_tree_block_stat(tree, partition, set(ichain(tree, root, cp_end)))
        # if draw:
        #     draw_tree(tree, partition, draw_blocks=True, draw_weights=False)
    print('#' * 80)


def print_par_tree_block_stat(tree: nx.DiGraph, partition: T_PART, cpath: typing.Iterable[int], N: int = 1):
    """
    Print cost memory and latency values of partition blocks in tabulated format  assuming parallelized execution model.

    :param tree:        input tree
    :param partition:   given partitioning
    :param cpath:       critical path
    :param N:           CPU count
    """
    stat = []
    for blk in partition:
        blk_cost = par_subtree_cost(tree, blk[0], blk, N)
        blk_lat = par_subchain_latency(tree, blk[0], set(blk), set(cpath), N)
        stat.append([str([blk[0], blk[-1]]), blk_cost, sum(tree.nodes[v][MEMORY] for v in blk), blk_lat])
    print(tabulate.tabulate(stat, ['Block', 'Cost', 'Memory', 'Latency'], numalign='decimal', stralign='center'))


def print_par_cpath_stat(tree: nx.DiGraph, partition: T_PART, cpath: list[int] = None, delay: int = 10, N: int = 1):
    """
    Print the related block of the critical path assuming parallelized execution model.

    :param tree:        input tree
    :param partition:   given partitioning
    :param cpath:       critical path
    :param delay:       platform invocation delay
    :param N:           CPU count
    """
    cpath = set(cpath)
    if len(partition) > 0:
        restricted_blk = [blk for blk in partition if blk[0] in cpath]
        blk_lats = [par_subchain_latency(tree, blk[0], set(blk), cpath, N) for blk in restricted_blk]
        sum_lat = sum(blk_lats) + (len(restricted_blk) - 1) * delay
        print("Critical blocks wrt. cpath:", sorted(cpath), "=>", restricted_blk, "-", "opt_lat:", sum_lat)


def evaluate_par_tree_partitioning(tree: nx.DiGraph, partition: T_PART, opt_cost: int, opt_lat: int, root: int,
                                   cp_end: int, M: int | None, L: int | None, N: int, delay: int, draw: bool = True,
                                   **params):
    """
    Evaluate tree partitioning and print its characteristics assuming a parallelized platform execution model.

    :param tree:        input tree
    :param partition:   given partitioning
    :param opt_cost:    optimal partitioning cost
    :param opt_lat:     latency value of the partitioning
    :param root:        root node
    :param cp_end:      end node of the critical path
    :param M:           upper memory limit
    :param L:           latency limit
    :param N:           CPU count
    :param delay:       platform invocation delay
    :param draw:        draw tree
    """
    tree = leaf_label_nodes(tree)
    # noinspection PyUnresolvedReferences
    print(tree.graph.get(NAME, "tree").center(80, '#'))
    print("Runtime:", [tree.nodes[v][RUNTIME] for v in tree.nodes if v is not PLATFORM])
    print("Memory:", [tree.nodes[v][MEMORY] for v in tree.nodes if v is not PLATFORM])
    print("Data:", [tree[next(tree.predecessors(v))][v][DATA] for v in tree.nodes if v is not PLATFORM])
    print("Rate:", [tree[next(tree.predecessors(v))][v][RATE] for v in tree.nodes if v is not PLATFORM])
    print(f"Tree partitioning [{M=}, {L=}:{(root, cp_end)}, {N=}] => {partition} - opt_cost: {opt_cost},"
          f" opt_lat: {opt_lat}")
    if partition:
        print_par_cpath_stat(tree, partition, list(ichain(tree, root, cp_end)), delay, N)
        print_par_tree_block_stat(tree, partition, set(ichain(tree, root, cp_end)), N)
        # if draw:
        #     draw_tree(tree, partition, draw_blocks=True, draw_weights=False)
    print('#' * 80)


def evaluate_gen_tree_partitioning(tree: nx.DiGraph, partition: T_FPART, opt_cost: int, opt_lat: int, root: int,
                                   flavors: list, cp_end: int, L: int, delay: int, draw: bool = True, **params):
    """
    Evaluate tree partitioning and print its characteristics assuming parallelized platform execution model.

    :param tree:        input tree
    :param partition:   given partitioning
    :param opt_cost:    optimal partitioning cost
    :param opt_lat:     latency value of the partitioning
    :param root:        root node
    :param flavors:     list of flavors
    :param cp_end:      end node of critical path
    :param L:           latency limit
    :param delay:       platform invocation delay
    :param draw:        draw tree
    """
    tree = leaf_label_nodes(tree)
    # noinspection PyUnresolvedReferences
    print(tree.graph.get(NAME, "tree").center(80, '#'))
    print("Runtime:", [tree.nodes[v][RUNTIME] for v in tree.nodes if v is not PLATFORM])
    print("Memory:", [tree.nodes[v][MEMORY] for v in tree.nodes if v is not PLATFORM])
    print("Data:", [tree[next(tree.predecessors(v))][v][DATA] for v in tree.nodes if v is not PLATFORM])
    print("Rate:", [tree[next(tree.predecessors(v))][v][RATE] for v in tree.nodes if v is not PLATFORM])
    M, N, cfactor = zip(*flavors)
    print(f"Tree partitioning [{M=}, {L=}:{(root, cp_end)}, {N=}] => {partition} - opt_cost: {opt_cost},"
          f" opt_lat: {opt_lat}")
    # if partition:
    # print_par_cpath_stat(tree, partition, list(ichain(tree, root, cp_end)), delay, N)
    # print_par_tree_block_stat(tree, partition, set(ichain(tree, root, cp_end)), N)
    # if draw:
    #     draw_tree(tree, partition, draw_blocks=True, draw_weights=False)
    print('#' * 80)


def print_ser_chain_summary(runtime: list[int], memory: list[int], rate: list[int], data: list[int]):
    """
    Print chain summary assuming serialized execution model.

    :param runtime:     list of runtime values
    :param memory:      list of memory values
    :param rate:        list of rate values
    :param data:        list of data values
    """
    print("Chain:", "[", *(f"-{r}-> F(D{d}|T{t}|M{m})" for t, m, r, d in zip(runtime, memory, rate, data)), "]")


def print_ser_block_stat(partition: T_PART, runtime: list[int], memory: list[int], rate: list[int], data: list[int],
                         delay: float, start: int = 0, end: int = None):
    """
    Print block stats of a chain partitioning assuming serialized execution model.

    :param partition:   given partitioning
    :param runtime:     list of runtime values
    :param memory:      list of memory values
    :param rate:        list of rate values
    :param data:        list of data values
    :param delay:       platform delay
    :param start:       fist node to consider
    :param end:         last node to consider
    """
    end = end if end is not None else len(runtime) - 1
    stat = [[str([blk[0], blk[-1]]),
             ser_chain_subcost(runtime, rate, data, blk[0], blk[-1]),
             ser_chain_submemory(memory, blk[0], blk[-1]),
             ser_chain_sublatency(runtime, rate, data, blk[0], blk[-1], delay, start, end)] for blk in partition]
    print(tabulate.tabulate(stat, ['Block', 'Cost', 'Memory', 'Latency'],
                            numalign='decimal', stralign='center', tablefmt='pretty'))


def evaluate_ser_chain_partitioning(partition: T_PART, opt_cost: int, opt_lat: int, runtime: list[int],
                                    memory: list[int], rate: list[int], data: list[int], M: int = math.inf,
                                    L: int = math.inf, start: int = 0, end: int = None, delay: int = 1, **params):
    """
    Evaluate chain partitioning and print its characteristics assuming serialized execution model.

    :param partition:   given partitioning
    :param opt_cost:    optimal partitioning cost
    :param opt_lat:     latency value of the partitioning
    :param runtime:     list of runtime values
    :param memory:      list of memory values
    :param rate:        list of rate values
    :param data:        list of data values
    :param M:           upper memory limit
    :param L:           latency limit
    :param start:       fist node to consider
    :param end:         last node to consider
    :param delay:       platform delay
    """
    print('#' * 80)
    print(f"Chain partitioning [M={M}, L={L}:{(start, end)}] => "
          f"{partition} - opt_cost: {opt_cost}, opt_lat: {opt_lat}")
    print_ser_block_stat(partition, runtime, memory, rate, data, delay, start, end)
    print('#' * 80)


def print_par_dag_block_stat(dag: nx.DiGraph, partition: T_PART, cpath: typing.Iterable[int], N: int = 1):
    """
    Print cost memory and latency values of partition blocks in tabulated format  assuming a
    parallelized execution model.

    :param dag:         input DAG graph
    :param partition:   given partitioning
    :param cpath:       critical path
    :param N:           CPU count
    """
    stat = []
    for blk in partition:
        blk_cost = par_subgraph_cost(dag, blk[0], blk, N)
        blk_lat = par_subgraph_latency(dag, blk[0], set(blk), set(cpath), N)
        blk_mem = par_subgraph_memory(dag, blk[0], set(blk), N)
        stat.append([str([blk[0], blk[-1]]), blk_cost, blk_mem, blk_lat])
    print(tabulate.tabulate(stat, ['Block', 'Cost', 'Memory', 'Latency'], numalign='decimal', stralign='center'))


def print_dag_cpath_stat(dag: nx.DiGraph, partition: T_PART, cpath: typing.Iterable[int] = None, delay: int = 10,
                         N: int = 1):
    """
    Print the related block of the critical path assuming a parallelized execution model.

    :param dag:         input DAG graph
    :param partition:   given partitioning
    :param cpath:       critical path
    :param delay:       platform invocation delay
    :param N:           CPU count
    """
    cpath = set(cpath)
    if len(partition) > 0:
        restricted_blk = [blk for blk in partition if blk[0] in cpath]
        blk_lats = [par_subgraph_latency(dag, blk[0], set(blk), cpath, N) for blk in restricted_blk]
        sum_lat = sum(blk_lats) + (len(restricted_blk) - 1) * delay
        print("Critical blocks wrt. cpath:", sorted(cpath), "=>", restricted_blk, "-", "opt_lat:", sum_lat)


def evaluate_par_dag_partitioning(dag: nx.DiGraph, partition: T_PART, opt_cost: int, opt_lat: int, root: int,
                                  cp_end: int, M: int, L: int, N: int, delay: int, draw: bool = True, **params):
    """
    Evaluate tree partitioning and print its characteristics assuming a parallelized platform execution model.

    :param dag:         input tree
    :param partition:   given partitioning
    :param opt_cost:    optimal partitioning cost
    :param opt_lat:     latency value of the partitioning
    :param root:        root node
    :param cp_end:      end node of the critical path
    :param M:           upper memory limit
    :param L:           latency limit
    :param N:           CPU count
    :param delay:       platform invocation delay
    :param draw:        draw tree
    """
    # noinspection PyUnresolvedReferences
    print(dag.graph.get(NAME, "tree").center(80, '#'))
    print(f"Tree partitioning [{M=}, {L=}:{(root, cp_end)}, {N=}] => {partition} - opt_cost: {opt_cost},"
          f" opt_lat: {opt_lat}")
    if partition:
        cpath = set(ibacktrack_chain(dag, root, cp_end))
        print_dag_cpath_stat(dag, partition, cpath, delay, N)
        print_par_dag_block_stat(dag, partition, cpath, N)
        # if draw:
        #     draw_dag(dag, partition, draw_weights=False)
    print('#' * 80)


########################################################################################################################


def print_lp_desc(model: pulp.LpProblem):
    """
    Print the lp format of the model.

    :param model:   PuLP model object
    """
    with tempfile.TemporaryDirectory() as tmp:
        model.writeLP(f"{tmp}/chain_model.lp")
        with open(f"{tmp}/chain_model.lp") as f:
            print(f.read())


def convert_var_dict(X: dict[int, dict[int, ...]]) -> list[list[pulp.LpVariable]]:
    """
    Convert dict-of-dict variable matrix into list-of-list format.

    :param X:   specific structure of decision variables
    :return:    converted format of decision variables
    """
    return [[X[i][j] if j in X[i] else None for j in range(1, i + 1)] for i in sorted(X)]


def print_var_matrix(X: list[list[pulp.LpVariable]]):
    """
    Print matrix of decision variables names in tabular format.

    :param X:   specific structure of decision variables
    """
    print(tabulate.tabulate([list(map(lambda x: x if isinstance(x, (int, type(None))) else x.name, x_i)) for x_i in X],
                            missingval="-", numalign='center', stralign='center', tablefmt='outline'))


def print_pulp_matrix_values(X: list[list[pulp.LpVariable]]):
    """
    Print matrix of decision variables values in tabular format.

    :param X:   specific structure of decision variables
    """
    print(tabulate.tabulate([list(map(lambda x: x if isinstance(x, (int, type(None))) else pulp.value(x), x_i))
                             for x_i in X], missingval="-", numalign='center', stralign='center', tablefmt='outline'))


def print_cplex_matrix_values(X: list[list[pulp.LpVariable]]):
    """
    Print matrix of decision variables values in tabular format.

    :param X:   specific structure of decision variables
    """
    print(tabulate.tabulate([list(map(lambda x: x if isinstance(x, (int, type(None))) else round(x.solution_value),
                                      x_i)) for x_i in X],
                            missingval="-", numalign='center', stralign='center', tablefmt='outline'))


def print_cost_coeffs(model: pulp.LpProblem, X: list[list[pulp.LpVariable]]):
    """
    Print cost coefficients of the given LP *model*.

    :param model:   model object
    :param X:       specific structure of decision variables
    """
    print(tabulate.tabulate([[model.objective.get(x) for x in x_i] for x_i in X],
                            missingval="-", numalign='center', stralign='center', tablefmt='outline'))


def print_lat_coeffs(model: pulp.LpProblem, X: list[list[pulp.LpVariable]]):
    """
    Print latency coefficients of the given LP *model*.

    :param model:   model object
    :param X:       specific structure of decision variables
    """
    print(tabulate.tabulate([[model.constraints[LP_LAT].get(x, default=None) for x in x_i] for x_i in X],
                            missingval="-", numalign='center', stralign='center', tablefmt='outline'))
