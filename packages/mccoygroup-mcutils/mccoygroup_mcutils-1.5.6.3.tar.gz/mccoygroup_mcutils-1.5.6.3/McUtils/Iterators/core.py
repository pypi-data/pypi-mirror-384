import itertools
import numbers

__all__ = [
    "is_fixed_size",
    "consume",
    "chunked",
    "take_lists",
    "split",
    "split_by",
    "counts",
    "dict_diff",
    "transpose",
    "riffle",
    "flatten",
    "delete_duplicates"
]

def is_fixed_size(iterable):
    return hasattr(iterable, '__len__')

def consume(iterable, n, return_values=True):
    if return_values:
        return list(itertools.islice(iterable, n))
    else:
        return next(itertools.islice(iterable, n, n), None)

def chunked(a, upto):
    if is_fixed_size(a):
        l = len(a)
        blocks = (l // upto) +  (0 if (l % upto) == 0 else 1)
        for i in range(blocks):
            yield a[i*upto:(i+1)*upto]
    else:
        def consumer(a=a):
            return list(itertools.islice(a, upto))
        return iter(consumer, [])

def split(a, test=None):
    if is_fixed_size(a):
        prev = a[0]
        sep = 0
        for i, b in a[1]:
            if test(b, prev):
                yield a[sep:i+1]
                sep = i
                prev = b
    else:
        a, t = itertools.tee(a, 2)
        prev = next(t)
        sep = -1
        i = -1
        if test is None:
            test = lambda x,y: x != y
        for i, b in enumerate(t):
            if test(b, prev):
                yield consume(a, i + 1 - sep)
                sep = i
                prev = b
        yield consume(a, i + 1 - sep)

def split_by(a, canonicalizer):
    def test(next, prev, canonicalizer=canonicalizer, cache=[True, None]):
        if cache[0]:
            cache[1] = canonicalizer(prev)
        new = canonicalizer(next)
        ret = new != cache[1]
        cache[1] = new
        return ret
    return split(a, test)

def take_lists(a, splits):
    if is_fixed_size(a):
        sep = 0
        for s in splits:
            new = sep + s
            yield a[sep:new]
            sep = new
        if sep < len(a) - 1:
            yield a[sep:]
    else:
        for s in splits:
            yield consume(a, s)
def counts(iterable, test=None, hashable=True):
    if test is None: test = lambda x:x
    if hashable:
        counts_dict = {}
        for v in iterable:
            k = test(v)
            counts_dict[k] = counts_dict.get(k, 0) + 1
        return counts_dict
    else:
        keys = []
        counts = []
        for v in iterable:
            k = test(v)
            try:
                i = keys.index(k)
            except ValueError:
                keys.append(k)
                counts.append(1)
            else:
                counts[i] += 1

        return keys, counts

def dict_diff(iterable1:dict, iterable2):
    return {
        k:v
        for k,v in iterable1.items()
        if k not in iterable2 or v != iterable2[k]
    } | {k:iterable2[k] for k in iterable2.keys() - iterable1.keys()}

def transpose_iter(data, default=None):
    sentinel = object()
    any_full = True
    while any_full:
        any_full = False
        sublist = []
        for d in data:
            new = next(d, sentinel)
            if new is sentinel:
                sublist.append(default)
            else:
                any_full = True
                sublist.append(new)
        yield sublist
def transpose(data, default=None, pad=False):
    if is_fixed_size(data):
        fixed_data = is_fixed_size(data[0])
        if fixed_data:
            max_len = max(len(x) for x in data)
            if pad:
                return [
                    [d[i] if len(d) > i else default for d in data]
                    for i in range(max_len)
                ]
            else:
                return [
                    [d[i] for d in data if len(d) > i]
                    for i in range(max_len)
                ]
        else:
           return transpose_iter(data, default=default)
    else:
        return transpose(list(data), default=default) # need to cache results...

def riffle(a, b, *extras):
    if not is_fixed_size(a):
        a = list(a)
    l = len(a)
    n = -1
    for n,p in enumerate(zip(a, b, *extras)):
        if n == l - 1:
            yield p[0]
        else:
            for x in p:
                yield x
    for x in a[n+1:]: yield x # exhaust a

def _is_atomic(atomic_obj, atomic_types):
    if isinstance(atomic_obj, atomic_types): return True
    try:
        for _ in iter(atomic_obj): break
    except TypeError:
        return True
    return False

def flatten(iterable, atomic_types=None):
    if atomic_types is None:
        atomic_types = (int,str,float,numbers.Number)
    for o in iterable:
        if _is_atomic(o, atomic_types):
            yield o
        else:
            for f in flatten(o, atomic_types=atomic_types):
                yield f

def delete_duplicates(iterable, key=None, hashable=None, cache=None):
    hashable = hashable
    if cache is None:
        cache = set() if (hashable or hashable is None) else []
    elif hashable is None:
        hashable = hasattr(cache, 'add')
    if key is None:
        key = lambda x:x
    for o in iterable:
        test = key(o)
        if test in cache: continue
        if hashable is None:
            try:
                cache.add(test)
            except TypeError:
                cache = list(cache)
                hashable = False
        elif hashable:
            cache.add(test)
        else:
            cache.append(test)

        yield o