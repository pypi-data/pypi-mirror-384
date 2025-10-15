from asap3 import EMT
from asap3.analysis import PTM
from ase.lattice.cubic import FaceCenteredCubic
import numpy as np
import ase.data
from asap3.test.pytest_markers import serial

import pytest


@serial
@pytest.mark.core
def test_ptm_small():
    element = "Cu"
    latconst = ase.data.reference_states[ase.data.atomic_numbers[element]]['a']
    nndist = latconst / np.sqrt(2)

    sizes = [(3,3,3), (2, 2, 2), (1, 1, 1)]
    withpotential =  (False, True)
    quicklist = (False, True)

    for size in sizes:
        for usepot in withpotential:
            for quick in quicklist:
                print(f'Size: {size}  -  use potential: {usepot}  -  quick: {quick}.')
                atoms = FaceCenteredCubic(
                    directions=[[1,0,0],[0,1,1],[0,0,1]], 
                    size=size,
                    symbol=element,
                    pbc=True
                )
                
                if usepot:
                    atoms.calc = EMT()
                    epot = atoms.get_potential_energy()

                cutoff = nndist * (1 + np.sqrt(2)) / 2
                ptmdata = PTM(atoms, cutoff=cutoff, rmsd_max=0.1, quick=quick)
                structure = ptmdata['structure']
                assert np.equal(structure, 1).all()


