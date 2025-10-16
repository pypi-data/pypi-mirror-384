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
import pprint
import sys
import time

import pulp
import pytest

from slambuc.alg import LP_LAT
from slambuc.alg.chain.serial.ilp import (build_chain_mtx_model, chain_mtx_partitioning, recreate_blocks_from_xmatrix,
                                          extract_blocks_from_xmatrix, build_greedy_chain_mtx_model)
from slambuc.misc.random import get_random_chain_data
from slambuc.misc.util import (print_lp_desc, evaluate_ser_chain_partitioning, print_ser_chain_summary,
                               print_var_matrix, print_pulp_matrix_values, print_cost_coeffs, print_lat_coeffs,
                               get_cplex_path, get_glpk_path)


def test_mtx_model_creation(save_file: bool = False):
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=50,
                  # start=1,
                  # end=2,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print('=' * 80)
    #
    _s = time.perf_counter()
    model_greedy, X_greedy = build_greedy_chain_mtx_model(**params)
    _d = time.perf_counter() - _s
    print(f"Greedy Model building time: {_d * 1000} ms")
    _s = time.perf_counter()
    model, X = build_chain_mtx_model(**params)
    _d = time.perf_counter() - _s
    #
    print(f"Direct Model building time: {_d * 1000} ms")
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
        model_greedy.writeLP("chain_mtx_model.lp")


def test_mtx_model_solution():
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=150,
                  # start=1,
                  # end=2,
                  delay=10)
    print("  Run CBC solver  ".center(80, '='))
    #
    print(" Greedy model ".center(80, '='))
    model, X = build_greedy_chain_mtx_model(**params)
    status = model.solve(solver=pulp.PULP_CBC_CMD(mip=True, msg=True))
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    #
    print(" Direct model ".center(80, '='))
    model, X = build_chain_mtx_model(**params)
    status = model.solve(solver=pulp.PULP_CBC_CMD(mip=True, msg=True))
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    print(f"Cost/Lat: {pulp.value(model.objective)}, {pulp.value(model.constraints[LP_LAT])}")
    #
    print("Solution:")
    print_pulp_matrix_values(X)
    _s = time.perf_counter()
    rec_partition = recreate_blocks_from_xmatrix(X)
    _d = time.perf_counter() - _s
    print(f"Recreate: {_d * 1000} ms")
    _s = time.perf_counter()
    ext_partition = extract_blocks_from_xmatrix(X)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {rec_partition = }, {ext_partition = }")
    print(f"{model.solutionTime    = } s")
    print(f"{model.solutionCpuTime = }")


@pytest.mark.skipif(get_cplex_path() is None, reason="CPLEX is not available!")
@pytest.mark.skipif(not (sys.version_info < (3, 13)), reason="PY version is not supported!")
def test_mtx_model_solution_cplex():
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=150,
                  start=1,
                  end=2,
                  delay=10)
    print("  Run CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = chain_mtx_partitioning(**params, solver=pulp.CPLEX_PY(mip=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")


@pytest.mark.skipif(get_glpk_path() is None, reason="GLPK is not available!")
def test_mtx_model_solution_glpk():
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=150,
                  start=1,
                  end=2,
                  delay=10)
    print("  Run GLPK solver  ".center(80, '='))
    partition, opt_cost, opt_lat = chain_mtx_partitioning(**params, solver=pulp.GLPK_CMD(mip=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")


def evaluate_mtx_model():
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=50,
                  start=1,
                  end=2,
                  delay=10)
    print("  CBC solver  ".center(80, '='))
    partition, opt_cost, opt_lat = chain_mtx_partitioning(**params, solver=pulp.PULP_CBC_CMD(mip=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_chain_partitioning(partition, opt_cost, opt_lat, **params)
    print("  CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = chain_mtx_partitioning(**params, solver=pulp.CPLEX_PY(mip=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_chain_partitioning(partition, opt_cost, opt_lat, **params)


########################################################################################################################


def run_test(runtime: list, memory: list, rate: list, data: list, M: int = math.inf, L: int = math.inf, delay: int = 1):
    partition, opt_cost, opt_lat = chain_mtx_partitioning(runtime, memory, rate, data, M, L, delay,
                                                          solver=pulp.PULP_CBC_CMD(mip=True, msg=False))
    evaluate_ser_chain_partitioning(partition, opt_cost, opt_lat, runtime, memory, rate, data, M, L, 0, None, delay)
    return partition, opt_cost, opt_lat


def test_ser_chain():
    params = dict(runtime=[20, 40, 50, 20, 70, 40, 50, 60, 40, 10],
                  memory=[3, 3, 2, 1, 2, 1, 2, 1, 2, 3],
                  rate=[1, 1, 2, 2, 1, 3, 1, 2, 1, 3],
                  data=[5, 3, 5, 2, 1, 3, 2, 3, 5, 1],
                  delay=10,
                  M=6,
                  L=800)
    print_ser_chain_summary(params['runtime'], params['memory'], params['rate'], params['data'])
    run_test(**params)


def test_random_ser_chain(n: int = 10):
    runtime, memory, rate, data = get_random_chain_data(n, (10, 100), (1, 3), (1, 3), (1, 5))
    params = dict(runtime=runtime,
                  memory=memory,
                  rate=rate,
                  data=data,
                  delay=10,
                  M=6,
                  L=700)
    print_ser_chain_summary(runtime, memory, rate, data)
    run_test(**params)


def test_partial_ser_chain():
    params = dict(runtime=[20, 40, 50, 20, 70, 40, 50, 60, 40, 10],
                  memory=[3, 3, 2, 1, 2, 1, 2, 1, 2, 3],
                  rate=[1, 1, 2, 2, 1, 3, 1, 2, 1, 3],
                  data=[5, 3, 5, 2, 1, 3, 2, 3, 5, 1],
                  delay=10,
                  M=6,
                  L=math.inf)
    print_ser_chain_summary(params['runtime'], params['memory'], params['rate'], params['data'])
    # No restriction
    run_test(**params)
    # Optimal
    params['L'] = 702
    run_test(**params)
    # Stricter restriction
    for l in [600, 540, 535, 525, 465]:
        params['L'] = l
        run_test(**params)
    # Infeasible due to M
    params['L'] = 455
    run_test(**params)


if __name__ == '__main__':
    # test_mtx_model_creation(save_file=False)
    # test_mtx_model_solution()
    # test_mtx_model_solution_cplex()
    test_mtx_model_solution_glpk()
    # evaluate_mtx_model()
    # test_ser_chain()
    # test_random_ser_chain()
    # test_partial_ser_chain()
