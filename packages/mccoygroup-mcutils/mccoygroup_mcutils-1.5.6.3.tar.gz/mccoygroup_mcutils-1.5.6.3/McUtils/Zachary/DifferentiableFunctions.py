
import abc
import numpy as np
import copy

from .. import Numputils as nput
from .. import Iterators as itut
from .. import Coordinerds as coords

from .Taylor import FunctionExpansion

__all__ = [
    "DifferentiableFunction",
    "PolynomialFunction",
    "MorseFunction",
    "CoordinateFunction"
]

class DifferentiableFunction(metaclass=abc.ABCMeta):
    def __init__(self, inds=None):
        self.inds = inds # the application inds

    def reindex(self, idx_perm):
        # if self.inds is None: self.inds = [0] # this is the most reasonable default...?
        if self.inds is None: return self
        new = copy.copy(self)
        idx_perm = np.asanyarray(idx_perm)
        new.inds = [np.where(idx_perm == i)[0][0] for i in self.inds] #TODO: find a cleaner 'find'
        return new

    def get_consistent_inds(self, funcs:'list[DifferentiableFunction]'):
        inds = [f.inds for f in funcs if f.inds is not None]
        if len(inds) == 0: return None, funcs
        new_inds = np.unique(np.concatenate(inds))
        new_funcs = [f.reindex(new_inds) for f in funcs]
        return new_inds, new_funcs

    def __call__(self, coords, order=0):
        coords = np.asanyarray(coords)
        if self.inds is None:
            return self.evaluate(coords, order=order)
        else:
            subc = coords[..., self.inds]
            subtensors = self.evaluate(subc, order=order)
            expansions = subtensors[:1]
            base_shape = coords.shape[:-1]
            coords_shape = expansions[0].shape[len(base_shape):]
            ncoords = coords.shape[-1]
            for n,s in enumerate(subtensors[1:]):
                t = np.zeros(base_shape + (ncoords,) * (n+1) + coords_shape, dtype=s.dtype)
                if not nput.is_numeric(s):
                    idx = (...,) + np.ix_(*[self.inds]*(n+1)) + (slice(None),) * len(coords_shape)
                    t[idx] = s
                expansions.append(t)
            return expansions

    @abc.abstractmethod
    def evaluate(self, coords, order=0) -> list[np.ndarray]:
        ...

    @abc.abstractmethod
    def get_children(self):
        ...

    def __add__(self, other):
        if isinstance(other, DifferentiableFunction):
            if isinstance(self, FunctionSum):
                if isinstance(other, FunctionSum):
                    return FunctionSum(self.funcs + other.funcs)
                else:
                    return FunctionSum(self.funcs + [other])
            elif isinstance(other, FunctionSum):
                return FunctionSum([self] + other.funcs)
            else:
                return FunctionSum([self, other])
        else:
            return ConstantShiftedFunction(self, other)
    def __radd__(self, other):
        return self + other
    def __mul__(self, other):
        if isinstance(other, DifferentiableFunction):
            if isinstance(self, FunctionProduct):
                if isinstance(other, FunctionProduct):
                    return FunctionProduct(self.funcs + other.funcs)
                else:
                    return FunctionProduct(self.funcs + [other])
            elif isinstance(other, FunctionProduct):
                return FunctionProduct([self] + other.funcs)
            else:
                return FunctionProduct([self, other])
        else:
            return ConstantScaledFunction(self, other)
    def __truediv__(self, other):
        if isinstance(other, DifferentiableFunction):
            if isinstance(self, FunctionProduct):
                if isinstance(other, FunctionProduct):
                    return FunctionProduct(self.funcs + [f.flip() for f in other.funcs])
                else:
                    return FunctionProduct(self.funcs + [other.flip()])
            elif isinstance(other, FunctionProduct):
                return FunctionProduct([self] + [f.flip() for f in other.funcs])
            else:
                return FunctionProduct([self, other.flip()])
        else:
            return ConstantScaledFunction(self, 1/other)
    def __rtruediv__(self, other):
        return self.flip() * other
    def __rmul__(self, other):
        return self * other
    def __neg__(self):
        if isinstance(self, NegatedFunction):
            return self.func
        else:
            return NegatedFunction(self)

    def flip(self):
        return ReciprocalFunction(self)

