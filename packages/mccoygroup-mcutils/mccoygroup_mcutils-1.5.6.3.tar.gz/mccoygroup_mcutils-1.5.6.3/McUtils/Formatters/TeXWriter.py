
import abc, numpy as np, io, weakref
from .. import Devutils as dev
from .. import Numputils as nput
from .TableFormatters import TableFormatter
from ..Misc.Symbolics import Abstract

__all__ = [
    "TeX"
]

class TeXWriter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def format_tex(self, context=None):
        ...

    real_digits = 3
    @classmethod
    def dispatch_format(cls, b, context):
        if isinstance(b, TeXWriter) or hasattr(b, 'format_tex'):
            return b.format_tex(context)
        elif isinstance(b, (float, np.floating)):
            return ('{:.'+str(cls.real_digits)+'f}').format(b)
        elif isinstance(b, np.ndarray):
            return TeXArray(b).format_tex(context)
        elif isinstance(b, (list, tuple)):
            if isinstance(b[0], (list, tuple)):
                return TeXArray(b).format_tex(context)
            else:
                return TeXRow(b).format_tex(context)
        else:
            return str(b)

    def as_expr(self):
        return TeXExpr(self)

class TeXContextManager:
    default_contexts = weakref.WeakValueDictionary()
    @classmethod
    def resolve(cls, name='default'):
        if name not in cls.default_contexts:
            ctx = cls()
            cls.default_contexts[name] = ctx
        return cls.default_contexts[name]

    def __init__(self):
        self.context_stack = []
    def subcontext(self, cls):
        return cls(self)
    def set_context(self, ctx):
        self.context_stack.append(ctx)
        return ctx
    def leave_context(self):
        self.context_stack.pop()
    @property
    def context(self):
        if len(self.context_stack) == 0:
            return None
        else:
            return self.context_stack[-1]
    @property
    def math_mode(self):
        return isinstance(self.context, MathContext)

class TeXContext:
    def __init__(self, manager:TeXContextManager):
        self.manager = manager
    def __enter__(self):
        self.manager.set_context(self)
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.manager.leave_context()
class MathContext(TeXContext):
    ...

class TeXBlock(TeXWriter):
    tag = None
    modifier = None
    modifier_type = '[]'
    separator = '\n'
    context = None
    label_header = None
    def __init__(self,
                 body=None, *,
                 tag=None,
                 modifier=None,
                 modifier_type=None,
                 separator=None,
                 context=None,
                 label=None
                 ):
        self.body = body
        if tag is None:
            tag = self.tag
        self.tag = tag
        if modifier is None:
            modifier = self.modifier
        self.modifier = modifier
        if modifier_type is None:
            modifier_type = self.modifier_type
        self.modifier_type = modifier_type
        if separator is None:
            separator = self.separator
        self.sep = separator
        if context is None:
            context = self.context
        self.ctx = context
        self.label = label
    def prep_body(self, context=None):
        if self.body is None:
            params = []
        elif isinstance(self.body, (list, tuple)):
            params = [self.dispatch_format(b, context) for b in self.body]
        else:
            params = [self.dispatch_format(self.body, context)]
        if self.label is not None:
            label = self.label
            if self.label_header is not None and ':' not in label:
                label = self.label_header + ':' + label
            params = params + ['\\label{' + label + "}"]
        return params
    @classmethod
    def construct_modified_tag(self, tag, mod, mod_type='[]'):
        header = "\\begin{"+str(tag)+"}"
        if mod is not None:
            if isinstance(mod_type, str):
                l, r = mod_type
                header = header + l + mod + r
            else:
                bits = []
                for m,t in zip(mod, mod_type):
                    l, r = t
                    bits.append(l + m + r)
                header = header + "".join(bits)
        return header, "\\end{"+str(tag)+"}"
    def construct_header_footer(self):
        return self.construct_modified_tag(self.tag, self.modifier, self.modifier_type)
    def format_body(self, body_params):
        header, footer = self.construct_header_footer()
        if self.tag is not None:
            body_params = [header] + body_params + [footer]
        return self.sep.join(body_params)
    def format_tex(self, context=None):
        if self.ctx is not None:
            if context is None:
                context = TeXContextManager.resolve()
            elif isinstance(context, str):
                context = TeXContextManager.resolve(context)

        if self.ctx is not None:
            with context.subcontext(self.ctx):
                body_args = self.prep_body(context)
        else:
            body_args = self.prep_body(context)
        return self.format_body(body_args)
    def __call__(self, body):
        return type(self)(
            body,
            tag=self.tag,
            modifier=self.modifier,
            modifier_type=self.modifier_type,
            separator=self.separator,
            context=self.ctx,
            label=self.label
        )

