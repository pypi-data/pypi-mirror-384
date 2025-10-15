"""Usage: python test_reproducible.py [init]

Used to test if the EMT potential still produces the same energies, forces
and stresses as it used to.

Call it the first time with the "init" argument to generate a data file.

Subsequent calls calculate the same quantities, but compare them with the
database.

This is the very first test introduced in Asap, going all the way back to 
Asap version 1.  The script has been updated to handle changes in syntax,
and the input file has been converted as we moved from Numeric to
numarray to numpy.
"""

import pytest

from numpy import sin, arange
from asap3 import EMT, Atoms
import pickle, os, sys, time

from asap3.test.pytest_markers import serial

@pytest.mark.core
@serial
def test_reproducible(datadir):
    datafile = datadir / "test_reproducible_results.pickle"
    infile = datadir / "test_reproducible_in.pickle"

    with open(infile, 'rb') as inpickle:
       indata = pickle.load(inpickle, encoding='latin1')
    lattice = Atoms(positions=indata['positions'], cell=indata['cell'], symbols=["Cu"]*len(indata['positions']), pbc=True)
    
    print("Number of atoms", len(lattice))
    print(lattice.get_cell())
    # Perturb the positions
    r = lattice.get_positions()
    dr =  0.05 * sin(arange(3*len(lattice)))
    dr.shape = (-1,3)
    r += dr
    lattice.set_positions(r)

    atoms1 = Atoms(lattice)
    atoms1.calc = EMT()

    print("Total energy:", atoms1.get_potential_energy())
    print("Stress:", atoms1.get_stress(include_ideal_gas=True))

    z = lattice.get_atomic_numbers()
    z[0] = z[1] = 47
    lattice.set_atomic_numbers(z)
    atoms2 = Atoms(lattice)
    atoms2.calc = EMT()
    
    with open(datafile, "rb") as datapickle:
        data = pickle.load(datapickle, encoding='latin1')
    Cu = data["Cu"]
    AgCu = data["AgCu"]
    print("*** Checking pure copper ***")
    e = 0
    e = e + evaluate("energies", Cu["energies"], atoms1.get_potential_energies())
    e = e + evaluate("forces", Cu["forces"], atoms1.get_forces())
    e = e + evaluate("stresses", Cu["stresses"], atoms1.get_stresses())
    print("*** Checking silver in copper ***")
    e = e + evaluate("energies", AgCu["energies"], atoms2.get_potential_energies())
    e = e + evaluate("forces", AgCu["forces"], atoms2.get_forces())
    e = e + evaluate("stresses", AgCu["stresses"], atoms2.get_stresses())
    if e == 6:
        print("*** All tests passed ***")
    else:
        raise RuntimeError("*** THERE WERE ERRORS IN SOME TESTS! ***")

def evaluate(text, expected, actual):
    diff = max(abs(expected.flat[:] - actual.flat[:]))
    passed = diff < 1e-10
    assert passed, f"Checking {text}: max error = {diff:g}"
    return passed

    

