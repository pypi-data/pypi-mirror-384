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
import tabulate

from slambuc.alg.app import NAME
from slambuc.alg.tree.serial.pseudo import pseudo_btree_partitioning, pseudo_ltree_partitioning
from slambuc.alg.util import ipostorder_dfs, ileft_right_dfs
from slambuc.misc.plot import draw_tree
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import evaluate_ser_tree_partitioning


def test_btree_traversal(draw: bool = True):
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_pseudo"
    subcases = []
    for p, v in ipostorder_dfs(tree, 1):
        # print(f"({p=} -->)  [{v}]")
        subcases.append([f"{p}     -", f"[{v}]", 0])
        for i, b in enumerate(tree.succ[v], start=1):
            # print(f"({p=} -->)  [{v=}]  --({i=})-->  {b=}")
            subcases.append([f"{p}     -", f"[{v}]", f"--({i})-->", f"[{b}]"])
    print(tabulate.tabulate(subcases, headers=['p', 'v', 'i', 'b'], stralign='center', tablefmt='presto'))
    if draw:
        draw_tree(tree)


def test_ltree_traversal(draw: bool = True):
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_pseudo"
    subcases = []
    for p, n in ipostorder_dfs(tree, 1):
        subcases.append([f"T[{n}]"])
        for (u, v_p), b_p, (v, b) in ileft_right_dfs(tree, n):
            subcases.append([])
            subcases.append([None, None, "|-->", f"({v_p})" if v_p else None, "|-->",
                             f"({b_p})" if b_p else None])
            subcases.append([None, u if v != n else f"({p})", "-------->", v, "-------->", b])
    print(tabulate.tabulate(subcases, headers=['n', 'u', '', 'v', '', 'b'], stralign='right', tablefmt='presto'))
    print("Iteration for the whole tree:")
    for (u, v_p), b_p, (v, b) in ileft_right_dfs(tree, 1):
        print(u, v_p, '-', b_p, '-', v, b)
    if draw:
        draw_tree(tree)


def run_test(tree: nx.DiGraph, M: int, L: int, root: int = 1, cp_end: int = None, delay: int = 10):
    partition, opt_cost, opt_lat = pseudo_btree_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, partition, opt_cost, opt_lat, root, cp_end, M, L, delay)
    partition, opt_cost, opt_lat = pseudo_ltree_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, partition, opt_cost, opt_lat, root, cp_end, M, L, delay)
    return partition, opt_cost, opt_lat


def test_ser_tree_pseudo_partitioning():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_pseudo"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=math.inf,
                  # L = 430,
                  delay=10)
    run_test(**params)


def test_random_tree_partitioning(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-ser_pseudo"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=6,
                  L=math.inf,
                  # L = 430,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    # test_btree_traversal()
    # test_ltree_traversal()
    test_ser_tree_pseudo_partitioning()
    # test_random_tree_partitioning()
