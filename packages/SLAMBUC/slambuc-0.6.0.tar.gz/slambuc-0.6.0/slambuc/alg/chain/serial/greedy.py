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

from slambuc.alg import INFEASIBLE, T_PART_GEN, T_RESULTS
from slambuc.alg.util import ipowerset, split_chain, ser_chain_sublatency, ser_chain_subcost, ser_chain_submemory


def ichain_blocks(memory: list[int], M: int) -> T_PART_GEN:
    """
    Calculates all combinations of chain cuts with respect to the *memory* values and constraint *M*.

    Block memories are calculated by assuming a serialized platform execution model.

    The calculation is improved compared to brute force to only start calculating cuts from minimal cut size *c_min*.

    :param memory:  list of node memory values
    :param M:       upper memory limit
    :return:        Generator over M-feasible cuts.
    """
    n = len(memory)
    for cut in ipowerset(range(1, n), start=(math.ceil(sum(memory) / M) - 1) if 0 < M < math.inf else 0):
        barr = sorted({0}.union(cut))
        # Consider only block with the appropriate size
        valid = [blk for blk in split_chain(barr, n) if ser_chain_submemory(memory, blk[0], blk[-1]) <= M]
        if len(valid) == len(barr):
            yield valid


def greedy_ser_chain_partitioning(runtime: list[int], memory: list[int], rate: list[int], data: list[int],
                                  M: int = math.inf, L: int = math.inf, start: int = 0, end: int = None,
                                  delay: int = 1) -> list[T_RESULTS]:
    """
    Calculates all minimal-cost partitioning outcomes of a given chain by applying exhaustive search.

    Parameters are the same as the partitioning algorithms in ``slambuc.alg.chain.serial.ilp``.

    Block metrics are calculated assuming a serialized platform execution model.

    :param runtime: running times in ms
    :param memory:  memory requirements in MB
    :param rate:    avg. rate of function invocations
    :param data:    input data fetching delay in ms
    :param M:       upper memory bound of the partition blocks (in MB)
    :param L:       latency limit defined on the critical path in the form of subchain[start -> end] (in ms)
    :param delay:   invocation delay between blocks
    :param start:   head node of the latency-limited subchain
    :param end:     tail node of the latency-limited subchain
    :return:        list if min-cost partitions, related optimal cost and latency
    """
    end = end if end is not None else len(runtime) - 1
    best_res, best_cost = [INFEASIBLE], math.inf
    for partition in ichain_blocks(memory, M):
        if (sum_lat := sum(ser_chain_sublatency(runtime, rate, data, blk[0], blk[-1], delay, start, end)
                           for blk in partition)) > L:
            continue
        elif (sum_cost := sum(ser_chain_subcost(runtime, rate, data, blk[0], blk[-1])
                              for blk in partition)) == best_cost:
            best_res.append((partition, sum_cost, sum_lat))
        elif sum_cost < best_cost:
            best_res, best_cost = [(partition, sum_cost, sum_lat)], sum_cost
    return best_res
