
import abc, numpy as np, typing, weakref, hashlib
import collections

from ...Numputils import vec_outer, vec_tensordot
from ...Combinatorics import IntegerPartitioner, UniquePermutations

__all__ = [
    'TensorDerivativeConverter',
    'TensorExpansionTerms',
    'TensorExpression'
]


class TensorExpression:
    def __init__(self, expr:'TensorExpression.Term|List', **vars):
        self.expr = expr
        self.vars = vars
        self._prims = None
    def eval(self, subs:dict=None, print_terms=False):
        if subs is None:
            subs = self.vars
        if subs is None:
            subs = {}
        prims = self.primitives
        cache = {}
        names = {p.name:p for p in prims}
        _ac = TensorExpression.Term._array_cache
        TensorExpression.Term._array_cache = {k:v for k,v in zip(_ac.keys(), _ac.values())}
        for k in subs.keys() & names.keys():
            p = names[k]
            v = subs[k]
            cache[p] = TensorExpression.Term._array_cache.get(p, None)
            TensorExpression.Term._array_cache[p] = v

        try:
            if isinstance(self.expr, TensorExpression.Term):
                res = self.expr.asarray(print_terms=print_terms)
                if isinstance(res, TensorExpression.ArrayStack):
                    res = res.array
            else: # depth-first evaluation
                dfs_queue = collections.deque([self.expr])
                stack = collections.deque()
                sentinel = object() # for reconstructing arrays
                res = None # by construction we should never use this...?
                while dfs_queue:
                    e = dfs_queue.popleft()
                    # print("<<<<", id(e), str(e)[:25].replace("\n", ""))
                    if isinstance(e, TensorExpression.Term):
                        ar = e.asarray(print_terms=print_terms)
                        if isinstance(ar, TensorExpression.ArrayStack):
                            ar = ar.array
                        # print(ar.shape)
                        res.append(ar)
                    elif e is sentinel:
                        # print("  ="*10)
                        new_res = stack.pop()
                        if new_res is not None: # hit the bottom of the stack
                            new_res.append(res)
                            res = new_res
                        elif dfs_queue:
                            raise ValueError("sentinel at bad time")
                        else:
                            break
                    else:
                        stack.append(res)
                        res = []
                        # stick a sentinel in so we know when we've finished the array and can pop back out
                        dfs_queue.appendleft(sentinel)
                        # for sub_e in reversed(e):
                            # print("   >>>>", id(sub_e), str(sub_e)[:25].replace("\n", ""))
                        dfs_queue.extendleft(reversed(e))

        finally:
            TensorExpression.Term._array_cache = _ac
            # for p,v in cache.items():
            #     if v is None:
            #         del TensorExpression.Term._array_cache[p]
            #     else:
            #         TensorExpression.Term._array_cache[p] = v
        return res
    @property
    def primitives(self):
        if self._prims is None:
            self._prims = self.get_prims()
        return self._prims
    def walk(self, callback):
        bfs_queue = collections.deque([self.expr])
        visited = set()
        while bfs_queue:
            e = bfs_queue.popleft()
            if isinstance(e, TensorExpression.Term):
                if e not in visited:
                    bfs_queue.extend(c for c in e.children if isinstance(c, TensorExpression.Term))
                    callback(e)
                    visited.add(e)
            else:
                bfs_queue.extend(e) # flattening arrays
    def get_prims(self):
        kids = set()
        def add_if_prim(e):
            if isinstance(e, TensorExpression.Term) and len(e.children) == 0:
                kids.add(e)
        self.walk(add_if_prim)
        return kids
    def __repr__(self):
        return '{}({})'.format(type(self).__name__, self.expr)

    class ArrayStack:
        __slots__ = ['stack_shape', 'array']
        def __init__(self, shape, array):
            """
            :param shape: shape of the stack of arrays to thread over
            :type shape:
            :param array:
            :type array:
            """
            self.array = array
            self.stack_shape = shape
        def __hash__(self):
            buf = self.array.view(np.uint8)
            return hash(hashlib.sha1(buf).hexdigest())
        def __eq__(self, other):
            return (
                    type(other) is type(self)
                    and self.stack_shape == other.stack_shape
                    and np.all(self.array == other.array)
            )
        @staticmethod
        def _make_broadcastable(a1, a2, offset):
            if a1.ndim < a2.ndim:
                for _ in range(a2.ndim - a1.ndim):
                    a1 = np.expand_dims(a1, -1)
            elif a2.ndim < a1.ndim:
                for _ in range(a1.ndim - a2.ndim):
                    a2 = np.expand_dims(a2, offset)
            return a1, a2
        @classmethod
        def _pad_shape(cls, arr, other, stack_shape):
            ogs = other.shape
            for _ in stack_shape:
                other = np.expand_dims(other, 0)
            other = np.broadcast_to(other, stack_shape + ogs)
            return cls._make_broadcastable(arr, other, len(stack_shape))
        def __add__(self, other):
            if isinstance(other, TensorExpression.ArrayStack):
                a1, a2 = self._make_broadcastable(
                    self.array,
                    other.array,
                    other.stack_dim
                )
                return type(self)(self.stack_shape, a1+a2)
            elif isinstance(other, (int, float, np.integer, np.floating)):
                return type(self)(self.stack_shape, self.array + other)
            else:
                arr, other = self._pad_shape(self.array, other, self.stack_shape)
                return type(self)(self.stack_shape, arr + other)
        def __mul__(self, other):
            if isinstance(other, TensorExpression.ArrayStack):
                a1, a2 = self._make_broadcastable(
                    self.array,
                    other.array,
                    other.stack_dim
                )
                return type(self)(self.stack_shape, a1 * a2)
            elif isinstance(other, (int, float, np.integer, np.floating)):
                return type(self)(self.stack_shape, self.array * other)
            else:
                # print(">>>", self.array.shape, other.shape, self.stack_shape)
                arr, other = self._pad_shape(self.array, other, self.stack_shape)
                # print(arr.shape, other.shape, "<<<")
                return type(self)(self.stack_shape, arr * other)
        def __rmul__(self, other):
            return self*other
        def __pos__(self):
            return self
        def __neg__(self):
            return -1 * self
        def __truediv__(self, other):
            if isinstance(other, TensorExpression.ArrayStack):
                a1, a2 = self._make_broadcastable(
                    self.array,
                    other.array,
                    other.stack_dim
                )
                return type(self)(self.stack_shape, a1 / a2)
            elif isinstance(other, (int, float, np.integer, np.floating)):
                return type(self)(self.stack_shape, self.array / other)
            else:
                arr, other = self._pad_shape(self.array, other, self.stack_shape)
                return type(self)(self.stack_shape, arr / other)
        def __rtruediv__(self, other):
            return other * self.flip()
        def flip(self):
            return type(self)(self.stack_shape, 1/self.array)

        def __pow__(self, power, modulo=None):
            if isinstance(power, TensorExpression.ArrayStack):
                a1, a2 = self._make_broadcastable(
                    self.array,
                    power.array,
                    power.stack_dim
                )
                return type(self)(self.stack_shape, a1 ** a2)
            elif isinstance(power, (int, float, np.integer, np.floating)):
                return type(self)(self.stack_shape, self.array ** power)
            else:
                arr, power = self._pad_shape(self.array, power, self.stack_shape)
                return type(self)(self.stack_shape, arr ** power)

        @property
        def stack_dim(self):
            return len(self.stack_shape)
        @property
        def shape(self):
            return self.array.shape[self.stack_dim:]
        @property
        def ndim(self):
            return self.array.ndim - self.stack_dim
        def expand_dims(self, where):
            if isinstance(where, int):
                where = [where]
            t = self.array
            offset = self.stack_dim
            for i in where:
                if i >= 0:
                    i = offset + i
                t = np.expand_dims(t, i)
            return type(self)(self.stack_shape, t)

        def moveaxis(self, i, j):
            offset = self.stack_dim
            if i >= 0:
                i = offset + i
            if j >= 0:
                j = offset + j
            return type(self)(self.stack_shape, np.moveaxis(self.array, i, j))
        def tensordot(self, other, axes=None):
            if isinstance(other, TensorExpression.ArrayStack):
                other = other.array
            else:
                ogs = other.shape
                for _ in range(self.stack_dim):
                    other = np.expand_dims(other, 0)
                other = np.broadcast_to(other, self.stack_shape + ogs)
            sd = self.stack_dim
            ax1, ax2 = axes
            if isinstance(ax1, int):
                ax1 = [ax1]
            if isinstance(ax2, int):
                ax2 = [ax2]
            axes = [
                [sd + a if a >= 0 else a for a in ax1],
                [sd + b if b >= 0 else b for b in ax2]
            ]
            return type(self)(self.stack_shape, vec_tensordot(self.array, other, shared=len(self.stack_shape), axes=axes))

        def outer(self, other, axes=None):
            if isinstance(other, TensorExpression.ArrayStack):
                other = other.array
            else:
                ogs = other.shape
                for _ in range(self.stack_dim):
                    other = np.expand_dims(other, 0)
                other = np.broadcast_to(other, self.stack_shape + ogs)
            if axes is None:
                exp_axes = [
                    np.arange(self.stack_dim, self.array.ndim),
                    np.arange(self.stack_dim, other.ndim)
                ]
            else:
                sd = self.stack_dim
                exp_axes = [
                    [sd+a if a >= 0 else a for a in axes[0]],
                    [sd+b if b >= 0 else b for b in axes[1]]
                ]
            return type(self)(self.stack_shape, vec_outer(self.array, other, axes=exp_axes))

        def rev_outer(self, other, axes=None):
            if not isinstance(other, TensorExpression.ArrayStack):
                _, other = self._pad_shape(self.array, other, self.stack_shape)
                other = TensorExpression.ArrayStack(self.stack_shape, other)
            return other.outer(self, axes=[axes[1], axes[0]] if axes is not None else axes)

        def __repr__(self):
            return "{}({},\n{}\n)".format(
                type(self).__name__,
                self.stack_shape,
                self.array
            )

    class Term(metaclass=abc.ABCMeta):
        _array_cache = weakref.WeakKeyDictionary()
        # for keeping track of array vals for eval
        def __init__(self, array=None, name=None):
            self._arr = array
            self.name = name
            self._hash = None
        @abc.abstractmethod
        def get_children(self) -> 'Iterable[TensorExpression.Term]':
            raise NotImplementedError("base class")
        @property
        def children(self):
            return self.get_children()
        @abc.abstractmethod
        def deriv(self) -> 'TensorExpression.Term':
            raise NotImplementedError("base class")
        def dQ(self):
            new_term = self.deriv()
            if self.name is not None and isinstance(new_term, TensorExpression.Term):
                new_term.name = 'dQ({})'.format(self.name)
            return new_term
        @abc.abstractmethod
        def array_generator(self, **kwargs) -> np.ndarray:
            raise NotImplementedError("base class")
        @property
        def ndim(self):
            return self.array.ndim
        def get_hash(self):
            return hash((self.name, self.to_string()))
        def __hash__(self):
            if self._hash is None:
                self._hash = self.get_hash()
            return self._hash
        def __eq__(self, other):
            return type(self) is type(other) and hash(self) == hash(other)
        def asarray(self, print_terms=False, cache=True, **kw):
            if self in self._array_cache:  # this allows me to share arrays as long as the hash is right
                return self._array_cache[self]
            else:
                # print(self)
                try:
                    res = self.array_generator(print_terms=print_terms, **kw)
                except TensorExpansionError:
                    raise
                except Exception as e:
                    raise TensorExpansionError('failed to convert {} to an array'.format(self))
                else:
                    if print_terms:
                        print(self)
                        if isinstance(res, TensorExpression.ArrayStack):
                            print(">>>", res.array.shape)
                        else:
                            print(">>>", res.shape)
                    if cache:
                        self._array_cache[self] = res
                        # print(list(self._array_cache.keys()))
                    return res
        @property
        def array(self):
            if self not in self._array_cache: # this allows me to share arrays as long as the hash is right
                if self._arr is None:
                    try:
                        self._arr = self.array_generator()
                    except TensorExpansionError:
                        raise
                    except Exception as e:
                        raise TensorExpansionError('failed to convert {} to an array'.format(self))
                self._array_cache[self] = self._arr
            return self._array_cache[self]
        @array.setter
        def array(self, arr):
            self._arr = arr
        @abc.abstractmethod
        def rank(self) -> int:
            raise NotImplementedError("base class")
        @property
        def ndim(self):
            return self.rank()
        @abc.abstractmethod
        def to_string(self) -> str:
            raise NotImplementedError("base class")
        def __repr__(self):
            if self.name is None:
                name = self.to_string()
                # if name is None or name == "None":
                #     raise ValueError("bad name for type {}".format(type(self).__name__))
                return name
            else:
                return self.name
        @abc.abstractmethod
        def reduce_terms(self, check_arrays=False) -> 'TensorExpression.Term':
            raise NotImplementedError("base class")
        def _check_simp(self, new):
            new._arr = None
            n2 = new.array
            if not np.allclose(self.array, n2):
                raise TensorExpansionError("bad simplification {} -> {}".format(self, new))
        def simplify(self, check_arrays=False):
            if check_arrays:
                arr = self.array
                self._arr = None
                red = self.reduce_terms(check_arrays=True)
                new = red.array
                if not np.allclose(arr, new):
                    raise TensorExpansionError("bad simplification {} -> {}".format(self, red))
                new = red
            else:
                new = self.reduce_terms()
            if isinstance(new, TensorExpression.Term):
                if new.name is None:
                    new.name = self.name
                if new._arr is None:
                    new._arr = self._arr
            return new
        def __add__(self, other):
            return TensorExpression.SumTerm(self, other)
        def __mul__(self, other):
            return TensorExpression.ScalingTerm(self, other)
        def __rmul__(self, other):
            return TensorExpression.ScalingTerm(self, other)

        def __pos__(self):
            return self
        def __neg__(self):
            return -1 * self
        def flip(self):
            raise NotImplementedError("base class")

        def divided(self):
            if self.ndim > 0:
                raise ValueError("term {} isn't a scalar".format(self))
            else:
                return TensorExpression.FlippedTerm(self)
        def __truediv__(self, other):
            if isinstance(other, TensorExpression.Term):
                return TensorExpression.ScalingTerm(self, other.divided())
            else:
                return TensorExpression.ScalingTerm(self, 1 / other)
        def __rtruediv__(self, other):
            if isinstance(other, TensorExpression.Term):
                return other.__truediv__(self)
            else:
                return TensorExpression.ScalingTerm(self.divided(), other)

        def dot(self, other, i, j):
            return TensorExpression.ContractionTerm(self, i, j, other)

        def shift(self, i, j):
            if i < 1 or j < 1 or i == j:
                return self
            else:
                return TensorExpression.AxisShiftTerm(self, i, j)

        def det(self):
            return TensorExpression.DeterminantTerm(self)

        def tr(self, axis1=1, axis2=2):
            return TensorExpression.TraceTerm(self, axis1=axis1, axis2=axis2)

        def inverse(self):
            return TensorExpression.InverseTerm(self)

        def __invert__(self):
            return self.inverse()

        def outer(self, other):
            return TensorExpression.OuterTerm(self, other)

        # def __hash__(self):
        #     return hash(str(self))

        # def __eq__(self, other):
        #     return str(self) == str(other)

    class SumTerm(Term):
        def __init__(self, *terms: 'TensorExpression.Term', array=None, name=None):
            super().__init__(array=array, name=name)
            self.terms = terms
        def get_children(self):
            return self.terms
        def deriv(self):
            return type(self)(*(s.dQ() for s in self.terms))

        def array_generator(self, print_terms=False):
            all_terms = [(i, s.asarray(print_terms=print_terms)) for i, s in enumerate(self.terms)]
            clean_terms = [s for s in all_terms if
                           not (isinstance(s[1], (int, float, np.integer, np.floating)) and s[1] == 0)]
            shp = None
            for s in clean_terms:
                if shp is None:
                    shp = s[1].shape
                if s[1].shape != shp:
                    raise Exception(
                        "this term is bad {} in {} (shape {} instead of shape {})".format(self.terms[s[0]], self,
                                                                                          s[1].shape,
                                                                                          clean_terms[0][1].shape
                                                                                          ))
            clean_terms = [c[1] for c in clean_terms]
            # try:
            if len(clean_terms) > 0:
                s = sum(clean_terms[1:], clean_terms[0])
            else:
                s = 0
            # except:
            #     raise Exception(clean_terms)
            # else:
            return s

        def rank(self):
            return self.terms[0].ndim

        def reduce_terms(self, check_arrays=False):
            full_terms = []
            cls = type(self)
            for t in self.terms:
                t = t.simplify(check_arrays=check_arrays)
                if isinstance(t, cls):
                    full_terms.extend(t.terms)
                elif not (isinstance(t, (int, float, np.integer, np.floating)) and t == 0):
                    full_terms.append(t)
            full_terms = list(sorted(full_terms, key=lambda t: str(t)))  # canonical sorting is string sorting b.c. why not
            return type(self)(*full_terms, array=self._arr)

        def get_hash(self):
            return hash((self.name, tuple(hash(x) for x in self.terms)))
        def to_string(self):
            return '+'.join(str(x) for x in self.terms)

        def substitute(self, other):
            """substitutes other in to the sum by matching up all necessary terms"""
            if isinstance(other, TensorExpression.SumTerm):
                my_terms = list(self.terms)
                for t in other.terms:
                    i = my_terms.index(t)
                    my_terms = my_terms[:i] + my_terms[i + 1:]
                my_terms.append(other)
                return type(self)(*my_terms)
            else:
                my_terms = list(self.terms)
                i = my_terms.index(other)
                my_terms = my_terms[:i] + my_terms[i + 1:]
                my_terms.append(other)
                return type(self)(*my_terms)
    class ScalingTerm(Term):
        def __init__(self, term: 'TensorExpression.Term', scaling, array=None, name=None):
            super().__init__(array=array, name=name)
            self.scaling = scaling
            self.term = term
        def get_children(self):
            return [self.scaling, self.term]
        def rank(self):
            if isinstance(self.scaling, TensorExpression.Term):
                scale_dim = self.scaling.ndim
            elif isinstance(self.scaling, np.ndarray):
                scale_dim = self.scaling.ndim
            else:
                scale_dim = 0
            return scale_dim + self.term.ndim
        def array_generator(self, print_terms=False):
            scaling = self.scaling
            if isinstance(self.scaling, TensorExpression.Term):
                scaling = scaling.asarray(print_terms=print_terms)
            if isinstance(scaling, (np.ndarray, TensorExpression.ArrayStack)): # really doing an outer product...
                term = self.term.asarray(print_terms=print_terms)
                if scaling.ndim > 0 and term.ndim > 0:
                    og_term_dim = term.ndim
                    if isinstance(term, TensorExpression.ArrayStack):
                        term = term.expand_dims([-1]*scaling.ndim)
                    else:
                        for i in range(scaling.ndim):
                            term = np.expand_dims(term, -1)
                    if isinstance(scaling, TensorExpression.ArrayStack):
                        scaling = scaling.expand_dims([0]*og_term_dim)
                    else:
                        for i in range(og_term_dim):
                            scaling = np.expand_dims(scaling, 0)
            else:
                term = self.term.asarray(print_terms=print_terms)
            arr = scaling * term
            return arr

        def to_string(self):
            meh_1 = '({})'.format(self.scaling) if isinstance(self.scaling, TensorExpression.SumTerm) else self.scaling
            meh_2 = '({})'.format(self.term) if isinstance(self.term, TensorExpression.SumTerm) else self.term
            return '{}*{}'.format(meh_1, meh_2)

        def reduce_terms(self, check_arrays=False):
            scaling = self.scaling
            if isinstance(self.scaling, TensorExpression.Term):
                scaling = scaling.simplify(check_arrays=check_arrays)
            if isinstance(scaling, (int, float, np.integer, np.floating)) and scaling == 1:
                return self.term.simplify(check_arrays=check_arrays)
            elif (
                    (isinstance(scaling, (int, float, np.integer, np.floating)) and scaling == 0)
                    or
                    (isinstance(self.term, (int, float, np.integer, np.floating)) and self.term == 0)
            ):
                return 0
            else:
                return type(self)(self.term.simplify(check_arrays=check_arrays), scaling, array=self._arr)

        def deriv(self):
            term = type(self)(self.term.dQ(), self.scaling)
            if isinstance(self.scaling, TensorExpression.Term):
                ugh2 = type(self)(self.term, self.scaling.dQ())
                term += ugh2
            return term

    class ScalarScalingTerm(Term):
        """
        Scaling elementwise with correct broadcasting
        """
        def __init__(self, term: 'TensorExpression.Term', scaling, axes=None, array=None, name=None):
            super().__init__(array=array, name=name)
            self.scaling = scaling
            self.term = term
            self.axes = axes
        def get_children(self):
            return [self.scaling, self.term]
        def rank(self):
            if isinstance(self.scaling, TensorExpression.Term):
                scale_dim = self.scaling.ndim
            elif isinstance(self.scaling, np.ndarray):
                scale_dim = self.scaling.ndim
            else:
                scale_dim = 0
            return scale_dim + self.term.ndim
        def array_generator(self, print_terms=False):
            scaling = self.scaling
            if isinstance(self.scaling, TensorExpression.Term):
                scaling = scaling.asarray(print_terms=print_terms)
            # if isinstance(scaling, (np.ndarray, TensorExpression.ArrayStack)): # really doing an outer product...
            #     term = self.term.asarray(print_terms=print_terms)
            #     if scaling.ndim > 0 and term.ndim > 0:
            #         og_term_dim = term.ndim
            #         if isinstance(term, TensorExpression.ArrayStack):
            #             term = term.expand_dims([-1]*scaling.ndim)
            #         else:
            #             for i in range(scaling.ndim):
            #                 term = np.expand_dims(term, -1)
            #         if isinstance(scaling, TensorExpression.ArrayStack):
            #             scaling = scaling.expand_dims([0]*og_term_dim)
            #         else:
            #             for i in range(og_term_dim):
            #                 scaling = np.expand_dims(scaling, 0)
            # else:

            term = self.term.asarray(print_terms=print_terms)
            # print(self)
            # print(self.axes, term.shape, scaling.shape)
            if (
                    self.axes is None
                    or not isinstance(scaling, (np.ndarray, TensorExpression.ArrayStack))
                    or (
                            self.axes is not None
                            and (
                                    term.ndim - len(self.axes[0]) <= 0 or
                                    scaling.ndim - len(self.axes[1]) <= 0
                            )
                        )
            ):
                # print("???")
                arr = scaling * term
            else: # manage broadcasting for effectively a vecouter
                mask = np.ones(term.ndim, dtype=np.uint8)
                mask[[term.ndim+a if a < 0 else a for a in self.axes[0]]] = 0
                ax1 = np.where(mask)[0]

                mask = np.ones(scaling.ndim, dtype=np.uint8)
                mask[[term.ndim+a if a < 0 else a for a in self.axes[1]]] = 0
                ax2 = np.where(mask)[0]

                axes = [ax1, ax2]
                    # np.setdiff1d(np.arange(term.ndim), [term.ndim+a if a < 0 else a for a in self.axes[0]]),
                    # np.setdiff1d(np.arange(scaling.ndim), [term.ndim+a if a < 0 else a for a in self.axes[1]])
                # ]
                # print(term.shape)
                # print(scaling.shape)
                # print(axes)
                if isinstance(term, TensorExpression.ArrayStack):
                    arr = term.outer(scaling, axes=axes)
                elif isinstance(scaling, TensorExpression.ArrayStack):
                    arr = scaling.rev_outer(term, axes=axes)
                else:
                    arr = vec_outer(term, scaling, axes=axes)
                # print(self)
                # print(arr.shape)
            return arr

        def to_string(self):
            meh_1 = '({})'.format(self.scaling) if isinstance(self.scaling, TensorExpression.SumTerm) else self.scaling
            meh_2 = '({})'.format(self.term) if isinstance(self.term, TensorExpression.SumTerm) else self.term
            return '{}({}*{})'.format(type(self).__name__, meh_2, meh_1)

        def reduce_terms(self, check_arrays=False):
            return self
        #     scaling = self.scaling
        #     if isinstance(self.scaling, TensorExpression.Term):
        #         scaling = scaling.simplify(check_arrays=check_arrays)
        #     if isinstance(scaling, (int, float, np.integer, np.floating)) and scaling == 1:
        #         return self.term.simplify(check_arrays=check_arrays)
        #     elif (
        #             (isinstance(scaling, (int, float, np.integer, np.floating)) and scaling == 0)
        #             or
        #             (isinstance(self.term, (int, float, np.integer, np.floating)) and self.term == 0)
        #     ):
        #         return 0
        #     else:
        #         return type(self)(self.term.simplify(check_arrays=check_arrays), scaling, array=self._arr)

        def deriv(self):
            axes = self.axes
            if axes is None:
                axes = [[0], [0]]
            a = [
                [i+1 if i >= 0 else i for i in axes[0]],
                axes[1]
            ]
            term = type(self)(self.term.dQ(), self.scaling, axes=a)
            if isinstance(self.scaling, TensorExpression.Term):
                b = [
                    axes[1],
                    [i+1 if i >= 0 else i for i in axes[1]]
                ]
                ugh2 = type(self)(self.term, self.scaling.dQ(), axes=b)
                term += ugh2
            return term
    class ScalarPowerTerm(Term):
        """
        Represents x^n.
        Only can get valid derivatives for scalar terms.
        Beware of that.
        """
        def __init__(self, term: 'TensorExpression.Term', pow, array=None, name=None):
            super().__init__(array=array, name=name)
            self.term = term
            self.pow = pow
        def get_children(self):
            return [self.pow, self.term]
        def rank(self):
            return self.term.rank()
        def array_generator(self, print_terms=False):
            wat = self.term.asarray(print_terms=print_terms)
            out = wat ** self.pow
            return out
        def to_string(self):
            return '({}**{})'.format(self.term, self.pow)
        def reduce_terms(self, check_arrays=False):
            if self.pow == 1:
                return self.term.simplify(check_arrays=check_arrays)
            elif self.pow == 0:
                return 1
            elif self.pow == -1:
                return TensorExpression.FlippedTerm(self.term.simplify(check_arrays=True), array=self._arr)
            else:
                return TensorExpression.ScalarPowerTerm(self.term.simplify(check_arrays=check_arrays), self.pow,
                                                        array=self._arr)
        def deriv(self):
            if self.pow == 0:
                return 0 # should probably be doing size stuff but I'm hoping to get away with this...
            elif self.pow == 1:
                return self.term.dQ()
            elif self.pow == 2:
                prod_term = self.term
            else:
                prod_term = TensorExpression.ScalarPowerTerm(self.term, self.pow - 1)
            tdQ = self.term.dQ()
            # print(">>>", tdQ)
            # print(" > ", prod_term)
            # if (
            #         isinstance(prod_term, TensorExpression.Term)
            #         and isinstance(tdQ, TensorExpression.Term)
            #         and tdQ.rank() > 0
            #         and prod_term.rank() > 0
            # ):
            #     return TensorExpression.OuterTerm(
            #         self.pow * tdQ, prod_term
            #     )
            # else:
            return TensorExpression.ScalarScalingTerm(
                tdQ,
                self.pow * prod_term,
                axes=[[-1] if self.term.rank() > 0 else [], [-1]]
            )
    class FlippedTerm(ScalarPowerTerm):
        """
        Represents 1/x. Only can get valid derivatives for scalar terms. Beware of that.
        """

        def __init__(self, term: 'TensorExpression.Term', pow=-1, array=None):
            super().__init__(term, -1, array=array)
        def get_children(self):
            return [self.term]

        def to_string(self):
            return '1/{}'.format(self.term)

        def array_generator(self, print_terms=False):
            out = 1 / self.term.asarray(print_terms=print_terms)
            return out

        def reduce_terms(self, check_arrays=False):
            if isinstance(self.term, TensorExpression.FlippedTerm):
                wat = self.term.term.simplify(check_arrays=check_arrays)
                if check_arrays: self._check_simp(wat)
                return wat
            else:
                return super().reduce_terms(check_arrays=check_arrays)
    class AxisShiftTerm(Term):
        def __init__(self, term: 'TensorExpression.Term', start: int, end: int, array=None, name=None):
            super().__init__(array=array, name=name)
            self.term = term
            self.a = start
            self.b = end
        def get_children(self):
            return [self.term]
        def deriv(self):
            return type(self)(self.term.dQ(), self.a + 1, self.b + 1)

        def array_generator(self, print_terms=False):
            t = self.term.asarray(print_terms=print_terms)
            if isinstance(t, (int, float, np.integer, np.floating)) and t == 0:
                return 0
            else:
                if isinstance(t, TensorExpression.ArrayStack):
                    return t.moveaxis(self.a-1, self.b-1)
                else:
                    return np.moveaxis(t, self.a - 1, self.b - 1)

        def rank(self):
            return self.term.ndim

        def to_string(self):
            return '{{{}#{}->{}}}'.format(self.term, self.a, self.b)

        def reduce_terms(self, check_arrays=False):
            """We simplify over the possible swap classes"""
            cls = type(self)
            simp = self.term.simplify(check_arrays=check_arrays)
            sela = self.a
            selb = self.b
            if sela == selb:
                new = simp
                if check_arrays: self._check_simp(new)
            elif sela > selb:  # we flip this around
                new = cls(simp, selb, sela)
                for i in range(sela - selb - 1):
                    new = cls(new, selb, sela)
                new._arr = self._arr
                new = new.simplify(check_arrays=check_arrays)
                if check_arrays: self._check_simp(new)
            elif isinstance(simp, cls):
                otht = simp.term.simplify(check_arrays=check_arrays)
                otha = simp.a
                othb = simp.b
                if sela == othb:
                    if otha == selb:  # inverses although we shouldn't get here...
                        if otht._arr is None:
                            otht._arr = self._arr
                        new = otht
                    else:  # reduces to a single term
                        new_a = otha
                        new_b = selb
                        new = cls(otht, new_a, new_b, array=self._arr)
                        if check_arrays: self._check_simp(new)
                elif otha > sela:  # we needed to pick a convention...
                    new_sela = sela
                    new_selb = selb if selb < otha else selb + 1
                    other = cls(otht, new_sela, new_selb)
                    new_a = otha if otha > selb else otha - 1
                    new_b = othb if othb > selb else othb - 1
                    new = cls(other, new_a, new_b)
                    if check_arrays: self._check_simp(new)
                    if new._arr is None: new._arr = self._arr
                    return new
                elif otha == sela and othb == selb:
                    # check if we have enough iterates to get the identity
                    is_ident = True
                    for i in range(selb - sela):
                        if isinstance(otht, cls) and otht.a == sela and otht.b == selb:
                            otht = otht.term
                        else:
                            is_ident = False
                            break
                    if is_ident:
                        new = otht
                        if check_arrays:
                            self._check_simp(new)
                    else:
                        new = self
                else:
                    new = cls(simp, sela, selb)
            elif isinstance(simp, TensorExpression.SumTerm):
                new = TensorExpression.SumTerm(
                    *(
                        x.shift(self.a, self.b).simplify(check_arrays=check_arrays)
                        for x in simp.terms
                    ),
                    array=self._arr
                )
                if check_arrays:
                    self._check_simp(new)
            else:
                new = self

            return new

    class OuterTerm(Term):
        """
        Provides an outer product
        """
        def __init__(self,
                     a: 'TensorExpression.Term',
                     b: 'TensorExpression.Term',
                     array=None, name=None
                     ):
            super().__init__(array=array, name=name)
            self.a = a
            self.b = b
        def get_children(self):
            return [self.a, self.b]
        def rank(self):
            return self.a.rank() + self.b.rank()
        def array_generator(self, print_terms=False):
            a = self.a.asarray(print_terms=print_terms)
            b = self.b.asarray(print_terms=print_terms)
            # print(self)
            # print(">", type(a), type(b), a.shape, b.shape)
            og_bdim = b.ndim
            if isinstance(b, TensorExpression.ArrayStack):
                b = b.expand_dims([-1]*a.ndim)
            else:
                for i in range(a.ndim):
                    b = np.expand_dims(b, -1)

            if isinstance(a, TensorExpression.ArrayStack):
                a = a.expand_dims([0]*og_bdim)
            else:
                for i in range(og_bdim):
                    a = np.expand_dims(a, 0)

            return a * b
        def to_string(self):
            meh_1 = '({})'.format(self.a) if isinstance(self.a, TensorExpression.SumTerm) else self.a
            meh_2 = '({})'.format(self.b) if isinstance(self.b, TensorExpression.SumTerm) else self.b
            return '{}<x>{}'.format(meh_1, meh_2)

        def reduce_terms(self, check_arrays=False):
            return self

        # def reduce_terms(self, check_arrays=False):
        #     scaling = self.a
        #     if isinstance(self.scaling, TensorExpression.Term):
        #         scaling = scaling.simplify(check_arrays=check_arrays)
        #     if isinstance(scaling, (int, float, np.integer, np.floating)) and scaling == 1:
        #         return self.term.simplify(check_arrays=check_arrays)
        #     elif (
        #             (isinstance(scaling, (int, float, np.integer, np.floating)) and scaling == 0)
        #             or
        #             (isinstance(self.term, (int, float, np.integer, np.floating)) and self.term == 0)
        #     ):
        #         return 0
        #     else:
        #         return type(self)(self.term.simplify(check_arrays=check_arrays), scaling, array=self._arr)

        def deriv(self):
            return type(self)(self.a.dQ(), self.b) + type(self)(self.a, self.b.dQ())

    class ContractionTerm(Term):
        def __init__(self, left: 'TensorExpression.Term',
                     i: typing.Union[int, typing.Iterable[int]],
                     j: typing.Union[int, typing.Iterable[int]],
                     right: 'TensorExpression.Term', array=None, name=None):
            super().__init__(array=array, name=name)
            self.left = left
            self.i = i
            self.j = j
            self.right = right
        def get_children(self):
            return [self.left, self.right]

        def array_generator(self, print_terms=False):
            t1 = self.left.asarray(print_terms=print_terms)
            t2 = self.right.asarray(print_terms=print_terms)
            if isinstance(t1, (int, float, np.integer, np.floating)) and t1 == 0:
                return 0
            elif isinstance(t2, (int, float, np.integer, np.floating)) and t2 == 0:
                return 0
            else:
                # try:
                i = self.i
                if isinstance(i, (int, np.integer)):
                    i = i - 1
                else:
                    i = [x - 1 for x in i]
                j = self.j
                if isinstance(i, (int, np.integer)):
                    j = j - 1
                else:
                    j = [x - 1 for x in j]
                if isinstance(t1, TensorExpression.ArrayStack):
                    return t1.tensordot(t2, axes=[i, j])
                elif isinstance(t2, TensorExpression.ArrayStack):
                    ogs = t1.shape
                    for _ in range(t2.stack_dim):
                        t1 = np.expand_dims(t1, 0)
                    t1 = np.broadcast_to(t1, t2.stack_shape + ogs)
                    t1 = TensorExpression.ArrayStack(t2.stack_shape, t1)
                    return t1.tensordot(t2, axes=[i, j])
                else:
                    try:
                        return np.tensordot(t1, t2, axes=[i, j])
                    except:
                        raise TensorExpansionError(
                            'failed to contract {}[{}]x{}[{}] for {} and {}'.format(t1.shape, i, t2.shape, j, self.left,
                                                                                    self.right))
                # except (ValueError, IndexError):
                #     raise ValueError("failed to execute {}".format(self))

        def rank(self):
            return self.left.ndim + self.right.ndim - 2

        def deriv(self):
            t1 = type(self)(self.left.dQ(),
                            self.i + 1 if isinstance(self.i, (int, np.integer)) else [x + 1 for x in self.i],
                            # not sure if this is right...
                            self.j,
                            self.right
                            )
            t2 = type(self)(self.left,
                            self.i,
                            self.j + 1 if isinstance(self.j, (int, np.integer)) else [x + 1 for x in self.j],
                            self.right.dQ()
                            )
            return t1 + t2.shift(
                self.left.ndim - (0 if isinstance(self.j, (int, np.integer)) else len(self.j) - 1),
                1
            )

        def to_string(self):
            return '<{}:{},{}:{}>'.format(self.left, self.i, self.j, self.right)

        def reduce_terms(self, check_arrays=False):
            cls = type(self)
            left = self.left.simplify(check_arrays=check_arrays)
            right = self.right.simplify(check_arrays=check_arrays)
            if isinstance(right, TensorExpression.AxisShiftTerm):
                # I flip the names just so it agrees with my math...
                t = right.term
                i = right.a
                j = right.b
                a = self.i
                b = self.j
                n = left.ndim
                if b < i:
                    new = cls(left, a, b, t).shift(n - 2 + i, n - 2 + j)
                    if check_arrays:
                        self._check_simp(new)
                elif b < j:
                    new = cls(left, a, b + 1, t).shift(n - 1 + i, n - 2 + j)
                    if check_arrays:
                        self._check_simp(new)
                elif b == j:
                    new = cls(left, a, i, t)
                    if check_arrays:
                        self._check_simp(new)
                else:
                    new = cls(left, a, b, t).shift(n - 1 + i, n - 1 + j)
                    if check_arrays:
                        self._check_simp(new)

            elif isinstance(left, TensorExpression.AxisShiftTerm):
                # I flip the names just so it agrees with my math...
                t = left.term
                i = left.a
                j = left.b
                a = self.i
                b = self.j
                if a > j:
                    new = cls(t, a, b, right).shift(i, j)
                    if check_arrays:
                        self._check_simp(new)
                elif a == j:
                    new = cls(t, i, b, right)
                    if check_arrays:
                        self._check_simp(new)
                elif a >= i:
                    new = cls(t, a + 1, b, right).shift(i, j - 1)
                    if check_arrays:
                        self._check_simp(new)
                else:
                    new = cls(t, a, b, right).shift(i - 1, j - 1)
                    if check_arrays:
                        self._check_simp(new)
            elif isinstance(left, TensorExpression.SumTerm):
                new = TensorExpression.SumTerm(
                    *(cls(x, self.i, self.j, right).simplify(check_arrays=check_arrays) for x in left.terms),
                    array=self._arr
                )
                if check_arrays:
                    self._check_simp(new)
            elif isinstance(right, TensorExpression.SumTerm):
                new = TensorExpression.SumTerm(
                    *(cls(left, self.i, self.j, x).simplify(check_arrays=check_arrays) for x in right.terms),
                    array=self._arr
                )
                if check_arrays:
                    self._check_simp(new)
            # elif isinstance(self.left, QXTerm) and isinstance(self.right, XVTerm):
            #     new = BasicContractionTerm(self.left.terms, self.left.n, self.i, self.j, self.right.m,
            #                                                      array=self._arr)
            else:
                new = cls(self.left.simplify(check_arrays=check_arrays), self.i, self.j,
                          self.right.simplify(check_arrays=check_arrays), array=self._arr)

            if new._arr is None:
                new._arr = self._arr

            return new

    # fancier terms
    class InverseTerm(Term):
        def __init__(self, term: 'TensorExpression.Term', array=None, name=None):
            super().__init__(array=array, name=name)
            self.term = term

        def get_children(self):
            return [self.term]

        def rank(self):
            return self.term.rank()

        def array_generator(self, print_terms=False):
            t = self.term.asarray(print_terms=print_terms)
            stack_shape = None
            if isinstance(t, TensorExpression.ArrayStack):
                stack_shape = t.stack_shape
                t = t.array
            arr = np.linalg.inv(t)
            if stack_shape is not None:
                arr = TensorExpression.ArrayStack(stack_shape, arr)
            return arr

        def to_string(self):
            return '({}^-1)'.format(self.term)

        def reduce_terms(self, check_arrays=False):
            return type(self)(self.term.simplify(check_arrays=check_arrays), array=self._arr)

        def deriv(self):
            dq = self.term.dQ()
            sub = self.dot(dq, self.ndim, 2).shift(self.ndim, 1)  # self.dot(self.term.dQ(), self.ndim, 2)
            return -sub.dot(self, sub.ndim, 1)  # .shift(self.ndim, 1)
    class TraceTerm(Term):
        def __init__(self, term:'TensorExpression.Term', axis1=1, axis2=2, array=None, name=None):
            super().__init__(array=array, name=name)
            self.term = term
            self.axis1 = axis1
            self.axis2 = axis2

        def get_children(self):
            return [self.term]

        def rank(self):
            return self.term.ndim - 2

        def array_generator(self, print_terms=False):
            t = self.term.asarray(print_terms=print_terms)
            stack_shape = None
            offset = 0
            if isinstance(t, TensorExpression.ArrayStack):
                stack_shape = t.stack_shape
                offset = len(stack_shape)
                t = t.array
            arr = np.trace(t, axis1=offset + self.axis1 - 1, axis2=offset + self.axis2 - 1)
            if stack_shape is not None:
                arr = TensorExpression.ArrayStack(stack_shape, arr)
            return arr

        def to_string(self):
            return 'Tr[{},{}+{}]'.format(self.term, self.axis1, self.axis2)

        def reduce_terms(self, check_arrays=False):
            simp = self.term.simplify(check_arrays=check_arrays)
            if isinstance(simp, TensorExpression.SumTerm):
                new = TensorExpression.SumTerm(
                    *(type(self)(t, axis1=self.axis1, axis2=self.axis2) for t in simp.terms),
                    array=self._arr
                )
                if check_arrays: self._check_simp(new)
            # elif isinstance(simp, AxisShiftTerm):
            #     # wait this is completely wrong...?
            #
            #     sub = type(self)(simp.term, axis1=self.axis1, axis2=self.axis2)
            #     new = AxisShiftTerm(
            #         type(self)(simp.term, axis1=self.axis1, axis2=self.axis2),
            #         simp.a,
            #         simp.b,
            #         array=self._arr
            #     )
            #     if check_arrays: self._check_simp(new)
            else:
                new = type(self)(simp, axis1=self.axis1, axis2=self.axis2, array=self._arr)
            return new

        def deriv(self):
            wat = self.term.dQ()
            return type(self)(wat, axis1=self.axis1 + 1, axis2=self.axis2 + 1)
    class DeterminantTerm(Term):
        def __init__(self, term: 'TensorExpression.Term', array=None, name=None):
            super().__init__(array=array, name=name)
            self.term = term
        def get_children(self):
            return [self.term]
        def rank(self):
            return 0
        def array_generator(self, print_terms=False):
            t = self.term.asarray(print_terms=print_terms)
            stack_shape = None
            if isinstance(t, TensorExpression.ArrayStack):
                stack_shape = t.stack_shape
                t = t.array
            arr = np.linalg.det(t)
            if stack_shape is not None:
                arr = TensorExpression.ArrayStack(stack_shape, arr)
            return arr
        def to_string(self):
            return '|{}|'.format(self.term)
        def reduce_terms(self, check_arrays=False):
            return type(self)(self.term.simplify(check_arrays=check_arrays), array=self._arr)
        def deriv(self):
            inv_dot = TensorExpression.InverseTerm(self.term).dot(
                self.term.dQ(),
                self.term.ndim,
                2
            )
            if self.term.ndim > 1:
                inv_dot = inv_dot.shift(self.term.ndim, 1)
            # print(inv_dot)
            tr = TensorExpression.TraceTerm(
                inv_dot,
                axis1=2,
                axis2=inv_dot.ndim
            ) * self
            # if self.term.ndim > 2:
            #     tr = tr.shift(self.term.ndim-1, 1)
            return tr
    class VectorNormTerm(Term):
        def __init__(self, term: 'TensorExpression.Term', array=None, name=None, axis=-1):
            super().__init__(array=array, name=name)
            self.term = term
            self.axis = axis
        def get_children(self):
            return [self.term]
        def rank(self):
            return self.term.rank() - 1
        def array_generator(self, print_terms=False):
            t = self.term.asarray(print_terms=print_terms)
            stack_shape = None
            offset = 0
            if isinstance(t, TensorExpression.ArrayStack):
                stack_shape = t.stack_shape
                offset = len(stack_shape)
                t = t.array
            ax = (self.axis + offset) if self.axis >= 0 else self.axis
            arr = np.linalg.norm(t, axis=ax)
            # arr = np.ones(arr.shape) if isinstance(arr, np.ndarray) else arr
            if stack_shape is not None:
                arr = TensorExpression.ArrayStack(stack_shape, arr)
            return arr
        def to_string(self):
            return '||{}||'.format(self.term)
        def reduce_terms(self, check_arrays=False):
            return type(self)(self.term.simplify(check_arrays=check_arrays), array=self._arr)
        def deriv(self):
            return self.term / self

    class ScalarFunctionTerm(Term):
        def __init__(self, term, name='f', f=None, array=None, derivative_order=0):
            super().__init__(array=array)
            self.term = term
            self.fname = name
            if f is not None and not isinstance(f, dict):
                f = {'function':f, 'derivatives':None}
            self.func = f
            self.deriv_order = derivative_order
        def get_children(self):
            return [self.term]
        def rank(self):
            return self.term.rank() + self.deriv_order
        def array_generator(self, print_terms=False):
            t = self.term.asarray(print_terms=print_terms)
            stack_shape = None
            if isinstance(t, TensorExpression.ArrayStack):
                stack_shape = t.stack_shape
                t = t.array
            if self.func is None:
                raise NotImplementedError("need concrete function to evaluate")
            if self.deriv_order == 0:
                f = self.func['function']
                if f is None:
                    raise NotImplementedError("need concrete function to evaluate")
                res = f(t)
            else:
                df = self.func['derivatives']
                if df is None:
                    raise NotImplementedError("need concrete derivatives to evaluate")
                res = df(self.deriv_order)(t)
            if stack_shape is not None:
                res = TensorExpression.ArrayStack(stack_shape, res)
            return res
        def to_string(self):
            return (
                "{}({})".format(self.fname, self.term)
                if self.deriv_order == 0 else
                "{}[{}']({})".format(self.fname, self.deriv_order, self.term)
            )
        def reduce_terms(self, check_arrays=False):
            return type(self)(self.term.simplify(check_arrays=check_arrays),
                              name=self.fname, f=self.func, array=self._arr,
                              derivative_order=self.deriv_order
                              )
        def deriv(self):
            return TensorExpression.ScalarScalingTerm(
                self.term.deriv(),
                type(self)(
                    self.term, name=self.fname, f=self.func, array=None,
                    derivative_order=self.deriv_order + 1
                ),
                axes=[[-1] if self.term.rank() > 0 else [], [-1] if self.term.rank() > 0 else []]
                #TODO: I _know_ this is wrong in general
                #      but I'm not sure about all the correct rules yet
            )
    class ConstantArray(Term):
        """
        Square tensor of constants (squareness assumed, not checked)
        """
        def __init__(self, array, parent:'TensorExpression.Term'=None, name=None):
            self.base_array = np.asanyarray(array)
            super().__init__(array=None, name=name)
            self.parent = parent
        def get_children(self): # really what this term needs to be evaluated before it can be evaluated...
            return [self.parent]
        def rank(self):
            return self.base_array.ndim
        def array_generator(self, print_terms=False):
            a = self.base_array
            if not isinstance(a, TensorExpression.ArrayStack) and self.parent is not None:
                p = self.parent.asarray()
                if isinstance(p, TensorExpression.ArrayStack):
                    ogs = a.shape
                    for _ in p.stack_shape:
                        a = np.expand_dims(a, 0)
                    a = np.broadcast_to(a, p.stack_shape + ogs)
                    a = TensorExpression.ArrayStack(p.stack_shape, a)
            return a
        def get_hash(self):
            if isinstance(self._arr, np.ndarray):
                buf = self._arr.view(np.uint8)
                h = hashlib.sha1(buf).hexdigest()
            elif self._arr is None:
                if self.base_array is not None:
                    buf = self.base_array.view(np.uint8)
                    h = hashlib.sha1(buf).hexdigest()
                else:
                    h = hash(self.base_array)
            else:
                h = hash(self._arr)
            return hash((self.name, h))
        def to_string(self):
            if self._arr is None:
                return str(self.base_array)
            else:
                return str(self._arr)
        def deriv(self):
            a = self.base_array
            return TensorExpression.ConstantArray(np.zeros(a.shape + (a.shape[-1],)), parent=self)
        def reduce_terms(self, check_arrays=False):
            return self
    class IdentityMatrix(ConstantArray):
        def __init__(self, ndim, parent=None, name="I"):
            super().__init__(np.eye(ndim), parent=parent, name=name)

    class OuterPowerTerm(Term):
        """
        Represents a matrix-power type term
        """
        def __init__(self, base:'TensorExpression.Term', pow:int, array=None, name=None):
            if pow<1:
                raise NotImplementedError("???")
            super().__init__(array=array, name=name)
            self.base = base
            self.pow = pow
        def get_children(self):
            return [self.base]
        def rank(self):
            return self.base.rank() * self.pow
        def array_generator(self, print_terms=False):
            # print(hash(self))
            # allows caching to be reused hopefully...
            if self.pow == 1:
                return self.base.asarray(print_terms=print_terms)
            else:
                return type(self)(self.base, self.pow-1).outer(self.base).asarray(print_terms=print_terms)
        def get_hash(self):
            if self.pow == 1:
                return hash(self.base)
            else:
                return hash((self.name, hash(self.base), self.pow))
        def to_string(self):
            return "{}({}, {})".format(type(self).__name__, self.base, self.pow)
        def deriv(self):
            if self.pow > 2:
                return TensorExpression.OuterTerm(type(self)(self.base, self.pow-1), self.base).dQ()
            elif self.pow == 2:
                return TensorExpression.OuterTerm(self.base, self.base).dQ()
            else:
                return self.base.dQ()
        def reduce_terms(self, check_arrays=False):
            return self
    class TermVector(Term):
        def __init__(self, *terms:'TensorExpression.Term|List[TensorExpression.Term]', array=None, name=None):
            if len(terms) == 1 and not isinstance(terms[0], TensorExpression.Term):
                terms = terms[0]
            self.terms = terms
            super().__init__(array=array, name=name)
        def get_children(self):
            return self.terms
        def rank(self):
            r = self.terms[0].rank()
            if all(t.rank() == r for t in self.terms):
                return r+1
            else:
                return 1
        def array_generator(self, print_terms=False):
            return np.array([
                t.asarray(print_terms=print_terms) for t in self.terms
            ])
        def to_string(self):
            return str(self.terms)
        def deriv(self):
            return type(self)([
                t.deriv() for t in self.terms
            ])
        def reduce_terms(self, check_arrays=False):
            return self
    class CoordinateVector(Term):
        def __init__(self, vals_array, array=None, name=None):
            if not isinstance(vals_array, int) and array is None:
                if isinstance(vals_array, np.ndarray) or isinstance(vals_array[0], (int, float, np.integer, np.floating)):
                    vals_array = np.asanyarray(vals_array)
                    array = vals_array
            super().__init__(array=array, name=name)
            self.base_array = vals_array
        def get_children(self):
            if isinstance(self.base_array, (int, np.integer)):
                return []
            elif not isinstance(self.base_array, (np.ndarray, TensorExpression.ArrayStack)):
                return list(self.base_array)
            else:
                return []
        def rank(self):
            return 1
        def array_generator(self, print_terms=False):
            if isinstance(self.base_array, (np.ndarray, TensorExpression.ArrayStack)):
                return self.base_array
            else:
                raise Exception("need explicit array")
        def to_string(self):
            return "{}({})".format(type(self).__name__, self.base_array)
        def deriv(self):
            if isinstance(self.base_array, int):
                return TensorExpression.IdentityMatrix(self.base_array, parent=self)
            else:
                return TensorExpression.IdentityMatrix(len(self.base_array), parent=self)
        def reduce_terms(self, check_arrays=False):
            return self
    class CoordinateTerm(Term):
        def __init__(self,
                     idx:int,
                     vec:'TensorExpression.CoordinateVector',
                     array=None, name=None
                     ):
            super().__init__(array=array, name=name)
            self.vec = vec
            self.idx = idx
        def get_children(self):
            return []
        def rank(self):
            return 0
        def array_generator(self, print_terms=False):
            return self.vec.asarray(print_terms=print_terms)[self.idx]
        def to_string(self):
            return "{}({}, {})".format(type(self).__name__, self.vec, self.idx)
        def deriv(self):
            vec = np.zeros(len(self.vec.base_array))
            vec[self.idx] = 1
            return TensorExpression.ConstantArray(vec)
        def reduce_terms(self, check_arrays=False):
            return self
    class PolynomialTerm(Term):
        def __init__(self,
                     expansion:'Taylor.FunctionExpansion',
                     coords:'TensorExpression.TermVector'=None,
                     array=None, name=None
                     ):
            super().__init__(array=array, name=name)
            self.expansion = expansion
            self.coords = coords
        def get_children(self):
            return [self.coords]
        def rank(self):
            return 0
        def array_generator(self, print_terms=False):
            arr = self.coords.asarray(print_terms=print_terms)
            stack_shape = None
            if isinstance(arr, TensorExpression.ArrayStack):
                stack_shape = arr.stack_shape
                arr = arr.array
            res = self.expansion(arr)
            if stack_shape is not None:
                res = TensorExpression.ArrayStack(stack_shape, res)
            return res
        def to_string(self):
            return "{}({})".format(self.expansion, self.coords)
        def deriv(self):
            return type(self)(self.expansion.deriv(), coords=self.coords)
        def reduce_terms(self, check_arrays=False):
            return self

