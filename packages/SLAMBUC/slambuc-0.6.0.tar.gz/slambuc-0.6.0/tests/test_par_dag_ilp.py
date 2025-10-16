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

from slambuc.alg.app import NAME
from slambuc.alg.dag.ilp import (build_greedy_dag_mtx_model, greedy_dag_partitioning, build_dag_mtx_model,
                                 dag_partitioning)
from slambuc.alg.util import ibacktrack_chain
from slambuc.misc.plot import draw_dag
from slambuc.misc.random import get_random_dag
from slambuc.misc.util import (print_lp_desc, print_var_matrix, convert_var_dict, print_cost_coeffs, print_lat_coeffs,
                               evaluate_par_dag_partitioning)


def test_greedy_dag_model_creation(dag_file: str = pathlib.Path(__file__).parent / "data/graph_test_dag.gml",
                                   save_file: bool = False):
    dag = nx.read_gml(dag_file, destringizer=int)
    dag.graph[NAME] += "-greedy_dag_mtx"
    cpath = set(ibacktrack_chain(dag, 1, 10))
    params = dict(dag=dag,
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
    model_greedy, X_greedy = build_greedy_dag_mtx_model(**params)
    _d = time.perf_counter() - _s
    print(f"Greedy Model building time: {_d * 1000} ms")
    X_greedy = convert_var_dict(X_greedy)
    print("  Decision variables  ".center(80, '='))
    print("Greedy:")
    print_var_matrix(X_greedy)
    print("  Cost Coefficients  ".center(80, '='))
    print("Greedy:")
    print_cost_coeffs(model_greedy, X_greedy)
    print("  Latency Coefficients  ".center(80, '='))
    print("Greedy:")
    print_lat_coeffs(model_greedy, X_greedy)
    print("  Generated LP model  ".center(80, '='))
    print_lp_desc(model_greedy)
    if save_file:
        model_greedy.writeLP("tree_par_mtx_model.lp")


def test_dag_model_creation(dag_file: str = pathlib.Path(__file__).parent / "data/graph_test_dag.gml",
                            save_file: bool = False):
    dag = nx.read_gml(dag_file, destringizer=int)
    dag.graph[NAME] += "-dag_mtx"
    cpath = set(ibacktrack_chain(dag, 1, 10))
    params = dict(dag=dag,
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
    model_greedy, X_greedy = build_dag_mtx_model(**params)
    _d = time.perf_counter() - _s
    print(f"Greedy Model building time: {_d * 1000} ms")
    X_greedy = convert_var_dict(X_greedy)
    print("  Decision variables  ".center(80, '='))
    print("Greedy:")
    print_var_matrix(X_greedy)
    print("  Cost Coefficients  ".center(80, '='))
    print("Greedy:")
    print_cost_coeffs(model_greedy, X_greedy)
    print("  Latency Coefficients  ".center(80, '='))
    print("Greedy:")
    print_lat_coeffs(model_greedy, X_greedy)
    print("  Generated LP model  ".center(80, '='))
    print_lp_desc(model_greedy)
    if save_file:
        model_greedy.writeLP("tree_par_mtx_model.lp")


def compare_dag_models(dag_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml"):
    tree = nx.read_gml(dag_file, destringizer=int)
    tree.graph[NAME] += "-dag_mtx"
    cpath = set(ibacktrack_chain(tree, 1, 10))
    params = dict(dag=tree,
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
    model_greedy, X_greedy = build_greedy_dag_mtx_model(**params)
    _d = time.perf_counter() - _s
    print(f"Greedy Model building time: {_d * 1000} ms")
    _s = time.perf_counter()
    model, X = build_dag_mtx_model(**params)
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


def evaluate_greedy_dag_model(file_name: str = "data/graph_test_dag.gml", path_tree: bool = False):
    dag = nx.read_gml(pathlib.Path(__file__).parent / file_name, destringizer=int)
    draw_dag(dag)
    dag.graph[NAME] += f"-dag_mtx{'_path_tree' if path_tree else ''}"
    params = dict(dag=dag,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  N=2,
                  delay=10,
                  path_tree=path_tree)
    print("  CBC solver  ".center(80, '='))
    partition, opt_cost, opt_lat = greedy_dag_partitioning(**params,
                                                           solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_par_dag_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)


def evaluate_dag_model(file_name: str = "data/graph_test_dag.gml", path_tree: bool = False):
    dag = nx.read_gml(pathlib.Path(__file__).parent / file_name, destringizer=int)
    draw_dag(dag)
    dag.graph[NAME] += f"-dag_mtx{'_path_tree' if path_tree else ''}"
    params = dict(dag=dag,
                  root=1,
                  cp_end=10,
                  M=6,
                  L=430,
                  N=2,
                  delay=10,
                  path_tree=path_tree)
    print("  CBC solver  ".center(80, '='))
    partition, opt_cost, opt_lat = dag_partitioning(**params,
                                                    solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_par_dag_partitioning(partition=partition, opt_cost=opt_cost, opt_lat=opt_lat, **params)


########################################################################################################################

def run_test(dag: nx.DiGraph, root: int, cp_end: int, M: int, L: int, N: int, delay: int, path_tree: bool):
    try:
        partition, opt_cost, opt_lat = dag_partitioning(dag, root, M, L, N, cp_end, delay, path_tree,
                                                        solver=pulp.PULP_CBC_CMD(mip=True, warmStart=False,
                                                                                 msg=False))
        evaluate_par_dag_partitioning(dag, partition, opt_cost, opt_lat, root, cp_end, M, L, N, delay)
    except Exception as e:
        print(e)
        nx.write_gml(dag, "failed.gml", stringizer=str)
        return
    return partition, opt_cost, opt_lat


def test_par_dag(path_tree: bool = False):
    dag = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_dag.gml", destringizer=int)
    dag.graph[NAME] += f"-dag_mtx{'_path_tree' if path_tree else ''}"
    params = dict(dag=dag,
                  root=1,
                  cp_end=10,
                  M=6,
                  # L = math.inf
                  L=430,
                  N=2,
                  delay=10,
                  path_tree=path_tree
                  )
    run_test(**params)


def test_random_par_dag(n: int = 10, x: int = 3, path_tree: bool = False):
    dag = get_random_dag(n, x)
    # noinspection PyUnresolvedReferences
    dag.graph[NAME] += f"-dag_mtx{'_path_tree' if path_tree else ''}"
    params = dict(dag=dag,
                  root=1,
                  cp_end=n,
                  M=6,
                  L=math.inf,
                  N=2,
                  delay=10,
                  path_tree=path_tree
                  )
    run_test(**params)


if __name__ == '__main__':
    # test_greedy_dag_model_creation()
    # test_dag_model_creation()
    # test_dag_model_creation("failed.gml")
    # compare_dag_models()
    #
    # evaluate_greedy_dag_model()
    # evaluate_greedy_dag_model(path_tree=True)
    # evaluate_greedy_dag_model("data/graph_test_tree_par.gml")
    # evaluate_dag_model()
    # evaluate_dag_model(path_tree=True)
    # evaluate_dag_model("data/graph_test_tree_par.gml")
    #
    # test_par_dag()
    # test_random_par_dag(path_tree=True)
    test_random_par_dag()