class TeXRow(TeXBlock):
    tag = None
    separator = ' '

class TeXArray(TeXBlock):
    tag = 'tabular'
    modifier_type = '{}'
    separator = '\n'
    array_separator = " & "
    array_newline = " \\\\\n"
    header_separator = "\n\\hline \\\\[-4ex]\n"
    header_lines = "\n\\hline \\\\[-4ex]"
    footer_lines = "\\hline \\\\[-4ex]\n"
    number_format = "{:8.3f}"
    def __init__(self, headers_or_body, body=None, *,
                 alignment='auto',
                 number_format="{:8.3f}",
                 content_join=None,
                 column_join=None,
                 row_join=None,
                 separator=None,
                 header_spans=None,
                 header_alignments=None,
                 resizeable=False,
                 **opts):
        self.resizeable = resizeable
        if resizeable:
            self.tag = 'tabularx'
            self.modifier_type = ["{}", "{}"]
            self.array_separator = " && "

        if body is None:
            body = headers_or_body
            headers_or_body = None
        self.headers = headers_or_body
        self.alignment = alignment
        if content_join is None:
            content_join = self.header_separator
        opts['content_join'] = content_join
        if row_join is None:
            row_join = self.array_newline
        opts['row_join'] = row_join
        if column_join is None:
            column_join = self.array_separator
        opts['column_join'] = column_join
        if separator is None:
            separator = ""
        opts['separator'] = separator
        self.format_opts, opts = dev.OptionsSet(opts).split(TableFormatter)
        self.format = number_format
        self.header_spans = header_spans
        self.header_alignments = header_alignments
        super().__init__(
            body,
            **opts
        )

    def construct_alignment_spec(self, body):
        if isinstance(body, np.ndarray):
            if np.issubdtype(body.dtype, np.integer):
                spec = "c" * body.shape[1]
            elif np.issubdtype(body.dtype, np.floating):
                spec = 'r' * body.shape[1]
            else:
                spec = 'c' * body.shape[1]
        else:
            specs = []
            for array_row in body:
                for i, e in enumerate(array_row):
                    if i >= len(specs):
                        specs = specs + ['r']
                    if (
                            specs[i] != 'c' and
                            not isinstance(e, (float, np.floating)) and
                            not (isinstance(e, str) and len(e.strip()) == 0)
                    ):
                        specs[i] = 'c'
            spec = "".join(specs)
        return spec
    def construct_header_footer(self):
        body = self.body
        if isinstance(body, np.ndarray) and not np.issubdtype(body.dtype, (np.integer, np.floating)):
            body = body.tolist()
        if self.alignment is not None and self.modifier is None:
            mod = self.construct_alignment_spec(body)
        else:
            mod = self.modifier
        if self.resizeable:
            mod = ['\\textwidth', "X".join(mod)]
        header, footer = self.construct_modified_tag(self.tag, mod, self.modifier_type)
        return header + self.header_lines, self.footer_lines + footer

    def format_numpy_array(self, array):
        int_digits = int(np.floor(np.log10(np.max(np.abs(array))))) + 1
        with io.StringIO() as stream:
            if np.issubdtype(array.dtype, np.floating):
                real_digits = self.real_digits
            else:
                real_digits = 0
            total_digits = int_digits + real_digits + 2
            fmt = '%{}.{}f'.format(total_digits, real_digits)
            np.savetxt(stream, array, fmt=fmt, delimiter=self.array_separator, newline=self.array_newline)
            stream.seek(0)
            return stream.read()
    def format_mixed_array(self, array, context=None):
        row_padding = []
        string_array = []
        for array_row in array: # convert and track padding
            conv_row = []
            for i,c in enumerate(array_row):
                s = self.dispatch_format(c, context)
                conv_row.append(s)
                if i >= len(row_padding):
                    row_padding = row_padding + [0]
                if len(s) > row_padding[i]:
                    row_padding[i] = len(s)
            string_array.append(conv_row)
        return self.array_newline.join(
            self.array_separator.join(" " * (row_padding[i] - len(s)) + s for i,s in enumerate(string_row))
            for string_row in string_array
        )
    def prep_body(self, context=None, headers=None, body=None):
        if body is None:
            body = self.body
        if headers is None:
            headers = self.headers
        if headers is None:
            if len(body) == 2 and not all(dev.is_atomic(b) for b in body[0]):
                headers, body = body
        opts = self.format_opts
        if 'column_formats' in opts:
            opts = opts.copy()
            column_formats = opts.pop('column_formats')
        else:
            column_formats = [
                ""
                    if not nput.is_numeric(o) else
                "{:>.0f}"
                    if nput.is_int(o) else
                self.format
                for o in body[0]
            ]

        if headers is not None:
            if dev.is_list_like(headers[0]):
                headers = [
                    [
                        h.format_tex(context=context)
                        if isinstance(h, TeXWriter) else
                        h
                        for h in hl
                    ]
                    for hl in headers
                ]
                if self.header_spans is not None:
                    alignments = self.header_alignments
                    if alignments is None:
                        alignments = [
                            ["c"] * len(hl)
                            for hl in headers
                        ]

                    _blocks = []
                    for lhl, lhs, lhc in zip(headers, self.header_spans, alignments):
                        _ = []
                        for hl, hs, hc in zip(lhl, lhs, lhc):
                            _.append(
                                TeXMulticolumn(2*hs - 1, hc, hl).format_tex(context)
                                    if hs > 1 else
                                hl
                            )
                        _blocks.append(_)
                    headers = _blocks
            else:
                headers = [
                    h.format_tex(context=context)
                        if isinstance(h, TeXWriter) else
                    h
                    for h in headers
                ]
                if self.header_spans is not None:
                    alignments = self.header_alignments
                    if alignments is None:
                        alignments = ["c"] * len(headers)

                    _ = []
                    for hl, hs, hc in zip(headers, self.header_spans, alignments):
                        _.append(
                            TeXMulticolumn(hs, hc, hl).format_tex(context)
                                if hs > 1 else
                            hl
                        )
                    headers = _

        wtf = TableFormatter(
            column_formats,
            headers=headers,
            header_spans=self.header_spans,
            **self.format_opts
        ).format(body) + self.array_newline.strip()
        return [
            wtf
        ]

