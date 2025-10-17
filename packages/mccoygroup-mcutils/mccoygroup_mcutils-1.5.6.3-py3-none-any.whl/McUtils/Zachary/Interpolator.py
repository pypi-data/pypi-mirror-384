"""
Sets up a general Interpolator class that looks like Mathematica's InterpolatingFunction class
"""
import typing

import numpy as np, abc, enum, math
import scipy.interpolate as interpolate
import scipy.spatial as spat
from .Mesh import Mesh, MeshType

from .. import Numputils as nput
from .NeighborBasedInterpolators import *

__all__ = [
    "Interpolator",
    "Extrapolator",
    "RBFDInterpolator",
    "InverseDistanceWeightedInterpolator",
    "ProductGridInterpolator",
    "UnstructuredGridInterpolator",
    "CoordinateInterpolator"
]


class InterpolatorException(Exception):
    pass


######################################################################################################
##
##                                   Interpolator Class
##
######################################################################################################

class BasicInterpolator(metaclass=abc.ABCMeta):
    """
    Defines the abstract interface we'll need interpolator instances to satisfy so that we can use
    `Interpolator` as a calling layer
    """

    @abc.abstractmethod
    def __init__(self, grid, values, **opts):
        raise NotImplementedError("abstract interface")

    @abc.abstractmethod
    def __call__(self, points, **kwargs):
        raise NotImplementedError("abstract interface")

    @abc.abstractmethod
    def derivative(self, order):
        """
        Constructs the derivatives of the interpolator at the given order
        :param order:
        :type order:
        :return:
        :rtype: BasicInterpolator
        """
        raise NotImplementedError("abstract interface")

