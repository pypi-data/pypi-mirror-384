import sys, os, pathlib, abc, enum, types, string, inspect
import ast, functools, re, fnmatch, collections
import typing, itertools, builtins
from typing import *

from ... import Devutils as dev
from .ObjectWalker import *
__reload_hook__ = [".ObjectWalker"]

__all__ = [
    "TemplateFormatter",
    "FormatDirective",
    "TemplateFormatDirective",
    "TemplateOps",
    "TemplateEngine",
    "ResourceLocator",
    "TemplateResourceExtractor",
    "TemplateWalker",
    "TemplateHandler",
    "ModuleTemplateHandler",
    "ClassTemplateHandler",
    "FunctionTemplateHandler",
    "MethodTemplateHandler",
    "ObjectTemplateHandler",
    "IndexTemplateHandler",
    "TemplateInterfaceEngine",
    "TemplateInterfaceFormatter"
]

class TemplateOps:
    @staticmethod
    def loop(caller: typing.Callable, *args, joiner="", formatter=None, **kwargs):
        if len(kwargs) == 0:
            res = [caller(*a) for a in zip(*args)]
        elif len(args) == 0:
            res = [
                caller(**{k:v for k,v in zip(kwargs.keys(), kv)})
                for kv in zip(*kwargs.values())
            ]
        else:
            res = [
                caller(*a, **{k:v for k,v in zip(kwargs.keys(), kv)})
                for a,kv in zip(zip(*args), zip(*kwargs.values()))
            ]
        if joiner is not None:
            res = joiner.join(res)
        return res
    @classmethod
    def loop_template(cls, template:str, *args, joiner="", formatter=None, **kwargs):
        return cls.loop(
            template.format,
            *args,
            joiner=joiner,
            formatter=formatter,
            **kwargs
        )
    @staticmethod
    def join(*args, joiner=" ", formatter=None):
        if len(args) == 1 and not isinstance(args[0], str):
            args = args[0]
        return joiner.join(args)
    @classmethod
    def load(cls, template, formatter=None):
        return formatter.load_template(template)
    @classmethod
    def include(cls, template, formatter=None):
        return formatter.vformat(formatter.load_template(template), (), formatter.format_parameters)
    @classmethod
    def apply(cls, template, *args, formatter=None, **kwargs):
        if formatter is None:
            raise ValueError("`{}` can't be `None`".format('formatter'))
        return formatter.format(template, *args, **kwargs)
    @classmethod
    def nonempty(cls, data, formatter=None):
        return data is not None and len(data) > 0
    @classmethod
    def wrap(cls, fn):
        @functools.wraps(fn)
        def f(*args, formatter=None, **kwargs):
            return fn(*args, **kwargs)
        return f
    @staticmethod
    def cleandoc(txt, formatter=None):
        return inspect.cleandoc(txt)
    @staticmethod
    def wrap_str(obj, formatter=None):
        txt = str(obj)
        txt = txt.replace('"', '\\"').replace("'", "\\'")
        if '\n' in txt:
            txt = '"""'+txt+'"""'
        return txt
    @staticmethod
    def optional(key, default="", formatter=None):
        return formatter.format_parameters.get(key, default)

class FormatDirective(enum.Enum):
    """
    Base class for directives -- shouldn't be an enum really...
    """
    def __init__(self, name, callback=None):
        self.key = name
        if isinstance(callback, str):
            callback = callback.format
        elif isinstance(callback, (staticmethod, classmethod, property)):
            callback = callback.__get__(self)
        self.callback = callback if not isinstance(callback, str) else callback.format
    def _call(self, *data, **kwargs):
        return self.callback(*data, **kwargs)
    @classmethod
    def _keymap(cls):
        if not hasattr(cls, '_keymap_dict'):
            cls._keymap_dict = None
        return cls._keymap_dict
    @classmethod
    def _load(cls, name:str):
        k = cls._keymap()
        if k is None:
            cls._keymap_dict = {c.key:c for c in cls}
            k = cls._keymap_dict
        return k[name]
    @classmethod
    def extend(cls, *others):
        vals = {
            o.name:o.value
            for c in (cls,) + others
            for o in c
        }
        return FormatDirective(cls.__name__, vals)

