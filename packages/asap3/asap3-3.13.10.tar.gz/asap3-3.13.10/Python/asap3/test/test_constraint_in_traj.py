from asap3 import *
from asap3.constraints import FixAtoms
from ase.lattice.cubic import FaceCenteredCubic
from ase.io import read, write
from asap3.io import Trajectory
from asap3.test.pytest_markers import ReportTest, serial

import os
import numpy as np

import pytest

usemask = True

@serial
@pytest.mark.parametrize('usemask', (True, False))
def test_constr_in_traj(usemask, in_tmp_dir):
    fn = "testconstraint"
    atoms = FaceCenteredCubic(symbol='Cu', size=(3,3,3))
    if usemask:
        c = FixAtoms(mask=np.arange(len(atoms))<3)
    else:
        c = FixAtoms(indices=(2,3))
    atoms.set_constraint(c)
    print(c)

    traj = Trajectory(fn+'.trj', "w", atoms)
    traj.write()
    traj.close()
    del traj

    traj = BundleTrajectory(fn+'.bundle', "w", atoms)
    traj.write()
    traj.close()
    del traj

    traj = Trajectory(fn+'.traj', "w", atoms)
    traj.write()
    traj.close()
    del traj

    traj2 = Trajectory(fn+'.trj')
    atoms2 = traj2[-1]
    c2 = atoms2.constraints[0]

    print("*** Trajectory")
    print("Original class:", c.__class__)
    print("New class:", c2.__class__)
    assert c.__class__ is c2.__class__

    traj2 = read(fn+'.bundle')
    c2 = atoms2.constraints[0]

    print("*** BundleTrajectory")
    print("Original class:", c.__class__)
    print("New class:", c2.__class__)
    assert c.__class__ is c2.__class__

    print("*** Cleaning up")
    os.unlink(fn+'.traj')
    os.unlink(fn+'.trj')
    BundleTrajectory.delete_bundle(fn+'.bundle')

    print("Test passed.")

