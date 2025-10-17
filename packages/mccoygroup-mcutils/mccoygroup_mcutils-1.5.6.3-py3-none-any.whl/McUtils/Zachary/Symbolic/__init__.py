"""
The symbolic function capabilities of `McUtils`.
Intended not to give SymPy-like elegant reduction of arbitrary expressions
but instead work with the very common case of having a function composed
of elementary functions or tensor expressions and needing derivatives and evaluation
"""

__all__ = []
from .TensorExpressions import *; from .TensorExpressions import __all__ as exposed
__all__ += exposed
from .ElementaryFunctions import *; from .ElementaryFunctions import __all__ as exposed
__all__ += exposed