class TeXTable(TeXBlock):
    tag = 'table'
    modifier = 'ht'
    modifier_type = '[]'
    separator = '\n'
    # array_separator = " & "
    # array_newline = " \\\\\n"
    def __init__(self,
                 headers_or_body,
                 body=None,
                 width=1,
                 caption=None,
                 # label=None,
                 resizeable=False,
                 number_format=None,
                 header_spans=None,
                 **etc
                 ):
        if body is None:
            body = headers_or_body
            headers_or_body = None
        body = [
            TeXArray(headers_or_body, body,
                     number_format=number_format,
                     resizeable=resizeable,
                     header_spans=header_spans
                     )
                if not isinstance(body, TeXWriter) else
            body
        ]
        self.width = width
        self.caption = caption
        # self.label = label
        super().__init__(body, **etc)

    def prep_body(self, context=None, body=None):
        if body is None:
            body = self.body

        base = [
            TeXBlock(
                TeXBlock(
                    body,
                    tag='minipage',
                    modifier_type=["[]", "{}"],
                    modifier=['c', f'{self.width} \\textwidth']
                ),
                tag="center"
            )
        ]
        if self.caption is not None:
            base.append(
                TeXFunction(self.caption, function_name="caption")
                    if not isinstance(self.caption, TeXWriter) else
                self.caption
            )
        if self.label is not None:
            base.append(
                TeXFunction(self.label, function_name="label")
                    if not isinstance(self.label, TeXWriter) else
                self.label
            )
        return [
            b.format_tex(context=context)
            for b in base
        ]

