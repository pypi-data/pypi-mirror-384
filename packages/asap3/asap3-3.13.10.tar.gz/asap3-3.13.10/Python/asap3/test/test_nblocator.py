from asap3 import EMT, NeighborList, NeighborCellLocator, Atoms
from ase.lattice.cubic import FaceCenteredCubic
import ase.data
from asap3.test.pytest_markers import ReportTest, serial
import numpy as np

import pytest


def CheckLists(nblist, nblist2, name, natoms, count=None):
    "Run the tests on a half and a full neighbor list."
    print("Running tests on", name)
    print(f"Testing {name}: Lengths of lists.")
    if count:
        sum = 0
        for lst in nblist:
            sum += len(lst)
        ReportTest("Absolute length of list", sum, count * natoms, 0)

    sum1 = sum2 = 0
    for nb in enumerate(nblist):
        sum1 += len(nb)
    for nb in enumerate(nblist2):
        sum2 += len(nb)
        
    ReportTest("Equal total length of lists", sum2, sum1, 0)
    
    print(f"Testing {name}: List 1 atoms on list 2.")
    for i, nb in enumerate(nblist):
        for jj in nb:
            j = int(jj)
            assert (j in nblist2[i]) != (i in nblist2[j]), f'Atom {j} on list {i} (forward)'
    
    print(f"Testing {name}: List 2 atoms on list 1.")
    for i, nb in enumerate(nblist2):
        for jj in nb:
            j = int(jj)
            assert (j in nblist[i]) != (i in nblist[j]), f'Atom {j} on list {i} (reverse)'


@pytest.mark.slow
@serial
def test_cellneighborlocator():
    element = "Cu"
    latconst = ase.data.reference_states[ase.data.atomic_numbers[element]]['a']

    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,1],[0,0,1]], size=(9,7,5),
                            symbol=element, debug=0, pbc=(0,0,0))
    print("Symmetry:", atoms.get_pbc())
    atoms.calc = EMT()
    epot = atoms.get_potential_energy()

    nblist1 = NeighborList(latconst * 0.5 * (1/np.sqrt(2) + 1), atoms, 0.0)
    nblist2 = NeighborCellLocator(latconst * 0.5 * (1/np.sqrt(2) + 1), Atoms(atoms), 0.0)
    CheckLists(nblist1, nblist2, "nearest-neigbor lists (free)", len(atoms))

    atoms = Atoms(atoms, pbc=(1,1,1))
    print("Symmetry:", atoms.get_pbc())

    nblist1 = NeighborList(latconst * 0.5 * (1/np.sqrt(2) + 1), atoms, 0.0)
    nblist2 = NeighborCellLocator(latconst * 0.5 * (1/np.sqrt(2) + 1), Atoms(atoms), 0.0)
    CheckLists(nblist1, nblist2, "nearest-neigbor lists (periodic)", len(atoms), 6)

    nblist1 = NeighborCellLocator(4.98409, atoms, 0.0)
    nblist2 = NeighborList(4.98409, Atoms(atoms), 0.0)
    CheckLists(nblist1, nblist2, "long neigbor lists (periodic)", len(atoms), 21)

    atoms = Atoms(atoms, pbc=(0,0,0))
    print("Symmetry:", atoms.get_pbc())

    nblist = NeighborCellLocator(4.98409, atoms, 0.0)
    nblist2 = NeighborList(4.98409, Atoms(atoms), 0.0)
    CheckLists(nblist, nblist2, "long neigbor lists (free)", len(atoms))

    atoms1 = Atoms(atoms, pbc=(1,1,1))
    atoms2 = Atoms(atoms, pbc=(1,1,1))
    nblist = NeighborCellLocator(4.98409, atoms1)
    nblist2 = NeighborList(4.98409, atoms2)

    x0 = atoms1.get_positions()[2,0]
    for i in range(30):
        r = atoms1.get_positions()
        r[2,0] += 0.05
        atoms1.set_positions(r)
        print(r[2,0], end=' ')
        r = atoms2.get_positions()
        r[2,0] += 0.05
        print(r[2,0])
        atoms2.set_positions(r)
        nblist.check_and_update(atoms1)
        nblist2.check_and_update(atoms2)
        CheckLists(nblist, nblist2, "Translation step "+str(i), len(atoms))

