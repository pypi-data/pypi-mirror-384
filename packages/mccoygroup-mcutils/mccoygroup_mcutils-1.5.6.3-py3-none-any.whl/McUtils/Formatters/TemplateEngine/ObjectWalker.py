
"""
Provides a class that will walk through a set of objects & their children, as loaded into memory,
and call appropriate handlers for each
"""

import os, types, collections, abc
import sys, importlib
# from .Writers import *

__all__ = [
    "ObjectWalker",
    "ObjectHandler",
    "ObjectSpec"
]

class ObjectTree(dict):
    """
    Simple tree that stores the structure of the documentation
    """
class ObjectSpec(dict):
    required_keys = ['id']

class MethodDispatch(collections.OrderedDict):
    """
    Provides simple utility to dispatch methods based on types
    """

    def __init__(self, *args, default=None, **kwargs):
        self.default = default
        super().__init__(*args, **kwargs)
    class DispatchTests:
        def __init__(self, *tests):
            self.tests = tests
        def __hash__(self):
            return self.tests.__hash__()
        def __call__(self, obj):
            return all(self.test(t, obj) for t in self.tests)
        @classmethod
        def test(cls, k, obj):
            """
            Does the actual dispatch testing

            :param k:
            :type k:
            :param obj:
            :type obj:
            :return:
            :rtype:
            """
            if (
                    isinstance(k, type) or
                    isinstance(k, tuple) and all(isinstance(kk, type) for kk in k)
            ):
                return isinstance(obj, k)
            elif isinstance(k, str):
                return hasattr(obj, k)
            elif isinstance(k, tuple) and all(isinstance(kk, str) for kk in k):
                return any(hasattr(obj, kk) for kk in k)
            elif isinstance(k, tuple):
                return any(kk(obj) for kk in k)
            elif k is None:
                return True
            else:
                return k(obj)
    def method_dispatch(self, obj, *args, **kwargs):
        """
        A general-ish purpose type or duck-type method dispatcher.

        :param obj:
        :type obj:
        :param table:
        :type table:
        :return:
        :rtype:
        """

        for k, v in self.items():
            if isinstance(k, self.DispatchTests):
                matches = k(obj)
            else:
                matches = self.DispatchTests.test(k, obj)
            if matches:
                return v(obj, *args, **kwargs)

        if self.default is None:
            raise TypeError("object {} can't dispatch from table {}".format(
                obj, self
            ))
        else:
            return self.default(obj, *args, **kwargs)
    def __call__(self, obj, *args, **kwargs):
        return self.method_dispatch(obj, *args, **kwargs)
    def __setitem__(self, key, value):
        """
        :param key:
        :type key:
        :param value:
        :type value:
        :return:
        :rtype:
        """
        #TODO: make dispatch keys automatically feed into
        if isinstance(key, tuple):
            # make sure we're not just doing alternatives
            if not (
                    all(isinstance(k, str) for k in key) or
                    all(isinstance(k, type) for k in key) or
                    all(callable(k) for k in key)
            ):
                # then we do, basically, an 'and' operand
                key = self.DispatchTests(*key)
        super().__setitem__(key, value)

