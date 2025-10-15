from asap3 import Atoms, EMT, EMTRasmussenParameters, EMT2013
from asap3.md.verlet import VelocityVerlet
from asap3.EMT2013Parameters import sihb_PtY_parameters
from ase.lattice.cubic import FaceCenteredCubic
from ase.lattice.compounds import L1_2
from ase.data import atomic_masses_legacy
from asap3.test.pytest_markers import serial

import numpy as np

import os
import json

import pytest

pytestmark = [pytest.mark.core, serial]

@pytest.fixture
def potResults(datadir):
    with open(datadir / 'potResults.json', 'rt') as resfile:
        return json.load(resfile)
    
@pytest.fixture
def copper():
    return FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], 
                             size=(15,15,15), symbol="Cu",
                             pbc=(1,0,1), debug=0)

@pytest.fixture
def cu_au_3():
    return L1_2(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(15,15,15),
                symbol=("Cu", "Au"), latticeconstant=3.95, pbc=(1,0,1), 
                debug=0)

@pytest.fixture
def platinum():
    return FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                             size=(15,15,15), symbol="Pt", pbc=(1,0,1), 
                             debug=0)

@pytest.fixture
def yttrium():
    return FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], 
                             size=(15,15,15), symbol="Y", 
                             latticeconstant=4.97,
                             pbc=(1,0,1), debug=0)

@pytest.fixture
def pt_3_y():
    return L1_2(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(15,15,15),
                symbol=("Y", "Pt"), latticeconstant=4.06, pbc=(1,0,1), 
                debug=0)

def test_EMT_Cu(copper, potResults):
    atoms = Atoms(copper)
    atoms.calc = EMT()
    dotest(atoms, 50, 0.1, "EMT_Cu", potResults)

def test_EMT_Cu_Rasm(copper, potResults):
    atoms = Atoms(copper)
    atoms.calc = EMT(EMTRasmussenParameters())
    dotest(atoms, 50, 0.1, "EMT_Cu_Rasm", potResults)

def test_EMT_CuAu3(cu_au_3, potResults):
    atoms = Atoms(cu_au_3)
    nCu = np.sum(np.equal(atoms.get_atomic_numbers(), 29))
    nAu = np.sum(np.equal(atoms.get_atomic_numbers(), 79))
    assert nCu == 13500 / 4, 'Number of Cu atoms in alloy'
    assert nAu == 3 * 13500 / 4, 'Number of Au atoms in alloy'
    atoms.calc = EMT()
    dotest(atoms, 50, 0.06, "EMT_CuAu3", potResults)

def test_EMT2013_Pt(platinum, potResults):
    atoms = Atoms(platinum)
    atoms.calc = EMT2013(sihb_PtY_parameters)
    dotest(atoms, 50, 0.1, "EMT2013_Pt", potResults)

def test_EMT2013_Y(yttrium, potResults):
    atoms = Atoms(yttrium)
    atoms.calc = EMT2013(sihb_PtY_parameters)
    dotest(atoms, 50, 0.1, "EMT2013_Y", potResults)

def test_EMT2013_Pt3Y(pt_3_y, potResults):
    atoms = Atoms(pt_3_y)
    atoms.calc = EMT2013(sihb_PtY_parameters)
    dotest(atoms, 50, 0.06, "EMT2013_Pt3Y", potResults)

def dotest(atoms, nsteps, ampl, name, potResults):
    assert len(atoms) == 13500, f'Number of atoms ({name})'
    timeunit = 1.018047e-14             # Seconds
    femtosecond = 1e-15 / timeunit      # Femtosecond in atomic units
    atoms.set_masses(atomic_masses_legacy[atoms.numbers])
    print("Potential energy", atoms.get_potential_energy() / len(atoms))
    r = atoms.get_positions()
    r.flat[:] += ampl * np.sin(np.arange(3*len(atoms)))
    atoms.set_positions(r)
    print("Potential energy", atoms.get_potential_energy() / len(atoms))

    print(f"Running Verlet dynamics ({name})")
    dyn = VelocityVerlet(atoms, 2*femtosecond)
    etot1 = (atoms.get_potential_energy() + atoms.get_kinetic_energy())
    dyn.run(nsteps)
    etot2 = (atoms.get_potential_energy() + atoms.get_kinetic_energy())
    assert np.isclose(etot1, etot2, atol=1.0), f"Energy conservation ({name})"
    print(etot1, etot2)

    epot = atoms.get_potential_energies()
    stress = atoms.get_stresses(include_ideal_gas=True)

    print("Testing energies and stresses")
    j = 0
    eres=potResults["e"+name]
    sres=potResults["s"+name]
    for i in range(len(atoms)//100):
        assert np.isclose(epot[i*100], eres[i], atol=1e-8), f'{name} energy {i*100}'
        assert np.isclose(stress[i*100, j], sres[i], atol=1e-8), f'{name} stress {i*100}'
        j = (j + 1) % 6
