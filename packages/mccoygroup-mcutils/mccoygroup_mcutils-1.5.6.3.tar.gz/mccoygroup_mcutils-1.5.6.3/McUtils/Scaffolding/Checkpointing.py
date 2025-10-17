
import abc, os
from .. import Devutils as dev
from .Serializers import *

__all__ = [
    "Checkpointer",
    "CheckpointerKeyError",
    "DumpCheckpointer",
    "JSONCheckpointer",
    "NumPyCheckpointer",
    "HDF5Checkpointer",
    "DictCheckpointer",
    "NullCheckpointer"
]

class CheckpointerKeyError(KeyError):
    ...

class Checkpointer(metaclass=abc.ABCMeta):
    """
    General purpose base class that allows checkpointing to be done easily and cleanly.
    Intended to be a passable object that allows code to checkpoint easily.
    """

    default_extension=""
    def __init__(self, checkpoint_file,
                 allowed_keys=None,
                 omitted_keys=None
                 ):
        self.checkpoint_file = checkpoint_file
        self.allowed_keys = allowed_keys
        self.omitted_keys = omitted_keys
        self._came_open = not isinstance(checkpoint_file, str)
        self._open_depth = 0
        self._stream = None
    def __repr__(self):
        return "{}({!r})".format(type(self).__name__, self.checkpoint_file)

    _ext_map = None
    @classmethod
    def extension_map(cls):
        if cls._ext_map is not None:
            return cls._ext_map
        else:
            return {c.default_extension:c for c in [JSONCheckpointer, HDF5Checkpointer, NumPyCheckpointer]}

    @classmethod
    def build_canonical(cls, checkpoint):
        """
        Dispatches over types of objects to make a canonical checkpointer
        from the supplied data

        :param checkpoint: provides
        :type checkpoint: None | str | Checkpoint | file | dict
        :return:
        :rtype: Checkpointer
        """

        if checkpoint is None:
            return NullCheckpointer(None)
        elif isinstance(checkpoint, str):
            return Checkpointer.from_file(checkpoint)
        elif isinstance(checkpoint, Checkpointer):
            return checkpoint
        elif dev.is_dict_like(checkpoint):
            if dev.Schema(["file"]).validate(checkpoint, throw=False):
                checkpoint = dev.Schema(["file"], ['keys', 'opts']).to_dict(checkpoint)
                opts = checkpoint['opts'] if 'opts' in checkpoint else {}
                if 'keys' in checkpoint:
                    allowed_opts = dev.Schema(['allowed_keys'], ['omitted_keys']).to_dict(checkpoint['keys'], throw=False)
                    if allowed_opts is not None:
                        opts = dict(opts, **allowed_opts)
                    else:
                        omitted_opts = dev.Schema(['omitted_keys']).to_dict(checkpoint['keys'], throw=False)
                        if allowed_opts is not None:
                            opts = dict(opts, **omitted_opts)
                        else:
                            opts['allowed_keys'] = checkpoint['keys']
                return cls.from_file(checkpoint['file'], **opts)
            else:
                return DictCheckpointer(checkpoint)
        else:
            return checkpoint

    @classmethod
    def from_file(cls, file, **opts):
        """
        Dispatch function to load from the appropriate file
        :param file:
        :type file: str | File
        :param opts:
        :type opts:
        :return:
        :rtype:
        """

        if not isinstance(file, str):
            #TODO: make this cleaner
            file_name = file.name # might break in the future...
        else:
            file_name = file

        _, ext = os.path.splitext(file_name)

        ext_map = cls.extension_map()

        if ext not in ext_map:
            raise ValueError("don't know have default checkpointer type registered for extension {}".format(ext))

        return ext_map[ext](file, **opts)

    def __enter__(self):
        self._open_depth+=1
        if self._stream is None:
            self._stream = self.open_checkpoint_file(self.checkpoint_file)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._open_depth-=1
        if self._stream is not None:
            if self._open_depth == 0:
                self.close_checkpoint_file(self._stream)
                self._stream = None

    def cached_eval(self, key, generator, *,
                    condition=None,
                    args=(),
                    kwargs=None):
        return dev.cached_eval(
            self,
            key,
            generator,
            condition=condition,
            args=args,
            kwargs=kwargs
        )

    @property
    def is_open(self):
        return self._stream is not None

    @property
    def stream(self):
        return self._stream

    @abc.abstractmethod
    def open_checkpoint_file(self, chk):
        """
        Opens the passed `checkpoint_file` (if not already open)
        :param chk:
        :type chk:
        :return:
        :rtype:
        """
        raise NotImplementedError("CheckpointerBase is an abstract base class...")
    @abc.abstractmethod
    def close_checkpoint_file(self, stream):
        """
        Closes the opened checkpointing stream
        :param stream:
        :type stream:
        :return:
        :rtype:
        """
        raise NotImplementedError("CheckpointerBase is an abstract base class...")
    @abc.abstractmethod
    def save_parameter(self, key, value):
        """
        Saves a parameter to the checkpoint file
        :param key:
        :type key:
        :param value:
        :type value:
        :return:
        :rtype:
        """
        raise NotImplementedError("CheckpointerBase is an abstract base class...")
    @abc.abstractmethod
    def load_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        raise NotImplementedError("CheckpointerBase is an abstract base class...")

    def delete_parameter(self, key):
        raise NotImplementedError("checkpointer does not need to implement deletion")
    def check_parameter(self, key):
        try:
            self.check_allowed_key(key)
            self.__getitem__(key)
        except KeyError:
            return False
        else:
            return True

    def update(self, vals):
        if dev.is_dict_like(vals):
            return self.update(vals.items())

        if not self.is_open:
            with self:
                return self.update(vals)

        for k, v in vals:
            self[k] = v
    def get_keys(self, keys):
        if not self.is_open:
            with self:
                return self.get_keys(keys)

        return [
            self[k] for k in keys
        ]

    def check_allowed_key(self, item):
        if isinstance(item, tuple):
            # for subkey in item:
            self.check_allowed_key(item[0]) # only check topline items
        else:
            if self.allowed_keys is not None:
                if item not in self.allowed_keys:
                    raise CheckpointerKeyError("key {} not allowed by {}".format(
                        item,
                        self
                    ))
            if self.omitted_keys is not None:
                if item in self.omitted_keys:
                    raise CheckpointerKeyError("key {} not allowed by {}".format(
                        item,
                        self
                    ))

    def __contains__(self, key):
        if not self.is_open:
            with self:
                return self.__contains__(key)
        return self.check_parameter(key)

    def __getitem__(self, item):
        if not self.is_open:
            with self:
                return self.__getitem__(item)
        self.check_allowed_key(item)
        return self.load_parameter(item)
    def get(self, key, default=None):
        try:
            val = self[key]
        except KeyError:
            val = default
        return val
    def __setitem__(self, key, value):
        if not self.is_open:
            with self:
                return self.__setitem__(key, value)
        self.check_allowed_key(key)
        self.save_parameter(key, value)

    def __delitem__(self, key):
        if not self.is_open:
            with self:
                return self.__delitem__(key)
        self.check_allowed_key(key)
        self.delete_parameter(key)
    def pop(self, key, *default):
        if len(default) > 0:
            try:
                val = self[key]
            except KeyError:
                val = default[0]
            else:
                del self[key]
        else:
            val = self[key]
            del self[key]
        return val

    @abc.abstractmethod
    def keys(self):
        """
        Returns the keys of currently checkpointed
        objects

        :return:
        :rtype:
        """
        raise NotImplementedError("Checkpointer is an abstract base class...")

