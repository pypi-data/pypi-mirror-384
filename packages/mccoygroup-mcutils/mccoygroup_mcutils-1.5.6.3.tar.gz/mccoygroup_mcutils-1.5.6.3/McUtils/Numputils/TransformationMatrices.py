import enum
import itertools

import scipy.linalg

from .VectorOps import vec_normalize, vec_angles
from . import VectorOps as vec_ops
from . import Misc as misc
from . import PermutationOps as perm_ops
import math, numpy as np, scipy as sp

__all__ = [
    "rotation_matrix",
    "skew_symmetric_matrix",
    "rotation_matrix_skew",
    "youla_skew_decomp",
    "youla_skew_matrix",
    "youla_angles",
    "youla_matrix",
    "skew_from_rotation_matrix",
    "translation_matrix",
    "affine_matrix",
    "reflection_matrix",
    "permutation_matrix",
    "extract_rotation_angle_axis",
    "extract_reflection_axis",
    "view_matrix",
    "find_coordinate_matching_permutation",
    "symmetry_permutation",
    "apply_symmetries",
    "symmetry_reduce",
    "identify_cartesian_transformation_type",
    "TransformationTypes",
    "cartesian_transformation_from_data"
]

#######################################################################################################################
#
#                                                 rotation_matrix
#

def rotation_matrix_2d(theta):
    return np.moveaxis(
        np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)]
        ]),
        0, -2
    )

def rotation_matrix_basic(xyz, theta):
    """rotation matrix about x, y, or z axis

    :param xyz: x, y, or z axis
    :type xyz: str
    :param theta: counter clockwise angle in radians
    :type theta: float
    """

    axis = xyz.lower()
    theta = np.asanyarray(theta)
    one = np.ones_like(theta)
    zero = np.zeros_like(theta)
    if axis == "z": # most common case so it comes first
        mat = [
            [ np.cos(theta), -np.sin(theta), zero],
            [ np.sin(theta),  np.cos(theta), zero],
            [ zero,                    zero,  one]
        ]
    elif axis == "y":
        mat = [
            [ np.cos(theta), zero, -np.sin(theta)],
            [ zero,           one,           zero],
            [ np.sin(theta), zero,  np.cos(theta)]
        ]
    elif axis == "x":
        mat = [
            [  one,           zero,           zero],
            [ zero,  np.cos(theta), -np.sin(theta)],
            [ zero,  np.sin(theta),  np.cos(theta)]
        ]
    else:
        raise Exception("{}: axis '{}' invalid".format('rotation_matrix_basic', xyz))
    return np.moveaxis(np.array(mat), 0, -1)

