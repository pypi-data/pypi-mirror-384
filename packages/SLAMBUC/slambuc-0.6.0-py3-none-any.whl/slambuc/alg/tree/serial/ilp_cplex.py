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
import math
import sys
import typing
import warnings

import docplex
import docplex.cp.model as cpo
import docplex.mp.model as cpx
import networkx as nx
from docplex.mp.dvar import Var

if sys.version_info.minor > 10 and docplex.docplex_version_minor <= 30:
    warnings.warn(f"docplex[{docplex.version.docplex_version_string}] package does not support Python version >3.12!")

from slambuc.alg import LP_LAT, INFEASIBLE, T_RESULTS, T_PART
from slambuc.alg.app import *
from slambuc.alg.tree.serial.ilp import ifeasible_subtrees
from slambuc.alg.util import (ibacktrack_chain, induced_subtrees, ser_subchain_latency, ser_subtree_cost,
                              recreate_subtree_blocks, verify_limits)
from slambuc.misc.util import get_cpo_path

CPO_PATH = get_cpo_path()
T_VARS = dict[int, list[cpo.CpoIntVar]]


def build_tree_cfg_cpo_model(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                             cpath: set[int] = frozenset(), delay: int = 1,
                             isubtrees: typing.Callable = ifeasible_subtrees) -> tuple[cpo.CpoModel, T_VARS]:
    """
    Generate the configuration CP model.

    :return: tuple of the created model and list of decision variables
    """
    # Model
    model = cpo.CpoModel(name="Tree_Partitioning")
    # Decision variables with precalculated coefficients
    c_x, l_x, X_n = [], [], collections.defaultdict(list)
    for i, (b, nodes) in enumerate(isubtrees(tree, root, M)):
        # Decision variable for the subtree
        x = cpo.binary_var(name=f"x_{b:02d}_{i}")
        # Add subtree block cost
        c_x.append(ser_subtree_cost(tree, b, nodes) * x)
        # Add subtree block latency if required
        if b in cpath:
            st_lat = ser_subchain_latency(tree, b, nodes, cpath)
            l_x.append((st_lat + delay) * x if b != root else st_lat * x)
        # Cache node coverage of subtree block
        for n in nodes:
            X_n[n].append(x)
    # Objective
    model.add(cpo.minimize(cpo.sum(c_x)))
    # Feasibility constraints
    for i, x_i in X_n.items():
        model.add(cpo.sum(x_i) == 1)
    # Latency constraint
    sum_lat = cpo.sum(l_x)
    model.add(sum_lat <= L if L < math.inf else sum_lat >= 0)
    model.add_kpi(sum_lat, LP_LAT)
    return model, X_n


def _set_cpo_context():
    """Set best performing CP solver configuration"""
    from docplex.cp.config import context
    context.verbose = 0
    context.model.add_source_location = False
    context.model.length_for_alias = 10
    context.model.name_all_constraints = False
    context.model.dump_directory = None
    context.model.sort_names = None
    context.solver.trace_cpo = False
    context.solver.trace_log = False
    context.solver.add_log_to_solution = False


