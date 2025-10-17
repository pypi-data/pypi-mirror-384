import collections

import numpy as np
import scipy
from .. import Numputils as nput
from .. import Coordinerds as coordops
from .. import Iterators as itut
from .Elements import *
from .PointGroups import PointGroup
from .SymmetryIdentifier import PointGroupIdentifier


__all__ = [
    "symmetrize_structure",
    "symmetrized_coordinate_coefficients",
    "get_internal_permutation_symmetry_matrices",
    "symmetrize_internals"
]

def _symmetry_reduce(coords, op:np.ndarray, labels=None):
    perm = nput.symmetry_permutation(coords, op)
    cycles = nput.permutation_cycles(perm, return_groups=True)
    coords = np.array([
        coords[p[0]]
        for p in cycles
    ])
    if labels is not None:
        labels = [
            labels[p[0]]
            for p in cycles
        ]
        return coords, labels
    else:
        return coords

def prep_symmetry_operations(symmetry_elements: 'PointGroup|list[SymmetryElement|np.ndarray]'):
    if isinstance(symmetry_elements, PointGroup):
        symmetry_elements = symmetry_elements.elements
    return [
        e.get_transformation()
            if isinstance(e, SymmetryElement) else
        np.asanyarray(e)
        for e in symmetry_elements
    ]

# def apply_symmetry_elements(coords, symmetry_elements: 'PointGroup|list[SymmetryElement|np.ndarray]', labels=None, tol=1e-1):
#     coords = np.asanyarray(coords)
#     symmetry_elements = prep_symmetry_operations(symmetry_elements)
#
#     for e in symmetry_elements:
#         new_coords = coords @ e
#         coord_diffs = np.linalg.norm(coords[:, np.newaxis, :] - new_coords[np.newaxis, :, :], axis=-1)
#         dupe_pos = np.where(coord_diffs < tol)
#         new_labs = None
#         if len(dupe_pos) > 0 and len(dupe_pos[0]) > 0:
#             rem = np.setdiff1d(np.arange(len(new_coords)), dupe_pos[0])
#             if labels is not None:
#                 new_labs = [labels[l] for l in rem]
#             new_coords = new_coords[rem,]
#         elif labels is not None:
#             new_labs = labels
#         if labels is not None:
#             labels = labels + new_labs
#         coords = np.concatenate([coords, new_coords], axis=0)
#
#     if labels is not None:
#         return coords, labels
#     else:
#         return coords

def symmetrize_structure(coords,
                         symmetry_elements: 'PointGroup|list[SymmetryElement|np.ndarray]',
                         labels=None,
                         masses=None,
                         groups=None,
                         tol=1e-1,
                         mass_tol=1,
                         expand=True
                         ):
    coords = np.asanyarray(coords)
    if groups is None:
        if labels is not None:
            label_map = {}
            g_vec = []
            for l in labels:
                label_map[l] = label_map.get(l, len(label_map))
                g_vec.append(l)
            (_, groups), _ = nput.group_by(np.arange(len(g_vec)), g_vec)
        elif masses is not None:
            (_, groups), _ = nput.group_by(np.arange(len(masses)), np.round(masses/mass_tol))
        else:
            groups = [np.arange(len(coords))]
    symmetry_elements = prep_symmetry_operations(symmetry_elements)

    all_coords = []
    all_labels = [] if labels is not None else None
    for g in groups:
        subcoords = coords[g,]
        if labels is not None:
            sublabels = [labels[gg] for gg in g]
        else:
            sublabels = None
        for e in symmetry_elements:
            subcoords = _symmetry_reduce(subcoords, e, labels=sublabels)
            if sublabels is not None:
                subcoords, sublabels = subcoords
        if expand:
            subcoords = nput.apply_symmetries(subcoords,
                                              prep_symmetry_operations(symmetry_elements),
                                              labels=sublabels,
                                              tol=tol)
            if sublabels is not None:
                subcoords, sublabels = subcoords
        if all_labels is not None:
            all_labels.append(sublabels)
        all_coords.append(subcoords)

    all_coords = np.concatenate(all_coords)
    all_labels = sum(all_labels, [])
    if labels is not None:
        return all_coords, all_labels
    else:
        return all_coords