class ObjectHandler(metaclass=abc.ABCMeta):
    protected_fields = set()
    default_fields = {}
    def __init__(self,
                 obj,
                 *,
                 spec=None,
                 tree=None,
                 name=None,
                 parent=None,
                 walker:'ObjectWalker'=None,
                 extra_fields=None,
                 **kwargs
                 ):

        self.walker = walker
        self.obj = obj
        self._id = None
        self._name = name
        self._parent = parent
        self._pobj = None
        self._chobj = None
        self.spec = {} if spec is None else spec
        self.tree = tree

        if extra_fields is None:
            extra_fields = kwargs
        else:
            extra_fields = dict(kwargs, **extra_fields)

        self.extra_fields = extra_fields
        for k in self.default_fields.keys() - self.extra_fields.keys():
            self.extra_fields[k] = self.default_fields[k]
        for k in self.extra_fields.keys() & set(self.protected_fields):
            del self.extra_fields[k]


    def __getitem__(self, item):
        return self.resolve_key(item)
    def resolve_key(self, key, default=None):
        if key in self.spec:
            return self.spec.get(key, default)
        elif key in self.extra_fields:
            return self.extra_fields.get(key, default)
        else:
            return default

    @property
    def name(self):
        """
        Returns the name (not full identifier) of the object
        being documented

        :return:
        :rtype:
        """
        return self.get_name()

    def get_name(self):
        """
        Returns the name the object will have in its documentation page

        :return:
        :rtype:
        """
        if self._name is not None:
            name = self._name
        else:
            try:
                name = self.obj.__name__
            except AttributeError:
                name = "<{} Instance>".format(type(self.obj).__name__)

        return name

    @classmethod
    def get_identifier(cls, o):
        if hasattr(o, '__identifier__'):
            return o.__identifier__

        try:
            pkg = o.__module__
        except AttributeError:
            pkg = ""

        try:
            n = o.__qualname__
        except AttributeError:
            try:
                n = o.__name__
            except AttributeError:
                n = type(o).__name__

        qn = pkg + ('.' if pkg != "" else "") + n
        return qn
    @property
    def identifier(self):
        if self._id is None:
            self._id = self.get_identifier(self.obj)
        return self._id

    @property
    def parent(self):
        """
        Returns the parent object for docs purposes

        :return:
        :rtype:
        """
        if self._pobj is None:
            self._pobj = self.resolve_parent()
        return self._pobj
    def resolve_parent(self, check_tree=True):
        """
        Resolves the "parent" of obj.
        By default, just the module in which it is contained.
        Allows for easy skipping of pieces of the object tree,
        though, since a parent can be directly added to the set of
        written object which is distinct from the module it would
        usually resolve to.
        Also can be subclassed to provide more fine grained behavior.

        :param obj:
        :type obj:
        :return:
        :rtype:
        """

        if check_tree:
            oid = self.identifier
            if self.tree is not None and oid in self.tree:
                return self.tree[oid]['parent']

        if self._parent is not None:
            if isinstance(self._parent, str):
                return self.walker.resolve_object(self._parent)
            else:
                return self._parent
        elif 'parent' in self.spec:
            parent = self.spec['parent']
            if isinstance(parent, str):
                return self.walker.resolve_object(parent)
            else:
                return parent

        if isinstance(self.obj, types.ModuleType):
            # not totally sure this will work...
            modspec = self.obj.__name__.rsplit(".", 1)[0]
        else:
            try:
                modspec = self.obj.__module__
            except AttributeError:
                modspec = type(self.obj).__module__

        if modspec == "":
            return None

        return self.walker.resolve_object(modspec)

    def resolve_relative_obj(self, spec:str):

        if '.' == spec[0]:
            n = 0
            while spec[0] == ".":
                n += 1
                spec = spec[1:]
            if isinstance(self.obj, types.ModuleType):
                # not totally sure this will work...
                modspec = self.obj.__name__
            else:
                try:
                    modspec = self.obj.__module__
                except AttributeError:
                    modspec = type(self.obj).__module__
            modspec = modspec.rsplit(".", n)[0]
            o = self.walker.resolve_object(modspec+"."+spec)
        else:
            bits = spec.split(".")
            try:
                o = getattr(self.obj, bits[0])
            except AttributeError:
                try:
                    modspec = self.obj.__module__
                except AttributeError:
                    modspec = type(self.obj).__module__
                o = getattr(self.walker.resolve_object(modspec), bits[0])
            for s in bits[1:]:
                o = getattr(o, s)
        return o

    @property
    def children(self):
        """
        Returns the child objects for docs purposes

        :return:
        :rtype:
        """
        if self._chobj is None:
            self._chobj = self.resolve_children()
        return self._chobj
    def resolve_children(self, check_tree=True):
        """
        Resolves the "children" of obj.
        First tries to use any info supplied by the docs tree
        or a passed object spec, then that failing looks for an
        `__all__` attribute

        :param obj:
        :type obj:
        :return:
        :rtype:
        """

        childs = None
        if check_tree:
            oid = self.identifier
            if self.tree is not None and oid in self.tree:
                childs = self.tree[oid]['children']
        if childs is None:
            if 'children' in self.spec:
                childs = self.spec['children']
            elif hasattr(self.obj, '__all__'):
                childs = self.obj.__all__
            else:
                childs = []

        oid = self.identifier
        return [self.walker.resolve_object(oid + "." + x) if isinstance(x, str) else x for x in childs]

    @property
    def tree_spec(self):
        """
        Provides info that gets added to the `written` dict and which allows
        for a doc tree to be built out.

        :return:
        :rtype:
        """

        base_spec = {
            'id': self.identifier,
            'parent': self.parent,
            'children': self.children
        }
        base_spec.update(self.spec)
        return base_spec

    @abc.abstractmethod
    def handle(self):
        raise NotImplementedError("abstract method")
    def stop_traversal(self):
        return False

