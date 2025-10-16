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
from .greedy import greedy_par_tree_partitioning
from .ilp import (tree_par_cfg_partitioning, tree_par_hybrid_partitioning, tree_par_mtx_partitioning,
                  all_par_tree_mtx_partitioning)
from .pseudo import pseudo_par_ltree_partitioning
from .pseudo_mp import pseudo_par_mp_ltree_partitioning
