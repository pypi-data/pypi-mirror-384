import itertools
import numpy as np
# import scipy as scipy

from .. import Combinatorics as comb
from .. import Numputils as nput

__all__ = [
    "CharacterTable",
    "symmetric_group_class_sizes",
    "symmetric_group_character_table",
    "point_group_data",
    # "parametrized_point_group_matrices"
    # "dihedral_group_character_table",
    # "dihedral_group_classes",
]

def check_boundary_strip_sst(vals, sst):
    diffs = []

    # check for 2x2 blocks
    for i,row in enumerate(sst[:-1]):
        if len(diffs) < i+1:
            diffs.append(np.diff(row))
        dd = diffs[i]
        eq_pos = np.where(dd == 0)
        if len(eq_pos) == 0: continue
        for p in eq_pos[0]:
            if len(diffs) < i + 2:
                diffs.append(np.diff(sst[i+1]))
            d2 = diffs[i+1]
            if (
                    len(d2) > p
                    and d2[p] == 0
                    and sst[i][p] == sst[i+1][p]
                    and sst[i][p+1] == sst[i+1][p+1]
            ):
                return False

    # check for connected-ness
    for v in vals:
        pos = []
        for i,r in enumerate(sst):
            j = np.where(r == v)
            if len(j) > 0 and len(j[0]) > 0:
                pos.extend([i,jj] for jj in j[0])
        if len(pos) > 1:
            pos = np.array(pos)
            dm = nput.distance_matrix(pos)
            np.fill_diagonal(dm, 2)
            min_vals = np.min(dm, axis=1)
            if np.max(min_vals) > 1:
                return False

    return True

def _group_size(n, p):
    p, c = np.unique(p, return_counts=True)
    num_terms = np.arange(n+1)[2:]
    denom_terms = sum(
        ([pp]*cc + list(range(cc+1))[2:] for pp, cc in zip(p, c)),
        []
    )
    return comb.stable_factorial_ratio(num_terms, denom_terms)

def symmetric_group_class_sizes(n, partitions=None):
    if partitions is None:
        partitions = reversed(list(itertools.chain(*comb.IntegerPartitioner.partitions(n))))
    return np.array([_group_size(n, p) for p in partitions])

def symmetric_group_character_table(n, tableaux=None, partitions=None, return_partitions=False, return_weights=False):
    if tableaux is None:
        tableaux, _ = comb.YoungTableauxGenerator(n).get_standard_tableaux(return_partitions=True)
        if partitions is None:
            partitions = list(reversed(_))
    characters = []
    if partitions is None:
        partitions = list(reversed(list(itertools.chain(*comb.IntegerPartitioner.partitions(n)))))

    for p in partitions:
        vals = list(range(1, len(p)+1))
        types = np.concatenate([[i + 1] * k for i, k in enumerate(p)])
        subcharacters = []
        for sst_set in tableaux:
            term = 0
            seen = set()
            for sst in zip(*sst_set):
                sst = [types[b,] for b in sst]
                key = tuple(np.concatenate(sst))
                if key in seen: continue
                seen.add(key)
                from McUtils.Formatters import TableFormatter
                cbs = check_boundary_strip_sst(vals, sst)
                # print(cbs)
                # print(TableFormatter("").format(sst))
                if cbs:
                    heights = {}
                    for row in sst:
                        for k in np.unique(row):
                            heights[k] = 1 + heights.get(k, -1)
                    term += (-1)**(sum(heights.values()))
            subcharacters.append(term)
        characters.append(subcharacters)

    ct = np.array(characters).T
    if return_partitions or return_weights:
        res = (ct,)
        if return_partitions:
            res = res + (partitions,)
        if return_weights:
            res = res + (symmetric_group_class_sizes(n, partitions),)
        return res
    else:
        return ct

def cyclic_group_character_table(n):
    table = np.zeros((n, n), dtype=complex)
    table[0] = 1
    inds = np.arange(1, n)[:, np.newaxis] * np.arange(n)[np.newaxis, :]
    table[1:] = np.exp(2j*np.pi*inds/n)
    return table

def cyclic_permutations(n):
    elements = np.zeros((n, n), dtype=int)
    elements[0] = np.arange(n)
    for i in range(1, n):
        elements[i, :n-i] = elements[0][i:]
        elements[i, -i:] = elements[0][:i]
    return elements
def cyclic_group_classes(n):
    # cyclic permutations, kinda slow
    elements = cyclic_permutations(n)
    classes = np.arange(n)[:, np.newaxis]

    return elements, classes

def cyclic_group_operation_representation(n, elements=None, check_mod=True):
    if elements is None:
        elements = np.arange(n)

    elements = np.asanyarray(elements)
    base_elems = elements % n
    elements, inv = np.unique(base_elems, return_inverse=True)

    # base rotation matrices
    x = (2 * np.pi * elements) / n
    c = np.cos(x)
    s = np.sin(x)
    z = np.zeros(len(x))
    a = np.ones(len(x))
    base_elems = np.moveaxis(
        np.array([
            [ c, s, z],
            [-s, c, z],
            [ z, z, a]
        ]),
        -1,
        0
    )

    return base_elems[inv,]