def symmetrized_coordinate_coefficients(point_group,
                                        coords,
                                        masses=None,
                                        permutation_basis=None,
                                        as_characters=True,
                                        normalize=False,
                                        perms=None,
                                        ops=None,
                                        return_basis=None,
                                        merge_equivalents=None,
                                        drop_empty_modes=None,
                                        realign=True,
                                        permutation_tol=1e-2,
                                        **pg_tols
                                        ):

    if perms is None:
        if ops is None:
            if isinstance(point_group, str):
                point_group = PointGroup.from_name(point_group)
            elif isinstance(point_group, (list, tuple)) and isinstance(point_group[0], str):
                point_group = PointGroup.from_name(*point_group)

            id = PointGroupIdentifier(coords, masses, **pg_tols)
            if hasattr(point_group, "character_table"):
                if realign:
                    point_group = id.embed_point_group(point_group)
                ops = point_group.get_matrices(only_class_representatives=False)
                class_perm = np.concatenate(point_group.character_table.classes, axis=0)
            elif hasattr(point_group, 'get_full_matrices'):
                ops = point_group.get_full_matrices()
                if realign:
                    elems = [
                        SymmetryElement.from_transformation_matrix(x)
                        for x in point_group.matrices
                    ]
                    axes = id.find_point_group_alignment_axes(elems)
                    base_axes = PointGroup.get_axes_from_symmetry_elements(elems)
                    tf = axes.T @ base_axes
                    ops = tf[np.newaxis] @ ops @ tf.T[np.newaxis]
                class_perm = np.concatenate(point_group.classes, axis=0)
            else:
                ops = point_group
                class_perm = np.arange(len(point_group))

            ops = ops[class_perm,]

        # TODO: find a cleaner way to do this...
        perms = np.array([
            nput.symmetry_permutation(coords, m, tol=permutation_tol)
            for m in ops
        ])

    if permutation_basis is None:
        full_modes = np.zeros((3 * perms.shape[1],) + coords.shape + (len(ops),))

        inv = np.argsort(perms, axis=1)
        for n, (p, m) in enumerate(zip(inv, ops)):
            for i, j in enumerate(p):
                full_modes[3 * i:(3 * i + 3), j, :, n] = m
        full_basis = None
    else:
        full_modes, full_basis = permutation_basis(perms)

    equivalent_coords = None
    if merge_equivalents is None:
        merge_equivalents = as_characters
    if merge_equivalents is True:
        mask = np.moveaxis(np.abs(full_modes) > 1e-6, -1, 0)
        graph = mask[0]
        for m in mask:
            graph = np.logical_or(graph, m)  # TODO: speed this up with better masks

        _, comps = scipy.sparse.csgraph.connected_components(graph.reshape(graph.shape[0], -1))
        (_, equivalent_coords) = nput.group_by(
            np.arange(len(graph)),
            comps
        )[0]

    if as_characters:
        ct = point_group
        if hasattr(ct, "character_table"):
            ct = point_group.character_table

        full_modes = np.tensordot(ct.extend_class_representation(ct.table), full_modes, axes=[-1, -1])
        if normalize:
            full_modes = nput.vec_normalize(
                full_modes.reshape(full_modes.shape[:2] + (-1,)),
                axis=-1
            ).reshape(full_modes.shape)

        if drop_empty_modes is None:
            drop_empty_modes = normalize

        if equivalent_coords is not None:
            full_modes = full_modes.reshape(full_modes.shape[:2] + (-1,))
            rep_dims = ct.table[:, 0].astype(int)

            new_modes = []
            for character_modes, character_dim in zip(full_modes, rep_dims):
                comp_bits = [x for c in equivalent_coords for x in c[:character_dim]]
                new_modes.append(character_modes[:, comp_bits])
            full_modes = new_modes

        if drop_empty_modes:
            where_pos = lambda m:np.where(np.linalg.norm(m, axis=0) > 1e-12)[0]
            full_modes = [
                modes[:, where_pos(modes)]
                for modes in full_modes
            ]
    else:
        full_modes = np.moveaxis(full_modes, -1, 0)
        if normalize:
            full_modes = nput.vec_normalize(
                full_modes.reshape(full_modes.shape[:2] + (-1,)),
                axis=-1
            ).reshape(full_modes.shape)

        if drop_empty_modes is None:
            drop_empty_modes = normalize

        if equivalent_coords is not None:
            comp_bits = [c[0] for c in equivalent_coords]
            full_modes = full_modes.reshape((full_modes.shape[0], full_modes.shape[-1], -1))
            full_modes = full_modes[:, :, comp_bits]

        if drop_empty_modes:
            where_pos = lambda modes:np.where(np.linalg.norm(modes, axis=0) > 1e-12)[0]
            full_modes = [
                modes[:, where_pos(modes)]
                for modes in full_modes
            ]

    if return_basis is None:
        return_basis = full_basis is not None

    if return_basis:
        return full_modes, full_basis
    else:
        return full_modes

