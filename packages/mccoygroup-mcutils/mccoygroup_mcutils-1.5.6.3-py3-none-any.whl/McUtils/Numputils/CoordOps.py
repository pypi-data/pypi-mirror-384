"""
Provides analytic derivatives for some common base terms with the hope that we can reuse them elsewhere
"""
import itertools
import math
import enum
import numpy as np
from .VectorOps import *
from . import TensorDerivatives as td
from . import Misc as misc
from . import SetOps as setops
from . import PermutationOps as pops
from .Options import Options

__all__ = [
    'rot_deriv',
    'rot_deriv2',
    'cartesian_from_rad_derivatives',
    'dist_basis',
    'angle_basis',
    # 'dihed_bases',
    'internal_basis',
    'dist_deriv',
    'angle_deriv',
    'dihed_deriv',
    'book_deriv',
    'oop_deriv',
    'wag_deriv',
    'vec_norm_derivs',
    'vec_sin_cos_derivs',
    'vec_angle_derivs',
    'rock_deriv',
    'rock_vec',
    'dist_vec',
    'angle_vec',
    'dihed_vec',
    'book_vec',
    'oop_vec',
    'wag_vec',
    "internal_conversion_function",
    "internal_coordinate_tensors",
    "inverse_internal_coordinate_tensors",
    "inverse_coordinate_solve",
    "metric_tensor",
    "delocalized_internal_coordinate_transformation",
    "relocalize_coordinate_transformation",
    "transform_cartesian_derivatives",
    "legendre_integer_coefficients",
    "triangle_convert",
    "triangle_converter",
    "triangle_area",
    "dihedral_distance",
    "dihedral_distance_converter",
    "dihedral_from_distance",
    "dihedral_from_distance_converter",
]

def _prod_deriv(op, a, b, da, db):
    """
    Simple product derivative to make apply the product rule and its analogs
    a bit cleaner. Assumes a derivative that doesn't change dimension.
    Should be generalized at some point to handle arbitrary outer products and shit of that sort.
    :param op:
    :type op:
    :param a:
    :type a:
    :param b:
    :type b:
    :param da:
    :type da:
    :param db:
    :type db:
    :return:
    :rtype:
    """
    return op(a, db) + op(da, b)
def _prod_deriv_2(op, a, b, da1, da2, db1, db2, da12, db12):
    """
    2nd derivative of op(a, b) assuming it operates under a product-rule type ish
    """
    return op(da12, b) + op(da1, db2) + op(da2, db1) + op(a, db12)

def normalized_vec_deriv(v, dv):
    """
    Derivative of a normalized vector w/r/t some unspecified coordinate
    """
    norms = vec_norms(v)[..., np.newaxis]
    vh = v / norms
    i3 = np.broadcast_to(np.eye(3), dv.shape[:-1] + (3, 3))
    vXv = vec_outer(vh, vh)
    wat = np.matmul(i3 - vXv, dv[..., np.newaxis])[..., 0] # gotta add a 1 for matmul
    return wat / norms

def normalized_vec_deriv2(v, dv1, dv2, d2v):
    """
    Second derivative of a normalized vector w/r/t some unspecified coordinates
    """
    # derivative of inverse norm
    norms = vec_norms(v)[..., np.newaxis]
    vds2 = vec_dots(dv2, v)[..., np.newaxis]
    dnorminv = -1/(norms**3) * vds2
    vh = v / norms
    i3 = np.broadcast_to(np.eye(3), dv1.shape[:-1] + (3, 3))
    vXv = vec_outer(vh, vh)
    dvh2 = normalized_vec_deriv(v, dv2)
    dvXv2 = _prod_deriv(vec_outer, vh, vh, dvh2, dvh2)
    right = np.matmul(i3 - vXv, dv1[..., np.newaxis])[..., 0]  # gotta add a 1 for matmul
    dright = _prod_deriv(np.matmul, i3 - vXv, dv1[..., np.newaxis], -dvXv2, d2v[..., np.newaxis])[..., 0]
    der = _prod_deriv(np.multiply, 1/norms, right, dnorminv, dright)
    return der

def rot_deriv(angle, axis, dAngle, dAxis):
    """
    Gives a rotational derivative w/r/t some unspecified coordinate
    (you have to supply the chain rule terms)
    Assumes that axis is a unit vector.

    :param angle: angle for rotation
    :type angle: float
    :param axis: axis for rotation
    :type axis: np.ndarray
    :param dAngle: chain rule angle deriv.
    :type dAngle: float
    :param dAxis: chain rule axis deriv.
    :type dAxis: np.ndarray
    :return: derivatives of the rotation matrices with respect to both the angle and the axis
    :rtype: np.ndarray
    """

    # Will still need work to be appropriately vectorized (can't remember if I did this or not?)
    vdOdv = vec_outer(dAxis, axis) + vec_outer(axis, dAxis)
    c = np.cos(angle)[..., np.newaxis]
    s = np.sin(angle)[..., np.newaxis]
    i3 = np.broadcast_to(np.eye(3), axis.shape[:-1] + (3, 3))
    e3 = np.broadcast_to(pops.levi_cevita3, axis.shape[:-1] + (3, 3, 3))
    # e3 = pops.levi_cevita3
    # i3 = np.eye(3)
    ct = vdOdv*(1-c[..., np.newaxis])
    st = (i3-vec_outer(axis, axis))*s[..., np.newaxis]*dAngle
    wat = (dAxis*s + axis*c*dAngle)
    et = vec_tensordot(e3, wat, axes=[-1, 1]) # currently explicitly takes a stack of vectors...
    return ct - st - et

def rot_deriv2(angle, axis, dAngle1, dAxis1, dAngle2, dAxis2, d2Angle, d2Axis):
    """
    Gives a rotation matrix second derivative w/r/t some unspecified coordinate
    (you have to supply the chain rule terms)

    :param angle: angle for rotation
    :type angle: float
    :param axis: axis for rotation
    :type axis: np.ndarray
    :param dAngle: chain rule angle deriv.
    :type dAngle: float
    :param dAxis: chain rule axis deriv.
    :type dAxis: np.ndarray
    :return: derivatives of the rotation matrices with respect to both the angle and the axis
    :rtype: np.ndarray
    """

    from operator import mul

    # lots of duplication since we've got the same axis twice
    vXv = vec_outer(axis, axis)
    dvXv1 = _prod_deriv(vec_outer, axis, axis, dAxis1, dAxis1)
    dvXv2 = _prod_deriv(vec_outer, axis, axis, dAxis2, dAxis2)
    d2vXv = _prod_deriv_2(vec_outer, axis, axis, dAxis1, dAxis2, dAxis1, dAxis2, d2Axis, d2Axis)

    i3 = np.broadcast_to(np.eye(3), axis.shape[:-1] + (3, 3))
    e3 = np.broadcast_to(pops.levi_cevita3, axis.shape[:-1] + (3, 3, 3))

    c = np.cos(angle)
    s = np.sin(angle)

    dc1 = -s * dAngle1
    dc2 = -s * dAngle2
    d2c = -s * d2Angle - c * dAngle1 * dAngle2

    cos_term = _prod_deriv_2(mul,
                             i3 - vXv,
                             c[..., np.newaxis, np.newaxis],
                             dvXv1, dvXv2,
                             dc1[..., np.newaxis, np.newaxis], dc2[..., np.newaxis, np.newaxis],
                             d2vXv, d2c[..., np.newaxis, np.newaxis]
                             )

    ds1 = c * dAngle1
    ds2 = c * dAngle2
    d2s = c * d2Angle - s * dAngle1 * dAngle2
    fack = _prod_deriv_2(mul, axis, s[..., np.newaxis], dAxis1, dAxis2, ds1[..., np.newaxis], ds2[..., np.newaxis], d2Axis, d2s[..., np.newaxis])
    sin_term = vec_tensordot(e3, fack, axes=[-1, 1])

    return d2vXv + cos_term - sin_term

def _rad_d1(i, z, m, r, a, d, v, u, n, R1, R2, Q, rv, dxa, dxb, dxc):

    # derivatives of coordinates
    dr = 1 if (z == i and m == 0) else 0
    dq = 1 if (z == i and m == 1) else 0
    df = 1 if (z == i and m == 2) else 0

    dv_ = dxb - dxa
    dv = normalized_vec_deriv(v, dv_)
    v = vec_normalize(v)
    if a is None:
        # no derivative about any of the rotation shit
        drv = _prod_deriv(np.multiply, r[..., np.newaxis], v, dr, dv)
        du_ = dn_ = dR1 = dR2 = dQ = None
        der = dxa + drv
    else:
        # derivatives of axis system vectors
        du_ = dxc - dxb
        du = normalized_vec_deriv(u, du_)
        u = vec_normalize(u)
        dn_ = _prod_deriv(vec_crosses, v, u, dv, du)
        # we actually need the derivatives of the unit vectors for our rotation axes
        dn = normalized_vec_deriv(n, dn_)
        n = vec_normalize(n)
        # raise Exception(n.shape, dn.shape, dn_.shape)

        # derivatives of rotation matrices
        dR1 = rot_deriv(a, n, dq, dn)
        if d is not None:
            dR2 = rot_deriv(d, v, df, dv)
            # derivative of total rotation matrix
            dQ = _prod_deriv(np.matmul, R2, R1, dR2, dR1)
        else:
            dR2 = None
            dQ = dR1

        # derivative of vector along the main axis
        drv = _prod_deriv(np.multiply, r, v, dr, dv)
        der = dxa + _prod_deriv(np.matmul, Q, rv[..., np.newaxis], dQ, drv[..., np.newaxis])[..., 0]

    return der, (dr, dq, df, dv_, du_, dn_, dR1, dR2, dQ, drv)

def _rad_d2(i, z1, m1, z2, m2, # don't actually use these because all the coordinate 2nd derivatives are 0 :yay:
            r, a, d, v, u, n, R1, R2, Q, rv,
            dr1, dq1, df1, dv1, du1, dn1, dR11, dR21, dQ1, drv1,
            dr2, dq2, df2, dv2, du2, dn2, dR12, dR22, dQ2, drv2,
            d2xa, d2xb, d2xc):

    # second derivatives of embedding axes
    # fuck this is annoying...need to get the _unnormalized_ shit too to get the norm deriv as I have it...
    d2v = normalized_vec_deriv2(v, dv1, dv2, d2xb - d2xa)
    dv1 = normalized_vec_deriv(v, dv1)
    dv2 = normalized_vec_deriv(v, dv2)
    v = vec_normalize(v)
    if r.shape[-1] == 1: # shape hack for now... to flatten r I guess...
        r = r[..., 0]
    if a is None:
        d2rv = _prod_deriv_2(np.multiply, r[..., np.newaxis], v, dr1, dr2, dv1, dv2, 0, d2v)
        der = d2xa + d2rv
        d2u = d2n = d2R1 = d2R2 = d2Q = None
    else:
        d2u = normalized_vec_deriv2(u, du1, du2, d2xc - d2xb)
        du1 = normalized_vec_deriv(u, du1)
        du2 = normalized_vec_deriv(u, du2)
        u = vec_normalize(u)
        d2n_ = _prod_deriv_2(vec_crosses, v, u, dv1, dv2, du1, du2, d2v, d2u)
        d2n = normalized_vec_deriv2(v, dn1, dn2, d2n_)
        dn1 = normalized_vec_deriv(u, dn1)
        dn2 = normalized_vec_deriv(u, dn2)
        n = vec_normalize(n)

        # second derivatives of rotation matrices
        d2R1 = rot_deriv2(a, n, dq1, dn1, dq2, dn2, 0, d2n)
        if d is None:
            d2R2 = None
            d2Q = d2R1
        else:
            d2R2 = rot_deriv2(d, v, df1, dv1, df2, dv2, 0, d2v)
            d2Q = _prod_deriv_2(np.matmul, R2, R1, dR21, dR22, dR11, dR12, d2R1, d2R2)

        # second derivatives of r*v
        d2rv = _prod_deriv_2(np.multiply, r[..., np.newaxis], v, dr1, dr2, dv1, dv2, 0, d2v)

        # new derivative
        der = d2xa + _prod_deriv_2(np.matmul, Q, rv[..., np.newaxis], dQ1, dQ2, drv1[..., np.newaxis], drv2[..., np.newaxis], d2Q, d2rv[..., np.newaxis])[..., 0]

    # if der.shape == (7, 7, 3):
    #     raise ValueError(r.shape, d2v.shape, d2rv.shape)#, d2u.shape, d2n.shape, d2R1.shape, d2R2.shape, d2Q.shape, d2rv.shape)
    return der, (d2v, d2u, d2n, d2R1, d2R2, d2Q, d2rv)

class _dumb_comps_wrapper:
    """
    Exists solely to prevent numpy from unpacking
    """
    def __init__(self, comp):
        self.comp = comp
def cartesian_from_rad_derivatives(
        xa, xb, xc,
        r, a, d,
        i,
        ia, ib, ic,
        derivs,
        order=2,
        return_comps=False
):
    """
    Returns derivatives of the generated Cartesian coordinates with respect
    to the internals
    """

    if order > 2:
        raise NotImplementedError("bond-angle-dihedral to Cartesian derivatives only implemented up to order 2")

    coord, comps = cartesian_from_rad(xa, xb, xc, r, a, d, return_comps=True)
    v, u, n, R2, R1 = comps
    if R2 is not None:
        Q = np.matmul(R2, R1)
    elif R1 is not None:
        Q = R1
    else:
        Q = None
    if r.ndim < v.ndim:
        rv = r[..., np.newaxis] * vec_normalize(v)
    else:
        rv = r * vec_normalize(v)

    #TODO: I think I'm re-calculating terms I did for a previous value of i?
    #       ...except I'm not because _rad_d1 has some Kronecker delta terms...
    #       still, it could all be made way more efficient I bet by reusing stuff
    new_derivs = []
    new_derivs.append(coord)
    new_comps = []
    new_comps.append(comps)
    inds = np.arange(len(ia))
    if order > 0:
        if derivs[1].ndim != 5:
            raise ValueError("as implemented, derivative blocks have to look like (nconfigs, nzlines, 3, natoms, 3)")
        config_shape = derivs[1].shape[:-4]
        d1 = np.zeros(config_shape + (i+1, 3, 3)) # the next block in the derivative tensor
        d1_comps = np.full((i+1, 3), None) # the components used to build the derivatives
        for z in range(i + 1):  # Lower-triangle is 0 so we do nothing with it
            for m in range(3):
                # we'll need to do some special casing for z < 2
                # also we gotta pull o
                dxa = derivs[1][inds, z, m, ia, :]
                dxb = derivs[1][inds, z, m, ib, :]
                dxc = derivs[1][inds, z, m, ic, :]

                # raise Exception(dxa.shape, derivs[1].shape)
                der, comps1 = _rad_d1(i, z, m, r, a, d, v, u, n, R1, R2, Q, rv, dxa, dxb, dxc)
                d1_comps[z, m] = _dumb_comps_wrapper(comps1)

                d1[inds, z, m, :] = der
        new_derivs.append(d1)
        new_comps.append(d1_comps)
        if order > 1:
            d2 = np.zeros(config_shape + (i+1, 3, i+1, 3, 3)) # the next block in the 2nd derivative tensor
            d2_comps = np.full((i+1, 3, i+1, 3), None) # the components used to build the derivatives
            for z1 in range(i + 1):
                for m1 in range(3):
                    for z2 in range(i + 1):
                        for m2 in range(3):
                                d2xa = derivs[2][inds, z1, m1, z2, m2, ia, :]
                                d2xb = derivs[2][inds, z1, m1, z2, m2, ib, :]
                                d2xc = derivs[2][inds, z1, m1, z2, m2, ic, :]
                                dr1, dq1, df1, dv1, du1, dn1, dR11, dR21, dQ1, drv1 = d1_comps[z1, m1].comp
                                dr2, dq2, df2, dv2, du2, dn2, dR12, dR22, dQ2, drv2 = d1_comps[z2, m2].comp

                                # now we feed this in
                                der, comps2 = _rad_d2(i, z1, m1, z2, m2,
                                                      r, a, d, v, u, n, R1, R2, Q, rv,
                                                      dr1, dq1, df1, dv1, du1, dn1, dR11, dR21, dQ1, drv1,
                                                      dr2, dq2, df2, dv2, du2, dn2, dR12, dR22, dQ2, drv2,
                                                      d2xa, d2xb, d2xc
                                                      )
                                d2[inds, z1, m1, z2, m2, :] = der
                                d2_comps[z1, m1, z2, m2] = _dumb_comps_wrapper(comps2)
            new_derivs.append(d2)
            new_comps.append(d2_comps)

    if return_comps:
        return new_derivs, new_comps
    else:
        return new_derivs

def vec_norm_derivs(a, order=1, zero_thresh=None):
    """
    Derivative of the norm of `a` with respect to its components

    :param a: vector
    :type a: np.ndarray
    :param order: number of derivatives to return
    :type order: int
    :param zero_thresh:
    :type zero_thresh:
    :return: derivative tensors
    :rtype: list
    """

    if order > 2:
        raise NotImplementedError("derivatives currently only up to order {}".format(2))

    derivs = []

    na = vec_norms(a)
    derivs.append(np.copy(na)) # we return the value itself for Taylor-series reasons

    # print(a.shape)
    a, zeros = vec_handle_zero_norms(a, na, zero_thresh=zero_thresh)
    na = na[..., np.newaxis]
    na[zeros] = Options.zero_placeholder

    if order >= 1:
        d1 = a / na
        # print(a.shape, na.shape)

        derivs.append(d1)

    if order >= 2:
        n = a.shape[-1]
        extra_shape = a.ndim - 1
        if extra_shape > 0:
            i3 = np.broadcast_to(np.eye(n), (1,)*extra_shape + (n, n))
        else:
            i3 = np.eye(n)
        v = vec_outer(d1, d1)
        # na shold have most of the extra_shape needed
        d2 = (i3 - v) / na[..., np.newaxis]
        derivs.append(d2)

    return derivs

