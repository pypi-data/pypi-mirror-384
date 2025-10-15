"""Test periodic boundary conditions."""

from asap3 import *
from asap3.analysis.localstructure import RestrictedCNA, CoordinationNumbers
from asap3.mpi import world
from ase.build import bulk
import numpy as np
from asap3.test.pytest_markers import ReportTest, parallel

import pytest


ismaster = world.rank == 0
isparallel = world.size != 1

pbc_list = [(True, True, False),
                (False, True, True),
                (True, False, True)]

def makesystem():
    atoms = bulk('Cu')
    atoms = atoms.repeat((25, 25, 25))
    return atoms

@parallel
@pytest.mark.core
def test_par_pbc(cpulayout):
    seratoms = makesystem()
    seratoms.set_pbc(pbc_list[-1])
    seratoms.calc = EMT()
    old_energy = seratoms.get_potential_energy()

    for pbc in pbc_list:
        # Make parallel nb list
        if ismaster:
            atoms = makesystem()
            atoms.set_pbc(pbc)
        else:
            atoms = None
        if isparallel:
            atoms = MakeParallelAtoms(atoms, cpulayout)
        natoms = atoms.get_global_number_of_atoms()
        atoms.calc = EMT()
        energy = atoms.get_potential_energy()
        ReportTest(f"PBC={str(pbc)}", energy, old_energy, 1e-6)

