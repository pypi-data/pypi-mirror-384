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

from slambuc.alg import INFEASIBLE, T_RESULTS, T_PART_GEN
from slambuc.alg.util import ipowerset, split_chain, chain_cost, chain_latency, chain_cpu, chain_memory_opt


def ichain_blocks(memory: list[int], rate: list[int], N: int, M: int) -> T_PART_GEN:
    """
    Calculates all combinations of chain cuts with respect to *memory* and *rate* values and the constraint **M**.

    The calculation is improved compared to brute force to only start calculating cuts from minimal cut size *c_min*.

    :param memory:  list of node memory values
    :param rate:    list of invocation rate values
    :param N:       number of vCPU cores
    :param M:       upper memory limit
    :return:        Generator over M-feasible cuts.
    """
    n = len(memory)
    for cut in ipowerset(range(1, n), start=(math.ceil(sum(memory) / M) - 1) if 0 < M < math.inf else 0):
        barr = sorted({0}.union(cut))
        # Consider only block with the appropriate size
        valid = [blk for blk in split_chain(barr, n)
                 if chain_memory_opt(memory, rate, blk[0], blk[-1]) <= M and chain_cpu(rate, blk[0], blk[-1]) <= N]
        if len(valid) == len(barr):
            yield valid


def greedy_chain_partitioning(runtime: list[int], memory: list[int], rate: list[int], M: int = math.inf,
                              N: int = math.inf, L: int = math.inf, start: int = 0, end: int = None,
                              delay: int = 1, unit: int = 1) -> list[T_RESULTS]:
    """
    Calculates all minimal-cost partitioning outcomes of a given chain by applying exhaustive search.

    Parameters are the same as the partitioning algorithms in ``slambuc.alg.chain.path.mtx``
    and ``slambuc.alg.chain.path.min``.

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
    :return:        list if min-cost partitions, related optimal cost and latency
    """
    n = len(runtime)
    end = end if end is not None else n - 1
    best_res, best_cost = [INFEASIBLE], math.inf
    for partition in ichain_blocks(memory, rate, N, M):
        if (sum_lat := sum(chain_latency(runtime, blk[0], blk[-1], delay, start, end) for blk in partition)) > L:
            continue
        elif (sum_cost := sum(chain_cost(runtime, rate, blk[0], blk[-1], unit) for blk in partition)) == best_cost:
            best_res.append((partition, sum_cost, sum_lat))
        elif sum_cost < best_cost:
            best_res, best_cost = [(partition, sum_cost, sum_lat)], sum_cost
    return best_res
