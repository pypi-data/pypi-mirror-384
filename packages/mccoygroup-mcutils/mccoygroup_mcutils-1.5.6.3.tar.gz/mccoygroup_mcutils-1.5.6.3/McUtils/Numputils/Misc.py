
import numpy as np

__all__ = [
    'infer_inds_dtype',
    'infer_int_dtype',
    'flatten_dtype',
    'unflatten_dtype',
    'recast_permutation',
    'recast_indices',
    'downcast_index_array',
    'numeric_types',
    'is_atomic',
    'is_numeric',
    'is_int',
    'is_zero',
    'is_array_like',
    'is_numeric_array_like',
    'flatten_inds'
]

int_types = (int, np.integer)
float_types = (float, np.floating)
numeric_types = int_types + float_types
atomic_types = numeric_types + (str, )
def is_atomic(obj, types=None):
    if types is None: types = atomic_types
    return isinstance(obj, types) or (
            isinstance(obj, np.ndarray) and obj.shape == () and is_atomic(obj[()], types)
    )
def is_numeric(obj, types=None):
    if types is None: types = numeric_types
    return is_atomic(obj, types=types)
def is_int(obj, types=None):
    if types is None: types = int_types
    return is_atomic(obj, types=types)
def is_zero(obj, numeric_types=None):
    return is_numeric(obj, types=numeric_types) and obj == 0

def is_array_like(obj, valid_dtypes=None, ndim=None):
    if isinstance(obj, np.ndarray):
        if ndim is None:
            return True
        else:
            return obj.ndim == ndim
    elif is_atomic(obj):
        return False
    else:
        try:
            arr = np.asanyarray(obj)
        except ValueError:
            return False
        else:
            if (
                    valid_dtypes is not None
                    and not any(np.issubdtype(arr.dtype, dt) for dt in valid_dtypes)
            ):
                return False
            elif arr.dtype == np.dtype(object):
                return False
            elif ndim is None:
                return True
            else:
                return arr.ndim == ndim
def is_numeric_array_like(obj, ndim=None):
    return is_array_like(obj, [np.number], ndim=ndim)

def downcast_index_array(a, max_val):
    return a.astype(infer_inds_dtype(max_val))

def recast_permutation(permutation_array):
    a = np.asanyarray(permutation_array)
    max_val = a.shape[-1]
    return downcast_index_array(a, max_val)

def recast_indices(indexing_array):
    a = np.asanyarray(indexing_array)
    max_val = np.max(a)
    return downcast_index_array(a, max_val)

def infer_inds_dtype(max_size):
    return np.min_scalar_type(max_size) # reset
    # needed the memory help back...
    # if max_size < 256:
    #     minimal_dtype = 'uint8'
    # elif max_size < 65535:
    #     minimal_dtype = 'uint16'
    # elif max_size < 4294967295:
    #     minimal_dtype = 'uint32'
    # else:
    #     minimal_dtype = 'uint64'
    # return minimal_dtype

def infer_int_dtype(max_dim):
    return np.min_scalar_type(-(max_dim+1))
    # max_dim = abs(max_dim)
    # if max_dim < 128:
    #     minimal_dtype = 'int8'
    # elif max_dim < 32768:
    #     minimal_dtype = 'int16'
    # elif max_dim < 2147483648:
    #     minimal_dtype = 'int32'
    # else:
    #     minimal_dtype = 'int64'
    # return minimal_dtype

def flatten_dtype(ar, dtype=None):
    """
    Extracted from the way NumPy treats unique
    Coerces ar into a compound dtype so that it can be treated
    like a 1D array for set operations
    """

    # Must reshape to a contiguous 2D array for this to work...
    orig_shape, orig_dtype = ar.shape, ar.dtype
    ar = ar.reshape(orig_shape[0], np.prod(orig_shape[1:], dtype=np.intp))
    ar = np.ascontiguousarray(ar)
    if dtype is None:
        dtype = [('f{i}'.format(i=i), ar.dtype) for i in range(ar.shape[1])]
    # At this point, `ar` has shape `(n, m)`, and `dtype` is a structured
    # data type with `m` fields where each field has the data type of `ar`.
    # In the following, we create the array `consolidated`, which has
    # shape `(n,)` with data type `dtype`.
    try:
        if ar.shape[1] > 0:
            consolidated = ar.view(dtype)
            if len(consolidated.shape) > 1:
                consolidated = consolidated.squeeze()
                if consolidated.shape == ():
                    consolidated = np.expand_dims(consolidated, 0)
        else:
            # If ar.shape[1] == 0, then dtype will be `np.dtype([])`, which is
            # a data type with itemsize 0, and the call `ar.view(dtype)` will
            # fail.  Instead, we'll use `np.empty` to explicitly create the
            # array with shape `(len(ar),)`.  Because `dtype` in this case has
            # itemsize 0, the total size of the result is still 0 bytes.
            consolidated = np.empty(len(ar), dtype=dtype)
    except TypeError:
        # There's no good way to do this for object arrays, etc...
        msg = 'The axis argument to `coerce_dtype` is not supported for dtype {dt}'
        raise TypeError(msg.format(dt=ar.dtype))

    return consolidated, dtype, orig_shape, orig_dtype

def unflatten_dtype(consolidated, orig_shape, orig_dtype, axis=None):
    """
    Converts a coerced array back to a full array
    :param consolidated:
    :type consolidated:
    :param orig_shape:
    :type orig_shape:
    :param orig_dtype:
    :type orig_dtype:
    :param axis: where to shift the main axis
    :type axis:
    :return:
    :rtype:
    """
    n = len(consolidated)
    uniq = consolidated.view(orig_dtype)
    uniq = uniq.reshape(n, *orig_shape[1:])
    if axis is not None:
        uniq = np.moveaxis(uniq, 0, axis)
    return uniq


def flatten_inds(A, *idx_blocks):
    idx_blocks = [
        (
            (i + A.ndim) if i < 0 else i,
            (j + A.ndim) if j < 0 else j
        )
        for i, j in idx_blocks
    ]
    block_map = {
        i: np.prod(A.shape[i:j+1], dtype=int)
        for i, j in idx_blocks
    }
    new_shape = [
        A.shape[k]
        if not any(i <= k and k <= j for i, j in idx_blocks) else
        block_map.get(k)
        for k in range(A.ndim)
    ]
    new_shape = [s for s in new_shape if s is not None]

    return A.reshape(new_shape)