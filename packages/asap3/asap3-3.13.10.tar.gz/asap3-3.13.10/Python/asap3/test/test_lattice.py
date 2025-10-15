#!/usr/bin/env python
"""Tests that lattices are set up correctly by Asap

Description: Part of the Asap test suite.  Tests that FCC, BCC and HCP lattices
    are set up correctly.
"""

import sys
from numpy import *
from asap3 import *
from asap3.optimize.mdmin import MDMin
from asap3.analysis import CNA, CoordinationNumbers
from ase.lattice.cubic import *
from ase.lattice.orthorhombic import BodyCenteredOrthorhombic,\
     FaceCenteredOrthorhombic
from ase.lattice.hexagonal import HexagonalClosedPacked
from ase.lattice.triclinic import Triclinic
from ase.lattice.monoclinic import BaseCenteredMonoclinic
from asap3.test.pytest_markers import ReportTest, serial

import pytest

def checkFCC(atoms, n, name):
    print("Test '%s': %d atoms" % (name, len(atoms)))
    ReportTest((f"Number of atoms ({name})"), len(atoms), n, 0)
    atoms.calc = EMT()
    cn = CoordinationNumbers(atoms)
    ReportTest((f"Coordination number is 12 ({name})"),
               sum(equal(cn, 12)), len(atoms), 0)
    cna = CNA(atoms)
    ReportTest((f"CNA says FCC ({name})"),
               sum(equal(cna, 0)), len(atoms), 0)
    epot = atoms.get_potential_energy()/len(atoms)
    ReportTest((f"Potential energy ({name})"), epot, 0.0, 1e-3)

def checkBCC(atoms, n, name):
    print("Test '%s': %d atoms" % (name, len(atoms)))
    ReportTest((f"Number of atoms ({name})"), len(atoms), n, 0)
    cn = CoordinationNumbers(atoms, 2.94)
    ReportTest((f"Coordination number is 8 ({name})"),
               sum(equal(cn, 8)), len(atoms), 0)
    cna = CNA(atoms)
    ReportTest((f"CNA says neither FCC nor HCP ({name})"),
               sum(equal(cna, 2)), len(atoms), 0)

def checkHCP(atoms, n, name):
    print("Test '%s': %d atoms" % (name, len(atoms)))
    ReportTest((f"Number of atoms ({name})"), len(atoms), n, 0)
    atoms.calc = EMT()
    cn = CoordinationNumbers(atoms)
    ReportTest((f"Coordination number is 12 ({name})"),
               sum(equal(cn, 12)), len(atoms), 0)
    cna = CNA(atoms)
    ReportTest((f"CNA says HCP ({name})"),
               sum(equal(cna, 1)), len(atoms), 0)
    epot1 = atoms.get_potential_energy()/len(atoms)
    print("Potential energy:", epot1, "eV/atom")
    r1 = atoms.get_positions()
    dyn = MDMin(atoms, dt=2*units.fs)
    dyn.run(fmax=0.001, steps=50)
    epot2 = atoms.get_potential_energy()/len(atoms)
    ReportTest((f"Change in potential energy ({name})"), epot2-epot1,
               0.0, 1e-6)


@serial
@pytest.mark.core
def test_lattice_fcc():
    a = FaceCenteredCubic(size=(10,10,10), symbol="Cu", pbc=(1,1,1))
    checkFCC(a, 4000, "FCC 1")

    dirs = [[1,5,2], [-3,-1,4]]
    dirs.append(cross(dirs[0], dirs[1]))
    a = FaceCenteredCubic(directions=dirs, size=(2,2,1), symbol="Cu",
                        pbc=(1,1,1))
    checkFCC(a, 1560, "FCC 2")

    directions = [[5,1,3], [3,5,1], [2,2,-7]]
    a = FaceCenteredCubic(directions=directions, size=(2,2,2), symbol="Cu")
    checkFCC(a, 5568, "FCC 4")

    directions = [[5,1,3], [3,5,1], [-2,-2,7]]
    a = FaceCenteredCubic(directions=directions, size=(2,2,2), symbol="Cu")
    checkFCC(a, 5568, "FCC 5")

    a = FaceCenteredCubic(directions=[[1,0,0], [0,1,0], [0,0,1]], size=(10,10,10),
                        symbol=29)
    checkFCC(a, 4000, "FCC 7")

    a = FaceCenteredCubic(directions=[[1,0,0], [0,1,0], [0,0,-1]], size=(10,10,10),
                        symbol="Cu")
    checkFCC(a, 4000, "FCC 8")

    a = FaceCenteredCubic(directions=[[1,0,0], [0,-1,0], [0,0,1]], size=(10,10,10),
                        symbol="Cu")
    checkFCC(a, 4000, "FCC 9")

    a = FaceCenteredCubic(directions=[[-1,0,0], [0,1,0], [0,0,1]], size=(10,10,10),
                        symbol="Cu")
    checkFCC(a, 4000, "FCC 10")

    a = FaceCenteredCubic(directions=[[-1,0,0], [0,-1,0], [0,0,-1]], size=(10,10,10),
                        symbol="Cu")
    checkFCC(a, 4000, "FCC 11")

