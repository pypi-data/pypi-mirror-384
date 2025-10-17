
import enum, numpy as np, collections

__all__ = [
    "FFIModule",
    "FFIMethod",
    "FFIArgument",
    "FFIType"
]

try: # guard clause
    np_float128 = np.float128
except AttributeError:
    np_float128 = np.longdouble # bad vibes but we'll see what happens

class FFIType(enum.Enum):
    """
    The set of supported enum types.
    Maps onto the native python convertable types and NumPy dtypes.
    In the future, this should be done more elegantly, but for now it suffices
    that these types align on the C++ side and this side.
    Only NumPy arrays are handled using the buffer interface & so if you want to pass a pointer
    you gotta do it using a NumPy array.
    """

    _type_map = {}

    GENERIC = -1

    Void = 1
    _type_map[Void] = ("void", None)

    # for k in type_map[NUMPY_Float64]: type_map[k] = NUMPY_Float64

    PY_TYPES=1000

    UnsignedChar = PY_TYPES + 10
    _type_map[UnsignedChar] = ("b", int)
    Short = PY_TYPES + 20
    _type_map[Short] = ("h", int)
    UnsignedShort = PY_TYPES + 21
    _type_map[UnsignedShort] = ("H", int)
    Int = PY_TYPES + 30
    _type_map[Int] = ("i", int)
    UnsignedInt = PY_TYPES + 31
    _type_map["I"] = UnsignedInt
    _type_map[UnsignedInt] = ("I", int)
    Long = PY_TYPES + 40
    _type_map[Long] = ("l", int)
    UnsignedLong = PY_TYPES + 41
    _type_map[UnsignedLong] = ("L", int)
    LongLong = PY_TYPES + 50
    _type_map["k"] = LongLong
    _type_map[LongLong] = ("k", int)
    UnsignedLongLong = PY_TYPES + 51
    _type_map["K"] = UnsignedLongLong
    _type_map[UnsignedLongLong] = ("K", int)
    PySizeT = PY_TYPES + 60
    _type_map[PySizeT] = ("n", int)

    Float = PY_TYPES + 70
    _type_map["f"] = Float
    _type_map[Float] = ("f", float)
    Double = PY_TYPES + 71
    _type_map["d"] = Double
    _type_map[Double] = ("d", float)

    Bool = PY_TYPES + 80
    _type_map[Bool] = ("p", bool)
    String = PY_TYPES + 90
    _type_map[String] = ("s", str)
    PyObject = PY_TYPES + 100
    _type_map["O"] = PyObject
    _type_map[PyObject] = ("O", object)

    Compound = PY_TYPES + 500
    _type_map[Compound] = ("compound", dict)

    # supports the NumPy NPY_TYPES enum
    # 200 is python space
    NUMPY_TYPES = 2000

    NUMPY_Int8 = NUMPY_TYPES + 10
    _type_map[NUMPY_Int8] = ("int8", np.int8)
    NUMPY_UnsignedInt8 = NUMPY_TYPES + 11
    _type_map[NUMPY_UnsignedInt8] = ("uint8", np.uint8)
    NUMPY_Int16 = NUMPY_TYPES + 12
    _type_map[NUMPY_Int16] = ("int16", np.int16)
    NUMPY_UnsignedInt16 = NUMPY_TYPES + 13
    _type_map[NUMPY_UnsignedInt16] = ("uint16", np.uint16)
    NUMPY_Int32 = NUMPY_TYPES + 14
    _type_map[NUMPY_Int32] = ("int32", np.int32)
    NUMPY_UnsignedInt32 = NUMPY_TYPES + 15
    _type_map[NUMPY_UnsignedInt32] = ("uint32", np.uint32)
    NUMPY_Int64 = NUMPY_TYPES + 16
    _type_map[NUMPY_Int64] = ("int64", np.int64)
    NUMPY_UnsignedInt64 = NUMPY_TYPES + 17
    _type_map[NUMPY_UnsignedInt64] = ("uint64", np.uint64)

    NUMPY_Float16 = NUMPY_TYPES + 20
    _type_map[NUMPY_Float16] = ("float16", np.float16)
    NUMPY_Float32 = NUMPY_TYPES + 21
    _type_map[NUMPY_Float32] = ("float32", np.float32)
    NUMPY_Float64 = NUMPY_TYPES + 22
    _type_map[NUMPY_Float64] = ("float64", np.float64)
    NUMPY_Float128 = NUMPY_TYPES + 23
    _type_map[NUMPY_Float128] = ("float128", np_float128)

    NUMPY_Bool = NUMPY_TYPES + 30
    _type_map[NUMPY_Bool] = ("bool", bool)

    @classmethod
    def type_data(cls, val):
        mapp = cls._type_map.value
        if isinstance(val, cls):
            val = val.value
        return mapp[val]

    _rev_map = {}
    @classmethod
    def resolve_ffi_type(cls, val):
        mapp = cls._rev_map.value
        if len(mapp) == 0: # initialize reverse map
            for k,v in cls._type_map.value.items():
                if isinstance(v, tuple):
                    for kk in v:
                        mapp[kk] = k
        return FFIType(mapp[val])

