import collections
import itertools, numpy as np, math
# import uuid

from .. import Devutils as dev

from . import PermutationOps as perms
from . import VectorOps as vec_ops
from . import SetOps as set_ops
from .Misc import is_numeric, is_zero

__all__ = [
    "nca_op_deriv",
    "tensordot_deriv",
    "tensorprod_deriv",
    "scalarprod_deriv",
    "inverse_transformation",
    "optimizing_transformation",
    "matinv_deriv",
    "matdet_deriv",
    "matsqrt_deriv",
    "scalarinv_deriv",
    "scalarpow_deriv",
    "tensor_reexpand",
    "tensorops_deriv",
    "vec_norm_unit_deriv",
    "vec_angle_deriv",
    "vec_cross_deriv",
    "vec_anglecos_deriv",
    "vec_anglesin_deriv",
    "vec_dihed_deriv",
    "vec_plane_angle_deriv",
    "shift_expansion",
    "scale_expansion",
    "add_expansions",
    "subtract_expansions"
]

# levi_cevita3.__name__ = "levi_cevita3"
# levi_cevita3.__doc__ = """
#     The 3D Levi-Cevita tensor.
#     Used to turn cross products into matmuls
#     """



def get_nca_shifts(order, k):
    permute_pos = np.arange(k)
    ncombs = math.comb(order, k)
    shifts = np.broadcast_to(np.arange(order)[np.newaxis], (ncombs, order)).copy()
    for i,pos in enumerate(itertools.combinations(range(order), r=k)):
        shifts[i, pos] = permute_pos
    return shifts
def apply_nca_op(op, order, k,
                 A_expansion, B_expansion, deriv_axis,
                 a, b, contract, shared, identical,
                 root_dim=2
                 ):
    s = order - k
    if s >= len(A_expansion) or k >= len(B_expansion):
        return 0

    A = A_expansion[s]
    B = B_expansion[k]
    for T in [A, B]:
        if (
            is_zero(T)
            or (T.shape == () and T == 0)
        ):
            return 0
    if shared is None:
        shared = 0
    if contract: # axes disappear, so we just account for the shifts
        axes = [[x+s for x in a], [x+k for x in b]]
    else: # axes appeared, so we need to include those in the product
          # we _forced_ axes to be at the end of the arrays since it was too hard
          # to keep track of them otherwise...
          # actually I guess I could have put the derivative axes at the end...
          # and then the axes would never change...but that has other complications
        axes = [
            [shared + i for i in range(s)] + [x+s for x in a],
            [shared + i for i in range(k)] + [x+k for x in b]
        ]

    if shared == 0:
        base = op(A, B, axes=axes)
    else:
        base = op(A, B, axes=axes, shared=shared)

    # next we need to move all of the derivative axes in the second tensor to the beginning
    # so we can symmetrize
    d = deriv_axis + s
    sa = (A.ndim - len(axes[0]) if contract else A.ndim)
    for i in range(k):
        base = np.moveaxis(base, d+i, sa)
    part = [x for x in [s, k] if x > 0]
    if len(part) > 1:
        base = nca_symmetrize(base, part, contract=contract, shared=shared, identical=identical)
    return base
def nca_op_order_deriv(op, order, A_expansion, B_expansion, deriv_axis, a, b, contract, shared, identical):
    full = None
    for k in range(order+1):
        term = apply_nca_op(op, order, k, A_expansion, B_expansion, deriv_axis, a, b, contract, shared, identical)
        if full is None:
            full = term
        else:
            full = full + term
    return full
def nca_op_deriv(op,
                 A_expansion,
                 B_expansion,
                 order,
                 axes,
                 contract,
                 shared=None,
                 identical=False
                 ):
    A_expansion = [np.asanyarray(A) for A in A_expansion]
    B_expansion = [np.asanyarray(B) for B in B_expansion]

    a_ax, b_ax = axes
    if isinstance(a_ax, int): a_ax = [a_ax]
    if isinstance(b_ax, int): b_ax = [b_ax]
    a_ax = [ a if a >= 0 else A_expansion[0].ndim + a for a in a_ax ]
    b_ax = [ b if b >= 0 else B_expansion[0].ndim + b for b in b_ax ]

    if contract: # the derivative axis will always be at nA + 1 - num_contracted - the shared axes
        deriv_axis = A_expansion[0].ndim - len(a_ax)
    else:
        # we require that the outer product be ordered
        # so we now which axes to move around
        a_ax = np.sort(a_ax)
        a_dim = A_expansion[0].ndim
        if np.any(a_ax != np.arange(a_dim - len(a_ax), a_dim)):
            raise ValueError("axes {} must be the final axes of A".format(a_ax))
        b_ax = np.sort(b_ax)
        b_dim = B_expansion[0].ndim
        if np.any(b_ax != np.arange(b_dim - len(b_ax), b_dim)):
            raise ValueError("axes {} must be the final axes of B".format(b_ax))
        deriv_axis = a_dim

    if isinstance(order, int):
        order = list(range(1, order+1))

    # if shared is not None:
    #     deriv_axis = deriv_axis - shared

    derivs = [
        nca_op_order_deriv(op, o, A_expansion, B_expansion, deriv_axis, a_ax, b_ax,
                           contract, shared, identical
                           )
        for o in order
    ]

    return derivs

def _deriv_construct(zero_order_handler, expansion_generator, order):
    if is_numeric(order):
        order = list(range(order+1))
    high_order_expansion = expansion_generator([o for o in order if o > 0])

    # a lot of work to make sure we can do derivatives at a specifically targeted order
    n = 0
    final_expansion = []
    for o in order:
        if o == 0:
            final_expansion.append(
                zero_order_handler()
            )
        else:
            final_expansion.append(high_order_expansion[n])
            n += 1
    return final_expansion

def _clean_vdot(a, b, *, axes, shared=None):
    return (
        0
            if is_zero(a) or is_zero(b) else
        vec_ops.vec_tensordot(a, b, axes=axes, shared=shared)
    )
def _clean_tdot(a, b, *, axes, shared=None):
    return (
        0
            if is_zero(a) or is_zero(b) else
        np.tensordot(a, b, axes=axes)
    )
def tensordot_deriv(A_expansion, B_expansion,
                    order,
                    axes=None,
                    shared=None,
                    identical=False
                    ):

    if len(A_expansion) == 0 or len(B_expansion) == 0:
        return [0]*((order+1) if is_numeric(order) else len(order))

    if axes is None: axes = [-1, 0]
    if shared is not None and shared > 0:
        base_op = _clean_vdot
    else:
        base_op = _clean_tdot
    op = base_op
    return _deriv_construct(
        lambda : op(A_expansion[0], B_expansion[0], axes=axes, shared=shared),
        lambda ords: nca_op_deriv(op,
                     A_expansion, B_expansion,
                     ords,
                     axes=axes,
                     contract=True,
                     shared=shared,
                     identical=identical
                     ),
        order
    )

def prep_prod_arrays(A_expansion, a_ax):
    _ = []
    for n,a in enumerate(A_expansion):
        a = np.asanyarray(a)
        for x in a_ax:
            x = (a.ndim + x) if x < 0 else (x + n)
            a = np.moveaxis(a, x, -1)
        _.append(a)
    return _
