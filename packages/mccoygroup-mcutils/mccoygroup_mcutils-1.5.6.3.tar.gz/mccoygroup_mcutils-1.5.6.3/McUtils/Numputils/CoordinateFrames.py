
__all__ = [
    "center_of_mass",
    "inertia_tensors",
    "moments_of_inertia",
    "inertial_frame_derivatives",
    "translation_rotation_eigenvectors",
    "translation_rotation_projector",
    "remove_translation_rotations",
    "translation_rotation_invariant_transformation",
    "eckart_embedding",
    "rmsd_minimizing_transformation",
    "eckart_permutation",


]

import itertools, collections

import numpy as np, scipy.optimize as opt
from . import VectorOps as vec_ops
from . import PermutationOps as perm_ops
# from . import SetOps as set_ops
# from . import Misc as misc
# from . import TransformationMatrices as tf_mats

def center_of_mass(coords, masses=None):
    """Gets the center of mass for the coordinates

    :param coords:
    :type coords: CoordinateSet
    :param masses:
    :type masses:
    :return:
    :rtype:
    """

    if masses is None:
        masses = np.ones(coords.shape[-2])

    masses = masses.copy()
    masses[masses < 0] = 0

    return np.tensordot(masses / np.sum(masses), coords, axes=[0, -2])

def inertia_tensors(coords, masses=None):
    """
    Computes the moment of intertia tensors for the walkers with coordinates coords (assumes all have the same masses)

    :param coords:
    :type coords: CoordinateSet
    :param masses:
    :type masses: np.ndarray
    :return:
    :rtype:
    """

    if masses is None:
        masses = np.ones(coords.shape[-2])

    com = center_of_mass(coords, masses)
    coords = coords - com[..., np.newaxis, :]

    real_spots = masses > 0 # allow for dropping out dummy atoms
    coords = coords[..., real_spots, :]
    masses = masses[real_spots]

    d = np.zeros(coords.shape[:-1] + (3, 3), dtype=float)
    diag = vec_ops.vec_dots(coords, coords)
    d[..., (0, 1, 2), (0, 1, 2)] = diag[..., np.newaxis]
    # o = np.array([[np.outer(a, a) for a in r] for r in coords])
    o = vec_ops.vec_outer(coords, coords, axes=[-1, -1])
    tens = np.tensordot(masses, d - o, axes=[0, -3])

    return tens

def inertial_frame_derivatives(coords, masses=None, sel=None):
    if masses is None:
        masses = np.ones(coords.shape[-2])

    masses = np.asanyarray(masses)
    coords = np.asanyarray(coords)
    real_pos = masses > 0
    if sel is not None:
        real_pos = np.intersect1d(sel, real_pos)

    smol = coords.ndim == 2
    if smol:
        coords = coords[np.newaxis]
    base_shape = coords.shape[:-2]
    coords = coords.reshape((-1,) + coords.shape[-2:])
    if masses.ndim == 1:
        masses = masses[np.newaxis]
    else:
        masses = np.reshape(masses, (-1, masses.shape[-1]))

    masses = masses[..., real_pos]
    coords = coords[..., real_pos, :]

    masses = np.sqrt(masses)
    carts = masses[..., :, np.newaxis] * coords  # mass-weighted Cartesian coordinates

    ### compute basic inertia tensor derivatives
    # first derivs are computed as a full (nAt, 3, I_rows (3), I_cols (3)) tensor
    # and then reshaped to (nAt * 3, I_rows, I_cols)
    eyeXeye = np.eye(9).reshape(3, 3, 3, 3).transpose((2, 0, 1, 3))
    I0Y_1 = np.tensordot(carts, eyeXeye, axes=[2, 0])

    nAt = carts.shape[1]
    nY = nAt * 3
    I0Y_21 = (
            np.reshape(np.eye(3), (9,))[np.newaxis, :, np.newaxis]
            * carts[:, :, np.newaxis, :]
    )  # a flavor of outer product
    I0Y_21 = I0Y_21.reshape((-1, nAt, 3, 3, 3))
    I0Y_2 = (I0Y_21 + I0Y_21.transpose((0, 1, 2, 4, 3)))
    I0Y = 2 * I0Y_1 - I0Y_2
    I0Y = I0Y.reshape(base_shape + (nY, 3, 3))

    # second derivatives are 100% independent of coorinates
    # only the diagonal blocks are non-zero, so we compute that block
    # and then tile appropriately
    keyXey = np.eye(9).reshape(3, 3, 3, 3)
    I0YY_nn = 2 * eyeXeye - (keyXey + keyXey.transpose((0, 1, 3, 2)))
    I0YY = np.zeros((nAt, 3, nAt, 3, 3, 3))
    for n in range(nAt):
        I0YY[n, :, n, :, :, :] = I0YY_nn
    I0YY = I0YY.reshape((nY, nY, 3, 3))
    I0YY = np.broadcast_to(I0YY[np.newaxis, :, :, :, :], (carts.shape[0],) + I0YY.shape)
    I0YY = np.reshape(I0YY, base_shape + (nY, nY, 3, 3))

    if smol:
        I0Y = I0Y[0]
        I0YY = I0YY[0]

    return [I0Y, I0YY]

