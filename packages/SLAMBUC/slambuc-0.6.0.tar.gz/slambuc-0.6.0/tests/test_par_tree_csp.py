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

import cspy
import networkx as nx

from slambuc.alg import INFEASIBLE
from slambuc.alg.app.common import NAME, Flavor
from slambuc.alg.ext import *
from slambuc.alg.util import ibacktrack_chain
from slambuc.misc.plot import draw_state_dag
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import evaluate_gen_tree_partitioning


def test_par_csp_dag_creation(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml",
                              draw: bool = False, full: bool = False):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  flavors=[Flavor(6, 2, 1)],
                  # cp_end=10,
                  cpath=set(ibacktrack_chain(tree, 1, 10)),
                  # M=6,
                  # L=430,
                  # N=2,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    _s = time.perf_counter()
    models = [ret for ret in ibuild_gen_csp_dag(**params)]
    _d = time.perf_counter() - _s
    print(f"Model building time: sum: {_d * 1000} / avg: {_d * 1000 / len(models)} ms")
    for i, (dag, chains) in enumerate(models):
        print(f"Chain[{i}]:", chains)
        print(f"DAG[{i}]:", dag)
    if draw:
        for dag, chains in models:
            draw_state_dag(dag, chains, draw_weights=full)


def test_par_csp_solution(solver=cspy.BiDirectional, **kwargs):
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  flavors=[Flavor(6, 2, 1)],
                  # cp_end=10,
                  cpath=set(ibacktrack_chain(tree, 1, 10)),
                  # M=6,
                  # L=430,
                  # N=2,
                  delay=10)
    L = 430
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print(f"Latency constraint: {L}")
    runtimes = []
    best_res = INFEASIBLE
    for i, (dag, chains) in enumerate(ibuild_gen_csp_dag(**params)):
        print(f" Run Bidirectional model[{i}] ".center(80, '='))
        print(f"Chain[{i}]:", chains)
        print(f"DAG[{i}]:", dag)
        max_res, min_res = [len(dag.edges), L], [1, 0]
        print(f"Alg params: {max_res=}, {min_res=}")
        _s = time.perf_counter()
        model = solver(dag, max_res, min_res, **kwargs)
        model.run()
        _d = time.perf_counter() - _s
        runtimes.append(_d)
        print(f"Exec. time: {_d * 1000} ms")
        cost, lat = model.total_cost, model.consumed_resources
        print(f"Result[{i}]:", model.path, "cost/lat:", cost, "/", lat)
        if cost is not None and cost < best_res[1]:
            best_res = [extract_grp_from_path(model.path), cost, lat[1]]
            print("New min cost partitioning found!")
    print('=' * 80)
    print(f"Sum time: {sum(runtimes) * 1000} ms")
    print(f"Best result: {best_res[0]} with cost/lat: {best_res[1]} / {best_res[2]}")


def evaluate_csp_model(file_name: str = pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", M: int = 6,
                       N: int = 2, L: int = math.inf):
    tree = nx.read_gml(file_name, destringizer=int)
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  # cp_end=10,
                  cpath=set(ibacktrack_chain(tree, 1, 10)),
                  # M=6,
                  # N=2,
                  flavors=[Flavor(M, N, 1)],
                  L=L,
                  delay=10)
    solvers = [cspy.BiDirectional,  # Bidirectional labelling algorithm with dynamic half-way point [(Tilk at al. 2017]
               cspy.Tabu,  # Simple Tabu-esque algorithm
               cspy.GreedyElim,  # Simple Greedy elimination (eliminates resource infeasible edges iteratively)
               cspy.GRASP,  # Greedy Randomised Adaptive Search Procedure [Ferone et al. 2019]
               # cspy.PSOLGENT # Particle Swarm Optimization [Marinakis et al. 2017] - bugs in swarm initialization
               ]
    runtimes = []
    results = []
    for solver in solvers:
        print(f" {solver.__name__} solver  ".center(80, '='))
        _s = time.perf_counter()
        partition, opt_cost, opt_lat = csp_gen_tree_partitioning(solver=solver, **params)
        runtimes.append(time.perf_counter() - _s)
        results.append((partition, opt_cost, opt_lat))
        evaluate_gen_tree_partitioning(tree, partition, opt_cost, opt_lat, params['root'], params['flavors'],
                                       params['cp_end'], params['L'], params['delay'])
    for solver, rt, (partition, opt_cost, opt_lat) in zip(solvers, runtimes, results):
        print(f"[{solver.__name__}] Exec. time: {rt * 1000} ms")
        print(f"[{solver.__name__}] Partitioning: {partition}, {opt_cost = }, {opt_lat = }")