class ConstantScaledFunction(DifferentiableFunction):
    def __init__(self, func:DifferentiableFunction, scaling, inds=None):
        if inds is None: inds = func.inds
        super().__init__(inds=inds)
        self.func = func
        self.scaling = scaling
    def evaluate(self, coords, order=0) -> list[np.ndarray]:
        expansion = self.func(coords, order=order)
        return [self.scaling*e for e in expansion]
    def get_children(self):
        return [self.func]

class ConstantShiftedFunction(DifferentiableFunction):
    def __init__(self, func:DifferentiableFunction, shift, inds=None):
        if inds is None: inds = func.inds
        super().__init__(inds=inds)
        self.func = func
        self.shift = shift
    def evaluate(self, coords, order=0) -> list[np.ndarray]:
        expansion = self.func(coords, order=order)
        return [self.shift + expansion[0]] + expansion[1:]
    def get_children(self):
        return [self.func]

class NegatedFunction(DifferentiableFunction):
    def __init__(self, func:DifferentiableFunction, inds=None):
        if inds is None: inds = func.inds
        super().__init__(inds=inds)
        self.func = func
    def evaluate(self, coords, order=0) -> list[np.ndarray]:
        expansion = self.func(coords, order=order)
        return [-e for e in expansion]
    def get_children(self):
        return [self.func]

class FunctionSum(DifferentiableFunction):
    def __init__(self, funcs: list[DifferentiableFunction], inds=None):
        if inds is None: inds, funcs = self.get_consistent_inds(funcs)
        super().__init__(inds=inds)
        self.funcs = funcs
    def evaluate(self, coords, order=0) -> list[np.ndarray]:
        expansions = [f(coords, order=order) for f in self.funcs]
        return [
            sum(e[i] for e in expansions)
            for i in range(order+1)
        ]
    def get_children(self):
        return self.funcs

class FunctionProduct(DifferentiableFunction):
    def __init__(self, funcs:list[DifferentiableFunction], inds=None):
        if inds is None: inds, funcs = self.get_consistent_inds(funcs)
        super().__init__(inds=inds)
        self.funcs = funcs

    def evaluate(self, coords, order=0):
        expansions = [
            f(coords, order=order)
            for f in self.funcs
        ]

        base_shape = coords.shape[:-1]
        ncs = len(base_shape)
        nvals = len(expansions[0][0].shape[ncs:])
        # we move these axes to the back of the tensor for constructing the products
        new_exps = []
        for subexp in expansions:
            sube = []
            for e in subexp:
                for _ in range(nvals):
                    e = np.moveaxis(e, -1, ncs)
                sube.append(e)
            new_exps.append(sube)

        riffs = list(itut.riffle(new_exps, ['x']*len(expansions)))
        derivs = nput.tensorops_deriv(
            *riffs,
            order=order,
            shared=ncs + nvals
        )

        finals = []
        for d in derivs:
            for _ in range(nvals):
                d = np.moveaxis(d, ncs, -1)
            finals.append(d)

        return finals
    def get_children(self):
        return self.funcs

class FunctionComposition(DifferentiableFunction):
    def __init__(self, outer_func, inner_funcs:list[DifferentiableFunction], inds=None):
        if inds is None:
            inds, funcs = self.get_consistent_inds([outer_func] + list(inner_funcs))
            outer_func, inner_funcs = funcs[0], funcs[1:]
        super().__init__(inds=inds)
        self.outer_func = outer_func
        self.inner_funcs = list(inner_funcs)
    def evaluate(self, coords, order=0):
        inner_expansions = [
            f(coords, order=order)
            for f in self.inner_funcs
        ]
        inner_expansion = [
            np.array([e[i] for e in inner_expansions])
            for i in range(order+1)
        ]
        outer_expansion = self.outer_func(inner_expansion[0], order=order)

        if order > 0:
            derivs = nput.tensordot_deriv(
                inner_expansion[1:],
                outer_expansion[1:],
                order=order
            )
        else:
            derivs = []

        return outer_expansion[:1] + derivs
    def get_children(self):
        return [self.outer_func] + self.inner_funcs

class ReciprocalFunction(DifferentiableFunction):
    def __init__(self, func: DifferentiableFunction, inds=None):
        if inds is None: inds = func.inds
        super().__init__(inds=inds)
        self.func = func

    def evaluate(self, coords, order=0) -> list[np.ndarray]:
        expansion = self.func(coords, order=order)
        return nput.scalarinv_deriv(expansion, order)

    def get_children(self):
        return [self.func]

