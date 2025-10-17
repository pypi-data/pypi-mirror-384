import json
import os.path

from .Jobs import ExternalProgramJob, OptionsBlock, SystemBlock

__all__ = [
    "GaussianJob"
]

class GaussianOptionsBlock(OptionsBlock):
    opts_key = None

    job_params_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Templates', 'gaussian_opts.json')
    _json = None
    @classmethod
    def load_json(cls):
        if cls._json is None:
            with open(cls.job_params_json) as opts_json:
                cls._json = json.load(opts_json)
        return cls._json

    @classmethod
    def get_props(cls):
        return list(cls.load_json()[cls.opts_key].keys())

    @classmethod
    def check_subopts(cls, key, opt_list, opt_dict=None, ignore_missing=False):
        if opt_dict is None:
            opt_list, opt_dict = cls.prep_opts(opt_list)

        base_opts = cls.load_json()
        if ignore_missing and key not in base_opts:
            return

        valid_opts = set(k.lower() for k in base_opts[key])
        bad_opts = []
        for o in opt_list:
            if o.lower() not in valid_opts:
                bad_opts.append(o)
        for o in opt_dict:
            if o.lower() not in valid_opts:
                bad_opts.append(o)
        if len(bad_opts) > 0:
            raise ValueError("got unknown options {} for property {} (known values are {})")

    @classmethod
    def format_opts(cls, opt_list, opt_dict=None, wrap=False):
        if opt_dict is None:
            if isinstance(opt_list, str):
                return opt_list
            else:
                opt_list, opt_dict = cls.prep_opts(opt_list)

        opt_strings = [
            cls.format_opts(o)
            for o in opt_list
        ] + [
            "{}={}".format(k, cls.format_opts(o))
            for k, o in opt_dict.items()
        ]
        if wrap and len(opt_strings) > 0 or len(opt_strings) > 1:
            return "(" + ",".join(opt_strings) + ")"
        else:
            return "".join(opt_strings)

    def format_base_params(self, opts=None):
        base_params = []
        if opts is None:
            opts = self.opts
        for k,o in opts.items():
            if o is True:
                base_params.append(k)
            elif o is False:
                ...
            else:
                fmt = self.format_opts(o)
                if len(fmt) == 0:
                    base_params.append(k)
                else:
                    base_params.append(k+"="+fmt)
        return base_params

class GaussianLinkBlock(GaussianOptionsBlock):
    opts_key = "Link0"

    def get_params(self):
        base = self.format_base_params()
        return {'link0':"\n".join("%"+b for b in base)}

class GaussianLOTBlock(GaussianOptionsBlock):
    opts_key = "LevelOfTheory"

    @classmethod
    def get_props(cls):
        return ["basis_set", "level_of_theory"] + super().get_props()

    @classmethod
    def get_basis_set_map(cls):
        return {
            k.lower():k
            for k in cls.load_json()["BasisSets"]
        }

    def get_params(self):
        lot = self.opts.get("level_of_theory", self.opts)
        if isinstance(lot, str):
            lot = {lot:[]}
        else:
            lot = lot.copy()

        lots = []
        for method, opts in lot.items():
            opt_list, opt_dict = self.prep_opts(opts)

            if 'basis_set' in opt_dict:
                basis_set = opt_dict['basis_set']
                del opt_dict[basis_set]
            elif 'basis_set' in self.opts:
                basis_set = self.opts['basis_set']
            else:
                bs_map = self.get_basis_set_map()
                for k in opt_list:
                    k = k.lower()
                    if k in bs_map:
                        basis_set = bs_map[k]
                        break
                else:
                    basis_set = ""
                opt_list = [k for k in opt_list if k.lower() not in bs_map]

            self.check_subopts(method, opt_list, opt_dict, ignore_missing=True)

            bs_string = ("/"+basis_set) if len(basis_set) > 0 else ""
            lots.append(
                method + self.format_opts(opt_list, opt_dict, wrap=True) + bs_string
            )

        if len(lots) == 0:
            return {}
        else:
            return {'level_of_theory':"#" + " ".join(lots)}

