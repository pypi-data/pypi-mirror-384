print("Check that it is possible to load ASE before Asap without messing up ase.parallel.world.")

from  ase.parallel import world as ase_world
from  asap3.mpi import world as asap_world
assert(ase_world.size == asap_world.size)
