from asap3 import EMT, MakeParallelAtoms, BundleTrajectory, units
from asap3.md.verlet import VelocityVerlet
from ase.lattice.cubic import FaceCenteredCubic
from asap3.io.trajectory import *
import sys, os, time
from asap3.mpi import world
from asap3.test.pytest_markers import ReportTest, parallel
import numpy as np

import pytest

ismaster = world.rank == 0
isparallel = world.size != 1
delete = True
precision = 1e-8

def maketraj(atoms, t, nstep):
    e = [atoms.get_potential_energy()]
    print("Shape of force:", atoms.get_forces().shape)
    dyn = VelocityVerlet(atoms, 5*units.fs)
    for i in range(nstep):
        dyn.run(10)
        energy = atoms.get_potential_energy()
        e.append(energy)
        if ismaster:
            print("Energy: ", energy)
        if t is not None:
            t.write()
    return e

def checktraj(t, e, cpus=None):
    i = 0
    for energy in e:
        atoms = t.get_atoms(i, cpus)
        atoms.calc = EMT()
        ReportTest("Checking frame %d / cpus=%s" % (i, str(cpus)),
                   atoms.get_potential_energy(), energy, precision)
        i += 1

@parallel
def test_split_bundletraj(in_tmp_dir, cpulayout):
    'Test writing of BundleTrajectory in "split mode" in parallel simulations.'
    if ismaster:
        initial = FaceCenteredCubic(size=(10,10,10), symbol="Cu", pbc=(1,0,0))
    else:
        initial = None
    if isparallel:
        atoms = MakeParallelAtoms(initial, cpulayout)
    else:
        atoms = initial.copy()
        
    atoms.calc = EMT()
    atoms.set_momenta(np.zeros((len(atoms), 3)))
    print("Writing trajectory")
    traj = BundleTrajectory("traj1.bundle", "w", atoms,
                            split=True, singleprecision=False)
    traj.write()
    energies = maketraj(atoms, traj, 10)
    traj.close()

    if ismaster:
        print("Reading trajectory (serial)")
        traj = BundleTrajectory("traj1.bundle")
        checktraj(traj, energies)

    if isparallel:
        world.barrier()
        print("Reading trajectory (parallel)")
        traj = BundleTrajectory("traj1.bundle")
        checktraj(traj, energies, cpulayout)
        world.barrier()

    print("Repeating simulation")
    atoms = traj.get_atoms(5, cpulayout)
    atoms.calc = EMT()
    energies2 = maketraj(atoms, None, 5)
    if ismaster:
        for i in range(5):
            ReportTest("Rerun[%d]" % (i,), energies2[i], energies[i+5], precision)
    traj.close()
    world.barrier()

    print("Appending to trajectory")
    atoms = BundleTrajectory("traj1.bundle").get_atoms(-1, cpulayout)
    atoms.calc = EMT()
    traj = BundleTrajectory("traj1.bundle", "a", atoms)
    energies2 = maketraj(atoms, traj, 5)
    traj.close()
    world.barrier()

    if ismaster:
        print("Reading longer trajectory")
        traj = BundleTrajectory("traj1.bundle")
        checktraj(traj, energies + energies2[1:])

    world.barrier()
    if delete:
        if ismaster:
            print("Deleting trajectory")
        BundleTrajectory.delete_bundle("traj1.bundle")
