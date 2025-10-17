import numpy as np
import itertools
import collections
from .. import Numputils as nput
from ..Graphs import EdgeGraph

__all__ = [
    "get_stretch_angles",
    "get_angle_dihedrals",
    "get_angle_stretches",
    "get_dihedral_stretches",
    "get_stretch_angle_dihedrals",
    "get_stretch_coordinate_system",
    "PrimitiveCoordinatePicker"
]


def get_stretch_angles(stretches):
    angles = []
    for i,(sa,sb) in enumerate(stretches):
        for sc,sd in stretches[i+1:]:
            if sa == sc:
                if sb == sd: continue
                angles.append((sb, sa, sd))
            elif sa == sd:
                if sb == sc: continue
                angles.append((sb, sa, sc))
            elif sb == sc:
                angles.append((sa, sb, sd))
            elif sb == sd:
                angles.append((sa, sb, sc))
    return angles
def get_stretch_angle_dihedrals(stretches, angles):
    dihedrals = []
    for sa,sb in stretches:
        for ba,bc,bd in angles:
            if sa in (ba,bc,bd) and sb in (ba,bc,bd): continue
            # enumerate for simplicity & avoiding try/except
            if sa == ba:
                dihedrals.append(
                    (sb, ba, bc, bd)
                )
            elif sa == bc:
                dihedrals.append(
                    (ba, sb, bc, bd)
                )
            elif sa == bd:
                dihedrals.append(
                    (ba, bc, bd, sb)
                )
            elif sb == ba:
                dihedrals.append(
                    (sa, ba, bc, bd)
                )
            elif sb == bc:
                dihedrals.append(
                    (ba, sa, bc, bd)
                )
            elif sb == bd:
                dihedrals.append(
                    (ba, bc, bd, sa)
                )
    return dihedrals
def get_angle_stretches(angles):
    return [
        s
        for a,b,c in angles
        for s in [(a, b), (b, c)]
    ]
def get_dihedral_stretches(dihedrals):
    return [
        s
        for a,b,c,d in dihedrals
        for s in [(a, b), (b, c), (c,d)]
    ]
def get_angle_dihedrals(angles):
    dihedrals = []
    for i, (aa, ab, ac) in enumerate(angles):
        for ad, ae, af in angles[i + 1:]:
            if ae == ac:
                if ad == ab:
                    if af == aa: continue
                    dihedrals.append((aa, ab, ac, af))
                elif af == ab:
                    if ad == aa: continue
                    dihedrals.append((aa, ab, ac, ad))
            elif ae == aa:
                if ad == ab:
                    if af == ac: continue
                    dihedrals.append((af, aa, ab, ac))
                elif af == ab:
                    if ad == ac: continue
                    dihedrals.append((ad, aa, ab, ac))
    return dihedrals

def get_stretch_coordinate_system(stretches):
    angles = get_stretch_angles(stretches)
    dihedrals = get_angle_dihedrals(angles)
    return stretches,angles,dihedrals


