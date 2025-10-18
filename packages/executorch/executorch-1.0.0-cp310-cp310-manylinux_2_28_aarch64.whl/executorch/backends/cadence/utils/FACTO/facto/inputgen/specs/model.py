# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional

from facto.inputgen.argument.type import ArgType
from facto.inputgen.attribute.model import Attribute


class ConstraintSuffix(str, Enum):
    EQ = "eq"  # ==
    NE = "ne"  # !=
    IN = "in"  # in list
    NOTIN = "notin"  # not in list
    LE = "le"  # <=
    LT = "lt"  # <
    GE = "ge"  # >=
    GT = "gt"  # >
    # TODO(mcandales): Enable Such That
    # ST = "st"  # such that.
    GEN = "gen"  # generate.
    # This constraint is used to provide functions that generate
    # valid and invalid values
    BE = "be"  # be
    # This constraint is used to provide values that we want to
    # sample from, in cases where there are no imposed constraints
    # on the attribute, but we still have a preference for certain
    # values.


@dataclass
class Constraint:
    attribute: Attribute
    suffix: ConstraintSuffix
    fn: Callable


class ConstraintAttributeSuffixes:
    def __init__(self, attr: Attribute):
        self.Eq = lambda fn: Constraint(attr, ConstraintSuffix.EQ, fn)
        self.Ne = lambda fn: Constraint(attr, ConstraintSuffix.NE, fn)
        self.In = lambda fn: Constraint(attr, ConstraintSuffix.IN, fn)
        self.NotIn = lambda fn: Constraint(attr, ConstraintSuffix.NOTIN, fn)
        if attr in [Attribute.LENGTH, Attribute.RANK, Attribute.SIZE, Attribute.VALUE]:
            self.Le = lambda fn: Constraint(attr, ConstraintSuffix.LE, fn)
            self.Lt = lambda fn: Constraint(attr, ConstraintSuffix.LT, fn)
            self.Ge = lambda fn: Constraint(attr, ConstraintSuffix.GE, fn)
            self.Gt = lambda fn: Constraint(attr, ConstraintSuffix.GT, fn)
        # TODO(mcandales): Enable Such That
        # self.St = lambda fn: Constraint(attr, ConstraintSuffix.ST, fn)
        self.Be = lambda fn: Constraint(attr, ConstraintSuffix.BE, fn)
        self.Gen = lambda fn: Constraint(attr, ConstraintSuffix.GEN, fn)


class ConstraintProducer:
    Optional = ConstraintAttributeSuffixes(Attribute.OPTIONAL)
    Dtype = ConstraintAttributeSuffixes(Attribute.DTYPE)
    Length = ConstraintAttributeSuffixes(Attribute.LENGTH)
    Rank = ConstraintAttributeSuffixes(Attribute.RANK)
    Size = ConstraintAttributeSuffixes(Attribute.SIZE)
    Value = ConstraintAttributeSuffixes(Attribute.VALUE)


class BaseArg:
    def __init__(
        self,
        argtype: ArgType,
        name: str,
        deps: Optional[List[int]] = None,
        constraints: Optional[List[Constraint]] = None,
    ):
        self.name: str = name
        self.type: ArgType = argtype
        self.deps = () if deps is None else tuple(deps)
        self.constraints = [] if constraints is None else constraints
        self._kw: bool = False
        self._out: bool = False
        self._ret: bool = False

    @property
    def kw(self):
        return self._kw

    @kw.setter
    def kw(self, v):
        if not isinstance(v, bool):
            raise ValueError("kw property should be boolean")
        self._kw = v

    @property
    def out(self):
        return self._out

    @out.setter
    def out(self, v):
        if not isinstance(v, bool):
            raise ValueError("out property should be boolean")
        self._out = v

    @property
    def ret(self):
        return self._ret

    @ret.setter
    def ret(self, v):
        if not isinstance(v, bool):
            raise ValueError("ret property should be boolean")
        self._ret = v


class InArg(BaseArg):
    def __init__(self, *args, **kwargs):
        BaseArg.__init__(self, *args, **kwargs)


class InPosArg(InArg):
    def __init__(self, *args, **kwargs):
        BaseArg.__init__(self, *args, **kwargs)


class InKwArg(InArg):
    def __init__(self, *args, **kwargs):
        BaseArg.__init__(self, *args, **kwargs)
        self._kw = True


class OutArg(BaseArg):
    def __init__(self, argtype: ArgType, name: str = "out", *args, **kwargs):
        BaseArg.__init__(self, argtype, name, *args, **kwargs)
        self._kw = True
        self._out = True


class Return(BaseArg):
    def __init__(self, argtype: ArgType, name: str = "__ret", *args, **kwargs):
        BaseArg.__init__(self, argtype, name, *args, **kwargs)
        self._ret = True


class Spec:
    def __init__(self, op: str, inspec: List[InArg], outspec: List[OutArg]):
        self.op = op
        self.inspec = inspec
        self.outspec = outspec