class TemplateFormatDirective(FormatDirective):
    Loop = "loop", TemplateOps.loop
    LoopTemplate = "loop_template", TemplateOps.loop_template
    Join = "join", TemplateOps.join
    Load = "load", TemplateOps.load
    Include = "include", TemplateOps.include
    Apply = "apply", TemplateOps.apply
    NonEmpty = "nonempty", TemplateOps.nonempty
    CleanDoc = "cleandoc", TemplateOps.cleandoc
    Optional = "optional", TemplateOps.optional

    Str = "str", TemplateOps.wrap_str
    Int = "int", TemplateOps.wrap(int)
    Float = "float", TemplateOps.wrap(float)
    Round = "round", TemplateOps.wrap(round)
    Len = "len", TemplateOps.wrap(len)
    Dict = "dict", TemplateOps.wrap(dict)
    List = "list", TemplateOps.wrap(list)
    Tuple = "tuple", TemplateOps.wrap(tuple)
    Set = "set", TemplateOps.wrap(set)

class TemplateFormatterError(ValueError):
    ...
class TemplateASTEvaluator:
    def __init__(self, formatter, directives, format_parameters:dict):
        self.formatter = formatter
        self.directives = directives
        self.format_parameters = format_parameters
    def handle_comprehension(self, g, expr, callback):
        target = g.target.id
        restore = False
        if target in self.format_parameters:
            restore = True
            old = self.format_parameters[target]
        try:
            itt = self.evaluate_node(g.iter)
            for v in itt:
                self.format_parameters[target] = v
                if all(self.evaluate_node(e) for e in g.ifs):
                    callback(self.evaluate_node(expr))
        finally:
            if restore:
                self.format_parameters[target] = old
            else:
                if target in self.format_parameters:
                    del self.format_parameters[target]
    def evaluate_node(self, node:typing.Union[ast.AST,ast.expr,tuple]):
        if isinstance(node, tuple):
            return tuple(self.evaluate_node(n) for n in node)
        elif isinstance(node, ast.Module):
            bits = []
            for e in node.body:
                res = self.evaluate_node(e)
                if res is None:
                    res = ""
                bits.append(str(res))
            return "".join(bits)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            name = node.id
            try:
                val = self.format_parameters[name]
            except KeyError:
                need_raise = False
                try:
                    val = getattr(builtins, name)
                except AttributeError:
                    need_raise = True
                if need_raise:
                    raise
            return val
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            return getattr(self.evaluate_node(node.value), node.attr)
        elif isinstance(node, ast.Assign):
            if len(node.targets) > 1:
                raise TemplateFormatterError("Template assignments are restricted to single reassignments")
            if not isinstance(node.targets[0], ast.Name):
                raise TemplateFormatterError("Template assignments are restricted to variable names")
            self.format_parameters[node.targets[0].id] = self.evaluate_node(node.value)
        elif isinstance(node, ast.Expr):
            return self.evaluate_node(node.value)
        elif isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.List):
            return [self.evaluate_node(e) for e in node.elts]
        elif isinstance(node, ast.ListComp):
            l = []
            for g in node.generators:
                if isinstance(g, ast.comprehension):
                    self.handle_comprehension(
                        g,
                        node.elt,
                        l.append
                    )
            return l
        elif isinstance(node, ast.Tuple):
            return tuple(self.evaluate_node(e) for e in node.elts)
        elif isinstance(node, ast.Set):
            return {self.evaluate_node(e) for e in node.elts}
        elif isinstance(node, ast.SetComp):
            l = set
            for g in node.generators:
                if isinstance(g, ast.comprehension):
                    self.handle_comprehension(
                        g,
                        node.elt,
                        l.add
                    )
            return l
        elif isinstance(node, ast.Dict):
            return {self.evaluate_node(k):self.evaluate_node(v) for k,v in zip(node.keys, node.values)}
        elif isinstance(node, ast.DictComp):
            l = {}
            add = lambda kv:l.__setitem__(*kv)
            for g in node.generators:
                if isinstance(g, ast.comprehension):
                    self.handle_comprehension(
                        g,
                        (node.key, node.value),
                        add
                    )
            return l

        elif isinstance(node, ast.UnaryOp):
            val = self.evaluate_node(node.operand)
            if isinstance(node.op, ast.Not):
                return not val
            else:
                raise TemplateFormatterError("unsupported operation {}".format(ast.dump(node.op)))
        elif isinstance(node, ast.BinOp):
            left = self.evaluate_node(node.left)
            right = self.evaluate_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            elif isinstance(node.op, ast.Sub):
                return left - right
            elif isinstance(node.op, ast.Mult):
                return left * right
            elif isinstance(node.op, ast.Div):
                return left / right
            elif isinstance(node.op, ast.FloorDiv):
                return left // right
            elif isinstance(node.op, ast.MatMult):
                return left @ right
            elif isinstance(node.op, ast.And):
                return left and right
            elif isinstance(node.op, ast.Or):
                return left or right
            elif isinstance(node.op, ast.BitOr):
                return left | right
            elif isinstance(node.op, ast.BitAnd):
                return left & right
            elif isinstance(node.op, ast.Pow):
                return left ** right
            else:
                raise TemplateFormatterError("unsupported operation {}".format(ast.dump(node.op)))
        elif isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.Or):
                return self.evaluate_node(node.values[0]) or self.evaluate_node(node.values[1])
            elif isinstance(node.op, ast.And):
                return self.evaluate_node(node.values[0]) and self.evaluate_node(node.values[1])
            else:
                raise TemplateFormatterError("unsupported operation {}".format(ast.dump(node.op)))
        elif isinstance(node, ast.Compare):
            left = self.evaluate_node(node.left)
            op = node.ops[0]
            right = self.evaluate_node(node.comparators[0])
            if isinstance(op, ast.Eq):
                return left == right
            elif isinstance(op, ast.NotEq):
                return left != right
            elif isinstance(op, ast.Lt):
                return left < right
            elif isinstance(op, ast.Gt):
                return left > right
            elif isinstance(op, ast.LtE):
                return left <= right
            elif isinstance(op, ast.GtE):
                return left >= right
            elif isinstance(op, ast.In):
                return left in right
            elif isinstance(op, ast.NotIn):
                return left not in right
            elif isinstance(op, ast.Is):
                return left is right
            elif isinstance(op, ast.IsNot):
                return left is not right
            else:
                raise TemplateFormatterError("unsupported comparison {}".format(ast.dump(op)))
        elif isinstance(node, ast.IfExp):
            if self.evaluate_node(node.test):
                return self.evaluate_node(node.body)
            else:
                return self.evaluate_node(node.orelse)
        elif isinstance(node, ast.Subscript):
            return self.evaluate_node(node.value).__getitem__(self.evaluate_node(node.slice))
        elif isinstance(node, ast.Index):
            return self.evaluate_node(node.value)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute): # subattr of some object...I guess we can call it?
                directive = self.evaluate_node(node.func)
            directive = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name == 'raw':
                    return TemplateOps.wrap_str(node.args[0])
                elif name == 'assign':
                    self.format_parameters[self.evaluate_node(node.args[0])] = self.evaluate_node(node.args[1])
                    return ""
                try:
                    directive = self.directives._load(name)
                except KeyError:
                    need_raise = name in {'open'}
                    if not need_raise:
                        try:
                            directive = getattr(builtins, name)
                        except AttributeError:
                            need_raise = True
                    if need_raise:
                        raise
                else:
                    directive = lambda *a, _d=directive, **k: _d._call(*a, formatter=self.formatter, **k)
            if directive is None:
                directive = self.evaluate_node(node.func)
            args = [self.evaluate_node(a) for a in node.args]
            kwargs = {k.arg: self.evaluate_node(k.value) for k in node.keywords}
            return directive(*args, **kwargs)
        else:
            raise TemplateFormatterError("Node {} unsupported".format(ast.dump(node)))
