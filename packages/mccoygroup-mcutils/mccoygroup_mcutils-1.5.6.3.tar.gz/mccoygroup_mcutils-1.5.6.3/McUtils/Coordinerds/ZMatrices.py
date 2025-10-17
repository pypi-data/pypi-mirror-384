import collections

import numpy as np
import itertools
from .. import Numputils as nput
from .. import Iterators as itut
from ..Graphs import EdgeGraph

from .Internals import canonicalize_internal

__all__ = [
    "zmatrix_unit_convert",
    "zmatrix_indices",
    "num_zmatrix_coords",
    "zmatrix_embedding_coords",
    "set_zmatrix_embedding",
    "enumerate_zmatrices",
    "extract_zmatrix_internals",
    "extract_zmatrix_values",
    "parse_zmatrix_string",
    "format_zmatrix_string",
    "validate_zmatrix",
    "chain_zmatrix",
    "center_bound_zmatrix",
    "spoke_zmatrix",
    # "methyl_zmatrix",
    # "ethyl_zmatrix",
    "attached_zmatrix_fragment",
    "functionalized_zmatrix",
    "add_missing_zmatrix_bonds",
    "bond_graph_zmatrix",
    "reindex_zmatrix",
    "sort_complex_attachment_points",
    "complex_zmatrix"
]


def zmatrix_unit_convert(zmat, distance_conversion, angle_conversion=None, rad2deg=False, deg2rad=False):
    zm2 = np.asanyarray(zmat)
    if zm2 is zmat: zm2 = zm2.copy()

    zm2[..., :, 0] *= distance_conversion
    if angle_conversion is None:
        if deg2rad:
            zm2[..., :, 1] = np.deg2rad(zm2[..., :, 1])
            zm2[..., :, 2] = np.deg2rad(zm2[..., :, 2])
        elif rad2deg:
            zm2[..., :, 1] = np.rad2deg(zm2[..., :, 1])
            zm2[..., :, 2] = np.rad2deg(zm2[..., :, 2])
    else:
        zm2[..., :, 1] *= angle_conversion
        zm2[..., :, 2] *= angle_conversion

    return zm2

def zmatrix_indices(zmat, coords, strip_embedding=True):
    base_coords = [canonicalize_internal(c) for c in extract_zmatrix_internals(zmat, strip_embedding=strip_embedding)]
    return [
        base_coords.index(canonicalize_internal(c))
        for c in coords
    ]

emb_pos_map = [
    (0,1),
    (0,2),
    (0,3),
    None,
    (1,2),
    (1,3),
    None,
    None,
    (2,3)
]
def zmatrix_embedding_coords(zmat_or_num_atoms, array_inds=False):
    if array_inds:
        base_inds = zmatrix_embedding_coords(zmat_or_num_atoms, array_inds=False)
        return [emb_pos_map[i] for i in base_inds]
    else:
        if not nput.is_int(zmat_or_num_atoms):
            zmat_or_num_atoms = len(zmat_or_num_atoms) + (1 if len(zmat_or_num_atoms[0]) == 3 else 0)
        n: int = zmat_or_num_atoms

        if n < 1:
            return []
        elif n == 1:
            return [0, 1, 2]
        elif n == 2:
            return [0, 1, 2, 4, 5]
        else:
            return [0, 1, 2, 4, 5, 8]

def num_zmatrix_coords(zmat_or_num_atoms, strip_embedding=True):
    if not nput.is_int(zmat_or_num_atoms):
        zmat_or_num_atoms = len(zmat_or_num_atoms) + (1 if len(zmat_or_num_atoms[0]) == 3 else 0)
    n: int = zmat_or_num_atoms

    return (n*3) - (
        0
            if not strip_embedding else
        len(zmatrix_embedding_coords(n))
    )