class PolynomialFunction(DifferentiableFunction):
    def __init__(self, taylor_poly:FunctionExpansion, inds=None):
        super().__init__(inds=inds)
        self.poly = taylor_poly

    @classmethod
    def from_coefficients(cls,
                          coeffs,
                          center=None,
                          ref=0,
                          inds=None
                          ):
        return cls(
            FunctionExpansion(coeffs, center=center, ref=ref),
            inds=inds
        )

    def evaluate(self, coords, order=0):
        return self.poly.expand(coords, order=order)
    def get_children(self):
        return []

class UnivariateFunction(DifferentiableFunction):

    def __init__(self, term_generator, *, inds=None):
        super().__init__(inds=inds)
        self.term_generator = term_generator
    def evaluate(self, coords, order=0) -> list[np.ndarray]:
        nshared = len(coords.shape[:-1])
        coords = coords[..., 0]

        expansions = []
        for n in range(order+1):
            expansions.append(
                np.expand_dims(
                    self.term_generator(coords, order=n, previous_terms=expansions),
                    list(range(nshared, nshared+n))
                )
            )

        return expansions

class Poly1D(UnivariateFunction):
    def __init__(self, coeffs, ref, center, inds=None):
        super().__init__(self.evaluate_term, inds=inds)
        self.coeffs = coeffs
        self.center = center
        self.ref = ref

    @classmethod
    def fac_pow(cls, k, n):
        return np.prod(np.arange(k+1, k+n+1))

    def evaluate_term(self, r, order=0, previous_terms=None):
        disp = r - self.center
        n = order

        if order == 0:
            return self.ref + sum(
                d * ( disp**(k+1) )
                for k,d in enumerate(self.coeffs)
            )
        else:
            return sum(
                (self.fac_pow(k, n)*d) * ( disp**(k) )
                for k,d in enumerate(self.coeffs[n-1:])
            )
    def get_children(self):
        return []

class MorseFunction(UnivariateFunction):
    def __init__(self, *, de, a, re, inds=None):
        super().__init__(self.evaluate_term, inds=inds)
        self.de = de
        self.a = a
        self.re = re

    @classmethod
    def from_anharmonicity(cls, w, wx, g, re, inds=None):
        wx = np.abs(wx)
        de = (w ** 2) / (4 * wx)
        a = np.sqrt(2 * wx / g)

        return cls(de=de, a=a, re=re, inds=inds)

    def evaluate_term(self, r, order=0, previous_terms=None):
        de = self.de
        a = self.a
        re = self.re
        n = order

        if order == 0:
            return de*(1 - np.exp(-a*(r-re)))**2
        else:
            return (
                    ((-1) ** (n + 1) * 2 * a ** n * de)
                    * np.exp(-2 * a * (r - re))
                    * (np.exp(a * (r - re)) - (2 ** (n - 1)))
            )

    def get_children(self):
        return []

class Sin(UnivariateFunction):
    def __init__(self, *, n=1, l=1, inds=None):
        super().__init__(self.evaluate_term, inds=inds)
        self.n = n
        self.l = l

    def evaluate_term(self, r, order=0, previous_terms=None):
        scaling = (self.n/self.l)
        return scaling ** (order) * np.sin(order*np.pi/2 + scaling * r)

    def get_children(self):
        return []

class Cos(UnivariateFunction):
    def __init__(self, *, n=1, l=1, inds=None):
        super().__init__(self.evaluate_term, inds=inds)
        self.n = n
        self.l = l

    def evaluate_term(self, r, order=0, previous_terms=None):
        scaling = (self.n/self.l)
        return scaling ** (order) * np.cos(order*np.pi/2 + scaling * r)

    def get_children(self):
        return []

class Exp(UnivariateFunction):
    def __init__(self, *, s=1, inds=None):
        super().__init__(self.evaluate_term, inds=inds)
        self.s = s

    def evaluate_term(self, r, order=0, previous_terms=None):
        return self.s ** (order) * np.exp(self.s * r)

    def get_children(self):
        return []

