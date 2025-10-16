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
import math
import typing

# Service graph attributes
PLATFORM = 'P'
NAME = 'name'

# Node properties
RUNTIME = 'time'
MEMORY = 'mem'
# Optional, denoting the vCPU core demands in case of multi-threaded functions
CPU = 'cpu'

# Edge properties
RATE = 'rate'
DATA = 'data'
WEIGHT = 'weight'

# Additional attributes for plotting and preprocessing
COLOR = 'color'
LABEL = 'label'

# Separator character for state names, separating nodes in the group (VSEP) and group from assigned flavor (FSEP)
SEP = '|'
ASSIGN = '@'


class Flavor(typing.NamedTuple):
    """Store subtree partitioning attributes for a given subcase."""
    mem: int = math.inf  # Available memory
    ncore: int = 1  # Available relative vCPU cores
    cfactor: float = 1.0  # Relative cost factor

    def __repr__(self):
        # return repr(tuple(self))
        return self.name

    @property
    def name(self) -> str:
        """String representation of the given flavor."""
        return f"F{{{self.mem}|{self.ncore}|{self.cfactor}}}"
