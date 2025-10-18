# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import math
from typing import Any, List, Union

from facto.inputgen.variable.space import Discrete, VariableSpace
from facto.inputgen.variable.type import convert_to_vtype, invalid_vtype, is_integer


class SolvableVariable:
    """
    A solvable variable is a variable over which we can impose constraints.
    It needs to be initialized with the variable type. It maintains an internal state
    of the possible values of the variable, represented by a VariableSpace object.
    It supports the following constraints:
        - Eq: Equal to a specific value
        - Ne: Not equal to a specific value
        - In: Contained in a list of values
        - NotIn: Not contained in a list of values
        - Le: Less than or equal to a specific value
        - Lt: Less than a specific value
        - Ge: Greater than or equal to a specific value
        - Gt: Greater than a specific value
    The result of applying multiple constraints to a solvable variable, is the
    conjunction of those constraints.
    """

    def __init__(self, vtype: type):
        self.vtype = vtype
        self.space = VariableSpace(vtype)

    def Eq(self, v: Any) -> None:
        if invalid_vtype(self.vtype, v):
            raise TypeError("Variable type mismatch")
        if self.space.empty():
            return
        if self.space.contains(v):
            self.space.discrete = Discrete([convert_to_vtype(self.vtype, v)])
        else:
            self.space.discrete = Discrete([])

    def Ne(self, v: Any) -> None:
        if invalid_vtype(self.vtype, v):
            raise TypeError("Variable type mismatch")
        if self.space.empty():
            return
        self.space.remove(v)

    def In(self, values: List[Any]) -> None:
        for v in values:
            if invalid_vtype(self.vtype, v):
                raise TypeError("Variable type mismatch")
        if self.space.empty():
            return
        self.space.discrete = Discrete(
            [convert_to_vtype(self.vtype, v) for v in values if self.space.contains(v)]
        )

    def NotIn(self, values: List[Any]) -> None:
        for v in values:
            if invalid_vtype(self.vtype, v):
                raise TypeError("Variable type mismatch")
        if self.space.empty():
            return
        for v in values:
            self.space.remove(v)

    def Le(self, upper: Union[bool, int, float]) -> None:
        if self.vtype not in [bool, int, float]:
            raise Exception(f"Le is not valid constraint on {self.vtype}")
        if invalid_vtype(self.vtype, upper):
            raise TypeError("Variable type mismatch")
        if self.space.empty():
            return
        elif self.space.discrete.initialized:
            self.space.discrete.filter(lambda v: v <= upper)
        elif self.vtype == int:
            if math.isfinite(upper):
                self.space.intervals.set_upper(math.ceil(upper), upper_open=False)
            else:
                self.space.intervals.set_upper(upper, upper_open=False)
        else:
            self.space.intervals.set_upper(float(upper), upper_open=False)

    def Lt(self, upper: Union[bool, int, float]) -> None:
        if self.vtype not in [bool, int, float]:
            raise Exception(f"Lt is not valid constraint on {self.vtype}")
        if invalid_vtype(self.vtype, upper):
            raise TypeError("Variable type mismatch")
        if self.space.empty():
            return
        elif self.space.discrete.initialized:
            self.space.discrete.filter(lambda v: v < upper)
        elif self.vtype == int:
            if math.isfinite(upper):
                self.space.intervals.set_upper(
                    math.floor(upper), upper_open=is_integer(upper)
                )
            else:
                self.space.intervals.set_upper(upper, upper_open=True)
        else:
            self.space.intervals.set_upper(float(upper), upper_open=True)

    def Ge(self, lower: Union[bool, int, float]) -> None:
        if self.vtype not in [bool, int, float]:
            raise Exception(f"Ge is not valid constraint on {self.vtype}")
        if invalid_vtype(self.vtype, lower):
            raise TypeError("Variable type mismatch")
        if self.space.empty():
            return
        elif self.space.discrete.initialized:
            self.space.discrete.filter(lambda v: v >= lower)
        elif self.vtype == int:
            if math.isfinite(lower):
                self.space.intervals.set_lower(math.ceil(lower), lower_open=False)
            else:
                self.space.intervals.set_lower(lower, lower_open=False)
        else:
            self.space.intervals.set_lower(float(lower), lower_open=False)

    def Gt(self, lower: Union[bool, int, float]) -> None:
        if self.vtype not in [bool, int, float]:
            raise Exception(f"Gt is not valid constraint on {self.vtype}")
        if invalid_vtype(self.vtype, lower):
            raise TypeError("Variable type mismatch")
        if self.space.empty():
            return
        elif self.space.discrete.initialized:
            self.space.discrete.filter(lambda v: v > lower)
        elif self.vtype == int:
            if math.isfinite(lower):
                self.space.intervals.set_lower(
                    math.ceil(lower), lower_open=is_integer(lower)
                )
            else:
                self.space.intervals.set_lower(lower, lower_open=True)
        else:
            self.space.intervals.set_lower(float(lower), lower_open=True)