def moments_of_inertia(coords, masses=None):
    """
    Computes the moment of inertia tensor for the walkers with coordinates coords (assumes all have the same masses)

    :param coords:
    :type coords: CoordinateSet
    :param masses:
    :type masses: np.ndarray
    :return:
    :rtype:
    """

    if coords.ndim == 1:
        raise ValueError("can't get moment of inertia for single point (?)")
    elif coords.ndim == 2:
        multiconfig = False
        coords = coords[np.newaxis]
        extra_shape = None
    else:
        multiconfig = True
        extra_shape = coords.shape[:-2]
        coords = coords.reshape((np.prod(extra_shape),) + coords.shape[-2:])


    if masses is None:
        masses = np.ones(coords.shape[-2])

    massy_doop = inertia_tensors(coords, masses)
    moms, axes = np.linalg.eigh(massy_doop)
    # a = axes[..., :, 0]
    # c = axes[..., :, 2]
    # b = nput.vec_crosses(a, c)  # force right-handedness to avoid inversions
    # axes[..., :, 1] = b
    a = axes[..., :, 0]
    b = axes[..., :, 1]
    c = vec_ops.vec_crosses(b, a)  # force right-handedness to avoid inversions
    axes[..., :, 2] = c
    dets = np.linalg.det(axes) # ensure we have true rotation matrices to avoid inversions
    axes[..., :, 2] /= dets[..., np.newaxis]

    if multiconfig:
        moms = moms.reshape(extra_shape + (3,))
        axes = axes.reshape(extra_shape + (3, 3))
    else:
        moms = moms[0]
        axes = axes[0]
    return moms, axes

