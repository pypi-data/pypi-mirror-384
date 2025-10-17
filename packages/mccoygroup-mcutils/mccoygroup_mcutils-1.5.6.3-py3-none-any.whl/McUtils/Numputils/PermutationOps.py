import collections

import numpy as np
from . import Misc as misc
from . import SetOps as sets
from . import VectorOps as vec_ops

__all__ = [
    "permutation_sign",
    "levi_cevita_maps",
    "levi_cevita_tensor",
    "levi_cevita3",
    "levi_cevita_dot",
    "normalize_commutators",
    "commutator_terms",
    "commutator_evaluate",
    "permutation_cycles",
    "enumerate_permutations"
]


def permutation_sign(perm, check=True):
    # essentially a swap sort on perm
    # https://stackoverflow.com/a/73511014
    parity = 1
    perm = np.asanyarray(perm)
    if check:
        perm = np.argsort(np.argsort(perm))
    else:
        perm = perm.copy()
    for i in range(len(perm)):
        while perm[i] != i: # ensure subblock is sorted
            parity *= -1
            j = perm[i]
            perm[i], perm[j] = perm[j], perm[i]
    return parity
def levi_cevita_maps(k):
    perms = sets.permutation_indices(k, k)
    signs = np.array([permutation_sign(p, check=False) for p in perms])
    return perms, signs
def levi_cevita_tensor(k, sparse=False):
    pos, vals = levi_cevita_maps(k)
    if sparse:
        from .Sparse import SparseArray
        a = SparseArray.from_data(
            (
                pos.T,
                vals
            ),
            shape=(k,)*k
        )
    else:
        a = np.zeros((k,)*k, dtype=int)
        a[tuple(pos.T)] = vals
    return a
# levi_cevita3 = levi_cevita_tensor(3)
levi_cevita3 = np.array([
    [[0, 0, 0],
     [0, 0, 1],
     [0, -1, 0]],

    [[0, 0, -1],
     [0, 0, 0],
     [1, 0, 0]],

    [[0, 1, 0],
     [-1, 0, 0],
     [0, 0, 0]]
])

def levi_cevita_dot(k, a, /, axes, shared=None):
    pos, vals = levi_cevita_maps(k)
    return vec_ops.semisparse_tensordot((tuple(pos.T), vals, (k,) * k), a, axes, shared=shared)

def _flatten_comstr(cs):
    for o in cs:
        if isinstance(o, (int, np.integer)):
            yield o
        else:
            for f in _flatten_comstr(o):
                yield f

def normalize_commutators(commutator_string):
    a, b = commutator_string
    a_int = isinstance(a, (int, np.integer))
    b_int = isinstance(b, (int, np.integer))
    if b_int and a_int:
        return [1], [commutator_string], [a, b]
    elif a_int:
        ps, bs, ts = normalize_commutators(b)
        return [-p for p in ps], [
            [b, a]
            for b in bs
        ], ts + [a]
    elif b_int:
        ps, as_, ts = normalize_commutators(a)
        return [p for p in ps], [
            [a, b]
            for a in as_
        ], ts + [b]
    else:
        aa, bb = a
        aa_int = isinstance(aa, (int, np.integer))
        bb_int = isinstance(bb, (int, np.integer))
        cc, dd = b
        cc_int = isinstance(cc, (int, np.integer))
        dd_int = isinstance(dd, (int, np.integer))

        if aa_int and bb_int:
            if cc_int and dd_int:
                forms = [
                    [[[aa, bb], cc], dd],
                    [[[dd, aa], bb], cc],
                    [[[cc, dd], aa], bb],
                    [[[bb, cc], dd], aa]
                ]
                phases = [1, 1, 1, 1]
                terms = [aa, bb, cc, dd]
                return phases, forms, terms
            else:
                pb, bs_, tb = normalize_commutators(b)
                return [-p for p in pb], [
                    [b, a]
                    for b in bs_
                ], tb + [aa, bb]
        elif cc_int and dd_int:
            pa, as_, ta = normalize_commutators(a)
            return [p for p in pa], [
                [a, b]
                for a in as_
            ], ta + [cc, dd]
        else:
            pa, as_, ta = normalize_commutators(a)
            pb, bs_, tb = normalize_commutators(b)
            if len(tb) > len(ta):
                return [
                    -p1 * p2
                    for p2 in pb
                    for p1 in pa
                ], [
                    [b, a]
                    for b in bs_
                    for a in as_
                ], tb + ta
            else:
                return [
                    p1 * p2
                    for p1 in pa
                    for p2 in pb
                ], [
                    [a, b]
                    for a in as_
                    for b in bs_
                ], ta + tb