def pre_broadcast_prod(A_expansion, B_expansion, axes):

    a_ax, b_ax = axes
    if isinstance(a_ax, int): a_ax = [a_ax]
    if isinstance(b_ax, int): b_ax = [b_ax]

    A_expansion = prep_prod_arrays(A_expansion, a_ax)
    B_expansion = prep_prod_arrays(B_expansion, b_ax)

    expand_dims = ...

def _clean_outer(left, right, *, axes, shared=None):
    return (
        0
            if is_zero(left) or is_zero(right) else
        vec_ops.vec_outer(left, right, axes=axes, order=0)
    )
def tensorprod_deriv(
        A_expansion, B_expansion,
        order,
        axes=None,
        identical=False
):
    if len(A_expansion) == 0 or len(B_expansion) == 0:
        return [0]*((order+1) if is_numeric(order) else len(order))
    if axes is None:
        axes = [-1, -1]
    elif isinstance(axes, str) and axes == 'all':
        axes = [np.arange(A_expansion[0].ndim), np.arange(B_expansion[0].ndim)]
    a_ax, b_ax = axes
    if isinstance(a_ax, int): a_ax = [a_ax]
    if isinstance(b_ax, int): b_ax = [b_ax]
    # a_ax, b_ax = pre_broadcast_prod(A_expansion, B_expansion, axes)

    shared = A_expansion[0].ndim - len(a_ax)
    # if is_numeric(A_expansion[0]) or is_numeric(B_expansion[0]):
    #     # scalar product
    #     return scalarprod_deriv(A_expansion, B_expansion, order, identical=identical)

    A_expansion = [np.asanyarray(a) for a in A_expansion]
    B_expansion = [np.asanyarray(b) for b in B_expansion]
    op = _clean_outer
    return _deriv_construct(
        lambda: op(A_expansion[0], B_expansion[0], axes=axes, shared=shared),
        lambda ords: nca_op_deriv(op,
                                  A_expansion, B_expansion,
                                  ords,
                                  axes=[a_ax, b_ax],
                                  contract=False,
                                  shared=shared,
                                  identical=identical
                                  ),
        order
    )

def _scalar_prod(a, b, axes=None, shared=None):
    if is_numeric(a) or is_numeric(b):
        if is_zero(a) or is_zero(b):
            return 0
        else:
            return a * b
    else:
        if shared is None:
            shared = 0
        return vec_ops.vec_outer(a, b, axes=[list(range(shared, a.ndim)), list(range(shared, b.ndim))], order=0)

def scalarprod_deriv(s_expansion, A_expansion,
                     order,
                     identical=False
                     ):
    s_expansion = [np.asarray(s) for s in s_expansion]
    A_expansion = [np.asarray(a) for a in A_expansion]
    s0_shape = s_expansion[0].shape if len(s_expansion) > 0 else ()
    A0_shape = A_expansion[0].shape if len(A_expansion) > 0 else ()
    shared = min([len(s0_shape), len(A0_shape)])
    terms = tensorprod_deriv(
        s_expansion,
        A_expansion,
        order=order,
        identical=identical,
        axes=[
            np.arange(shared, s_expansion[0].ndim),
            np.arange(shared, A_expansion[0].ndim)
        ]
    )
    return terms

    if is_numeric(order):
        order = list(range(order+1))
    suborder = [o for o in order if o > 0]
    # s_expansion, A_expansion = pre_broadcast_scalar_mult(s_expansion, A_expansion)
    if is_numeric(A_expansion[0]):
        if is_numeric(s_expansion[0]):
            base_expansion = scalarprod_deriv(s_expansion, A_expansion[1:],
                                              [o - 1 for o in suborder],
                                              identical=identical)
        else:
            shared = min([s_expansion[0].ndim, A_expansion[0].ndim])
            base_expansion = tensorprod_deriv(s_expansion, A_expansion[1:],
                                              [o - 1 for o in suborder],
                                              identical=identical,
                                              axes=[
                                                  np.arange(shared, s_expansion[0].ndim),
                                                  np.arange(shared, A_expansion[0].ndim)
                                              ])
        rem_expansion = [
            _scalar_prod(s_expansion[o], A_expansion[0])
                if len(s_expansion) > o else 0
            for o in suborder
        ]
    elif not is_numeric(s_expansion[0]):
        shared = min([s_expansion[0].ndim, A_expansion[0].ndim])
        return tensorprod_deriv(s_expansion, A_expansion,
                                order,
                                identical=identical,
                                axes=[
                                    np.arange(shared, s_expansion[0].ndim),
                                    np.arange(shared, A_expansion[0].ndim)
                                ])
    else:
        base_expansion = tensorprod_deriv(s_expansion[1:], A_expansion,
                                          order=[o - 1 for o in suborder],
                                          axes=[
                                              np.arange(s_expansion[1].ndim),
                                              np.arange(A_expansion[0].ndim)
                                          ],
                                          identical=identical)
        rem_expansion = [
            _scalar_prod(s_expansion[0], A_expansion[o]) if len(A_expansion) > o else 0
            for o in suborder
        ]
    high_order_expansion = [x + y for x, y in zip(base_expansion, rem_expansion)]

    # a lot of work to make sure we can do derivatives at a specifically targeted order
    n = 0
    final_expansion = []
    for o in order:
        if o == 0:
            final_expansion.append(_scalar_prod(s_expansion[0], A_expansion[0]))
        else:
            final_expansion.append(high_order_expansion[n])
            n += 1
    return final_expansion

def scalarfunc_deriv(scalar_func, arg_expansion, order):
    scalar_expansion = [scalar_func(arg_expansion[0], i) for i in range(order+1)]
    return [scalar_expansion[0]] + scalarprod_deriv(scalar_expansion[1:], arg_expansion[1:], order)

def shift_expansion(expansion, scalar):
    return [expansion[0] + scalar] + list(expansion[1:])

def scale_expansion(expansion, scalar):
    if scalar == -1:
        return [-e for e in expansion] # can be faster
    elif is_zero(scalar):
        return [0 for e in expansion]
    else:
        return [scalar * e for e in expansion]

def add_expansions(*expansions, order=None):
    if order is None:
        order = max(len(e) for e in expansions) - 1
    o = order + 1
    pad_expansions = [
        list(e) + [0]*(o - len(e))
        for e in expansions
    ]
    return [
        sum(x for x in e if not is_zero(x))
        for e in zip(*pad_expansions)
    ]

def subtract_expansions(a_expansion, b_expansion, order=None):
    if order is None:
        order = max([len(a_expansion), len(b_expansion)]) - 1
    o = order + 1
    a_expansion, b_expansion = [
        list(e) + [0]*(o - len(e))
        for e in [a_expansion, b_expansion]
    ]
    return [
        a - b
        for a,b in zip(a_expansion, b_expansion)
    ]

#TODO: add a DifferentiableExpansion class so I can have nicer overloads on all of this...

def inverse_transformation(forward_expansion, order, reverse_expansion=None, allow_pseudoinverse=False):
    if reverse_expansion is None:
        if allow_pseudoinverse and forward_expansion[0].shape[0] != forward_expansion[0].shape[1]:
            B = np.linalg.pinv(forward_expansion[0])
        else:
            B = np.linalg.inv(forward_expansion[0])
        reverse_expansion = [B]
    else:
        reverse_expansion = list(reverse_expansion)
        B = reverse_expansion[0]

    if not is_numeric(order): order = np.max(order)
    order = list(range(2, order+1))
    shared = B.ndim - 2

    for o in order:
        new_B = -tensor_reexpand(reverse_expansion, forward_expansion, [o])[-1]
        if isinstance(new_B, np.ndarray):
            # need to multiply in the inverse now, too
            new_B = vec_ops.vec_tensordot(new_B, B, axes=[-1, shared], shared=shared)
            # for _ in range(new_B.ndim - 1):
            #     new_B = np.tensordot(B, new_B, axes=[1, -2])
        reverse_expansion = reverse_expansion + [new_B]
    return reverse_expansion

