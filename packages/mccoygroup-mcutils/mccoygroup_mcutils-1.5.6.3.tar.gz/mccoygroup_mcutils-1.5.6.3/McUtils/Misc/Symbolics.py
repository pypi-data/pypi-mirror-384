
import ast, abc, copy
import numpy as np
ellipsis = type(...)

__all__ = [
    'Abstract'
]

class ASTUtils:
    """
    Provides utilities for writing easier AST expressions
    by essentially allowing for the creation of an alternate,
    less-annotated tree that can be manipulated naturally using
    python operations and then can record and replay those ops
    """

    @staticmethod
    def ast_var(var):
        if isinstance(var, str):
            var = ast.Name(id=var, ctx=ast.Load())
        return var
    @classmethod
    def ast_attr(cls, obj, attr):
        if isinstance(obj, str):
            obj = cls.ast_var(obj)
        return ast.Attribute(value=cls.astify(obj), attr=attr, ctx=ast.Load())
    @classmethod
    def astify(cls, val):
        if isinstance(val, AbstractExpr):
            val = val.to_ast()
        elif not isinstance(val, ast.AST):
            if isinstance(val, (int, float, str, np.integer, np.floating, ellipsis)):
                val = ast.Constant(value=val, kind=None)
            else:
                val = cls.convert(val).to_ast()
        return val

    @classmethod
    def prep_args(cls, args):
        return [
            a.to_star() if isinstance(a, AbstractStarOrIter) else
            a for a in args
        ]
    @classmethod
    def ast_call(cls, fn, *args, **kwargs):
        return ast.Call(
            func=cls.astify(fn) if not isinstance(fn, str) else cls.ast_var(fn),
            args=[cls.astify(a) for a in cls.prep_args(args)],
            keywords=[
                ast.keyword(arg=None, value=cls.astify(v.var))
                    if isinstance(v, AbstractStarStar) else
                ast.keyword(arg=k, value=cls.astify(v))

                for k, v in kwargs.items()
            ]
        )

    @classmethod
    def ast_arglist(cls, spec):
        if isinstance(spec, AbstractArgSpec):
            return spec.to_ast()

        if isinstance(spec, str):
            spec = (spec,)
        if isinstance(spec[0], str):
            spec = (spec, {})

        vararg = None
        args = []
        for a in spec[0]:
            if isinstance(a, AbstractStarOrIter):
                a = a.to_star()
            if isinstance(a, str):
                args.append(ast.arg(arg=a, annotation=None, type_comment=None))
            elif isinstance(a, AbstractName):
                args.append(ast.arg(arg=a.name, annotation=None, type_comment=None))
            elif isinstance(a, AbstractStar):
                var = a.iterable
                if isinstance(var, AbstractName):
                    var = var.name
                if not isinstance(var, str):
                    raise NotImplementedError("????")
                vararg = ast.arg(arg=var, annotation=None, type_comment=None)
            else:
                args.append(a)

        varkwarg = None
        kwarg_keys = []
        kwarg_vals = []
        for k, v in spec[1].items():
            if isinstance(v, AbstractStarStar):
                var = v.var
                if isinstance(var, AbstractName):
                    var = var.name
                varkwarg = ast.arg(arg=var, annotation=None, type_comment=None)
            elif isinstance(k, str):
                kwarg_keys.append(ast.arg(arg=k, annotation=None, type_comment=None))
                kwarg_vals.append(cls.astify(v))
            else:
                kwarg_keys.append(k)
                kwarg_vals.append(cls.astify(v))

        return ast.arguments(
            posonlyargs=[],
            args=args,
            vararg=vararg,
            kwonlyargs=kwarg_keys,
            kw_defaults=kwarg_vals,
            kwarg=varkwarg,
            defaults=[]
        )

    @classmethod
    def ast_const(cls, value):
        if not isinstance(value, (str, int, float, np.integer, np.floating)):
            value = cls.astify(value)
        return ast.Constant(value=value, kind=None)

    @classmethod
    def ast_iterable(cls, otype, values):
        return otype(
            elts=[cls.astify(v) for v in values],
            ctx=ast.Load()
        )
    @classmethod
    def ast_list(cls, *values):
        return cls.ast_iterable(
            ast.List,
            values
        )
    @classmethod
    def ast_tuple(cls, *values):
        return cls.ast_iterable(
            ast.Tuple,
            values
        )
    @classmethod
    def ast_set(cls, *values):
        return cls.ast_iterable(
            ast.Set,
            values
        )
    @classmethod
    def ast_dict(cls, **key_pairs):
        return ast.Dict(
            keys=[cls.astify(k) for k in key_pairs.keys()],
            values=[cls.astify(k) for k in key_pairs.values()],
        )

    @classmethod
    def ast_comprehension(cls, var, iterable, filter=None):
        return ast.comprehension(
            target=cls.ast_var(var) if isinstance(var, str) else cls.astify(var),
            iter=cls.astify(iterable),
            ifs=[cls.astify(f) for f in ([filter] if not isinstance(filter, (list, tuple)) else filter)],
            is_async=0 # someday maybe I'll add in async but I just don't need it right now
        )
    @classmethod
    def ast_type_comprehension(cls, otype, expr, comprehension, iterable=None, filter=None):
        return otype(
            elt=expr,
            generators=[
                cls.ast_comprehension(comprehension, iterable, filter=filter)
                if iterable is not None else
                comprehension
            ]
        )
    @classmethod
    def ast_generator(cls, expr, comprehension, iterable=None, filter=None):
        return cls.ast_type_comprehension(
            ast.GeneratorExp,
            expr, comprehension,
            iterable=iterable, filter=filter
        )
    @classmethod
    def ast_list_comprehension(cls, expr, comprehension, iterable=None, filter=None):
        return cls.ast_type_comprehension(
            ast.ListComp,
            expr, comprehension,
            iterable=iterable, filter=filter
        )
    @classmethod
    def ast_set_comprehension(cls, expr, comprehension, iterable=None, filter=None):
        return cls.ast_type_comprehension(
            ast.ListComp,
            expr, comprehension,
            iterable=iterable, filter=filter
        )
    @classmethod
    def ast_dict_comprehension(cls, key_expr, value_expr, comprehension, iterable=None, filter=None):
        return ast.DictComp(
            key=cls.astify(key_expr),
            value=cls.astify(value_expr),
            generators=[
                cls.ast_comprehension(comprehension, iterable, filter=filter)
                if iterable is not None else
                comprehension
            ]
        )

    @classmethod
    def ast_lambda(cls, spec, body):
        return ast.Lambda(
            args=cls.ast_arglist(spec) if not isinstance(spec, ast.arguments) else spec,
            body=cls.astify(body)
        )

    class ContextModifier(ast.NodeTransformer):
        def __init__(self, ctx):
            self.ctx = ctx
        def generic_visit(self, node: ast.AST) -> ast.AST:
            if hasattr(node, 'ctx'):
                node = copy.copy(node)
                node.ctx = self.ctx
            return super().generic_visit(node)

    @classmethod
    def ast_assign(cls, targets, value):
        mod = cls.ContextModifier(ast.Store())
        return ast.Assign(targets=[mod.visit(cls.astify(t)) for t in targets], value=cls.astify(value))

    @classmethod
    def ast_boolop(cls, op, left, right, *extra):
        return ast.BoolOp(
            op=op,
            values=[cls.astify(left), cls.astify(right), *(cls.astify(e) for e in extra)]
        )
    @classmethod
    def ast_and(cls, left, right, *extra):
        return cls.ast_boolop(ast.And(), left, right, *extra)
    @classmethod
    def ast_or(cls, left, right, *extra):
        return cls.ast_boolop(ast.Or(), left, right, *extra)

    @classmethod
    def ast_binop(cls, op, left, right):
        return ast.BinOp(
            left=cls.astify(left),
            op=op,
            right=cls.astify(right)
        )
    @classmethod
    def ast_add(cls, left, right):
        return cls.ast_binop(ast.Add(), left, right)
    @classmethod
    def ast_sub(cls, left, right):
        return cls.ast_binop(ast.Sub(), left, right)
    @classmethod
    def ast_mult(cls, left, right):
        return cls.ast_binop(ast.Mult(), left, right)
    @classmethod
    def ast_div(cls, left, right):
        return cls.ast_binop(ast.Div(), left, right)
    @classmethod
    def ast_matmult(cls, left, right):
        return cls.ast_binop(ast.MatMult(), left, right)
    @classmethod
    def ast_floordiv(cls, left, right):
        return cls.ast_binop(ast.FloorDiv(), left, right)
    @classmethod
    def ast_pow(cls, left, right):
        return cls.ast_binop(ast.Pow(), left, right)
    @classmethod
    def ast_mod(cls, left, right):
        return cls.ast_binop(ast.Mod(), left, right)
    @classmethod
    def ast_bitxor(cls, left, right):
        return cls.ast_binop(ast.BitXor(), left, right)
    @classmethod
    def ast_bitand(cls, left, right):
        return cls.ast_binop(ast.BitAnd(), left, right)
    @classmethod
    def ast_bitor(cls, left, right):
        return cls.ast_binop(ast.BitOr(), left, right)

    @classmethod
    def ast_comp(cls, op, left, right, *extra):
        return ast.Compare(
            left=cls.astify(left),
            op=op,
            comparators=[cls.astify(right), *(cls.astify(v) for v in extra)]
        )
    @classmethod
    def ast_eq(cls, left, right, *extra):
        return cls.ast_comp(ast.Eq(), left, right, *extra)
    @classmethod
    def ast_ne(cls, left, right, *extra):
        return cls.ast_comp(ast.NotEq(), left, right, *extra)
    @classmethod
    def ast_lt(cls, left, right, *extra):
        return cls.ast_comp(ast.Lt(), left, right, *extra)
    @classmethod
    def ast_gt(cls, left, right, *extra):
        return cls.ast_comp(ast.Gt(), left, right, *extra)
    @classmethod
    def ast_lte(cls, left, right, *extra):
        return cls.ast_comp(ast.LtE(), left, right, *extra)
    @classmethod
    def ast_gte(cls, left, right, *extra):
        return cls.ast_comp(ast.GtE(), left, right, *extra)
    @classmethod
    def ast_in(cls, left, right, *extra):
        return cls.ast_comp(ast.In(), left, right, *extra)
    @classmethod
    def ast_ni(cls, left, right, *extra):
        return cls.ast_comp(ast.NotIn(), left, right, *extra)
    @classmethod
    def ast_is(cls, left, right, *extra):
        return cls.ast_comp(ast.Is(), left, right, *extra)
    @classmethod
    def ast_isnt(cls, left, right, *extra):
        return cls.ast_comp(ast.IsNot(), left, right, *extra)

    @classmethod
    def ast_unop(cls, op, val):
        return ast.UnaryOp(
            op=op,
            operand=cls.astify(val)
        )
    @classmethod
    def ast_not(cls, val):
        return cls.ast_unop(ast.Not(), val)
    @classmethod
    def ast_inv(cls, val):
        return cls.ast_unop(ast.Invert(), val)
    @classmethod
    def ast_pos(cls, val):
        return cls.ast_unop(ast.UAdd(), val)
    @classmethod
    def ast_neg(cls, val):
        return cls.ast_unop(ast.USub(), val)

    @classmethod
    def ast_star(cls, iterable):
        return ast.Starred(cls.astify(iterable), ctx=ast.Load())

    @classmethod
    def ast_ternary(cls, test, body, orelse):
        return ast.IfExp(
            test=cls.astify(test),
            body=cls.astify(body),
            orelse=cls.astify(orelse)
        )

    @classmethod
    def ast_subscript(cls, value, index):
        return ast.Subscript(
            value=cls.astify(value),
            slice=cls.ast_index(index) if not isinstance(index, slice) else cls.ast_slice(
                index.start,
                index.stop,
                index.step
            ),
            ctx=ast.Load()
        )

    @classmethod
    def ast_index(cls, value):
        return ast.Index(value=cls.astify(value))
    @classmethod
    def ast_slice(cls, start=None, stop=None, step=None):
        return ast.Slice(
            lower=cls.astify(start) if start is not None else start,
            upper=cls.astify(stop) if stop is not None else stop,
            step=cls.astify(step) if step is not None else step
            )

    @classmethod
    def convert(cls, val) -> 'AbstractExpr':
        if isinstance(val, (str, int, float, np.integer, np.floating, ellipsis)):
            val = AbstractConstant(val)
        elif isinstance(val, list):
            val = AbstractList(*val)
        elif isinstance(val, tuple):
            val = AbstractTuple(*val)
        elif isinstance(val, set):
            val = AbstractSet(*val)
        elif isinstance(val, dict):
            val = AbstractDict(**val)
        elif not isinstance(val, AbstractExpr):
            raise ValueError("no rules for converting {}".format(val))
        return val

