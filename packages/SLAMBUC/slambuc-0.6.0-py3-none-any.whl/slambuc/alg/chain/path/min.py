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

from slambuc.alg import MEM, COST, LAT, CPU, T_BARRS, T_BRESULTS
from slambuc.alg.chain.path.dp import State


def min_chain_partitioning(runtime: list[int], memory: list[int], rate: list[int], M: int = math.inf,
                           N: int = math.inf, L: int = math.inf, start: int = 0, end: int = None,
                           delay: int = 1, unit: int = 1, unfold: bool = False) -> T_BRESULTS:
    """
    Calculates minimal-cost partitioning of a chain based on the node properties of *running time*, *memory usage* and
    *invocation rate* with respect to an upper bound **M** on the total memory of blocks and a latency constraint **L**
    defined on the subchain between *start* and *end* nodes.

    Cost calculation relies on the rounding *unit* and number of vCPU cores *N*, whereas platform invocation *delay*
    is used for latency calculations.

    It gives an optimal result only in case the cost function regarding the chain attributes is subadditive,
    that is k_opt = k_min is guaranteed for each case.

    Instead of full partitioning, it only returns the list of barrier nodes.

    :param runtime: Running times in ms
    :param memory:  memory requirements in MB
    :param rate:    avg. rate of function invocations
    :param M:       upper memory bound of the partition blocks (in MB)
    :param N:       upper CPU core bound of the partition blocks
    :param L:       latency limit defined on the critical path in the form of subchain[start -> end] (in ms)
    :param delay:   invocation delay between blocks
    :param start:   head node of the latency-limited subchain
    :param end:     tail node of the latency-limited subchain
    :param unit:    rounding unit for the cost calculation (default: 100 ms)
    :param unfold:  return full blocks instead of barrier nodes
    :return:        tuple of barrier nodes, sum cost of the partitioning, and the calculated latency on the subchain
    """
    n = len(runtime)
    end = end if end is not None else n - 1

    def block_memory(_b: int, _w: int, cumsum: list) -> int:
        """Calculate memory of a block from the cached cumulative values of block[b+1, w]."""
        cumsum[MEM][0] += memory[_b]  # Function binary preloading
        cumsum[MEM][1] = max(cumsum[MEM][1], max(math.ceil(rate[j] / rate[_b]) * memory[j]
                                                 for j in range(_b, _w + 1)))  # Demand of parallel instances
        return max(cumsum[MEM])

    def block_cpu(_b: int, cumsum: list) -> int:
        """Calculate CPU need of a block from the cached cumulative sum of block[b+1, w]."""
        cumsum[CPU][0] = max(cumsum[CPU][0], rate[_b])
        cumsum[CPU][1] = max(cumsum[CPU][1], math.ceil(cumsum[CPU][0] / rate[_b]))
        return cumsum[CPU][1]

    def block_cost(_b: int, cumsum: list) -> int:
        """Calculate running time of block[b, w] from the cached cumulative sum of block[b+1, w]."""
        cumsum[COST] += runtime[_b]
        return rate[_b] * (math.ceil(cumsum[COST] / unit) * unit)

    def block_latency(_b: int, _w: int, cumsum: list) -> int:
        """Calculate relevant latency for block[b, w] from the cached cumulative sum of block[b+1, w]."""
        # Do not consider latency if no intersection
        if end < _b or _w < start:
            return 0
        if b < start:
            return cumsum[LAT]
        cumsum[LAT] += runtime[_b]
        # Ignore delay if the latency path starts within the subchain
        return delay + cumsum[LAT] if start < _b else cumsum[LAT]

    # Check lower bound for latency limit
    if L < (lat_min := sum(runtime[start: end + 1])):
        return None, None, lat_min
    # Check if memory constraint allows feasible solutions for the given latency constraint
    k_min = max(math.ceil(sum(memory[start: end + 1]) / M),
                sum(1 for i, j in itertools.pairwise(rate) if math.ceil(j / i) > N))
    k_max = math.floor(min((L - sum(runtime[start: end + 1])) / delay + 1, n))
    if k_max < k_min:
        return None, None, None
    # Check single node partitioning
    _cache = [[0, 0], 0, 0, [0, 0]]
    if len(runtime) == 1:
        return [0], block_cost(0, _cache), block_latency(0, 0, _cache)
    # Initialize DP matrix with an additional trailing element for the backward reference of the trivial singleton cases
    DP = [State() for _ in range(n + 1)]
    # Initialize default reference values for the trivial singleton subcases
    DP[-1] = State(None, 0, 0)
    # Calculate Dynamic Programming matrix
    for w in range(0, n):
        # Cache for the cumulative sum that is based calculation of expanding block's memory, runtime and latency values
        _cache = [[0, 0], 0, 0, [0, 1]]
        for b in reversed(range(0, w + 1)):
            # Larger groups will not satisfy the memory constraint M
            if block_memory(b, w, _cache) > M or block_cpu(b, _cache) > N:
                break
            # For the singleton subcases (b=0) the reference values are zero: DP[-1] -> 0
            if (lat := DP[b - 1].lat + block_latency(b, w, _cache)) <= L:
                # Store and overwrite subcases with equal costs (<=) to consider larger blocks for lower latency
                if (cost := DP[b - 1].cost + block_cost(b, _cache)) <= DP[w].cost:
                    DP[w] = State(b, cost, lat)
    return (extract_min_barr(DP, unfold), DP[n - 1].cost, DP[n - 1].lat) if DP[n - 1].cost < math.inf else DP[n - 1]


def extract_min_barr(DP: list[State], unfold: bool = False) -> T_BARRS:
    """
    Extract barrier nodes form DP list by iteratively backtracking minimal cost subcases.

    :param DP:      dynamic programming structure storing intermediate *States*
    :param unfold:  return full blocks instead of barrier nodes
    :return:        list of barrier nodes
    """
    barr = [DP[-2].barr]
    while barr[-1]:
        barr.append(DP[barr[-1] - 1].barr)
    barr.reverse()
    return list(list(range(b, w)) for b, w in itertools.pairwise(barr + [len(DP) - 1])) if unfold else barr