def _zmatrix_iterate(coords, natoms=None,
                     include_origins=False,
                     canonicalize=True,
                     deduplicate=True,
                     allow_completions=False
                     ):
    # TODO: this fixes an atom ordering, to change that up we'd need to permute the initial coords...
    if canonicalize:
        coords = [tuple(reversed(canonicalize_internal(s))) for s in coords]

    if deduplicate:
        dupes = set()
        _ = []
        for c in coords:
            if c in dupes: continue
            _.append(c)
            dupes.add(c)
        coords = _

    if include_origins:
        if (1, 0) not in coords:
            coords = [(1, 0)] + coords
        if (2, 1) not in coords and (2, 0) not in coords:
            if (2, 1, 0) in coords:
                coords = [(2, 1)] + coords
            else:
                coords = [(2, 0)] + coords
        if (2, 0) in coords and (2, 0, 1) not in coords: # can this happen?
            coords.append((2,1,0))

    if natoms is None:
        all_atoms = {i for s in coords for i in s}
        natoms = len(all_atoms)

    dihedrals = [k for k in coords if len(k) == 4]
    all_dihedrals = [
        (i, j, k, l)
        for (i, j, k, l) in dihedrals
        if i > j and i > k and i > l
    ]

    # need to iterate over all N-2 choices of dihedrals (in principle)...
    # should first reduce over consistent sets
    if not allow_completions:
        dihedrals = [
            (i,j,k,l) for i,j,k,l in dihedrals
            if (i,j) in coords and (i,j,k) in coords
            # if (
            #         any(x in coords or tuple(reversed(x)) in coords for x in [(i,j), (l,k)])
            #         and any(x in coords or tuple(reversed(x)) in coords for x in [(i,j,k), (l,k,j)])
            # )
        ]

    embedding = [
        x for x in [(2, 0, 1), (2, 1, 0)]
        if x in coords
    ]

    # we also will want to sample from dihedrals that provide individual atoms
    atom_diheds = [[] for _ in range(natoms)]
    for n,(i,j,k,l) in enumerate(dihedrals):
        atom_diheds[i].append((i,j,k,l))

    # completions = []
    # if allow_completions:
    #     for d in all_dihedrals:
    #         if d in dihedrals: continue
    #         completions.extend([d[:2], d[:3]])
    #
    #     c_set = set()
    #     for d in dihedrals:
    #         c_set.add(d[:2])
    #         c_set.add(d[:3])
    #     coord_pairs = [
    #         (c[:2],c[:3])
    #         for
    #     ]
    #     for d in all_dihedrals:
    #         if d in dihedrals: continue
    #         completions.extend([d[:2], d[:3]])

    for dihed_choice in itertools.product(embedding, *atom_diheds[3:]):
        emb, dis = dihed_choice[0], dihed_choice[1:]
        yield (
            (0, -1, -1, -1),
            (1, 0, -1, -1),
            emb + (-1,)
        ) + dis

def enumerate_zmatrices(coords, natoms=None,
                        allow_permutation=True,
                        include_origins=False,
                        canonicalize=True,
                        deduplicate=True,
                        preorder_atoms=True,
                        allow_completions=False
                        ):
    if canonicalize:
        coords = [tuple(reversed(canonicalize_internal(s))) for s in coords]

    if deduplicate:
        dupes = set()
        _ = []
        for c in coords:
            if c in dupes: continue
            _.append(c)
            dupes.add(c)
        coords = _

    if natoms is None:
        all_atoms = {i for s in coords for i in s}
        natoms = len(all_atoms)

    if preorder_atoms:
        counts = itut.counts(itertools.chain(*coords))
        max_order = list(sorted(range(natoms), key=lambda k:-counts[k]))
    else:
        max_order = np.arange(natoms)

    for atoms in (
            itertools.permutations(max_order)
                if allow_permutation else
            [max_order]
    ):
        atom_perm = np.argsort(atoms)
        perm_coords = [
            tuple(reversed(canonicalize_internal([atom_perm[c] for c in crd])))
            for crd in coords
        ]
        for zm in _zmatrix_iterate(perm_coords,
                                   natoms=natoms,
                                   include_origins=include_origins,
                                   canonicalize=False,
                                   deduplicate=False,
                                   allow_completions=allow_completions
                                   ):
            yield [
                [atoms[c] if c >= 0 else c for c in z]
                for z in zm
            ]

