import abc, weakref
import enum
from collections import OrderedDict
from .. import Devutils as dev

__all__ = [
    "Cache",
    "MaxSizeCache",
    "ObjectRegistry"
]

class Cache(metaclass=abc.ABCMeta):
    """
    Simple cache base class
    """
    @abc.abstractmethod
    def __getitem__(self, item):
        raise NotImplementedError("Cache is an abstract base class")
    def get(self, item, default=None):
        try:
            return self.__getitem__(item)
        except KeyError:
            return default
    @abc.abstractmethod
    def __contains__(self, item):
        raise NotImplementedError("Cache is an abstract base class")
    @abc.abstractmethod
    def __setitem__(self, key, value):
        raise NotImplementedError("Cache is an abstract base class")

class MaxSizeBackend(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def keys(self):
        cls = type(self)
        raise NotImplementedError(f"{cls.__name__} is an abstract base class")
    @abc.abstractmethod
    def __len__(self):
        cls = type(self)
        raise NotImplementedError(f"{cls.__name__} is an abstract base class")
    @abc.abstractmethod
    def __getitem__(self, item):
        cls = type(self)
        raise NotImplementedError(f"{cls.__name__} is an abstract base class")
    @abc.abstractmethod
    def __contains__(self, item):
        cls = type(self)
        raise NotImplementedError(f"{cls.__name__} is an abstract base class")
    @abc.abstractmethod
    def __setitem__(self, key, value):
        cls = type(self)
        raise NotImplementedError(f"{cls.__name__} is an abstract base class")
    @abc.abstractmethod
    def pop(self):
        cls = type(self)
        raise NotImplementedError(f"{cls.__name__} is an abstract base class")

class LRUDict(MaxSizeBackend):
    def __init__(self):
        self.od = OrderedDict()
    def __len__(self):
        return len(self.od)
    def keys(self):
        return self.od.keys()
    def __contains__(self, item):
        return item in self.od
    def __getitem__(self, item):
        val = self.od[item]
        self.od.move_to_end(item)
        return val
    def __setitem__(self, key, value):
        self.od[key] = value
        self.od.move_to_end(key)
    def pop(self):
        return self.od.popitem(last=False)

class FIFODict(MaxSizeBackend):
    def __init__(self):
        self.od = {}
    def __len__(self):
        return len(self.od)
    def keys(self):
        return self.od.keys()
    def __contains__(self, item):
        return item in self.od
    def __getitem__(self, item):
        val = self.od[item]
        return val
    def __setitem__(self, key, value):
        self.od[key] = value
    def pop(self):
        return self.od.pop(next(iter(self.od.keys())))

class MaxSizeCache(Cache):
    """
    Simple lru-cache to support ravel/unravel ops
    """
    def __init__(self, max_items=128, cache_type=None):
        self.backend = self.resolve_cache_type(cache_type)
        self.max_items = max_items
    class Backends(enum.Enum):
        LRU = "lru"
        FIFO = "fifo"
    cache_types = dev.OptionsMethodDispatch(
        {
            Backends.LRU:LRUDict,
            Backends.FIFO:FIFODict,
        },
        methods_enum=Backends,
        default_method=Backends.LRU
    )
    @classmethod
    def resolve_cache_type(cls, type_name):
        if callable(type_name):
            method = type_name
            opts = {}
        else:
            method, opts = cls.cache_types.resolve(type_name)
        return method(**opts)

    def keys(self):
        return self.backend.keys()
    def __contains__(self, item):
        return item in self.backend
    def __getitem__(self, item):
        return self.backend.__getitem__(item)
    def __setitem__(self, key, value):
        self.backend.__setitem__(key, value)
        if len(self.backend) > self.max_items:
            self.backend.pop()

class ObjectRegistryDefaults:
    Raise="raise"
    NotFound="NotFound"

class RegistryDefaultContext:
    def __init__(self, registry:'ObjectRegistry', value):
        self.reg = registry
        self.old = None
        self.val = value
    def __enter__(self):
        self.old = self.reg.default
        self.reg.default = self.val
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reg.default = self.old

class ObjectRegistry:
    """
    Provides a simple interface to global object registries
    so that pieces of code don't need to pass things like loggers
    or parallelizers through every step of the code
    """

    def __init__(self, default=ObjectRegistryDefaults.Raise):
        self.cache = weakref.WeakValueDictionary() # allow unused vals to get gc'd
        self.default = default

    def temp_default(self, val):
        return RegistryDefaultContext(self, val)

    def __contains__(self, item):
        return self.cache.__contains__(item)

    def lookup(self, key):
        if self.default is ObjectRegistryDefaults.Raise:
            return self.cache[key]
        else:
            try:
                return self.cache[key]
            except KeyError:
                return self.default
    def __getitem__(self, item):
        return self.lookup(item)

    def register(self, key, val):
        self.cache[key] = val
    def __setitem__(self, key, value):
        self.register(key, value)

    def keys(self):
        return self.cache.keys()
    def items(self):
        return self.cache.items()
    def values(self):
        return self.cache.values()