def kron_prod_derivs(A_expansion, B_expansion, order):
    # s = A_expansion[0].ndim - 2
    C_expansion = tensorprod_deriv(A_expansion, B_expansion, order,
                                   axes=[[-1, -2], [-1, -2]]
                                   )
    # now we need to reshape based on the fact that we end up with nnxmm
    return [
        c.reshape(c.shape[:-4] + (c.shape[-4]*c.shape[-3], c.shape[-2]*c.shape[-1]))
        for c in C_expansion
    ]

def kron_sum_derivs(A_expansion, B_expansion, order):
    base_shape = B_expansion[0].shape[:-2]
    ns = len(base_shape)
    m = B_expansion[0].shape[-1]
    if ns > 0:
        I_expansion = np.expand_dims(np.eye(m), list(range(ns)))
        I_expansion = np.broadcast_to(I_expansion, base_shape + (m, m))
    else:
        I_expansion = np.eye(m)
    I_expansion = [I_expansion]
    left_expansion = kron_prod_derivs(A_expansion, I_expansion, order)

    n = A_expansion[0].shape[-1]
    if ns > 0:
        I_expansion = np.expand_dims(np.eye(n), list(range(ns)))
        I_expansion = np.broadcast_to(I_expansion, base_shape + (n, n))
    else:
        I_expansion = np.eye(n)
    I_expansion = [I_expansion]
    right_expansion = kron_prod_derivs(I_expansion, B_expansion, order)

    return [l+r for l,r in zip(left_expansion, right_expansion)]

def sylv_derivs(A_expansion, B_expansion, C_expansion, order, shared=None, ks_expansion=None, inv_expansion=None):
    n = A_expansion[0].shape[-1]
    m = B_expansion[0].shape[-1]
    B_expansion = [np.moveaxis(b, -1, -2) for b in B_expansion]
    if ks_expansion is not None:
        ks_expansion = list(ks_expansion) + kron_sum_derivs(A_expansion, B_expansion, order)
    else:
        ks_expansion = kron_sum_derivs(A_expansion, B_expansion, order)
    if isinstance(order, list):
        inv_expansion = matinv_deriv(ks_expansion, order[0], base_expansion=inv_expansion)
    else:
        inv_expansion = matinv_deriv(ks_expansion, order, base_expansion=inv_expansion)
    C_expansion = [np.reshape(c, c.shape[:-2] + (c.shape[-1] * c.shape[-2],)) for c in C_expansion]
    X_expansion = tensordot_deriv(C_expansion, inv_expansion, order,
                                  axes=[-1, -1],
                                  shared=shared
                                  )

    return [np.reshape(x, x.shape[:-1] + (n,m)) for x in X_expansion], (ks_expansion, inv_expansion)

def matsqrt_deriv(A_expansion, order):
    shared = A_expansion[0].ndim - 2
    if shared == 0: shared = None
    B_expansion = [
        vec_ops.frac_powh(A_expansion[0], 1/2, pow=lambda evals,_:np.sqrt(evals))
        # sqrt maybe faster than pow(..., 1/2)
    ]
    inv_expansion = None
    ks_expansion = None
    for o in range(1, order+1):
        new_expansion, (ks_expansion, inv_expansion) = sylv_derivs(B_expansion, B_expansion, A_expansion[1:],
                                                                   ks_expansion=ks_expansion,
                                                                   inv_expansion=inv_expansion,
                                                                   shared=shared,
                                                                   order=[o - 1])
        B_expansion = B_expansion + new_expansion

    return B_expansion

def matinv_deriv(A_expansion, order, base_expansion=None):
    shared = s = A_expansion[0].ndim - 2
    if shared == 0: shared = None
    if base_expansion is None:
        B = np.linalg.inv(A_expansion[0])
        base_expansion = [B]
    inverse_expansion = list(base_expansion)

    for o in range(len(inverse_expansion), order+1):
        expansion = tensorops_deriv(
            A_expansion[1:],
                [s, s + 1],
            inverse_expansion,
                [s, s + 0],
            inverse_expansion,
            order=[o - 1],
            shared=shared
        )
        inverse_expansion = inverse_expansion + [-expansion[-1]]
    return inverse_expansion

def matdet_deriv(forward_expansion, order):
    shared = forward_expansion[0].ndim - 2
    reverse_expansion = matinv_deriv(forward_expansion, order)
    tr_inner_exp = tensordot_deriv(forward_expansion[1:], reverse_expansion,
                                   order - 1,
                                   axes=[1+shared, 1+shared],
                                   shared=shared
                                   )
    tr_exp = [np.trace(a, axis1=-2, axis2=-1) for a in tr_inner_exp]
    det_exp = [np.linalg.det(forward_expansion[0])]
    for o in range(0, order):
        det_exp = det_exp + [scalarprod_deriv(det_exp, tr_exp, [o])[-1]]
    return det_exp

def _broadcast_mul(scalar, other):
    if (
            isinstance(scalar, np.ndarray)
            and isinstance(other, np.ndarray)
            and scalar.ndim < other.ndim
    ):
        return np.expand_dims(scalar, list(range(scalar.ndim, other.ndim))) * other
    else:
        return scalar * other

_integer_partition_cache = {}
def get_integer_partitions(o):
    from ..Combinatorics import IntegerPartitioner

    return dev.cached_eval(
        _integer_partition_cache,
        o,
        IntegerPartitioner.partitions,
        args=(o,)
    )
def _scalarinv_deriv(scalar_expansion, o):

    shared = scalar_expansion[0].ndim
    term = 0
    for parts in get_integer_partitions(o):
        l = len(parts[0])
        scaling = ((-1) ** l) * math.factorial(l) / (scalar_expansion[0] ** (l + 1))
        # term = 0
        # for p in parts:
        #     nca_term = nca_partition_prod(p, scalar_expansion[1:], shared=shared)
        #     b_term = _broadcast_mul(scaling, nca_term)
        #     term += b_term
        term = sum(
            _broadcast_mul(scaling, nca_partition_prod(p, scalar_expansion[1:], shared=shared))
            for p in parts
        )
    return term

def scalarinv_deriv(scalar_expansion, order):
    return _deriv_construct(
        lambda : 1/scalar_expansion[0],
        lambda ords: [_scalarinv_deriv(scalar_expansion, o) for o in ords],
        order
    )

def _scalarpow_deriv(scalar_expansion, exp, o):
    shared = scalar_expansion[0].ndim

    term = 0
    for parts in get_integer_partitions(o):
        l = len(parts[0])
        factorial_terms = np.prod(exp - np.arange(l))
        if factorial_terms == 0:
            continue
        scaling = factorial_terms * (scalar_expansion[0] ** (exp - l))
        term += sum(
            _broadcast_mul(scaling, nca_partition_prod(p, scalar_expansion[1:], shared=shared))
            for p in parts
        )
    return term

def scalarpow_deriv(scalar_expansion, exp, order):
    scalar_expansion = [np.asanyarray(s) for s in scalar_expansion]
    return _deriv_construct(
        lambda : np.power(scalar_expansion[0], exp),
        lambda ords: [_scalarpow_deriv(scalar_expansion, exp, o) for o in ords],
        order
    )