def extract_zmatrix_internals(zmat, strip_embedding=True, canonicalize=True):
    specs = []
    if len(zmat[0]) == 3:
        return extract_zmatrix_internals(
            [[0, -1, -1, -1]]
            + [
                [i + 1] + list(z)
                for i, z in enumerate(zmat)
            ],
            strip_embedding=strip_embedding,
            canonicalize=canonicalize
        )
        # zmat = np.asanyarray(zmat)
        # return np.delete(zmat.flatten(), zmatrix_embedding_coords(len(zmat)))
    else:
        for n,row in enumerate(zmat):
            if strip_embedding and n == 0: continue
            if canonicalize:
                coord = canonicalize_internal(row[:2])
            else:
                coord = tuple(row[:2])
            specs.append(coord)
            if strip_embedding and n == 1: continue
            if canonicalize:
                coord = canonicalize_internal(row[:3])
            else:
                coord = tuple(row[:3])
            specs.append(coord)
            if strip_embedding and n == 2: continue
            if canonicalize:
                coord = canonicalize_internal(row[:4])
            else:
                coord = tuple(row[:4])
            specs.append(coord)
    return specs

def extract_zmatrix_values(zmat, inds=None, strip_embedding=True):
    zmat = np.asanyarray(zmat)
    if zmat.shape[-1] == 4:
        zmat = zmat[1:, 1:]
    if inds is None:
        n = zmat.shape[-1]*zmat.shape[-2]
        inds = np.arange(n)
        if strip_embedding:
            inds = np.delete(inds, zmatrix_embedding_coords(zmat))
    elif strip_embedding:
        real_coords = np.delete(
            np.arange(zmat.shape[-1]*zmat.shape[-2]),
            zmatrix_embedding_coords(zmat)
        )
        inds = real_coords[inds,]
    flat_mat = np.reshape(zmat, zmat.shape[:-2] + (zmat.shape[-1]*zmat.shape[-2],))
    return flat_mat[..., inds]


scan_spec = collections.namedtuple('scan_spec', ['value', 'steps', 'amount'])
def _prep_var_spec(v):
    if len(v) == 1:
        return float(v[0])
    elif len(v) == 2 and v[1] in {'f', 'F'}:
        return scan_spec(float(v[0]), -1, 0)
    elif len(v) == 3:
        return scan_spec(float(v[0]), int(v[1]), float(v[2]))
    else:
        raise ValueError(f"can't parse var spec {v}")
def parse_zmatrix_string(zmat, units="Angstroms", in_radians=False,
                         keep_variables=False,
                         variables=None,
                         dialect='gaussian'):
    from ..Data import AtomData, UnitsData
    # we have to reparse the Gaussian Z-matrix...

    possible_atoms = {d["Symbol"][:2] for d in AtomData.data.values()}

    atoms = []
    ordering = []
    coords = []
    # vars = {}

    if "Variables:" in zmat:
        zmat, vars_block = zmat.split("Variables:", 1)
    else:
        zmat = zmat.split("\n\n", 1)
        if len(zmat) == 1:
            zmat = zmat[0]
            vars_block = ""
        else:
            zmat, vars_block = zmat
    bits = [b.strip() for b in zmat.split() if len(b.strip()) > 0]

    coord = []
    ord = []
    complete = False
    last_complete = -1
    last_idx = len(bits) - 1
    for i, b in enumerate(bits):
        d = (i - last_complete) - 1
        m = d % 2
        if d == 0:
            atoms.append(b)
        elif m == 1:
            b = int(b)
            if b > 0: b = b - 1
            ord.append(b)
        elif m == 0:
            coord.append(b)

        terminal = (
                i == last_idx
                or i in {0, 3, 8}
                or (i > 8 and (i - 9) % 7 == 6)
        )
        # atom_q = bits[i + 1][:2] in possible_atoms
        if terminal:
            last_complete = i
            ord = [len(ordering)] + ord + [-1] * (3 - len(ord))
            coord = coord + [0] * (3 - len(coord))
            ordering.append(ord)
            coords.append(coord)
            ord = []
            coord = []

    split_vars = [
        vb.strip().replace("=", " ").split()
        for vb in vars_block.split("\n")
    ]
    # split_pairs = [s for s in split_pairs if len(s) == 2]

    if dialect != "gaussian":
        raise NotImplementedError(f"unsupported z-matrix dialect '{dialect}'")
    vars = {
        v[0]:_prep_var_spec(v[1:])
        for v in split_vars
        if len(v) > 0
    }
    if variables is not None:
        vars.update(variables)

    # ordering = [
    #     [i] + o
    #     for i, o in enumerate(ordering)
    # ]

    if not keep_variables:
        vals = {
            k:(
                v.value
                    if not nput.is_numeric(v) else
                v
            )
            for k, v in vars.items()
        }
        coords = [
            [
                vals[x] if x in vals else float(x)
                for x in c
            ]
            for c in coords
        ]

        # convert book angles into sensible dihedrals...
        # actually...I think I don't need to do anything for this?
        ordering = np.array(ordering)[:, :4]

        coords = np.array(coords)
        coords[:, 0] *= UnitsData.convert(units, "BohrRadius")
        coords[:, 1] = coords[:, 1] if in_radians else np.deg2rad(coords[:, 1])
        coords[:, 2] = coords[:, 2] if in_radians else np.deg2rad(coords[:, 2])
        return (atoms, ordering, coords)
    else:
        return (atoms, ordering, coords), vars

