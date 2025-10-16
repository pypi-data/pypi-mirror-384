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
import itertools
import math
import time
from collections.abc import Generator, Callable

import cspy
import networkx as nx
import numpy as np

from slambuc.alg import INFEASIBLE, T_BLOCK, T_RESULTS
from slambuc.alg.app.common import SEP, ASSIGN, Flavor
from slambuc.alg.util import (leaf_label_nodes, ibacktrack_chain, iflattened_tree, gen_subtree_memory, gen_subtree_cost,
                              gen_subchain_latency, verify_limits)

# Naming convention for state-space DAG required by *cspy* lib
START, END = 'Source', 'Sink'
COST, LAT = 'weight', 'res_cost'


def encode_state(grp: T_BLOCK, flavor: Flavor) -> str:
    """
    Encode DAG node name with flavor's memory as a unique str (hashable).

    :param grp:     partition block
    :param flavor:  assigned *flavor*
    :return:        encoded partition block
    """
    return f"{SEP.join(map(str, grp))}{ASSIGN}{SEP.join(map(str, flavor))}"


def decode_state(name: str) -> tuple[T_BLOCK, Flavor]:
    """
    Decode DAG node name from encoded str into partition block (list of int) and flavor's memory (mem).

    :param name:    encoded partition block
    :return:        decoded block and assigned flavor
    """
    parts = name.rsplit(ASSIGN, maxsplit=1)
    mem, ncore, cf = parts[1].split(SEP, maxsplit=2)
    return list(map(int, parts[0].split(SEP))), Flavor(math.inf if mem == 'inf' else int(mem), int(ncore), float(cf))


def ibuild_gen_csp_dag(tree: nx.DiGraph, root: int = 1, flavors: list[Flavor] = (Flavor(),),
                       exec_calc: Callable[[int, int, int], int] = lambda i, t, n: t,
                       cpath: set[int] = frozenset(), delay: int = 1) -> Generator[tuple[nx.DiGraph, list[int]]]:
    """
    Calculate all state-space DAGs of the given *tree* based on the alternative chain decompositions.

    The given flavors as list of (memory, CPU, cost_factor) tuples define the available memory (and group upper limit),
    available relative vCPU cores and relative cost multiplier.

    :param tree:        app graph annotated with node runtime(ms), memory(MB) and edge rate
    :param root:        root node of the graph
    :param flavors:     list of flavors resources given by the tuple of available *(memory, relative CPU cores)*
    :param exec_calc:   function that calculates the effective runtimes from reference runtime and available CPU cores
    :param cpath:       critical path in the form of subchain[root -> cp_end]
    :param delay:       invocation delay between blocks
    :return:            generated DAG graph and the related nodes of the flattened tree
    """
    # Annotate nodes with reachable leafs of tree
    tree = leaf_label_nodes(tree)
    # Iterate over the feasible chain-flattened tree
    for chains in iflattened_tree(tree, root):
        # Initiate data structure for DAG
        _cache = collections.defaultdict(list)
        _cache.update({START: [START], END: [END]})
        # noinspection PyUnresolvedReferences
        dag = nx.DiGraph(directed=True, n_res=2, **tree.graph)
        # Iterate the subchains backward
        # noinspection PyTypeChecker
        for prev, chain in itertools.pairwise(itertools.chain([_cache[END]], reversed(chains))):
            # Generate the subcases of the given subchain
            for i, b in enumerate(reversed(chain), start=1):
                grp = []
                for j, v in enumerate(chain[-i:], start=1):
                    grp = grp + [v]
                    for f in flavors:
                        # Skip infeasible subcase due to memory constraint
                        if gen_subtree_memory(tree, b, grp, f.ncore) > f.mem:
                            break
                        grp_id = encode_state(grp, f)
                        _cache[b].append(grp_id)
                        # Get starting node of dependent subcases from the cache
                        nxt = prev[0] if v == chain[-1] else chain[-i + j]
                        # Calculate subcase cost and latency
                        grp_cost = round(gen_subtree_cost(tree, b, grp, f.ncore, exec_calc) * f.cfactor)
                        grp_lat = gen_subchain_latency(tree, b, set(grp), cpath, f.ncore, exec_calc)
                        # Add invocation delay for inter-block invocations
                        if b != root and grp_lat > 0:
                            grp_lat += delay
                        # Add connection between related subcases
                        for sc in _cache[nxt]:
                            dag.add_edge(grp_id, sc, **{COST: grp_cost, LAT: np.array([1, grp_lat])})
            # Remove unnecessary subcases from cache
            for p in prev:
                del _cache[p]
        # Add initial connections from START node
        for sc in _cache[root]:
            dag.add_edge(START, sc, **{COST: 0, LAT: np.array([1, 0])})
        yield dag, chains


