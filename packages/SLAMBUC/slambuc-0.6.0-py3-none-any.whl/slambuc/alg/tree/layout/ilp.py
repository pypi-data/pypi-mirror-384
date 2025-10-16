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
from collections.abc import Generator

import networkx as nx
import pulp as lp

from slambuc.alg import LP_LAT, INFEASIBLE, T_FRESULTS, T_FPART
from slambuc.alg.app.common import *
from slambuc.alg.util import (ipowerset, ipostorder_dfs, ibacktrack_chain, gen_subtree_memory, gen_subtree_cost,
                              gen_subchain_latency, recreate_subtree_blocks, x_eval)


def ifeasible_gen_subtrees(tree: nx.DiGraph, root: int, M: int, N: int = 1) -> Generator[tuple[int, set[int]]]:
    """
    Generate M-feasible(connected) subtrees and roots in bottom-up way, which meet the memory constraint *M*.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:    root node of the graph
    :param M:       upper memory bound of the partition blocks (in MB)
    :param N:       upper CPU core bound of the partition blocks
    :return:        generator of subtree root and regarding subtree nodes
    """
    subtrees = collections.defaultdict(list)
    for _, n in ipostorder_dfs(tree, root):
        # noinspection PyTypeChecker
        for children in ipowerset(tuple(tree.successors(n))):
            for sts in itertools.product(*(subtrees[c] for c in children)):
                st = {n}.union(*sts)
                if gen_subtree_memory(tree, n, st, N) <= M:
                    subtrees[n].append(st)
                    yield n, st
        for c in tree.succ[n]:
            del subtrees[c]


def build_gen_tree_cfg_model(tree: nx.DiGraph, root: int = 1, flavors: list[Flavor] = (Flavor(),),
                             exec_calc: collections.abc.Callable[[int, int, int], int] = lambda i, t, n: t,
                             L: int = math.inf, cp_end: int = None,
                             delay: int = 1) -> tuple[lp.LpProblem, dict[Flavor, dict[int, list[lp.LpVariable]]]]:
    """
    Generate the configuration ILP model with the given *flavors*.

    :return: tuple of the created model and list of decision variables
    """
    # Model
    model = lp.LpProblem(name="Tree_Partitioning", sense=lp.LpMinimize)
    # Critical path
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Decision variables with precalculated coefficients
    c_x, l_x, X = [], [], {f: {v: list() for v in tree if v is not PLATFORM} for f in flavors}
    for fi, f in enumerate(flavors):
        for i, (b, nodes) in enumerate(ifeasible_gen_subtrees(tree, root, f.mem, f.ncore)):
            # Decision variable for the subtree
            x = lp.LpVariable(f"x_{fi}_{b:02d}_{i}", cat=lp.LpBinary)
            # Add subtree block cost
            c_x.append(gen_subtree_cost(tree, b, nodes, f.ncore, exec_calc) * x)
            # Add subtree block latency if required
            if b in cpath:
                st_lat = gen_subchain_latency(tree, b, nodes, cpath, f.ncore, exec_calc)
                l_x.append((st_lat + delay) * x if b != root else st_lat * x)
            # Cache node coverage of subtree block
            for n in nodes:
                X[f][n].append(x)
    # Objective
    model += lp.lpSum(c_x)
    # Feasibility constraints
    for v in tree:
        if v is PLATFORM:
            continue
        # noinspection PyTypeChecker
        model += lp.lpSum(X[f][v] for f in X) == 1, f"Cf_{v:03d}"
    # Latency constraint
    model += lp.lpSum(l_x) <= L if L < math.inf else lp.lpSum(l_x) >= 0, LP_LAT
    return model, X