def get_internal_permutation_symmetry_matrices(internals, permutations):
    map = {
        coordops.canonicalize_internal(i): n
        for n, i in enumerate(internals)
    }
    internals = list(map.keys())
    basis = []
    p_coords = internals
    while len(p_coords) > 0:
        new_coords = []
        for n,p in enumerate(permutations):
            if len(basis) < n+1:
                subbasis = [
                    [0] * len(internals)
                    for _ in range(len(internals))
                ]
                basis.append(subbasis) # take advantage of mutability
            else:
                subbasis = basis[n]
            new_ints = coordops.permute_internals(p_coords, p, canonicalize=True)
            for old,new in zip(p_coords, new_ints):
                j = map[old]
                if new == old:
                    subbasis[j][j] = 1
                elif (
                        len(new) == 4
                        and new[0] == old[0] and new[3] == old[3]
                        and new[1] == old[2] and new[2] == old[1]
                ):
                    subbasis[j][j] = 1
                else:
                    if len(old) < 4:
                        sign = 1
                    else:
                        sign = 1

                    if (i := map.get(new)) is None:
                        if len(new) == 4:
                            for o,k in map.items():
                                if (
                                        len(o) == 4
                                        and new[0] == o[0] and o[3] == o[3]
                                        and new[1] == o[2] and new[2] == o[1]
                                ):
                                    i = k
                                    # sign *= -1
                        if i is None:
                            for sb in basis:
                                sb.append([0] * (len(internals)))
                                for b in sb: b.append(0)
                            i = len(internals)
                            map[new] = i
                            internals.append(new)
                            new_coords.append(new)
                    subbasis[j][i] = sign
        p_coords = new_coords

    #TODO: handle newly add internals, we need their permutation symmetries too

    full_basis = []
    for subbasis in basis:
        if len(subbasis) < len(internals):
            subbasis.extend(
                [[0]*len(internals)]
                * (len(internals) - len(subbasis))
            )

        full_basis.append([
            s + [0]*(len(internals) - len(s))
            for s in subbasis
        ])

    return np.moveaxis(np.array(full_basis, dtype=int), 0, -1), internals

