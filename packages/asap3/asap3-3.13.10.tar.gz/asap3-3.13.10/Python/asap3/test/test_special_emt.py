"""Usage: python SpecialEMT.py [init]

Used to test if the EMT potential still produces the same energies,
forces and stresses as it used to.  It tests all elements with the
standard EMT parameters, including alloys, and also the special
parameters for Ruthenium and for CuMg and CuZr metallic glasses.

This has some overlap with test_potentials.py
"""


from asap3 import EMT, EMThcpParameters, EMTMetalGlassParameters
import pickle
from ase.lattice.cubic import FaceCenteredCubic
from ase.lattice.hexagonal import HexagonalClosedPacked
from ase.lattice.compounds import B2
from asap3.test.pytest_markers import ReportTest, serial
import numpy as np

import pytest

@pytest.fixture
def data(datadir):
    datafile = datadir / "SpecialEMT.pickle"
    return pickle.load(open(datafile, "rb"), encoding='latin1')

@pytest.fixture
def elements():
    return ["Al", "Ni", "Cu", "Pd", "Ag", "Pt", "Au"]

def check(a, key, data):
    print("Testing", key)
    expected_n = data[key+"_n"]
    expected_e = data[key+"_e"]
    expected_f = data[key+"_f"]
    e = a.get_potential_energies()
    f = a.get_forces().ravel()
    ReportTest(f"Number of atoms ({key})", len(a), expected_n, 0)
    ReportTest(f"Energies ({key})", max(np.fabs(e-expected_e)), 0.0, 1e-8)
    ReportTest(f"Forces ({key})", max(np.fabs(f-expected_f)), 0.0, 1e-8)

@serial
def test_ordinary_emt(elements, data):
    print("Checking single elements")
    for e in elements:
        atoms = FaceCenteredCubic(size=(4,4,4), symbol=e, pbc=False)
        atoms.calc = EMT()
        check(atoms, e, data)

@serial
@pytest.mark.core
def test_b2_alloys(elements, data):
    print("Checking B2 alloys")
    for i in range(1, len(elements)):
        e1 = elements[i]
        e2 = elements[i-1]
        atoms = B2(size=(4,4,4), symbol=(e1,e2), latticeconstant=3.5, pbc=False)
        atoms.calc = EMT()
        check(atoms, e1+e2, data)

@serial
@pytest.mark.core
def test_ruthenium(data):
    print("Checking Ruthenium")
    atoms = HexagonalClosedPacked(directions=[[1,0,-1,0],[0,1,-1,0],[0,0,0,1]],
                                size=(4,4,4), symbol="Ru", pbc=False)
    atoms.calc = EMT(EMThcpParameters())
    check(atoms, "Ru", data)

@serial
@pytest.mark.core
def test_metal_glass(data):
    print("Checking metallic glasses")
    for e1, e2 in (("Cu", "Mg"), ("Cu", "Zr")):
        atoms = B2(size=(4,4,4), symbol=(e1,e2), latticeconstant=3.5, pbc=False)
        atoms.calc = EMT(EMTMetalGlassParameters())
        check(atoms, e1+e2, data)

    
