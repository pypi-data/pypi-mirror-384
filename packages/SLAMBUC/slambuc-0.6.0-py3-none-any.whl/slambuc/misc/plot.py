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
import warnings

import networkx as nx
from matplotlib import pyplot as plt

from slambuc.alg.app.common import *
from slambuc.alg.ext.csp import decode_state, START, END, COST, LAT
from slambuc.alg.util import path_blocks, ihierarchical_nodes

PART_COLORS = ('red', 'orange', "brown", 'green', "purple", "blue", "black", "magenta")


def draw_tree(tree: nx.DiGraph, partition: list = None, cuts: list = None, draw_weights=False, draw_blocks=False,
              figsize=None, ax=None, **kwargs):
    """
    Draw tree with given partitioning in a top-down topological structure.

    :param tree:            app tree
    :param partition:       calculated partitioning (optional)
    :param cuts:            calculated cuts (optional)
    :param draw_weights:    draw node/edge weights instead of IDs
    :param draw_blocks:     draw surrounding blocks
    :param figsize:         figure dimensions (optional)
    :param ax:              matplotlib axis (optional)
    """
    if figsize is None:
        d = nx.dag_longest_path_length(tree)
        figsize = (d, d)
    if ax is None:
        plt.figure(figsize=figsize, dpi=300)
        ax = plt.gca()
    colors = itertools.cycle(PART_COLORS)
    for v in tree.nodes:
        if COLOR in tree.nodes[v]:
            del tree.nodes[v][COLOR]
    tree.nodes[PLATFORM][COLOR] = "gray"
    if partition:
        if isinstance(partition[0], tuple):
            if len(PART_COLORS) < len(set(p[-1] for p in partition)):
                warnings.warn(f"Not enough colors({len(PART_COLORS)}) for all different flavor!")
            f_colors = dict()
            for (blk, f) in partition:
                if f not in f_colors:
                    f_colors[f] = next(colors)
                for n in blk:
                    tree.nodes[n][COLOR] = f_colors[f]
            partition = [blk[0] for blk in partition]
        else:
            for node, pred in nx.bfs_predecessors(tree, PLATFORM):
                if COLOR in tree.nodes[node]:
                    continue
                blk = 0
                while node not in partition[blk]:
                    blk += 1
                color = next(colors)
                if COLOR in tree.nodes[pred]:
                    while tree.nodes[pred][COLOR] == color:
                        color = next(colors)
                for n in partition[blk]:
                    tree.nodes[n][COLOR] = color
        node_colors = [tree.nodes[n][COLOR] for n in tree.nodes]
    else:
        node_colors = ["tab:gray" if n is PLATFORM else "tab:green" for n in tree.nodes]
    if cuts:
        edge_colors = ["tab:red" if e in cuts else "black" for e in tree.edges]
    else:
        edge_colors = "black"
    if draw_weights:
        labels = {n: f"T{tree.nodes[n][RUNTIME]}\nM{tree.nodes[n][MEMORY]}" for n in tree.nodes if n is not PLATFORM}
    else:
        labels = {n: n for n in tree.nodes}
    labels[PLATFORM] = PLATFORM
    pos = nx.drawing.nx_agraph.graphviz_layout(tree, prog='dot', root=str(0))
    nx.draw(tree, ax=ax, pos=pos, arrows=True, arrowsize=20, width=2, with_labels=True, node_size=1000, font_size=10,
            font_color="white", labels=labels, node_color=node_colors, edge_color=edge_colors, **kwargs)
    if draw_weights:
        e_labels = {(u, v): f"R{tree[u][v][RATE]}\nD{tree[u][v][DATA]}" for u, v in tree.edges}
        nx.draw_networkx_edge_labels(tree, pos, edge_labels=e_labels, label_pos=0.5, font_size=10)
    if draw_blocks:
        dist_x = sorted({k[0] for k in pos.values()})
        dist_y = sorted({k[1] for k in pos.values()})
        off_x = 0.5 * (sum(abs(b - a) for a, b in itertools.pairwise(dist_x)) // len(dist_x)
                       if len(dist_x) > 1 else pos[PLATFORM][0])
        off_y = 0.5 * (sum(abs(b - a) for a, b in itertools.pairwise(dist_y)) // len(dist_y)
                       if len(dist_y) > 1 else pos[PLATFORM][1])
        for blk in partition:
            lefts, rights = ([(pos[blk[0]][0] - off_x, pos[blk[0]][1] + off_y)],
                             [(pos[blk[0]][0] + off_x, pos[blk[0]][1] + off_y)])
            levels = path_blocks(list(nx.topological_generations(tree)), blk)
            for i, lvl in enumerate(levels):
                lefts.append((pos[min(lvl)][0] - off_x, pos[min(lvl)][1]))
                rights.append((pos[max(lvl)][0] + off_x, pos[max(lvl)][1]))
            lefts.append((pos[min(levels[-1])][0] - off_x, pos[min(levels[-1])][1] - off_y))
            rights.append((pos[max(levels[-1])][0] + off_x, pos[max(levels[-1])][1] - off_y))
            rights.reverse()
            poly = plt.Polygon(lefts + rights, closed=True, fc=tree.nodes[blk[0]][COLOR], ec=tree.nodes[blk[0]][COLOR],
                               lw=3, ls=':', fill=True, alpha=0.3, capstyle='round', zorder=0)
            ax.add_patch(poly)
    # noinspection PyUnresolvedReferences
    plt.title(tree.graph[NAME])
    plt.tight_layout()
    plt.show()
    plt.close()


