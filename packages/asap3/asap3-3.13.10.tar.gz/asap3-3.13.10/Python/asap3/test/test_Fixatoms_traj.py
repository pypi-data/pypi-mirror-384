from asap3 import *
from asap3.md.verlet import VelocityVerlet
from ase.lattice.cubic import FaceCenteredCubic
from asap3.io.trajectory import Trajectory
from ase.parallel import world
from asap3.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from asap3.constraints import FixAtoms
from ase.io import read
import os

import pytest


@pytest.mark.core
def test_Fixatoms_trajectory(cpulayout, in_tmp_dir):

    ismaster = world.rank == 0
    isparallel = world.size != 1

    delete = True
    filename = "fixatoms.traj"

    if ismaster:
        initial = FaceCenteredCubic(size=(10,10,10), symbol="Cu", pbc=(1,0,0))
    else:
        initial = None
    if isparallel:
        atoms = MakeParallelAtoms(initial, cpulayout)
        atoms.set_constraint(FixAtoms(mask=(atoms.get_ids() < 5)))
    else:
        atoms = initial.copy()
        atoms.set_constraint(FixAtoms(indices=range(5)))

    atoms.calc = EMT()
    MaxwellBoltzmannDistribution(atoms, temperature_K=5000)
    Stationary(atoms)

    dyn = VelocityVerlet(atoms, 3*units.fs)
    traj = Trajectory(filename, "w", atoms)
    dyn.attach(traj, interval=10)
    dyn.run(50)

    e = atoms.get_potential_energy()

    atoms2 = read(filename)
    e2 = atoms2.get_potential_energy()

    world.barrier()
    if delete and world.rank == 0:
        os.remove(filename)
        
    world.barrier()
