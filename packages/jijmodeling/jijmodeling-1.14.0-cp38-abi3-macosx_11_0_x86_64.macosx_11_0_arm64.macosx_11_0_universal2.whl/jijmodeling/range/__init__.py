# `jijmodeling.jijmodeling` is a module corresponding to the shared library
# created by PyO3,
# and `jijmodeling.jijmodeling.range` is its submodule defined dynamically
# while the initialization of the shared library.
#
# This file defines a new sub-module `jijmodeling.range`,
# and exposes all the components in `jijmodeling.jijmodeling.range`
#

from .._jijmodeling import range as _range  # type: ignore
import sys

for component in _range.__all__:
    setattr(sys.modules[__name__], component, getattr(_range, component))
