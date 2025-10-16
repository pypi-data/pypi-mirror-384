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
import pytest

from slambuc.alg.app import NAME
from slambuc.alg.tree.path.greedy import greedy_tree_partitioning
from slambuc.alg.util import leaf_label_nodes
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import evaluate_tree_partitioning


def run_test(tree: nx.DiGraph, M: int, N: int, L: int, root: int = 1, cp_end: int = None, delay: int = 10,
             unit: int = 100):
    leaf_label_nodes(tree)
    results = greedy_tree_partitioning(tree, root, M, N, L, cp_end, delay, unit)
    for i, (part, best_cost, best_lat) in enumerate(results):
        print(f"  GREEDY[{i}]  ".center(80, '#'))
        evaluate_tree_partitioning(tree, part, best_cost, root, cp_end, M, N, L, delay, unit)
    return results


def test_greedy_partitioning():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree.gml", destringizer=int)
    tree.graph[NAME] += "-greedy"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=15,
                  N=2,
                  L=math.inf,
                  delay=10)
    run_test(**params)


@pytest.mark.skip("No failed input tree is provided.")
def test_failed_greedy_partitioning(graph_path: str, L=math.inf):
    tree = nx.read_gml(graph_path, destringizer=int)
    tree.graph[NAME] += "-greedy"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  N=2,
                  L=L,
                  delay=10)
    run_test(**params)


def test_random_greedy_partitioning(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-greedy"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=6,
                  N=2,
                  L=math.inf,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    test_greedy_partitioning()
    # test_failed_greedy_partitioning("failed_tree_random_tree_1659449915.340366.gml", L=396)
    # test_random_greedy_partitioning()