class TemplateFormatter(string.Formatter):
    """
    Provides a formatter for fields that allows for
    the inclusion of standard Bootstrap HTML elements
    alongside the classic formatting
    """
    max_recusion=6
    directives = TemplateFormatDirective
    class frozendict(dict):
        def __setitem__(self, key, value):
            raise TypeError("`frozendict` is immutable")
    def __init__(self, templates):
        self.__templates = self.frozendict(templates)
        self._fmt_stack = []
    @property
    def format_parameters(self):
        return self._fmt_stack[-1] if len(self._fmt_stack) > 0 else None
    @property
    def templates(self):
        return self.__templates
    @property
    def special_callbacks(self):
        return {"%":self.apply_eval_tree, "$":self.apply_directive_tree, "#":self.apply_comment, 'raw$':self.apply_raw, 'assign%':self.apply_assignment}
    @property
    def callback_map(self):
        return dict(
            self.special_callbacks,
            **{d.key+"$":self.apply_directive for d in self.directives}
        )

    def apply_eval_tree(self, _, spec) -> str:
        tree = ast.parse(inspect.cleandoc(spec))
        ev = TemplateASTEvaluator(self, self.directives, self.format_parameters).evaluate_node(tree)
        if ev is None:
            ev = ""
        return ev
    def apply_directive_tree(self, _, spec) -> str:
        return self.apply_eval_tree(_, "("+spec+")")
    def apply_assignment(self, key, spec) -> str:
        key, val = spec.split("=", 1)
        self.format_parameters[key] = val
        return ""
    def apply_raw(self, key, spec) -> str:
        return spec
    def apply_comment(self, key, spec) -> str:
        return ""
    def apply_directive(self, key, spec) -> str:
        return self.apply_directive_tree(
            key,
            "{}({})".format(key.strip("$"), spec)
        )
    def format_field(self, value: Any, format_spec: str) -> str:
        if self.format_parameters is None:
            raise NotImplementedError("{}.{} called outside of `vformat`".format(
                type(self).__name__,
                'format_field'
            ))
        callback = (
            self.callback_map.get(value, None)
            if isinstance(value, str)
            else None
        )
        if callback is None:
            return super().format_field(value, format_spec)
        else:
            return callback(value, format_spec)

    _template_cache = {}
    def load_template(self, template):
        if template not in self.__templates:
            raise ValueError("can't load templates on the fly ({} not in {})".format(
                template, self.__templates
            ))
        template = self.templates[template]
        if os.path.exists(template):
            if template not in self._template_cache:
                with open(template) as file:
                    template = file.read()
                self._template_cache[template] = template
            else:
                template = self._template_cache[template]
        return template

        # if value in s
        #     ...
        # else:
        #     super()
        # directive, args = self.parse_spec(format_spec)
        # self.directives(directive).apply(
        #     value, *args
        # )

    def vformat(self, format_string: str, args: Sequence[Any], kwargs: Mapping[str, Any]):
        try:
            self._fmt_stack.append(kwargs.copy())
            for k in self.special_callbacks:
                kwargs[k] = k
            for d in self.directives:
                if d.key+"$" not in kwargs:
                    kwargs[d.key+"$"] = d.key+"$"
            used_args = set()
            result, _ = self._vformat(format_string, args, kwargs, used_args, self.max_recusion)
            self.check_unused_args(used_args, args, kwargs)
            return result
        finally:
            self._fmt_stack.pop()