def csp_tree_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                          N: int = 1, cp_end: int = None, delay: int = 1, exhaustive: bool = True,
                          solver=cspy.BiDirectional, timeout: int = None, **cspargs) -> T_RESULTS:
    """
    Calculate minimal-cost partitioning of a *tree* based on constrained shortest path (CSP) formalization
    without considering flavor assignment.

    Details in: T. Elgamal at al.: “Costless: Optimizing Cost of Serverless Computing through Function Fusion
    and Placement,” in 2018 IEEE/ACM Symposium on Edge Computing (SEC), 2018, pp. 300–312. doi: 10.1109/SEC.2018.00029.

    :param tree:        app tree annotated with node runtime(ms), memory(MB) and edge rate
    :param root:        root node of the graph
    :param M:           upper memory bound of the partition blocks in MB
    :param L:           latency limit defined on the critical path in ms
    :param N:           available CPU core count
    :param cp_end:      tail node of the critical path in the form of subchain[root -> c_pend]
    :param delay:       invocation delay between blocks
    :param exhaustive:  iterate over all topological ordering of the app tree or stop at first feasible solution
    :param solver:      specific solver class (default: cspy.BiDirectional)
    :param timeout:     time limit in sec
    :param cspargs:     additional CSP solver parameters
    :return:            tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    best_res, t_start = INFEASIBLE, time.process_time()
    # Critical path
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    for dag, chains in ibuild_gen_csp_dag(tree, root, [Flavor(M, N, 1.0)], cpath=cpath, delay=delay):
        try:
            model = solver(dag, max_res=[len(dag.edges), L], min_res=[1, 0], time_limit=timeout, **cspargs)
            model.run()
            if model.path is not None and model.total_cost < best_res[1]:
                best_res = (extract_grp_from_path(model.path, False),
                            model.total_cost,
                            float(model.consumed_resources[-1]))
                if not exhaustive:
                    # Stop at first feasible solution
                    break
        except Exception:
            # No feasible solution
            continue
        finally:
            if timeout and time.process_time() - t_start > timeout:
                break
    return best_res


def csp_gen_tree_partitioning(tree: nx.DiGraph, root: int = 1, flavors: list[Flavor] = (Flavor(),),
                              exec_calc: collections.abc.Callable[[int, int, int], int] = lambda i, t, n: t,
                              L: int = math.inf, cp_end: int = None, delay: int = 1, solver=cspy.BiDirectional,
                              timeout: int = None, **cspargs) -> T_RESULTS:
    """
    Calculate minimal-cost partitioning of a *tree* based on constrained shortest path (CSP) formalization with
    incorporated flavor assignment.

    Details in: T. Elgamal at al.: “Costless: Optimizing Cost of Serverless Computing through Function Fusion
    and Placement,” in 2018 IEEE/ACM Symposium on Edge Computing (SEC), 2018, pp. 300–312. doi: 10.1109/SEC.2018.00029.


    :param tree:        app graph annotated with node runtime(ms), memory(MB) and edge rate
    :param root:        root node of the graph
    :param flavors:     list of flavors resources given by the tuple of available *(memory, rel CPU cores, cost factor)*
    :param exec_calc:   function that calculates the effective runtimes from reference runtime and available CPU cores
    :param L:           latency limit defined on the critical path (in ms)
    :param cp_end:      tail node of the critical path in the form of subchain[root -> c_pend]
    :param delay:       invocation delay between blocks
    :param solver:      specific solver class (default: cspy.BiDirectional)
    :param timeout:     time limit in sec
    :param cspargs:     additional CSP solver parameters
    :return:            tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    best_res = INFEASIBLE
    # Critical path
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, max(m for m, *_ in flavors), L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    for dag, chains in ibuild_gen_csp_dag(tree, root, flavors, exec_calc, cpath, delay):
        model = solver(dag, max_res=[len(dag.edges), L], min_res=[1, 0], time_limit=timeout, **cspargs)
        try:
            model.run()
            if model.path is not None and model.total_cost < best_res[1]:
                best_res = extract_grp_from_path(model.path), model.total_cost, float(model.consumed_resources[-1])
        except Exception:
            # No feasible solution
            continue
    return best_res


def extract_grp_from_path(path: list[str], flavors: bool = True) -> list[tuple[T_BLOCK, Flavor]] | list[tuple[T_BLOCK]]:
    """
    Extract partitioning from *path* and recreate partition blocks.

    :param path:    solution path of the CSP graph
    :param flavors: whether return flavors or not
    :return:        resulted partitioning blocks
    """
    return sorted(decode_state(grp) if flavors else decode_state(grp)[0] for grp in path[1:-1])