class AbstractExpr(metaclass=abc.ABCMeta):
    __tag__ = None
    __slots__ = []
    def __hash__(self):
        return hash((type(self), tuple(getattr(self, k) for k in self.__slots__)))

    @abc.abstractmethod
    def to_ast(self)->'ast.AST':
        ...

    def to_eval_expr(self):
        return ast.fix_missing_locations(ast.Expression(body=self.to_ast()))
    def compile(self, namespace=None):
        if namespace is None:
            namespace = {}
        return eval(
            compile(self.to_eval_expr(), '<symbolic expression>', mode='eval'),
            namespace
        )

    def transmogrify(self, converter_dispatch:dict):
        def convert(expr):
            if not isinstance(expr, AbstractExpr):
                conversion_func = converter_dispatch.get(None, None)
                if conversion_func is None:
                    raise ValueError("missing conversion for object {}".format(expr))
                return conversion_func(expr, convert)

            conversion_func = converter_dispatch.get(expr.__tag__, None)
            if conversion_func is None:
                conversion_func = converter_dispatch.get('Expr', None)
                if conversion_func is None:
                    raise ValueError("missing conversion for tag {}".format(expr.__tag__))
            return conversion_func(expr, convert)
        return convert(self)


    def __call__(self, *args, **kwargs):
        return AbstractCall(self, *args, **kwargs)

    def __not__(self):
        return AbstractNot(self)
    def __invert__(self):
        return AbstractInv(self)
    def __pos__(self):
        return AbstractPos(self)
    def __neg__(self):
        return AbstractNeg(self)

    def __add__(self, other):
        return AbstractAdd(self, other)
    def __radd__(self, other):
        return AbstractAdd(other, self)
    def __sub__(self, other):
        return AbstractSub(self, other)
    def __mul__(self, other):
        return AbstractMult(self, other)
    def __rmul__(self, other):
        return AbstractMult(other, self)
    def __pow__(self, other):
        return AbstractPow(self, other)
    def __truediv__(self, other):
        return AbstractDiv(self, other)
    def __floordiv__(self, other):
        return AbstractFloorDiv(self, other)
    def __xor__(self, other):
        return AbstractBitXOr(self, other)
    def __rxor__(self, other):
        return AbstractBitXOr(other, self)
    def __or__(self, other):
        return AbstractBitOr(self, other)
    def __ror__(self, other):
        return AbstractBitOr(other, self)
    def __and__(self, other):
        return AbstractBitAnd(self, other)
    def __rand__(self, other):
        return AbstractBitAnd(other, self)

    def __contains__(self, item):
        return AbstractIn(self, item)

    def __abs__(self):
        return AbstractAbs(self)
    def __floor__(self):
        return AbstractFloor(self)
    def __ceil__(self):
        return AbstractCeil(self)

    def __iter__(self):
        yield AbstractStarOrIter(self)

    def keys(self):
        yield AbstractUnwrapKeys(self)
    def __getitem__(self, item):
        if isinstance(item, AbstractUnwrapKeys):
            return AbstractStarStar(self)
        else:
            return AbstractSubscript(self, item)

    def __getattr__(self, item):
        return AbstractAttribute(self, item)

    def Equals(self, right):
        return AbstractEq(self, right)
    Eq = Equals
    def LessThan(self, right):
        return AbstractLt(self, right)
    Lt = LessThan
    def LessEquals(self, right):
        return AbstractLtE(self, right)
    LtE = LessEquals
    def GreaterThan(self, right):
        return AbstractGt(self, right)
    Gt = GreaterThan
    def GreaterEquals(self, right):
        return AbstractGtE(self, right)
    GtE = GreaterEquals
    def And(self, right):
        return AbstractAnd(self, right)
    def Or(self, right):
        return AbstractOr(self, right)

    def Is(self, other):
        return AbstractIs(self, other)
    def IsNot(self, other):
        return AbstractIsNot(self, other)
    Isnt = IsNot

    def generator(self, expr, var, filter=None):
        return AbstractGenerator(expr, var, self, filter=filter)
    Gen = generator
    def list_comp(self, expr, var, filter=None):
        return AbstractListComp(expr, var, self, filter=filter)
    LC = list_comp
    def set_comp(self, expr, var, filter=None):
        return AbstractSetComp(expr, var, self, filter=filter)
    SC = set_comp
    def dict_comp(self, key_expr, value_expr, var, filter=None):
        return AbstractDictComp(key_expr, value_expr, var, self, filter=filter)
    DC = dict_comp

    def if_test(self, test, else_expr=None):
        return AbstractIfExp(test, self, else_expr)
    def if_self(self, expr, else_expr=None):
        return AbstractIfExp(self, expr, else_expr)

    def __repr__(self):
        return "{}()".format(type(self).__name__)

