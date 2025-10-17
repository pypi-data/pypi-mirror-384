from ..LazyTensors import Tensor
from .Derivatives import FiniteDifferenceDerivative
from ...Coordinerds import CoordinateSet, CoordinateSystem
# from ..Symbolic import TensorDerivativeConverter
from ... import Numputils as nput
import numpy as np, itertools, copy, math

__all__ = [
    'FunctionExpansion'
]

########################################################################################################################
#
#                                           Polynomial
#
class TaylorPoly:
    """
    A handler for dealing with multidimensional polynomials

    Can be used to handle multiple polynomials simultaneously, but requires
    that all expansions are provided up to the same order.
    """

    def __init__(self,
                 derivatives,
                 transforms=None,
                 transformed_derivatives=False,
                 center=None,
                 ref=None,
                 weight_coefficients=False
                 ):
        """
        :param derivatives: Derivatives of the function being expanded
        :type derivatives: Iterable[np.ndarray | Tensor]
        :param transforms: Jacobian and higher order derivatives in the coordinates
        :type transforms: Iterable[np.ndarray | Tensor] | None
        :param center: the reference point for expanding aobut
        :type center: np.ndarray | None
        :param ref: the reference point value for shifting the expansion
        :type ref: float | np.ndarray
        :param weight_coefficients: whether the derivative terms need to be weighted or not
        :type weight_coefficients: bool
        """

        if ref is None:
            if nput.is_numeric(derivatives[0]): #TODO: handle multi-expansion case
                ref = derivatives[0]
            else:
                ref = 0


        # raise NotImplementedError("doesn't deal with higher-order expansions properly yet")
        self._derivs = self.FunctionDerivatives(derivatives, weight_coefficients)
        self._center = np.asanyarray(center) if center is not None else center
        self.ref = np.asanyarray(ref) if not nput.is_numeric(ref) else ref
        self._tf_derivs = transformed_derivatives
        if transforms is None:
            self._transf, self._inv = None, None
        else:
            # transformation matrices from cartesians to internals
            self._transf, self._inv = self.canonicalize_tfs(transforms)
        self._tensors = None
    @property
    def center(self):
        return self._center
    @property
    def is_multi(self):
        return self._derivs[0].ndim > 1
    @classmethod
    def multipolynomial(cls, *expansions):
        return cls(
            list(zip(*[e.expansion_tensors for e in expansions])),
            center=np.asanyarray([e.center for e in expansions]),
            ref=np.asanyarray([e.ref for e in expansions]),
            weight_coefficients=False
        )
    @classmethod
    def canonicalize_tfs(cls, tfs):
        if len(tfs) == 2 and (
                nput.is_numeric_array_like(tfs[0][0])
                and nput.is_numeric_array_like(tfs[1][0])
                and np.asanyarray(tfs[0][0]).ndim == np.asanyarray(tfs[1][0]).ndim
        ):
            return [np.asanyarray(t) for t in tfs[0]], [np.asanyarray(t) for t in tfs[1]]
        else:
            return [np.asanyarray(t) for t in tfs], None
    @property
    def transforms(self):
        return (
            [list(self._transf), list(self._inv)]
                if self._inv is not None else
            [list(self._transf)]
                if self._transf is not None else
            None
        )
    @property
    def expansion_tensors(self):
        """
        Provides the tensors that will contracted

        :return:
        :rtype: Iterable[np.ndarray]
        """
        if self._tensors is None:
            if self._transf is None or self._tf_derivs:
                self._tensors = self._derivs
            else:
                self._tensors = nput.tensor_reexpand(self.transforms[0], self._derivs, len(self._derivs))
        return self._tensors
    @expansion_tensors.setter
    def expansion_tensors(self, tensors):
        """
        Are we going to assume in setting the tensors that
        people have done any requisite coordinate transformations?

        -> I think that's leaving room open for nasty surprises since we have
        the `_transf_ member
        -> but the `expansion_tensors` are in general expected to ... be transformed?

        Which means that we need _two_ properties 1) these tensors and 2) the derivs
        neither of which is transformed when being set
        """
        self._tensors = tensors

    @property
    def derivative_tensors(self):
        """
        Provides the base derivative tensors
        independent of any coordinate transformations

        :return:
        :rtype: Iterable[np.ndarray]
        """
        return self._derivs
    @derivative_tensors.setter
    def derivative_tensors(self, derivs):
        self._tensors = derivs

    def get_expansions(self, coords, transform_displacements=True, subexpansions=None, outer=True, order=None, squeeze=None):
        """

        :param coords: Coordinates to evaluate the expansion at
        :type coords: np.ndarray | CoordinateSet
        :param subexpansions: A set of tensor expansion indices to use if we have a multiexpansion
        but only want some subset of the relevant points
        :type subexpansions: int | Iterable[int]
        :return:
        :rtype:
        """

        if not outer and not self.is_multi:
            raise ValueError("outer doesn't make sense without multiexpansion")
        outer = (not self.is_multi) or outer
        # doesn't really make sense if we don't have stuff to take the outer product over

        coords = np.asanyarray(coords)
        base_shape = coords.shape[:-1]
        if outer:
            coords = np.reshape(coords, (-1, coords.shape[-1]))
        else:
            if coords.shape[0] != len(self.expansion_tensors):
                raise ValueError("coords of shape {} can't map onto {} polys".format(
                    coords.shape, len(self.expansion_tensors)
                ))
            coords = np.reshape(coords, (coords.shape[0], -1, coords.shape[-1]))

        center = self._center
        if center is None:
            # we assume we have a vector of points
            disp = coords
        else:
            # by default we take the outer product through
            # broacasting, but if outer==False I want to be
            # able to just thread things and require that the number
            # of vectors of points is the same as the numbers of expansions
            # which I think has to map onto the number of centers
            if outer:
                center = center[np.newaxis]
            else:
                # we need to coerce things into the appropriate form
                # and by now we _know_ coords is rank three and now we just
                # need to make sure that center has the appropriate shape
                # for this
                if center.ndim == 1:
                    center = center[np.newaxis, np.newaxis]
                else:
                    center = center[:, np.newaxis, :]
            disp = coords - center

        if transform_displacements is None and self._transf is not None:
            transform_displacements = disp.shape[-1] != self._transf[0].shape[0]

        if transform_displacements and self._transf is not None:
            if self._inv is not None:
                inv = self._inv[0]
            else:
                tf = self._transf[0]
                inv = np.linalg.pinv(tf) if tf.shape[-1] != tf.shape[-2] else np.linalg.inv(tf)
            disp = np.tensordot(disp, inv, axes=[-1, -2])

        if nput.is_numeric(subexpansions):
            subexpansions = [subexpansions]

        if order is None: order = 0
        expansions = [[] for _ in range(order+1)]
        for i, tensr in enumerate(self.expansion_tensors):
            if subexpansions is not None:
                tensr = tensr[subexpansions] # I think it's really this simple...?
                # TBH I'm not entirely sure why one would want to use this kind of subexpansion
                # since it's generally not that expensive to build one of the smaller expansions
                # but it's nice to have the option since I can see this being a small optimization on the
                # edge somewhere.
            # contract the tensor by the displacements until it's completely reduced
            if outer:
                tensr = np.broadcast_to(tensr[np.newaxis], (disp.shape[0],) + tensr.shape)
            n = i + 1
            if order >= n:
                scaling = np.prod(np.arange(1, n))
                expansions[n].append(tensr * scaling)
            for j in range(n):
                tensr = nput.vec_tensordot(disp, tensr, axes=[[-1], [-1]], shared=1)
                o = i - j
                if o <= order:
                    scaling = np.prod(np.arange(n-order, n+1))
                    expansions[o].append(tensr * scaling)
            # contraction = tensr
            # expansions[0].append(tensr)

        expansions = [
            [e.reshape(base_shape + (e.shape[1:] if outer else e.shape[2:])) for e in ord_exp]
            for ord_exp in expansions
        ]

        return expansions
    def expand(self, coords, order=None, outer=True, transform_displacements=True, squeeze=True):
        """Returns a numerical value for the expanded coordinates

        :param coords:
        :type coords: np.ndarray
        :return:
        :rtype: float | np.ndarray
        """
        ref = self.ref
        base_exps = self.get_expansions(coords, outer=outer, transform_displacements=transform_displacements, order=order)
        exps = [sum(e) for e in base_exps]
        if transform_displacements is None and self._transf is not None:
            transform_displacements = self.ref.shape != self._transf[0].shape[0]

        if transform_displacements and len(exps) > 1 and self._transf is not None:
            inv = self._inv
            if inv is None:
                inv = nput.inverse_transformation(self._transf, order=len(exps) - 1)
                exps = exps[1:] + nput.tensor_reexpand(inv, exps)
        exps[0] = exps[0] + ref
        if order is None:
            exps = exps[0]
        return exps

    def __call__(self, coords, **kw):
        return self.expand(coords, **kw)

    class CoordinateTransforms:
        def __init__(self, transforms):
            self._transf = [np.asanyarray(t) for t in transforms]
        def __getitem__(self, i):
            if len(self._transf) < i:
                raise FunctionExpansionException("{}: transformations requested up to order {} but only provided to order {}".format(
                    type(self).__name__,
                    i,
                    len(self._transf)
                ))
            return self._transf[i]
        def __len__(self):
            return len(self._transf)
    class FunctionDerivatives:
        def __init__(self, derivs, weight_coefficients=True):
            self.derivs = [ np.asanyarray(t) for t in derivs ]
            if weight_coefficients:
                self.derivs = [self.weight_derivs(t, o+1) if weight_coefficients else t for o, t in enumerate(self.derivs)]
        def weight_derivs(self, t, order = None):
            """

            :param order:
            :type order: int
            :param t:
            :type t: Tensor
            :return:
            :rtype:
            """
            weighted = t
            if order is None:
                order = len(t.shape)
            if order > 1:
                weighted = weighted * (1/math.factorial(order))
                # s = t.shape
                # weights = np.ones(s)
                # all_inds = list(range(len(s)))
                # for i in range(2, order+1):
                #     for inds in itertools.combinations(all_inds, i):
                #         # define a diagonal slice through
                #         sel = tuple(slice(None, None, None) if a not in inds else np.arange(s[a]) for a in all_inds)
                #         weights[sel] = 1/math.factorial(i)
                # weighted = weighted.mul(weights)
                # print(weights, weighted.array)

            return weighted

        def __getitem__(self, i):
            if len(self.derivs) < i:
                raise FunctionExpansionException("{}: derivatives requested up to order {} but only provided to order {}".format(
                    type(self).__name__,
                    i,
                    len(self.derivs)
                ))
            return self.derivs[i]
        def __len__(self):
            return len(self.derivs)

    def deriv(self, which=None):
        """
        Computes the derivative(s) of the expansion(s) with respect to the
        supplied coordinates (`which=None` means compute the gradient)

        :param which:
        :type which:
        :return:
        :rtype:
        """

        expansions = self.expansion_tensors
        smol = isinstance(which, int)
        if smol:
            which = [which]
        elif which is None:
            which = list(range(expansions[0].shape[-1]))

        res = []
        cls = type(self)
        for i in which:
            derivs = []
            for j,e in enumerate(expansions):
                # need to know the shift dims?.... ?
                base_slice = tuple(slice(None, None, None) for _ in range(j+1))
                red = 0
                for k in range(j+1):
                    s = (...,) + base_slice[:k] + (i,) + base_slice[k+1:]
                    red = red + e[s] # this iteration is how we get the different multiples...?
                    # and even though it seems like it makes off diagonal mat els contribute too much
                    # this is actually correct!
                derivs.append(red * (j+1))
            res.append(cls(
                derivs[1:],
                ref=derivs[0],
                center=self._center,
                weight_coefficients=False
            ))
        return cls.multipolynomial(*res)

    @classmethod
    def from_indices(cls, inds, ref=0, expansion_order=None, ndim=None, symmetrize=True, **opts):
        #TODO: handle via `SparseArray` methods
        if isinstance(inds, dict):
            inds = tuple(inds.items())
        ref = ref
        if ndim is None or expansion_order is None:
            if ndim is None:
                ndim = 0
            if expansion_order is None:
                expansion_order = 0
            for (i, v) in inds: # prescan to get tensor dimensions
                if len(i) == 0:
                    continue
                expansion_order = max(expansion_order, len(i))
                ndim = max(ndim, max(i)+1)
        t = [np.zeros((ndim,)*n) for n in range(1, expansion_order+1)]
        for (i, v) in inds:
            if len(i) == 0:
                ref = v
                continue
            tens = t[len(i)-1]
            if symmetrize:
                for p in itertools.permutations(i):
                    tens[p] = v
            else:
                tens[i] = v
        return cls(
            t,
            ref=ref,
            **opts
        )

    def _build_binomial_inds(self, g_partitions, w_partitions):
        """
        An unnecessarily efficient algorithm to get the set
        pairs of indices into the integer partitions of `g` and `w`
        plus an optional permutation of `g` which will lead to non-zero
        terms when the product of the pairwise binomial terms is computed


        :param g_partitions:
        :type g_partitions:
        :param w_partitions:
        :type w_partitions:
        :return:
        :rtype:
        """

        w_start = 0
        w_lens = np.count_nonzero(w_partitions, axis=1)
        g_lens = np.count_nonzero(g_partitions, axis=1)

        # build a mask telling us which leading terms are greater than
        # or equal to a given number
        len_mask = [
            np.arange(len(w_partitions))
        ]
        for i in range(1, max(w_lens)+1):
            cur = len_mask[-1]
            new = cur[w_lens[cur] >= i]
            len_mask.append(new)

        permutation_breakpoint = w_partitions[0]//2 + w_partitions[0] % 2
        partition_perm_inds = []
        for i, g in enumerate(g_partitions):
            # need to track _where_ we start in the w_partitions
            ng = g_lens[i]
            w_choice = w_partitions[len_mask[ng]]
            for j, w in enumerate(w_choice):
                if w[0] < g[0]: # I should be able to build a first-element mask
                    break
                if all(gg<=ww for gg,ww in zip(g[1:ng],w[1:ng])): # It's an open question if this can be faster?
                    partition_perm_inds.append([(i, len_mask[ng][j]), None])
                    if w[0] <= permutation_breakpoint:
                        # need to test against permutatons to see if it'll work
                        # TODO: use a bell-ringer pattern but with quick aborts by
                        #       ordering conditions
                        base_perm = np.arange(ng)
                        shift_idx = 0
                        for p in range():
                            ...


    def shift(self, new_origin):
        """
        Uses binomial expansion to new polynomial centered at the `new_origin`

        :param new_origin:
        :type new_origin:
        :return:
        :rtype:
        """
        from ...Combinatorics import Binomial, IntegerPartitionPermutations

        raise NotImplementedError("shifted polys on hold for a moment")

        cur_tensors = self.expansion_tensors
        n = len(cur_tensors)
        new_tensors = [0]*(n+1)

        delta = self.center - new_origin #????
        delta_prime = np.array([
            np.concatenate([delta[:i], [1], delta[i+1:]])
            for i in range(len(delta))
        ]).T

        binomials = Binomial(n+1)
        delta_tensors = np.full((n+1, n+1), None, dtype=object)
        binomial_tensors = np.full((n+1, n+1), None, dtype=object)

        iparts = [IntegerPartitionPermutations(i, dim=len(delta)) if i > 0 else None for i in range(n+1)]
        for g in range(n+1):
            if g > 0:
                gidx = iparts[g].partitions

            for w in range(g, n+1):
                if g > 0:
                    widx = iparts[w].partitions
                    binomial_tensors[w, g] = ...
                    # outer(d[w, g], dp, expand_axes=[w, -1]) -> would otherwise be an outer + a moveaxis
                    delta_tensors[w, g] = np.expand_dims(
                            delta_tensors[w-1, g-1],
                            [-1, w]
                        ) * np.expand_dims(
                            delta_prime,
                            np.concatenate([
                                np.arange(w),
                                np.arange(w, (w-1)+(g-1))
                            ])
                        )

                    D = binomial_tensors[w][g] * delta_tensors[w][g]
                else:
                    delta_tensors[w, 0] = np.expand_dims(
                            delta_tensors[w - 1, 0],
                            [-1]
                        ) * np.expand_dims(
                            delta,
                            np.arange(w)
                        )
                    D = delta_tensors[w][g]

                D *= (-1)**(w-g)

                new_tensors[g] += np.tensordot(cur_tensors[w], D, axes=list(range(w)))








########################################################################################################################
#
#                                           FunctionExpansion
#
class FunctionExpansionException(Exception):
    pass
class FunctionExpansion(TaylorPoly):
    """
    Specifically for expanding functions
    """

    @classmethod
    def expand_function(cls,
                        f, point,
                        order=4,
                        basis=None,
                        function_shape=None,
                        transforms=None,
                        weight_coefficients=True,
                        **fd_options
                        ):
        """
        Expands a function about a point up to the given order

        :param f:
        :type f: function
        :param point:
        :type point: np.ndarray | CoordinateSet
        :param order:
        :type order: int
        :param basis:
        :type basis: None | CoordinateSystem
        :param fd_options:
        :type fd_options:
        :return:
        :rtype:
        """

        derivs = FiniteDifferenceDerivative(f, function_shape=function_shape)(point, **fd_options)
        ref = f(point)
        dts = [derivs.derivative_tensor(i) for i in range(1, order + 1)]
        if transforms is None:
            if basis is not None and isinstance(point, CoordinateSet):
                transforms = [point.jacobian(basis, order=i) for i in range(order)]
            else:
                transforms = None
        return cls(dts, center=point, ref=ref, transforms=transforms, weight_coefficients=weight_coefficients)