def tree_cpo_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf, cp_end: int = None,
                          delay: int = 1, **kwargs) -> T_RESULTS:
    """
    Calculates minimal-cost partitioning of a tree based on configuration CP formulation.

    :param tree:      app graph annotated with node runtime(ms), memory(MB) and edge rate
    :param root:    root node of the graph
    :param M:       upper memory bound of the partition blocks (in MB)
    :param L:       latency limit defined on the critical path (in ms)
    :param cp_end:  tail node of the critical path in the form of subchain[root -> c_pend]
    :param delay:   invocation delay between blocks
    :return:        tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    # Critical path
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    model, Xn = build_tree_cfg_cpo_model(tree, root, M, L, cpath, delay)
    result = model.solve(agent='local', execfile=CPO_PATH, LogVerbosity='Quiet', SearchType='DepthFirst', Workers=1)
    if result:
        opt_cost, opt_lat = result.get_objective_values()[0], result.solution.get_kpis()[LP_LAT]
        return recreate_subtrees_from_cpo_xdict(tree, result, Xn), round(opt_cost, ndigits=6), round(opt_lat, ndigits=6)
    else:
        return INFEASIBLE


def recreate_subtrees_from_cpo_xdict(tree: nx.DiGraph, result: cpo.CpoSolveResult,
                                     Xn: dict[int, list[cpo.CpoIntVar]]) -> T_PART:
    """
    Extract barrier nodes from variable names (x_{b}_{w}) and recreate partitioning blocks.

    :param tree:    app graph annotated with node runtime(ms), memory(MB) and edge rates and data overheads(ms)
    :param result:  result object
    :param Xn:      specific structure of decision variables
    :return:        calculated partitioning
    """
    barr = set(int(next(filter(lambda x: result[x], x_n)).name.split('_', 2)[1]) for x_n in Xn.values())
    return recreate_subtree_blocks(tree=tree, barr=barr)


########################################################################################################################


def build_greedy_tree_cplex_model(tree: nx.DiGraph, root: int = 1, M: int = math.inf,
                                  L: int = math.inf, cpath: set[int] = frozenset(),
                                  delay: int = 1) -> tuple[cpx.Model, dict[int, dict[int, Var]]]:
    """
    Generate the matrix ILP model using CPLEX Python binding.

    :return: tuple of the created model and list of decision variables
    """
    # Model
    model = cpx.Model(name="Tree_Partitioning")
    # Empty decision variable matrix
    X = {j: {} for j in filter(lambda n: n is not PLATFORM, tree)}
    # Objective
    sum_cost = model.linear_expr()
    for j in X:
        cost_pre = 0
        nodes = set()
        for v in nx.dfs_preorder_nodes(tree, source=j):
            nodes |= {v}
            cost_vj = ser_subtree_cost(tree, j, nodes)
            X[v][j] = model.binary_var(f"x_{v:02d}_{j:02d}")
            sum_cost += (cost_vj - cost_pre) * X[v][j]
            cost_pre = cost_vj
    model.minimize(sum_cost)
    # Feasibility constraints
    for i in X:
        model.add_constraint(model.sum(X[i].values()) == 1, ctname=f"Cf_{i:02d}")
    # Knapsack constraints
    if M < math.inf:
        for j in X:
            model.add_constraint(model.sum(tree.nodes[i][MEMORY] * X[i][j]
                                           for i in nx.dfs_preorder_nodes(tree, source=j)) <= M, f"Ck_{j:02d}")
    # Connectivity constraints
    for j in X:
        for u, v in nx.dfs_edges(tree, source=j):
            model.add_constraint(X[u][j] - X[v][j] >= 0, ctname=f"Cc_{j:02d}_{u:02d}_{v:02d}")
    # Latency constraint
    sum_lat = model.linear_expr()
    for j in X:
        if j not in cpath:
            continue
        lat_pre = 0
        nodes = set()
        for v in nx.dfs_preorder_nodes(tree, source=j):
            nodes |= {v}
            # Add subtree block latency if required
            lat_vj = ser_subchain_latency(tree, j, nodes, cpath)
            sum_lat += (lat_vj - lat_pre) * X[v][j]
            if v == j and j != root:
                sum_lat += delay * X[v][j]
            lat_pre = lat_vj
    # Latency constraint
    if L < math.inf:
        model.add_constraint(sum_lat <= L, ctname=LP_LAT)
    # Add calculated sum latency as KPI for tracking
    model.add_kpi(sum_lat, LP_LAT)
    return model, X


def build_tree_cplex_model(tree: dict[str | int, dict[str | int, dict[str, int]]] | nx.DiGraph, root: int = 1,
                           M: int = math.inf, L: int = math.inf, cpath: set[int] = frozenset(),
                           delay: int = 1) -> tuple[cpx.Model, dict[int, dict[int, Var]]]:
    """
    Generate the matrix ILP model using CPLEX Python binding.

    :return: tuple of the created model and list of decision variables
    """
    # Model
    model = cpx.Model(name="Tree_Partitioning")
    # Decision variable matrix with trivial variables
    X: dict[int, dict] = {j: {j: model.binary_var(f"x_{j:02d}_{j:02d}")} for j in tree.nodes if j is not PLATFORM}
    # Empty objective
    sum_cost = model.linear_expr()
    # Empty latency constraint
    sum_lat = model.linear_expr()
    # Generate decision variables
    for (p, j), st_edges in induced_subtrees(tree, root):
        blk_mem = tree.nodes[j][MEMORY] * X[j][j]
        # Add coefficients for single node block [j]
        r_j, d_j, t_j = tree[p][j][RATE], tree[p][j][DATA], tree.nodes[j][RUNTIME]
        sum_cost += (r_j * (d_j + t_j) + sum(js[RATE] * js[DATA] for js in tree.succ[j].values())) * X[j][j]
        if j in cpath:
            jc = next(filter(lambda c: c in cpath, tree.successors(j)), None)
            sum_lat += (d_j + t_j + (math.ceil(tree[j][jc][RATE] / r_j) * tree[j][jc][DATA] if jc else 0)) * X[j][j]
            if j != root:
                sum_lat += delay * X[j][j]
        # Cache instance factor for nodes in cpath
        n_v = 1
        # Candidate nodes for block_j
        for u, v in st_edges:
            X[v][j] = model.binary_var(f"x_{v:02d}_{j:02d}")
            blk_mem += tree.nodes[v][MEMORY] * X[v][j]
            # Add coefficients for merging single node v to block [j,...]
            r_v, d_v, t_v = tree[u][v][RATE], tree[u][v][DATA], tree.nodes[v][RUNTIME]
            sum_cost += (r_v * (t_v - d_v) + sum(vs[RATE] * vs[DATA] for vs in tree.succ[v].values())) * X[v][j]
            # u -> v edge on cpath
            if v in cpath:
                n_v *= math.ceil(r_v / tree[next(tree.predecessors(u))][u][RATE])
                vc = next(filter(lambda c: c in cpath, tree.successors(v)), None)
                w_v = math.ceil(tree[v][vc][RATE] / r_v) * tree[v][vc][DATA] if vc else 0
                sum_lat += n_v * (t_v - d_v + w_v) * X[v][j]
            # Connectivity constraint
            model.add_constraint(X[u][j] - X[v][j] >= 0, ctname=f"Cc_{j:02d}_{u:02d}_{v:02d}")
        # Knapsack constraint, X[l][l] <= M for each leaf node l can be omitted
        if blk_mem.size > 1 and M < math.inf:
            model.add_constraint(blk_mem <= M, ctname=f"Ck_{j:02d}")
    # Objective
    model.minimize(sum_cost)
    # Feasibility constraints, X[root][root] = 1 can be omitted else it ensures that X[root][root] must be 1
    for i in X:
        model.add_constraint(model.sum(X[i].values()) == 1, ctname=f"Cf_{i:02d}")
    # Latency constraint
    if L < math.inf:
        model.add_constraint(sum_lat <= L, ctname=LP_LAT)
    # Add calculated sum latency as KPI for tracking
    model.add_kpi(sum_lat, LP_LAT)
    return model, X


def tree_cplex_partitioning(tree: nx.DiGraph, root: int = 1, M: int = math.inf, L: int = math.inf,
                            cp_end: int = None, delay: int = 1, **kwargs) -> tuple[T_PART, float, float | None]:
    """
    Calculates minimal-cost partitioning of a tree based on matrix CPLEX ILP formulation.

    :param tree:      app graph annotated with node runtime(ms), memory(MB) and edge rate
    :param root:    root node of the graph
    :param M:       upper memory bound of the partition blocks (in MB)
    :param L:       latency limit defined on the critical path (in ms)
    :param cp_end:  tail node of the critical path in the form of subchain[root -> c_pend]
    :param delay:   invocation delay between blocks
    :return:        tuple of list of best partitions, sum cost of the partitioning, and resulted latency
    """
    # Critical path
    cpath = set(ibacktrack_chain(tree, root, cp_end))
    # Verify the min values of limits for a feasible solution
    if not all(verify_limits(tree, cpath, M, L)):
        # No feasible solution due to too strict limits
        return INFEASIBLE
    model, X = build_tree_cplex_model(tree, root, M, L, cpath, delay)
    solution = model.solve(agent='local', log_output=False, **kwargs)
    if solution is not None:
        opt_cost, opt_lat = solution.get_objective_value(), model.kpi_value_by_name(LP_LAT)
        return extract_subtrees_from_cplex_xmatrix(X), round(opt_cost, ndigits=6), round(opt_lat, ndigits=6)
    else:
        return INFEASIBLE


def extract_subtrees_from_cplex_xmatrix(X: dict[int, dict[int, Var]]) -> T_PART:
    """
    Extract barrier nodes from variable matrix(dict-of-dict) and recreate partitioning blocks.

    :param X:   specific structure of decision variables
    :return:    calculated partitioning
    """
    return [[i for i in sorted(X) if j in X[i] and round(X[i][j].solution_value, ndigits=6) == 1]
            for j in sorted(X) if round(X[j][j].solution_value, ndigits=6) == 1]
