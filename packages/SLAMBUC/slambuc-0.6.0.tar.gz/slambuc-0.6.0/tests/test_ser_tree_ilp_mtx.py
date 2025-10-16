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
import numpy as np
import pulp
import pytest
import tabulate

from slambuc.alg import LP_LAT
from slambuc.alg.app import NAME, PLATFORM
from slambuc.alg.tree.serial.ilp import (build_tree_mtx_model, tree_mtx_partitioning, recreate_subtrees_from_xmatrix,
                                         extract_subtrees_from_xmatrix, build_greedy_tree_mtx_model)
from slambuc.alg.util import induced_subtrees, ibacktrack_chain
from slambuc.misc.plot import draw_tree
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import (print_lp_desc, evaluate_ser_tree_partitioning, print_var_matrix, get_cplex_path,
                               print_pulp_matrix_values, convert_var_dict, print_cost_coeffs, print_lat_coeffs,
                               get_glpk_path)


def test_reachable_nodes(branch: int = 2, depth: int = 3, random_nodes: int = 0):
    if random_nodes:
        tree = get_random_tree(nodes=random_nodes)
    else:
        tree = nx.balanced_tree(branch, depth, create_using=nx.DiGraph)
        tree.graph[NAME] = f"balanced_tree({branch=},{depth=})"
        tree.add_edge(PLATFORM, 0)
    print("\nReachable nodes:")
    for (_, n), nodes in induced_subtrees(tree, int(bool(random_nodes)), only_nodes=True):
        print(n, '-->', nodes)
    print("\nReachable edges:")
    for (_, n), edges in induced_subtrees(tree, int(bool(random_nodes)), only_nodes=False):
        print(n, '-->', edges)
    reachable = {n: r for (_, n), r in induced_subtrees(tree, int(bool(random_nodes)), only_nodes=True)}
    rm = np.full((len(tree) - 1, len(tree) - 1), None)
    for i, r in reachable.items():
        for j in r:
            coord = (i - 1, j - 1) if random_nodes else (i, j)
            rm[coord] = 1
    print("Reachability Matrix (R):")
    print(tabulate.tabulate(rm, tablefmt='outline'))
    print("Connectivity coefficients (R^T):")
    print(tabulate.tabulate(rm.transpose(), tablefmt='outline'))
    draw_tree(tree)


def test_mtx_model_creation(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml",
                            save_file: bool = False):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-ser_ilp_mtx"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  subchains=True,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    _s = time.perf_counter()
    model_greedy, X_greedy = build_greedy_tree_mtx_model(**params)
    _d = time.perf_counter() - _s
    print(f"Greedy Model building time: {_d * 1000} ms")
    _s = time.perf_counter()
    model, X = build_tree_mtx_model(**params)
    _d = time.perf_counter() - _s
    print(f"Direct Model building time: {_d * 1000} ms")
    X = convert_var_dict(X)
    X_greedy = convert_var_dict(X_greedy)
    print("  Decision variables  ".center(80, '='))
    print("Greedy:")
    print_var_matrix(X_greedy)
    print("Direct:")
    print_var_matrix(X)
    print("  Cost Coefficients  ".center(80, '='))
    print("Greedy:")
    print_cost_coeffs(model_greedy, X_greedy)
    print("Direct:")
    print_cost_coeffs(model, X)
    print("  Latency Coefficients  ".center(80, '='))
    print("Greedy:")
    print_lat_coeffs(model_greedy, X_greedy)
    print("Direct:")
    print_lat_coeffs(model, X)
    print("  Generated LP model  ".center(80, '='))
    print_lp_desc(model_greedy)
    print_lp_desc(model)
    if save_file:
        model.writeLP("tree_mtx_model.lp")