class ProductGridInterpolator(BasicInterpolator):
    """
    A set of interpolators that support interpolation
    on a regular (tensor product) grid
    """

    def __init__(self, grids, vals,
                 caller=None, order=None,
                 extrapolate=True,
                 periodic=False,
                 boundary_conditions=None
                 ):
        #TODO: add richer support for different types of boundary conditions to allow us to
        #      handler extrapolations easier, e.g. we can fix the linear term in the first derivative
        #      at the boundary or we can specify that a function is periodic along a given coordinate
        """
        :param grids:
        :type grids:
        :param points:
        :type points:
        :param caller:
        :type caller:
        :param order:
        :type order: int | Iterable[int]
        """

        if order is None:
            order = 3

        if nput.is_numeric(grids[0]):
            grids = [grids]
        self.grids = grids
        self.vals = vals
        self.periodic = periodic
        if caller is None:
            ndim = len(grids)
            if ndim == 1:
                opts = {}
                if order is not None:
                    opts["k"] = order
                caller = self.get_base_spline(
                    grids[0], vals, order,
                    periodic=periodic,
                    boundary_conditions=boundary_conditions,
                    extrapolate=extrapolate
                )
            else:
                caller = self.construct_ndspline(grids, vals, order, extrapolate=extrapolate,
                                                 periodic=periodic,
                                                 boundary_conditions=boundary_conditions
                                                 )
        self.caller = caller

    @classmethod
    def get_base_spline(cls, grid, vals, order, periodic=False, boundary_conditions=None, extrapolate=False):
        base_spline = interpolate.make_interp_spline(
            grid, vals, k=order,
            bc_type='periodic' if periodic else boundary_conditions
        )

        # Adapated from interpolate.PPoly.from_spline

        if vals.ndim > 1:
            tck = base_spline.tck
            t, c, k = tck
            polys = [interpolate.PPoly.from_spline((t, cj, k)) for cj in c.T]
            cc = np.dstack([p.c for p in polys])
            return interpolate.PPoly.construct_fast(cc, polys[0].x, extrapolate)
        else:
            return interpolate.PPoly.from_spline(base_spline.tck, extrapolate)

    @classmethod
    def construct_ndspline(cls, grids, vals, order, extrapolate=True,
                           periodic=False,
                           boundary_conditions=None
                           ):
        """
        Builds a tensor product ndspline by constructing a product of 1D splines

        :param grids: grids for each dimension independently
        :type grids: Iterable[np.ndarray]
        :param vals:
        :type vals: np.ndarray
        :param order:
        :type order: int | Iterable[int]
        :return:
        :rtype: interpolate.NdPPoly
        """

        # inspired by `csaps` python package
        # idea is to build a spline approximation in
        # every direction (where the return values are multidimensional)
        ndim = len(grids)
        if isinstance(order, (int, np.integer)):
            order = [order] * ndim

        if periodic is True or periodic is False:
            periodic = [periodic] * ndim
        if (
                boundary_conditions is None
                or isinstance(boundary_conditions, str)
                or len(boundary_conditions[0]) == 2 and nput.is_numeric(boundary_conditions[0][0])
        ):
            boundary_conditions = [boundary_conditions] * ndim

        coeffs = vals
        x = [None]*ndim
        for i, (g, o, p, bcs) in enumerate(zip(grids, order, periodic, boundary_conditions)):
            og_shape = coeffs.shape
            coeffs = coeffs.reshape((len(g), -1)).T
            sub_coeffs = [np.empty(0)]*len(coeffs)
            for e,v in enumerate(coeffs):
                ppoly = cls.get_base_spline(g, v, o, periodic=p, boundary_conditions=bcs)
                x[i] = ppoly.x
                sub_coeffs[e] = ppoly.c
            coeffs = np.array(sub_coeffs)
            coeffs = coeffs.reshape(
                og_shape[1:]+
                    sub_coeffs[0].shape
            )
            tot_dim = ndim+i+1
            coeffs = np.moveaxis(coeffs, tot_dim-2, tot_dim-2-i)

        return interpolate.NdPPoly(coeffs, x, extrapolate=extrapolate)

    def handle_periodicity(self, coords):
        if not self.periodic: return coords

        coords = np.asanyarray(coords)
        ndim = len(self.grids)
        one_d = coords.ndim == 0
        if one_d:
            coords = coords[np.newaxis]
        smol = coords.ndim == 1
        if smol:
            if ndim == 1:
                coords = coords[:, np.newaxis]
            else:
                coords = coords[np.newaxis]

        periodic = self.periodic
        if periodic is True: periodic = [periodic] * ndim
        new_coords = coords.copy()
        for i,(g,p) in enumerate(zip(self.grids, periodic)):
            if p:
                ptp = g[-1] - g[0]
                new_coords[..., i] = np.mod((coords[..., i] - g[0]), ptp) + g[0]

        if smol:
            if ndim == 1:
                new_coords = new_coords[:, 0]
            else:
                new_coords = new_coords[0]

        if one_d:
            new_coords = new_coords[0]

        return new_coords


    def __call__(self, coords, *etc, **kwargs):
        """
        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype: np.ndarray
        """
        coords = self.handle_periodicity(coords)
        return self.caller(coords, *etc, **kwargs)

    def derivative(self, order):
        """
        :param order:
        :type order:
        :return:
        :rtype: ProductGridInterpolator
        """
        # ndim = len(self.grids)
        # if ndim == 1:
        return type(self)(
            self.grids,
            self.vals,
            caller=self.caller.derivative(order),
            periodic=self.periodic
        )
        # elif ndim == 2:
        #     def caller(coords, _og=self.caller, **kwargs):
        #         return _og(coords, dx=order[0], dy=order[1], **kwargs)
        #     return type(self)(
        #         self.grids,
        #         self.vals,
        #         caller=caller
        #     )
        # else:
        #     derivs = self.caller.derivative(order)
        #     raise NotImplementedError("woof")

class UnstructuredGridInterpolator(BasicInterpolator):
    """
    Defines an interpolator appropriate for totally unstructured grids by
    delegating to the scipy `RBF` interpolators
    """

    default_neighbors=25
    def __init__(self, grid, values, order=None, neighbors=None, extrapolate=True, **opts):
        """
        :param grid:
        :type grid: np.ndarray
        :param values:
        :type values:  np.ndarray
        :param order:
        :type order: int
        :param neighbors:
        :type neighbors: int
        :param extrapolate:
        :type extrapolate: bool
        :param opts:
        :type opts:
        """
        self.extrapolate=extrapolate
        self._hull = None
        self._grid = grid

        if neighbors is None:
            neighbors = np.min([self.default_neighbors, len(grid)])

        if order is not None:
            if isinstance(order, int):
                if order == 1:
                    order = "linear"
                elif order == 3:
                    order = "cubic"
                elif order == 5:
                    order = "quintic"
                else:
                    raise InterpolatorException("{} doesn't support interpolation order '{}'".format(
                        interpolate.RBFInterpolator,
                        order
                    ))
            self.caller = interpolate.RBFInterpolator(grid, values, kernel=order, neighbors=neighbors, **opts)
        else:
            self.caller = interpolate.RBFInterpolator(grid, values, neighbors=neighbors, **opts)

    def _member_q(self, points):
        """
        Checks if the points are in the interpolated convex hull
        in the case that we aren't extrpolating so we can return
        NaN for those points
        :param points:
        :type points:
        :return:
        :rtype:
        """
        if self._hull is None:
            self._hull = spat.ConvexHull(self._grid)
            self._hull = spat.Delaunay(self._hull)
        return self._hull.find_simplex(points) >= 0
    def __call__(self, points):
        if self.extrapolate:
            return self.caller(points)
        else:
            hull_points = self._member_q(points)
            res = np.full(len(points), np.nan)
            res[hull_points] = self.caller(points[hull_points])
            return res

    def derivative(self, order):
        """
        Constructs the derivatives of the interpolator at the given order
        :param order:
        :type order:
        :return:
        :rtype: UnstructuredGridInterpolator
        """
        raise NotImplementedError("derivatives not implemented for unstructured grids")

