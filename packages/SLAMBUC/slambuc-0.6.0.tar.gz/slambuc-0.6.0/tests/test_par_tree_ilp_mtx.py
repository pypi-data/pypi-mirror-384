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
import time

import networkx as nx
import pulp

from slambuc.alg import LP_LAT
from slambuc.alg.app import NAME
from slambuc.alg.tree.parallel.ilp import (build_greedy_par_tree_mtx_model, build_par_tree_mtx_model,
                                           tree_par_mtx_partitioning)
from slambuc.alg.tree.serial.ilp import extract_subtrees_from_xmatrix
from slambuc.alg.util import ibacktrack_chain
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import (print_lp_desc, print_var_matrix, evaluate_par_tree_partitioning,
                               print_pulp_matrix_values, convert_var_dict, print_cost_coeffs, print_lat_coeffs)


def test_par_mtx_model_creation(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml",
                                save_file: bool = False):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-par_ilp_mtx"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  N=2,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    _s = time.perf_counter()
    model_greedy, X_greedy = build_greedy_par_tree_mtx_model(**params)
    _d = time.perf_counter() - _s
    print(f"Greedy Model building time: {_d * 1000} ms")
    _s = time.perf_counter()
    model, X = build_par_tree_mtx_model(**params)
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
        model.writeLP("tree_par_mtx_model.lp")


def test_par_mtx_model_solution():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_ilp_mtx"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  N=2,
                  delay=10)
    print("  Run CBC solver  ".center(80, '='))
    #
    print(" Greedy model ".center(80, '='))
    model, X = build_greedy_par_tree_mtx_model(**params)
    status = model.solve(solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=True))
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    print("Solution:")
    print_pulp_matrix_values(convert_var_dict(X))
    #
    print(" Direct model ".center(80, '='))
    model, X = build_par_tree_mtx_model(**params)
    solver = pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=True)
    status = model.solve(solver=solver)
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    #
    print("Solution:")
    print_pulp_matrix_values(convert_var_dict(X))
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    _s = time.perf_counter()
    ext_partition = extract_subtrees_from_xmatrix(X)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {ext_partition = }")
    print(f"{model.solutionTime    = } s")
    print(f"{model.solutionCpuTime = }")


def evaluate_ilp_par_mtx_model():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  N=2,
                  delay=10)
    print("  CBC solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_par_mtx_partitioning(**params,
                                                             solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_par_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)
    print("  CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_par_mtx_partitioning(**params, solver=pulp.CPLEX_PY(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_par_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)


def evaluate_ilp_par_subchain_mtx_model():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  N=2,
                  delay=10)
    print("  CBC solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_par_mtx_partitioning(**params, subchains=True,
                                                             solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_par_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)
    print("  CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = tree_par_mtx_partitioning(**params, subchains=True,
                                                             solver=pulp.CPLEX_PY(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_par_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)


########################################################################################################################

def run_test(tree: nx.DiGraph, root: int, cp_end: int, M: int, L: int, N: int, delay: int):
    partition, opt_cost, opt_lat = tree_par_mtx_partitioning(tree, root, M, L, N, cp_end, delay,
                                                             solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False,
                                                                                      msg=False))
    evaluate_par_tree_partitioning(tree, partition, opt_cost, opt_lat, root, cp_end, M, L, N, delay)
    return partition, opt_cost, opt_lat


def test_par_tree():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  # L = math.inf
                  L=430,
                  N=2,
                  delay=10)
    run_test(**params)


def test_random_par_tree(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-par_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=6,
                  L=math.inf,
                  N=2,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    # test_par_mtx_model_creation()
    # test_par_mtx_model_solution()
    evaluate_ilp_par_mtx_model()
    # evaluate_ilp_par_subchain_mtx_model()
    # test_par_mtx_model_creation(tree_file="failed_random_tree_1675189959.6335204-ser_partition_L358_M6.gml")
    # test_par_tree()
    # test_random_par_tree()