def test_mtx_model_solution(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml"):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-ser_ilp_mtx"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  delay=10)
    print("  Run CBC solver  ".center(80, '='))
    #
    print(" Greedy model ".center(80, '='))
    model, X = build_greedy_tree_mtx_model(**params)
    status = model.solve(solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=True))
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    print("Solution:")
    print_pulp_matrix_values(convert_var_dict(X))
    #
    print(" Direct model ".center(80, '='))
    model, X = build_tree_mtx_model(**params)
    solver = pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=True)
    status = model.solve(solver=solver)
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    #
    print("Solution:")
    print_pulp_matrix_values(convert_var_dict(X))
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    _s = time.perf_counter()
    rec_partition = recreate_subtrees_from_xmatrix(tree, X)
    _d = time.perf_counter() - _s
    print(f"Recreate: {_d * 1000} ms")
    _s = time.perf_counter()
    ext_partition = extract_subtrees_from_xmatrix(X)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {rec_partition = }, {ext_partition = }")
    print(f"{model.solutionTime    = } s")
    print(f"{model.solutionCpuTime = }")


@pytest.mark.skipif(get_cplex_path() is None, reason="CPLEX is not available!")
@pytest.mark.skipif(not (sys.version_info < (3, 13)), reason="PY version is not supported!")
def test_mtx_model_solution_cplex():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_mtx"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  delay=10)
    print("  Run CPLEX solver  ".center(80, '='))
    model, X = build_tree_mtx_model(**params)
    solver = pulp.CPLEX_PY(mip=True, warmStart=False, msg=True)
    status = model.solve(solver=solver)
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    if status == pulp.LpStatusOptimal:
        opt_cost, opt_lat = pulp.value(model.objective), pulp.value(model.constraints[LP_LAT])
        partition = extract_subtrees_from_xmatrix(X)
        opt_lat = params['L'] + opt_lat if params['L'] < math.inf else opt_lat
        print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
        print(f"{model.solutionTime    = } s")
        print(f"{model.solutionCpuTime = } s")
        print(f"{solver.solveTime = } s")
        #
        print("*" * 30)
        print(f"CPLEX model: {solver.solverModel}")
        print("CPLEX stat:", solver.solverModel.get_stats())


@pytest.mark.skipif(get_glpk_path() is None, reason="GLPK is not available!")
def test_mtx_model_solution_glpk():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  delay=10)
    print("  Run GLPK solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_mtx_partitioning(**params, solver=pulp.GLPK_CMD(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")


def evaluate_ilp_mtx_model():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  delay=10)
    print("  CBC solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_mtx_partitioning(**params, solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)
    print("  CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_mtx_partitioning(**params, solver=pulp.CPLEX_PY(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)


def evaluate_ilp_mtx_subchains_model():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  delay=10)
    print("  CBC solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_mtx_partitioning(**params, subchains=True,
                                                         solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)
    print("  CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_mtx_partitioning(**params, subchains=True,
                                                         solver=pulp.CPLEX_PY(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)


########################################################################################################################


def run_test(tree: nx.DiGraph, root: int, cp_end: int, M: int, L: int, delay: int):
    partition, opt_cost, opt_lat = tree_mtx_partitioning(tree, root, M, L, cp_end, delay,
                                                         solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=False))
    evaluate_ser_tree_partitioning(tree, partition, opt_cost, opt_lat, root, cp_end, M, L, delay)
    return partition, opt_cost, opt_lat


def test_ser_tree():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_ilp_mtx"
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
    tree.graph[NAME] += "-ser_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=6,
                  L=math.inf,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    # test_reachable_nodes(random_nodes=0)
    test_mtx_model_creation()
    # test_mtx_model_creation(tree_file="failed_tree_random_tree_1673972740.2507007.gml")
    # test_mtx_model_solution()
    # test_mtx_model_solution_cplex()
    # test_mtx_model_solution_glpk()
    # evaluate_ilp_mtx_model()
    # evaluate_ilp_mtx_subchains_model()
    # test_ser_tree()
    # test_random_ser_tree()
