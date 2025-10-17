import abc, numpy as np, scipy.signal, math
import itertools as it
from ..Combinatorics import UniquePermutations, Binomial
from ..Numputils import SparseArray, group_by

__all__ = [
    "AbstractPolynomial",
    "DensePolynomial",
    "SparsePolynomial",
    "PureMonicPolynomial",
    "TensorCoefficientPoly"
]

class AbstractPolynomial(metaclass=abc.ABCMeta):
    """
    Provides the general interface an abstract polynomial needs ot support, including
    multiplication, addition, shifting, access of coefficients, and evaluation
    """

    @property
    @abc.abstractmethod
    def scaling(self):
        raise NotImplementedError("abstract base class")

    @abc.abstractmethod
    def __mul__(self, other)->'AbstractPolynomial':
        raise NotImplementedError("abstract base class")
    @abc.abstractmethod
    def __add__(self, other)->'AbstractPolynomial':
        raise NotImplementedError("abstract base class")

    @abc.abstractmethod
    def shift(self, shift)->'AbstractPolynomial':
        raise NotImplementedError("abstract base class")

    def __rmul__(self, other)->'AbstractPolynomial':
        return self * other
    def __radd__(self, other)->'AbstractPolynomial':
        return self + other
    def __truediv__(self, other)->'AbstractPolynomial':
        return self * (1/other)
    def __neg__(self):
        return -1*self
    def __sub__(self, other):
        return self + (-other)
    def __rsub__(self, other):
        return (-self)+other


    # def __rtruediv__(self, other):
    #     return other * (1/self)


