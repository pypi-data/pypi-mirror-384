'''Test that forces sum to zero on inner atoms in 1D chain.

... also in parallel simulations.
'''
from asap3 import *
from asap3.mpi import world
from ase.visualize import view
import numpy as np
import time
import os
import sys
from asap3.test.pytest_markers import ReportTest, parallel

import pytest

@pytest.mark.core
@pytest.mark.skipif(world.size > 3, reason='Runs on at most 3 cpus')
def test_force_1D():
    N = 20
    d = 3.0
    w = 10.0

    cpulayout = (world.size, 1, 1)
    isparallel = world.size > 1
    ismaster = world.rank == 0

    positions = np.zeros((N, 3))
    positions[:,0] = d * np.arange(N)
    if ismaster:
        atoms = Atoms("Cu%i" % (N,), positions=positions, cell=(N*d, w, w),
                      pbc=False)
        atoms.center()
    else:
        atoms = None
    if isparallel:
        atoms = MakeParallelAtoms(atoms, cpulayout)
        id = atoms.get_ids()
    else:
        id = np.arange(N)
    #view(atoms)
    
    atoms.calc = EMT()
    f = atoms.get_forces()
    x = atoms.get_positions()[:,0]
    # time.sleep(world.rank)
    for i in range(len(atoms)):
        print(world.rank, x[i], f[i])
        
    # Now running actual tests - these are different on the two processors, but that should
    # not be a problem
    for i in range(len(f)):
        if id[i] > 1 and id[i] < N - 2:
            ftot = (f[i] * f[i]).sum()
            ReportTest("Force on atom %i" % (id[i],), ftot, 0.0, 1e-13)
    world.barrier()        
