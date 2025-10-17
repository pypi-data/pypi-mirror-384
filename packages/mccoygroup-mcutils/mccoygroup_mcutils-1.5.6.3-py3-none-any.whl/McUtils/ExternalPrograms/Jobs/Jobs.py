import abc
from ...Formatters import OptionalTemplate

__all__ = [
    "OptionsBlock",
    "ExternalProgramJob"
]

class JobBlockBase(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_template(self):
        ...
    @abc.abstractmethod
    def get_params(self):
        ...
    def format(self):
        params = {
            k:v.format() if hasattr(v, 'format') else v
            for k,v in self.get_params().items()
        }
        return OptionalTemplate(self.get_template(), **params).apply()

class JobBlock(JobBlockBase):
    template = None
    def __init__(self, **opts):
        self.opts = opts

    def get_template(self):
        return self.template

    def get_params(self):
        return {k:v.format() if hasattr(v, 'format') else v for k,v in self.opts.items()}

class OptionsBlock(JobBlock):
    __props__ = ()
    __aliases__ = {}
    def __init__(self, canonicalize_opts=True, **opts):
        if canonicalize_opts:
            opts = self.check_opts(opts)
        super().__init__(**opts)
    _canon_opts = None

    @classmethod
    def get_props(cls):
        return cls.__props__
    @classmethod
    def get_aliases(cls):
        return cls.__aliases__
    @classmethod
    def get_canonical_opts_map(cls):
        if cls._canon_opts is None:
            cls._canon_opts = {
                k.lower():k for k in cls.get_props()
            }
        return cls._canon_opts
    _check_props = None
    @classmethod
    def get_props_set(cls):
        if cls._check_props is None:
            cls._check_props = set(cls.get_props())
        return cls._check_props
    _inv_alias_map = None
    @classmethod
    def get_inverse_alias_map(cls):
        if cls._inv_alias_map is None:
            cls._inv_alias_map = {
                a.lower(): k
                for k, aliases in cls.get_aliases().items()
                for a in aliases
            }
        return cls._inv_alias_map

    require_value = None
    @classmethod
    def check_canon(cls, opt, val):

        if cls.require_value is not None:
            no_val = val is None or val is True
            if (
                    (no_val and cls.require_value)
                    or (not no_val and not cls.require_value)
            ):
                return False, opt

        opt = cls.canonicalize_opt_name(opt)
        return opt in cls.get_props_set(), opt


    @classmethod
    def canonicalize_opt_name(cls, opt):
        opt = cls.get_inverse_alias_map().get(opt.lower(), opt)
        opt = cls.get_canonical_opts_map().get(opt.lower(), opt)
        return opt
    def check_opts(self, opts):
        new_opts = {}
        dupe_opts = set()
        bad_opts = set()
        check_props = self.get_props_set()
        for k,v in opts.items():
            k = self.canonicalize_opt_name(k)
            if k not in check_props:
                bad_opts.add(k)
            elif k in new_opts:
                dupe_opts.add(k)
            else:
                new_opts[k] = v

        if len(bad_opts) > 0:
            raise ValueError(f"options {bad_opts} invalid for {type(self).__name__} (valid set: {check_props})")
        if len(bad_opts) > 0:
            raise ValueError(f"got two values for option {dupe_opts} after canonicalization")

        return new_opts

    @classmethod
    def prep_opts(cls, opts):
        if opts is True:
            opts = []
        if isinstance(opts, str):
            opts = [[opts], {}]
        elif hasattr(opts, 'items'):
            opts = [[], opts]
        elif not (len(opts) == 2 and hasattr(opts[1], 'items') and not hasattr(opts[0], 'items')):
            opts = [opts, {}]
        return opts


class SystemBlock(OptionsBlock):
    __props__ = ("charge", "multiplicity", "atoms", "cartesians", "zmatrix", "ordering", "internals", "bonds")

    @classmethod
    def fmt_carts(cls, atoms, carts, float_fmt="{:11.8f}"):
        max_at_len = max(len(a) for a in atoms)
        carts = [
            [float_fmt.format(x) if not isinstance(x, str) else x for x in xyz]
            for xyz in carts
        ]
        col_lens = [
            max([len(xyz[i]) for xyz in carts])
            for i in range(3)
        ]
        fmt_string = f"{{a:<{max_at_len}}} {{xyz[0]:>{col_lens[0]}}} {{xyz[1]:>{col_lens[1]}}} {{xyz[2]:>{col_lens[2]}}}"
        return "\n".join(
            fmt_string.format(
                a=a,
                xyz=xyz
            )
            for a, xyz in zip(atoms, carts)
        )

    @classmethod
    def fmt_zmat(cls, atoms, zmat, ordering=None, float_fmt="{:11.8f}"):
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
        if len(ordering) < len(atoms):
            ordering = [[-1, -1, -1]] + list(ordering)
        if len(zmat) < len(atoms):
            zmat = [[-1, -1, -1]] + list(zmat)

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
            [float_fmt.format(x) if not isinstance(x, str) else x for x in zz]
            for zz in zmat
        ]
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
            ["{:.0f}".format(x) if not isinstance(x, str) else x for x in zz]
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
        return "\n".join(
            fmt_string.format(
                a=a,
                n=n,
                r=r
            )
            for a, n, r in zip(atoms, ordering, zmat)
        )

    @classmethod
    def fmt_orca_zmat(cls, atoms, zmat, ordering=None, float_fmt="{:11.8f}"):
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
        if len(ordering) < len(atoms):
            ordering = [[-1, -1, -1]] + list(ordering)
        if len(zmat) < len(atoms):
            zmat = [[-1, -1, -1]] + list(zmat)

        zmat = [
            ["0.0", "0.0", "0.0"]
                if i == 0 else
            [z[0], "0.0", "0.0"]
                if i == 1 else
            [z[0], z[1], "0.0"]
                if i == 2 else
            [z[0], z[1], z[2]]
            for i, z in enumerate(zmat)
        ]
        zmat = [
            [float_fmt.format(x) if not isinstance(x, str) else x for x in zz]
            for zz in zmat
        ]
        ordering = [
            [0, 0, 0]
                if i == 0 else
            [z[0], 0, 0]
                if i == 1 else
            [z[0], z[1], 0]
                if i == 2 else
            [z[0], z[1], z[2]]
            for i, z in enumerate(ordering)
        ]
        ordering = [
            ["{:.0f}".format(x) if not isinstance(x, str) else x for x in zz]
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
        fmt_string = f"{{a:<{max_at_len}}} {{n[0]:>{nls[0]}}} {{n[1]:>{nls[1]}}} {{n[2]:>{nls[2]}}} {{r[0]:>{zls[0]}}} {{r[1]:>{zls[1]}}} {{r[2]:>{zls[2]}}}"
        return "\n".join(
            fmt_string.format(a=a, n=n,r=r)
            for a, n, r in zip(atoms, ordering, zmat)
        )

    def format_bonds_block(self):
        bonds = self.opts.get('bonds')
        return "\n".join(
            ' {l} {r}{t}'.format(
                l='{:.0f}'.format(b[0]) if not isinstance(b[0], str) else b[0],
                r='{:.0f}'.format(b[1]) if not isinstance(b[1], str) else b[1],
                t=(
                    (" " + ('{:.0f}'.format(b[2]) if not isinstance(b[2], str) else b[2]))
                        if len(b) > 2 else
                    ""
                )
            )
            for b in bonds
        )

class ExternalProgramJob(metaclass=abc.ABCMeta):
    # blocks: 'tuple[OptionsBlock]' = []
    # base_template = None
    def __init__(self, **opts):
        self.blocks = self.get_block_types()
        self.base_template = self.load_template()
        self._block_keys = {
            k:b
            for b in self.get_block_types()
            for k in b.__props__
        }
        self.block_opts = self.populate_blocks(opts)
    @abc.abstractmethod
    def get_block_types(self):
        ...
    @abc.abstractmethod
    def load_template(self):
        ...

    def populate_blocks(self, opts):
        block_opts = [
            {} for b in self.blocks
        ]
        bad_opts = set()
        for o,v in opts.items():
            for i,b in enumerate(self.blocks):
                valid, o = b.check_canon(o, v)
                if valid:
                    block_opts[i][o] = v
                    break
            else:
                bad_opts.add(o)
        if len(bad_opts) > 0:
            raise ValueError(f"can't find block type for opts {bad_opts} in {self.blocks}")

        return block_opts

    def get_params(self):
        block_opts = [
            b(**o).get_params()
            for b, o in zip(self.blocks, self.block_opts)
        ]
        all_opts = block_opts[0]
        for o in block_opts[1:]:
            double_keys = all_opts.keys() & o.keys()
            if len(double_keys) > 0:
                raise ValueError(f"got duplicate keys {double_keys}")
            all_opts = dict(all_opts, **o)
        return all_opts

    def format(self):
        all_opts = self.get_params()
        return OptionalTemplate(self.base_template).apply(**all_opts)

    def write(self, file, mode='w'):
        if hasattr(file, 'write'):
            file.write(self.format())
        else:
            with open(file, mode) as out:
                out.write(self.format())
        return file