# class _PolyFitManager:
#     """
#     Provides ways to evaluate polynomials
#     fast and get matrices of terms to fit
#     """
#     def __init__(self, order, ndim):
#         self.order = order
#         self.ndim = ndim
#         self._expr = None
#     @property
#     def perms(self):
#         from ..Combinatorics import SymmetricGroupGenerator
#
#         if self._perms is None:
#             # move this off to cached classmethod
#             # since there are restricted numbers of (order, ndim) pairs
#             sn = SymmetricGroupGenerator(self.ndim)
#             self._perms = sn.get_terms(list(range(self.order+1)))
#         return self._perms
#     def eval_poly_mat(self, coords):
#         """
#
#         :param coords: shape=(npts, ndim)
#         :type coords: np.ndarray
#         :return:
#         :rtype:
#         """
#         return np.power(coords[:, np.newaxis, :], self.perms[np.newaxis])
#     def eval_poly_mat_deriv(self, which):
#         which, counts = np.unique(which, return_counts=True)
#         perm_inds = self.perms[:, which]
#         shift_perms = perm_inds - counts[np.newaxis, :] # new monom orders


class ExtrapolatorType(enum.Enum):
    Default='Automatic'
    Error='Raise'

class Interpolator:
    """
    A general purpose that takes your data and just interpolates it without whining or making you do a pile of extra work
    """
    DefaultExtrapolator = ExtrapolatorType.Default
    def __init__(self,
                 grid,
                 vals,
                 interpolation_function=None,
                 interpolation_order=None,
                 extrapolator=None,
                 extrapolation_order=None,
                 **interpolation_opts
                 ):
        """
        :param grid: an unstructured grid of points **or** a structured grid of points **or** a 1D array
        :type grid: np.ndarray
        :param vals: the values at the grid points
        :type vals: np.ndarray
        :param interpolation_function: the basic function to be used to handle the raw interpolation
        :type interpolation_function: None | BasicInterpolator
        :param interpolation_order: the order of extrapolation to use (when applicable)
        :type interpolation_order: int | str | None
        :param extrapolator: the extrapolator to use for data points not on the grid
        :type extrapolator: Extrapolator | None | str | function
        :param extrapolation_order: the order of extrapolation to use by default
        :type extrapolation_order: int | str | None
        :param interpolation_opts: the options to be fed into the interpolating_function
        :type interpolation_opts:
        """
        self.grid = grid = Mesh(grid) if not isinstance(grid, Mesh) else grid
        self.vals = vals
        if interpolation_function is None:
            interpolation_function = self.get_interpolator(grid, vals,
                                                           interpolation_order=interpolation_order,
                                                           allow_extrapolation=extrapolator is None,
                                                           **interpolation_opts
                                                           )
        self.interpolator = interpolation_function

        if extrapolator is not None:
            if isinstance(extrapolator, ExtrapolatorType):
                if extrapolator == ExtrapolatorType.Default:
                    extrapolator = self.get_extrapolator(grid, vals, extrapolation_order=extrapolation_order)
                else:
                    raise ValueError("don't know what do with extrapolator type {}".format(extrapolator))
            elif not isinstance(extrapolator, Extrapolator):
                extrapolator = Extrapolator(extrapolator)
        self.extrapolator = extrapolator

    @classmethod
    def get_interpolator(cls, grid, vals, interpolation_order=None, allow_extrapolation=True, **opts):
        """Returns a function that can be called on grid points to interpolate them

        :param grid:
        :type grid: Mesh
        :param vals:
        :type vals: np.ndarray
        :param interpolation_order:
        :type interpolation_order: int | str | None
        :param opts:
        :type opts:
        :return: interpolator
        :rtype: function
        """
        if grid.ndim == 1:
            interpolator = ProductGridInterpolator(
                grid,
                vals,
                order=interpolation_order,
                extrapolate=allow_extrapolation
            )
        elif (
                grid.mesh_type == MeshType.Structured
                or grid.mesh_type == MeshType.Regular
        ):
            interpolator = ProductGridInterpolator(
                grid.subgrids,
                vals,
                order=interpolation_order,
                extrapolate=allow_extrapolation
            )
        elif grid.mesh_type == MeshType.Unstructured:
            # for now we'll only use the RadialBasisFunction interpolator, but this may be extended in the future
            interpolator = UnstructuredGridInterpolator(
                grid,
                vals,
                order=interpolation_order,
                extrapolate=allow_extrapolation
            )
        elif grid.mesh_type == MeshType.SemiStructured:
            raise NotImplementedError("don't know what I want to do with semistructured meshes anymore")
        else:
            raise InterpolatorException("{}.{}: can't handle mesh_type '{}'".format(
                cls.__name__,
               'get_interpolator',
                grid.mesh_type
            ))

        return interpolator

    @classmethod
    def get_extrapolator(cls, grid, vals, extrapolation_order=1, **opts):
        """
        Returns an Extrapolator that can be called on grid points to extrapolate them

        :param grid:
        :type grid: Mesh
        :param extrapolation_order:
        :type extrapolation_order: int
        :return: extrapolator
        :rtype: Extrapolator
        """

        # Extrapolator(
        #     cls(
        #         grid,
        #         vals,
        #         interpolation_order=extrapolation_order,
        #         extrapolator=Extrapolator(lambda g: np.full(g.shape, np.nan))
        #     )
        # )

        if grid.ndim == 1:
            extrapolator = ProductGridInterpolator(
                grid,
                vals,
                order=extrapolation_order,
                extrapolate=True
            )
        elif (
                grid.mesh_type == MeshType.Structured
                or grid.mesh_type == MeshType.Regular
        ):
            extrapolator = ProductGridInterpolator(
                grid.subgrids,
                vals,
                order=extrapolation_order,
                extrapolate=True
            )
        elif grid.mesh_type == MeshType.Unstructured:
            # for now we'll only use the RadialBasisFunction interpolator, but this may be extended in the future
            extrapolator = UnstructuredGridInterpolator(
                grid,
                vals,
                neighbors=extrapolation_order+1,
                order=extrapolation_order,
                extrapolate=True
            )
        elif grid.mesh_type == MeshType.SemiStructured:
            raise NotImplementedError("don't know what I want to do with semistructured meshes anymore")
        else:
            raise InterpolatorException("{}.{}: can't handle mesh_type '{}'".format(
                cls.__name__,
               'get_interpolator',
                grid.mesh_type
            ))

        return Extrapolator(
            extrapolator,
            **opts
        )

    def apply(self, grid_points, **opts):
        """Interpolates then extrapolates the function at the grid_points

        :param grid_points:
        :type grid_points:
        :return:
        :rtype:
        """
        # determining what points are "inside" an interpolator region is quite tough
        # instead it is probably better to allow the basic thing to interpolate and do its thing
        # and then allow the extrapolator to post-process that result
        vals = self.interpolator(grid_points, **opts)
        if self.extrapolator is not None:
            vals = self.extrapolator(grid_points, vals)
        return vals

    def derivative(self, order):
        """
        Returns a new function representing the requested derivative
        of the current interpolator

        :param order:
        :type order:
        :return:
        :rtype:
        """
        return type(self)(
            self.grid,
            self.vals,
            interpolation_function=self.interpolator.derivative(order),
            extrapolator=self.extrapolator.derivative(order) if self.extrapolator is not None else self.extrapolator
        )

    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)

