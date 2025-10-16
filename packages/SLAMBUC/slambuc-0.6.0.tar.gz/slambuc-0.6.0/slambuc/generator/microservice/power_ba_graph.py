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
import bisect
import functools
import itertools
import random

import networkx as nx


def wrand_sample(population: list[int | float], weights: list[int], k: int = 1) -> list[int | float]:
    """
    Provide an *k*-size weighted random sample from *population* without replacement according to the given *weights*.

    See more: https://stackoverflow.com/questions/43549515/weighted-random-sample-without-replacement-in-python

    :param population:  list of items
    :param weights:     list of item weights
    :param k:           sample size (default: 1)
    :return:            sample list
    """
    # Trivial solution
    if len(population) <= k:
        return population
    # Cumulative distribution of weights
    acc_weights = list(itertools.accumulate(weights))
    w_sum, opted = acc_weights[-1], set()
    while len(opted) < k:
        idx = bisect.bisect_left(acc_weights, int(w_sum * random.random()))
        # Overwrite already drawn item to ensure that one item is chosen only for once
        opted.add(idx)
    return list(population[idx] for idx in opted)


def generate_power_ba_graph(n: int, m: int, Alpha: float = 1.0, a: float = 0.0, root: int = 0,
                            create_using: nx.Graph = None) -> nx.Graph:
    """
    Generate Barabasi-Albert (BA) graph where the probability of choosing a vertex *v* for connecting to another node
    follows a Power law distribution as *P(v) = deg(v)^Alpha + a*.

    Thus, choosing *Alpha = 1.0* and *a = 0.0* falls back to standard BA graph generation.

    Choosing *m = 1* ensures the output to be a tree by default.

    See also: https://networkx.org/documentation/stable/_modules/networkx/generators/random_graphs.html#barabasi_albert_graph
    and the related paper: https://dl.acm.org/doi/abs/10.5555/3432601.3432616.

    :param n:               number of nodes
    :param m:               number of existing nodes (or new edges) attached to the new node in each step
    :param Alpha:           power of preferential attachment (default: 1.0)
    :param a:               attractiveness of vertices with no edges (default: 0.0)
    :param root:            initial node ID that is increased in each attachment step (default: 0)
    :param create_using:    graph type to construct (default: undirected, use `nx.DiGraph` to get a directed graph)
    :return:                created graph
    """
    graph = nx.from_edgelist(((root, i) for i in range(root + 1, root + m + 1)), create_using=create_using)
    node_max, node_miss = max(graph), n - len(graph)
    for source in range(node_max + 1, node_max + node_miss + 1):
        nodes, deg_weights = zip(*((v, d ** Alpha + a) for v, d in graph.degree))
        graph.add_edges_from(zip(itertools.repeat(source), wrand_sample(nodes, deg_weights, m)))
    return graph


generate_power_ba_tree = functools.partial(generate_power_ba_graph, m=1)  # Generate power BA trees using m=1.
