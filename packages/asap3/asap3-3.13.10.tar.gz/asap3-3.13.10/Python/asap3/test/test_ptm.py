"""
Tests that polyhedral template matching works on the simplest possible system.
"""

from ase.lattice.cubic import FaceCenteredCubic, BodyCenteredCubic
from ase.lattice.hexagonal import HexagonalClosedPacked
from ase.build import bulk
from asap3.analysis import PTM
from asap3 import MakeParallelAtoms
from asap3.mpi import world
import numpy as np
from asap3.test.pytest_markers import ReportTest

import pytest



def distribute(atoms, layout):
    if world.rank != 0:
        atoms = None
    if world.size > 1:
        atoms = MakeParallelAtoms(atoms, layout)
    return atoms

def mysum(x):
    """Sum arrays across processors, taking into account that the length may vary.

    No array is longer than 10, so we just extend them all.
    """
    data = np.zeros(10, x.dtype)
    data[:len(x)] = x
    world.sum(data)
    return data

@pytest.mark.core
@pytest.mark.skipif(world.size not in (1, 2, 4, 8), reason='Number of cores must be 1,2,4 or 8')
def test_ptm(cpulayout):
    atoms = distribute(FaceCenteredCubic("Cu", size=(14,14,14), pbc=False), cpulayout)

    data = PTM(atoms, rmsd_max=0.1, calculate_strains=True)
    print("DONE")
    cnt = np.bincount(data['structure'])
    cnt = mysum(cnt)
    print(cnt)
    print(data['info'])

    ReportTest("Number of FCC atoms", cnt[1], 13*13*13*4, 0)
    ReportTest("Number of non-classified atoms", cnt[0], atoms.get_global_number_of_atoms() - 13*13*13*4, 0)

    data = PTM(atoms, rmsd_max=0.1, calculate_strains=True, quick=True)
    cnt = np.bincount(data['structure'])
    cnt = mysum(cnt)
    print(cnt)
    print(data['info'])

    ReportTest("Number of FCC atoms", cnt[1], 13*13*13*4, 0)
    ReportTest("Number of non-classified atoms", cnt[0], atoms.get_global_number_of_atoms() - 13*13*13*4, 0)

    data = PTM(atoms, rmsd_max=0.1, target_structures=('fcc', 'hcp'))
    cnt = np.bincount(data['structure'])
    cnt = mysum(cnt)
    print(cnt)
    print(data['info'])

    ReportTest("Number of FCC atoms", cnt[1], 13*13*13*4, 0)
    ReportTest("Number of non-classified atoms", cnt[0], atoms.get_global_number_of_atoms() - 13*13*13*4, 0)

    atoms = distribute(BodyCenteredCubic("Fe", size=(14,14,14), pbc=(True,True,False)), cpulayout)
    data = PTM(atoms, rmsd_max=0.001, cutoff=8.0)
    cnt = np.bincount(data['structure'])
    cnt = mysum(cnt)
    print(cnt)
    print(data['info'])

    ReportTest("Number of BCC atoms", cnt[3], 14*14*12*2, 0)
    ReportTest("Number of non-classified atoms", cnt[0], atoms.get_global_number_of_atoms() - 14*14*12*2, 0)

    atoms = distribute(HexagonalClosedPacked("Mg", size=(14,14,14), pbc=(True,True,False)), cpulayout)
    cutoff = atoms.get_cell()[0,0] / 4 / np.sqrt(3) * 0.95
    print("Cutoff", cutoff)
    data = PTM(atoms, rmsd_max=0.01, cutoff=cutoff)  # Need a slightly larger rmsd as c/a deviates from ideal.
    cnt = np.bincount(data['structure'])
    cnt = mysum(cnt)
    print(cnt)
    print(data['info'])

    ReportTest("Number of HCP atoms", cnt[2], 14*14*13*2, 0)
    ReportTest("Number of non-classified atoms", cnt[0], atoms.get_global_number_of_atoms() - 14*14*13*2, 0)
    #atoms.set_tags(data['structure'])
    #view(atoms)

    atoms = bulk("Mg", orthorhombic=True)
    atoms = atoms.repeat((14,14,14))
    atoms.set_pbc((True, True, False))
    atoms = distribute(atoms, cpulayout)
    data = PTM(atoms, rmsd_max=0.01)  # Need a slightly larger rmsd as c/a deviates from ideal.
    cnt = np.bincount(data['structure'])
    cnt = mysum(cnt)
    print(cnt)
    print(data['info'])

    ReportTest("Number of HCP atoms", cnt[2], 14*14*13*4, 0)
    ReportTest("Number of non-classified atoms", cnt[0], atoms.get_global_number_of_atoms() - 14*14*13*4, 0)

    # Make a combined system

    atoms = bulk("Mg", orthorhombic=True)
    atoms = atoms.repeat((14,8,14))

    atoms2 = bulk("Fe", orthorhombic=True).repeat((6,6,6))
    uc1 = atoms.get_cell()
    uc2 = atoms2.get_cell()
    factor1 = uc1[0,0] / uc2[0,0]
    factor2 = uc1[1,1] / uc2[1,1]
    uc2 = uc2 * np.array((factor1, factor2, 0.5*(factor1+factor2)))
    atoms2.set_cell(uc2, scale_atoms=True)
    # Combine unit cell, stack BCC atoms on top of HCP atoms.
    uc3 = np.array(uc1)
    dz = uc3[2,2]
    uc3[2,2] += uc2[2,2]
    atoms.set_cell(uc3, scale_atoms=False)
    atoms2.set_positions(atoms2.get_positions() + np.array((0.1,0.1,dz))[np.newaxis,:])
    atoms.extend(atoms2)
    atoms = distribute(atoms, cpulayout)

    data = PTM(atoms, rmsd_max=0.005)
    cnt = np.bincount(data['structure'])
    cnt = mysum(cnt)
    print(cnt)
    print(data['info'])

    ReportTest("Number of HCP atoms", cnt[2], 14*8*13*4, 0)
    ReportTest("Number of BCC atoms", cnt[3], 6*6*4*2, 0)
    ReportTest("Number of FCC atoms", cnt[1], 0, 0)
    ReportTest("All classes of atoms", cnt[:4].sum(), atoms.get_global_number_of_atoms(), 0)