class OrderedSet(dict):
    def __init__(self, *iterable):
        if len(iterable) > 0:
            iterable = iterable[0]
        super().__init__({k:None for k in iterable})
    def union(self, other:'OrderedSet'):
        return type(self)(itertools.chain(self.keys(), other.keys()))
    def __repr__(self):
        return "{}({})".format(type(self).__name__, list(self.keys()))
    def __iter__(self):
        return iter(self.keys())
    def add(self, k):
        self[k] = None
    def update(self, ks):
        super().update({k:None for k in ks})
    def __delitem__(self, k):
        del self[k]
class Locator(typing.Protocol):
    def locate(self, identifier):
        ...
    def paths(self, **opts)->"Iterable":
        ...
class ResourcePathLocator(Locator):
    def __init__(self, path:Iterable[str]):
        if isinstance(path, str):
            path = [path]
        self.path = list(path)
    def locate(self, identifier):
        if os.path.exists(identifier):
            return os.path.abspath(identifier)
        else:
            for d in self.path:
                f = self.resource_path(d, identifier)
                if os.path.exists(f):
                    return f
    def resource_path(self, d, f):
        return os.path.join(d, f)
    def paths(self, max_depth=7, **_):
        s = OrderedSet()
        for d in self.path:
            base = self.resource_path(d, "")
            base_depth = len(pathlib.Path(base).parts)
            for root, dirs, files in os.walk(base, topdown=True):
                br = pathlib.Path(root).parts[base_depth:]
                if len(br) > max_depth:
                    break
                s.update(os.path.join(*br, f) for f in files)
        return s
    def directories(self):
        return [self.resource_path(d, "") for d in self.path]
    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            self.path
        )
class SubresourcePathLocator(ResourcePathLocator):
    def __init__(self, roots, extension):
        self.ext = extension
        super().__init__(roots)
    def resource_path(self, d, f):
        return os.path.join(d, self.ext, f)
    def __repr__(self):
        return "{}({}, {})".format(
            type(self).__name__,
            self.path,
            self.ext
        )
