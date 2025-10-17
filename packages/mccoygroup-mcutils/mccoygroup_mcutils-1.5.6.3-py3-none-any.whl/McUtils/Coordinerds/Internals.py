import collections
import itertools

import numpy as np
from .. import Devutils as dev
from .. import Numputils as nput

__all__ = [
    "canonicalize_internal",
    "is_coordinate_list_like",
    "is_valid_coordinate",
    "permute_internals",
    "find_internal",
    "coordinate_sign",
    "coordinate_indices",
    "get_internal_distance_conversion",
    "internal_distance_convert"
]

def canonicalize_internal(coord, return_sign=False):
    sign = 1
    if len(coord) == 2:
        i, j = coord
        if i == j: return None # faster to just do the cases
        if i > j:
            j, i = i, j
            sign = -1
        coord = (i, j)
    elif len(coord) == 3:
        i, j, k = coord
        if i == j or j == k or i == k: return None
        if i > k:
            i, j, k = k, j, i
            sign = -1
        coord = (i, j, k)
    elif len(coord) == 4:
        i, j, k, l = coord
        if (
                i == j or j == k or i == k
                or i == l or j == l or k == l
        ): return None
        if i > l:
            i, j, k, l = l, k, j, i
            sign = -1
        coord = (i, j, k, l)
    else:
        if len(np.unique(coord)) < len(coord): return None
        if coord[0] > coord[-1]:
            coord = tuple(reversed(coord))
            sign = -1
        else:
            coord = tuple(coord)
    if return_sign:
        return coord, sign
    else:
        return coord

def is_valid_coordinate(coord):
    return (
        len(coord) > 1 and len(coord) < 5
        and all(nput.is_int(c) for c in coord)
    )

def is_coordinate_list_like(clist):
    return dev.is_list_like(clist) and all(
        is_valid_coordinate(c) for c in clist
    )

class InternalsSet:
    def __init__(self, coord_specs:'list[tuple[int]]', prepped_data=None):
        self._specs = tuple(coord_specs) if coord_specs is not None else coord_specs
        if prepped_data is not None:
            self._indicator, self.coordinate_indices, self.ind_map, self.coord_map = prepped_data
        else:
            self._indicator, self.coordinate_indices, self.ind_map, self.coord_map = self.prep_coords(coord_specs)

    @property
    def specs(self):
        if self._specs is None:
            self._specs = tuple(self._create_coord_list(self._indicator, self.ind_map, self.coord_map))
        return self._specs

    IndicatorMap = collections.namedtuple("IndicatorMap", ['primary', 'child'])
    IndsMap = collections.namedtuple("IndsMap", ['dists', 'angles', 'diheds'])
    InternalsMap = collections.namedtuple("InternalsMap", ['dists', 'angles', 'diheds'])
    @classmethod
    def prep_coords(cls, coord_specs):
        dist_inds = []
        dists = []
        angle_inds = []
        angles = []
        dihed_inds = []
        diheds = []
        indicator = []
        subindicator = []
        atoms = {}

        for i,c in coord_specs:
            c = canonicalize_internal(c)
            atoms.update(c)
            if len(c) == 2:
                indicator.append(0)
                subindicator.append(len(dists))
                dist_inds.append(i)
                dists.append(c)
            elif len(c) == 2:
                indicator.append(1)
                angle_inds.append(i)
                subindicator.append(len(angles))
                angles.append(c)
            elif len(c) == 4:
                indicator.append(2)
                subindicator.append(len(diheds))
                dihed_inds.append(i)
                diheds.append(c)
            else:
                raise ValueError(f"don't know what to do with coord spec {c}")

        return (
            cls.IndicatorMap(np.array(indicator), np.array(subindicator)),
            tuple(sorted(atoms)),
            cls.IndsMap(np.array(dist_inds), np.array(angle_inds), np.array(dihed_inds)),
            cls.InternalsMap(np.array(dists), np.array(angles), np.array(diheds))
        )

    @classmethod
    def _map_dispatch(cls, map, coord):
        if nput.is_int(coord):
            if coord == 0:
                return map.dists
            elif coord == 1:
                return map.angles
            else:
                return map.diheds
        else:
            if len(coord) == 2:
                return map.dists
            elif len(coord) == 3:
                return map.dists
            elif len(coord) == 4:
                return map.diheds
            else:
                raise ValueError(f"don't know what to do with coord spec {coord}")

    def _coord_map_dispatch(self, coord):
        return self._map_dispatch(self.coord_map, coord)
    def _ind_map_dispatch(self, i):
        return self._map_dispatch(self.ind_map, i)
    def find(self, coord):
        return nput.find(self._coord_map_dispatch(coord), coord)

    @classmethod
    def get_coord_from_maps(cls, item, indicator:IndicatorMap, ind_map, coord_map):
        if nput.is_int(item):
            map = indicator.primary[item]
            subloc = indicator.child[item]
            c_map = cls._map_dispatch(coord_map, map)
            return c_map[subloc,]
        else:
            map = indicator.primary[item,]
            uinds = np.unique(map)
            if len(uinds) > 1:
                return [
                    cls.get_coord_from_maps(i, indicator, ind_map, coord_map)
                    for i in item
                ]
            else:
                subloc = indicator.child[item,]
                c_map = cls._map_dispatch(coord_map, uinds[0])
                return c_map[subloc,]

    def __getitem__(self, item):
        return self.get_coord_from_maps(item, self._indicator, self.ind_map, self.coord_map)

    @classmethod
    def _create_coord_list(cls, indicator, inds, vals:InternalsMap):
        #TODO: make this more efficient, just concat the sub
        map = np.argsort(indicator.child)
        full = vals.diheds.tolist() + vals.angles.tolist() + vals.diheds.tolist()
        return [ tuple(full[i]) for i in map ]
    def permute(self, perm, canonicalize=True):
        #TODO: handle padding this
        inv = np.argsort(perm)
        dists = self.coord_map.dists
        if len(dists) > 0:
            dists = inv[dists]
        angles = self.coord_map.angles
        if len(angles) > 0:
            angles = inv[angles]
        diheds = self.coord_map.diheds
        if len(diheds) > 0:
            diheds = inv[diheds]

        cls = type(self)
        int_map = self.InternalsMap(dists, angles, diheds)
        if canonicalize:
            return cls(self._create_coord_list(self._indicator, self.ind_map, int_map))
        else:
            return cls(None, prepped_data=[self._indicator, self.coordinate_indices, self.ind_map, int_map])