def draw_dag(dag: nx.DiGraph, partition: list = None, draw_weights=False, figsize=None, ax=None, **kwargs):
    """
    Draw tree with given partitioning in a top-down topological structure.

    :param dag:             app tree
    :param partition:       calculated partitioning (optional)
    :param cuts:            calculated cuts (optional)
    :param draw_weights:    draw node/edge weights instead of IDs
    :param figsize:         figure dimensions (optional)
    :param ax:              matplotlib axis (optional)
    """
    if figsize is None:
        d = nx.dag_longest_path_length(dag)
        figsize = (d, d)
    if ax is None:
        plt.figure(figsize=figsize, dpi=300)
        ax = plt.gca()
    colors = itertools.cycle(PART_COLORS)
    for v in dag.nodes:
        if COLOR in dag.nodes[v]:
            del dag.nodes[v][COLOR]
    dag.nodes[PLATFORM][COLOR] = "gray"
    if partition:
        if isinstance(partition[0], tuple):
            if len(PART_COLORS) < len(set(p[-1] for p in partition)):
                warnings.warn(f"Not enough colors({len(PART_COLORS)}) for all different flavor!")
            f_colors = dict()
            for (blk, f) in partition:
                if f not in f_colors:
                    f_colors[f] = next(colors)
                for n in blk:
                    dag.nodes[n][COLOR] = f_colors[f]
            partition = [blk[0] for blk in partition]
        else:
            for node, pred in nx.bfs_predecessors(dag, PLATFORM):
                if COLOR in dag.nodes[node]:
                    continue
                blk = 0
                while node not in partition[blk]:
                    blk += 1
                color = next(colors)
                if COLOR in dag.nodes[pred]:
                    while dag.nodes[pred][COLOR] == color:
                        color = next(colors)
                for n in partition[blk]:
                    dag.nodes[n][COLOR] = color
            for u, v in dag.edges:
                if dag.nodes[u][COLOR] == dag.nodes[v][COLOR]:
                    dag[u][v][COLOR] = dag.nodes[v][COLOR]
        node_colors = [dag.nodes[n][COLOR] for n in dag.nodes]
        edge_colors = [dag[u][v][COLOR] if COLOR in dag[u][v] else "lightgray" for u, v in dag.edges]
    else:
        node_colors = ["tab:gray" if n is PLATFORM else "tab:green" for n in dag.nodes]
        edge_colors = "black"
    if draw_weights:
        labels = {n: f"T{dag.nodes[n][RUNTIME]}\nM{dag.nodes[n][MEMORY]}" for n in dag.nodes if n is not PLATFORM}
    else:
        labels = {n: n for n in dag.nodes}
    labels[PLATFORM] = PLATFORM
    layers = {v: i for i, l in enumerate(ihierarchical_nodes(dag, PLATFORM)) for v in l}
    for v in dag.nodes:
        dag.nodes[v]['layer'] = layers[v]
    # pos = nx.multipartite_layout(dag, align="horizontal", subset_key='layer', scale=1)
    # noinspection PyUnresolvedReferences
    pos = nx.bfs_layout(dag, start=PLATFORM, align="horizontal", scale=1)
    pos = {k: [x, -y] for k, (x, y) in pos.items()}
    nx.draw(dag, ax=ax, pos=pos, arrows=True, arrowsize=20, width=2, with_labels=True, node_size=1000, font_size=10,
            font_color="white", labels=labels, node_color=node_colors, edge_color=edge_colors, **kwargs)
    if draw_weights:
        e_labels = {(u, v): f"R{dag[u][v][RATE]}\nD{dag[u][v][DATA]}" for u, v in dag.edges}
        nx.draw_networkx_edge_labels(dag, pos, edge_labels=e_labels, label_pos=0.5, font_size=10)
    # noinspection PyUnresolvedReferences
    plt.title(dag.graph[NAME])
    plt.tight_layout()
    plt.show()
    plt.close()


def draw_state_dag(dag: nx.DiGraph, chains: list[list[int]], draw_weights: bool = False):
    """
    Draw state-space DAG in a vertically-ordered multipartite layout.

    :param dag:             input DAG
    :param chains:          chain decomposition of the given tree
    :param draw_weights:    draw node/edge weights instead of IDs
    """
    h = max(len(c) for c in chains) * 1.5
    plt.figure(figsize=(2 * h, h), dpi=300)
    layers = [START, *itertools.chain.from_iterable(chains), END]
    for v in dag.nodes:
        dag.nodes[v]['layer'] = layers.index(decode_state(v)[0][0] if v not in (START, END) else v)
    node_color = ["tab:green" if n is START else "tab:red" if n is END else "tab:blue" for n in dag.nodes]
    pos = nx.multipartite_layout(dag, subset_key='layer', scale=1)
    nx.draw(dag, pos=pos, arrows=True, arrowsize=15, width=2, with_labels=True, node_size=1000, font_size=10,
            node_color=node_color)
    if draw_weights:
        e_labels = {(u, v): f"C:{dag[u][v][COST]},L:{dag[u][v][LAT][1]}" for u, v in dag.edges}
        nx.draw_networkx_edge_labels(dag, pos, edge_labels=e_labels, label_pos=0.5, font_size=10)
    plt.show()
    plt.close()