def format_zmatrix_string(atoms, zmat, ordering=None, units="Angstroms",
                          in_radians=False,
                          float_fmt="{:11.8f}",
                          index_padding=1,
                          variables=None,
                          variable_modifications=None,
                          distance_variable_format="r{i}",
                          angle_variable_format="a{i}",
                          dihedral_variable_format="d{i}"
                          ):
    from ..Data import UnitsData
    if ordering is None:
        if len(zmat) == len(atoms):
            zmat = zmat[1:]
        ordering = [
            [z[0], z[2], z[4]]
            if i > 1 else
            [z[0], z[2], -1]
            if i > 0 else
            [z[0], -1, -1]
            for i, z in enumerate(zmat)
        ]
        zmat = [
            [z[1], z[3], z[5]]
            if i > 1 else
            [z[1], z[3], -1]
            if i > 0 else
            [z[1], -1, -1]
            for i, z in enumerate(zmat)
        ]

    if isinstance(zmat, np.ndarray):
        zmat = zmat.copy()
        zmat[:, 0] *= UnitsData.convert("BohrRadius", units)
        zmat[:, 1] = zmat[:, 1] if in_radians else np.rad2deg(zmat[:, 1])
        zmat[:, 2] = zmat[:, 2] if in_radians else np.rad2deg(zmat[:, 2])
        zmat = zmat.tolist()
    else:
        cr = UnitsData.convert("BohrRadius", units)
        zmat = [
            [
                r * cr if nput.is_numeric(r) else r,
                np.rad2deg(a) if not in_radians and nput.is_numeric(a) else a,
                np.rad2deg(d) if not in_radians and nput.is_numeric(d) else d
            ]
            for r, a, d in zmat
        ]

    if variables is True:
        variables = {}
        _ = []
        for i,(r,a,d) in enumerate(zmat):
            s = []
            vr = distance_variable_format.format(i=i)
            variables[vr] = r
            s.append(vr)
            if i > 0:
                va = angle_variable_format.format(i=i)
                variables[va] = a
                s.append(va)
            else:
                s.append("")
            if i > 1:
                vd = dihedral_variable_format.format(i=i)
                variables[vd] = d
                s.append(vd)
            else:
                s.append("")
            _.append(s)
        zmat = _

    includes_atom_list = len(ordering[0]) == 4
    if not includes_atom_list:
        if len(ordering) < len(atoms):
            ordering = [[-1, -1, -1, -1]] + list(ordering)
        if len(zmat) < len(atoms):
            zmat = [[-1, -1, -1]] + list(zmat)

    if variable_modifications is not None:
        if variables is None:
            variables = {}
        includes_atom_list = len(ordering[0]) == 4
        for i,(x,r,a,d) in enumerate(ordering):
            for k,fmt,j in [
                [(x, r), distance_variable_format, 0],
                [(r, x), distance_variable_format, 0],
                [(x, r, a), angle_variable_format, 1],
                [(a, r, x), angle_variable_format, 1],
                [(x, r, a, d), dihedral_variable_format, 2],
                [(d, a, r, x), dihedral_variable_format, 2],
            ]:
                if k in variable_modifications:
                    vr = fmt.format(i=i)
                    val = variables.get(vr, zmat[i][j])
                    if not isinstance(val, str):
                        val = float_fmt.format(val)
                    variables[vr] = val + " " + variable_modifications[k]
                    zmat[i][j] = vr
                    break

    zmat = [
        ["", "", ""]
        if i == 0 else
        [z[0], "", ""]
        if i == 1 else
        [z[0], z[1], ""]
        if i == 2 else
        [z[0], z[1], z[2]]
        for i, z in enumerate(zmat)
    ]
    zmat = [
        [
            float_fmt.format(x)
                if not isinstance(x, str) else
            x
            for x in zz
        ]
        for zz in zmat
    ]
    if includes_atom_list:
        ord_list = [o[0] for o in ordering]
        atom_order = np.argsort(ord_list)
        atoms = [atoms[o] for o in ord_list]
        ordering = [
            ["", "", ""]
              if i == 0 else
            [atom_order[z[1]], "", ""]
              if i == 1 else
            [atom_order[z[1]], atom_order[z[2]], ""]
              if i == 2 else
            [atom_order[z[1]], atom_order[z[2]], atom_order[z[3]]]
              for i, z in enumerate(ordering)
        ]
    else:
        ordering = [
            ["", "", ""]
            if i == 0 else
                [z[0], "", ""]
            if i == 1 else
                [z[0], z[1], ""]
            if i == 2 else
                [z[0], z[1], z[2]]
            for i, z in enumerate(ordering)
        ]
    ordering = [
        ["{:.0f}".format(x + index_padding) if not isinstance(x, str) else x for x in zz]
        for zz in ordering
    ]

    max_at_len = max(len(a) for a in atoms)

    nls = [
        max([len(xyz[i]) for xyz in ordering])
        for i in range(3)
    ]
    zls = [
        max([len(xyz[i]) for xyz in zmat])
        for i in range(3)
    ]

    fmt_string = f"{{a:<{max_at_len}}} {{n[0]:>{nls[0]}}} {{r[0]:>{zls[0]}}} {{n[1]:>{nls[1]}}} {{r[1]:>{zls[1]}}} {{n[2]:>{nls[2]}}} {{r[2]:>{zls[2]}}}"
    zm = "\n".join(
        fmt_string.format(
            a=a,
            n=n,
            r=r
        )
        for a, n, r in zip(atoms, ordering, zmat)
    )
    if variables is not None:
        max_symbol_len = max(len(s.split()[0]) for s in variables)
        variables = {
            k: v if isinstance(v, str) else float_fmt.format(v)
            for k, v in variables.items()
        }
        max_v_len = max(len(s) for s in variables.values())
        variables_fmt = f" {{:<{max_symbol_len}}} = {{:>{max_v_len}}}"
        variables_block = "\n".join(
            variables_fmt.format(k, v if isinstance(v, str) else float_fmt.format(v))
            for k,v in variables.items()
        )
        zm = zm + "\nVariables:\n" + variables_block

    return zm