def translation_rotation_eigenvectors(coords, masses=None, mass_weighted=True):
    """
    Returns the eigenvectors corresponding to translations and rotations
    in the system

    :param coords:
    :type coords:
    :param masses:
    :type masses:
    :return:
    :rtype:
    """


    if masses is None:
        masses = np.ones(coords.shape[-2])
    masses = np.asanyarray(masses)

    n = len(masses)
    # explicitly put masses in m_e from AMU
    # masses = UnitsData.convert("AtomicMassUnits", "AtomicUnitOfMass") * masses
    mT = np.sqrt(np.sum(masses))
    mvec = np.sqrt(masses)

    # no_derivs = order is None
    # if no_derivs:
    #     order = 0

    smol = coords.ndim == 2
    if smol:
        coords = coords[np.newaxis]
    # base_shape = None
    # if coords.ndim > 3:
    base_shape = coords.shape[:-2]
    coords = coords.reshape((-1,) + coords.shape[-2:])

    M = np.kron(mvec / mT, np.eye(3)).T  # translation eigenvectors
    mom_rot, ax_rot = moments_of_inertia(coords, masses)
    # if order > 0:
    #     base_tensor = StructuralProperties.get_prop_inertia_tensors(coords, masses)
    #     mom_expansion = StructuralProperties.get_prop_inertial_frame_derivatives(coords, masses)
    #     inertia_expansion = [base_tensor] + mom_expansion
    #     sqrt_expansion = nput.matsqrt_deriv(inertia_expansion, order)
    #     inv_rot_expansion = nput.matinv_deriv(sqrt_expansion, order=order)
    #     inv_rot_2 = inv_rot_expansion[0]
    # else:
    good_ax = np.abs(mom_rot) > 1e-8
    nonlinear = good_ax.flatten().all()
    if nonlinear:
        inv_mom_2 = vec_ops.vec_tensordiag(1 / np.sqrt(mom_rot))
        inv_rot_2 = vec_ops.vec_tensordot(
            ax_rot,
            vec_ops.vec_tensordot(
                ax_rot,
                inv_mom_2,
                shared=1,
                axes=[-1, -1]
            ),
            shared=1,
            axes=[-1, -1]
        )
    else:
        all_linear = len(good_ax)==0 or np.sum(np.abs(np.diff(good_ax, axis=0))) == 0
        if all_linear:
            good_ax = good_ax[0]
            inv_mom_2 = vec_ops.vec_tensordiag(1 / np.sqrt(mom_rot[:, good_ax,]))
            inv_rot_2 = vec_ops.vec_tensordot(
                ax_rot[:, :, good_ax],
                vec_ops.vec_tensordot(
                    ax_rot[:, :, good_ax],
                    inv_mom_2,
                    shared=1,
                    axes=[-1, -1]
                ),
                shared=1,
                axes=[-1, -1]
            )
        else:
            inv_rot_2 = []
            for sel,moms,rot in zip(good_ax, mom_rot, ax_rot):
                inv_mom_2 = vec_ops.vec_tensordiag(1 / np.sqrt(moms[sel,]))
                subinv = rot[:, sel] @ inv_mom_2 @ rot[:, sel].T
                rem = np.array([0, 1, 2])[np.logical_not(sel)]
                subinv[:, rem] = rot.T[:, rem]
                inv_rot_2.append(subinv)
            inv_rot_2 = np.array(inv_rot_2)

    com = center_of_mass(coords, masses)
    com = np.expand_dims(com, 1) # ???
    shift_crds = mvec[np.newaxis, :, np.newaxis] * (coords - com[: np.newaxis, :])
    cos_rot = perm_ops.levi_cevita_dot(3, inv_rot_2, axes=[0, -1], shared=1) # kx3bx3cx3j
    R = vec_ops.vec_tensordot(
        shift_crds, cos_rot,
        shared=1,
        axes=[-1, 1]
    ).reshape((coords.shape[0], 3 * n, 3))  # rotations

    if nonlinear:
        freqs = np.concatenate([
            np.broadcast_to([[1e-14, 1e-14, 1e-14]], mom_rot.shape),
            (1 / (2 * mom_rot))
            # this isn't right, I'm totally aware, but I think the frequency is supposed to be zero anyway and this
            # will be tiny
        ], axis=-1)
        M = np.broadcast_to(M[np.newaxis], R.shape)
        eigs = np.concatenate([M, R], axis=2)
    elif all_linear:
        mom_rot = mom_rot[:, good_ax]
        freqs = np.concatenate([
            np.broadcast_to([[1e-14, 1e-14, 1e-14]], R.shape[:1] + (3,)),
            (1 / (2 * mom_rot))
            # this isn't right, I'm totally aware, but I think the frequency is supposed to be zero anyway and this
            # will be tiny
        ], axis=-1)
        R = R[:, :, good_ax]
        M = np.broadcast_to(M[np.newaxis], R.shape[:1] + M.shape)
        eigs = np.concatenate([M, R], axis=2)
    else:
        freqs = []
        eigs = []
        for sel, moms, rot in zip(good_ax, mom_rot, R):
            f = np.concatenate([[1e-14, 1e-14, 1e-14], 1/(2*mom_rot[sel,])])
            r = rot[:, sel]
            freqs.append(f)
            eigs.append(np.concatenate([M, r], axis=1))

    if not mass_weighted:
        W = np.diag(np.repeat(1/np.sqrt(masses), 3))
        eigs = np.moveaxis(np.tensordot(eigs, W, axes=[-2, 0]), -1, -2)

    if smol:
        eigs = eigs[0]
        freqs = freqs[0]
    else:
        eigs = eigs.reshape(base_shape + eigs.shape[1:])
        freqs = freqs.reshape(base_shape + freqs.shape[1:])

    return freqs, eigs

