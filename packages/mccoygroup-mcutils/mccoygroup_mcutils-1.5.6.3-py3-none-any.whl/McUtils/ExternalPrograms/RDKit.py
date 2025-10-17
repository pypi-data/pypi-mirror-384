

__all__ = [
    "RDMolecule"
]

import numpy as np, io, os
from .. import Numputils as nput
from ..Devutils import OutputRedirect

from .ChemToolkits import RDKitInterface
from .ExternalMolecule import ExternalMolecule

class RDMolecule(ExternalMolecule):
    """
    A simple interchange format for RDKit molecules
    """

    def __init__(self, rdconf, charge=None):
        #atoms, coords, bonds):
        self._rdmol = rdconf.GetOwningMol()
        super().__init__(rdconf)
        self.charge = charge

    @property
    def rdmol(self):
        if self._rdmol is None:
            self._rdmol = self.mol.GetOwningMol()
        return self._rdmol
    @property
    def atoms(self):
        mol = self.rdmol
        return [atom.GetSymbol() for atom in mol.GetAtoms()]
    @property
    def bonds(self):
        mol = self.rdmol
        return [
            [b.GetBeginAtomIdx(), b.GetEndAtomIdx(), b.GetBondTypeAsDouble()]
            for b in mol.GetBonds()
        ]
    @property
    def coords(self):
        return self.mol.GetPositions()
    @property
    def rings(self):
        return self.rdmol.GetRingInfo().AtomRings()
    @property
    def meta(self):
        return self.rdmol.GetPropsAsDict()

    def copy(self):
        Chem = self.chem_api()
        conf = self.mol
        new_mol = Chem.AddHs(Chem.Mol(self.rdmol), explicitOnly=True)
        new_mol.AddConformer(conf)
        return type(self).from_rdmol(new_mol,
                                     conf_id=conf.GetId(),
                                     charge=self.charge, sanitize=False,
                                     guess_bonds=False,
                                     add_implicit_hydrogens=False
                                     )
    @property
    def charges(self):
        from rdkit.Chem import AllChem
        AllChem.ComputeGasteigerCharges(self.rdmol)
        return [
            at.GetDoubleProp('_GasteigerCharge')
            for at in self.rdmol.GetAtoms()
        ]

    @classmethod
    def chem_api(cls):
        return RDKitInterface.submodule("Chem")
    @classmethod
    def from_rdmol(cls, rdmol, conf_id=0, charge=None, guess_bonds=False, sanitize=True,
                   add_implicit_hydrogens=False,
                   sanitize_ops=None):
        Chem = cls.chem_api() # to get nice errors
        rdmol = Chem.AddHs(rdmol, explicitOnly=not add_implicit_hydrogens)
        if guess_bonds:
            rdDetermineBonds = RDKitInterface.submodule("Chem.rdDetermineBonds")
            rdmol = Chem.Mol(rdmol)
            if charge is None:
                charge = 0
            rdDetermineBonds.DetermineConnectivity(rdmol, charge=charge)
            # return cls.from_rdmol(rdmol, conf_id=conf_id, guess_bonds=False, charge=charge)
        if sanitize:
            rdmolops = RDKitInterface.submodule("Chem.rdmolops")
            if sanitize_ops is None:
                sanitize_ops = (
                        rdmolops.SANITIZE_ALL
                        ^rdmolops.SANITIZE_PROPERTIES
                        # ^rdmolops.SANITIZE_ADJUSTHS
                        # ^rdmolops.SANITIZE_CLEANUP
                        ^rdmolops.SANITIZE_CLEANUP_ORGANOMETALLICS
                )
            rdmol = Chem.Mol(rdmol)
            Chem.SanitizeMol(rdmol, sanitize_ops)
        conf = rdmol.GetConformer(conf_id)
        return cls(conf, charge=charge)

    @classmethod
    def resolve_bond_type(cls, t):
        Chem = cls.chem_api()

        if abs(t - 1.5) < 1e-2:
            t = Chem.BondType.names["AROMATIC"]
        elif abs(t - 2.5) < 1e-2:
            t = Chem.BondType.names["TWOANDAHALF"]
        elif abs(t - 3.5) < 1e-2:
            t = Chem.BondType.names["TWOANDAHALF"]
        else:
            t = Chem.BondType.values[int(t)]

        return t
    @classmethod
    def from_coords(cls, atoms, coords, bonds=None, charge=None, guess_bonds=None):
        Chem = cls.chem_api()
        mol = Chem.EditableMol(Chem.Mol())
        mol.BeginBatchEdit()
        for a in atoms:
            a = Chem.Atom(a)
            mol.AddAtom(a)
        if bonds is not None:
            for b in bonds:
                if len(b) == 2:
                    i,j = b
                    t = 1
                else:
                    i,j,t = b
                if nput.is_numeric(t):
                    t = cls.resolve_bond_type(t)
                else:
                    t = Chem.BondType.names[t]
                mol.AddBond(int(i), int(j), t)
        mol.CommitBatchEdit()

        mol = mol.GetMol()
        mol = Chem.AddHs(mol, explicitOnly=True)
        conf = Chem.Conformer(len(atoms))
        conf.SetPositions(np.asanyarray(coords))
        conf.SetId(0)
        mol.AddConformer(conf)

        if guess_bonds is None:
            guess_bonds = bonds is None

        return cls.from_rdmol(mol, charge=charge, guess_bonds=guess_bonds)

    @classmethod
    def from_mol(cls, mol, coord_unit="Angstroms", guess_bonds=None):
        from ..Data import UnitsData

        return cls.from_coords(
            mol.atoms,
            mol.coords * UnitsData.convert(coord_unit, "Angstroms"),
            bonds=mol.bonds,
            charge=mol.charge,
            guess_bonds=guess_bonds
        )

    @classmethod
    def _load_sdf_conf(cls, stream, which=0):
        Chem = cls.chem_api()
        mol = None
        for i in range(which+1):
            mol = next(Chem.ForwardSDMolSupplier(stream, sanitize=False, removeHs=False))
        return mol
    @classmethod
    def from_sdf(cls, sdf_string, which=0):
        if os.path.isfile(sdf_string):
            with open(sdf_string, 'rb') as stream:
                mol = cls._load_sdf_conf(stream, which=which)
        else:
            mol = cls._load_sdf_conf(io.BytesIO(sdf_string.encode()), which=which)
        return cls.from_rdmol(mol)

    @classmethod
    def get_confgen_opts(cls):
        AllChem = cls.allchem_api()
        params = AllChem.ETKDGv3()
        params.useExpTorsionAnglePrefs = True
        params.useBasicKnowledge = True
        return params
    @classmethod
    def from_smiles(cls, smiles,
                    sanitize=False,
                    parse_name=True,
                    allow_cxsmiles=True,
                    strict_cxsmiles=True,
                    remove_hydrogens=False,
                    replacements=None,
                    add_implicit_hydrogens=False,
                    call_add_hydrogens=True,
                    num_confs=1, optimize=False, take_min=True,
                    force_field_type='mmff',
                    **opts):

        if os.path.isfile(smiles):
            with open(smiles) as f:
                smiles = f.read()
        Chem = cls.chem_api()

        params = Chem.SmilesParserParams()
        params.removeHs = remove_hydrogens
        params.sanitize = sanitize
        if replacements is not None:
            params.replacements = replacements
        params.parseName = parse_name
        params.allowCXSMILES = allow_cxsmiles
        params.strictCXSMILES = strict_cxsmiles
        for k,v in opts.items():
            setattr(params, k, v)

        rdkit_mol = Chem.MolFromSmiles(smiles, params)
        if not sanitize:
            rdkit_mol.UpdatePropertyCache()
        if call_add_hydrogens:
            mol = Chem.AddHs(rdkit_mol, explicitOnly=not add_implicit_hydrogens)
        else:
            mol = rdkit_mol

        return cls.from_base_mol(mol,
                                 num_confs=1, optimize=False, take_min=True,
                                 force_field_type='mmff'
                                 )

        # rdDistGeom = RDKitInterface.submodule("Chem.rdDistGeom")
        # rdDistGeom.EmbedMolecule(mol, num_confs, **cls.get_confgen_opts())

    @classmethod
    def from_base_mol(cls, mol,
                           conf_id=-1,
                           num_confs=1,
                           optimize=False,
                           take_min=None,
                           force_field_type='mmff',
                           **mol_opts):
        try:
            conf = mol.GetConformer(conf_id)
        except ValueError:
            conf = None
        if conf:
            return cls.from_rdmol(mol, conf_id, **mol_opts)
        else:
            if conf_id > num_confs + 1:
                num_confs = conf_id
            return cls.from_no_conformer_molecule(mol,
                                                  num_confs=num_confs,
                                                  optimize=optimize,
                                                  take_min=conf_id < 0 if take_min is None else take_min,
                                                  force_field_type=force_field_type,
                                                  **mol_opts
                                                  )

    @classmethod
    def from_no_conformer_molecule(cls,
                                   mol,
                                   num_confs=1,
                                   optimize=False,
                                   take_min=True,
                                   force_field_type='mmff',
                                   add_implicit_hydrogens=False,
                                   **etc
                                   ):
        AllChem = cls.allchem_api()

        AllChem.AddHs(mol, explicitOnly=not add_implicit_hydrogens)

        with OutputRedirect():
            conformer_set = AllChem.EmbedMultipleConfs(mol, numConfs=num_confs, params=cls.get_confgen_opts())
        if optimize:
            rdForceFieldHelpers = RDKitInterface.submodule("Chem.rdForceFieldHelpers")
            if force_field_type == 'mmff':
                rdForceFieldHelpers.MMFFOptimizeMoleculeConfs(mol)
            elif force_field_type == 'uff':
                rdForceFieldHelpers.UFFOptimizeMoleculeConfs(mol)
            else:
                raise NotImplementedError(f"no basic preoptimization support for {force_field_type}")

        if take_min and num_confs > 1:
            conf_ids = list(conformer_set)
            force_field_type = cls.get_force_field_type(force_field_type)
            if isinstance(force_field_type, (list, tuple)):
                force_field_type, prop_gen = force_field_type
            else:
                prop_gen = None

            if prop_gen is not None:
                props = prop_gen(mol)
            else:
                props = None

            engs = [
                force_field_type(mol, props, confId=conf_id).CalcEnergy()
                for conf_id in conf_ids
            ]

            conf_id = conf_ids[np.argmin(engs)]
        else:
            conf_id = 0

        return cls.from_rdmol(mol, conf_id=conf_id, add_implicit_hydrogens=add_implicit_hydrogens, **etc)

    def to_smiles(self):
        return self.chem_api().MolToSmiles(self.rdmol)

    @classmethod
    def from_molblock(cls,
                      molblock,
                      add_implicit_hydrogens=False,
                      call_add_hydrogens=True,
                      ):
        Chem = cls.chem_api()
        if os.path.isfile(molblock):
            mol = Chem.MolFromMolFile(molblock, sanitize=False, removeHs=False)
        else:
            mol = Chem.MolFromMolBlock(molblock, sanitize=False, removeHs=False)
        return cls.from_rdmol(mol, add_implicit_hydrogens=add_implicit_hydrogens)

    @classmethod
    def allchem_api(cls):
        return RDKitInterface.submodule("Chem.AllChem")
    @classmethod
    def get_force_field_type(cls, ff_type):
        AllChem = cls.allchem_api()

        if isinstance(ff_type, str):
            if ff_type == 'mmff':
                ff_type = (AllChem.MMFFGetMoleculeForceField, AllChem.MMFFGetMoleculeProperties)
            elif ff_type == 'uff':
                ff_type = (AllChem.UFFGetMoleculeForceField, None)
            else:
                raise ValueError(f"can't get RDKit force field type from '{ff_type}")

        return ff_type

    def get_force_field(self, force_field_type='mmff', conf=None, mol=None, conf_id=None, **extra_props):
        if conf is None:
            if mol is None:
                mol = self
            if conf_id is None:
                conf_id = mol.mol.GetId()
            mol = mol.rdmol
        else:
            if mol is None:
                mol = conf.GetOwningMol()
            if conf_id is None:
                conf_id = conf.GetId()
            if np.sum(np.abs(conf.GetPositions() - mol.GetConformer(conf_id).GetPositions())) > 1e-6:
                print(mol)
                print(self.rdmol)
                raise ValueError(
                    conf, mol.GetConformer(conf_id)
                )

        force_field_type = self.get_force_field_type(force_field_type)
        if isinstance(force_field_type, (list, tuple)):
            force_field_type, prop_gen = force_field_type
        else:
            prop_gen = None

        if prop_gen is not None:
            props = prop_gen(mol)
        else:
            props = None

        if props is not None:
            return force_field_type(mol, props, confId=conf_id, **extra_props)
        else:
            return force_field_type(mol, confId=conf_id, **extra_props)

    def evaluate_charges(self, coords, model='gasteiger'):
        if model == 'gasteiger':
            from rdkit.Chem import AllChem
            AllChem.ComputeGasteigerCharges(self.rdmol)
            return [
                at.GetDoubleProp('_GasteigerCharge')
                for at in self.rdmol.GetAtoms()
            ]
        else:
            raise ValueError(f"charge model {model} not supported in RDKit")

    def calculate_energy(self, geoms=None, force_field_generator=None, force_field_type='mmff', conf_id=None):
        Chem = self.chem_api()
        if conf_id is None:
            conf_id = self.mol.GetId()
        mol = Chem.Mol(self.rdmol, confId=conf_id)
        conf = mol.GetConformer(0)

        if force_field_generator is None:
            force_field_generator = self.get_force_field
        if geoms is not None:
            cur_geom = np.array(self.mol.GetPositions()).reshape(-1, 3)
            geoms = np.asanyarray(geoms)
            base_shape = geoms.shape[:-2]
            geoms = geoms.reshape((-1,) + cur_geom.shape)
            vals = np.empty(len(geoms), dtype=float)
            try:
                for i,g in enumerate(geoms):
                    conf.SetPositions(g.copy())
                    ff = force_field_generator(force_field_type, conf=conf, mol=mol)
                    vals[i] = ff.CalcEnergy()
            finally:
                conf.SetPositions(cur_geom)
            return vals.reshape(base_shape)
        else:
            ff = force_field_generator(force_field_type, conf_id=conf_id)
            return ff.CalcEnergy()

    def calculate_gradient(self, geoms=None, force_field_generator=None, force_field_type='mmff', conf_id=None):
        if force_field_generator is None:
            force_field_generator = self.get_force_field

        Chem = self.chem_api()
        if conf_id is None:
            conf_id = self.mol.GetId()
        mol = Chem.Mol(self.rdmol, confId=conf_id)
        conf = mol.GetConformer(0)

        cur_geom = np.array(conf.GetPositions()).reshape(-1, 3)
        if geoms is not None:
            geoms = np.asanyarray(geoms)
            base_shape = geoms.shape[:-2]
            geoms = geoms.reshape((-1,) + cur_geom.shape)
            vals = np.empty((len(geoms), np.prod(cur_geom.shape, dtype=int)), dtype=float)
            try:
                for i, g in enumerate(geoms):
                    new_geom = g.copy().view(np.ndarray)
                    conf.SetPositions(new_geom)
                    ff = force_field_generator(force_field_type, conf=conf, mol=mol)
                    vals[i] = ff.CalcGrad()
            finally:
                conf.SetPositions(cur_geom)
            return vals.reshape(base_shape + (-1,))
        else:
            ff = force_field_generator(force_field_type, conf_id=conf_id, conf=conf, mol=mol)
            return np.array(ff.CalcGrad()).reshape(-1)

    def calculate_hessian(self, force_field_generator=None, force_field_type='mmff', stencil=5, mesh_spacing=.01, **fd_opts):
        from ..Zachary import FiniteDifferenceDerivative

        cur_geom = np.array(self.mol.GetPositions()).reshape(-1, 3)

        # if force_field_generator is None:
        #     force_field_generator = self.get_force_field(force_field_type)

        # def eng(structs):
        #     structs = structs.reshape(structs.shape[:-1] + (-1, 3))
        #     new_grad = self.calculate_energy(structs, ff=ff)
        #     return new_grad
        # der = FiniteDifferenceDerivative(eng, function_shape=((0,), (0,)), stencil=stencil, mesh_spacing=mesh_spacing, **fd_opts)
        # return der.derivatives(cur_geom.flatten()).derivative_tensor(2)

        def jac(structs):
            structs = structs.reshape(structs.shape[:-1] + (-1, 3))
            new_grad = self.calculate_gradient(structs,
                                               force_field_generator=force_field_generator,
                                               force_field_type=force_field_type
                                               )
            return new_grad
        der = FiniteDifferenceDerivative(jac, function_shape=((0,), (0,)), stencil=stencil, mesh_spacing=mesh_spacing, **fd_opts)
        return der.derivatives(cur_geom.flatten()).derivative_tensor(1)

    def get_optimizer_params(self, maxAttempts=1000, useExpTorsionAnglePrefs=True, useBasicKnowledge=True, **etc):
        AllChem = self.allchem_api()

        params = AllChem.ETKDGv3()
        params.maxAttempts = maxAttempts  # Increase the number of attempts
        params.useExpTorsionAnglePrefs = useExpTorsionAnglePrefs
        params.useBasicKnowledge = useBasicKnowledge
        for k,v in etc.items():
            setattr(params, k, v)

        return params

    def optimize_structure(self, geoms=None, force_field_type='mmff', optimizer=None, maxIters=1000, **opts):

        if optimizer is None:
            ff_helpers = RDKitInterface.submodule("Chem.rdForceFieldHelpers")
            def optimizer(mol, **etc):
                ff = mol.get_force_field(force_field_type)
                return ff_helpers.OptimizeMolecule(ff)

        maxIters = int(maxIters)
        if geoms is not None:
            cur_geom = np.array(self.mol.GetPositions()).reshape(-1, 3)
            geoms = np.asanyarray(geoms, dtype=float)
            base_shape = geoms.shape[:-2]
            geoms = geoms.reshape((-1,) + cur_geom.shape)
            opt_vals = np.empty((len(geoms),), dtype=int)
            opt_geoms = np.empty_like(geoms)
            try:
                for i, g in enumerate(geoms):
                    self.mol.SetPositions(g)
                    opt_vals[i] = optimizer(self, maxIters=maxIters, **opts)
                    opt_geoms[i] = self.mol.GetPositions()
            finally:
                self.mol.SetPositions(cur_geom)
            return opt_vals.reshape(base_shape), opt_geoms.reshape(base_shape + opt_geoms.shape[1:]), {}
        else:
            opt = optimizer(self, maxIters=maxIters, **opts)
            return opt, self.mol.GetPositions(), {}

    def show(self):
        return RDKitInterface.submodule('Chem.Draw.IPythonConsole').drawMol3D(
            self.mol.GetOwningMol(),
            confId=self.mol.GetId()
            # view=None, confId=-1, drawAs=None, bgColor=None, size=None
        )
