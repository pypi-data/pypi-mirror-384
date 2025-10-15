'''Check safe migration triggered by secondary neighbor list.

Check that doing an analysis in a situation where this would
trigger a migration does not cause subsequent calculations to
fail (issue #43).
'''

from asap3 import *
from ase.lattice.cubic import FaceCenteredCubic
from asap3.md.velocitydistribution import *
from asap3.analysis import CoordinationNumbers, PTM
from ase.parallel import world
from ase.visualize import view
from asap3.test.pytest_markers import ReportTest, parallel

import pytest

# Important: always at least two cores along x direction
ismaster = world.rank == 0
isparallel = world.size != 1


def make_atoms(layout):
    """Make an atomic system.

    Some vacuum is added, so that shearing it changes the number of
    atoms on the different MPI tasks.
    """
    if ismaster:
        atoms = FaceCenteredCubic('Cu', size=(20,20,20))
        atoms.pbc = False
        atoms.center(vacuum=5.0, axis=0)
        atoms.pbc = True
    else:
        atoms = None
    if world.size > 1:
        atoms = MakeParallelAtoms(atoms, layout)
    atoms.calc = EMT()
    atoms.get_forces()
    return atoms

def deform_atoms(atoms):
    """Shear the atoms."""
    r = atoms.get_positions()
    df =  0.1 * r[:,1]
    r[:,0] += df
    atoms.set_positions(r)
    
@parallel
@pytest.mark.core
def test_safe_nbl(cpulayout):
    atoms = make_atoms(cpulayout)
    e0 = atoms.get_potential_energy()
    deform_atoms(atoms)
    e1 = atoms.get_potential_energy()
    if world.rank == 0:
        print(f"\n\nEnergy of atoms changed from {e0} to {e1}")
    assert np.abs(e0 - e1) > 50.0, 'Energy has changed significantly'

    atoms = make_atoms(cpulayout)
    print(f"A: {len(atoms)} atoms on cpu {world.rank}")
    deform_atoms(atoms)
    #atoms.get_potential_energy()    # Workaround
    CoordinationNumbers(atoms)
    atoms.get_forces()
    e2 = atoms.get_potential_energy()
    print(f"B: {len(atoms)} atoms on cpu {world.rank}")
    ReportTest("Energy after CoordinationNumbers()", e2, e1, 0.001)


    atoms = make_atoms(cpulayout)
    deform_atoms(atoms)
    #atoms.get_potential_energy()    # Workaround
    nbl = atoms.calc.get_neighborlist()
    nbl.check_and_update(atoms)
    atoms.get_forces()
    e2 = atoms.get_potential_energy()
    ReportTest("Energy after borrowed neighborlist update", e2, e1, 0.001)

    atoms = make_atoms(cpulayout)
    deform_atoms(atoms)
    #atoms.get_potential_energy()    # Workaround
    PTM(atoms, cutoff=4.7)
    atoms.get_forces()
    e2 = atoms.get_potential_energy()
    ReportTest("Energy after PTM()", e2, e1, 0.001)


    # The following are not expected to be affected by issue #43.

    for i, nbtype in enumerate((FullNeighborList, NeighborCellLocator)):
        atoms = make_atoms(cpulayout)
        nbl = nbtype(4.8, atoms)
        deform_atoms(atoms)
        #atoms.get_potential_energy()    # Workaround
        nbl.check_and_update(atoms)
        atoms.get_forces()
        e2 = atoms.get_potential_energy()
        ReportTest(f"Energy neighbor list type {i}", e2, e1, 0.001)
