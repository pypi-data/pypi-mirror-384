import abc

import numpy as np
from .. import Devutils as dev
from .. import Numputils as nput

from .Internals import canonicalize_internal

__all__ = [
    "prune_internal_coordinates"
]



class InternalCoordinatePruner(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def prune_coordinates(self, coords, *args, **kwargs):
        ...

class UniqueInternalCoordinatePruner(InternalCoordinatePruner):
    def prune_coordinates(cls, coords):
        _coords = []
        _cache = set()
        for x in coords:
            x = canonicalize_internal(x)
            if x not in _cache:
                _coords.append(x)
                _cache.add(x)
        return coords

class EquivalentInternalCoordinatePruner(InternalCoordinatePruner):
    @classmethod
    def get_equivalent_stretch_coordinates(cls, i, j):
        return []

    @classmethod
    def get_equivalent_angle_coordinates(cls, i, j, k):
        return [
            [
                (i, k, j),
                (k, i, j)
            ]
        ]

    @classmethod
    def get_equivalent_dihedral_coordinates(cls, i, j, k, l):
        return [
            [
                (i, k, j, l)
            ]
        ]

    def get_equivalent_coordinates(self, coord):
        if len(coord) == 2:
            return self.get_equivalent_stretch_coordinates(*coord)
        elif len(coord) == 3:
            return self.get_equivalent_angle_coordinates(*coord)
        elif len(coord) == 4:
            return self.get_equivalent_dihedral_coordinates(*coord)

    def prune_coordinates(self, coord_set, canonicalized=False):
        if not canonicalized:
            coord_set = [canonicalize_internal(c) for c in coord_set]
            coord_set = [c for c in coord_set if c is not None]
        dupe_set = set()
        coords = []
        for coord in coord_set:
            if coord in dupe_set: continue
            dupe_set.add(coord)
            dupe_sets = self.get_equivalent_coordinates(coord)
            if any(
                    all(canonicalize_internal(c) in dupe_set for c in dupes)
                    for dupes in dupe_sets
            ): continue
            coords.append(coord)

        return coords

class GeometricInternalCoordinatePruner(InternalCoordinatePruner):

    def prune_coordinates(cls,
                          coords, b_matrix,
                          max_coords=None,
                          small_value_cutoff=1e-8,
                          max_contrib_cutoff=5e-2,
                          return_positions=False
                          ):
        if not nput.is_numeric_array_like(b_matrix):
            b_matrix_generator = b_matrix
        else:
            b_matrix_generator = lambda pos, coords: b_matrix[:, pos]

        if max_coords is None:
            max_coords = b_matrix_generator([0], [coords[0]]).shape[0] - 1
        subspace = max_coords

        sub_b = b_matrix_generator(np.arange(subspace), coords[:subspace])
        _, s, Q = np.linalg.svd(sub_b)
        min_comp = np.min(s)
        while min_comp < small_value_cutoff:
            subspace = subspace - 1
            sub_b = sub_b[:, :-1]
            _, s, Q = np.linalg.svd(sub_b)
            min_comp = np.min(s)

        coord_pos = np.arange(subspace)
        rem_coords = np.setdiff1d(np.arange(len(coords)), coord_pos)
        for test_coord in rem_coords:
            b_vec = b_matrix_generator((test_coord,), [coords[test_coord]])
            b_test = np.concatenate([sub_b, b_vec], axis=1)
            min_comp = np.min(np.linalg.svd(b_test)[1])
            if min_comp > small_value_cutoff:
                coord_pos = np.concatenate([coord_pos, [test_coord]])
                if len(coord_pos) >= max_coords:
                    break
                sub_b = b_test

        coords = [coords[p] for p in coord_pos]
        if return_positions:
            return coord_pos, coords
        else:
            return coords


pruner_dispatch = dev.OptionsMethodDispatch(
    {
        'unique':InternalCoordinatePruner,
        'equivalent':EquivalentInternalCoordinatePruner,
        'b_matrix':GeometricInternalCoordinatePruner
    }
)


def prune_internal_coordinates(coords, *args, method='equivalent', **kwargs):
    pruner:'type[InternalCoordinatePruner]'
    pruner, subopts = pruner_dispatch.resolve(method)
    return pruner().prune_coordinates(coords, *args, **dict(subopts, **kwargs))