def validate_zmatrix(ordering,
                     allow_reordering=True,
                     ensure_nonnegative=True,
                     raise_exception=False
                     ):
    proxy_order = np.array([o[0] for o in ordering])
    if allow_reordering:
        order_sorting = np.argsort(proxy_order)
        proxy_order = proxy_order[order_sorting,]
        if ensure_nonnegative and proxy_order[0] < 0:
            if raise_exception:
                raise ValueError("atom indices not all nonnegative")
            return False
        new_order = [
            [order_sorting[i] if i >= 0 else i for i in row]
            for row in ordering
        ]
        return validate_zmatrix(new_order, allow_reordering=False)
    if ensure_nonnegative and proxy_order[0] < 0:
        if raise_exception:
            raise ValueError("Z-matrix atom spec {} is non-zero")
        return False

    for n,row in enumerate(ordering):
        if (
                any(i > n for i in row)
                or any(i > row[0] for i in row[1:])
                or len(set(row)) < len(row)
        ):
            if raise_exception:
                raise ValueError(f"Z-matrix line {n} invalid {row}")
            return False

    return True

def chain_zmatrix(n):
    return [
        list(range(i, i-4, -1))
        for i in range(n)
    ]

def center_bound_zmatrix(n, center=-1):
    return [
        [
            i,
            center,
            (
                (i - 2)
                if i > 1 else
                0
                if i == 1 else
                -2
            ),
            (
                (i - 1)
                if i > 1 else
                -3 + i
            ),
        ]
        for i in range(n)
    ]

def attached_zmatrix_fragment(n, fragment, attachment_points):
    return [
        [attachment_points[-r-1] if r < 0 else n+r for r in row]
        for row in fragment
    ]

def set_zmatrix_embedding(zmat, embedding=None):
    zmat = np.array(zmat)
    if embedding is None:
        embedding = [-1, -2, -3, -1, -2, -1]
    emb_pos = zmatrix_embedding_coords(zmat, array_inds=True)
    for (i,j),v in zip(emb_pos, embedding):
        zmat[..., i,j] = v
    return zmat

