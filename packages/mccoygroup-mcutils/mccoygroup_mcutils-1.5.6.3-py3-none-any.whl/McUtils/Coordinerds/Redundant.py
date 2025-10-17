import itertools

import numpy as np
import collections

from .. import Numputils as nput

__all__ = [
    "RedundantCoordinateGenerator"
]


class RedundantCoordinateGenerator:

    def __init__(self,
                 coordinate_specs, angle_ordering='ijk',
                 untransformed_coordinates=None, masses=None,
                 relocalize=False,
                 **opts):
        self.specs = coordinate_specs
        self.untransformed_coordinates = untransformed_coordinates
        self.relocalize = relocalize
        self.masses = masses
        self.opts = dict(
            opts,
            angle_ordering=angle_ordering
        )

    @classmethod
    def _pad_redund_tf(cls, redund_tf, n):
        ndim = redund_tf.ndim - 2
        eye = nput.identity_tensors(redund_tf.shape[:-2], n)
        return np.concatenate(
            [
                np.pad(eye, ([[0, 0]] * ndim) + [[0, redund_tf.shape[-2]], [0, 0]]),
                np.pad(redund_tf, ([[0, 0]] * ndim) + [[n, 0], [0, 0]])
            ],
            axis=-1
        )

    @classmethod
    def _relocalize_tf(cls, redund_tf, untransformed_coordinates=None):
        n = redund_tf.shape[-1]
        if untransformed_coordinates is None:
            # target = np.pad(np.eye(n), [[0, 173 - 108], [0, 0]])
            ndim = redund_tf.ndim - 2
            eye = nput.identity_tensors(redund_tf.shape[:-2], n)
            target = np.pad(eye, ([[0, 0]] * ndim) + [[0, redund_tf.shape[-2] - n], [0, 0]])
        else:
            untransformed_coordinates = np.asanyarray(untransformed_coordinates)
            coords = np.concatenate([
                untransformed_coordinates,
                np.delete(np.arange(redund_tf.shape[-2]), untransformed_coordinates)
                ])[:n]
            target = np.moveaxis(np.zeros(redund_tf.shape), -1, -2)
            idx = nput.vector_ix(target.shape[:-1], coords[:, np.newaxis])
            target[idx] = 1
            target = np.moveaxis(target, -1, -2)
        loc = np.linalg.lstsq(redund_tf, target, rcond=None)
        U, s, V = np.linalg.svd(loc[0])
        R = U @ V
        return redund_tf @ R


    @classmethod
    def base_redundant_transformation(cls, expansion,
                                      untransformed_coordinates=None,
                                      masses=None,
                                      relocalize=False
                                      ):
        conv = np.asanyarray(expansion[0])
        if masses is not None:
            masses = np.asanyarray(masses)
            if len(masses) == conv.shape[-2] // 3:
                masses = np.repeat(masses, 3)
            masses = np.diag(1 / np.sqrt(masses))
            if conv.ndim > 2:
                masses = np.broadcast_to(
                    np.expand_dims(masses, list(range(conv.ndim - 2))),
                    conv.shape[:-2] + masses.shape
                )
            conv = masses @ conv

        if untransformed_coordinates is not None:
            transformed_coords = np.setdiff1d(np.arange(conv.shape[-1]), untransformed_coordinates)
            ut_conv = conv[..., untransformed_coordinates]
            conv = conv[..., transformed_coords]

            # project out contributions along untransformed coordinates to ensure
            # dimension of space remains unchanged
            ut_conv_norm = nput.vec_normalize(np.moveaxis(ut_conv, -1, -2))
            proj = np.moveaxis(ut_conv_norm, -1, -2) @ ut_conv_norm
            proj = nput.identity_tensors(proj.shape[:-2], proj.shape[-1]) - proj

            conv = np.concatenate([ut_conv, proj @ conv], axis=-1)

        G_internal = np.moveaxis(conv, -1, -2) @ conv
        redund_vals, redund_tf = np.linalg.eigh(G_internal)
        redund_pos = np.where(np.abs(redund_vals) > 1e-10)
        if redund_vals.ndim > 1:
            redund_tf = nput.take_where_groups(redund_tf, redund_pos)
        else:
            redund_tf = redund_tf[:, redund_pos[0]]
        if isinstance(redund_tf, np.ndarray):
            redund_tf = np.flip(redund_tf, axis=-1)
        else:
            redund_tf = [
                np.flip(tf, axis=-1)
                for tf in redund_tf
            ]

        # if transformed_coords is not None:
        #     n = len(untransformed_coordinates)
        #     if isinstance(redund_tf, np.ndarray):
        #         redund_tf = cls._pad_redund_tf(redund_tf, n)
        #     else:
        #         redund_tf = [
        #             cls._pad_redund_tf(tf, n)
        #             for tf in redund_tf
        #         ]

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
            # provide some facility for rearranging coords?
            if isinstance(redund_tf, np.ndarray):
                redund_tf = cls._relocalize_tf(redund_tf, untransformed_coordinates=untransformed_coordinates)
            else:
                redund_tf = [
                    cls._relocalize_tf(tf, untransformed_coordinates=untransformed_coordinates)
                    for tf in redund_tf
                ]



        return redund_tf


    @classmethod
    def get_redundant_transformation(cls, base_expansions, untransformed_coordinates=None, masses=None,
                                     relocalize=False):
        if isinstance(base_expansions, np.ndarray) and base_expansions.ndim == 2:
            base_expansions = [base_expansions]
            base_inv = None
        elif (
                len(base_expansions) == 2
                and not nput.is_numeric_array_like(base_expansions[0], ndim=2)
        ):
            base_expansions, base_inv = base_expansions
        else:
            base_inv = None
        redund_tf = cls.base_redundant_transformation(base_expansions,
                                                      untransformed_coordinates=untransformed_coordinates,
                                                      masses=masses,
                                                      relocalize=relocalize
                                                      )

        # dQ/dR, which we can transform with dR/dX to get dQ/dX
        if isinstance(redund_tf, np.ndarray):
            redund_expansions = nput.tensor_reexpand(base_expansions, [redund_tf], order=len(base_expansions))
            if base_inv is not None:
                redund_inv = nput.tensor_reexpand([redund_tf.T], base_inv, order=len(base_inv))
                redund_expansions = (redund_expansions, redund_inv)
        else:
            redund_expansions = [
                nput.tensor_reexpand(base_expansions, [tf], order=len(base_expansions))
                for tf in redund_tf
            ]
            if base_inv is not None:
                redund_inv = [
                    nput.tensor_reexpand([tf.T], base_inv, order=len(base_inv))
                    for tf in redund_tf
                ]
                redund_expansions = (redund_expansions, redund_inv)

        return redund_tf, redund_expansions

    def compute_redundant_expansions(self,
                                     coords,
                                     order=None,
                                     untransformed_coordinates=None,
                                     expansions=None,
                                     relocalize=None):
        coords = np.asanyarray(coords)
        if order is None:
            opts = dict(dict(order=1), **self.opts)
        else:
            opts = dict(self.opts, order=order)
        if untransformed_coordinates is None:
            untransformed_coordinates = self.untransformed_coordinates
        if relocalize is None:
            relocalize = self.relocalize
        if expansions is None:
            base_expansions = nput.internal_coordinate_tensors(coords, self.specs, **opts)[1:]
        else:
            base_expansions = expansions
        return self.get_redundant_transformation(base_expansions,
                                                 untransformed_coordinates=untransformed_coordinates,
                                                 masses=self.masses,
                                                 relocalize=relocalize
                                                 )

    @classmethod
    def _prune_coords_svd(cls, b_mat, svd_cutoff=5e-2, sort=True, fixed_vecs=None):
        # turns out, equivalent to finding maximimum loc in eigenvectors of G
        if fixed_vecs is not None:
            transformed_coords = np.delete(np.arange(b_mat.shape[-1]), fixed_vecs)
            ut_conv = b_mat[..., fixed_vecs]
            conv = b_mat[..., transformed_coords]

            # project out contributions along untransformed coordinates to ensure
            # dimension of space remains unchanged
            ut_conv = nput.vec_normalize(ut_conv)
            proj = ut_conv @ np.moveaxis(ut_conv, -1, -2)
            proj = nput.identity_tensors(proj.shape[:-2], proj.shape[-1]) - proj

            b_mat = proj @ conv

        _, s, Q = np.linalg.svd(b_mat)
        pos = np.where(s > 1e-8)
        loc_val = np.max(Q[pos]**2, axis=0)
        coords = np.where(loc_val > svd_cutoff)[0]
        if sort:
            coords = coords[np.argsort(-loc_val[coords,],)]
        if fixed_vecs is not None:
            coords = transformed_coords[coords,]
            coords = np.concatenate([fixed_vecs, coords])
        return coords

    @classmethod
    def _prune_coords_loc(cls, b_mat, loc_cutoff=.33, sort=True, fixed_vecs=None):
        # if fixed_vecs is not None:
        #     transformed_coords = np.delete(np.arange(b_mat.shape[-1]), fixed_vecs)
        #     ut_conv = b_mat[..., fixed_vecs]
        #     b_mat = b_mat[..., transformed_coords]
        #
        #     # # project out contributions along untransformed coordinates to ensure
        #     # # dimension of space remains unchanged
        #     # ut_conv = nput.vec_normalize(ut_conv)
        #     # proj = ut_conv @ np.moveaxis(ut_conv, -1, -2)
        #     # proj = nput.identity_tensors(proj.shape[:-2], proj.shape[-1]) - proj
        #     #
        #     # b_mat = proj @ conv

        s, Q = np.linalg.eigh(b_mat.T @ b_mat)
        pos = np.where(s > 1e-8)[0]
        Q = Q[:, pos]
        loc_mat = np.linalg.lstsq(Q, np.eye(Q.shape[-2]), rcond=None)
        loc_val = np.diag(Q @ loc_mat[0])
        coords = np.where(loc_val > loc_cutoff)[0]
        if fixed_vecs is not None:
            coords = np.setdiff1d(coords, fixed_vecs)
        if sort:
            coords = coords[np.argsort(-loc_val[coords,], )]
        if fixed_vecs is not None:
            coords = np.concatenate([fixed_vecs, coords])

            # have to run this back again in case these added coords break the localization
            # a third run back isn't work it since that will just repeat what's found here
            b_mat = b_mat[:, coords]
            s, Q = np.linalg.eigh(b_mat.T @ b_mat)
            pos = np.where(s > 1e-8)[0]
            Q = Q[:, pos]
            loc_mat = np.linalg.lstsq(Q, np.eye(Q.shape[-2]), rcond=None)
            loc_val = np.diag(Q @ loc_mat[0])
            subcoords = np.setdiff1d(np.where(loc_val > loc_cutoff)[0], np.arange(len(fixed_vecs)))
            if sort:
                subcoords = subcoords[np.argsort(-loc_val[subcoords,], )]
            coords = np.concatenate([coords[:len(fixed_vecs)], coords[subcoords]])

        return coords

    @classmethod
    def _prune_coords_gs(cls, b_mat, fixed_vecs=None, core_scaling=1e3, max_condition_number=1e8):
        if fixed_vecs is None:
            _, s, Q = np.linalg.svd(b_mat)
            pos = np.where(s > 0)
            fixed_vecs = np.where(np.linalg.norm(Q[pos], axis=0) > .9)[0]
        fixed_vecs = np.array(fixed_vecs)
        core_mask = np.full(b_mat.shape[1], False)
        core_mask[fixed_vecs] = True
        all_mask = core_mask.copy()
        rem_pos = np.setdiff1d(np.arange(b_mat.shape[1]), fixed_vecs)
        base_evals = np.linalg.eigvalsh(b_mat[:, core_mask].T @ b_mat[:, core_mask])
        base_cond = base_evals[-1] / base_evals[0] * core_scaling
        for r in rem_pos:
            core_mask[r] = True
            evals = np.linalg.eigvalsh(b_mat[:, core_mask].T @ b_mat[:, core_mask])
            new_cond = abs(evals[-1] / evals[0])
            if new_cond < max_condition_number:
                all_mask[r] = True
                if new_cond > base_cond:
                    core_mask[r] = False
            else:
                core_mask[r] = False

        return np.where(all_mask)[0]

    @classmethod
    def prune_coordinate_specs(cls, expansion,
                               masses=None,
                               untransformed_coordinates=None,
                               pruning_mode='loc',
                               **opts
                               ):
        conv = np.asanyarray(expansion[0])
        masses = np.asanyarray(masses)
        if len(masses) == conv.shape[-2] // 3:
            masses = np.repeat(masses, 3)
        masses = np.diag(1 / np.sqrt(masses))
        b_mat = masses @ conv

        if pruning_mode == 'svd':
            return cls._prune_coords_svd(b_mat, fixed_vecs=untransformed_coordinates, **opts)
        elif pruning_mode == 'loc':
            return cls._prune_coords_loc(b_mat, fixed_vecs=untransformed_coordinates, **opts)
        elif pruning_mode == 'gs':
            return cls._prune_coords_gs(b_mat, fixed_vecs=untransformed_coordinates, **opts)
        else:
            raise ValueError(f"don't understand pruning mode {pruning_mode}")

class MultiOriginCoordinates:

    def __init__(self, origins, zmats):
        ...