class DensePolynomial(AbstractPolynomial):
    """
    A straightforward dense n-dimensional polynomial data structure with
    multiplications and shifts
    """
    def __init__(self,
                 coeffs,
                 prefactor=None,
                 shift=None,
                 stack_dim=0
                 ):
        self._scaling = prefactor
        self._shift = shift
        self._poly_coeffs = np.asanyarray(coeffs) if not isinstance(coeffs, SparseArray) else coeffs
        self._coeff_tensors = None
        self._uc_tensors = None
        self.stack_dim = stack_dim
    def __repr__(self):
        return "{}({}, {})".format(type(self).__name__, self.coeffs.shape, self.scaling)
    @classmethod
    def from_tensors(cls, tensors, prefactor=None, shift=None, rescale=True):
        coeffs, stack_dim = cls.condense_tensors(tensors, rescale=rescale)
        new = cls(coeffs, prefactor=prefactor, shift=shift, stack_dim=stack_dim)
        return new

    @property
    def shape(self):
        return self._poly_coeffs.shape

    @property
    def scaling(self):
        return 1 if self._scaling is None else self._scaling
    @scaling.setter
    def scaling(self, s):
        self._scaling = s

    @property
    def coeffs(self) -> 'np.ndarray|SparseArray':
        if self._shift is not None:
            self._poly_coeffs = self.compute_shifted_coeffs(self._poly_coeffs, self._shift, stack_dim=self.stack_dim)
            self._shift = None
        if self._scaling is not None:
            self._poly_coeffs = self._poly_coeffs * self._scaling
            self.scaling = None
        return self._poly_coeffs
    @coeffs.setter
    def coeffs(self, cs):
        self._poly_coeffs = cs

    @property
    def coordinate_dim(self):
        return self._poly_coeffs.ndim - self.stack_dim

    @classmethod
    def _manage_stack_bcast(cls, c1, c2, s1, s2):
        if s1 == s2:
            if s1 == 0:
                return c1, c2, 0
            sd = s1
            final_shape = np.broadcast_shapes(c1.shape[:s1], c2.shape[:s2])
            if isinstance(c1, np.ndarray):
                c1 = np.broadcast_to(c1, final_shape + c1.shape[s1:])
            else:
                c1 = c1.broadcast_to(final_shape + c1.shape[s1:])
            if isinstance(c2, np.ndarray):
                c2 = np.broadcast_to(c2, final_shape + c2.shape[s2:])
            else:
                c2 = c2.broadcast_to(final_shape + c2.shape[s2:])
        elif s1 == 0:
            sd = s2
            if isinstance(c1, np.ndarray):
                c1 = np.broadcast_to(np.expand_dims(c1, list(range(s2))), c2.shape[:s2] + c1.shape)
            else:
                c1 = c1.expand_and_broadcast(
                    list(range(s2)),
                    c2.shape[:s2] + c1.shape
                )
        elif s2 == 0:
            sd = s1
            if isinstance(c2, np.ndarray):
                c2 = np.broadcast_to(np.expand_dims(c2, list(range(s1))), c1.shape[:s1] + c2.shape)
            else:
                c2 = c2.expand_and_broadcast(
                    list(range(s1)),
                    c1.shape[:s1] + c2.shape
                )
        else:
            raise ValueError("can't broadcast shapes {} and {}".format(
                c1.shape[:s1],
                c2.shape[:s2]
            ))

        sh1 = c1.shape
        sh2 = c2.shape
        padding = len(sh2) - len(sh1)
        if padding > 0:
            if isinstance(c1, np.ndarray):
                c1 = np.expand_dims(c1, [-x for x in range(1, padding+1)])
            else:
                c1 = c1.expand_dims([-x for x in range(1, padding+1)])
        elif padding < 0:
            padding = -padding
            if isinstance(c2, np.ndarray):
                c2 = np.expand_dims(c2, [-x for x in range(1, padding+1)])
            else:
                c2 = c2.expand_dims([-x for x in range(1, padding+1)])

        return c1, c2, sd

    @classmethod
    def _sparse_convolve_vals_inds(cls,
                                   vals1, vals2,
                                   inds1, inds2,
                                   ):
        # print(inds1)
        # print(inds2)
        vals = (vals1[:, np.newaxis] * vals2[np.newaxis, :]).flatten()
        inds = np.array([
            (i1[:, np.newaxis] + i2[np.newaxis, :]).flatten()
            for i1, i2 in zip(inds1, inds2)
        ])
        # print(inds)
        # print(vals)
        (inds, valsets) = group_by(vals, inds.T)[0]
        vals = np.array([np.sum(v) for v in valsets])
        return inds.T, vals
    @classmethod
    def _sparse_convolve_single(cls, coeffs_1, coeffs_2):
        v1, i1 = coeffs_1.block_data
        v2, i2 = coeffs_2.block_data
        inds, vals = cls._sparse_convolve_vals_inds(
            v1, v2,
            i1, i2
        )
        shp = tuple(c1 + c2 - 1 for c1,c2 in zip(coeffs_1.shape, coeffs_2.shape))
        return SparseArray.from_data(
            (vals, tuple(inds)),
            shape=shp
        )

    @classmethod
    def _sparse_convolve_stacks(cls, coeffs_1, coeffs_2, stack_dim):
        v1, i1 = coeffs_1.block_data
        v2, i2 = coeffs_2.block_data

        stacks_1, inds_1 = group_by(
            np.arange(len(v1)),
            np.array(i1[:stack_dim]).T
        )[0]
        stacks_2, inds_2 = group_by(
            np.arange(len(v2)),
            np.array(i2[:stack_dim]).T
        )[0]

        ind_blocks = [

        ]
        val_blocks = [

        ]
        prev_match = 0
        for s1, pos1 in zip(stacks_1, inds_1):
            for j in range(prev_match, len(stacks_2)):
                if np.all(s1 == stacks_2[j]):
                    prev_match = j
                    pos2 = inds_2[j]
                    if len(pos1) > 0 and len(pos2) > 0:
                        subinds, subvals = cls._sparse_convolve_vals_inds(
                            v1[pos1], v2[pos2],
                            [x[pos1] for x in i1[stack_dim:]], [y[pos2] for y in i2[stack_dim:]]
                        )
                        # now we need to stick copy s1 onto every val to get the stacking right
                        header = tuple(np.full(len(subvals), s) for s in s1)
                        ind_blocks.append(header + tuple(subinds))
                        val_blocks.append(subvals)
                    break

        vals = np.concatenate(val_blocks)
        inds = tuple(
            np.concatenate([ib[j] for ib in ind_blocks])
            for j in range(len(i1))
        )

        shp = coeffs_1.shape[:stack_dim] + tuple(c1 + c2 - 1
                    for c1, c2 in zip(coeffs_1.shape[stack_dim:], coeffs_2.shape[stack_dim:])
                    )
        return SparseArray.from_data(
            (vals, inds),
            shape=shp
        )
    def __mul__(self, other)->'DensePolynomial':
        if isinstance(other, (int, float, np.integer, np.floating)):
            if other == 1:
                return self
            elif other == 0:
                return 0
        if isinstance(other, DensePolynomial):
            # print(self.coeffs.shape, other.coeffs.shape)
            scs, ocs, sd = self._manage_stack_bcast(
                self.coeffs, other.coeffs,
                self.stack_dim, other.stack_dim
            )
            if sd > 0:
                if isinstance(scs, np.ndarray):
                    new_coeffs = np.array([
                        scipy.signal.convolve(s, o)
                        for s,o in zip(
                            scs.reshape((-1,) + scs.shape[sd:]),
                            ocs.reshape((-1,) + ocs.shape[sd:]),
                        )
                    ])
                    new_coeffs = new_coeffs.reshape(scs.shape[:sd] + new_coeffs.shape[1:])
                else:
                    new_coeffs = self._sparse_convolve_stacks(scs, ocs, sd)
            else:
                if isinstance(scs, np.ndarray):
                    new_coeffs = scipy.signal.convolve(scs, ocs)
                else:
                    new_coeffs = self._sparse_convolve_single(scs, ocs)
            return DensePolynomial(
                new_coeffs,
                shift=None,
                prefactor=self.scaling * other.scaling,
                stack_dim=sd
            )
        else:
            return DensePolynomial(
                self._poly_coeffs,
                shift=self._shift,
                prefactor=self.scaling * other
            )

    def _force_consistent_addition_shapes(self, other):
        if self.shape[:self.stack_dim] != other.shape[:other.stack_dim]:
            fcs = self.coeffs #type: np.ndarray | SparseArray
            ocs = other.coeffs #type: np.ndarray | SparseArray
            bcast_shape = (np.zeros(self.shape[:self.stack_dim]) * np.zeros(other.shape[:other.stack_dim])).shape
            if isinstance(fcs, np.ndarray):
                fcs = np.broadcast_to(fcs, bcast_shape + self.shape[self.stack_dim:])
            else:
                fcs = fcs.broadcast_to(bcast_shape + self.shape[self.stack_dim:])
            if isinstance(ocs, np.ndarray):
                ocs = np.broadcast_to(ocs, bcast_shape + other.shape[other.stack_dim:])
            else:
                ocs = ocs.broadcast_to(bcast_shape + other.shape[other.stack_dim:])
        else:
            fcs = self.coeffs
            ocs = other.coeffs
        return fcs, ocs
    @staticmethod
    def _enforce_ndarray_padding(fcs:np.ndarray, consistent_shape, pad_fcs, fc_padding):
        if fc_padding > 0:
            fcs = np.expand_dims(fcs, [-x for x in range(1, fc_padding + 1)])
        fcs = np.pad(fcs,
                     [[0, c - s] for c, s in zip(consistent_shape, pad_fcs)]
                     )
        return fcs
    @staticmethod
    def _enforce_sparse_padding(fcs:SparseArray, consistent_shape, pad_fcs, fc_padding):
        padding = [c - s for c, s in zip(consistent_shape, pad_fcs)]
        if fc_padding > 0:
            if np.sum(padding) == 0:
                fcs = fcs.expand_dims([-x for x in range(1, fc_padding + 1)])
            else:
                fcs = fcs.expand_and_pad(
                    [-x for x in range(1, fc_padding + 1)],
                    padding
                )
        elif np.sum(padding) > 0:
            fcs = fcs.pad_right(padding)
        return fcs
    @classmethod
    def _enforce_addition_padding(cls, fcs, consistent_shape, pad_fcs, fc_padding):
        if isinstance(fcs, np.ndarray):
            return cls._enforce_ndarray_padding(fcs, consistent_shape, pad_fcs, fc_padding)
        else:
            return cls._enforce_sparse_padding(fcs, consistent_shape, pad_fcs, fc_padding)
    def __add__(self, other)->'DensePolynomial':
        if isinstance(other, DensePolynomial):
            stack_dim = max([self.stack_dim, other.stack_dim])

            fcs, ocs = self._force_consistent_addition_shapes(other)
            if self.shape[self.stack_dim:] != other.shape[other.stack_dim:]:  # need to cast to consistent shape
                fc_padding = len(ocs.shape) - len(fcs.shape)
                oc_padding = -fc_padding
                pad_fcs = fcs.shape + tuple(1 for _ in range(fc_padding))
                pad_ocs = ocs.shape + tuple(1 for _ in range(oc_padding))
                consistent_shape = [
                    max(s1, s2)
                    for s1, s2 in zip(
                        pad_fcs,
                        pad_ocs
                    )
                ]

                fcs = self._enforce_addition_padding(fcs, consistent_shape, pad_fcs, fc_padding)
                ocs = self._enforce_addition_padding(ocs, consistent_shape, pad_ocs, oc_padding)

            try:
                fcs + ocs * (other.scaling / self.scaling)
            except:
                raise ValueError(fcs.shape, ocs.shape, (ocs*(other.scaling/self.scaling)).shape)
            return DensePolynomial(
                fcs + ocs*(other.scaling/self.scaling),
                shift=None,
                stack_dim=stack_dim,
                prefactor=self.scaling
            )
        else:
            if isinstance(other, (int, float, np.integer, np.floating)) and other == 0:
                return self

            if self.scaling != 1:
                other = other / self.scaling
            new = self._poly_coeffs.copy().flatten()
            new[0] += other
            new = new.reshape(self._poly_coeffs.shape)
            return DensePolynomial(
                new,
                shift=self._shift,
                prefactor=self.scaling,
                stack_dim=self.stack_dim
            )

    def shift(self, shift)->'DensePolynomial':
        if not isinstance(shift, (int, np.integer, float, np.floating)):
            shift = np.asanyarray(shift)
        return DensePolynomial(
            self._poly_coeffs,
            shift=(0 if self._shift is None else self._shift) + shift,
            prefactor=self._scaling,
            stack_dim=self.stack_dim
        )
    @classmethod
    def compute_shifted_coeffs(cls, poly_coeffs, shift, stack_dim=0):
        #TODO: make this consistent with non-zero stack_dim

        # if fourier_coeffs is None:
        #     raise ValueError("need fourier coeffs for shifted coeff calc")
        if isinstance(shift, (int, float, np.integer, np.floating)):
            shift = [shift]
        shift = np.asanyarray(shift)

        stack_shape = poly_coeffs.shape[:stack_dim]
        poly_shape = poly_coeffs.shape[stack_dim:]
        poly_dim = len(poly_shape)

        # handle broadcasting of shift
        if stack_dim > 0 and shift.ndim == 1 and shift.shape[0] == poly_dim:
            shift = np.expand_dims(shift, list(range(0, stack_dim)))#[0]*stack_dim)
        shift = np.broadcast_to(shift, stack_shape + (poly_dim,))

        # factorial outer product
        factorial_terms = np.array([math.factorial(x) for x in range(poly_shape[0])])
        for s in poly_shape[1:]:
            factorial_terms = np.expand_dims(factorial_terms, -1) * np.reshape(
                np.array([math.factorial(x) for x in range(s)]),
                [1]*factorial_terms.ndim + [s]
            )
        if stack_dim > 0:
            factorial_terms = np.broadcast_to(
                np.expand_dims(factorial_terms, list(range(0, stack_dim))),
                poly_coeffs.shape
            )

        if stack_dim > 0:
            shift = np.moveaxis(shift, -1, 0)
            shift_terms = np.power(
                shift[0][..., np.newaxis],
                np.expand_dims(np.arange(poly_shape[0]), list(range(0, stack_dim)))
            )
            for f,s in zip(shift[1:], poly_shape[1:]):
                shift_terms = np.expand_dims(shift_terms, -1) * np.reshape(
                    np.power(f[..., np.newaxis], np.expand_dims(np.arange(s), list(range(0, stack_dim)))),
                    stack_shape + (1,)*(shift_terms.ndim - stack_dim) + (s,)
                )
        else:
            shift_terms = np.power(shift[0], np.arange(poly_shape[0]))
            for f, s in zip(shift[1:], poly_shape[1:]):
                shift_terms = np.expand_dims(shift_terms, -1) * np.reshape(
                    np.power(f, np.arange(s)),
                    (1,) * shift_terms.ndim + (s,)
                )

        # build shifted polynomial coefficients
        rev_fac = factorial_terms
        for i in range(factorial_terms.ndim - stack_dim):
            rev_fac = np.flip(rev_fac, axis=stack_dim+i)
            shift_terms = np.flip(shift_terms, axis=stack_dim+i)

        poly_terms = poly_coeffs * factorial_terms
        shift_terms = shift_terms / rev_fac

        if not isinstance(poly_terms, np.ndarray):
            # poly_terms = poly_terms #type: SparseArray
            # raise Exception(
            #     len(poly_terms.block_vals) / np.prod(poly_terms.shape)
            # )
            poly_terms = poly_terms.asarray()

        if isinstance(poly_terms, np.ndarray):
            if stack_dim > 0:
                new = np.array([
                    scipy.signal.convolve(p, s)
                    for p,s in zip(
                        poly_terms.reshape((-1,)+poly_shape),
                        shift_terms.reshape((-1,)+poly_shape)
                    )
                ])
                new = new.reshape(stack_shape + new.shape[1:])
            else:
                new = scipy.signal.convolve(
                    poly_terms,
                    shift_terms
                )

            # stack_slice = (slice(None),)*stack_dim
            for i,s in enumerate(poly_shape):
                new = np.take(new, np.arange(-s, 0), axis=stack_dim+i)
            new = new / factorial_terms
        else:
            raise NotImplementedError(...)


        return new

    @classmethod
    def fill_tensors(self, tensors, idx, value, stack_dim, pcache, permute, rescale):
        # we compute the order of the index, compute the number of
        # permutations of the index, and then set all of the permutations
        # equal to the value divided by the number of perms
        order = sum(idx[stack_dim:])
        if order == 0:
            if stack_dim > 0:  # this corresponds to an element of only one of the polynomials
                tensors[0][idx[:stack_dim]] = value
            else:
                tensors[0] = value
        else:
            new_idx = sum(
                ([i] * n for i, n in enumerate(idx[stack_dim:])),
                []
            )  # we figure out which coords are affected and by how much
            if permute:
                idx_key = tuple(new_idx)
                if idx_key not in pcache:
                    final_perms = UniquePermutations(new_idx).permutations()
                    pcache[idx_key] = final_perms
                else:
                    final_perms = pcache[idx_key]
            else:
                final_perms = np.array([new_idx])
            # print(final_perms)
            if rescale:
                subvalue = value / len(final_perms)
            else:
                subvalue = value
            fp_inds = tuple(final_perms.T)
            if stack_dim > 0:  # this corresponds to an element of only one of the polynomials
                extra_idx = idx[:stack_dim]
                nels = len(fp_inds[0])
                bcast_idx = tuple(np.full(nels, i, dtype=int) for i in extra_idx)
                fp_inds = bcast_idx + fp_inds
            tensors[order][fp_inds] = subvalue
    @classmethod
    def extract_tensors(cls, coeffs, stack_dim=None, permute=True, rescale=True, cutoff=1e-15):
        if stack_dim is None:
            stack_dim = 0
            stack_shape = ()
        else:
            stack_shape = coeffs.shape[:stack_dim]

        if isinstance(coeffs, np.ndarray):
            nz_pos = np.where(np.abs(coeffs) > cutoff)
        else:
            nz_pos = coeffs.block_data[1]

        if len(nz_pos) == 0 or len(nz_pos[0]) == 0:
            return [0]
        max_order = np.max(np.sum(nz_pos[stack_dim:], axis=0, dtype=int))
        num_dims = len(coeffs.shape) - stack_dim
        tensors = [
            np.zeros(stack_shape + (num_dims,) * i)
            for i in range(1, max_order + 1)
        ]

        ref = [0] if stack_dim == 0 else [np.zeros(stack_shape)]
        tensors = ref + tensors  # include ref
        pcache = {}

        if isinstance(coeffs, np.ndarray):
            for idx in zip(*nz_pos): # TODO: speed this up...
                value = coeffs[idx]
                cls.fill_tensors(tensors, idx, value, stack_dim, pcache, permute, rescale)
        else:
            vals = coeffs.block_vals
            for vidx in zip(vals, *nz_pos):
                value, idx = vidx[0], vidx[1:]
                cls.fill_tensors(tensors, idx, value, stack_dim, pcache, permute, rescale)

        return tensors
    @classmethod
    def condense_tensors(cls, tensors, rescale=True, allow_sparse=True):
        # we'll be a bit slower here in constructing so we can make sure
        # we get the smallest tensor

        if not isinstance(tensors[0], (int, float, np.integer, np.floating)):
            tensors = [np.asanyarray(t) for t in tensors]
            stack_shape = np.asanyarray(tensors[0]).shape
        else:
            tensors = [tensors[0]] + [np.asanyarray(t) for t in tensors[1:]]
            stack_shape = ()
        stack_dim = len(stack_shape)

        # order = len(tensors)
        if len(tensors) == 1:
            raise NotImplementedError("constant polynomial support coming")

        ncoord = tensors[1].shape[-1]
        tensor_elems = {}
        shape = [1] * ncoord
        # we could be more efficient through where tricks if we wanted
        for o,t in enumerate(tensors):
            if o == 0:
                for idx in zip(*np.where(t != 0)):
                    tidx = idx + (0,)*ncoord
                    tensor_elems[tidx] = t[idx]
            else:
                utri_pos = tuple(np.array(list(it.combinations_with_replacement(range(ncoord), r=o))).T)
                if stack_dim > 0:
                    utri_pos = (slice(None),)*stack_dim + utri_pos
                vals = t[utri_pos]
                nz_pos = np.where(vals != 0)
                for p in zip(*nz_pos):
                    val = vals[p]
                    upos = [u[p[-1]] for u in utri_pos[stack_dim:]]
                    idx = tuple(np.bincount(upos, minlength=ncoord))
                    if rescale:
                        val = val * UniquePermutations.count_permutations(idx)
                    tidx = p[:-1] + idx
                    tensor_elems[tidx] = val
                    for n, i in enumerate(idx):
                        shape[n] = max(i + 1, shape[n])

        # raise Exception(shape)
        shp = stack_shape + tuple(shape)
        if allow_sparse:
            nv = len(tensor_elems)
            density = nv / np.prod(shp)
            allow_sparse = density < .5
        if allow_sparse:
            inds = tuple(np.array(list(tensor_elems.keys())).T)
            vals = np.array(list(tensor_elems.values()))
            condensed_tensor = SparseArray.from_data(
                (
                    vals,
                    inds
                ),
                shape=shp
            )
        else:
            condensed_tensor = np.zeros(shp)
            for idx,val in tensor_elems.items():
                condensed_tensor[idx] = val
        return condensed_tensor, stack_dim

    @property
    def coefficient_tensors(self):
        if self._coeff_tensors is None:
            self._coeff_tensors = self.extract_tensors(self.coeffs, stack_dim=self.stack_dim)
        return self._coeff_tensors
    @property
    def unscaled_coefficient_tensors(self):
        if self._uc_tensors is None:
            self._uc_tensors = self.extract_tensors(self.coeffs, rescale=False, stack_dim=self.stack_dim)
        return self._uc_tensors
    def transform(self, lin_transf):
        """
        Applies (for now) a linear transformation to the polynomial
        """
        #TODO: make this consistent with non-zero stack_dim
        if self.stack_dim != 0:
            raise NotImplementedError("need to make work with non-zero stack dims")

        tensors = self.coefficient_tensors
        transf_tensors = []
        for n,t in enumerate(tensors):
            for ax in range(n):
                t = np.tensordot(lin_transf, t, axes=[1, n-1])
            transf_tensors.append(t)
        new = self.condense_tensors(transf_tensors)
        return DensePolynomial(new)

    def outer(self, other):
        if self.stack_dim != 0 or other.stack_dim != 0:
            raise NotImplementedError("need to make work with non-zero stack dims")
        return DensePolynomial(
            np.multiply.outer(self.coeffs, other),
            prefactor=self.scaling*other.scaling
        )

    @classmethod
    def _coord_deriv(cls, coeffs, coord, stack_dim):
        coord = coord + stack_dim
        if coeffs.shape[coord] == 1:
            return 0
        n = coeffs.shape[coord]
        scaling = np.arange(1, n)
        scaling = np.expand_dims(scaling, list(range(coord)) + list(range(coord+1, coeffs.ndim)))
        new_coeffs = scaling * np.take(coeffs, np.arange(1, n), axis=coord)
        return new_coeffs
    def deriv(self, coord):
        if self._poly_coeffs.shape[self.stack_dim + coord] == 1:
            return 0
        new_coeffs = self._coord_deriv(self.coeffs, coord, self.stack_dim)
        return DensePolynomial(
            new_coeffs,
            prefactor=self.scaling,
            stack_dim=self.stack_dim
        )

    @classmethod
    def _apply_dense_grad(cls, coeffs, stack_dim ,shape, n, c):
        new_shape = shape[:stack_dim] + (n,) + c
        new_coeffs = np.zeros(new_shape)
        for i in range(n):
            sub_coeffs = cls._coord_deriv(coeffs, i, stack_dim)
            if not isinstance(sub_coeffs, np.ndarray):
                if sub_coeffs != 0: raise ValueError("...?")
                continue
            # construct slice spec for inserting into new coeffs
            insert_spec = (
                # [i, :, ..., :, :-1, :, ..., :]
                    (slice(None),) * stack_dim
                    + (i,)
                    + (slice(None),) * i
                    + (slice(None, c[i] - 1),)
                    + (slice(None),) * (n - (i + 1))
            )
            new_coeffs[insert_spec] = sub_coeffs

        return new_coeffs

    @classmethod
    def _take_sparse_position_derivs(cls, stack_dim, axis, nzvals, nzinds):
        axis = axis + stack_dim
        ax_inds = nzinds[axis]
        if np.sum(ax_inds) == 0: return 0 # quick fall through
        good_pos = np.where(ax_inds > 0)
        nzvals = nzvals[good_pos]
        ax_inds = ax_inds[good_pos]
        new_ax = ax_inds - 1
        nzvals = nzvals * ax_inds
        nzinds = tuple(
            nzinds[i][good_pos]
                if i != axis else
            new_ax
            for i in range(len(nzinds))
        )
        return nzvals, nzinds
    @classmethod
    def _apply_sparse_grad(cls, coeffs:SparseArray, stack_dim, shape, n, c):
        block_vals, block_inds = coeffs.block_data
        new_stuff = [
            cls._take_sparse_position_derivs(stack_dim, i, block_vals, block_inds)
            for i in range(n)
        ]
        if all(isinstance(x, int) and x==0 for x in new_stuff):
            return SparseArray.empty(shape[:stack_dim] + (n,))

        final_vals = np.concatenate([
            vals_inds[0] for vals_inds in new_stuff
            if not (isinstance(vals_inds, int) and vals_inds == 0)
        ])
        stack_inds = tuple(
            np.concatenate([
                vals_inds[1][i] for vals_inds in new_stuff
                if not (isinstance(vals_inds, int) and vals_inds == 0)
            ])
            for i in range(stack_dim)
        )
        new_inds = np.concatenate([
            np.full(len(vals_inds[0]), i, dtype='uint8')
            for i,vals_inds in enumerate(new_stuff)
            if not (isinstance(vals_inds, int) and vals_inds == 0)
        ])
        rem_inds = tuple(
            np.concatenate([
                vals_inds[1][i] for vals_inds in new_stuff
                if not (isinstance(vals_inds, int) and vals_inds == 0)
            ])
            for i in range(stack_dim, len(shape))
        )
        final_inds = stack_inds + (new_inds,) + rem_inds

        new_shape = shape[:stack_dim] + (n,) + c
        return SparseArray.from_data(
            (
                final_vals,
                final_inds
            ),
            shape=new_shape
        )

    @classmethod
    def _apply_grad(cls, coeffs, stack_dim):
        shape = coeffs.shape
        n = coeffs.ndim - stack_dim
        c = shape[stack_dim:]

        if isinstance(coeffs, SparseArray):
            new_coeffs = cls._apply_sparse_grad(coeffs, stack_dim, shape, n, c)
        else:
            new_coeffs = cls._apply_dense_grad(coeffs, stack_dim, shape, n, c)

        return new_coeffs

    def grad(self):

        return DensePolynomial(
            self._apply_grad(self.coeffs, self.stack_dim),
            prefactor=self._scaling,
            stack_dim=self.stack_dim+1
        )

    def clip(self, threshold=1e-15):
        clipped_inds = np.where(np.abs(self.coeffs * self.scaling) > threshold)
        if len(clipped_inds) == 0 or len(clipped_inds[0]) == 0:
            return 0
        new_shape = tuple(max(x) + 1 for x in clipped_inds)
        coeffs = np.zeros(new_shape)
        coeffs[clipped_inds] = self.coeffs[clipped_inds]
        return DensePolynomial(
            coeffs,
            prefactor=self._scaling,
            stack_dim=self.scaling
        )

    def make_sparse_backed(self, threshold=1e-15):
        base = SparseArray.from_data(self.clip(threshold).coeffs)
        return type(self)(
            base,
            prefactor=self._scaling,
            stack_dim=self.stack_dim
        )
    