class AbstractName(AbstractExpr):
    __tag__ = "Name"
    __slots__ = ['name']
    def __init__(self, name):
        self.name = name
    def to_ast(self)->'ast.Name':
        return ASTUtils.ast_var(self.name)
    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.name)

class AbstractConstant(AbstractExpr):
    __tag__ = 'Const'
    __slots__ = ['value']
    def __init__(self, value):
        self.value = value
    def to_ast(self):
        return ASTUtils.ast_const(self.value)
    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.value)

class AbstractCall(AbstractExpr):
    __tag__ = 'Call'
    __slots__ = ['fn', 'args', 'kwargs']
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
    def to_ast(self)->'ast.Call':
        return ASTUtils.ast_call(self.fn,
                             *self.args,
                             **self.kwargs
                             )
    def __repr__(self):
        return "{}({}, {}, {})".format(type(self).__name__, self.fn, self.args, self.kwargs)

class AbstractAttribute(AbstractExpr):
    __tag__ = 'Attr'
    __slots__ = ['obj', 'attr']
    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr
    def to_ast(self) -> 'ast.Attribute':
        return ASTUtils.ast_attr(self.obj, self.attr)
    def __repr__(self):
        return "{}({}, {})".format(type(self).__name__, self.obj, self.attr)

class AbstractBinOp(AbstractExpr):
    __slots__ = ['left', 'right']
    def __init__(self, left, right):
        self.left = left
        self.right = right