def vec_sin_cos_derivs(a, b, order=1,
                       up_vectors=None,
                       check_derivatives=False, zero_thresh=None):
    """
    Derivative of `sin(a, b)` and `cos(a, b)` with respect to both vector components

    :param a: vector
    :type a: np.ndarray
    :param a: other vector
    :type a: np.ndarray
    :param order: number of derivatives to return
    :type order: int
    :param zero_thresh: threshold for when a norm should be called 0. for numerical reasons
    :type zero_thresh: None | float
    :return: derivative tensors
    :rtype: list
    """

    if order > 2:
        raise NotImplementedError("derivatives currently only up to order {}".format(2))

    extra_dims = a.ndim - 1

    sin_derivs = []
    cos_derivs = []

    a, n_a = vec_apply_zero_threshold(a, zero_thresh=zero_thresh)
    b, n_b = vec_apply_zero_threshold(b, zero_thresh=zero_thresh)

    n = vec_crosses(a, b)
    n, n_n, bad_ns = vec_apply_zero_threshold(n, zero_thresh=zero_thresh, return_zeros=True)

    adb = vec_dots(a, b)[..., np.newaxis]

    zero_thresh = Options.norm_zero_threshold if zero_thresh is None else zero_thresh

    s = n_n / (n_a * n_b)
    # s[n_n <= zero_thresh] = 0.
    c = adb / (n_a * n_b)
    # c[adb <= zero_thresh] = 0.

    sin_derivs.append(s)
    cos_derivs.append(c)

    if order > 0:
        if bad_ns.any():  # ill-defined sin components need an "up" vector and then point perpendicular to this
            if up_vectors is None:
                if n.ndim > 1:
                    up_vectors = np.broadcast_to(
                        np.array([0, 0, 1])[np.newaxis],
                        a.shape[:-1] + (3,)
                    )
                else:
                    up_vectors = np.array([0, 0, 1])
            if n.ndim == 1:
                n = vec_normalize(up_vectors)
                n_n = 1
            else:
                n[bad_ns] = vec_normalize(up_vectors[bad_ns])
                n_n[bad_ns] = 1

        bxn_ = vec_crosses(b, n)
        bxn, n_bxn = vec_apply_zero_threshold(bxn_, zero_thresh=zero_thresh)

        nxa_ = vec_crosses(n, a)
        nxa, n_nxa = vec_apply_zero_threshold(nxa_, zero_thresh=zero_thresh)

        if order <= 1:
            _, na_da = vec_norm_derivs(a, order=1)
            _, nb_db = vec_norm_derivs(b, order=1)
        else:
            _, na_da, na_daa = vec_norm_derivs(a, order=2)
            _, nb_db, nb_dbb = vec_norm_derivs(b, order=2)
            _, nn_dn, nn_dnn = vec_norm_derivs(n, order=2)

        if order >= 1:
            s_da = (bxn / (n_b * n_n) - s * na_da) / n_a
            s_db = (nxa / (n_n * n_a) - s * nb_db) / n_b

            # now we build our derivs, but we also need to transpose so that the OG shape comes first
            d1 = np.array([s_da, s_db])
            d1_reshape = tuple(range(1, extra_dims+1)) + (0, extra_dims+1)
            meh = d1.transpose(d1_reshape)

            sin_derivs.append(meh)

            # print(
            #     nb_db.shape,
            #     na_da.shape,
            #     c.shape,
            #     n_a.shape
            # )

            c_da = (nb_db - c * na_da) / n_a
            c_db = (na_da - c * nb_db) / n_b

            d1 = np.array([c_da, c_db])
            meh = d1.transpose(d1_reshape)

            cos_derivs.append(meh)

        if order >= 2:

            extra_dims = a.ndim - 1
            extra_shape = a.shape[:-1]
            if check_derivatives:
                if extra_dims > 0:
                    bad_norms = n_n.flatten() <= zero_thresh
                    if bad_norms.any():
                        raise ValueError("2nd derivative of sin not well defined when {} and {} are nearly colinear".format(
                            a[bad_norms],
                            b[bad_norms]
                        ))
                else:
                    if n_n <= zero_thresh:
                        raise ValueError("2nd derivative of sin not well defined when {} and {} are nearly colinear".format(
                            a, b
                        ))

            if extra_dims > 0:
                e3 = np.broadcast_to(pops.levi_cevita3,  extra_shape + (3, 3, 3))
                # td = np.tensordot
                outer = vec_outer
                vec_td = lambda a, b, **kw: vec_tensordot(a, b, shared=extra_dims, **kw)
            else:
                e3 = pops.levi_cevita3
                # td = np.tensordot
                vec_td = lambda a, b, **kw: vec_tensordot(a, b, shared=0, **kw)
                outer = np.outer
                a = a.squeeze()
                b = b.squeeze()
                nb_db = nb_db.squeeze(); na_da = na_da.squeeze(); nn_dn = nn_dn.squeeze()
                na_daa = na_daa.squeeze(); nb_dbb = nb_dbb.squeeze(); nn_dnn = nn_dnn.squeeze()

            # print(na_da, s_da, s, na_daa, bxdna)

            # compute terms we'll need for various cross-products
            e3b = vec_td(e3, b, axes=[-1, -1])
            e3a = vec_td(e3, a, axes=[-1, -1])
            # e3n = vec_td(e3, n, axes=[-1, -1])

            e3nbdb = vec_td(e3, nb_db, axes=[-1, -1])
            e3nada = vec_td(e3, na_da, axes=[-1, -1])
            e3nndn = vec_td(e3, nn_dn, axes=[-1, -1])

            n_da = -vec_td(e3b,  nn_dnn, axes=[-1, -2])
            bxdna = vec_td(n_da, e3nbdb, axes=[-1, -2])

            s_daa = - (
                outer(na_da, s_da) + outer(s_da, na_da)
                + s[..., np.newaxis] * na_daa
                - bxdna
            ) / n_a[..., np.newaxis]

            ndaXnada = -vec_td(n_da, e3nada, axes=[-1, -2])
            nndnXnadaa = vec_td(na_daa, e3nndn, axes=[-1, -2])

            s_dab = (
                         ndaXnada + nndnXnadaa - outer(s_da, nb_db)
            ) / n_b[..., np.newaxis]

            n_db = vec_td(e3a, nn_dnn, axes=[-1, -2])

            nbdbXnda = vec_td(n_db, e3nbdb, axes=[-1, -2])
            nbdbbXnndn = -vec_td(nb_dbb, e3nndn, axes=[-1, -2])

            s_dba = (
                    nbdbXnda + nbdbbXnndn - outer(s_db, na_da)
            ) / n_a[..., np.newaxis]

            dnbxa = - vec_td(n_db, e3nada, axes=[-1, -2])

            s_dbb = - (
                outer(nb_db, s_db) + outer(s_db, nb_db) + s[..., np.newaxis] * nb_dbb - dnbxa
            ) / n_b[..., np.newaxis]

            s2 = np.array([
                [s_daa, s_dab],
                [s_dba, s_dbb]
            ])

            d2_reshape = tuple(range(2, extra_dims+2)) + (0, 1, extra_dims+2, extra_dims+3)
            s2 = s2.transpose(d2_reshape)

            sin_derivs.append(s2)

            # na_daa = np.zeros_like(na_daa)

            c_daa = - (
                outer(na_da, c_da) + outer(c_da, na_da)
                + c[..., np.newaxis] * na_daa
            ) / n_a[..., np.newaxis]
            c_dab = (na_daa - outer(c_da, nb_db)) / n_b[..., np.newaxis]
            c_dba = (nb_dbb - outer(c_db, na_da)) / n_a[..., np.newaxis]
            c_dbb = - (
                outer(nb_db, c_db) + outer(c_db, nb_db)
                + c[..., np.newaxis] * nb_dbb
            ) / n_b[..., np.newaxis]

            c2 = np.array([
                [c_daa, c_dab],
                [c_dba, c_dbb]
            ])

            c2 = c2.transpose(d2_reshape)

            cos_derivs.append(c2)

    return sin_derivs, cos_derivs

def coord_deriv_mat(nats, coords, axes=None, base_shape=None):
    if axes is None:
        axes = [0, 1, 2]
    if misc.is_numeric(coords):
        coords = [coords]
    z = np.zeros((nats, 3, nats, 3))
    row_inds = np.repeat(coords, len(axes), axis=0)
    col_inds = np.repeat(axes, len(coords), axis=0).flatten()
    z[row_inds, col_inds, row_inds, col_inds] = 1
    z = z.reshape(nats*3, nats*3)
    if base_shape is not None:
        sh = z.shape
        expax = list(range(len(base_shape)))
        z = np.broadcast_to(np.expand_dims(z, expax), base_shape + sh)
    return z

def jacobian_mat_inds(ind_lists, axes=None):
    if axes is None:
        axes = [0, 1, 2]

    smol = misc.is_numeric(ind_lists[0])
    ind_lists = [
        np.asanyarray([i] if smol else i).reshape(-1)
        for i in ind_lists
    ]

    nstruct = ind_lists[0].shape[0]
    struct_inds = np.repeat(np.arange(nstruct), len(axes), axis=0)

    inds = []
    for i in ind_lists:
        row_inds = np.repeat(i, len(axes), axis=0)
        col_inds = np.repeat(axes, len(i), axis=0).flatten()
        inds.append((struct_inds, row_inds, col_inds, col_inds))

    return inds

def jacobian_proj_inds(ind_lists, axes=None):
    if axes is None:
        axes = [0, 1, 2]
    axes = np.asanyarray(axes)

    smol = misc.is_numeric(ind_lists[0][0])
    ind_lists = [
        [
            np.asanyarray([i] if smol else i).reshape(-1),
            np.asanyarray([a] if smol else a).reshape(-1)
        ]
        for i,a in ind_lists
    ]

    nstruct = ind_lists[0][0].shape[0]
    struct_inds = np.repeat(np.arange(nstruct), len(axes), axis=0)

    inds = []
    for i,a in ind_lists:
        ax = axes + len(axes) * a
        row_inds = np.repeat(i, len(axes), axis=0)
        col_inds = np.repeat(axes, len(i), axis=0).flatten()
        scol_inds = ax
        inds.append((struct_inds, row_inds, col_inds, scol_inds))

    return inds

def fill_disp_jacob_atom(mat, ind_val_pairs, base_shape=None, axes=None):
    ind_lists = [i for i,v in ind_val_pairs]
    vals = [v for i,v in ind_val_pairs]
    smol = misc.is_numeric(ind_lists[0])
    ind_lists = [
        np.asanyarray([i] if smol else i)
        for i in ind_lists
    ]

    i_shape = ind_lists[0].shape
    nnew = len(i_shape)
    if base_shape is None:
        base_shape = mat.shape[:-3]
    target_shape = base_shape + i_shape + mat.shape[-3:]
    if target_shape != mat.shape:
        nog = len(base_shape)
        mat = np.broadcast_to(
            np.expand_dims(mat, np.arange(nog, nog+nnew).tolist()),
            target_shape
        ).copy()
    else:
        base_shape = mat.shape[:-(3+nnew)]
        # target_shape = base_shape + i_shape + mat.shape[-3:]

    mat = np.reshape(mat, base_shape + (np.prod(i_shape, dtype=int),) + mat.shape[-3:])
    for idx_tup,val in zip(jacobian_mat_inds(ind_lists, axes=axes), vals):
        idx_tup = (...,) + idx_tup
        mat[idx_tup] = val
    mat = mat.reshape(target_shape)

    if smol:
        mat = mat.reshape(base_shape + mat.shape[-3:])
    return mat

def fill_proj_jacob_atom(mat, ind_val_pairs, base_shape=None, axes=None):
    ind_lists = [[i,a] for i,a,v in ind_val_pairs]
    vals = [v for i,a,v in ind_val_pairs]
    smol = misc.is_numeric(ind_lists[0][0])
    ind_lists = [
        [
            np.asanyarray([i] if smol else i),
            np.asanyarray([a] if smol else a),
        ]
        for i,a in ind_lists
    ]

    i_shape = ind_lists[0][0].shape
    nnew = len(i_shape)
    if base_shape is None:
        base_shape = mat.shape[:-3]
    target_shape = base_shape + i_shape + mat.shape[-3:]
    if target_shape != mat.shape:
        nog = len(base_shape)
        mat = np.broadcast_to(
            np.expand_dims(mat, np.arange(nog, nog+nnew).tolist()),
            target_shape
        ).copy()
    else:
        base_shape = mat.shape[:-(3+nnew)]
        # target_shape = base_shape + i_shape + mat.shape[-3:]

    mat = np.reshape(mat, base_shape + (np.prod(i_shape, dtype=int),) + mat.shape[-3:])
    for idx_tup,val in zip(jacobian_proj_inds(ind_lists, axes=axes), vals):
        idx_tup = (...,) + idx_tup
        mat[idx_tup] = val
    mat = mat.reshape(target_shape)

    if smol:
        mat = mat.reshape(base_shape + mat.shape[-3:])
    return mat

fast_proj = True
def disp_deriv_mat(coords, i, j, at_list, axes=None):
    if not fast_proj:
        mats = np.zeros(coords.shape + (3,))
        return None, fill_disp_jacob_atom(
            mats,
            [[i, 1], [j, -1]],
            axes=axes,
            base_shape=coords.shape[:-2]
        )
    else:
        proj = np.zeros(coords.shape + (3 * len(at_list),))
        mats = np.zeros(coords[..., at_list, :].shape + (3,))
        _, (a, b), _ = np.intersect1d(at_list, [i, j], return_indices=True)
        a, b = np.sort([a,b])
        mats = fill_disp_jacob_atom(
            mats,
            [[a, 1], [b, -1]],
            axes=axes,
            base_shape=coords.shape[:-2]
        )
        proj = fill_proj_jacob_atom(
            proj,
            [[x, n, 1] for n,x in enumerate(at_list)],
            axes=axes,
            base_shape=coords.shape[:-2]
        )
        proj = proj.reshape(proj.shape[:-3] + (-1, proj.shape[-1]))
        return proj, mats

def prep_disp_expansion(coords, i, j, at_list, fixed_atoms=None, expand=True):
    a = coords[..., j, :] - coords[..., i, :]

    if expand:
        proj, A_d = disp_deriv_mat(coords, j, i, at_list)
        if fixed_atoms is not None:
            if fast_proj:
                _, fixed_atoms, _ = np.intersect1d(at_list, fixed_atoms, return_indices=True)
            A_d = fill_disp_jacob_atom(A_d, [[x, 0] for x in fixed_atoms], base_shape=coords.shape[:-2])

        return proj, [a, misc.flatten_inds(A_d, [-3, -2])]
    else:
        return [a]


def vec_angle_derivs(a, b, order=1, up_vectors=None, zero_thresh=None, return_comps=False):
    """
    Returns the derivatives of the angle between `a` and `b` with respect to their components

    :param a: vector
    :type a: np.ndarray
    :param b: vector
    :type b: np.ndarray
    :param order: order of derivatives to go up to
    :type order: int
    :param zero_thresh: threshold for what is zero in a vector norm
    :type zero_thresh: float | None
    :return: derivative tensors
    :rtype: list
    """

    if order > 2:
        raise NotImplementedError("derivatives currently only up to order {}".format(2))

    derivs = []

    sin_derivs, cos_derivs = vec_sin_cos_derivs(a, b,
                                                up_vectors=up_vectors,
                                                order=order, zero_thresh=zero_thresh)
    # cos_expansion = [0] + [block_array(c, i+1) for i,c in enumerate(cos_derivs[1:])]
    # sin_expansion = [0] + [block_array(c, i+1) for i,c in enumerate(sin_derivs[1:])]
    # print(
    #     (cos_expansion[1][:, np.newaxis, np.newaxis] * sin_expansion[2][np.newaxis, :, :])[2][:3, :3]
    # )
    # print(
    #     (sin_expansion[1][:, np.newaxis, np.newaxis] * cos_expansion[2][np.newaxis, :, :])[2][:3, :3]
    # )

    s = sin_derivs[0]
    c = cos_derivs[0]

    q = np.arctan2(s, c)
    # # force wrapping if near to pi
    # if isinstance(q, np.ndarray):
    #     sel = np.abs(q) > np.pi - 1e-10
    #     q[sel] = np.abs(q[sel])
    # elif np.abs(q) > np.pi - 1e-10:
    #     q = np.abs(q)

    if up_vectors is not None:
        n = vec_crosses(a, b)
        if up_vectors.ndim < n.ndim:
            up_vectors = np.broadcast_to(up_vectors, n.shape[:-len(up_vectors.shape)] + up_vectors.shape)

        # zero_thresh = Options.norm_zero_threshold if zero_thresh is None else zero_thresh
        up = vec_dots(up_vectors, n)
        # up[np.abs(up) < zero_thresh] = 0.
        sign = np.sign(up)
    else:
        sign = np.ones(a.shape[:-1])

    if isinstance(sign, np.ndarray):
        sign[sign == 0] = 1.
    elif sign == 0:
        sign = np.array(1)

    derivs.append(sign*q)

    if order >= 1:
        # d = sin_derivs[1]
        # s_da = d[..., 0, :]; s_db = d[..., 1, :]
        # d = cos_derivs[1]
        # c_da = d[..., 0, :]; c_db = d[..., 1, :]
        #
        # q_da = c * s_da - s * c_da
        # q_db = c * s_db - s * c_db

        # we can do some serious simplification here
        # if we use some of the analytic work I've done
        # to write these in terms of the vector tangent
        # to the rotation

        a, na = vec_apply_zero_threshold(a, zero_thresh=zero_thresh)
        b, nb = vec_apply_zero_threshold(b, zero_thresh=zero_thresh)

        ha = a / na
        hb = b / nb

        ca = hb - (vec_dots(ha, hb)[..., np.newaxis]) * ha
        cb = ha - (vec_dots(hb, ha)[..., np.newaxis]) * hb

        ca, nca = vec_apply_zero_threshold(ca, zero_thresh=zero_thresh)
        cb, ncb = vec_apply_zero_threshold(cb, zero_thresh=zero_thresh)

        ca = ca / nca
        cb = cb / ncb

        q_da = -ca/na
        q_db = -cb/nb

        extra_dims = a.ndim - 1
        extra_shape = a.shape[:-1]

        d1 = (
            sign[np.newaxis, ..., np.newaxis] *
            np.array([q_da, q_db])
        )
        d1_reshape = tuple(range(1, extra_dims + 1)) + (0, extra_dims + 1)
        derivs.append(d1.transpose(d1_reshape))

    if order >= 2:

        d = sin_derivs[1]
        s_da = d[..., 0, :]; s_db = d[..., 1, :]
        d = cos_derivs[1]
        c_da = d[..., 0, :]; c_db = d[..., 1, :]

        d = sin_derivs
        s_daa = d[2][..., 0, 0, :, :]; s_dab = d[2][..., 0, 1, :, :]
        s_dba = d[2][..., 1, 0, :, :]; s_dbb = d[2][..., 1, 1, :, :]

        d = cos_derivs
        c_daa = d[2][..., 0, 0, :, :]; c_dab = d[2][..., 0, 1, :, :]
        c_dba = d[2][..., 1, 0, :, :]; c_dbb = d[2][..., 1, 1, :, :]

        c = c[..., np.newaxis]
        s = s[..., np.newaxis]
        q_daa = vec_outer(c_da, s_da) + c * s_daa - vec_outer(s_da, c_da) - s * c_daa
        q_dba = vec_outer(c_da, s_db) + c * s_dba - vec_outer(s_da, c_db) - s * c_dba
        q_dab = vec_outer(c_db, s_da) + c * s_dab - vec_outer(s_db, c_da) - s * c_dab
        q_dbb = vec_outer(c_db, s_db) + c * s_dbb - vec_outer(s_db, c_db) - s * c_dbb

        d2 = (
                sign[np.newaxis, np.newaxis, ..., np.newaxis, np.newaxis] *
                np.array([
                    [q_daa, q_dab],
                    [q_dba, q_dbb]
                ])
        )

        d2_reshape = tuple(range(2, extra_dims+2)) + (0, 1, extra_dims+2, extra_dims+3)

        derivs.append(
            d2.transpose(d2_reshape)
        )

    if return_comps:
        return derivs, (sin_derivs, cos_derivs)
    else:
        return derivs

def dist_deriv(coords, i, j, /, order=1, method='expansion', fixed_atoms=None, expanded_vectors=None, zero_thresh=None):
    """
    Gives the derivative of the distance between i and j with respect to coords i and coords j

    :param coords:
    :type coords: np.ndarray
    :param i: index of one of the atoms
    :type i: int | Iterable[int]
    :param j: index of the other atom
    :type j: int | Iterable[int]
    :return: derivatives of the distance with respect to atoms i, j, and k
    :rtype: list
    """

    if method == 'expansion':
        proj, A_expansion = prep_disp_expansion(coords, j, i, [i, j], fixed_atoms=fixed_atoms, expand=True)
        base_deriv = td.vec_norm_unit_deriv(A_expansion, order=order)[0]
        if proj is None: return base_deriv
        return [base_deriv[0]] + td.tensor_reexpand([proj], base_deriv[1:])
    else:

        if order > 2:
            raise NotImplementedError("derivatives currently only up to order {}".format(2))

        a = coords[..., j, :] - coords[..., i, :]
        d = vec_norm_derivs(a, order=order, zero_thresh=zero_thresh)

        derivs = []

        derivs.append(d[0])

        if order >= 1:
            da = d[1]
            derivs.append(np.array([-da, da]))

        if order >= 2:
            daa = d[2]
            # ii ij
            # ji jj
            derivs.append(np.array([
                [ daa, -daa],
                [-daa,  daa]
            ]))

        return derivs

