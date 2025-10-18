# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

from collections import OrderedDict
from typing import Any, Generator, List, Tuple

from facto.inputgen.argtuple.engine import MetaArgTupleEngine
from facto.inputgen.argument.engine import MetaArg
from facto.inputgen.argument.gen import ArgumentGenerator
from facto.inputgen.specs.model import Spec


class ArgumentTupleGenerator:
    def __init__(self, spec: Spec):
        self.spec = spec

    def gen_tuple(
        self, meta_tuple: Tuple[MetaArg], *, out: bool = False
    ) -> Tuple[List[Any], OrderedDict[str, Any], OrderedDict[str, Any]]:
        posargs = []
        inkwargs = OrderedDict()
        outargs = OrderedDict()
        for ix, arg in enumerate(self.spec.inspec):
            m = meta_tuple[ix]
            val = ArgumentGenerator(m).gen()
            if arg.kw:
                inkwargs[arg.name] = val
            else:
                posargs.append(val)
        if out:
            for ix, arg in enumerate(self.spec.outspec):
                m = meta_tuple[ix + len(self.spec.inspec)]
                val = ArgumentGenerator(m).gen()
                outargs[arg.name] = val
        return posargs, inkwargs, outargs

    def gen(
        self, *, valid: bool = True, out: bool = False
    ) -> Generator[
        Tuple[List[Any], OrderedDict[str, Any], OrderedDict[str, Any]], Any, Any
    ]:
        engine = MetaArgTupleEngine(self.spec, out=out)
        for meta_tuple in engine.gen(valid=valid):
            yield self.gen_tuple(meta_tuple, out=out)
