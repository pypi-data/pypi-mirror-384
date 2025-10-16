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
import time

import networkx as nx
import pandas as pd

from slambuc.alg.app import NAME
from slambuc.alg.tree.serial.bicriteria import biheuristic_btree_partitioning, bifptas_ltree_partitioning, \
    bifptas_dual_ltree_partitioning
from slambuc.alg.tree.serial.pseudo import pseudo_btree_partitioning, pseudo_ltree_partitioning
from slambuc.alg.util import recalculate_partitioning
from slambuc.misc.random import get_random_tree
from slambuc.misc.util import evaluate_ser_tree_partitioning


def run_validation_test(tree: nx.DiGraph, M: int, L: int, root: int = 1, cp_end: int = None, delay: int = 10):
    print(" Run pseudo BTree algorithm ".center(80, '#'))
    b_part, b_opt_cost, b_opt_lat = pseudo_btree_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, b_part, b_opt_cost, b_opt_lat, root, cp_end, M, L, delay)
    print(" Run bi-PTAS BTree algorithm ".center(80, '#'))
    bc_part, bc_opt_cost, bc_opt_lat = biheuristic_btree_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, bc_part, bc_opt_cost, bc_opt_lat, root, cp_end, M, L, delay)
    print(" Run pseudo LTree algorithm ".center(80, '#'))
    l_part, l_opt_cost, l_opt_lat = pseudo_ltree_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, l_part, l_opt_cost, l_opt_lat, root, cp_end, M, L, delay)
    print(" Run bi-PTAS LTree algorithm ".center(80, '#'))
    lc_part, lc_opt_cost, lc_opt_lat = bifptas_ltree_partitioning(tree, root, M, L, cp_end, delay)
    evaluate_ser_tree_partitioning(tree, lc_part, lc_opt_cost, lc_opt_lat, root, cp_end, M, L, delay)


def test_ser_bicriteria_tree_partitioning():
    tree = nx.read_gml(pathlib.Path(__file__).parent / "data/graph_test_tree_ser.gml", destringizer=int)
    tree.graph[NAME] += "-ser_bic"
    params = dict(tree=tree,
                  root=1,
                  cp_end=10,
                  M=6,
                  # L=math.inf,
                  L=430,
                  delay=10)
    run_validation_test(**params)


def test_random_bicriteria_tree_partitioning(n: int = 10):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-ser_bic"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=6,
                  L=math.inf,
                  # L = 430,
                  delay=10)
    run_validation_test(**params)


