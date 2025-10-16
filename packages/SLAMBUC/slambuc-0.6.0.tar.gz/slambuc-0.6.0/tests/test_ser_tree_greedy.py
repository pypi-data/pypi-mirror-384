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
import math
import pathlib

import networkx as nx

from slambuc.alg.app import NAME
from slambuc.alg.tree.serial.greedy import greedy_ser_tree_partitioning
from slambuc.alg.util import leaf_label_nodes
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import evaluate_ser_tree_partitioning


def run_test(tree: nx.DiGraph, M: int, L: int, root: int = 1, cp_end: int = None, delay: int = 10):
    leaf_label_nodes(tree)
    results = greedy_ser_tree_partitioning(tree, root, M, L, cp_end, delay)
    for i, (part, best_cost, best_lat) in enumerate(results):
        print(f"  GREEDY[{i}]  ".center(80, '#'))
        evaluate_ser_tree_partitioning(tree, part, best_cost, best_lat, root, cp_end, M, L, delay)
    return results


def test_ser_tree_greedy_partitioning():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-greedy_ser"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  # L = math.inf,
                  L=430,
                  delay=10)
    run_test(**params)


def test_random_greedy_partitioning(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-greedy_ser"
    params = dict(tree=tree,
                  M=6,
                  L=math.inf,
                  root=1,
                  cp_end=n,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    test_ser_tree_greedy_partitioning()
    # test_random_greedy_partitioning()