class ResourceLocator(Locator):
    def __init__(self,
                 locators:Iterable[Union[ResourcePathLocator,Iterable[str], Tuple[Iterable[str], Union[str, Iterable[str]]]]]
                 ):
        if isinstance(locators, str):
            locators = [locators]
        self.locators = []
        for s in locators:
            if isinstance(s, ResourcePathLocator):
                s = [s]
            elif isinstance(s[0], str):
                s = [ResourcePathLocator(s)]
            elif isinstance(s[1], str):
                s = [SubresourcePathLocator(*s)]
            else:
                s = [SubresourcePathLocator(s[0], e) for e in s[1]]
            self.locators.extend(s)
    def locate(self, identifier):
        for l in self.locators:
            res = l.locate(identifier)
            if res is not None:
                return res
    def paths(self, filter_pattern=None, **_):
        paths = {r for l in self.locators for r in l.paths()}
        if filter_pattern is not None:
            if isinstance(filter_pattern, str):
                try:
                    filter_pattern = re.compile(filter_pattern)
                except (re.error, ValueError):
                    filter_pattern = re.compile(fnmatch.translate(filter_pattern))
            paths = OrderedSet(p for p in paths if filter_pattern.match(p))
        return paths
    def directories(self):
        return OrderedSet(r for l in self.locators for r in l.directories())
    def __repr__(self):
        return "{}({})".format(
            type(self).__name__,
            self.directories()
        )

class TemplateEngine:
    """
    Provides an engine for generating content using a
    `TemplateFormatter` and `ResourceLocator`
    """

    formatter_class = TemplateFormatter
    def __init__(self,
                 locator:Locator,
                 template_pattern="*.*",
                 ignore_missing=False,
                 formatter_class=None,
                 ignore_paths=()
                 ):
        self.locator = locator
        self.templates = {
            k:self.locator.locate(k)
            for k in self.locator.paths(filter_pattern=template_pattern)
        }
        if formatter_class is None:
            formatter_class = self.formatter_class
        self.formatter = formatter_class(self.templates)
        self.ignore_missing = ignore_missing
        self.ignore_paths = ignore_paths
    def __repr__(self):
        cls = type(self)
        return dev.str_elide(f"{cls.__name__}({self.locator})", width=50)


    def format_map(self, template, parameters):
        if template in self.templates:
            template = self.formatter.load_template(template)
        return self.formatter.vformat(
            template,
            (),
            parameters if not self.ignore_missing else collections.defaultdict(parameters)
        )
    def format(self, template, **parameters):
        return self.format_map(template, parameters)

    class outStream:
        def __init__(self, file, mode='w+', **kw):
            self.file = file
            self.file_handle = None
            self.mode = mode
            self.kw = kw

        def __enter__(self):
            if self.file_handle is None:
                if isinstance(self.file, str):
                    try:
                        os.makedirs(os.path.dirname(self.file))
                    except OSError:
                        pass
                    self.file_handle = open(self.file, self.mode, **self.kw)
                else:
                    self.file_handle = self.file
            return self.file_handle

        def __exit__(self, exc_type, exc_val, exc_tb):
            if isinstance(self.file, str):
                self.file_handle.close()
            self.file_handle = None

        def write(self, s):
            with self as out:
                out.write(s)
            return self.file
    def write_string(self, target, txt):
        return self.outStream(target).write(txt)
    def apply(self, template, target, **template_params):
        try:
            if target is None:
                return self.format_map(template, template_params)
            elif target not in self.ignore_paths:
                return self.write_string(target, self.format_map(template, template_params))
        except:
            raise ValueError("{}: error in filling template {}".format(
                type(self).__name__,
                template
            ))