class AbstractAdd(AbstractBinOp):
    __tag__ = 'Add'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_add(self.left, self.right)
class AbstractSub(AbstractBinOp):
    __tag__ = 'Sub'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_sub(self.left, self.right)
class AbstractMult(AbstractBinOp):
    __tag__ = 'Mul'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_mult(self.left, self.right)
class AbstractDiv(AbstractBinOp):
    __tag__ = 'Div'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_div(self.left, self.right)
class AbstractMatMult(AbstractBinOp):
    __tag__ = 'MatMul'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_matmult(self.left, self.right)
class AbstractFloorDiv(AbstractBinOp):
    __tag__ = 'FloorDiv'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_floordiv(self.left, self.right)
class AbstractPow(AbstractBinOp):
    __tag__ = 'Pow'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_pow(self.left, self.right)
class AbstractMod(AbstractBinOp):
    __tag__ = 'Mod'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_mod(self.left, self.right)
class AbstractBitXOr(AbstractBinOp):
    __tag__ = 'BitXOr'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_bitxor(self.left, self.right)
class AbstractBitOr(AbstractBinOp):
    __tag__ = 'BitOr'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_bitor(self.left, self.right)
class AbstractBitAnd(AbstractBinOp):
    __tag__ = 'BitAnd'
    def to_ast(self) ->'ast.BinOp':
        return ASTUtils.ast_bitand(self.left, self.right)