class ObjectWalker:
    """
    A class that walks a module/object structure, calling handlers
    appropriately at each step

    A class that walks a module structure, generating .md files for every class inside it as well as for global functions,
    and a Markdown index file.

    Takes a set of objects & writers and walks through the objects, generating files on the way
    """

    spec = ObjectSpec
    default_handlers = collections.OrderedDict()
    def __init__(self,
                 handlers=None,
                 tree=None,
                 **extra_fields
                 ):
        """
        :param objects: the objects to write out
        :type objects: Iterable[Any]
        :param out: the directory in which to write the files (`None` means `sys.stdout`)
        :type out: None | str
        :param out: the directory in which to write the files (`None` means `sys.stdout`)
        :type out: None | str
        :param: writers
        :type: DispatchTable
        :param ignore_paths: a set of paths not to write (passed to the objects)
        :type ignore_paths: None | Iterable[str]
        """

        # obtain default writer set
        if handlers is None:
            handlers = {}
        if not isinstance(handlers, MethodDispatch):
            fallback_handler = ObjectHandler if None not in self.default_handlers else self.default_handlers[None]
            if hasattr(handlers, 'items'):
                handlers = MethodDispatch(handlers.items(), default=fallback_handler)
            else:
                handlers = MethodDispatch(handlers, default=fallback_handler)
        for k, v in self._initial_handlers.items():
            if k not in handlers:
                handlers[k] = v
        self.handlers = handlers

        # obtain default tree
        if tree is None:
            tree = ObjectTree()
        self.tree = tree

        self.extra_fields = extra_fields

    @property
    def _initial_handlers(self):
        """
        Adds a minor hook onto the default_writes dict and returns it
        :return:
        :rtype:
        """

        writers = self.default_handlers.copy()
        writers[self.spec] = self.resolve_spec
        return writers

    def get_handler(self, obj, *, tree=None, walker=None, cls=None, **kwargs):
        if cls is not None:
            return cls(obj, **dict(self.extra_fields, walker=self, tree=self.tree, **kwargs))
        else:
            return self.handlers(obj,
                                 **dict(self.extra_fields, walker=self, tree=self.tree, **kwargs)
                                 )
    @staticmethod
    def resolve_object(o):
        """
        Resolves to an arbitrary object by name

        :param o:
        :type o:
        :return:
        :rtype:
        """

        if o in sys.modules:
            # first we try to do a direct look up
            o = sys.modules[o]
        elif o.rsplit(".", 1)[0] in sys.modules:
            # if direct lookup failed, but the parent module has been loaded
            # try direct lookup on that
            try:
                mod, attr = o.rsplit(".", 1)
                o = getattr(sys.modules[mod], attr)
            except AttributeError:
                o = importlib.import_module(o)
        else:
            # otherwise fall back on standard import machinery
            try:
                o = importlib.import_module(o)
            except ModuleNotFoundError:  # tried to load a member but couldn't...
                # we try to resolve this first by importing as deep as we can and then
                # requesting the final attribute pieces
                p_split = o.split(".")
                for i in range(1, len(p_split)):
                    mod_spec = ".".join(p_split[:-i])
                    try:
                        mood = importlib.import_module(mod_spec)
                    except ModuleNotFoundError:
                        pass
                    else:
                        try:
                            from functools import reduce
                            v = reduce(lambda m, a: getattr(m, a), p_split[-i:], mood)
                        except AttributeError:
                            pass
                        else:
                            o = v
                            break
                else:
                    raise ValueError("couldn't resolve {}".format(o))
        return o

    def resolve_spec(self, spec, **kwargs):
        """
        Resolves an object spec.

        :param spec: object spec
        :type spec: ObjectSpec
        :return:
        :rtype:
        """

        # for the moment we only reolve using the `id` parameter
        oid = spec['id']
        o = self.resolve_object(oid)
        return self.get_handler(o, spec=spec, **kwargs)

    def visit(self, o, parent=None, depth=0, max_depth=-1, **kwargs): # TODO: add traversal control
        """
        Visits a single object in the tree
        Provides type dispatching to a handler, basically.

        :param o: the object we want to handler
        :type o: Any
        :param parent: the handler that was called right before this
        :type parent: ObjectHandler
        :return: the result of handling
        :rtype: Any
        """

        if max_depth < 0 or depth < max_depth:

            if (
                    isinstance(o, (dict, collections.OrderedDict))
                    and all(k in o for k in self.spec.required_keys)
            ):
                o = self.spec(o.items())

            if parent is not None:
                pid = parent.identifier
            else:
                pid = None

            if isinstance(o, self.spec):
                handler = self.resolve_spec(o, parent=pid, **kwargs)
            else:
                handler = self.get_handler(o, parent=pid, **kwargs)
            oid = handler.identifier
            if oid not in self.tree:
                if handler.stop_traversal():
                    res = None
                else:
                    spec = handler.tree_spec
                    self.tree[oid] = spec

                    for child in handler.children: # depth first traversal
                        self.visit(child, parent=handler, depth=depth+1, max_depth=max_depth, **dict(handler.extra_fields, **kwargs))

                    res = handler.handle()
                    spec.update(output=res)

                return res