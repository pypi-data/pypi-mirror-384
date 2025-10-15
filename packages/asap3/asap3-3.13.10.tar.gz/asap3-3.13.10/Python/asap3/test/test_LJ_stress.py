from asap3 import LennardJones
from ase.lattice.compounds import B2
from asap3.test.pytest_markers import ReportTest, serial
import numpy as np

import pytest

@serial
def test_LJ_stress():
    'Test for an old bug where stresses were not always correct in LennardJones.'
    atoms = B2(size=(332,166,5), symbol=('Cu', 'Zr'), latticeconstant=2.7)
    lj = LennardJones((29,40), 0.2 * np.array([0.5, 1.0, 1.0, 0.5]),
                    np.array([1.236, 2.0, 2.0, 2.352]),
                    rCut=2.0 * 2.352)
    atoms.calc = lj

    # If the following line is included, the bug is not seen.
    #atoms.get_potential_energy()
    stress = atoms.get_stress()
    exp_tr = 9.30356046e-02
    for i in range(3):
        ReportTest("Diagonal elements of stress tensor", stress[i], exp_tr, 1e-6)
    for i in range(3,6):
        ReportTest("Off-diagonal elements of stress tensor", stress[i], 0.0, 1e-8)
    