def find_internal(coords, coord):
    if isinstance(coords, InternalsSet):
        return coords.find(coord)
    else:
        try:
            idx = coords.index(coord)
        except IndexError:
            idx = None

        if idx is None:
            idx = coords.index(canonicalize_internal(coord))
        return idx

def permute_internals(coords, perm, canonicalize=True):
    if isinstance(coords, InternalsSet):
        return coords.permute(perm, canonicalize=canonicalize)
    else:
        return [
            canonicalize_internal([perm[c] if c < len(perm) else c for c in coord])
                if canonicalize else
            tuple(perm[c] if c < len(perm) else c for c in coord)
            for coord in coords
        ]

def coordinate_sign(old, new, canonicalize=True):
    if len(old) != len(new): return 0
    if len(old) == 2:
        i,j = old
        m,n = new
        if i == n:
            return int(j == m)
        elif i == m:
            return int(i == n)
        else:
            return 0
    elif len(old) == 3:
        i,j,k = old
        m,n,o = new
        if j != n:
            return 0
        elif i == m:
            return int(k == o)
        elif i == o:
            return int(k == m)
        else:
            return 0
    elif len(old) == 4:
        # all pairwise comparisons now too slow
        if canonicalize:
            old = canonicalize_internal(old)
            new = canonicalize_internal(new)

        i,j,k,l = old
        m,n,o,p = new

        if i != m or l != p:
            return 0
        elif j == n:
            return int(k == o)
        elif j == o:
            return -int(k == n)
        else:
            return 0
    else:
        raise ValueError(f"can't compare coordinates {old} and {new}")

def coordinate_indices(coords):
    if isinstance(coords, InternalsSet):
        return coords.coordinate_indices
    else:
        return tuple(sorted(
            {x for c in coords for x in c}
        ))

dm_conv_data = collections.namedtuple("dm_conv_data",
                                      ['input_indices', 'pregen_indices', 'conversion', 'mapped_pos'])
tri_conv = collections.namedtuple("tri_conv", ['type', 'coords', 'val'])
dihed_conv = collections.namedtuple("dihed_conv", ['type', 'coords'])
def _get_input_ind(dm_data):
    return (
        dm_data.input_indices[0]
            if dm_data.conversion is None else
        None
    )
def _get_pregen_ind(dm_data):
    return (
        None
            if dm_data.conversion is None else
        dm_data.mapped_pos
    )
