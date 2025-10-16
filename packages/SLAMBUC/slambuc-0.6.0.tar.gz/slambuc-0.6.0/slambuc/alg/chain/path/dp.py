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
import functools
import itertools
import math
import typing

import numpy as np

from slambuc.alg import INFEASIBLE, T_BARRS, MEM, CPU, COST, LAT, BARR


class State(typing.NamedTuple):
    """Store block attributes for a given DP subcase."""
    barr: int | None = None  # Barrier/heading node of the last block in the given subcase partitioning
    cost: int = math.inf  # Sum cost of the partitioning
    lat: int = math.inf  # Sum latency of the partitioning regarding the limited subchain[start, end]

    def __repr__(self):
        return repr(tuple(self))


def chain_partitioning(runtime: list, memory: list, rate: list, M: int = math.inf, N: int = math.inf,
                       L: int = math.inf, start: int = 0, end: int = None, delay: int = 1,
                       unit: int = 1, ret_dp: bool = False, unfold: bool = False) -> tuple[
    T_BARRS | list[list[State]], int, int]:
    """
    Calculates minimal-cost partitioning of a chain based on the node properties of *running time*, *memory usage* and
    *invocation rate* with respect to an upper bound **M** on the total memory of blocks and a latency constraint **L**
    defined on the subchain between *start* and *end* nodes.

    Cost calculation relies on the rounding *unit* and number of vCPU cores *N*, whereas platform invocation *delay*
    is used for latency calculations.

    Details in: J. Czentye, I. Pelle and B. Sonkoly, "Cost-optimal Operation of Latency Constrained Serverless
    Applications: From Theory to Practice," NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium,
    Miami, FL, USA, 2023, pp. 1-10, doi: 10.1109/NOMS56928.2023.10154412.

    :param runtime: running times in ms
    :param memory:  memory requirements in MB
    :param rate:    avg. rate of function invocations
    :param M:       upper memory bound of the partition blocks (in MB)
    :param N:       upper CPU core bound of the partition blocks
    :param L:       latency limit defined on the critical path in the form of subchain[start -> end] (in ms)
    :param delay:   invocation delay between blocks
    :param start:   head node of the latency-limited subchain
    :param end:     tail node of the latency-limited subchain
    :param unit:    rounding unit for the cost calculation (default: 100 ms)
    :param ret_dp:  return the calculated DP matrix instead of barrier nodes
    :param unfold:  return full blocks instead of barrier nodes
    :return:        tuple of barrier nodes, sum cost of the partitioning, and the calculated latency on the subchain
    """
    n = len(runtime)
    end = end if end is not None else n - 1

    @functools.lru_cache(maxsize=n - 1)
    def block_memory(_b: int, _w: int) -> int:
        """Calculate memory of block[b, w]"""
        return max(sum(itertools.islice(memory, _b, _w + 1)),
                   functools.reduce(lambda p, i: max(p, max(math.ceil(rate[j] / rate[i]) * memory[j]
                                                            for j in range(i, _w + 1))), reversed(range(_b, _w + 1)),
                                    0))

    @functools.lru_cache(maxsize=n - 1)
    def block_cpu(_b: int, _w: int) -> int:
        """Calculate memory of block[b, w]"""
        # noinspection PyTypeChecker
        r_max = itertools.chain((1,), enumerate(itertools.accumulate(reversed(rate[_b: _w + 1]), max)))
        return functools.reduce(lambda pre, max_i: max(pre, math.ceil(max_i[1] / rate[_w - max_i[0]])), r_max)

    @functools.lru_cache(maxsize=n - 1)
    def block_cost(_b: int, _w: int) -> int:
        """Calculate running time of block[b, w]"""
        return rate[_b] * (math.ceil(sum(runtime[_b: _w + 1]) / unit) * unit)

    @functools.lru_cache(maxsize=n - 1)
    def block_latency(_b: int, _w: int) -> int:
        """Calculate relevant latency for block[b, w]"""
        # Do not consider latency if no intersection
        if end < _b or _w < start:
            return 0
        blk_lat = sum(runtime[max(_b, start): min(_w, end) + 1])
        # Ignore delay if the latency path starts within the subchain
        return delay + blk_lat if start < _b else blk_lat

    # Check lower bound for latency limit
    if L < sum(runtime[start: end + 1]):
        return INFEASIBLE
    # Check if memory constraint allows feasible solutions for the given latency constraint
    k_min = max(math.ceil(sum(memory[start: end + 1]) / M),
                sum(1 for i, j in itertools.pairwise(rate) if math.ceil(j / i) > N))
    k_max = math.floor(min((L - sum(runtime[start: end + 1])) / delay + 1, n))
    if k_max < k_min:
        return INFEASIBLE
    # Check single node partitioning
    if len(runtime) == 1:
        return [0], block_cost(0, 0), block_latency(0, 0)
    # Initialize left triangular part of DP matrix -> DP[i][j][COST, LAT, BARR]
    DP = [[State() for _ in range(i + 1)] for i in range(n)]
    # Initialize default values for grouping the first w nodes into one group
    for w in range(0, n):
        if block_memory(0, w) > M or block_cpu(0, w) > N:
            break
        DP[w][0] = State(0, block_cost(0, w), block_latency(0, w))
    # Calculate Dynamic Programming matrix
    for w in range(1, n):
        for k in range(1, w + 1):
            for b in reversed(range(k, w + 1)):
                # As k decreases, bigger blocks [k, w] will continue violating the memory constraint
                if block_memory(b, w) > M or block_cpu(b, w) > N:
                    break
                if (lat := DP[b - 1][k - 1].lat + block_latency(b, w)) <= L:
                    # Store and overwrite subcases with equal costs (<=) to consider larger blocks for lower latency
                    if (cost := DP[b - 1][k - 1].cost + block_cost(b, w)) <= DP[w][k].cost:
                        DP[w][k] = State(b, cost, lat)
            # If the first w node cannot be partitioned into k blocks due to L, then it cannot be partitioned into k+1
            if DP[w][k - 1].lat < DP[w][k].lat == math.inf:
                break
    # Index of optimal cost partition, the fist one if multiple min values exist
    k_opt = min(range(n), key=lambda x: DP[-1][x].cost)
    _, opt_cost, opt_lat = DP[-1][k_opt]
    if opt_cost < math.inf:
        return DP if ret_dp else extract_blocks(DP, k_opt, unfold), opt_cost, opt_lat
    else:
        return INFEASIBLE


