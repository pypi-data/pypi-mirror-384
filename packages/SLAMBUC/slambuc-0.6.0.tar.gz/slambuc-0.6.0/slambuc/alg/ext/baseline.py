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
import networkx as nx

from slambuc.alg import T_RESULTS, T_PART
from slambuc.alg.app import PLATFORM
from slambuc.alg.util import recalculate_partitioning


def baseline_singleton_partitioning(tree: nx.DiGraph, root: int = 1, N: int = 1, cp_end: int = None,
                                    delay: int = 1, **kwargs) -> T_RESULTS:
    """
    Derive the trivial partitioning of grouping all nodes into one single block.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rate and data
    :param root:    root node of the graph
    :param N:       available CPU core count
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:   invocation delay between blocks
    :return:        tuple of partitioning, reached sum cost and latency on the critical path
    """
    partitioning: T_PART = [sorted(filter(lambda v: v is not PLATFORM, tree))]
    # noinspection PyTypeChecker
    return partitioning, *recalculate_partitioning(tree, partitioning, root, N, cp_end, delay)


def baseline_no_partitioning(tree: nx.DiGraph, root: int = 1, N: int = 1, cp_end: int = None,
                             delay: int = 1, **kwargs) -> T_RESULTS:
    """
    Derive the trivial solution of not merging any of the given tree nodes.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rate and data
    :param root:    root node of the graph
    :param N:       available CPU core count
    :param cp_end:  tail node of the critical path in the form of subchain[root -> cp_end]
    :param delay:   invocation delay between blocks
    :return:        tuple of partitioning, reached sum cost and latency on the critical path
    """
    partitioning = [[v] for v in tree if v is not PLATFORM]
    # noinspection PyTypeChecker
    return partitioning, *recalculate_partitioning(tree, partitioning, root, N, cp_end, delay)
