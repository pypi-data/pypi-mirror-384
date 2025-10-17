import functools

__all__ = [
    "mixedmethod"
]

class mixedmethod:
    def __init__(self, wrapped_fn):
        self.wrapped_fn = wrapped_fn
    def __get__(self, obj, obj_type=None):
        if obj_type is None:
            obj_type = type(obj)
        return functools.partial(self.wrapped_fn, obj if obj is not None else obj_type)