def get_accuracy_stats(n: int = 10, M: int = 6, L: int = math.inf, Epsilon: float = 0.0, Lambda: float = 0.0,
                       stop_failed: bool = False):
    tree = get_random_tree(n)
    # noinspection PyUnresolvedReferences
    tree.graph[NAME] += "-ser_bic"
    params = dict(tree=tree,
                  root=1,
                  cp_end=n,
                  M=M,
                  # L=math.inf,
                  L=L,
                  delay=10,
                  bidirectional=False)
    bic_params: dict = params.copy()
    bic_params.update(Epsilon=Epsilon, Lambda=Lambda)
    #
    # Btree exact
    _s = time.perf_counter()
    btree_part, btree_opt_cost, btree_opt_lat = pseudo_btree_partitioning(**params)
    btree_time = time.perf_counter() - _s
    _s = time.perf_counter()
    # Bi-Btree reference
    b_part, b_opt_cost, b_opt_lat = biheuristic_btree_partitioning(**params)
    bc_exact_time = time.perf_counter() - _s
    _s = time.perf_counter()
    # Bi-Btree
    bc_part, bc_opt_cost, bc_opt_lat = biheuristic_btree_partitioning(**bic_params)
    bc_bic_time = time.perf_counter() - _s
    #
    # Ltree exact
    _s = time.perf_counter()
    ltree_part, ltree_opt_cost, ltree_opt_lat = pseudo_ltree_partitioning(**params)
    ltree_time = time.perf_counter() - _s
    # Bi-Ltree reference
    _s = time.perf_counter()
    l_part, l_opt_cost, l_opt_lat = bifptas_ltree_partitioning(**params)
    lc_exact_time = time.perf_counter() - _s
    _s = time.perf_counter()
    # Bi-Ltree
    lc_part, lc_opt_cost, lc_opt_lat = bifptas_ltree_partitioning(**bic_params)
    lc_bic_time = time.perf_counter() - _s
    #
    # Bi-Ltree dual reference
    _s = time.perf_counter()
    dl_part, dl_opt_cost, dl_opt_lat = bifptas_dual_ltree_partitioning(**params)
    dlc_exact_time = time.perf_counter() - _s
    _s = time.perf_counter()
    # Bi-Ltree dual
    dlc_part, dlc_opt_cost, dlc_opt_lat = bifptas_dual_ltree_partitioning(**bic_params)
    dlc_bic_time = time.perf_counter() - _s
    #
    print(" Results ".center(80, '#'))
    print(f"Btree:     {b_part}")
    print(f"Bi-Btree:  {bc_part}")
    print(f"Ltree:     {l_part}")
    print(f"Bi-Ltree:  {lc_part}")
    print(f"DLtree:    {l_part}")
    print(f"Bi-DLtree: {lc_part}")
    if btree_part:
        print("#### Btree alg execution:")
        print(f"Btree pseudo exact cost:  {btree_opt_cost:>5},  lat: {btree_opt_lat:>5}  "
              f"with time: {btree_time * 1000:>3.4f} ms")
        print(f"Bi-Btree ref. exact cost: {b_opt_cost:>5},  lat: {b_opt_lat:>5}  "
              f"with time: {bc_exact_time * 1000:>3.4f} ms")
    if bc_part:
        print(f"Bi-Btree bicriteria cost: {bc_opt_cost:>5},  lat: {bc_opt_lat:>5}  "
              f"with time: {bc_bic_time * 1000:>3.4f} ms")
        bc_sum_cost, bc_sum_lat = recalculate_partitioning(tree, bc_part, root=params['root'], cp_end=params['cp_end'],
                                                           delay=params['delay'])
        b_cost_err = (bc_sum_cost - btree_opt_cost) / btree_opt_cost
        b_lat_err = (bc_sum_lat - L) / L
        print(f">>>> Errors:   {b_cost_err = :.4f}  (<= {Epsilon=}) [{bc_sum_cost}/{btree_opt_cost=}], "
              f"   {b_lat_err = :.4f}  (<= {Lambda=}) [{bc_sum_lat}/{L=}]")
    else:
        b_cost_err, b_lat_err = 0, 0
    if ltree_part:
        print("#### Ltree alg execution:")
        print(f"Ltree pseudo exact cost:  {ltree_opt_cost:>5},  lat: {ltree_opt_lat:>5},  "
              f"with time: {ltree_time * 1000:>3.4f} ms")
    if lc_part:
        print(f"Bi-Ltree ref. exact cost: {l_opt_cost:>5},  lat: {lc_opt_lat:>5},  "
              f"with time: {lc_exact_time * 1000:>3.4f} ms")
        print(f"Bi-Ltree bicriteria cost: {lc_opt_cost:>5},  lat: {lc_opt_lat:>5},  "
              f"with time: {lc_bic_time * 1000:>3.4f} ms")
        lc_sum_cost, lc_sum_lat = recalculate_partitioning(tree, lc_part, root=params['root'], cp_end=params['cp_end'],
                                                           delay=params['delay'])
        l_cost_err = (lc_sum_cost - ltree_opt_cost) / ltree_opt_cost
        l_lat_err = (lc_sum_lat - L) / L
        print(f">>>> Errors:    {l_cost_err = :.4f}  (<= {Epsilon=}) [{lc_sum_cost}/{ltree_opt_cost=}], "
              f"   {l_lat_err = :.4f}  (<= {Lambda=}) [{lc_sum_lat}/{L=}]")
    else:
        l_cost_err, l_lat_err = 0, 0
    if dlc_part:
        print(f"Bi-Ltree dual ref. cost:  {dl_opt_cost:>5},  lat: {dlc_opt_lat:>5},  "
              f"with time: {dlc_exact_time * 1000:>3.4f} ms")
        print(f"Bi-Ltree dual bic. cost:  {dlc_opt_cost:>5},  lat: {dlc_opt_lat:>5},  "
              f"with time: {dlc_bic_time * 1000:>3.4f} ms")
        dlc_sum_cost, dlc_sum_lat = recalculate_partitioning(tree, dlc_part, root=params['root'],
                                                             cp_end=params['cp_end'], delay=params['delay'])
        dl_cost_err = (dlc_sum_cost - ltree_opt_cost) / ltree_opt_cost
        dl_lat_err = (dlc_sum_lat - L) / L
        print(f">>>> Errors:   {dl_cost_err = :.4f}  (<= {Epsilon=}) [{dlc_sum_cost}/{ltree_opt_cost=}], "
              f"  {dl_lat_err = :.4f}  (<= {Lambda=}) [{dlc_sum_lat}/{L=}]")
    else:
        dl_cost_err, dl_lat_err = 0, 0
    if stop_failed:
        assert all((b_cost_err <= Epsilon if math.isfinite(b_cost_err) else True,
                    l_cost_err <= Epsilon if math.isfinite(l_cost_err) else True,
                    dl_cost_err <= Epsilon if math.isfinite(dl_cost_err) else True,
                    b_lat_err <= Lambda if math.isfinite(b_lat_err) else True,
                    dl_lat_err <= Lambda if math.isfinite(dl_lat_err) else True,
                    l_lat_err <= Lambda if math.isfinite(l_lat_err) else True))
    return ((btree_time * 1000, bc_exact_time * 1000, bc_bic_time * 1000, b_cost_err, b_lat_err),  # Btree stats
            (ltree_time * 1000, lc_exact_time * 1000, lc_bic_time * 1000, l_cost_err, l_lat_err),
            (ltree_time * 1000, dlc_exact_time * 1000, dlc_bic_time * 1000, dl_cost_err, dl_lat_err))  # Ltree stats