def symmetrize_internals(point_group,
                         internals,
                         cartesians=None,
                         *,
                         masses=None,
                         as_characters=True,
                         normalize=None,
                         perms=None,
                         return_expansions=False,
                         return_base_expansion=False,
                         ops=None,
                         atom_selection=None,
                         reduce_redundant_coordinates=None,
                         **etc
                         ):
    if cartesians is not None:
        cartesians = np.asanyarray(cartesians)
        if np.issubdtype(cartesians.dtype, np.integer):
            # we'll support permutations as Cartesians even if it feels like a bad idea
            # it's just so convenient...
            atom_list = coordops.coordinate_indices(internals)
            nats = len(atom_list)
            if cartesians.shape != (nats, 3):
                if nats == 3:
                    # we'll check to see if we have permutations...
                    test = np.sort(cartesians, axis=0)
                    if np.sum(np.abs(test - np.arange(nats)[:, np.newaxis])) < 1e-8:
                        perms, cartesians = cartesians, None
            elif cartesians.shape[-1] == nats:
                perms, cartesians = cartesians, None
        # if cartesians.shape ==
    if perms is None and cartesians is None:
        raise ValueError("either Cartesians or explicit set of atom permutations required")

    if normalize is None:
        normalize = return_expansions

    if reduce_redundant_coordinates is None:
        reduce_redundant_coordinates = return_expansions and normalize

    if return_expansions and cartesians is None:
        raise ValueError("Cartesians are required to return coordinate expansions")
    if reduce_redundant_coordinates and not return_expansions:
        raise ValueError("Expansions are required to generate redundant coordinates")

    base_carts = cartesians
    base_masses = masses
    if atom_selection is not None and cartesians is not None:
        internal_reindexing = np.argsort(np.concatenate([
            atom_selection,
            np.delete(np.arange(len(cartesians)), atom_selection)
        ]))
        cartesians = cartesians[atom_selection,]
        internals = coordops.permute_internals(internals, internal_reindexing)
        if masses is not None:
            masses = np.asanyarray(masses)[atom_selection,]
    else:
        internal_reindexing = None


    symm = lambda p: get_internal_permutation_symmetry_matrices(internals, p)
    coeffs, full_basis = symmetrized_coordinate_coefficients(
        point_group,
        cartesians,
        masses=masses,
        permutation_basis=symm,
        as_characters=as_characters,
        normalize=normalize,
        perms=perms,
        ops=ops,
        **etc
    )

    if internal_reindexing is not None:
        internal_reindexing = np.argsort(internal_reindexing)
        full_basis = coordops.permute_internals(full_basis, internal_reindexing)

    res = (coeffs, full_basis)
    if return_expansions:
        if return_expansions is True: return_expansions = 1
        normalized_coefficients = normalize is not False and (as_characters or normalize)
        expansions = symmetrized_internal_coordinate_expansions(
            coeffs,
            base_carts,
            full_basis,
            order=return_expansions,
            masses=base_masses,
            normalized_coefficients=normalized_coefficients,
            return_base_expansion=return_base_expansion,
            return_inverse=True
        )

        if isinstance(reduce_redundant_coordinates, dict):
            redundant_opts = reduce_redundant_coordinates
            reduce_redundant_coordinates = True
        else:
            redundant_opts = {}

        if reduce_redundant_coordinates:
            if return_base_expansion:
                expansions, base_expansions = expansions
            else:
                base_expansions = None
            all_exps = [e[0] for e in expansions]
            all_tfs = [np.concatenate(e, axis=-1) for e in itut.transpose(all_exps)]
            all_inv = [np.concatenate(e, axis=0) for e in itut.transpose([e[1] for e in expansions])]
            # all_coeffs = np.concatenate(coeffs, axis=-1)
            red_coeffs, red_exps = coordops.RedundantCoordinateGenerator.get_redundant_transformation(
                all_tfs[1:],
                masses=base_masses,
                **collections.ChainMap(redundant_opts, dict(relocalize=True))
            )
            red_inv = nput.inverse_internal_coordinate_tensors(
                red_exps,
                base_carts,
                masses=base_masses,
                remove_translation_rotation=True
            )
            red_exps = red_coeffs, (red_exps, red_inv)
            expansions = (red_exps, expansions)
            if base_expansions is not None:
                expansions = expansions + (base_expansions,)
        elif not return_base_expansion:
            expansions = (expansions,)

        res = res + expansions

    return res

def symmetrized_internal_coordinate_expansions(coeffs, cartesians, full_basis,
                                               order=1,
                                               masses=None,
                                               return_inverse=False,
                                               normalized_coefficients=True,
                                               return_base_expansion=False,
                                               ):

    exps = nput.internal_coordinate_tensors(cartesians, full_basis,
                                                return_inverse=return_inverse,
                                                masses=masses,
                                                order=order
                                                )

    if return_inverse:
        exp, inv = exps
        coeff_inv = [
            c.T
                if normalized_coefficients else
            np.linalg.pinv(c)
            for c in coeffs
        ]
        expansions = [
            (
                [np.dot(exp[0], c)] + nput.tensor_reexpand(exp[1:], [c]),
                nput.tensor_reexpand([ci], inv)
            )
            for c, ci in zip(coeffs, coeff_inv)
        ]
    else:
        exp = exps
        expansions = [
            [np.dot(exp[0], c)] + nput.tensor_reexpand(exp[1:], [c])
            for c in coeffs
        ]

    if return_base_expansion:
        return expansions, exps
    else:
        return expansions

    # return symm_coeffs, storage[1]

# def symmetry_projected_coordinates():
#     # get a relocalized delocalized coordinate set projected in the space of symmetric
#     # coordinates
#     ...