class GaussianRouteBlock(GaussianOptionsBlock):
    opts_key = "Route"

    @property
    def special_param_dispatch(self):
        return {
            "freq":self.handle_freq
        }

    def handle_freq(self, opts):
        opt_list, opt_dict = self.prep_opts(opts)
        base = {}
        extra = {}
        for k, o in opt_dict.items():
            if k.lower() in {"selanharmonicmodes"}:
                opt_list.append(k)
                extra["select_anharmonic_modes"] = " ".join(str(i) for i in o)
            elif k.lower() in {"selnormalmodes"}:
                opt_list.append(k)
                extra["select_normal_modes"] = " ".join(str(i) for i in o)
            else:
                base[k] = o

        return (opt_list, base), extra

    linewidth = 80
    def get_params(self):
        base_params = {}
        extra_params = {}
        disp = self.special_param_dispatch
        for k,o in self.opts.items():
            d = disp.get(k.lower())
            if d is None:
                base_params[k] = o
            else:
                o1, o2 = d(o)
                base_params[k] = o1
                extra_params.update(o2)
        gp_params = self.format_base_params(base_params)
        blocks = [ [] ]
        bl = 1
        for g in gp_params:
            pad = len(g) + 1
            bl = bl + pad
            if bl > self.linewidth:
                blocks.append([])
                bl = 1 + pad
            blocks[-1].append(g)

        params = {}
        route_str = "\n".join("#" + " ".join(b) for b in blocks if len(b) > 0)
        if len(route_str) > 0:
            params['route'] = route_str
        params.update(extra_params)

        return params

class GaussianSystemBlock(SystemBlock):
    __props__ = SystemBlock.__props__ + ("variables", "constants")

    fmt_key = ""


    @classmethod
    def format_vars_block(cls, vars, float_fmt="{:11.8f}", joiner=None):
        if isinstance(vars, dict):
            if joiner is None:
                joiner = "="
            vars = vars.items()
        if joiner is None:
            joiner = " "
        return "\n".join(
            " {k}{joiner}{v}".format(
                k=k,
                joiner=joiner,
                v=v if isinstance(v, str) else float_fmt.format(v)
            )
            for k, v in vars
        )

    def format_coordinate_block(self):
        charge = self.opts.get("charge", 0)
        multiplicity = self.opts.get("multiplicity", 1)
        carts = self.opts.get("cartesians")
        zmat = self.opts.get("zmatrix")

        chunks = []
        chunks.append(f"{charge} {multiplicity}")

        if carts is not None:
            if isinstance(carts, str):
                chunks.append(carts)
            else:
                chunks.append(self.fmt_carts(self.opts.get('atoms'), carts))
        elif zmat is not None:
            if isinstance(zmat, str):
                chunks.append(zmat)
            else:
                chunks.append(self.fmt_zmat(self.opts.get('atoms'), zmat, self.opts.get('ordering')))
        else:
            raise ValueError("no coordinate spec supplied")

        consts = self.opts.get("constants")
        if consts is None: consts = []
        if len(consts) > 0:
            chunks.append("Constants:")
            chunks.append(self.format_vars_block(consts))
        vars = self.opts.get("variables")
        if vars is None: vars = []
        if len(vars) > 0:
            chunks.append("Variables:")
            chunks.append(self.format_vars_block(vars))

        return "\n".join(chunks)

    def get_params(self):
        base_opts = {}
        if len(self.opts) > 0:
            base_opts[self.fmt_key + "system"] = self.format_coordinate_block()
            if len(self.opts.get('bonds', [])) > 0:
                base_opts[self.fmt_key + "bonds"] = self.format_bonds_block()
        return base_opts

class GaussianRestBlock(GaussianOptionsBlock):
    opts_key = "rest"
    job_template = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Templates', 'gaussian_job.gjf')
    @classmethod
    def load_json(cls):
        if cls._json is None:
            with open(cls.job_template) as r:
                t = r.read()
            return {"rest":{s.strip("{").strip("}"):[] for s in t.split()}}
        return cls._json

class GaussianJob(ExternalProgramJob):
    job_template = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Templates', 'gaussian_job.gjf')
    blocks = [
        GaussianLinkBlock,
        GaussianLOTBlock,
        GaussianRouteBlock,
        GaussianSystemBlock,
        GaussianRestBlock
    ]

    def __init__(self, *strs, **opts):
        for o in strs:
            rt, o = GaussianRouteBlock.check_canon(o)
            if rt:
                opts[o] = True
            else:
                opts['level_of_theory'] = o
        super().__init__(**opts)

    @classmethod
    def get_extra_keys(cls):
        with open(cls.job_template) as r:
            t = r.read()
        return {s.strip("{").strip("}") for s in t.split()}

    @classmethod
    def get_block_types(cls):
        return cls.blocks

    @classmethod
    def load_template(cls):
        return cls.job_template

    non_blank_line_terminated = {'link0', 'level_of_theory'}
    def get_params(self):
        base_params = super().get_params()
        for k,b in base_params.items():
            if k not in self.non_blank_line_terminated:
                base_params[k] = b + "\n"

        return base_params