######################################################################################################
##
##                                   Extrapolator Class
##
######################################################################################################
class Extrapolator:
    """
    A general purpose that takes your data and just extrapolates it.
    This currently only exists in template format.
    """
    def __init__(self,
                 extrapolation_function,
                 warning=False,
                 **opts
                 ):
        """
        :param extrapolation_function: the function to handle extrapolation off the interpolation grid
        :type extrapolation_function: None | function | Callable | Interpolator
        :param warning: whether to emit a message warning about extrapolation occurring
        :type warning: bool
        :param opts: the options to feed into the extrapolator call
        :type opts:
        """
        self.extrapolator = extrapolation_function
        self.extrap_warning = warning
        self.opts = opts

    def derivative(self, n):
        return type(self)(
            self.extrapolator.derivative(n),
            warning=self.extrapolator
        )

    def find_extrapolated_points(self, gps, vals, extrap_value=np.nan):
        """
        Currently super rough heuristics to determine at which points we need to extrapolate
        :param gps:
        :type gps:
        :param vals:
        :type vals:
        :return:
        :rtype:
        """
        if extrap_value is np.nan:
            where = np.isnan(vals)
        elif extrap_value is np.inf:
            where = np.isinf(vals)
        elif not isinstance(extrap_value, (int, float, np.floating, np.integer)):
            where = np.logical_and(vals <= extrap_value[0], vals >= extrap_value[1])
        else:
            where = np.where(vals == extrap_value)

        return gps[where], where

    def apply(self, gps, vals, extrap_value=np.nan):
        ext_gps, inds = self.find_extrapolated_points(gps, vals, extrap_value=extrap_value)
        if len(ext_gps) > 0:
            new_vals = self.extrapolator(ext_gps)
            # TODO: emit a warning about extrapolating if we're doing so?
            vals[inds] = new_vals
        return vals

    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)

