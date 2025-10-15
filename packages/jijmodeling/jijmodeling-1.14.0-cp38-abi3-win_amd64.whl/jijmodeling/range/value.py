# `jijmodeling.jijmodeling` is a module corresponding to the shared library
# created by PyO3,
# and `jijmodeling.jijmodeling.range` is its submodule defined dynamically
# while the initialization of the shared library.
#
# This file defines a new sub-module `jijmodeling.range`,
# and exposes all the components in `jijmodeling.jijmodeling.range`
#

from . import value as _value  # type: ignore
import sys

for component in _value.__all__:  # type: ignore
    setattr(sys.modules[__name__], component, getattr(_value, component))
