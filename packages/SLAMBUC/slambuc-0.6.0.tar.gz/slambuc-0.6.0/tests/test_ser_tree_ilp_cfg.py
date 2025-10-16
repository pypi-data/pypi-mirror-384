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
import pprint
import sys
import time

import networkx as nx
import pulp
import pytest
import tabulate

from slambuc.alg.app import *
from slambuc.alg.tree.serial.ilp import (ifeasible_subtrees, ifeasible_greedy_subtrees, build_tree_cfg_model,
                                         tree_hybrid_partitioning, extract_subtrees_from_xdict,
                                         recreate_subtrees_from_xdict)
from slambuc.alg.util import ibacktrack_chain
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import print_lp_desc, evaluate_ser_tree_partitioning, get_cplex_path, get_glpk_path


def test_feasible_subtrees(branch: int = 2, depth: int = 2):
    tree = nx.balanced_tree(branch, depth, create_using=nx.DiGraph)
    # noinspection PyTypeChecker
    nx.set_node_attributes(tree, 1, MEMORY)
    tree.add_edge(PLATFORM, 0)
    print("  All blocks (exhaustive)  ".center(80, '='))
    print(f"{tree = !s}")
    _start = time.perf_counter()
    blocks = list(ifeasible_greedy_subtrees(tree, root=None, M=math.inf))
    _stop = time.perf_counter()
    print(f"Number of generated blocks: {len(blocks)}")
    print(f"Sum time: {(_stop - _start) * 1000} ms")
    print("  All blocks (bottom-up)  ".center(80, '='))
    print(f"{tree = !s}")
    _start = time.perf_counter()
    blocks = list(ifeasible_subtrees(tree, root=0, M=math.inf))
    _stop = time.perf_counter()
    print(f"Number of generated blocks: {len(blocks)}")
    print(f"Sum time: {(_stop - _start) * 1000} ms")
    pprint.pprint(blocks)


def test_restricted_feasible_subtrees():
    memory, M = {i: m for i, m in enumerate((3, 3, 2, 1, 3, 1, 3, 2, 2, 1, 2, 1, 1, 3, 3, 2))}, 6
    print(f"Data: {memory = }, {M = }")
    tree = nx.balanced_tree(2, 3, create_using=nx.DiGraph)
    nx.set_node_attributes(tree, memory, MEMORY)
    tree.add_edge(PLATFORM, 0)

    print("  Restricted blocks (exhaustive)  ".center(80, '='))
    print(f"{tree = !s}")
    _start = time.perf_counter()
    blocks = list(ifeasible_greedy_subtrees(tree, root=None, M=M))
    _stop = time.perf_counter()
    print(f"Number of generated blocks: {len(blocks)}")
    print(f"Sum time: {(_stop - _start) * 1000} ms")
    mem_data = [[memory[v] for v in b] for _, b in blocks]
    greedy_blocks_data = list(zip(blocks, mem_data, map(sum, mem_data)))
    print(tabulate.tabulate(greedy_blocks_data, ('Block', 'Memory', 'Sum')))

    print("  Restricted blocks (bottom-up)  ".center(80, '='))
    print(f"{tree = !s}")
    _start = time.perf_counter()
    blocks = list(ifeasible_subtrees(tree, root=0, M=M))
    _stop = time.perf_counter()
    print(f"Number of generated blocks: {len(blocks)}")
    print(f"Sum time: {(_stop - _start) * 1000} ms")
    mem_data = [[memory[v] for v in b] for _, b in blocks]
    blocks_data = list(zip(blocks, mem_data, map(sum, mem_data)))
    print(tabulate.tabulate(blocks_data, ('Block', 'Memory', 'Sum')))


def test_model_creation(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml",
                        save_file: bool = False):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-ser_ilp_cfg"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print(f"All unfiltered blocks: {len(list(ifeasible_subtrees(params['tree'], params['root'], math.inf)))}")
    print("  Feasible blocks  ".center(80, '='))
    for i, blk in enumerate(ifeasible_subtrees(params['tree'], params['root'], params['M'])):
        print(f"{i} ==> {blk}")
    model, _ = build_tree_cfg_model(**params)
    print("  Generated LP model  ".center(80, '='))
    # print(model)
    print_lp_desc(model)
    if save_file:
        model.writeLP("tree_cfg_model.lp")


def test_model_solution(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml"):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-ser_ilp_cfg"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  delay=10)
    print("  Run CBC solver  ".center(80, '='))
    model, X = build_tree_cfg_model(**params)
    status = model.solve(solver=pulp.PULP_CBC_CMD(mip=True, msg=True))
    print("Solution:")
    pprint.pprint({x.name: x.varValue for x in model.variables()})
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    _s = time.perf_counter()
    rec_partition = recreate_subtrees_from_xdict(tree, X)
    _d = time.perf_counter() - _s
    print(f"Recreate: {_d * 1000} ms")
    _s = time.perf_counter()
    ext_partition = extract_subtrees_from_xdict(model)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {rec_partition = }, {ext_partition = }")
    print(f"{model.solutionTime    = } s")
    print(f"{model.solutionCpuTime = }")


@pytest.mark.skipif(get_cplex_path() is None, reason="CPLEX is not available!")
@pytest.mark.skipif(not (sys.version_info < (3, 13)), reason="PY version is not supported!")
def test_model_solution_cplex():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_cfg"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  delay=10)
    print("  Run CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_hybrid_partitioning(**params, solver=pulp.CPLEX_PY(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")


@pytest.mark.skipif(get_glpk_path() is None, reason="GLPK is not available!")
def test_model_solution_glpk():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_cfg"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  delay=10)
    print("  Run GLPK solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_hybrid_partitioning(**params, solver=pulp.GLPK_CMD(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")


def evaluate_ilp_cfg_model():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_cfg"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  delay=10)
    print("  CBC solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_hybrid_partitioning(**params, solver=pulp.PULP_CBC_CMD(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)
    print("  CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_hybrid_partitioning(**params, solver=pulp.CPLEX_PY(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)


########################################################################################################################


def run_test(tree: nx.DiGraph, root: int, cp_end: int, M: int, L: int, delay: int):
    partition, opt_cost, opt_lat = tree_hybrid_partitioning(tree, root, M, L, cp_end, delay,
                                                            solver=pulp.PULP_CBC_CMD(mip=True, msg=True))
    evaluate_ser_tree_partitioning(tree, partition, opt_cost, opt_lat, root, cp_end, M, L, delay)
    return partition, opt_cost, opt_lat


def test_ser_tree():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_cfg"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  # L = math.inf
                  L=430,
                  delay=10)
    run_test(**params)


def test_random_ser_tree(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-ser_ilp_cfg"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=6,
                  L=math.inf,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    # test_feasible_subtrees(branch=2, depth=2)
    # test_restricted_feasible_subtrees()
    # test_model_creation(save_file=False)
    # test_model_solution()
    # test_model_solution_cplex()
    # test_model_solution_glpk()
    # evaluate_ilp_cfg_model()
    test_ser_tree()
    # test_random_ser_tree()
