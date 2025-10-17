import uuid
import numpy as np

from .CoordinateSystem import CoordinateSystem
from .CoordinateSystemConverter import CoordinateSystemConverter
from ... import Numputils as nput
import weakref

__all__ = [
    "CompositeCoordinateSystem",
    "CompositeCoordinateSystemConverter",
    # "TransformedCoordinateSystem",
    # "TransformedCoordinateSystemConverter",
]

#TODO: these should all be metaclasses but :shrag:
class CompositeCoordinateSystem(CoordinateSystem):
    """
    Defines a coordinate system that comes from applying a transformation
    to another coordinate system
    """

    _register_cache = weakref.WeakValueDictionary()
    def __init__(self,
                 base_system,
                 conversion,
                 inverse_conversion=None,
                 jacobian=None,
                 inverse_jacobian=None,
                 name=None, batched=None, pointwise=True,
                 # max_expansion_order=0,
                 **opts):
        self.base_system = base_system
        self.conversion = conversion
        self.inverse_conversion = inverse_conversion
        self.pointwise = pointwise
        self.batched = batched if batched is not None else not pointwise
        # self.max_expansion_order = max_expansion_order
        super().__init__(**opts)
        self.name = self.canonical_name(name, conversion)
        self.fwd_jacobian = jacobian
        self.inverse_jacobian = inverse_jacobian
    @classmethod
    def canonical_name(cls, name, conversion):
        if name is None:
            if hasattr(conversion, 'name'):
                name = conversion.name
            else:
                name = str(uuid.uuid4()).replace("-", "")
        return name
        #
        #     return type('CompositeCoordinateSystem' + name, (cls,),
        #                 {'base_system': base_system, 'conversion': conversion, 'inverse': inverse})
        # # if self.base_system is None:
        # #     raise ValueError('{name} is a factory class and {name}.{method} should be used to register coordinate systems'.format(
        # #         name=type(self).__name__,
        # #         method='register'
        # #     ))
        # # super().__init__()

    @classmethod
    def register(cls, base_system, conversion, inverse_conversion=None, name=None, batched=None, pointwise=True, **opts):
        if (base_system, conversion) not in cls._register_cache:
            system_class = cls(base_system, conversion, inverse_conversion=inverse_conversion, name=name,
                               batched=batched, pointwise=pointwise, **opts)
            CompositeCoordinateSystemConverter(system_class).register()
            if system_class.inverse_conversion is not None:
                CompositeCoordinateSystemConverter(system_class, direction='inverse').register()
            cls._register_cache[(base_system, conversion)] = system_class
        return cls._register_cache[(base_system, conversion)]
    def unregister(self):
        raise NotImplementedError("destructor not here yet")
    def __repr__(self):
        return "{}({}, {})".format(
            type(self).__name__,
            self.base_system,
            self.name
        )


class CompositeCoordinateSystemConverter(CoordinateSystemConverter):
    def __init__(self, system:CompositeCoordinateSystem, direction='forward'):
        self.system = system
        self.direction = direction
    @property
    def types(self):
        if self.direction == 'inverse':
            return (self.system, self.system.base_system)
        else:
            return (self.system.base_system, self.system)
    def get_conversion(self):
        if self.direction == 'forward':
            convertser = self.system.conversion
        elif self.direction == 'inverse':
            convertser = self.system.inverse_conversion
        else:
            raise NotImplementedError("bad value for '{}': {}".format('direction', self.direction))
        return convertser
    def convert(self, coords, **kw):
        if self.system.pointwise:
            return nput.apply_by_coordinates(self.get_conversion(), coords, **kw)
        else:
            return self.get_conversion()(coords, **kw)
    def convert_many(self,
                     coords,
                     order=0,
                     derivs=None,
                     return_derivs=None,
                     **kw):
        # if self.system.max_expansion_order > 0:
        #     raise NotImplementedError(...)
        # else:
        if self.system.pointwise:
            base, opts = nput.apply_by_coordinates(self.get_conversion(), coords, **kw)
        elif self.system.batched:
            base, opts = self.convert(coords, **kw)
        else:
            base, opts = super().convert_many(coords, **kw)

        if return_derivs:
            if order is None or order == 0: order = 1

        if order > 0:
            if self.direction == 'inverse':
                test_jacobian = self.system.inverse_jacobian
                inv_jacobian = self.system.fwd_jacobian
            else:
                test_jacobian = self.system.fwd_jacobian
                inv_jacobian = self.system.inverse_jacobian

            if test_jacobian is not None:
                opts['derivs'] = test_jacobian(coords, order=order, **kw)
            elif inv_jacobian is not None:
                opts['derivs'] = nput.inverse_transformation(inv_jacobian(coords, order=order, **kw), order)

        return base, opts


# class TransformedCoordinateSystemConverter(CompositeCoordinateSystem):
#
#     def __init__(self, base_system, forward_transformation, reverse_transformation=None,
#                  name=None,
#                  batched=True, pointwise=False,
#                  **opts):
#         self.transformations = self.prep_transformations(forward_transformation, reverse_transformation)
#         super().__init__(base_system, self.apply_transformation, self.invert_transformation,
#                          name=name, batched=batched, pointwise=pointwise, **opts
#                          )
#
#     def prep_transformations(self):
#
#         if nput.is_numeric_array_like(forward_transformations):
#             forward_transformations = np.asanyarray(forward_transformations)
#             if forward_transformations.ndim == 2:
#                 forward_transformations = [forward_transformations]
#
#         if reverse_transformation is None:
#             reverse_transformation = nput.inverse_transformation(forward_transformations, len(forward_transformations))