class TensorExpansionError(Exception):
    ...
class TensorExpansionTerms:
    """
    A friend of DumbTensor which exists
    to not only make the tensor algebra suck less but also
    to make it automated by making use of some simple rules
    for expressing derivatives specifically in the context of
    doing the coordinate transformations we need to do.
    Everything here is 1 indexed since that's how I did the OG math
    """
    def __init__(self, qx_terms, xv_terms, qxv_terms=None, base_qx=None, base_xv=None,
                 q_name='Q',
                 v_name='V'
                 ):
        """
        :param qx_terms:
        :type qx_terms: Iterable[np.ndarray]
        :param xv_terms:
        :type xv_terms: Iterable[np.ndarray]
        """
        self.qx_terms = qx_terms
        self.xv_terms = [0.]*len(qx_terms) if xv_terms is None else xv_terms
        self.qxv_terms = qxv_terms
        self.base_qx = base_qx
        self.base_xv = base_xv
        self.q_name = q_name
        self.v_name = v_name
    def QX(self, n):
        return self.QXTerm(self, n)
    def XV(self, m):
        return self.XVTerm(self, m)
    def QXV(self, n, m):
        return self.QXVTerm(self,n,  m)

    class QXTerm(TensorExpression.Term):
        def __init__(self, terms: 'TensorExpansionTerms', n: int, array=None):
            super().__init__(array=array)
            self.terms = terms
            self.n = n
        def get_children(self):
            return []
        def deriv(self):
            return type(self)(self.terms, self.n + 1)
        def array_generator(self, print_terms=False):
            if self.n == 0:
                return self.terms.base_qx
            else:
                return self.terms.qx_terms[self.n - 1]
        def rank(self):
            if isinstance(self.array, (int, float, np.integer, np.floating)) and self.array == 0:
                return self.n + 1
            else:
                return self.array.ndim

        def to_string(self):
            return '{}[{}]'.format(self.terms.q_name, self.n)

        def reduce_terms(self, check_arrays=False):
            return self
    class XVTerm(TensorExpression.Term):
        def __init__(self, terms: 'TensorExpansionTerms', m: int, array=None):
            super().__init__(array=array)
            self.terms = terms
            self.m = m
        def get_children(self):
            return []
        def deriv(self):
            mixed_terms = self.terms.qxv_terms
            if (
                    mixed_terms is not None
                    and self.m > 0
                    and len(mixed_terms) > 0
                    # and mixed_terms[0] is not None
                    and len(mixed_terms[0]) >= self.m
                    and mixed_terms[0][self.m - 1] is not None
            ):
                return self.terms.QXV(1, self.m)
            else:
                return TensorExpression.ContractionTerm(self.terms.QX(1), 2, 1, self.terms.XV(self.m + 1))
        def array_generator(self, print_terms=False):
            if self.m == 0:
                return self.terms.base_qx
            else:
                return self.terms.xv_terms[self.m - 1]
        def rank(self):
            if isinstance(self.array, (int, float, np.integer, np.floating)) and self.array == 0:
                return self.m
            else:
                return self.array.ndim
        def to_string(self):
            return '{}[{}]'.format(self.terms.v_name, self.m)
        def reduce_terms(self, check_arrays=False):
            return self
    class QXVTerm(TensorExpression.Term):
        def __init__(self, terms: 'TensorExpansionTerms', n: int, m: int, array=None):
            super().__init__(array=array)
            self.terms = terms
            self.n = n
            self.m = m
        def get_children(self):
            return []
        def deriv(self):
            return type(self)(self.terms, self.n + 1, self.m)

        def array_generator(self, print_terms=False):
            return self.terms.qxv_terms[self.n - 1][self.m - 1]

        def rank(self):
            if isinstance(self.array, (int, float, np.integer, np.floating)) and self.array == 0:
                return self.n + self.m
            else:
                return self.array.ndim

        def to_string(self):
            return '{}{}[{},{}]'.format(self.terms.q_name, self.terms.v_name, self.n, self.m)

        def reduce_terms(self, check_arrays=False):
            return self
    class BasicContractionTerm(TensorExpression.Term):
        """
        Special case tensor contraction term between two elements of the
        tensor expansion terms.
        """

        def __init__(self, terms: 'TensorExpansionTerms', n: int, i: int, j: int, m: int, array=None):
            super().__init__(array=array)
            self.terms = terms
            self.n = n
            self.m = m
            self.i = i
            self.j = j

        def deriv(self):
            return TensorExpression.SumTerm(
                type(self)(
                    self.terms,
                    self.n + 1,
                    self.i + 1,
                    self.j,
                    self.m
                ),
                TensorExpression.ContractionTerm(
                    self.terms.QX(1),
                    2,
                    self.n,
                    type(self)(
                        self.terms,
                        self.n,
                        self.i,
                        self.j + 1,
                        self.m + 1
                    )
                )
            )

        def array_generator(self, print_terms=False):
            arr = np.tensordot(self.terms.qx_terms[self.n - 1], self.terms.xv_terms[self.m - 1], axes=[self.i, self.j])
            return arr

        def rank(self):
            return self.terms.qx_terms[self.n - 1].ndim + self.terms.xv_terms[self.m - 1].ndim - 2

        def to_string(self):
            return '<Q[{}]:{},{}:V[{}]>'.format(self.n, self.i, self.j, self.m)

        def reduce_terms(self, check_arrays=False):
            return self

