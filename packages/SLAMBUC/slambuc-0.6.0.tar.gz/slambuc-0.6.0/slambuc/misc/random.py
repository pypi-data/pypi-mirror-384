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
import random
import time

import networkx
import networkx as nx

from slambuc.alg.app.common import *


def get_random_chain_data(nodes: int = 10, runtime: tuple[int, int] = (1, 100), memory: tuple[int, int] = (1, 3),
                          rate: tuple[int, int] = (1, 3),
                          data: tuple[int, int] = (1, 20)) -> tuple[list[int], list[int], list[int], list[int]]:
    """
    Generate random chain(path graph) data with properties from given intervals.

    :param nodes:   number of nodes
    :param runtime: interval of runtime values
    :param memory:  interval of memory values
    :param rate:    interval of rate values
    :param data:    interval of data values
    :return:        generated chain data
    """
    t = [random.randint(*runtime) for _ in range(nodes)]
    m = [random.randint(*memory) for _ in range(nodes)]
    d = [random.randint(*data) for _ in range(nodes)]
    r = [1, *(random.randint(*rate) for _ in range(nodes - 1))]
    return t, m, r, d


# noinspection PyTypeChecker
def get_random_chain(nodes: int = 10, runtime: tuple[int, int] = (1, 100), memory: tuple[int, int] = (1, 3),
                     rate: tuple[int, int] = (1, 3), data: tuple[int, int] = (1, 20)) -> nx.DiGraph:
    """
    Generate random chain(path graph) with properties from given intervals.

    :param nodes:   number of nodes
    :param runtime: interval of runtime values
    :param memory:  interval of memory values
    :param rate:    interval of rate values
    :param data:    interval of data values
    :return:        generated random chain
    """
    chain = nx.path_graph(range(0, nodes + 1), nx.DiGraph)
    nx.set_node_attributes(chain, {i: random.randint(*runtime) for i in range(1, nodes + 1)}, RUNTIME)
    nx.set_node_attributes(chain, {i: random.randint(*memory) for i in range(1, nodes + 1)}, MEMORY)
    for _, _, d in chain.edges(data=True):
        d[RATE] = random.randint(*rate)
        d[DATA] = random.randint(*data)
    chain = nx.relabel_nodes(chain, {0: PLATFORM})
    chain[PLATFORM][1][RATE] = 1
    # noinspection PyUnresolvedReferences
    chain.graph[NAME] = "random_chain"
    return chain


# noinspection PyTypeChecker
def get_random_tree(nodes: int = 20, runtime: tuple[int, int] = (1, 100), memory: tuple[int, int] = (1, 3),
                    rate: tuple[int, int] = (1, 3), data: tuple[int, int] = (1, 20),
                    name: str = None) -> nx.DiGraph:
    """
    Generate random tree from Prufer sequence with properties from given intervals.

    :param nodes:   number of nodes
    :param runtime: interval of runtime values
    :param memory:  interval of memory values
    :param rate:    interval of rate values
    :param data:    interval of data values
    :param name:    tree name suffix
    :return:        generated random tree
    """
    # noinspection PyUnresolvedReferences
    raw_tree = nx.bfs_tree(nx.random_labeled_tree(nodes + 1), 0)
    while raw_tree.out_degree[0] > 1:
        # noinspection PyUnresolvedReferences
        raw_tree = nx.bfs_tree(networkx.generators.trees.random_labeled_tree(nodes + 1), 0)
    tree = nx.convert_node_labels_to_integers(raw_tree, first_label=0)
    nx.set_node_attributes(tree, {i: random.randint(*runtime) for i in range(1, nodes + 1)}, RUNTIME)
    nx.set_node_attributes(tree, {i: random.randint(*memory) for i in range(1, nodes + 1)}, MEMORY)
    for _, _, d in tree.edges(data=True):
        d[RATE] = random.randint(*rate)
        d[DATA] = random.randint(*data)
    tree = nx.DiGraph(nx.relabel_nodes(tree, {0: PLATFORM}))
    tree[PLATFORM][1][RATE] = 1
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] = f"random_tree_{time.time()}" if name is None else name
    return tree


# noinspection PyTypeChecker
def get_random_dag(nodes: int = 20, crossing: int = 5, runtime: tuple[int, int] = (1, 100),
                   memory: tuple[int, int] = (1, 3), rate: tuple[int, int] = (1, 3),
                   data: tuple[int, int] = (1, 20), name: str = None) -> nx.DiGraph:
    """
    Generate random DAG from a directed tree with 'crossing' edges and properties from given intervals.

    :param nodes:       number of nodes
    :param crossing:    number of cross-edges
    :param runtime:     interval of runtime values
    :param memory:      interval of memory values
    :param rate:        interval of rate values
    :param data:        interval of data values
    :param name:        tree name suffix
    :return:            generated random tree
    """
    # noinspection PyUnresolvedReferences
    raw_tree = nx.bfs_tree(nx.random_labeled_tree(nodes + 1), 0)
    while raw_tree.out_degree[0] > 1:
        # noinspection PyUnresolvedReferences
        raw_tree = nx.bfs_tree(nx.random_labeled_tree(nodes + 1), 0)
    dag = nx.convert_node_labels_to_integers(raw_tree, first_label=0)
    # noinspection PyTypeChecker
    dag.add_edges_from([sorted(random.sample(range(1, nodes + 1), 2)) for _ in range(crossing)])
    nx.set_node_attributes(dag, {i: random.randint(*runtime) for i in range(1, nodes + 1)}, RUNTIME)
    nx.set_node_attributes(dag, {i: random.randint(*memory) for i in range(1, nodes + 1)}, MEMORY)
    for _, _, d in dag.edges(data=True):
        d[RATE] = random.randint(*rate)
        d[DATA] = random.randint(*data)
    dag = nx.DiGraph(nx.relabel_nodes(dag, {0: PLATFORM}))
    dag[PLATFORM][1][RATE] = 1
    # noinspection PyUnresolvedReferences
    dag.graph[NAME] = f"random_dag_{time.time()}" if name is None else name
    return dag