#thank you SE for the nice Euler-Rodrigues imp: https://stackoverflow.com/questions/6802577/rotation-of-3d-vector
def rotation_matrix_ER(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([
        [aa + bb - cc - dd, 2 * (bc + ad),     2 * (bd - ac)    ],
        [2 * (bc - ad),     aa + cc - bb - dd, 2 * (cd + ab)    ],
        [2 * (bd + ac),     2 * (cd - ab),     aa + dd - bb - cc]
    ])

def rotation_matrix_ER_vec(axes, thetas):
    """
    Vectorized version of basic ER
    """

    axes = vec_normalize(np.asanyarray(axes))
    thetas = np.asanyarray(thetas)
    # if len(axes.shape) == 1:
    #     axes = axes/np.linalg.norm(axes)
    #     axes = np.broadcast_to(axes, (len(thetas), 3))
    # else:
    #     axes = vec_normalize(axes)

    ax_shape = axes.shape[:-1]
    t_shape = thetas.shape
    if thetas.ndim == 0:
        base_shape = ax_shape
    elif axes.ndim == 1:
        base_shape = t_shape
    elif thetas.ndim != axes.ndim - 1:
        raise ValueError(f"can't broadcast axes and angles with shapes {ax_shape} and {t_shape}")
    else:
        base_shape = tuple(a if t == 1 else t for a,t in zip(ax_shape, t_shape))

    axes = np.reshape(axes, (-1, 3))
    thetas = thetas.reshape(-1)
    if thetas.shape[0] < axes.shape[0]:
        thetas = np.broadcast_to(thetas, axes.shape[:-1])
    elif axes.shape[0] < thetas.shape[0]:
        axes = np.broadcast_to(axes, thetas.shape + axes.shape[-1:])

    a = np.cos(thetas/2.0)
    b, c, d = np.moveaxis(-axes * np.reshape(np.sin(thetas / 2.0), (len(thetas), 1)), -1, 0)
    v = np.array([a, b, c, d])
    # triu_indices
    rows, cols = (
        np.array([0, 0, 0, 0, 1, 1, 1, 2, 2, 3]),
        np.array([0, 1, 2, 3, 1, 2, 3, 2, 3, 3])
    )
    aa, ab, ac, ad, bb, bc, bd, cc, cd, dd = v[rows] * v[cols]
    ## Uses half-angle formula to get compact form for Euler-Rodrigues
    # a^2 * I + [[ 0,    2ad, -2ac]   + [[b^2 - c^2 - d^2,               2bc,              2bd]
    #            [-2ad,    0,  2ab],     [             2bc, -b^2 + c^2 - d^2,              2cd]
    #            [ 2ac, -2ab,    0]]     [             2bd,              2cd, -b^2 - c^2 + d^2]]
    R = np.array([
        [aa + bb - cc - dd,      2 * (bc + ad),         2 * (bd - ac)],
        [    2 * (bc - ad),  aa - bb + cc - dd,         2 * (cd + ab)],
        [    2 * (bd + ac),      2 * (cd - ab),     aa - bb - cc + dd]
    ])
    R = np.moveaxis(R, -1, 0)

    return R.reshape(base_shape + (3, 3))

def rotation_matrix_align_vectors(vec1, vec2):
    vec1 = vec_ops.vec_normalize(vec1)
    vec2 = vec_ops.vec_normalize(vec2)
    s = vec1 + vec2
    i = vec_ops.identity_tensors(vec1.shape[:-1], vec1.shape[-1])
    inner = 1 + vec1[..., np.newaxis, :] @ vec2[..., :, np.newaxis]

    return i - s[..., :, np.newaxis] * (s[..., np.newaxis, :]/inner) + 2 * vec1[..., :, np.newaxis] * vec2[..., np.newaxis, :]

def rotation_matrix(axis, theta=None):
    """
    :param axis:
    :type axis:
    :param theta: angle to rotate by (or Euler angles)
    :type theta:
    :return:
    :rtype:
    """
    if theta is None:
        skew_vector = np.asanyarray(axis, dtype=float)
        if skew_vector.ndim == 0:
            skew_vector = skew_vector[np.newaxis]
        base_shape = skew_vector.shape[:-1]
        skew_vector = skew_vector.reshape(-1, skew_vector.shape[-1])
        rots = np.array([
            rotation_matrix_skew(v)
            for v in skew_vector
        ])
        return rots.reshape(base_shape + rots.shape[-2:])
    elif isinstance(axis, str):
        if axis.lower() == '2d':
            return rotation_matrix_2d(theta)

        theta = np.asanyarray(theta)
        if len(axis) == 1 and theta.ndim == 1 or theta.shape[-2] != 1:
            theta = np.expand_dims(theta, -2)
        rot_mat = None
        for x,t in zip(axis.lower(), np.moveaxis(theta, -2, 0)):
            rr = rotation_matrix_basic(x, t)
            if rot_mat is None:
                rot_mat = rr
            else:
                rot_mat = rr @ rot_mat
        return rot_mat
    else:
        axis = np.asanyarray(axis)
        theta = np.asanyarray(theta)

        if axis.shape == theta.shape:
            return rotation_matrix_align_vectors(axis, theta)
        elif (axis.ndim == theta.ndim + 1) or theta.ndim == 0 and axis.shape[-1] == 3:
            return rotation_matrix_ER_vec(axis, theta)
        else:
            # we have the vectors that get mixed and their mixing angles, we assume any fixed axis is the 0 element
            # I haven't vectorized this at all...
            base_shape = axis.shape[:-1]
            theta = theta.reshape(-1, theta.shape[-1])
            axis = axis.reshape((-1,) + axis.shape[-1:])

            rots = np.array([
                rotation_matrix_from_angles_vectors(l, T)
                for T, l in zip(axis, theta)
            ])

            return rots.reshape(base_shape + rots.shape[-2:])

def skew_symmetric_matrix(upper_tri):
    upper_tri = np.asanyarray(upper_tri)
    l = upper_tri.shape[-1]
    n = (1 + np.sqrt(1 + 8*l)) / 2
    if int(n) != n:
        raise ValueError(f"vector of shape {l} doesn't correspond to the upper triangle of a matrix")
    n = int(n)
    base_shape = upper_tri.shape[:-1]
    m = np.zeros(base_shape + (n, n))
    rows, cols = np.triu_indices_from(m, 1)
    m[..., rows, cols] = upper_tri
    m[..., cols, rows] = -upper_tri
    return m

def extract_rotation_angle_axis(rot_mat, normalize=True):
    rot_mat = np.asanyarray(rot_mat)
    if rot_mat.shape[-1] == 2:
        return np.arccos(rot_mat[..., 0, 0]), None
    elif rot_mat.shape[-1] == 3:
        base_shape = rot_mat.shape[:-2]
        rot_mat = rot_mat.reshape((-1,) + rot_mat.shape[-2:])
        rows, cols = (np.array([2, 0, 1]), np.array([1, 2, 0]))
        skew = (rot_mat[:, rows, cols] - rot_mat[:, cols, rows]) / 2

        ax = np.empty(rot_mat.shape[:-1], dtype=float)
        ang = np.empty(rot_mat.shape[:-2], dtype=float)

        pos_mask = np.linalg.norm(skew, axis=-1) < 1e-6
        bad_pos = np.where(pos_mask)[0]
        rem_pos = np.arange(len(rot_mat))
        if len(bad_pos) > 0:
            rem_pos = np.setdiff1d(rem_pos, bad_pos)
            shift_rot = 1/2 * (rot_mat[bad_pos,] + vec_ops.identity_tensors((len(bad_pos),), rot_mat.shape[-1]))
            for b,r in zip(bad_pos, shift_rot):
                ord = np.lexsort(r)
                ax[b] = r[ord[-1]]
            if normalize:
                ax[bad_pos,] = vec_ops.vec_normalize(ax[bad_pos,])

            # check identity
            id_mask = np.abs(np.trace(rot_mat[bad_pos,], axis1=-1, axis2=-2) > 3-3e-6)
            ang[bad_pos,] = np.pi * np.logical_not(id_mask)

        if len(rem_pos) > 0:
            ax[rem_pos,] = vec_ops.vec_normalize(skew[rem_pos,])

            # uses an efficient implementation by Jens Noeckel: https://mathematica.stackexchange.com/a/29966/38205
            proj = vec_ops.orthogonal_projection_matrix(ax[rem_pos,][:, :, np.newaxis])
            perm = skew[rem_pos,][:, (1, 2, 0)] * np.array([-1, 1, 1])
            ort_vec = (proj @ perm[:, :, np.newaxis]).reshape(perm.shape)
            ort_norms = np.linalg.norm(ort_vec, axis=-1)
            bad_orts = np.where(ort_norms < 1e-4)
            if len(bad_orts) > 0 and len(bad_orts[0]) > 0:
                perm[bad_orts] = vec_ops.vec_normalize(np.random.uniform(size=perm[bad_orts].shape))
                ort_vec = (proj @ perm[:, :, np.newaxis]).reshape(perm.shape)
            normal = vec_ops.vec_crosses(ax[rem_pos,], ort_vec)
            w = np.reshape(rot_mat[rem_pos,] @ ort_vec[:, :, np.newaxis], ort_vec.shape)
            ang[rem_pos,] = np.arctan2(vec_ops.vec_dots(w, normal), vec_ops.vec_dots(w, ort_vec))


        # """
        # ovec = w - axis Dot[w, axis];
        # nvec = Cross[axis, ovec];
        # w1 = m . ovec;
        # """
        #
        # tr_rot = np.trace(rot_mat, axis1=-2, axis2=-1)
        # ang = np.arccos((tr_rot - 1) / 2)
        #
        # zero_mask = np.abs(ang) < 1e-6
        # zero_pos = np.where(zero_mask)
        # gimbal_mask = np.abs(np.abs(ang) - np.pi) < 1e-6
        # gimbal_locked = np.where(gimbal_mask)
        # rem = np.where(np.logical_not(np.logical_or(zero_mask, gimbal_mask)))
        #
        # ax = np.zeros(rot_mat.shape[:-1])
        # if len(zero_pos) > 0 and len(zero_pos[0]) > 0:
        #     ax[zero_pos] = np.repeat([[0, 0, 1]], len(zero_pos[0]), axis=0)
        # if len(gimbal_locked) > 0:
        #     eigs, gimb_ax = np.linalg.eigh(rot_mat[gimbal_locked])
        #     one_pos = np.where(eigs > 1-1e-4)
        #     ax[gimbal_locked] = gimb_ax[one_pos[0], :, one_pos[1]]
        # if len(rem) > 0 and len(rem[0]) > 0:
        #     skew = (rot_mat[rem] - np.moveaxis(rot_mat[rem], -1, -2)) / 2
        #     rows, cols = (np.array([2, 0, 1]), np.array([1, 2, 0]))
        #     ax[rem] = skew[..., rows, cols]
        #     ax[rem] = skew[..., rows, cols]
        # if normalize:
        #     ax = vec_normalize(ax)
        # else:
        #     ax = ax
        return ang.reshape(base_shape), ax.reshape(base_shape + ax.shape[-1:])
    else:
        base_shape = rot_mat.shape[:-2]
        rot_mat = np.reshape(rot_mat, (-1,) + rot_mat.shape[-2:])
        angles = []
        axes = []
        for r in rot_mat:
            U, Q = scipy.linalg.schur(r)
            angles.append(youla_angles(U))
            axes.append(Q)

        angles = np.array(angles)
        axes = np.array(axes)

        return angles.reshape(base_shape + angles.shape[-1:]), axes.reshape(base_shape + axes.shape[-2:])

def extract_reflection_axis(reflection_mat):
    reflection_mat = np.asarray(reflection_mat)
    base_shape = reflection_mat.shape[:-2]
    reflection_mat = np.reshape(reflection_mat, (-1,) + reflection_mat.shape[-2:])
    # if reflection_mat.shape[-1] < 3:
    pt = vec_ops.vec_normalize(np.random.rand(1, reflection_mat.shape[-1]), axis=-1)
    tf_pts = np.reshape(reflection_mat @ pt[:, :, np.newaxis], (reflection_mat.shape[0], reflection_mat.shape[-1]))
    vecs = (pt - tf_pts)
    norms = vec_ops.vec_norms(vecs)
    in_planes = np.where(norms < 1e-4)
    if len(in_planes) > 0 and len(in_planes[0]) > 0: # might have randomly ended up in the reflection plane
        subpt = pt[in_planes]
        subref = reflection_mat[in_planes]
        pt2 = vec_ops.vec_normalize(np.random.rand(1, reflection_mat.shape[-1]), axis=-1)
        pt2 = pt2 - vec_ops.vec_dots(pt[in_planes], pt2)[:, np.newaxis]*pt[in_planes]
        tf_pts = np.reshape(subref @ subpt[:, :, np.newaxis], (subref.shape[0], reflection_mat.shape[-1]))
        vecs[in_planes] = (pt2 - tf_pts)
        norms[in_planes] = vec_ops.vec_norms(vecs[in_planes])
    return vec_ops.vec_normalize(vecs, norms).reshape(base_shape + (reflection_mat.shape[-1],))

def youla_skew_decomp(A):
    n = len(A)
    s, T = sp.linalg.schur(A)

    l = np.diag(s, 1)
    if n % 2 == 0:
        start = 0
        end = n
    else:  # manage padding for odd dimension
        if abs(l[0]) < 1e-7:
            start = 1
            end = n
        else:
            start = 0
            end = n - 1
    l = l[start:end-1:2]

    return youla_matrix(l, n, axis_pos=0 if start == 0 else n), T

def youla_skew_matrix(l, n, axis_pos=0):

    U = np.zeros((n, n))
    o = np.concatenate([  # even inds
        np.arange(0, axis_pos, 2),
        np.arange(axis_pos + 1, n, 2),
    ])
    e = np.concatenate([  # odd inds
        np.arange(1, axis_pos, 2),
        np.arange(axis_pos + 2, n, 2),
    ])

    U[o, e] = l
    U[e, o] = -l

    return U

def youla_matrix(angles, n, axis_pos=0):

    cos = np.cos(angles)
    sin = np.sin(angles)

    # build 2x2 block mat
    U = np.eye(n)
    if n % 2 == 1:
        o = np.concatenate([  # even inds
            np.arange(0, axis_pos, 2),
            np.arange(axis_pos+1, n, 2),
            ])
        e = np.concatenate([  # even inds
            np.arange(1, axis_pos, 2),
            np.arange(axis_pos+2, n, 2),
            ])
    else:
        o = np.arange(0, n, 2)
        e = np.arange(1, n, 2)

    U[o, o] = cos
    U[e, e] = cos
    U[o, e] = sin
    U[e, o] = -sin

    return U

def youla_angles(U, axis_pos=None):
    l = np.arccos(np.round(np.diag(U), 8))
    n = len(U)
    if axis_pos is None:
        if n % 2 == 0:
            axis_pos = -1
        else:  # manage padding for odd dimension
            axis_pos = np.where(abs(l) < 1e-7)[0]
            axis_pos = 0 if axis_pos[0] == 0 else axis_pos[-1]
        if axis_pos < 0:
            axis_pos = n + axis_pos

    return np.concatenate([
        l[0:axis_pos:2],
        l[axis_pos+1::2]
    ])

def rotation_matrix_skew(upper_tri, create_skew=True):
    upper_tri = np.asanyarray(upper_tri)
    if create_skew:
        if (
                upper_tri.ndim < 2
                or upper_tri.shape[-1] != upper_tri.shape[-2]
                or not np.allclose(upper_tri, -np.moveaxis(upper_tri, -2, -1))
        ):
            upper_tri = skew_symmetric_matrix(upper_tri)

    U, T = youla_skew_decomp(upper_tri)
    return T@U@T.T

def skew_from_rotation_matrix(rot_mat):
    U, Q = sp.linalg.schur(rot_mat)

    l = youla_angles(U)
    s = youla_skew_matrix(l, U.shape[0], axis_pos=0 if U[0, 0] == 1 else U.shape[0])
    A = Q @ s @ Q.T
    return A[np.triu_indices_from(A, k=1)]

def rotation_matrix_from_angles_vectors(l, T):
    n = T.shape[0]
    if n % 2 == 1 and len(l) == (n // 2) + 1: # the axis is encoded in l
        axis_pos = np.where(np.abs(l) > 2 * np.pi)[0]
        if len(axis_pos) == 0:
            axis_pos = np.where(np.abs(l) < 1e-7)[0]
            if len(axis_pos) == 0:
                raise ValueError(f"can't find fixed axis position from angle encoding {l}")
        axis_pos = axis_pos[0]
    else:
        axis_pos = 0
    return T @ youla_matrix(l, n, axis_pos=axis_pos) @ T.T

#######################################################################################################################
#
#                                                 translation_matrix
#

def translation_matrix(shift):
    share = np.asarray(shift)
    if len(share.shape) == 1:
        ss = share
        zs = 0.
        os = 1.
        mat = np.array(
            [
                [os, zs, zs, ss[0]],
                [zs, os, zs, ss[1]],
                [zs, zs, os, ss[2]],
                [zs, zs, zs, os   ]
            ]
        )
    else:
        zs = np.zeros((share.shape[0],))
        os = np.ones((share.shape[0],))
        ss = share.T
        mat = np.array(
            [
                [os, zs, zs, ss[0]],
                [zs, os, zs, ss[1]],
                [zs, zs, os, ss[2]],
                [zs, zs, zs, os   ]
            ]
        ).T
    return mat

#######################################################################################################################
#
#                                                 affine_matrix
#

def affine_matrix(tmat, shift):
    """Creates an affine transformation matrix from a 3x3 transformation matrix or set of matrices and a shift or set of vecs

    :param tmat: base transformation matrices
    :type tmat: np.ndarray
    :param shift:
    :type shift:
    :return:
    :rtype:
    """

    base_mat = np.asanyarray(tmat)
    if shift is None:
        return base_mat

    if base_mat.ndim > 2:
        shifts = np.asanyarray(shift)
        if shifts.ndim == 1:
            shifts = np.broadcast_to(shifts, (1,)*(base_mat.ndim-2) + shifts.shape)
        shifts = np.broadcast_to(shifts, base_mat.shape[:-2] + (shifts.shape[-1],))
        shifts = np.expand_dims(shifts, -1)
        mat = np.concatenate([base_mat, shifts], axis=-1)
        padding = np.zeros(shifts.shape[-2]+1)
        padding[-1] = 1
        padding = np.broadcast_to(
            np.broadcast_to(padding, (1,)*(base_mat.ndim-2) + padding.shape),
            mat.shape[:-2] + (shifts.shape[-2]+1,)
        )
        padding = np.expand_dims(padding, -2)
        mat = np.concatenate([mat, padding], axis=-2)
    else:
        shift = np.asanyarray(shift)
        mat = np.concatenate([base_mat, shift[:, np.newaxis]], axis=-1)
        padding = np.zeros(shift.shape[-1]+1)
        padding[-1] = 1
        mat = np.concatenate([mat, padding[np.newaxis]], axis=-2)
    return mat

def view_matrix(
        up_vector,
        view_vector=(0, 0, 1),
        output_order=None
):

    up_vector = vec_ops.vec_normalize(up_vector)
    d = up_vector.shape[-1]
    base_shape = up_vector.shape[:-1]
    up_vector = up_vector.reshape(-1, d)
    view_vector = vec_normalize(view_vector)
    view_vector = view_vector.reshape(-1, d)
    overlaps = vec_ops.vec_dots(up_vector, view_vector)
    bad_views = np.where(np.abs(overlaps) > 1-1e-6) # TOOD: make this a threshold
    if len(bad_views) > 0 and len(bad_views[0]) > 0:
        new_views = np.repeat(np.array([[1, 0, 0]]), len(bad_views[0])).copy()
        overlaps2 = vec_ops.vec_dots(new_views, view_vector[bad_views])
        bad_views2 = np.where(np.abs(overlaps2) > 1-1e-6) # TOOD: make this a threshold
        if len(bad_views2) > 0 and len(bad_views2[0]) > 0:
            new_views[bad_views2] = np.array([[0, 0, 1]])
        new_views = new_views - vec_ops.vec_dots(new_views, view_vector[bad_views]) * view_vector[bad_views]
        view_vector[bad_views] = new_views
    right_vector = vec_ops.vec_normalize(
        vec_ops.vec_crosses(up_vector, view_vector)
    )
    view_vector = vec_ops.vec_normalize(
        vec_ops.vec_crosses(up_vector, right_vector)
    )
    axes = np.concatenate([
        view_vector[..., np.newaxis],
        up_vector[..., np.newaxis],
        right_vector[..., np.newaxis]
    ], axis=-1).reshape(base_shape + (d, d))

    if output_order is not None:
        from .PermutationOps import permutation_sign
        sign = permutation_sign(output_order)
        axes = axes[..., :, output_order]
        axes[..., :, 1] *= sign

    return axes

def reflection_matrix(axes):
    # need to find space of "null" vectors
    axes = np.asanyarray(axes)
    smol = axes.ndim == 1
    if smol:
        axes = axes[np.newaxis]
    if axes.ndim == 2:
        axes = axes[:, np.newaxis, :]
    base_shape = axes.shape[:-2]
    axes = axes.reshape((-1,) + axes.shape[-2:])
    nax = axes.shape[-2]
    ndim = axes.shape[-1]
    eyes = vec_ops.identity_tensors(axes.shape[0], ndim)
    full_basis = np.concatenate([axes, eyes], axis=-2)
    q, r = np.linalg.qr(np.moveaxis(full_basis, -2, -1))
    tf = q[:, :, :ndim]

    diag_refl = np.diag([-1] * nax + [1] * (ndim - nax))[np.newaxis]
    refls = tf @ diag_refl @ np.moveaxis(tf, -2, -1)

    refls = refls.reshape(base_shape + refls.shape[1:])
    if smol: refls = refls[0]

    return refls

def permutation_matrix(perm):
    perm = np.asanyarray(perm)
    smol = perm.ndim == 1
    if smol:
        perm = perm[np.newaxis]
    base_shape = perm.shape[:-1]
    perm = perm.reshape(-1, perm.shape[-1])
    mats = np.zeros((perm.shape[0], perm.shape[-1], perm.shape[-1]), dtype='uint8')
    ix = (
        np.expand_dims(np.arange(mats.shape[0]), [1]),
        np.expand_dims(np.arange(perm.shape[-1]), [0]),
        perm
    )
    mats[ix] = 1

    mats = mats.reshape(base_shape + mats.shape[1:])
    if smol: mats = mats[0]

    return mats

def find_coordinate_matching_permutation(coords, new_coords, return_row_ordering=False, tol=None):
    base_shape = coords.shape[:-2]
    coords = coords.reshape((-1,) + coords.shape[-2:])
    new_coords = new_coords.reshape((-1,) + new_coords.shape[-2:])
    dm = np.linalg.norm(coords[:, :, np.newaxis] - new_coords[:, np.newaxis, :], axis=-1)
    # quick_test = np.where(dm < 1e-2)
    # iteratively find best matches and map them onto each other
    perm_rows = np.repeat(np.arange(coords.shape[1])[np.newaxis], coords.shape[0], axis=0)
    perm_cols = np.repeat(np.arange(coords.shape[1])[np.newaxis], coords.shape[0], axis=0)
    a = np.arange(dm.shape[0])
    a1 = np.arange(dm.shape[0])[:, np.newaxis]
    a2 = np.arange(dm.shape[1])
    for i in range(coords.shape[1]):
        # we drop one more row each loop
        if i > 0:
            sel = a2[np.newaxis, :(-i)]
        else:
            sel = a2[np.newaxis, :]

        # print(np.round(dm, 8))
        min_pos = np.argmin(dm, axis=-1) # min across columns
        min_vals = dm[a1, sel, min_pos]
        ord = np.argsort(min_vals, axis=-1) # min across rows
        if tol is not None:
            max_min = np.max(min_vals)
            if max_min > tol:
                raise ValueError(f"maximum minimum deviation too large {max_min} > {tol}")
        # ord = np.argsort(ord, axis=-1)
        # assign row permutation
        perm_next = perm_rows[:, i:][a1[:, np.newaxis], ord[:, 0]]
        perm_rows[:, i+1:] = perm_rows[:, i:][a1[:, np.newaxis], ord[:, 1:]]
        perm_rows[:, i] = perm_next

        # # column can be duplicated, so we reorder just based on the minimum row
        min_pos = np.argsort(dm[a, ord[:, 0]], axis=-1) # min across columns
        # # print("?", ord[:, 0].shape, dm[a1, ord[:, 0]].shape)
        # # min_pos = min_pos[a1, ord]
        perm_next = perm_cols[:, i:][a1[:, np.newaxis], min_pos[:, 0]]
        # print(perm_cols[:, i:][a1[:, np.newaxis], min_pos[:, 1:]])
        perm_cols[:, i+1:] = perm_cols[:, i:][a1[:, np.newaxis], min_pos[:, 1:]]
        perm_cols[:, i] = perm_next

        # print("?", perm_rows)
        # print(">", np.sort(min_pos[:, 1:], axis=-1))
        # print(ord)
        dm = dm[a1, ord[:, 1:, np.newaxis], min_pos[:, np.newaxis, 1:]]


    if return_row_ordering:
        return perm_rows.reshape(base_shape), perm_cols.reshape(base_shape)
    else:
        row_sort = np.argsort(perm_rows, axis=1)
        perms = perm_cols[a1, row_sort].reshape(base_shape + perm_cols.shape[1:])
        return perms

def symmetry_permutation(coords, op:np.ndarray, return_row_ordering=False, tol=None):
    # converts a symmetry operation into a permutation of the coords
    coords = np.asanyarray(coords)
    op = np.asanyarray(op)

    base_shape = coords.shape[:-2]
    coords = coords.reshape((-1,) + coords.shape[-2:])
    op = op.reshape((-1,) + op.shape[-2:])
    new_coords = coords @ op

    perm_data = find_coordinate_matching_permutation(coords, new_coords,
                                                     return_row_ordering=return_row_ordering, tol=tol
                                                     )

    if return_row_ordering:
        perm_rows, perm_cols = perm_data
        return perm_rows.reshape(base_shape + perm_rows.shape[-1:]), perm_cols.reshape(base_shape + perm_cols.shape[-1:])
    else:
        return perm_data.reshape(base_shape + perm_data.shape[-1:])

def apply_symmetries(coords, symmetry_elements: 'list[np.ndarray]', labels=None, tol=1e-1):
    coords = np.asanyarray(coords)
    if coords.ndim == 1:
        coords = coords[np.newaxis]
    elif coords.ndim > 2:
        raise NotImplementedError("currently don't have good batching on coord symmetry application")
    og_labels = labels
    if labels is not None:
        if labels is True:
            labels = np.arange(len(coords))
        else:
            labels = np.arange(len(labels))
    # symmetry_elements = prep_symmetry_operations(symmetry_elements)

    for e in symmetry_elements:
        new_coords = coords @ e
        coord_diffs = np.linalg.norm(coords[:, np.newaxis, :] - new_coords[np.newaxis, :, :], axis=-1)
        dupe_pos = np.where(coord_diffs < tol)
        new_labs = None
        if len(dupe_pos) > 0 and len(dupe_pos[0]) > 0:
            rem = np.setdiff1d(np.arange(len(new_coords)), dupe_pos[0])
            if labels is not None:
                new_labs = labels[rem,]
            new_coords = new_coords[rem,]
        elif labels is not None:
            new_labs = labels
        if labels is not None:
            labels = np.concatenate([labels, new_labs])
        coords = np.concatenate([coords, new_coords], axis=0)

    if labels is not None:
        if og_labels is not True:
            labels = [og_labels[i] for i in labels]
        return coords, labels
    else:
        return coords

def symmetry_reduce(coords, op:np.ndarray, labels=None):
    coords = np.asarray(coords)
    if coords.ndim == 1:
        if labels is not None:
            return coords, labels
        else:
            return coords
    elif coords.ndim > 2:
        raise NotImplementedError("currently don't have good batching on coord symmetry reduction")

    perm = symmetry_permutation(coords, op)
    cycles = perm_ops.permutation_cycles(perm, return_groups=True)
    coords = np.array([
        coords[p[0]]
        for p in cycles
    ])
    if labels is not None:
        labels = [
            labels[p[0]]
            for p in cycles
        ]
        return coords, labels
    else:
        return coords

class TransformationTypes(enum.Enum):
    Identity = 0
    Inversion = 1
    Rotation = 2
    Reflection = 3
    ImproperRotation = 4
    Scaling = 5

def identify_cartesian_transformation_type(x, max_rotation_order=None):
        # check unitary
        x = np.asanyarray(x)
        base_shape = x.shape[:-2]
        x = x.reshape((-1,) + x.shape[-2:])
        scalings, x = vec_ops.polar_decomposition(x)

        types = np.zeros(x.shape[0], dtype=int)
        axes = np.zeros((x.shape[0], 3))
        orders = np.full(x.shape[0], -1, dtype=int)
        roots = np.full(x.shape[0], -1, dtype=float)

        rem_pos = np.arange(x.shape[0])
        t = np.trace(x, axis1=-2, axis2=-1)
        inversion_mask = t < -3 + 1e-2
        types[inversion_mask] = 1

        rem = np.logical_not(inversion_mask)
        rem_pos = rem_pos[rem]
        x = x[rem]
        t = t[rem]


        if len(rem_pos) > 0:
            # identity by default
            rem = t < 3 - 1e-2
            rem_pos = rem_pos[rem]
            x = x[rem]


        if len(rem_pos) > 0:
            d = np.linalg.det(x)
            rotation_mask = d > 1-1e-2

            rotations = x[rotation_mask]

            rot_sel = rem_pos[rotation_mask]
            types[rot_sel,] = 2
            ang, ax = extract_rotation_angle_axis(rotations)
            axes[rot_sel,] = ax

            rationals = ang / (2 * np.pi)
            if max_rotation_order is None:
                roots[rot_sel,] = rationals
                orders[rot_sel,] = 1
            else:
                for rational, i in zip(rationals, rot_sel):
                    for o in range(1, max_rotation_order + 1):
                        root = rational * o
                        if abs(root - np.round(root)) < 1e-6:
                            roots[i] = int(np.round(root))
                            orders[i] = o
                            break
                    else:
                        #TODO: don't just terminate...
                        raise ValueError(
                            f"angle ratio {ang} doesn't correspond to a rational number up to order {max_rotation_order} rotations"
                        )

            rem = np.logical_not(rotation_mask)
            x = x[rem]
            rem_pos = rem_pos[rem]

        if len(rem_pos) > 0:
            reflection_mask = np.max(np.max(x - np.moveaxis(x, -1, -2), axis=-1), axis=-1) < 1e-6 # symmetric
            ref_sel = rem_pos[reflection_mask]
            types[ref_sel,] = 3
            axes[ref_sel,] = extract_reflection_axis(x[reflection_mask])

            rem = np.logical_not(reflection_mask)
            x = x[rem]
            rem_pos = rem_pos[rem]

        if len(rem_pos) > 0:
            # it turns out the same axis trick works for improper rotations
            types[rem_pos,] = 4

            ang, ax = extract_rotation_angle_axis(x)
            axes[rem_pos,] = ax

            rationals = ang / (2 * np.pi)
            if max_rotation_order is None:
                roots[rem_pos,] = rationals
                orders[rem_pos,] = 1
            else:
                for rational, i in zip(rationals, rem_pos):
                    for o in range(1, max_rotation_order + 1):
                        root = rational * o
                        if abs(root - np.round(root)) < 1e-6:
                            roots[i] = int(np.round(root))
                            orders[i] = o
                            break
                    else:
                        # TODO: don't just terminate...
                        raise ValueError(
                            f"angle ratio {ang} doesn't correspond to a rational number up to order {max_rotation_order} rotations"
                        )

        if scalings is not None:
            scalings.reshape(base_shape + scalings.shape[-2:])
        types = types.reshape(base_shape)
        axes = axes.reshape(base_shape + axes.shape[-1:])
        roots = roots.reshape(base_shape)
        orders = orders.reshape(base_shape)
        return scalings, types, axes, roots, orders

def cartesian_transformation_from_data(scalings, types, axes, roots, orders):
    if scalings is not None:
        scalings = np.asanyarray(scalings)
        if scalings.ndim == 1:
            scalings = np.diag(scalings)
        elif scalings.shape[-1] != scalings.shape[-2]:
            scalings = vec_ops.vec_tensordiag(scalings)
    types = np.asanyarray(types)
    axes = np.asanyarray(axes)
    roots = np.asanyarray(roots)
    orders = np.asanyarray(orders)

    base_shape = types.shape
    if scalings is not None:
        scalings = np.reshape(scalings, (-1,) + scalings.shape[-2:])
    types = np.reshape(types, (-1,))
    axes = np.reshape(axes, (-1,) + axes.shape[-1:])
    roots = np.reshape(roots, (-1,))
    orders = np.reshape(orders, (-1,))

    unitary_tfs = np.empty((types.shape[0], axes.shape[-1], axes.shape[-1]), dtype=float)
    rem_pos = np.arange(types.shape[0])

    identity_mask = types == 0
    sel = rem_pos[identity_mask]
    if len(sel) > 0:
        unitary_tfs[sel,] = np.eye(3)[np.newaxis]
        rem = np.logical_not(identity_mask)
        rem_pos = rem_pos[rem]

        types = types[rem]
        axes = axes[rem]
        roots = roots[rem]
        orders = orders[rem]

    if len(types) > 0:
        inverse_mask = types == 1
        sel = rem_pos[inverse_mask]
        if len(sel) > 0:
            unitary_tfs[sel,] = -np.eye(3)[np.newaxis]
            rem = np.logical_not(inverse_mask)
            rem_pos = rem_pos[rem]

            types = types[rem]
            axes = axes[rem]
            roots = roots[rem]
            orders = orders[rem]

    if len(types) > 0:
        rotation_mask = types == 2
        sel = rem_pos[rotation_mask]
        if len(sel) > 0:
            angles = 2*np.pi*roots[rotation_mask]/orders[rotation_mask]
            unitary_tfs[sel,] = rotation_matrix_ER_vec(axes[rotation_mask], angles)
            rem = np.logical_not(rotation_mask)
            rem_pos = rem_pos[rem]

            types = types[rem]
            axes = axes[rem]
            roots = roots[rem]
            orders = orders[rem]

    if len(types) > 0:
        reflection_mask = types == 3
        sel = rem_pos[reflection_mask]
        if len(sel) > 0:
            unitary_tfs[sel,] = reflection_matrix(axes[reflection_mask,])
            rem = np.logical_not(reflection_mask)
            rem_pos = rem_pos[rem]

            types = types[rem]
            axes = axes[rem]
            roots = roots[rem]
            orders = orders[rem]

    if len(types) > 0:
        # improt_mask = types == 4
        angles = 2*np.pi*roots/orders
        unitary_tfs[rem_pos,] = reflection_matrix(axes) @ rotation_matrix_ER_vec(axes, angles)
        # rem = np.logical_not(reflection_mask)
        # rem_pos = rem_pos[rem]
        #
        # types = types[rem]
        # axes = axes[rem]
        # orders = orders[rem]

    if scalings is not None:
        unitary_tfs = scalings @ unitary_tfs

    return unitary_tfs.reshape(base_shape + unitary_tfs.shape[-2:])