def translation_rotation_projector(coords, masses=None, mass_weighted=False, return_modes=False,
                                   orthonormal=True
                                   ):
    if masses is None:
        masses = np.ones(coords.shape[-2])
    _, tr_modes = translation_rotation_eigenvectors(coords, masses, mass_weighted=mass_weighted)
    if orthonormal:
        if not mass_weighted:
            tr_modes = vec_ops.vec_normalize(tr_modes, axis=0)
        projector = vec_ops.orthogonal_projection_matrix(tr_modes, orthonormal=True)
    else:
        shared = tr_modes.ndim - 2
        eye = vec_ops.identity_tensors(tr_modes.shape[:-2], tr_modes.shape[-2])
        projector = eye - vec_ops.vec_tensordot(tr_modes, tr_modes, axes=[-1, -1], shared=shared)

    if return_modes:
        return projector, tr_modes
    else:
        return projector


def remove_translation_rotations(expansion, coords, masses=None, mass_weighted=False):
    projector = translation_rotation_projector(coords, masses=masses, mass_weighted=mass_weighted)
    shared = projector.ndim - 2

    proj_expansion = []
    for n,d in enumerate(expansion):
        for ax in range(n+1):
            d = vec_ops.vec_tensordot(projector, d, axes=[-1, shared+ax], shared=shared)
        proj_expansion.append(d)

    return proj_expansion

def translation_rotation_invariant_transformation(
        coords, masses=None,
        mass_weighted=True,
        strip_embedding=True
):

    if masses is None:
        masses = np.ones(coords.shape[-2])

    A, L_tr = translation_rotation_projector(coords, masses, mass_weighted=True, return_modes=True)
    base_shape = A.shape[:-2]
    A = A.reshape((-1,) + A.shape[-2:])
    L_tr = L_tr.reshape((-1,) + L_tr.shape[-2:])
    evals, tf = np.linalg.eigh(A)
    zero_pos = np.abs(evals) < 1e-4# the rest should be 1
    zero_counts = np.sum(zero_pos, axis=1)
    ucounts = np.min(zero_counts)

    tf[:, :, :ucounts] = L_tr
    if strip_embedding:
        # nzpos = np.where(np.abs(evals) > 1e-4) # the rest should be 1
        # nzpos = nzpos[:-1] + (slice(None),) + nzpos[-1:]
        tf = tf[:, :, ucounts:]
    else:
        tf[:, :, :ucounts] = L_tr

    inv = np.moveaxis(tf, -1, -2)
    if not mass_weighted:
        W = np.diag(np.repeat(np.sqrt(masses), 3))
        tf = np.moveaxis(
            np.tensordot(W, tf, axes=[0, 1]),
            1, 0
        )

        W = np.diag(np.repeat(1/np.sqrt(masses), 3))
        inv = np.tensordot(inv, W, axes=[2, 0])

    tf = tf.reshape(base_shape + tf.shape[-2:])
    inv = inv.reshape(base_shape + inv.shape[-2:])

    return tf, inv