@serial
@pytest.mark.core
def test_lattice_bcc():
    a = BodyCenteredCubic(directions=[[1,0,0], [0,1,0], [0,0,1]], size=(10,10,10),
                        symbol="Mo")
    checkBCC(a, 2000, "BCC 1")

    a = BodyCenteredCubic(directions=[[8,5,2], [-1,0,4], [20,-34,5]], size=(2,1,1),
                        symbol="Mo")
    checkBCC(a, 12648/2, "BCC 2")

    a = BodyCenteredCubic(directions=[[8,5,3], [-1,1,1], [3, 5, -2]], size=(3,4,3),
                        symbol="Mo")
    checkBCC(a, 75*3*4*3, "BCC 3")

    a = BodyCenteredCubic(directions=[[1,0,0], [0,1,0], [0,0,1]], size=(10,10,10),
                        symbol="Mo")
    checkBCC(a, 2000, "BCC 4")

    a = BodyCenteredCubic(directions=[[-1,0,0], [0,1,0], [0,0,1]], size=(10,10,10),
                        symbol="Mo")
    checkBCC(a, 2000, "BCC 5")

@serial
@pytest.mark.core
def test_lattice_bcorthorhombic():
    a = BodyCenteredOrthorhombic(directions=[[1,0,0], [0,1,0], [0,0,1]],
                                size=(10,10,10),
                                symbol="Mo", latticeconstant=(3.15, 3.15, 3.15))
    checkBCC(a, 2000, "BC Orthorhombic/BCC")

    a = BodyCenteredOrthorhombic(directions=[[1,0,0], [0,1,0], [0,0,1]],
                                size=(10,10,10),
                                symbol="Cu", latticeconstant=(3.61/sqrt(2),
                                                            3.61/sqrt(2), 3.61))
    checkFCC(a, 2000, "BC Orthorhombic/FCC")

@serial
@pytest.mark.core
def test_lattice_fcorthorhombic():
    a = FaceCenteredOrthorhombic(directions=[[1,0,0], [0,1,0], [0,0,1]],
                                size=(10,10,10),
                                symbol="Cu", latticeconstant=(3.61, 3.61, 3.61))
    checkFCC(a, 4000, "FC Orthorhombic/FCC")

@serial
@pytest.mark.core
def test_lattice_triclinic():
    a0 = 3.61 / sqrt(2.0)
    a = Triclinic(directions=[[2,1,0],[-2,3,0],[0,1,4]], size=(3,3,3), symbol="Cu",
                latticeconstant=(a0,a0,a0,60,60,60))
    checkFCC(a, 32*3*3*3, "Triclinic/FCC 1")
                
    a = Triclinic(directions=[[-1,1,1],[1,-1,1],[1,1,-1]], size=(4,4,4), symbol="Cu",
                latticeconstant=(a0,a0,a0,60,60,60))
    checkFCC(a, 4*4*4*4, "Triclinic/FCC 2")

    a = Triclinic(directions=[[2,1,0],[-2,3,0],[0,1,4]], size=(3,3,3), symbol="Cu",
                latticeconstant=(3.61,a0,a0,60,45,45))
    checkFCC(a, 32*3*3*3, "Triclinic/FCC 3")

    a = BaseCenteredMonoclinic(directions=[[2,1,0],[-2,3,0],[0,1,4]], size=(3,3,3),
                            symbol="Cu", latticeconstant=(3.61,3.61,a0,45))
    checkFCC(a, 64*3*3*3, "Monoclinic/FCC")


    a0 = 3.15 * sqrt(3)/2
    a = Triclinic(directions=[[2,1,0],[-2,3,0],[0,1,4]], size=(3,3,3), symbol="Mo",
                latticeconstant=(3.15,3.15,a0,54.736,54.736,90))
    checkBCC(a, 32*3*3*3, "Triclinic/BCC")

@serial
@pytest.mark.core
def test_lattice_hcp():
    a = HexagonalClosedPacked(directions=[[2,-1,-1,0], [0,1,-1,0], [0,0,0,1]],
                            size=(10,5,5),
                            symbol="Cu", 
                            latticeconstant={'a': 3.61/sqrt(2),
                                            'c/a':2*sqrt(2)/sqrt(3)})
    checkHCP(a, 1000, "HCP 1")

