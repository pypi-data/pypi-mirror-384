# `jijmodeling.jijmodeling` is a module corresponding to the shared library created by PyO3,
# and `jijmodeling.jijmodeling.experimental` is its submodule defined dynamically
# while the initialization of the shared library.
#
# This file defines a new sub-module `jijmodeling.experimental`,
# and exposes all the components in `jijmodeling.jijmodeling.experimental`
#

from ._jijmodeling import experimental as _experimental  # type: ignore
import sys

for component in _experimental.__all__:
    setattr(sys.modules[__name__], component, getattr(_experimental, component))
