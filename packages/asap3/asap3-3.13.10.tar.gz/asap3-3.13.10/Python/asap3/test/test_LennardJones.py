from asap3 import Atoms, MakeParallelAtoms, LennardJones, units
from ase.md.verlet import VelocityVerlet
from ase.lattice.cubic import FaceCenteredCubic
from asap3.io.trajectory import Trajectory
from numpy import sqrt, sin, arange
from asap3.mpi import world
from asap3.test.pytest_markers import ReportTest, serial

import pytest


elements = [29]
epsilon  = [0.15]
sigma    = [2.7]

@pytest.fixture
def initial():
    if world.rank == 0:
        initial = FaceCenteredCubic(directions=((1,0,0),(0,1,0),(0,0,1)),
                                    size=(40,40,40), symbol="Cu",
                                    latticeconstant=1.09*sigma[0]*1.41,
                                    pbc=(1,1,0))
        momenta = sqrt(2*63.5 * units.kB * 400) * sin(arange(3*len(initial)))
        momenta.shape = (-1,3)
        initial.set_momenta(momenta)
        print("Number of atoms:", len(initial))
    else:
        initial = None
    return initial

@pytest.mark.slow
def test_LennardJones(initial, multicpulayout):

    for layout in multicpulayout:
        if layout:
            print("Test with layout "+str(layout))
            atoms = MakeParallelAtoms(initial, layout)
            natoms = atoms.get_global_number_of_atoms()
        else:
            print("Serial test")
            atoms = Atoms(initial)
            natoms = len(atoms)
        print("Number of atoms:", natoms)
        temp = atoms.get_kinetic_energy() / (1.5*units.kB*natoms)
        print("Temp:", temp, "K")
        ReportTest("Initial temperature", temp, 400.0, 1.0)
        atoms.calc = LennardJones(elements, epsilon, sigma, -1.0, True)

        epot = atoms.get_potential_energy()
        print("Potential energy:", epot)
        ReportTest("Initial potential energy", epot, -301358.3, 0.5)
        etot = epot + atoms.get_kinetic_energy()


        dyn = VelocityVerlet(atoms, 3*units.fs)
        if 0:
            traj = Trajectory("llj.traj", "w", atoms)
            dyn.attach(traj, interval=2)
                    
        etot2 = None
        for i in range(5):
            dyn.run(15)
            newetot = atoms.get_potential_energy()+ atoms.get_kinetic_energy()
            print("Total energy:", newetot)
            temp = atoms.get_kinetic_energy() / (1.5*units.kB*natoms)
            print("Temp:", temp, "K")
            if etot2 == None:
                ReportTest("Total energy (first step)", newetot, etot, 40.0)
                etot2=newetot
            else:
                ReportTest(("Total energy (step %d)" % (i+1,)),
                        newetot, etot2, 20.0)
        print(" *** This test completed ***")