class DumpCheckpointer(Checkpointer):
    """
    A subclass of `CheckpointerBase` that writes an entire dump to file at once & maintains
    a backend cache to update it cleanly
    """
    def __init__(self, file, cache=None, open_kwargs=None,
                 allowed_keys=None,
                 omitted_keys=None
                 ):
        self.backend = cache # cache values
        super().__init__(file, allowed_keys=allowed_keys, omitted_keys=omitted_keys)
        if open_kwargs is None:
            open_kwargs = {'mode':"w+"}
        self.open_kwargs = open_kwargs
    def load_cache(self):
        if self.backend is None:
            self.backend = {}
    def __enter__(self):
        self.load_cache()
        return super().__enter__()
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.dump()
        finally:
            super().__exit__(exc_type, exc_val, exc_tb)
    @abc.abstractmethod
    def dump(self):
        """
        Writes the entire data structure
        :return:
        :rtype:
        """
        raise NotImplementedError("DumpCheckpointer is an ABC and doesn't know how to write to file")
    def convert(self):
        """
        Converts the cache to an exportable form if needed
        :return:
        :rtype:
        """
        return self.backend
    def open_checkpoint_file(self, chk):
        """
        Opens the passed `checkpoint_file` (if not already open)
        :param chk:
        :type chk:
        :return:
        :rtype:
        """
        if isinstance(chk, str):
            chk = open(chk, **self.open_kwargs)
        return chk
    def close_checkpoint_file(self, stream):
        """
        Closes the opened checkpointing stream
        :param stream:
        :type stream:
        :return:
        :rtype:
        """
        if not self._came_open:
            stream.close()
    def save_parameter(self, key, value):
        """
        Saves a parameter to the checkpoint file
        :param key:
        :type key:
        :param value:
        :type value:
        :return:
        :rtype:
        """
        if isinstance(key, tuple):
            base = self.backend
            cur = key[0]
            for subk in key[1:]:
                if cur not in base: base[cur] = {}
                base = base[cur]
                cur = subk
            base[cur] = value
        else:
            self.backend[key] = value
    def check_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        if isinstance(key, tuple):
            base = self.backend
            cur = key[0]
            for subk in key[1:]:
                if cur not in base: return False
                base = base[cur]
                cur = subk
            return cur in base
        else:
            return key in self.backend
    def load_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        if isinstance(key, tuple):
            base = self.backend
            cur = key[0]
            for subk in key[1:]:
                if cur not in base:
                    raise KeyError(f"{key} not found")
                base = base[cur]
                cur = subk
            val = base[cur]
        else:
            val = self.backend[key]
        return val
    def delete_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        if isinstance(key, tuple):
            base = self.backend
            cur = key[0]
            for subk in key[1:]:
                if cur not in base:
                    raise KeyError(f"{key} not found")
                base = base[cur]
                cur = subk
            del base[cur]
        else:
            del self.backend[key]

    def keys(self):
        if not self.is_open:
            with self:
                return self.keys()
        return self.backend.keys()