class IncrementalCartesianCoordinateInterpolation:
    def __init__(self,
                 abcissae,
                 coords,
                 *,
                 coordinate_system,
                 max_displacement_step=1.0,
                 max_refinements=1,
                 reembed=False,
                 embedding_options=None
                 ):
        self.abcissae = list(abcissae)
        self.coords = self.prep_cartesians(coords)
        self.converter = self.prep_coordinate_system_converter(coordinate_system)
        self.internals = [
            self.converter(c) for c in self.coords
        ]
        self.max_disp_step = max_displacement_step
        self.max_refinements = max_refinements
        self.reembed=reembed
        self.embedding_options={} if embedding_options is None else embedding_options

    @classmethod
    def wrap_convert(cls, system):
        def convert(coords):
            return coords.convert(system)
        return convert

    @classmethod
    def prep_coordinate_system_converter(cls, coordinate_system):
        from McUtils.Coordinerds import CartesianCoordinates3D

        if coordinate_system is None:
            return cls.wrap_convert(CartesianCoordinates3D)
        elif hasattr('coordinate_system', 'convert'):
            return cls.wrap_convert(coordinate_system)
        else:
            return coordinate_system

    @classmethod
    def refined_step_conv(cls,
                          pct,
                          converter,
                          init_abc, final_abc,
                          init_coords, final_coords,
                          init_internals, final_internals,
                          max_refinements=None, max_disp=.5,
                          reembed=False, embedding_options=None
                          ):
        from McUtils.Coordinerds import CoordinateSet

        if embedding_options is None:
            embedding_options = {}

        # d = CoordinateSet(self.internals[start] + disp, self.internals[start].system)
        # d.convert(self.coords[start].system)
        if pct > .5:
            return cls.refined_step_conv(
                1 - pct,
                converter,
                final_abc, init_abc,
                final_coords, init_coords,
                final_internals, init_internals,
                max_refinements=max_refinements, max_disp=max_disp,
                reembed=reembed
            )

        disp = final_coords.convert(init_internals.system) - init_internals
        step = final_abc - init_abc

        new_abcissae = []
        new_internals = []
        new_coords = []

        d = pct * disp
        md = np.max(np.abs(d))
        n_ref = 0
        while md > max_disp and (max_refinements is None or n_ref < max_refinements):
            scaling = max_disp / md
            d = d * scaling
            new_abc = init_abc + (step * pct * scaling)
            new_step = final_abc - new_abc
            pct = pct * (1 - scaling) / (1 - pct * scaling) # make sure we end up at the same spot
            init_abc = new_abc
            step = new_step
            target_internals = init_internals + d
            new_disp = CoordinateSet(target_internals, init_internals.system)
            # new_disp.converter_options = init_internals.system.converter_options
            new_carts = new_disp.convert(init_coords.system)
            if reembed:
                emb = nput.eckart_embedding(
                    init_coords,
                    new_carts,
                    **embedding_options
                )
                new_carts = (new_carts*0) + emb.coordinates
            init_coords = new_carts
            init_internals = converter(init_coords)
            new_abcissae.append(init_abc)
            new_coords.append(init_coords)
            new_internals.append(init_internals)

            disp = final_coords.convert(init_internals.system) - init_internals
            d = pct * disp
            md = np.max(np.abs(d))
            n_ref += 1

        target_internals = CoordinateSet(init_internals + d, init_internals.system)
        new_carts = target_internals.convert(init_coords.system)
        if reembed:
            emb = nput.eckart_embedding(
                init_coords,
                new_carts,
                **embedding_options
            )
            new_carts = (new_carts*0) + emb.coordinates
        return new_carts, (new_abcissae, new_coords, new_internals)

    def prep_cartesians(self, coords):
        from ..Coordinerds import CoordinateSet, CartesianCoordinates3D
        coords = np.asanyarray(coords)
        if not hasattr(coords, 'system'):
            coords = CoordinateSet(coords, CartesianCoordinates3D)
        return list(coords)

    def incremental_interp(self, start, point):
        b = self.abcissae[start]
        a = self.abcissae[start+1]
        width = a - b
        pct = (point - b) / width

        coords, (new_abcissae, new_coords, new_internals) = self.refined_step_conv(
            pct,
            self.converter,
            b, a,
            self.coords[start], self.coords[start+1],
            self.internals[start], self.internals[start+1],
            max_refinements=self.max_refinements,
            max_disp=self.max_disp_step,
            reembed=self.reembed
        )

        self.abcissae = self.abcissae[:start+1] + new_abcissae + self.abcissae[start+1:]
        self.coords = self.coords[:start+1] + new_coords + self.coords[start+1:]
        self.internals = self.internals[:start+1] + new_internals + self.internals[start+1:]

        return coords

    def interpolate(self, point):
        point = np.asanyarray(point)
        base_shape = point.shape
        point = point.reshape(-1)
        ord = np.argsort(point)
        point = point[ord]

        vals = np.empty(point.shape + self.coords[0].shape, dtype=self.coords[0].dtype)
        for k,p in enumerate(point):
            i = np.searchsorted(self.abcissae, p)
            if i > 0: i = i - 1
            crds = self.incremental_interp(i, p)
            vals[k] = crds
        inv = np.argsort(ord)
        vals = vals[inv,]
        return vals.reshape(base_shape + vals.shape[-2:])

    def __call__(self, point):
        return self.interpolate(point)