def tree_gen_hybrid_partitioning(tree: nx.DiGraph, root: int = 1, flavors: list[Flavor] = (Flavor(),),
                                 exec_calc: collections.abc.Callable[[int, int, int], int] = lambda i, t, n: t,
                                 L: int = math.inf, cp_end: int = None, delay: int = 1, solver: lp.LpSolver = None,
                                 timeout: int = None, **lpargs) -> T_FRESULTS:
    """
    Calculate minimal-cost partitioning of a tree based on configuration LP formulation and given *flavors*.

    :param tree:        app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:        root node of the graph
    :param flavors:     list of flavors resources given by the tuple of available *(memory, relative CPU cores)*
    :param exec_calc:   function that calculates the effective runtimes from reference runtime and available CPU cores
    :param L:           latency limit defined on the critical path (in ms)
    :param cp_end:      tail node of the critical path in the form of subchain[root -> c_pend]
    :param delay:       invocation delay between blocks
    :param solver:      specific solver class (default: COIN-OR CBC)
    :param timeout:     time limit in sec
    :param lpargs:      additional LP solver parameters
    :return:            tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    model, X = build_gen_tree_cfg_model(tree, root, flavors, exec_calc, L, cp_end, delay)
    solver = solver if solver else lp.PULP_CBC_CMD(mip=True, msg=False)
    solver.timeLimit = timeout
    status = model.solve(solver=solver, **lpargs)
    if status == lp.LpStatusOptimal:
        opt_cost, opt_lat = lp.value(model.objective), lp.value(model.constraints[LP_LAT])
        return recreate_st_from_gen_xdict(tree, X), opt_cost, L + opt_lat if L < math.inf else opt_lat
    else:
        return INFEASIBLE


def recreate_st_from_gen_xdict(tree: nx.DiGraph, X: dict[Flavor, dict[int, list[lp.LpVariable]]]) -> T_FPART:
    """
    Extract barrier nodes from variable names (x_{b}_{w}) and recreate partitioning blocks.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param X:       internal structure of decision variables
    :return:        partition blocks
    """
    dbarr = {int(x.name.rsplit('_', 2)[1]): f
             for f in X for v in X[f] for x in filter(lambda _x: _x.varValue == 1, X[f][v])}
    return [(p, dbarr[p[0]]) for p in recreate_subtree_blocks(tree=tree, barr=dbarr)]


########################################################################################################################


def build_gen_tree_mtx_model(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                             flavors: list[Flavor] = (Flavor(),),
                             exec_calc: collections.abc.Callable[[int, int, int], int] = lambda i, t, n: t,
                             L: int = math.inf, cp_end: int = None, subchains: bool = False,
                             delay: int = 1) -> tuple[lp.LpProblem, dict[Flavor, dict[int, dict[int, lp.LpVariable]]]]:
    """
    Generate the matrix ILP model with the given *flavors*.

    :return: tuple of the created model and list of decision variables
    """
    # Model
    model = lp.LpProblem(name="Tree_Partitioning", sense=lp.LpMinimize)
    # Empty decision variable matrix
    X = {f: {j: {} for j in tree if j is not PLATFORM} for f in flavors}
    # Objective
    sum_cost = lp.LpAffineExpression()
    for fi, f in enumerate(flavors):
        for j in X[f]:
            cost_pre = 0
            _nodes = set()
            for v in nx.dfs_preorder_nodes(tree, source=j):
                _nodes |= {v}
                cost_vj = gen_subtree_cost(tree, j, _nodes, f.ncore, exec_calc)
                X[f][v][j] = lp.LpVariable(f"x_{fi}_{v:02d}_{j:02d}", cat=lp.LpBinary)
                sum_cost += (cost_vj - cost_pre) * X[f][v][j]
                cost_pre = cost_vj
    model += sum_cost
    # Feasibility constraints
    for v in tree:
        if v is PLATFORM:
            continue
        # noinspection PyTypeChecker
        model += lp.lpSum(X[f][v] for f in flavors) == 1, f"Cf_{v:02d}"
    # Knapsack constraints
    for fi, f in enumerate(filter(lambda _f: _f.mem < math.inf, X)):
        for j in X[f]:
            # Cumulative memory demand of prefetched models
            model += lp.lpSum(tree.nodes[i][MEMORY] * X[f][i][j]
                              for i in nx.dfs_preorder_nodes(tree, source=j)) <= f.mem, f"C_{fi}_k{j:02d}"
            r_j = tree[next(tree.predecessors(j))][j][RATE]
            # Operative memory demand of instances running in parallel
            for u, v in nx.dfs_edges(tree, source=j):
                vj_sat = min(math.ceil(tree[u][v][RATE] / r_j), math.ceil(f.ncore / tree.nodes[v].get(CPU, 1)))
                # Add only non-trivial memory constraint
                if vj_sat > 1:
                    model += vj_sat * tree.nodes[v][MEMORY] * X[f][v][j] <= f.mem, f"Ck_{fi}_{j:02d}_{v:02d}"
    # Connectivity constraints
    for fi, f in enumerate(X):
        for j in X[f]:
            for u, v in nx.dfs_edges(tree, source=j):
                model += X[f][u][j] - X[f][v][j] >= 0, f"Cc_{fi}_{j:02d}_{u:02d}_{v:02d}"
    # Path-tree constraints
    if subchains:
        for fi, f in enumerate(X):
            for pt in ((lp.lpSum(X[f][i][j] for i in tree.successors(v)) <= 1, f"Cp_{fi}_{j:02d}_{v:02d}")
                       for v in X[f] for j in X[f][v] if tree.succ[v]):
                model += pt
    # Latency constraint
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    sum_lat = lp.LpAffineExpression()
    for fi, f in enumerate(X):
        for j in X[f]:
            if j not in cpath:
                continue
            lat_pre = 0
            nodes = set()
            for v in nx.dfs_preorder_nodes(tree, source=j):
                nodes |= {v}
                # Add subtree block latency if required
                lat_vj = gen_subchain_latency(tree, j, nodes, cpath, f.ncore, exec_calc)
                sum_lat += (lat_vj - lat_pre) * X[f][v][j]
                if v == j and j != root:
                    sum_lat += delay * X[f][v][j]
                lat_pre = lat_vj
    if L < math.inf:
        model += sum_lat <= L, LP_LAT
    else:
        # Add redundant constraint to implicitly calculate the latency value
        model += sum_lat >= 0, LP_LAT
    return model, X


def tree_gen_mtx_partitioning(tree: nx.DiGraph, root: int = 1, flavors: list[Flavor] = (Flavor(),),
                              exec_calc: collections.abc.Callable[[int, int, int], int] = lambda i, t, n: t,
                              L: int = math.inf, cp_end: int = None, subchains: bool = False, delay: int = 1,
                              solver: lp.LpSolver = None, timeout: int = None, **lpargs) -> T_FRESULTS:
    """
    Calculate minimal-cost partitioning of a tree based on matrix LP formulation and given *flavors*.

    :param tree:        app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:        root node of the graph
    :param flavors:     list of flavors resources given by the tuple of available *(memory, relative CPU cores)*
    :param exec_calc:   function that calculates the effective runtimes from reference runtime and available CPU cores
    :param L:           latency limit defined on the critical path (in ms)
    :param cp_end:      tail node of the critical path in the form of subchain[root -> c_pend]
    :param subchains:   only subchain blocks are considered (path-tree)
    :param delay:       invocation delay between blocks
    :param solver:      specific solver class (default: COIN-OR CBC)
    :param timeout:     time limit in sec
    :param lpargs:      additional LP solver parameters
    :return:            tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    model, X = build_gen_tree_mtx_model(tree, root, flavors, exec_calc, L, cp_end, subchains, delay)
    solver = solver if solver else lp.PULP_CBC_CMD(mip=True, msg=False)
    solver.timeLimit = timeout
    status = model.solve(solver=solver, **lpargs)
    if status == lp.LpStatusOptimal:
        opt_cost, opt_lat = round(lp.value(model.objective), 0), round(lp.value(model.constraints[LP_LAT]), 0)
        return extract_st_from_gen_xmatrix(X), opt_cost, L + opt_lat if L < math.inf else opt_lat
    else:
        return INFEASIBLE


