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
import pathlib
import random

from slambuc.misc.io import save_trees_to_file
from slambuc.misc.random import get_random_tree

# Attribute intervals
RUNTIME = (10, 500)  # Overall running time in ms
MEMORY = (64, 512)  # Peak memory demand in MB
DATA = (10, 100)  # Read/write overhead in ms
RATE = (1, 10)  # Invocations rate in 1/s

DEF_RAND_TREE_PREFIX = "random_tree"


def generate_random_trees(n: int, data_dir: str, iteration: int = 1000, file_prefix: str = DEF_RAND_TREE_PREFIX):
    """
    Generate random trees with attributes uniformly drawn form intervals.

    :param n:           tree size
    :param data_dir:    directory of saved trees
    :param iteration:   number of generated trees
    :param file_prefix: prefix name of tree files
    """
    print(f"Generating random trees with size {n}...")
    trees = [get_random_tree(nodes=n, runtime=RUNTIME, memory=MEMORY, rate=RATE, data=DATA) for _ in range(iteration)]
    file_name = pathlib.Path(data_dir, f"{file_prefix}_n{n}.npy").resolve()
    print(f"Saving trees into {file_name}...")
    save_trees_to_file(trees, file_name)


def generate_all_random_trees(data_dir: str, iteration: int = 100, start: int = 10, end: int = 100, step: int = 10,
                              file_prefix: str = DEF_RAND_TREE_PREFIX):
    """
    Generate random app trees with random sizes from given intervals.

    :param data_dir:    directory of saved trees
    :param iteration:   number of generated trees
    :param start:       minimum of size intervals
    :param end:         maximum of size intervals
    :param step:        step size of intervals
    :param file_prefix: prefix name of tree files
    """
    for min_size, max_size in itertools.pairwise(range(start, end + step, step)):
        print(f"Generating random trees with {min_size} <= size <= {max_size}...")
        trees = [get_random_tree(nodes=random.randint(min_size, max_size), runtime=RUNTIME, memory=MEMORY,
                                 rate=RATE, data=DATA, name=DEF_RAND_TREE_PREFIX + f"_{i}") for i in range(iteration)]
        file_name = pathlib.Path(data_dir, f"{file_prefix}_n{min_size}-{max_size}.npy").resolve()
        print(f"Saving trees into {file_name}...")
        save_trees_to_file(trees, file_name, padding=max_size)
    print("Finished")


if __name__ == '__main__':
    generate_all_random_trees("../../../validation/data")