class TemplateHandler(ObjectHandler):
    template = None
    extension = ".md"
    squash_repeat_packages=True
    def __init__(self,
                 obj,
                 *,
                 out=None,
                 engine:TemplateEngine=None,
                 root=None,
                 squash_repeat_packages=True,
                 is_package_root=False,
                 **extra_fields
                 ):
        super().__init__(obj, **extra_fields)
        self.is_package_root = is_package_root
        self.squash_repeat_packages = squash_repeat_packages
        self.target = self.get_output_file(out)
        # if root is None:
        #     root = os.path.dirname(self.target)
        if root is None and out is not None and os.path.isdir(out):
            root = out
        self.root = root
        if engine is None:
            raise ValueError("{}:`engine` can't be None".format(type(self).__name__))
        self.engine = engine

        test_path = os.path.join(*self.identifier.split(".")) + ".md"
        if self.engine.locator.locate(test_path) is not None:
            self.template = test_path
        if self.template is None:
            raise ValueError("{}: template can't be None".format(type(self).__name__))

    def template_params(self, **kwargs):
        base_parms = self.extra_fields.copy()
        base_parms.update(self.get_template_params(**kwargs))
        return base_parms
    @abc.abstractmethod
    def get_template_params(self, **kwargs):
        """
        Returns the parameters that should be inserted into the template

        :return:
        :rtype: dict
        """
        raise NotImplementedError("abstract base class")

    @property
    def package_path(self):
        return self.get_package_and_url()
    def get_package_and_url(self, include_url_base=True):
        """
        Returns package name and corresponding URL for the object
        being documented
        :return:
        :rtype:
        """
        ident = self.identifier
        if self.squash_repeat_packages:
            ident = self.squash_reps(ident)
        pkg_split = ident.split(".", 1)

        if len(pkg_split) == 1:
            pkg = pkg_split[0]
            rest = ""
        elif len(pkg_split) == 0:
            pkg = ""
            rest = "Not.A.Real.Package"
        else:
            pkg, rest = pkg_split

        # if self.squash_repeat_packages:
        #     base_id = rest.split(".")
        #     new_id = [base_id[0]]
        #     for i,k in enumerate(base_id[1:]):
        #         if new_id[-1] != k:
        #             new_id.extend(base_id[1+i:])
        #             break
        #     rest = ".".join(new_id)

        # if len(rest) == 0:
        #     file_url = "__init__.py"
        # else:
        file_url = ident.replace(".", "/")
        if self.is_package_root:
            file_url += "/__init__.py"
        else:
            file_url += '.py'

        if include_url_base and 'url_base' in self.extra_fields:
            file_url = self.extra_fields['url_base'] + "/" + file_url
        return pkg, file_url

    @property
    def target_identifier(self):
        return ".".join(self.get_target_extension())
    @classmethod
    def squash_reps(cls, ident):
        ident = ident.split('.')
        up = ident[0]
        i = -1
        for i,r in enumerate(ident[1:]):
            if r != up:
                i = i - 1
                break
        return '.'.join(ident[i+1:])
    def get_target_extension(self, identifier=None):
        if identifier is None:
            identifier = self.identifier
        elif not isinstance(identifier, str):
            identifier = self.get_identifier(identifier)
        base_id = identifier.split(".")
        if self.squash_repeat_packages:
            new_id = [base_id[0]]
            for i, k in enumerate(base_id[1:]):
                if new_id[-1] != k:
                    new_id.extend(base_id[1 + i:])
                    break
            base_id = new_id
        return base_id
    def get_output_file(self, out):
        """
        Returns package name and corresponding URL for the object
        being documented
        :return:
        :rtype:
        """
        if out is None:
            out = sys.stdout
        elif isinstance(out, str):# and os.path.isdir(out):
            base_id = self.identifier.split(".")
            if self.squash_repeat_packages:
                new_id = [base_id[0]]
                for i, k in enumerate(base_id[1:]):
                    if new_id[-1] != k:
                        new_id.extend(base_id[1 + i:])
                        break
                base_id = new_id
            out = os.path.join(out, *base_id) + self.extension
        return out
    def handle(self, template=None, target=None, write=True):
        """
        Formats the documentation Markdown from the supplied template

        :param template:
        :type template:
        :return:
        :rtype:
        """
        if self.check_should_write():
            if template is None:
                template = self.template
            params = self.template_params()
            if target is None:
                out_file = self.target
            else:
                out_file = target
            if isinstance(out_file, str):
                pkg, file_url = self.package_path
                params['package_name'] = pkg
                params['file_url'] = file_url
                params['package_url'] = os.path.dirname(file_url)

                if self.root is not None:
                    root = self.root
                    root_split = pathlib.Path(root).parts
                    out_split = pathlib.Path(out_file).parts
                    root_depth = len(root_split)
                    out_url = "/".join(out_split[root_depth:])
                else:
                    file_split = pathlib.Path(file_url).parts
                    out_split = pathlib.Path(out_file).parts
                    out_url = "/".join(out_split[-len(file_split):])
                params['file'] = out_file
                params['url'] = out_url
            try:
                out = self.engine.apply(template, out_file if write else None, _self=self, **params)
            except KeyError as e:
                raise ValueError("{} ({}): template needs key {}".format(
                    type(self).__name__,
                    self.obj,
                    e.args[0]
                ))
            except IndexError as e:
                raise ValueError("{} ({}): template index {} out of range...".format(
                    type(self).__name__,
                    self.obj,
                    e.args[0]
                ))
            except Exception as e:
                raise ValueError("{} ({}): {}".format(
                    type(self).__name__,
                    self.obj,
                    self.template,
                    e
                ))
            return out
        else:
            if not write:
                return ""

    blacklist_packages = {'numpy', 'scipy', 'matplotlib'} #TODO: more sophisticated blacklisting
    def check_should_write(self):
        """
        Determines whether the object really actually should be
        documented (quite permissive)
        :return:
        :rtype:
        """
        base = self.identifier.split(".", 1)[0]
        stdlib = base == 'builtins'
        if not stdlib:
            try:
                loc = sys.modules[base].__file__
            except KeyError:
                stdlib = False
            else:
                stdlib = loc.startswith(sys.prefix) and 'site-packages' not in loc
        return not stdlib and base not in self.blacklist_packages

