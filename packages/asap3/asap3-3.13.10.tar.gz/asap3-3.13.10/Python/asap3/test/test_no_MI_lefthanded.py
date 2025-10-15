#!/usr/bin/env python
"""
Tests that EMT works with a twisted, left-hand unit cell when
minimimum-image convention is turned off.
"""

from asap3 import EMT
from asap3.optimize.mdmin import MDMin
from asap3.analysis import CNA, CoordinationNumbers
from ase.lattice.cubic import FaceCenteredCubic
from asap3.test.pytest_markers import ReportTest, serial
import numpy as np

import pytest


def checkFCC(atoms, n, name):
    print("Test '%s': %d atoms" % (name, len(atoms)))
    ReportTest((f"Number of atoms ({name})"), len(atoms), n, 0)
    atoms.calc = EMT(minimum_image=False)
    cn = CoordinationNumbers(atoms)
    ReportTest((f"Coordination number is 12 ({name})"),
               np.sum(np.equal(cn, 12)), len(atoms), 0)
    cna = CNA(atoms)
    ReportTest((f"CNA says FCC ({name})"),
               np.sum(np.equal(cna, 0)), len(atoms), 0)
    epot = atoms.get_potential_energy()/len(atoms)
    ReportTest((f"Potential energy ({name})"), epot, 0.0, 1e-3)

@serial
@pytest.mark.core
def test_no_MI_lefthanded():
    directions = [[5,1,3], [3,5,1], [2,2,-7]]
    a = FaceCenteredCubic(directions=directions, size=(2,2,2), symbol="Cu")
    print(a.get_cell())
    checkFCC(a, 5568, "FCC")

