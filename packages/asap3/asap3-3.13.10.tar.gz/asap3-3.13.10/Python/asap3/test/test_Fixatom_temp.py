from asap3 import *
from asap3.md.verlet import VelocityVerlet
from ase.lattice.cubic import FaceCenteredCubic
from asap3.io.trajectory import *
from ase.parallel import world
from asap3.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from asap3.constraints import FixAtoms
from asap3.test.pytest_markers import ReportTest
import numpy as np

import pytest


def test_Fixatoms_temperature(cpulayout):
    ismaster = world.rank == 0
    isparallel = world.size != 1

    temp = 3000  # K

    if ismaster:
        initial = FaceCenteredCubic(size=(10,10,10), symbol="Cu", pbc=(1,0,0))
    else:
        initial = None
    if isparallel:
        atoms = MakeParallelAtoms(initial, cpulayout)
        atoms.set_constraint(FixAtoms(mask=(atoms.get_ids() < atoms.get_global_number_of_atoms()/2)))
    else:
        atoms = initial.copy()
        atoms.set_constraint(FixAtoms(indices=range(len(atoms)//2)))

    atoms.calc = EMT()
    MaxwellBoltzmannDistribution(atoms, temperature_K=temp)
    Stationary(atoms)

    dyn = Langevin(atoms, 3*units.fs, temperature_K=temp, friction=0.02)
    dyn.run(1000)

    temps = [atoms.get_temperature()]
    for i in range(10):
        dyn.run(10)
        temps.append(atoms.get_temperature())
        
    avgtemp = np.mean(temps)
    print(f"Average temperature T={avgtemp:.1f}K  (task {world.rank})")
    c = atoms.constraints[0]
    print(f"Removed DOF: {c.get_removed_dof(atoms)}   (task {world.rank})")
    ReportTest("Mean temperature:", avgtemp, temp, 200)
