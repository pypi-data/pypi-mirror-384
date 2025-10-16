#!/usr/bin/env python3
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
import enum
import functools
import importlib
import inspect
import itertools
import json
import math
import os
import pathlib
import sys
import time
import traceback
import typing

import click
import cspy
import networkx as nx
import numpy as np
import pulp

import slambuc
from slambuc.alg import Flavor
from slambuc.misc.io import load_tree

GLOBAL_CTX_SETTINGS = dict(
    help_option_names=['-h', '--help'],
    show_default=True,
    max_content_width=120,
    auto_envvar_prefix="SLAMBUC"
)


@click.group('slambuc', context_settings=GLOBAL_CTX_SETTINGS,
             epilog="See https://github.com/hsnlab/SLAMBUC for more details.")
@click.option('-j', '--json', 'format_json', is_flag=True, default=False, help="Output as valid JSON")
@click.option('-s', '--split', 'format_split', is_flag=True, default=False, help="Split result into separate lines")
@click.option('-q', '--quiet', 'output_quiet', is_flag=True, default=False, help="Suppress logging messages")
@click.version_option(slambuc.__version__, "-v", "--version", package_name="slambuc")
@click.pass_context
def main(ctx: click.Context, format_json: bool, format_split: bool, output_quiet: bool):
    """Serverless Layout Adaptation with Memory-Bounds and User Constraints (SLAMBUC)."""
    ctx.ensure_object(dict)
    ctx.obj['FORMAT_JSON'] = format_json
    ctx.obj['FORMAT_SPLIT'] = format_split
    ctx.obj['OUTPUT_QUIET'] = output_quiet


########################################################################################################################


class HalfOpenIntRangeType(click.IntRange):
    """Custom Integer range type that supports positive half-open intervals to infinity."""
    name = "INT"

    def __init__(self):
        super().__init__(min=0, min_open=True, clamp=False)

    def convert(self, value: typing.Any, param: click.Parameter, ctx: click.Context) -> int | float:
        if ((isinstance(value, float) and math.isinf(value)) or
                (isinstance(value, str) and value.lower() == 'inf')):
            return math.inf
        else:
            try:
                return super().convert(value, param, ctx)
            except ValueError:
                self.fail(f"'{value}' is not a valid integer or {math.inf}", param, ctx)


HalfOpenRange = HalfOpenIntRangeType()


class IndexRangeType(click.IntRange):
    """Custom Integer range type that supports custom/abstract array size depicted as 'n'."""
    name = "IDX"

    class IndexMaxSize(float):

        def __str__(self):
            return 'n'

    def __init__(self, max_value: str | int = None):
        super().__init__(min=0, min_open=False, max_open=True, clamp=False)
        self.max = self.IndexMaxSize(max_value if isinstance(max_value, int) else math.inf)


IndexRange = IndexRangeType()


class CallGraphPathType(click.Path):
    """Custom Path type that explicitly checks for supported data file extensions."""
    name: str = "CALL_GRAPH_FILE"
    ext: set[str] = {'gml', 'npy', 'npz', 'csv'}

    def __init__(self):
        super().__init__(exists=True, file_okay=True, dir_okay=False, readable=True,
                         resolve_path=True, path_type=pathlib.Path)

    def convert(self, value: typing.Any, param: click.Parameter, ctx: click.Context) -> pathlib.Path:
        if (file_ext := value.rsplit('.', maxsplit=1)[-1]) not in self.ext:
            self.fail(f"Call graph format: {file_ext} is not in the supported formats: {self.ext}!", param, ctx)
        return pathlib.Path(super().convert(value, param, ctx))


CallGraphFile = CallGraphPathType()


class SlambucFlavorType(click.ParamType):
    """Custom resource type matching SLAMBUC's own Flavor type."""
    name: str = 'Flavor'
    _format = 'mem[int>0],ncore[int>0],cfactor[float>0.0]'

    def convert(self, value: typing.Any, param: click.Parameter, ctx: click.Context) -> Flavor:
        """Parse and convert flavors from CLI inf format <mem[int]>,<ncore[int]>,<cfactor[float]>"""
        if isinstance(value, Flavor):
            return value
        try:
            mem, ncore, cfactor = value.split(',', maxsplit=2)
            _flavor = Flavor(math.inf if mem == 'inf' else int(mem), int(ncore), float(cfactor))
            if not all(metric > 0 for metric in _flavor):
                self.fail(f"Flavor {_flavor} is out of range! Correct format: {self._format}", param, ctx)
            return _flavor
        except ValueError as e:
            self.fail(f"{e}! Correct format: {self._format}", param, ctx)

    def split_envvar_value(self, rv: str):
        """Splitting multiple flavor definitions given as an envvars. Default is split on whitespace.
        https://click.palletsprojects.com/en/stable/options/#multiple-options-from-environment-values
        """
        return super().split_envvar_value(rv)

    def __repr__(self) -> str:
        return self._format