class TeXFunction(TeXWriter):
    function_name = None
    def __init__(self, *args, function_name=None):
        if function_name is None:
            function_name = self.function_name
        self.function_name = function_name
        self.args = args
    def format_tex(self, context=None):
        tag = "\\" + self.function_name
        body = ["{" + self.dispatch_format(b, context) + "}" for b in self.args]
        return tag + "".join(body)

class TeXMulticolumn(TeXFunction):
    function_name = 'multicolumn'
    def __init__(self, width, fmt, body):
        super().__init__(width, fmt, body)

class TeXBold(TeXFunction):
    function_name = 'textbf'

class TeXBracketed(TeXWriter):
    brackets = (None, None)
    def __init__(self, body, brackets=None):
        self.body = body
        if brackets is None:
            brackets = self.brackets
        self.brackets = brackets
    def format_tex(self, context=None):
        l, r = self.brackets
        base = self.dispatch_format(self.body, context)
        return l + base + r

class TeXParenthesized(TeXBracketed):
    brackets = ('\\left(', '\\right)')

class TeXEquation(TeXBlock):
    tag = 'equation'
    context = MathContext
    label_header = 'eq'

########################################################################################################################
#
#       TeX Equations
#
#

#region Equations
class TeXNode(Abstract.Expr):
    def to_ast(self):
        raise NotImplementedError("TeXNodes are for formatting only")
class TeXSuperscript(TeXNode):
    __tag__ = "Superscript"
    __slots__ = ['obj', 'index']
    def __init__(self, obj, index):
        self.obj = obj
        self.index = index
class TeXApply(TeXNode):
    __tag__ = "Apply"
    __slots__ = ['function', 'argument']
    def __init__(self, function, argument):
        self.function = function
        self.argument = argument
class TeXSymbol(Abstract.Name):
    def __call__(self, *args):
        return TeXApply(self, args)