class SparsePolynomial(AbstractPolynomial):
    """
    A semi-symbolic representation of a polynomial of tensor
    coefficients
    """
    def __init__(self, terms:dict, prefactor=1, ndim=None, canonicalize=True):
        self.terms = terms
        self.prefactor = prefactor
        self._ndim = ndim
        self._shape = None

    @property
    def scaling(self):
        return 1 if self.prefactor is None else self.prefactor
    @scaling.setter
    def scaling(self, s):
        self.prefactor = s

    def expand(self):
        if self.prefactor == 1:
            return self
        else:
            return type(self)({k:self.prefactor*v for k,v in self.terms.items()}, prefactor=1,
                              canonicalize=False)
    @classmethod
    def monomial(cls, idx, value=1):
        return cls({idx:value})
    def __repr__(self):
        return "{}({},{})".format(type(self).__name__, self.terms,self.prefactor)

    def __mul__(self, other):
        if isinstance(other, (int, float, np.integer, np.floating)):
            if other == 1:
                return self
            elif other == 0:
                return SparsePolynomial({})
        if isinstance(other, SparsePolynomial):
            new_terms = {}
            for k,v in other.terms.items():
                for k2,v2 in self.terms.items():
                    t = tuple(sorted(k + k2))
                    new_terms[t] = new_terms.get(t, 0) + v * v2
                    if new_terms[t] == 0:
                        del new_terms[t]
            return type(self)(new_terms, prefactor=self.prefactor*other.prefactor)
        else:
            return type(self)(self.terms, prefactor=self.prefactor*other)
            # new_terms = {}
            # for k,v in self.terms.items():
            #     new_terms[k] = self.prefactor*other*v
            # return SparsePolynomial(new_terms)
    def __add__(self, other):
        if isinstance(other, (int, float, np.integer, np.floating)):
            if other == 0:
                return self
            else:
                return self + type(self)({():other})
        else:
            self = self.expand()
            new_terms = {}
            if isinstance(other, SparsePolynomial):
                other = other.expand()
                for s in other.terms.keys() & self.terms.keys():
                    v = other.terms[s]
                    v2 = self.terms[s]
                    new = v + v2
                    if new != 0:
                        new_terms[s] = new
                for o in other.terms.keys() - self.terms.keys():
                    new_terms[o] = other.terms[o]
                for o in self.terms.keys() - other.terms.keys():
                    new_terms[o] = self.terms[o]
            else:
                for k2, v2 in self.terms.items():
                    new = v2 + other
                    if new != 0:
                        new_terms[k2] = new
            if len(new_terms) == 0:
                return 0
            return type(self)(new_terms, canonicalize=False)

    @classmethod
    def _to_tensor_idx(cls, term, ndim, tupleate=True):
        base = np.zeros(ndim, dtype=int)
        for idx, cnt in zip(*np.unique(term, return_counts=True)): #TODO: kinda dumb to do this 2x but w/e
            base[idx] = cnt
        if tupleate:
            return tuple(base)
        else:
            return base
        # idx_terms = {}
        # m = 0
        # for t in idx:
        #     m = max(m, t)
        #     idx_terms[t] = idx_terms.get(t, 0) + 1
        # return tuple(idx_terms[t] for t in range(m))
    @property
    def shape(self):
        if self._shape is None:
            max_dims = {}
            for t in self.terms.keys():
                for idx,cnt in zip(*np.unique(t, return_counts=True)): # can I assume sorted?
                    max_dims[idx] = max(max_dims.get(idx, 1), cnt + 1)
            if self._ndim is None:
                max_key = max(list(max_dims.keys()))
            else:
                max_key = self._ndim - 1
            self._shape = tuple(max_dims.get(k, 1) for k in range(max_key+1))
        return self._shape
    def as_dense(self)->DensePolynomial:
        new_coeffs = np.zeros(self.shape)
        ndim = new_coeffs.ndim
        for key, val in self.terms.items():
            idx = self._to_tensor_idx(key, ndim)
            new_coeffs[idx] = val
        return DensePolynomial(
            new_coeffs,
            prefactor=self.prefactor
        )

    def _get_sparse_shift_terms(self, term_vector, shift_vector) -> dict:
        """
        Provides the set of terms corresponding to shifting a term of the form
         `prod(x[i]**p[i])` (where `p` is the `term_vector`) by the corresponding `shift_vector`


        :param term_vector:
        :param shift_vector:
        :return:
        """

        max_dim = np.max(term_vector)
        if max_dim == 0:
            return {():1}
        bin_mat = Binomial(np.max(term_vector)+1)
        inds = np.moveaxis(np.indices(term_vector+1), 0, -1).reshape(-1, term_vector.shape[0])
        rp_binoms = bin_mat[term_vector[np.newaxis, :], inds]
        term_diffs = term_vector[np.newaxis, :] - inds
        rp_shifts = shift_vector[np.newaxis, :] ** term_diffs
        # rp_binoms[:, term_vector == 0] = 0 # shift shouldn't contribute here

        new_terms = {}
        full_terms = np.prod(rp_shifts*rp_binoms, axis=-1)
        for idx, t in zip(inds, full_terms):
            key = sum(( (i,)*n for i,n in enumerate(idx) ), ())
            new_terms[key] = t

        return new_terms
    def shift(self, shift)->'SparsePolynomial':
        shift = np.asanyarray(shift)

        new_terms = {}
        ndim = len(self.shape)
        for term,scaling in self.terms.items():
            idx = self._to_tensor_idx(term, ndim, tupleate=False)
            # print(ndim, idx, term)
            subterms = self._get_sparse_shift_terms(idx, shift)
            # print(scaling, subterms)
            for s in subterms.keys() & new_terms.keys():
                v = scaling*subterms[s]
                v2 = new_terms[s]
                new = v + v2
                if new != 0:
                    new_terms[s] = new
            for o in subterms.keys() - new_terms.keys():
                new_terms[o] = scaling*subterms[o]
            for o in new_terms.keys() - subterms.keys():
                new_terms[o] = new_terms[o]

        return type(self)(
            new_terms,
            prefactor=self.scaling,
            ndim=ndim
        )


