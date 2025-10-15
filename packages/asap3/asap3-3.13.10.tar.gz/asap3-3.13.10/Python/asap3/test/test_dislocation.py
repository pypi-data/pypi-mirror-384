#!/usr/bin/env python

from asap3 import Atoms, EMT
from ase.lattice.cubic import FaceCenteredCubic
from asap3.setup.dislocation import Dislocation
from asap3.analysis import CNA
# from asap3.visualize.primiplotter import *
from asap3.test.pytest_markers import ReportTest, serial
import numpy as np

import pytest


@serial
def test_make_dislocation():
    splitting = 5
    #size = (50, 88, 35)
    size = (30, 25, 7)

    Gold = "Au"
    slab = FaceCenteredCubic(directions=((1,1,-2), (-1,1,0), (1,1,1)),
                            size=size, symbol=Gold)
    basis = slab.get_cell()
    print(basis)
    print("Number of atoms:", len(slab))

    center = 0.5 * np.array([basis[0,0], basis[1,1], basis[2,2]]) + np.array([0.1, 0.1, 0.1])
    offset = 0.5 * splitting * slab.miller_to_direction((-1,0,1))
    print(center)

    d1 = Dislocation(center - offset, slab.miller_to_direction((-1,-1,0)),
                    slab.miller_to_direction((-2,-1,1))/6.0)
    d2 = Dislocation(center + offset, slab.miller_to_direction((1,1,0)),
                    slab.miller_to_direction((1,2,1))/6.0)

    atoms = Atoms(slab)
    (d1+d2).apply_to(atoms)
    del slab

    print("Now running CNA")

    atoms.calc = EMT()
    c = CNA(atoms)
    atoms.set_tags(c)

    expected = [27703, 314, 3483]

    for i in range(3):
        print(i, sum(np.equal(c, i)))
        ReportTest("Number of atoms with CNA class "+str(i), sum(np.equal(c, i)), expected[i], 0)

