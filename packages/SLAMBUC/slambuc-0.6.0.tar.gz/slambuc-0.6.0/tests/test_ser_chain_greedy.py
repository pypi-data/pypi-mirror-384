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

from slambuc.alg.chain.serial.greedy import greedy_ser_chain_partitioning
from slambuc.misc.random import get_random_chain_data
from slambuc.misc.util import evaluate_ser_chain_partitioning, print_ser_chain_summary


def run_test(runtime: list, memory: list, rate: list, data: list, M: int = math.inf, L: int = math.inf, start: int = 0,
             end: int = None, delay: int = 1):
    results = greedy_ser_chain_partitioning(runtime, memory, rate, data, M, L, start, end, delay)
    for i, (partition, opt_cost, opt_lat) in enumerate(results):
        print(f"  GREEDY[{i}]  ".center(80, '#'))
        evaluate_ser_chain_partitioning(partition, opt_cost, opt_lat, runtime, memory, rate, data, M, L, start, end,
                                        delay)
    return results


def test_chain():
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
        print(f"  New latency limit({l})  ".center(80, '='))
        run_test(**params)
    # Infeasible due to M
    params['L'] = 455
    run_test(**params)


def test_random_chain(n: int = 10):
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


if __name__ == '__main__':
    # test_chain()
    # test_random_chain()
    test_partial_ser_chain()
