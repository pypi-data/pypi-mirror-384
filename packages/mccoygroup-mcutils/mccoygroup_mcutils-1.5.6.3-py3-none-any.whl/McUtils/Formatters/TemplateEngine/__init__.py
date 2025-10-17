"""
Provides a uniform interface for generating layouts from templates
by walking an object and its properties/children.
"""

__all__ = []
from .ObjectWalker import *; from .ObjectWalker import __all__ as exposed
__all__ += exposed
from .TemplateEngine import *; from .TemplateEngine import __all__ as exposed
__all__ += exposed