class AbstractUnOp(AbstractExpr):
    __slots__ = ['operand']
    def __init__(self, operand):
        self.operand = operand
class AbstractNot(AbstractUnOp):
    __tag__ = 'Not'
    def to_ast(self) ->'ast.UnaryOp':
        return ASTUtils.ast_not(self.operand)
class AbstractInv(AbstractUnOp):
    __tag__ = 'Inv'
    def to_ast(self) ->'ast.UnaryOp':
        return ASTUtils.ast_inv(self.operand)
class AbstractPos(AbstractUnOp):
    __tag__ = 'Pos'
    def to_ast(self) ->'ast.UnaryOp':
        return ASTUtils.ast_pos(self.operand)
class AbstractNeg(AbstractUnOp):
    __tag__ = 'Neg'
    def to_ast(self) ->'ast.UnaryOp':
        return ASTUtils.ast_neg(self.operand)

class AbstractComp(AbstractExpr):
    __slots__ = ['left', 'right', 'extra']
    def __init__(self, left, right, *extra):
        self.left = left
        self.right = right
        self.extra = extra
class AbstractEq(AbstractComp):
    __tag__ = 'Equals'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_eq(self.left, self.right, *self.extra)
class AbstractNotEq(AbstractComp):
    __tag__ = 'NotEquals'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_ne(self.left, self.right, *self.extra)