class JSONCheckpointer(DumpCheckpointer):
    """
    A checkpointer that uses JSON as a backend
    """

    default_extension=JSONSerializer.default_extension
    def __init__(self, file, cache=None, serializer=None, open_kwargs=None,
                 allowed_keys=None,
                 omitted_keys=None
                 ):
        if serializer is None:
            serializer = JSONSerializer()
        self.serializer = serializer
        super().__init__(file, cache=cache, open_kwargs=open_kwargs, allowed_keys=allowed_keys, omitted_keys=omitted_keys)

    def load_cache(self):
        cache = self.backend
        if cache is None:
            file = self.checkpoint_file
            serializer = self.serializer
            if isinstance(file, str) and os.path.exists(file) and os.stat(file).st_size > 0:
                with open(file, 'r') as stream:
                    cache = serializer.deserialize(stream)
                if not isinstance(cache, dict):
                    cache = {}
            else:
                cache = {}
            self.backend = cache

    def dump(self):
        """
        Writes the entire data structure
        :return:
        :rtype:
        """
        self.serializer.serialize(self.stream, self.backend)

class NumPyCheckpointer(DumpCheckpointer):
    """
    A checkpointer that uses NumPy as a backend
    """

    default_extension = NumPySerializer.default_extension
    def __init__(self, file, cache=None, serializer=None, open_kwargs=None,
                 allowed_keys=None,
                 omitted_keys=None
                 ):
        if isinstance(file, str):
            if not os.path.exists(file):
                if os.path.exists(file + '.npz'):
                    file = file + '.npz'
                elif os.path.exists(file + '.npy'):
                    file = file + '.npy'

        if serializer is None:
            serializer = NumPySerializer()
        self.serializer = serializer
        if open_kwargs is None:
            open_kwargs = {'mode':'bw'}
        super().__init__(file, cache=cache, open_kwargs=open_kwargs,
                         allowed_keys=allowed_keys,
                         omitted_keys=omitted_keys
                         )

    def load_cache(self):
        cache = self.backend
        if cache is None:
            file = self.checkpoint_file
            serializer = self.serializer
            if isinstance(file, str) and os.path.exists(file) and os.stat(file).st_size > 0:
                with open(file, 'br') as stream:
                    cache = serializer.deserialize(stream)
                if not isinstance(cache, dict):
                    cache = {}
            else:
                cache = {}
            self.backend = cache

    def dump(self):
        """
        Writes the entire data structure
        :return:
        :rtype:
        """
        self.serializer.serialize(self.stream, self.backend)

