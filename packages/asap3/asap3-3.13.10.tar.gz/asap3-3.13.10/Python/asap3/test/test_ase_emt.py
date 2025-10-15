"""Check that ASE.calculators.emt and asap3.EMT give the same."""

from ase.lattice.compounds import *
from ase.lattice.cubic import *
from ase.calculators.emt import EMT as EMT_ASE
from asap3 import EMT as EMT_ASAP
from asap3.test.pytest_markers import ReportTest, serial
import numpy as np

import pytest

@serial
@pytest.mark.core
def test_ase_emt():
    elements = ("Ni", "Cu", "Pd", "Ag", "Pt")
    for e1 in elements:
        for e2 in elements:
            atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(1,1,2),
                                    symbol=e1, pbc=(1,0,1), debug=0)
            atoms.calc = EMT_ASE(asap_cutoff=True)
            e_e1_ase = atoms.get_potential_energy()
            atoms.calc = EMT_ASAP()
            e_e1_asap = atoms.get_potential_energy()
            natoms = len(atoms)

            print(f"{e1} energy (ASE) \t{e_e1_ase/natoms:.5f}")
            print(f"{e1} energy (ASAP)\t{e_e1_asap/natoms:.5f}")

            atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(1,1,2),
                                    symbol=e2, pbc=(1,0,1), debug=0)
            atoms.calc = EMT_ASE(asap_cutoff=True)
            e_e2_ase = atoms.get_potential_energy()
            atoms.calc = EMT_ASAP()
            e_e2_asap = atoms.get_potential_energy()

            print(f"{e2} energy (ASE) \t{e_e2_ase/natoms:.5f}")
            print(f"{e2} energy (ASAP)\t{e_e2_asap/natoms:.5f}")

            atoms = L1_2(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(1,1,2),
                        symbol=(e1, e2), latticeconstant=3.95, pbc=(1,0,1), 
                        debug=0)
            
            atoms.calc = EMT_ASE(asap_cutoff=True)
            e_alloy_ase = atoms.get_potential_energy() - (2*e_e1_ase + 6*e_e2_ase)/8
            atoms.calc = EMT_ASAP()
            e_alloy_asap = atoms.get_potential_energy() - (2*e_e1_asap + 6*e_e2_asap)/8

            print(f"Alloy energy (ASE) \t{e_alloy_ase/natoms:.5f}")
            print(f"Alloy energy (ASAP)\t{e_alloy_asap/natoms:.5f}")
            ReportTest(f"{e1}{e2}_3 alloy energy", e_alloy_ase, e_alloy_asap, 1e-4)