class FFIContainerType(enum.Enum):
    Untyped = 0
    Raw = 1
    Vector = 2
    Array = 3

class DebugLevels(enum.Enum):
    Quiet = 0
    Normal = 5
    More = 10
    All = 50
    Excessive = 100

class ThreadingMode(enum.Enum):
    Serial = 'serial'
    OpenMP = 'omp'
    TBB = 'tbb'


class FFISpec:
    """
    Provides a uniform layout for handling specs of different parts of an FFI library
    """
    __fields__ = []

    def __init__(self, **kwargs):
        for k in self.__fields__:
            if k not in kwargs or kwargs[k] is None:
                raise ValueError("{} got no value for required parameter {}".format(
                    type(self).__name__,
                    k
                ))
        for k in kwargs:
            if k not in self.__fields__:
                raise ValueError("{} got value for unexpected parameter {}".format(
                    type(self).__name__,
                    k
                ))
class FFIArgument(FFISpec):
    """
    An argument spec for data to be passed to an FFIMethod
    """
    __fields__ = ["name", "dtype", "shape", "container_type"]
    def __init__(self, name=None, dtype=None, shape=None, container_type=None, value=None):
        if shape is None:
            shape = ()
        if container_type is None:
            container_type = 'Untyped'
        super().__init__(name=name, dtype=dtype, shape=shape, container_type=container_type)
        self.arg_name = name
        self.arg_type = self.infer_dtype(dtype)
        self.arg_shape = shape
        self.container_type = self.infer_ctype(container_type)
    _base_dtype_map = {
        'int8':FFIType
    }
    @classmethod
    def infer_dtype(cls, dtype):
        if dtype is None:
            raise ValueError("can't infer dtype for value `None`")
        if isinstance(dtype, FFIType):
            return dtype
        elif isinstance(dtype, (int, np.integer)):
            return FFIType(dtype)
        elif isinstance(dtype, str):
            try:
                return FFIType[dtype]
            except KeyError:
                return FFIType.resolve_ffi_type(dtype)
        elif isinstance(dtype, np.dtype):
            return FFIType.resolve_ffi_type(dtype.name)
        else:
            return FFIType.resolve_ffi_type(dtype)
            # for type_val, pair in FFIType.type_map.value.items():
            #         if isinstance(pair, tuple) and pair[1] == dtype:
            #             return FFIType(type_val)
            # raise ValueError("can't infer FFIType for {}".format(dtype))
    @classmethod
    def infer_ctype(cls, container_type):
        if isinstance(container_type, FFIContainerType):
            return container_type
        elif isinstance(container_type, str):
            return FFIContainerType[container_type]
        else:
            return FFIContainerType(container_type)
    @classmethod
    def from_arg_sig(cls, arg):
        #arg is an ArgumentSignature.Argument but I need to do a more serious
        # refactor later so I won't import that module yet
        return cls(
            arg.name,
            arg.typechar,
            shape=None, # no shapes built into Argument at this point,
            container_type=FFIContainerType.Raw if (arg.is_pointer() or arg.is_array()) else None
        )
    def __repr__(self):
        return "{}('{}', {}, {}, {})".format(
            type(self).__name__,
            self.arg_name,
            self.arg_type,
            self.arg_shape,
            self.container_type,
        )
    def cast(self, val):
        """

        :param val:
        :type val:
        :return:
        :rtype:
        """

        type_str, dtype = FFIType.type_data(self.arg_type)
        if isinstance(dtype, np.dtype): # have a numpy type
            dat = np.asanyarray(val, dtype=dtype)
        elif len(self.arg_shape) > 0:
            dat = np.asanyarray(val, dtype=dtype)
        else:
            if isinstance(val, np.ndarray):
                dat = np.ascontiguousarray(val.astype(dtype))
            elif not isinstance(val, dtype):
                dat = dtype(val)
            else:
                dat = val

        # do some shape checks...
        return FFIParameter(self, dat)