class AbstractLt(AbstractComp):
    __tag__ = 'Less'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_lt(self.left, self.right, *self.extra)
class AbstractGt(AbstractComp):
    __tag__ = 'Greater'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_gt(self.left, self.right, *self.extra)
class AbstractLtE(AbstractComp):
    __tag__ = 'LessEquals'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_lte(self.left, self.right, *self.extra)
class AbstractGtE(AbstractComp):
    __tag__ = 'GreaterEquals'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_gte(self.left, self.right, *self.extra)
class AbstractIn(AbstractComp):
    __tag__ = 'In'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_in(self.left, self.right, *self.extra)
class AbstractNotIn(AbstractComp):
    __tag__ = 'NotIn'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_ni(self.left, self.right, *self.extra)
class AbstractIs(AbstractComp):
    __tag__ = 'Is'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_is(self.left, self.right, *self.extra)
class AbstractIsNot(AbstractComp):
    __tag__ = 'IsNot'
    def to_ast(self) ->'ast.Compare':
        return ASTUtils.ast_isnt(self.left, self.right, *self.extra)

class AbstractSubscript(AbstractExpr):
    __tag__ = 'Subscript'
    __slots__ = ['obj', 'index']
    def __init__(self, obj, index):
        self.obj, self.index = obj, index
    def to_ast(self):
        return ASTUtils.ast_subscript(self.obj, self.index)

class AbstractBoolOp(AbstractExpr):
    __slots__ = ['left', 'right', 'extra']
    def __init__(self, left, right, *extra):
        self.left = left
        self.right = right
        self.extra = extra
class AbstractAnd(AbstractComp):
    __tag__ = 'And'
    def to_ast(self) ->'ast.BoolOp':
        return ASTUtils.ast_and(self.left, self.right, *self.extra)