def _setup_com_terms(full_phases, storage, i0, idx, j0, j, term):
    a,b = term
    if isinstance(a, (int, np.integer)): # simple swap, nothing more needed
        prev = storage[i0:i0+idx]
        n = idx * 2
        new = storage[i0+idx:i0+n]
        new[:, :j0] = prev[:, :j0]
        new[:, j0], new[:, j0+1:j+j0+1] = prev[:, j0+j], prev[:, j0:j0+j]
        full_phases[i0+idx:i0+n] = -full_phases[i0:i0+idx]
        j = j + 1
    else:
        idx, j = _setup_com_terms(full_phases, storage, i0, idx, j0, j, a)
        if isinstance(b, (int, np.integer)): # swap all priors
            n = idx * 2
            prev = storage[i0:i0+idx]
            new = storage[i0 + idx:i0 + n]
            new[:, :j0] = prev[:, :j0]
            new[:, j0], new[:, j0 + 1:j + j0 + 1] = prev[:, j0 + j], prev[:, j0:j0 + j]
            full_phases[i0+idx:i0+n] = -full_phases[i0:i0+idx]
            j = j + 1
        else:
            n, j1 = _setup_com_terms(full_phases, storage, i0, idx, j, 1, b)
            idx = n
            n = 2 * n
            prev = storage[i0:i0+idx]
            new = storage[i0+idx:i0+n]
            new[:, j0:j0+j1], new[:, j0+j1:j0+j1+j] = prev[:, j0+j:j0+j+j1], prev[:, j0:j0+j]
            full_phases[i0+idx:i0+n] = -full_phases[i0:i0+idx]
    return n, j

def commutator_terms(commutator_strings):
    phases, normal_forms, symbols = normalize_commutators(commutator_strings)
    storage = np.full((2**(len(symbols)-1), len(symbols)), symbols)
    full_phases = np.ones(len(storage), dtype=int)
    idx = 0
    for base_phase,term in zip(phases, normal_forms):
        nx, _ = _setup_com_terms(full_phases, storage, idx, 1, 0, 1, term)
        full_phases[idx:idx+nx] *= base_phase
        idx += nx

    return full_phases, storage

def commutator_evaluate(commutator, expansion_terms, normalized=False, direct=None, recursive=False):
    if recursive:
        a,b = commutator
        if not isinstance(a, (int, np.integer)):
            a = commutator_evaluate(a, expansion_terms, recursive=True)
        else:
            a = expansion_terms[a]
        if not isinstance(b, (int, np.integer)):
            b = commutator_evaluate(b, expansion_terms, recursive=True)
        else:
            b = expansion_terms[b]
        return a@b - b@a

    if direct is None:
        test_phases, test_terms = commutator
        direct = (
                isinstance(test_phases, (int, np.integer))
                or not isinstance(test_phases[0], (int, np.integer))
                or not (abs(test_phases[-1]) == 1 and abs(test_phases[0]) == 1)
        )
    if direct:
        terms = collections.deque()
        terms.append([(0,), commutator])
        exprs = {}
        while terms:
            idx, (a,b) = terms.pop()
            ta = exprs.pop(idx + (0,), None)
            tb = exprs.pop(idx + (1,), None)
            if ta is None and isinstance(a, (int, np.integer)):
                ta = expansion_terms[a]
            if tb is None and isinstance(b, (int, np.integer)):
                tb = expansion_terms[b]
            if ta is not None and tb is not None:
                exprs[idx] = ta @ tb - tb @ ta
            else:
                terms.append([idx,(None, None)]) # by the time this comes back up we expect those to be filled in
                if tb is None:
                    terms.append([idx+(1,), b])
                else:
                    exprs[idx+(1,)] = tb
                if ta is None:
                    terms.append([idx+(0,), a])
                else:
                    exprs[idx+(0,)] = ta
        return exprs[(0,)]
    else:
        if not normalized:
            commutator = commutator_terms(commutator)
        phases, terms = commutator
        comm = 0
        for p,t in zip(phases, terms):
            res = expansion_terms[t[0]]
            for i in t[1:]:
                res = res @ expansion_terms[i]
            if p < 0:
                comm -= res
            else:
                comm += res
        return comm


