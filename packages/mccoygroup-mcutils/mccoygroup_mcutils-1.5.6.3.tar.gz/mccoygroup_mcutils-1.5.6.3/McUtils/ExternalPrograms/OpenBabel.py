

__all__ = [
    "OBMolecule"
]

import numpy as np, io, os

# from .. import Numputils as nput
from ..Devutils import OutputRedirect
from ..Data import AtomData

from .ChemToolkits import OpenBabelInterface
from .ExternalMolecule import ExternalMolecule

class OBMolecule(ExternalMolecule):
    """
    A simple interchange format for RDKit molecules
    """

    def __init__(self, obmol, charge=None):
        super().__init__(obmol)
        self.charge = charge


    @classmethod
    def get_api(cls):
        return OpenBabelInterface()
    @property
    def atoms(self):
        ob = self.get_api()
        return [a.GetAtomicNum() for a in ob.OBMolAtomIter(self.mol)]
    @property
    def bonds(self):
        ob = self.get_api()
        return [
            [b.GetBeginAtomIdx()-1 , b.GetEndAtomIdx()-1, b.GetBondOrder()]
            for b in ob.OBMolBondIter(self.mol)
        ]
    @property
    def coords(self):
        ob = self.get_api()
        return np.array([
            [a.GetX(), a.GetY(), a.GetZ()]
            for a in ob.OBMolAtomIter(self.mol)
        ])

    @classmethod
    def from_obmol(cls, obmol, add_implicit_hydrogens=False, charge=None, guess_bonds=False):
        if add_implicit_hydrogens:
            obmol.AddHydrogens()
        if guess_bonds:
            ...
        return cls(obmol, charge=charge)

    @classmethod
    def from_string(cls, data, fmt=None, target_fmt="mol2",
                    add_implicit_hydrogens=False, charge=None, guess_bonds=False):
        ob = cls.get_api()
        obConversion = ob.OBConversion()
        obConversion.SetInAndOutFormats(fmt, target_fmt)

        mol = ob.OBMol()
        obConversion.ReadString(mol, data)
        return cls.from_obmol(mol,
                              add_implicit_hydrogens=add_implicit_hydrogens,
                              charge=charge,
                              guess_bonds=guess_bonds)

    @classmethod
    def from_file(cls, file, fmt=None, target_fmt="mol2",
                  add_implicit_hydrogens=False, charge=None, guess_bonds=False):
        ob = cls.get_api()
        if fmt is None:
            _, fmt = os.path.splitext(file)
            fmt = fmt.strip(".")
        obConversion = ob.OBConversion()
        obConversion.SetInAndOutFormats(fmt, target_fmt)

        mol = ob.OBMol()
        obConversion.ReadFile(mol, file)
        return cls.from_obmol(mol,
                              add_implicit_hydrogens=add_implicit_hydrogens,
                              charge=charge,
                              guess_bonds=guess_bonds)

    def to_file(self, file, fmt=None, base_fmt="mol2"):
        ob = self.get_api()
        if fmt is None:
            _, fmt = os.path.splitext(file)
            fmt = fmt.strip(".")
        obConversion = ob.OBConversion()
        obConversion.SetInAndOutFormats(base_fmt, fmt)

        obConversion.WriteFile(self.mol, file)
        return file

    def to_string(self, fmt, base_fmt="mol2"):
        ob = self.get_api()
        obConversion = ob.OBConversion()
        obConversion.SetInAndOutFormats(base_fmt, fmt)

        return obConversion.WriteString(self.mol)

    @classmethod
    def from_coords(cls, atoms, coords, bonds=None, add_implicit_hydrogens=False, charge=None, guess_bonds=False):
        ob = cls.get_api()

        mol = ob.OBMol()
        for elem, crd in zip(atoms, coords):
            a = mol.NewAtom()
            a.SetAtomicNum(AtomData[elem]["Number"])  # carbon atom
            a.SetVector(*(float(c) for c in crd))  # coordinates

        if bonds is not None:
            for b in bonds:
                mol.AddBond(int(b[0])+1, int(b[1])+1, int(b[2]) if len(b) > 2 else 1)  # atoms indexed from 1

        return cls.from_obmol(mol,
                              add_implicit_hydrogens=add_implicit_hydrogens,
                              charge=charge,
                              guess_bonds=guess_bonds)

    @classmethod
    def from_mol(cls, mol, coord_unit="Angstroms", guess_bonds=False):
        from ..Data import UnitsData

        return cls.from_coords(
            mol.atoms,
            mol.coords * UnitsData.convert(coord_unit, "Angstroms"),
            bonds=mol.bonds,
            charge=mol.charge,
            guess_bonds=guess_bonds
        )

    # def calculate_energy(self, geoms=None, force_field_generator=None, force_field_type='mmff', conf_id=None):
    #     if force_field_generator is None:
    #         force_field_generator = self.get_force_field
    #     if geoms is not None:
    #         cur_geom = np.array(self.mol.GetPositions()).reshape(-1, 3)
    #         geoms = np.asanyarray(geoms)
    #         base_shape = geoms.shape[:-2]
    #         geoms = geoms.reshape((-1,) + cur_geom.shape)
    #         vals = np.empty(len(geoms), dtype=float)
    #         try:
    #             for i,g in enumerate(geoms):
    #                 self.mol.SetPositions(g)
    #                 ff = force_field_generator(force_field_type)
    #                 vals[i] = ff.CalcEnergy()
    #         finally:
    #             self.mol.SetPositions(cur_geom)
    #         return vals.reshape(base_shape)
    #     else:
    #         ff = force_field_generator(force_field_type, conf_id=conf_id)
    #         return ff.CalcEnergy()
    #
    # def calculate_gradient(self, geoms=None, force_field_generator=None, force_field_type='mmff', conf_id=None):
    #     if force_field_generator is None:
    #         force_field_generator = self.get_force_field
    #     cur_geom = np.array(self.mol.GetPositions()).reshape(-1, 3)
    #     if geoms is not None:
    #         geoms = np.asanyarray(geoms)
    #         base_shape = geoms.shape[:-2]
    #         geoms = geoms.reshape((-1,) + cur_geom.shape)
    #         vals = np.empty((len(geoms), np.prod(cur_geom.shape, dtype=int)), dtype=float)
    #         try:
    #             for i, g in enumerate(geoms):
    #                 self.mol.SetPositions(g)
    #                 ff = force_field_generator(force_field_type)
    #                 vals[i] = ff.CalcGrad()
    #         finally:
    #             self.mol.SetPositions(cur_geom)
    #         return vals.reshape(base_shape + (-1,))
    #     else:
    #         ff = force_field_generator(force_field_type, conf_id=conf_id)
    #         return np.array(ff.CalcGrad()).reshape(-1)
    #
    # def calculate_hessian(self, force_field_generator=None, force_field_type='mmff', stencil=5, mesh_spacing=.01, **fd_opts):
    #     from ..Zachary import FiniteDifferenceDerivative
    #
    #     cur_geom = np.array(self.mol.GetPositions()).reshape(-1, 3)
    #
    #     # if force_field_generator is None:
    #     #     force_field_generator = self.get_force_field(force_field_type)
    #
    #     # def eng(structs):
    #     #     structs = structs.reshape(structs.shape[:-1] + (-1, 3))
    #     #     new_grad = self.calculate_energy(structs, ff=ff)
    #     #     return new_grad
    #     # der = FiniteDifferenceDerivative(eng, function_shape=((0,), (0,)), stencil=stencil, mesh_spacing=mesh_spacing, **fd_opts)
    #     # return der.derivatives(cur_geom.flatten()).derivative_tensor(2)
    #
    #     def jac(structs):
    #         structs = structs.reshape(structs.shape[:-1] + (-1, 3))
    #         new_grad = self.calculate_gradient(structs,
    #                                            force_field_generator=force_field_generator,
    #                                            force_field_type=force_field_type
    #                                            )
    #         return new_grad
    #     der = FiniteDifferenceDerivative(jac, function_shape=((0,), (0,)), stencil=stencil, mesh_spacing=mesh_spacing, **fd_opts)
    #     return der.derivatives(cur_geom.flatten()).derivative_tensor(1)
    #
    # def get_optimizer_params(self, maxAttempts=1000, useExpTorsionAnglePrefs=True, useBasicKnowledge=True, **etc):
    #     AllChem = self.allchem_api()
    #
    #     params = AllChem.ETKDGv3()
    #     params.maxAttempts = maxAttempts  # Increase the number of attempts
    #     params.useExpTorsionAnglePrefs = useExpTorsionAnglePrefs
    #     params.useBasicKnowledge = useBasicKnowledge
    #     for k,v in etc.items():
    #         setattr(params, k, v)
    #
    #     return params
    #
    # def optimize_structure(self, geoms=None, force_field_type='mmff', optimizer=None, maxIters=1000, **opts):
    #
    #     if optimizer is None:
    #         ff_helpers = RDKitInterface.submodule("Chem.rdForceFieldHelpers")
    #         def optimizer(mol, **etc):
    #             ff = mol.get_force_field(force_field_type)
    #             return ff_helpers.OptimizeMolecule(ff, **etc)
    #
    #     if geoms is not None:
    #         cur_geom = np.array(self.mol.GetPositions()).reshape(-1, 3)
    #         geoms = np.asanyarray(geoms, dtype=float)
    #         base_shape = geoms.shape[:-2]
    #         geoms = geoms.reshape((-1,) + cur_geom.shape)
    #         opt_vals = np.empty((len(geoms),), dtype=int)
    #         opt_geoms = np.empty_like(geoms)
    #         try:
    #             for i, g in enumerate(geoms):
    #                 self.mol.SetPositions(g)
    #                 opt_vals[i] = optimizer(self, maxIters=maxIters, **opts)
    #                 opt_geoms[i] = self.mol.GetPositions()
    #         finally:
    #             self.mol.SetPositions(cur_geom)
    #         return opt_vals.reshape(base_shape), opt_geoms.reshape(base_shape + opt_geoms.shape[1:])
    #     else:
    #         opt = optimizer(self, maxIters=maxIters, **opts)
    #         return opt, self.mol.GetPositions()

    def show(self):
        return RDKitInterface.submodule('Chem.Draw.IPythonConsole').drawMol3D(
            self.mol.GetOwningMol(),
            confId=self.mol.GetId()
            # view=None, confId=-1, drawAs=None, bgColor=None, size=None
        )