def cyclic_group_irrep_names(n):
    names = ["A"]
    if n % 2 == 0:
        names.append("B")
    if n < 4:
        names.extend(["Ea", "Eb"])
    else:
        for i in range( (n - (n%2)) // 2 ):
            names.extend([f"Ea[{i+1}]", f"Eb[{i+1}]"])
    return names



def dihedral_group_character_table(n):
    # if n < 3:
    #     raise ValueError("no dihedral group under 3 elements")

    # if n == 3:
    #     return symmetric_group_character_table(3)

    k = (2*n + 9 + 3*(-1)**n) // 4
    table = np.zeros((k, k))
    if n % 2 == 0:
        m = n // 2
        inds = np.arange(1, m)[:, np.newaxis] * np.arange(m+1)[np.newaxis, :]
        alt = (-1)**np.arange(m+1)
        table[:4] = 1
        table[1, -1] = -1
        table[1, -2] = -1
        table[2, :-2] = alt
        table[2, -1] = -1
        table[3, :-2] = alt
        table[3, -2] = -1
        table[4:, :-2] = 2*np.cos(2*np.pi*inds/n)
    else:
        m = (n - 1) // 2
        inds = np.arange(1, m+1)[:, np.newaxis] * np.arange(m+1)[np.newaxis, :]
        table[:2] = 1
        table[1, -1] = -1
        table[2:, :-1] = 2*np.cos(2*np.pi*inds/n)

    if np.sum(np.abs(table - np.round(table))) < 1e-6:
        table = np.round(table).astype(int)

    return table

def dihedral_group_classes(n):
    if n == 1:
        elements = np.array([
            [0, 1],
            [1, 0]
        ])
    elif n == 2:
        elements = np.array([
            [0, 1, 2, 3],
            [0, 1, 3, 2],
            [1, 0, 2, 3],
            [1, 0, 3, 2]
        ])
    else:
        # cyclic permutations, kinda slow
        elements = np.zeros((2*n, n), dtype=int)
        elements[0] = np.arange(n)
        for i in range(1, n):
            elements[i, :n-i] = elements[0][i:]
            elements[i, -i:] = elements[0][:i]
        elements[n:] = np.flip(elements[:n], axis=1)

    if n % 2 == 1:
        classes = [np.array([0])] + [
            np.array([i + 1, n - i - 1])
            for i in range((n - 1) // 2)
        ] + [
            np.arange(n, 2*n)
        ]
    else:
        classes = [np.array([0])] + [
            np.array([i + 1, n - i])
            for i in range((n - 1) // 2)
        ] + [np.array([n//2])] + [
            np.arange(n, 2 * n, 2),
            np.arange(n+1, 2 * n, 2)
        ]
    return elements, classes

def dihedral_group_operation_representation(n, elements=None):
    if elements is None:
        elements = np.arange(2*n)
    elements = np.asanyarray(elements)
    cyclics = cyclic_group_operation_representation(n, elements)
    refl = np.where((elements//n) % 2 == 1)
    if len(refl) > 0 and len(refl[0]) > 0:
        refl_mat = np.array([[
            [1,  0, 0],
            [0, -1, 0],
            [0,  0, 1]
        ]])
        #TODO: speed this up in case of large n?
        cyclics[refl] = refl_mat @ cyclics[refl]

    return cyclics

def cv_group_irrep_names(n):
    if n == 1:
        names = ["A'", "A''"]
    elif n % 2 == 0:
        names = ["A1", "A2", "B1", "B2"]
        if n == 4:
            names.append("E")
        else:
            for i in range(n//2 - 1):
                names.append(f"E{i+1}")
    else:
        names = ["A1", "A2"]
        if n == 3:
            names.append("E")
        else:
            for i in range((n-1)//2):
                names.append(f"E{i+1}")
    return names

def d_group_matrices(n, elements=None):
    if elements is None:
        elements = np.arange(2*n)
    elements = np.asanyarray(elements)
    cyclics = cyclic_group_operation_representation(n, elements)
    refl = np.where((elements//n) % 2 == 1)
    if len(refl) > 0 and len(refl[0]) > 0:
        refl_mat = np.array([[
            [1, 0, 0],
            [0, -1, 0],
            [0, 0, -1]
        ]])
        #TODO: speed this up in case of large n?
        cyclics[refl] = refl_mat @ cyclics[refl]

    return cyclics

def dh_group_character_table(n):
    if n % 2 == 1:
        table = np.zeros((n+3, n+3), dtype=float)
        table[0] = 1
        table[1] = 1
        k = (n + 1) // 2
        table[1, k] = -1
        table[1, -1] = -1
        m = (n - 1) // 2
        inds = np.arange(1, m+1)[:, np.newaxis] * np.arange(m+1)[np.newaxis, :]
        j = (n+3)//2
        table[2:j, :m+1] = 2*np.cos(2*np.pi*inds/n)
        table[2:j, m+2:-1] = table[2:j, :m+1]
        table[j:] = table[:j] @ np.diag(np.concatenate([np.ones(j), -np.ones(j)]))
    else:
        table = np.zeros((n+6, n+6), dtype=float)
        table[:2] = 1
        k = n // 2
        table[1, k+1:k+3] = -1
        table[1, -2:] = -1

        table[2, :k+1] = (-1)**np.arange(k+1)
        table[2, k+2] = -1
        table[2, -1] = -1
        table[2, k+1] = 1
        table[2, -2] = 1
        table[2, k+3:2*k+4] = table[2, :k+1]

        table[3] = table[2]
        table[3, k+2] = 1
        table[3, -1] = 1
        table[3, k+1] = -1
        table[3, -2] = -1

        inds = np.arange(1, k)[:, np.newaxis] * np.arange(k+1)[np.newaxis, :]
        table[4:4+k-1, :k+1] = 2*np.cos(2*np.pi*inds/n)
        table[4:4+k-1, k+3:2*k+4] = table[4:4+k-1, :k+1]

        table[4+k-1:] = table[:4+k-1] @ np.diag(np.concatenate([np.ones(k+3), -np.ones(k+3)]))

    if np.sum(np.abs(table - np.round(table))) < 1e-6:
        table = np.round(table).astype(int)

    return table

def dh_group_classes(n):
    if n % 2 == 1:
        c1 = np.arange((n-3)//4+1)
        c1 = np.array([n - (2*c1 + 1), n + 2*c1 + 1]).T
        c2 = np.arange((n-5)//4+1)
        c2 = np.array([2 + 2*c2, 2*n - 2*c2 - 2]).T
        c3 = np.arange(2, n, 2)
        c3 = np.array([c3 - 1, 2*n - c3 + 1]).T
        classes = [
            np.array([0])
        ] + [
            p
            for r in zip(c1, c2)
            for p in r
        ] + list(
            c1[len(c2):]
        ) + [
            np.arange(2*n, 4*n, 2),
            np.array([n])
        ] + list(
            c3
        ) + [
            np.arange(2*n+1, 4*n, 2),
        ]
        classes = [
            c for c in classes
            if len(c) > 0
        ]

        elements = dihedral_group_classes(2*n)[0]

    else:
        c1 = np.arange(1, n//2)
        c1 = np.array([c1, n - c1]).T
        c2 = np.arange(5*(n//2), 2*n+1, -1)
        c2 = np.array([c2-1, 5*n + 1 - c2]).T
        classes = [
            np.array([0])
        ] + list(c1) + [
            np.array([n//2]),
            np.arange(n, 2*n, 2),
            np.arange(n+1, 2*n, 2),
            np.array([2*n])
        ] + list(c2) + [
            np.array([5*(n//2)]),
            np.arange(3*n, 4*n, 2),
            np.arange(3*n+1, 4*n+1, 2)
        ]

        elements=np.array(list(_permutation_product([
            cyclic_permutations(2),
            dihedral_group_classes(n)[0]
        ])))

    return elements, classes

def dh_group_matrices(n, elements=None):
    if elements is None:
        elements = np.arange(4*n)
    elements = np.asanyarray(elements)
    if n == 2:
        flips = [
            (),
            (0, 1),
            (0, 2),
            (1, 2),
            (0, 1, 2),
            (2),
            (1),
            (0)
        ]
        flips = [flips[e] for e in elements]
        diags = np.ones((len(flips), 3))
        for i,f in flips:
            diags[i, f] = -1
        return nput.vec_tensordiag(diags)
    elif n%2 == 1:
        dihedrals = improper_rotation_group_operation_representation(2*n, elements)
        refl = np.where((elements // (2*n)) % 2 == 1)
        if len(refl) > 0 and len(refl[0]) > 0:
            refl_mat = np.array([[
                [1,  0,  0],
                [0, -1,  0],
                [0,  0, -1]
            ]])
            # TODO: speed this up in case of large n?
            dihedrals[refl] = refl_mat @ dihedrals[refl]
        return dihedrals
    else:
        cyclics = cyclic_group_operation_representation(n, elements)
        mods = (elements // n) % 4
        for key,refs in zip(*nput.group_by(np.arange(len(mods)), mods)[0]):
            if key > 0 and len(refs) > 0:
                if key == 1:
                    refl_mat = np.array([[
                        [1,  0,  0],
                        [0, -1,  0],
                        [0,  0, -1]
                    ]])
                    cyclics[refs,] = refl_mat @ cyclics[refs]
                elif key == 2:
                    refl_mat = np.array([[
                        [-1,  0,  0],
                        [0, -1,  0],
                        [0,  0, -1]
                    ]])
                    cyclics[refs,] = refl_mat @ cyclics[refs]
                else:
                    refl_mat = np.array([[
                        [-1, 0, 0],
                        [0, 1, 0],
                        [0, 0, 1]
                    ]])
                    cyclics[refs,] = refl_mat @ cyclics[refs]
        return cyclics

def dh_group_names(n):
    if n % 2 == 0:
        names = cv_group_irrep_names(n)
        names = [n+"g" for n in names] + [n+"u" for n in names]
    else:
        names = cv_group_irrep_names(n)
        names = [n+"'" for n in names] + [n+"''" for n in names]
    return names


def dd_group_character_table(n):
    if n % 2 == 1:
        return dh_group_character_table(n)
    else:
        return dihedral_group_character_table(2*n)

def dd_group_classes(n):
    if n % 2 == 1:
        c1 = np.arange(2, n, 2)
        c1 = np.array([c1, 2*n-c1]).T
        c2 = np.arange(n-2, 0, -2)
        c2 = np.array([c2, 2*n-c2]).T
        classes = [
            np.array([0]),
        ] + list(c1) + [
            np.arange(2*n, 4*n, 2),
            np.array([n])
        ] + list(c2) + [
            np.arange(2*n+1, 4*n, 2)
        ]
        classes = [
            c for c in classes
            if len(c) > 0
        ]

        elements = dihedral_group_classes(2*n)[0]
        return elements, classes
    else:
        return dihedral_group_classes(2*n)

def dd_group_matrices(n, elements=None):
    if elements is None:
        elements = np.arange(4*n)
    elements = np.asanyarray(elements)

    imp_rots = improper_rotation_group_operation_representation(2*n, elements)
    refl = np.where((elements // (2 * n)) % 2 == 1)
    if len(refl) > 0 and len(refl[0]) > 0:
        refl_mat = np.array([[
            [1, 0, 0],
            [0, -1, 0],
            [0, 0, -1]
        ]])
        # TODO: speed this up in case of large n?
        imp_rots[refl] = refl_mat @ imp_rots[refl]
    return imp_rots

def dd_group_names(n):
    if n % 2 == 0:
        names = cv_group_irrep_names(2*n)
    else:
        names = cv_group_irrep_names(n)
        names = [n+"g" for n in names] + [n+"u" for n in names]
    return names

def _permutation_product(perms_lists):
    perm_sizes = np.array([0] + [p.shape[-1] for p in perms_lists])
    perm_shifts = np.cumsum(perm_sizes[:-1])
    actual_perms = [
        p+s
        for p,s in zip(perms_lists, perm_shifts)
    ]
    for p in itertools.product(*actual_perms):
        yield np.concatenate(p)

def cycle_decomposition_permutation_product(n):
    primes, orders = comb.prime_factorize(n)
    primes = np.array(primes)
    orders = np.array(orders)
    mask = np.where(orders > 0)
    factors = -np.sort(-np.concatenate([primes[mask]**orders[mask], [2]]))
    elements = np.array(list(_permutation_product([
        cyclic_permutations(m)
        for m in factors
    ])))

    return elements

def improper_rotation_group_character_table(n):
    if n % 2 == 1:
        raise ValueError("improper rotation groups must be even")
    if n % 4 == 0:
        table = np.zeros((n, n), dtype=complex)
        table[0] = 1
        table[1] = (-1)**np.arange(n)
        inds = np.arange(1, n//2)[:, np.newaxis] * np.arange(n)[np.newaxis, :]
        table[2::2] = np.exp(inds*2j*np.pi/n)
        table[3::2] = np.exp(-inds*2j*np.pi/n)
    else:
        table = np.zeros((n, n), dtype=complex)
        table[0] = 1
        inds = np.arange(1, (n-2)//4 + 1)[:, np.newaxis] * np.arange(n)[np.newaxis, :]
        m = n//2
        table[1:m:2] = np.exp(inds*4j*np.pi/n)
        table[2:m:2] = np.exp(-inds*4j*np.pi/n)
        table[m:] = table[:m] @ np.diag(np.concatenate([np.ones(m), -np.ones(m)]))
    return table

def improper_rotation_group_classes(n):
    if n % 2 == 1:
        elements = cycle_decomposition_permutation_product(n)
    else:
        elements = cyclic_permutations(n)

    if n % 4 == 0:
        classes = np.arange(n)[:, np.newaxis]
    elif n % 2 == 0:
        classes = np.concatenate([
            np.arange(0, n, 2),
            (n//2 + 2*np.arange(n//2)) % n
        ])[:, np.newaxis]
    else:
        classes = np.arange(2*n)[:, np.newaxis]

    return elements, classes

def improper_rotation_group_operation_representation(n, elements=None):
    if elements is None:
        elements = np.arange(n)
    elements = np.asanyarray(elements)
    cyclics = cyclic_group_operation_representation(n, elements)
    cyclics[:, 2, 2] = (-1)**(elements)

    return cyclics

def improper_rotation_group_names(n):
    names = cyclic_group_irrep_names(n)
    if n % 2 == 1:
        names = [n+"'" for n in names] + [n+"''" for n in names]
    return names

def ch_group_character_table(n):
    # rewrite in terms of diag
    table = np.zeros((2*n, 2*n), dtype=complex)
    table[0] = 1
    inds = np.arange(1, n)[:, np.newaxis] * np.arange(2*n)[np.newaxis, :]
    table[1:n] = np.exp(inds*2j*np.pi/n)
    table[n:] = table[:n] @ np.diag(np.concatenate([np.ones(n), -np.ones(n)]))
    return table

def ch_group_classes(n):
    # get cycle decomposition
    elements = cycle_decomposition_permutation_product(n)

    if n % 2 == 0:
        classes = np.concatenate([
            np.arange(n),
            np.arange((3*n)//2, 2*n),
            np.arange(n, (3 * n) // 2),
        ])[:, np.newaxis]
    else:
        classes = np.arange(2*n)[:, np.newaxis]
    return elements, classes

def ch_group_matrices(n, elements=None):
    if elements is None:
        elements = np.arange(2*n)
    elements = np.asanyarray(elements)
    cyclics = cyclic_group_operation_representation(n, elements)
    refl = np.where((elements//n) % 2 == 1)
    if len(refl) > 0 and len(refl[0]) > 0:
        refl_mat = np.array([[
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, -1]
        ]])
        #TODO: speed this up in case of large n?
        cyclics[refl] = refl_mat @ cyclics[refl]

    return cyclics

def ch_group_names(n):
    names = cyclic_group_irrep_names(n)
    if n % 2 == 1:
        names = [n+"'" for n in names] + [n+"''" for n in names]
    else:
        names = [n+"g" for n in names] + [n+"u" for n in names]
    return names


point_group_map = {
    'Cv':{
        "characters":dihedral_group_character_table,
        "classes":dihedral_group_classes,
        "matrices":dihedral_group_operation_representation,
        "names":cv_group_irrep_names
    },
    'S':{
        "characters":improper_rotation_group_character_table,
        "classes":improper_rotation_group_classes,
        "matrices":improper_rotation_group_operation_representation,
        "names":improper_rotation_group_names
    },
    'D':{
        "characters":dihedral_group_character_table,
        "classes":dihedral_group_classes,
        "matrices":d_group_matrices,
        "names":cv_group_irrep_names
    },
    'Dh':{
        "characters":dh_group_character_table,
        "classes":dh_group_classes,
        "matrices":dh_group_matrices,
        "names":dh_group_names
    },
    "Dd":{
        "characters":dd_group_character_table,
        "classes":dd_group_classes,
        "matrices":dd_group_matrices,
        "names":dd_group_names
    },
    "Ch":{
        "characters":ch_group_character_table,
        "classes":ch_group_classes,
        "matrices":ch_group_matrices,
        "names":ch_group_names
    },
    "C":{
        "characters":cyclic_group_character_table,
        "classes":cyclic_group_classes,
        "matrices":cyclic_group_operation_representation,
        "names":cyclic_group_irrep_names
    }
}

def parametrized_point_group_character_table(key, n, **etc):
    return point_group_map[key]["characters"](n, **etc)
def parametrized_point_group_classes(key, n, **etc):
    class_gen = point_group_map[key].get("classes")
    if class_gen is not None:
        return class_gen(n, **etc)
    else:
        return None
def parametrized_point_group_matrices(key, n, **etc):
    mat_gen = point_group_map[key].get("matrices")
    if mat_gen is not None:
        return mat_gen(n, **etc)
    else:
        return None

def I_point_group():
    return np.array([
        [1, 1, 1, 1, 1],
        [3, 2 * np.cos(np.pi / 5), 2 * np.cos((3 * np.pi) / 5), 0, -1],
        [3, 2 * np.cos((3 * np.pi) / 5), 2 * np.cos(np.pi / 5), 0, -1],
        [4, -1, -1, 1, 0],
        [5, 0, 0, -1, 1]
    ])

def I_group_classes():
    classes = [
        np.array([0]),
        np.array([3, 8, 11, 12, 13, 14, 27, 30, 33, 41, 43, 47, 53, 55, 59]),
        np.array([1, 2, 4, 5, 6, 7, 9, 10, 15, 19, 22, 24, 28, 29, 37, 39, 40, 49, 51, 52]),
        np.array([16, 18, 23, 26, 34, 35, 38, 42, 44, 48, 57, 58]),
        np.array([17, 20, 21, 25, 31, 32, 36, 45, 46, 50, 54, 56])
        ]
    elements = np.array([[0, 1, 2, 3, 4],
                         [0, 1, 3, 4, 2],
                         [0, 1, 4, 2, 3],
                         [0, 2, 1, 4, 3],
                         [0, 2, 3, 1, 4],
                         [0, 2, 4, 3, 1],
                         [0, 3, 1, 2, 4],
                         [0, 3, 2, 4, 1],
                         [0, 3, 4, 1, 2],
                         [0, 4, 1, 3, 2],
                         [0, 4, 2, 1, 3],
                         [0, 4, 3, 2, 1],
                         [1, 0, 2, 4, 3],
                         [1, 0, 3, 2, 4],
                         [1, 0, 4, 3, 2],
                         [1, 2, 0, 3, 4],
                         [1, 2, 3, 4, 0],
                         [1, 2, 4, 0, 3],
                         [1, 3, 0, 4, 2],
                         [1, 3, 2, 0, 4],
                         [1, 3, 4, 2, 0],
                         [1, 4, 0, 2, 3],
                         [1, 4, 2, 3, 0],
                         [1, 4, 3, 0, 2],
                         [2, 0, 1, 3, 4],
                         [2, 0, 3, 4, 1],
                         [2, 0, 4, 1, 3],
                         [2, 1, 0, 4, 3],
                         [2, 1, 3, 0, 4],
                         [2, 1, 4, 3, 0],
                         [2, 3, 0, 1, 4],
                         [2, 3, 1, 4, 0],
                         [2, 3, 4, 0, 1],
                         [2, 4, 0, 3, 1],
                         [2, 4, 1, 0, 3],
                         [2, 4, 3, 1, 0],
                         [3, 0, 1, 4, 2],
                         [3, 0, 2, 1, 4],
                         [3, 0, 4, 2, 1],
                         [3, 1, 0, 2, 4],
                         [3, 1, 2, 4, 0],
                         [3, 1, 4, 0, 2],
                         [3, 2, 0, 4, 1],
                         [3, 2, 1, 0, 4],
                         [3, 2, 4, 1, 0],
                         [3, 4, 0, 1, 2],
                         [3, 4, 1, 2, 0],
                         [3, 4, 2, 0, 1],
                         [4, 0, 1, 2, 3],
                         [4, 0, 2, 3, 1],
                         [4, 0, 3, 1, 2],
                         [4, 1, 0, 3, 2],
                         [4, 1, 2, 0, 3],
                         [4, 1, 3, 2, 0],
                         [4, 2, 0, 1, 3],
                         [4, 2, 1, 3, 0],
                         [4, 2, 3, 0, 1],
                         [4, 3, 0, 2, 1],
                         [4, 3, 1, 0, 2],
                         [4, 3, 2, 1, 0]])
    return elements, classes

def I_group_matrices(elements=None):
    a1 = (1 + np.sqrt(5))/4
    a2 = (1 - np.sqrt(5))/4
    base_mats = np.array([[[1, 0, 0],
                           [0, 1, 0],
                           [0, 0, 1]],
                          [[0, 1, 0],
                           [0, 0, -1],
                           [-1, 0, 0]],
                          [[0, 0, -1],
                           [1, 0, 0],
                           [0, -1, 0]],
                          [[1, 0, 0],
                           [0, -1, 0],
                           [0, 0, -1]],
                          [[0, 0, -1],
                           [-1, 0, 0],
                           [0, 1, 0]],
                          [[0, 1, 0],
                           [0, 0, 1],
                           [1, 0, 0]],
                          [[0, -1, 0],
                           [0, 0, 1],
                           [-1, 0, 0]],
                          [[0, 0, 1],
                           [-1, 0, 0],
                           [0, -1, 0]],
                          [[-1, 0, 0],
                           [0, -1, 0],
                           [0, 0, 1]],
                          [[0, 0, 1],
                           [1, 0, 0],
                           [0, 1, 0]],
                          [[0, -1, 0],
                           [0, 0, -1],
                           [1, 0, 0]],
                          [[-1, 0, 0],
                           [0, 1, 0],
                           [0, 0, -1]],
                          [[-1 / 2, -a1, a2],
                           [-a1, -a2, 1 / 2],
                           [a2, 1 / 2, -a1]],
                          [[-a1, -a2, 1 / 2],
                           [-a2, -1 / 2, a1],
                           [1 / 2, a1, -a2]],
                          [[-a2, -1 / 2, a1],
                           [-1 / 2, -a1, a2],
                           [a1, a2, -1 / 2]],
                          [[-1 / 2, a1, -a2],
                           [-a1, a2, -1 / 2],
                           [a2, -1 / 2, a1]],
                          [[a2, -1 / 2, -a1],
                           [1 / 2, -a1, -a2],
                           [-a1, a2, 1 / 2]],
                          [[a1, a2, 1 / 2],
                           [a2, 1 / 2, a1],
                           [-1 / 2, -a1, -a2]],
                          [[-a1, a2, -1 / 2],
                           [-a2, 1 / 2, -a1],
                           [1 / 2, -a1, a2]],
                          [[a2, 1 / 2, a1],
                           [1 / 2, a1, a2],
                           [-a1, -a2, -1 / 2]],
                          [[1 / 2, -a1, -a2],
                           [a1, -a2, -1 / 2],
                           [-a2, 1 / 2, a1]],
                          [[-a2, 1 / 2, -a1],
                           [-1 / 2, a1, -a2],
                           [a1, -a2, 1 / 2]],
                          [[a1, -a2, -1 / 2],
                           [a2, -1 / 2, -a1],
                           [-1 / 2, a1, a2]],
                          [[1 / 2, a1, a2],
                           [a1, a2, 1 / 2],
                           [-a2, -1 / 2, -a1]],
                          [[-1 / 2, -a1, a2],
                           [a1, a2, -1 / 2],
                           [-a2, -1 / 2, a1]],
                          [[-a2, -1 / 2, a1],
                           [1 / 2, a1, -a2],
                           [-a1, -a2, 1 / 2]],
                          [[-a1, -a2, 1 / 2],
                           [a2, 1 / 2, -a1],
                           [-1 / 2, -a1, a2]],
                          [[-1 / 2, a1, -a2],
                           [a1, -a2, 1 / 2],
                           [-a2, 1 / 2, -a1]],
                          [[a1, a2, 1 / 2],
                           [-a2, -1 / 2, -a1],
                           [1 / 2, a1, a2]],
                          [[a2, -1 / 2, -a1],
                           [-1 / 2, a1, a2],
                           [a1, -a2, -1 / 2]],
                          [[-a2, 1 / 2, -a1],
                           [1 / 2, -a1, a2],
                           [-a1, a2, -1 / 2]],
                          [[a1, -a2, -1 / 2],
                           [-a2, 1 / 2, a1],
                           [1 / 2, -a1, -a2]],
                          [[1 / 2, a1, a2],
                           [-a1, -a2, -1 / 2],
                           [a2, 1 / 2, a1]],
                          [[-a1, a2, -1 / 2],
                           [a2, -1 / 2, a1],
                           [-1 / 2, a1, -a2]],
                          [[a2, 1 / 2, a1],
                           [-1 / 2, -a1, -a2],
                           [a1, a2, 1 / 2]],
                          [[1 / 2, -a1, -a2],
                           [-a1, a2, 1 / 2],
                           [a2, -1 / 2, -a1]],
                          [[a1, a2, -1 / 2],
                           [a2, 1 / 2, -a1],
                           [1 / 2, a1, -a2]],
                          [[a2, 1 / 2, -a1],
                           [1 / 2, a1, -a2],
                           [a1, a2, -1 / 2]],
                          [[1 / 2, a1, -a2],
                           [a1, a2, -1 / 2],
                           [a2, 1 / 2, -a1]],
                          [[a1, -a2, 1 / 2],
                           [a2, -1 / 2, a1],
                           [1 / 2, -a1, a2]],
                          [[-1 / 2, a1, a2],
                           [-a1, a2, 1 / 2],
                           [-a2, 1 / 2, a1]],
                          [[-a2, -1 / 2, -a1],
                           [-1 / 2, -a1, -a2],
                           [-a1, -a2, -1 / 2]],
                          [[a2, -1 / 2, a1],
                           [1 / 2, -a1, a2],
                           [a1, -a2, 1 / 2]],
                          [[-1 / 2, -a1, -a2],
                           [-a1, -a2, -1 / 2],
                           [-a2, -1 / 2, -a1]],
                          [[-a1, a2, 1 / 2],
                           [-a2, 1 / 2, a1],
                           [-1 / 2, a1, a2]],
                          [[1 / 2, -a1, a2],
                           [a1, -a2, 1 / 2],
                           [a2, -1 / 2, a1]],
                          [[-a2, 1 / 2, a1],
                           [-1 / 2, a1, a2],
                           [-a1, a2, 1 / 2]],
                          [[-a1, -a2, -1 / 2],
                           [-a2, -1 / 2, -a1],
                           [-1 / 2, -a1, -a2]],
                          [[a2, 1 / 2, -a1],
                           [-1 / 2, -a1, a2],
                           [-a1, -a2, 1 / 2]],
                          [[a1, a2, -1 / 2],
                           [-a2, -1 / 2, a1],
                           [-1 / 2, -a1, a2]],
                          [[1 / 2, a1, -a2],
                           [-a1, -a2, 1 / 2],
                           [-a2, -1 / 2, a1]],
                          [[a2, -1 / 2, a1],
                           [-1 / 2, a1, -a2],
                           [-a1, a2, -1 / 2]],
                          [[-1 / 2, -a1, -a2],
                           [a1, a2, 1 / 2],
                           [a2, 1 / 2, a1]],
                          [[-a1, a2, 1 / 2],
                           [a2, -1 / 2, -a1],
                           [1 / 2, -a1, -a2]],
                          [[a1, -a2, 1 / 2],
                           [-a2, 1 / 2, -a1],
                           [-1 / 2, a1, -a2]],
                          [[-1 / 2, a1, a2],
                           [a1, -a2, -1 / 2],
                           [a2, -1 / 2, -a1]],
                          [[-a2, -1 / 2, -a1],
                           [1 / 2, a1, a2],
                           [a1, a2, 1 / 2]],
                          [[1 / 2, -a1, a2],
                           [-a1, a2, -1 / 2],
                           [-a2, 1 / 2, -a1]],
                          [[-a1, -a2, -1 / 2],
                           [a2, 1 / 2, a1],
                           [1 / 2, a1, a2]],
                          [[-a2, 1 / 2, a1],
                           [1 / 2, -a1, -a2],
                           [a1, -a2, -1 / 2]]])

    if elements is None:
        return base_mats
    else:
        return base_mats[elements,]

def I_group_names():
    return ["A", "T1", "T2", "G", "H"]

def Ih_point_group():
    return np.array([
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [3, 2 * np.cos(np.pi / 5), 2 * np.cos((3 * np.pi) / 5), 0, -1, 3, 2 * np.cos((3 * np.pi) / 5),
         2 * np.cos(np.pi / 5), 0, -1],
        [3, 2 * np.cos((3 * np.pi) / 5), 2 * np.cos(np.pi / 5), 0, -1, 3, 2 * np.cos(np.pi / 5),
         2 * np.cos((3 * np.pi) / 5), 0, -1],
        [4, -1, -1, 1, 0, 4, -1, -1, 1, 0],
        [5, 0, 0, -1, 1, 5, 0, 0, -1, 1],
        [1, 1, 1, 1, 1, -1, -1, -1, -1, -1],
        [3, 2 * np.cos(np.pi / 5), 2 * np.cos((3 * np.pi) / 5), 0, -1, -3, -2 * np.cos((3 * np.pi) / 5),
         -2 * np.cos(np.pi / 5), 0, 1],
        [3, 2 * np.cos((3 * np.pi) / 5), 2 * np.cos(np.pi / 5), 0, -1, -3, -2 * np.cos(np.pi / 5),
         -2 * np.cos((3 * np.pi) / 5), 0, 1],
        [4, -1, -1, 1, 0, -4, 1, 1, -1, 0],
        [5, 0, 0, -1, 1, -5, 0, 0, 1, -1]
    ])

def Ih_group_classes():
    classes = [
        np.array([0]),
        np.array([60]),
        np.array([3, 8, 11, 12, 13, 14, 27, 30, 33, 41, 43, 47, 53, 55, 59]),
        np.array([63, 68, 71, 72, 73, 74, 87, 90, 93, 101, 103, 107, 113, 115, 119]),
        np.array([1, 2, 4, 5, 6, 7, 9, 10, 15, 19, 22, 24, 28, 29, 37, 39, 40, 49, 51, 52]),
        np.array([16, 18, 23, 26, 34, 35, 38, 42, 44, 48, 57, 58]),
        np.array([17, 20, 21, 25, 31, 32, 36, 45, 46, 50, 54, 56]),
        np.array([61, 62, 64, 65, 66, 67, 69, 70, 75, 79, 82, 84, 88, 89, 97, 99, 100, 109, 111, 112]),
        np.array([76, 78, 83, 86, 94, 95, 98, 102, 104, 108, 117, 118]),
        np.array([77, 80, 81, 85, 91, 92, 96, 105, 106, 110, 114, 116])
        ]
    elements = np.array([[0, 1, 2, 3, 4, 5, 6],
                         [0, 1, 2, 3, 5, 6, 4],
                         [0, 1, 2, 3, 6, 4, 5],
                         [0, 1, 2, 4, 3, 6, 5],
                         [0, 1, 2, 4, 5, 3, 6],
                         [0, 1, 2, 4, 6, 5, 3],
                         [0, 1, 2, 5, 3, 4, 6],
                         [0, 1, 2, 5, 4, 6, 3],
                         [0, 1, 2, 5, 6, 3, 4],
                         [0, 1, 2, 6, 3, 5, 4],
                         [0, 1, 2, 6, 4, 3, 5],
                         [0, 1, 2, 6, 5, 4, 3],
                         [0, 1, 3, 2, 4, 6, 5],
                         [0, 1, 3, 2, 5, 4, 6],
                         [0, 1, 3, 2, 6, 5, 4],
                         [0, 1, 3, 4, 2, 5, 6],
                         [0, 1, 3, 4, 5, 6, 2],
                         [0, 1, 3, 4, 6, 2, 5],
                         [0, 1, 3, 5, 2, 6, 4],
                         [0, 1, 3, 5, 4, 2, 6],
                         [0, 1, 3, 5, 6, 4, 2],
                         [0, 1, 3, 6, 2, 4, 5],
                         [0, 1, 3, 6, 4, 5, 2],
                         [0, 1, 3, 6, 5, 2, 4],
                         [0, 1, 4, 2, 3, 5, 6],
                         [0, 1, 4, 2, 5, 6, 3],
                         [0, 1, 4, 2, 6, 3, 5],
                         [0, 1, 4, 3, 2, 6, 5],
                         [0, 1, 4, 3, 5, 2, 6],
                         [0, 1, 4, 3, 6, 5, 2],
                         [0, 1, 4, 5, 2, 3, 6],
                         [0, 1, 4, 5, 3, 6, 2],
                         [0, 1, 4, 5, 6, 2, 3],
                         [0, 1, 4, 6, 2, 5, 3],
                         [0, 1, 4, 6, 3, 2, 5],
                         [0, 1, 4, 6, 5, 3, 2],
                         [0, 1, 5, 2, 3, 6, 4],
                         [0, 1, 5, 2, 4, 3, 6],
                         [0, 1, 5, 2, 6, 4, 3],
                         [0, 1, 5, 3, 2, 4, 6],
                         [0, 1, 5, 3, 4, 6, 2],
                         [0, 1, 5, 3, 6, 2, 4],
                         [0, 1, 5, 4, 2, 6, 3],
                         [0, 1, 5, 4, 3, 2, 6],
                         [0, 1, 5, 4, 6, 3, 2],
                         [0, 1, 5, 6, 2, 3, 4],
                         [0, 1, 5, 6, 3, 4, 2],
                         [0, 1, 5, 6, 4, 2, 3],
                         [0, 1, 6, 2, 3, 4, 5],
                         [0, 1, 6, 2, 4, 5, 3],
                         [0, 1, 6, 2, 5, 3, 4],
                         [0, 1, 6, 3, 2, 5, 4],
                         [0, 1, 6, 3, 4, 2, 5],
                         [0, 1, 6, 3, 5, 4, 2],
                         [0, 1, 6, 4, 2, 3, 5],
                         [0, 1, 6, 4, 3, 5, 2],
                         [0, 1, 6, 4, 5, 2, 3],
                         [0, 1, 6, 5, 2, 4, 3],
                         [0, 1, 6, 5, 3, 2, 4],
                         [0, 1, 6, 5, 4, 3, 2],
                         [1, 0, 2, 3, 4, 5, 6],
                         [1, 0, 2, 3, 5, 6, 4],
                         [1, 0, 2, 3, 6, 4, 5],
                         [1, 0, 2, 4, 3, 6, 5],
                         [1, 0, 2, 4, 5, 3, 6],
                         [1, 0, 2, 4, 6, 5, 3],
                         [1, 0, 2, 5, 3, 4, 6],
                         [1, 0, 2, 5, 4, 6, 3],
                         [1, 0, 2, 5, 6, 3, 4],
                         [1, 0, 2, 6, 3, 5, 4],
                         [1, 0, 2, 6, 4, 3, 5],
                         [1, 0, 2, 6, 5, 4, 3],
                         [1, 0, 3, 2, 4, 6, 5],
                         [1, 0, 3, 2, 5, 4, 6],
                         [1, 0, 3, 2, 6, 5, 4],
                         [1, 0, 3, 4, 2, 5, 6],
                         [1, 0, 3, 4, 5, 6, 2],
                         [1, 0, 3, 4, 6, 2, 5],
                         [1, 0, 3, 5, 2, 6, 4],
                         [1, 0, 3, 5, 4, 2, 6],
                         [1, 0, 3, 5, 6, 4, 2],
                         [1, 0, 3, 6, 2, 4, 5],
                         [1, 0, 3, 6, 4, 5, 2],
                         [1, 0, 3, 6, 5, 2, 4],
                         [1, 0, 4, 2, 3, 5, 6],
                         [1, 0, 4, 2, 5, 6, 3],
                         [1, 0, 4, 2, 6, 3, 5],
                         [1, 0, 4, 3, 2, 6, 5],
                         [1, 0, 4, 3, 5, 2, 6],
                         [1, 0, 4, 3, 6, 5, 2],
                         [1, 0, 4, 5, 2, 3, 6],
                         [1, 0, 4, 5, 3, 6, 2],
                         [1, 0, 4, 5, 6, 2, 3],
                         [1, 0, 4, 6, 2, 5, 3],
                         [1, 0, 4, 6, 3, 2, 5],
                         [1, 0, 4, 6, 5, 3, 2],
                         [1, 0, 5, 2, 3, 6, 4],
                         [1, 0, 5, 2, 4, 3, 6],
                         [1, 0, 5, 2, 6, 4, 3],
                         [1, 0, 5, 3, 2, 4, 6],
                         [1, 0, 5, 3, 4, 6, 2],
                         [1, 0, 5, 3, 6, 2, 4],
                         [1, 0, 5, 4, 2, 6, 3],
                         [1, 0, 5, 4, 3, 2, 6],
                         [1, 0, 5, 4, 6, 3, 2],
                         [1, 0, 5, 6, 2, 3, 4],
                         [1, 0, 5, 6, 3, 4, 2],
                         [1, 0, 5, 6, 4, 2, 3],
                         [1, 0, 6, 2, 3, 4, 5],
                         [1, 0, 6, 2, 4, 5, 3],
                         [1, 0, 6, 2, 5, 3, 4],
                         [1, 0, 6, 3, 2, 5, 4],
                         [1, 0, 6, 3, 4, 2, 5],
                         [1, 0, 6, 3, 5, 4, 2],
                         [1, 0, 6, 4, 2, 3, 5],
                         [1, 0, 6, 4, 3, 5, 2],
                         [1, 0, 6, 4, 5, 2, 3],
                         [1, 0, 6, 5, 2, 4, 3],
                         [1, 0, 6, 5, 3, 2, 4],
                         [1, 0, 6, 5, 4, 3, 2]])
    return elements, classes

def Ih_group_matrices(elements=None):
    a1 = (1 + np.sqrt(5))/4
    a2 = (1 - np.sqrt(5))/4
    base_mats = np.array([[[1, 0, 0],
                           [0, 1, 0],
                           [0, 0, 1]],
                          [[0, 1, 0],
                           [0, 0, -1],
                           [-1, 0, 0]],
                          [[0, 0, -1],
                           [1, 0, 0],
                           [0, -1, 0]],
                          [[1, 0, 0],
                           [0, -1, 0],
                           [0, 0, -1]],
                          [[0, 0, -1],
                           [-1, 0, 0],
                           [0, 1, 0]],
                          [[0, 1, 0],
                           [0, 0, 1],
                           [1, 0, 0]],
                          [[0, -1, 0],
                           [0, 0, 1],
                           [-1, 0, 0]],
                          [[0, 0, 1],
                           [-1, 0, 0],
                           [0, -1, 0]],
                          [[-1, 0, 0],
                           [0, -1, 0],
                           [0, 0, 1]],
                          [[0, 0, 1],
                           [1, 0, 0],
                           [0, 1, 0]],
                          [[0, -1, 0],
                           [0, 0, -1],
                           [1, 0, 0]],
                          [[-1, 0, 0],
                           [0, 1, 0],
                           [0, 0, -1]],
                          [[-1 / 2, -a1, a2],
                           [-a1, -a2, 1 / 2],
                           [a2, 1 / 2, -a1]],
                          [[-a1, -a2, 1 / 2],
                           [-a2, -1 / 2, a1],
                           [1 / 2, a1, -a2]],
                          [[-a2, -1 / 2, a1],
                           [-1 / 2, -a1, a2],
                           [a1, a2, -1 / 2]],
                          [[-1 / 2, a1, -a2],
                           [-a1, a2, -1 / 2],
                           [a2, -1 / 2, a1]],
                          [[a2, -1 / 2, -a1],
                           [1 / 2, -a1, -a2],
                           [-a1, a2, 1 / 2]],
                          [[a1, a2, 1 / 2],
                           [a2, 1 / 2, a1],
                           [-1 / 2, -a1, -a2]],
                          [[-a1, a2, -1 / 2],
                           [-a2, 1 / 2, -a1],
                           [1 / 2, -a1, a2]],
                          [[a2, 1 / 2, a1],
                           [1 / 2, a1, a2],
                           [-a1, -a2, -1 / 2]],
                          [[1 / 2, -a1, -a2],
                           [a1, -a2, -1 / 2],
                           [-a2, 1 / 2, a1]],
                          [[-a2, 1 / 2, -a1],
                           [-1 / 2, a1, -a2],
                           [a1, -a2, 1 / 2]],
                          [[a1, -a2, -1 / 2],
                           [a2, -1 / 2, -a1],
                           [-1 / 2, a1, a2]],
                          [[1 / 2, a1, a2],
                           [a1, a2, 1 / 2],
                           [-a2, -1 / 2, -a1]],
                          [[-1 / 2, -a1, a2],
                           [a1, a2, -1 / 2],
                           [-a2, -1 / 2, a1]],
                          [[-a2, -1 / 2, a1],
                           [1 / 2, a1, -a2],
                           [-a1, -a2, 1 / 2]],
                          [[-a1, -a2, 1 / 2],
                           [a2, 1 / 2, -a1],
                           [-1 / 2, -a1, a2]],
                          [[-1 / 2, a1, -a2],
                           [a1, -a2, 1 / 2],
                           [-a2, 1 / 2, -a1]],
                          [[a1, a2, 1 / 2],
                           [-a2, -1 / 2, -a1],
                           [1 / 2, a1, a2]],
                          [[a2, -1 / 2, -a1],
                           [-1 / 2, a1, a2],
                           [a1, -a2, -1 / 2]],
                          [[-a2, 1 / 2, -a1],
                           [1 / 2, -a1, a2],
                           [-a1, a2, -1 / 2]],
                          [[a1, -a2, -1 / 2],
                           [-a2, 1 / 2, a1],
                           [1 / 2, -a1, -a2]],
                          [[1 / 2, a1, a2],
                           [-a1, -a2, -1 / 2],
                           [a2, 1 / 2, a1]],
                          [[-a1, a2, -1 / 2],
                           [a2, -1 / 2, a1],
                           [-1 / 2, a1, -a2]],
                          [[a2, 1 / 2, a1],
                           [-1 / 2, -a1, -a2],
                           [a1, a2, 1 / 2]],
                          [[1 / 2, -a1, -a2],
                           [-a1, a2, 1 / 2],
                           [a2, -1 / 2, -a1]],
                          [[a1, a2, -1 / 2],
                           [a2, 1 / 2, -a1],
                           [1 / 2, a1, -a2]],
                          [[a2, 1 / 2, -a1],
                           [1 / 2, a1, -a2],
                           [a1, a2, -1 / 2]],
                          [[1 / 2, a1, -a2],
                           [a1, a2, -1 / 2],
                           [a2, 1 / 2, -a1]],
                          [[a1, -a2, 1 / 2],
                           [a2, -1 / 2, a1],
                           [1 / 2, -a1, a2]],
                          [[-1 / 2, a1, a2],
                           [-a1, a2, 1 / 2],
                           [-a2, 1 / 2, a1]],
                          [[-a2, -1 / 2, -a1],
                           [-1 / 2, -a1, -a2],
                           [-a1, -a2, -1 / 2]],
                          [[a2, -1 / 2, a1],
                           [1 / 2, -a1, a2],
                           [a1, -a2, 1 / 2]],
                          [[-1 / 2, -a1, -a2],
                           [-a1, -a2, -1 / 2],
                           [-a2, -1 / 2, -a1]],
                          [[-a1, a2, 1 / 2],
                           [-a2, 1 / 2, a1],
                           [-1 / 2, a1, a2]],
                          [[1 / 2, -a1, a2],
                           [a1, -a2, 1 / 2],
                           [a2, -1 / 2, a1]],
                          [[-a2, 1 / 2, a1],
                           [-1 / 2, a1, a2],
                           [-a1, a2, 1 / 2]],
                          [[-a1, -a2, -1 / 2],
                           [-a2, -1 / 2, -a1],
                           [-1 / 2, -a1, -a2]],
                          [[a2, 1 / 2, -a1],
                           [-1 / 2, -a1, a2],
                           [-a1, -a2, 1 / 2]],
                          [[a1, a2, -1 / 2],
                           [-a2, -1 / 2, a1],
                           [-1 / 2, -a1, a2]],
                          [[1 / 2, a1, -a2],
                           [-a1, -a2, 1 / 2],
                           [-a2, -1 / 2, a1]],
                          [[a2, -1 / 2, a1],
                           [-1 / 2, a1, -a2],
                           [-a1, a2, -1 / 2]],
                          [[-1 / 2, -a1, -a2],
                           [a1, a2, 1 / 2],
                           [a2, 1 / 2, a1]],
                          [[-a1, a2, 1 / 2],
                           [a2, -1 / 2, -a1],
                           [1 / 2, -a1, -a2]],
                          [[a1, -a2, 1 / 2],
                           [-a2, 1 / 2, -a1],
                           [-1 / 2, a1, -a2]],
                          [[-1 / 2, a1, a2],
                           [a1, -a2, -1 / 2],
                           [a2, -1 / 2, -a1]],
                          [[-a2, -1 / 2, -a1],
                           [1 / 2, a1, a2],
                           [a1, a2, 1 / 2]],
                          [[1 / 2, -a1, a2],
                           [-a1, a2, -1 / 2],
                           [-a2, 1 / 2, -a1]],
                          [[-a1, -a2, -1 / 2],
                           [a2, 1 / 2, a1],
                           [1 / 2, a1, a2]],
                          [[-a2, 1 / 2, a1],
                           [1 / 2, -a1, -a2],
                           [a1, -a2, -1 / 2]],
                          [[-1, 0, 0],
                           [0, -1, 0],
                           [0, 0, -1]],
                          [[0, -1, 0],
                           [0, 0, 1],
                           [1, 0, 0]],
                          [[0, 0, 1],
                           [-1, 0, 0],
                           [0, 1, 0]],
                          [[-1, 0, 0],
                           [0, 1, 0],
                           [0, 0, 1]],
                          [[0, 0, 1],
                           [1, 0, 0],
                           [0, -1, 0]],
                          [[0, -1, 0],
                           [0, 0, -1],
                           [-1, 0, 0]],
                          [[0, 1, 0],
                           [0, 0, -1],
                           [1, 0, 0]],
                          [[0, 0, -1],
                           [1, 0, 0],
                           [0, 1, 0]],
                          [[1, 0, 0],
                           [0, 1, 0],
                           [0, 0, -1]],
                          [[0, 0, -1],
                           [-1, 0, 0],
                           [0, -1, 0]],
                          [[0, 1, 0],
                           [0, 0, 1],
                           [-1, 0, 0]],
                          [[1, 0, 0],
                           [0, -1, 0],
                           [0, 0, 1]],
                          [[1 / 2, a1, -a2],
                           [a1, a2, -1 / 2],
                           [-a2, -1 / 2, a1]],
                          [[a1, a2, -1 / 2],
                           [a2, 1 / 2, -a1],
                           [-1 / 2, -a1, a2]],
                          [[a2, 1 / 2, -a1],
                           [1 / 2, a1, -a2],
                           [-a1, -a2, 1 / 2]],
                          [[1 / 2, -a1, a2],
                           [a1, -a2, 1 / 2],
                           [-a2, 1 / 2, -a1]],
                          [[-a2, 1 / 2, a1],
                           [-1 / 2, a1, a2],
                           [a1, -a2, -1 / 2]],
                          [[-a1, -a2, -1 / 2],
                           [-a2, -1 / 2, -a1],
                           [1 / 2, a1, a2]],
                          [[a1, -a2, 1 / 2],
                           [a2, -1 / 2, a1],
                           [-1 / 2, a1, -a2]],
                          [[-a2, -1 / 2, -a1],
                           [-1 / 2, -a1, -a2],
                           [a1, a2, 1 / 2]],
                          [[-1 / 2, a1, a2],
                           [-a1, a2, 1 / 2],
                           [a2, -1 / 2, -a1]],
                          [[a2, -1 / 2, a1],
                           [1 / 2, -a1, a2],
                           [-a1, a2, -1 / 2]],
                          [[-a1, a2, 1 / 2],
                           [-a2, 1 / 2, a1],
                           [1 / 2, -a1, -a2]],
                          [[-1 / 2, -a1, -a2],
                           [-a1, -a2, -1 / 2],
                           [a2, 1 / 2, a1]],
                          [[1 / 2, a1, -a2],
                           [-a1, -a2, 1 / 2],
                           [a2, 1 / 2, -a1]],
                          [[a2, 1 / 2, -a1],
                           [-1 / 2, -a1, a2],
                           [a1, a2, -1 / 2]],
                          [[a1, a2, -1 / 2],
                           [-a2, -1 / 2, a1],
                           [1 / 2, a1, -a2]],
                          [[1 / 2, -a1, a2],
                           [-a1, a2, -1 / 2],
                           [a2, -1 / 2, a1]],
                          [[-a1, -a2, -1 / 2],
                           [a2, 1 / 2, a1],
                           [-1 / 2, -a1, -a2]],
                          [[-a2, 1 / 2, a1],
                           [1 / 2, -a1, -a2],
                           [-a1, a2, 1 / 2]],
                          [[a2, -1 / 2, a1],
                           [-1 / 2, a1, -a2],
                           [a1, -a2, 1 / 2]],
                          [[-a1, a2, 1 / 2],
                           [a2, -1 / 2, -a1],
                           [-1 / 2, a1, a2]],
                          [[-1 / 2, -a1, -a2],
                           [a1, a2, 1 / 2],
                           [-a2, -1 / 2, -a1]],
                          [[a1, -a2, 1 / 2],
                           [-a2, 1 / 2, -a1],
                           [1 / 2, -a1, a2]],
                          [[-a2, -1 / 2, -a1],
                           [1 / 2, a1, a2],
                           [-a1, -a2, -1 / 2]],
                          [[-1 / 2, a1, a2],
                           [a1, -a2, -1 / 2],
                           [-a2, 1 / 2, a1]],
                          [[-a1, -a2, 1 / 2],
                           [-a2, -1 / 2, a1],
                           [-1 / 2, -a1, a2]],
                          [[-a2, -1 / 2, a1],
                           [-1 / 2, -a1, a2],
                           [-a1, -a2, 1 / 2]],
                          [[-1 / 2, -a1, a2],
                           [-a1, -a2, 1 / 2],
                           [-a2, -1 / 2, a1]],
                          [[-a1, a2, -1 / 2],
                           [-a2, 1 / 2, -a1],
                           [-1 / 2, a1, -a2]],
                          [[1 / 2, -a1, -a2],
                           [a1, -a2, -1 / 2],
                           [a2, -1 / 2, -a1]],
                          [[a2, 1 / 2, a1],
                           [1 / 2, a1, a2],
                           [a1, a2, 1 / 2]],
                          [[-a2, 1 / 2, -a1],
                           [-1 / 2, a1, -a2],
                           [-a1, a2, -1 / 2]],
                          [[1 / 2, a1, a2],
                           [a1, a2, 1 / 2],
                           [a2, 1 / 2, a1]],
                          [[a1, -a2, -1 / 2],
                           [a2, -1 / 2, -a1],
                           [1 / 2, -a1, -a2]],
                          [[-1 / 2, a1, -a2],
                           [-a1, a2, -1 / 2],
                           [-a2, 1 / 2, -a1]],
                          [[a2, -1 / 2, -a1],
                           [1 / 2, -a1, -a2],
                           [a1, -a2, -1 / 2]],
                          [[a1, a2, 1 / 2],
                           [a2, 1 / 2, a1],
                           [1 / 2, a1, a2]],
                          [[-a2, -1 / 2, a1],
                           [1 / 2, a1, -a2],
                           [a1, a2, -1 / 2]],
                          [[-a1, -a2, 1 / 2],
                           [a2, 1 / 2, -a1],
                           [1 / 2, a1, -a2]],
                          [[-1 / 2, -a1, a2],
                           [a1, a2, -1 / 2],
                           [a2, 1 / 2, -a1]],
                          [[-a2, 1 / 2, -a1],
                           [1 / 2, -a1, a2],
                           [a1, -a2, 1 / 2]],
                          [[1 / 2, a1, a2],
                           [-a1, -a2, -1 / 2],
                           [-a2, -1 / 2, -a1]],
                          [[a1, -a2, -1 / 2],
                           [-a2, 1 / 2, a1],
                           [-1 / 2, a1, a2]],
                          [[-a1, a2, -1 / 2],
                           [a2, -1 / 2, a1],
                           [1 / 2, -a1, a2]],
                          [[1 / 2, -a1, -a2],
                           [-a1, a2, 1 / 2],
                           [-a2, 1 / 2, a1]],
                          [[a2, 1 / 2, a1],
                           [-1 / 2, -a1, -a2],
                           [-a1, -a2, -1 / 2]],
                          [[-1 / 2, a1, -a2],
                           [a1, -a2, 1 / 2],
                           [a2, -1 / 2, a1]],
                          [[a1, a2, 1 / 2],
                           [-a2, -1 / 2, -a1],
                           [-1 / 2, -a1, -a2]],
                          [[a2, -1 / 2, -a1],
                           [-1 / 2, a1, a2],
                           [-a1, a2, 1 / 2]]])

    if elements is None:
        return base_mats
    else:
        return base_mats[elements,]

def Ih_group_names():
    names = I_group_names()
    return [s+"g" for s in names] + [s+"u" for s in names]

def O_point_group():
    return np.array([
        [1, 1, 1, 1, 1],
        [1, -1, 1, 1, -1],
        [2, 0, 2, -1, 0],
        [3, 1, -1, 0, -1],
        [3, -1, -1, 0, 1]
    ])

def O_group_classes():
    classes = [
        np.array([0]),
        np.array([9, 10, 13, 17, 18, 22]),
        np.array([7, 16, 23]),
        np.array([3, 4, 8, 11, 12, 15, 19, 20]),
        np.array([1, 2, 5, 6, 14, 21])
    ]
    elements = np.array([[0, 1, 2, 3],
                         [0, 1, 3, 2],
                         [0, 2, 1, 3],
                         [0, 2, 3, 1],
                         [0, 3, 1, 2],
                         [0, 3, 2, 1],
                         [1, 0, 2, 3],
                         [1, 0, 3, 2],
                         [1, 2, 0, 3],
                         [1, 2, 3, 0],
                         [1, 3, 0, 2],
                         [1, 3, 2, 0],
                         [2, 0, 1, 3],
                         [2, 0, 3, 1],
                         [2, 1, 0, 3],
                         [2, 1, 3, 0],
                         [2, 3, 0, 1],
                         [2, 3, 1, 0],
                         [3, 0, 1, 2],
                         [3, 0, 2, 1],
                         [3, 1, 0, 2],
                         [3, 1, 2, 0],
                         [3, 2, 0, 1],
                         [3, 2, 1, 0]])
    return elements, classes

def O_group_matrices(elements=None):
    # TODO: compress this
    perms = np.array([[0, 1, 2],
                      [1, 0, 2],
                      [0, 2, 1],
                      [1, 2, 0],
                      [2, 0, 1],
                      [2, 1, 0],
                      [1, 0, 2],
                      [0, 1, 2],
                      [2, 0, 1],
                      [2, 1, 0],
                      [0, 2, 1],
                      [1, 2, 0],
                      [1, 2, 0],
                      [0, 2, 1],
                      [2, 1, 0],
                      [2, 0, 1],
                      [0, 1, 2],
                      [1, 0, 2],
                      [2, 1, 0],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 2, 1],
                      [1, 0, 2],
                      [0, 1, 2]])
    vals = np.array([[1, 1, 1],
                     [1, 1, -1],
                     [-1, 1, 1],
                     [-1, -1, 1],
                     [1, -1, -1],
                     [-1, -1, -1],
                     [-1, -1, -1],
                     [-1, -1, 1],
                     [-1, 1, -1],
                     [1, 1, -1],
                     [1, -1, 1],
                     [1, 1, 1],
                     [1, -1, -1],
                     [1, 1, -1],
                     [1, -1, 1],
                     [-1, -1, 1],
                     [-1, 1, -1],
                     [-1, 1, 1],
                     [-1, 1, 1],
                     [1, 1, 1],
                     [-1, 1, -1],
                     [-1, -1, -1],
                     [1, -1, 1],
                     [1, -1, -1]])
    if elements is None:
        elements = len(perms)

    mats = np.zeros((len(elements), 3, 3))
    perms = perms[elements,]
    vals = vals[elements,]
    for i, (p, v) in enumerate(zip(perms, vals)):
        mats[i][(0, 1, 2), p] = v

    return mats

def O_group_names():
    return ["A1", "A2", "E", "T1", "T2"]

def Oh_point_group():
    return np.array([
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 1, -1, -1, 1, 1, -1, 1, 1, -1],
        [2, -1, 0, 0, 2, 2, 0, -1, 2, 0],
        [3, 0, -1, 1, -1, 3, 1, 0, -1, -1],
        [3, 0, 1, -1, -1, 3, -1, 0, -1, 1],
        [1, 1, 1, 1, 1, -1, -1, -1, -1, -1],
        [1, 1, -1, -1, 1, -1, 1, -1, -1, 1],
        [2, -1, 0, 0, 2, -2, 0, 1, -2, 0],
        [3, 0, -1, 1, -1, -3, -1, 0, 1, 1],
        [3, 0, 1, -1, -1, -3, 1, 0, 1, -1]
    ])
def Oh_group_classes():
    classes = [
        np.array([0]),
        np.array([3, 4, 13, 17, 30, 34, 43, 44]),
        np.array([1, 2, 5, 12, 31, 46]),
        np.array([15, 16, 32, 35, 42, 45]),
        np.array([14, 33, 47]),np.array([41]),
        np.array([8, 11, 18, 21, 25, 26]),
        np.array([9, 10, 19, 23, 24, 28, 37, 38]),
        np.array([6, 20, 27]),
        np.array([7, 22, 29, 36, 39, 40])
        ]
    elements = np.array([[0, 1, 2, 3, 4, 5, 6, 7],
                         [0, 1, 5, 4, 3, 2, 6, 7],
                         [0, 3, 2, 1, 4, 7, 6, 5],
                         [0, 3, 7, 4, 1, 2, 6, 5],
                         [0, 4, 5, 1, 3, 7, 6, 2],
                         [0, 4, 7, 3, 1, 5, 6, 2],
                         [1, 0, 3, 2, 5, 4, 7, 6],
                         [1, 0, 4, 5, 2, 3, 7, 6],
                         [1, 2, 3, 0, 5, 6, 7, 4],
                         [1, 2, 6, 5, 0, 3, 7, 4],
                         [1, 5, 4, 0, 2, 6, 7, 3],
                         [1, 5, 6, 2, 0, 4, 7, 3],
                         [2, 1, 0, 3, 6, 5, 4, 7],
                         [2, 1, 5, 6, 3, 0, 4, 7],
                         [2, 3, 0, 1, 6, 7, 4, 5],
                         [2, 3, 7, 6, 1, 0, 4, 5],
                         [2, 6, 5, 1, 3, 7, 4, 0],
                         [2, 6, 7, 3, 1, 5, 4, 0],
                         [3, 0, 1, 2, 7, 4, 5, 6],
                         [3, 0, 4, 7, 2, 1, 5, 6],
                         [3, 2, 1, 0, 7, 6, 5, 4],
                         [3, 2, 6, 7, 0, 1, 5, 4],
                         [3, 7, 4, 0, 2, 6, 5, 1],
                         [3, 7, 6, 2, 0, 4, 5, 1],
                         [4, 0, 1, 5, 7, 3, 2, 6],
                         [4, 0, 3, 7, 5, 1, 2, 6],
                         [4, 5, 1, 0, 7, 6, 2, 3],
                         [4, 5, 6, 7, 0, 1, 2, 3],
                         [4, 7, 3, 0, 5, 6, 2, 1],
                         [4, 7, 6, 5, 0, 3, 2, 1],
                         [5, 1, 0, 4, 6, 2, 3, 7],
                         [5, 1, 2, 6, 4, 0, 3, 7],
                         [5, 4, 0, 1, 6, 7, 3, 2],
                         [5, 4, 7, 6, 1, 0, 3, 2],
                         [5, 6, 2, 1, 4, 7, 3, 0],
                         [5, 6, 7, 4, 1, 2, 3, 0],
                         [6, 2, 1, 5, 7, 3, 0, 4],
                         [6, 2, 3, 7, 5, 1, 0, 4],
                         [6, 5, 1, 2, 7, 4, 0, 3],
                         [6, 5, 4, 7, 2, 1, 0, 3],
                         [6, 7, 3, 2, 5, 4, 0, 1],
                         [6, 7, 4, 5, 2, 3, 0, 1],
                         [7, 3, 0, 4, 6, 2, 1, 5],
                         [7, 3, 2, 6, 4, 0, 1, 5],
                         [7, 4, 0, 3, 6, 5, 1, 2],
                         [7, 4, 5, 6, 3, 0, 1, 2],
                         [7, 6, 2, 3, 4, 5, 1, 0],
                         [7, 6, 5, 4, 3, 2, 1, 0]])

    return elements, classes

def Oh_group_matrices(elements=None):
    # TODO: compress this
    perms = np.array([[0, 1, 2],
                      [1, 0, 2],
                      [2, 1, 0],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 2, 1],
                      [0, 1, 2],
                      [1, 0, 2],
                      [2, 1, 0],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 2, 1],
                      [2, 1, 0],
                      [2, 0, 1],
                      [0, 1, 2],
                      [1, 0, 2],
                      [0, 2, 1],
                      [1, 2, 0],
                      [2, 1, 0],
                      [2, 0, 1],
                      [0, 1, 2],
                      [1, 0, 2],
                      [0, 2, 1],
                      [1, 2, 0],
                      [1, 2, 0],
                      [0, 2, 1],
                      [1, 0, 2],
                      [0, 1, 2],
                      [2, 0, 1],
                      [2, 1, 0],
                      [1, 2, 0],
                      [0, 2, 1],
                      [1, 0, 2],
                      [0, 1, 2],
                      [2, 0, 1],
                      [2, 1, 0],
                      [0, 2, 1],
                      [1, 2, 0],
                      [2, 0, 1],
                      [2, 1, 0],
                      [1, 0, 2],
                      [0, 1, 2],
                      [0, 2, 1],
                      [1, 2, 0],
                      [2, 0, 1],
                      [2, 1, 0],
                      [1, 0, 2],
                      [0, 1, 2]])
    vals = np.array([[1, 1, 1],
                     [-1, -1, -1],
                     [1, -1, 1],
                     [-1, 1, -1],
                     [1, -1, -1],
                     [-1, 1, 1],
                     [1, 1, -1],
                     [-1, -1, 1],
                     [1, -1, -1],
                     [-1, 1, 1],
                     [1, -1, 1],
                     [-1, 1, -1],
                     [-1, -1, -1],
                     [1, 1, 1],
                     [-1, 1, -1],
                     [1, -1, 1],
                     [1, 1, -1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [1, 1, -1],
                     [-1, 1, 1],
                     [1, -1, -1],
                     [1, 1, 1],
                     [-1, -1, -1],
                     [1, 1, -1],
                     [-1, -1, 1],
                     [-1, 1, -1],
                     [1, -1, 1],
                     [-1, -1, -1],
                     [1, 1, 1],
                     [1, 1, 1],
                     [-1, -1, -1],
                     [-1, 1, 1],
                     [1, -1, -1],
                     [-1, -1, 1],
                     [1, 1, -1],
                     [1, -1, -1],
                     [-1, 1, 1],
                     [1, -1, 1],
                     [-1, 1, -1],
                     [1, 1, 1],
                     [-1, -1, -1],
                     [1, -1, 1],
                     [-1, 1, -1],
                     [1, -1, -1],
                     [-1, 1, 1],
                     [1, 1, -1],
                     [-1, -1, 1]])
    if elements is None:
        elements = len(perms)

    mats = np.zeros((len(elements), 3, 3))
    perms = perms[elements,]
    vals = vals[elements,]
    for i, (p, v) in enumerate(zip(perms, vals)):
        mats[i][(0, 1, 2), p] = v

    return mats

def Oh_group_names():
    names = O_group_names()
    return [s+"g" for s in names] + [s+"u" for s in names]

def T_point_group():
    return np.array([
        [1, 1, 1, 1],
        [1, np.exp((2j * np.pi) / 3), np.exp(-((2j * np.pi) / 3)), 1],
        [1, np.exp(-((2j * np.pi) / 3)), np.exp((2j * np.pi) / 3), 1],
        [3, 0, 0, -1]
    ])

def T_group_classes():
    classes = [
        np.array([0]),
        np.array([1, 5, 6, 10]),
        np.array([2, 4, 7, 9]),
        np.array([3, 8, 11])
    ]
    elements = np.array([[0, 1, 2, 3],
                         [0, 2, 3, 1],
                         [0, 3, 1, 2],
                         [1, 0, 3, 2],
                         [1, 2, 0, 3],
                         [1, 3, 2, 0],
                         [2, 0, 1, 3],
                         [2, 1, 3, 0],
                         [2, 3, 0, 1],
                         [3, 0, 2, 1],
                         [3, 1, 0, 2],
                         [3, 2, 1, 0]])
    return elements, classes

def T_group_matrices(elements=None):
    # TODO: compress this
    perms = np.array([[0, 1, 2],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 1, 2],
                      [1, 2, 0],
                      [2, 0, 1],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 1, 2],
                      [1, 2, 0],
                      [2, 0, 1],
                      [0, 1, 2]])
    vals = np.array([[1, 1, 1],
                     [1, 1, 1],
                     [1, 1, 1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [1, -1, -1],
                     [1, -1, -1],
                     [1, -1, -1],
                     [-1, 1, -1],
                     [-1, 1, -1],
                     [-1, 1, -1]])
    if elements is None:
        elements = len(perms)

    mats = np.zeros((len(elements), 3, 3))
    perms = perms[elements,]
    vals = vals[elements,]
    for i, (p, v) in enumerate(zip(perms, vals)):
        mats[i][(0, 1, 2), p] = v

    return mats

def T_group_names():
    return ["A", "Ea", "Eb", "T"]

def Td_point_group():
    return np.array([
        [1, 1, 1, 1, 1],
        [1, 1, 1, -1, -1],
        [2, -1, 2, 0, 0],
        [3, 0, -1, 1, -1],
        [3, 0, -1, -1, 1]
    ])
def Td_group_classes():
    classes = [
        np.array([0]),
        np.array([3, 4, 8, 11, 12, 15, 19, 20]),
        np.array([7, 16, 23]),
        np.array([9, 10, 13, 17, 18, 22]),
        np.array([1, 2, 5, 6, 14, 21])
    ]
    elements = np.array([[0, 1, 2, 3],
                         [0, 1, 3, 2],
                         [0, 2, 1, 3],
                         [0, 2, 3, 1],
                         [0, 3, 1, 2],
                         [0, 3, 2, 1],
                         [1, 0, 2, 3],
                         [1, 0, 3, 2],
                         [1, 2, 0, 3],
                         [1, 2, 3, 0],
                         [1, 3, 0, 2],
                         [1, 3, 2, 0],
                         [2, 0, 1, 3],
                         [2, 0, 3, 1],
                         [2, 1, 0, 3],
                         [2, 1, 3, 0],
                         [2, 3, 0, 1],
                         [2, 3, 1, 0],
                         [3, 0, 1, 2],
                         [3, 0, 2, 1],
                         [3, 1, 0, 2],
                         [3, 1, 2, 0],
                         [3, 2, 0, 1],
                         [3, 2, 1, 0]])
    return elements, classes

def Td_group_matrices(elements=None):
    #TODO: compress this
    perms = np.array([[0, 1, 2],
                      [2, 1, 0],
                      [0, 2, 1],
                      [2, 0, 1],
                      [1, 2, 0],
                      [1, 0, 2],
                      [2, 1, 0],
                      [0, 1, 2],
                      [1, 2, 0],
                      [1, 0, 2],
                      [0, 2, 1],
                      [2, 0, 1],
                      [2, 0, 1],
                      [0, 2, 1],
                      [1, 0, 2],
                      [1, 2, 0],
                      [0, 1, 2],
                      [2, 1, 0],
                      [1, 0, 2],
                      [1, 2, 0],
                      [2, 0, 1],
                      [0, 2, 1],
                      [2, 1, 0],
                      [0, 1, 2]])
    vals = np.array([[1, 1, 1],
                     [1, 1, 1],
                     [1, 1, 1],
                     [1, 1, 1],
                     [1, 1, 1],
                     [1, 1, 1],
                     [-1, 1, -1],
                     [-1, 1, -1],
                     [-1, 1, -1],
                     [-1, 1, -1],
                     [-1, 1, -1],
                     [-1, 1, -1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [1, -1, -1],
                     [1, -1, -1],
                     [1, -1, -1],
                     [1, -1, -1],
                     [1, -1, -1],
                     [1, -1, -1]])
    if elements is None:
        elements = len(perms)

    mats = np.zeros((len(elements), 3, 3))
    perms = perms[elements,]
    vals = vals[elements,]
    for i,(p,v) in enumerate(zip(perms, vals)):
        mats[i][(0, 1, 2), p] = v

    return mats

def Td_group_names():
    return ["A1", "A2", "E", "T1", "T2"]

def Th_point_group():
    return np.array([
        [1, 1, 1, 1, 1, 1, 1, 1],
        [1, np.exp((2j * np.pi) / 3), np.exp(-((2j * np.pi) / 3)), 1, 1, np.exp((2j * np.pi) / 3),
         np.exp(-((2j * np.pi) / 3)), 1],
        [1, np.exp(-((2j * np.pi) / 3)), np.exp((2j * np.pi) / 3), 1, 1, np.exp(-((2j * np.pi) / 3)),
         np.exp((2j * np.pi) / 3), 1],
        [3, 0, 0, -1, 3, 0, 0, -1],
        [1, 1, 1, 1, -1, -1, -1, -1],
        [1, np.exp((2j * np.pi) / 3), np.exp(-((2j * np.pi) / 3)), 1, -1, -np.exp((2j * np.pi) / 3),
         -np.exp(-((2j * np.pi) / 3)), -1],
        [1, np.exp(-((2j * np.pi) / 3)), np.exp((2j * np.pi) / 3), 1, -1, -np.exp(-((2j * np.pi) / 3)),
         -np.exp((2j * np.pi) / 3), -1],
        [3, 0, 0, -1, -3, 0, 0, 1]
    ])

def Th_group_classes():
    classes = [
        np.array([0]), np.array([1, 5, 6, 10]), np.array([2, 4, 7, 9]), np.array([3, 8, 11]), np.array([12]),
        np.array([14, 16, 19, 21]), np.array([13, 17, 18, 22]), np.array([15, 20, 23])
    ]
    elements = np.array([[0, 1, 2, 3, 4, 5],
                         [0, 2, 3, 1, 4, 5],
                         [0, 3, 1, 2, 4, 5],
                         [1, 0, 3, 2, 4, 5],
                         [1, 2, 0, 3, 4, 5],
                         [1, 3, 2, 0, 4, 5],
                         [2, 0, 1, 3, 4, 5],
                         [2, 1, 3, 0, 4, 5],
                         [2, 3, 0, 1, 4, 5],
                         [3, 0, 2, 1, 4, 5],
                         [3, 1, 0, 2, 4, 5],
                         [3, 2, 1, 0, 4, 5],
                         [0, 1, 2, 3, 5, 4],
                         [0, 2, 3, 1, 5, 4],
                         [0, 3, 1, 2, 5, 4],
                         [1, 0, 3, 2, 5, 4],
                         [1, 2, 0, 3, 5, 4],
                         [1, 3, 2, 0, 5, 4],
                         [2, 0, 1, 3, 5, 4],
                         [2, 1, 3, 0, 5, 4],
                         [2, 3, 0, 1, 5, 4],
                         [3, 0, 2, 1, 5, 4],
                         [3, 1, 0, 2, 5, 4],
                         [3, 2, 1, 0, 5, 4]])
    return elements, classes

def Th_group_matrices(elements=None):
    # TODO: compress this
    perms = np.array([[0, 1, 2],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 1, 2],
                      [1, 2, 0],
                      [2, 0, 1],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 1, 2],
                      [1, 2, 0],
                      [2, 0, 1],
                      [0, 1, 2],
                      [0, 1, 2],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 1, 2],
                      [1, 2, 0],
                      [2, 0, 1],
                      [2, 0, 1],
                      [1, 2, 0],
                      [0, 1, 2],
                      [1, 2, 0],
                      [2, 0, 1],
                      [0, 1, 2]])
    vals = np.array([[1, 1, 1],
                     [1, 1, 1],
                     [1, 1, 1],
                     [1, -1, -1],
                     [1, -1, -1],
                     [1, -1, -1],
                     [-1, 1, -1],
                     [-1, 1, -1],
                     [-1, 1, -1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [-1, -1, 1],
                     [-1, -1, -1],
                     [-1, -1, -1],
                     [-1, -1, -1],
                     [-1, 1, 1],
                     [-1, 1, 1],
                     [-1, 1, 1],
                     [1, -1, 1],
                     [1, -1, 1],
                     [1, -1, 1],
                     [1, 1, -1],
                     [1, 1, -1],
                     [1, 1, -1]])
    if elements is None:
        elements = len(perms)

    mats = np.zeros((len(elements), 3, 3))
    perms = perms[elements,]
    vals = vals[elements,]
    for i, (p, v) in enumerate(zip(perms, vals)):
        mats[i][(0, 1, 2), p] = v

    return mats

def Th_group_names():
    names = T_group_names()
    return [s+"g" for s in names] + [s+"u" for s in names]

fixed_size_point_group_map = {
    'I': {
        "characters":I_point_group,
        "classes":I_group_classes,
        "matrices":I_group_matrices,
        "names":I_group_names
    },
    "Ih": {
        "characters":Ih_point_group,
        "classes":Ih_group_classes,
        "matrices":Ih_group_matrices,
        "names":Ih_group_names
    },
    "O": {
        "characters":O_point_group,
        "classes":O_group_classes,
        "matrices":O_group_matrices,
        "names":O_group_names
    },
    "Oh": {
        "characters":Oh_point_group,
        "classes":Oh_group_classes,
        "matrices":Oh_group_matrices,
        "names":Oh_group_names
    },
    "T": {
        "characters":T_point_group,
        "classes":T_group_classes,
        "matrices":T_group_matrices,
        "names":T_group_names
    },
    "Td": {
        "characters":Td_point_group,
        "classes":Td_group_classes,
        "matrices":Td_group_matrices,
        "names":Td_group_names
    },
    "Th": {
        "characters":Th_point_group,
        "classes":Th_group_classes,
        "matrices":Th_group_matrices,
        "names":Th_group_names
    }
}


def fixed_size_point_group_character_table(key, **etc):
    return fixed_size_point_group_map[key]["characters"](**etc)
def fixed_size_point_group_classes(key, **etc):
    class_gen = fixed_size_point_group_map[key].get("classes")
    if class_gen is not None:
        return class_gen(**etc)
    else:
        return None
def fixed_size_point_group_matrices(key, **etc):
    mat_gen = fixed_size_point_group_map[key].get("matrices")
    if mat_gen is not None:
        return mat_gen(**etc)
    else:
        return None

def point_group_data(key, n=None, prop=None, **etc):
    if n is None:
        if key not in fixed_size_point_group_map and key in point_group_map:
            raise ValueError(f"group order must be supplied for parametrized point group '{key}")
        data = fixed_size_point_group_map[key]
    else:
        if key not in point_group_map and key in fixed_size_point_group_map:
            raise ValueError(f"group order cannot be supplied for fixed sized point group '{key}")
        data = point_group_map[key]

    if prop is None:
        return data
    else:
        gen = data.get(prop)
        if gen is None: return None

        if n is None:
            return gen(**etc)
        else:
            return gen(n, **etc)

class CharacterTable:
    def __init__(self,
                 characters,
                 group_name=None,
                 class_names=None,
                 irrep_names=None,
                 permutations=None,
                 classes=None,
                 matrices=None
                 ):
        self.table = np.asanyarray(characters)
        if np.issubdtype(self.table.dtype, np.dtype(complex)):
            col_weights = np.real(nput.vec_dots(self.table.T, np.conj(self.table.T)))
        else:
            col_weights = nput.vec_dots(self.table.T, self.table.T)
        self.group_order = int(col_weights[0])
        self.class_sizes = (col_weights[0] // col_weights).astype(int)
        self.group_name = group_name
        self.class_names = class_names
        self.irrep_names = irrep_names
        self.permutations = permutations
        self.classes = classes
        self.matrices = matrices

    @classmethod
    def symmetric_group(cls, n):
        chars, parts = symmetric_group_character_table(n, return_partitions=True)
        return cls(
            chars,
            group_name=f"S_{n}",
            class_names=[
                "".join(f"{x}[{c}]" for x, c in zip(*np.unique(p, return_counts=True)))
                for p in parts
            ],
            classes=parts
        )

    @classmethod
    def cyclic_group(cls, n):
        elements, classes = cyclic_group_classes(n)
        mats = cyclic_group_operation_representation(n, [c[0] for c in classes])

        return cls(
            cyclic_group_character_table(n),
            group_name=f"C_{n}",
            class_names=[str(i) for i in range(n)],
            permutations=elements,
            classes=classes,
            matrices=mats
        )

    @classmethod
    def dihedral_group(cls, n):
        elements, classes = dihedral_group_classes(n)
        mats = dihedral_group_operation_representation(n, [c[0] for c in classes])

        return cls(
            dihedral_group_character_table(n),
            group_name=f"D_{n}",
            permutations=elements,
            classes=classes,
            matrices=mats
        )

    @classmethod
    def improper_rotation_group(cls, n):
        elements, classes = improper_rotation_group_classes(n)
        mats = improper_rotation_group_operation_representation(n, [c[0] for c in classes])

        return cls(
            improper_rotation_group_character_table(n),
            group_name=f"s_{n}",
            permutations=elements,
            classes=classes,
            matrices=mats
            # classes=[str(i) for i in range(n)]
        )

    @classmethod
    def point_group(cls, key, n=None):
        class_data = point_group_data(key, n=n, prop='classes')
        if class_data is not None:
            elements, classes = class_data
            mats = point_group_data(key, n=n, prop='matrices', elements=[c[0] for c in classes])
        else:
            elements = classes = mats = None
        return cls(
            point_group_data(key, n=n, prop='characters'),
            group_name=(key, n) if n is not None else key,
            classes=classes,
            permutations=elements,
            matrices=mats,
            irrep_names=point_group_data(key, n=n, prop='names')
            # classes=[str(i) for i in range(n)]
        )

    @classmethod
    def fixed_size_point_group(cls, key):
        return cls.point_group(key, n=None)

    @classmethod
    def format_character_table(self, table, group_name=None, classes=None, irrep_names=None):
        from ..Formatters import TableFormatter

        table = np.asanyarray(table)
        dtype = table.dtype
        col_types = ["{:.0f}" if np.issubdtype(dtype, np.dtype(int)) else "{:.3f}"] * len(table[0])

        table = table.tolist()
        if group_name is not None:
            group_name = str(group_name)
            if irrep_names is None:
                irrep_names = [""] * len(table)
            if classes is None:
                classes = [""] * len(table[0])

        if irrep_names is not None:
            table = [
                [i] + t
                for i,t in zip(irrep_names, table)
            ]


        return TableFormatter(
            ([""] if irrep_names is not None else []) + col_types,
            headers=([group_name] + classes) if group_name is not None else classes,
            column_join=[" | "] + [" "]*len(table[0]) if irrep_names is not None else None
        ).format(table)

    @property
    def group_key(self):
        if self.group_name is not None:
            if (
                    isinstance(self.group_name, tuple)
                    and len(self.group_name) == 2
                    and isinstance(self.group_name[0], str)
                    and nput.is_int(self.group_name[1])
            ):
                return self.group_name[0][:1] + str(self.group_name[1]) + self.group_name[0][1:]
            else:
                return self.group_name

    @classmethod
    def symmetry_symbol(cls, primary_axis, secondary_axis, type, axis, root, order):
        t = nput.TransformationTypes(type)
        if t == nput.TransformationTypes.Identity:
            return "E"
        elif t == nput.TransformationTypes.Inversion:
            return "i"
        elif t == nput.TransformationTypes.Rotation:
            if root == 1:
                return f"C{order:.0f}"
            else:
                return f"C{order:.0f}[{root:.0f}]"
        elif t == nput.TransformationTypes.Reflection:
            if primary_axis is None or abs(np.dot(primary_axis, axis)) > 1 - 1e-2:
                return "ph"
            elif secondary_axis is not None:
                ov = abs(np.dot(secondary_axis, axis))
                if ov > 1 - 1e-2:
                    return "pv"
                else:
                    return "pd"
            else:
                return "pv"
        elif t == nput.TransformationTypes.ImproperRotation:
            if root == 1:
                return f"S{order:.0f}"
            else:
                return f"S{order:.0f}[{root:.0f}]"
        else:
            raise ValueError(f"don't have a symbol for {t}")


    def get_class_symbols(self):
        if self.matrices is None: return None

        _, types, axes, roots, orders = nput.identify_cartesian_transformation_type(self.matrices, max_rotation_order=60)
        primary_axis = None
        primary_axis_order = None
        secondary_axis = None
        for t,a,o in zip(types, axes, orders):
            t = nput.TransformationTypes(t)
            if t == nput.TransformationTypes.Rotation:
                if primary_axis_order is None or primary_axis_order < o:
                    primary_axis_order = o
                    primary_axis = a
        if primary_axis is not None:
            for t, a, o in zip(types, axes, orders):
                t = nput.TransformationTypes(t)
                if (
                        t == nput.TransformationTypes.Rotation
                        and o == 2
                        and abs(np.dot(primary_axis, a)) < 1e-2
                ):
                    secondary_axis = a
                    break

        syms = []
        for t, a, r, o in zip(types, axes, roots, orders):
            s = self.symmetry_symbol(primary_axis, secondary_axis, t, a, r, o)
            s_counts = sum(1 for s2 in syms if s2.strip("'") == s)
            syms.append(s + "'"*s_counts)

        return syms

    def format(self, classes=None, irrep_names=None, group_name=None):
        if classes is None:
            classes = self.class_names
            if classes is None:
                classes = self.get_class_symbols()
        if irrep_names is None:
            irrep_names = self.irrep_names
        if group_name is None:
            group_name = self.group_key
        return self.format_character_table(
            self.table,
            group_name=group_name,
            classes=classes,
            irrep_names=irrep_names
        )

    @property
    def character_basis(self):
        weights = self.class_sizes / self.group_order
        # print(self.class_sizes, self.group_order)
        # print(self.table)
        # print(self.table * weights[np.newaxis, :])
        return self.table * weights[np.newaxis, :]

    def extend_class_representation(self, rep):
        full = np.empty((rep.shape[0], self.group_order), dtype=rep.dtype)
        p = 0
        for i in range(rep.shape[1]):
            e = p+self.class_sizes[i]
            full[:, p:e] = rep[:, (i,)]
            p = e
        return full

    def get_extended_character_table(self):
        return self.extend_class_representation(self.table)

    def decompose_representation(self, rep):
        rep = np.asanyarray(rep)
        t = self.character_basis
        if np.issubdtype(t.dtype, np.dtype(complex)):
            t = np.conj(t)
        return np.tensordot(t, rep, axes=[-1, -1])

    def space_representation(self, mats, symms=None):
        if symms is None:
            symms = self.matrices
        if symms is None:
            raise ValueError("need `matrices` to construct concrete space representation")
        mats = np.asanyarray(mats)
        if mats.ndim == 1:
            mats = np.diag(mats)
        elif mats.shape[-1] != mats.shape[-2]:
            raise ValueError("matrices required, if stack of vectors used, wrap input with `nput.vec_tensordiag`")

        rep_dim = (mats.shape[-1] - (mats.shape[-1] % 3)) // 3
        if affine := mats.shape[-1] % 3 != 0: # affine transform for fixed atom comparisons
            symms = nput.vec_block_diag(
                np.broadcast_to(symms[:, np.newaxis, :, :], (symms.shape[0], rep_dim) + symms.shape[-2:])
            )
            shifts = np.broadcast_to(
                np.zeros(symms.shape[-1])[np.newaxis, :],
                symms.shape[:-1]
            )
            symms = nput.affine_matrix(symms, shifts)

        rep = np.moveaxis(np.moveaxis(np.tensordot(symms, mats, axes=[-1, -2]), 0, -2), 0, -2)
        # rep = np.moveaxis(tf, -2, -3)
        if affine:
            disps_new = rep[..., :-1, -1]
            disps_old = mats[..., :-1, -1][..., np.newaxis, :]
            dists = np.linalg.norm(
                disps_new.reshape(disps_new.shape[:-1] + (-1, 3))
                - disps_old.reshape(disps_old.shape[:-1] + (-1, 3)),
                axis=-1)
            dists = np.repeat(dists[..., :, np.newaxis], 3, axis=-1).reshape(disps_new.shape)
            mask = (dists < 1e-2).astype(int)
            rep = rep[..., :-1, :-1]
        else:
            mask = None

        diag_inds = nput.diag_indices(rep.shape[:-2], rep.shape[-1])
        tr_elems = rep[diag_inds]
        if mask is not None:
            tr_elems = tr_elems * mask
        return np.sum(tr_elems, axis=-1)

    def matrix_from_representation(self, vec):
        vec = np.asanyarray(vec)
        weights = self.class_sizes / self.group_order
        scaled_mats = weights[:, np.newaxis, np.newaxis] * self.matrices
        return np.tensordot(vec, scaled_mats, axes=[-1, 0])

    def inverse_character_representation(self, chars):
        return self.matrix_from_representation(
            np.tensordot(chars, self.character_basis, axes=[-1, -2])
        )

    def symmetry_permutations(self, coords):
        return np.array([
            nput.symmetry_permutation(coords, m)
            for m in self.matrices
        ]).T

    def axis_representation(self, include_rotations=True):
        carts = self.space_representation(nput.vec_tensordiag(np.eye(3)))
        if not include_rotations: return carts
        reflection_pos = np.where(np.linalg.det(self.matrices) < 0)
        rots = carts.copy()
        if len(reflection_pos) > 0:
            # I think this is justified, but not sure...
            # the handedness of the rotation has to flip after
            # reflection is the idea
            rots[..., reflection_pos[0]] *= -1
        return np.concatenate([carts, rots], axis=0)

    def fixed_permutation_representation(self, base_rep, perms):
        nc = len(perms)
        nrep = len(base_rep)
        mask = np.arange(nc)[:, np.newaxis] == perms
        bcast_mask = np.repeat(mask[:, np.newaxis, :], len(base_rep), axis=1).reshape(nc*nrep, -1)
        bcast_rep = np.repeat(base_rep[np.newaxis, :, :], nc, axis=0).reshape(nc*nrep, -1)
        return bcast_rep * bcast_mask

    # def symmetry_coefficients(self, permutations, signs):
    #     """
    #     Constructs symmetry coefficients given a specific permutation symmetry
    #     on the class members.
    #     There should be `nxk` permutations where `n` is the number of coordinates and `k` is the number of classes.
    #
    #     :param permutations:
    #     :return:
    #     """
    #     coeff_order = np.argsort(permutations, axis=0)
    #     perm_signs = np.vstack([s[c] for s,c in zip(signs.T, coeff_order.T)])
    #     # print()
    #     # print(permutations)
    #     # print(signs)
    #     # print(perm_signs.T)
    #     # return
    #     base_mat = np.moveaxis(np.tensordot(self.extended_character_table, perm_signs, axes=[-1, 0]), 0, -1)
    #     return base_mat

    def coordinate_representation(self, coords):
        coords = np.asanyarray(coords)
        perms = self.symmetry_permutations(coords)
        base_rep = self.axis_representation(include_rotations=False)
        return self.fixed_permutation_representation(base_rep, perms)

    def coordinate_mode_reduction(self, coords):
        base_rep = np.sum(self.coordinate_representation(coords), axis=0)
        reduced = self.decompose_representation(base_rep)
        axes = self.decompose_representation(np.sum(self.axis_representation(), axis=0))
        return reduced - axes

    def get_full_matrices(self):
        gn = self.group_name
        if isinstance(gn, str): gn = (gn,)
        return point_group_data(*gn, prop="matrices")

    def __repr__(self):
        cls = type(self)
        return f"{cls.__name__}<{self.group_key}>"
    def _ipython_display_(self):
        from ..Jupyter import NoLineWrapFormatter
        return NoLineWrapFormatter(self.format())._ipython_display_()