def angle_deriv(coords, i, j, k, /, order=1, method='expansion', angle_ordering='jik',
                fixed_atoms=None,
                expanded_vectors=None,
                zero_thresh=None
                ):
    """
    Gives the derivative of the angle between i, j, and k with respect to the Cartesians

    :param coords:
    :type coords: np.ndarray
    :param i: index of the central atom
    :type i: int | Iterable[int]
    :param j: index of one of the outside atoms
    :type j: int | Iterable[int]
    :param k: index of the other outside atom
    :type k: int | Iterable[int]
    :return: derivatives of the angle with respect to atoms i, j, and k
    :rtype: np.ndarray
    """

    if method == 'expansion':
        if expanded_vectors is None:
            expanded_vectors = [0, 1]
        if angle_ordering == 'ijk':
            proj, A_expansion = prep_disp_expansion(coords, i, j, [j, i, k], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
            _, B_expansion = prep_disp_expansion(coords, k, j, [j, i, k], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)
        else:
            proj, A_expansion = prep_disp_expansion(coords, j, i, [i, j, k], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
            _, B_expansion = prep_disp_expansion(coords, k, i, [i, j, k], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)

        # A_expansion = [A_expansion[0], np.concatenate([np.eye(3), np.zeros((3, 3))], axis=0)]
        # B_expansion = [B_expansion[0], np.concatenate([np.zeros((3, 3)), np.eye(3)], axis=0)]
        base_deriv = td.vec_angle_deriv(A_expansion, B_expansion, order=order)
        if proj is None: return base_deriv
        return [base_deriv[0]] + td.tensor_reexpand([proj], base_deriv[1:])
    else:
        if angle_ordering == 'ijk':
            # derivs = angle_deriv(coords, j, i, k, order=order, angle_ordering='jik',
            #                      method=method,
            #                      fixed_atoms=fixed_atoms,
            #                      expanded_vectors=expanded_vectors,
            #                      zero_thresh=zero_thresh
            #                      )
            # change signs if necessary
            raise NotImplementedError('too annoying')


        if order > 2:
            raise NotImplementedError("derivatives currently only up to order {}".format(2))

        a = coords[..., j, :] - coords[..., i, :]
        b = coords[..., k, :] - coords[..., i, :]
        d = vec_angle_derivs(a, b, order=order, zero_thresh=zero_thresh)

        derivs = []

        derivs.append(d[0])

        if order >= 1:
            da = d[1][..., 0, :]; db = d[1][..., 1, :]
            derivs.append(np.array([-(da + db), da, db]))

        if order >= 2:
            daa = d[2][..., 0, 0, :, :]; dab = d[2][..., 0, 1, :, :]
            dba = d[2][..., 1, 0, :, :]; dbb = d[2][..., 1, 1, :, :]
            # ii ij ik
            # ji jj jk
            # ki kj kk
            derivs.append(np.array([
                [daa + dba + dab + dbb, -(daa + dab), -(dba + dbb)],
                [         -(daa + dba),          daa,   dba       ],
                [         -(dab + dbb),          dab,   dbb       ]
            ]))

        return derivs

def rock_deriv(coords, i, j, k, /, order=1, method='expansion', angle_ordering='ijk', zero_thresh=None, fixed_atoms=None, expanded_vectors=None):
    """
    Gives the derivative of the rocking motion (symmetric bend basically)

    :param coords:
    :type coords: np.ndarray
    :param i: index of the central atom
    :type i: int | Iterable[int]
    :param j: index of one of the outside atoms
    :type j: int | Iterable[int]
    :param k: index of the other outside atom
    :type k: int | Iterable[int]
    :return: derivatives of the angle with respect to atoms i, j, and k
    :rtype: np.ndarray
    """


    if method == 'expansion':
        if expanded_vectors is None:
            expanded_vectors = [0, 1]

        if angle_ordering == 'ijk':
            proj, A_expansion = prep_disp_expansion(coords, i, j, [i, j, k], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
            _, B_expansion = prep_disp_expansion(coords, k, j, [i, j, k], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)
        else:
            proj, A_expansion = prep_disp_expansion(coords, j, i, [i, j, k], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
            _, B_expansion = prep_disp_expansion(coords, k, i, [i, j, k], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)

        A_deriv = td.vec_angle_deriv(A_expansion, B_expansion[:1], order=order)
        B_deriv = td.vec_angle_deriv(A_expansion[:1], B_expansion, order=order)
        base_deriv = [A_deriv[0]] + [ad - bd for ad,bd in zip(A_deriv[1:], B_deriv[1:])]
        if proj is None: return base_deriv
        return [base_deriv[0]] + td.tensor_reexpand([proj], base_deriv[1:])

    else:

        if angle_ordering == 'ijk':
            raise NotImplementedError("too annoying")

        if order > 2:
            raise NotImplementedError("derivatives currently only up to order {}".format(2))
        a = coords[..., j, :] - coords[..., i, :]
        b = coords[..., k, :] - coords[..., i, :]

        d = vec_angle_derivs(a, b, order=order, zero_thresh=zero_thresh)

        derivs = []

        derivs.append(d[0])

        if order >= 1:
            da = d[1][..., 0, :]; db = d[1][..., 1, :]
            derivs.append(np.array([-(da - db), da, -db]))

        if order >= 2:
            daa = d[2][..., 0, 0, :, :]; dab = d[2][..., 0, 1, :, :]
            dba = d[2][..., 1, 0, :, :]; dbb = d[2][..., 1, 1, :, :]
            # ii ij ik
            # ji jj jk
            # ki kj kk
            derivs.append(np.array([
                [daa + dba + dab + dbb, -(daa + dab), -(dba + dbb)],
                [         -(daa + dba),          daa,   dba       ],
                [         -(dab + dbb),          dab,   dbb       ]
            ]))

        return derivs

def dihed_deriv(coords, i, j, k, l, /, order=1, zero_thresh=None, method='expansion',
                fixed_atoms=None,
                expanded_vectors=None):
    """
    Gives the derivative of the dihedral between i, j, k, and l with respect to the Cartesians
    Currently gives what are sometimes called the `psi` angles.
    Can also support more traditional `phi` angles by using a different angle ordering

    :param coords:
    :type coords: np.ndarray
    :param i:
    :type i: int | Iterable[int]
    :param j:
    :type j: int | Iterable[int]
    :param k:
    :type k: int | Iterable[int]
    :param l:
    :type l: int | Iterable[int]
    :return: derivatives of the dihedral with respect to atoms i, j, k, and l
    :rtype: np.ndarray
    """

    if method == 'expansion':
        if expanded_vectors is None:
            expanded_vectors = [0, 1, 2]
        proj, A_expansion = prep_disp_expansion(coords, j, i, [i, j, k, l], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
        _, B_expansion = prep_disp_expansion(coords, k, j, [i, j, k, l], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)
        _, C_expansion = prep_disp_expansion(coords, l, k, [i, j, k, l], fixed_atoms=fixed_atoms, expand=2 in expanded_vectors)

        base_deriv = td.vec_dihed_deriv(A_expansion, B_expansion, C_expansion, order=order)
        if proj is None: return base_deriv
        return [base_deriv[0]] + td.tensor_reexpand([proj], base_deriv[1:])

    else:
        if fixed_atoms is not None:
            raise NotImplementedError("direct derivatives with specified fixed atoms not implemented")
        if order > 2:
            raise NotImplementedError("derivatives currently only up to order {}".format(2))

        a = coords[..., j, :] - coords[..., i, :]
        b = coords[..., k, :] - coords[..., j, :]
        c = coords[..., l, :] - coords[..., k, :]

        n1 = vec_crosses(a, b)
        n2 = vec_crosses(b, c)

        # coll = vec_crosses(n1, n2)
        # coll_norms = vec_norms(coll)
        # bad = coll_norms < 1.e-17
        # if bad.any():
        #     raise Exception([
        #         bad,
        #         i, j, k, l,
        #         a[bad], b[bad], c[bad]])

        # zero_thresh = Options.norm_zero_threshold if zero_thresh is None else zero_thresh

        cnb = vec_crosses(n1, n2)

        cnb, n_cnb, bad_friends = vec_apply_zero_threshold(cnb, zero_thresh=zero_thresh, return_zeros=True)
        bad_friends = bad_friends.reshape(cnb.shape[:-1])
        orient = vec_dots(b, cnb)
        # orient[np.abs(orient) < 1.0] = 0.
        sign = np.sign(orient)

        d, (sin_derivs, cos_derivs) = vec_angle_derivs(n1, n2, order=order,
                                                       up_vectors=vec_normalize(b),
                                                       zero_thresh=zero_thresh, return_comps=True)

        derivs = []

        derivs.append(d[0])

        if order >= 1:
            dn1 = d[1][..., 0, :]; dn2 = d[1][..., 1, :]
            if dn1.ndim == 1:
                if bad_friends:
                    dn1 = sin_derivs[1][0]
                    dn2 = sin_derivs[1][1]
                    sign = np.array(1)
            else:
                dn1[bad_friends] = sin_derivs[1][bad_friends, 0, :] # TODO: clean up shapes I guess...
                dn2[bad_friends] = sin_derivs[1][bad_friends, 1, :]
                sign[bad_friends] = 1

            di = vec_crosses(b, dn1)
            dj = vec_crosses(c, dn2) - vec_crosses(a+b, dn1)
            dk = vec_crosses(a, dn1) - vec_crosses(b+c, dn2)
            dl = vec_crosses(b, dn2)

            deriv_tensors = sign[np.newaxis, ..., np.newaxis]*np.array([di, dj, dk, dl])

            # if we have problem points we deal with them via averaging
            # over tiny displacements since the dihedral derivative is
            # continuous
            # if np.any(bad_friends):
            #     raise NotImplementedError("planar dihedral angles remain an issue for me...")
            #     if coords.ndim > 2:
            #         raise NotImplementedError("woof")
            #     else:
            #         bad_friends = bad_friends.flatten()
            #         bad_i = i[bad_friends]
            #         bad_j = j[bad_friends]
            #         bad_k = k[bad_friends]
            #         bad_l = l[bad_friends]
            #         bad_coords = np.copy(coords)
            #         if isinstance(i, (int, np.integer)):
            #             raise NotImplementedError("woof")
            #         else:
            #             # for now we do this with finite difference...
            #             for which,(bi,bj,bk,bl) in enumerate(zip(bad_i, bad_j, bad_k, bad_l)):
            #                 for nat,at in enumerate([bi, bj, bk, bl]):
            #                     for x in range(3):
            #                         bad_coords[at, x] += zero_point_step_size
            #                         d01, = dihed_deriv(bad_coords, bi, bj, bk, bl, order=0, zero_thresh=-1.0)
            #                         bad_coords[at, x] -= 2*zero_point_step_size
            #                         d02, = dihed_deriv(bad_coords, bi, bj, bk, bl, order=0, zero_thresh=-1.0)
            #                         bad_coords[at, x] += zero_point_step_size
            #                         deriv_tensors[nat, which, x] = (d01[0] + d02[0])/(2*zero_point_step_size)
            #                         # print(
            #                         #     "D1", d1[nat, x]
            #                         #
            #                         # )
            #                         # print(
            #                         #     "D2", d2[nat, x]
            #                         #
            #                         # )
            #                         # print("avg", (d1[nat, x] + d2[nat, x])/2)
            #                         # print("FD", (d01[0], d02[0]))#/(2*zero_point_step_size))
            #                         # raise Exception(
            #                         #  "wat",
            #                         #     di,
            #                         # d01.shape
            #                         # )

            derivs.append(deriv_tensors)


        if order >= 2:

            d11 = d[2][..., 0, 0, :, :]; d12 = d[2][..., 0, 1, :, :]
            d21 = d[2][..., 1, 0, :, :]; d22 = d[2][..., 1, 1, :, :]

            # explicit write out of chain-rule transformations to isolate different Kron-delta terms
            extra_dims = a.ndim - 1
            extra_shape = a.shape[:-1]
            dot = lambda x, y, axes=(-1, -2) : vec_tensordot(x, y, axes=axes, shared=extra_dims)
            if extra_dims > 0:
                e3 = np.broadcast_to(pops.levi_cevita3,  extra_shape + pops.levi_cevita3.shape)
            else:
                e3 = pops.levi_cevita3

            Ca = dot(e3, a, axes=[-1, -1])
            Cb = dot(e3, b, axes=[-1, -1])
            Cc = dot(e3, c, axes=[-1, -1])
            Cab = Ca+Cb
            Cbc = Cb+Cc

            CaCa, CaCb, CaCc, CaCab, CaCbc = [dot(Ca, x) for x in (Ca, Cb, Cc, Cab, Cbc)]
            CbCa, CbCb, CbCc, CbCab, CbCbc = [dot(Cb, x) for x in (Ca, Cb, Cc, Cab, Cbc)]
            CcCa, CcCb, CcCc, CcCab, CcCbc = [dot(Cc, x) for x in (Ca, Cb, Cc, Cab, Cbc)]
            CabCa, CabCb, CabCc, CabCab, CabCbc = [dot(Cab, x) for x in (Ca, Cb, Cc, Cab, Cbc)]
            CbcCa, CbcCb, CbcCc, CbcCab, CbcCbc = [dot(Cbc, x) for x in (Ca, Cb, Cc, Cab, Cbc)]

            dii = dot(CbCb, d11)
            dij = dot(CcCb, d12) - dot(CabCb, d11)
            dik = dot(CaCb, d11) - dot(CbcCb, d12)
            dil = dot(CbCb, d12)

            dji = dot(CbCc, d21) - dot(CbCab, d11)
            djj = dot(CabCab, d11) - dot(CabCc, d21) - dot(CcCab, d12) + dot(CcCc, d22)
            djk = dot(CbcCab, d12) - dot(CbcCc, d22) - dot(CaCab, d11) + dot(CaCc, d21)
            djl = dot(CbCc, d22) - dot(CbCab, d12)

            dki = dot(CbCa, d11) - dot(CbCbc, d21)
            dkj = dot(CabCbc, d21) - dot(CcCbc, d22) - dot(CabCa, d11) + dot(CcCa, d12)
            dkk = dot(CaCa, d11) - dot(CaCbc, d21) - dot(CbcCa, d12) + dot(CbcCbc, d22)
            dkl = dot(CbCa, d12) - dot(CbCbc, d22)

            dli = dot(CbCb, d21)
            dlj = dot(CcCb, d22) - dot(CabCb, d21)
            dlk = dot(CaCb, d21) - dot(CbcCb, d22)
            dll = dot(CbCb, d22)

            derivs.append(
                -sign[np.newaxis, np.newaxis, ..., np.newaxis, np.newaxis] *
                np.array([
                    [dii, dij, dik, dil],
                    [dji, djj, djk, djl],
                    [dki, dkj, dkk, dkl],
                    [dli, dlj, dlk, dll]
                ])
            )

    return derivs

def book_deriv(coords, i, j, k, l, /, order=1, zero_thresh=None, method='expansion',
               fixed_atoms=None,
               expanded_vectors=None):
    if method == 'expansion':
        if expanded_vectors is None:
            expanded_vectors = [0, 1, 2]
        proj, A_expansion = prep_disp_expansion(coords, j, i, [i, j, k, l], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
        _, B_expansion = prep_disp_expansion(coords, k, j, [i, j, k, l], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)
        _, C_expansion = prep_disp_expansion(coords, l, j, [i, j, k, l], fixed_atoms=fixed_atoms, expand=2 in expanded_vectors)

        base_deriv = td.vec_dihed_deriv(A_expansion, B_expansion, C_expansion, order=order)
        if proj is None: return base_deriv
        return [base_deriv[0]] + td.tensor_reexpand([proj], base_deriv[1:])
    else:
        raise NotImplementedError("too annoying")

def oop_deriv(coords, i, j, k, /, order=1, method='expansion',
               fixed_atoms=None,
               expanded_vectors=None):
    if method == 'expansion':
        if fixed_atoms is None: fixed_atoms = []
        fixed_atoms = list(fixed_atoms) + [j]
        if expanded_vectors is None:
            expanded_vectors = [0, 1]
        proj, A_expansion = prep_disp_expansion(coords, j, i, [i, j, k], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
        _, B_expansion = prep_disp_expansion(coords, k, j, [i, j, k], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)
        _, C_expansion = prep_disp_expansion(coords, i, k, [i, j, k], fixed_atoms=fixed_atoms, expand=2 in expanded_vectors)

        base_deriv = td.vec_dihed_deriv(A_expansion, B_expansion, C_expansion, order=order)
        if proj is None: return base_deriv
        return [base_deriv[0]] + td.tensor_reexpand([proj], base_deriv[1:])
    else:
        raise NotImplementedError("too annoying")

def plane_angle_deriv(coords, i, j, k, l, m, n, /, order=1,
                      method='expansion',
                      fixed_atoms=None,
                      expanded_vectors=None,

                      ):
    if method == 'expansion':
        if expanded_vectors is None:
            expanded_vectors = [0, 1, 2, 3]
        proj, A_expansion = prep_disp_expansion(coords, j, i, [i, j, k, l, m], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
        _, B_expansion = prep_disp_expansion(coords, k, j, [i, j, k, l, m], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)
        _, C_expansion = prep_disp_expansion(coords, m, l, [i, j, k, l, m], fixed_atoms=fixed_atoms, expand=2 in expanded_vectors)
        _, D_expansion = prep_disp_expansion(coords, n, m, [i, j, k, l, m], fixed_atoms=fixed_atoms, expand=3 in expanded_vectors)

        base_deriv = td.vec_plane_angle_deriv(A_expansion, B_expansion, C_expansion, D_expansion, order=order)
        if proj is None: return base_deriv
        return [base_deriv[0]] + td.tensor_reexpand([proj], base_deriv[1:])
    else:
        raise NotImplementedError("too annoying")

def wag_deriv(coords, i, j, k, l=None, m=None, n=None, /, order=1, method='expansion',
               fixed_atoms=None,
               expanded_vectors=None):
    if method == 'expansion':
        if fixed_atoms is None: fixed_atoms = []
        fixed_atoms = list(fixed_atoms) + [j]
        if expanded_vectors is None:
            expanded_vectors = [0, 1]
        if l is None: l = i
        if m is None: m = j
        if n is None: n = k
        proj, A_expansion = prep_disp_expansion(coords, j, i, [i, j, k, l, m, n], fixed_atoms=fixed_atoms, expand=0 in expanded_vectors)
        _, B_expansion = prep_disp_expansion(coords, k, j, [i, j, k, l, m, n], fixed_atoms=fixed_atoms, expand=1 in expanded_vectors)
        _, C_expansion = prep_disp_expansion(coords, m, l, [i, j, k, l, m, n], fixed_atoms=fixed_atoms, expand=2 in expanded_vectors)
        _, D_expansion = prep_disp_expansion(coords, n, m, [i, j, k, l, m, n], fixed_atoms=fixed_atoms, expand=2 in expanded_vectors)

        i_deriv = td.vec_dihed_deriv(A_expansion, B_expansion[:1], C_expansion, order=order)
        k_deriv = td.vec_dihed_deriv(A_expansion[:1], B_expansion, C_expansion, order=order)
        base_deriv = [i_deriv[0]] + [ad - bd for ad, bd in zip(i_deriv[1:], k_deriv[1:])]
        if proj is None: return base_deriv
        return [base_deriv[0]] + td.tensor_reexpand([proj], base_deriv[1:])
    else:
        raise NotImplementedError("too annoying")



def _pop_bond_vecs(bond_tf, i, j, coords):
    bond_vectors = np.zeros(coords.shape)
    bond_vectors[..., i, :] = bond_tf[0]
    bond_vectors[..., j, :] = bond_tf[1]

    return bond_vectors.reshape(
        coords.shape[:-2] + (coords.shape[-2] * coords.shape[-1],)
    )
def _fill_derivs(coords, idx, derivs):
    vals = []
    # nx = np.prod(coords.shape, dtype=int)
    nats = len(coords)
    for n, d in enumerate(derivs):
        if n == 0:
            vals.append(d)
            continue
        tensor = np.zeros((nats, 3) * n)
        for pos in itertools.product(*[range(len(idx)) for _ in range(n)]):
            actual = ()
            for r in pos:
                actual += (slice(None) if idx[r] is None else idx[r], slice(None))
            tensor[actual] = d[pos]
        vals.append(tensor.reshape((nats * 3,) * n))
    return vals
def dist_vec(coords, i, j, order=None, method='expansion', fixed_atoms=None):
    """
    Returns the full vectors that define the linearized version of a bond displacement

    :param coords:
    :param i:
    :param j:
    :return:
    """

    derivs = dist_deriv(coords, i, j, method=method, order=(1 if order is None else order), fixed_atoms=fixed_atoms)
    if method == 'expansion':
        return derivs[1] if order is None else derivs
    else:
        if order is None:
            return _pop_bond_vecs(derivs[1], i, j, coords)
        else:
            return _fill_derivs(coords, (i,j), derivs)

def angle_vec(coords, i, j, k, order=None, method='expansion', angle_ordering='ijk', fixed_atoms=None):
    """
    Returns the full vectors that define the linearized version of an angle displacement

    :param coords:
    :param i:
    :param j:
    :return:
    """

    derivs = angle_deriv(coords, i, j, k, order=(1 if order is None else order), method=method,
                         angle_ordering=angle_ordering,
                         fixed_atoms=fixed_atoms)
    if method == 'expansion':
        return derivs[1] if order is None else derivs
    else:
        full = _fill_derivs(coords, (i, j, k), derivs)
        if order is None:
            return full[1]
        else:
            return full

def rock_vec(coords, i, j, k, order=None, method='expansion', fixed_atoms=None):
    """
    Returns the full vectors that define the linearized version of an angle displacement

    :param coords:
    :param i:
    :param j:
    :return:
    """

    derivs = rock_deriv(coords, i, j, k, order=(1 if order is None else order), fixed_atoms=fixed_atoms, method=method)
    if method == 'expansion':
        return derivs[1] if order is None else derivs
    else:
        full = _fill_derivs(coords, (i, j, k), derivs)
        if order is None:
            return full[1]
        else:
            return full

def dihed_vec(coords, i, j, k, l, order=None, method='expansion', fixed_atoms=None):
    """
    Returns the full vectors that define the linearized version of a dihedral displacement

    :param coords:
    :param i:
    :param j:
    :return:
    """
    derivs = dihed_deriv(coords, i, j, k, l, method=method, order=(1 if order is None else order), fixed_atoms=fixed_atoms)
    if method == 'expansion':
        return derivs[1] if order is None else derivs
    else:
        full = _fill_derivs(coords, (i, j, k, l), derivs)
        if order is None:
            return full[1]
        else:
            return full

def book_vec(coords, i, j, k, l, order=None, method='expansion', fixed_atoms=None):
    """
    Returns the full vectors that define the linearized version of a dihedral displacement

    :param coords:
    :param i:
    :param j:
    :return:
    """

    if method == 'expansion':
        derivs = book_deriv(coords, i, j, k, l, method=method, order=(1 if order is None else order), fixed_atoms=fixed_atoms)
        return derivs[1] if order is None else derivs
    else:
        derivs = dihed_deriv(coords, j, k, i, l, order=(1 if order is None else order), method=method,
                             fixed_atoms=fixed_atoms)
        full = _fill_derivs(coords, (i, j, k, l), derivs)
        if order is None:
            return full[1]
        else:
            return full

def oop_vec(coords, i, j, k, order=None, method='expansion', fixed_atoms=None):
    """
    Returns the full vectors that define the linearized version of an oop displacement

    :param coords:
    :param i:
    :param j:
    :return:
    """

    if method == 'expansion':
        derivs = oop_deriv(coords, i, j, k, order=(1 if order is None else order), method=method, fixed_atoms=fixed_atoms)
        return derivs[1] if order is None else derivs
    else:
        dihed_tf = dihed_deriv(coords, i, k, j, i, order=(1 if order is None else order), method=method,
                               fixed_atoms=fixed_atoms,
                               expanded_vectors=[0]
                               )
        full = _fill_derivs(coords, (i, j, k, None), dihed_tf)
        if order is None:
            return full[1]
        else:
            return full
        # if order is not None and order > 1:
        #     raise NotImplementedError("OOP deriv reshaping not done yet")
        # else:
        #     dihed_tf = dihed_tf[1]
        # dihed_vectors = np.zeros(coords.shape)
        # dihed_vectors[..., i, :] = dihed_tf[0]
        # dihed_vectors[..., j, :] = dihed_tf[1]
        # dihed_vectors[..., k, :] = dihed_tf[2]
        #
        # return dihed_vectors.reshape(
        #     coords.shape[:-2] + (coords.shape[-2] * coords.shape[-1],)
        # )

def wag_vec(coords, i, j, k, order=None, method='expansion', fixed_atoms=None):
    """
    Returns the full vectors that define the linearized version of an oop displacement

    :param coords:
    :param i:
    :param j:
    :return:
    """

    if method == 'expansion':
        derivs = wag_deriv(coords, i, j, k, order=(1 if order is None else order), method=method, fixed_atoms=fixed_atoms)
        return derivs[1] if order is None else derivs
    else:
        raise NotImplementedError("too annoying")

coord_type_map = {
    'dist':dist_vec,
    'bend':angle_vec,
    'rock':rock_vec,
    'dihed':dihed_vec,
    'book':book_vec,
    'oop':oop_vec,
    'wag':wag_vec
}
def internal_conversion_specs(specs, angle_ordering='ijk', coord_type_dispatch=None, **opts):
    if coord_type_dispatch is None:
        coord_type_dispatch = coord_type_map
    targets = []
    for idx in specs:
        if isinstance(idx, dict):
            for k in coord_type_dispatch.keys():
                if k in idx:
                    coord_type = k
                    subopts = idx.copy()
                    idx = idx[k]
                    del subopts[k]
                    break
            else:
                raise ValueError("can't parse coordinate spec {}".format(idx))
        else:
            nidx = len(idx)
            if nidx == 2:
                coord_type = 'dist'
            elif nidx == 3:
                coord_type = 'bend'
            elif nidx == 4:
                coord_type = 'dihed'
            else:
                raise ValueError("can't parse coordinate spec {}".format(idx))
            subopts = {}

        if coord_type in {'bend', 'rock'}: # very common to change
            subopts['angle_ordering'] = subopts.get('angle_ordering', angle_ordering)
        targets.append((coord_type_dispatch[coord_type], idx, dict(opts, **subopts)))

    return targets

def internal_conversion_function(specs,
                                 base_transformation=None,
                                 reference_internals=None,
                                 **opts):
    base_specs = internal_conversion_specs(specs, **opts)
    def convert(coords, order=None, reference_internals=reference_internals, base_transformation=base_transformation):
        targets = []
        for f, idx, subopts in base_specs:
            targets.append(f(coords, *idx, **dict(subopts, order=order)))

        if order is None:
            base = np.moveaxis(np.array(targets), 0, -1)
            if base_transformation is not None:
                base = td.tensor_reexpand(base, base_transformation) # del_XR * del_RQ
        else:
            base = [
                np.moveaxis(np.array(t), 0, -1)
                for t in zip(*targets)
            ]
            internals, expansion = base[0], base[1:]
            if reference_internals is not None:
                if reference_internals.ndim == 1 and internals.ndim > 1:
                    reference_internals = np.expand_dims(reference_internals, list(range(internals.ndim - 1)))
                internals = internals - reference_internals
            if base_transformation is not None:
                if base_transformation[0].ndim == 2 and len(expansion) > 0 and expansion[0].ndim > 2:
                    base_transformation = [
                        np.broadcast_to(
                            np.expand_dims(b, list(range(expansion[0].ndim - 2))),
                            expansion[0].shape[:-2] + b.shape
                        ) for b in base_transformation
                    ]
                internals = (internals[..., np.newaxis, :] @ base_transformation[0]).reshape(
                    internals.shape[:-1] + base_transformation[0].shape[-1:]
                )
                expansion = (
                    td.tensor_reexpand(expansion, base_transformation, order=len(expansion))
                        if len(expansion) > 0 else
                    expansion
                )
            base = [internals] + expansion
        return base
    return convert


def internal_coordinate_tensors(coords, specs, order=None, return_inverse=False, masses=None, **opts):
    base_tensors = internal_conversion_function(specs, **opts)(
        coords,
        order=order
    )
    if return_inverse:
        if order is None:
            bt = [base_tensors]
        else:
            bt = base_tensors[1:]
        return base_tensors, inverse_internal_coordinate_tensors(bt, coords, masses=masses, order=order)
    else:
        return base_tensors

def inverse_internal_coordinate_tensors(expansion,
                                        coords=None, masses=None, order=None,
                                        mass_weighted=True,
                                        remove_translation_rotation=True,
                                        fixed_atoms=None,
                                        fixed_coords=None
                                        ):
    from .CoordinateFrames import translation_rotation_invariant_transformation

    if order is None:
        order = len(expansion)

    if fixed_atoms is not None:
        atom_pos = np.reshape(
            (np.array(fixed_atoms) * 3)[:, np.newaxis]
            + np.arange(3)[np.newaxis],
            -1
        )
        expansion = [e.copy() for e in expansion]
        for n, e in enumerate(expansion):
            idx = (...,) + np.ix_(*[atom_pos] * (n + 1)) + (slice(None),)
            e[idx] = 0
    if fixed_coords is not None:
        expansion = [e.copy() for e in expansion]
        for n, e in enumerate(expansion):
            e[..., fixed_coords] = 0

    if coords is not None and remove_translation_rotation:
        # expansion = remove_translation_rotations(expansion, coords[opt_inds], masses)
        L_base, L_inv = translation_rotation_invariant_transformation(coords, masses,
                                                                    mass_weighted=False, strip_embedding=True)
        new_tf = td.tensor_reexpand([L_inv], expansion, order)
        inverse_tf = td.inverse_transformation(new_tf, order, allow_pseudoinverse=True)
        inverse_expansion = [
            vec_tensordot(j, np.moveaxis(L_inv, -1, -2), axes=[-1, -1], shared=L_base.ndim - 2)
                if not misc.is_numeric(j) else
            j
            for j in inverse_tf
        ]
    elif mass_weighted and masses is not None:
        sqrt_mass = np.expand_dims(
            np.repeat(
                np.diag(np.repeat(1 / np.sqrt(masses), 3)),
                coords.shape[0],
                axis=0
            ),
            list(range(expansion[0].ndim - 2))
        )
        expansion = td.tensor_reexpand([sqrt_mass], expansion, len(expansion))
        inverse_expansion = td.inverse_transformation(expansion, order=order, allow_pseudoinverse=True)
        inverse_expansion = td.tensor_reexpand(inverse_expansion, [sqrt_mass], order)
    else:
        inverse_expansion = td.inverse_transformation(expansion, order=order, allow_pseudoinverse=True)

    if fixed_atoms is not None:
        atom_pos = np.reshape(
            (np.array(fixed_atoms) * 3)[:, np.newaxis]
            + np.arange(3)[np.newaxis],
            -1
        )
        for n, e in enumerate(inverse_expansion):
            e[..., atom_pos] = 0
    if fixed_coords is not None:
        for n, e in enumerate(inverse_expansion):
            idx = (...,) + np.ix_(*[fixed_coords] * (n + 1)) + (slice(None),)
            e[idx] = 0

    return inverse_expansion

class _inverse_coordinate_conversion_caller:
    def __init__(self, conversion, target_internals,
                 remove_translation_rotation=True,
                 masses=None,
                 order=1,
                 gradient_function=None,
                 gradient_scaling=None,
                 fixed_atoms=None,
                 fixed_coords=None
                 ):
        self.conversion = conversion
        self.target_internals = target_internals
        self.masses = masses
        self.remove_translation_rotation = remove_translation_rotation
        self.gradient_function = gradient_function
        self.gradient_scaling = gradient_scaling
        self.last_call = None
        self.caller_order = order
        self.fixed_atoms = fixed_atoms
        self.fixed_coords = fixed_coords

    def func(self, coords, mask):
        coords = coords.reshape(coords.shape[0], -1, 3)
        internals = self.conversion(coords, order=0)[0]
        delta = internals - self.target_internals[mask]
        return np.sum(delta, axis=1)

    def jacobian(self, coords, mask):
        ord = self.caller_order
        coords = coords.reshape(coords.shape[0], -1, 3)
        expansion = self.last_call = self.conversion(coords, order=ord)
        internals, expansion = expansion[0], expansion[1:] # dr/dx
        delta = internals - self.target_internals[mask]
        fixed_coords = self.fixed_coords

        if self.fixed_atoms is not None:
            atom_pos = np.reshape(
                (np.array(self.fixed_atoms) * 3)[:, np.newaxis]
                + np.arange(3)[np.newaxis],
                -1
            )
            for n,e in enumerate(expansion):
                idx = (...,) + np.ix_(*[atom_pos] * (n + 1)) + (slice(None),)
                e[idx] = 0
        if fixed_coords is not None:
            for n,e in enumerate(expansion):
                e[..., fixed_coords] = 0

        if self.remove_translation_rotation: # dx/dr
            inverse_expansion = inverse_internal_coordinate_tensors(expansion, coords, self.masses, ord)
        else:
            sqrt_mass = np.expand_dims(
                np.repeat(
                    np.diag(np.repeat(1 / np.sqrt(self.masses), 3)),
                    coords.shape[0],
                    axis=0
                ),
                list(range(expansion[0].ndim - 2))
            )
            expansion = td.tensor_reexpand([sqrt_mass], expansion, len(expansion))
            inverse_expansion = td.inverse_transformation(expansion, order=ord, allow_pseudoinverse=True)
            inverse_expansion = td.tensor_reexpand(inverse_expansion, [sqrt_mass], ord)

        if self.fixed_atoms is not None:
            atom_pos = np.reshape(
                    (np.array(self.fixed_atoms) * 3)[:, np.newaxis]
                    + np.arange(3)[np.newaxis],
                -1
            )
            for n,e in enumerate(inverse_expansion):
                e[..., atom_pos] = 0
        if fixed_coords is not None:
            delta[..., fixed_coords] = 0
            for n,e in enumerate(inverse_expansion):
                idx = (...,) + np.ix_(*[fixed_coords]*(n+1)) + (slice(None),)
                e[idx] = 0

        nr_change = 0
        for n, e in enumerate(inverse_expansion):
            for ax in range(n + 1):
                e = vec_tensordot(e, delta, axes=[1, -1], shared=1)
            nr_change += (1 / math.factorial(n + 1)) * e

        if self.gradient_function is not None:
            if self.fixed_atoms is not None:
                subcrd = np.delete(coords, self.fixed_atoms, axis=-2).reshape(coords.shape[0], -1)
                subgrad = self.gradient_function(subcrd, mask)
                contrib = np.zeros((coords.shape[0], coords.shape[1]*coords.shape[2]), dtype=subgrad.dtype)
                atom_pos = np.reshape(
                    (np.array(self.fixed_atoms) * 3)[:, np.newaxis]
                    + np.arange(3)[np.newaxis],
                    -1
                )
                rem_pos = np.delete(np.arange(contrib.shape[1]), atom_pos)
                contrib[..., rem_pos] = subgrad
            else:
                contrib = self.gradient_function(coords.reshape(coords.shape[0], -1), mask)
            extra_gradient = -self.gradient_scaling * contrib
            nr_change = nr_change + extra_gradient

        return nr_change

DEFAULT_SOLVER_ORDER = 1
def inverse_coordinate_solve(specs, target_internals, initial_cartesians,
                             masses=None,
                             remove_translation_rotation=True,
                             order=None,
                             solver_order=None,
                             tol=1e-3, max_iterations=15,
                             max_displacement=.5,
                             gradient_function=None,
                             gradient_scaling=.1,
                             # method='quasi-newton',
                             method='gradient-descent',
                             optimizer_parameters=None,
                             line_search=False,
                             damping_parameter=None,
                             damping_exponent=None,
                             restart_interval=None,
                             raise_on_failure=False,
                             return_internals=True,
                             return_expansions=True,
                             base_transformation=None,
                             reference_internals=None,
                             fixed_atoms=None,
                             fixed_coords=None,
                             angle_ordering='ijk'):
    from . import Optimization as opt

    if method == 'quasi-newton':
        if optimizer_parameters is None: optimizer_parameters = {}
        optimizer_parameters['initial_beta'] = optimizer_parameters.get('initial_beta', 70)

    if order is None:
        order = DEFAULT_SOLVER_ORDER
    if solver_order is None:
        solver_order = order
    if not misc.is_numeric(solver_order):
        solver_order = max(solver_order)

    if callable(specs):
        conversion = specs
    else:
        conversion = internal_conversion_function(specs,
                                                  angle_ordering=angle_ordering,
                                                  base_transformation=base_transformation,
                                                  reference_internals=reference_internals
                                                  )
    target_internals = np.asanyarray(target_internals)
    initial_cartesians = np.asanyarray(initial_cartesians)

    base_shape = target_internals.shape[:-1]
    smol = len(base_shape) == 0
    if smol:
        target_internals = target_internals[np.newaxis]
        initial_cartesians = initial_cartesians[np.newaxis]
        base_shape = (1,)
    if initial_cartesians.ndim == 2:
        coords = np.expand_dims(initial_cartesians, list(range(len(base_shape))))
        coords = np.broadcast_to(coords, base_shape + coords.shape[-2:]).copy()
    else:
        coords = initial_cartesians.copy()
    coords = coords.reshape((-1,) + coords.shape[-2:])
    init_coords = coords
    target_internals = target_internals.reshape((-1,) + target_internals.shape[-1:])

    caller = _inverse_coordinate_conversion_caller(
        conversion,
        target_internals,
        remove_translation_rotation=remove_translation_rotation,
        masses=masses,
        gradient_function=gradient_function,
        gradient_scaling=gradient_scaling,
        fixed_atoms=fixed_atoms,
        fixed_coords=fixed_coords
    )

    coords, converged, (errors, its) = opt.iterative_step_minimize(
        coords.reshape(coords.shape[:1] + (-1,)),
        opt.get_step_finder(
            caller.func,
            method=method,
            jacobian=caller.jacobian,
            damping_parameter=damping_parameter,
            damping_exponent=damping_exponent,
            restart_interval=restart_interval,
            line_search=line_search,
            **({} if optimizer_parameters is None else optimizer_parameters)
        ),
        tol=tol,
        max_displacement=max_displacement,
        max_iterations=max_iterations,
        prevent_oscillations=True
        # termination_function=caller.terminate
    )

    coords = coords.reshape(coords.shape[:1] + (-1, 3))
    opt_internals = conversion(
        coords,
        order=0 if not return_expansions else order
    )
    if not converged:
        init_internals = conversion(
            init_coords,
            order=0 if not return_expansions else order
        )[0]
        if raise_on_failure:
            raise ValueError(
                f"failed to find coordinates after {max_iterations} iterations"
                f"\ntarget:{target_internals}\ninitial:{init_internals}"
                f"\nresidual:{target_internals - opt_internals[0]}"
                f"\n1-norm error: {errors}"
                f"\n1-norm error: {errors}"
                f"\nmax deviation error: {np.max(abs(target_internals - opt_internals[0]))}"
            )
        # else:
        #     print(
        #         f"failed to find coordinates after {max_iterations} iterations"
        #         f"\ntarget:{target_internals}\ninitial:{init_internals}"
        #         f"\nresidual:{target_internals - opt_internals[0]}"
        #         f"\n1-norm error: {errors}"
        #         f"\nmax deviation error: {np.max(abs(target_internals - opt_internals[0]))}"
        #     )
    if return_expansions:
        expansion = opt_internals[1:]
        if remove_translation_rotation:
            opt_expansions = inverse_internal_coordinate_tensors(expansion, coords, masses, order)
        else:
            opt_expansions = td.inverse_transformation(expansion, order=order, allow_pseudoinverse=True)
    else:
        opt_expansions = None

    coords = coords.reshape(base_shape + coords.shape[-2:])
    errors = errors.reshape(base_shape)
    if opt_expansions is not None:
        opt_expansions = [
            o.reshape(base_shape + o.shape[1:]) if isinstance(o, np.ndarray) else o
            for o in opt_expansions
        ]
    opt_internals = [o.reshape(base_shape + o.shape[1:]) for o in opt_internals]
    if smol:
        coords = coords[0]
        errors = errors[0]
        opt_internals = [o[0] for o in opt_internals]
        if opt_expansions is not None:
            opt_expansions = [
                o[0] if isinstance(o, np.ndarray) else o
                for o in opt_expansions
            ]


    if return_expansions:
        tf = [coords] + opt_expansions
    else:
        tf = coords
    if return_internals:
        return (tf, errors), opt_internals
    else:
        return tf, errors

def coordinate_projection_data(basis_mat, fixed_mat, inds, nonzero_cutoff=1e-8,
                               masses=None, coords=None,
                               project_transrot=False):
    from .CoordinateFrames import translation_rotation_projector

    if project_transrot and coords is not None:
        sub_projector, sub_tr_modes = translation_rotation_projector(
            coords[..., inds, :],
            masses=(
                [masses[i] for i in inds]
                    if masses is not None else
                masses
            ),
            mass_weighted=False,
            return_modes=True
        )
        cs = coords.shape[-1]
        ncoord = coords.shape[-2]*coords.shape[-1]
        projector = np.zeros(coords.shape[:-2] + (ncoord, ncoord))
        full_idx = sum(( tuple(i*3+j for j in range(cs)) for i in inds ), ())
        proj_sel = (...,) + np.ix_(full_idx, full_idx)
        projector[proj_sel] = sub_projector
        tr_modes = np.zeros(coords.shape[:-2] + (ncoord, sub_tr_modes.shape[-1]))
        tr_modes[..., full_idx, :] = sub_tr_modes
    else:
        projector, tr_modes = None, None
    if basis_mat is not None:
        if projector is not None:
            #TODO: handle broadcasting
            basis_mat = projector @ basis_mat
        nats = basis_mat.shape[-2] // 3
        basis_mat = find_basis(basis_mat, nonzero_cutoff=nonzero_cutoff)
        mat = np.zeros(basis_mat.shape[:-2] + (nats, 3, nats, 3))
    else:
        if projector is not None:
            #     #TODO: handle broadcasting
            #     fixed_mat = projector @ fixed_mat
            fixed_mat = np.concatenate([tr_modes, fixed_mat], axis=-1)
        nats = fixed_mat.shape[-2] // 3
        fixed_mat = find_basis(fixed_mat, nonzero_cutoff=nonzero_cutoff)
        mat = np.zeros(fixed_mat.shape[:-2] + (nats, 3, nats, 3))
    for x in range(3):
        for i in inds:
            mat[..., i, x, i, x] = 1
    mat = np.reshape(mat, mat.shape[:-4] + (nats*3, nats*3))

    if basis_mat is not None:
        return basis_mat, find_basis(mat - projection_matrix(basis_mat, orthonormal=True)), mat
    else:
        return find_basis(mat - projection_matrix(fixed_mat, orthonormal=True)), fixed_mat, mat

def dist_basis_mat(coords, i, j):
    coords = np.asanyarray(coords)
    mat = np.zeros(coords.shape + (3,))
    for x in range(3):
        mat[..., i, x, x] = 1
        mat[..., j, x, x] = -1

    mat = mat.reshape(mat.shape[:-3] + (-1, 3))
    return mat

def dist_basis(coords, i, j, **opts):
    basis_mat = dist_basis_mat(coords, i, j)
    return coordinate_projection_data(basis_mat, None, (i,j),
                                      coords=coords,
                                      **opts
                                      )

def fixed_angle_basis(coords, i, j, k):
    coords = np.asanyarray(coords)
    mat = np.zeros(coords.shape + (7,))
    for x in range(3):
        mat[..., i, x, x] = 1
        mat[..., j, x, x] = 1
        mat[..., k, x, x] = 1
    v1 = coords[..., i, :] - coords[..., j, :]
    mat[..., i, :, 3] = v1
    mat[..., j, :, 4] = -v1
    mat[..., k, :, 4] = -v1
    v2 = coords[..., k, :] - coords[..., j, :]
    mat[..., k, :, 5] = v2
    mat[..., j, :, 6] = -v2
    mat[..., i, :, 6] = -v2

    mat = mat.reshape(mat.shape[:-3] + (-1, 7))
    return mat

def angle_basis(coords, i, j, k, angle_ordering='ijk', **opts):
    if angle_ordering == 'jik':
        i,j,k = j,i,k
    fixed_mat = fixed_angle_basis(coords, i, j, k)
    return coordinate_projection_data(None, fixed_mat, (i,j,k),
                                      coords=coords,
                                      **opts
                                      )

def fixed_dihed_basis(coords, i, j, k, l):
    coords = np.asanyarray(coords)
    mat = np.zeros(coords.shape + (9,))
    for x in range(3):
        mat[..., i, x, x] = 1
        mat[..., j, x, x] = 1
        mat[..., k, x, x] = 1
        mat[..., l, x, x] = 1
    # basis for plane 1
    v1 = coords[..., i, :] - coords[..., j, :]
    v2 = coords[..., j, :] - coords[..., k, :]
    mat[..., i, :, 3] = v1
    mat[..., i, :, 4] = v2
    mat[..., j, :, 5] = v2
    # basis for plane 2
    v3 = coords[..., l, :] - coords[..., k, :]
    mat[..., l, :, 6] = v2
    mat[..., l, :, 7] = v3
    mat[..., k, :, 8] = v2

    mat = mat.reshape(mat.shape[:-3] + (-1, 9))
    return mat

def dihed_basis(coords, i, j, k, l, **opts):
    fixed_mat = fixed_dihed_basis(coords, i, j, k, l)
    return coordinate_projection_data(None, fixed_mat, (i,j,k,l),
                                      coords=coords,
                                      **opts
                                      )

basis_coord_type_map = {
    'dist':dist_basis,
    'bend':angle_basis,
    'dihed':dihed_basis,
}
def internal_basis_specs(specs, angle_ordering='ijk', **opts):
    return internal_conversion_specs(
        specs,
        angle_ordering=angle_ordering,
        coord_type_dispatch=basis_coord_type_map,
        **opts
    )
def internal_basis(coords, specs, **opts):
    base_specs = internal_basis_specs(specs, **opts)
    bases = []
    ortos = []
    subprojs = []
    for f, idx, subopts in base_specs:
        basis, orthog, subproj = f(coords, *idx, **subopts)
        bases.append(basis)
        ortos.append(orthog)
        subprojs.append(subproj)
    return bases, ortos, subprojs


def metric_tensor(internals_by_cartesians, masses=None):
    if misc.is_numeric_array_like(internals_by_cartesians):
        internals_by_cartesians = np.asanyarray(internals_by_cartesians)
        if internals_by_cartesians.ndim == 2:
            internals_by_cartesians = [internals_by_cartesians]
    transformation = np.asanyarray(internals_by_cartesians[0])
    if masses is not None:
        g12_base = np.diag(np.repeat(1/np.sqrt(masses), 3))
        transformation = np.moveaxis(
            np.tensordot(transformation, g12_base, axes=[-2, 0]),
            -1, -2
        )
    return np.moveaxis(transformation, -1, -2) @ transformation

def delocalized_internal_coordinate_transformation(
        internals_by_cartesians,
        untransformed_coordinates=None,
        masses=None,
        relocalize=False
):
    if misc.is_numeric_array_like(internals_by_cartesians):
        internals_by_cartesians = [internals_by_cartesians]
    conv = np.asanyarray(internals_by_cartesians[0])
    if masses is not None:
        g12_base = np.diag(np.repeat(1/np.sqrt(masses), 3))
        conv = np.moveaxis(
            np.tensordot(conv, g12_base, axes=[-2, 0]),
            -1, -2
        )

    if untransformed_coordinates is not None:
        transformed_coords = np.setdiff1d(np.arange(conv.shape[-1]), untransformed_coordinates)
        ut_conv = conv[..., untransformed_coordinates]
        conv = conv[..., transformed_coords]

        # project out contributions along untransformed coordinates to ensure
        # dimension of space remains unchanged
        ut_conv_norm = vec_normalize(np.moveaxis(ut_conv, -1, -2))
        proj = np.moveaxis(ut_conv_norm, -1, -2) @ ut_conv_norm
        proj = identity_tensors(proj.shape[:-2], proj.shape[-1]) - proj

        conv = np.concatenate([ut_conv, proj @ conv], axis=-1)

    G_internal = np.moveaxis(conv, -1, -2) @ conv
    redund_vals, redund_tf = np.linalg.eigh(G_internal)
    redund_pos = np.where(np.abs(redund_vals) > 1e-10)
    if redund_vals.ndim > 1:
        redund_tf = setops.take_where_groups(redund_tf, redund_pos)
    else:
        redund_tf = redund_tf[:, redund_pos[0]]
    if isinstance(redund_tf, np.ndarray):
        redund_tf = np.flip(redund_tf, axis=-1)
    else:
        redund_tf = [
            np.flip(tf, axis=-1)
            for tf in redund_tf
        ]

    if relocalize:
        if untransformed_coordinates is not None:
            perm = np.concatenate([untransformed_coordinates,
                                   np.delete(np.arange(redund_tf.shape[-2]), untransformed_coordinates)
                                   ])
            perm = np.argsort(perm)
            if isinstance(redund_tf, np.ndarray):
                redund_tf = redund_tf[..., perm, :]
            else:
                redund_tf = [
                    redund_tf[..., perm, :]
                    for tf in redund_tf
                ]


    return redund_tf

def relocalize_coordinate_transformation(redund_tf, untransformed_coordinates=None):
    n = redund_tf.shape[-1]
    if untransformed_coordinates is None:
        ndim = redund_tf.ndim - 2
        eye = identity_tensors(redund_tf.shape[:-2], n)
        target = np.pad(eye, ([[0, 0]] * ndim) + [[0, redund_tf.shape[-2] - n], [0, 0]])
    else:
        untransformed_coordinates = np.asanyarray(untransformed_coordinates)
        coords = np.concatenate([
            untransformed_coordinates,
            np.delete(np.arange(redund_tf.shape[-2]), untransformed_coordinates)
        ])[:n]
        target = np.moveaxis(np.zeros(redund_tf.shape), -1, -2)
        idx = setops.vector_ix(target.shape[:-1], coords[:, np.newaxis])
        target[idx] = 1
        target = np.moveaxis(target, -1, -2)
    loc = np.linalg.lstsq(redund_tf, target, rcond=None)
    U, s, V = np.linalg.svd(loc[0])
    R = U @ V
    return redund_tf @ R

def transform_cartesian_derivatives(
        derivs,
        tfs,
        axes=None
):
    if axes is None:
        axes = -1
    if misc.is_numeric(axes):
        axes = [-1, -2]
    derivs = [
        np.asanyarray(d) if not misc.is_numeric(d) else d
        for d in derivs
    ]

    tfs = np.asanyarray(tfs)
    d_ax, t_ax = axes
    if d_ax < 0:
        d_ax = derivs[0].ndim + d_ax
    if tfs.ndim > 2:
        shared = d_ax
    else:
        shared = None

    new_derivs = []
    for i,d in enumerate(derivs):
        if not misc.is_numeric(d):
            for j in range(i+1):
                d_shape = d.shape
                d = d.reshape(
                    d.shape[:d_ax+j] + (d.shape[d_ax+j]//3, 3) + d.shape[d_ax+j+1:]
                )
                if shared is not None:
                    d = vec_tensordot(d, tfs, axes=[d_ax+j+1, tfs], shared=shared)
                else:
                    d = np.tensordot(d, tfs, axes=[d_ax + j + 1, tfs])
                d = np.moveaxis(d, -1, d_ax + j + 1).reshape(d_shape)
            new_derivs.append(d)

    return new_derivs


def law_of_cosines_cos(a, b, c):
    return ((a**2 + b**2) - c**2) / (2*a*b)
def law_of_sines_sin(a, b, A):
    return np.sin(A) * b / a
def law_of_sines_dist(a, B, A):
    return a * np.sin(B) / np.sin(A)
def law_of_cosines_dist(a, b, C):
    return np.sqrt(a**2 + b**2 - 2*a*b*np.cos(C))
def tri_sss_area(a, b, c):
    s = (a + b + c) / 2
    tris = np.sqrt(s * (s - a) * (s - b) * (s - c))
    return tris
def tri_sas_area(a, C, b):
    return 1/2 * (a * b * np.sin(C))
def tri_sss_to_sas(a, b, c):
    C = np.arccos(law_of_cosines_cos(a, b, c))
    return (a, C, b)
def tri_sss_to_ssa(a, b, c):
    A = np.arccos(law_of_cosines_cos(b, c, a))
    return (a, b, A)
def tri_sss_to_saa(a, b, c):
    A = np.arccos(law_of_cosines_cos(b, c, a))
    B = np.arccos(law_of_cosines_cos(a, c, b))
    return (a, B, A)
def tri_sss_to_asa(a, b, c):
    B = np.arccos(law_of_cosines_cos(a, c, b))
    C = np.arccos(law_of_cosines_cos(a, b, c))
    return (C, a, B)
def tri_sas_to_sss(a, C, b):
    c = law_of_cosines_dist(a, b, C)
    return (a, b, c)
def tri_sas_to_ssa(a, C, b):
    return tri_sss_to_ssa(*tri_sas_to_sss(a,C,b))
def tri_sas_to_saa(a, C, b):
    return tri_sss_to_saa(*tri_sas_to_sss(a,C,b))
def tri_sas_to_asa(a, C, b):
    return tri_sss_to_asa(*tri_sas_to_sss(a,C,b))
def tri_ssa_to_sas(a, b, A):
    B = np.arcsin(law_of_sines_sin(a, b, A))
    C = np.pi - (A + B)
    return (a, C, b)
def tri_ssa_to_saa(a, b, A):
    B = np.arcsin(law_of_sines_sin(a, b, A))
    return (a, B, A)
def tri_ssa_to_asa(a, b, A):
    B = np.arcsin(law_of_sines_sin(a, b, A))
    C = np.pi - (A + B)
    return (C, a, B)
def tri_ssa_to_sss(a, b, A):
    return tri_sas_to_sss(*tri_ssa_to_sas(a, b, A))
def tri_saa_to_ssa(a, B, A):
    b = law_of_sines_dist(a, B, A)
    return (a, b, A)
def tri_saa_to_sas(a, B, A):
    b = law_of_sines_dist(a, B, A)
    C = np.pi - (A + B)
    return (a, C, b)
def tri_saa_to_asa(a, B, A):
    C = np.pi - (A + B)
    return (C, a, B)
def tri_saa_to_sss(a, B, A):
    return tri_sas_to_sss(*tri_saa_to_sas(a, B, A))
def tri_asa_to_saa(C, a, B):
    A = np.pi - (B + C)
    return (a, B, A)
def tri_asa_to_sas(C, a, B):
    A = np.pi - (B + C)
    b = law_of_sines_dist(a, B, A)
    return (a, C, b)
def tri_asa_to_ssa(C, a, B):
    A = np.pi - (B + C)
    b = law_of_sines_dist(a, B, A)
    return (a, b, A)
def tri_asa_to_sss(C, a, B):
    return tri_sas_to_sss(*tri_asa_to_sas(C, a, B))


def law_of_cosines_cos_deriv(a_expansion, b_expansion, c_expansion, order,
                             return_components=False,
                             a2_expansion=None,
                             b2_expansion=None,
                             c2_expansion=None,
                             abinv_expansion=None,
                             ab_expansion=None
                             ):
    if a2_expansion is None:
        a2_expansion = td.scalarprod_deriv(a_expansion, a_expansion, order)
    if b2_expansion is None:
        b2_expansion = td.scalarprod_deriv(b_expansion, b_expansion, order)
    if c2_expansion is None:
        c2_expansion = td.scalarprod_deriv(c_expansion, c_expansion, order)
    if abinv_expansion is None:
        if ab_expansion is None:
            ab_expansion = td.scalarprod_deriv(a_expansion, b_expansion, order)
        abinv_expansion = td.scalarinv_deriv(ab_expansion, order)
    term = td.scalarprod_deriv(
        (c2_expansion - (a2_expansion + b2_expansion)),
        abinv_expansion,
        order
    )
    if return_components:
        return term, (a2_expansion, b2_expansion, c2_expansion, abinv_expansion, ab_expansion)
    else:
        return term

def power_deriv(term, p, order):
    scaling = np.prod(p - np.arange(order))
    if scaling == 0:
        return np.zeros_like(term)
    else:
        return scaling * np.power(term, p - order)
def square_deriv(term, order):
    return power_deriv(term, 2, order)
def sqrt_deriv(term, order):
    return power_deriv(term, 1/2, order)
def cos_deriv(term, order):
    return np.cos(order*np.pi/2 + term)
def sin_deriv(term, order):
    return np.cos(order*np.pi/2 + term)
def legendre_scaling(n):
    if n > 1:
        rems, _ = integer_exponent(np.arange(1, n+1), 2)
        return np.prod(rems)
    else:
        return 1
def legendre_integer_coefficients(n):
    coeffs = np.zeros((n+1, n+1), dtype=int)
    coeffs[0, 0] = 1
    if n > 0:
        coeffs[1, 1] = 1
        if n > 1:
            ind_sets = np.arange(2, n+1)
            ind_sets = ind_sets - (ind_sets % 2)
            _, indicators = integer_exponent(ind_sets, 2)
            for i in range(n-2):
                m = (i+2)
                p1 = (2*m - 1) * np.roll(coeffs[i+1], 1)
                p2 = (m - 1) * coeffs[i]
                s2 = 2 ** indicators[i] # already shifted by a few bits
                s1 = s2 if i % 2 == 0 else 1
                coeffs[i+2] = (s1*p1 - s2*p2) // m
    return coeffs
def arcsin_deriv(term, order):
    #TODO: cache these
    coeffs = np.abs(legendre_integer_coefficients(order))
    scaling = legendre_scaling(order)
    sec_exp = np.cos(term)**(-(order+1))
    tan_exp = np.tan(term)**np.arange(order+1)
    return scaling*sec_exp*np.dot(tan_exp, coeffs[-1])
def arccos_deriv(term, order):
    #TODO: cache these
    coeffs = np.abs(legendre_integer_coefficients(order))
    scaling = legendre_scaling(order)
    s = np.sin(term)
    c = np.cos(term)
    csc_exp = np.sin(term)**(-(order+1))
    cot_exp = (c/s)**np.arange(order+1)
    return scaling*csc_exp*np.dot(cot_exp, coeffs[-1])
def law_of_cosines_dist_deriv(a_expansion, b_expansion, C_expansion, order,
                              return_components=False,
                              a2_expansion=None,
                              b2_expansion=None,
                              abcosC_expansion=None,
                              ab_expansion=None,
                              cosC_expansion=None,
                              return_square=False
                              ):
    if a2_expansion is None:
        a2_expansion = td.scalarfunc_deriv(square_deriv, a_expansion, order)
    if b2_expansion is None:
        b2_expansion = td.scalarfunc_deriv(square_deriv, b_expansion, order)
    if abcosC_expansion is None:
        if ab_expansion is None:
            ab_expansion = td.scalarprod_deriv(a_expansion, b_expansion, order)
        if cosC_expansion is None:
            cosC_expansion = td.scalarfunc_deriv(cos_deriv, C_expansion, order)
        abcosC_expansion = td.scalarprod_deriv(ab_expansion, cosC_expansion, order)
    term = [a+b-2*c for a,b,c in zip(a2_expansion, b2_expansion, abcosC_expansion)]
    if not return_square:
        term = td.scalarfunc_deriv(sqrt_deriv, term, order)
    if return_components:
        return term, (a2_expansion, b2_expansion, abcosC_expansion, ab_expansion, abcosC_expansion, cosC_expansion)
    else:
        return term

def law_of_sines_sin_deriv(a_expansion, b_expansion, A_expansion, order,
                           return_components=False,
                           sinA_expansion=None,
                           binva_expansion=None,
                           ainv_expansion=None
                           ):
    if binva_expansion is None:
        if ainv_expansion is None:
            ainv_expansion = td.scalarinv_deriv(a_expansion, order)
        binva_expansion = td.scalarprod_deriv(b_expansion, ainv_expansion, order)
    if sinA_expansion is None:
        sinA_expansion = td.scalarfunc_deriv(sin_deriv, A_expansion, order)
    term = td.scalarprod_deriv(sinA_expansion, binva_expansion, order)

    if return_components:
        return term, (sinA_expansion, binva_expansion, ainv_expansion)
    else:
        return term
def law_of_sines_dist_deriv(a_expansion, B_expansion, A_expansion, order,
                              return_components=False,
                              sinBinvsinA_expansion=None,
                              sinA_expansion=None,
                              sinB_expansion=None,
                              sinAinv_expansion=None
                              ):
    if sinBinvsinA_expansion is None:
        if sinB_expansion is None:
            sinB_expansion = td.scalarfunc_deriv(sin_deriv, B_expansion, order)
        if sinAinv_expansion is None:
            if sinA_expansion is None:
                sinA_expansion = td.scalarfunc_deriv(sin_deriv, A_expansion, order)
            sinAinv_expansion = td.scalarinv_deriv(sinAinv_expansion, order)
        sinBinvsinA_expansion = td.scalarprod_deriv(sinB_expansion, sinAinv_expansion, order)
    term = td.scalarprod_deriv(a_expansion, sinBinvsinA_expansion, order)

    if return_components:
        return term, (sinBinvsinA_expansion, sinA_expansion, sinB_expansion, sinAinv_expansion)
    else:
        return term

def _angle_complement_expansion(A_expansion, B_expansion):
    return td.shift_expansion(
        td.scale_expansion(td.add_expansions(A_expansion, B_expansion), -1),
        np.pi
    )

def tri_sss_to_sas_deriv(a_expansion, b_expansion, c_expansion, order,
                         return_components=False,
                         return_cos=False,
                         a2_expansion=None,
                         b2_expansion=None,
                         c2_expansion=None,
                         abinv_expansion=None,
                         ab_expansion=None,
                         cosC_expansion=None
                         ):
    if cosC_expansion is None:
        cosC_expansion, (a2_expansion, b2_expansion, c2_expansion, abinv_expansion, ab_expansion) = law_of_cosines_cos_deriv(
            a_expansion, b_expansion, c_expansion, order,
            return_components=True,
            a2_expansion=a2_expansion,
            b2_expansion=b2_expansion,
            c2_expansion=c2_expansion,
            abinv_expansion=abinv_expansion,
            ab_expansion=ab_expansion
        )

    bits = (a2_expansion, b2_expansion, c2_expansion, abinv_expansion, ab_expansion, cosC_expansion)
    if not return_cos:
        C_expansion = td.scalarfunc_deriv(arccos_deriv, cosC_expansion, order)
    else:
        C_expansion = cosC_expansion

    if return_components:
        return (a_expansion, C_expansion, b_expansion), bits
    else:
        return (a_expansion, C_expansion, b_expansion)
def tri_sss_to_ssa_deriv(a_expansion, b_expansion, c_expansion, order,
                         return_components=False,
                         return_cos=False,
                         a2_expansion=None,
                         b2_expansion=None,
                         c2_expansion=None,
                         bcinv_expansion=None,
                         bc_expansion=None,
                         cosA_expansion=None
                         ):
    if cosA_expansion is None:
        cosA_expansion, bits = law_of_cosines_cos_deriv(
            b_expansion, c_expansion, a_expansion, order,
            return_components=True,
            a2_expansion=a2_expansion,
            b2_expansion=b2_expansion,
            c2_expansion=c2_expansion,
            abinv_expansion=bcinv_expansion,
            ab_expansion=bc_expansion
        )
    else:
        bits = (a2_expansion, b2_expansion, c2_expansion, bcinv_expansion, bc_expansion)
    bits = bits + (cosA_expansion,)
    if not return_cos:
        A_expansion = td.scalarfunc_deriv(arccos_deriv, cosA_expansion, order)
    else:
        A_expansion = cosA_expansion

    if return_components:
        return (a_expansion, b_expansion, A_expansion), bits
    else:
        return (a_expansion, b_expansion, A_expansion)
def tri_sss_to_saa_deriv(a_expansion, b_expansion, c_expansion, order,
                         return_components=False,
                         return_cos=False,
                         a2_expansion=None,
                         b2_expansion=None,
                         c2_expansion=None,
                         acinv_expansion=None,
                         ac_expansion=None,
                         bcinv_expansion=None,
                         bc_expansion=None,
                         cosA_expansion=None,
                         cosB_expansion=None
                         ):
    if cosA_expansion is None:
        cosA_expansion, (b2_expansion, c2_expansion, a2_expansion, bcinv_expansion, bc_expansion) = law_of_cosines_cos_deriv(
            b_expansion, c_expansion, a_expansion, order,
            return_components=True,
            a2_expansion=a2_expansion,
            b2_expansion=b2_expansion,
            c2_expansion=c2_expansion,
            abinv_expansion=bcinv_expansion,
            ab_expansion=bc_expansion
        )
    if cosB_expansion is None:
        cosB_expansion, (a2_expansion, c2_expansion, b2_expansion, acinv_expansion, ac_expansion) = law_of_cosines_cos_deriv(
            a_expansion, c_expansion, b_expansion, order,
            return_components=True,
            a2_expansion=a2_expansion,
            b2_expansion=b2_expansion,
            c2_expansion=c2_expansion,
            abinv_expansion=acinv_expansion,
            ab_expansion=ac_expansion
        )

    bits = (
        a2_expansion,
        b2_expansion,
        c2_expansion,
        acinv_expansion,
        ac_expansion,
        bcinv_expansion,
        bc_expansion,
        cosA_expansion,
        cosB_expansion
    )

    if not return_cos:
        A_expansion = td.scalarfunc_deriv(arccos_deriv, cosA_expansion, order)
        B_expansion = td.scalarfunc_deriv(arccos_deriv, cosB_expansion, order)
    else:
        A_expansion = cosA_expansion
        B_expansion = cosB_expansion

    if return_components:
        return (a_expansion, B_expansion, A_expansion), bits
    else:
        return(a_expansion, B_expansion, A_expansion)
def tri_sss_to_asa_deriv(a_expansion, b_expansion, c_expansion, order,
                         return_components=False,
                         return_cos=False,
                         a2_expansion=None,
                         b2_expansion=None,
                         c2_expansion=None,
                         abinv_expansion=None,
                         ab_expansion=None,
                         acinv_expansion=None,
                         ac_expansion=None,
                         cosB_expansion=None,
                         cosC_expansion=None
                         ):
    if cosB_expansion is None:
        cosB_expansion, (a2_expansion, c2_expansion, b2_expansion, acinv_expansion, ac_expansion) = law_of_cosines_cos_deriv(
            a_expansion, c_expansion, b_expansion, order,
            return_components=True,
            a2_expansion=a2_expansion,
            b2_expansion=b2_expansion,
            c2_expansion=c2_expansion,
            abinv_expansion=acinv_expansion,
            ab_expansion=ac_expansion
        )
    if cosC_expansion is None:
        cosC_expansion, (a2_expansion, b2_expansion, c2_expansion, acinv_expansion, ac_expansion) = law_of_cosines_cos_deriv(
            a_expansion, b_expansion, c_expansion, order,
            return_components=True,
            a2_expansion=a2_expansion,
            b2_expansion=b2_expansion,
            c2_expansion=c2_expansion,
            abinv_expansion=abinv_expansion,
            ab_expansion=ab_expansion
        )

    bits = (
        a2_expansion,
        b2_expansion,
        c2_expansion,
        abinv_expansion,
        ab_expansion,
        acinv_expansion,
        ac_expansion,
        cosB_expansion,
        cosC_expansion
    )

    if not return_cos:
        C_expansion = td.scalarfunc_deriv(arccos_deriv, cosC_expansion, order)
        B_expansion = td.scalarfunc_deriv(arccos_deriv, cosB_expansion, order)
    else:
        C_expansion = cosC_expansion
        B_expansion = cosB_expansion

    if return_components:
        return (C_expansion, a_expansion, B_expansion), bits
    else:
        return (C_expansion, a_expansion, B_expansion)
def tri_sas_to_sss_deriv(a_expansion, C_expansion, b_expansion, order,
                         return_components=False,
                         a2_expansion=None,
                         b2_expansion=None,
                         abcosC_expansion=None,
                         ab_expansion=None,
                         cosC_expansion=None,
                         return_square=False
                         ):
    c_expansion, bits = law_of_cosines_dist_deriv(a_expansion, b_expansion, C_expansion, order,
                                                  a2_expansion=a2_expansion,
                                                  b2_expansion=b2_expansion,
                                                  abcosC_expansion=abcosC_expansion,
                                                  ab_expansion=ab_expansion,
                                                  cosC_expansion=cosC_expansion,
                                                  return_components=True,
                                                  return_square=return_square)
    if return_components:
        return (a_expansion, b_expansion, c_expansion), bits
    else:
        return (a_expansion, b_expansion, c_expansion)
def tri_sas_to_ssa_deriv(a_expansion, b_expansion, C_expansion, order,
                         return_components=False,
                         return_cos=False,
                         a2_expansion=None,
                         b2_expansion=None,
                         c2_expansion=None,
                         abcosC_expansion=None,
                         ab_expansion=None,
                         cosC_expansion=None,
                         bcinv_expansion=None,
                         bc_expansion=None,
                         cosA_expansion=None,
                         ):
    (a_expansion, b_expansion, c_expansion), (
        a2_expansion,
        b2_expansion,
        abcosC_expansion,
        ab_expansion,
        cosC_expansion
    ) = tri_sas_to_sss_deriv(a_expansion, b_expansion, C_expansion, order,
                                                                   return_components=True,
                                                                   a2_expansion=a2_expansion,
                                                                   b2_expansion=b2_expansion,
                                                                   abcosC_expansion=abcosC_expansion,
                                                                   ab_expansion=ab_expansion,
                                                                   cosC_expansion=cosC_expansion
                                                                   )
    (a_expansion, b_expansion, A_expansion), (
        a2_expansion,
        b2_expansion,
        c2_expansion,
        bcinv_expansion,
        bc_expansion,
        cosA_expansion
    ) = tri_sss_to_ssa_deriv(a_expansion, b_expansion, c_expansion, order,
                             return_components=False,
                             return_cos=return_cos,
                             a2_expansion=a2_expansion,
                             b2_expansion=b2_expansion,
                             c2_expansion=c2_expansion,
                             bcinv_expansion=bcinv_expansion,
                             bc_expansion=bc_expansion,
                             cosA_expansion=cosA_expansion
                             )
    if return_components:
        return (a_expansion, b_expansion, A_expansion), (
            a2_expansion,
            b2_expansion,
            c2_expansion,
            abcosC_expansion,
            ab_expansion,
            cosC_expansion,
            bcinv_expansion,
            bc_expansion,
            cosA_expansion
        )
    else:
        return (a_expansion, b_expansion, A_expansion)
def tri_sas_to_saa_deriv(a_expansion, b_expansion, C_expansion, order,
                         return_components=False,
                         return_cos=False,
                         a2_expansion=None,
                         b2_expansion=None,
                         c2_expansion=None,
                         abcosC_expansion=None,
                         ab_expansion=None,
                         cosC_expansion=None,
                         acinv_expansion=None,
                         ac_expansion=None,
                         bcinv_expansion=None,
                         bc_expansion=None,
                         cosA_expansion=None,
                         cosB_expansion=None
                         ):
    (a_expansion, b_expansion, c_expansion), (
        a2_expansion,
        b2_expansion,
        abcosC_expansion,
        ab_expansion,
        cosC_expansion
    ) = tri_sas_to_sss_deriv(a_expansion, b_expansion, C_expansion, order,
                                                                   return_components=True,
                                                                   a2_expansion=a2_expansion,
                                                                   b2_expansion=b2_expansion,
                                                                   abcosC_expansion=abcosC_expansion,
                                                                   ab_expansion=ab_expansion,
                                                                   cosC_expansion=cosC_expansion
                                                                   )
    (a_expansion, B_expansion, A_expansion), (
        a2_expansion,
        b2_expansion,
        c2_expansion,
        acinv_expansion,
        ac_expansion,
        bcinv_expansion,
        bc_expansion,
        cosA_expansion,
        cosB_expansion
    ) = tri_sss_to_saa_deriv(a_expansion, b_expansion, c_expansion, order,
                             return_components=True,
                             return_cos=return_cos,
                             a2_expansion=a2_expansion,
                             b2_expansion=b2_expansion,
                             c2_expansion=c2_expansion,
                             acinv_expansion=acinv_expansion,
                             ac_expansion=ac_expansion,
                             bcinv_expansion=bcinv_expansion,
                             bc_expansion=bc_expansion,
                             cosA_expansion=cosA_expansion,
                             cosB_expansion=cosB_expansion
                             )
    if return_components:
        return (a_expansion, B_expansion, A_expansion), (
            a2_expansion,
            b2_expansion,
            c2_expansion,
            abcosC_expansion,
            ab_expansion,
            cosC_expansion,
            acinv_expansion,
            ac_expansion,
            bcinv_expansion,
            bc_expansion,
            cosA_expansion,
            cosB_expansion
        )
    else:
        return (a_expansion, B_expansion, A_expansion)
def tri_sas_to_asa_deriv(a_expansion, b_expansion, C_expansion, order,
                         return_components=False,
                         return_cos=False,
                         a2_expansion=None,
                         b2_expansion=None,
                         c2_expansion=None,
                         abcosC_expansion=None,
                         ab_expansion=None,
                         cosC_expansion=None,
                         abinv_expansion=None,
                         acinv_expansion=None,
                         ac_expansion=None,
                         cosB_expansion=None
                         ):
    (a_expansion, b_expansion, c_expansion), (
        a2_expansion,
        b2_expansion,
        abcosC_expansion,
        ab_expansion,
        cosC_expansion
    ) = tri_sas_to_sss_deriv(a_expansion, b_expansion, C_expansion, order,
                                                                   return_components=True,
                                                                   a2_expansion=a2_expansion,
                                                                   b2_expansion=b2_expansion,
                                                                   abcosC_expansion=abcosC_expansion,
                                                                   ab_expansion=ab_expansion,
                                                                   cosC_expansion=cosC_expansion
                                                                   )
    (C_expansion, a_expansion, B_expansion), (
        a2_expansion,
        b2_expansion,
        c2_expansion,
        abinv_expansion,
        ab_expansion,
        acinv_expansion,
        ac_expansion,
        cosB_expansion,
        cosC_expansion
    ) = tri_sss_to_asa_deriv(a_expansion, b_expansion, c_expansion, order,
                             return_components=True,
                             return_cos=return_cos,
                             a2_expansion=a2_expansion,
                             b2_expansion=b2_expansion,
                             c2_expansion=c2_expansion,
                             abinv_expansion=abinv_expansion,
                             ab_expansion=ab_expansion,
                             acinv_expansion=acinv_expansion,
                             ac_expansion=ac_expansion,
                             cosB_expansion=cosB_expansion,
                             cosC_expansion=cosC_expansion
                             )

    if return_components:
        return (C_expansion, a_expansion, B_expansion), (
            a2_expansion,
            b2_expansion,
            c2_expansion,
            abcosC_expansion,
            ab_expansion,
            cosC_expansion,
            abinv_expansion,
            acinv_expansion,
            ac_expansion,
            cosB_expansion
        )
    else:
        return (C_expansion, a_expansion, B_expansion)
def tri_ssa_to_sas_deriv(a_expansion, b_expansion, A_expansion, order,
                         return_components=False,
                         sinA_expansion=None,
                         binva_expansion=None,
                         ainv_expansion=None,
                         B_expansion=None,
                         sinB_expansion=None
                         ):
    if B_expansion is None:
        if sinB_expansion is None:
            sinB_expansion = law_of_sines_sin_deriv(a_expansion, b_expansion, A_expansion, order,
                                                    return_components=True,
                                                    sinA_expansion=sinA_expansion,
                                                    binva_expansion=binva_expansion,
                                                    ainv_expansion=ainv_expansion
                                                    )
        B_expansion = td.scalarfunc_deriv(arcsin_deriv, sinB_expansion, order)

    bits = (
        sinA_expansion,
        binva_expansion,
        ainv_expansion,
        B_expansion,
        sinB_expansion
    )

    C_expansion = _angle_complement_expansion(A_expansion, B_expansion)

    if return_components:
        return (a_expansion, C_expansion, b_expansion), bits
    else:
        return (a_expansion, C_expansion, b_expansion)
def tri_ssa_to_saa_deriv(a_expansion, b_expansion, A_expansion, order,
                         return_components=False,
                         sinA_expansion=None,
                         binva_expansion=None,
                         ainv_expansion=None,
                         B_expansion=None,
                         sinB_expansion=None
                         ):
    if B_expansion is None:
        if sinB_expansion is None:
            sinB_expansion = law_of_sines_sin_deriv(a_expansion, b_expansion, A_expansion, order,
                                                    return_components=True,
                                                    sinA_expansion=sinA_expansion,
                                                    binva_expansion=binva_expansion,
                                                    ainv_expansion=ainv_expansion
                                                    )
        B_expansion = td.scalarfunc_deriv(arcsin_deriv, sinB_expansion, order)

    bits = (
        sinA_expansion,
        binva_expansion,
        ainv_expansion,
        B_expansion,
        sinB_expansion
    )

    if return_components:
        return (a_expansion, B_expansion, A_expansion), bits
    else:
        return (a_expansion, B_expansion, A_expansion)
def tri_ssa_to_asa_deriv(a_expansion, b_expansion, A_expansion, order,
                         return_components=False,
                         sinA_expansion=None,
                         binva_expansion=None,
                         ainv_expansion=None,
                         B_expansion=None,
                         sinB_expansion=None
                         ):
    if B_expansion is None:
        if sinB_expansion is None:
            sinB_expansion = law_of_sines_sin_deriv(a_expansion, b_expansion, A_expansion, order,
                                                    return_components=True,
                                                    sinA_expansion=sinA_expansion,
                                                    binva_expansion=binva_expansion,
                                                    ainv_expansion=ainv_expansion
                                                    )
        B_expansion = td.scalarfunc_deriv(arcsin_deriv, sinB_expansion, order)

    bits = (
        sinA_expansion,
        binva_expansion,
        ainv_expansion,
        B_expansion,
        sinB_expansion
    )

    C_expansion = _angle_complement_expansion(A_expansion, B_expansion)

    if return_components:
        return (C_expansion, a_expansion, B_expansion), bits
    else:
        return (C_expansion, a_expansion, B_expansion)
def tri_ssa_to_sss_deriv(
        a_expansion, b_expansion, A_expansion, order,
        return_components=False,
        sinA_expansion=None,
        binva_expansion=None,
        ainv_expansion=None,
        B_expansion=None,
        sinB_expansion=None,
        a2_expansion=None,
        b2_expansion=None,
        abcosC_expansion=None,
        ab_expansion=None,
        cosC_expansion=None,
):
    (a_expansion, C_expansion, b_expansion), (
        sinA_expansion,
        binva_expansion,
        ainv_expansion,
        B_expansion,
        sinB_expansion
    ) = tri_ssa_to_sas_deriv(a_expansion, b_expansion, A_expansion, order,
                             return_components=True,
                             sinA_expansion=sinA_expansion,
                             binva_expansion=binva_expansion,
                             ainv_expansion=ainv_expansion,
                             B_expansion=B_expansion,
                             sinB_expansion=sinB_expansion
                             )

    (a_expansion, b_expansion, c_expansion), (
        a2_expansion,
        b2_expansion,
        abcosC_expansion,
        ab_expansion,
        cosC_expansion,
    ) = tri_sas_to_sss_deriv(a_expansion, C_expansion, b_expansion, order,
                             return_components=True,
                             a2_expansion=a2_expansion,
                             b2_expansion=b2_expansion,
                             abcosC_expansion=abcosC_expansion,
                             ab_expansion=ab_expansion,
                             cosC_expansion=cosC_expansion,
                             return_square=False
                             )
    if return_components:
        return (a_expansion, b_expansion, c_expansion), (
            sinA_expansion,
            binva_expansion,
            ainv_expansion,
            B_expansion,
            sinB_expansion,
            a2_expansion,
            b2_expansion,
            abcosC_expansion,
            ab_expansion,
            cosC_expansion
        )
    else:
        return (a_expansion, b_expansion, c_expansion)
def tri_saa_to_ssa_deriv(a_expansion, B_expansion, A_expansion, order,
                         return_components=False,
                         sinBinvsinA_expansion=None,
                         sinA_expansion=None,
                         sinB_expansion=None,
                         sinAinv_expansion=None):
    b_expansion, bits = law_of_sines_dist_deriv(a_expansion, B_expansion, A_expansion, order,
                                                return_components=True,
                                                sinBinvsinA_expansion=sinBinvsinA_expansion,
                                                sinA_expansion=sinA_expansion,
                                                sinB_expansion=sinB_expansion,
                                                sinAinv_expansion=sinAinv_expansion
                                                )
    if return_components:
        return (a_expansion, b_expansion, A_expansion), bits
    else:
        return (a_expansion, b_expansion, A_expansion)
def tri_saa_to_sas_deriv(a_expansion, B_expansion, A_expansion, order,
                         return_components=False,
                         sinBinvsinA_expansion=None,
                         sinA_expansion=None,
                         sinB_expansion=None,
                         sinAinv_expansion=None):
    b_expansion, bits = law_of_sines_dist_deriv(a_expansion, B_expansion, A_expansion, order,
                                                return_components=True,
                                                sinBinvsinA_expansion=sinBinvsinA_expansion,
                                                sinA_expansion=sinA_expansion,
                                                sinB_expansion=sinB_expansion,
                                                sinAinv_expansion=sinAinv_expansion
                                                )

    C_expansion = _angle_complement_expansion(A_expansion, B_expansion)

    if return_components:
        return (a_expansion, C_expansion, b_expansion), bits
    else:
        return (a_expansion, C_expansion, b_expansion)
def tri_saa_to_asa_deriv(a_expansion, B_expansion, A_expansion, order):
    C_expansion = _angle_complement_expansion(A_expansion, B_expansion)
    return (C_expansion, a_expansion, B_expansion)
def tri_saa_to_sss_deriv(a_expansion, B_expansion, A_expansion, order,
                         return_components=False,
                         sinBinvsinA_expansion=None,
                         sinA_expansion=None,
                         sinB_expansion=None,
                         sinAinv_expansion=None,
                         a2_expansion=None,
                         b2_expansion=None,
                         abcosC_expansion=None,
                         ab_expansion=None,
                         cosC_expansion=None,
                         return_square=False
                         ):
    (a_expansion, C_expansion, b_expansion), (
        sinBinvsinA_expansion,
        sinA_expansion,
        sinB_expansion,
        sinAinv_expansion
    ) = tri_saa_to_sas_deriv(a_expansion, B_expansion, A_expansion,
                             order,
                             return_components=True,
                             sinBinvsinA_expansion=sinBinvsinA_expansion,
                             sinA_expansion=sinA_expansion,
                             sinB_expansion=sinB_expansion,
                             sinAinv_expansion=sinAinv_expansion,
                             )
    (a_expansion, b_expansion, c_expansion), (
        a2_expansion,
        b2_expansion,
        abcosC_expansion,
        ab_expansion,
        cosC_expansion,
    ) = tri_sas_to_sss_deriv(
        a_expansion, C_expansion, b_expansion, order,
        return_components=True,
        a2_expansion=a2_expansion,
        b2_expansion=b2_expansion,
        abcosC_expansion=abcosC_expansion,
        ab_expansion=ab_expansion,
        cosC_expansion=cosC_expansion,
        return_square=return_square
    )

    if return_components:
        return (a_expansion, b_expansion, c_expansion), (
            sinBinvsinA_expansion,
            sinA_expansion,
            sinB_expansion,
            sinAinv_expansion,
            a2_expansion,
            b2_expansion,
            abcosC_expansion,
            ab_expansion,
            cosC_expansion
        )
    else:
        return (a_expansion, b_expansion, c_expansion)
def tri_asa_to_saa_deriv(C_expansion, a_expansion, B_expansion, order):
    A_expansion = _angle_complement_expansion(C_expansion, B_expansion)
    return (a_expansion, B_expansion, A_expansion)
def tri_asa_to_sas_deriv(C_expansion, a_expansion, B_expansion, order,
                         return_components=False,
                         A_expansion=None,
                         sinBinvsinA_expansion=None,
                         sinA_expansion=None,
                         sinB_expansion=None,
                         sinAinv_expansion=None
                         ):
    if A_expansion is None:  # TODO: skip this if other components are supplied
        A_expansion = _angle_complement_expansion(C_expansion, B_expansion)
    b_expansion, (
        sinBinvsinA_expansion,
        sinA_expansion,
        sinB_expansion,
        sinAinv_expansion
    ) = law_of_sines_dist_deriv(a_expansion, B_expansion, A_expansion, order,
                                                sinBinvsinA_expansion=sinBinvsinA_expansion,
                                                sinA_expansion=sinA_expansion,
                                                sinB_expansion=sinB_expansion,
                                                sinAinv_expansion=sinAinv_expansion,
                                                return_components=True
                                                )
    if return_components:
        return (a_expansion, C_expansion, b_expansion), (
            A_expansion,
            sinBinvsinA_expansion,
            sinA_expansion,
            sinB_expansion,
            sinAinv_expansion
        )
    else:
        return (a_expansion, C_expansion, b_expansion)
def tri_asa_to_ssa_deriv(C_expansion, a_expansion, B_expansion, order,
                         return_components=False,
                         A_expansion=None,
                         sinBinvsinA_expansion=None,
                         sinA_expansion=None,
                         sinB_expansion=None,
                         sinAinv_expansion=None
                         ):
    if A_expansion is None:  # TODO: skip this if other components are supplied
        A_expansion = _angle_complement_expansion(C_expansion, B_expansion)
    b_expansion, (
        sinBinvsinA_expansion,
        sinA_expansion,
        sinB_expansion,
        sinAinv_expansion
    ) = law_of_sines_dist_deriv(a_expansion, B_expansion, A_expansion, order,
                                sinBinvsinA_expansion=sinBinvsinA_expansion,
                                sinA_expansion=sinA_expansion,
                                sinB_expansion=sinB_expansion,
                                sinAinv_expansion=sinAinv_expansion,
                                return_components=True
                                )
    if return_components:
        return (a_expansion, b_expansion, A_expansion), (
            sinBinvsinA_expansion,
            sinA_expansion,
            sinB_expansion,
            sinAinv_expansion
        )
    else:
        return (a_expansion, b_expansion, A_expansion)
def tri_asa_to_sss_deriv(C_expansion, a_expansion, B_expansion, order,
                   return_components=False,
                   A_expansion=None,
                   sinBinvsinA_expansion=None,
                   sinA_expansion=None,
                   sinB_expansion=None,
                   sinAinv_expansion=None,
                   a2_expansion=None,
                   b2_expansion=None,
                   abcosC_expansion=None,
                   ab_expansion=None,
                   cosC_expansion=None,
                   return_square=False
                   ):
    (a_expansion, C_expansion, b_expansion), bits = tri_asa_to_sas_deriv(C_expansion, a_expansion, B_expansion, order,
                         return_components=True,
                         A_expansion=A_expansion,
                         sinBinvsinA_expansion=sinBinvsinA_expansion,
                         sinA_expansion=sinA_expansion,
                         sinB_expansion=sinB_expansion,
                         sinAinv_expansion=sinAinv_expansion
                         )
    (a_expansion, b_expansion, c_expansion), bits2 = tri_sas_to_sss_deriv(
        a_expansion, C_expansion, b_expansion, order,
        return_components=True,
        a2_expansion=a2_expansion,
        b2_expansion=b2_expansion,
        abcosC_expansion=abcosC_expansion,
        ab_expansion=ab_expansion,
        cosC_expansion=cosC_expansion,
        return_square=return_square
    )
    if return_components:
        return (a_expansion, b_expansion, c_expansion), bits + bits2
    else:
        return (a_expansion, b_expansion, c_expansion)

class TriangleType(enum.Enum):
    SSS = "sss"
    SAS = "sas"
    SSA = "ssa"
    SAA = "saa"
    ASA = "asa"
def _echo_tri_args(x, y, z):
    return (x, y, z)
def _echo_tri_deriv_args(x_expansion, y_expansion, z_expansion, order, return_components=False, **kwargs):
    if return_components:
        return (x_expansion, y_expansion, z_expansion), kwargs
    else:
        return (x_expansion, y_expansion, z_expansion)
def triangle_converter(type1:str|TriangleType, type2:str|TriangleType):
    # only 9 possible conversions, let's just write them down
    type1 = TriangleType(type1)
    type2 = TriangleType(type2)
    if type1 == TriangleType.SSS:
        if type2 == TriangleType.SSS:
            return (_echo_tri_args, _echo_tri_deriv_args)
        elif type2 == TriangleType.SAS:
            return (tri_sss_to_sas, tri_sss_to_sas_deriv)
        elif type2 == TriangleType.SSA:
            return (tri_sss_to_ssa, tri_sss_to_ssa_deriv)
        elif type2 == TriangleType.SAA:
            return (tri_sss_to_saa, tri_sss_to_saa_deriv)
        elif type2 == TriangleType.ASA:
            return (tri_sss_to_asa, tri_sss_to_asa_deriv)
    elif type1 == TriangleType.SAS:
        if type2 == TriangleType.SSS:
            return (tri_sas_to_sss, tri_sas_to_sss_deriv)
        elif type2 == TriangleType.SAS:
            return (_echo_tri_args, _echo_tri_deriv_args)
        elif type2 == TriangleType.SSA:
            return (tri_sas_to_ssa, tri_sas_to_ssa_deriv)
        elif type2 == TriangleType.SAA:
            return (tri_sas_to_saa, tri_sas_to_saa_deriv)
        elif type2 == TriangleType.ASA:
            return (tri_sas_to_saa, tri_sas_to_asa_deriv)
    elif type1 == TriangleType.SSA:
        if type2 == TriangleType.SSS:
            return (tri_ssa_to_sss, tri_ssa_to_sss_deriv)
        elif type2 == TriangleType.SAS:
            return (tri_ssa_to_sas, tri_ssa_to_sas_deriv)
        elif type2 == TriangleType.SSA:
            return (_echo_tri_args, _echo_tri_deriv_args)
        elif type2 == TriangleType.SAA:
            return (tri_ssa_to_saa, tri_ssa_to_saa_deriv)
        elif type2 == TriangleType.ASA:
            return (tri_ssa_to_asa, tri_ssa_to_asa_deriv)
    elif type1 == TriangleType.SAA:
        if type2 == TriangleType.SSS:
            return (tri_saa_to_sss, tri_saa_to_sss_deriv)
        elif type2 == TriangleType.SAS:
            return (tri_saa_to_sas, tri_saa_to_sas_deriv)
        elif type2 == TriangleType.SSA:
            return (tri_saa_to_ssa, tri_saa_to_ssa_deriv)
        elif type2 == TriangleType.SAA:
            return (_echo_tri_args, _echo_tri_deriv_args)
        elif type2 == TriangleType.ASA:
            return (tri_ssa_to_sss, tri_ssa_to_sss_deriv)
    elif type1 == TriangleType.ASA:
        if type2 == TriangleType.SSS:
            return (tri_asa_to_sss, tri_asa_to_sss_deriv)
        elif type2 == TriangleType.SAS:
            return (tri_asa_to_sas, tri_asa_to_sas_deriv)
        elif type2 == TriangleType.SSA:
            return (tri_asa_to_ssa, tri_asa_to_ssa_deriv)
        elif type2 == TriangleType.SAA:
            return (tri_asa_to_saa, tri_asa_to_saa_deriv)
        elif type2 == TriangleType.ASA:
            return (_echo_tri_args, _echo_tri_deriv_args)
    return None
def triangle_convert(tri_spec, type1:str|TriangleType, type2:str|TriangleType, order=None, **kwargs):
    converter, deriv_converter = triangle_converter(type1, type2)
    if converter is None:
        raise ValueError(f"can't convert from triangle type {type1} to triangle type {type2}")
    b1,b2,b3 = tri_spec
    if order is None:
        b1 = np.asanyarray(b1)
        b2 = np.asanyarray(b2)
        b3 = np.asanyarray(b3)
        return converter(b1, b2, b3)
    else:
        b1 = [np.asanyarray(b) for b in b1]
        b2 = [np.asanyarray(b) for b in b2]
        b3 = [np.asanyarray(b) for b in b3]
        return deriv_converter(b1, b2, b3, order, **kwargs)
def triangle_area(tri_spec, type:str|TriangleType):
    type = TriangleType(type)
    b1,b2,b3 = tri_spec
    b1 = np.asanyarray(b1)
    b2 = np.asanyarray(b2)
    b3 = np.asanyarray(b3)
    if type == TriangleType.SSS:
        return tri_sss_area(b1, b2, b3)
    elif type == TriangleType.SAS:
        return tri_sas_area(b1, b2, b3)
    else:
        return tri_sas_area(*triangle_convert(tri_spec, type, TriangleType.SAS))

def dihedral_sssaa_distance(a, b, c, alpha, beta, tau, use_cos=False):
    """
    a^2 + b^2 + c^2 - 2 (
        a b Cos[\[Alpha]] + b c Cos[\[Beta]]
        + a c (Cos[\[Tau]] Sin[\[Alpha]] Sin[\[Beta]] - Cos[\[Alpha]] Cos[\[Beta]])
       )
    """
    ca = np.cos(alpha)
    cb = np.cos(beta)
    sa = np.sin(alpha)
    sb = np.sin(beta)
    if use_cos:
        ct = tau
    else:
        ct = np.cos(tau)
    return np.sqrt(
        a**2+b**2+c**2
        - 2*(a*b*ca + b*c*cb + a*c*(ct*sa*sb-ca*cb))
    )

def dihedral_sssaa_distance_deriv(a_expansion, b_expansion, c_expansion,
                                  alpha_expansion, beta_expansion, tau_expansion,
                                  order,
                                  return_components=False,
                                  return_square=False,
                                  cos_alpha_expansion=None,
                                  cos_beta_expansion=None,
                                  sin_alpha_expansion=None,
                                  sin_beta_expansion=None,
                                  cos_tau_expansion=None,
                                  a2_expansion=None,
                                  b2_expansion=None,
                                  c2_expansion=None,
                                  ab_cos_alpha_expansion=None,
                                  ab_expansion=None,
                                  bc_cos_beta_expansion=None,
                                  bc_expansion=None,
                                  ac_expansion=None,
                                  cos_alpha_cos_beta_expansion=None,
                                  sin_alpha_sin_beta_expansion=None
                                  ):

    if ab_cos_alpha_expansion is None:
        if ab_expansion is None:
            ab_expansion = td.scalarprod_deriv(a_expansion, b_expansion, order)
        if cos_alpha_expansion is None:
            cos_alpha_expansion = td.scalarfunc_deriv(cos_deriv, alpha_expansion, order)
        ab_cos_alpha_expansion = td.scalarprod_deriv(
            ab_expansion,
            cos_alpha_expansion,
            order
        )

    if bc_cos_beta_expansion is None:
        if bc_expansion is None:
            bc_expansion = td.scalarprod_deriv(b_expansion, c_expansion, order)
        if cos_beta_expansion is None:
            cos_beta_expansion = td.scalarfunc_deriv(cos_deriv, beta_expansion, order)
        bc_cos_beta_expansion = td.scalarprod_deriv(
            bc_expansion,
            cos_beta_expansion,
            order
        )

    if cos_alpha_cos_beta_expansion is None:
        if cos_alpha_expansion is None:
            cos_alpha_expansion = td.scalarfunc_deriv(cos_deriv, alpha_expansion, order)
        if cos_beta_expansion is None:
            cos_beta_expansion = td.scalarfunc_deriv(cos_deriv, beta_expansion, order)
        cos_alpha_cos_beta_expansion = td.scalarprod_deriv(
            cos_alpha_expansion,
            cos_beta_expansion,
            order
        )

    if sin_alpha_sin_beta_expansion is None:
        if sin_alpha_expansion is None:
            sin_alpha_expansion = td.scalarfunc_deriv(sin_deriv, alpha_expansion, order)
        if sin_beta_expansion is None:
            sin_beta_expansion = td.scalarfunc_deriv(sin_deriv, beta_expansion, order)
        sin_alpha_sin_beta_expansion = td.scalarprod_deriv(
            sin_alpha_expansion,
            sin_beta_expansion,
            order
        )

    if cos_tau_expansion is None:
        cos_tau_expansion = td.scalarfunc_deriv(cos_deriv, tau_expansion, order)

    if a2_expansion is None:
        a2_expansion = td.scalarfunc_deriv(square_deriv, a_expansion, order)
    if b2_expansion is None:
        b2_expansion = td.scalarfunc_deriv(square_deriv, b_expansion, order)
    if c2_expansion is None:
        c2_expansion = td.scalarfunc_deriv(square_deriv, c_expansion, order)

    if ac_expansion is None:
        ac_expansion = td.scalarprod_deriv(a_expansion, c_expansion, order)
    extra_cos_term = td.scalarprod_deriv(
        ac_expansion,
        td.subtract_expansions(
            td.scalarprod_deriv(cos_tau_expansion, sin_alpha_sin_beta_expansion, order),
            cos_alpha_cos_beta_expansion
        ),
        order
    )

    r2_term = td.add_expansions(a2_expansion, b2_expansion, c2_expansion)
    radj_term = td.scale_expansion(
        td.add_expansions(
            ab_cos_alpha_expansion,
            bc_cos_beta_expansion,
            extra_cos_term
        ),
        2
    )

    # np.sqrt(
    #     a ** 2 + b ** 2 + c ** 2
    #     - 2 * (a * b * ca + b * c * cb + a * c * (ct * sa * sb - ca * cb))
    # )

    term = td.subtract_expansions(r2_term, radj_term)
    if not return_square:
        term = td.scalarfunc_deriv(sqrt_deriv, term, order)

    if return_components:
        return term, (
            cos_alpha_expansion,
            cos_beta_expansion,
            sin_alpha_expansion,
            sin_beta_expansion,
            cos_tau_expansion,
            a2_expansion,
            b2_expansion,
            c2_expansion,
            ab_cos_alpha_expansion,
            ab_expansion,
            bc_cos_beta_expansion,
            bc_expansion,
            ac_expansion,
            cos_alpha_cos_beta_expansion,
            sin_alpha_sin_beta_expansion
        )
    else:
        return term
def dihedral_ssssa_distance(a, b, c, x, beta, tau, use_cos=False):
    a2 = a**2
    b2 = b**2
    x2 = x**2
    ca = (a2+b2-x2)/(2*a*b)
    cb = np.cos(beta)
    sa = np.sqrt(1-ca**2)
    sb = np.sin(beta)
    if use_cos:
        ct = tau
    else:
        ct = np.cos(tau)
    return np.sqrt(
        x2+c**2 - 2*(b*c*cb + a*c*(ct*sa*sb-ca*cb))
    )
def _dist_cos_expansion(a2_expansion, b2_expansion, x2_expansion, ab_expansion, order):
    # (a2+b2-x2)/(2*a*b)
    return td.scale_expansion(
        td.scalarprod_deriv(
            td.subtract_expansions(td.add_expansions(a2_expansion, b2_expansion), x2_expansion),
            td.scalarinv_deriv(ab_expansion, order),
            order
        ),
        1 / 2
    )
def dihedral_ssssa_distance_deriv(a_expansion, b_expansion, c_expansion, x_expansion,
                                  beta_expansion, tau_expansion, order,
                                  return_components=False,
                                  return_square=False,
                                  cos_alpha_expansion=None,
                                  cos_beta_expansion=None,
                                  sin_alpha_expansion=None,
                                  sin_beta_expansion=None,
                                  cos_tau_expansion=None,
                                  a2_expansion=None,
                                  b2_expansion=None,
                                  c2_expansion=None,
                                  x2_expansion=None,
                                  ab_expansion=None,
                                  bc_cos_beta_expansion=None,
                                  bc_expansion=None,
                                  ac_expansion=None,
                                  cos_alpha_cos_beta_expansion=None,
                                  sin_alpha_sin_beta_expansion=None
                                  ):
    if a2_expansion is None:
        a2_expansion = td.scalarfunc_deriv(square_deriv, a_expansion, order)
    if b2_expansion is None:
        b2_expansion = td.scalarfunc_deriv(square_deriv, b_expansion, order)
    if c2_expansion is None:
        c2_expansion = td.scalarfunc_deriv(square_deriv, c_expansion, order)
    if x2_expansion is None:
        x2_expansion = td.scalarfunc_deriv(square_deriv, x_expansion, order)
    if cos_alpha_cos_beta_expansion is None:
        if cos_alpha_expansion is None:
            if ab_expansion is None:
                ab_expansion = td.scalarprod_deriv(a_expansion, b_expansion, order)
            cos_alpha_expansion = _dist_cos_expansion(a2_expansion, b2_expansion, x2_expansion, ab_expansion, order)
        if cos_beta_expansion is None:
            cos_beta_expansion = td.scalarfunc_deriv(cos_deriv, beta_expansion, order)
        cos_alpha_cos_beta_expansion = td.scalarprod_deriv(cos_alpha_expansion, cos_beta_expansion, order)
    if sin_alpha_sin_beta_expansion is None:
        if sin_alpha_expansion is None:
            ca2 = td.scalarfunc_deriv(square_deriv, cos_alpha_expansion, order)
            sin_alpha_expansion = td.scalarfunc_deriv(
                sqrt_deriv,
                td.shift_expansion(td.scale_expansion(ca2, -1), 1),
                order
            )
        if sin_beta_expansion is None:
            sin_beta_expansion = td.scalarfunc_deriv(sin_deriv, beta_expansion, order)
        sin_alpha_sin_beta_expansion = td.scalarprod_deriv(sin_alpha_expansion, sin_beta_expansion, order)
    if cos_tau_expansion is None:
        cos_tau_expansion = td.scalarfunc_deriv(cos_deriv, tau_expansion, order)

    if bc_cos_beta_expansion is None:
        if bc_expansion is None:
            bc_expansion = td.scalarprod_deriv(b_expansion, c_expansion, order)
        if cos_beta_expansion is None:
            cos_beta_expansion = td.scalarfunc_deriv(cos_deriv, beta_expansion, order)
        bc_cos_beta_expansion = td.scalarprod_deriv(bc_expansion, cos_beta_expansion, order)
    # x2+c**2 - 2*(b*c*cb + a*c*(ct*sa*sb-ca*cb))
    if ac_expansion is None:
        ac_expansion = td.scalarprod_deriv(a_expansion, c_expansion, order)
    extra_cos_term = td.scalarprod_deriv(
        ac_expansion,
        td.subtract_expansions(
            td.scalarprod_deriv(cos_tau_expansion, sin_alpha_sin_beta_expansion, order),
            cos_alpha_cos_beta_expansion
        ),
        order
    )
    r2_term = td.add_expansions(x2_expansion, c2_expansion)
    radj_term = td.scale_expansion(
        td.add_expansions(
            bc_cos_beta_expansion,
            extra_cos_term
        ),
        2
    )

    term = td.subtract_expansions(r2_term, radj_term)
    if not return_square:
        term = td.scalarfunc_deriv(sqrt_deriv, term, order)

    if return_components:
        return term, (
            cos_alpha_expansion,
            cos_beta_expansion,
            sin_alpha_expansion,
            sin_beta_expansion,
            cos_tau_expansion,
            a2_expansion,
            b2_expansion,
            c2_expansion,
            x2_expansion,
            ab_expansion,
            bc_cos_beta_expansion,
            bc_expansion,
            ac_expansion,
            cos_alpha_cos_beta_expansion,
            sin_alpha_sin_beta_expansion
        )
    else:
        return term
def dihedral_sssss_distance(a,b, c, x, y, tau, use_cos=False):
    # potentially more stable than just computing the sin and cos in the usual way...
    xp = (a+b)**2
    xm = (a-b)**2
    yp = (b+c)**2
    ym = (b-c)**2
    x2 = x**2
    y2 = y**2
    a2 = a**2
    b2 = b**2
    c2 = c**2
    if use_cos:
        ct = tau
    else:
        ct = np.cos(tau)
    return np.sqrt(
        x2+y2-b2
        + (
                (a2+b2-x2)*(b2+c2-y2)
                -np.sqrt((xm - x2)*(xp - x2)*(ym - y2)*(yp - y2))*ct
        )/(2*b2)
    )

def dihedral_sssss_distance_deriv(
        a_expansion, b_expansion, c_expansion, x_expansion, y_expansion, order,
        tau_expansion,
        return_components=False,
        return_square=False,
        a2_expansion=None,
        b2_expansion=None,
        c2_expansion=None,
        x2_expansion=None,
        y2_expansion=None,
        cos_tau_expansion=None,
        abplus_expansion=None,
        abminus_expansion=None,
        bcplus_expansion=None,
        bcminus_expansion=None,
        det_expansion=None,
):
    # potentially more stable than just computing the sin and cos in the usual way...
    if x2_expansion is None:
        x2_expansion = td.scalarpow_deriv(x_expansion, 2, order)
    if y2_expansion is None:
        y2_expansion = td.scalarpow_deriv(y_expansion, 2, order)
    if a2_expansion is None:
        a2_expansion = td.scalarpow_deriv(a_expansion, 2, order)
    if b2_expansion is None:
        b2_expansion = td.scalarpow_deriv(b_expansion, 2, order)
    if c2_expansion is None:
        c2_expansion = td.scalarpow_deriv(c_expansion, 2, order)
    if cos_tau_expansion is None:
        cos_tau_expansion = td.scalarfunc_deriv(cos_deriv, tau_expansion, order)

    if det_expansion is None:
        if abplus_expansion is None:
            abplus_expansion = td.scalarpow_deriv(td.add_expansions(a_expansion, b_expansion), 2, order)
        if abminus_expansion is None:
            abminus_expansion = td.scalarpow_deriv(td.subtract_expansions(a_expansion, b_expansion), 2, order)
        if bcplus_expansion is None:
            bcplus_expansion = td.scalarpow_deriv(td.add_expansions(b_expansion, c_expansion), 2, order)
        if bcminus_expansion is None:
            bcminus_expansion = td.scalarpow_deriv(td.subtract_expansions(b_expansion, c_expansion), 2, order)
        # np.sqrt((xm - x2)*(xp - x2)*(ym - y2)*(yp - y2))
        abp = td.subtract_expansions(abplus_expansion, x2_expansion)
        abm = td.subtract_expansions(abminus_expansion, x2_expansion)
        bcp = td.subtract_expansions(bcplus_expansion, y2_expansion)
        bcm = td.subtract_expansions(bcminus_expansion, y2_expansion)
        det_expansion = td.scalarfunc_deriv(sqrt_deriv,
                                            td.scalarprod_deriv(
                                                td.scalarprod_deriv(abm, abp, order),
                                                td.scalarprod_deriv(bcm, bcp, order),
                                                order
                                            ),
                                            order
                                            )
    det_cos_expansion = td.scalarprod_deriv(det_expansion, cos_tau_expansion, order)
    num_expansion = td.scalarprod_deriv(
        td.subtract_expansions(td.add_expansions(a2_expansion, b2_expansion), x2_expansion),
        td.subtract_expansions(td.add_expansions(b2_expansion, c2_expansion), y2_expansion),
        order
    )
    invb2_expansion = td.scale_expansion(td.scalarinv_deriv(b2_expansion, order), 1/2)
    r2_term = td.subtract_expansions(td.add_expansions(x2_expansion, y2_expansion), b2_expansion)

    term = td.add_expansions(
        r2_term,
        td.scalarprod_deriv(
            td.subtract_expansions(num_expansion, det_cos_expansion),
            invb2_expansion,
            order
        )
    )
    if not return_square:
        term = td.scalarfunc_deriv(sqrt_deriv, term, order)

    # x2+y2-b2
    #         + (
    #                 (a2+b2-x2)*(b2+c2-y2)
    #                 -np.sqrt((xm - x2)*(xp - x2)*(ym - y2)*(yp - y2))*ct
    #         )/(2*b2)

    if return_components:
        return term, (
            a2_expansion,
            b2_expansion,
            c2_expansion,
            x2_expansion,
            y2_expansion,
            cos_tau_expansion,
            abplus_expansion,
            abminus_expansion,
            bcplus_expansion,
            bcminus_expansion,
            det_expansion
        )
    else:
        return term
def dihedral_from_ssssaa(a, b, c, alpha, beta, r, use_cos=False):
    ca = np.cos(alpha)
    cb = np.cos(beta)
    sa = np.sin(alpha)
    sb = np.sin(beta)
    ct = ((a**2 + b**2 + c**2) - r**2 - 2*a*b*ca - 2*b*c*cb + 2*a*c*ca*cb) / (2*a*c*sa*sb)
    if use_cos:
        return ct
    else:
        return np.arccos(ct)
def dihedral_from_ssssaa_deriv(
        a_expansion, b_expansion, c_expansion,
        alpha_expansion, beta_expansion, r_expansion,
        order,
        return_components=False,
        return_cos=False,
        cos_alpha_expansion=None,
        cos_beta_expansion=None,
        sin_alpha_expansion=None,
        sin_beta_expansion=None,
        a2_expansion=None,
        b2_expansion=None,
        c2_expansion=None,
        r2_expansion=None,
        ab_cos_alpha_expansion=None,
        ab_expansion=None,
        bc_cos_beta_expansion=None,
        bc_expansion=None,
        ac_expansion=None,
        cos_alpha_cos_beta_expansion=None,
        sin_alpha_sin_beta_expansion=None
):
    if ab_cos_alpha_expansion is None:
        if ab_expansion is None:
            ab_expansion = td.scalarprod_deriv(a_expansion, b_expansion, order)
        if cos_alpha_expansion is None:
            cos_alpha_expansion = td.scalarfunc_deriv(cos_deriv, alpha_expansion, order)
        ab_cos_alpha_expansion = td.scalarprod_deriv(
            ab_expansion,
            cos_alpha_expansion,
            order
        )

    if bc_cos_beta_expansion is None:
        if bc_expansion is None:
            bc_expansion = td.scalarprod_deriv(b_expansion, c_expansion, order)
        if cos_beta_expansion is None:
            cos_beta_expansion = td.scalarfunc_deriv(cos_deriv, beta_expansion, order)
        bc_cos_beta_expansion = td.scalarprod_deriv(
            bc_expansion,
            cos_beta_expansion,
            order
        )

    if cos_alpha_cos_beta_expansion is None:
        if cos_alpha_expansion is None:
            cos_alpha_expansion = td.scalarfunc_deriv(cos_deriv, alpha_expansion, order)
        if cos_beta_expansion is None:
            cos_beta_expansion = td.scalarfunc_deriv(cos_deriv, beta_expansion, order)
        cos_alpha_cos_beta_expansion = td.scalarprod_deriv(
            cos_alpha_expansion,
            cos_beta_expansion,
            order
        )

    if sin_alpha_sin_beta_expansion is None:
        if sin_alpha_expansion is None:
            sin_alpha_expansion = td.scalarfunc_deriv(sin_deriv, alpha_expansion, order)
        if sin_beta_expansion is None:
            sin_beta_expansion = td.scalarfunc_deriv(sin_deriv, beta_expansion, order)
        sin_alpha_sin_beta_expansion = td.scalarprod_deriv(
            sin_alpha_expansion,
            sin_beta_expansion,
            order
        )

    if a2_expansion is None:
        a2_expansion = td.scalarfunc_deriv(square_deriv, a_expansion, order)
    if b2_expansion is None:
        b2_expansion = td.scalarfunc_deriv(square_deriv, b_expansion, order)
    if c2_expansion is None:
        c2_expansion = td.scalarfunc_deriv(square_deriv, c_expansion, order)
    if r2_expansion is None:
        r2_expansion = td.scalarfunc_deriv(square_deriv, r_expansion, order)

    if ac_expansion is None:
        ac_expansion = td.scalarprod_deriv(a_expansion, c_expansion, order)

    ac_cos_cos_expansion = td.scalarprod_deriv(ac_expansion, cos_alpha_cos_beta_expansion, order)
    ac_sin_sin_expansion = td.scalarprod_deriv(ac_expansion, sin_alpha_sin_beta_expansion, order)

    # ((a**2 + b**2 + c**2) - r**2 - 2*a*b*ca - 2*b*c*cb + 2*a*c*ca*cb)
    rd_expansion = td.subtract_expansions(
        td.add_expansions(a2_expansion, b2_expansion, c2_expansion),
        td.add_expansions(r2_expansion,
                          td.scale_expansion(
                              td.subtract_expansions(
                                  td.add_expansions(ab_cos_alpha_expansion, bc_cos_beta_expansion),
                                  ac_cos_cos_expansion
                              ),
                              2
                          )
                          )
    )
    ac_denom_expansion = td.scale_expansion(td.scalarinv_deriv(ac_sin_sin_expansion, order), 1 / 2 )
    term = td.scalarprod_deriv(
        rd_expansion,
        ac_denom_expansion
    )
    if not return_cos:
        term = td.scalarfunc_deriv(arccos_deriv, term, order)

    if return_components:
        return term, (
            cos_alpha_expansion,
            cos_beta_expansion,
            sin_alpha_expansion,
            sin_beta_expansion,
            a2_expansion,
            b2_expansion,
            c2_expansion,
            r2_expansion,
            ab_cos_alpha_expansion,
            ab_expansion,
            bc_cos_beta_expansion,
            bc_expansion,
            ac_expansion,
            cos_alpha_cos_beta_expansion,
            sin_alpha_sin_beta_expansion
        )
    else:
        return term

def dihedral_from_sssssa(a, b, c, x, beta, r, use_cos=False):
    a2 = a**2
    b2 = b**2
    x2 = x**2
    ca = (a2+b2-x2)/(2*a*b)
    cb = np.cos(beta)
    sa = np.sqrt(1-ca**2)
    sb = np.sin(beta)
    r2 = r**2
    ct = ((x2+c**2) - r2 - 2*b*c*cb + 2*a*c*ca*cb) / (2*a*c*sa*sb)
    if use_cos:
        return ct
    else:
        return np.arccos(ct)
def dihedral_from_sssssa_deriv(a_expansion, b_expansion, c_expansion, x_expansion,
                               beta_expansion, r_expansion, order,
                               return_components=False,
                               return_cos=False,
                               cos_alpha_expansion=None,
                               cos_beta_expansion=None,
                               sin_alpha_expansion=None,
                               sin_beta_expansion=None,
                               a2_expansion=None,
                               b2_expansion=None,
                               c2_expansion=None,
                               x2_expansion=None,
                               r2_expansion=None,
                               ab_expansion=None,
                               bc_cos_beta_expansion=None,
                               bc_expansion=None,
                               ac_expansion=None,
                               cos_alpha_cos_beta_expansion=None,
                               sin_alpha_sin_beta_expansion=None
                               ):
    if a2_expansion is None:
        a2_expansion = td.scalarfunc_deriv(square_deriv, a_expansion, order)
    if b2_expansion is None:
        b2_expansion = td.scalarfunc_deriv(square_deriv, b_expansion, order)
    if c2_expansion is None:
        c2_expansion = td.scalarfunc_deriv(square_deriv, c_expansion, order)
    if r2_expansion is None:
        r2_expansion = td.scalarfunc_deriv(square_deriv, r_expansion, order)
    if x2_expansion is None:
        x2_expansion = td.scalarfunc_deriv(square_deriv, x_expansion, order)
    if cos_alpha_cos_beta_expansion is None:
        if cos_alpha_expansion is None:
            if ab_expansion is None:
                ab_expansion = td.scalarprod_deriv(a_expansion, b_expansion, order)
            cos_alpha_expansion = _dist_cos_expansion(a2_expansion, b2_expansion, x2_expansion, ab_expansion, order)
        if cos_beta_expansion is None:
            cos_beta_expansion = td.scalarfunc_deriv(cos_deriv, beta_expansion, order)
        cos_alpha_cos_beta_expansion = td.scalarprod_deriv(cos_alpha_expansion, cos_beta_expansion, order)
    if sin_alpha_sin_beta_expansion is None:
        if sin_alpha_expansion is None:
            ca2 = td.scalarfunc_deriv(square_deriv, cos_alpha_expansion, order)
            sin_alpha_expansion = td.scalarfunc_deriv(
                sqrt_deriv,
                td.shift_expansion(td.scale_expansion(ca2, -1), 1),
                order
            )
        if sin_beta_expansion is None:
            sin_beta_expansion = td.scalarfunc_deriv(sin_deriv, beta_expansion, order)
        sin_alpha_sin_beta_expansion = td.scalarprod_deriv(sin_alpha_expansion, sin_beta_expansion, order)

    if bc_cos_beta_expansion is None:
        if bc_expansion is None:
            bc_expansion = td.scalarprod_deriv(b_expansion, c_expansion, order)
        if cos_beta_expansion is None:
            cos_beta_expansion = td.scalarfunc_deriv(cos_deriv, beta_expansion, order)
        bc_cos_beta_expansion = td.scalarprod_deriv(bc_expansion, cos_beta_expansion, order)
    # x2+c**2 - 2*(b*c*cb + a*c*(ct*sa*sb-ca*cb))
    if ac_expansion is None:
        ac_expansion = td.scalarprod_deriv(a_expansion, c_expansion, order)

    ac_cos_cos_expansion = td.scalarprod_deriv(ac_expansion, cos_alpha_cos_beta_expansion, order)
    ac_sin_sin_expansion = td.scalarprod_deriv(ac_expansion, sin_alpha_sin_beta_expansion, order)

    # ct = ((x2+c**2) - r2 - 2*b*c*cb + 2*a*c*ca*cb) / (2*a*c*sa*sb)
    numerator = td.subtract_expansions(
        td.add_expansions(x2_expansion, c2_expansion),
        td.add_expansions(
            r2_expansion,
            td.scale_expansion(
                td.subtract_expansions(bc_cos_beta_expansion, ac_cos_cos_expansion),
                2
            )
        )
    )
    denom = td.scale_expansion(
        td.scalarinv_deriv(ac_sin_sin_expansion),
        2
    )

    term = td.scalarprod_deriv(numerator, denom, order)
    if not return_cos:
        term = td.scalarfunc_deriv(arccos_deriv, term, order)

    if return_components:
        return term, (
            cos_alpha_expansion,
            cos_beta_expansion,
            sin_alpha_expansion,
            sin_beta_expansion,
            a2_expansion,
            b2_expansion,
            c2_expansion,
            x2_expansion,
            r2_expansion,
            ab_expansion,
            bc_cos_beta_expansion,
            bc_expansion,
            ac_expansion,
            cos_alpha_cos_beta_expansion,
            sin_alpha_sin_beta_expansion
        )
    else:
        return term

def dihedral_from_ssssss(a, b, c, x, y, r, use_cos=False):
    xp = (a + b) ** 2
    xm = (a - b) ** 2
    yp = (b + c) ** 2
    ym = (b - c) ** 2
    x2 = x ** 2
    y2 = y ** 2
    a2 = a ** 2
    b2 = b ** 2
    c2 = c ** 2
    r2 = r ** 2
    ct = (
            (a2 + b2 - x2) * (b2 + c2 - y2)
            - ((r2 - (x2 + y2 - b2)) * (2 * b2))
    ) / np.sqrt((xm - x2) * (xp - x2) * (ym - y2) * (yp - y2))
    if use_cos:
        return ct
    else:
        return np.arccos(ct)
def dihedral_from_ssssss_deriv(a_expansion, b_expansion, c_expansion, x_expansion,
                               y_expansion, r_expansion, order,
                               return_components=False,
                               return_cos=False,
                               a2_expansion=None,
                               b2_expansion=None,
                               c2_expansion=None,
                               x2_expansion=None,
                               y2_expansion=None,
                               r2_expansion=None,
                               abplus_expansion=None,
                               abminus_expansion=None,
                               bcplus_expansion=None,
                               bcminus_expansion=None,
                               det_expansion=None,
                               ):
    # potentially more stable than just computing the sin and cos in the usual way...
    if x2_expansion is None:
        x2_expansion = td.scalarpow_deriv(x_expansion, 2, order)
    if y2_expansion is None:
        y2_expansion = td.scalarpow_deriv(y_expansion, 2, order)
    if a2_expansion is None:
        a2_expansion = td.scalarpow_deriv(a_expansion, 2, order)
    if b2_expansion is None:
        b2_expansion = td.scalarpow_deriv(b_expansion, 2, order)
    if c2_expansion is None:
        c2_expansion = td.scalarpow_deriv(c_expansion, 2, order)
    if r2_expansion is None:
        r2_expansion = td.scalarpow_deriv(r_expansion, 2, order)

    if det_expansion is None:
        if abplus_expansion is None:
            abplus_expansion = td.scalarpow_deriv(td.add_expansions(a_expansion, b_expansion), 2, order)
        if abminus_expansion is None:
            abminus_expansion = td.scalarpow_deriv(td.subtract_expansions(a_expansion, b_expansion), 2, order)
        if bcplus_expansion is None:
            bcplus_expansion = td.scalarpow_deriv(td.add_expansions(b_expansion, c_expansion), 2, order)
        if bcminus_expansion is None:
            bcminus_expansion = td.scalarpow_deriv(td.subtract_expansions(b_expansion, c_expansion), 2, order)
        # np.sqrt((xm - x2)*(xp - x2)*(ym - y2)*(yp - y2))
        abp = td.subtract_expansions(abplus_expansion, x2_expansion)
        abm = td.subtract_expansions(abminus_expansion, x2_expansion)
        bcp = td.subtract_expansions(bcplus_expansion, y2_expansion)
        bcm = td.subtract_expansions(bcminus_expansion, y2_expansion)
        det_expansion = td.scalarfunc_deriv(sqrt_deriv,
                                            td.scalarprod_deriv(
                                                td.scalarprod_deriv(abm, abp, order),
                                                td.scalarprod_deriv(bcm, bcp, order),
                                                order
                                            ),
                                            order
                                            )

    #     ct = (
    #             (a2 + b2 - x2) * (b2 + c2 - y2)
    #             - ((r2 - (x2 + y2 - b2)) * (2 * b2))
    #     ) / np.sqrt((xm - x2) * (xp - x2) * (ym - y2) * (yp - y2))
    det_inv_expansion = td.scalarinv_deriv(det_expansion, order)
    num_expansion_1 = td.scalarprod_deriv(
        td.subtract_expansions(td.add_expansions(a2_expansion, b2_expansion), x2_expansion),
        td.subtract_expansions(td.add_expansions(b2_expansion, c2_expansion), y2_expansion),
        order

    )
    # ((r2 - (x2 + y2 - b2)) * (2 * b2))
    num_expansion_2 = td.scalarprod_deriv(
        td.subtract_expansions(
            td.add_expansions(r2_expansion, b2_expansion),
            td.add_expansions(x2_expansion, y2_expansion)
        ),
        td.scale_expansion(b2_expansion, 2),
        order
    )
    term = td.scalarprod_deriv(
        td.subtract_expansions(num_expansion_1, num_expansion_2),
        det_inv_expansion,
        order
    )

    if not return_cos:
        term = td.scalarfunc_deriv(arccos_deriv, term, order)

    if return_components:
        return term, (
            a2_expansion,
            b2_expansion,
            c2_expansion,
            x2_expansion,
            y2_expansion,
            r2_expansion,
            abplus_expansion,
            abminus_expansion,
            bcplus_expansion,
            bcminus_expansion,
            det_expansion
        )
    else:
        return term


class DihedralSpecifierType(enum.Enum):
    SSSAAT = "sssaat"
    SSSSAT = "ssssat"
    SSSSST = "ssssst"
def dihedral_distance_converter(dihedral_type:str|DihedralSpecifierType):
    dihedral_type = DihedralSpecifierType(dihedral_type)
    if dihedral_type == DihedralSpecifierType.SSSSST:
        return (dihedral_sssss_distance, dihedral_sssss_distance_deriv)
    elif dihedral_type == DihedralSpecifierType.SSSSAT:
        return (dihedral_ssssa_distance, dihedral_ssssa_distance_deriv)
    else:
        return (dihedral_sssaa_distance, dihedral_sssaa_distance_deriv)
def dihedral_distance(spec, dihedral_type:str|DihedralSpecifierType,
                      order=None,
                      use_cos=False,
                      **deriv_kwargs
                      ) -> float|np.ndarray:
    converter, deriv_converter = dihedral_distance_converter(dihedral_type)
    if order is None:
        return converter(*spec, use_cos=use_cos)
    else:
        x,y,z,a,b,t = spec
        return deriv_converter(x,y,z,a,b,t, order, **deriv_kwargs)
def dihedral_from_distance_converter(dihedral_type:str|DihedralSpecifierType):
    dihedral_type = DihedralSpecifierType(dihedral_type)
    if dihedral_type == DihedralSpecifierType.SSSSST:
        return (dihedral_from_ssssss, dihedral_from_ssssss_deriv)
    elif dihedral_type == DihedralSpecifierType.SSSSAT:
        return (dihedral_from_sssssa, dihedral_from_sssssa_deriv)
    else:
        return (dihedral_from_ssssaa, dihedral_from_ssssaa_deriv)
def dihedral_from_distance(spec, dihedral_type:str|DihedralSpecifierType,
                           order=None,
                           use_cos=False,
                           **deriv_kwargs
                           ) -> float|np.ndarray:

    converter, deriv_converter = dihedral_from_distance_converter(dihedral_type)
    if order is None:
        return converter(*spec, use_cos=use_cos)
    else:
        x,y,z,a,b,r = spec
        return deriv_converter(x,y,z,a,b,r, order, **deriv_kwargs)