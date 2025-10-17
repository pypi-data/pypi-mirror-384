"""
Sets up a general Interpolator class that looks like Mathematica's InterpolatingFunction class
"""

import numpy as np, math, time, abc
import scipy.spatial as spat
import itertools, typing, dataclasses

import scipy.special as special

from ..Numputils import vec_outer, vec_tensordot, unique as nput_unique, vec_tensordiag, tensordot_deriv, tensorprod_deriv
from .Taylor import FunctionExpansion
from .Symbolic import TensorExpression
from ..Scaffolding import Logger

__all__ = [
    "RBFDInterpolator",
    "InverseDistanceWeightedInterpolator"
]

class NeighborBasedInterpolator(metaclass=abc.ABCMeta):
    """
    Useful base class for neighbor-based interpolation
    """

    __props__ = (
        "clustering_radius",
        "neighborhood_size",
        "neighborhood_merge_threshold",
        "neighborhood_clustering_radius",
        "coordinate_transform",
        "bad_interpolation_retries",
        "logger"
    )
    def __init__(self,
                 pts, values, *derivatives,
                 clustering_radius=None,
                 neighborhood_size=15,
                 neighborhood_merge_threshold=None,
                 neighborhood_max_merge_size=100,
                 neighborhood_clustering_radius=None,
                 coordinate_transform=None,
                 bad_interpolation_retries=2,
                 # max_interpolant_weight=1e25,
                 logger=None
                 ):

        pts = np.asanyarray(pts)
        values = np.asarray(values)
        derivatives = [np.asanyarray(d) for d in derivatives]
        # self._coord_shape = pts.shape[-1]
        if pts.ndim == 1:
            pts = pts[:, np.newaxis]
        elif pts.ndim > 2:
            pts = pts.reshape((pts.shape[0], -1))
            ders = []
            for i, d in enumerate(derivatives):
                ders.append(d.reshape((pts.shape[0],) + pts.shape[1:]*(i+1)))
            derivatives = ders
        # if clustering_radius is None:
        #     clustering_radius = .01**(1/pts.shape[-1])
        if clustering_radius is not None and clustering_radius >= 0:
            pts, values, derivatives = self.decluster_data(pts, values, derivatives, clustering_radius)
        self.grid = pts
        self.coordinate_transform=coordinate_transform

        self.tree = spat.KDTree(self.grid)
        self.neighborhood_size = neighborhood_size
        self.neighborhood_clustering_radius = neighborhood_clustering_radius
        self.merge_limit = neighborhood_merge_threshold
        self.max_merge_size = neighborhood_max_merge_size

        self.bad_interpolation_retries = bad_interpolation_retries

        self._pos_cache = {}
        self.vals = values
        self.derivs = derivatives

        self._globint = None

        self.logger = Logger.lookup(logger)

    @staticmethod
    def _decluster(pts, radius):
        mask = np.ones(len(pts), dtype=bool)
        for i in range(len(pts) - 1):
            if mask[i]:
                test_pos = np.where(mask[i + 1:])
                if len(test_pos) == 0 or len(test_pos[0]) == 0:
                    break
                samp_pos = i + 1 + test_pos[0]
                dists = np.linalg.norm(pts[samp_pos] - pts[i][np.newaxis], axis=1)
                mask[samp_pos] = dists > radius
        return pts[mask]
    @classmethod
    def decluster_data(cls, pts, vals, derivs, radius, return_mask=False): #TODO: I think this is broken maybe?
        rpts, _, _ = cls.RescalingData.renormalize_grid(pts)
        chunk_size = int(1e4)
        num_chunks = int(len(rpts)/chunk_size) + 1
        N = len(rpts)
        bad_pos = []
        for i in range(num_chunks):
            row_start = i * chunk_size
            row_end = min((i+1) * chunk_size, N)
            if row_start >= N:
                continue
            for j in range(num_chunks):
                col_start = j * chunk_size
                col_end = min((j+1) * chunk_size, N)
                if col_start >= N:
                    continue
                rinds, cinds = np.triu_indices(row_end - row_start, m=col_end - col_start, k=1)
                v = rpts[row_start + rinds] - rpts[col_start + cinds]
                dvec = np.linalg.norm(v, axis=1)
                bad_spots = dvec < radius
                if bad_spots.any():
                    col_start = j*chunk_size
                    bad_pos.append(col_start + cinds[bad_spots])

        if len(bad_pos) == 0 or len(bad_pos[0]) == 0:
            if return_mask:
                return pts, vals, derivs, np.ones(len(pts), dtype=bool)
            else:
                return pts, vals, derivs

        mask = np.ones(len(pts), dtype=bool)
        for b in bad_pos:
            mask[b] = False
        pts = pts[mask]
        vals = vals[mask]
        derivs = [d[mask] for d in derivs]

        if return_mask:
            return pts, vals, derivs, mask
        else:
            return pts, vals, derivs

    @dataclasses.dataclass
    class RescalingData:
        grid_shifts:'Iterable[float]'
        grid_scaling:'Iterable[float]'
        vals_shift:'float'
        vals_scaling:'float'
        __slots__ = [
            'grid_shifts', 'grid_scaling',
            'vals_shift', 'vals_scaling'
        ]

        @classmethod
        def initialize_subgrid_data(cls, pts, values, derivatives):
            grid, grid_shifts, grid_scaling = cls.renormalize_grid(pts)
            vals, val_shift, val_scaling = cls.renormalize_values(values)
            derivs = cls.renormalize_derivs(derivatives, val_scaling, grid_scaling)
            return grid, vals, derivs, cls(grid_shifts, grid_scaling, val_shift, val_scaling)

        @classmethod
        def renormalize_grid(cls, pts):
            dim_slices = np.transpose(pts)
            mins = [np.min(x) for x in dim_slices]
            maxs = [np.max(x) for x in dim_slices]
            scalings = [1 if M - m < 1e-8 else M - m for M, m in zip(maxs, mins)]
            rescaled_slices = [
                (x - m) / s for x, m, s in zip(dim_slices, mins, scalings)
            ]
            return np.transpose(rescaled_slices), np.array(mins), np.array(scalings)
        @classmethod
        def renormalize_values(cls, values):
            min = np.min(values)
            scaling = np.max(values) - min
            return (values - min) / scaling, min, scaling
        @classmethod
        def renormalize_derivs(cls, derivs, vals_scaling, grid_scaling):
            ders = []
            for n, values in enumerate(derivs):
                values = values / vals_scaling
                ndim = len(grid_scaling)
                gs = grid_scaling
                for d in range(n):
                    gs = np.expand_dims(gs, 0)
                    grid_scaling = grid_scaling[..., np.newaxis] * gs
                values = values * grid_scaling
                inds = (slice(None, None, None),) + tuple(
                    np.array(list(itertools.combinations_with_replacement(range(ndim), r=n + 1))).T
                )
                ders.append(values[inds])
            return ders

        def apply_renormalization(self, pts):
            pts = pts.T
            scaligns = self.grid_scaling.copy()
            scaligns[scaligns == 0] = 1. # only gonna happen when there's no shift anyway...
            return ((pts - self.grid_shifts[:, np.newaxis]) / scaligns[:, np.newaxis]).T
        def reverse_renormalization(self, pts):
            return pts * self.grid_scaling + self.grid_shifts

        def reverse_value_renormalization(self, vs):
            return vs * self.vals_scaling + self.vals_shift

        def reverse_derivative_renormalization(self, derivs, reshape=True):
            ders = []
            npts = None
            ndim = len(self.grid_scaling)
            for n, values in enumerate(derivs):

                # we assume we have npts x (ndim,)*n so we reshape
                if npts is None: # we start with 1D
                    npts = len(values) / ndim
                    npp = int(npts)
                    if npts != npp:
                        raise ValueError("wtf")
                    npts = npp

                k = n+1

                shp = (npts,) + (ndim,) * k
                if reshape:
                    if np.prod(shp) == len(values):
                        values = values.reshape(shp)
                    else:
                        a = np.zeros(shp)
                        base_inds = NeighborBasedInterpolator.triu_inds(ndim, k)
                        inds = (slice(None, None, None),) + base_inds
                        a[inds] = values.reshape((npts, -1))
                        for pos in np.array(base_inds).T:
                            base = (slice(None, None, None),) + tuple(pos)
                            for p in itertools.permutations(pos):
                                ind = (slice(None, None, None),) + p
                                a[ind] = a[base]
                        values = a
                else:
                    values = values.reshape((npts, -1))

                values = values * self.vals_scaling
                grid_scaling = self.grid_scaling
                gs = grid_scaling
                for d in range(n): # for a small performance boost I can avoid doing this repeatedly
                    gs = np.expand_dims(gs, 0)
                    grid_scaling = grid_scaling[..., np.newaxis] * gs
                if reshape:
                    values = values / grid_scaling
                else:
                    inds = RBFDInterpolator.triu_inds(ndim, k)
                    values = values / grid_scaling[inds]
                # inds = (slice(None, None, None),) + tuple(
                #     np.array(list(itertools.combinations_with_replacement(range(ndim), r=n + 1))).T
                # )
                ders.append(values)
            return ders

    @staticmethod # this is surprisingly slow and totally cacheable
    def triu_inds(ndim, rank):
        return tuple(
            np.array(
                list(itertools.combinations_with_replacement(range(ndim), r=rank))
            ).T
        )
    @staticmethod
    def triu_num(ndim, rank):
        if ndim == 1:
            return 1
        else:
            return math.comb(rank+(ndim-1), (ndim-1))

    def get_neighborhood(self, pts, *, neighbors, return_distances=False):
        if neighbors is None:
            neighbors = self.neighborhood_size
        distances, yindices = self.tree.query(pts, k=neighbors)
        if neighbors == 1:
            # `KDTree` squeezes the output when neighbors=1.
            yindices = yindices[:, np.newaxis]
            distances = distances[:, np.newaxis]
        # if self.grid.shape[-1] == 3:
        #     for p,idx,ddd in zip(pts, yindices, distances):
        #         nss = self.grid[idx]
        #         print(f"{p} --> {nss} ({ddd})")

        res = yindices
        if return_distances:
            res = (yindices, distances)
        return res

    def create_neighbor_groups(self, inds, merge_limit=None, max_merge_size=None):
        #TODO: lots of optimizations here, cutting down on loops, making use of sorting
        #      not doing useless setdiffs, etc.
        # _, sorting, subinds = nput_unique(inds, axis=0, return_index=True)
        if merge_limit is None:
            merge_limit = self.merge_limit
        if max_merge_size is None:
            max_merge_size = self.max_merge_size

        inds, sorting, counts = nput_unique(inds, axis=0, return_counts=True)
        subinds = np.split(sorting, np.cumsum(counts))[:-1]
        # raise Exception(nput_unique(inds, axis=0, return_index=True))
        if merge_limit is not None:
            allowed_diffs = len(inds[0]) - merge_limit
        else:
            allowed_diffs = -1
        if allowed_diffs > 0:
            groups = []
            idx_mapping = []
            for i,idx in zip(subinds, inds):
                for n,g in enumerate(groups):
                    if len(g) < self.max_merge_size:
                        idx = idx[idx > 0]
                        g = g[g > 0]
                        diff = np.setdiff1d(idx, g, assume_unique=True)
                        if len(diff) < allowed_diffs:
                            groups[n] = np.sort(np.concatenate([g, diff]))
                            idx_mapping[n] = np.concatenate([idx_mapping[n], i])
                            break
                else:
                    groups.append(idx[idx > 0])
                    idx_mapping.append(i)
        else:
            groups = inds
            idx_mapping = subinds
        # print(np.cumsum(counts),
        #       idx_mapping)

        return groups, idx_mapping

    def prep_interpolation_data(self, inds):
        grid = self.grid[inds]
        vals = self.vals[inds]
        derivs = [d[inds] for d in self.derivs]

        # print("=>", grid.shape, vals.shape, [d.shape for d in derivs])

        grid, vals, derivs, scaling_data = self.RescalingData.initialize_subgrid_data(
            grid,
            vals,
            derivs
        )

        return grid, vals, derivs, scaling_data

    @abc.abstractmethod
    def construct_interpolation(self, inds, solver_data=False, return_error=False):
        ...

    @abc.abstractmethod
    def apply_interpolation(self, pts, data, inds, deriv_order=0,
                            reshape_derivatives=True,
                            return_data=False
                            ):
        """

        :param pts:
        :type pts:
        :param data:
        :type data:
        :param deriv_order:
        :type deriv_order:
        :return:
        :rtype:
        """

    def prep_neighborhoods(self,
                           pts,
                           hoods,
                           distances,
                           neighbors,
                           merge_neighbors=None,
                           neighborhood_clustering_radius=None,
                           min_distance=None,
                           max_distance=None,
                           use_natural_neighbors=None
                           ):

        if neighborhood_clustering_radius is None:
            neighborhood_clustering_radius = self.neighborhood_clustering_radius
        if neighborhood_clustering_radius is not None:
            self.logger.log_print("declustering neighbor data...", log_level=Logger.LogLevel.Debug)
            subhoods = self.grid[hoods]
            row_inds, col_inds = np.triu_indices(neighbors, k=1)
            subdists = np.linalg.norm(
                subhoods[:, row_inds] - subhoods[:, col_inds],
                axis=-1
            )
            mask = subdists < neighborhood_clustering_radius
            for i in range(len(mask)):
                kill_me = np.where(mask[i])
                if len(kill_me) > 0 and len(kill_me[0]) > 0:
                    hoods[i][col_inds[kill_me[0]]] = -1

        if min_distance is not None or max_distance is not None:
            dist_sets = distances.copy()
            ldr = np.arange(len(dist_sets), dtype=np.int)
            nds = np.argmin(dist_sets, axis=1)
            hood_nearest = hoods[ldr, nds]
            # dist_vals = dists[ldr, nds]
            nds2 = np.argmax(dist_sets, axis=1)
            hood_furthest = hoods[ldr, nds2]
            # dists[ldr, nds] = dist_vals # reset this for later

            if min_distance is not None:
                self.logger.log_print("applying min-distance cutoff...", log_level=Logger.LogLevel.Debug)
                dist_mask = dist_sets < min_distance

                # we're gonna drop points below the distance cutoff, then
                # resample the distances so we have close the the target number of
                # neighbors
                target_neighbors = int(neighbors / 2)

                to_shrink = np.sum(dist_mask,
                                   axis=1) < target_neighbors  # we dropped less than half of the extra neighbors
                if np.any(to_shrink):
                    # now we find the first non-dropped position for these chunks
                    dist_sets[dist_mask] = np.max(dist_sets)  # this will be -1 later

                    start_pos = np.argmin(dist_sets[to_shrink], axis=1)
                    end_pos = start_pos + target_neighbors
                    subhoods = hoods[to_shrink]
                    for i, e in enumerate(end_pos):  # drop all excess points
                        subhoods[e:] = -1
                    dist_sets[dist_mask] = -1  # so we can later apply a max cutoff

                submask = np.where(np.all(dist_mask, axis=1))  # make sure we're not dropping everything...
                if len(submask) > 0:  # we'll leave in the two nearest points since we're just extrapolating basically
                    set_mask = submask + (np.zeros(len(submask[0]), dtype=np.uint8),)
                    hoods[set_mask] = hood_nearest[submask]

            if max_distance is not None:
                self.logger.log_print("applying max-distance cutoff...", log_level=Logger.LogLevel.Debug)
                dist_mask = dist_sets > max_distance
                hoods[dist_mask] = -1
                submask = np.where(np.all(dist_mask, axis=1))
                if len(submask) > 0:
                    set_mask = submask + (np.zeros(len(submask[0]), dtype=np.uint8),)
                    hoods[set_mask] = hood_nearest[submask]
                    set_mask = submask + (np.ones(len(submask[0]), dtype=np.uint8),)
                    hoods[set_mask] = hood_furthest[submask]

        if use_natural_neighbors:
            self.logger.log_print("getting natural neighbors...", log_level=Logger.LogLevel.Debug)
            for p, hh in zip(pts, hoods):
                h = hh[hh > -1]
                if len(h) > 2 * pts.shape[-1]:
                    # shit_pts = self.grid[h]
                    # shit_rows, shit_cols = np.triu_indices(len(shit_pts), k=1)
                    # raise Exception(
                    #     np.min(
                    #         np.linalg.norm(shit_pts[shit_rows] - shit_pts[shit_cols], axis=-1)
                    #     )
                    # )
                    # raise Exception(
                    #     [(np.min(self.grid[h][:, i]), np.max(self.grid[h][i])) for i in range(self.grid[h].shape[-1])]
                    # )
                    # raise Exception(self.grid[h].shape)
                    mesh_pts = np.concatenate([self.grid[h], [p]], axis=0)
                    triang = spat.Delaunay(mesh_pts, qhull_options='QJ')
                    indptr, indices = triang.vertex_neighbor_vertices
                    hood = indices[indptr[len(mesh_pts) - 1]:indptr[len(mesh_pts)]]
                    # print(len(h), len(hood))
                    hh[:len(hood)] = h[hood]
                    hh[len(hood):] = -1
                # raise Exception(hood)
            # raise Exception(hoods)
        if len(hoods) > 0:
            ind_grps, pts_grps = self.create_neighbor_groups(hoods, merge_limit=merge_neighbors)
        else:
            ind_grps = pts_grps = []

        return ind_grps, pts_grps

    def eval(self,
             pts,
             deriv_order=0,
             neighbors=None,
             merge_neighbors=None,
             reshape_derivatives=True,
             return_interpolation_data=False,
             check_in_sample=True,
             zero_tol=1e-8,
             return_error=False,
             use_cache=True,
             retries=None,
             # resiliance_test_options=None,
             # extrapolation_warning=None
             max_distance=None,
             min_distance=None,
             neighborhood_clustering_radius=None,
             use_natural_neighbors=False,
             chunk_size=None
             ):

        pts = np.asanyarray(pts)
        # check against coord shape ?
        # if pts.shape[-len(self._coord_shape):] == self._coord_shape:
        #     pts.reshape()
        if pts.ndim == 1:
            pts = pts[np.newaxis]

        if pts.ndim > 2:
            extra_shape = pts.shape[:-1]
            pts = pts.reshape(-1, pts.shape[-1])
        else:
            extra_shape = None

        if retries is None:
            retries = self.bad_interpolation_retries
        with self.logger.block(
                tag="evaluating interpolation over {n} points with {o}-order derivatives".format(n=len(pts),
                                                                                                 o=deriv_order),
                log_level=Logger.LogLevel.Debug
        ):
            # set up return locations...
            val_sets = np.empty(len(pts))
            interp_data = np.full(len(pts), None) if return_interpolation_data else None
            der_sets = [
                np.empty((len(pts),) + d.shape[1:])
                    if reshape_derivatives else
                np.empty((len(pts), self.triu_num(pts.shape[-1], d.ndim - 1)))
                for d in self.derivs
            ] if deriv_order > 0 else None
            errors = np.empty((len(pts), 2)) if return_error else None

            if neighbors is None:
                neighbors = self.neighborhood_size
            if min_distance is not None:
                neighbors = 2 * neighbors

            if chunk_size is None:
                pts_chunks = [pts]
            else:
                num_chunk = int(len(pts) / chunk_size) + 1
                pts_chunks = np.array_split(pts, num_chunk)
            chunk_offset = 0

            cache = self._pos_cache if use_cache else {}

            for k, pts in enumerate(pts_chunks):

                self.logger.log_print("applying interpolation for chunk {k} (size={s})...", k=k, s=len(pts),
                                      log_level=Logger.LogLevel.Debug)
                hoods, dists = self.get_neighborhood(pts, neighbors=neighbors,
                                                     return_distances=check_in_sample or min_distance is not None)

                sub_map = None  # to map from the reduced sample to the full one if we are able to reduce
                if check_in_sample:  # look for things very close to an abcissa
                    zero_pos = np.where(dists < zero_tol)
                    if len(zero_pos) > 0:
                        sample_pos = hoods[zero_pos]
                        zero_pos = zero_pos[0]
                        if len(zero_pos) > 0:
                            val_sets[zero_pos] = self.vals[sample_pos]
                            if deriv_order > 0:
                                for n, d in enumerate(self.derivs):
                                    der_sets[n][zero_pos] = d[sample_pos]
                            if return_error:
                                errors[zero_pos] = np.broadcast_to([[0, 0]], (len(zero_pos), 2))
                            sub_map = np.setdiff1d(np.arange(len(pts)), zero_pos)
                            hoods = hoods[sub_map]
                            pts = pts[sub_map]
                            dists = dists[sub_map]

                ind_grps, pts_grps = self.prep_neighborhoods(
                    pts,
                    hoods,
                    dists,
                    neighbors,
                    merge_neighbors=merge_neighbors,
                    neighborhood_clustering_radius=neighborhood_clustering_radius,
                    min_distance=min_distance,
                    max_distance=max_distance,
                    use_natural_neighbors=use_natural_neighbors
                )

                if len(ind_grps) > 0:
                    self.logger.log_print("solving and applying interpolation equations for {n} neighborhoods",
                                          n=len(pts_grps), log_level=Logger.LogLevel.Debug)
                    self.logger.log_print("largest neighborhood: {N}", N=max(len(x) for x in ind_grps),
                                          log_level=Logger.LogLevel.Debug)

                print_block_modulus = 25  # 1 if pts.shape[-1] > 5 else 25
                block_start_time = None
                for gn, (pts_inds, vals_inds, ds) in enumerate(zip(pts_grps, ind_grps, dists)):  # we need to evaluate this entire loop for each point......
                    # ds = ds[vals_inds > -1]
                    vals_inds = vals_inds[vals_inds > -1]
                    if gn % print_block_modulus == 0:
                        if block_start_time is not None:
                            self.logger.log_print("    block took {s:.3f}s", s=time.time() - block_start_time,
                                                  log_level=Logger.LogLevel.Debug
                                                  )
                        block_start_time = time.time()
                        self.logger.log_print("  starting group {gn} (doing {gn} to {gnm})", gn=gn, size=len(vals_inds),
                                              gnm=gn + print_block_modulus - 1,
                                              log_level=Logger.LogLevel.Debug
                                              )

                        self.logger.log_print("  group sizes: {gss}",
                                              gss=[np.sum(ind_grps[gg] > 0) for gg in
                                                   range(gn, min(len(ind_grps), gn + print_block_modulus))],
                                              log_level=Logger.LogLevel.Debug
                                              )
                    # if len(pts_inds) != len(vals_inds):
                    #     raise ValueError(f"Mismatch between points {pts_inds} and values {vals_inds}")

                    # print(vals_inds)
                    # print("dist data:", np.min(ds), np.max(ds), np.std(ds))
                    k = tuple(vals_inds)
                    if len(k) == 1:
                        res = (self.vals[k], [d[k] for d in self.derivs])
                        if return_interpolation_data:
                            res = res + (None,)
                    else:
                        if k not in cache:
                            neighs = self.neighborhood_size if neighbors is None else neighbors
                            et = self.error_threshold  # for the cases where we have errors _at the points_
                            retries = max(retries, 1)
                            for n in range(retries):
                                try:
                                    if n == retries - 1:
                                        self.error_threshold = None  # always gotta succeed in the end...
                                    interp_stuff = self.construct_interpolation(vals_inds,
                                                                                solver_data=return_interpolation_data,
                                                                                return_error=return_error
                                                                                )
                                except RBFDError:
                                    # print(">>", n, vals_inds)
                                    neighs = neighs * 2  # just try to expand a little bit to fix things...
                                    new_hoods, new_dists = self.get_neighborhood(pts[pts_inds], neighbors=neighs, return_distances=True)
                                    # vals_inds = np.unique(np.concatenate([vals_inds, new_nearest.flatten()]))

                                    prepped_inds, _ = self.prep_neighborhoods(
                                        pts[pts_inds],
                                        new_hoods,
                                        new_dists,
                                        neighbors,
                                        merge_neighbors=-1,
                                        neighborhood_clustering_radius=neighborhood_clustering_radius,
                                        min_distance=min_distance,
                                        max_distance=max_distance,
                                        use_natural_neighbors=use_natural_neighbors
                                    )
                                    vals_inds = np.concatenate([p[p>-1] for p in prepped_inds])

                                else:
                                    # if resiliance_test_options is not None:
                                    #     expansion = self.construct_function_expansion(vals_inds)
                                    #     self.resiliance_test(expansion, interp_stuff, **resiliance_test_options)
                                    break
                                finally:
                                    self.error_threshold = et
                            if return_error:
                                errors[pts_inds, :] = np.broadcast_to(interp_stuff.interpolation_error,
                                                                      (len(pts_inds), 2))
                            cache[k] = interp_stuff
                        res = self.apply_interpolation(pts[pts_inds], cache[k], vals_inds,
                                                       deriv_order=deriv_order,
                                                       reshape_derivatives=reshape_derivatives,
                                                       return_data=return_interpolation_data
                                                       )
                    res_inds = chunk_offset + (pts_inds if sub_map is None else sub_map[pts_inds])
                    if return_interpolation_data:
                        vals, ders, mat = res
                        interp_data[res_inds] = {
                            'points': self.grid[vals_inds],
                            'data': cache[k],
                            'matrix': mat,
                            'solver_data': cache[k].solver_data
                        }
                    else:
                        vals, ders = res
                    val_sets[res_inds] = vals
                    if deriv_order > 0:
                        for n, d in enumerate(ders):
                            der_sets[n][res_inds] = d

                    # print(vals)
                    # if deriv_order > 0:
                    #     print(ders)

                else:
                    if block_start_time is not None:
                        self.logger.log_print("    final block took {s:.3f}s", s=time.time() - block_start_time,
                                              log_level=Logger.LogLevel.Debug
                                              )

                chunk_offset += len(pts)

            self.logger.log_print("reshaping interpolated data", log_level=Logger.LogLevel.Debug)

            if extra_shape is not None:
                val_sets = np.reshape(val_sets, extra_shape)
                if return_interpolation_data:
                    interp_data = np.reshape(interp_data, extra_shape)
                if return_error:
                    errors = np.reshape(errors, extra_shape + (2,))
                if der_sets is not None:
                    der_sets = [
                        d.reshape(extra_shape + d.shape[1:])
                        for d in der_sets
                    ]

            if deriv_order > 0:
                if der_sets is None and len(pts) == 0:
                    der_sets = []
                res = [val_sets] + der_sets
            else:
                res = val_sets

            if return_interpolation_data or return_error:
                res = (res,)

            if return_error:
                res = res + (errors,)

            if return_interpolation_data:
                res = res + (interp_data,)

        return res

    def resiliance_test(self, expansion, interpolation_data, mesh_spacing=0.01, tolerance=0.05):
        raise NotImplementedError("changed things up...")
        # allow 5% error (maybe scaled by mesh spacing)?
        # -> presumably we have some kind of assurance based on the
        # order of the polynomial approximation for how large our error is?
        # we could calculate the interpolation at all of its target points...?

        points = expansion.center + mesh_spacing
        expand = expansion(points, outer=False)
        interp = self.apply_interpolation(points, interpolation_data)[0]
        m = np.min([np.min(expand), np.min(interp)])
        M = np.max([np.max(expand), np.max(interp)])

        error = np.abs(expand - interp) / (M - m)

        if np.max(error) > tolerance:
            raise RBFDError(
                "failed resiliance test (mesh spacing {} leads to scaled deviation from expansion greater than {})".format(
                    mesh_spacing,
                    tolerance
                ))

    def __call__(self, pts, deriv_order=0,
                 neighbors=None,
                 merge_neighbors=None,
                 reshape_derivatives=True,
                 return_interpolation_data=False,
                 use_cache=True,
                 return_error=False,
                 zero_tol=1e-8,
                 retries=None,
                 **extra_opts
                 ):
        return self.eval(pts,
                         deriv_order=deriv_order, neighbors=neighbors,
                         merge_neighbors=merge_neighbors, reshape_derivatives=reshape_derivatives,
                         return_interpolation_data=return_interpolation_data,
                         use_cache=use_cache,
                         return_error=return_error,
                         zero_tol=zero_tol,
                         retries=retries,
                         **extra_opts
                         )


    def construct_function_expansion(self, inds):
        grid = self.grid[inds]
        vals = self.vals[inds]
        derivs = [d[inds] for d in self.derivs]

        return FunctionExpansion(
            derivs,
            center=grid,
            ref=vals,
            weight_coefficients=False # I'm _pretty_ sure that's what I want?
        )

    @classmethod
    def create_function_interpolation(cls,
                                      pts,
                                      fn,
                                      *derivatives,
                                      derivative_order=None,
                                      function_shape=None,
                                      **opts):
        from ..Scaffolding import ParameterManager
        from .Taylor import FiniteDifferenceDerivative

        if derivative_order is None:
            derivative_order = len(derivatives)
        vals = fn(pts)
        dvals = []
        for n,d in enumerate(derivatives):
            if n < derivative_order:
                dvals.append(d(pts))
            else:
                break

        if pts.ndim == 1:
            input_shape = 0
        else:
            input_shape = pts.shape[-1]

        opts = ParameterManager(opts)
        if len(dvals) < derivative_order:
            fd_opts = opts.filter(FiniteDifferenceDerivative)
            base_deriv_order = len(derivatives)
            fdd = FiniteDifferenceDerivative(
                derivatives[-1] if base_deriv_order > 0 else fn,
                function_shape=(input_shape, 0) if function_shape is None else function_shape
            )

            deriv_tensors = fdd.derivatives(
                center=pts,
                **fd_opts
            ).compute_derivatives(list(range(1, derivative_order - base_deriv_order + 1)))

            dvals.extend(
                np.moveaxis(a, 0, -1) for a in deriv_tensors[base_deriv_order:]
            )

        return cls(
            pts,
            vals,
            *dvals,
            **opts.exclude(FiniteDifferenceDerivative)
        )

    def nearest_interpolation(self, pts, neighbors=None, solver_data=False, interpolator=True):
        """

        :param pts:
        :type pts:
        :param neighbors:
        :type neighbors:
        :param solver_data:
        :type solver_data:
        :param interpolator:
        :type interpolator:
        :return:
        :rtype: RBFDInterpolator.Interpolator|RBFDInterpolator.InterpolationData
        """
        pts = np.asanyarray(pts)
        smol = pts.ndim == 1
        if smol:
            pts = pts[np.newaxis]
        inds = self.get_neighborhood(pts, neighbors=neighbors)
        dats = [self.construct_interpolation(i, solver_data=solver_data) for i in inds]
        if interpolator:
            dats = [self.Interpolator(d, self) for d in dats]
        if smol:
            dats = dats[0]
        return dats

    class Interpolator:
        __slots__ = ['data', 'inds', 'parent']
        def __init__(self, data, inds, parent:'NeighborBasedInterpolator'):
            self.data = data
            self.parent = parent
            self.inds = inds
        def __call__(self, pts, deriv_order=0, reshape_derivatives=True):
            pts = np.asanyarray(pts)
            smol = pts.ndim == 1
            if smol:
                pts = pts[np.newaxis]
            vals, ders = self.parent.apply_interpolation(pts, self.data, self.inds,
                                                   deriv_order=deriv_order,
                                                   reshape_derivatives=reshape_derivatives
                                                   )
            # TODO: ADD ANY RESHAPING
            if deriv_order > 0:
                return [vals] + ders
            else:
                return vals


    @property
    def global_interpolator(self):
        if self._globint is None:
            et = self.error_threshold
            try: # ignore errors
                self.error_threshold = None
                interp = self.construct_interpolation(np.arange(len(self.grid)))
            finally:
                self.error_threshold = et
            self._globint = self.Interpolator(interp, np.arange(len(self.grid)), self)
        return self._globint

