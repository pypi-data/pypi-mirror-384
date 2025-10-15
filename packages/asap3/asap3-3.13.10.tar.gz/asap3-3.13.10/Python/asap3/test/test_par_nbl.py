"""Test that the parallel neighbor list.

 Checks that the parallel neighbor list returns the same number of
 neighbors as the serial one, both when it originates from a 
 potential and when it is created from Python.
 
 The test really only makes sense in parallel, but can run in serial."""

from asap3 import EMT, MakeParallelAtoms, FullNeighborList
from asap3.analysis.localstructure import RestrictedCNA, CoordinationNumbers
from asap3.mpi import world
from ase.build import bulk
import numpy as np

from asap3.test.pytest_markers import ReportTest, parallel

import pytest

ismaster = world.rank == 0
isparallel = world.size != 1
nbl_cutoff = 4.5

def makesystem(layout):
    atoms = bulk('Cu')
    atoms = atoms.repeat((15, 15, 15))
    if layout:
        atoms = atoms.repeat(layout)
    atoms.set_pbc((True, False, True))
    #atoms.set_pbc((False, True, True))
    del atoms[87]   #Create point defect
    return atoms

@parallel
@pytest.mark.parametrize('usepot', (True, False))
def test_par_neighborlist(usepot, cpulayout):
    # Make serial nb list.
    seratoms = makesystem(cpulayout)
    sernblist = FullNeighborList(nbl_cutoff, seratoms)

    # Make parallel nb list
    if ismaster:
        atoms = makesystem(cpulayout)
    else:
        atoms = None
    if isparallel:
        atoms = MakeParallelAtoms(atoms, cpulayout)
    natoms = atoms.get_global_number_of_atoms()
    if usepot:
        atoms.calc = EMT()
        old_energy = atoms.get_potential_energy()
        print(atoms.calc.get_cutoff())
        print(len(atoms), atoms.get_global_number_of_atoms())
        #assert atoms.get_calculator().get_cutoff() >= nbl_cutoff
    
    print(f"Testing parallel neighbor locator (usepot = {usepot})")
    nblist = FullNeighborList(nbl_cutoff, atoms)
    print("Length of neighbor locator", len(nblist), len(atoms))
    print(nblist[-1])
    if isparallel:
        ids = atoms.get_ids()
    else:
        ids = range(len(atoms))
    maxlen = -1
    minlen = 1e100
    for i in range(len(atoms)):
        l = len(nblist[i])
        l_exp = len(sernblist[ids[i]])
        ReportTest(f"NBlist length (i={i}, id={ids[i]})", 
                   l, l_exp, 0)
        if l > maxlen:
            maxlen = l
        if l < minlen:
            minlen = l
        if l == l_exp:
            snbl = {n for n in sernblist[ids[i]]}
            for nb in nblist[i]:
                if nb < len(atoms):
                    assert ids[nb] in snbl

    print("Neighbor list length:", minlen, '-', maxlen)
    if usepot:
        atoms[1].position += np.array((1e-5,0,0))
        ReportTest("Energy", atoms.get_potential_energy(), old_energy, 1e-4)
 