FlavorType = SlambucFlavorType()


class PulpSolverType(enum.Enum):
    """Specific param type corresponding to PulP's solver classes supported by SLAMBUC."""
    cbc = pulp.PULP_CBC_CMD
    glpk = pulp.GLPK_CMD
    cplex = pulp.CPLEX_CMD
    DEF = cbc


class CSPSolverType(enum.Enum):
    """Specific param type corresponding to CSP's solver classes supported by SLAMBUC."""
    bidirect = cspy.BiDirectional
    tabu = cspy.Tabu
    greedy = cspy.GreedyElim
    grasp = cspy.GRASP
    DEF = bidirect


def algorithm(enum_type: enum.EnumType, *options) -> typing.Callable:
    """Decorator for common Click arguments and options for algorithm invocations."""

    def wrapped(func):
        func = click.argument('filename', required=True, nargs=1, type=CallGraphFile)(func)
        # parameters = lambda *options: functools.reduce(lambda f, g: lambda x: f(g(x)), reversed(options))
        for param in reversed(options):
            func = param(func)
        func = click.option('--alg', required=False, help="Specific algorithm to be run",
                            type=click.Choice(enum_type, case_sensitive=False),
                            default=enum_type['DEF'])(func)
        return func

    return wrapped


########################################################################################################################

root = click.option('--root', 'root', metavar='<NODE>', type=click.INT, required=False,
                    envvar='SLAMBUC_ROOT', default=1, help="Root node ID of the call graph")
M = click.option('--M', 'M', type=HalfOpenRange, required=False, default=math.inf,
                 envvar='SLAMBUC_M', help="Upper memory bound for blocks")
L = click.option('--L', 'L', type=HalfOpenRange, required=False, default=math.inf,
                 envvar='SLAMBUC_L', help="Latency limit for critical path")
N = click.option('--N', 'N', type=HalfOpenRange, required=False, default=1,
                 envvar='SLAMBUC_N', help="Available vCPU cores for blocks")
cp_end = click.option('--cp_end', 'cp_end', metavar='<NODE>', type=click.INT, required=False,
                      envvar='SLAMBUC_CP_END', show_default='ignore', help="Tail node ID of the critical path")
delay = click.option('--delay', 'delay', type=HalfOpenRange, required=False, default=1,
                     envvar='SLAMBUC_DELAY', help="Invocation delay between blocks")
bidirect = click.option('--bidirect/--one-off', 'bidirectional', metavar='BOOL',
                        type=click.BOOL, required=False, show_default=True, default=True,
                        envvar='SLAMBUC_BIDIRECT', help="Use bidirectional/single subcase elimination")
pulp_solver = click.option('--solver', 'solver', type=click.Choice(PulpSolverType, case_sensitive=False),
                           required=False, show_default=True, default=PulpSolverType.DEF, envvar='SLAMBUC_PULP_SOLVER',
                           callback=lambda c, p, v: v.value(mip=True, msg=False), help="Used linear programming solver")
csp_solver = click.option('--solver', 'solver', type=click.Choice(CSPSolverType, case_sensitive=False),
                          required=False, show_default=True, default=CSPSolverType.DEF, envvar='SLAMBUC_CSP_SOLVER',
                          callback=lambda c, p, v: v.value, help="Used linear programming solver")
timeout = click.option('--timeout', 'timeout', type=HalfOpenRange, required=False,
                       envvar='SLAMBUC_TIMEOUT', show_default='ignore', help="ILP solver timeout in seconds")
subchains = click.option('--subchains/--subtrees', 'subchains', metavar='BOOL', type=click.BOOL,
                         required=False, is_flag=True, show_default=True, default=False, envvar='SLAMBUC_SUBCHAINS',
                         help="Consider blocks as single chains or trees")
Epsilon = click.option('--epsilon', 'Epsilon', metavar='FLOAT', required=False, show_default='ignore',
                       type=click.FloatRange(min=0.0, max=1.0, min_open=True, max_open=False), envvar='SLAMBUC_EPSILON',
                       help="Weight factor for trimming")
Lambda = click.option('--lambda', 'Lambda', metavar='FLOAT', required=False, default=0.0,
                      envvar='SLAMBUC_LAMBDA', type=click.FloatRange(min=0.0, min_open=False),
                      help="Latency factor for trimming")
flavor = click.option('--flavor', 'flavors', type=FlavorType, multiple=True, required=False,
                      default=(Flavor(),), metavar='<mem,ncore,cfactor>', show_default=True, envvar='SLAMBUC_FLAVOR',
                      help=f"Resource flavor as a comma-separated tuple")
unit = click.option('--unit', 'unit', type=HalfOpenRange, required=False, default=1, envvar='SLAMBUC_UNIT',
                    show_default=True, help="Rounding unit for cost calculation")
only_cuts = click.option('--cuts/--latency', 'only_cuts', metavar='BOOL', type=click.BOOL, required=False,
                         is_flag=True, show_default=True, default=False, envvar='SLAMBUC_CUTS',
                         help="Return only cut size or latency")