class FFIParameter:
    """
    Just an FFIArgument + associated value
    """
    def __init__(self, arg, val):
        if not isinstance(arg, FFIArgument):
            raise TypeError("{}: arg is expected to be an FFIArgument")
        self.arg = arg
        self.val = val
    @property
    def arg_name(self):
        return self.arg.arg_name
    @property
    def arg_type(self):
        return self.arg.arg_type
    @property
    def arg_shape(self):
        argshp = self.arg.arg_shape
        if isinstance(self.val, np.ndarray) and (0 in argshp or len(argshp) == 0):
            argshp = self.val.shape # gotta be a numpy value
        return argshp
    @property
    def container_type(self):
        return self.arg.container_type
    @property
    def arg_value(self):
        if (
                len(self.arg_shape) > 0
                or
                self.container_type == FFIContainerType.Raw
                or
                self.container_type == FFIContainerType.Vector
        ) and not isinstance(self.val, np.ndarray):
            self.val = np.ascontiguousarray(np.array(self.val)) # to be able to treat as a pointer
            # raise Exception(self.val)
            # if val.shape == ():
            #     val = np.array([self.val])
            # self.val = val
        return self.val
    def __repr__(self):
        return "{}({}, {}, {})->{}".format(
            type(self).__name__,
            self.arg_name,
            self.arg_type,
            self.arg_shape,
            self.arg_value
        )

class FFIParameters:
    """

    """
    def __init__(self, dats):
        self.dats = dats
        self._params = None
        self._map = None
    def __iter__(self):
        return iter(self.ffi_parameters)
    @property
    def ffi_parameters(self):
        if self._params is None:
            if isinstance(self.dats, (dict, collections.OrderedDict)):
                dat = tuple(self.dats.values())
            else:
                dat = self.dats
            self._params = dat # trying to keep stuff from going out of scope?
        return self._params
    @property
    def ffi_map(self):
        if self._map is None:
            self._map = {}
            for p in self.ffi_parameters:
                self._map[p.arg_name] = p
        return self._map
    def __getitem__(self, item):
        return self.ffi_map[item].arg_value

class FFIMethod(FFISpec):
    """
    Represents a C++ method callable through the plzffi interface
    """
    __fields__ = ["name", "arguments", "rtype", "vectorized"]
    def __init__(self, name=None, arguments=None, rtype=None, vectorized=None, module=None):
        super().__init__(name=name, arguments=arguments, rtype=rtype, vectorized=vectorized)
        self.name = name
        self.args = [FFIArgument(**x) if not isinstance(x, FFIArgument) else x for x in arguments]
        self.rtype = FFIType(rtype)
        self.vectorized = vectorized
        self.mod = module #type: None | FFIModule
    def bind_module(self, mod):
        self.mod = mod #type: FFIModule

    @property
    def arg_names(self):
        return tuple(x.arg_name for x in self.args)

    @classmethod
    def collect_args_from_list(cls, arg_list, *args, excluded_args=None, **kwargs):
        arg_dict = collections.OrderedDict()

        req_dict = collections.OrderedDict(
            (k.arg_name, k)
            for k in arg_list
        )

        for k in kwargs:
            arg_dict[k] = req_dict[k].cast(kwargs[k])
            del req_dict[k]

        if excluded_args is not None:
            for k in excluded_args:
                if k in req_dict:
                    del req_dict[k]

        if len(req_dict) > 0:
            for v, k in zip(args, req_dict.copy()):
                arg_dict[k] = req_dict[k].cast(v)
                del req_dict[k]

        if len(req_dict) > 0:
            raise ValueError("{}.{}: missing required arguments {}".format(
                cls.__name__,
                'collect_args',
                tuple(req_dict.values())
            ))
        return arg_dict

    def collect_args(self, *args, excluded_args=None, **kwargs):
        return self.collect_args_from_list(self.args, *args, excluded_args=excluded_args, **kwargs)

    @classmethod
    def from_signature(cls, sig, module=None):
        name, args, ret, vec = sig
        return cls(
            name=name,
            arguments=[{k:v for k,v in zip(FFIArgument.__fields__, x)} for x in args],
            rtype=ret,
            vectorized=vec,
            module=module
        )

    def call(self, *args, debug=False, **kwargs):
        fack = self.collect_args(*args, **kwargs)
        return self.mod.call_method(self.name, fack, debug=debug)
    def call_threaded(self, *args, threading_var=None, threading_mode="serial", debug=False, **kwargs):
        fack = self.collect_args(*args, **kwargs)
        return self.mod.call_method_threaded(self.name, fack, threading_var, mode=threading_mode, debug=debug)
    def __call__(self, *args, threading_var=None, threading_mode="serial", debug=False, **kwargs):
        fack = self.collect_args(*args, **kwargs)
        if threading_var is None and (threading_mode is None or threading_mode=='serial'):
            return self.mod.call_method(self.name, fack, debug=debug)
        else:
            return self.mod.call_method_threaded(self.name, fack, threading_var, mode=threading_mode, debug=debug)

    def __repr__(self):
        return "{}('{}', {})=>{}".format(
            type(self).__name__,
            self.name,
            self.args,
            "array({})".format(self.rtype) if self.vectorized else self.rtype
        )