class RBFDError(ValueError):
    ...

class RBFDInterpolator(NeighborBasedInterpolator):
    """
    Provides a flexible RBF interpolator that also allows
    for matching function derivatives
    """

    def __init__(self,
                 pts, values, *derivatives,
                 kernel:typing.Union[callable,dict]='thin_plate_spline',
                 kernel_options=None,
                 auxiliary_basis=None,
                 auxiliary_basis_options=None,
                 extra_degree=0,
                 clustering_radius=None,
                 monomial_basis=True,
                 multicenter_monomials=True,
                 neighborhood_size=15,
                 neighborhood_merge_threshold=None,
                 neighborhood_max_merge_size=100,
                 neighborhood_clustering_radius=None,
                 solve_method='svd',
                 max_condition_number=np.inf,
                 error_threshold=.01,
                 bad_interpolation_retries=3,
                 coordinate_transform=None,
                 # max_interpolant_weight=1e25,
                 logger=None
                 ):

        super().__init__(pts, values, *derivatives,
                         neighborhood_size=neighborhood_size,
                         neighborhood_merge_threshold=neighborhood_merge_threshold,
                         neighborhood_max_merge_size=neighborhood_max_merge_size,
                         neighborhood_clustering_radius=neighborhood_clustering_radius,
                         clustering_radius=clustering_radius,
                         bad_interpolation_retries=bad_interpolation_retries,
                         coordinate_transform=coordinate_transform,
                         logger=logger
                         )

        self.solve_method = solve_method
        self.max_condition_number = max_condition_number # not actually using this...
        # self.max_interpolant_weight = max_interpolant_weight # hopefully this is enough...
        self.error_threshold = error_threshold

        if isinstance(kernel, str):
            kernel = self.default_kernels[kernel]
        if not isinstance(kernel, dict):
            kernel = {'function':kernel}
        if 'derivatives' not in kernel:
            kernel['derivatives'] = None
        if 'zero_handler' not in kernel:
            kernel['zero_handler'] = None
        if kernel_options is not None:
            kernel['function'] = lambda r,fn=kernel['function'],opt=kernel_options,inds=None:fn(r,inds=inds,**opt)
            if kernel['derivatives'] is not None:
                kernel['derivatives'] = lambda n, fn=kernel['derivatives'],opt=kernel_options,inds=None: (lambda r,d=fn(n):d(r, inds=inds, **opt))
            if kernel['zero_handler'] is not None:
                kernel['zero_handler'] = lambda n,ndim,fn=kernel['zero_handler'],opt=kernel_options,inds=None: (lambda r,d=fn(n, ndim):d(r, inds=inds, **opt))
        self.kernel = kernel

        if isinstance(auxiliary_basis, str):
            auxiliary_basis = self.default_auxiliary_bases[auxiliary_basis]
        if not isinstance(auxiliary_basis, dict):
            auxiliary_basis = {'function':auxiliary_basis}
        if 'derivatives' not in auxiliary_basis:
            auxiliary_basis['derivatives'] = None
        if auxiliary_basis_options is not None:
            auxiliary_basis['function'] = lambda r,fn=auxiliary_basis['function'],opt=auxiliary_basis_options,inds=None:fn(r,inds=inds,**opt)
            if auxiliary_basis['derivatives'] is not None:
                auxiliary_basis['derivatives'] = lambda n, fn=auxiliary_basis['derivatives'],opt=auxiliary_basis_options,inds=None: (lambda r,d=fn(n):d(r, inds=inds, **opt))
        self.aux_poly = auxiliary_basis
        self.extra_degree = extra_degree
        self.monomial_basis = monomial_basis
        self.multicenter_monomials = multicenter_monomials

        self._expr_cache = {}

    # def to_state(self, serializer=None):
    #     """
    #     Provides just the state that is needed to
    #     serialize the object
    #     :param serializer:
    #     :type serializer:
    #     :return:
    #     :rtype:
    #     """
    #     return {
    #         'grid': self.grid,
    #         'vals': self.vals,
    #         'derivs': self.derivs,
    #         'kernel': self.kernel,
    #         'neighborhood_size': self.neighborhood_size,
    #         'aux_poly': self.aux_poly,
    #         'monomial_basis': self.monomial_basis,
    #         'multicenter_monomials': self.multicenter_monomials,
    #         'merge_limit': self.merge_limit,
    #         'max_merge_size': self.max_merge_size,
    #         'extra_degree': self.extra_degree,
    #         'solve_method': self.solve_method,
    #         'max_condition_number': self.max_condition_number,
    #         'error_threshold': self.error_threshold,
    #     }
    # @classmethod
    # def from_state(cls, state, serializer=None):
    #     return cls(
    #         state['grid'],
    #         state['vals'],
    #         *state['derivs'],
    #         kernel=state['kernel'],
    #         neighborhood_size=state['neighborhood_size'],
    #         neighborhood_merge_threshold=state['merge_limit'],
    #         neighborhood_max_merge_size=state['max_merge_size'],
    #         solve_method=state['solve_method'],
    #         max_condition_number=state['max_condition_number'],
    #         error_threshold=state['error_threshold'],
    #         auxiliary_basis=state['aux_poly'],
    #         extra_degree=state['extra_degree'],
    #         monomial_basis=state['monomial_basis'],
    #         multicenter_monomials=state['multicenter_monomials'],
    #     )

    # TODO: add more structure defining RBF class and have each type of interpolant
    #       specialize that

    @staticmethod
    def gaussian(r, e=1, inds=None):
        if inds is not None and not isinstance(e, (int, float, np.integer, np.floating)):
            e = e[inds]
        return np.exp(-(r**2)/(2*e**2))
    @staticmethod
    def gaussian_derivative(n:int, inds=None):
        from scipy.special import hermite
        s = -1 if n%2 == 1 else 1
        def deriv(r, e=1, inds=inds):
            if inds is not None and not isinstance(e, (int, float, np.integer, np.floating)):
                e = e[inds]
            w = 1 / (e * np.sqrt(2))
            r = w * r
            return s*(w**n)*hermite(n)(r)*np.exp(-r**2)
        return deriv
    @staticmethod
    def gaussian_singularity_handler(n: int, ndim: int, inds=None):
        # handler for what happens at zero specifically
        def deriv(r, e=1, inds=inds): # r will be a vector of zeros..., inds=None):
            if inds is not None and not isinstance(e, (int, float, np.integer, np.floating)):
                e = e[inds]
            dmat = np.zeros((len(r),) + (ndim,)*n)
            if n % 2 == 0:
                crds = np.arange(ndim)
                # take tuples of crds, could be faster but we shouldn't
                # need many evals of this...
                for tup in itertools.combinations_with_replacement(crds, r=n//2):
                    idx, counts = np.unique(tup, return_counts=True)
                    val = np.prod([np.arange(1, 2*c+1, 2) for c in counts])/(e**n) # rising factorial
                    idx = sum(
                        [
                            [i] * (2 * c) for i, c in
                            zip(idx, counts)
                        ],
                        []
                    )
                    for p in itertools.permutations(idx):
                        p = (slice(None, None, None),) + p
                        dmat[p] = val
            return ((-1)**(n//2))*dmat
        return deriv

    @staticmethod
    def thin_plate_spline(r, o=3, inds=None):
        return r**o * (1 if o%2 == 1 else np.log(r+1))
    @staticmethod
    def thin_plate_spline_derivative(n: int, inds=None):
        def deriv(r, o=3, inds=inds):
            if o % 2 == 1:
                k = np.prod(o-np.arange(n))
                return k * r**(o-n)
            elif n == 1: # clearly could work this out but I don't want to right now
                """r^n/(1 + r) + n r^(-1 + n) Log[1 + r]"""
                return r**n/(1+r) + n*r**(n-1)*np.log(1+r)
            elif n == 2:
                """-(r^n/(1 + r)^2) + (2 n r^(-1 + n))/(1 + r) + (-1 + n) n r^(-2 + n) Log[1 + r]"""
                return -(r**n/(1+r)**2) + (2*n*r**(n-1))/(1+r) + n*(n-1)*r**(n-2)*np.log(1+r)
            else:
                raise NotImplementedError("need higher derivs for even thin plate splines...")
        return deriv
    @staticmethod
    def thin_plate_spline_singularity_handler(n: int, ndim: int, inds=None):
        # handler for what happens at zero specifically
        def deriv(r, o=3, inds=inds):  # r will be a vector of zeros...
            if n - (1 - (o%2)) > o:
                raise ValueError("thin plate spline deriv not defined")
            return  np.zeros((len(r),) + (ndim,) * n)
        return deriv

    wendland_coefficient_cache = {}
    @classmethod
    def wendland_coefficient(cls, l, j, k):
        if k == 0:
            return (-1)**j * special.binom(l, j)
        elif j == 1:
            return 0
        else:
            if (l, j, k) not in cls.wendland_coefficient_cache:
                if j == 0:
                    cls.wendland_coefficient_cache[(l, j, k)] = sum(
                        cls.wendland_coefficient(
                            l, j, k-1
                        ) / (j + 2)
                        for j in range(0, l + 2*k + 1)
                    )
                else:
                    cls.wendland_coefficient_cache[(l, j, k)] = -cls.wendland_coefficient(
                        l, j - 2, k - 1
                    ) / j
                # else:
                #     raise ValueError("bad ljk ({}, {}, {})".format(l, j, k))
            return cls.wendland_coefficient_cache[(l, j, k)]
    @classmethod
    def wendland_polynomial(cls, r, d=None, k=3, inds=None):
        l = int(np.floor(d/2) + k + 1)
        powers = np.arange(0, l+2*k+1)
        coeffs = [
            cls.wendland_coefficient(l, j, k)
                if j % 2 == 0 or j > 2 * k - 1 else # "the first k odd powers vanish"
            0
            for j in powers
        ]
        # raise Exception(coeffs)
        return np.dot(coeffs, r[np.newaxis, :] ** powers[:, np.newaxis]) * (r <= 1).astype(int)
    @classmethod
    def wendland_polynomial_derivative(cls, n: int, inds=None):
        def deriv(r, k=3, d=None, inds=inds):
            l = np.floor(d / 2) + k + 1
            powers = np.arange(n, l + 2*k+1)
            coeffs = [
                np.prod(j - np.arange(n)) * cls.wendland_coefficient(l, j, k)
                    if j % 2 == 1 or j > 2 * k - 1 else  # "the first k odd powers vanish"
                0
                for j in powers
            ]
            return np.dot(coeffs, r[np.newaxis, :] ** (powers-n)[:, np.newaxis]) * (r <= 1).astype(int)
        return deriv
    @staticmethod
    def wendland_polynomial_singularity_handler(n: int, ndim: int, inds=None):
        # handler for what happens at zero specifically
        def deriv(r, k=3, d=None, inds=inds):  # r will be a vector of zeros...
            if n - (1 - (k % 2)) > k:
                raise ValueError("Wendland polynomial deriv not defined")
            return np.zeros((len(r),) + (ndim,) * n)
        return deriv

    @staticmethod
    def zeros(r, inds=None):
        return np.zeros(len(r))
    @staticmethod
    def zeros_derivative(n: int, inds=None):
        def deriv(r, inds=inds):
            return np.zeros(len(r))
        return deriv
    @staticmethod
    def zeros_singularity_handler(n: int, ndim: int, inds=None):
        # handler for what happens at zero specifically
        def deriv(r, inds=inds):  # r will be a vector of zeros...
            return np.zeros((len(r),) + (ndim,) * n)
        return deriv

    @property
    def default_kernels(self):
        return {
            'gaussian': {
                'function': self.gaussian,
                'derivatives': self.gaussian_derivative,
                'zero_handler': self.gaussian_singularity_handler
            },

            'thin_plate_spline': {
                'function': self.thin_plate_spline,
                'derivatives': self.thin_plate_spline_derivative,
                'zero_handler': self.thin_plate_spline_singularity_handler
            },

            'wendland_polynomial': {
                'function': self.wendland_polynomial,
                'derivatives': self.wendland_polynomial_derivative,
                'zero_handler': self.wendland_polynomial_singularity_handler
            },

            'zeros': {
                'function': self.zeros,
                'derivatives': self.zeros_derivative,
                'zero_handler': self.zeros_singularity_handler
            }
        }

    @staticmethod
    def morse(r, a=1, inds=None):
        if inds is not None:
            if not isinstance(a, (int, float, np.integer, np.floating)):
                a = a[inds]
        return (1-np.exp(-a*r))
    @staticmethod
    def morse_derivative(n: int, inds=None):
        s = -1 if n % 2 == 1 else 1
        def deriv(r, a=1, inds=inds):
            if inds is not None:
                if not isinstance(a, (int, float, np.integer, np.floating)):
                    a = a[inds]
            return s * a**n * np.exp(-a*r) #TODO: I think this is wrong...?

        return deriv

    @staticmethod
    def even_powers(r, o=1, inds=None):
        return r**(2*o)
    @staticmethod
    def even_powers_deriv(n: int, inds=None):
        # s = -1 if n % 2 == 1 else 1

        def deriv(r, o=1, inds=inds):
            s = np.prod(np.arange(2*o, 2*o - n, -1))
            return s * r**(2*o - n)

        return deriv

    @staticmethod
    def laguerre(r, k=3, shift=2.29428, inds=None):
        return special.eval_laguerre(k, r + shift) # shift to the minimum basically...
    @staticmethod
    def laguerre_deriv(n:int, inds=None):
        """(-1)^n LaguerreL[k - n, n, x]"""
        s = -1 if n % 2 == 1 else 1
        def deriv(r, k=3, shift=2.29428, inds=inds):
            return s * special.eval_genlaguerre(k-n, n, r + shift)
        return deriv

    @classmethod
    def compact_laguerre(cls, r, e=1, k=3, shift=2.29428, inds=None):
        return cls.gaussian(r, e=e) * cls.laguerre(r, k=k, shift=shift)
    @classmethod
    def compact_laguerre_deriv(cls, n:int, inds=None):
        from scipy.special import hermite

        funs = [
            (
                cls.gaussian_derivative(i) if i > 0 else cls.gaussian,
                cls.laguerre_deriv(n-i) if i < n else cls.laguerre
            )
            for i in range(n+1)
        ]
        def deriv(r, e=1, k=3, shift=2.29428, inds=inds):
            val = 0
            for g,l in funs:
                val = val + g(r, e=e)*l(r, k=k, shift=shift)
            return val

        return deriv

    @property
    def default_auxiliary_bases(self):
        return {
            'power':None,
            'morse':{
                'function': self.morse,
                'derivatives': self.morse_derivative
            },
            'even_powers':{
                'function': self.even_powers,
                'derivatives': self.even_powers_deriv
            },
            'laguerre':{
                'function': self.laguerre,
                'derivatives': self.laguerre_deriv
            },
            'compact_laguerre':{
                'function': self.compact_laguerre,
                'derivatives': self.compact_laguerre_deriv
            }
        }

    def _poly_exprs(self, ndim:int, order:int, deriv_order:int, monomials=True):
        k = (ndim, order, deriv_order)
        if k not in self._expr_cache:
            if self.aux_poly['function'] is not None:
                coord_expr = TensorExpression.ScalarFunctionTerm(
                    TensorExpression.CoordinateVector(ndim, name='coord_vec'),
                    f=self.aux_poly
                )
            else:
                coord_expr = TensorExpression.CoordinateVector(ndim, name='coord_vec')
            if monomials:
                base_expr = TensorExpression.ScalarPowerTerm(coord_expr, order)
            else:
                # if self.aux_poly['function'] is not None:
                #     raise NotImplementedError(
                #         "auxiliary polynomial not supported for non-monomial basis".format(self.aux_poly)
                #     )
                base_expr = TensorExpression.OuterPowerTerm(coord_expr, order)
            exprs = [base_expr]
            for _ in range(deriv_order):
                exprs.append(exprs[-1].dQ())
            self._expr_cache[k] = exprs
        return self._expr_cache[k]
    def evaluate_poly_matrix(self, pts, degree, deriv_order=0, poly_origin=0.5, include_constant_term=True, monomials=True):

        if isinstance(poly_origin, (int, float, np.integer, np.floating)):
            pts = pts - poly_origin
        else:
            poly_origin = np.asanyarray(poly_origin)
            pts = pts[np.newaxis, :, :] - poly_origin[:, np.newaxis, :]

        ndim = pts.shape[-1]
        exprs = (
                (
                    [    # add in constant term by hand
                        [
                            TensorExpression.ConstantArray(np.ones(pts.shape[:-1] + (1,)))
                        ] +
                        [
                            TensorExpression.ConstantArray(np.zeros(pts.shape[:-1] + (ndim,)*d + (1,)) )
                            for d in range(1, deriv_order+1)
                        ]
                    ]
                    if include_constant_term else
                    []
                ) +
                [self._poly_exprs(ndim, d, deriv_order, monomials=monomials) for d in range(1, degree + 1)]
        )

        crds = TensorExpression.ArrayStack(pts.shape[:-1], pts)
        vals = TensorExpression(exprs, coord_vec=crds).eval()

        # raise Exception(
        #     pts.shape,
        #     [[v.shape for v in _] for _ in vals])

        # for exp_list in exprs:
        #     sublist = []
        #     for e in exp_list:
        #         print("=="*50)
        #         print(e)
        #         sublist.append(TensorExpression(e, coord_vec=crds).eval())
        #     vals.append(sublist)
        # vals = [ # evaluate poly values & derivs at each order in a dumb, kinda inefficient way? (for now)
        #     [
        #         TensorExpression(e, coord_vec=crds).eval()
        #         for e in exp_list
        #     ]
        #     for exp_list in exprs
        # ]

        # print("==="*20)
        # print(
        #     len(vals), len(vals[0]), vals[0][0].shape,
        #     len(old_vals), len(old_vals[0]), old_vals[0][0].shape
        # )
        # for new_v, old_v in zip(vals, old_vals):
        #     for a1, a2 in zip(new_v, old_v):
        #         print(a1.shape, a2.shape)
        #         print(np.sum(a1))
        #         print(np.sum(a2))
        #         assert np.allclose(a1, a2)
        #
        # raise ValueError("...")

        # Set things up so that arbitrary numbers of centers can be used at once
        padding = (slice(None, None, None),) * (2 if isinstance(poly_origin, np.ndarray) else 1)

        # now we take only upper triangle indices to get only unique ones
        flat_vals = [[] for _ in range(deriv_order+1)]
        for o, v_list in enumerate(vals): # loop over different stacks
            # get upper inds for the OuterPower term
            if not include_constant_term or o > 0:
                if not include_constant_term:
                    o = o+1
                if monomials:
                    power_inds = ()
                else:
                    power_inds = self.triu_inds(ndim, o)
                pis = padding + power_inds
                flat_vals[0].append(v_list[0][pis])
            else:
                power_inds = ()
                flat_vals[0].append(v_list[0]) # need to add a dimension for joining...
            for n,d in enumerate(v_list[1:]): #need utri inds
                # sample first power inds then derivs
                pis = padding + (slice(None, None, None),)*(n+1) + power_inds
                d = d[pis]
                # get upper inds for the different derivatives
                inds = self.triu_inds(ndim, n+1)
                inds = padding + inds
                d = d[inds]
                flat_vals[n+1].append(d)

        mats = [np.concatenate(v, axis=-1) for v in flat_vals]
        if isinstance(poly_origin, np.ndarray):
            mats = [np.moveaxis(m, 0, -1) for m in mats]
            mats = [np.reshape(m, m.shape[:-2] + (-1,)) for m in mats]
        mat = np.concatenate(
            [
                m.reshape((-1, m.shape[-1]))
                for m in mats
            ],
            axis=0
        )

        # max_value_cutoff = 1e20  # anything bigger is likely to cause numerical issues...
        # mat = np.nan_to_num(mat, nan=max_value_cutoff)
        # shit_pos = np.abs(mat) > max_value_cutoff
        # mat[shit_pos] = np.sign(mat[shit_pos]) * max_value_cutoff
        return mat

    def _rbf_exprs(self, ndim, deriv_order, inds):
        k = (ndim, deriv_order)
        # if k not in self._expr_cache:
        exprs = [
            TensorExpression.ScalarFunctionTerm(
                TensorExpression.VectorNormTerm(
                    TensorExpression.CoordinateVector(ndim, name="pts")
                ),
                f={
                    k:(lambda r,f=f:f(r, inds=inds))
                    for k,f in self.kernel.items()
                }
            )
        ]
        for _ in range(deriv_order):
            exprs.append(exprs[-1].dQ())
        self._expr_cache[k] = exprs
        return self._expr_cache[k]
    def evaluate_rbf_matrix(self, pts, centers, inds, deriv_order=0, zero_tol=1e-8):
        displacements = np.reshape(pts[:, np.newaxis, :] - centers[np.newaxis, :, :], (-1, centers.shape[-1]))
        inds = np.broadcast_to(inds[np.newaxis], (len(pts), len(centers))).flatten()
        distances = np.linalg.norm(displacements, axis=1)
        zero_pos = np.where(np.abs(distances) <= zero_tol) # we don't feed these displacements into the derivative evals
        nonz_pos = np.where(np.abs(distances) > zero_tol) # this could be fast but w/e
        displacements = displacements[nonz_pos]

        nonz_inds = inds[nonz_pos]
        zero_inds = inds[zero_pos]

        # now we evaluate the norm term...
        ndim = displacements.shape[-1]
        crds = TensorExpression.ArrayStack((len(displacements),), displacements)
        expr_vals = TensorExpression(self._rbf_exprs(ndim, deriv_order, nonz_inds), pts=crds).eval()
            # for e in self._rbf_exprs(ndim, deriv_order)
        # ]
        flat_expr_vals = [expr_vals[0]]
        for n, d in enumerate(expr_vals[1:]):  # need utri inds
            # get upper inds for the different derivatives
            inds = self.triu_inds(ndim, n+1)# tuple(np.array(list(itertools.combinations_with_replacement(range(ndim), r=n + 1))).T)
            inds = (slice(None, None, None),) + inds
            d = d[inds]
            flat_expr_vals.append(d)

        # handle singularities
        if len(zero_pos) > 0:
            zv = np.zeros(len(zero_pos[0]))
            # now we manage the singularities in the derivs
            sing_vals = [self.kernel['function'](zv, inds=zero_inds)]
            handler = self.kernel['zero_handler']
            for n in range(1, deriv_order+1):
               d = handler(n, ndim, inds=zero_inds)(zv)
               inds = self.triu_inds(ndim, n)#tuple(np.array(list(itertools.combinations_with_replacement(range(ndim), r=n))).T)
               inds = (slice(None, None, None),) + inds
               d = d[inds]
               sing_vals.append(d)

            #create final vectors by merge datasets appropriately
            full_exprs = []
            for v,s in zip(flat_expr_vals, sing_vals):
                a = np.zeros( (len(distances),) + v.shape[1:] )
                a[zero_pos] = s
                a[nonz_pos] = v
                full_exprs.append(a)
            flat_expr_vals = full_exprs

        # now reshape to turn into full mats
        npts = len(centers)

        flat_expr_vals = [
            np.moveaxis(
                a.reshape((len(pts), len(centers)) + a.shape[1:]),
                1, -1
            )
            for a in flat_expr_vals
        ]
        mat = np.concatenate(
            [
                a.reshape((-1, npts))
                for a in flat_expr_vals
            ],
            axis=0
        )

        return mat
    poly_origin = 0.5
    def construct_matrix(self,
                         pts,
                         centers,
                         inds,
                         degree=0, # passed independently
                         deriv_order=0, # passed independently
                         zero_tol=1e-8, # not really intended to be changed...
                         poly_origin=None, # can be set at the class level
                         include_constant_term=True, # can be set at the class level
                         force_square=False,
                         monomials=True,
                         multicentered_polys=False
                         ):
        if poly_origin is None:
            poly_origin = self.poly_origin
        if degree > 0:
            pol_mats = self.evaluate_poly_matrix(pts, degree,
                                                 poly_origin=poly_origin if not multicentered_polys else centers,
                                                 include_constant_term=include_constant_term,
                                                 deriv_order=deriv_order,
                                                 monomials=monomials)
        else:
            pol_mats = None
        rbf_mats = self.evaluate_rbf_matrix(pts, centers, inds, deriv_order=deriv_order, zero_tol=zero_tol)
        # print(">>", degree, rbf_mats.shape, pol_mats.shape)
        if pol_mats is not None:
            rbf_mats = np.concatenate([rbf_mats, pol_mats], axis=1)
        if force_square and rbf_mats.shape[1] > rbf_mats.shape[0]: # force it to be square by including extra polys
            curl = rbf_mats.shape[0]
            neel = rbf_mats.shape[1]
            disp = neel-curl
            rbf_mats = np.concatenate([rbf_mats, np.zeros((disp, neel))], axis=0)
            rbf_mats[curl:, :curl] = rbf_mats[:curl, -disp:].T
        return rbf_mats

    @staticmethod
    def svd_solve(a, b, svd_cutoff=1e-12):
        [U, s, Vt] = np.linalg.svd(a, full_matrices=False)
        r = max(np.where(s >= svd_cutoff)[0])
        temp = np.dot(U[:, :r].T, b) / s[:r]
        return np.dot(Vt[:r, :].T, temp)
    def solve_system(self, centers, vals, derivs:list, inds, solver=None, return_data=False, error_threshold=None):
        if len(vals) != len(centers):
            raise ValueError("need same number of interpolation points and values (got {} and {})".format(
                len(centers),
                len(vals)
            ))
        # TODO: compute the appropriate deriv order to match the vals and derivs
        derivs = [d.flatten() for d in derivs]
        nder = len(derivs)
        og_vals = vals
        vals = np.concatenate([vals]+derivs, axis=0)

        degree = 0
        if nder > 0:
            # I now know how many derivs I have per order...but I get the same contrib from each
            # degree order, but the issue is the num derivs scales with the number of centers too
            # so it needs to be solved for differently
            ndim = centers.shape[-1]
            target_extra = len(centers)*sum(self.triu_num(ndim, k) for k in range(1, nder + (0 if self.multicenter_monomials else 1) )) - 1
            cur = 0
            ncent = len(centers) if self.multicenter_monomials else 1
            for degree in range(1, nder*(target_extra//ndim)):# not sure where I need to stop?
                cur = cur + (self.triu_num(ndim, degree) if not self.monomial_basis else ndim*ncent)
                if cur >= target_extra:
                    break

        M = self.construct_matrix(centers, centers, inds,
                                  degree=degree+self.extra_degree,
                                  deriv_order=nder,
                                  monomials=self.monomial_basis,
                                  multicentered_polys=self.multicenter_monomials,
                                  force_square=True) # deriv_order and degree collaborate to get a square matrix...?

        if len(M) > len(vals):
            vals = np.concatenate([vals, np.zeros(len(M) - len(vals))])

        # with np.printoptions(linewidth=1e8, threshold=1e8):
        #     # print(centers)
        #     # print(np.min(M), np.max(M), np.linalg.cond(M))
        #     # print(vals[:, np.newaxis])
        if self.max_condition_number is not None and self.max_condition_number is not np.inf:
            cn = np.linalg.cond(M)
            if cn > self.max_condition_number:
                print("WARNING: condition number={}".format(cn))

        if solver is None:
            solver = self.solve_method
        if solver == "least_squares":
            # self.logger.log_print("   dimension of interpolation matrix: {}".format(M.shape))
            w_data = np.linalg.lstsq(M, vals, rcond=None)
        elif solver == "svd":
            w_data = self.svd_solve(M, vals)  # , rcond=None)
            w_data = (w_data,)
        elif solver is None or solver == 'solver':
            w_data = np.linalg.solve(M, vals)#, rcond=None)
            w_data = (w_data,)

        # with np.printoptions(linewidth=1e8, threshold=1e8):
        #     print(w_data[0])
        #     print(
        #         len(w_data[0]),
        #         np.argmin(w_data[0]), np.max(w_data[0]),
        #         np.argmax(w_data[0]), np.min(w_data[0]),
        #         np.std(w_data)
        #     )

        test_vals = np.dot(M, w_data[0])
        nv = len(og_vals)
        base_error = og_vals - test_vals[:nv]
        # often there's a consistent shift when things break down
        extra_shift = np.average(base_error)

        evec = np.concatenate([
            base_error - extra_shift,
            (vals[nv:] - test_vals[nv:])
        ])
        test_norm = np.linalg.norm(evec) / len(evec)  # average percent error ?
        # print(">>", test_norm, error_threshold)
        # print(len(evec), len(vals))

        test_err = np.max(np.abs(evec)) # max diff error?

        errors = [test_norm, test_err]

        if error_threshold is None:
            error_threshold = self.error_threshold

        if error_threshold is not None:
            if test_norm > error_threshold: #
                # print("...?")
                raise RBFDError("solution doesn't solve equations")
                # print("="*5)
                # print(test_norm)
                # print(vals - test_vals)



        if return_data:
            data = {'matrix':M, 'vals':vals, 'condition_number':cn}
            return w_data, degree+self.extra_degree, extra_shift, errors, data
        else:
            return w_data, degree+self.extra_degree, extra_shift, errors

    class InterpolationData:
        __slots__ = ['weights', 'centers', 'degree', 'scaling_data', 'extra_shift', 'interpolation_error', 'solver_data']
        def __init__(self, w, grid, degree, scaling_data, extra_shift=0, interpolation_error=0, solver_data=None):
            self.weights = w
            self.centers = grid
            self.degree = degree
            self.scaling_data = scaling_data
            self.solver_data = solver_data
            self.extra_shift = extra_shift
            self.interpolation_error = interpolation_error
        # def eval(self, *args, **kwargs):
        #     grid = self.grid[vals_inds]
        #     vals = self.vals[vals_inds]
        #     derivs = [d[vals_inds] for d in self.derivs]
        #
        #     grid, vals, derivs, scaling_data = self.RescalingData.initialize_subgrid_data(
        #         grid,
        #         vals,
        #         derivs
        #     )
        #
        #     # print(vals_inds)
        #     # print(vals)
        #     # print(derivs)
        #
        #     w, degree = self.solve_system(grid, vals, derivs)
        #
        #     self._pos_cache[k] = (w, grid, degree, scaling_data)

    def construct_evaluation_matrix(self, pts, data, deriv_order=0):
        """
        :param pts:
        :type pts:
        :param data:
        :type data:
        :param deriv_order:
        :type deriv_order:
        :return:
        :rtype:
        """

        scaling_data = data.scaling_data
        # w = data.weights
        degree = data.degree
        centers = data.centers

        sub_pts = scaling_data.apply_renormalization(pts)
        M = self.construct_matrix(sub_pts, centers, degree=degree, deriv_order=deriv_order, monomials=self.monomial_basis, multicentered_polys=self.multicenter_monomials)
        return M

    def apply_interpolation(self, pts, data, inds, reshape_derivatives=True, return_data=False, deriv_order=0):
        """

        :param pts:
        :type pts:
        :param data:
        :type data:
        :param deriv_order:
        :type deriv_order:
        :return:
        :rtype:
        """

        scaling_data = data.scaling_data
        w = data.weights
        degree = data.degree
        centers = data.centers

        sub_pts = scaling_data.apply_renormalization(pts)
        M = self.construct_matrix(sub_pts, centers, inds, degree=degree,
                                  deriv_order=deriv_order,
                                  monomials=self.monomial_basis,
                                  multicentered_polys=self.multicenter_monomials
                                  )
        # with np.printoptions(linewidth=1e8, threshold=1e8):
        #     print(sub_pts, M[:, -10:])
        v = np.dot(M, w[0])

        npts = len(sub_pts)
        vals = scaling_data.reverse_value_renormalization(v[:npts] - data.extra_shift)
        dvs = []
        if deriv_order > 0:  # derivatives
            offset = npts
            ndim = pts.shape[-1]
            for o in range(1, 1 + deriv_order):
                num = npts * self.triu_num(ndim, o)
                dvs.append(v[offset:offset + num])
                # print(dvs[-1])
                offset += num
            dvs = scaling_data.reverse_derivative_renormalization(dvs, reshape=reshape_derivatives)

        res = (vals, dvs)
        if return_data:
            res = res + (M,)
        return res

    def construct_interpolation(self, inds, solver_data=False, return_error=False):
        grid, vals, derivs, scaling_data = self.prep_interpolation_data(inds)

        # print("< ", grid.shape, vals.shape, [d.shape for d in derivs])

        res = self.solve_system(grid, vals, derivs, inds, return_data=solver_data)
        if solver_data:
            w, degree, extra, error, data = res
        else:
            w, degree, extra, error = res
            data = None

        #TODO: should I be tracking the indices of the points as well?
        # currently we just let those disappear but it's entirely possible
        # that someone might want to do some extra testing (a la resiliance test)
        # which would make it relevant to have access to extra information
        # relating to the original data...?
        new = self.InterpolationData(w, grid, degree, scaling_data, extra_shift=extra, interpolation_error=error, solver_data=data)
        return new

    class Interpolator(NeighborBasedInterpolator.Interpolator):
        parent:'RBFDInterpolator'
        def matrix(self, pts, deriv_order=0):
            pts = np.asanyarray(pts)
            smol = pts.ndim == 1
            if smol:
                pts = pts[np.newaxis]
            return self.parent.construct_evaluation_matrix(pts, self.data, deriv_order=deriv_order)

class DistanceWeightedInterpolator(NeighborBasedInterpolator):
    """
    Provides a quick implementation of inverse distance weighted interpolation
    """

    class InterpolationData:
        __slots__ = ['centers']
        def __init__(self, grid):
            self.centers = grid

    def construct_interpolation(self, inds, solver_data=False, return_error=False):
        grid = self.grid[inds]
        new = self.InterpolationData(grid)
        return new

    def apply_weights(self, weights, inds, deriv_order=0, reshape_derivatives=False):
        """
        Weights the values and derivatives

        :param weights: npts x hood_size matrix of weights
        :type weights:
        :param inds: npts x hood_size set of indices for the values
        :type inds:
        :return:
        :rtype:
        """
        vals = self.vals[inds]
        derivs = [self.derivs[i][inds] for i in range(deriv_order)]

        vals = np.matmul(weights[:, np.newaxis], vals[:, :, np.newaxis]).reshape((-1,))
        derivs = [
            vec_tensordot(d, weights, shared=1, axes=[1, 1]).reshape((-1,) + d.shape[2:])
            for d in derivs
        ]

        if reshape_derivatives:
            npts = len(vals)
            ndim = self.grid.shape[-1]
            reshaped = []

            for k,values in enumerate(derivs):
                k = k + 1
                shp = (npts,) + (ndim,) * k
                if shp != values.shape:
                    a = np.zeros(shp)
                    base_inds = NeighborBasedInterpolator.triu_inds(ndim, k)
                    inds = (slice(None, None, None),) + base_inds
                    a[inds] = values.reshape((npts, -1))
                    for pos in np.array(base_inds).T:
                        base = (slice(None, None, None),) + tuple(pos)
                        for p in itertools.permutations(pos):
                            ind = (slice(None, None, None),) + p
                            a[ind] = a[base]
                    values = a
                reshaped.append(values)

        return vals, derivs

    @abc.abstractmethod
    def get_weights(self, pts, data, inds):
        """
        Computes weights for pts from the inds

        :param pts:
        :type pts:
        :param inds:
        :type inds:
        :return:
        :rtype:
        """
        ...

    def apply_interpolation(self,
                            pts, data, inds,
                            deriv_order=0,
                            reshape_derivatives=True,
                            return_data=False
                            ):
        """
        :param pts:
        :type pts:
        :param data:
        :type data:
        :param deriv_order:
        :type deriv_order:
        :return:
        :rtype:
        """

        weights = self.get_weights(pts, data, inds)

        vals, derivs = self.apply_weights(weights, inds, deriv_order=deriv_order, reshape_derivatives=reshape_derivatives)

        if return_data:
            return vals, derivs, weights
        else:
            return vals, derivs

class InverseDistanceWeightedInterpolator(DistanceWeightedInterpolator):

    @classmethod
    def weight_deriv(cls, disp, dists, norm, power, n, gammas_1=None):
        prefactor = power + n + 1
        if gammas_1 is None: # we can reuse this...
            gammas_1 = dists ** -(power + 2*n) / norm[:, np.newaxis]
        gammas_2 = dists ** -(power + 2*(n+1)) / norm[:, np.newaxis]
        gouter = gammas_1[:, :, np.newaxis] * gammas_2[:, np.newaxis, :] # N x k x k
        grad = prefactor * (disp - np.matmul(gouter, disp)).transpose(0, 2, 1) # disp is N x k x d
        return gammas_2, grad

    @classmethod
    def idw_derivs(cls, deriv_order, disp, dists, norm, power, weights):
        derivs = []
        gammas = []
        if deriv_order > 0:
            gammas1, grad = cls.weight_deriv(disp, dists, norm, power, 0, weights)
            gammas.append(gammas1)
            derivs.append(grad)
        if deriv_order > 1:
            gammas1 = gammas[0]
            grad = derivs[0]
            gammas2, grad2 = cls.weight_deriv(disp, dists, norm, power, 1, gammas1)
            gammas.append(gammas2)
            prefactor = power + 2
            g1_expansion = [gammas1, grad]
            g2_expansion = [gammas2, grad2]
            inner_term_expansion = [
                vec_tensordiag(gammas1, axis=1) - vec_outer(gammas1, gammas2, axes=[-1, -1]),
                vec_tensordiag(grad, axis=2) - tensorprod_deriv(g1_expansion, g2_expansion, [1], axes=[-1, -1])[0]
            ]
            base_eye = np.eye(disp.shape[-1])
            disp_eye = np.broadcast_to(base_eye[np.newaxis], disp.shape[:2] + base_eye.shape)
            disp_eye = np.moveaxis(disp_eye, 2, 1)
            disp_expansion = [disp, disp_eye]
            # print("???", [e.shape for e in inner_term_expansion], [d.shape for d in disp_expansion])
            hess = prefactor * tensordot_deriv(inner_term_expansion, disp_expansion, [1],
                                               axes=[2, 1], shared=1
                                               )[0]
            hess = np.moveaxis(hess, 2, -1)
            derivs.append(hess)

        if deriv_order > 2:
            raise NotImplementedError('idw_derivs only up to 2nd order')
        return derivs

    @classmethod
    def get_idw_weights(cls, pts, dists, disps=None, deriv_order=None, zero_tol=1e-6, power=2):
        scaling = np.min(dists, axis=1)
        zero_pos = np.where(dists < zero_tol)
        if len(zero_pos) > 0 and len(zero_pos[0]) > 0:
            weights = np.zeros_like(dists)
            zero_row, zero_idx = np.unique(zero_pos[0], return_index=True) # so annoying but have to be clean about degenerate abcissae
            zero_col = zero_pos[1][zero_idx]
            weights[zero_row, zero_col] = 1
            nonz_pos = np.setdiff1d(np.arange(len(pts)), zero_row)
            if len(nonz_pos) > 0:
                normed_dists = dists[nonz_pos] / scaling[nonz_pos, np.newaxis]
                sdists = np.power(normed_dists, -power)
                norm = np.sum(sdists, axis=1)
                weights[nonz_pos] = sdists / norm[:, np.newaxis]
                if deriv_order is not None:
                    if disps is None: raise ValueError("displacements needed for derivatives")
                    weight_derivs = cls.idw_derivs(deriv_order, disps[nonz_pos], normed_dists, norm,
                                                   power, weights[nonz_pos])
                    derivs = []
                    for w in weight_derivs:
                        full_d = np.zeros((len(dists),) + w.shape[1:])
                        full_d[nonz_pos] = w
                        derivs.append(full_d)
                    weights = [weights] + derivs
            elif deriv_order is not None:
                weights = [weights]
        else:
            normed_dists = dists / scaling[:, np.newaxis]
            sdists = np.power(normed_dists, -power)
            norm = np.sum(sdists, axis=1)
            weights = sdists / norm[:, np.newaxis]
            if deriv_order is not None:
                if disps is None: raise ValueError("displacements needed for derivatives")
                weight_derivs = cls.idw_derivs(deriv_order, disps, normed_dists, norm, power, weights)
                weights = [weights] + weight_derivs

        return weights
    def get_weights(self, pts, dists, inds, zero_tol=1e-6, power=2):
        return self.get_idw_weights(pts, dists, zero_tol=zero_tol, power=power)

    def eval(self,
             pts,
             deriv_order=0,
             neighbors=None,
             merge_neighbors=None,
             reshape_derivatives=True,
             return_interpolation_data=False,
             check_in_sample=True,
             zero_tol=1e-8,
             return_error=False,
             use_cache=True,
             retries=None,
             # resiliance_test_options=None,
             # extrapolation_warning=None
             max_distance=None,
             min_distance=None,
             neighborhood_clustering_radius=None,
             use_natural_neighbors=False,
             chunk_size=None,
             power=2,
             mode='fast'
             ):
        if deriv_order is None:
            deriv_order = 0

        if mode == 'fast':
            pts = np.asanyarray(pts)
            # check against coord shape ?
            # if pts.shape[-len(self._coord_shape):] == self._coord_shape:
            #     pts.reshape()
            if pts.ndim == 1:
                pts = pts[np.newaxis]

            if pts.ndim > 2:
                extra_shape = pts.shape[:-1]
                pts = pts.reshape(-1, pts.shape[-1])
            else:
                extra_shape = None

            hoods, dists = self.get_neighborhood(pts, neighbors=neighbors, return_distances=True)
            val_sets, der_sets = self.apply_interpolation(pts, dists, hoods,
                                                          deriv_order=deriv_order,
                                                          reshape_derivatives=reshape_derivatives)

            if extra_shape is not None:
                val_sets = np.reshape(val_sets, extra_shape)
                # if return_interpolation_data:
                #     interp_data = np.reshape(weights, extra_shape) # wat
                # if return_error:
                #     errors = np.reshape(errors, extra_shape + (2,)) # wat
                if der_sets is not None:
                    der_sets = [
                        d.reshape(extra_shape + d.shape[1:])
                        for d in der_sets
                    ]

            if deriv_order > 0:
                res = [val_sets] + der_sets
            else:
                res = val_sets

            # if return_interpolation_data or return_error:
            #     res = (res,)
            #
            # if return_error:
            #     res = res + (errors,)

            # if return_interpolation_data:
            #     res = res + (interp_data,)

            return res
        else:
            return super().eval(
                pts,
                deriv_order=deriv_order,
                neighbors=neighbors,
                merge_neighbors=merge_neighbors,
                reshape_derivatives=reshape_derivatives,
                return_interpolation_data=return_interpolation_data,
                check_in_sample=check_in_sample,
                zero_tol=zero_tol,
                return_error=return_error,
                use_cache=use_cache,
                retries=retries,
                # resiliance_test_options=None,
                # extrapolation_warning=None
                max_distance=max_distance,
                min_distance=min_distance,
                neighborhood_clustering_radius=neighborhood_clustering_radius,
                use_natural_neighbors=use_natural_neighbors,
                chunk_size=chunk_size
            )

# class NaturalNeighborInterpolator(NeighborBasedInterpolator):
#     """
#     Provides a quick implementation of natural neighbor interpolation
#     """
#     ...