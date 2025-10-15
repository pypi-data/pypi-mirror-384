from asap3 import EMT, MakeParallelAtoms, BundleTrajectory
from ase import units
import ase.data
from ase.md.verlet import VelocityVerlet
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.lattice.compounds import L1_2
from asap3.mpi import world
from asap3.test.pytest_markers import ReportTest, serial
import numpy as np

import pytest

cu = ase.data.atomic_numbers['Cu']
au = ase.data.atomic_numbers['Au']

def check_z(a):
    try:
        id = a.get_ids()
    except AttributeError:
        id = np.arange(len(a))
    z = a.get_atomic_numbers()
    z_expect = np.where(id % 4, cu, au)
    assert (z == z_expect).all()

@pytest.mark.slow
def test_bundle_traj_preserves_z(cpulayout, in_tmp_dir):
    cu3au_a = 3.72977
    delete = True

    ismaster = world.rank == 0
    isparallel = world.size != 1

    if ismaster:
        initial = L1_2(size=(15,15,15), symbol=(au,cu),
                    latticeconstant=cu3au_a, pbc=(1,0,0))
    else:
        initial = None
    if isparallel:
        atoms = MakeParallelAtoms(initial, cpulayout)
        print("Min ID", atoms.get_ids().min())
    else:
        atoms = initial.copy()
    
    check_z(atoms)

    print("Simulation: create the bundle")
    # Give a momentum distribution likely to cause migration
    MaxwellBoltzmannDistribution(atoms, temperature_K=5000)
    p = atoms.get_momenta()
    pz = p[10,2]
    p[:,2] += pz

    atoms.calc = EMT()
    if isparallel:
        traj = BundleTrajectory("preservez.bundle", "w", atoms, split=True)
    else:
        traj = BundleTrajectory("preservez.bundle", "w", atoms)
    dyn = VelocityVerlet(atoms, 5*units.fs)
    dyn.attach(traj, interval=50)
    dyn.attach(check_z, interval=25, a=atoms)
    traj.write()
    dyn.run(150)
    traj.close()
    
    print("Reading in serial mode:")
    traj = BundleTrajectory("preservez.bundle")
    for i, atoms in enumerate(traj):
        print(f"Task {world.rank}, step {i}: found {len(atoms)} atoms")
        check_z(atoms)
    traj.close()

    world.barrier()
    print("Reading in parallel mode.")
    traj = BundleTrajectory("preservez.bundle")
    for i in range(len(traj)):
        atoms = traj.get_atoms(i, cpulayout)
        print(f"Task {world.rank}, step {i}: found {len(atoms)} atoms")
        check_z(atoms)
    traj.close()
    del traj

    world.barrier()
    if delete:
        #if ismaster:
        print("Deleting trajectory")
        BundleTrajectory.delete_bundle("preservez.bundle")