def extract_st_from_gen_xmatrix(X: dict[Flavor, dict[int, dict[int, lp.LpVariable]]]) -> T_FPART:
    """
    Extract barrier nodes from variable matrix(dict-of-dict) and recreate partitioning blocks.

    :param X:       internal structure of decision variables
    :return:        partition blocks
    """
    return sorted(([i for i in sorted(X[f]) if j in X[f][i] and x_eval(X[f][i][j])], f)
                  for f in X for j in sorted(X[f]) if x_eval(X[f][j][j]))


########################################################################################################################


def all_gen_tree_mtx_partitioning(tree: nx.DiGraph, root: int = 1, flavors: list[Flavor] = (Flavor(),),
                                  exec_calc: collections.abc.Callable[[int, int, int], int] = lambda i, t, n: t,
                                  L: int = math.inf, cp_end: int = None, subchains: bool = False, delay: int = 1,
                                  solver: lp.LpSolver = None, timeout: int = None, **lpargs) -> list[T_FPART]:
    """
    Calculate all minimal-cost partitioning variations of a tree based on matrix ILP formulation and *flavors*.

    :param tree:        app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param root:        root node of the graph
    :param flavors:     list of flavors resources given by the tuple of available *(memory, relative CPU cores)*
    :param exec_calc:   function that calculates the effective runtimes from reference runtime and available CPU cores
    :param L:           latency limit defined on the critical path (in ms)
    :param cp_end:      tail node of the critical path in the form of subchain[root -> c_pend]
    :param subchains:   only subchain blocks are considered (path-tree)
    :param delay:       invocation delay between blocks
    :param solver:      specific solver class (default: COIN-OR CBC)
    :param timeout:     time limit in sec
    :param lpargs:      additional LP solver parameters
    :return:            tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    # Get model
    model, X = build_gen_tree_mtx_model(tree, root, flavors, exec_calc, L, cp_end, subchains, delay)
    # Init for min-cost results
    results, min_cost = [], math.inf
    solver = solver if solver else lp.PULP_CBC_CMD(mip=True, msg=False, timeLimit=timeout, **lpargs)
    # Iterate over the optimal solutions
    while model.solve(solver) == lp.LpStatusOptimal:
        opt_cost, opt_lat = round(model.objective.value(), 0), round(model.constraints[LP_LAT].value(), 0)
        # If solution is not min-cost then exit else store the min-cost solution
        if min_cost < opt_cost:
            break
        else:
            min_cost = opt_cost
        results.append((extract_st_from_gen_xmatrix(X), opt_cost, L + opt_lat if L < math.inf else opt_lat))
        # Collect barrier nodes of the current optimal solution
        barr = [(f, j) for f in X for j in X[f] if x_eval(X[f][j][j])]
        # Add extra constraint for excluding the current set of barrier nodes
        model += (lp.lpSum(X[f][j][j] for f, j in barr) <= len(barr) - 1,
                  f"Ca_{'_'.join(map(str, itertools.chain.from_iterable(barr)))}")
    # Return min-cost solutions
    return results if results else [INFEASIBLE]