class PureMonicPolynomial(SparsePolynomial):
    def __init__(self, terms: dict, prefactor=1, canonicalize=True):
        if canonicalize:
            new_terms = {}
            for k,v in terms.items():
                k = self.canonical_key(k)
                new_terms[k] = new_terms.get(k, 0) + v
            terms = new_terms
        super().__init__(terms, prefactor)

    @property
    def shape(self):
        raise ValueError("{} doesn't have a dense counterpart".format(type(self).__name__))
    def as_dense(self):
        raise ValueError("{} doesn't have a dense counterpart".format(type(self).__name__))
    def shift(self, shift) -> DensePolynomial:
        raise ValueError("{} doesn't have a dense counterpart".format(type(self).__name__))

    @classmethod
    def monomial(cls, idx, value=1):
        return cls({(idx,): value})

    @classmethod
    def key_hash(cls, monomial_tuple):
        # hashes tuples of indices to give a fast check that the tuples
        # are the same independent of ordering
        return sum(hash(x) for x in monomial_tuple)

    @classmethod
    @abc.abstractmethod
    def canonical_key(cls, monomial_tuple):
        raise NotImplementedError("{} is abstract".format(cls.__name__))

    def direct_multiproduct(self, other, key_value_generator):
        if not isinstance(other, PureMonicPolynomial):
            raise TypeError("doesn't make sense")

        new_terms = {}
        term_hashes = {}
        for k, v in self.terms.items():
            for k2, v2 in other.terms.items():
                for k3, v3 in key_value_generator(k, k2, v, v2):
                    # new_hash = self.key_hash(k3) #+ self.key_hash(k2)
                    # if new_hash in term_hashes:
                    #     t = term_hashes[new_hash]
                    #     if t != self.canonical_key(k3):
                    #         raise ValueError(k, k2, t, self.canonical_key(k3))
                    # else:
                    #     t = self.canonical_key(k3)  # construct new tuple and canonicalize
                    #     term_hashes[new_hash] = t
                    t = self.canonical_key(k3) # caching this led to collisions, need better tuple hashes
                    new_terms[t] = new_terms.get(t, 0) + v3  # this is the case where after mult. two terms merge
                    if new_terms[t] == 0:
                        del new_terms[t]
        if self.prefactor is None:
            pref = other.prefactor
        elif other.prefactor is None:
            pref = self.prefactor
        else:
            pref = self.prefactor * other.prefactor
        return type(self)(new_terms, prefactor=pref, canonicalize=False)
    def direct_product(self, other, key_func=None, mul=None):
        if isinstance(other, (int, float, np.integer, np.floating)):
            if other == 1:
                return self
            elif other == 0:
                return 0
                # return type(self)({})
        if isinstance(other, PureMonicPolynomial):
            if mul is None:
                mul = lambda a,b:a*b
            if key_func is None:
                key_func = lambda key1,key2:k+k2
            new_terms = {}
            term_hashes = {}
            for k,v in self.terms.items():
                for k2,v2 in other.terms.items():
                    new_hash = self.key_hash(k) + self.key_hash(k2)
                    if new_hash in term_hashes:
                        t = term_hashes[new_hash]
                    else:
                        t = self.canonical_key(key_func(k, k2)) # construct new tuple and canonicalize
                        term_hashes[new_hash] = t
                    new_terms[t] = new_terms.get(t, 0) + mul(v, v2) # this is the case where after mult. two terms merge
                    if new_terms[t] == 0:
                        del new_terms[t]
            if self.prefactor is None:
                pref = other.prefactor
            elif other.prefactor is None:
                pref = self.prefactor
            else:
                pref = self.prefactor*other.prefactor
            return type(self)(new_terms, prefactor=pref, canonicalize=False)
        else:
            return type(self)(self.terms, prefactor=self.prefactor*other if self.prefactor is not None else other, canonicalize=False)

    def rebuild(self, new_terms, prefactor=None, canonicalize=None):
        return type(self)(new_terms,
                          prefactor=self.prefactor if prefactor is None else prefactor,
                          canonicalize=False if canonicalize is None else canonicalize
                          )

    def filter(self, keys, mode='match'):
        if mode == 'match':
            return self._filter_exact(keys)
        elif mode == 'include':
            return self._filter_include(keys)
        elif mode == 'exclude':
            return self._filter_exclude(keys)
        else:
            raise ValueError("bad mode '{}'".format(mode))
    def _filter_exact(self, test_keys):
        subterms = {}
        test_terms = self.terms
        for t, v in test_terms.items():
            test_t = t
            for required_keys in test_keys:
                for k in required_keys:
                    if k in test_t:
                        i = test_t.index(k)
                        test_t = test_t[:i] + test_t[i + 1:]
                    else:
                        break
                else:
                    subterms[t] = v

        return self.rebuild(subterms)
    def _filter_include(self, test_keys):
        subterms = {}
        test_terms = self.terms
        test_keys = set(test_keys)
        for t, v in test_terms.items():
            for k in t:
                if k not in test_keys:
                    break
            else:
                subterms[t] = v

        return self.rebuild(subterms)
    def _filter_exclude(self, test_keys):
        subterms = {}
        test_terms = self.terms
        test_keys = set(test_keys)
        for t, v in test_terms.items():
            for k in test_keys:
                if k in t:
                    break
            else:
                subterms[t] = v

        return self.rebuild(subterms)

    def __mul__(self, other):
        return self.direct_product(other)
