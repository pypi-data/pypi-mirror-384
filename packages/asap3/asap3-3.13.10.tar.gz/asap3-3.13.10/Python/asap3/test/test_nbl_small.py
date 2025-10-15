from asap3 import EMT, FullNeighborList
from ase.lattice.cubic import FaceCenteredCubic
import numpy as np
import ase.data
from asap3.test.pytest_markers import serial

import pytest


element = "Cu"
latconst = ase.data.reference_states[ase.data.atomic_numbers[element]]['a']
nndist = latconst / np.sqrt(2)

sizes = [(3,3,3), (2, 2, 2), (1, 1, 1)]
withpotential = (False, True)

@pytest.mark.core
@serial
@pytest.mark.parametrize('size', sizes)
@pytest.mark.parametrize('usepot', withpotential)
def test_neighborlist_small(size, usepot):
        shells = (1, 2, 3, 4)
        expected = (12, 18, 42, 54)

        print(f'Size: {size}  -  use potential: {usepot}')
        atoms = FaceCenteredCubic(
            directions=[[1,0,0],[0,1,1],[0,0,1]], 
            size=size,
            symbol=element
        )
        
        if usepot:
            atoms.calc = EMT()
            epot = atoms.get_potential_energy()

        for shell, expect in zip(shells, expected):
            cutoff = nndist * (np.sqrt(shell) + np.sqrt(shell + 1)) / 2
            nbl = FullNeighborList(cutoff, atoms, 0.0)
            allreal = True
            assert len(nbl) == len(atoms)
            # Test short neighbor lists
            for i, lst in enumerate(nbl):
                # print(f'Atom {i} has {len(lst)} neighbors: {str(lst)}')
                assert len(lst) == expect
                allreal *= max(lst) < len(atoms)
            print(f'Test passed for shell number {shell}  (all neighbors real: {allreal})')
            assert allreal

            # Test full interface
            allreal = True
            for i in range(len(atoms)):
                indices, vectors, dist2 = nbl.get_neighbors(i)
                allreal *= max(indices) < len(atoms)
                assert vectors.shape == (expect, 3)
                sumvec = vectors.sum(axis=0)
                assert sumvec.shape == (3,)
                assert np.isclose(sumvec, 0, atol=1e-8).all()
                # Convert dist2 to shell number
                shnum = dist2 / nndist**2
                shnum_int = np.round(shnum)
                assert np.isclose(shnum, shnum_int, atol=1e-6).all()
                assert shnum_int.max() == shell
            print(f'Test 2 passed for shell number {shell}  (all neighbors real: {allreal})')
            assert allreal

        if size == (1, 1, 1) and usepot:
            # Bonus test: We have an object with and EMT
            # potential attached, and minimum image convention disabled.

            nblist = atoms.calc.get_neighborlist()
            print("Length of EMT neighbor list:", len(nblist))
            for i, nbl in enumerate(nblist):
                print(f'Atom {i} has {len(nbl)} neighbors.')
                assert max(nbl) < len(atoms)
