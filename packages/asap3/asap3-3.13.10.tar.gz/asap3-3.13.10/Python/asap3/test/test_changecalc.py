from asap3 import EMT, Atoms
from ase.lattice.cubic import FaceCenteredCubic
from asap3.test.pytest_markers import ReportTest
from asap3.test.pytest_markers import serial

import pytest

@serial
@pytest.mark.core
def test_changecalculator():
    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                            size=(6,6,6), symbol="Cu")
    atoms.calc = EMT()
    f1 = atoms.get_forces()
    atoms.calc = EMT()
    f2 = atoms.get_forces()
    maxdev = abs(f2 - f1).max()
    print(maxdev)
    ReportTest("Max error 1:", maxdev, 0.0, 1e-6)

    atoms2 = Atoms(atoms)

    f2 = atoms2.get_forces()
    maxdev = abs(f2 - f1).max()
    print(maxdev)
    ReportTest("Max error 2:", maxdev, 0.0, 1e-6)

    f2 = atoms.get_forces()
    maxdev = abs(f2 - f1).max()
    print(maxdev)
    ReportTest("Max error 1:", maxdev, 0.0, 1e-6)

