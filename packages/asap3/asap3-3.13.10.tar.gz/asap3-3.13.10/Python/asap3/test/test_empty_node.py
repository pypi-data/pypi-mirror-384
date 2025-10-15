"""
Tests that Asap works in parallel simulations even if a process has no atoms.

Name: emptyNode.py

Description: Part of the Asap test suite.  Tests parallelization robustness.

Usage: mpirun -np 4 asap-python emptyNode.py

Expected result: The output should end with 'ALL TESTS SUCCEEDED'.
"""

from ase.build import bulk
from ase.lattice.cubic import FaceCenteredCubic
from asap3 import MakeParallelAtoms, EMT
from asap3.mpi import world
import numpy as np
from ase.visualize import view

from asap3.test.pytest_markers import ReportTest, parallel

import pytest

def makesystem(delta):
    atoms = FaceCenteredCubic("Cu", size=(15,15,15), pbc=False)
    x = atoms.cell[0,0] / 2
    y = atoms.cell[1,1] / 2
    pos = atoms.get_positions()
    keep = np.logical_or(pos[:,0] > x + delta, pos[:,1] > y + delta)
    return atoms[keep]

def distribute(atoms, cpulayout):
    if world.rank != 0:
        atoms = None
    return MakeParallelAtoms(atoms, cpulayout)

def checksystem(origatoms, label, cpulayout):
    origatoms.calc = None
    atoms = distribute(origatoms, cpulayout)
    atoms.suppress_warning_noatoms = True   # Kill a warning on stderr
    print(f"Number of atoms on process {world.rank}: {len(atoms)}")
    atoms.calc = EMT()
    energy_par = atoms.get_potential_energy()

    origatoms.calc = EMT()
    energy_ser = origatoms.get_potential_energy()

    ReportTest(label+": Energy match", energy_par, energy_ser, 1e-6)

@pytest.mark.skipif(world.size != 4, reason='Requires 4 MPI tasks')
def test_empty_nodes(cpulayout):
    a = makesystem(10.0)
    checksystem(a, "Large missing part on master", cpulayout)

    a.rotate(90, 'z', center='COU')
    checksystem(a, "Large missing part on slave", cpulayout)

    a = makesystem(1.0)
    checksystem(a, "Small missing part on master", cpulayout)

    a.rotate(90, 'z', center='COU')
    checksystem(a, "Small missing part on slave", cpulayout)
