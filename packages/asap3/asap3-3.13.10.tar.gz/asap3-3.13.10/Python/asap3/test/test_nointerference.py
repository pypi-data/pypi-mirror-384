# Test that various observers and analysis tools do not interfere with
# the energy calculator e.g. by messing up the neighbor list.
#
# It works by making a short simulation without any observers, and then
# repeating it with observers, checking that the result is the same.

from asap3 import EMT, Atoms, units, MakeParallelAtoms
from asap3.md.verlet import VelocityVerlet
from asap3.md.langevin import Langevin
from ase.lattice.cubic import FaceCenteredCubic
from asap3.analysis import RestrictedCNA, RadialDistributionFunction
from asap3.test.pytest_markers import ReportTest, serial
from ase.parallel import world
import numpy as np

import pytest

def Compare(name, atoms, observer, ref, interval=4):
    dyn = VelocityVerlet(atoms, 5*units.fs)
    dyn.attach(observer, interval=interval)
    r = []
    for i in range(50):
        dyn.run(5)
        epot = atoms.get_potential_energy() / len(atoms)
        ekin = atoms.get_kinetic_energy() / len(atoms)
        r.append([epot, ekin, epot+ekin])
    r = np.array(r)
    diff = r - ref
    maxdiff = diff.max()
    print("Maximal difference is", maxdiff)
    ReportTest(name, maxdiff, 0.0, 1e-6)
    
@serial   # It looks like RadialDistributionFunction coredumps in parallel
@pytest.mark.core
def test_nointerference(cpulayout):
    if cpulayout:
        size = np.array((5, 5, 5)) * cpulayout
    else:
        size = (10, 5, 5)
    print("Making initial system")
    if world.rank == 0:
        iniatoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                                    size=size, symbol="Cu", pbc=(1,1,0))
        iniatoms.calc = EMT()
        inidyn = Langevin(iniatoms, 5*units.fs, temperature_K=450, friction=0.05)
        inidyn.run(100)
        print("Temperature is now", iniatoms.get_kinetic_energy() / (1.5*units.kB*len(iniatoms)), "K")
    else:
        iniatoms = None
    world.barrier()

    print("Making reference simulation")
    if world.size == 1:
        refatoms = Atoms(iniatoms)
    else:
        refatoms = MakeParallelAtoms(iniatoms, cpulayout)
    refatoms.calc = EMT()
    dyn = VelocityVerlet(refatoms, 5*units.fs)
    ref = []
    for i in range(50):
        dyn.run(5)
        epot = refatoms.get_potential_energy() / len(refatoms)
        ekin = refatoms.get_kinetic_energy() / len(refatoms)
        ref.append([epot, ekin, epot+ekin])

    ref = np.array(ref)

    print("Testing RestrictedCNA")
    if world.size == 1:
        atoms = Atoms(iniatoms)
    else:
        atoms = MakeParallelAtoms(iniatoms, cpulayout)
    atoms.calc = EMT()
    cna = RestrictedCNA(atoms)
    Compare("RestrictedCNA", atoms, cna.analyze, ref)

    print("Testing RadialDistributionFunction")
    if world.size == 1:
        atoms = Atoms(iniatoms)
    else:
        atoms = MakeParallelAtoms(iniatoms, cpulayout)
    atoms.calc = EMT()
    rdf = RadialDistributionFunction(atoms, 4.0, 25)
    Compare("RadialDistributionFunction", atoms, rdf.update, ref)

