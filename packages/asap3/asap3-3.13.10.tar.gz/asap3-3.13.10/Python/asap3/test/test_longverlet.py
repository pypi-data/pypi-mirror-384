'Test of energy conservation in long VelocityVerlet run.'

from asap3 import EMT, MakeParallelAtoms, VelocityVerlet, Trajectory, MDLogger, units
from ase.lattice.cubic import FaceCenteredCubic
import numpy as np
from asap3.mpi import world
from asap3.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3.test.pytest_markers import ReportTest

import pytest

writetraj = True

@pytest.mark.slow
@pytest.mark.parametrize('boundary', [(1,1,1), (0,1,1)])
def test_longverlet(boundary, cpulayout, in_tmp_dir):
        ismaster = world.rank == 0
        isparallel = world.size != 1
        print ("CPU Layout: %s.  Periodic boundary conditions: %s."
               % (str(cpulayout), str(boundary)))
        if ismaster:
            size = np.array((11, 8, 7))
            if cpulayout:
                size *= cpulayout
            atoms = FaceCenteredCubic(size=size, symbol="Cu",
                                      pbc=boundary, latticeconstant=3.61*1.04)
        else:
            atoms = None
        if isparallel:
            atoms = MakeParallelAtoms(atoms, cpulayout)
        natoms = atoms.get_global_number_of_atoms()
        atoms.calc = EMT()
        MaxwellBoltzmannDistribution(atoms, temperature_K=3000)
        if ismaster:
            print("Initializing")

        dyn = VelocityVerlet(atoms, logfile="-", timestep=3*units.fs, loginterval=1)
        dyn.run(50)
        e_start = (atoms.get_potential_energy() 
                   + atoms.get_kinetic_energy())/natoms
        if ismaster:
            print("Running")
        dyn = VelocityVerlet(atoms, timestep=5*units.fs)
        logger = MDLogger(dyn, atoms, '-', peratom=True)
        logger()
        dyn.attach(logger, interval=25)
        if writetraj:
            if cpulayout is None:
                tname = "longVerlet-serial-%d-%d-%d.traj" % tuple(boundary)
            else:
                tname = ("longVerlet-%d-%d-%d--%d-%d-%d.traj" %
                         (tuple(cpulayout) + tuple(boundary)))
            traj = Trajectory(tname, "w", atoms)
            traj.write()
            dyn.attach(traj, interval=1000)
        
        for i in range(40):
            dyn.run(100)
            if i % 5 == 4:
                print(i+1, "%")
            e = (atoms.get_potential_energy() + atoms.get_kinetic_energy())/natoms
            ReportTest("Step "+str(i), e, e_start, 3e-4)