class CoordinateFunction:
    def __init__(self, conversion, expr:DifferentiableFunction):
        self.conversion, self.coordinate_conversion = self.canonicalize_conversion(conversion)
        self._conv = None
        self.expr = expr

    @classmethod
    def canonicalize_conversion(cls, conv):
        if callable(conv):
            return conv, conv
        else:
            if nput.is_numeric(conv[0]):
                conv = [conv]
            canon = [coords.canonicalize_internal(c) for c in conv]
            return canon, nput.internal_conversion_function(canon)

    def __call__(self, coords, order=0, preconverted=False, reexpress=True):
        # subexprs that only map to some coordinated need to map correctly!
        # not sure how best to handle that though...
        if not preconverted:
            coord_expansion = self.coordinate_conversion(coords, order=0 if not reexpress else order)
        else:
            coord_expansion = [coords]
            reexpress = False
        base_expr = self.expr(coord_expansion[0], order=order)
        if reexpress:
            expansion_vals = base_expr[:1] + (
                nput.tensor_reexpand(coord_expansion[1:], base_expr[1:], order)
                    if order > 0 else
                []
            )
        else:
            expansion_vals = base_expr
        return coord_expansion, expansion_vals

    @classmethod
    def merge_conversion_functions(cls, conv_1, conv_2):
        if conv_1 is conv_2:
            return None, conv_1

        if callable(conv_1) or callable(conv_2):
            raise ValueError("can't manage merging callable conversions")

        c1_disp = set(conv_1)
        new_conv = conv_1 + [c for c in conv_2 if c not in c1_disp]
        reindexing = np.full(len(new_conv), -1)
        for n,c in enumerate(conv_2):
            i = new_conv.index(c)
            reindexing[i] = n
        return reindexing, new_conv

    def __add__(self, other):
        if isinstance(other, CoordinateFunction):
            reindexing, conv = self.merge_conversion_functions(self.conversion, other.conversion)
            return type(self)(
                conv,
                self.expr + other.expr.reindex(reindexing)
            )
        else:
            return type(self)(self.conversion, self.expr + other)
    def __radd__(self, other):
        return self + other
    def __mul__(self, other):
        if isinstance(other, CoordinateFunction):
            reindexing, conv = self.merge_conversion_functions(self.conversion, other.conversion)
            return type(self)(
                conv,
                self.expr * other.expr.reindex(reindexing)
            )
        else:
            return type(self)(self.conversion, self.expr * other)
    def __rmul__(self, other):
        return self * other
    def __truediv__(self, other):
        if isinstance(other, CoordinateFunction):
            reindexing, conv = self.merge_conversion_functions(self.conversion, other.conversion)
            return type(self)(
                conv,
                self.expr / other.expr.reindex(reindexing)
            )
        else:
            return type(self)(self.conversion, self.expr / other)
    def __rtruediv__(self, other):
        return 1/self * other
    def __neg__(self):
        return type(self)(self.conversion, -self.expr)

    @classmethod
    def polynomial(cls, coord_spec, *, coeffs, center, ref):
        if nput.is_numeric(coord_spec[0]):
            fun = Poly1D(
                [np.array([c]).flatten()[0] for c in coeffs],
                ref=np.array([ref]).flatten()[0],
                center=np.array([center]).flatten()[0],
                inds=[0]
            )
        else:
            fun = PolynomialFunction.from_coefficients(
                coeffs=coeffs,
                center=center,
                ref=ref,
                inds=list(range(len(coord_spec)))
            )
        return cls(coord_spec, fun)

    @classmethod
    def morse(cls, coord, *, re, a=None, de=None, w=None, wx=None, g=None):
        if w is not None:
            fun = MorseFunction.from_anharmonicity(w=w, wx=wx, g=g, re=re, inds=[0])
        else:
            fun = MorseFunction(a=a, de=de, re=re, inds=[0])
        return cls([coord], fun)
    @classmethod
    def sin(cls, coord, *, n=1, l=1):
        return cls([coord], Sin(n=n, l=l, inds=[0]))
    @classmethod
    def cos(cls, coord, *, n=1, l=1):
        return cls([coord], Cos(n=n, l=l, inds=[0]))
    @classmethod
    def exp(cls, coord, *, s=1):
        return cls([coord], Exp(s=s, inds=[0]))


# class SympyFunction(DifferentiableFunction):
#     def __init__(self, sympy_expr):
#         self.expr = sympy_expr
#         self.coords = ...

