from asap3 import EMT2013
from asap3.EMT2013Parameters import sihb_PtY_parameters
from ase.build import  bulk 
from asap3.test.pytest_markers import ReportTest, serial

import pytest

def make_Pt():
    return bulk('Pt', 'fcc', orthorhombic=True).repeat((6,6,6))

def make_Y():
        return bulk('Y', 'hcp', orthorhombic=True).repeat((6,6,6))

@serial
def test_EMT2013elements():
    atoms = make_Pt()
    atoms.calc = EMT2013(sihb_PtY_parameters, True)
    e_Pt1 = atoms.get_potential_energy()
    print("Pt (1):", e_Pt1)

    atoms = make_Y()
    atoms.calc = EMT2013(sihb_PtY_parameters, True)
    e_Y1 = atoms.get_potential_energy()
    print("Y (1):", e_Y1)

    calc = EMT2013(sihb_PtY_parameters)

    atoms = make_Pt()
    atoms.calc = calc
    e_Pt2 = atoms.get_potential_energy()
    print("Pt (1):", e_Pt2)

    atoms = make_Y()
    atoms.calc = calc
    e_Y2 = atoms.get_potential_energy()
    print("Y (1):", e_Y2)

    ReportTest("Energy of first element (Pt)", e_Pt2, e_Pt1, 1e-9)
    ReportTest("Energy of second element (Y)", e_Y2, e_Y1, 1e-9)
