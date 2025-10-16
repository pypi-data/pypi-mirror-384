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
import itertools

import networkx as nx

from slambuc.alg.app import PLATFORM


def faasify_dag_by_duplication(dag: nx.DiGraph, root: int) -> nx.DiGraph | None:
    """
    One-way transformation of a DAG of modules/components into a tree by iteratively duplicating sub-graphs
    related to nodes with multiple predecessors.

    The algorithm requires that the input DAG must have only one source node.

    :param dag:     input DAG
    :param root:    root node
    :return:        generated tree
    """
    if dag is None:
        return None
    while not nx.is_tree(dag):
        new_id = itertools.count(max(filter(lambda _v: _v is not PLATFORM, dag.nodes)) + 1)
        for v in list(dag.nodes):
            if len(dag.pred[v]) > 1:
                while len(ingress := list(dag.pred[v])) > 1:
                    p = ingress.pop(0)
                    e_data = dag[p][v]
                    st = dag.subgraph(nx.dfs_postorder_nodes(dag, source=v))
                    relabel = {sv: next(new_id) for sv in st.nodes}
                    st = nx.relabel_nodes(st, mapping=relabel)
                    dag.update(st)
                    dag.remove_edge(p, v)
                    dag.add_edge(p, relabel[v], **e_data)
    # Add front-end dispatcher node for nodes without predecessors
    shift = max(filter(lambda _v: _v is not PLATFORM, dag.nodes))
    # Relabel nodes to confirm to our app tree structure demands
    shifted_mapper = {v: v + shift for _, v in nx.bfs_edges(dag, source=root)}
    nx.relabel_nodes(dag, mapping=shifted_mapper, copy=False)
    relabel = itertools.count(1)
    relabel_mapper = {v: next(relabel) for _, v in nx.bfs_edges(dag, source=PLATFORM, sort_neighbors=sorted)}
    nx.relabel_nodes(dag, mapping=relabel_mapper, copy=False)
    return dag


def faasify_dag_by_cutting(dag: nx.DiGraph, root: int) -> nx.DiGraph:
    ...
    # TODO
