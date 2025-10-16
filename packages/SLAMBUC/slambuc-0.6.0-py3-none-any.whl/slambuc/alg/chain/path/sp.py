# Copyright 2024 Janos Czentye
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
import math

import networkx as nx

from slambuc.alg import INFEASIBLE
from slambuc.alg.util import chain_cost, chain_cpu, chain_memory_opt

# Naming convention for state-space DAG
START, END = 's', 't'


def encode_blk(b: int | str, w: int | str) -> str:
    """
    Encode node blocks as str.

    :param b:   barrier node
    :param w:   ending node
    :return:    encoded blk
    """
    return f"{b}|{w}"


def decode_blk(s: str, unfold: bool = False) -> list[int] | int:
    """
    Decode encoded block str.

    :param s:   encoded str
    :param unfold:  return full blocks instead of barrier nodes
    :return:    tuple of block barrier and ending nodes
    """
    b, w = s.split('|', maxsplit=1)
    return list(range(int(b), int(w) + 1)) if unfold else int(b)


def _build_sp_dag(runtime: list, memory: list, rate: list, M: int = math.inf, N: int = math.inf,
                  unit: int = 1) -> nx.DiGraph:
    """
    Build configuration state graph of the given function chain.

    :param runtime: Running times in ms
    :param memory:  memory requirements in MB
    :param rate:    avg. Rate of function invocations
    :param M:       upper memory bound of the partition blocks (in MB)
    :param N:       upper CPU core bound of the partition blocks
    :param unit:    rounding unit for the cost calculation (default: 100 ms)
    :return:        return state graph
    """
    n = len(runtime)
    # Initiate data structure for DAG
    _cache = collections.defaultdict(list)
    _cache.update({START: [START], END: [END]})
    dag = nx.DiGraph(directed=True)
    for b in range(n):
        prev = b - 1 if b > 0 else START
        for w in range(b, n):
            if chain_memory_opt(memory, rate, b, w) > M or chain_cpu(rate, b, w) > N:
                break
            blk_id = encode_blk(b, w)
            _cache[w].append(blk_id)
            blk_cost = chain_cost(runtime, rate, b, w, unit)
            # Add connection between related subcases
            for p in _cache[prev]:
                dag.add_edge(p, blk_id, weight=blk_cost)
    # Add connection for ending subcases
    for p in _cache[n - 1]:
        dag.add_edge(p, END, weight=0)
    return dag


def hop_limited_shortest_path(dag: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph,
                              source: str | int, target: str | int,
                              max_hops: int = math.inf) -> tuple[int, int, list[int | str]] | tuple[None, None, None]:
    """
    Calculate the shortest path in graph 'dag' between 'source' and 'target' with the hop limit 'max_hops'.

    :param dag:         state graph
    :param source:      start node in 'dag'
    :param target:      end node in 'dag'
    :param max_hops:    hop limit of for the path
    :return:            calculated sum weights, hop count, nodes of the shortest path
    """
    #
    dist: dict[int, dict[int, int | float]] = collections.defaultdict(lambda: collections.defaultdict(lambda: math.inf))
    prev = collections.defaultdict(lambda: collections.defaultdict(lambda: None))
    pq = []
    dist[source][0] = 0
    heapq.heappush(pq, (source, 0))
    # Iterate over graph edges combined with possible hops
    while pq:
        u, h = heapq.heappop(pq)
        if h == max_hops:
            continue
        for v in dag.succ[u]:
            alt = dist[u][h] + dag[u][v].get('weight', 0)
            if alt < dist[v][h + 1]:
                dist[v][h + 1] = alt
                prev[v][h + 1] = u
                heapq.heappush(pq, (v, h + 1))
    # Reconstruct the shortest path
    if not len(dist[target]):
        return None, None, None
    path, _u, _h = [], target, min(dist[target], key=lambda x: dist[target][x])
    min_weight, hcount = dist[target][_h], _h
    while _u:
        path.append(_u)
        _u = prev[_u][_h]
        _h -= 1
    path.reverse()
    return min_weight, hcount, path


def sp_chain_partitioning(runtime: list, memory: list, rate: list, M: int = math.inf,
                          N: int = math.inf, L: int = math.inf, delay: int = 1, unit: int = 1,
                          unfold: bool = False, **kwargs) -> tuple[list[int], int, int]:
    """
    Calculates minimal-cost partitioning of a chain based on the node properties of *running time*, *memory usage* and
    *invocation rate* with respect to an upper bound **M** on the total memory of blocks and a latency constraint **L**
    defined on the subchain between *start* and *end* nodes.

    Partitioning is based on the shortest path calculation of the state graph of feasible blocks.

    :param runtime: running times in ms
    :param memory:  memory requirements in MB
    :param rate:    avg. rate of function invocations
    :param M:       upper memory bound of the partition blocks (in MB)
    :param N:       upper CPU core bound of the partition blocks
    :param L:       latency limit defined on the critical path in the form of subchain[start -> end] (in ms)
    :param delay:   invocation delay between blocks
    :param unit:    rounding unit for the cost calculation (default: 100 ms)
    :param unfold:  return full blocks instead of barrier nodes
    :return:        tuple of barrier nodes, sum cost of the partitioning, and the calculated edge cuts
    """
    dag = _build_sp_dag(runtime, memory, rate, M, N, unit)
    h_max = math.floor(min((L - sum(runtime)) / delay, len(runtime) - 1))
    min_cost, hops, sp = hop_limited_shortest_path(dag, source=START, target=END, max_hops=h_max + 2)
    return ([decode_blk(v, unfold) for v in sp[1:-1]], min_cost, hops - 2) if sp else INFEASIBLE
