import os, collections
from ..SharedLibraryManager import SharedLibrary, SharedLibraryFunction
from .Module import FFIModule, FFIMethod, FFIArgument, FFIParameters, ThreadingMode

__all__ = [
    "DynamicFFIFunctionLoader",
    "DynamicFFIFunction",
    "DynamicFFILibrary"
]

class DynamicFFIFunctionLoader:
    """
    This is a singleton class that can be set to define the global
    linkage to the DynamicLibrary extension module
    """
    _loader=None
    _compile_args={}
    _lib_dir=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'libs', 'DynamicFFILibrary')
    @classmethod
    def configure(cls, **compile_args):
        cls._compile_args.update(compile_args)
    @classmethod
    def load(cls):
        if cls._loader is None:
            cls._loader = FFIModule.from_lib(
                cls._lib_dir,
                **cls._compile_args
                # threaded=True,
                # extra_compile_args=(['-ftime-report'] if opts.time_report else []) + (
                #     ['-O0'] if opts.cmode == 'fast' else []),
                # include_dirs=['/usr/local/opt/llvm/include'],
                # runtime_dirs=['/usr/local/opt/llvm/lib', '/usr/local/opt/llvm/lib/c++'],
                # extra_link_args=['-mmacosx-version-min=12.0'],
                # recompile=opts.recompile
            )
        return cls._loader

class DynamicFFIFunction(SharedLibraryFunction):
    """
    Specialization of base `SharedLibraryFunction` to call
    through the `DynamicLibrary` module instead of `ctypes`
    """
    _caller = None
    @classmethod
    def _load_lib(cls):
        if cls._caller is None:
            cls._caller = DynamicFFIFunctionLoader.load()
        return cls._caller

    def __init__(self,
                 shared_library,
                 signature,
                 defaults=None,
                 docstring=None,
                 call_directory=None,
                 return_handler=None,
                 prep_args=None
                 ):
        super().__init__(shared_library, signature,
                         defaults=defaults, docstring=docstring,
                         call_directory=call_directory, return_handler=return_handler,
                         prep_args=prep_args
                         )
        self._ffi_args = None
        self._func_data = None
        self._call_info = []

    def initialize(self):
        # super().initialize()
        self._load_lib()
        if self._ffi_args is None:
            self._ffi_args = [
                FFIArgument.from_arg_sig(a) for a
                in self._sig.args
            ]

    class LibFFIMethodData:
        def __init__(self, lib, name, return_type, args, vectorized=False):
            self.library = lib
            self.name = name
            self.return_type = return_type
            self.args = args
            self.vectorized = vectorized
    @property
    def function_data(self):
        if self._func_data is None:
            self.initialize()
            self._func_data = self.LibFFIMethodData(
                self._loader.lib,
                self._sig.name,
                FFIArgument.infer_dtype(self.signature.return_argtype.typechar),
                self._ffi_args
            )
        return self._func_data

    def _call(self, args, kwargs):
        fdat = self.function_data # needs to be calculated here...
        if args is not None: # easy way to say no prep needed...
            kwargs = self._sig.populate_kwargs(args, kwargs, defaults=self.defaults) # populate args from ...
        params = FFIMethod.collect_args_from_list(self._ffi_args, **kwargs)
        req_attrs = ("arg_type", "arg_name", "arg_shape", "arg_value")
        if isinstance(params, (dict, collections.OrderedDict)):
            params = FFIParameters(params)
        for p in params:
            if not all(hasattr(p, x) for x in req_attrs):
                raise AttributeError("parameter {} needs attributes {}".format(p, req_attrs))
        callinfo = self._call_info.pop()
        debug = callinfo['debug']
        threading_vars = callinfo['threading_vars']
        threading_mode = callinfo['threading_mode']
        if threading_vars is not None:
            if isinstance(threading_vars, str):
                threading_vars = [threading_vars]
            if threading_mode is None:
                threading_mode = 'serial'
            if not isinstance(threading_mode, ThreadingMode):
                threading_mode = ThreadingMode(threading_mode)
            threading_mode = threading_mode.name
            res = self._caller.call_libffi_threaded.call(
                function_data=fdat, parameters=params,
                threading_vars=threading_vars, threading_mode=threading_mode, debug=debug
            )
        else:
            res = self._caller.call_libffi.call(function_data=fdat, parameters=params, debug=debug)
        return res, params

    def __call__(self, *args, debug=False, threading_vars=None, threading_mode=None, **kwargs):
        # kinda hacky...
        self._call_info.append({
            'debug':debug,
            'threading_vars':threading_vars,
            'threading_mode':threading_mode
        })
        return super().call(*args, **kwargs)

class DynamicFFILibrary(SharedLibrary):
    """
    Directly analogous to a regular shared library but it uses
    `DynamicFFIFunction` to dispatch calls
    """
    method_type = DynamicFFIFunction

    def __init__(
            self,
            library,
            compiler_options=None,
            **functions
    ):
        super().__init__(library, **functions)
        self._loaded = False
        self.compiler_opts = compiler_options

    def get_function(self, item):
        if not self._loaded and self.compiler_opts is not None:
            self.configure_loader(**self.compiler_opts)
        self._loaded = True
        return super().get_function(item)

    @classmethod
    def configure_loader(cls, **compile_opts):
        DynamicFFIFunctionLoader.configure(**compile_opts)