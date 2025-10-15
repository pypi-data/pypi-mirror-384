from asap3 import *
from asap3.mpi import world
from asap3.io import Trajectory
from ase.io import write
from ase.build import bulk
from asap3.test.pytest_markers import ReportTest, parallel

import pytest

@parallel
def test_autodistribution(in_tmp_dir):
    'Tests the auto keyword for cpulayout when loading from a Trajectory'
    if world.rank == 0:
        atoms1 = bulk("Cu", cubic=True).repeat((20,20,20))
        atoms1.set_pbc = False
        atoms1.center(vacuum=5.)
        ReportTest("Number of atoms", len(atoms1), 32000, 0)
        atoms1.calc = EMT()
        e0 = atoms1.get_potential_energy()
        write("serialatoms.traj", atoms1, parallel=False)
    else:
        atoms1 = None

    world.barrier()

    atoms = Trajectory("serialatoms.traj").get_atoms(-1, 'auto')
    atoms.calc = EMT()
    e = atoms.get_potential_energy()
    world.barrier()   # Protects cleanup
    if world.rank == 0:
        os.unlink('serialatoms.traj')
        ReportTest("Energy of saved atoms", e, e0, 1e-3)

    world.barrier()