class AbstractOr(AbstractComp):
    __tag__ = 'Or'
    def to_ast(self) ->'ast.BoolOp':
        return ASTUtils.ast_or(self.left, self.right, *self.extra)


class AbstractImportModule(AbstractCall):
    def __init__(self, mod):
        super().__init__('__import__', mod)

class AbstractAbs(AbstractCall):
    def __init__(self, val):
        super().__init__('abs', val)
class AbstractFloor(AbstractCall):
    def __init__(self, val):
        super().__init__(AbstractImportModule('math').floor, val)
class AbstractCeil(AbstractCall):
    def __init__(self, val):
        super().__init__(AbstractImportModule('math').ceil, val)


class AbstractIter(AbstractCall):
    def __init__(self, val):
        super().__init__('iter', val)
class AbstractStar(AbstractExpr):
    __tag__ = 'Star'
    __slots__ = ['iterable']
    def __init__(self, iterable):
        self.iterable = iterable
    def to_ast(self) ->'ast.Starred':
        return ASTUtils.ast_star(self.iterable)
class AbstractStarOrIter(AbstractExpr):
    __tag__ = 'StarOrIter'
    __slots__ = ['val']
    def __init__(self, val):
        self.val = val
    def to_iter(self):
        return AbstractIter(self.val)
    def to_star(self):
        return AbstractStar(self.val)
    def to_ast(self) ->'ast.AST':
        raise ValueError("type of `AbstractStarOrIter` is indeterminate")

class AbstractUnwrapKeys(str):
    __tag__ = 'UnwrapKeys'
    __slots__ = ['val']
    def __new__(cls, content):
        return str.__new__(cls, "____init_keys" + str(content))
    def __init__(self, val):
        super().__init__()
        self.val = val
    def to_iter(self):
        return AbstractCall(AbstractAttribute(self.val, 'keys'))
    def to_starstar(self):
        return AbstractStarStar(self.val)
    def to_ast(self) -> 'ast.AST':
        raise ValueError("type of `AbstractUnwrapKeys` is indeterminate")
class AbstractStarStar(AbstractExpr):
    __tag__ = 'StarStar'
    __slots__ = ['var']
    def __init__(self, var):
        self.var = var
    def to_ast(self):
        raise ValueError("type of `AbstractStarStar` has not ast equivalent")

class AbstractList(AbstractExpr):
    __tag__ = 'List'
    __slots__ = ['args']
    def __init__(self, *args):
        self.args = args
    def to_ast(self) ->'ast.List':
        return ASTUtils.ast_list(*self.args)
class AbstractTuple(AbstractExpr):
    __tag__ = 'Tuple'
    __slots__ = ['args']
    def __init__(self, *args):
        self.args = args
    def to_ast(self) ->'ast.Tuple':
        return ASTUtils.ast_tuple(*self.args)
class AbstractSet(AbstractExpr):
    __tag__ = 'Set'
    __slots__ = ['args']
    def __init__(self, *args):
        self.args = args
    def to_ast(self) ->'ast.Set':
        return ASTUtils.ast_set(*self.args)
class AbstractDict(AbstractExpr):
    __tag__ = 'Dict'
    __slots__ = ['kwargs']
    def __init__(self, **kwargs):
        self.kwargs = kwargs
    def to_ast(self) ->'ast.Dict':
        return ASTUtils.ast_dict(**self.kwargs)

class AbstractListComp(AbstractExpr):
    __tag__ = 'ListComp'
    __slots__ = ['expr', 'var', 'iterable', 'filter']
    def __init__(self, expr, var, iterable, filter=None):
        self.expr, self.var, self.iterable, self.filter = expr, var, iterable, filter
    def to_ast(self) ->'ast.ListComp':
        return ASTUtils.ast_list_comprehension(self.expr, self.var, self.iterable, filter=self.filter)
class AbstractGenerator(AbstractExpr):
    __tag__ = 'Generator'
    __slots__ = ['expr', 'var', 'iterable', 'filter']
    def __init__(self, expr, var, iterable, filter=None):
        self.expr, self.var, self.iterable, self.filter = expr, var, iterable, filter
    def to_ast(self) ->'ast.GeneratorExp':
        return ASTUtils.ast_generator(self.expr, self.var, self.iterable, filter=self.filter)
