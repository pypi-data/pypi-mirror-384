import uuid

from .CommonCoordinateSystems import InternalCoordinateSystem, CartesianCoordinates3D
from .CoordinateSystemConverter import CoordinateSystemConverter
from ... import Numputils as nput
# import weakref

__all__ = [
    "GenericInternalCoordinateSystem",
    "GenericInternalCoordinates",
    "CartesianToGICSystemConverter",
    "GICSystemToCartesianConverter"
]

#TODO: these should all be metaclasses but :shrag:
class GenericInternalCoordinateSystem(InternalCoordinateSystem):
    """
    Represents ZMatrix coordinates generally
    """
    name = "GenericInternals"
    def __init__(self,
                 converter_options=None,
                 dimension=(None,),
                 coordinate_shape=(None,),
                 angle_ordering='ijk',
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
        if converter_options is None:
            converter_options = opts
        converter_options['angle_ordering'] = converter_options.get('angle_ordering', angle_ordering)
        super().__init__(dimension=dimension, coordinate_shape=coordinate_shape, converter_options=converter_options)

    # def jacobian(self,
    #              coords,
    #              system,
    #              order=1,
    #              coordinates=None,
    #              converter_options=None,
    #              all_numerical=False,
    #              analytic_deriv_order=None,
    #              **finite_difference_options
    #              ):
    #     carts = self.convert_coords(coords, CartesianCoordinates3D,
    #                                 order=order,
    #                                 converter_options=converter_options
    #                                 )
    #     if system
    #     cart_jacs = carts.jacobian(system, order=order,
    #                                all_numerical=all_numerical,
    #                                analytic_deriv_order=analytic_deriv_order,
    #                                **finite_difference_options
    #                                )
    #     return nput.tensor_reexpand(
    #         super().jacobian(coords, CartesianCoordinates3D, order)
    #     )

GenericInternalCoordinates = GenericInternalCoordinateSystem()
GenericInternalCoordinates.__name__ = "ZMatrixCoordinates"
GenericInternalCoordinates.__doc__ = """Generic internals"""

class CartesianToGICSystemConverter(CoordinateSystemConverter):
    """
    A converter class for going from Cartesian coordinates to internals coordinates
    """

    @property
    def types(self):
        return (CartesianCoordinates3D, GenericInternalCoordinates)

    def convert_many(self, coords, *, specs, order=0, masses=None, remove_translation_rotation=True,
                     reference_coordinates=None,
                     return_derivs=None,
                     derivs=None,
                     gradient_function=None,
                     gradient_scaling=None,
                     **kw):
        """
        We'll implement this by having the ordering arg wrap around in coords?
        """

        if return_derivs is None or return_derivs is True:
            return_derivs = order
        if return_derivs == 0: return_derivs = 1
        if not nput.is_numeric(return_derivs):
            return_derivs = max(return_derivs)

        internals = nput.internal_coordinate_tensors(coords, specs, order=return_derivs, **kw)
        internals, derivs = internals[0], internals[1:]
        return internals, {
            'specs':specs,
            'derivs':derivs,
            'reference_coordinates':coords,
            'masses': masses,
            'remove_translation_rotation': remove_translation_rotation
        }

    def convert(self, coords, *, specs, order=0, **kw):
        return self.convert_many(coords, specs=specs, order=order, **kw)


class GICSystemToCartesianConverter(CoordinateSystemConverter):
    """
    A converter class for going from Cartesian coordinates to internals coordinates
    """

    @property
    def types(self):
        return (GenericInternalCoordinates, CartesianCoordinates3D)

    def convert_many(self, coords, *, reference_coordinates, specs, order=0,
                     masses=None,
                     remove_translation_rotation=True,
                     derivs=None,
                     return_derivs=None,
                     **kw):
        """
        We'll implement this by having the ordering arg wrap around in coords?
        """

        if return_derivs is None or return_derivs is True:
            return_derivs = order
        if return_derivs == 0: return_derivs = 1
        if not nput.is_numeric(return_derivs):
            return_derivs = max(return_derivs)
        (expansions, errors), _ = nput.inverse_coordinate_solve(specs, coords, reference_coordinates,
                                                                order=return_derivs,
                                                                return_expansions=True,
                                                                return_internals=True,
                                                                masses=masses,
                                                                remove_translation_rotation=remove_translation_rotation,
                                                                **kw
                                                                )
        carts, derivs = expansions[0], expansions[1:]
        return carts, {
            'specs':specs,
            'derivs': derivs,
            'masses': masses,
            'remove_translation_rotation': remove_translation_rotation
        }

    def convert(self, coords, *, reference_coordinates, specs, order=0, **kw):
        return self.convert_many(coords, reference_coordinates=reference_coordinates, specs=specs, order=order, **kw)

__converters__ = [CartesianToGICSystemConverter(), GICSystemToCartesianConverter()]

