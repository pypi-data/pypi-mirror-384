"""
The Coordinerds package implements stuff for dealing with coordinates and generalized coordinate systems

It provides a semi-symbolic way to represent a CoordinateSystem and a CoordinateSet that provides coordinates within a
coordinate system. An extensible system for converting between coordinate systems and is provided.

The basic design of the package is set up so that one creates a `CoordinateSet` object, which in turn tracks its `CoordinateSystem`.
A `CoordinateSet` is a subclass of `np.ndarray`, and so any operation that works for a `np.ndarray` will work in turn for `CoordinateSet`.
This provides a large amount flexibility.

The `CoordinateSystem` object handles much of the heavy lifting for a `CoordinateSet`.
Conversions between different systems are implemented by a `CoordinateSystemConverter`.
Chained conversions are not _currently_ supported, but might well become supported in the future.
"""


__all__ = []
from .CoordinateSystems import *; from .CoordinateSystems import __all__ as exposed
__all__ += exposed
# from .CoordinateTransformations import __all__ as exposed
# __all__ += exposed
from .Conveniences import *; from .Conveniences import __all__ as exposed
__all__ += exposed
from .Internals import *; from .Internals import __all__ as exposed
__all__ += exposed
from .ZMatrices import *; from .ZMatrices import __all__ as exposed
__all__ += exposed
from .Labels import *; from .Labels import __all__ as exposed
__all__ += exposed
from .Generators import *; from .Generators import __all__ as exposed
__all__ += exposed
from .Pruning import *; from .Pruning import __all__ as exposed
__all__ += exposed
from .Redundant import *; from .Redundant import __all__ as exposed
__all__ += exposed