def get_internal_distance_conversion_spec(internals, canonicalize=True):
    if isinstance(internals, InternalsSet):
        internals = internals.specs
    dists:dict[tuple[int,int], dm_conv_data] = {}
    # we do an initial pass to separate out dists, angles, and dihedrals
    # for checking
    angles:list[tuple[tuple[int,int,int], int]] = []
    dihedrals:list[tuple[tuple[int,int,int,int], int]] = []
    for n,coord in enumerate(internals):
        if canonicalize:
            coord = canonicalize_internal(coord)
            if coord is None: continue
        if len(coord) == 2:
            coord:tuple[int,int]
            dists[coord] = dm_conv_data([n], [None], None, len(dists))
        elif len(coord) == 3:
            coord:tuple[int,int,int]
            angles.append((coord, n))
        else:
            coord:tuple[int,int,int,int]
            dihedrals.append((coord, n))

    #TODO: add in multiple passes until we stop picking up new distances
    #TODO: prune out ssa rules...these are ambiguous
    for n,((i,j,k),m) in enumerate(angles):
        a = canonicalize_internal((i,j))
        b = canonicalize_internal((j,k))
        c = (i,k)
        if a in dists and b in dists:
            if c not in dists:
                C = (i,j,k)
                d1 = dists[a]
                d2 = dists[b]
                # sas triangle
                dists[c] = dm_conv_data(
                    (_get_input_ind(d1), m, _get_input_ind(d2)),
                    (_get_pregen_ind(d1), None, _get_pregen_ind(d2)),
                    tri_conv('sas', (a, C, b), 2),
                    len(dists)
                )
        # elif a in dists and c in dists:
        #     # ssa triangle, angle at `i`
        #     if b not in dists:
        #         C = (i,j,k)
        #         d1 = dists[c]
        #         d2 = dists[a]
        #         # sas triangle
        #         dists[b] = dm_conv_data(
        #             (_get_input_ind(d1), _get_input_ind(d2), m),
        #             (_get_pregen_ind(d1), _get_pregen_ind(d2), None),
        #             tri_conv('ssa', (c, a, C), 2),
        #             len(dists)
        #         )
        # elif b in dists and c in dists:
        #     # ssa triangle, angle at `k`
        #     if a not in dists:
        #         B = (i,j,k)
        #         d1 = dists[b]
        #         d2 = dists[c]
        #         # sas triangle
        #         dists[a] = dm_conv_data(
        #             (_get_input_ind(d1), _get_input_ind(d2), m),
        #             (_get_pregen_ind(d1), _get_pregen_ind(d2), None),
        #             tri_conv('ssa', (b, c, B), 2),
        #             len(dists)
        #         )
        else:
            # try to another angle triangle coordinates that can be converted back to sss form
            for (ii,jj,kk),m2 in angles[n+1:]:
                # all points must be shared
                if k == jj and (
                        i == ii and j == kk
                        or i == kk and j == ii
                ):
                    C = (i, j, k)
                    A = (i, k, j)
                    if a in dists: # (i,j)
                        # we have saa
                        d = dists[a]
                        if b not in dists:
                            dists[b] = dm_conv_data(
                                (_get_input_ind(d), m, m2),
                                (_get_pregen_ind(d), None, None),
                                tri_conv('saa', (a, C, A), 2),
                                len(dists)
                            )
                        if c not in dists:
                            dists[c] = dm_conv_data(
                                (_get_input_ind(d), m, m2),
                                (_get_pregen_ind(d), None, None),
                                tri_conv('saa', (a, C, A), 1),
                                len(dists)
                            )
                    elif b in dists: # (k, j)
                        d = dists[b]
                        if a not in dists:
                            dists[a] = dm_conv_data(
                                (m, _get_input_ind(d), m2),
                                (None, _get_pregen_ind(d), None),
                                tri_conv('asa', (C, b, A), 1),
                                len(dists)
                            )
                        if c not in dists:
                            dists[c] = dm_conv_data(
                                (m, _get_input_ind(d), m2),
                                (None, _get_pregen_ind(d), None),
                                tri_conv('asa', (C, b, A), 2),
                                len(dists)
                            )
                    elif c in dists: # (i, k)
                        d = dists[c]
                        if b not in dists:
                            dists[b] = dm_conv_data(
                                (_get_input_ind(d), m2, m),
                                (_get_pregen_ind(d), None, None),
                                tri_conv('saa', (c, A, C), 2),
                                len(dists)
                            )
                        if c not in dists:
                            dists[a] = dm_conv_data(
                                (_get_input_ind(d), m2, m),
                                (_get_pregen_ind(d), None, None),
                                tri_conv('saa', (c, A, C), 1),
                                len(dists)
                            )
                elif i == jj and (
                        k == ii and j == kk
                        or k == kk and j == ii
                ):
                    C = (i, j, k)
                    B = (j, i, k)
                    if a in dists: # (i,j)
                        d = dists[a]
                        if b not in dists:
                            dists[b] = dm_conv_data(
                                (m, _get_input_ind(d), m2),
                                (None, _get_pregen_ind(d), None),
                                tri_conv('asa', (C, a, B), 1),
                                len(dists)
                            )
                        if c not in dists:
                            dists[c] = dm_conv_data(
                                (m, _get_input_ind(d), m2),
                                (None, _get_pregen_ind(d), None),
                                tri_conv('asa', (C, a, B), 2),
                                len(dists)
                            )
                    elif b in dists: # (k, j)
                        d = dists[b]
                        if a not in dists:
                            dists[a] = dm_conv_data(
                                (_get_input_ind(d), m, m2),
                                (_get_pregen_ind(d), None, None),
                                tri_conv('saa', (b, C, B), 2),
                                len(dists)
                            )
                        if c not in dists:
                            dists[c] =  dm_conv_data(
                                (_get_input_ind(d), m, m2),
                                (_get_pregen_ind(d), None, None),
                                tri_conv('saa', (b, C, B), 1),
                                len(dists)
                            )
                    elif c in dists: # (i, k)
                        d = dists[c]
                        if a not in dists:
                            dists[a] = dm_conv_data(
                                (_get_input_ind(d), m2, m),
                                (_get_pregen_ind(d), None, None),
                                tri_conv('saa', (c, B, C), 2),
                                len(dists)
                            )
                        if b not in dists:
                            dists[b] = dm_conv_data(
                                (_get_input_ind(d), m2, m),
                                (_get_pregen_ind(d), None, None),
                                tri_conv('saa', (c, B, C), 1),
                                len(dists)
                            )
                # x = canonicalize_internal((ii, jj))
                # y = canonicalize_internal((jj, kk))
                # z = (ii, kk)
                # if x == a:
                #     ...

    angle_dict = dict(angles)
    for n,((i,j,k,l),m) in enumerate(dihedrals):
        d = canonicalize_internal((i,l))
        if d not in dists:
            a = canonicalize_internal((i,j))
            b = canonicalize_internal((j,k))
            c = canonicalize_internal((k,l))
            x = canonicalize_internal((i,k))
            y = canonicalize_internal((j,l))
            if (
                    a in dists
                    and b in dists
                    and c in dists
            ):
                A = canonicalize_internal((i,j,k))
                B = canonicalize_internal((j,k,l))
                if A in angle_dict:
                    if B in angle_dict:
                        d1 = dists[a]
                        d2 = dists[b]
                        d3 = dists[c]
                        m1 = angle_dict[A]
                        m2 = angle_dict[B]
                        dists[d] = dm_conv_data(
                            (_get_input_ind(d1), _get_input_ind(d2), _get_input_ind(d3), m1, m2, m),
                            (_get_pregen_ind(d1), _get_pregen_ind(d2), _get_pregen_ind(d3), None, None, None),
                            dihed_conv('sssaat', (a, b, c, A, B, (i,j,k,l))),
                            len(dists)
                        )
                    elif y in dists:
                        d1 = dists[c]
                        d2 = dists[b]
                        d3 = dists[a]
                        d4 = dists[y]
                        m1 = angle_dict[A]
                        dists[d] = dm_conv_data(
                            (_get_input_ind(d1), _get_input_ind(d2), _get_input_ind(d3), _get_input_ind(d4), m1, m),
                            (_get_pregen_ind(d1), _get_pregen_ind(d2), _get_pregen_ind(d3), _get_pregen_ind(d4), None, None, None),
                            dihed_conv('ssssat', (c, b, a, y, A, (i,j,k,l))),
                            len(dists)
                        )
                elif B in angle_dict:
                    if x in dists:
                        d1 = dists[a]
                        d2 = dists[b]
                        d3 = dists[c]
                        d4 = dists[x]
                        m1 = angle_dict[B]
                        dists[d] = dm_conv_data(
                            (_get_input_ind(d1), _get_input_ind(d2), _get_input_ind(d3), _get_input_ind(d4), m1, m),
                            (_get_pregen_ind(d1), _get_pregen_ind(d2), _get_pregen_ind(d3), _get_pregen_ind(d4), None, None),
                            dihed_conv('ssssat', (a, b, c, x, B, (i,j,k,l))),
                            len(dists)
                        )
                elif x in dists and y in dists:
                    d1 = dists[a]
                    d2 = dists[b]
                    d3 = dists[c]
                    d4 = dists[x]
                    d5 = dists[y]
                    dists[d] = dm_conv_data(
                        (_get_input_ind(d1), _get_input_ind(d2), _get_input_ind(d3), _get_input_ind(d4), _get_input_ind(d5), m),
                        (_get_pregen_ind(d1), _get_pregen_ind(d2), _get_pregen_ind(d3), _get_pregen_ind(d4), _get_pregen_ind(d5), None,
                         None),
                        dihed_conv('ssssst', (a, b, c, x, y, (i, j, k, l))),
                        len(dists)
                    )


    return dists

