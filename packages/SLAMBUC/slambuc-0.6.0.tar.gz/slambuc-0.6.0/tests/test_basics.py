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
import pathlib
import pprint
import random

import networkx as nx

from slambuc.alg.app import PLATFORM, RUNTIME, DATA
from slambuc.alg.util import recreate_subtree_blocks, split_chain, recreate_subchain_blocks, ihierarchical_nodes, \
    ihierarchical_edges, iclosed_subgraph, isubgraph_bfs
from slambuc.alg.tree.path.state import transform_autonomous_caching
from slambuc.misc.io import encode_service_tree, decode_service_tree, save_trees_to_file, iload_trees_from_file
from slambuc.misc.plot import draw_tree, draw_dag
from slambuc.misc.random import get_random_chain, get_random_tree
from slambuc.misc.util import print_tree_summary, is_compatible


def test_chain_plotter():
    chain = get_random_chain()
    print_tree_summary(chain)
    barr = [1] + sorted(random.sample(range(2, len(chain)), len(chain) // 2))
    partition = split_chain(barr, len(chain))
    print("Partition", partition)
    draw_tree(chain, partition, draw_blocks=True, draw_weights=True)


def test_chain_tree_plotter():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree.gml", destringizer=int)
    print_tree_summary(tree)
    barr = [1, 2, 6, 7, 9]
    partition = recreate_subchain_blocks(tree, barr)
    print("Partition", partition)
    draw_tree(tree, partition, draw_blocks=True, draw_weights=True)


def test_random_tree_plotter():
    tree = get_random_tree()
    print_tree_summary(tree)
    barr = random.sample(list(n for n in tree.nodes if n is not PLATFORM), len(tree) // 3)
    if 1 not in barr:
        barr.append(1)
    partition = recreate_subtree_blocks(tree, barr)
    print("Partition", partition)
    draw_tree(tree, partition, draw_blocks=True, draw_weights=True)


def draw_tree_from_file(file_name: str, draw_weights: bool = False):
    draw_tree(nx.read_gml(file_name, destringizer=int), draw_weights=draw_weights)


def test_tree_enc_dec(n: int = 10):
    tree = get_random_tree(n)
    print_tree_summary(tree)
    draw_tree(tree)
    print("Encoded tree:")
    tdata = encode_service_tree(tree)
    print(tdata)
    for part, (i, j) in zip(("Structure", "Data", "Rate", "Runtime", "Memory"),
                            itertools.pairwise(range(0, len(tdata) + 1, n))):
        print(part, tdata[i:j])
    tree2 = decode_service_tree(tdata)
    print("Decoded tree:")
    print_tree_summary(tree2)
    draw_tree(tree2)
    print(f"Isomorphic: {nx.is_isomorphic(tree, tree2)}")
    print(f"Compatible: {is_compatible(tree, tree2)}")


def test_tree_io():
    trees = [get_random_tree(10) for _ in range(10)]
    pprint.pprint("Generated trees:")
    pprint.pprint(trees)
    print("Saving to file...")
    save_trees_to_file(trees, "test_trees.npy")
    print("Loading trees separately from file...")
    for i, tree in enumerate(iload_trees_from_file("test_trees.npy")):
        print(i, "->", tree)
        print("\tisomorphic:", nx.is_isomorphic(trees[i], tree), "compatible:", is_compatible(trees[i], tree))


def test_cache_transform():
    tree = get_random_tree(10)
    print("Generated tree:")
    print(RUNTIME, pprint.pformat(nx.get_node_attributes(tree, name=RUNTIME)))
    print(DATA, pprint.pformat(nx.get_edge_attributes(tree, name=DATA)))
    tree2 = transform_autonomous_caching(tree, 1)
    print("Transformed tree:")
    print(RUNTIME, pprint.pformat(nx.get_node_attributes(tree2, name=RUNTIME)))


def test_dag_traversal(dag_file: str = pathlib.Path(__file__).parent / "data/graph_test_dag.gml"):
    print(dag_file)
    dag = nx.read_gml(dag_file, destringizer=int)
    draw_dag(dag)
    print("ihierarchical_nodes")
    for v in ihierarchical_nodes(dag, 1):
        print(v)
    print("ihierarchical_edges")
    for v in ihierarchical_edges(dag, 1):
        print(v)
    print("isubgraph_bfs")
    for v in isubgraph_bfs(dag, 1):
        print(v)
    print("iclosed_subgraph")
    for j in dag.nodes:
        print(f"---- {j}")
        for v in iclosed_subgraph(dag, j):
            print(v)


if __name__ == '__main__':
    # test_chain_plotter()
    # test_chain_tree_plotter()
    # test_random_tree_plotter()
    # draw_tree_from_file(pathlib.Path(__file__).parent / "data/graph_test_tree_ser_latency1.gml", draw_weights=False)
    # draw_tree_from_file(pathlib.Path(__file__).parent / "data/graph_test_tree_ser_latency2.gml", draw_weights=True)
    # draw_tree_from_file(pathlib.Path(__file__).parent / "data/graph_test_tree_par_btree.gml", draw_weights=False)
    # draw_tree_from_file(pathlib.Path(__file__).parent / "data/graph_test_tree_par_ltree.gml", draw_weights=False)
    # test_tree_enc_dec()
    # test_tree_io()
    # test_cache_transform()
    # test_dag_traversal()
    test_dag_traversal("failed.gml")