def permutation_cycles(perms, return_groups=False):
    # since cycles have no set size, this can't be efficiently vectorized
    # a much better candidate for speeding up with numba if we need it
    perms = np.asanyarray(perms)
    if return_groups and perms.ndim > 2:
        raise ValueError(
            f"can't destructure permutations of shape {perms.shape} into groups, "
            "try `return_groups=False` to just get labels"
        )
    base_shape = perms.shape[:-1]
    perms = perms.reshape(-1, perms.shape[-1])

    labels = np.full(perms.shape, -1, dtype=int)
    group_indicators = np.zeros(len(perms), dtype=int)
    for i in range(perms.shape[-1]):
        mask = np.where(labels[:, i] < 0)
        if len(mask) == 0 or len(mask[0]) == 0:
            continue

        mask = mask[0]
        start = new = perms[mask, i]
        x = group_indicators[mask,]
        group_indicators[mask,] += 1
        for _ in range(perms.shape[-1]):
            labels[mask, new] = x
            new = perms[mask, new]
            checks = np.where(start == new)
            if len(checks) > 0 and len(checks[0]) > 0:
                checks = checks[0]
                if len(checks) == len(mask): break
                rem = np.delete(np.arange(len(mask)), checks)
                mask = mask[rem,]
                x = x[rem,]
                new = new[rem,]
                start = start[rem,]
            labels[mask, new] = x

    labels = labels.reshape(base_shape + (labels.shape[-1],))
    if return_groups:
        if labels.ndim == 1:
            groups = sets.group_by(np.arange(len(labels)), labels)[0][1]
            return [
                perms[0][g] for g in groups
            ]
        elif labels.ndim == 2:
            cycle_lists = []
            for l, p in zip(labels, perms):
                groups = sets.group_by(np.arange(len(l)), l)[0][1]
                cycle_lists.append([
                    p[g] for g in groups
                ])
            return cycle_lists

    return labels
def permutation_from_cycles(cycle):
    base_concat = np.concatenate(cycle, axis=-1)
    subconcat = np.concatenate([np.roll(p, 1, axis=-1) for p in cycle])
    sort = np.argsort(base_concat, axis=-1)
    return subconcat[sort]

def compute_cycle_orders(perms):
    perms = np.asanyarray(perms)
    if perms.ndim == 1:
        groups = permutation_cycles(perms, return_groups=True)
        cycle_orders = np.prod([len(g) for g in groups], dtype=int)
    else:
        cycles = permutation_cycles(perms, return_groups=False).view('uint64')  # want underflow
        max_cycle_size = np.max(cycles)
        cycle_orders = np.ones(perms.shape[:-1], dtype=int)
        cycles = np.sort(cycles)
        for i in range(max_cycle_size):
            subcounts = sets.fast_first_nonzero(cycles)
            subcounts[subcounts < 0] = perms.shape[-1]
            subcounts[subcounts == 0] = 1
            cycle_orders *= subcounts
            cycles = np.sort(cycles - 1)  # yes I should do this better but...
    return cycle_orders

def enumerate_permutations(perm, cycle_orders=None):
    perm = np.asanyarray(perm)
    if perm.ndim == 1:
        if cycle_orders is None:
            groups = permutation_cycles(perm, return_groups=True)
            cycle_orders = np.prod([len(g) for g in groups], dtype=int)
        perms = np.empty((cycle_orders, perm.shape[-1]), dtype=perm.dtype)
        perms[0, :] = perm
        for i in range(1, cycle_orders):
            perms[i, :] = perms[i-1, :][perm,]
        return perms
    elif perm.ndim > 2:
        raise NotImplementedError("too annoying to do ndim > 2")
    else:
        if cycle_orders is None:
            cycle_orders = compute_cycle_orders(perm)
        return [
            enumerate_permutations(p, c)
            for p,c in zip(perm, cycle_orders)
        ]


