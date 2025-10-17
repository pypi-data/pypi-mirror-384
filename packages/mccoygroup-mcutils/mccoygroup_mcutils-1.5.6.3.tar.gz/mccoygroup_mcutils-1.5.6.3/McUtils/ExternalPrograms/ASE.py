

__all__ = [
    "ASEMolecule"
]

import sys

import numpy as np, io, os
from .. import Numputils as nput

from .ExternalMolecule import ExternalMolecule
from .ChemToolkits import ASEInterface

class ASEMolecule(ExternalMolecule):
    """
    A simple interchange format for ASE molecules
    """

    @property
    def atoms(self):
        return self.mol.symbols
    @property
    def coords(self):
        return self.mol.positions
    @property
    def charges(self):
        return self.mol.charges

    @classmethod
    def from_coords(cls, atoms, coords, charge=None, spin=None, info=None, calculator=None, **etc):
        if calculator is not None and charge is not None:
            if hasattr(calculator, 'set_charge'):
                calculator.set_charge(charge)

        if info is None and charge is not None or spin is not None:
            info = {}
        if charge is not None:
            info['charge'] = charge
        if spin is not None:
            info['spin'] = spin

        return cls(
            ASEInterface.Atoms(
                atoms,
                coords,
                calculator=calculator,
                info=info,
                **etc
            )
        )

    @classmethod
    def from_mol(cls, mol, coord_unit="Angstroms", calculator=None):
        from ..Data import UnitsData

        return cls.from_coords(
            mol.atoms,
            mol.coords * UnitsData.convert(coord_unit, "Angstroms"),
            # bonds=mol.bonds,
            charge=mol.charge,
            calculator=calculator
        )

    # def calculate_gradient(self, geoms=None, force_field_generator=None, force_field_type='mmff'):
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
    #         ff = force_field_generator(force_field_type)
    #         return np.array(ff.CalcGrad()).reshape(-1)

    # def get_calculator(self):
    #     if isinstance(self.calc, MassWeightedCalculator):
    #         return self.calc.copy()
    #     else:
    #         return self.load_class()(self.calc.base_calc)
    def calculate_props(self, props, geoms=None, calc=None, extra_calcs=None):
        from ase.calculators.calculator import all_changes
        if calc is None:
            calc = self.mol.calc
        if geoms is None:
            calc.calculate(self.mol, properties=props, system_changes=all_changes)
            base = {
                k:calc.results[k]
                for k in props
            }
            if extra_calcs is not None:
                updates = extra_calcs(self.mol)
                base.update(updates)
            return base
        else:
            cur_geom = self.mol.positions
            geoms = np.asanyarray(geoms)
            base_shape = geoms.shape[:-2]
            geoms = geoms.reshape((-1,) + cur_geom.shape)
            prop_arrays = {}

            try:
                for i, g in enumerate(geoms):
                    self.mol.positions = g
                    calc.calculate(self.mol, properties=props, system_changes=all_changes)
                    for k in props:
                        res = calc.results[k]
                        if k not in prop_arrays:
                            if hasattr(res, 'shape'):
                                shp = res.shape
                            else:
                                shp = ()
                            prop_arrays[k] = np.empty(
                                (len(geoms),) + shp,
                                dtype=type(res) if not hasattr(res, 'dtype') else res.dtype
                            )
                        prop_arrays[k][i] = res
                    if extra_calcs is not None:
                        updates = extra_calcs(self.mol)
                        for k,res in updates.items():
                            if k not in prop_arrays:
                                prop_arrays[k] = np.empty(
                                    (len(geoms),) + res.shape,
                                    dtype=res.dtype
                                )
                            prop_arrays[k][i] = res
            finally:
                self.mol.positions = cur_geom

            return {
                k:r.reshape(base_shape + r.shape[1:])
                for k,r in prop_arrays.items()
            }

    def calculate_energy(self, geoms=None, order=None, calc=None):
        if calc is None:
            calc = self.mol.calc
        just_eng = order is None
        if just_eng: order = 0
        props = ['energy']
        if order > 0:
            props.append('forces')
        extra_calcs = None
        if order > 1:
            if hasattr(calc, 'get_hessian'):
                extra_calcs = lambda m:{'hessian':calc.get_hessian(m)}
            else:
                raise ValueError("ASE calculators only need to implement forces")
        if order > 2:
            raise ValueError("ASE calculators don't support 3rd derivatives by default")
        res = self.calculate_props(props, geoms=geoms, calc=calc, extra_calcs=extra_calcs)
        if just_eng:
            return res['energy']

        base_ndim = 0 if geoms is None else np.asarray(geoms).ndim - 2
        ncoord = 3 * len(self.masses)

        ret_tup = (res['energy'],)
        if order > 0:
            ret_tup = ret_tup + (
                -res['forces'].reshape(res['forces'].shape[:base_ndim] + (ncoord,)),
            )
        if order > 1:
            ret_tup = ret_tup + (
                res['hessian'].reshape(res['forces'].shape[:base_ndim] + (ncoord, ncoord)),
            )
        return ret_tup


    convergence_criterion = 1e-4
    max_steps = 100
    def optimize_structure(self, geoms=None, calc=None, quiet=True, logfile=None, fmax=None, steps=None, **opts):
        BFGS = ASEInterface.submodule('optimize').BFGS

        if logfile is None:
            if quiet:
                logfile = io.StringIO()
            else:
                logfile = sys.stdout

        if calc is None:
            calc = self.mol.calc
        cur_calc = self.mol.calc
        cur_geom = self.mol.positions
        try:
            self.mol.calc = calc
            if geoms is None:
                opt_rea = BFGS(self.mol, logfile=logfile, **opts)
                if fmax is None:
                    fmax = self.convergence_criterion
                if steps is None:
                    steps = self.max_steps
                opt = opt_rea.run(fmax=fmax, steps=steps)
                opt_coords = self.mol.positions
            else:
                cur_geom = self.mol.positions
                geoms = np.asanyarray(geoms)
                base_shape = geoms.shape[:-2]
                geoms = geoms.reshape((-1,) + cur_geom.shape)
                opt = np.empty((len(geoms),), dtype=object)
                opt_coords = np.empty_like(geoms)

                for i, g in enumerate(geoms):
                    self.mol.positions = g
                    opt_rea = BFGS(self.mol, logfile=logfile, **opts)
                    if fmax is None:
                        fmax = self.convergence_criterion
                    if steps is None:
                        steps = self.max_steps
                    opt[i] = opt_rea.run(fmax=fmax, steps=steps)
                    opt_coords[i] = self.mol.positions
                opt = opt.reshape(base_shape)
                opt_coords = opt_coords.reshape(base_shape + opt_coords.shape[1:])
        finally:
            self.mol.calc = cur_calc
            self.mol.positions = cur_geom

        return opt, opt_coords, {}