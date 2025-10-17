
import numpy as np
import re
from ...Parsers import FileLineByLineReader

__all__ = [
    "CIFParser",
    "CIFConverter"
]

class CIFSymmetriesArray:
    def __init__(self, key, symmetry_list):
        self.key = key
        self.symms = symmetry_list
        self._arr = None
    def __repr__(self):
        cls = type(self)
        return f"{cls.__name__}(<{len(self.symms)}>)"

    def _parse_symmetry_function(self, arr, row, sf):
        sums = sf.split("+")
        for sm_cmp in sums:
            if len(sm_cmp) == 0: continue
            for i,sub_cmp in enumerate(sm_cmp.split("-")):
                if len(sub_cmp) == 0: continue
                # positive term is the first, the rest are negative
                parity = (-1) if i > 0 else 1
                scaling_comps = sub_cmp.split('*')
                if len(scaling_comps) == 1:
                    scaling = 1
                else:
                    if '/' in scaling_comps[0]:
                        num, den = scaling_comps[0].split('/')
                        scaling = float(num) / float(den)
                    else:
                        scaling = float(scaling_comps[0])
                comp = scaling_comps[-1]
                idx = {'x':0,'y':1,'z':2}.get(comp)
                if idx is None:
                    if '/' in comp:
                        num, den = comp.split('/')
                        comp = float(num) / float(den)
                    else:
                        comp = float(comp)
                    arr[row, 3] = scaling * float(comp) * parity
                else:
                    arr[row, idx] = scaling * parity
    def _get_symmetries(self, key, symm_labels):
        if isinstance(symm_labels, str):
            arr = np.zeros((4, 4)) # affine transformation
            arr[-1, -1] = 1
            cols = symm_labels.split(",")
            for i,c in enumerate(cols):
                self._parse_symmetry_function(arr, i, c)
            return arr
        else:
            return np.array([self._get_symmetries(key, sf) for sf in symm_labels])
    @property
    def transformation(self):
        if self._arr is None:
            self._arr = self._get_symmetries(self.key, self.symms)
        return self._arr

class CIFParser(FileLineByLineReader):
    # tags = {'_database_code_CSD', '_cell_length_a', '_cell_length_b', '_cell_length_c',
    #         '_cell_angle_alpha', '_cell_angle_beta', '_cell_angle_gamma',
    #         '_cell_formula_units_Z', '_chemical_formula_moiety', '_chemical_formula_sum',
    #         '_atom_site_fract_z', 'atom_type_radius_bond'}
    # aliases = {
    #     '_database_code_CSD': 'name', '_cell_length_a': 'a', '_cell_length_b': 'b', '_cell_length_c': 'c',
    #     '_cell_angle_alpha': 'alpha', '_cell_angle_beta': 'beta',
    #     '_cell_angle_gamma': 'gamma', '_cell_formula_units_Z': 'Z',
    #     '_chemical_formula_sum': 'sum', '_chemical_formula_moiety': 'moiety',
    #     '_atom_site_fract_z': 'atomloop', 'atom_type_radius_bond': 'bondradii'
    # }
    # exceptions = {'_chemical_formula_moiety', '_atom_site_fract_z', 'atom_type_radius_bond'}

    def __init__(self, file, fields=None, **kw):
        super().__init__(file, max_nesting_depth=1, **kw)
        self.fields = fields
    def check_tag(self, line:str, depth:int=0, active_tag=None, label:str=None, history:list[str]=None):
        if len(line) == 0:
            return self.LineReaderTags.SKIP
        elif line.startswith('data_'):
            return self.LineReaderTags.BLOCK_START, line[5:], None
        elif line.startswith('#'):
            if line == '#END':
                return self.LineReaderTags.BLOCK_END
            else:
                return self.LineReaderTags.COMMENT, line.lstrip('#')
        elif line.startswith('loop_'):
            return self.LineReaderTags.BLOCK_START
        elif line.startswith('_'):
            in_loop = depth == 1 and active_tag is self.LineReaderTags.BLOCK_START and label is None
            if in_loop:
                if len(history) > 0 and isinstance(history[-1], str) and not history[-1].startswith('_'):
                    return self.LineReaderTags.RESETTING_BLOCK_END
                else:
                    return None
            else:
                bits = line[1:].split(maxsplit=1)
                if len(bits) == 1: bits = bits + [""]
                return [self.LineReaderTags.BLOCK_START] + bits
        else:
            return None

    custom_handlers = {}
    def get_block_handlers(self):
        return {
            'cell_length_a':self._get_float,
            'cell_length_b':self._get_float,
            'cell_length_c':self._get_float,
            'cell_angle_alpha':self._get_float,
            'cell_angle_beta':self._get_float,
            'cell_angle_gamma':self._get_float,
            'cell_volume':self._get_float,
            'journal_page_first':self._get_int,
            'journal_page_last':self._get_int,
            'journal_volume':self._get_int,
            'journal_year':self._get_int,
            'atom_site_symmetry_multiplicity':self._get_int,
            'atom_site_fract_x':self._get_float,
            'atom_site_fract_y':self._get_float,
            'atom_site_fract_z':self._get_float,
            'atom_site_occupancy':self._get_float,
            'atom_type_oxidation_number':self._get_float,
            'symmetry_equiv_pos_as_xyz':CIFSymmetriesArray
        }
    def _get_float(self, key, val):
        if isinstance(val, str):
            return float(val)
        else:
            return np.array(val).astype(float)
    def _get_int(self, key, val):
        if isinstance(val, str):
            return float(val)
        else:
            return np.array(val).astype(int)
    def resolve_handler(self, label:'str|None'):
        handler = self.get_block_handlers().get(label)
        if label is not None:
            if label.endswith('_num') or label.endswith('_number'):
                handler = self._get_int
        return handler

    def handle_block(self, label:'str|None', block_data, join=True, depth=0):
        handler = self.get_block_handlers().get(label)
        if handler is not None:
            if len(block_data) == 1:
                return handler(label, block_data[0])
            else:
                return handler(label, block_data)
        else:
            if label is not None:
                if not join or isinstance(block_data, str) or not all(isinstance(b, str) for b in block_data):
                    return block_data
                else:
                    return "".join(block_data).strip()
            else:
                key_list = []
                datasets = {}
                key_parse = True
                for line in block_data:
                    if key_parse and line.startswith("_"):
                        key_list.append(line[1:].strip())
                    else:
                        if key_parse:
                            key_parse = False # keys come first done
                            for k in key_list:
                                datasets[k] = []
                        for k,v in zip(key_list, line.split()):
                            datasets[k].append(v)
                return {k:self.handle_block(k, v, join=False) for k,v in datasets.items()}

    # MAX_BLOCKS = 10
    def parse(self, target_fields=None):
        tmp_fields = self.fields
        try:
            self.fields = target_fields
            return list(iter(self))
        finally:
            self.fields = tmp_fields