class PrimitiveCoordinatePicker:

    light_atom_types = {"H", "D"}
    def __init__(self, atoms, bonds, base_coords=None, rings=None, fragments=None, light_atoms=None, backbone=None, neighbor_count=3):
        self.graph = EdgeGraph(atoms, bonds)
        if rings is None:
            rings = self.graph.get_rings()
        self.rings = rings
        self.ring_atoms = {k:n for n,rats in enumerate(rings) for k in rats}
        if fragments is None:
            fragments = self.graph.get_fragments()
        self.fragments = fragments
        self.backbone = backbone
        self.light_atoms = (
            [
                i for i, l in enumerate(self.graph.labels)
                if l in self.light_atom_types
            ]
                if light_atoms is None else
            light_atoms
        )
        self.base_coords = list(base_coords) if base_coords is not None else []
        self.neighbors = neighbor_count
        self._coords = None
    @property
    def coords(self):
        if self._coords is None:
            self._coords = tuple(self.generate_coords())
        return self._coords
    def generate_coords(self):
        coords = []
        for ring in self.rings:
            coords.extend(self.ring_coordinates(ring))
        for i,r1 in enumerate(self.rings):
            for r2 in self.rings[i+1:]:
                coords.extend(self.fused_ring_coordinates(r1, r2))
        for i,r1 in enumerate(self.fragments):
            for r2 in self.fragments[i+1:]:
                coords.extend(self.fragment_connection_coords(r1, r2))
        for a in range(len(self.graph.labels)):
            if a not in self.ring_atoms:
                symm_c = self.symmetry_coords(a, neighborhood=self.neighbors, backbone=self.backbone)
                coords.extend(symm_c)
        coords = self.base_coords + coords
        return self.prune_excess_coords(coords)

    @classmethod
    def canonicalize_coord(cls, coord):
        dupes = len(np.unique(coord)) < len(coord)
        if dupes: return None
        if len(coord) == 2:
            i,j = coord
            if i > j:
                coord = (j, i)
        elif len(coord) == 3:
            i,j,k = coord
            if i > k:
                coord = (k, j, i)
        elif len(coord) == 4:
            i, j, k, l = coord
            if i > l:
                coord = (l, k, j, i)
        elif coord[0] > coord[-1]:
            coord = tuple(reversed(coord))
        return coord

    @classmethod
    def prep_unique_coords(cls, coords):
        _coords = []
        _cache = set()
        for x in coords:
            x = cls.canonicalize_coord(x)
            if x not in _cache:
                _coords.append(x)
                _cache.add(x)
        return coords

    @classmethod
    def prune_excess_coords(cls, coord_set, canonicalized=False):
        if not canonicalized:
            coord_set = [cls.canonicalize_coord(c) for c in coord_set]
            coord_set = [c for c in coord_set if c is not None]
        dupe_set = set()
        coords = []
        coord_counts = {}
        for coord in coord_set:
            if coord in dupe_set: continue
            dupe_set.add(coord)
            if len(coord) == 4:
                i,j,k,l = coord
                if (i, k, j, l) in dupe_set: continue
                # only one choice of ordering for shared bond, even though implies different exterior bonds
            elif len(coord) == 3:
                i,j,k = coord
                if ( # can't have all three angles, dealing with the ordering manually
                    (k < j and (i, k, j) in dupe_set and (k, i, j) in dupe_set)
                    or (k > j and (j, i, k) in dupe_set) and ((i, k, j) in dupe_set or (j, k, i) in dupe_set)
                ): continue
            coords.append(coord)
            # key = tuple(sorted(coord))
            # coord_counts[key] = coord_counts.get(key, 0) + 1
            # if len(coord_counts)

        return coords

    @classmethod
    def ring_coordinates(cls, ring_atoms):
        # ordered as pair-wise bonded

        bonds = list(zip(
            ring_atoms, ring_atoms[1:] + ring_atoms[:1]
        ))
        angles = list(zip(
            ring_atoms, ring_atoms[1:] + ring_atoms[:1], ring_atoms[2:] + ring_atoms[:2]
        ))
        dihedrals = list(zip(
            ring_atoms, ring_atoms[1:] + ring_atoms[:1],
                        ring_atoms[2:] + ring_atoms[:2],
                        ring_atoms[3:] + ring_atoms[:3],
        ))

        return bonds + angles + dihedrals

    fused_ring_dispatch_table = {

    }
    @classmethod
    def _fused_dispatch(cls):
        return dict({
            0:cls.unfused_ring_coordinates,
            1:cls.pivot_fused_ring_coordinates,
            2:cls.simple_fused_ring_coordinates
        }, **cls.fused_ring_dispatch_table)
    @classmethod
    def unfused_ring_coordinates(cls, ring_atoms1, ring_atoms2, shared_atoms, shared_indices1, shared_indices2):
        return []
    @classmethod
    def pivot_fused_ring_coordinates(cls, ring_atoms1, ring_atoms2, shared_atoms, shared_indices1, shared_indices2):
        p = shared_atoms[0]
        i = shared_indices1[0]
        n = len(ring_atoms1)
        j = shared_indices2[0]
        m = len(ring_atoms2)

        # add in all relative angles
        ip1 = (i+1) % n
        jp1 = (j+1) % m
        return [
            (ring_atoms1[i-1], p, ring_atoms2[j-1]),
            (ring_atoms1[ip1], p, ring_atoms2[j-1]),
            (ring_atoms1[i-1], p, ring_atoms2[jp1]),
            (ring_atoms1[ip1], p, ring_atoms2[jp1])
        ]

    @classmethod
    def simple_fused_ring_coordinates(cls, ring_atoms1, ring_atoms2, shared_atoms, shared_indices1, shared_indices2):
        j, k = shared_atoms
        j1, k1 = shared_indices1
        j2, k2 = shared_indices2
        # we want relative orientation indices for both rings
        inds = []
        if j1 > k1:
            j1, k1 = k1, j1
        if j2 > k2:
            j2, k2 = k2, j2
        i1 = ring_atoms1[j1 - 1]; l1 = ring_atoms1[(k1 + 1) % len(ring_atoms1)]
        i2 = ring_atoms2[j2 - 1]; l2 = ring_atoms2[(k2 + 1) % len(ring_atoms2)]

        return [
            (i1, j, k, l2),
            (i2, j, k, l1)
        ]

    @classmethod
    def fused_ring_coordinates(cls, ring_atoms1, ring_atoms2):
        shared_atoms, _, _, r1_indices, r2_indices = nput.intersection(ring_atoms1, ring_atoms2, return_indices=True)
        if len(shared_atoms) == 0:
            return []
        else:
            n = len(shared_atoms)
            coord_func = cls._fused_dispatch().get(n)
            if coord_func is None:
                raise ValueError(f"can't deal with fused rings with {n} shared atoms")
            return coord_func(ring_atoms1, ring_atoms2, shared_atoms, r1_indices, r2_indices)

    def fragment_connection_coords(self, frag_1, frag_2):
        heavy_frag1 = set(frag_1) - set(self.light_atoms)
        if len(heavy_frag1) > 2:
            frag_1 = list(sorted(heavy_frag1))
        heavy_frag2 = set(frag_2) - set(self.light_atoms)
        if len(heavy_frag2) > 2:
            frag_2 = list(sorted(heavy_frag2))

        coords = []
        coords.append((frag_1[0], frag_2[0]))
        if len(frag_2) > 1:
            coords.append((frag_1[0], frag_2[0], frag_2[1]))
        if len(frag_1) > 1:
            coords.append((frag_1[1], frag_1[0], frag_2[0]))
        if len(frag_2) > 1 and len(frag_1) > 1:
            coords.append((frag_1[1], frag_1[0], frag_2[0], frag_2[1]))
        if len(frag_1) > 2:
            coords.append((frag_1[2], frag_1[1], frag_1[0], frag_2[0]))
        if len(frag_2) > 2:
            coords.append((frag_1[0], frag_2[0], frag_2[1], frag_2[2]))

        return coords

    def get_neighborhood_symmetries(self, atoms, ignored=None, neighborhood=3):
        graphs = [
            self.graph.neighbor_graph(a, ignored=ignored, num=neighborhood)
            for a in atoms
        ]
        rows, cols = np.triu_indices(len(graphs), k=1)
        return [graphs[r] == graphs[c] for r,c in zip(rows, cols)]

    def chain_coords(self, R, y):
        coords = []
        if len(R) > 0:
            coords.append((y, R[-1]))
        if len(R) > 1:
            coords.append((y, R[-1], R[-2]))
        if len(R) > 2:
            coords.append((y, R[-1], R[-2], R[-3]))
        return coords

    def RYX2_coords(self, R, y, X):
        coords = []
        coords.extend((y, x) for x in X)
        coords.extend(
            (X[i], y, X[j])
            for i, j in itertools.combinations(range(3), 2)
        )
        if len(R) > 0:
            coords.append((R[-1], y))
            # add in RYX angles
            coords.extend(
                (R[-1], y, x)
                for x in X
            )
        if len(R) > 1:
            # add in RRY angle
            coords.append(
                (R[-2], R[-1], y)
            )
        if len(R) > 2:
            # add in RRRY dihedral
            coords.append(
                (R[-3], R[-2], R[-1], y)
            )

        return coords

    def RYX3_coords(self, R, y, X):
        coords = []
        coords.extend((y, x) for x in X)
        coords.extend(
            (X[i], y, X[j])
            for i, j in itertools.combinations(range(3), 2)
        )
        if len(R) > 0:
            coords.append((R[-1], y))
            # add in RYX angles
            coords.extend(
                (R[-1], y, x) for x in X
            )
        if len(R) > 1:
            # add in RRY angle
            coords.append(
                (R[-2], R[-1], y)
            )
        if len(R) > 2:
            # add in RRRY dihedral
            coords.append(
                (R[-3], R[-2], R[-1], y)
            )

        return coords

    def get_precedent_chains(self, atom, num_precs=2, ring_atoms=None, light_atoms=None, ignored=None, backbone=None):
        chains = []
        visited = set([] if ignored is None else ignored)
        ring_atoms = set(self.ring_atoms if ring_atoms is None else ring_atoms)
        light_atoms = set(self.light_atoms if light_atoms is None else light_atoms)
        if backbone is not None:
            backbone = set(backbone)

        visited = visited #| ring_atoms # | light_atoms

        # do a dfs exploration up to the given depth over non-ring, heavy atoms
        queue = collections.deque([[[], 0, atom]])
        while queue:
            chain, depth, root = queue.pop()
            neighbors = self.graph.map[root]
            visited.add(root)
            branches = neighbors - visited
            if len(branches) == 0:
                chains.append(chain)
            elif depth == num_precs - 1:
                chains.extend(chain + [n] for n in branches)
            else:
                queue.extend([chain + [n], depth+1, n] for n in branches)

            #
            # queue.extend(rem)
            # while len(rem) == 0 and queue:
            #     # walk up dfs tree until we find a branch with nodes that work
            #     root = queue.pop()
            #     if root not in visited:
            #         rem = {root}
            # else:
            #     if len(rem) == 0: rem = neighbors - visited - light_atoms
            #     # if len(rem) == 0: rem = neighbors - visited
            #     if len(rem) == 0: break
            #
            #     if backbone is not None:
            #         bb_chain = rem & backbone
            #     else:
            #         bb_chain = []
            #     if len(bb_chain) > 0:
            #         atom = min(bb_chain)
            #     else:
            #         atom = min(rem)
            #     chain.append(atom)

        # chain = list(reversed(chain))

        return [list(reversed(c)) for c in chains]

    symmetry_type_dispatch = {}
    def _symmetry_dispatch(self):
        return dict({
            (3,):self._3_coords,
            (2,1):self._2_1_coords,
            (3,1):self._3_1_coords
        })
    def _2_1_coords(self, atom, neighbors, X, R, backbone=None):
        coords = []
        R = R[0]
        chains = self.get_precedent_chains(R, 1, ignored=[atom] + neighbors, backbone=backbone)
        if len(chains) == 0: chains = [[]]
        for c in chains:
            coords.extend(self.RYX2_coords(c + [R], atom, X))
        return coords
    def _3_coords(self, atom, neighbors, X, backbone=None):
        return self.RYX3_coords([], atom, X)
    def _3_1_coords(self, atom, neighbors, X, R, backbone=None):
        coords = []
        R = R[0]
        chains = self.get_precedent_chains(R, 1, ignored=[atom] + neighbors, backbone=backbone)
        if len(chains) == 0: chains = [[]]
        for c in chains:
            coords.extend(self.RYX3_coords(c + [R], atom, X))
        return coords

    # def _2_2_coords(self, atom, neighbors, X, R, backbone=None):
    #     coords = []
    #     R = R[0]
    #     # chains = self.get_precedent_chains(R, 1, ignored=[atom] + neighbors, backbone=backbone)
    #     if len(chains) == 0: chains = [[]]
    #     for c in chains:
    #         coords.extend(self.R2YX2_coords(c + [R], atom, X))
    #     return coords


    @classmethod
    def get_symmetry_groups(cls, neighbors, matches):
        groups = {}
        n = len(neighbors)
        k = 0
        for i in range(n):
            if i not in groups:
                groups[i] = {i}
            for j in range(i+1, n):
                eq = matches[k]
                k += 1
                if eq:
                    groups[j] = groups[i]
                    groups[i].add(j)
        groups = {id(g):g for g in groups.values()}
        groups = list(reversed(sorted(groups.values(), key=lambda g:len(g))))
        return [
            [neighbors[i] for i in g]
            for g in groups
        ]

    def symmetry_coords(self, atom, neighborhood=3, backbone=None):
        # neighbors = list(self.graph.map[atom])
        coords = []
        # dispatch = self._symmetry_dispatch()
        # neighbor_counts = {sum(k) for k in dispatch.keys()}
        # if len(neighbors) in neighbor_counts:
        #     symms = self.get_neighborhood_symmetries(neighbors, ignored=[atom], neighborhood=neighborhood)
        #     groups = self.get_symmetry_groups(neighbors, symms)
        #     key = tuple(len(g) for g in groups)
        #     dfunc = dispatch.get(key)
        #     if dfunc is not None:
        #         coords = dfunc(atom, neighbors, *groups, backbone=backbone)
        chains = self.get_precedent_chains(atom, 3, backbone=backbone)
        if len(chains) == 0: chains = [[]]
        for R in chains:
            coords.extend(self.chain_coords(R, atom))

        # if coords is None:
        #     R = self.get_precedent_chain(atom, 3, backbone=backbone)
        #     coords = self.chain_coords(R, atom)

        return coords