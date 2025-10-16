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
import pytest

from slambuc.alg import LP_LAT
from slambuc.alg.app import NAME

try:
    from slambuc.alg.tree.serial.ilp_cplex import (build_greedy_tree_cplex_model, build_tree_cplex_model,
                                                   tree_cplex_partitioning, extract_subtrees_from_cplex_xmatrix,
                                                   build_tree_cfg_cpo_model, CPO_PATH, recreate_subtrees_from_cpo_xdict)
except ImportError:
    pytest.skip(allow_module_level=True)

from slambuc.alg.util import ibacktrack_chain
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import (evaluate_ser_tree_partitioning, print_var_matrix, convert_var_dict,
                               print_cplex_matrix_values, get_cpo_path, get_cplex_path)


@pytest.mark.skipif(get_cpo_path() is None, reason="CPO is not available!")
def test_cpo_model_creation(save_file: bool = False):
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-cplex_ser"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    _s = time.perf_counter()
    model, X = build_tree_cfg_cpo_model(**params)
    _d = time.perf_counter() - _s
    print(f"Greedy CPO Model building time: {_d * 1000} ms")
    #
    print("Summary:")
    model.print_information()
    print("Model:")
    model.export_model(short_output=True)
    if save_file:
        model.export_model("chain_model.lp")


@pytest.mark.skipif(get_cpo_path() is None, reason="CPO is not available!")
def test_cpo_model_solution():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-cplex_ser"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  # L=math.inf,
                  L=430,
                  delay=10)
    model, Xn = build_tree_cfg_cpo_model(**params)
    print("CPO Greedy model")
    model.print_information()
    print("Solve model...")
    solution = model.solve(agent='local', execfile=CPO_PATH,
                           TimeMode='ElapsedTime', LogVerbosity='Verbose', WarningLevel=3,
                           SearchType='DepthFirst', Workers=1)
    print("Solve status:", solution.get_solve_status())
    print("Solution time:", solution.get_solve_time())
    print("Result:")
    solution.print_solution()
    print(f"Cost/Lat: {solution.get_objective_values()[0]} / {solution.get_kpis()[LP_LAT]}")
    _s = time.perf_counter()
    partition = recreate_subtrees_from_cpo_xdict(tree, solution, Xn)
    _d = time.perf_counter() - _s
    print(f"Recreate:  {_d * 1000} ms")
    print(f"Partitioning: {partition = }")


########################################################################################################################


@pytest.mark.skipif(get_cplex_path() is None, reason="CPLEX is not available!")
def test_cplex_model_creation(save_file: bool = False):
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-cplex_ser"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  L=430,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    _s = time.perf_counter()
    model_greedy, X_greedy = build_greedy_tree_cplex_model(**params)
    _d = time.perf_counter() - _s
    print(f"Greedy Model building time: {_d * 1000} ms")
    _s = time.perf_counter()
    model, X = build_tree_cplex_model(**params)
    _d = time.perf_counter() - _s
    print(f"Direct Model building time: {_d * 1000} ms")
    X = convert_var_dict(X)
    X_greedy = convert_var_dict(X_greedy)
    print("  Decision variables  ".center(80, '='))
    print("Greedy:")
    print_var_matrix(X_greedy)
    print("Direct:")
    print_var_matrix(X)
    #
    print("Summary:")
    model.print_information()
    if save_file:
        model.export_as_lp("tree_cplex_model.lp")


@pytest.mark.skipif(get_cplex_path() is None, reason="CPLEX is not available!")
@pytest.mark.skipif(not (sys.version_info < (3, 13)), reason="PY version is not supported!")
def test_cplex_model_solution():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-cplex_ser"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(tree=tree,
                  root=1,
                  cpath=cpath,
                  M=6,
                  # L=math.inf,
                  L=430,
                  delay=10)
    print("Test greedy model")
    model, X = build_greedy_tree_cplex_model(**params)
    model.solve(log_output=True)
    model.print_solution()
    print("  build CPLEX model  ".center(80, '='))
    model, X = build_tree_cplex_model(**params)
    model.print_information()
    print("  Run CPLEX solver  ".center(80, '='))
    solution = model.solve(log_output=True)
    print(f"Cost/Lat: {solution.get_objective_value()} / {model.kpi_value_by_name(LP_LAT)}")
    print("Model report:")
    model.report()
    #
    print("Model solution:")
    model.print_solution()
    print("Solution details:")
    print(model.get_solve_details())
    print_cplex_matrix_values(convert_var_dict(X))
    _s = time.perf_counter()
    ext_partition = extract_subtrees_from_cplex_xmatrix(X)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {ext_partition = }")


########################################################################################################################


def run_test(tree: nx.DiGraph, root: int, cp_end: int, M: int, L: int, delay: int):
    partition, opt_cost, opt_lat = tree_cplex_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, partition, opt_cost, opt_lat, root, cp_end, M, L, delay)
    return partition, opt_cost, opt_lat


@pytest.mark.skipif(get_cplex_path() is None, reason="CPLEX is not available!")
@pytest.mark.skipif(not (sys.version_info < (3, 13)), reason="PY version is not supported!")
def test_ser_tree():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-cplex_ser"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  # L=math.inf,
                  L=430,
                  delay=10)
    run_test(**params)


@pytest.mark.skipif(get_cplex_path() is None, reason="CPLEX is not available!")
@pytest.mark.skipif(not (sys.version_info < (3, 13)), reason="PY version is not supported!")
def test_random_ser_tree(n: int = 10):
    tree = get_random_tree(n)
    tree.graph[NAME] += "-cplex_ser"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=6,
                  L=math.inf,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    # test_cpo_model_creation()
    test_cpo_model_solution()
    #
    # test_cplex_model_creation(save_file=False)
    # test_cplex_model_solution()
    #
    # test_ser_tree()
    # test_random_ser_tree()