class TeXExpr(TeXWriter):

    @classmethod
    def name(cls, s):
        if isinstance(s, str) and len(s) > 1:
            s = "\\" + s
        return cls(Abstract.Name(s))
    @classmethod
    def symbol(cls, s):
        if isinstance(s, str) and len(s) > 1:
            s = "\\" + s
        return cls(TeXSymbol(s))

    # a, b, c, f, g, i, j, k, l, m, n, x, y, z = Abstract.vars(
    #     'a', 'b', 'c', 'f', 'g', 'i', 'j', 'k', 'l', 'm', 'n',
    #     'x', 'y', 'z'
    # )
    # omega, nu, tau, psi, phi, sigma = Abstract.vars(
    #     '\\omega', '\\nu', '\\tau', '\\psi', '\\phi', '\\sigma'
    # )
    # Omega, Nu, Tau, Psi, Phi, Sigma = Abstract.vars(
    #     '\\Omega', '\\Nu', '\\Tau', '\\Psi', '\\Phi', '\\Sigma'
    # )
    # sum, int, prod, bra, ket, braket = Abstract.vars(
    #     '\\sum', '\\int', '\\prod',
    #     '\\bra', '\\ket', '\\braket',
    #     symbol_type=TeXSymbol
    # )

    def __init__(self, body):
        if not isinstance(body, Abstract.Expr):
            body = Abstract.Name(body)
        self.body = body
    def __add__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body + other)
    def __radd__(self, other):
        return type(self)(other + self.body)
    def __mul__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body * other)
    def __rmul__(self, other):
        return type(self)(other * self.body)
    def __pow__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body ** other)
    def __neg__(self):
        return type(self)(-self.body)
    def __xor__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body ^ other)
    def __or__(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body | other)
    def __getitem__(self, item):
        return type(self)(self.body[item])

    def Equals(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.Equals(other))
    Eq = Equals
    def LessThan(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.LessThan(other))
    Lt = LessThan
    def LessEquals(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.LessEquals(other))
    LtE = LessEquals
    def GreaterThan(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.GreaterThan(other))
    Gt = GreaterThan
    def GreaterEquals(self, other):
        if isinstance(other, TeXExpr):
            other = other.body
        return type(self)(self.body.GreaterEquals(other))
    GtE = GreaterEquals

    @staticmethod
    def convert_name(name, converter):
        name = name.name
        if hasattr(name, 'format_tex'):
            name = name.format_tex()
        return name
    @staticmethod
    def convert_const(const, converter):
        return const.value
    @staticmethod
    def convert_call(call, converter):
        return "{}({})".format(
            converter(call.fn),
            ",".join(converter(k) for k in call.args)
        )
    @staticmethod
    def convert_superscript(op, converter):
        return "{}^{{{}}}".format(
            converter(op.obj),
            converter(op.index)
        )
    @staticmethod
    def convert_bitxor(op, converter):
        return "{}^{{{}}}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_power(op, converter):
        return "{}^{{{}}}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_subscript(op, converter):
        idx = op.index
        if isinstance(idx, slice):
            var = idx.start
            min = idx.stop
            max = idx.step
            if max is None:
                return "{}_{{{}={}}}".format(
                    converter(op.obj),
                    converter(var),
                    converter(min)
                )
            else:
                return "{}_{{{}={}}}^{{{}}}".format(
                    converter(op.obj),
                    converter(var),
                    converter(min),
                    converter(max)
                )
        else:
            return "{}_{{{}}}".format(
                converter(op.obj),
                converter(op.index)
            )
    @staticmethod
    def convert_add(op, converter):
        return "{}+{}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_sub(op, converter):
        return "{}-{}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_mul(op, converter):
        return "{} {}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_bitor(op, converter):
        return "{} {}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_div(op, converter):
        return "\\frac{{{}}{{{}}}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_eq(op, converter):
        return "{} = {}".format(
            converter(op.left),
            converter(op.right)
        )
    @staticmethod
    def convert_raw(obj, converter):
        if hasattr(obj, 'format_tex'):
            return obj.format_tex()
        else:
            return TeXBlock(obj, separator=", ").format_tex()

    @property
    def converter_dispatch(self):
        return {
            'Name':self.convert_name,
            'Const':self.convert_const,
            'Superscript':self.convert_superscript,
            'Subscript':self.convert_subscript,
            'Pow':self.convert_power,
            'BitXOr':self.convert_bitxor,
            'BitOr':self.convert_bitor,
            'Add':self.convert_add,
            'Sub':self.convert_sub,
            'Mul':self.convert_mul,
            'Div':self.convert_div,
            'Equals':self.convert_eq,
            None:self.convert_raw
        }

    def format_tex(self, context=None):
        if context is None:
            context = TeXContextManager.resolve()
        elif isinstance(context, str):
            context = TeXContextManager.resolve(context)

        pad_dollars = not context.math_mode
        with context.subcontext(MathContext):
            expr = self.body.transmogrify(
                self.converter_dispatch
            )
        if pad_dollars:
            expr = '${}$'.format(expr)

        return expr

#endregion

########################################################################################################################
#
#       Wrapper
#
#

class TeX:
    """
    Namespace for TeX-related utilities, someday might help with document prep from templates
    """

    Writer = TeXWriter

    Block = TeXBlock
    Row = TeXRow

    Expr = TeXExpr
    Symbol = TeXExpr.name
    Function = TeXExpr.symbol

    Array = TeXArray
    Table = TeXTable
    Equation = TeXEquation

    wrap_parens = TeXParenthesized

    bold = TeXBold

    @classmethod
    def Matrix(cls, mat, **kwargs):
        return cls.wrap_parens(cls.Array(mat, **kwargs))
