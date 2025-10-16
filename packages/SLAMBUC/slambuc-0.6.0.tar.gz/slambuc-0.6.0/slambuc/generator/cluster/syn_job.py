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
import collections
import importlib.resources
import itertools
import math
import pickle
import random
import typing

import pandas as pd
import scipy

# Random job generation source code is moved from package *spar* with adaptations to newer versions of Python3.11
# and Scipy 1.10.  See also: https://github.com/All-less/trace-generator/blob/master/spar/generate.py

HIST_DATA_DIR = importlib.resources.files("slambuc.generator.cluster").joinpath("hist")
DIST_CACHE = {}


def draw(hist_name: str, num: int = 1, path: typing.Iterable = tuple(), ndigits: int = 2, positive: bool = True,
         output_integer: bool = False, seed: int = None) -> list[int | float]:
    """
    Draw random samples from a given distribution.

    Random job generation source code is moved from package *spar* with adaptations to newer versions of Python3.11
    and Scipy 1.10.  See also: https://github.com/All-less/trace-generator/blob/master/spar/generate.py
    """
    if hist_name not in DIST_CACHE:
        with (HIST_DATA_DIR / f"{hist_name}.pkl").open('rb') as f:
            hist = pickle.load(f)
            if isinstance(hist, dict):
                DIST_CACHE[hist_name] = {num: scipy.stats.rv_histogram(h, density=False, seed=seed)
                                         for num, h in hist.items()}
            else:
                DIST_CACHE[hist_name] = scipy.stats.rv_histogram(hist, density=False, seed=seed)
    dist = DIST_CACHE[hist_name]
    for p in path:
        dist = dist[p]
    samples = []
    while len(samples) < num:
        data = round(dist.rvs(), ndigits=None if output_integer else ndigits)
        if positive and data <= 0:
            continue
        samples.append(data)
    return samples


def random_levels(num_nodes: int, seed: int) -> list[int]:
    cpl = min(num_nodes, draw("cpl_hist", path=(min(num_nodes, 35),), output_integer=True, seed=seed)[0])
    levels = draw("level_hist", num=num_nodes - cpl, output_integer=True, path=(min(cpl, 20),), seed=seed)
    levels.extend(range(1, cpl + 1))
    return levels


def random_dag(num_nodes: int, seed: int = None) -> dict[int, list[int]]:
    if num_nodes == 1:
        return {1: []}
    # randomly select a critical path length and assign nodes along it
    nodes = collections.defaultdict(list)
    for n, l in enumerate(sorted(random_levels(num_nodes, seed=seed)), start=1):
        nodes[l].append(n)
    # randomly generate edges
    parents = {n: [] for n in range(1, num_nodes + 1)}
    for l in range(1, len(nodes)):
        for n in nodes[l]:
            for c in set(random.sample(nodes[l + 1], math.ceil(len(nodes[l + 1]) / len(nodes[l]) * 3 / 4))):
                parents[c].append(n)
    return parents


def random_job(task_num: int = None, seed: int = None) -> pd.DataFrame:
    random.seed(seed)
    if task_num is None:
        task_num = draw("task_num_hist", num=1, seed=seed, output_integer=True)[0]
    job_dag = random_dag(task_num, seed)  # { <task_1>: [ <parent_1, parent_2>, ... ], ... }
    # generate task_name, duration, plan_cpu, plan_mem, inst_num for each task
    task_info = zip(["_".join(itertools.chain((f"T{k}",), map(str, v))) for k, v in job_dag.items()],
                    draw("task_duration_hist", num=task_num, seed=seed, output_integer=True),
                    draw("task_cpu_hist", num=task_num, seed=seed),
                    draw("task_mem_hist", num=task_num, seed=seed),
                    draw("instance_num_hist", num=task_num, seed=seed, output_integer=True))
    return pd.DataFrame(task_info, columns=('task', 'duration', 'cpu', 'mem', 'num'))
