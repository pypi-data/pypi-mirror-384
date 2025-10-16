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
from collections.abc import Generator

from slambuc.alg.app import Flavor

# Function signature types
T_BLOCK = list[int]  # list of block nodes
T_PART = list[T_BLOCK]  # partitioning as list of blocks
T_RESULTS = tuple[T_PART, int, int]  # Partitioning, sum cost, sum latency
T_PART_GEN = Generator[T_PART]
T_IBLOCK = tuple[int, int]  # Block interval start and end nodes
T_IBLOCK_GEN = Generator[T_IBLOCK]
T_FBLOCK = tuple[T_BLOCK, Flavor]
T_FPART = list[T_FBLOCK]
T_FRESULTS = tuple[T_FPART, int, int]
T_BARRS = list[int] | set[int] | dict[int, Flavor]  # list/set of barrier nodes
T_BARRS_GEN = Generator[T_BARRS]
T_BRESULTS = tuple[T_BARRS, int, int] | tuple[None, None, None] | tuple[None, None, int] | tuple[list, None, int]

# Constants for attribute indices in DP matrix
import math

BARR, COST, LAT = 0, 1, 2
# Constant for block cache index
MEM, CPU = 0, 3
# Constant for ILP model names
LP_LAT = 'C_LAT'

# Infeasible solution [partitioning, opt_cost, opt_lat]
INFEASIBLE = ([], math.inf, None)
