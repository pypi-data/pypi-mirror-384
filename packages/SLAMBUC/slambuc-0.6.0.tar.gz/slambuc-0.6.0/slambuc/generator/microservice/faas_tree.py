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
import importlib.resources
import itertools
import pathlib
import random
import typing
from collections.abc import Generator

import networkx as nx
import numpy as np
import scipy

from slambuc.alg.app import *
from slambuc.generator.microservice.power_ba_graph import generate_power_ba_graph
from slambuc.misc.io import load_hist_params, save_trees_to_file

# Distribution parameters of Serverless functions
# See also: https://dl.acm.org/doi/10.5555/3489146.3489160
# Avg. function execution time in sec ~ Log-Normal(mu, sigma)
RT_MU = -0.38
RT_SIGMA = 2.36
# Scale down execution time values (recorded in sec) one magnitude lower compared to microservice components
RT_DIST = scipy.stats.lognorm(s=RT_SIGMA, loc=0.0, scale=np.exp(RT_MU) * 100)

# Avg. function memory demand in MB ~ Burr(c, k, lambda)
MEM_C = 11.652
MEM_K = 0.221
MEM_LAMBDA = 107.083
MEM_DIST = scipy.stats.burr12(c=MEM_C, d=MEM_K, loc=0.0, scale=MEM_LAMBDA)

# Empirical distribution parameters of function calls extracted from Alibaba traces
# See also: https://github.com/alibaba/clusterdata/tree/master/cluster-trace-microservices-v2021
HIST_DIR = importlib.resources.files("slambuc.generator.microservice").joinpath("hist")
# Invocation rate per services
RATE_HIST_NAME = "func_inv_rate_hist"
RATE_DIST = scipy.stats.rv_histogram(load_hist_params(HIST_DIR, RATE_HIST_NAME), density=True)

# Data R/W overhead
DATA_HIST_NAME = "rw_overhead_hist"
DATA_DIST = scipy.stats.rv_histogram(load_hist_params(HIST_DIR, DATA_HIST_NAME), density=True)

# Tree structure parameters of preferential attachment (Alpha) and attractiveness of leafs (a)
PREF_ATT_LOW, PREF_ATT_HIGH = 0.05, 0.9
LEAF_ATTR_LOW, LEAF_ATTR_HIGH = 0.1, 3.25

DEF_FAAS_TREE_PREFIX = f"faas_tree"


def ifunc_attributes(n: int, dist: scipy.stats.rv_continuous, transform: typing.Callable = np.round) -> Generator[int]:
    """
    Generate attribute values of the given size *n* base on the given distribution *dist*.

    :param n:           number of attributes
    :param dist:        build distribution object
    :param transform:   transform function applied on every attribute value
    :return:            generator of attributes
    """
    yield from transform(dist.rvs(size=n)).astype(int)


def get_faas_tree(n: int, Alpha: float = 1.0, a: float = 0.0) -> nx.DiGraph:
    """
    Generate app tree with attributes drawn from the predefined distributions.

    :param n:       number of nodes
    :param Alpha:   power of preferential attachment (default: 1.0)
    :param a:       attractiveness of vertices with no edges (default: 0.0)
    :return:        generated tree
    """
    tree = nx.bfs_tree(generate_power_ba_graph(n=n, m=1, Alpha=Alpha, a=a, root=1), source=1, sort_neighbors=sorted)
    runtimes, memories = ifunc_attributes(n, RT_DIST), ifunc_attributes(n, MEM_DIST)
    rates, data = ifunc_attributes(n, RATE_DIST, transform=np.floor), ifunc_attributes(n, DATA_DIST)
    tree.add_edge(PLATFORM, 1)
    for u, v in nx.dfs_edges(tree, source=PLATFORM):
        tree.nodes[v][RUNTIME], tree.nodes[v][MEMORY] = next(runtimes), next(memories)
        tree[u][v][RATE], tree[u][v][DATA] = next(rates), next(data)
    tree[PLATFORM][1][RATE] = 1
    tree.graph[NAME] = f"faas_tree_n{n}A{Alpha}a{a}"
    return tree


def generate_all_faas_trees(data_dir: str, Alpha: float = PREF_ATT_HIGH, a: float = LEAF_ATTR_HIGH,
                            iteration: int = 100, start: int = 10, end: int = 100, step: int = 10,
                            tree_name: str = DEF_FAAS_TREE_PREFIX):
    """
    Generate Serverless/Faas app trees with attributes from predefined and extracted distributions.

    :param data_dir:    directory of saved trees
    :param Alpha:       power of preferential attachment (default: 1.0)
    :param a:           attractiveness of vertices with no edges (default: 0.0)
    :param iteration:   number of generated trees
    :param start:       minimum of size intervals
    :param end:         maximum of size intervals
    :param step:        step size of intervals
    :param tree_name:   prefix name of tree files
    """
    for min_size, max_size in itertools.pairwise(range(start, end + step, step)):
        print(f"Generating Serverless/FaaS trees with {min_size} <= size <= {max_size}...")
        trees = [get_faas_tree(n=random.randint(min_size, max_size), Alpha=Alpha, a=a)
                 for _ in range(iteration)]
        file_name = pathlib.Path(data_dir, f"{tree_name}_n{min_size}-{max_size}.npy").resolve()
        print(f"Saving trees into {file_name}...")
        save_trees_to_file(trees, file_name, padding=max_size)
