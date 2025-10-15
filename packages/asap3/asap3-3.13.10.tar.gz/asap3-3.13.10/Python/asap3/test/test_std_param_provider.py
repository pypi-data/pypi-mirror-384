from asap3 import EMT, EMTStandardParameters
from ase.lattice.cubic import FaceCenteredCubic
from ase.lattice.compounds import B2
import numpy as np
from asap3.test.pytest_markers import ReportTest, serial

import pytest

def check(a1, e):
    a2 = a1.copy()
    a1.calc = EMT(EMTStandardParameters())
    a2.calc = EMT()
    ReportTest(f"Energy ({e})", a2.get_potential_energy(),
               a1.get_potential_energy(), 1e-8)
    f1 = a1.get_forces().ravel()
    f2 = a2.get_forces().ravel()
    ReportTest(f"Forces ({e})", max(np.fabs(f2-f1)), 0.0, 1e-8)

@serial
@pytest.mark.core
def test_standard():
    elements = ["Al", "Ni", "Cu", "Pd", "Ag", "Pt", "Au"]
    print("Comparing Default and Standard parameter providers.")
    for e in elements:
        atoms = FaceCenteredCubic(size=(4,4,4), symbol=e)
        check(atoms, e)
        
    for i in range(1, len(elements)):
        e1 = elements[i]
        e2 = elements[i-1]
        atoms = B2(size=(4,4,4), symbol=(e1,e2), latticeconstant=3.5, pbc=False)
        check(atoms, e1+e2)

        atoms = B2(size=(4,4,4), symbol=(e2,e1), latticeconstant=3.5, pbc=False)
        check(atoms, e2+e1)