class CIFConverter:
    def __init__(self, parsed_cif):
        self.data = parsed_cif
        self._cached_queries = {}
    @property
    def cell_properties(self):
        return self.prep_property_dict(
            self.find_all('cell_*', strict=False, cache=True)
        )
    @property
    def atom_properties(self):
        return self.prep_property_dict(
            self.find_all('atom_*', strict=False, cache=True)
        )
    @property
    def symmetry_properties(self):
        return self.prep_property_dict(
            self.find_all('symmetry_*', strict=False, cache=True)
        )
    def prep_property_dict(self, res):
        return {
            k:v
            for d in res
            for k,v in d.items()
        }
    def find(self, item, strict=True, cache=False):
        key = (item, strict)
        if key in self._cached_queries:
            return self._cached_queries[key]
        res = None
        if strict:
            for a in self.data:
                if item in a:
                    res = a[item]
                    break
        else:
            pattern = re.compile(item)
            for a in self.data:
                for k,v in a.items():
                    if re.match(pattern, k):
                        res = {k:v}
                        break
                if res is not None:
                    break
        if cache:
            self._cached_queries[key] = res
        return res
    def find_all(self, item, strict=True, cache=False):
        key = (item, strict)
        if key in self._cached_queries:
            return self._cached_queries[key]
        if strict:
            res = [
                a[item] for a in self.data if item in a
            ]
        else:
            pattern = re.compile(item)
            filter = [
                {k:v for k,v in a.items() if re.match(pattern, k)}
                for a in self.data
            ]
            res = [f for f in filter if len(f) > 0]
        if cache:
            self._cached_queries[key] = res
        return res

    @property
    def atoms(self):
        return self.construct_atom_coords(
            self.atom_properties,
            self.symmetry_properties
        )
    def construct_base_atom_coords(self, property_dict):
        elems_charges = [
            (a[:2], int(a[2:]))
                if not a[1].isdigit() else
            (a[:1], int(a[1:]))
            for a in property_dict['atom_site_type_symbol']
        ]
        coords = np.array([
            property_dict.get(f'atom_site_fract_{x}')
            for x in ['x', 'y', 'z']
        ]).T
        return {
            'atoms':[e for e,c in elems_charges],
            'coords':coords,
            'charges':[c for e,c in elems_charges]
        }
    def construct_atom_coords(self, atom_properties, symmetry_properties):
        structs = self.construct_base_atom_coords(atom_properties)
        symm_ops = symmetry_properties.get('symmetry_equiv_pos_as_xyz')
        if symm_ops is not None:
            ats = structs['atoms']
            crd = structs['coords']
            chg = structs['charges']
            crd = np.expand_dims(
                np.concatenate([crd, np.ones((crd.shape[0], 1))], axis=1),
                [0, 3]
            )
            all_symm = np.expand_dims(symm_ops.transformation, 1)
            full_crd = all_symm @ crd
            crd = full_crd[:, :, :3, 0].reshape(-1, 3)
            ats = list(ats) * full_crd.shape[0]
            chg = list(chg) * full_crd.shape[0]
            structs = {
                'atoms':ats,
                'coords':crd,
                'charges':np.array(chg)
            }
        return structs

