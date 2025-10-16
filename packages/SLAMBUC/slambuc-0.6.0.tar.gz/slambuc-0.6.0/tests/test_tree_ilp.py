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
from slambuc.alg.app.common import Flavor
from slambuc.alg.tree.layout.ilp import (build_gen_tree_cfg_model, recreate_st_from_gen_xdict, build_gen_tree_mtx_model,
                                         extract_st_from_gen_xmatrix, tree_gen_hybrid_partitioning,
                                         tree_gen_mtx_partitioning, all_gen_tree_mtx_partitioning)
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import (print_lp_desc, convert_var_dict, print_var_matrix, print_cost_coeffs, print_lat_coeffs,
                               print_pulp_matrix_values, evaluate_gen_tree_partitioning)


def test_gen_cfg_model_creation(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml",
                                save_file: bool = False):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-gen_ilp_cfg"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  L=430,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    _s = time.perf_counter()
    model, X = build_gen_tree_cfg_model(**params)
    _d = time.perf_counter() - _s
    print(f"General CFG model building time: {_d * 1000} ms")
    print("Distribution of configurations:")
    for flavor in X:
        print(f"#### Flavor: {flavor}")
        for i in X[flavor]:
            print(f"{i} -> {len(X[flavor][i])}")
    print("  Generated LP model  ".center(80, '='))
    print_lp_desc(model)
    if save_file:
        model.writeLP("tree_gen_model.lp")


def test_gen_cfg_model_solution():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-gen_ilp_cfg"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  L=430,
                  delay=10)
    print("  Run CBC solver  ".center(80, '='))
    #
    model, X = build_gen_tree_cfg_model(**params)
    solver = pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=True)
    status = model.solve(solver=solver)
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    _s = time.perf_counter()
    ext_partition = recreate_st_from_gen_xdict(tree, X)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {ext_partition = }")
    print(f"{model.solutionTime    = } s")
    print(f"{model.solutionCpuTime = }")


def test_gen_mtx_model_creation(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml",
                                save_file: bool = False):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-gen_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  L=430,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    _s = time.perf_counter()
    model, X = build_gen_tree_mtx_model(**params)
    _d = time.perf_counter() - _s
    print(f"General MTX model building time: {_d * 1000} ms")
    #
    X_f = [convert_var_dict(X[f]) for f in X]
    print("  Decision variables  ".center(80, '='))
    for f, X in zip(params['flavors'], X_f):
        print(f"Flavor: {f}")
        print_var_matrix(X)
    print("  Cost Coefficients  ".center(80, '='))
    for f, X in zip(params['flavors'], X_f):
        print(f"Flavor: {f}")
        print_cost_coeffs(model, X)
    print("  Latency Coefficients  ".center(80, '='))
    for f, X in zip(params['flavors'], X_f):
        print(f"Flavor: {f}")
        print_lat_coeffs(model, X)
    print("  Generated LP model  ".center(80, '='))
    print_lp_desc(model)
    if save_file:
        model.writeLP("tree_gen_mtx_model.lp")


def test_gen_mtx_model_solution():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  L=430,
                  delay=10)
    print("  Run CBC solver  ".center(80, '='))
    #
    print(" General MTX model ".center(80, '='))
    model, X = build_gen_tree_mtx_model(**params)
    solver = pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=True)
    status = model.solve(solver=solver)
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    print("Solution:")
    for f in X:
        print(f"Flavor: {f}")
        print_pulp_matrix_values(convert_var_dict(X[f]))
    #
    _s = time.perf_counter()
    ext_partition = extract_st_from_gen_xmatrix(X)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {ext_partition = }")
    print(f"{model.solutionTime    = } s")
    print(f"{model.solutionCpuTime = }")


def test_gen_mtx_subchain_model_solution():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_ilp_mtx"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  L=430,
                  subchains=True,
                  delay=10)
    print("  Run CBC solver  ".center(80, '='))
    #
    print(" General MTX model ".center(80, '='))
    model, X = build_gen_tree_mtx_model(**params)
    solver = pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=True)
    status = model.solve(solver=solver)
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    print("Solution:")
    for f in X:
        print(f"Flavor: {f}")
        print_pulp_matrix_values(convert_var_dict(X[f]))
    #
    _s = time.perf_counter()
    ext_partition = extract_st_from_gen_xmatrix(X)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {ext_partition = }")
    print(f"{model.solutionTime    = } s")
    print(f"{model.solutionCpuTime = }")
    evaluate_gen_tree_partitioning(tree, ext_partition, 0, 0, 0, [[0, 0, 0]], 0, 0, 0)


########################################################################################################################

def run_test(tree: nx.DiGraph, root: int, flavors: list[Flavor], cp_end: int, L: int, delay: int):
    partition, opt_cost, opt_lat = tree_gen_hybrid_partitioning(tree, root, flavors, L=L, cp_end=cp_end, delay=delay,
                                                                solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False,
                                                                                         msg=False))
    evaluate_gen_tree_partitioning(tree, partition, opt_cost, opt_lat, root, flavors, cp_end, L, delay)
    partition, opt_cost, opt_lat = tree_gen_mtx_partitioning(tree, root, flavors, L=L, cp_end=cp_end, delay=delay,
                                                             solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False,
                                                                                      msg=False))
    evaluate_gen_tree_partitioning(tree, partition, opt_cost, opt_lat, root, flavors, cp_end, L, delay)
    return partition, opt_cost, opt_lat


def test_gen_tree():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-gen_ilp"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  L=430,
                  delay=10)
    run_test(**params)


def test_random_gen_tree(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-gen_ilp"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  L=math.inf,
                  delay=10)
    run_test(**params)


def test_all_gen_tree():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-gen_ilp"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  L=430,
                  delay=10)
    results = all_gen_tree_mtx_partitioning(solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False, msg=False), **params)
    print("Results:")
    for partition, opt_cost, opt_lat in results:
        evaluate_gen_tree_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)


if __name__ == '__main__':
    # test_gen_cfg_model_creation()
    # test_gen_cfg_model_solution()
    # test_gen_mtx_model_creation()
    # test_gen_mtx_model_solution()
    test_gen_mtx_subchain_model_solution()
    #
    # test_gen_tree()
    # test_random_gen_tree()
    #
    # test_all_gen_tree()