# ethyl_zmatrix = [
#     [0, -1, -2, -3],
#     [1,  0, -1, -2],
#     [2,  0,  1, -1]
# ]
#
# methyl_zmatrix = [
#     [0, -1, -2, -3],
#     [1,  0, -1, -2],
#     [2,  0,  1, -1],
#     [3,  0,  2,  1]
# ]


def functionalized_zmatrix(
        base_zm,
        attachments:'dict|list[list[int], list[int]]'=None,
        single_atoms:list[int]=None, # individual components, embedding doesn't matter
        methyl_positions:list[int]=None, # all bonds attached to central atom, angles relative to eachother
        ethyl_positions:list[int]=None, # all bonds attached to central atom, angles relative to eachother
):
    if nput.is_numeric(base_zm):
        zm = chain_zmatrix(base_zm)
    else:
        zm = [
            list(x) for x in base_zm
        ]
    if attachments is None:
        attachments = {}
    if hasattr(attachments, 'items'):
        attachments = attachments.items()
    for attachment_points, fragment in attachments:
        if nput.is_numeric(fragment):
            fragment = chain_zmatrix(fragment)
        zm = zm + attached_zmatrix_fragment(
            len(zm),
            fragment,
            attachment_points
        )
    if single_atoms is not None:
        #TODO: make this bond graph relevant
        for atom in single_atoms:
            key = [z for z in zm if z[0] == atom]
            bonds = [z[0] for z in zm if z[1] == atom]
            if len(key) > 0:
                key = [
                    bonds[-(k+1)]
                        if k < 0 and abs(k) <= len(bonds) else
                    k
                    for k in key[0][:-1]
                ]
                zm = zm + [
                    [len(zm)] + key
                ]
            else:
                zm = zm + attached_zmatrix_fragment(
                    len(zm),
                    [[0, -1, -2, -3]],
                    [
                        (atom - i)
                            if i < 0 and (atom - i) < len(zm) else
                        i
                        for i in range(atom, atom - 4, -1)
                    ]
                )
    if methyl_positions is not None:
        for atom in methyl_positions:
            zm = zm + attached_zmatrix_fragment(
                len(zm),
                [
                    [0, -1, -2, -3],
                    [1, -1,  0, -2],
                    [2, -1,  0,  1],
                ],
                [
                    (atom - i) if i < 0 else i
                    for i in range(atom, atom - 4, -1)
                ]
            )
    if ethyl_positions is not None:
        for atom in ethyl_positions:
            zm = zm + attached_zmatrix_fragment(
                len(zm),
                [
                    [0, -1, -2, -3],
                    [1, -1,  0, -2]
                ],
                [
                    (atom - i) if i < 0 else i
                    for i in range(atom, atom - 4, -1)
                ]
            )
    return zm


def spoke_zmatrix(m, spoke=1, root=1):
    if nput.is_int(spoke):
        spoke = chain_zmatrix(spoke)

    if nput.is_int(root):
        root = chain_zmatrix(root)

    nroot = len(root) - 1
    if len(root) < 3:
        nrem = (3 - len(root))
        # no need for any moduli or floors, we just know
        if len(spoke) == 1:
            nspoke = nrem
        else:
            nspoke = 1

        for i in range(nspoke):
            if len(root) > 1:
                mroot = nroot + 1
            else:
                mroot = -1

            if len(root) > 2:
                proot = nroot + 2
            elif len(root) > 1:
                proot = nroot - 1
            else:
                proot = nroot - 2
            root = functionalized_zmatrix(
                root,
                [
                    [_attachment_point([
                        nroot,
                        mroot,
                        proot
                    ]), spoke]
                ]
            )
        if nspoke == 1:
            if nrem == 1:
                a = nroot - 1
                b = nroot + 1
            else:
                a = nroot + 1
                b = nroot + 2
        else:
            a = nroot + 1
            b = nroot + 2
        m = m - nspoke
    else:
        a = nroot - 1
        b = nroot - 2



    return functionalized_zmatrix(
        root,
        [
            [_attachment_point([nroot, a, b]), spoke]
            for _ in range(m)
        ]
    )