def _prep_interal_distance_conversion(conversion_spec:dm_conv_data):
    if conversion_spec.conversion is None:
        def convert(internal_values, _, n=conversion_spec.input_indices[0]):
            return internal_values[..., n]
    elif hasattr(conversion_spec.conversion, 'val'):
        # a triangle to convert
        #TODO: allow triangle conversions to share context
        conversion:tri_conv = conversion_spec.conversion
        triangle_converter = nput.triangle_converter(conversion.type, 'sss')
        val = conversion.val
        int_args = conversion_spec.input_indices
        dist_args = conversion_spec.pregen_indices
        def convert(internal_values, distance_values,
                    int_args=int_args,
                    dist_args=dist_args,
                    converter=triangle_converter,
                    val=val):
            args = [
                internal_values[..., n]
                    if n is not None else
                distance_values[..., m]
                for n,m in zip(int_args, dist_args)
            ]
            return converter(*args)[val]
    else:
        # a dihedral to convert
        conversion:dihed_conv = conversion_spec.conversion
        dist_converter = nput.dihedral_distance_converter(conversion.type)
        int_args = conversion_spec.input_indices
        dist_args = conversion_spec.pregen_indices
        def convert(internal_values, distance_values,
                    int_args=int_args,
                    dist_args=dist_args,
                    converter=dist_converter):
            args = [
                internal_values[..., n]
                    if n is not None else
                distance_values[..., m]
                for n,m in zip(int_args, dist_args)
            ]
            return converter(*args)
    return convert
