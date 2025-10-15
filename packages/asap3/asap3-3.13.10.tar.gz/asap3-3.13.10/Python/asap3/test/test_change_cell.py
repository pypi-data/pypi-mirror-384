# Checks for Ticket #11

from asap3 import *
from ase.lattice.cubic import FaceCenteredCubic

from asap3.test.pytest_markers import ReportTest, serial
import pytest

@serial
def test_not_wrapping():
    'Test that atoms are not wrapped when unit cell is set.'
    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(6,6,6),
                            symbol="Cu")
    atoms.calc = EMT()
    r = atoms.get_positions()
    print("Orig position", r[-1])

    uc = atoms.get_cell()
    print(uc)
    r[-1] = 1.51*uc[2]
    atoms.set_positions(r)
    print(atoms.get_potential_energy())

    p1 = atoms.get_positions()[-1]
    print("p1:", p1)

    atoms.set_cell(uc, scale_atoms=True)
    print(atoms.get_potential_energy())
    p2  = atoms.get_positions()[-1]
    print("p2:", p2)

    atoms.set_cell(uc, scale_atoms=False)
    print(atoms.get_potential_energy())
    p3 = atoms.get_positions()[-1]
    print("p3:", p3)

    ReportTest("p2 equals p1", p2[2], p1[2], 1e-6)
    ReportTest("p3 equals p1", p3[2], p1[2], 1e-6)


@serial
@pytest.mark.parametrize('pbc', (True, False, (1,1,0)), ids=('periodic', 'free', 'mixed'))
@pytest.mark.parametrize('scale', (True, False))
def test_recalc_scaling(pbc, scale):
    "Test for correct energy calculations with varying unit cell."

    print(f"Running test with pbc={pbc} and scale_atoms={scale}")
    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                                size=(6,6,6), symbol="Cu", pbc=pbc)
    atoms.calc = EMT()
    uc = atoms.get_cell()
    atoms.get_potential_energy()
    for factor in (1.0, 1.01, 1.02, 1.1, 1.5, 1.49, 1.4, 1.4, 1.0, 0.9):
        atoms.set_cell(uc * factor, scale_atoms=scale)
        f = atoms.get_forces()
        e = atoms.get_potential_energy()
        atoms2 = Atoms(atoms)
        atoms2.calc = EMT()
        e2 = atoms2.get_potential_energy()
        f2 = atoms2.get_forces()
        name = "(factor = {:.3f}  PBC = {}  scale_atoms = {})".format(factor,
                                                                pbc, scale)
        ReportTest("Energy "+name, e, e2, 1e-6)
        maxf = max(abs(f.flat[:] - f2.flat[:]))
        ReportTest("Forces "+name, maxf, 0.0, 1e-6)
