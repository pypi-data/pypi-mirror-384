import numpy as np
from asap3 import EMT
from ase.lattice.cubic import FaceCenteredCubic
from asap3.test.pytest_markers import ReportTest, serial

import pytest

@serial
@pytest.mark.core
def test_largeshear():
    'Test that energy varies smoothly under a large shear.'
    atoms = FaceCenteredCubic(symbol='Cu', size=(4,4,4))
    atoms.calc = EMT()
    uc = atoms.get_cell()
    vals = np.linspace(0, 0.2, 20)

    res = []
    for n,i in enumerate(vals):
        uc[0,2] = i
        atoms.set_cell(uc, scale_atoms=True)
        epot = atoms.get_potential_energy()
        print(n, i, epot)
        res.append(epot)

    poly = np.polyfit(vals, res, 2)
    fits = np.polyval(poly, vals)

    rms = np.sqrt((fits - res) * (fits - res))
    print(rms)
    maxrms = rms.max()
    ReportTest("Worse fit", maxrms, 0.0, 1e-5)



    

