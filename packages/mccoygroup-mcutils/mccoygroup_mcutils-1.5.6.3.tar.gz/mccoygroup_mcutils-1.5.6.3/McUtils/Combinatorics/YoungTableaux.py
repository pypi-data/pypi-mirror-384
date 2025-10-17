
import numpy as np
import itertools

from .. import Numputils as nput
from .. import Iterators as itut
from .Permutations import UniquePermutations, UniqueSubsets, IntegerPartitioner, IntegerPartitioner2D, lehmer_encode

__all__ = [
    "YoungTableauxGenerator"
]

class YoungTableauxGenerator:
    #TODO: save these to data file for future use

    tableaxu_cache = {}
    subset_cache = {}
    def __init__(self, base_int, tableaxu_cache=None, subset_cache=None):
        self.base = base_int
        if tableaxu_cache is None:
            tableaxu_cache = self.tableaxu_cache
        self.cache = tableaxu_cache
        if subset_cache is None:
            subset_cache = self.subset_cache
        self.subset_cache = subset_cache

    def number_of_tableaux(self, partitions=None, **partition_opts):
        if partitions is None:
            partitions = IntegerPartitioner.partitions(self.base, **partition_opts)

        smol = nput.is_numeric(partitions[0])
        if smol:
            partitions = [partitions]

        if not nput.is_numeric(partitions[0][0]):
            partitions = itertools.chain(*partitions)
        else:
            partitions = partitions
        return sum(self.count_standard_tableaux(p) for p in partitions)
    def get_standard_tableaux(self, partitions=None, *, symbols=None,  brute_force=False,
                              return_partitions=False,
                              **partition_opts):
        if partitions is None:
            partitions = IntegerPartitioner.partitions(self.base, **partition_opts)

        smol = nput.is_numeric(partitions[0])
        if smol:
            partitions = [partitions]

        if not nput.is_numeric(partitions[0][0]):
            part_iter = itertools.chain(*partitions)
            if return_partitions:
                partitions = list(part_iter)
                part_iter = partitions
        else:
            part_iter = partitions

        tabs = [
            self.standard_partition_tableaux(partition,
                                             cache=self.cache,
                                             subset_cache=self.subset_cache,
                                             brute_force=brute_force, symbols=symbols)
            for partition in part_iter
        ]
        if smol:
            tabs = tabs[0]

        if return_partitions:
            if smol:
                partitions = partitions[0]
            return tabs, partitions
        else:
            return tabs

    @classmethod
    def standard_partition_tableaux_bf(cls, partition, unique_perms=False, concatenate=False):
        if unique_perms:
            n = len(partition)
            perm_list = sum(([n - i] * k for i, k in enumerate(partition)), [])
            #
            perms = UniquePermutations(perm_list[1:]).permutations()
            perms = np.concatenate([
                np.full((len(perms), 1), n, dtype=perms.dtype),
                perms
            ], axis=1)
            idx_pos = np.argsort(np.argsort(-perms, axis=1))
        else:
            idx_pos = nput.permutation_indices(sum(partition), sum(partition))

        tableaux = np.array_split(idx_pos, np.cumsum(partition)[:-1], axis=1)
        valid = np.full(len(idx_pos), True)
        for i, t in enumerate(zip(*tableaux)):
            if any(len(tt) > 1 and (np.diff(tt) < 0).any() for tt in t):
                valid[i] = False
            if valid[i] and any(len(tt) > 1 and (np.diff(tt) < 0).any() for tt in itut.transpose(t)):
                valid[i] = False

        tableaux = [t[valid] for t in tableaux]
        if concatenate:
            tableaux = np.concatenate(tableaux, axis=1)

        # if return_perms:
        #     return perms[valid], tableaux
        # else:
        return tableaux

    @classmethod
    def populate_sst_frames(cls, partition, frame, segment_lists):
        frame_list = []
        for segments in segment_lists:
            splits = [0] * len(partition)
            subframe = [np.zeros(k, dtype=int) for k in partition]
            for s, r in zip(subframe, frame):
                k = 0
                for n, i in enumerate(r):
                    j = splits[n]
                    s[k:k + i] = segments[n][j:j + i]
                    splits[n] += i
                    k += i
            frame_list.append(subframe)
        return frame_list

    @classmethod
    def standard_partitions(cls, partition):
        #TODO: make this more efficient
        base_partitions = IntegerPartitioner2D.get_partitions(partition, partition)
        offsets = np.cumsum(base_partitions, axis=-1)
        valid = np.all(np.all(np.diff(offsets, axis=-2) <= 0, axis=-2), axis=-1)

        return [
            base_partitions[valid,],
            offsets[valid,],
        ]

    @classmethod
    def hook_numbers(cls, partition):
        return [
            (p - j) + sum(
                1 if pk >= (j+1) else 0
                for pk in partition[i + 1:]
            )
            for i, p in enumerate(partition)
            for j in range(p)
        ]

    @classmethod
    def count_standard_tableaux(cls, partition):
        nums = np.arange(1, np.sum(partition)+1)
        denoms = np.sort(cls.hook_numbers(partition))
        return np.round(np.prod(nums/denoms)).astype(int)

    @classmethod
    def split_frame(cls, partition, offsets):
        # `offsets` is just a vector of offset indices
        # we find the ways we need to split the partition
        frame_list = []
        mp = np.max(partition)
        partition = np.array(partition)
        offsets = np.array(offsets)
        for i in range(len(partition)):
            p = partition[i]
            if p == 0: continue
            o = offsets[i]
            frame_list.append([
                np.pad([p], [i, len(partition)-(i+1)]),
                np.pad([o], [i, len(partition)-(i+1)])
            ])
            # diffs = np.zeros_like(offsets)
            # diffs[i + 1:] = o - offsets[i + 1:]
            # col_offset = np.concatenate([np.full(i+1, o), offsets[i+1:]])
            # this_part = np.clip(partition - diffs, 0, mp)
            # frame_list.append([this_part, col_offset])
            # partition = np.min([partition, diffs], axis=0)
            # offsets[i+1:] += partition[i+1:]
        return frame_list

    @classmethod
    def _sst_2(cls, partition, cache=None, subset_cache=None, symbols=None):
        tableaux = None
        if len(partition) == 1:
            tableaux = [
                np.arange(partition[0], dtype=int)[np.newaxis]
            ]
        elif sum(partition) == 2:
            tableaux = [
                np.array([[0]], dtype=int),
                np.array([[1]], dtype=int)
            ]
        elif sum(partition) == 3:
            if partition[0] == 2:
                tableaux = [
                    np.array([[0, 1], [0, 2]], dtype=int),
                    np.array([[2], [1]], dtype=int)
                ]
            else:
                tableaux = [
                    np.array([[0]], dtype=int),
                    np.array([[1]], dtype=int),
                    np.array([[2]], dtype=int),
                ]
        if tableaux is not None:
            if symbols is not None:
                symbols = np.asanyarray(symbols)
                return [
                    symbols[tab]
                    for tab in tableaux
                ]

            return tableaux

        if cache is None:
            cache = {}
        if subset_cache is None:
            subset_cache = {}
        partition = tuple(partition)
        if partition in cache:
            tableaux = cache[partition]
            if symbols is not None:
                symbols = np.asanyarray(symbols)
                return [
                    symbols[tab]
                    for tab in tableaux
                ]

            return tableaux
        else:
            frames, offsets = cls.standard_partitions(partition)
            offsets[:, :, 1:] = offsets[:, :, :-1]
            offsets[:, :, 0] = 0

            if symbols is None:
                symbols = np.arange(np.sum(partition))
            segments = np.array_split(symbols, np.cumsum(partition)[:-1])

            # n_frames = 0
            tableaux_generators = []
            for f, o in zip(frames, offsets):
                # print("!", f, o)
                # nsubs = 1
                subframes = []
                for pp, oo, seg in zip(f.T, o.T, segments):
                    # print("|||", pp, oo, seg)
                    frame_splits = cls.split_frame(pp, oo)
                    # for p,o in frame_splits:
                    #     print(">", p)
                    partition_sizes = [
                        np.sum(p) for p, o in frame_splits
                    ]

                    tp_key = tuple(partition_sizes)
                    subsets = subset_cache.get(tp_key)
                    if subsets is None:
                        subsets = UniqueSubsets.unique_subsets(partition_sizes)
                        subset_cache[tp_key] = subsets

                    comb_splits = np.array_split(
                        subsets,
                        np.cumsum(partition_sizes)[:-1],
                        axis=1
                    )
                    # print(">><<>><<", partition_sizes)
                    # print(subsets)
                    subssts = []
                    for spl in zip(*comb_splits):
                        subrow = []
                        # print('...', spl)
                        for (p, o), ss in zip(frame_splits, spl):
                            if len(ss) == 0: continue
                            # print(":", seg[ss])
                            p_idx = [x for x, p0 in enumerate(p) if p0 > 0]
                            subsubssts = cls._sst_2([p[x] for x in p_idx], cache=cache, symbols=seg[ss])
                            reshaped_ssts = []
                            for ss in zip(*subsubssts):
                                p_full = [[]] * len(p)
                                for x, r in zip(p_idx, ss):
                                    p_full[x] = r
                                reshaped_ssts.append([o, p_full])
                            subrow.append(reshaped_ssts)
                        # subrow_joins = []
                        # for r in itertools.product(*subrow):
                        #     joins = [
                        #         np.concatenate([rr[1][i] for rr in r])
                        #         for i in range(len(r[0]))
                        #     ]
                        #     print(joins)
                        #     if all(np.all(j == np.sort(j)) for j in joins):
                        #         subrow_joins.append(r)
                        # subssts.append(subrow_joins)#
                        subssts.append(list(itertools.product(*subrow)))
                        # nsubs *= len(subssts[-1])

                    subframes.append(subssts)
                # n_frames += nsubs
                tableaux_generators.append(subframes)

            n_frames = sum(
                np.prod([
                    len(f)
                    for f in frame_list
                ])
                for subframes in tableaux_generators
                for frame_list in itertools.product(*subframes)
            )

            mask = np.full(n_frames, True)
            tableaux = [np.full((n_frames, p), -1, dtype=int) for p in partition]
            n = 0
            for subframes in tableaux_generators:
                for frame_list in itertools.product(*subframes):
                    for frame_choice in itertools.product(*frame_list):
                        for f in frame_choice:
                            for oo, p_sets in f:
                                if not mask[n]: break
                                for i, (o, ss) in enumerate(zip(oo, p_sets)):
                                    k = len(ss)
                                    if k > 0:
                                        for j in range(i):
                                            if np.any(tableaux[j][n, o:o + k] >= ss):
                                                mask[n] = False
                                                break
                                        if not mask[n]: break
                                        tableaux[i][n, o:o + k] = ss
                        n += 1

            tableaux = [
                t[mask, :]
                for t in tableaux
            ]

            mask = np.all([
                np.all(t > -1, axis=1)
                for t in tableaux
            ], axis=0)
            tableaux = [
                t[mask, :]
                for t in tableaux
            ]


            codes = lehmer_encode(np.concatenate(tableaux, axis=-1))
            _, mask = np.unique(codes, return_index=True)
            tableaux = [
                t[mask, :]
                for t in tableaux
            ]

            cache[partition] = tableaux

            return tableaux
    @classmethod
    def standard_partition_tableaux(cls, partition,
                                    cache=None,
                                    subset_cache=None,
                                    symbols=None, brute_force=False):
        if brute_force:
            tableaux = cls.standard_partition_tableaux_bf(partition, concatenate=False, unique_perms=False)
        else:
            tableaux = cls._sst_2(partition, cache=cache, subset_cache=subset_cache)
        if symbols is not None:
            symbols = np.asanyarray(symbols)
            tableaux = [
                symbols[tab]
                for tab in tableaux
            ]
        return tableaux

    @classmethod
    def print_tableaux(cls, tableaux):
        from ..Formatters import TableFormatter
        if isinstance(tableaux[0], np.ndarray):
            tableaux = [tableaux]
        for tabs in tableaux:
            for sst in zip(*tabs):
                tab = TableFormatter("").format(sst)
                print("-"*len(tab.split("\n")[0]))
                print(tab)