class CoordinateInterpolator:

    default_interpolator_type = IncrementalCartesianCoordinateInterpolation
    # default_smoothed_interpolator_type = IncrementalCartesianCoordinateInterpolation
    def __init__(self,
                 coordinates,
                 arc_lengths=None,
                 distance_function=None,
                 base_interpolator=None,
                 coordinate_system=None,
                 **interpolator_options
                 ):
        coordinates = np.asanyarray(coordinates)

        self.distance_function, abcissae = self.get_arc_lengths(
            coordinates,
            arc_lengths,
            distance_function=distance_function
        )

        if base_interpolator is None:
            interpolator_options['coordinate_system'] = interpolator_options.get(
                'coordinate_system',
                coordinate_system
            )
            base_interpolator = self.default_interpolator_type

        self.interpolator = base_interpolator(
            abcissae,
            coordinates,
            **interpolator_options
        )

    @classmethod
    def euclidean_coordinate_distance(cls, p1, p2):
        return np.linalg.norm(p2 - p1)


    @classmethod
    def lookup_distance_function(cls, distance_function):
        return {
            'uniform':cls.uniform_distance_function
        }[distance_function.lower()]

    @classmethod
    def uniform_distance_function(cls, coords):
        return np.linspace(0, 1, len(coords))

    @classmethod
    def get_arc_lengths(cls,
                        coordinates:np.ndarray,
                        arc_lengths=None,
                        distance_function:'typing.Callable[[np.ndarray, np.ndarray], float]'=None
                        ):

        if arc_lengths is None:
            if isinstance(distance_function, str):
                arc_lengths = cls.lookup_distance_function(distance_function)(coordinates)
            else:
                if distance_function is None:
                    distance_function = cls.euclidean_coordinate_distance
                arc_lengths = np.cumsum([0.] + [
                    distance_function(p1, p2)
                    for p1, p2 in zip(coordinates[:-1], coordinates[1:])
                ])
        arc_lengths = np.asanyarray(arc_lengths)

        return distance_function, (arc_lengths - np.min(arc_lengths)) / np.ptp(arc_lengths)

    def __call__(self, points, **etc):
        return self.interpolator(points, **etc)