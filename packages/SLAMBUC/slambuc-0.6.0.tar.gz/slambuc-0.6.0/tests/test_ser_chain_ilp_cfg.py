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
import tabulate

from slambuc.alg.chain.serial.ilp import (ifeasible_blocks, ifeasible_greedy_blocks, build_chain_cfg_model,
                                          chain_cfg_partitioning, recreate_blocks_from_xvars, extract_blocks_from_xvars)
from slambuc.misc.random import get_random_chain_data
from slambuc.misc.util import print_lp_desc, evaluate_ser_chain_partitioning, print_ser_chain_summary, get_cplex_path, \
    get_glpk_path


def test_feasible_blocks(n: int = 10):
    print("  All blocks (greedy)  ".center(80, '='))
    memory, M = [1] * n, math.inf
    print(f"Data: {memory = }, {M = }")
    _start = time.perf_counter()
    blocks = list(ifeasible_greedy_blocks(memory, M))
    _stop = time.perf_counter()
    print(f"All possible blocks count: {n*(n+1)//2 = }")
    print(f"Number of generated blocks: {len(blocks)}")
    print(f"Sum time: {(_stop - _start) * 1000} ms")
    print("  All blocks (filtered)  ".center(80, '='))
    memory, M = [1] * n, math.inf
    print(f"Data: {memory = }, {M = }")
    _start = time.perf_counter()
    blocks = list(ifeasible_blocks(memory, M))
    _stop = time.perf_counter()
    print(f"All possible blocks count: {n*(n+1)//2 = }")
    print(f"Number of generated blocks: {len(blocks)}")
    print(f"Sum time: {(_stop - _start) * 1000} ms")
    pprint.pprint([list(range(b, w + 1)) for (b, w) in blocks])


def test_restricted_feasible_blocks():
    print("  Restricted blocks  ".center(80, '='))
    memory, M = [3, 3, 2, 1, 2, 1, 2, 1, 2, 3], 6
    print(f"Data: {memory = }, {M = }")
    blocks = list(ifeasible_blocks(memory, M))
    print(f"Number of generated blocks: {len(blocks)}")
    mem_data = [memory[b[0]: b[-1] + 1] for b in blocks]
    blocks_data = list(zip(blocks, mem_data, map(sum, mem_data)))
    print(tabulate.tabulate(blocks_data, ('Block', 'Memory', 'Sum')))


def test_cfg_model_creation(save_file: bool = False):
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=50,
                  start=1,
                  end=2,
                  delay=10)
    print("  Test input  ".center(80, '='))
    pprint.pprint(params)
    print("  Feasible blocks  ".center(80, '='))
    for i, (b, w) in enumerate(ifeasible_blocks(params['memory'], params['M'])):
        print(f"{i} ==> {list(range(b, w + 1))}")
    model, _ = build_chain_cfg_model(**params)
    print("  Generated LP model  ".center(80, '='))
    print_lp_desc(model)
    if save_file:
        model.writeLP("chain_cfg_model.lp")


def test_cfg_model_solution():
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=50,
                  start=1,
                  end=2,
                  delay=10)
    print("  Run CBC solver  ".center(80, '='))
    model, X = build_chain_cfg_model(**params)
    status = model.solve()
    print("Solution:")
    print([x.value() for x in X.values()])
    print(f"Partitioning status: {status} / {pulp.LpStatus[status]}")
    _s = time.perf_counter()
    rec_partition = recreate_blocks_from_xvars(X, n=len(params['runtime']))
    _d = time.perf_counter() - _s
    print(f"Recreate: {_d * 1000} ms")
    _s = time.perf_counter()
    ext_partition = extract_blocks_from_xvars(X)
    _d = time.perf_counter() - _s
    print(f"Extract:  {_d * 1000} ms")
    print(f"Partitioning: {rec_partition = }, {ext_partition = }")
    print(f"{model.solutionTime   = } s")
    print(f"{model.solutionCpuTime = }")


@pytest.mark.skipif(get_cplex_path() is None, reason="CPLEX is not available!")
@pytest.mark.skipif(not (sys.version_info < (3, 13)), reason="PY version is not supported!")
def test_cfg_model_solution_cplex():
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=50,
                  start=1,
                  end=2,
                  delay=10)
    print("  Run CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = chain_cfg_partitioning(**params, solver=pulp.CPLEX_PY(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")


@pytest.mark.skipif(get_glpk_path() is None, reason="GLPK is not available!")
def test_cfg_model_solution_glpk():
    params = dict(runtime=[20, 10, 30, 20],
                  memory=[3, 3, 2, 1],
                  rate=[1, 2, 2, 1],
                  data=[5, 2, 5, 3],
                  M=6,
                  L=50,
                  start=1,
                  end=2,
                  delay=10)
    print("  Run GLPK solver  ".center(80, '='))
    partition, opt_cost, opt_lat = chain_cfg_partitioning(**params, solver=pulp.GLPK_CMD(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")


def evaluate_cfg_model():
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
    partition, opt_cost, opt_lat = chain_cfg_partitioning(**params, solver=pulp.PULP_CBC_CMD(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_chain_partitioning(partition, opt_cost, opt_lat, **params)
    print("  CPLEX solver  ".center(80, '='))
    partition, opt_cost, opt_lat = chain_cfg_partitioning(**params, solver=pulp.CPLEX_PY(mip=True, msg=True))
    print(f"Partitioning: {partition}, {opt_cost = }, {opt_lat = }")
    evaluate_ser_chain_partitioning(partition, opt_cost, opt_lat, **params)


########################################################################################################################


def run_test(runtime: list, memory: list, rate: list, data: list, M: int = math.inf, L: int = math.inf, start: int = 0,
             end: int = None, delay: int = 1):
    partition, opt_cost, opt_lat = chain_cfg_partitioning(runtime, memory, rate, data, M, L, start, end, delay,
                                                          solver=pulp.PULP_CBC_CMD(mip=True, msg=False))
    evaluate_ser_chain_partitioning(partition, opt_cost, opt_lat, runtime, memory, rate, data, M, L, start, end, delay)
    return partition, opt_cost, opt_lat


def test_ser_chain():
    params = dict(runtime=[20, 40, 50, 20, 70, 40, 50, 60, 40, 10],
                  memory=[3, 3, 2, 1, 2, 1, 2, 1, 2, 3],
                  rate=[1, 1, 2, 2, 1, 3, 1, 2, 1, 3],
                  data=[5, 3, 5, 2, 1, 3, 2, 3, 5, 1],
                  delay=10,
                  M=6,
                  L=800,
                  start=0,
                  end=9)
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
                  L=700,
                  start=0,
                  end=n - 1)
    print_ser_chain_summary(runtime, memory, rate, data)
    run_test(**params)


def test_partial_ser_chain():
    params = dict(runtime=[20, 40, 50, 20, 70, 40, 50, 60, 40, 10],
                  memory=[3, 3, 2, 1, 2, 1, 2, 1, 2, 3],
                  rate=[1, 1, 2, 2, 1, 3, 1, 2, 1, 3],
                  data=[5, 3, 5, 2, 1, 3, 2, 3, 5, 1],
                  delay=10,
                  M=6,
                  L=math.inf,
                  start=0,
                  end=9)
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
    # test_feasible_blocks(n=20)
    # test_restricted_feasible_blocks()
    # test_cfg_model_creation(save_file=False)
    # test_cfg_model_solution()
    test_cfg_model_solution_cplex()
    # test_cfg_model_solution_glpk()
    # evaluate_cfg_model()
    # test_ser_chain()
    # test_random_ser_chain()
    # test_partial_ser_chain()