def test_gen_csp_dag_creation(tree_file: str = pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml",
                              draw: bool = False, full: bool = False):
    tree = nx.read_gml(tree_file, destringizer=int)
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  # cp_end=10,
                  cpath=set(ibacktrack_chain(tree, 1, 10)),
                  # L=430,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    _s = time.perf_counter()
    models = [ret for ret in ibuild_gen_csp_dag(**params)]
    _d = time.perf_counter() - _s
    print(f"Model building time: sum: {_d * 1000} / avg: {_d * 1000 / len(models)} ms")
    for i, (dag, chains) in enumerate(models):
        print(f"Chain[{i}]:", chains)
        print(f"DAG[{i}]:", dag)
    if draw:
        for dag, chains in models:
            draw_state_dag(dag, chains, draw_weights=full)


def test_gen_csp_solution(solver=cspy.BiDirectional, **kwargs):
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  # cp_end=10,
                  cpath=set(ibacktrack_chain(tree, 1, 10)),
                  # L=430,
                  delay=10)
    L = 430
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print(f"Latency constraint: {L}")
    runtimes = []
    best_res = INFEASIBLE
    for i, (dag, chains) in enumerate(ibuild_gen_csp_dag(**params)):
        print(f" Run Bidirectional model[{i}] ".center(80, '='))
        print(f"Chain[{i}]:", chains)
        print(f"DAG[{i}]:", dag)
        max_res, min_res = [len(dag.edges), L], [1, 0]
        print(f"Alg params: {max_res=}, {min_res=}")
        _s = time.perf_counter()
        model = solver(dag, max_res, min_res, **kwargs)
        model.run()
        _d = time.perf_counter() - _s
        runtimes.append(_d)
        print(f"Exec. time: {_d * 1000} ms")
        cost, lat = model.total_cost, model.consumed_resources
        print(f"Result[{i}]:", model.path, "cost/lat:", cost, "/", lat)
        if cost is not None and cost < best_res[1]:
            best_res = [extract_grp_from_path(model.path), cost, lat[1]]
            print("New min cost partitioning found!")
    print('=' * 80)
    print(f"Sum time: {sum(runtimes) * 1000} ms")
    print(f"Best result: {best_res[0]} with cost/lat: {best_res[1]} / {best_res[2]}")


########################################################################################################################


def run_test(tree: nx.DiGraph, root: int, flavors: list[Flavor], cp_end: int, L: int, delay: int):
    _s = time.perf_counter()
    partition, opt_cost, opt_lat = csp_gen_tree_partitioning(tree, root, flavors, L=L, cp_end=cp_end, delay=delay)
    _d = time.perf_counter() - _s
    print(f"Sum time: {_d * 1000} ms")
    evaluate_gen_tree_partitioning(tree, partition, opt_cost, opt_lat, root, flavors, cp_end, L, delay)
    return partition, opt_cost, opt_lat


def test_par_tree():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  flavors=[Flavor(6, 2, 1)],
                  # L = math.inf
                  L=430,
                  delay=10)
    run_test(**params)


def test_random_par_tree(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  flavors=[Flavor(6, 2, 1)],
                  cp_end=n,
                  L=math.inf,
                  delay=10)
    run_test(**params)


def test_gen_tree():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", destringizer=int)
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  cp_end=10,
                  # L = math.inf
                  L=430,
                  delay=10)
    run_test(**params)


def test_random_gen_tree(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-par_csp"
    params = dict(tree=tree,
                  root=1,
                  flavors=[Flavor(6, 1, 1),
                           Flavor(9, 3, 1.1)],  # Higher memory with more core, but 10% more expensive
                  cp_end=n,
                  L=math.inf,
                  delay=10)
    run_test(**params)


if __name__ == '__main__':
    # test_par_csp_dag_creation(draw=True, full=True)
    # test_par_csp_dag_creation(draw=False)
    # test_par_csp_solution(solver=cspy.BiDirectional, direction="forward")
    # test_par_csp_solution(solver=cspy.PSOLGENT)
    # evaluate_csp_model(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", M=6, N=1, L=430)
    # evaluate_csp_model(pathlib.Path(__file__).parent / "data/graph_test_tree_par.gml", M=6, N=2, L=400)
    #
    # test_gen_csp_dag_creation(draw=False)
    # test_gen_csp_dag_creation(draw=True, full=True)
    # test_gen_csp_solution(solver=cspy.BiDirectional, direction="forward")
    #
    # test_par_tree()
    test_random_par_tree(n=30)
    #
    # test_gen_tree()
    # test_random_gen_tree(n=10)
