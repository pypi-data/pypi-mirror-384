"""
Defines a SharedLibrary object that makes it relatively straightforward to use
extensions direclty from .so files
"""

import os, ctypes
from .ArgumentSignature import FunctionSignature, Argument

__all__ = [
    "SharedLibrary",
    "SharedLibraryFunction"
]

class SharedLibraryLoader:

    def __init__(self, shared_library):
        if not isinstance(shared_library, str):
            lib_file = shared_library._name # I'd prefer not to access private members but my options were limited
            if not os.path.isfile(lib_file):
                lib_file = None
        else:
            lib_file = shared_library
            shared_library = None
        self._lib = shared_library
        self._lib_file = lib_file

    class InDir:
        """
        A super simple context manager that manages going into a directory and then leaving when finished
        """

        def __init__(self, dir_name):
            self._to = dir_name
            self._from = None

        def __enter__(self):
            self._from = os.getcwd()
            os.chdir(self._to)

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self._from is not None:
                os.chdir(self._from)
            self._from = None

    def in_dir(self):
        return self.InDir(self.lib_dir)

    @property
    def lib(self):
        if self._lib is None:
            with self.in_dir():
                self._lib = ctypes.cdll.LoadLibrary(self._lib_file)
        return self._lib

    @property
    def lib_dir(self):
        return os.path.dirname(self._lib_file)

class SharedLibraryFunction:
    """
    An object that provides a way to call into a shared library function
    """

    def __init__(self,
                 shared_library,
                 signature:FunctionSignature,
                 defaults=None,
                 docstring=None,
                 call_directory=None,
                 return_handler=None,
                 prep_args=None
                 ):
        """
        :param shared_library: the path to the shared library file you want to use
        :type shared_library: str |
        :param function_signature: the signature of the function to load
        :type function_signature: FunctionSignature
        :param call_directory: the directory for calling
        :type call_directory: str
        :param docstring: the docstring for the function
        :type docstring: str
        """
        if not isinstance(shared_library, SharedLibraryLoader):
            shared_library = SharedLibraryLoader(shared_library)
        self._loader = shared_library
        self._fun = None
        self._fname = None
        self._sig = signature
        self._doc = docstring
        # if call_directory is None:
        #     call_directory = self._loader.lib_dir
        self._dir = call_directory  # we could be kinder here and do stuff like add support for ".." and friends
        self.defaults = defaults
        if return_handler is None:
            return_handler = self._manage_return
        self.return_handler = return_handler
        self.arg_prepper = prep_args

    @classmethod
    def construct(cls,
                  name,
                  lib,
                  docstring=None,
                  defaults=None,
                  return_type=None,
                  return_handler=None,
                  **args
                  ):

        return cls(
            lib,
            FunctionSignature.construct(
                name
                **args,
                return_type=return_type
            ),
            docstring=docstring,
            defaults=defaults,
            return_handler=return_handler
        )

    @property
    def function(self):
        self.initialize()
        return self._fun
    def initialize(self):
        if self._fun is None:
            # means we need to load it from the shared lib
            if self._fname is None:
                self._fname = self._sig.name
            self._fun = getattr(self._loader.lib, self._fname)

            # now initialize the arg signature
            self._fun.restype = self._sig.return_type
            self._fun.argtypes = self._sig.arg_types # need to figure out what type I need...
    def doc(self):
        return self._sig.cpp_signature+"\n"+self._doc
    def __repr__(self):
        return "{}({}, {})".format(
            type(self).__name__,
            self._sig,
            self._loader.lib
        )

    @property
    def signature(self):
        return self._sig

    @classmethod
    def _manage_return(cls, res, args):
        return cls.uncast(res)
    @classmethod
    def uncast(cls, res):
        if hasattr(res, '_obj'): #byref
            res = res._obj
        if hasattr(res, 'value'):
            res = res.value
        return res

    def _call(self, args, kwargs): # here to be overloaded
        args = self._sig.prep_args(args, kwargs, defaults=self.defaults)
        if self._dir is not None:
            with SharedLibraryLoader.InDir(self._dir):
                res = self.function(*args)
        else:
            res = self.function(*args)
        args = dict(zip((a.name for a in self._sig.args), args))
        return res, args

    def call(self, *args, **kwargs):
        """
        Calls the function we loaded.
        This will be parallelized out to handle more complicated usages.

        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """

        if self.arg_prepper is not None:
            kwargs = self._sig.populate_kwargs(args, kwargs,  defaults=self.defaults)
            args = None
            kwargs = self.arg_prepper(kwargs)
        res, args = self._call(args, kwargs)
        return self.return_handler(res, args)

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

class SharedLibrary:

    method_type = SharedLibraryFunction
    def __init__(
            self,
            library,
            **functions
    ):
        if not isinstance(library, SharedLibraryLoader):
            library = SharedLibraryLoader(library)
        self._loader = library
        self._functions = {}
        for k,v in functions.items():
            self.register(k, **v)
    def register(self, tag, name=None, docstring=None, defaults=None, return_handler=None, prep_args=None, **params):
        if name is None:
            name = tag
        fn = self.method_type(
            self._loader,
            FunctionSignature.construct(name, **params),
            docstring=docstring,
            defaults=defaults,
            return_handler=return_handler,
            prep_args=prep_args
        )
        self._functions[tag] = fn
        return fn

    def get_function(self, item):
        if item in self._functions:
            return self._functions[item]
        else:
            raise ValueError("no shared library function {}".format(item))

    def __getattr__(self, item):
        return self.get_function(item)

    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            ", ".format(repr(fn.sig) for fn in self._functions)
        )