def odd_fac(x):
    return np.prod([2*o+1 for o in range((x-1)//2)])
def vec_norm_unit_deriv(vec_expansion, order, base_expansion=None):
    from ..Combinatorics import IntegerPartitioner

    a = vec_expansion[0]
    r = np.linalg.norm(a, axis=-1)
    a_expansion = [a, vec_ops.identity_tensors(a.shape[:-1], a.shape[-1])]

    if not is_numeric(order):
        order = max(order)

    base_expansion = []
    shared = len(a.shape[:-1])
    for o in range(order + 2):
        if o == 0:
            base_expansion.append(r)
            continue

        t = 0
        rr = np.expand_dims(r, [-(i+1) for i in range(o)])
        # print("->"*20, o, "<-"*20)
        for k in itertools.chain(*IntegerPartitioner.partitions(o)):
            if max(k) > 2: continue
            factor = a_expansion[k[0]-1]
            for p in k[1:]:
                factor = _scalar_prod(factor, a_expansion[p-1], shared=shared)
            factor = nca_symmetrize(factor, k, shared=shared, identical=True)

            # compute powers
            e = (o + 1) // 2
            n = len(k)
            s = o - (1 - o%2)
            x = s + 2*(n - e)
            pref = ((-1)**(s+n)) * odd_fac(x) / (rr**x)
            # print("!", n//2, odd_fac(n//2), e, k, x)
            t += factor * pref
        base_expansion.append(t)

    # if base_expansion is None:
    #     a = vec_expansion[0]
    #     r = np.linalg.norm(a, axis=-1)
    #     if a.ndim > 1:
    #         u = a / r[..., np.newaxis]
    #     else:
    #         u = a / r
    #     base_expansion = [r, u]
    # base_expansion = list(base_expansion)
    # norm_inv_expansion = scalarinv_deriv(base_expansion, order=len(base_expansion)-2)
    #
    # a_expansion = [vec_expansion[0], vec_ops.identity_tensors(base_expansion[1].shape[:-1], 3)]
    #
    # if not is_numeric(order):
    #     order = max(order)
    #
    # for o in range(len(base_expansion), order+2):
    #     norm_inv_expansion = norm_inv_expansion + scalarinv_deriv(base_expansion, order=[o-1])
    #     base_expansion = base_expansion + scalarprod_deriv(
    #         norm_inv_expansion,
    #         a_expansion,
    #         order=[o - 1],
    #         identical=True
    #     )

    # print([b.shape for b in base_expansion])
    # print([v.shape for v in vec_expansion])

    # reexpand in terms of original vectors
    norm_expansion = [base_expansion[0]] + (
        tensor_reexpand(
            vec_expansion[1:],
            base_expansion[1:],
            order + 1
            # shared=vec_expansion[0].ndim - 1
        ) if order > 0 else []
    )

    unit_expansion = [base_expansion[1]] + (
        tensor_reexpand(
            vec_expansion[1:],
            base_expansion[2:],
            order
            # shared=vec_expansion[0].ndim - 1
        ) if order > 0 else []
    )

    return norm_expansion, unit_expansion

def vec_anglecos_deriv(A_expansion, B_expansion, order, unitized=False):
    if not unitized:
        A_expansion = vec_norm_unit_deriv(A_expansion, order)[1]
        B_expansion = vec_norm_unit_deriv(B_expansion, order)[1]
    shared = A_expansion[0].ndim - 1
    ugh = tensordot_deriv(A_expansion, B_expansion, order=order, axes=[-1, -1], shared=shared)
    return ugh
    # n = A_expansion[0].shape[-1] # should be 3
    # z = np.zeros(A_expansion[0].shape[:-1] + (n, n))
    # I = vec_ops.identity_tensors(A_expansion[0].shape[:-1], n)
    # vec_expansion = [
    #     vec_ops.vec_tensordot(A_expansion[0], B_expansion[0], axes=[-1, -1], shared=shared),
    #     np.concatenate([B_expansion[0], A_expansion[0]], axis=-1),
    #     np.concatenate([
    #         np.concatenate([z, I], axis=-1),
    #         np.concatenate([I, z], axis=-1)
    #     ],
    #         axis=-2
    #     )
    # ]
    # cat_expansion = [
    #     np.concatenate([a, b], axis=-1)
    #     for a, b in zip(A_expansion[1:], B_expansion[1:])
    # ]
    # return [vec_expansion[0]] + tensor_reexpand(
    #     cat_expansion,
    #     vec_expansion[1:],
    #     order
    # )

def vec_cross_deriv(A_expansion, B_expansion, order):
    shared = A_expansion[0].ndim - 1
    base_shape = A_expansion[0].shape[:-1]
    e3 = np.broadcast_to(
        np.expand_dims(perms.levi_cevita3, list(range(shared))),
        base_shape + (3, 3, 3)
    )
    res = tensorops_deriv(
        B_expansion,
            [-1, shared],
        [e3],
            [-1, -1],
        A_expansion,
        order=order,
        shared=shared
    )
    return res

def vec_parallel_cross_norm_deriv(axb_expansion, bxc_expansion, order, *,
                                  component_vectors,
                                  unit_expansions=None
                                  ):
    base_shape = axb_expansion[0].shape[:-1]
    shared = len(base_shape)

    A_expansion, B_expansion, C_expansion = component_vectors
    if unit_expansions is None:
        axb_unit_expansion, _ = vec_norm_unit_deriv(axb_expansion, order)
        bxc_unit_expansion, _ = vec_norm_unit_deriv(bxc_expansion, order)
        B_unit_expansion, _ = vec_norm_unit_deriv(B_expansion, order)
    else:
        B_unit_expansion, axb_unit_expansion, bxc_unit_expansion = unit_expansions
    axc_expansion = vec_cross_deriv(A_expansion, C_expansion, order)

    # print([b.shape for b in B_expansion])
    # print([a.shape for a in axc_expansion])
    # print(order)
    base_expansion = tensordot_deriv(
        B_expansion,
        axc_expansion,
        order,
        axes=[-1, -1],
        shared=shared
    )
    axb_inv_expansion = scalarinv_deriv(axb_unit_expansion, order)
    bxc_inv_expansion = scalarinv_deriv(bxc_unit_expansion, order)
    # print("B", [b.shape for b in B_unit_expansion])
    # print("axb", [b.shape for b in axb_inv_expansion])
    # print("bxc", [b.shape for b in bxc_inv_expansion])
    scalar_term = scalarprod_deriv(
            B_unit_expansion,
            axb_inv_expansion,
            order
        )
    scalar_term = scalarprod_deriv(
        scalar_term,
        bxc_inv_expansion,
        order
    )
    woof = scalarprod_deriv(scalar_term, base_expansion, order)
    # print("woof", [w.shape for w in woof])
    return [-w for w in woof]

    # i3 = np.broadcast_to(np.eye(3)[np.newaxis], (3, 3, 3)).copy()
    # for i in range(3):
    #     i3[i, i, i] = 0
    #
    # base_shape = axb_expansion[0].shape[:-1]
    # shared = len(base_shape)
    # i3 = np.broadcast_to(np.expand_dims(i3, list(range(shared))), base_shape + (3, 3, 3))
    # overlaps = axb_expansion[0][..., np.newaxis, :] @ bxc_expansion[0][..., :, np.newaxis]
    # signs = np.reshape(np.sign(overlaps), base_shape)
    # B_exp = [
    #     # force parallel
    #     np.expand_dims(signs, list(range(-(o+1), 0))) * b
    #     for o,b in enumerate(bxc_expansion)
    # ]
    #
    # pseudo_norm = tensorops_deriv(
    #     B_exp,
    #         [-1, -1],
    #     [i3],
    #         [-1, -1],
    #     axb_expansion,
    #     order=0,
    #     shared=shared
    # )[0]
    # pseudo_norm_2 = np.sqrt(np.abs(pseudo_norm))
    #
    # if is_numeric(order):
    #     order = np.arange(order+1)
    #
    # A_exp = [
    #     vec_ops.vec_tensordot(axb_expansion[o], pseudo_norm_2, axes=[-1, -1], shared=shared)
    #         if len(axb_expansion) > o and not is_zero(axb_expansion[o])  else
    #     0
    #     for o in order
    # ]
    # B_exp = [
    #     vec_ops.vec_tensordot(B_exp[o], pseudo_norm_2, axes=[-1, -1], shared=shared)
    #         if len(B_exp) > o and not is_zero(B_exp[o]) else
    #     0
    #     for o in order
    # ]
    # pseudonorm_expansion = [
    #     a-b
    #     for a,b in zip(A_exp, B_exp)
    # ]
    #
    # return pseudonorm_expansion

def vec_anglesin_deriv(A_expansion, B_expansion, order, unitized=False, return_unit_vectors=True, planar=None,
                       up_vector=None,
                       component_vectors=None,
                       unit_expansions=None,
                       planar_threshold=1e-14):
    if is_numeric(order):
        max_order = order
    else:
        max_order = max(order)
    if not unitized:
        A_expansion = vec_norm_unit_deriv(A_expansion, max_order)[1]
        B_expansion = vec_norm_unit_deriv(B_expansion, max_order)[1]

    if not planar:
        vec_cross = vec_cross_deriv(A_expansion, B_expansion, order=max_order)
        if planar is None:
            planar = np.linalg.norm(vec_cross[0], axis=-1) <= planar_threshold
    else:
        vec_cross = None

    if np.all(planar):
        expansion = vec_parallel_cross_norm_deriv(A_expansion, B_expansion, order,
                                                  component_vectors=component_vectors,
                                                  unit_expansions=unit_expansions
                                                  )
        norms = expansion
        units = A_expansion
    elif np.any(planar):
        # gotta compute planar and nonplanar separately then remerge the tensors

        base_shape = A_expansion[0].shape[:-1]
        planar_pos = np.where(planar)
        nonplanar_pos = np.where(np.logical_not(planar))
        planar_A = [a[planar_pos] for a in A_expansion]
        planar_B = [b[planar_pos] for b in B_expansion]
        if component_vectors is not None:
            component_vectors = [
                [s[planar_pos] for s in S_expansion]
                for S_expansion in component_vectors
            ]
        if unit_expansions is not None:
            unit_expansions = [
                [s[planar_pos] for s in S_expansion]
                for S_expansion in unit_expansions
            ]
        expansion = vec_parallel_cross_norm_deriv(planar_A, planar_B, order,
                                                  component_vectors=component_vectors,
                                                  unit_expansions=unit_expansions
                                                  )
        planar_units = planar_A
        nonplanar_geoms = [v[nonplanar_pos] for v in vec_cross]
        norms, units = vec_norm_unit_deriv(nonplanar_geoms, order)
        if up_vector is not None:
            up_vector = np.asanyarray(up_vector)
            up_vector = np.expand_dims(
                up_vector,
                list(range((nonplanar_geoms[0].ndim - up_vector.ndim)))
            )
            signs = np.sign(
                vec_ops.vec_tensordot(
                    nonplanar_geoms[0][..., np.newaxis, :],
                    up_vector[nonplanar_pos][..., :, np.newaxis],
                    axes=[-1, -2]
                )
            )
            signs = signs.reshape(signs.shape[:-2])
            norms = [v * np.expand_dims(signs, [-(x+1) for x in range(o)]) for o, v in enumerate(norms)]
            units = [v * np.expand_dims(signs, [-(x+1) for x in range(o+1)]) for o, v in enumerate(norms)]

        final_tensors = [
            np.zeros(base_shape + e.shape[1:])
            for e in expansion
        ]
        for e,n,f in zip(expansion, norms, final_tensors):
            f[planar_pos] = e#[planar_pos]
            f[nonplanar_pos] = n#[nonplanar_pos]
        if return_unit_vectors:
            final_units = [
                np.zeros(base_shape + u.shape[1:])
                for u in units
            ]
            for e, n, f in zip(planar_units, units, final_units):
                f[planar_pos] = e#[planar_pos]
                f[nonplanar_pos] = n#[nonplanar_pos]

            units = final_units
        else:
            units = None
        norms = final_tensors
    else:
        norms, units = vec_norm_unit_deriv(vec_cross, order)
        if up_vector is not None:
            up_vector = np.asanyarray(up_vector)
            up_vector = np.expand_dims(
                up_vector,
                list(range((vec_cross[0].ndim - up_vector.ndim)))
            )
            signs = np.sign(
                vec_ops.vec_tensordot(
                    vec_cross[0][..., np.newaxis, :],
                    up_vector[..., :, np.newaxis],
                    axes=[-1, -2]
                )
            )
            signs = signs.reshape(signs.shape[:-2])
            norms = [v * np.expand_dims(signs, [-(x+1) for x in range(o)]) for o, v in enumerate(norms)]
            units = [v * np.expand_dims(signs, [-(x+1) for x in range(o+1)]) for o, v in enumerate(norms)]

    if return_unit_vectors:
        return norms, units
    else:
        return norms

def arctan_expansion_term(angle, order):
    e = np.asanyarray(np.sin(order*angle))
    o = np.asanyarray(np.cos(order*angle))
    if order%2 == 1:
        e, o = o, e
        c_nums = {0, 3}
    else:
        c_nums = {1, 2}
    array = np.empty(e.shape + (2,)*order, dtype=float)
    f = math.factorial(order-1)
    for combo in itertools.combinations_with_replacement(range(2), order):
        two_count = np.sum(combo)
        t = (e if (two_count % 2) == 1 else o) * f
        if two_count % 4 in c_nums:
            t = -t
        for p in get_unique_permutations(combo)[1]:
            i = (...,) + tuple(p)
            array[i] = t
    return array

def vec_angle_deriv(A_expansion, B_expansion, order, up_vector=None,
                    component_vectors=None,
                    unit_expansions=None,
                    unitized=False):
    if not unitized:
        units_A, A_expansion = vec_norm_unit_deriv(A_expansion, order)
        units_B, B_expansion = vec_norm_unit_deriv(B_expansion, order)
    cos_expansion = vec_anglecos_deriv(A_expansion, B_expansion, order, unitized=True)
    sin_expansion = vec_anglesin_deriv(A_expansion, B_expansion, order, unitized=True,
                                       up_vector=up_vector,
                                       component_vectors=component_vectors,
                                       unit_expansions=unit_expansions,
                                       return_unit_vectors=False)

    # for i in range(3):
    #     for j in range(i+1, 3):
    #         cos_expansion[2][3*i:3*(i+1), 3*j:3*(j+1)] = cos_expansion[2][3*i:3*(i+1), 3*j:3*(j+1)].T
    #         cos_expansion[2][3*j:3*(j+1), 3*i:3*(i+1)] = cos_expansion[2][3*j:3*(j+1), 3*i:3*(i+1)].T
    #         sin_expansion[2][3*i:3*(i+1), 3*j:3*(j+1)] = sin_expansion[2][3*i:3*(i+1), 3*j:3*(j+1)].T
    #         sin_expansion[2][3*j:3*(j+1), 3*i:3*(i+1)] = sin_expansion[2][3*j:3*(j+1), 3*i:3*(i+1)].T
    # print(cos_expansion[2])

    ang = np.arctan2(sin_expansion[0], cos_expansion[0])

    # cos_sin_expansion = [
    #     np.moveaxis(np.array([c, s]), 0, -1)
    #     for c, s in zip(cos_expansion, sin_expansion)
    # ]
    # angle_derivs = [ang] + (tensor_reexpand(
    #     cos_sin_expansion[1:],
    #     [arctan_expansion_term(ang, 1)],
    #     axes=[-1, -1],
    #     order=order,
    #     # shared=arctan_expansion[0].ndim - 1
    # ) if order > 0 else [])
    # return angle_derivs

    # print("???")
    # print(
    #     np.sum(np.abs(
    #         cos_expansion[2] - cos_expansion[2].T
    #     ))
    # )
    # print(
    #     (cos_expansion[0] * sin_expansion[3])[2][:3, :3]
    #     - (sin_expansion[0] * cos_expansion[3])[2][:3, :3]
    #     + nca_symmetrize(cos_expansion[1][:, np.newaxis, np.newaxis] * sin_expansion[2][np.newaxis, :, :], (1, 1))[2][:3, :3]
    #     # + (cos_expansion[1][:, np.newaxis, np.newaxis] * sin_expansion[2][np.newaxis, :, :])[2][:3, :3]
    #     - nca_symmetrize(sin_expansion[1][:, np.newaxis, np.newaxis] * cos_expansion[2][np.newaxis, :, :], (1, 1))[2][:3, :3]
    #     # - (sin_expansion[1][:, np.newaxis, np.newaxis] * cos_expansion[2][np.newaxis, :, :])[2][:3, :3]
    # )
    #
    # print(
    #     (cos_expansion[0] * sin_expansion[3])[2][:3, :3]
    #     - (sin_expansion[0] * cos_expansion[3])[2][:3, :3]
    #     + (cos_expansion[1][:, np.newaxis, np.newaxis] * sin_expansion[2][np.newaxis, :, :])[2][:3, :3]
    #     - (sin_expansion[1][:, np.newaxis, np.newaxis] * cos_expansion[2][np.newaxis, :, :])[2][:3, :3]
    # )

    # print("=oooo"*50)
    if order > 0:
        sc_expansion = scalarprod_deriv(cos_expansion, sin_expansion[1:], order-1)
        # print("=bbbb"*50)
        cs_expansion = scalarprod_deriv(sin_expansion, cos_expansion[1:], order-1)
    else:
        sc_expansion = []
        cs_expansion = []
    return [ang] + [
        s - c
        for s,c in zip(sc_expansion, cs_expansion)
    ]

    # huh_1 = angle_derivs
    #
    # print([h.shape for h in huh])
    # print([h1.shape for h1 in huh_1])

def vec_dihed_deriv(A_expansion, B_expansion, C_expansion, order, unitized=False, planar=None, planar_threshold=1e-14):
    # quick check

    if is_numeric(order):
        max_order = order
    else:
        max_order = max(order)

    B_norms, B_expansion = vec_norm_unit_deriv(B_expansion, len(B_expansion))
    # if not unitized:
    #     _, A_expansion = vec_norm_unit_deriv(A_expansion, len(A_expansion))
    #     _, B_expansion = vec_norm_unit_deriv(B_expansion, len(B_expansion))
    #     _, C_expansion = vec_norm_unit_deriv(C_expansion, len(C_expansion))
    n1_expansion = vec_cross_deriv(B_expansion, A_expansion, max_order)
    n2_expansion = vec_cross_deriv(B_expansion, C_expansion, max_order)
    # print("..."*10, "axb")
    # print(n1_expansion[0])
    n1_norms, axb_expansion = vec_norm_unit_deriv(n1_expansion, order)
    n2_norms, bxc_expansion = vec_norm_unit_deriv(n2_expansion, order)
    B_norms, up_expansion = vec_norm_unit_deriv(B_expansion, len(B_expansion))
    base_derivs = vec_angle_deriv(axb_expansion, bxc_expansion, order, unitized=True,
                                  # up_vector=None
                                  up_vector=up_expansion[0],
                                  unit_expansions=[B_norms, n1_norms, n2_norms],
                                  component_vectors=[A_expansion, B_expansion, C_expansion]
                                  )
    # add in the np.pi shift to account for imposed sign flip in standard imp. to match Gaussian
    base_derivs[0] = np.pi - base_derivs[0]
    return base_derivs
    # return [-x for x in base_derivs]

def vec_plane_angle_deriv(A_expansion, B_expansion, C_expansion, D_expansion, order, planar=None, planar_threshold=1e-14):
    # quick check

    if is_numeric(order):
        max_order = order
    else:
        max_order = max(order)

    axb_expansion = vec_cross_deriv(A_expansion, B_expansion, max_order)
    cxd_expansion = vec_cross_deriv(C_expansion, D_expansion, max_order)

    return vec_angle_deriv(axb_expansion, cxd_expansion, order, unitized=False,
                           # planar_threshold=planar_threshold
                           )


def nca_partition_terms(partition):
    """
    Computes the number of permutations for the non-commutative operation
    corresponding to the given partition

    :param cls:
    :param partition:
    :return:
    """
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

    return np.round(np.prod(multinomial_num / full_denom))

max_symm_perm_order = 4
unique_permutation_cache = {}
def get_unique_permutations(perm_idx):
    from ..Combinatorics import UniquePermutations
    key = tuple(perm_idx) if len(perm_idx) <= max_symm_perm_order else None

    return dev.cached_eval(
        unique_permutation_cache,
        key,
        lambda perm_idx:UniquePermutations(perm_idx).permutations(return_indices=True),
        condition=lambda k:k is not None and len(k) <= max_symm_perm_order,
        args=(perm_idx,)
    )
def get_nca_perm_iter(partition, identical=True):
    if identical:
        blocks, counts = np.unique(partition, return_counts=True)
        base_perm = sum([(b,) * (b*c) for b,c in zip(blocks, counts)], ())
        inv_perm = np.argsort(sum([(b,) * b for b in partition], ()))
    else:
        raise NotImplementedError("just use unique perms")
    base_perm_inds, _ = get_unique_permutations(base_perm)
    sub_ind_blocks = []
    padding = 0
    for b,c in zip(blocks, counts):
        if c == 1 or b == 1:
            sub_perm_inds = np.arange(b*c)[np.newaxis]
        else:
            # if len(c)
            sub_perm = sum([(c-i,) * b for i in range(c)], ())
            sub_perm_inds, _ = get_unique_permutations(sub_perm)
            inv_inds = np.argsort(sub_perm_inds, axis=1)
            filter_inds = [
                np.min(inv_inds[:, b*i:b*(i+1)], axis=1)
                for i in range(c)
            ]
            ord_filter = np.all(np.diff(filter_inds, axis=0) > 0, axis=0)
            sub_perm_inds = sub_perm_inds[ord_filter,]
        sub_ind_blocks.append(padding+sub_perm_inds)
        padding += b*c

    for block_list in itertools.product(*sub_ind_blocks):
        sublist = np.concatenate(block_list)
        p = set_ops.vector_take(sublist[inv_perm], base_perm_inds)
        yield p
def check_perm_sorting(block_counts, partition_inverse):
    p = 0
    for b,c in zip(*block_counts):
        if c > 1:
            if any(
                    np.min(partition_inverse[p+b*i:p+b*(i+1)]) <
                    np.min(partition_inverse[p+b*(i+1):p+b*(i+2)])
                for i in range(c - 1)
            ):
                return False

        p += b*c

    return True

def get_nca_perm_idx(partition, contract=True, identical=False):
    perm_counter = len(partition)
    perm_idx = []  # to establish the set of necessary permutations to make things symmetric
    for i in partition:
        if (not identical) or i > 1:
            perm_idx.extend([perm_counter] * i)
            perm_counter -= 1
        else:
            perm_idx.append(perm_counter)
    return perm_idx
def get_nca_symmetrizing_perms(partition,
                               perm_idx=None,
                               use_base_perms=True,
                               filter_unique=False,
                               contract=True,
                               identical=False):
    if perm_idx is None:
        perm_idx = get_nca_perm_idx(partition, contract=contract, identical=identical)

    nterms = nca_partition_terms(partition)
    if use_base_perms:
        perm_inds = np.concatenate(list(get_nca_perm_iter(partition, identical=identical)), axis=0)
        scaling = 1
        if len(perm_inds) != nterms:
            raise ValueError(f"mismatch between reduced perms and actual number, expected {nterms}, got {len(perm_inds)} for partition {partition}")
    elif filter_unique:
        raise Exception("?")
        all_perm_inds, _ = get_unique_permutations(perm_idx)
        counts = np.unique(partition, return_counts=True)
        inv_perms = np.argsort(all_perm_inds, axis=1)
        perm_inds = np.array([
            p
            for p, i in zip(all_perm_inds, inv_perms)
            if check_perm_sorting(counts, i)
        ])
        scaling = 1
        if len(perm_inds) != nterms:
            raise ValueError(f"mismatch between reduced perms and actual number, expected {nterms}, got {len(perm_inds)} for partition {partition}")
    else:
        raise Exception("?")
        perm_inds, _ = get_unique_permutations(perm_idx)
        overcount = len(perm_inds) / nterms
        scaling = 1 / overcount

    return perm_inds, scaling

def nca_symmetrize(tensor, partition,
                   shared=None,
                   identical=False,
                   contract=True,
                   use_base_perms=True,
                   filter_unique=False,
                   check_symmetry=False,
                   reweight=None):

    perm_idx = get_nca_perm_idx(partition, contract=contract, identical=identical)
    # sometimes we overcount, so we factor that out here
    if reweight or (reweight is None and identical):
        perm_inds, scaling = get_nca_symmetrizing_perms(partition, perm_idx,
                                                        filter_unique=filter_unique,
                                                        use_base_perms=use_base_perms,
                                                        identical=identical)
        tensor = tensor * scaling
    else:
        perm_inds, _ = get_unique_permutations(perm_idx)
        inv_perm = np.argsort(np.argsort(perm_idx))
        # perm_inds = inv_perm[perm_inds]

    if shared is None:
        shared = 0
        perm_inds = [
            list(p) + list(range(len(p), tensor.ndim))
            for p in perm_inds
        ]
    else:
        l = list(range(shared))
        perm_inds = [
            l + [shared + pp for pp in p] + list(range(shared+len(p), tensor.ndim))
            for p in perm_inds
        ]

    t = sum(
        tensor.transpose(p)
        for p in perm_inds
    )

    if check_symmetry:
        for p in itertools.permutations(
                range(shared, shared + sum(partition)),
                int(sum(partition))
        ):
            p = tuple(range(shared)) + p + tuple(range(shared + sum(partition), t.ndim))
            diff = t - np.transpose(t, p)
            m = np.max(np.abs(diff))
            # r = m / np.max(np.abs(t))
            if m > 1e-8 and np.max(np.abs(t)) < 1e6:
                # with np.printoptions(suppress=True, linewidth=1e8):
                #     print(tensor)
                #     print("   ", "."*20)
                #     print(t)
                print("|", t.shape)
                print("|", partition, p, perm_idx)
                print("|", perm_inds)
                raise ValueError("symmetry error")

    return t

def nca_partition_dot(partition, A_expansion, B_expansion, axes=None, shared=None, identical=False, symmetrize=True):
    if axes is None:
        axes = [-1, (0 if shared is None else shared)]
    if len(B_expansion) <= len(partition) - 1:
        return 0
    B = B_expansion[len(partition) - 1]
    if is_numeric(B) and B == 0:
        return 0
    a_ax, b_ax = [[x] if is_numeric(x) else x for x in axes]
    b_ax = [
        (B.ndim + b - (len(partition) - 1))
            if b < 0 else
        b #+ (len(partition) - 1)
        for b in b_ax
    ]
    # account for increasing dimension with longer partitions
    for i in reversed(partition):
        if len(A_expansion) <= i - 1:
            return 0
        A = A_expansion[i - 1]
        if is_numeric(A) and A == 0:
            return 0
        if shared is None:
            B = np.tensordot(A, B, axes=[a_ax, b_ax])
        else:
            B = vec_ops.vec_tensordot(A, B, axes=[a_ax, b_ax], shared=shared)
        b_ax = [min(B.ndim - 1, b + A.ndim - 1 - shared) for b in b_ax]

    if symmetrize is not None:
        symmetrize = len(A_expansion) > 1 and len(B_expansion) > 1

    if symmetrize:
        B = nca_symmetrize(B, partition, identical=identical, shared=shared)
    return B

def nca_partition_prod(partition, A_expansion, shared=None, symmetrize=True):
    i = partition[0]
    if len(A_expansion) <= i - 1:
        return 0
    A = A_expansion[i - 1]
    if is_numeric(A) and A == 0:
        return 0

    B = A
    for i in partition[1:]:
        if len(A_expansion) <= i - 1:
            return 0
        A = A_expansion[i - 1]
        if is_numeric(A) and A == 0:
            return 0
        if shared is not None:
            axes = [list(range(shared, B.ndim)), list(range(shared, A.ndim))]
        else:
            axes = [list(range(B.ndim)), list(range(A.ndim))]

        B = vec_ops.vec_outer(B, A, axes=axes, order=0)
    if symmetrize:
        B = nca_symmetrize(B, partition, shared=shared)
    return B

def tensor_reexpand(derivs, vals, order=None, axes=None):
    terms = []
    if order is None:
        order = len(vals)

    derivs = [
        np.asanyarray(d) if not is_zero(d) else d
        for d in derivs
    ]
    shared = 0
    for i,d in enumerate(derivs):
        if not is_zero(d):
            shared = d.ndim - (i + 2)
            break

    vals = [
        np.asanyarray(d) if not is_zero(d) else d
        for d in vals
    ]

    if is_numeric(order): order = list(range(1, order+1))

    for o in order:
        term = sum(
            nca_partition_dot(p, derivs, vals, axes=axes, identical=True, shared=shared)
            for parts in get_integer_partitions(o)
            for p in parts
        )
        if not is_zero(term):
            # if we are transforming beyond axis zero in the target array, need
            # to shift the new axes back
            if axes is not None:
                target = axes[-1]
                if target > 0:
                    target = target + (o - 1) # indexes past end of array otherwise
                for i in range(o):
                    term = np.moveaxis(term, shared, target)
        terms.append(term)

    return terms

def optimizing_transformation(expansion, order):
    V = expansion

    zero_order = 0
    for v in V:
        if is_zero(v):
            zero_order += 1
        else:
            break

    if zero_order > 2:
        raise ValueError("can't optimize without gradient or Hessian (tensor inverses not implemented)")

    W = V[zero_order]
    if zero_order == 0:
        w = W
        Q = [np.eye(V[1].shape[0])]
    elif zero_order == 1 and np.allclose(np.diag(np.diag(W)), W):
        Q = [np.eye(V[1].shape[0])]
        w = np.diag(W)
    else:
        Q = [np.linalg.inv(W)]
        w = np.ones(len(W))

    for o in range(1, order + 1):
        V_rem = tensor_reexpand(Q, V, [o], axes=[-1, 0])[-1]
        w = w[np.newaxis]
        new_Q = -V_rem / ((o + 2) * w)
        Q = Q + [new_Q]

    return Q

def apply_nca_multi_ops(partition, expansions, ops, shared, root_dim=2):
    terms = [
        e[p] if len(e) > p else 0
        for e,p in zip(expansions, partition)
    ]
    if any(is_numeric(t) and t == 0 for t in terms): return 0

    if shared is None: shared = 0

    A = terms[0]
    d0 = expansions[0][0].ndim
    d = A.ndim - root_dim - shared
    scaling = 2 if len(partition) == 3 and tuple(partition) == (1, 0, 1) else 1
    for B,p,(op, axes, contract) in zip(terms[1:], partition[1:], ops):
        a_ax, b_ax = [[x] if is_numeric(x) else x for x in axes]
        a_ax = [a if a >= 0 else (A.ndim + a - d) for a in a_ax]
        b_ax = [b if b >= 0 else (B.ndim + b - p) for b in b_ax]
        if contract: # axes disappear, so we just account for the shifts
            axes = [
                [x+d for x in a_ax],
                [x+p for x in b_ax]
            ]
            deriv_axis = A.ndim - len(a_ax)
        else: # axes appeared, so we need to include those in the product
              # we _forced_ axes to be at the end of the arrays since it was too hard
              # to keep track of them otherwise...
              # actually I guess I could have put the derivative axes at the end...
              # and then the axes would never change...but that has other complications
            axes = [
                [shared + i for i in range(d)] + [x+d for x in a_ax],
                [shared + i for i in range(p)] + [x+p for x in b_ax]
            ]
            # if B.ndim < A.ndim:
            #     B = np.expand_dims(B, list(range(B.ndim - A.ndim, 0, 1)))
            # elif A.ndim < B.ndim:
            #     A = np.expand_dims(A, list(range(A.ndim - B.ndim, 0, 1)))
            deriv_axis = A.ndim
        _as = A.shape
        if shared == 0:
            A = op(A, B, axes=axes)
        else:
            A = op(A, B, axes=axes, shared=shared)
        # next we need to move all of the derivative axes in the second tensor to the beginning
        # so we can symmetrize

        for i in range(p):
            A = np.moveaxis(A, deriv_axis+i, deriv_axis - root_dim)
        d += B.ndim - root_dim - shared
    partition = [p for p in partition if p > 0]
    if len(partition) > 1:
        A = nca_symmetrize(A, partition, shared=shared, identical=False)
    return A
def nca_multi_op_order_deriv(partition_generator, order, expansions, ops, shared, root_dim):
    full = None
    for part in partition_generator.get_terms(order):
        term = apply_nca_multi_ops(part, expansions, ops, shared, root_dim)
        if full is None:
            full = term
        else:
            full = full + term
    return full

def nca_canonicalize_multiops(expansion_op_pairs):
    if len(expansion_op_pairs) % 2 == 0: raise ValueError("invalid number of operations/expansions")

    expansions = []
    ops = []
    for i, t in enumerate(expansion_op_pairs):
        if i % 2 == 0:
            expansions.append([np.asanyarray(A) for A in t])
        else:
            op = None
            axes = None
            contract = None
            if isinstance(t, dict):
                op = t.get('op', None)
                axes = t.get('axes', None)
                contract = t.get('contract', None)
            elif isinstance(t, str):
                op = t
            elif is_numeric(t[0]) or is_numeric(t[0][0]):
                axes = t
            else:
                op = t[0]
                if len(t) > 1: axes = t[1]
                if len(t) > 2: contract = t[2]

            if op is None and axes is not None:
                op = '.'

            if isinstance(op, str):
                if op in {'.', 'dot', 'contract', 'inner'}:
                    op = _contract
                    if axes is None: axes = [-1, 0]
                    if contract is None: contract = True
                elif op in {'x', 'prod', 'product', 'outer'}:
                    op = _product
                    if axes is None: axes = 'all'
                    if contract is None: contract = False
                # elif op in {'*', 'sprod', 'scalar_product'}:
                #     op = _scalar_prod
                #     if axes is None: axes = 'all'
                #     if contract is None: contract = False
                else:
                    raise ValueError(f"can't canonicalize operation {op}")

            if contract is None:
                contract = op is _contract

            ops.append([op, axes, contract])

    return expansions, ops

def _contract(a, b, axes=None, shared=None):
    if shared is not None:
        res = vec_ops.vec_tensordot(a, b, axes=axes, shared=shared)
    else:
        res = np.tensordot(a, b, axes=axes)
    return res
def _product(a, b, axes=None, shared=None):
    return vec_ops.vec_outer(a, b, axes=axes, order=0)

generator_max_caching_order = 4
term_generator_caches = {}
class caching_perm_generator:
    def __init__(self, o):
        from ..Combinatorics import SymmetricGroupGenerator
        self.gen = SymmetricGroupGenerator(o)
        self._term_cache = {}

    def get_terms(self, order):
        return dev.cached_eval(
            self._term_cache,
            order,
            self.gen.get_terms,
            args=(order,)
        )

def get_term_generator(k):

    return dev.cached_eval(
        term_generator_caches,
        k,
        caching_perm_generator,
        condition=lambda k:k<generator_max_caching_order,
        args=(k,)
    )

def tensorops_deriv(
        *expansion_op_pairs,
        order,
        shared=None
):
    expansions, ops = nca_canonicalize_multiops(expansion_op_pairs)
    _ = []
    for i,(op, axes, contract) in enumerate(ops):
        if isinstance(axes, str): axes = [axes, axes]
        a_ax, b_ax = axes
        A = expansions[i][0]
        B = expansions[i+1][0]
        if isinstance(a_ax, str):
            if a_ax == 'all':
                a_ax = list(range(shared, A.ndim))
            else:
                raise ValueError(f"bad axes spec '{a_ax}'")
        if isinstance(b_ax, str):
            if b_ax == 'all':
                b_ax = list(range(shared, B.ndim))
            else:
                raise ValueError(f"bad axes spec '{b_ax}'")
        _.append([op, [a_ax, b_ax], contract])
    ops = _


    if isinstance(order, int):
        order = list(range(order+1))

    partition_generator = get_term_generator(len(expansions))
    derivs = [
        nca_multi_op_order_deriv(partition_generator, o, expansions, ops, shared,
                                 root_dim=expansions[0][0].ndim - (0 if shared is None else shared)
                                 )
        for o in order
    ]

    return derivs