def reindex_zmatrix(zm, perm):
    return [
        [perm[r] if r >= 0 else r for r in row]
        for row in zm
    ]

def canonicalize_zmatrix(zm):
    if len(zm[0]) == 3:
        zm = [
            [0, -1, -2, -3]
        ] + [
            [i+1] + z
            for i,z in enumerate(zm)
        ]

    z_vec = np.array([z[0] for z in zm])
    perm = {z:i for i,z in enumerate(z_vec)}
    return z_vec, reindex_zmatrix(zm, perm)

def _attachment_point(i_pos):
    r = None
    a = None
    d = None
    if nput.is_int(i_pos):
        i_pos = [i_pos]

    if len(i_pos) > 0:
        r = i_pos[0]
    if len(i_pos) > 1:
        a = i_pos[1]
    if len(i_pos) > 2:
        d = i_pos[2]

    if r is None:
        if a is not None:
            if d is not None:
                if a > 0:
                    r = a - 1
                    if r == d: r = a + 1
                else:
                    r = a + 1
                    if r == d: r = a + 2
            else:
                r = (a - 1) if a > 0 else (a + 1)
        elif d is not None:
            if d > 1:
                r = d - 2
            elif d > 0:
                r = d - 1
            else:
                r = d + 1
        else:
            r = 0
    if a is None:
        if r > 0:
            a = r - 1
            if d is not None and a == d:
                if r > 1:
                    a = r - 2
                else:
                    a = r + 1
        else:
            a = r + 1
            if d is not None and a == d:
                a = r + 2
    if d is None:
        if r > 1:
            d = r - 2
            if a is not None and a == d:
                d = r - 1
        elif r > 0:
            d = r - 1
            if a is not None and a == d:
                d = r + 1
        else:
            d = r + 1
            if a is not None and a == d:
                d = r + 2

    return (r, a, d)
def add_missing_zmatrix_bonds(
        base_zmat,
        bonds,
        max_iterations=None
):
    atoms, zm = canonicalize_zmatrix(base_zmat)
    new_bonds = {}
    reindexing = list(atoms)
    for bi, be in bonds:
        if bi in atoms and be in atoms: continue
        if bi not in atoms and be not in atoms: continue
        if bi in atoms:
            # bi_pos = np.where(atoms == bi)[0][0]
            if bi not in new_bonds: new_bonds[bi] = []
            new_bonds[bi].append(be)
        if be in atoms:
            if be not in new_bonds: new_bonds[be] = []
            new_bonds[be].append(bi)

    if len(new_bonds) == 0:
        return base_zmat, new_bonds
    else:
        mods = {}
        for i,v in new_bonds.items():
            i_pos = np.where(atoms == i)[0][0]
            reindexing.extend(v)
            ix = _attachment_point(i_pos)
            mods[ix] = center_bound_zmatrix(len(v))

        new_zm = reindex_zmatrix(
            functionalized_zmatrix(
                zm,
                mods
            ),
            reindexing
        )

        if max_iterations is None or max_iterations > 0:
            new_zm, new_new_bonds = add_missing_zmatrix_bonds(
                new_zm,
                bonds,
                max_iterations=max_iterations-1 if max_iterations is not None else max_iterations
            )

            new_bonds.update(new_new_bonds)

        return new_zm, new_bonds


def bond_graph_zmatrix(
        bonds,
        fragments,
        edge_map=None,
        reindex=True
):
    submats = []
    backbone = fragments[0]
    primary = chain_zmatrix(len(backbone))
    if edge_map is None:
        edge_map = EdgeGraph.get_edge_map(bonds)
    for frag in fragments[1:]:
        if nput.is_int(frag[0]):
            submats.append(
                chain_zmatrix(len(frag))
            )
        else:
            submats.append(
                bond_graph_zmatrix(
                    bonds,
                    frag,
                    edge_map=edge_map,
                    reindex=False
                )
            )


    attachment_points = []
    for frag in fragments[1:]:
        if not nput.is_int(frag[0]):
            frag = frag[0]

        for f in frag:
            attach = None
            submap = edge_map.get(f)
            if nput.is_int(submap):
                if submap in backbone:
                    attach = submap
            else:
                for s in submap:
                    if s in backbone:
                        attach = s
                        break

            if attach is not None:
                attachment_points.append(backbone.index(attach))
                break

        else:
            raise ValueError("can't attach fragment to backbone, no connections")

    fused = functionalized_zmatrix(
        len(primary),
        {
            _attachment_point(ap):zmat
            for ap,zmat in zip(attachment_points, submats)
        }
    )

    if reindex:
        flat_frags = list(itut.flatten(fragments))
        fused = reindex_zmatrix(fused, flat_frags)

    return fused

