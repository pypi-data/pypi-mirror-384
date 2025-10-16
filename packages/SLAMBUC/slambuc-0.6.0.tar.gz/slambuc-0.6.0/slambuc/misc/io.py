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
import operator
import pathlib
import warnings
from collections.abc import Generator
from functools import partial
from importlib.resources.abc import Traversable

import networkx as nx
import numpy as np

from slambuc.alg.app.common import *


def encode_service_tree(tree: nx.DiGraph, root: int = 0, pad_size: int = 0) -> np.ndarray:
    """
    Encode the given app *tree* into an array with size of **5*n** where n is the size of the tree.

    The tree must have the tree structure where the root is PLATFORM and the node IDs are increasing integers from *1*
    to *n*. The array's structure is *[r, S_(n-1), R_n, D_n, T_n, M_n]*, where
        - *r* is the root node of the tree (default is PLATFORM that is converted to node *0*),
        - *S_(n-1) is the Prufer sequence of the tree extended with root node PLATFORM,
        - *D_n, R_n* are the ingress edge attributes (DATA, RATE) and
        - *T_n, M_n* are the node attributes (RUNTIME, MEMORY) of the tree nodes in increasing order from *1* to *n*.

    :param tree:        app tree
    :param root:        root node
    :param pad_size:    padding size for uniform length
    :return:            encoded tree as value arrays
    """
    data_seq = np.fromiter(
        itertools.chain(
            [root, *nx.to_prufer_sequence(nx.relabel_nodes(tree.to_undirected(as_view=True), {PLATFORM: root}))],
            (tree[u][v][DATA] for u, v in sorted(tree.edges, key=operator.itemgetter(1))),
            (tree[u][v][RATE] for u, v in sorted(tree.edges, key=operator.itemgetter(1))),
            (tree.nodes[v][RUNTIME] for _, v in sorted(tree.edges, key=operator.itemgetter(1))),
            (tree.nodes[v][MEMORY] for _, v in sorted(tree.edges, key=operator.itemgetter(1)))),
        dtype=np.int64)
    # Padding each vector to have a uniform length for saving
    pad_width = max(0, pad_size - len(tree) + 1)
    return np.pad(data_seq.reshape((5, -1)), pad_width=((0, 0), (0, pad_width)))


def decode_service_tree(tdata: np.ndarray) -> nx.DiGraph:
    """
    Decode and rebuild app tree from value arrays.

    Inverse method of :func:`encode_service_tree`.

    :param tdata:   array values
    :return:        app tree
    """
    if tdata.shape[0] % 5:
        warnings.warn(f"Given data with shape {tdata.shape} is not a valid encoded tree!")
    root, *prufer_seq = np.trim_zeros(tdata[0, :], 'b')
    tree = nx.bfs_tree(nx.from_prufer_sequence(prufer_seq), source=root, sort_neighbors=sorted)
    for u, v in tree.edges:
        tree[u][v][DATA], tree[u][v][RATE], tree.nodes[v][RUNTIME], tree.nodes[v][MEMORY] = tdata[1:, v - 1]
    nx.relabel_nodes(tree, {0: PLATFORM}, copy=False)
    tree.graph[NAME] = "tree_" + "".join(map(str, tdata[0]))
    return tree


def save_tree(tree: nx.DiGraph, file_name: str | pathlib.Path, padding: int = 0, raw: bool = True):
    """
    Convert trees into a compact format and save them in a single file.
    """
    saver = partial(np.save, allow_pickle=False) if raw else partial(np.savetxt, fmt='%i', delimiter=',')
    saver(file_name, encode_service_tree(tree, pad_size=padding))


def load_tree(file_name: str | pathlib.Path, raw: bool = True) -> nx.DiGraph:
    """
    Convert trees into a compact format and save them in a single file.
    """
    if raw:
        loader = partial(np.load, mmap_mode="r", allow_pickle=False)
    else:
        loader = partial(np.loadtxt, dtype=int, delimiter=',')
    return decode_service_tree(loader(file_name))


def save_trees_to_file(trees: list[nx.DiGraph], file_name: str | pathlib.Path = "test_trees.npy", padding: int = 0):
    """
    Convert trees into a compact format and save them in a single file.

    :param trees:       list of trees
    :param file_name:   output file name
    :param padding:     padding size
    """
    enc_trees = list(encode_service_tree(t, pad_size=padding) for t in trees)
    if enc_trees:
        np.save(file_name, np.stack(enc_trees))


def get_tree_from_file(file_name: str | pathlib.Path, tree_num: int) -> nx.DiGraph:
    """
    Load and decode an app tree from the given *file_name* with specific ID *tree_num*.

    :param file_name:   file name
    :param tree_num:    tree ID
    :return:            loaded tree
    """
    np_trees = np.load(file_name, mmap_mode="r", allow_pickle=False)
    return decode_service_tree(np_trees[tree_num - 1, :])


def iload_trees_from_file(file_name: str | pathlib.Path) -> Generator[nx.DiGraph]:
    """
    Generator of app trees loaded from given *file_name*.

    :param file_name:   tree file
    :return:            generator of trees
    """
    np_trees = np.load(file_name, mmap_mode="r", allow_pickle=False)
    for idx in range(np_trees.shape[0]):
        yield decode_service_tree(np_trees[idx, :])


def load_hist_params(hist_dir: str | pathlib.Path | Traversable, hist_name: str) -> tuple[..., ...]:
    """
    Load pickled attributes from given file.

    :param hist_dir:    directory of histogram attributes
    :param hist_name:   name of the histogram
    :return:            loaded histogram attributes
    """
    return tuple(np.load((pathlib.Path(hist_dir, hist_name).with_suffix('.npz')).resolve()).values())
