"""
Provides support for chemical toolkits
"""

from .Interface import *

__all__ = [
    "OpenBabelInterface",
    "PybelInterface",
    "RDKitInterface",
    "ASEInterface",
    "OpenChemistryInterface",
    "CCLibInterface"
]

class OpenBabelInterface(ExternalProgramInterface):
    """
    A simple class to support operations that make use of the OpenBabel toolkit (which is installed with anaconda)
    """
    name = 'OpenBabel'
    module = 'openbabel.openbabel'

class PybelInterface(ExternalProgramInterface):
    """
    A simple class to support operations that make use of the OpenBabel toolkit (which is installed with anaconda)
    """
    name = 'Pybel'
    module = 'openbabel.pybel'

class RDKitInterface(ExternalProgramInterface):
    name = 'RDKit'
    module = 'rdkit'

class ASEInterface(ExternalProgramInterface):
    name = 'ASE'
    module = 'ase'

    @classmethod
    def Atoms(cls,
              symbols: list[str] = None,
              positions: list[tuple[float, float, float]] = None,
              numbers: list[int] = None,
              masses: list[float] = None,
              charges: list[float] = None,
              **etc
              ):
        return cls.method('Atoms')(
            symbols=symbols,
            positions=positions,
            numbers=numbers,
            masses=masses,
            charges=charges,
            **etc
        )

class OpenChemistryInterface:
    name = 'OpenChemistry'
    module = 'openchemistry.io'

class PySCFInterface:
    name = 'PySCF'
    module = 'pyscf'

class CCLibInterface:
    name = 'CCLib'
    module = 'cclib'