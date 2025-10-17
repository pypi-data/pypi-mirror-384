import uuid

import numpy as np
from .CommonCoordinateSystems import InternalCoordinateSystem, CartesianCoordinates3D, ZMatrixCoordinateSystem, ZMatrixCoordinates
from .CoordinateSystemConverter import CoordinateSystemConverter
from .ZMatrixToCartesian import ZMatrixToCartesianConverter
from .CartesianToZMatrix import CartesianToZMatrixConverter
from ... import Numputils as nput
# import weakref

__all__ = [
    "IterativeZMatrixCoordinateSystem",
    "IterativeZMatrixCoordinates",
    "CartesianToIZSystemConverter",
    "IZSystemToCartesianConverter"
]

#TODO: these should all be metaclasses but :shrag:
class IterativeZMatrixCoordinateSystem(ZMatrixCoordinateSystem):
    """
    Represents ZMatrix coordinates generally
    """
    name = "IterativeZMatrix"

    def __init__(self,
                 converter_options=None,
                 dimension=(None, None),
                 coordinate_shape=(None, 3),
                 **opts):
        """
        :param converter_options: options to be passed through to a `CoordinateSystemConverter`
        :type converter_options: None | dict
        :param coordinate_shape: shape of a single coordinate in this coordiante system
        :type coordinate_shape: Iterable[None | int]
        :param dimension: the dimension of the coordinate system
        :type dimension: Iterable[None | int]
        :param opts: other options, if `converter_options` is None, these are used as the `converter_options`
        :type opts:
        """
        super().__init__(dimension=dimension, coordinate_shape=coordinate_shape, converter_options=converter_options, **opts)
IterativeZMatrixCoordinates = IterativeZMatrixCoordinateSystem()
IterativeZMatrixCoordinates.__name__ = "IterativeZMatrixCoordinates"
IterativeZMatrixCoordinates.__doc__ = """Iterative Z-matrix internals"""

class CartesianToIZSystemConverter(CartesianToZMatrixConverter):
    """
    A converter class for going from Cartesian coordinates to internals coordinates
    """

    @property
    def types(self):
        return (CartesianCoordinates3D, IterativeZMatrixCoordinates)

    def convert_many(self, coords, *, ordering, use_rad=True, return_derivs=False, **kw):
        ints, opts = super().convert_many(
            coords=coords,
            ordering=ordering,
            use_rad=use_rad,
            return_derivs=return_derivs,
            **kw
        )
        opts['reference_coordinates'] = coords
        # opts['reference_internals'] = ints
        return ints, opts

class IZSystemToCartesianConverter(CoordinateSystemConverter):
    """
    A converter class for going from Cartesian coordinates to internals coordinates
    """

    @property
    def types(self):
        return (IterativeZMatrixCoordinates, CartesianCoordinates3D)

    def convert_many(self, coords, *, reference_coordinates, order=0,
                     masses=None,
                     remove_translation_rotation=True,
                     derivs=None,
                     return_derivs=None,
                     ordering=None,
                     origins=None,
                     axes=None,
                     embedding_coords=None,
                     jacobian_prep=None,
                     axes_labels=None,
                     fixed_atoms=None,
                     use_rad=True,
                     **kw):
        """
        We'll implement this by having the ordering arg wrap around in coords?
        """

        if return_derivs is None or return_derivs is True:
            return_derivs = order
        if return_derivs == 0: return_derivs = 1
        if not nput.is_numeric(return_derivs):
            return_derivs = max(return_derivs)

        sub_embedding = [1, 2, 5]
        def conv(carts, order=None, sys=coords.system):
            from .CoordinateSet import CoordinateSet
            base_shape = carts.shape[:-2]
            carts = CoordinateSet(carts, CartesianCoordinates3D)
            ints = carts.convert(sys,
                                 origins=origins, axes=axes, ordering=ordering,
                                 # embedding_coords=embedding_coords
                                 use_rad=use_rad
                                 )
            derivs = carts.jacobian(sys,
                                    order=order,
                                    converter_options=dict(
                                        origins=origins, axes=axes, ordering=ordering,
                                        use_rad=use_rad
                                        # embedding_coords=embedding_coords
                                    ),
                                    jacobian_prep=jacobian_prep,
                                    axes_labels=axes_labels
                                    )
            derivs = [
                d.reshape(base_shape + (carts.shape[-2] * 3,) * (n + 1) + (d.shape[-2] * d.shape[-1],))
                for n, d in enumerate(derivs)
            ]

            ints = ints.reshape(base_shape + (-1,)).view(np.ndarray)
            ints = np.delete(ints, sub_embedding, axis=-1)

            derivs = [
                np.delete(d, sub_embedding, axis=-1)
                for d in derivs
            ]

            return [ints] + derivs
        flat_coords = coords.reshape(coords.shape[:-2] + (-1,)).view(np.ndarray)
        flat_coords = np.delete(flat_coords, sub_embedding, axis=-1)
        (expansions, errors), _ = nput.inverse_coordinate_solve(conv,
                                                                flat_coords,
                                                                reference_coordinates,
                                                                order=return_derivs,
                                                                return_expansions=True,
                                                                return_internals=True,
                                                                masses=masses,
                                                                remove_translation_rotation=False,
                                                                fixed_atoms=fixed_atoms,
                                                                **kw
                                                                )
        carts, derivs = expansions[0], expansions[1:]
        opts = {
            # 'specs':specs,
            'derivs': derivs,
            'remove_translation_rotation': remove_translation_rotation
        }
        if masses is not None:
            opts['masses'] = masses

        return carts, opts

    def convert(self, coords, *, reference_coordinates, specs, order=0, **kw):
        return self.convert_many(coords, reference_coordinates=reference_coordinates, specs=specs, order=order, **kw)

__converters__ = [CartesianToIZSystemConverter(), IZSystemToCartesianConverter()]