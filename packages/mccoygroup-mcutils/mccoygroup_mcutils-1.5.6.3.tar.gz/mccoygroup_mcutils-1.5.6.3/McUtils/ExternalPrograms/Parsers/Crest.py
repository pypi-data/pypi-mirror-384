import os.path

import numpy as np
from collections import namedtuple
from ..Parsers import ElectronicStructureLogReader
from ...Parsers import FileStreamReader, XYZParser, Word, Number


__all__ = [
    "CRESTParser"
]

class CRESTOptLogParser(FileStreamReader):

    def __init__(self, file, **kwargs):
        super().__init__(file, **kwargs)

    CRESTCoords = namedtuple("CRESTCoords", ["energy", "atoms", "coords"])
    @classmethod
    def parse_struct(cls, data):
        coords = np.array(Number.findall(data)).astype(float)
        e, coords = coords[0], coords[1:].reshape(-1, 3)
        atoms = Word.findall(data)
        return cls.CRESTCoords(
            e,
            atoms,
            coords
        )

    def get_next_block(self):
        block = self.get_tagged_block("=", "Etot")
        if block is None:
            return None
        else:
            return block.rsplit("\n", 1)[0]

    def parse(self):
        res = []
        block = self.get_next_block()
        while block is not None:
            res.append(self.parse_struct(block))
            block = self.get_next_block()

        return res

class CRESTConfgenLogParser(ElectronicStructureLogReader):
    components_name = "CRESTLogComponents"

    def parse(self, keys=None, num=None, reset=False):
        if keys is None:
            keys = [
                "CommandLine",
                "CalculationInfo",
                "InputStructure",
                "FinalOptInfo",
                "FinalEnsembleInfo"
            ]
        return super().parse(keys, num=num, reset=reset)

class CRESTParser:

    opt_log_file = 'crestopt.log'
    confgen_log_file = 'confgen.log'
    ensemble_energies_file = 'ensemble_energies.log'
    ensembe_file = 'ensemble_energies.log'
    conformers_best_file = 'crest_best.xyz'
    conformers_file = 'crest_conformers.xyz'
    rotamers_file = 'crest_rotamers.xyz'
    def __init__(self, parse_dir,
                 opt_log_file=None,
                 confgen_log_file=None,
                 ensemble_energies_file=None,
                 conformers_file=None,
                 conformers_best_file=None,
                 rotamers_file=None
                 ):
        self.dir = parse_dir
        self.opt_log_file = self._locate_file(opt_log_file, self.opt_log_file)
        self.confgen_log_file = self._locate_file(confgen_log_file, self.confgen_log_file)
        self.ensemble_energies_file = self._locate_file(ensemble_energies_file, self.ensemble_energies_file)
        self.conformers_file = self._locate_file(conformers_file, self.conformers_file)
        self.conformers_best_file = self._locate_file(conformers_best_file, self.conformers_best_file)
        self.rotamers_file = self._locate_file(rotamers_file, self.rotamers_file)
    def parse_optimized_structures(self):
        with CRESTOptLogParser(self.opt_log_file) as parser:
            structs = parser.parse()
        return structs

    def parse_ensemble_enegies(self):
        return np.loadtxt(self.ensemble_energies_file)

    CRESTConformers = namedtuple("CRESTConformers", ['atoms', 'energies', 'coords'])
    def parse_conformers(self, conformers_file=None):
        if conformers_file is None:
            conformers_file = self.conformers_file
        with XYZParser(conformers_file) as parser:
            structs = parser.parse()
        atoms = structs[0][1]
        coords = np.array([s for c,a,s in structs])
        energies = np.array([c.strip() for c,a,s in structs]).astype(float)
        return self.CRESTConformers(atoms, energies, coords)

    def parse_best_conformers(self):
        return self.parse_conformers(self.conformers_best_file)

    CRESTRotamers = namedtuple("CRESTRotamers", ['atoms', 'energies', 'weights', 'coords'])
    def parse_rotamers(self, rotamers_file=None):
        if rotamers_file is None:
            rotamers_file = self.rotamers_file
        with XYZParser(rotamers_file) as parser:
            structs = parser.parse()
        atoms = structs[0][1]
        coords = np.array([s for c,a,s in structs])
        eng_rel = np.array([c.split()[:2] for c,a,s in structs]).astype(float)
        return self.CRESTRotamers(atoms, eng_rel[:, 0], eng_rel[:, 1], coords)

    def parse_log(self):
        with CRESTConfgenLogParser(self.confgen_log_file) as parser:
            structs = parser.parse()
        return structs

    def _locate_file(self, base_file, default_file):
        if base_file is None:
            base_file = default_file
        test = os.path.join(self.dir, base_file)
        if os.path.exists(test):
            return test
        else:
            return base_file