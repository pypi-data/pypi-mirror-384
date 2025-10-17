"""
A package for managing extension modules.
The existing `ExtensionLoader` will be moving here, and will be supplemented by classes for dealing with compiled extensions
"""




__all__ = []
from .CLoader import *; from .CLoader import __all__ as exposed
__all__ += exposed
from .ModuleLoader import *; from .ModuleLoader import __all__ as exposed
__all__ += exposed
from .ArgumentSignature import *; from .ArgumentSignature import __all__ as exposed
__all__ += exposed
from .SharedLibraryManager import *; from .SharedLibraryManager import __all__ as exposed
__all__ += exposed
from .FFI import *; from .FFI import __all__ as exposed
__all__ += exposed