EmbeddingData = collections.namedtuple("PrincipleAxisData", ['coords', 'com', 'axes'])
EckartData = collections.namedtuple('EckartData', ['rotations', 'coordinates', 'reference_data', 'coord_data'])
def principle_axis_embedded_coords(coords, masses=None):
    """
    Returns coordinate embedded in the principle axis frame

    :param coords:
    :type coords:
    :param masses:
    :type masses:
    :return:
    :rtype:
    """
    com = center_of_mass(coords, masses)
    # crds_ = coords
    coords = coords - com[..., np.newaxis, :]
    moms, pax_axes = moments_of_inertia(coords, masses)
    # pax_axes = np.swapaxes(pax_axes, -2, -1)
    coords = np.matmul(coords, pax_axes)

    return EmbeddingData(coords, com, pax_axes)

def _prep_eckart_data(ref, coords, masses, in_paf=False, sel=None):

    if masses is None:
        masses = np.ones(coords.shape[-2])

    if coords.ndim == 2:
        coords = np.broadcast_to(coords, (1,) + coords.shape)

    if not in_paf:
        coords, com, pax_axes = principle_axis_embedded_coords(coords, masses)
        ref, ref_com, ref_axes = principle_axis_embedded_coords(ref, masses)
        # raise ValueError(ref)
    else:
        com = pax_axes = None
        ref_com = ref_axes = None

    og_coords = coords
    if sel is not None:
        coords = coords[..., sel, :]
        masses = masses[sel]
        ref = ref[..., sel, :]

    real_pos = masses > 0
    # print(real_pos)
    # og_coords = coords
    coords = coords[..., real_pos, :]
    masses = masses[real_pos,]
    og_ref = ref
    ref = ref[..., real_pos, :]

    if ref.ndim == 2:
        ref = ref[np.newaxis]
    if ref.shape[0] > 1 and ref.shape[0] < coords.shape[0]:  # TODO: make less hacky
        # need to make them broadcast together and we assume
        # we have an extra stack of coords
        n_sys = coords.shape[0]
        ref = np.reshape(
            np.broadcast_to(
                ref[np.newaxis],
                (n_sys // ref.shape[0],) + ref.shape
            ),
            (n_sys,) + ref.shape[1:]
        )
        ref_axes = np.reshape(
            np.broadcast_to(
                ref_axes[np.newaxis],
                (n_sys // ref_axes.shape[0],) + ref_axes.shape
            ),
            (n_sys,) + ref_axes.shape[1:]
        )
        ref_com = np.reshape(
            np.broadcast_to(
                ref_com[np.newaxis],
                (n_sys // ref_com.shape[0],) + ref_com.shape
            ),
            (n_sys,) + ref_com.shape[1:]
        )

    return (ref, ref_com, ref_axes), (coords, com, pax_axes), masses, (og_ref, og_coords)

def _eckart_embedding(ref, coords,
                      masses=None,
                      sel=None,
                      in_paf=False,
                      planar_ref_tolerance=1e-6,
                      proper_rotation=False,
                      permutable_groups=None,
                      transform_coordinates=True
                      ):
    """
    Generates the Eckart rotation that will align ref and coords, assuming initially that `ref` and `coords` are
    in the principle axis frame

    :param masses:
    :type masses:
    :param ref:
    :type ref:
    :param coords:
    :type coords: np.ndarray
    :return:
    :rtype:
    """

    coords = np.asanyarray(coords)
    og_og_coords = coords
    ref = np.asanyarray(ref)
    og_og_ref = ref

    (ref, ref_com, ref_axes), (coords, com, pax_axes), masses, (og_ref, og_coords) = _prep_eckart_data(
        ref, coords, masses,
        sel=sel, in_paf=in_paf
    )

    # needs to be updated for the multiple reference case?
    # TODO: make sure that we broadcast this correctly to check if all or
    #       none of the reference structures are planar
    planar_ref = np.allclose(ref[0][:, 2], 0., atol=planar_ref_tolerance)

    if permutable_groups is not None:
        if sel is not None:
            reindexing = {a:i for i,a in enumerate(sel)}
            permutable_groups = [
                [reindexing[a] for a in g if a in reindexing]
                for g in permutable_groups
            ]
            permutable_groups = [g for g in permutable_groups if len(g) > 1]
        rem_atoms = np.delete(np.arange(len(masses)), np.concatenate(permutable_groups))
        permutable_groups = list(permutable_groups) + rem_atoms[:, np.newaxis].tolist()
    if not planar_ref:
        # generate pair-wise product matrix
        if permutable_groups is None:
            A = np.tensordot(
                masses / np.sum(masses),
                ref[:, :, :, np.newaxis] * coords[:, :, np.newaxis, :],
                axes=[0, 1]
            )
        else:
            mw_scaling = np.expand_dims(np.sqrt(masses) / np.sum(masses), [0, 2])
            mw_ref = ref * mw_scaling
            mw_coords = coords * mw_scaling
            A = sum(
                np.sum(
                    mw_ref[:, g, :, np.newaxis],
                    mw_coords[:, g, np.newaxis, :],
                    axis=1
                ) for g in permutable_groups
            )
        # take SVD of this
        U, S, V = np.linalg.svd(A)
        rot = np.matmul(U, V)
        if proper_rotation:
            dets = np.linalg.det(rot)
            inversions = np.where(dets < 0)
            V[inversions, :, 2] *= -1
            rot = np.matmul(U, V)

    else:
        # generate pair-wise product matrix but only in 2D
        if permutable_groups is None:
            F = ref[:, :, :2, np.newaxis] * coords[:, :, np.newaxis, :2]
            A = np.tensordot(masses / np.sum(masses), F, axes=[0, 1])
        else:
            mw_scaling = np.expand_dims(np.sqrt(masses) / np.sum(masses), [0, 2])
            mw_ref = ref * mw_scaling
            mw_coords = coords * mw_scaling
            A = sum(
                np.sum(
                    mw_ref[:, g, :2, np.newaxis],
                    mw_coords[:, g, np.newaxis, :2],
                    axis=1
                ) for g in permutable_groups
            )

        U, S, V = np.linalg.svd(A)
        base_rot = np.matmul(U, V)
        if proper_rotation:
            dets = np.linalg.det(base_rot)
            inversions = np.where(dets < 0)
            V[inversions, :, 1] *= -1
            base_rot = np.matmul(U, V)

        rot = np.broadcast_to(np.eye(3, dtype=float), (len(coords), 3, 3)).copy()
        rot[..., :2, :2] = base_rot

    if transform_coordinates:
        # crd is in _its_ principle axis frame, so now we transform it using ek_rot
        ek_rot = np.swapaxes(rot, -2, -1)
        coords = og_coords @ ek_rot
        # now we rotate this back to the reference frame
        coords = coords @ np.swapaxes(ref_axes if ref_axes.ndim > 2 else ref_axes[np.newaxis], -2, -1)
        # and then shift so the COM doesn't change
        coords = coords + (ref_com if ref_com.ndim > 1 else ref_com[np.newaxis, np.newaxis, :])
    else:
        coords = None

    base_coord_shape = og_og_coords.shape[:-2]
    coords = coords.reshape(base_coord_shape + coords.shape[-2:])
    og_coords = og_coords.reshape(base_coord_shape + og_coords.shape[-2:])
    com = com.reshape(base_coord_shape + com.shape[-1:])
    pax_axes = pax_axes.reshape(base_coord_shape + pax_axes.shape[-2:])
    rot = rot.reshape(base_coord_shape + rot.shape[-2:])
    base_ref_shape = og_og_ref.shape[:-2]
    og_ref = og_ref.reshape(base_ref_shape + og_ref.shape[-2:])
    ref_com = ref_com.reshape(base_ref_shape + ref_com.shape[-1:])
    ref_axes = ref_axes.reshape(base_ref_shape + ref_axes.shape[-2:])
    return EckartData(
        rot,
        coords,
        EmbeddingData(og_ref, ref_com, ref_axes),
        EmbeddingData(og_coords, com, pax_axes)
    )

def eckart_embedding(ref, coords,
                     masses=None,
                     sel=None,
                     in_paf=False,
                     planar_ref_tolerance=1e-6,
                     proper_rotation=False,
                     permutable_groups=None,
                     transform_coordinates=True):
    # if permutable_groups is None:
    return _eckart_embedding(
        ref, coords,
        masses=masses,
        sel=sel,
        in_paf=in_paf,
        planar_ref_tolerance=planar_ref_tolerance,
        proper_rotation=proper_rotation,
        permutable_groups=permutable_groups,
        transform_coordinates=transform_coordinates
    )
rmsd_minimizing_transformation = eckart_embedding

def eckart_permutation(
        ref, coords,
        masses=None,
        sel=None,
        in_paf=False,
        prealign=False,
        planar_ref_tolerance=1e-6,
        proper_rotation=False,
        permutable_groups=None
):

    ref = np.asanyarray(ref)
    og_og_ref = ref
    coords = np.asanyarray(coords)
    og_og_coords = coords
    if prealign:
        embedding_data = eckart_embedding(ref, coords,
                                          masses=masses,
                                          sel=sel,
                                          in_paf=in_paf,
                                          planar_ref_tolerance=planar_ref_tolerance,
                                          proper_rotation=proper_rotation,
                                          permutable_groups=permutable_groups)
        # ref = embedding_data.reference_data.coords
        coords = embedding_data.coordinates

    (ref, ref_com, ref_axes), (coords, com, pax_axes), masses, (og_ref, og_coords) = _prep_eckart_data(
        ref, coords, masses,
        sel=sel, in_paf=True
    )

    mw_scaling = np.expand_dims(np.sqrt(masses) / np.sum(masses), [0, 2])
    mw_ref = ref * mw_scaling
    # mw_coords = coords * mw_scaling

    if permutable_groups is not None:
        if sel is not None:
            reindexing = {a: i for i, a in enumerate(sel)}
            permutable_groups = [
                [reindexing[a] for a in g if a in reindexing]
                for g in permutable_groups
            ]
            permutable_groups = [g for g in permutable_groups if len(g) > 1]
        rem_atoms = np.delete(np.arange(len(masses)), np.concatenate(permutable_groups))
        permutable_groups = list(permutable_groups) + rem_atoms[:, np.newaxis].tolist()
    else:
        permutable_groups = [np.arange(mw_ref.shape[-2])]

    base_perm = np.repeat(np.arange(og_ref.shape[-2])[np.newaxis], ref.shape[0], axis=0)
    if sel is not None:
        perm = base_perm[:, sel]
    else:
        perm = base_perm
    base_shape = ref.shape[:-2]
    for p in permutable_groups:
        sub_data = eckart_embedding(ref, coords,
                                    masses=masses,
                                    sel=p,
                                    in_paf=in_paf,
                                    planar_ref_tolerance=planar_ref_tolerance,
                                    proper_rotation=proper_rotation,
                                    permutable_groups=[p])
        mw_coords = sub_data.coordinates * mw_scaling

        p = np.asanyarray(p)
        n = len(p)
        dists = np.zeros(base_shape + (n, n))
        rows, cols = np.triu_indices(n, k=0)
        dist_triu = np.linalg.norm(
            mw_coords[..., rows, :] - mw_ref[..., p[cols], :],
            axis=-1
        )
        dists[..., rows, cols] = dist_triu
        dists[..., cols, rows] = dist_triu

        for k,cost in enumerate(dists):
            _, sub_perm = opt.linear_sum_assignment(cost)
            perm[k][p] = p[sub_perm]
    if sel is not None:
        base_perm[:, sel] = perm

    targ_shape = og_og_coords.shape[:-2]
    return base_perm.reshape(targ_shape + (-1,))


def eckart_displacement_coords(coords, ref, masses=None, **embedding_parameters):
    ref_embedding, _ = translation_rotation_invariant_transformation(ref,
                                                                  masses=masses,
                                                                  mass_weighted=False
                                                                  )
    base_embedding = eckart_embedding(ref, coords, masses=masses, **embedding_parameters)
    return np.reshape(
        ref_embedding @ base_embedding.coordinates[..., np.newaxis],
        base_embedding.coordinates.shape
    )

