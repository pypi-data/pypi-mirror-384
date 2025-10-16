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
import pandas as pd
from matplotlib import pyplot as plt

from slambuc.generator.cluster.job_tree import (DEF_TASK_CSV, DEF_TASK_CSV_COLS, DEF_TASK_CSV_HEADER,
                                                convert_tasks_to_dag,
                                                igenerate_job_tree, DEF_BATCH_CSV)
from slambuc.generator.transform import faasify_dag_by_duplication
from slambuc.misc.plot import draw_tree


def plot_job_dist(task_file: str = DEF_TASK_CSV, min_size: int = 0):
    job_df = pd.read_csv(task_file, usecols=DEF_TASK_CSV_COLS, names=DEF_TASK_CSV_HEADER)
    jobs = job_df.groupby("job")["task"].count()
    jobs = jobs[jobs >= min_size]
    max_size = jobs.max()
    print("Max size:", max_size)
    jobs.plot.hist(bins=50)
    plt.grid(linestyle='dotted', zorder=0)
    plt.show()


def verify_job_tree(job_name: str, task_file: str = DEF_TASK_CSV, draw_weights: bool = False):
    """Generate one job with given *job_name* into app tree and draw tree"""
    print(f"Read data from {task_file}...")
    job_df = pd.read_csv(task_file, usecols=DEF_TASK_CSV_COLS, names=DEF_TASK_CSV_HEADER)
    print(f"Filter task data for job {job_name}...")
    task_data = job_df[job_df["job"] == job_name]
    print(f"Generate tree from {len(task_data)} tasks...")
    dag, root = convert_tasks_to_dag(job_name, task_data)
    tree = faasify_dag_by_duplication(dag, root)
    print(f"Generated tree: {tree}")
    draw_tree(tree, draw_weights=draw_weights)


def check_job_trees(task_file: str = DEF_TASK_CSV, min_size: int = 0, max_size: int = None):
    """Validate generated job trees with size between *min_size* and *max_size*"""
    print(f"Load data from {task_file}...")
    job_df = pd.read_csv(task_file, usecols=DEF_TASK_CSV_COLS, names=DEF_TASK_CSV_HEADER)
    jobs = job_df.groupby("job")["task"].count()
    max_size = max_size if max_size else max(jobs)
    viable_jobs = jobs[(min_size <= jobs) & (jobs <= max_size)]
    print(f"Found {len(viable_jobs)} jobs with size in ({min_size} - {max_size})")
    trees = [t for t in igenerate_job_tree(job_df, min_size=min_size)]
    print("Generated app trees:")
    for tree in trees:
        print(tree, "is tree:", nx.is_tree(tree))


if __name__ == '__main__':
    # plot_job_dist(min_size=30)
    verify_job_tree(job_name="j_905", task_file=DEF_BATCH_CSV, draw_weights=True)
    #
    # check_job_trees(min_size=20, max_size=30)
    # check_job_trees(min_size=30)