def extract_blocks(DP: list[list[State]], k: int, unfold: bool = False) -> T_BARRS:
    """
    Extract barrier nodes form DP matrix by iteratively backtracking the minimal cost subcases started from *k*.

    :param DP:      DP matrix containing subcase *States*
    :param k:       number of optimal cuts
    :param unfold:  return full blocks instead of barrier nodes
    :return:        list of barrier nodes
    """
    barr = []
    w = len(DP) - 1
    for k in reversed(range(0, k + 1)):
        # The cached b value marks the barrier node of the k. Block and refers the subcase => C[b-1,k-1] + c[b,w]
        b = DP[w][k].barr
        w = b - 1
        barr.append(b)
    barr.reverse()
    return list(list(range(b, w)) for b, w in itertools.pairwise(barr + [len(DP)])) if unfold else barr


########################################################################################################################


def vec_chain_partitioning(runtime: list, memory: list, rate: list, M: int = np.inf, N: int = np.inf, L: int = np.inf,
                           start: int = 0, end: int = None, delay: int = 1, unit: int = 1,
                           ret_dp: bool = False, unfold: bool = False) -> tuple[T_BARRS | np.ndarray, int, int]:
    """
    Calculates minimal-cost partitioning of a chain based on the node properties of *runtime*, *memory* and *rate* with
    respect to an upper bound **M** on the total memory of blocks and a latency constraint **L** defined on the subchain
    between *start* and *end* nodes leveraging vectorized operations.

    Cost calculation relies on the rounding *unit* and number of vCPU cores *N*, whereas platform invocation *delay*
    is used for latency calculations.

    Details in: J. Czentye, I. Pelle and B. Sonkoly, "Cost-optimal Operation of Latency Constrained Serverless
    Applications: From Theory to Practice," NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium,
    Miami, FL, USA, 2023, pp. 1-10, doi: 10.1109/NOMS56928.2023.10154412.

    :param runtime: running times in ms
    :param memory:  memory requirements in MB
    :param rate:    avg. rate of function invocations
    :param M:       upper memory bound of the partition blocks (in MB)
    :param N:       upper CPU core bound of the partition blocks
    :param L:       latency limit defined on the critical path in the form of subchain[start -> end] (in ms)
    :param delay:   invocation delay between blocks
    :param start:   head node of the latency-limited subchain
    :param end:     tail node of the latency-limited subchain
    :param unit:    rounding unit for the cost calculation (default: 100 ms)
    :param ret_dp:  return the calculated DP matrix instead of the barrier nodes
    :param unfold:  return full blocks instead of barrier nodes
    :return:        tuple of barrier nodes, sum cost of the partitioning, and the calculated latency on the subchain
    """
    n = len(runtime)
    end = end if end is not None else n - 1

    def block_memory(_b: int, _w: int, cumsum: list, from_left=False) -> int:
        """Calculate memory of a block from the cumulative sum of block[v+1, w] or block[b, v-1]"""
        if from_left:
            cumsum[MEM][0] += memory[_w]  # Function binary preloading
            return max(cumsum[MEM][0],
                       functools.reduce(lambda p, i: max(p, max(math.ceil(rate[j] / rate[i]) * memory[j]
                                                                for j in range(i, _w + 1))),
                                        reversed(range(_b, _w + 1)), 0))
        else:
            cumsum[MEM][0] += memory[_b]  # Function binary preloading
            cumsum[MEM][1] = max(cumsum[MEM][1], max(math.ceil(rate[j] / rate[_b]) * memory[j]
                                                     for j in range(_b, _w + 1)))  # Demand of parallel instances
            return max(cumsum[MEM])

    def block_cpu(_v: int, cumsum: list, from_left=False) -> int:
        """Calculate CPU need of a block from the cached cumulative sum of block[v+1, w]"""
        cumsum[CPU][0] = max(cumsum[CPU][0], rate[_v])
        if from_left:
            return cumsum[CPU][0]
        cumsum[CPU][1] = max(cumsum[CPU][1], math.ceil(cumsum[CPU][0] / rate[_v]))
        return cumsum[CPU][1]

    def block_cost(_v: int, cumsum: list, from_left: bool = False) -> int:
        """Calculate running time of block[b, w] from the cumulative sum of block[v+1, w] or block[0, v-1]"""
        cumsum[COST] += runtime[_v]
        return rate[0 if from_left else _v] * (math.ceil(cumsum[COST] / unit) * unit)

    def block_latency(_b: int, _w: int, cumsum: list, from_left: bool = False) -> int:
        """Calculate relevant latency for block[b, w] from the cumulative sum of block[b+1, w] or block[0, w-1]"""
        # Do not consider latency if no intersection
        if end < _b or _w < start:
            return 0
        if from_left:
            # No need to add the next node if it is outside of intersection
            if end < _w:
                return cumsum[LAT]
            cumsum[LAT] += runtime[_w]
        else:
            # No need to add the next node if it is outside of intersection
            if b < start:
                return cumsum[LAT]
            cumsum[LAT] += runtime[_b]
        # Ignore delay if the latency path starts within the subchain
        return delay + cumsum[LAT] if start < _b else cumsum[LAT]

    # Check lower bound for latency limit
    if L < sum(runtime[start: end + 1]):
        return INFEASIBLE
    # Check if memory constraint allows feasible solutions for the given latency constraint
    k_min = max(math.ceil(sum(memory[start: end + 1]) / M),
                sum(1 for i, j in itertools.pairwise(rate) if math.ceil(j / i) > N))
    k_max = math.floor(min((L - sum(runtime[start: end + 1])) / delay + 1, n))
    if k_max < k_min:
        return INFEASIBLE
    # Define cache for cumulative block attribute calculations: [MEM, COST, LAT]
    __cache = [[0, 0], 0, 0, [0, 0]]
    # Check single node partitioning
    if len(runtime) == 1:
        return [0], block_cost(0, __cache), block_latency(0, 0, __cache)
    # Initialize DP matrix -> DP[i][j][BARR, COST, LAT]
    DP = np.full((n, n, 3), np.inf)
    # Initialize default values for grouping the first w nodes into one group
    for w in range(0, n):
        if block_memory(0, w, __cache, from_left=True) > M or block_cpu(w, __cache, from_left=True) > N:
            break
        DP[w, 0] = np.array((0, block_cost(w, __cache, from_left=True), block_latency(0, w, __cache, from_left=True)))
    # Calculate Dynamic Programming matrix
    for w in range(1, n):
        # Cache for the cumulative sums based on calculation of expanding block's memory, runtime and latency values
        __cache = [[0, 0], 0, 0, [0, 0]]
        for b in reversed(range(1, w + 1)):
            # As k decreases, bigger blocks [k, w] will continue violating the memory constraint
            if block_memory(b, w, __cache) > M or block_cpu(b, __cache) > N:
                break
            subcases = DP[b - 1, :b] + np.array((0, block_cost(b, __cache), block_latency(b, w, __cache)))
            subcases[:, BARR] = b
            # Store and overwrite subcases with equal costs (<=) to consider larger blocks for lower latency
            feasible_idx = np.flatnonzero((subcases[:, LAT] <= L) & (subcases[:, COST] <= DP[w, 1:b + 1, COST]))
            DP[w, feasible_idx + 1] = subcases[feasible_idx]
    # Index of optimal cost partition, the fist one if multiple min values exist
    k_opt = int(np.argmin(DP[n - 1, :, COST]))
    _, opt_cost, opt_lat = DP[n - 1, k_opt]
    if opt_cost < np.inf:
        return DP if ret_dp else extract_vec_blocks(DP, k_opt, unfold), int(opt_cost), int(opt_lat)
    else:
        return INFEASIBLE


def extract_vec_blocks(DP: np.ndarray, k: int, unfold: bool = False) -> T_BARRS:
    """
    Extract barrier nodes from vectorized DP matrix by iteratively backtracking the minimal cost subcases from *k*.

    :param DP:      DP matrix containing subcase *States*
    :param k:       number of optimal cuts
    :param unfold:  return full blocks instead of barrier nodes
    :return:        list of barrier nodes
    """
    barr = []
    B = DP[..., BARR]
    w = len(B) - 1
    for k in reversed(range(0, k + 1)):
        # The cached b value marks the barrier node of the k. block and refers the subcase => C[b-1,k-1] + c[b,w]
        b = int(B[w, k])
        w = b - 1
        barr.append(b)
    barr.reverse()
    return list(list(range(b, w)) for b, w in itertools.pairwise(barr + [len(B)])) if unfold else barr
