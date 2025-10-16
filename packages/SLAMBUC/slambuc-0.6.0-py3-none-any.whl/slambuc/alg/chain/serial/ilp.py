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
import itertools
import math

import pulp as lp

from slambuc.alg import LP_LAT, INFEASIBLE, T_IBLOCK_GEN, T_RESULTS, T_PART
from slambuc.alg.util import (ser_chain_sublatency, split_chain, ser_chain_subcost, iser_mul_factor,
                              ser_chain_submemory)


def ifeasible_greedy_blocks(memory: list[int], M: int | float) -> T_IBLOCK_GEN:
    """
    Generate all feasible (connected) blocks that meet the memory constraint *M* in a greedy manner.

    Block memories are calculated by assuming a serialized platform execution model.

    :param memory:  list of node memory values
    :param M:       upper block memory limit
    :return:        generator of blocks
    """
    n = len(memory)
    yield from ((i, j) for i in range(n) for j in range(i, n) if ser_chain_submemory(memory, i, j) <= M)


def ifeasible_blocks(memory: list[int], M: int | float) -> T_IBLOCK_GEN:
    """
    Generate all feasible (connected) blocks that meet the memory constraint *M* assuming serialized executions.

    :param memory:  list of node memory values
    :param M:       upper block memory limit
    :return:        generator of blocks
    """
    n = len(memory)
    for i in range(n):
        cumsum = 0
        for j in range(i, n):
            if (cumsum := cumsum + memory[j]) > M:
                break
            else:
                yield i, j


def build_chain_cfg_model(runtime: list[int], memory: list[int], rate: list[int], data: list[int],
                          M: int = math.inf, L: int = math.inf, start: int = 0, end: int = None,
                          delay: int = 1) -> tuple[lp.LpProblem, dict[tuple[int, int], lp.LpVariable]]:
    """
    Generate the configuration ILP model for chains.

    Block metrics are calculated assuming serialized platform execution model.

    :return: tuple of the created LP model and the dict of created decision variables
    """
    # Model
    model = lp.LpProblem(name="Chain_Partitioning", sense=lp.LpMinimize)
    # Decision variables
    X = {(b, w): lp.LpVariable(f'x_{b}_{w}', cat=lp.LpBinary) for b, w in ifeasible_blocks(memory, M)}
    # Objective
    model += lp.lpSum(ser_chain_subcost(runtime, rate, data, b, w) * X[b, w] for b, w in X)
    # Feasibility constraints
    for j in range(len(runtime)):
        model += lp.lpSum(X[b, w] for b, w in X if b <= j <= w) == 1, f"C_{j:03d}"
    # Latency constraint
    sum_lat = lp.lpSum(ser_chain_sublatency(runtime, rate, data, b, w, delay, start, end) * X[b, w] for b, w in X)
    if L < math.inf:
        model += sum_lat <= L, LP_LAT
    else:
        # Add redundant constraint to implicitly calculate the latency value
        model += sum_lat >= 0, LP_LAT
    return model, X


