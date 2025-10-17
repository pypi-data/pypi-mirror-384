from .CoordinateSystemConverter import CoordinateSystemConverter
from .CommonCoordinateSystems import CartesianCoordinates3D, ZMatrixCoordinates
from ...Numputils import vec_norms, vec_angles, vec_dihedrals, pts_dihedrals, dist_deriv, angle_deriv, dihed_deriv, find
from ...Scaffolding import MaxSizeCache
import numpy as np
# this import gets bound at load time, so unfortunately PyCharm can't know just yet
# what properties its class will have and will try to claim that the files don't exist

class CartesianToZMatrixConverter(CoordinateSystemConverter):
    """
    A converter class for going from Cartesian coordinates to ZMatrix coordinates
    """

    @property
    def types(self):
        return (CartesianCoordinates3D, ZMatrixCoordinates)

    @staticmethod
    def get_dists(points, centers, return_diffs=False):
        diffs = centers-points
        ret = vec_norms(diffs)
        if return_diffs:
            ret = (ret, diffs)
        return ret
    @staticmethod
    def get_angles(lefts, centers, rights, norms=None):
        # need to look up again what the convention is for which atom is the central one...
        if rights is None:
            v1s = lefts
            v2s = centers
        else:
            v1s = centers-lefts
            v2s = centers-rights
        return vec_angles(v1s, v2s, norms=norms, return_crosses=True, return_norms=False)
    @staticmethod
    def get_diheds(points, centers, seconds, thirds, crosses=None, norms=None):
        if thirds is None:
            return vec_dihedrals(points, centers, seconds,
                                 crosses=crosses,
                                 norms=norms
                                 )
        else:
            return pts_dihedrals(points, centers, seconds, thirds, crosses=crosses, norms=norms)

    def convert_many(self, coords, ordering=None, use_rad=True, return_derivs=False, **kw):
        """
        We'll implement this by having the ordering arg wrap around in coords?
        """
        if ordering is None:
            ordering = range(len(coords[0]))
        base_shape = coords.shape
        new_coords = np.reshape(coords, (np.prod(base_shape[:-1]),) + base_shape[-1:])
        new_coords, ops = self.convert(new_coords, ordering=ordering, use_rad=use_rad, return_derivs=return_derivs)
        single_coord_shape = (base_shape[-2]-1, new_coords.shape[-1])
        new_shape = base_shape[:-2] + single_coord_shape
        new_coords = np.reshape(new_coords, new_shape)
        if return_derivs:
            ders = ops['derivs']
            # we assume we get a list of derivatives?
            reshaped_ders = [None]*len(ders)
            for i, v in enumerate(ders):
                single_base_shape = (base_shape[-2], new_coords.shape[-1])
                ders_shape = coords.shape + single_base_shape*i + single_coord_shape
                v = v.reshape(ders_shape)
                reshaped_ders[i] = v
                ops['derivs'] = reshaped_ders
        return new_coords, ops

    @staticmethod
    def _get_conversion_info(ncoords, ordering, canonicalize):
        if canonicalize:
            orig_ol = ZMatrixCoordinates.canonicalize_order_list(ncoords, ordering)
        else:
            orig_ol = ordering
        ol = orig_ol
        nol = len(ol)
        ncol = len(ol[0])

        return ol, nol, ncol

    @staticmethod
    def _build_ordering_list(multiconfig, ol, ncoords):
        if multiconfig:
            ol = ZMatrixCoordinates.tile_order_list(ol, ncoords)
            mc_ol = ol.copy()
        else:
            mc_ol = None

        # we define an order map that we'll index into to get the new indices for a
        # given coordinate
        om = 1+np.argsort(ol[:, 0])

        return ol, om, mc_ol

    @staticmethod
    def _get_dist_inds(mask, ol, nol):
        subs = ol.reshape(-1, nol, 4)[:, 1:].reshape(-1, 4)
        # subs = ol[mask]
        ix = subs[:, 0]
        jx = subs[:, 1]
        return ix, jx
    def _get_cached_dist_inds(self, ol_key, ncoords, ol, nol):
        if (ol_key, ncoords) in self._index_cache:
            idx_list = self._index_cache[(ol_key, ncoords)]
        else:
            # mask = np.arange(ncoords).reshape(-1, nol)[:, 1:].flatten()
            # mask = np.setdiff1d(np.arange(ncoords), np.arange(0, ncoords, nol))
            # raise Exception((mask_1 == mask).all())
            ix, jx = self._get_dist_inds(None, ol, nol)
            idx_list = [[ix, jx]]
            self._index_cache[(ol_key, ncoords)] = idx_list
        return idx_list

    def _get_cached_norms(self, distance_matrix, coords, ix, jx):
        target_norms_1 = distance_matrix[ix, jx]
        bad_norms_1 = np.where(target_norms_1 == 0)
        if len(bad_norms_1) > 0 and len(bad_norms_1[0]) > 0:
            bad_ix = ix[bad_norms_1]
            bad_jx = jx[bad_norms_1]
            bad_dists = self.get_dists(coords[bad_ix], coords[bad_jx])
            distance_matrix[bad_ix, bad_jx] = bad_dists
            distance_matrix[bad_jx, bad_ix] = bad_dists
            target_norms_1[bad_norms_1] = distance_matrix[bad_ix]
        return target_norms_1

    @staticmethod
    def _get_angle_inds(mask, ol, nol):
        subs = ol.reshape(-1, nol, 4)[:, 2:].reshape(-1, 4)
        # subs = ol[mask]
        ix = subs[:, 0]
        jx = subs[:, 1]
        kx = subs[:, 2]

        return ix, jx, kx
    def _get_cached_angle_inds(self, idx_list, mask, ncoords, ol, nol):
        if len(idx_list) < 2:
            # mask = mask.reshape(-1, nol-1)[:, 1:].flatten()
            # mask = np.delete(mask, np.arange(0, len(mask), nol-1))
            # mask = np.setdiff1d(mask, np.arange(1, ncoords, nol))
            # raise Exception(np.all(mask_1 == mask))
            ix, jx, kx = self._get_angle_inds(None, ol, nol)
            idx_list.append([ix, jx, kx])
        return idx_list

    def _get_angles_cached(self, distance_matrix, cross_mat, cross_norms, coords, ix, jx, kx):
        norms_1 = self._get_cached_norms(distance_matrix, coords, ix, jx)
        norms_2 = self._get_cached_norms(distance_matrix, coords, kx, jx)
        angles, crosses = self.get_angles(
            coords[ix], coords[jx], coords[kx],
            norms=[norms_1, norms_2]
        )
        cross_mat[ix, jx, kx] = crosses
        cross_mat[kx, jx, ix] = -crosses
        cnorms = vec_norms(crosses)
        cross_norms[ix, jx, kx] = cnorms
        cross_norms[kx, ix, jx] = cnorms
        return angles
    def _get_cached_crosses(self, distance_matrix, cross_mat, cross_norms, coords, ix, jx, kx):
        target_norms = cross_norms[ix, jx, kx]
        bad_norms = np.where(target_norms == 0)
        if len(bad_norms) > 0 and len(bad_norms[0]) > 0:
            bad_ix = ix[bad_norms]
            bad_jx = jx[bad_norms]
            bad_kx = kx[bad_norms]
            self._get_angles_cached(distance_matrix, cross_mat, cross_norms, coords, bad_ix, bad_jx, bad_kx)
        return cross_mat[ix, jx, kx], cross_norms[ix, jx, kx] # recalculated in the angles_cached call

    @staticmethod
    def _get_dihed_inds(mask, ol, nol):
        subs = ol.reshape(-1, nol, 4)[:, 3:].reshape(-1, 4)
        ix = subs[:, 0]
        jx = subs[:, 1]
        kx = subs[:, 2]
        lx = subs[:, 3]

        return ix, jx, kx, lx
    def _get_cached_dihed_inds(self, idx_list, mask, ncoords, ol, nol):
        if len(idx_list) < 3:
            # mask = np.setdiff1d(mask, np.arange(2, ncoords, nol))
            # mask = np.delete(mask, np.arange(0, len(mask), nol-2))
            # mask = mask.reshape(-1, nol-2)[:, 1:].flatten()
            ix, jx, kx, lx = self._get_dihed_inds(None, ol, nol)
            idx_list.append([ix, jx, kx, lx])
        return idx_list

    @staticmethod
    def _restructure_angles(angles, ncoords, steps, nol, use_rad):
        angles = np.append(angles, np.zeros(steps))
        insert_pos = np.arange(0, ncoords - 1 * steps - 1, nol - 2)
        angles = np.insert(angles, insert_pos, 0)
        angles = angles[:ncoords - steps]
        if not use_rad:
            angles = np.rad2deg(angles)
        return angles

    @staticmethod
    def _restructure_diheds(diheds, ncoords, steps, nol, use_rad):
        # pad diheds to be the size of ncoords
        diheds = np.append(diheds, np.zeros(2 * steps))

        # insert zeros where undefined
        diheds = np.insert(diheds, np.repeat(np.arange(0, ncoords - 2 * steps - 1, nol - 3), 2), 0)
        # take only as many as actually used
        diheds = diheds[:ncoords - steps]
        if not use_rad:
            diheds = np.rad2deg(diheds)
        return diheds

    @staticmethod
    def _build_post_ordering_lists(ol, om, ncoords, nol, ncol, steps):
        mask = np.full(ncoords, True)
        mask[np.arange(0, ncoords, nol)] = False
        ol = np.reshape(ol[mask], (steps, nol - 1, ncol)) - np.reshape(np.arange(steps), (steps, 1, 1))
        ol = np.reshape(ol, (ncoords - steps, ncol))
        om = np.reshape(om[mask], (steps, nol - 1)) - nol * np.reshape(np.arange(steps), (steps, 1)) - 1
        om = np.reshape(om, (ncoords - steps,))
        return ol, om

    @staticmethod
    def _build_coord_triples(dists, angles, diheds):
        return np.concatenate(
            [
                dists.reshape(-1, 1),
                angles.reshape(-1, 1),
                diheds.reshape(-1, 1)
            ],
            axis=-1
        )

    @staticmethod
    def _rebuild_ordering(ncol, ol, om):
        om = om - 1
        if ncol == 5:
            ordering = np.array([
                        np.argsort(ol[:, 0]), om[ol[:, 1]], om[ol[:, 2]], om[ol[:, 3]], ol[:, 4]
                    ]).T
        else:
            ordering = np.array([
                    np.argsort(ol[:, 0]), om[ol[:, 1]], om[ol[:, 2]], om[ol[:, 3]]
                ]).T
        return ordering

    @staticmethod
    def _compute_final_frame(multiconfig, coords, mc_ol, nol, ol):
        if multiconfig:
            # figure out what to use for the axes
            origins = coords[mc_ol[1::nol,  1]]
            x_axes  = coords[mc_ol[1::nol,  0]] - origins # the first displacement vector
            y_axes  = coords[mc_ol[2::nol,  0]] - origins # the second displacement vector (just defines the x-y plane, not the real y-axis)
            axes = np.array([x_axes, y_axes]).transpose((1, 0, 2))
        else:
            origins = coords[ol[0, 1]]
            axes = np.array([coords[ol[0, 0]] - origins, coords[ol[1, 0]] - origins])
        return origins, axes

    def _convert_multiconfig(self, coords, ol, om, orig_ol, ncoords, nol, ncol, steps, use_rad, return_derivs, derivs):

        # we do all of this stuff with masking operations in the multiconfiguration cases
        # ...except the mask was too slow so now we don't...
        if return_derivs:
            raise NotImplementedError(...)

        ol_key = tuple(tuple(o) for o in orig_ol)
        idx_list = self._get_cached_dist_inds(ol_key, ncoords, ol, nol)
        ix, jx = idx_list[0]
        # dupe over number of structures
        dist_pos = [[ix, jx]]
        num_dists = len(ix)
        if nol > 2:
            idx_list = self._get_cached_angle_inds(idx_list, None, ncoords, ol, nol)
            ix, jx, kx = idx_list[1] # mask
            num_angles = len(ix)

            dist_pos = dist_pos + [[jx, kx]]
            cross_pos = [[ix, jx, kx]]
            if nol > 3:
                idx_list = self._get_cached_dihed_inds(idx_list, None, ncoords, ol, nol)
                # mask[np.arange(2, ncoords, nol)] = 0
                ix, jx, kx, lx = idx_list[2]
                # raise Exception(
                #     [ix, dist_pos[0][0]],
                #     [jx, dist_pos[0][1]]
                # )
                if ol.shape[1] == 5:
                    raise ValueError("Unclear if there is a difference between tau and psi")
                    ix = ix.copy()
                    jx = jx.copy()
                    kx = kx.copy()
                    lx = lx.copy()
                    fx = ol[mask, 4]
                    swap_pos = np.where(fx == 1)
                    swap_i = ix[swap_pos]
                    swap_j = jx[swap_pos]
                    swap_k = kx[swap_pos]
                    swap_l = lx[swap_pos]
                    ix[swap_pos] = swap_l
                    jx[swap_pos] = swap_i
                    kx[swap_pos] = swap_j
                    lx[swap_pos] = swap_k
                dist_pos = dist_pos + [[kx, lx]]
                if len(idx_list) < 4:
                    all_dist_inds = np.concatenate(
                            [
                                np.concatenate([x[:, np.newaxis] for x in dlist], axis=-1)
                                for dlist in dist_pos
                            ],
                            axis=0
                        )
                    ud_inds, ud_inv = np.unique(
                        all_dist_inds,
                        axis=0,
                        # return_index=True,
                        return_inverse=True
                    )
                    # ud_sorting = np.argsort(ud_pos)
                    # ud_inv_sort = np.argsort(ud_sorting)
                    # ud_pos = ud_pos[ud_sorting]
                    # ud_inv = ud_inv_sort[ud_inv]
                    idx_list.append([ud_inds, ud_inv])

                cross_pos = cross_pos + [[jx, kx, lx]]
                if len(idx_list) < 5:
                    all_cross_pos = np.concatenate(
                        [
                            np.concatenate([x[:, np.newaxis] for x in clist], axis=-1)
                            for clist in cross_pos
                        ],
                        axis=0
                    )

                    # determine which unique cross products we need to calculate
                    # and make sure they remain sorted so we can just take the first chunks
                    uc_inds, uc_inv = np.unique(
                        all_cross_pos,
                        axis=0,
                        # return_index=True,
                        return_inverse=True
                    )

                    # uc_sorting = np.argsort(uc_pos)
                    # uc_inv_sort = np.argsort(uc_sorting)
                    # uc_pos = uc_pos[uc_sorting]
                    # uc_inv = uc_inv_sort[uc_inv]

                    # now we map these onto the corresponding distance positions

                    # raise Exception(
                    #     all_dist_inds[:5],
                    #     ud_inds_sorted[:5],
                    #     all_cross_pos[:5, (0, 1)]
                    # )
                    v1_map, _ = find(
                        ud_inds,
                        uc_inds[:, (0, 1)],
                        sorting='sorted',
                        search_space_sorting=[
                            np.arange(len(uc_inds)),
                            np.arange(len(uc_inds))
                        ]
                    )
                    v2_map, _ = find(
                        ud_inds,
                        uc_inds[:, (1, 2)],
                        sorting='sorted',
                        search_space_sorting=None
                    )

                    idx_list.append([uc_inds, uc_inv, v1_map, v2_map])
                # dihed_pos = idx_list[2]
            else:
                raise NotImplementedError("need to manage sorting")
                if len(idx_list) < 3:
                    ud_inds, ud_inv = np.unique(
                        np.concatenate(
                            [
                                np.concatenate([x[:, np.newaxis] for x in dlist], axis=-1)
                                for dlist in dist_pos
                            ],
                            axis=0
                        ),
                        axis=0,
                        return_inverse=True
                    )
                    idx_list.append([ud_inds, ud_inv])
                if len(idx_list) < 4:
                    uc_inds, uc_pos, uc_inv = np.unique(
                        np.concatenate(
                            [
                                np.concatenate([x[:, np.newaxis] for x in clist], axis=-1)
                                for clist in cross_pos
                            ],
                            axis=0
                        ),
                        axis=0,
                        return_index=True,
                        return_inverse=True
                    )
                    idx_list.append([uc_inds, uc_pos, uc_inv])

        else:
            raise NotImplementedError("need to manage sorting")
            if len(idx_list) < 2:
                ud_inds, ud_inv = np.unique(
                    np.concatenate(
                        [
                            np.concatenate([x[:, np.newaxis] for x in dlist], axis=-1)
                            for dlist in dist_pos
                        ],
                        axis=0
                    ),
                    axis=0,
                    return_inverse=True
                )
                idx_list.append([ud_inds, ud_inv])
            if len(idx_list) < 3:
                idx_list.append(None)

        # distance_matrix = np.zeros((ncoords, ncoords)) # we track this for reuse throughout remaining routines
        ud_inds, ud_inv = idx_list[-2]
        # ud_inds = all_dist_inds[ud_pos]
        #np.unique(dist_pos, axis=0, return_inverse=True)
        ix, jx = ud_inds[:, 0], ud_inds[:, 1]
        unique_dists, unique_diffs = self.get_dists(coords[ix], coords[jx], return_diffs=True)
        dists = unique_dists[ud_inv[:num_dists]]
        # all_dists, all_diffs = self.get_dists(coords[ix], coords[jx], return_diffs=True)
        # dists = all_dists[:num_dists]
        if return_derivs:
            raise NotImplementedError("needs to be updated to account for uniqueness")
            _, dist_derivs, dist_derivs_2 = dist_deriv(coords, ix, jx, order=2)
            drang = np.arange(nol - 1)
            nreps = int(len(ix) / (nol - 1))
            drang = np.broadcast_to(drang[np.newaxis], (nreps,) + drang.shape).flatten()
            derivs[0][ix, :, drang, 0] = dist_derivs[0]
            derivs[0][jx, :, drang, 0] = dist_derivs[1]

            for i, x1 in enumerate([ix, jx]):
                for j, x2 in enumerate([ix, jx]):
                    derivs[1][x1, :, x2 % nol, :, drang, 0] = dist_derivs_2[i, j]

        if nol > 2:
            # uc_inds, uc_pos, uc_inv = np.unique(cross_pos, axis=0, return_index=True, return_inverse=True)
            uc_inds, uc_inv, uc_norm_inds1, uc_norm_inds2 = idx_list[-1]

            # we now need to map the unique cross product indices to the corresponding
            # distance indices...
            # we do this by noting that if uc_pos < num_angles, there's a corresponding distance
            # index

            # indices used in computing the distances that are also used when computing the
            # angles and their corresponding norms
            # uc_norm_inds1 = angle_dist_inds[uc_pos]
            # uc_norm_inds2 = ud_inv[num_dists:num_dists+num_angles][uc_pos]

            # raise Exception(len(uc_norm_inds1), len(uc_norm_inds2))
            norms_1 = unique_dists[uc_norm_inds1]#.reshape(-1, nol-1)[:, 1:].flatten()
            diffs_1 = unique_diffs[uc_norm_inds1]#.reshape(-1, nol-1, 3)[:, 1:].reshape(-1, 3)
            norms_2 = unique_dists[uc_norm_inds2]
            diffs_2 = unique_diffs[uc_norm_inds2]

            # ix, jx, kx = uc_inds[:, 0], uc_inds[:, 1], uc_inds[:, 2]
            unique_angles, unique_crosses = self.get_angles(
                diffs_2,
                diffs_1, # flipping the order is the same as negating diffs_1 (which is otherwise necessary)
                None,
                norms=[norms_2, norms_1]
            )
            unique_cross_norms = vec_norms(unique_crosses)

            # idx_list, mask = self._get_cached_angle_inds(idx_list, mask, ncoords, ol, nol)
            # ix, jx, kx = idx_list[1]
            #
            #
            # cross_norms = np.zeros((ncoords, ncoords, ncoords))
            # cross_mat = np.zeros((ncoords, ncoords, ncoords, 3)) # we track this for reuse throughout remaining routines
            # angles = self._get_angles_cached(distance_matrix, cross_mat, cross_norms, coords, ix, jx, kx)
            angles = unique_angles[uc_inv[:num_angles]]
            # angles = all_angles[:num_angles]
            angles = self._restructure_angles(angles, ncoords, steps, nol, use_rad)
            if return_derivs:
                raise NotImplementedError("needs to be updated to account for uniqueness")
                # we might need to mess with the masks akin to the insert call...
                _, angle_derivs, angle_derivs_2 = angle_deriv(coords, jx, ix, kx, order=2)
                drang = 1 + np.arange(nol - 2)
                nreps = int(len(ix) / (nol - 2))
                drang = np.broadcast_to(drang[np.newaxis], (nreps,) + drang.shape).flatten()
                derivs[0][jx, :, drang, 1] = angle_derivs[0]
                derivs[0][ix, :, drang, 1] = angle_derivs[1]
                derivs[0][kx, :, drang, 1] = angle_derivs[2]

                for i, x1 in enumerate([ix, jx, kx]):
                    for j, x2 in enumerate([ix, jx, kx]):
                        derivs[1][x1, :, x2 % nol, :, drang, 0] = angle_derivs_2[i, j]
        else:
            angles = np.zeros(ncoords - steps)

        if nol > 3:
            norm_inds1 = ud_inv[:num_dists].reshape(-1, nol - 1)[:, 2:].flatten()
            norm_inds2 = ud_inv[num_dists:num_dists+num_angles].reshape(-1, nol - 2)[:, 1:].flatten()
            norm_inds3 = ud_inv[num_dists+num_angles:]

            norms_1 = unique_dists[norm_inds1]
            diffs_1 = unique_diffs[norm_inds1]
            norms_2 = unique_dists[norm_inds2]
            diffs_2 = unique_diffs[norm_inds2] # 3 - 2
            norms_3 = unique_dists[norm_inds3]
            diffs_3 = unique_diffs[norm_inds3] # 4 - 3

            cross_inds1 = uc_inv[:num_angles].reshape(-1, nol - 2)[:, 1:].flatten() # 3 - 2 x 2 - 1
            cross_inds2 = uc_inv[num_angles:] # 4 - 3 x 3 - 2
            crosses_1 = unique_crosses[cross_inds1]
            crosses_2 = unique_crosses[cross_inds2]
            cross_norms1 = unique_cross_norms[cross_inds1]
            cross_norms2 = unique_cross_norms[cross_inds2]

            diheds = self.get_diheds(
                diffs_1,
                diffs_2,
                diffs_3,
                None,
                norms=[norms_1, norms_2, norms_3],
                crosses=[[crosses_1, crosses_2], [cross_norms1, cross_norms2]]
            )
            diheds = self._restructure_diheds(diheds, ncoords, steps, nol, use_rad)

            # # set up mask to drop all of the second atom bits (wtf it means 'second')
            # idx_list, mask = self._get_cached_dihed_inds(idx_list, mask, ncoords, ol, nol)
            # # mask[np.arange(2, ncoords, nol)] = 0
            # ix, jx, kx, lx = idx_list[2]
            #
            # # norms_1 = self._get_cached_norms(distance_matrix, coords, ix, jx)
            # norms_2 = self._get_cached_norms(distance_matrix, coords, jx, kx)
            # # norms_3 = self._get_cached_norms(distance_matrix, coords, kx, lx)
            #
            # crosses_1, cross_norms_1 = self._get_cached_crosses(distance_matrix, cross_mat, cross_norms, coords, ix, jx, kx)
            # crosses_2, cross_norms_2 = self._get_cached_crosses(distance_matrix, cross_mat, cross_norms, coords, ix, jx, kx)
            #
            # diheds = self.get_diheds(coords[ix], coords[jx], coords[kx], coords[lx],
            #                          crosses=[(crosses_1, crosses_2), (cross_norms_1, cross_norms_2)],
            #                          norms=[None, norms_2, None] # all we really need to reuse...
            #                          )
            # diheds = self._restructure_diheds(diheds, ncoords, steps, nol, use_rad)

            # diheds = self.get_diheds(coords[ix], coords[jx], coords[kx], coords[lx],
            #                          crosses=[(crosses_1, crosses_2), (cross_norms_1, cross_norms_2)],
            #                          norms=[None, norms_2, None] # all we really need to reuse...
            #                          )

            if return_derivs:
                # Negative sign because my dihed_deriv code is for slightly different
                # ordering than expected
                _, dihed_derivs, dihed_derivs_2 = dihed_deriv(coords, ix, jx, kx, lx, order=2)
                drang = 2 + np.arange(nol - 3)
                nreps = int(len(ix) / (nol - 3))
                drang = np.broadcast_to(drang[np.newaxis], (nreps,) + drang.shape).flatten()
                derivs[0][ix, :, drang, 2] = dihed_derivs[0]
                derivs[0][jx, :, drang, 2] = dihed_derivs[1]
                derivs[0][kx, :, drang, 2] = dihed_derivs[2]
                derivs[0][lx, :, drang, 2] = dihed_derivs[3]

                for i, x1 in enumerate([ix, jx, kx, lx]):
                    for j, x2 in enumerate([ix, jx, kx, lx]):
                        derivs[1][x1, :, x2 % nol, :, drang, 0] = dihed_derivs_2[i, j]

        else:
            diheds = np.zeros(ncoords - steps)

        # after the np.insert calls we have the right number of final elements, but too many
        # ol and om elements and they're generally too large
        # so we need to shift them down and mask out the elements we don't want
        ol, om = self._build_post_ordering_lists(ol, om, ncoords, nol, ncol, steps)

        return dists, angles, diheds, ol, om


    _index_cache = MaxSizeCache()
    def convert(self, coords, ordering=None, use_rad=True, return_derivs=False, canonicalize=True, **kw):
        """The ordering should be specified like:

        [
            [n1],
            [n2, n1]
            [n3, n1/n2, n1/n2]
            [n4, n1/n2/n3, n1/n2/n3, n1/n2/n3]
            [n5, ...]
            ...
        ]

        :param coords:    array of cartesian coordinates
        :type coords:     np.ndarray
        :param use_rad:   whether to user radians or not
        :type use_rad:    bool
        :param ordering:  optional ordering parameter for the z-matrix
        :type ordering:   None or tuple of ints or tuple of tuple of ints
        :param kw:        ignored key-word arguments
        :type kw:
        :return: z-matrix coords
        :rtype: np.ndarray
        """
        ncoords = len(coords)
        ol, nol, ncol = self._get_conversion_info(ncoords, ordering, canonicalize)
        orig_ol = ol
        steps = ncoords // nol
        # steps = int(fsteps)

        # print(">> c2z >> ordering:", ol)

        multiconfig = nol < ncoords
        ol, om, mc_ol = self._build_ordering_list(multiconfig, ol, ncoords)

        # need to check against the cases of like 1, 2, 3 atom molecules
        # annoying but not hard
        if return_derivs:
            derivs = [
                np.zeros(coords.shape + (nol-1, 3)),
                np.zeros(coords.shape + (nol, 3) + (nol - 1, 3))
            ]
        else:
            derivs = None

        if not multiconfig:
            ix = ol[1:, 0]
            jx = ol[1:, 1]
            dists = self.get_dists(coords[ix], coords[jx])
            if return_derivs:
                _dists, dist_derivs, dist_derivs_2 = dist_deriv(coords, ix, jx, order=2)
                drang = np.arange(len(ix))
                derivs[0][ix, :, drang, 0] = dist_derivs[0]
                derivs[0][jx, :, drang, 0] = dist_derivs[1]

                for i, x1 in enumerate([ix, jx]):
                    for j, x2 in enumerate([ix, jx]):
                        # print(i, j, x1, x2,
                        #       # dist_derivs_2[i, j][0, 0],
                        #       drang
                        #       )
                        derivs[1][x1, :, x2, :, drang, 0] = dist_derivs_2[i, j]

            if len(ol) > 2:
                ix = ol[2:, 0]
                jx = ol[2:, 1]
                kx = ol[2:, 2]
                angles = np.concatenate( (
                    [0], self.get_angles(coords[ix], coords[jx], coords[kx])[0]
                ) )
                if not use_rad:
                    angles = np.rad2deg(angles)
                if return_derivs:
                    _angles, angle_derivs, angle_derivs_2 = angle_deriv(coords, jx, ix, kx, order=2)
                    drang = 1+np.arange(len(ix))
                    # print(">>>>", np.max(np.abs(angle_derivs)))
                    derivs[0][jx, :, drang, 1] = angle_derivs[0]
                    derivs[0][ix, :, drang, 1] = angle_derivs[1]
                    derivs[0][kx, :, drang, 1] = angle_derivs[2]

                    for i, x1 in enumerate([jx, ix, kx]):
                        for j, x2 in enumerate([jx, ix, kx]):
                            derivs[1][x1, :, x2, :, drang, 1] = angle_derivs_2[i, j]
            else:
                angles = np.array([0.])
            if len(ol) > 3:
                ix = ol[3:, 0]
                jx = ol[3:, 1]
                kx = ol[3:, 2]
                lx = ol[3:, 3]
                if ol.shape[1] == 5:
                    raise NotImplementedError("psi angles might be unnecessary")
                    ix = ix.copy()
                    jx = jx.copy()
                    kx = kx.copy()
                    lx = lx.copy()
                    fx = ol[3:, 4]
                    swap_pos = np.where(fx == 1)
                    swap_i = ix[swap_pos]
                    swap_j = jx[swap_pos]
                    swap_k = kx[swap_pos]
                    swap_l = lx[swap_pos]
                    ix[swap_pos] = swap_l
                    jx[swap_pos] = swap_i
                    kx[swap_pos] = swap_j
                    lx[swap_pos] = swap_k

                diheds = np.concatenate( (
                    [0, 0],
                    self.get_diheds(coords[ix], coords[jx], coords[kx], coords[lx])
                ) )
                if not use_rad:
                    diheds = np.rad2deg(diheds)
                if return_derivs:
                    _diheds, dihed_derivs, dihed_derivs_2 = dihed_deriv(coords, ix, jx, kx, lx, order=2)
                    drang = 2+np.arange(len(ix))
                    derivs[0][ix, :, drang, 2] = dihed_derivs[0]
                    derivs[0][jx, :, drang, 2] = dihed_derivs[1]
                    derivs[0][kx, :, drang, 2] = dihed_derivs[2]
                    derivs[0][lx, :, drang, 2] = dihed_derivs[3]

                    for i, x1 in enumerate([ix, jx, kx, lx]):
                        for j, x2 in enumerate([ix, jx, kx, lx]):
                            derivs[1][x1, :, x2, :, drang, 2] = dihed_derivs_2[i, j]
            else:
                diheds = np.array([0, 0])
            ol = ol[1:]

        else: # multiconfig
            dists, angles, diheds, ol, om = self._convert_multiconfig(
                coords,
                ol, om, orig_ol,
                ncoords, nol, ncol, steps,
                use_rad,
                return_derivs, derivs
            )

        final_coords = self._build_coord_triples(dists, angles, diheds)

        origins, axes = self._compute_final_frame(multiconfig, coords, mc_ol, nol, ol)

        ordering = self._rebuild_ordering(ncol, orig_ol, om)
        opts = dict(use_rad=use_rad, ordering=ordering, origins=origins, axes=axes)

        # if we're returning derivs, we also need to make sure that they're ordered the same way the other data is...
        if return_derivs:
            opts['derivs'] = derivs#[:1]

        return final_coords, opts

__converters__ = [ CartesianToZMatrixConverter() ]