only_barr = click.option('--barriers/--unfold', 'only_barr', metavar='BOOL', type=click.BOOL,
                         required=False, is_flag=True, show_default=True, default=False, envvar='SLAMBUC_BARRIERS',
                         help="Return only barrier nodes or full blocks")
full = click.option('--full/--tails', 'full', metavar='BOOL', type=click.BOOL, required=False,
                    is_flag=True, show_default=True, default=True, envvar='SLAMBUC_FULL',
                    help="Return full blocks or tail nodes only")
validate = click.option('--validate', 'validate', metavar='BOOL', type=click.BOOL, required=False,
                        show_default=True, default=True, envvar='SLAMBUC_VALIDATE',
                        help="Validate result for latency feasibility")
exhaustive = click.option('--exhaustive/--greedy', 'exhaustive', metavar='BOOL', type=click.BOOL,
                          required=False, is_flag=True, show_default=True, default=True, envvar='SLAMBUC_EXHAUSTIVE',
                          help="Iterate over all orderings or stop greedily")
metrics = click.option('--metrics/--no-metrics', 'metrics', metavar='BOOL', type=click.BOOL,
                       required=False, is_flag=True, show_default=True, default=True, envvar='SLAMBUC_METRICS',
                       help="Calculate cost/latency metrics explicitly")
k = click.option('--k', type=HalfOpenRange, required=False, default=None, show_default='auto',
                 envvar='SLAMBUC_K', help="Predefined number of clusters")
start = click.option('--start', 'start', metavar='<IDX>', type=IndexRange, required=False,
                     envvar='SLAMBUC_START', default=0, help="Head node index of the critical path")
end = click.option('--end', 'end', metavar='<IDX>', type=IndexRange, required=False, default=None,
                   show_default='n-1', envvar='SLAMBUC_END', help="Tail node index of the critical path")
unfold = click.option('--unfold/--barriers', 'unfold', metavar='BOOL', type=click.BOOL,
                      required=False, is_flag=True, show_default=True, default=False, envvar='SLAMBUC_UNFOLD',
                      help="Return full blocks or barrier nodes only")


########################################################################################################################

class InputDataType(enum.StrEnum):
    """Specific input data type corresponding to SLAMBUC's algorithms and package structure."""
    CHAIN = enum.auto()
    TREE = enum.auto()
    DAG = enum.auto()


@main.group("chain")
def chain():
    """Sequence partitioning algorithms.

    Calculates cost-optimal partitioning of a chain based on the node properties of 'running time', 'memory usage'
    and 'invocation rate' with respect to an upper bound 'M' on the total memory of blocks and a latency constraint
    'L' defined on the restricted subchain between 'start' and 'end' nodes.

    Cost calculation relies on the rounding 'unit' and number of vCPU cores 'N', whereas platform invocation 'delay'
    is used for latency calculations.
    """
    click.get_current_context().obj['INPUT_DATA_TYPE'] = InputDataType.CHAIN


@chain.group("path")
def chain__path():
    """Chain partitioning algorithms without data R/W overheads.

    For detailed information, see in J. Cz., I. P. and B. S., "Cost-optimal Operation of Latency Constrained Serverless
    Applications: From Theory to Practice," NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium,
    Miami, FL, USA, 2023, pp. 1-10, doi: 10.1109/NOMS56928.2023.10154412.
    """
    click.get_current_context().obj['INPUT_ARG_REF'] = ('runtime', 'memory', 'rate')


class ChainPathDPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.chain.path.dp`."""
    chain = "chain_partitioning"
    vector = "vec_chain_partitioning"
    DEF = vector


@chain__path.command("dp")
@algorithm(ChainPathDPType, M, N, L, start, end, delay, unit, unfold)
def chain__path__dp(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning based on (vectorized) dynamic programming."""
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class ChainPathGreedyType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.chain.path.greedy`."""
    greedy = "greedy_chain_partitioning"
    DEF = greedy


@chain__path.command("greedy")
@algorithm(ChainPathGreedyType, M, N, L, start, end, delay, unit)
def chain__path__greedy(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning using exhaustive search of edge cuts."""
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class ChainPathMinType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.chain.path.min`."""
    min = "min_chain_partitioning"
    DEF = min


@chain__path.command("min")
@algorithm(ChainPathMinType, M, N, L, start, end, delay, unit, unfold)
def chain__path__min(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-minimal partitioning assuming subadditive costs function.

    It gives an optimal result only in case the cost function regarding the chain attributes is subadditive,
    that is k_opt = k_min is guaranteed for each case.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class ChainPathSPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.chain.path.sp`."""
    sp = "sp_chain_partitioning"
    DEF = sp


@chain__path.command("sp")
@algorithm(ChainPathSPType, M, N, L, delay, unit, unfold)
def chain__path__sp(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning using shortest-path search in a state graph.

    Build configuration state graph of the given function chain.
    Partitioning is based on the shortest path calculation of the state graph of feasible blocks.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


########################################################################################################################

@chain.group("serial")
def chain__serial():
    """Chain partitioning algorithms using serialized platform execution model."""
    click.get_current_context().obj['INPUT_ARG_REF'] = ('runtime', 'memory', 'rate', 'data')


class ChainSerialGreedyType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.chain.serial.greedy`."""
    greedy = "greedy_ser_chain_partitioning"
    DEF = greedy