def test_accuracy():
    print(get_accuracy_stats())


def stress_test(iteration: int = 100, n: int = 10, M: int = 6, L: int = math.inf, Epsilon: float = 0.5,
                Lambda: float = 0.5, stop_failed: bool = False):
    b_stat, l_stat, dl_stat = zip(*[get_accuracy_stats(n, M, L, Epsilon, Lambda, stop_failed=stop_failed)
                                    for _ in range(iteration)])
    b_df = pd.DataFrame(b_stat, columns=['Btree', 'BiBtree_exact_time', 'BiBtree_time', 'B_omega', 'B_lambda'])
    l_df = pd.DataFrame(l_stat, columns=['Ltree', 'BiLtree_exact_time', 'BiLtree_time', 'L_omega', 'L_lambda'])
    dl_df = pd.DataFrame(dl_stat, columns=['Ltree', 'BiDLtree_exact_time', 'BiDLtree_time',
                                           'Dual_L_omega', 'Dual_L_lambda'])
    pd.set_option('display.expand_frame_repr', False)
    print(" Btree stat ".center(80, '#'))
    print(b_df.describe().transpose())
    print(" Ltree stat ".center(80, '#'))
    print(l_df.describe().transpose())
    print(" Dual Ltree stat ".center(80, '#'))
    print(dl_df.describe().transpose())


if __name__ == '__main__':
    # test_ser_bicriteria_tree_partitioning()
    # test_random_bicriteria_tree_partitioning()
    # test_accuracy(n=10, M=6, L=450, Epsilon=0.5, Lambda=0.2, stop_failed=True)
    # test_accuracy(n=10, M=6, L=math.inf, Epsilon=0.5, Lambda=0.2, stop_failed=True)
    stress_test(iteration=100, n=20, M=20, L=855, Epsilon=0, Lambda=0, stop_failed=True)
    # stress_test(iteration=100, n=40, M=30, L=855, Epsilon=0.5, Lambda=0.2, stop_failed=True)