class HDF5Checkpointer(Checkpointer):
    """
    A checkpointer that uses an HDF5 file as a backend.
    Doesn't maintain a secondary `dict`, because HDF5 is an updatable format.
    """

    default_extension = HDF5Serializer.default_extension
    def __init__(self, checkpoint_file, serializer=None,
                 allowed_keys=None,
                 omitted_keys=None
                 ):
        super().__init__(checkpoint_file, allowed_keys=allowed_keys, omitted_keys=omitted_keys)
        if serializer is None:
            serializer = HDF5Serializer()
        self.serializer = serializer

    def open_checkpoint_file(self, chk):
        """
        Opens the passed `checkpoint_file` (if not already open)
        :param chk:
        :type chk: str | file-like
        :return:
        :rtype:
        """
        if not self._came_open:
            try:
                if os.path.exists(chk):
                    return open(chk, 'r+b')
                else:
                    return open(chk, "w+b")
            except ValueError as e:
                if e.args[0] == 'seek of closed file':
                    raise IOError("existing HDF5 file {} is corrupted and can't be opened".format(chk))
                else:
                    raise
        elif 'b' not in chk.mode:
            raise IOError("{} isn't opened in binary mode (HDF5 needs that)".format(chk))
        else:
            return chk

    def close_checkpoint_file(self, stream):
        """
        Opens the passed `checkpoint_file` (if not already open)
        :param chk:
        :type chk:
        :return:
        :rtype:
        """
        if not self._came_open:
            self.stream.close()

    def save_parameter(self, key, value):
        """
        Saves a parameter to the checkpoint file
        :param key:
        :type key:
        :param value:
        :type value:
        :return:
        :rtype:
        """
        # HDF5 serialization is an updateable process
        if self.stream is None:
            raise IOError("stream for {} got closed and won't reopen".format(self.checkpoint_file))
        self.serializer.serialize(self.stream, {key:value})

    def load_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        return self.serializer.deserialize(self.stream, key=key)

    def keys(self):
        if not self.is_open:
            with self:
                return self.keys()
        file = self.stream
        if not isinstance(file, (self.serializer.api.File, self.serializer.api.Group)):
            file = self.serializer.api.File(file, "a")
        return list(file.keys())

class DictCheckpointer(Checkpointer):
    """
    A checkpointer that doesn't actually do anything, but which is provided
    so that programs can turn off checkpointing without changing their layout
    """
    def __init__(self, checkpoint_file=None,
                 allowed_keys=None,
                 omitted_keys=None
                 ):
        if checkpoint_file is None:
            checkpoint_file = {}
        super().__init__(checkpoint_file, allowed_keys=allowed_keys, omitted_keys=omitted_keys)
        self.backend = checkpoint_file

    def open_checkpoint_file(self, chk):
        """
        Opens the passed `checkpoint_file` (if not already open)
        :param chk:
        :type chk: str | file-like
        :return:
        :rtype:
        """
        return chk

    def close_checkpoint_file(self, stream):
        """
        Opens the passed `checkpoint_file` (if not already open)
        :param chk:
        :type chk:
        :return:
        :rtype:
        """
        pass

    def save_parameter(self, key, value):
        """
        Saves a parameter to the checkpoint file
        :param key:
        :type key:
        :param value:
        :type value:
        :return:
        :rtype:
        """
        self.backend[key] = value

    def load_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        return self.backend[key]
    def delete_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        del self.backend[key]

    def keys(self):
        return list(self.backend.keys())
    def get(self, key, default=None):
        return self.backend.get(key, default)
    def pop(self, key, *default):
        return self.backend.pop(key, *default)

class NullCheckpointer(Checkpointer):
    """
    A checkpointer that saves absolutely nothing
    """
    def __init__(self, checkpoint_file=None,
                 allowed_keys=None,
                 omitted_keys=None
                 ):
        super().__init__(checkpoint_file, allowed_keys=allowed_keys, omitted_keys=omitted_keys)
        self.backend = None

    def open_checkpoint_file(self, chk):
        """
        Opens the passed `checkpoint_file` (if not already open)
        :param chk:
        :type chk: str | file-like
        :return:
        :rtype:
        """
        return "NotAFile"

    def close_checkpoint_file(self, stream):
        """
        Opens the passed `checkpoint_file` (if not already open)
        :param chk:
        :type chk:
        :return:
        :rtype:
        """
        pass

    def save_parameter(self, key, value):
        """
        Saves a parameter to the checkpoint file
        :param key:
        :type key:
        :param value:
        :type value:
        :return:
        :rtype:
        """
        pass

    def load_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        raise CheckpointerKeyError("NullCheckpointer doesn't support _any_ keys")

    def delete_parameter(self, key):
        """
        Loads a parameter from the checkpoint file
        :param key:
        :type key:
        :return:
        :rtype:
        """
        raise CheckpointerKeyError("NullCheckpointer doesn't support _any_ keys")

    def keys(self):
        return []