@chain__serial.command("greedy")
@algorithm(ChainSerialGreedyType, M, L, start, end, delay)
def chain__serial__greedy(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning using exhaustive search of edge cuts.

    Calculates all combinations of chain cuts with respect to the 'memory' values and constraint 'M'.
    The calculation is improved compared to brute force to only start calculating cuts from minimal cut size 'c_min'.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class ChainSerialILPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.chain.serial.greedy`."""
    cfg = "chain_cfg_partitioning"
    mtx = "chain_mtx_partitioning"
    DEF = mtx


@chain__serial.command("ilp")
@algorithm(ChainSerialILPType, M, L, start, end, delay, pulp_solver, timeout)
def chain__serial__ilp(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Chain partitioning based on ILP formalization.

    Generate all feasible (connected) blocks that meet the memory constraint 'M' assuming serialized executions.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


########################################################################################################################

@main.group("dag")
def dag():
    """DAG partitioning algorithms.

    Block metrics are calculated based on a parallelized execution platform model.
    """
    click.get_current_context().obj.update({'INPUT_DATA_TYPE': InputDataType.DAG,
                                            'INPUT_ARG_REF': 'dag'})


class DagILPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.dag.ilp`."""
    greedy = "greedy_dag_partitioning"
    dag = "dag_partitioning"
    DEF = dag


@dag.command("ilp")
@algorithm(DagILPType, root, M, L, N, cp_end, delay, subchains, pulp_solver, timeout)
def dag__ilp(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """DAG partitioning based on matrix ILP formalization.

    Block metrics are calculated based on a parallelized execution platform model.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


########################################################################################################################

@main.group("ext")
def ext():
    """External partitioning algorithms and heuristics."""
    click.get_current_context().obj.update({'INPUT_DATA_TYPE': InputDataType.TREE,
                                            'INPUT_ARG_REF': 'tree'})


class ExtBaselineType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.ext.baseline`."""
    singleton = "baseline_singleton_partitioning"
    no = "baseline_no_partitioning"
    DEF = singleton


@ext.command("baseline")
@algorithm(ExtBaselineType, root, N, cp_end, delay)
def ext__baseline(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Derive trivial partitioning of graph nodes.

    Derive the trivial partitioning of grouping all nodes into one single block.
    Derive the trivial solution of not merging any of the given tree nodes.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class ExtCSPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.ext.csp`."""
    csp = "csp_tree_partitioning"
    gen = "csp_gen_tree_partitioning"
    DEF = csp


@ext.command("csp")
@algorithm(ExtCSPType, root, flavor, M, L, N, cp_end, delay, exhaustive, csp_solver, timeout)
def ext__csp(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-minimal tree partitioning heuristics based on CSP formalization.

    Calculate all state-space DAGs of the given 'tree' based on the alternative chain decompositions and constrained
    shortest path (CSP) formalization with or without considering flavor assignment.
    The given flavors as list of (memory, CPU, cost_factor) tuples define the available memory (and group upper limit),
    available relative vCPU cores and relative cost multiplier.

    For detailed information, see in T. E. at al.: “Costless: Optimizing Cost of Serverless Computing through Function
    Fusion and Placement,” in 2018 IEEE/ACM Symposium on Edge Computing (SEC), 2018, pp. 300–312.
    doi: 10.1109/SEC.2018.00029."""
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class ExtGreedyType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.ext.greedy`."""
    greedy = "min_weight_greedy_partitioning"
    weight = "min_weight_partition_heuristic"
    lat = "min_lat_partition_heuristic"
    DEF = greedy


@ext.command("greedy")
@algorithm(ExtGreedyType, root, M, L, N, cp_end, delay, metrics)
def ext__greedy(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-minimal tree partitioning using greedy edge merging/splitting.

    Greedy: Calculates memory-bounded tree partitioning in a greedy manner without any latency limit.

    Min weight: Greedy heuristic algorithm to calculate partitioning of the given *tree* regarding the given memory
    'M' and latency 'L' limits.
    It uses a greedy approach to calculate a low-cost critical path cut (might miss feasible solutions).
    It may conclude the partitioning problem infeasible despite there exist one with large costs.

    Min latency: Greedy heuristic algorithm to calculate partitioning of the given 'tree' regarding the given
    memory 'M' and latency 'L' limits.
    It uses Dijkstra's algorithm to calculate the critical path cut with the lowest latency (might be expensive).
    It always returns a latency-feasible solution if it exists.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class ExtMinCutType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.ext.min_cut`."""
    chain = "min_weight_chain_decomposition"
    ksplit = "min_weight_ksplit_clustering"
    tree = "min_weight_tree_clustering"
    DEF = tree


@ext.command("mincut")
@algorithm(ExtMinCutType, root, k, L, N, cp_end, delay, metrics)
def ext__mincut(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Weight-minimal tree partitioning using rank-based clustering.

    Min chain: Minimal edge-weight chain-based tree partitioning (O(n)) without memory and latency constraints.
    Although latency is not considered on the critical path the algorithm reports it with the sum cost.

    K-split: Minimal data-transfer tree clustering into 'k' clusters (with k-1 cuts) without memory and latency
    constraints. Although latency is not considered on the critical path the algorithm reports it along with
    the sum cost.

    Min tree: Minimal data-transfer tree clustering without memory constraints.
    Iteratively calculates 'k-1' different ksplit clustering in reverse order until an L-feasible solution is found.
    Although latency is not considered on the critical path the algorithm reports it with the sum cost.

    For detailed information, see in  M. M. et al.: “Clustering on trees,” Computational Statistics & Data Analysis,
    vol. 24, no. 2, pp. 217–234, Apr. 1997, doi: 10.1016/S0167-9473(96)00062-X.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


########################################################################################################################

@main.group("tree")
def tree():
    """Tree partitioning algorithms."""
    click.get_current_context().obj.update({'INPUT_DATA_TYPE': InputDataType.TREE,
                                            'INPUT_ARG_REF': 'tree'})


@tree.group("layout")
def tree__layout():
    """Cost-optimal partitioning based on predefined resource flavors."""
    pass


class TreeLayoutILPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.layout.ilp`."""
    hybrid = "tree_gen_hybrid_partitioning"
    mtx = "tree_gen_mtx_partitioning"
    all = "all_gen_tree_mtx_partitioning"
    DEF = mtx


@tree__layout.command("ilp")
@algorithm(TreeLayoutILPType, root, flavor, L, cp_end, subchains, delay, pulp_solver, timeout)
def tree__layout__ilp(filename: pathlib.Path, alg: TreeLayoutILPType, **parameters: dict[str, ...]):
    """Cost-optimal partitioning based on ILP formalization."""
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


########################################################################################################################

@tree.group("parallel")
def tree__parallel():
    """Cost-minimal partitioning based on parallelized platform execution model."""
    pass


class TreeParallelGreedyType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.parallel.greedy`."""
    greedy = "greedy_par_tree_partitioning"
    DEF = greedy


@tree__parallel.command("greedy")
@algorithm(TreeParallelGreedyType, root, M, L, N, cp_end, delay)
def tree__parallel__greedy(filename: pathlib.Path, alg: TreeParallelGreedyType, **parameters: dict[str, ...]):
    """Cost-optimal partitioning using greedy edge cuts.

    Calculate minimal-cost partitioning of an app graph(tree) by greedily iterating over all possible cuttings.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreeParallelILPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.parallel.ilp`."""
    cfg = "tree_par_cfg_partitioning"
    hybrid = "tree_par_hybrid_partitioning"
    mtx = "tree_par_mtx_partitioning"
    all = "all_par_tree_mtx_partitioning"
    DEF = mtx


@tree__parallel.command("ilp")
@algorithm(TreeParallelILPType, root, M, L, N, cp_end, delay, subchains, pulp_solver, timeout)
def tree__parallel__ilp(filename: pathlib.Path, alg: TreeParallelILPType, **parameters: dict[str, ...]):
    """Cost-optimal partitioning based on ILP formalization."""
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreeParallelPseudoType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.parallel.pseudo`."""
    btree = "pseudo_par_btree_partitioning"
    ltree = "pseudo_par_ltree_partitioning"
    DEF = ltree


@tree__parallel.command("pseudo")
@algorithm(TreeParallelPseudoType, root, M, L, N, cp_end, delay, bidirect)
def tree__parallel__pseudo(filename: pathlib.Path, alg: TreeParallelPseudoType, **parameters: dict[str, ...]):
    """Cost-minimal partitioning based on specific tree traversals.

    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound 'M' on the total
    memory of blocks and a latency constraint 'L' defined on the subchain between 'root' and 'cp_end' nodes, while
    applying a bottom-up/left-right tree traversal approach.

    Btree: Provide suboptimal partitioning due to the inaccurate latency calculation that directly comes from the
    bottom-up tree traversal approach and parallelized platform execution model.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreeParallelPseudoMPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.parallel.pseudo_mp`."""
    ltree = "pseudo_par_mp_ltree_partitioning"
    DEF = ltree


@tree__parallel.command("pseudo_mp")
@algorithm(TreeParallelPseudoMPType, root, M, L, N, cp_end, delay, bidirect)
def tree__parallel__pseudo_mp(filename: pathlib.Path, alg: TreeParallelPseudoMPType, **parameters: dict[str, ...]):
    """Cost-minimal partitioning using parallelized multiprocessing.

    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound 'M' on the total
    memory of blocks and a latency constraint 'L' defined on the subchain between 'root' and 'cp_end' nodes.

    Partitioning is calculated using the left-right tree traversal approach.
    Arbitrary disjoint subtrees are partitioned in separate subprocesses.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


########################################################################################################################

@tree.group("path")
def tree__path():
    """Cost-optimal path-tree partitioning based on single-chain blocks.

    For detailed information, see in: J. Cz., I. P. and B. S., "Cost-optimal Operation of Latency Constrained
    Serverless Applications: From Theory to Practice," NOMS 2023-2023 IEEE/IFIP Network Operations and Management
    Symposium, Miami, FL, USA, 2023, pp. 1-10, doi: 10.1109/NOMS56928.2023.10154412.
    """
    pass


class TreePathGreedyType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.path.greedy`."""
    greedy = "greedy_tree_partitioning"
    DEF = greedy


@tree__path.command("greedy")
@algorithm(TreePathGreedyType, root, M, N, L, cp_end, delay, unit, only_cuts)
def tree__path__greedy(filename: pathlib.Path, alg: TreePathGreedyType, **parameters: dict[str, ...]):
    """Cost-optimal partitioning using greedy edge cuts.

    Calculates minimal-cost partitioning of an app graph(tree) by iterating over all possible cuttings.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreePathMetaType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.path.greedy`."""
    meta = "meta_tree_partitioning"
    DEF = meta


@tree__path.command("meta")
@algorithm(TreePathMetaType, root, M, N, L, cp_end, delay, unit, only_barr)
def tree__path__meta(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning based on a chain partition subroutine.

    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound 'M' on the total
    memory of blocks and a latency constraint 'L' defined on the subchain between 'root' and 'cp_end' nodes using
    the 'partition' function to partition subchains independently.

    Cost calculation relies on the rounding 'unit' and number of vCPU cores 'N', whereas platform invocation 'delay'
    is used for latency calculations.

    It gives an optimal result only in case the cost function regarding the chain attributes is subadditive,
    that is k_opt = k_min is guaranteed for each case.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreePathMinType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.path.greedy`."""
    min = "min_tree_partitioning"
    DEF = min


@tree__path.command("min")
@algorithm(TreePathMinType, root, M, N, L, cp_end, delay, unit, full)
def tree__path__min(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning based on a DP approach with subadditive cost.

    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound 'M' on the total
    memory of blocks and a latency constraint 'L' defined on the subchain between *root* and *cp_end* nodes.

    Cost calculation relies on the rounding *unit* and number of vCPU cores 'N', whereas platform invocation 'delay'
    is used for latency calculations.

    It gives an optimal result only in case the cost function regarding the chain attributes is subadditive,
    that is k_opt = k_min is guaranteed for each case.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreePathSeqType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.path.greedy`."""
    seq = "seq_tree_partitioning"
    DEF = seq


@tree__path.command("seq")
@algorithm(TreePathSeqType, root, M, N, L, cp_end, delay, unit, full)
def tree__path__seq(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning based on a direct dynamic programming approach.

    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound 'M' on the total
    memory of blocks and a latency constraint 'L' defined on the subchain between 'root' and 'cp_end' nodes leveraging
    a bottom-up tree traversal approach.

    Cost calculation relies on the rounding *unit* and number of vCPU cores 'N', whereas platform invocation 'delay'
    is used for latency calculations.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreePathSeqStateType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.path.greedy`."""
    cacheless = "cacheless_path_tree_partitioning"
    stateful = "stateful_path_tree_partitioning"
    DEF = stateful


@tree__path.command("state")
@algorithm(TreePathSeqStateType, root, M, N, L, cp_end, delay, validate)
def tree__path__state(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning based on a DP approach without data externalization.

    Calculates minimal-cost partitioning using <seq_tree_partitioning> while considering data implicit state
    externalization.
    Input tree is preprocessed and function runtimes are altered to incorporate data read/write overheads.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


########################################################################################################################

@tree.group("serial")
def tree__serial():
    """Cost-minimal partitioning based on serialized platform execution model."""
    pass


class TreeSerialBicriteriaType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.serial.bicriteria`."""
    biheuristic = "biheuristic_tree_partitioning"
    bifptas = "bifptas_tree_partitioning"
    dual = "bifptas_dual_tree_partitioning"
    DEF = bifptas


@tree__serial.command("bicriteria")
@algorithm(TreeSerialBicriteriaType, root, M, L, cp_end, delay, Epsilon, Lambda, bidirect)
def tree__serial__bicriteria(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-minimal partitioning based on approximation schemes.

    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound 'M' on the total
    memory of blocks and a latency constraint 'L' defined on the subchain between 'root' and 'cp_end' nodes, while
    applying the bottom-up tree traversal approach.

    Cost approximation ratio 'Epsilon' controls the maximum deviation from the cost-optimal partitioning
    (Epsilon=0.0 enforces the algorithm to calculate exact solution) in exchange for reduces subcase calculations.
    Latency approximation ratio ('Lambda') controls the maximum deviation with respect to the latency limit 'L'
    (Lambda=0.0 enforces no rounding) in exchange for reduces subcase calculations.

    Btree: Provide suboptimal partitioning due to the simplified and inaccurate latency rounding.

    Dual: Instead of direct cost calculations, the cumulative overheads of externalized states are subject
    to minimization as a different formalization of the same optimization problem.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreeSerialGreedyType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.serial.greedy`."""
    greedy = "greedy_ser_tree_partitioning"
    DEF = greedy


@tree__serial.command("greedy")
@algorithm(TreeSerialGreedyType, root, M, L, cp_end, delay)
def tree__serial__greedy(filename: pathlib.Path, alg, **parameters: dict[str, ...]):
    """Cost-optimal partitioning using greedy edge cuts.

    Calculate minimal-cost partitioning of an app graph(tree) by greedily iterating over all possible cuttings.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreeSerialILPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.serial.ilp`."""
    cfg = "tree_cfg_partitioning"
    hybrid = "tree_hybrid_partitioning"
    mtx = "tree_mtx_partitioning"
    all = "all_tree_mtx_partitioning"
    DEF = mtx


@tree__serial.command("ilp")
@algorithm(TreeSerialILPType, root, M, L, cp_end, delay, subchains, pulp_solver, timeout)
def tree__serial__ilp(filename: pathlib.Path, alg: TreeSerialILPType, **parameters: dict[str, ...]):
    """Cost-optimal partitioning based on ILP formalization."""
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreeSerialPseudoType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.serial.pseudo`."""
    btree = "pseudo_btree_partitioning"
    ltree = "pseudo_ltree_partitioning"
    DEF = ltree


@tree__serial.command("pseudo")
@algorithm(TreeSerialPseudoType, root, M, L, cp_end, delay, bidirect)
def tree__serial__pseudo(filename: pathlib.Path, alg: TreeSerialPseudoType, **parameters: dict[str, ...]):
    """Cost-minimal partitioning based on specific tree traversals.

    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound 'M' on the total
    memory of blocks and a latency constraint 'L' defined on the subchain between 'root' and 'cp_end' nodes, while
    applying a bottom-up/left-right tree traversal approach.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


class TreeSerialPseudoMPType(enum.Enum):
    """Partitioning algorithms in `slambuc.alg.tree.serial.pseudo_mp`."""
    btree = "pseudo_mp_btree_partitioning"
    ltree = "pseudo_mp_ltree_partitioning"
    DEF = ltree


@tree__serial.command("pseudo_mp")
@algorithm(TreeSerialPseudoMPType, root, M, L, cp_end, delay, bidirect)
def tree__serial__pseudo_mp(filename: pathlib.Path, alg: TreeSerialPseudoMPType, **parameters: dict[str, ...]):
    """Cost-minimal partitioning using parallelized multiprocessing.

    Calculates minimal-cost partitioning of an app graph(tree) with respect to an upper bound 'M' on the total
    memory of blocks and a latency constraint 'L' defined on the subchain between 'root' and 'cp_end' nodes.

    Partitioning is calculated using the left-right tree traversal approach.
    Arbitrary disjoint subtrees are partitioned in separate subprocesses.
    """
    invoke_algorithm(filename=filename, alg=alg.value, parameters=parameters)


########################################################################################################################

def log_info(msg: str):
    """Pretty print log message."""
    if not click.get_current_context().obj.get('OUTPUT_QUIET'):
        click.secho(msg, err=True)


def log_warn(msg: str):
    """Pretty print error message."""
    if not click.get_current_context().obj.get('OUTPUT_QUIET'):
        click.secho(msg, err=True, fg='yellow')


def log_err(msg: str):
    """Pretty print error message."""
    click.secho(msg, err=True, fg='red')


def read_input_file(filename: pathlib.Path, data_type: str, arg_names: tuple[str] | list[str]):
    """Read input data structure(s) from file."""
    data: nx.DiGraph | list[nx.DiGraph | list] | None = None
    suffix = filename.suffix
    try:
        if data_type == InputDataType.DAG:
            if suffix == '.gml':
                data = nx.read_gml(filename, destringizer=int)
            else:
                raise click.BadParameter(f"Unsupported format: {suffix!r} for data type: {data_type}.")
        elif data_type == InputDataType.TREE:
            if suffix == '.gml':
                data = nx.read_gml(filename, destringizer=int)
            elif suffix in ('.npy', '.svt', '.csv'):
                data = load_tree(filename, raw=False if suffix == '.csv' else True)
            else:
                raise click.BadParameter(f"Unsupported format: {suffix!r} for data type: {data_type}.")
        elif data_type == InputDataType.CHAIN:
            if suffix == '.npy':
                data = np.load(filename, mmap_mode='r', allow_pickle=False).tolist()
                if len(data) != len(arg_names):
                    raise click.BadParameter(f"Ambiguous data size: {len(data)}! Input file must contain "
                                             f"{len(arg_names)} lists for {arg_names!r}.")
            elif suffix == '.npz':
                npz_file = np.load(filename, mmap_mode='r', allow_pickle=False)
                if not set(arg_names) <= set(npz_file.keys()):
                    raise click.BadParameter(f"Missing input data! Input file must contain "
                                             f"{len(arg_names)} lists for {arg_names!r}.")
                data = list(npz_file[arg].tolist() for arg in arg_names)
            else:
                raise click.BadParameter(f"Unsupported format: {suffix!r} for data type: {data_type}.")
    except (ValueError, OSError, nx.NetworkXError) as e:
        log_err(f"Failed to parse {filename}: {e}")
    return dict(zip(arg_names, data)) if isinstance(arg_names, (list, tuple)) else {arg_names: data}


def validate_config(ctx: click.Context) -> bool:
    params = ctx.params
    if (lat := params.get("L", math.inf)) < math.inf and not (params.get("cp_end") or params.get('end')):
        log_warn(f"WARNING: Latency limit (L={lat}) is set but the critical path tail node "
                 f"[{'cp_end' if 'cp_end' in ctx.params else 'end'}] is missing!")
    if (tail := (ctx.params.get("cp_end") or ctx.params.get('end'))) is not None and math.isinf(ctx.params.get("L")):
        log_warn(f"WARNING: Critical path tail node ({'cp_end' if 'cp_end' in ctx.params else 'end'}={tail}) "
                 f"is set but latency limit [L] is missing!")
    return True


########################################################################################################################

def invoke_algorithm(filename: pathlib.Path, alg: str, parameters: dict[str, ...]):
    """Load input data and dynamically invoke partitioning algorithm."""
    ctx = click.get_current_context()
    ##################################
    module_name = f"slambuc.alg.{inspect.currentframe().f_back.f_code.co_name.replace('__', '.')}"
    log_info(f"Importing algorithm function: <{alg}> from SLAMBUC module: <{module_name}>")
    try:
        module = importlib.import_module(module_name)
        alg_method = getattr(module, alg)
    except AttributeError as e:
        log_err(f"Got unexpected error: {e}")
        raise click.ClickException from e
    ##################################
    log_info(f"Loading input data from file: {click.format_filename(filename)}")
    data = read_input_file(filename=filename, data_type=ctx.obj['INPUT_DATA_TYPE'], arg_names=ctx.obj['INPUT_ARG_REF'])
    if not data:
        raise click.ClickException(f"Missing input data!")
    log_info(f"Parsed input:")
    for name, obj in data.items():
        log_info(f"  - {name}: {obj}")
    ##################################
    spec = inspect.getfullargspec(alg_method)
    defaults = dict(reversed(list(kv for kv in zip(reversed(spec.args), reversed(spec.defaults)))))
    params = {arg: parameters[arg] if parameters[arg] is not None else defaults[arg]
              for arg in defaults for p in parameters if arg.casefold() == p.casefold()}
    log_info(f"Collected parameters:")
    for param, v in params.items():
        log_info(f"  - {param}: {v if isinstance(v, (str, int, float, type(None)))
        else v.__name__ if isinstance(v, type) else type(v).__name__}")
    data.update(params)
    ##################################
    if not validate_config(ctx=ctx):
        log_err("Failed to validate algorithm configuration! Exiting...")
        sys.exit(os.EX_CONFIG)
    ##################################
    try:
        log_info(f"Executing partitioning algorithm...")
        _start = time.perf_counter()
        results = alg_method(**data)
        _elapsed = (time.perf_counter() - _start) * 1e3
        log_info(f"  -> Algorithm finished successfully in {_elapsed:.6f} ms!")
        result_metrics = list(map(bool, results[:-1]) if isinstance(results, tuple)
                              else itertools.chain(map(bool, r[:-1]) for r in results))
        feasible = all(result_metrics) if parameters.get('metrics', True) else result_metrics[0]
        log_info(f"Received {'FEASIBLE' if feasible else 'INFEASIBLE'} solution:")
        dumper = functools.partial(json.dumps, indent=None, default=str) if ctx.obj.get('FORMAT_JSON') else repr
        for res in (results if ctx.obj.get('FORMAT_SPLIT') else (results,)):
            click.secho(dumper(res), fg='green' if feasible else 'yellow', bold=True)
    except Exception:
        log_err(traceback.format_exc())
        log_err(f"Got unexpected error during algorithm execution!")
        sys.exit(os.EX_SOFTWARE)
    except KeyboardInterrupt:
        log_info("Execution interrupted. Exiting...")
        sys.exit(os.EX_OK)


if __name__ == "__main__":
    main()