def chain_cfg_partitioning(runtime: list[int], memory: list[int], rate: list[int], data: list[int],
                           M: int = math.inf, L: int = math.inf, start: int = 0, end: int = None,
                           delay: int = 1, solver: lp.LpSolver = None, timeout: int = None) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of a chain based on the configuration ILP formalization.

    Block metrics are calculated assuming serialized platform execution model.

    :param runtime: running times in ms
    :param memory:  memory requirements in MB
    :param rate:    avg. rate of function invocations
    :param data:    input data fetching delay in ms
    :param M:       upper memory bound of the partition blocks (in MB)
    :param L:       latency limit defined on the critical path in the form of subchain[start -> end] (in ms)
    :param start:   head node of the latency-limited subchain
    :param end:     tail node of the latency-limited subchain
    :param delay:   invocation delay between blocks
    :param solver:  specific solver class (default: COIN-OR CBC)
    :param timeout: time limit in sec
    :return:        tuple of partitioning blocks, optimal cost, and the calculated latency of the subchain
    """
    end = end if end is not None else len(runtime) - 1
    model, X = build_chain_cfg_model(runtime, memory, rate, data, M, L, start, end, delay)
    solver = solver if solver else lp.PULP_CBC_CMD(mip=True, msg=False)
    solver.timeLimit = timeout
    status = model.solve(solver=solver)
    if status == lp.LpStatusOptimal:
        opt_cost, opt_lat = lp.value(model.objective), lp.value(model.constraints[LP_LAT])
        return extract_blocks_from_xvars(X), opt_cost, L + opt_lat if L < math.inf else opt_lat
    else:
        return INFEASIBLE


def recreate_blocks_from_xvars(X: dict[tuple[int, int], lp.LpVariable], n: int) -> T_PART:
    """
    Extract barrier nodes from variable dict and recreate partitioning blocks.

    :param X:   dict of decision variables
    :param n:   chain size
    :return:    partition blocks
    """
    return split_chain(barr=[b for (b, _), x in X.items() if x.varValue == 1], n=n)


def extract_blocks_from_xvars(X: dict[tuple[int, int], lp.LpVariable]) -> T_PART:
    """
    Extract interval boundaries [b, w] relying on the decision variable's structure.

    :param X:   dict of decision variables
    :return:    partition blocks
    """
    return [list(range(b, w + 1)) for (b, w), x in X.items() if x.varValue == 1]


########################################################################################################################


def build_greedy_chain_mtx_model(runtime: list[int], memory: list[int], rate: list[int],
                                 data: list[int], M: int = math.inf, L: int = math.inf,
                                 delay: int = 1) -> tuple[lp.LpProblem, list[list[lp.LpVariable]]]:
    """
    Generate the matrix ILP model for chains by calculating block metrics greedily using utility functions.

    Block metrics are calculated assuming serialized platform execution model.

    :return: tuple of the created LP model and the dict of created decision variables
    """
    # Model
    model = lp.LpProblem(name="Chain_Partitioning", sense=lp.LpMinimize)
    n = len(runtime)
    # Decision variable matrix
    X = [[lp.LpVariable(f"x_{i}_{j}", cat=lp.LpBinary) for j in range(i + 1)] for i in range(n)]
    # Objective
    sum_cost = lp.LpAffineExpression()
    for j in range(n):
        cost_pre = 0
        for i in range(j, n):
            cost_ji = ser_chain_subcost(runtime, rate, data, j, i)
            sum_cost += (cost_ji - cost_pre) * X[i][j]
            cost_pre = cost_ji
    model += sum_cost
    # Feasibility constraints
    for i in range(n):
        model += lp.lpSum(X[i]) == 1, f"C_f{i:02d}"
    # Knapsack constraints
    if M < math.inf:
        for j in range(n):
            model += lp.lpSum(memory[i] * X[i][j] for i in range(j, n)) <= M, f"C_k{j:02d}"
    # Connectivity constraints
    for j in range(n):
        for i in range(j + 1, n):
            model += X[i - 1][j] - X[i][j] >= 0, f"C_c{j}_{i}"
    # Latency constraint
    sum_lat = lp.LpAffineExpression()
    for j in range(n):
        lat_pre = 0
        for i in range(j, n):
            lat_ji = ser_chain_sublatency(runtime, rate, data, j, i, delay, 0, n - 1)
            sum_lat += (lat_ji - lat_pre) * X[i][j]
            lat_pre = lat_ji
    if L < math.inf:
        model += sum_lat <= L, LP_LAT
    else:
        # Add redundant constraint to implicitly calculate the latency value
        model += sum_lat >= 0, LP_LAT
    return model, X


def build_chain_mtx_model(runtime: list[int], memory: list[int], rate: list[int],
                          data: list[int], M: int = math.inf, L: int = math.inf,
                          delay: int = 1) -> tuple[lp.LpProblem, list[list[lp.LpVariable]]]:
    """
    Generate the matrix ILP model for chains.

    Block metrics are calculated assuming serialized platform execution model.

    :return: tuple of the created model and list of decision variables
    """
    # Model
    model = lp.LpProblem(name="Chain_Partitioning", sense=lp.LpMinimize)
    n = len(runtime)
    # Decision variable matrix
    X = [[lp.LpVariable(f"x_{i}_{j}", cat=lp.LpBinary) for j in range(i + 1)] for i in range(n)]
    # Objective
    model += lp.lpSum(lp.lpSum((rate[j] * data[j] * X[j][j] if i == j else  # Add data fetching to first/barrier node
                                -1 * rate[i] * data[i] * X[i][j],  # Remove caching of prior last node
                                rate[i] * runtime[i] * X[i][j],  # Add runtime cost
                                rate[i + 1] * data[i + 1] * X[i][j] if i < n - 1 else 0))  # Add data caching
                      for j in range(n) for i in range(j, n))
    # Feasibility constraints
    for i in range(n):
        model += lp.lpSum(X[i]) == 1, f"C_f{i:02d}"
    # Knapsack constraints
    if M < math.inf:
        for j in range(n):
            model += lp.lpSum(memory[i] * X[i][j] for i in range(j, n)) <= M, f"C_k{j:02d}"
    # Connectivity constraints
    for j in range(n):
        for i in range(j + 1, n):
            model += X[i - 1][j] - X[i][j] >= 0, f"C_c{j}_{i}"
    # Latency constraint
    sum_lat = lp.LpAffineExpression()
    for j in range(n):
        n_pre = 1
        for i, n_i in enumerate(iser_mul_factor(itertools.islice(rate, j, n)), start=j):
            if i == j:
                # Add data fetching
                sum_lat += n_i * data[j] * X[j][j]
                if j > 0:
                    # Add block invocation delay
                    sum_lat += delay * X[j][j]
            else:
                # Remove prior last node data caching
                sum_lat -= n_pre * data[i] * X[i][j]
            # Add function instances
            sum_lat += n_i * runtime[i] * X[i][j]
            if i < n - 1:
                # Add caching
                sum_lat += n_i * data[i + 1] * X[i][j]
            n_pre = n_i
    if L < math.inf:
        model += sum_lat <= L, LP_LAT
    else:
        # Add redundant constraint to implicitly calculate the latency value
        model += sum_lat >= 0, LP_LAT
    return model, X


def chain_mtx_partitioning(runtime: list[int], memory: list[int], rate: list[int], data: list[int],
                           M: int = math.inf, L: int = math.inf, delay: int = 1, solver: lp.LpSolver = None,
                           timeout: int = None, **kwargs) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of a chain based on the matrix ILP formalization.

    Block metrics are calculated assuming serialized platform execution model.

    :param runtime: running times in ms
    :param memory:  memory requirements in MB
    :param rate:    avg. rate of function invocations
    :param data:    input data fetching delay in ms
    :param M:       upper memory bound of the partition blocks (in MB)
    :param L:       latency limit defined on the critical path in the form of subchain[start -> end] (in ms)
    :param delay:   invocation delay between blocks
    :param solver:  specific solver class (default: COIN-OR CBC)
    :param timeout: time limit in sec
    :return:        tuple of partitioning blocks, optimal cost, and the calculated latency of the subchain
    """
    model, X = build_chain_mtx_model(runtime, memory, rate, data, M, L, delay)
    solver = solver if solver else lp.PULP_CBC_CMD(mip=True, msg=False)
    solver.timeLimit = timeout
    status = model.solve(solver=solver)
    if status == lp.LpStatusOptimal:
        opt_cost, opt_lat = lp.value(model.objective), lp.value(model.constraints[LP_LAT])
        return recreate_blocks_from_xmatrix(X), opt_cost, L + opt_lat if L < math.inf else opt_lat
    else:
        return INFEASIBLE


def recreate_blocks_from_xmatrix(X: list[list[lp.LpVariable]]) -> T_PART:
    """
    Extract barrier nodes from decision variable matrix and recreate partitioning blocks.

    :param X:   matrix of decision variables
    :return:    partition blocks
    """
    return split_chain(barr=list(filter(lambda i: X[i][i].value(), range(len(X)))), n=len(X))


def extract_blocks_from_xmatrix(X: list[list[lp.LpVariable]]) -> T_PART:
    """
    Extract interval boundaries [b, w] directly from decision variable matrix.

    :param X:   matrix of decision variables
    :return:    partition blocks
    """
    return [list(itertools.takewhile(lambda i: X[i][j].value(), range(j, len(X))))
            for j in range(len(X)) if X[j][j].value()]