def sort_complex_attachment_points(
        fragment_inds,
        attachment_points: 'dict|tuple[tuple[int], list[list[int]]]'
):
    new_attachments = [None] * len(fragment_inds)
    fragment_inds = list(fragment_inds)
    if hasattr(attachment_points, 'items'):
        attachment_points = attachment_points.items()
    for start, end in attachment_points:
        if nput.is_int(start):
            start = [start]
        if nput.is_int(end):
            end = [end]

        start_frag = None
        for i, f in enumerate(fragment_inds):
            if start[0] in f:
                start_frag = i
                break
        else:
            raise ValueError(f"index {start[0]} not in fragments {fragment_inds}")

        end_frag = None
        for i, f in enumerate(fragment_inds):
            if end[0] in f:
                end_frag = i
                break
        else:
            raise ValueError(f"index {start[0]} not in fragments {fragment_inds}")

        if end_frag < start_frag:
            start, end = end, start
            start_frag, end_frag = end_frag, start_frag
        elif end_frag == start_frag:
            raise ValueError(f"root index {start[0]} and end index {end[0]} in same fragment")

        fragment_inds[start_frag] = tuple(sorted(
            fragment_inds[start_frag],
            key=lambda i: start.index(i) if i in start else len(start)
        ))
        fragment_inds[end_frag] = tuple(sorted(
            fragment_inds[end_frag],
            key=lambda i: end.index(i) if i in end else len(end)
        ))

        new_attachments[end_frag] = start

    return fragment_inds, new_attachments

def complex_zmatrix(
        bonds,
        fragment_inds=None,
        fragment_zmats=None,
        distance_matrix=None,
        attachment_points=None,
        check_attachment_points=True,
        graph=None,
        reindex=True
):

    if fragment_inds is None:
        if fragment_zmats is not None:
            raise ValueError("can't supply just Z-mats, unclear which fragments they come from...")
        all_inds = np.unique(np.concatenate(bonds))
        if graph is None:
            graph = EdgeGraph(all_inds, bonds)

        fragment_inds = graph.get_fragments()

    all_inds = np.concatenate(fragment_inds)
    if graph is None:
        graph = EdgeGraph(all_inds, bonds)

    if fragment_zmats is None:
        if isinstance(attachment_points, dict):
            fragment_inds, attachment_points = sort_complex_attachment_points(
                fragment_inds,
                attachment_points
            )

        fragment_zmats = [
            bond_graph_zmatrix(bonds, f, edge_map=graph.map)
            for f in fragment_inds
        ]
    elif isinstance(attachment_points, dict) and check_attachment_points:
        raise ValueError("can't supply Z-mats and dict of attachment points, can't be sure attachments are right")

    inds = np.asanyarray(fragment_inds[0])
    zm = fragment_zmats[0]
    if attachment_points is None:
        attachment_points = [None] * len(fragment_inds)
    if len(attachment_points) < len(fragment_inds):
        raise ValueError("too few attachment points specified")
    for inds_2, zm_2, root in zip(fragment_inds[1:], fragment_zmats[1:], attachment_points[1:]):
        if root is None:
            if distance_matrix is None:
                subgraph = graph.take(inds)
                root = subgraph.get_centroid(check_fragments=False)
            else:
                distance_matrix = np.asanyarray(distance_matrix)
                dm = distance_matrix[np.ix_(inds, inds_2)]
                min_cols = np.argmin(dm, axis=1)
                min_row = np.argmin(dm[np.arange(len(inds)), min_cols], axis=0)
                root = inds[min_row]
                # root = np.where(inds == min_row)[0][0]
        else:
            if nput.is_int(root):
                root = np.where(inds == root)[0][0]
            else:
                root = [np.where(inds == r)[0][0] for r in root]

        inds = np.concatenate([inds, inds_2])
        zm = functionalized_zmatrix(
            zm,
            {
                _attachment_point(root): zm_2
            }
        )

    if reindex:
        zm = reindex_zmatrix(zm, inds)

    return zm