def get_internal_distance_conversion(internals, canonicalize=True, shift_dihedrals=True, abs_dihedrals=True):
    base_conv = get_internal_distance_conversion_spec(internals, canonicalize=canonicalize)
    final_inds = list(sorted(base_conv.keys(), key=lambda k:base_conv[k].mapped_pos))
    rordered_conversion = list(sorted(base_conv.values(), key=lambda v:v.mapped_pos))
    convs = [
        _prep_interal_distance_conversion(v) for v in rordered_conversion
    ]
    dihedral_pos = [i for i,v in enumerate(internals) if len(v) == 4]
    def convert(internal_values,
                inds=final_inds, convs=convs,
                dihedral_pos=dihedral_pos,
                shift_dihedrals=shift_dihedrals):
        internal_values = np.asanyarray(internal_values)
        if shift_dihedrals:
            internal_values = internal_values.copy()
            # force to be positive, push back onto appro
            internal_values[..., dihedral_pos] = np.pi - np.abs(internal_values[..., dihedral_pos])
        elif abs_dihedrals:
            internal_values = internal_values.copy()
            # force to be positive, push back onto appro
            internal_values[..., dihedral_pos] = np.abs(internal_values[..., dihedral_pos])
        dists = np.zeros(internal_values.shape[:-1] + (len(convs),))
        for n,c in enumerate(convs):
            dists[..., n] = c(internal_values, dists)

        return dists

    return final_inds, convert
def _check_complete_distances(final_dists):
    ds = set(final_dists)
    final_dists = list(final_dists)
    inds = np.unique([x for y in final_dists for x in y])
    targs = list(itertools.combinations(inds, 2))
    missing = []
    ord = []
    for i,j in targs:
        if (i,j) in ds:
            ord.append(final_dists.index((i,j)))
        elif (j,i) in ds:
            ord.append(final_dists.index((j,i)))
        else:
            missing.append((i,j))

    if len(missing) > 0:
        raise ValueError(f"distance set missing: {missing}")

    return ord
def internal_distance_convert(coords, specs,
                              canonicalize=True,
                              shift_dihedrals=True,
                              abs_dihedrals=True,
                              check_distance_spec=True):
    final_dists, converter = get_internal_distance_conversion(specs,
                                                              canonicalize=canonicalize,
                                                              shift_dihedrals=shift_dihedrals,
                                                              abs_dihedrals=abs_dihedrals
                                                              )
    if check_distance_spec:
        ord = _check_complete_distances(final_dists)
    else:
        ord = None
    conv = converter(coords)
    if ord is not None:
        conv = conv[..., ord]
        final_dists = [final_dists[i] for i in ord]
    return final_dists, conv