class FFIModule(FFISpec):
    """
    Provides a layer to ingest a Python module containing an '_FFIModule' capsule.
    The capsule is expected to point to a `plzffi::FFIModule` object and can be called using a `PotentialCaller`
    """
    __fields__ = ["name", "methods"]
    def __init__(self, name=None, methods=None, module=None):
        super().__init__(name=name, methods=methods)
        self.name = name
        self.methods = [FFIMethod(**x) if not isinstance(x, FFIMethod) else x for x in methods]
        for m in self.methods:
            m.bind_module(self)
        self.mod = module

    @property
    def captup(self):
        return self.mod._FFIModule

    @classmethod
    def from_lib(cls, name,
                 src=None,
                 threaded=None,
                 extra_compile_args=None,
                 extra_link_args=None,
                 linked_libs=None,
                 **compile_kwargs
                 ):
        from .Loader import FFILoader
        if threaded is not None: # use the default
            compile_kwargs['threaded'] = threaded
        return FFILoader(name,
                         src=src,
                         extra_compile_args=extra_compile_args,
                         extra_link_args=extra_link_args,
                         linked_libs=linked_libs,
                         **compile_kwargs
                         ).call_obj

    @classmethod
    def from_signature(cls, sig, module=None):
        name, meths = sig
        return cls(
            name=name,
            methods=[FFIMethod.from_signature(x) for x in meths],
            module=module
        )
    @classmethod
    def get_debug_level(cls, debug):
        if debug is False:
            debug = DebugLevels.Quiet
        elif debug is True:
            debug = DebugLevels.Normal
        elif isinstance(debug, str):
            debug = DebugLevels[debug.lower().capitalize()]
        elif not isinstance(debug, (int, float, np.integer, np.floating)):
            debug = DebugLevels(debug)
        if isinstance(debug, DebugLevels):
            debug = debug.value
        return debug
    @classmethod
    def from_module(cls, module, debug=False):
        sig = module.get_signature(module._FFIModule, cls.get_debug_level(debug))
        return cls.from_signature(sig, module=module)

    @property
    def method_names(self):
        return tuple(x.name for x in self.methods)

    def get_method(self, name):
        # print(self.method_names)
        try:
            idx = self.method_names.index(name)
        except (ValueError, IndexError):
            idx = None
        if idx is not None:
            return self.methods[idx]
        else:
            raise AttributeError("FFIModule {} has no method {}".format(self.name, name))

    def call_method(self, name, params, debug=False):
        """
        Calls a method

        :param name:
        :type name:
        :param params:
        :type params:
        :return:
        :rtype:
        """
        req_attrs = ("arg_type", "arg_name", "arg_shape", "arg_value")
        if isinstance(params, (dict, collections.OrderedDict)):
            params = FFIParameters(params)
        for p in params:
            if not all(hasattr(p, x) for x in req_attrs):
                raise AttributeError("parameter {} needs attributes {}".format(p, req_attrs))
        return self.mod.call_method(self.captup, name, params, self.get_debug_level(debug))
    def call_method_threaded(self, name, params, thread_var, mode="serial", debug=False):
        """
        Calls a method with threading enabled

        :param name:
        :type name:
        :param params:
        :type params:
        :param thread_var:
        :type thread_var: str
        :param mode:
        :type mode:
        :return:
        :rtype:
        """
        req_attrs = ("arg_type", "arg_name", "arg_shape", "arg_value")
        if isinstance(params, (dict, collections.OrderedDict)):
            params = FFIParameters(params)
        for p in params:
            if not all(hasattr(p, x) for x in req_attrs):
                raise AttributeError("parameter needs attributes {}", req_attrs)
        if not isinstance(mode, ThreadingMode):
            mode = ThreadingMode(mode)
        mode = mode.name
        return self.mod.call_method_threaded(self.captup, name, params, thread_var, mode, self.get_debug_level(debug))

    def __getattr__(self, item):
        return self.get_method(item)

    def __repr__(self):
        return "{}('{}', methods={})".format(
            type(self).__name__,
            self.name,
            self.method_names
        )