class TensorDerivativeConverter:
    """
    A class that makes it possible to convert expressions
    involving derivatives in one coordinate system in another
    """

    TensorExpansionError=TensorExpansionError

    #TODO: add way to not recompute terms over and over
    def __init__(self,
                 jacobians,
                 derivatives=None,
                 mixed_terms=None,
                 jacobians_name='Q',
                 values_name='V'
                 ):
        """

        :param jacobians: The Jacobian and higher-order derivatives between the coordinate systems
        :type jacobians: Iterable[np.ndarray]
        :param derivatives: Derivatives of some quantity in the original coordinate system
        :type derivatives: Iterable[np.ndarray]
        :param mixed_terms: Mixed derivatives of some quantity involving the new and old coordinates
        :type mixed_terms: Iterable[Iterable[None | np.ndarray]]
        """

        if derivatives is None:
            derivatives = [0] * len(jacobians)

        if jacobians[0].ndim > 2:
            stack_shape = jacobians[0].shape[:-2]
            jacobians = [
                TensorExpression.ArrayStack(
                    stack_shape,
                    j
                )
                for j in jacobians
            ]
            derivatives = [
                TensorExpression.ArrayStack(
                    stack_shape,
                    d
                ) if not (isinstance(d, (int, float, np.integer, np.floating)) and d == 0) else 0
                for d in derivatives
            ]

        self.terms = TensorExpansionTerms(jacobians, derivatives, qxv_terms=mixed_terms, q_name=jacobians_name, v_name=values_name)

    def convert(self, order=None, print_transformations=False, check_arrays=False):

        if order is None:
            order = len(self.terms.qx_terms)

        if order < 0:
            raise ValueError("cannot convert derivatives between coordinates systems to order 0")

        arrays = []
        deriv = self.terms.QX(1).dot(self.terms.XV(1), 2, 1)
        arrays.append(deriv.array)

        for i in range(2, order+1):
            # print(">>>>>", deriv)
            deriv = deriv.dQ().simplify(check_arrays=check_arrays) # there's an occasional issue with shift simplifications I think...
            if print_transformations:
                print(">> order: ", i, deriv)
            arrays.append(deriv.array)

        arrays = [
            a.array if isinstance(a, TensorExpression.ArrayStack) else a
            for a in arrays
        ]
        return arrays

    @classmethod
    def compute_partition_terms(cls, partition):
        _, counts = np.unique(partition, return_counts=True)

        # compute the reduced multinomial coefficient in stable (enough) form
        multinomial_num = np.flip(np.arange(1, 1 + np.sum(partition)))
        multinomial_denum = np.concatenate([
            np.arange(1, 1 + j)
            for j in partition
        ])
        multi_redux_terms = np.concatenate([
            np.arange(1, 1 + j)
            for j in counts
        ])
        full_denom = np.flip(np.sort(np.concatenate([multinomial_denum, multi_redux_terms])))
        numl = len(multinomial_num)
        denl = len(full_denom)
        if numl > denl:
            full_denom = np.concatenate([full_denom, np.ones(numl - denl, dtype=full_denom.dtype)])
        elif denl > numl:
            multinomial_num = np.concatenate([multinomial_num, np.ones(denl - numl, dtype=multinomial_num.dtype)])

        return np.prod(multinomial_num / full_denom)

    @classmethod
    def convert_partition(cls, partition, derivs, vals, val_axis=0):
        if len(vals) <= len(partition) - 1:
            return 0
        base_term = vals[len(partition) - 1]
        if isinstance(base_term, (int, float, np.integer, np.floating)) and base_term == 0:
            return 0
        perm_counter = len(partition)
        perm_idx = []  # to establish the set of necessary permutations to make things symmetric
        if val_axis < 0:
            val_axis = base_term.ndim + val_axis
        for i in partition:
            if len(derivs) <= i - 1:
                return 0

            d = derivs[i - 1]
            if isinstance(d, (int, float, np.integer, np.floating)) and d == 0:
                return 0
            base_term = np.tensordot(d, base_term, axes=[-1, val_axis])
            if i > 1:
                perm_idx.extend([perm_counter] * i)
                perm_counter -= 1
            else:
                perm_idx.append(perm_counter)
            val_axis = min(base_term.ndim - 1, val_axis + d.ndim - 1)

        # sometimes we overcount, so we factor that out here
        nterms = cls.compute_partition_terms(partition)
        perm_inds, _ = UniquePermutations(perm_idx).permutations(return_indices=True)

        overcount = len(perm_inds) / nterms
        base_term = base_term / overcount

        return sum(
            base_term.transpose(list(p) + list(range(len(p), base_term.ndim)))
            for p in perm_inds
        )

    @classmethod
    def convert_fast(cls, derivs, vals, val_axis=-1, order=None):
        terms = []
        if order is None:
            order = len(vals)

        for o in range(1, order+1):
            term = sum(
                cls.convert_partition(p, derivs, vals, val_axis=val_axis)
                for parts in IntegerPartitioner.partitions(o)
                for p in parts
            )
            terms.append(term)

        return terms
