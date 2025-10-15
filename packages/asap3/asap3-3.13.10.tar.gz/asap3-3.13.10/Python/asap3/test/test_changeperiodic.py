from asap3 import EMT
from ase.lattice.cubic import FaceCenteredCubic
import numpy as np
from asap3.test.pytest_markers import ReportTest, serial
import pytest



@serial
def test_changeperiodic():

    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(6,6,6),
                            symbol="Cu", pbc=(1,1,0))
    atoms.calc = EMT()
    ecorrect = atoms.get_potential_energy()

    atoms2 = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(6,6,6),
                            symbol="Cu", pbc=(0,0,0))
    atoms2.calc = EMT()
    atoms2.get_potential_energy()
    atoms2.set_pbc((1,1,0))
    e1= atoms2.get_potential_energy()
    ReportTest("PBC (0,0,0) -> (1,1,0) correct", e1, ecorrect, 0.001)

    atoms3 = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(6,6,6),
                            symbol="Cu", pbc=(1,1,1))
    atoms3.calc = EMT()
    atoms3.get_potential_energy()
    atoms3.set_pbc((1,1,0))
    e3= atoms3.get_potential_energy()
    ReportTest("PBC (0,0,0) -> (1,1,0) correct", e3, ecorrect, 0.001)




    atoms.set_pbc((0,1,0))
    atoms.get_potential_energy()
    atoms.set_pbc((1,1,0))
    e2 = atoms.get_potential_energy()
    ReportTest("e2 correct", e2, ecorrect, 0.001)

    print("Setting pbc")
    atoms.set_pbc((0,1,0))
    print("Calculating energy")
    dummy =  atoms.get_potential_energy()
    assert np.fabs(dummy - ecorrect) > 1.0
    atoms.set_pbc((1,1,0))
    e3 = atoms.get_potential_energy()
    ReportTest("e3 correct", e3, ecorrect, 0.001)

    atoms.set_pbc((1,1,0))
    atoms.set_positions(atoms.get_positions())
    e4 = atoms.get_potential_energy()
    ReportTest("e4 correct", e4, ecorrect, 0.001)

    print("Repeating tests with an atom outside the unit cell.")
    for coordinate in (0,1,2):
        print("Using coordinate number", coordinate)

        atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(6,6,6),
                                symbol="Cu", pbc=(1,1,0))
        r = atoms.get_positions()
        uc = atoms.get_cell()
        r[-1,coordinate] = uc[coordinate,coordinate] * 1.51
        atoms.set_positions(r)
        atoms.calc = EMT()
        ecorrect = atoms.get_potential_energy()

        atoms.set_pbc((0,1,0))
        atoms.set_pbc((1,1,0))
        e2 = atoms.get_potential_energy()
        ReportTest("e2 correct", e2, ecorrect, 0.001)

        atoms.set_pbc((0,1,0))
        dummy =  atoms.get_potential_energy()
        assert np.fabs(dummy - ecorrect) > 1.0
        atoms.set_pbc((1,1,0))
        e3 = atoms.get_potential_energy()
        ReportTest("e3 correct", e3, ecorrect, 0.001)

        atoms.set_pbc((1,1,0))
        atoms.set_positions(atoms.get_positions())
        e4 = atoms.get_potential_energy()
        ReportTest("e4 correct", e4, ecorrect, 0.001)