class TemplateResourceExtractor(ResourceLocator):
    extension = '.md'
    def path_extension(self, handler:TemplateHandler):
        """
        Provides the default examples path for the object
        :return:
        :rtype:
        """
        return os.path.join(*handler.get_target_extension()) + self.extension
    resource_keys = []
    resource_attrs = []
    def get_resource(self, handler:TemplateHandler, keys=None, attrs=None):
        if keys is None:
            keys = self.resource_keys
        if attrs is None:
            attrs = self.resource_attrs
        for k in keys:
            res = handler[k]
            if res is not None:
                res_file = self.locate(res)
                if res_file is not None:
                    res = res
                break
        else:
            for a in attrs:
                res = getattr(handler.obj, a, None)
                if res is not None:
                    res_file = self.locate(res)
                    if res_file is not None:
                        res = res
                    break
            else:
                ext = self.path_extension(handler)
                if isinstance(ext, str):
                    res = self.locate(ext)
                else:
                    for e in ext:
                        res = self.locate(e)
                        if res is not None:
                            break
                    else:
                        res = None
        return res
    def load(self, handler:TemplateHandler):
        """
        Loads examples for the stored object if provided
        :return:
        :rtype:
        """

        resource = self.get_resource(handler)
        if resource is not None and os.path.isfile(resource):
            with open(resource) as f:
                resource = f.read()
        return resource

class ModuleTemplateHandler(TemplateHandler):
    template = 'module.md'
class ClassTemplateHandler(TemplateHandler):
    template = 'class.md'
class FunctionTemplateHandler(TemplateHandler):
    template = 'function.md'
class MethodTemplateHandler(TemplateHandler):
    template = 'method.md'
class ObjectTemplateHandler(TemplateHandler):
    template = 'object.md'
class IndexTemplateHandler(TemplateHandler):
    template = 'index.md'

class TemplateWalker(ObjectWalker):
    module_handler = ModuleTemplateHandler
    class_handler = ClassTemplateHandler
    function_handler = FunctionTemplateHandler
    method_handler = MethodTemplateHandler
    object_handler = ObjectTemplateHandler
    index_handler = IndexTemplateHandler
    def __init__(self, engine:TemplateEngine, out=None, description=None, **extra_fields):
        self.engine = engine
        self.out_dir = out
        self.description = description
        super().__init__(**extra_fields)

    @property
    def default_handlers(self):
        return collections.OrderedDict((
            ((str, types.ModuleType), self.module_handler),
            ((type,), self.class_handler),
            ((types.FunctionType,), self.function_handler),
            (None, self.object_handler)
        ))

    def get_handler(self, obj, *, out=None, engine=None, tree=None, **kwargs):
        return super().get_handler(
            obj,
            out=self.out_dir,
            engine=self.engine,
            tree=tree,
            **kwargs
        )

    def visit_root(self, o, **kwargs): # here for overloading
        return self.visit(o, **kwargs)

    def write(self, objects, max_depth=-1, index='index.md'):
        """
        Walks through the objects supplied and applies the appropriate templates
        :return: index of written files
        :rtype: str
        """

        if self.out_dir is not None and index is not None:
            try:
                os.makedirs(self.out_dir)
            except OSError:
                pass
            out_file = os.path.join(self.out_dir, index)
        else:
            out_file = None

        files = [
            self.visit_root(o, max_depth=max_depth)
            for o in objects
        ]
        files = [f for f in files if f is not None]
        w = self.get_handler(files,
                             cls=self.index_handler,
                             out=out_file,
                             engine=self.engine,
                             root=self.out_dir,
                             extra_fields=self.extra_fields,
                             description=self.description
                             )
        return w.handle()

class TemplateResourceList(Locator):
    """
    Implements the `ResourceLocator` interface, but is backed by a `dict` of
    explicit resources rather than a set of paths.
    """
    def __init__(self, resource_dict:Mapping[str, Any]):
        self.dict = resource_dict
    def paths(self, **_):
        return self.dict.keys()
    def locate(self, identifier):
        return self.dict.get(identifier, None)
class TemplateInterfaceList(TemplateResourceList):
    """
    A set of functions to be used to construct interfaces
    """
    def __init__(self, resource_dict:Mapping[str, Callable]):
        super().__init__(resource_dict)
