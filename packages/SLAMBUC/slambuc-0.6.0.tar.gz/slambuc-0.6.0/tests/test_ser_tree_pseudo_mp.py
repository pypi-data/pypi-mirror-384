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
from slambuc.alg.tree.serial.pseudo_mp import (isubtree_cutoffs, isubtree_sync_cutoffs, isubtree_splits, get_cpu_splits,
                                               pseudo_mp_btree_partitioning, pseudo_mp_ltree_partitioning)
from slambuc.misc.plot import draw_tree
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import evaluate_ser_tree_partitioning


def test_cpu_cutoff(tree: nx.DiGraph = None, cut_factor: int = None, draw: bool = True):
    if not tree:
        tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_pseudo_mp"
    cut_factor = cut_factor if cut_factor else math.ceil(math.sqrt(len(tree) - 1))
    #
    bounds = dict(lb=1, ub=math.inf)
    print(f" All non-trivial cutoffs ({bounds}) ".center(80, '='))
    coffs = list(isubtree_cutoffs(tree, root=1, **bounds))
    for i, (e, c) in enumerate(coffs):
        print(f"{i}.  {e[0]} -> {e[1]} : {c}")
    bounds.update(ub=cut_factor)
    print(f" All candidate cutoffs ({bounds}) ".center(80, '='))
    coffs = list(isubtree_cutoffs(tree, root=1, **bounds))
    for i, (e, c) in enumerate(coffs):
        print(f"{i}.  {e[0]} -> {e[1]} : {c}")
    bounds.update(lb=cut_factor - 1)
    print(f" Designated cutoffs ({bounds}) ".center(80, '='))
    coffs = list(isubtree_cutoffs(tree, root=1, **bounds))
    for i, (e, c) in enumerate(coffs):
        print(f"{i}.  {e[0]} -> {e[1]} : {c}")
    bounds.update(lb=cut_factor)
    print(f" Designated cutoffs ({bounds}) ".center(80, '='))
    coffs = list(isubtree_cutoffs(tree, root=1, **bounds))
    for i, (e, c) in enumerate(coffs):
        print(f"{i}.  {e[0]} -> {e[1]} : {c}")
    if draw:
        draw_tree(tree, cuts=[e for e, _ in coffs])


def test_subtree_split(tree: nx.DiGraph = None, size: int = None, draw: bool = True):
    if not tree:
        tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_pseudo_mp"
    size = size if size else math.ceil(math.sqrt(len(tree) - 1))
    #
    bounds = dict(lb=1, ub=size)
    print(f" All candidate cutoffs ({bounds}) ".center(80, '='))
    coffs = list(isubtree_cutoffs(tree, root=1, **bounds))
    for i, (e, c) in enumerate(coffs):
        print(f"{i}.  {e[0]} -> {e[1]} : {c}")
    #
    print(f" Tabu cutoffs ({size}) ".center(80, '='))
    coffs = list(isubtree_sync_cutoffs(tree, root=1, size=size))
    for i, (cut, n_free, sync) in enumerate(coffs):
        print(f"{i}.  {cut[0]} -> {cut[1]} : {n_free}, {sync=}")
    if draw:
        draw_tree(tree, cuts=[c[0] for c in coffs])


def test_rand_cpu_cutoff(n: int = 10, workers: int = None, draw: bool = True):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-ser_pseudo_mp"
    test_cpu_cutoff(tree, draw=False)
    print(f" CPU-based cutoffs ".center(80, '='))
    cuts = get_cpu_splits(tree, 1, workers)
    print(f"Calculated cuts({workers=}):", cuts)
    for i, c in enumerate(cuts):
        print(f"{i}.  {c[0]} -> {c[1]} ")
    if draw:
        draw_tree(tree, cuts=[c for c in cuts])


def test_rand_subtree_splits(n: int = 10, draw: bool = True):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-ser_pseudo_mp"
    test_subtree_split(tree, draw=False)
    cuts = list(isubtree_splits(tree, root=1))
    print(f" Tabu cutoffs ".center(80, '='))
    print(f"Calculated cuts:", cuts)
    for i, (cut, sync) in enumerate(cuts):
        print(f"{i}.  {cut[0]} -> {cut[1]} : {sync=}")
    if draw:
        draw_tree(tree, cuts=[c[0] for c in cuts])


def run_test(tree: nx.DiGraph, M: int, L: int, root: int = 1, cp_end: int = None, delay: int = 10):
    partition, opt_cost, opt_lat = pseudo_mp_btree_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, partition, opt_cost, opt_lat, root, cp_end, M, L, delay)
    partition, opt_cost, opt_lat = pseudo_mp_ltree_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, partition, opt_cost, opt_lat, root, cp_end, M, L, delay)
    return partition, opt_cost, opt_lat


def test_ser_tree_pseudo_partitioning():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_pseudo_mp"
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
    tree.graph[NAME] += "-ser_pseudo_mp"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=6,
                  L=math.inf,
                  # L = 430,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    # test_cpu_cutoff(cut_factor=3)
    # test_subtree_split(size=2)
    # test_subtree_split()
    # test_rand_cpu_cutoff(n=15, workers=3, draw=True)
    # test_rand_cpu_cutoff(n=15, workers=None, draw=True)
    # test_rand_subtree_splits(n=15, draw=True)

    test_ser_tree_pseudo_partitioning()
    # test_random_tree_partitioning()