class AbstractSetComp(AbstractExpr):
    __tag__ = 'SetComp'
    __slots__ = ['expr', 'var', 'iterable', 'filter']
    def __init__(self, expr, var, iterable, filter=None):
        self.expr, self.var, self.iterable, self.filter = expr, var, iterable, filter
    def to_ast(self) ->'ast.SetComp':
        return ASTUtils.ast_set_comprehension(self.expr, self.var, self.iterable, filter=self.filter)
class AbstractDictComp(AbstractExpr):
    __tag__ = 'DictComp'
    __slots__ = ['key_expr', 'value_expr', 'var', 'iterable', 'filter']
    def __init__(self, key_expr, value_expr, var, iterable, filter=None):
        self.key_expr, self.value_exp, self.var, self.iterable, self.filter = key_expr, value_expr, var, iterable, filter
    def to_ast(self) -> 'ast.DictComp':
        return ASTUtils.ast_dict_comprehension(self.key_expr, self.value_exp, self.var, self.iterable, filter=self.filter)

class AbstractArgSpec(AbstractExpr):
    __tag__ = 'ArgSpec'
    __slots__ = ['args', 'kwargs']
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
    def to_ast(self) ->'ast.arguments':
        return ASTUtils.ast_arglist((self.args, self.kwargs))
    def __repr__(self):
        return "{}({}, {})".format(
            type(self).__name__,
            self.args,
            self.kwargs
        )

class AbstractLambda(AbstractExpr):
    __tag__ = 'Lambda'
    __slots__ = ['spec', 'body']
    def __init__(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], AbstractArgSpec):
            self.spec = args[0]
        else:
            self.spec = AbstractArgSpec(*args, **kwargs)
        self.body = None
    def __call__(self, *args, **kwargs):
        if self.body is None:
            if len(kwargs) == 0:
                if len(args) > 1:
                    args = [AbstractList(*args)[-1]]
                self.body = args[0]
                return self
            raise ValueError("Lambda expression has no body yet...")
        return super().__call__(*args, **kwargs)
    def to_ast(self) ->'ast.Lambda':
        if self.body is None:
            raise ValueError("Lambda expression has no body yet...")
        return ASTUtils.ast_lambda(self.spec, self.body)
    def __repr__(self):
        return "{}({})({})".format(
            type(self).__name__,
            self.spec,
            self.body
        )

class AbstractIfExp(AbstractExpr):
    __tag__ = 'If'
    __slots__ = ['test', 'body', 'else_branch']
    def __init__(self, test, body, orelse=None):
        self.test, self.body, self.else_branch = test, body, orelse
    def orelse(self, orelse):
        self.else_branch = orelse
    def to_ast(self):
        if self.else_branch is None:
            raise ValueError("IfExp needs an else branch")
        return ASTUtils.ast_ternary(self.test, self.body, self.else_branch)

# def AbstractDecorator(abs_fun)

# TODO: Eventually I'll need proper module support (`for`, `def`, `class`) so I can "compile" programs against a stack

class Abstract:
    """
    Provides a namespace for the different abstract classes
    """

    @classmethod
    def vars(cls, *spec, symbol_type=None):
        if symbol_type is None:
            symbol_type = AbstractName
        if not isinstance(spec[0], str):
            spec = spec[0]
        if len(spec) == 1:
            spec = spec[0].split()
        return [symbol_type(x) for x in spec]

    Expr = AbstractExpr
    Name = AbstractName

    Lambda = AbstractLambda

    List = AbstractList
    Tuple = AbstractTuple
    Set = AbstractSet
    Dict = AbstractDict

    # Lambda = AbstractLambda

#     @classmethod
#     def name_redir(self, item):
#         return self.Name[item]
# Abstract.__getitem__ = Abstract.name_redir