class TemplateInterfaceFormatter:
    """
    Provides an interface that mimics a `TemplateFormatter`
    but does nothing more than route to a set of template functions
    """
    def __init__(self, templates):
        self.__templates = templates
        self._fmt_stack = []
    @property
    def format_parameters(self):
        return self._fmt_stack[-1] if len(self._fmt_stack) > 0 else None
    @property
    def templates(self):
        return self.__templates
    @property
    def special_callbacks(self):
        return {
            # "%":self.apply_eval_tree,
            # "$":self.apply_directive_tree,
            # "#":self.apply_comment,
            # 'raw$':self.apply_raw,
            # 'assign%':self.apply_assignment
        }
    # @property
    # def callback_map(self):
    #     return dict(
    #         self.special_callbacks,
    #         **{d.key+"$":self.apply_directive for d in self.directives}
    #     )
    #
    # def apply_eval_tree(self, _, spec) -> str:
    #     tree = ast.parse(inspect.cleandoc(spec))
    #     ev = TemplateASTEvaluator(self, self.directives, self.format_parameters).evaluate_node(tree)
    #     if ev is None:
    #         ev = ""
    #     return ev
    # def apply_directive_tree(self, _, spec) -> str:
    #     return self.apply_eval_tree(_, "("+spec+")")
    # def apply_assignment(self, key, spec) -> str:
    #     key, val = spec.split("=", 1)
    #     self.format_parameters[key] = val
    #     return ""
    # def apply_raw(self, key, spec) -> str:
    #     return spec
    # def apply_comment(self, key, spec) -> str:
    #     return ""
    # def apply_directive(self, key, spec) -> str:
    #     return self.apply_directive_tree(
    #         key,
    #         "{}({})".format(key.strip("$"), spec)
    #     )
    # def format_field(self, value: Any, format_spec: str) -> str:
    #     if self.format_parameters is None:
    #         raise NotImplementedError("{}.{} called outside of `vformat`".format(
    #             type(self).__name__,
    #             'format_field'
    #         ))
    #     callback = (
    #         self.callback_map.get(value, None)
    #         if isinstance(value, str)
    #         else None
    #     )
    #     if callback is None:
    #         return super().format_field(value, format_spec)
    #     else:
    #         return callback(value, format_spec)

    # _template_cache = {}
    def load_template(self, template):
        return self.templates[template]

        # if value in s
        #     ...
        # else:
        #     super()
        # directive, args = self.parse_spec(format_spec)
        # self.directives(directive).apply(
        #     value, *args
        # )

    def vformat(self, template: Callable, args: Sequence[Any], kwargs: Mapping[str, Any]):
        try:
            self._fmt_stack.append(kwargs.copy())
            for k in self.special_callbacks:
                kwargs[k] = k
            return template(*args, **kwargs)
            # for d in self.directives:
            #     if d.key+"$" not in kwargs:
            #         kwargs[d.key+"$"] = d.key+"$"
            # used_args = set()
            # result, _ = self._vformat(format_string, args, kwargs, used_args, self.max_recusion)
            # self.check_unused_args(used_args, args, kwargs)
            # return result
        finally:
            self._fmt_stack.pop()

class TemplateInterfaceEngine(TemplateEngine):
    """
    A variant on a template engine designed for more interactive use.
    In many ways, _not_ a template engine, but too useful to ignore while I
    find a more uniform abstraction.
    Generates _interfaces_ from a set of interface template functions
    rather than strings from template files.
    """

    formatter_class = TemplateInterfaceFormatter
    def __init__(self,
                 templates: 'TemplateInterfaceList|dict',
                 ignore_missing=False,
                 formatter_class=None,
                 ignore_paths=()
                 ):
        if isinstance(templates, dict):
            templates = TemplateInterfaceList(templates)
        super().__init__(
            templates,
            template_pattern=None,
            ignore_missing=ignore_missing,
            formatter_class=formatter_class,
            ignore_paths=ignore_paths
        )

    def format_map(self, template, parameters):
        if template in self.templates:
            template = self.formatter.load_template(template)
        return self.formatter.vformat(
            template,
            (),
            parameters if not self.ignore_missing else collections.defaultdict(parameters)
        )

    def apply(self, template, target, **template_params):
        try:
            if target is None or target is sys.stdout:
                return self.format_map(template, template_params)
            elif target not in self.ignore_paths:
                return {target:self.format_map(template, template_params)}
        except:
            raise ValueError("{}: error in filling template {}".format(
                type(self).__name__,
                template
            ))