class TensorCoefficientPoly(PureMonicPolynomial):
    """
    Represents a polynomial constructed using tensor elements as monomials
    by tracking sets of indices
    """

    @classmethod
    def canonical_key(cls, monomial_tuple):
        # we need a way to sort indices, which we do by grouping by key length,
        # doing a standard sort for each length, and reconcatenating
        s_groups = {}
        for index_tuple in monomial_tuple:
            l = len(index_tuple)
            grp = s_groups.get(l, [])
            s_groups[l] = grp
            grp.append(index_tuple)
        t = tuple(
            grp
            for l in sorted(s_groups.keys())
            for grp in sorted(s_groups[l])
        )
        return t

# class TensorCoeffPoly(AbstractPolynomial):
#     """
#     A semi-symbolic representation of a polynomial of tensor
#     coefficients
#     """
#
#     def __init__(self, terms:dict, prefactor=1):
#         self.terms = terms
#         self.prefactor = prefactor
#     def expand(self):
#         if self.prefactor == 1:
#             return self
#         else:
#             return TensorCoeffPoly({k:self.prefactor*v for k,v in self.terms.items()}, prefactor=1)
#     @classmethod
#     def monomial(cls, idx, value=1):
#         return cls({(idx,):value})
#     def __repr__(self):
#         return "{}({},{})".format(type(self).__name__, self.terms,self.prefactor)