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
import pathlib

import networkx as nx

from slambuc.alg.ext.mincut import (min_weight_subchain_split, min_weight_chain_decomposition, min_weight_ksplit,
                                    min_weight_ksplit_clustering)
from slambuc.alg.util import recreate_subchain_blocks
from slambuc.misc.plot import draw_tree
from slambuc.misc.util import evaluate_par_tree_partitioning


def test_min_weight_chain_decomposition(root: int = 1, N: int = 1, cp_end: int = 10, delay: int = 10):
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree.gml", destringizer=int)
    barr = min_weight_subchain_split(tree, root)
    partition = recreate_subchain_blocks(tree, barr)
    print("Partition:", partition)
    partition, sum_cost, sum_lat = min_weight_chain_decomposition(tree, root, N, cp_end, delay)
    evaluate_par_tree_partitioning(tree, partition, sum_cost, sum_lat, root, cp_end, None, None, N, delay, draw=False)
    draw_tree(tree, partition, draw_blocks=True, draw_weights=True)


def test_min_weight_tree_partitioning(k: int = 2, root: int = 1, N: int = 1, cp_end: int = 10, delay: int = 10):
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree.gml", destringizer=int)
    barr = min_weight_ksplit(tree, root, k)
    partition = recreate_subchain_blocks(tree, barr)
    print("Partition", partition)
    partition, sum_cost, sum_lat = min_weight_ksplit_clustering(tree, root, k, N, cp_end, delay)
    evaluate_par_tree_partitioning(tree, partition, sum_cost, sum_lat, root, cp_end, None, None, N, delay, draw=False)
    draw_tree(tree, partition, draw_blocks=True, draw_weights=True)


if __name__ == '__main__':
    # test_min_weight_chain_decomposition()
    test_min_weight_tree_partitioning(k=3)
