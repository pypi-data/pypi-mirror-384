"Main neighborlist test - tests consistency between half and full lists."
from asap3 import Atoms, EMT, NeighborList, FullNeighborList
from ase.lattice.cubic import FaceCenteredCubic
import ase.data
from asap3.test.pytest_markers import ReportTest, serial
from numpy import sqrt

import pytest


def TestLists(nblist, fnb, name, natoms, count=None):
    "Run the tests on a half and a full neighbor list."
    print("")
    if count:
        print(f"Testing {name}: Length of lists")
        sum = 0
        for lst in nblist:
            sum += len(lst)
        ReportTest("   Half list", sum, count * natoms, 0)

        lfnb = list(map(len, fnb))
        assert len(lfnb) == natoms
        ReportTest("   Shortest full list", min(lfnb), 2*count, 0)
        ReportTest("   Longest full list", max(lfnb), 2*count, 0)

    print ("Testing %s: Symmetry of full list; full list atoms on half-lists."
           % (name,))
    for i, nb in enumerate(fnb):
        for jj in nb:
            j = int(jj)
            assert i in fnb[j], f'Atom {j} on list {i}'
            assert (i in nblist[j]) != (j in nblist[i]), \
                f'Exactly one of atoms {j} and {i} on half-lists'

    print(f"Testing {name}: Half-list atoms on full list.")
    for i, nb in enumerate(nblist):
        for jj in nb:
            j = int(jj)
            assert j in fnb[i], f'Atom {j} on list {i} (forward)'
            assert i in fnb[j], f'Atom {i} on list {j} (reverse)'


@pytest.mark.core
@serial
def test_neighborlists():
    element = "Cu"
    latconst = ase.data.reference_states[ase.data.atomic_numbers[element]]['a']

    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,1],[0,0,1]], size=(9,7,5),
                            symbol=element, debug=0)
    atoms.calc = EMT(minimum_image=True)
    epot = atoms.get_potential_energy()

    nblist = atoms.calc.get_neighborlist()
    count = {}
    for lst in nblist:
        n = len(lst)
        try:
            count[n] += 1
        except KeyError:
            count[n] = 1
    # print "Histogram:"
    numbers = sorted(count.keys())
    sum = 0
    for i in numbers:
        #print i, count[i]
        sum += i*count[i]

    ReportTest("Number of neighbors (EMT's NB list)", sum, 21*len(atoms), 0)

    nblist = NeighborList(latconst * 0.5 * (1/sqrt(2) + 1), atoms, 0.0)
    #nblist = NeighborCellLocator(latconst * 0.5 * (1/sqrt(2) + 1), atoms, 0.0)
    fnb = FullNeighborList(latconst * 0.5 * (1/sqrt(2) + 1), Atoms(atoms))
    TestLists(nblist, fnb, "nearest-neigbor lists (periodic)", len(atoms), 6)

    ReportTest("Energy unperturbed 1", atoms.get_potential_energy(), epot, 1e-11)
    atoms.set_positions(atoms.get_positions())
    ReportTest("Energy unperturbed 2", atoms.get_potential_energy(), epot, 1e-11)

    nblist = NeighborList(4.98409, atoms, 0.0)
    fnb = FullNeighborList(4.98409, Atoms(atoms))
    TestLists(nblist, fnb, "long neigbor lists (periodic)", len(atoms), 21)

    ReportTest("Energy unperturbed 3", atoms.get_potential_energy(), epot, 1e-11)
    atoms.set_positions(atoms.get_positions())
    ReportTest("Energy unperturbed 4", atoms.get_potential_energy(), epot, 1e-11)

    atoms = Atoms(atoms, pbc=(0,0,0))

    nblist = NeighborList(latconst * 0.5 * (1/sqrt(2) + 1), atoms, 0.0)
    fnb = FullNeighborList(latconst * 0.5 * (1/sqrt(2) + 1), Atoms(atoms))
    TestLists(nblist, fnb, "nearest-neigbor lists (non-periodic)", len(atoms))

    atoms = Atoms(atoms, pbc=(0,1,0))

    nblist = NeighborList(4.98409, atoms, 0.0)
    fnb = FullNeighborList(4.98409, Atoms(atoms))
    TestLists(nblist, fnb, "long neigbor lists (semi-periodic)", len(atoms))
