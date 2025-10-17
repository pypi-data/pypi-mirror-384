"""
Provides a uniform interface for potentially installed external programs
"""

__all__ = [
    "ExternalProgramInterface"
]

import weakref
import importlib


class ExternalProgramInterface:
    name = None
    module = None
    lib_supported = None
    library = None

    @classmethod
    def try_load_lib(cls):
        if cls.library is None:
            if cls.lib_supported is False:
                raise ImportError("Library '{}' is not installed".format(cls.name))
            try:
                cls.library = cls.load_library()
            except ImportError:
                cls.lib_supported = False
            else:
                cls.lib_supported = True
        return cls.lib_supported

    @classmethod
    def get_lib(cls):
        if cls.try_load_lib():
            return cls.library
        else:
            raise ImportError("module {} not installed".format(cls.module))

    @classmethod
    def load_library(cls):
        if '.' in cls.module:
            return __import__(cls.module, fromlist=[None])
        else:
            return __import__(cls.module)
        # raise NotImplementedError("{} needs to implement `load_library`".format(cls.__name__))

    method_table = weakref.WeakValueDictionary()
    @classmethod
    def method(cls, name:'str|list[str]'):
        if isinstance(name, str):
            if name not in cls.method_table:
                cls.method_table[name] = getattr(cls.get_lib(), name)
            return cls.method_table[name]
        else:
            return [cls.method(s) for s in name]
    @classmethod
    def submodule(cls, submodule:'str|list[str]'):
        check_load = cls.get_lib()
        if isinstance(submodule, str):
            return importlib.import_module(cls.module+"."+submodule)
        else:
            return [importlib.import_module(cls.module+"."+s) for s in submodule]
    @property
    def lib(self):
        return self.get_lib()
    def __getattr__(self, item):
        return self.method(item)