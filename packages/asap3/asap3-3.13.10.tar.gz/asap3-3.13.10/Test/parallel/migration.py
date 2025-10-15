from asap3 import *
from ase.lattice.cubic import FaceCenteredCubic
from asap3.testtools import ReportTest
from asap3.mpi import world
from asap3.Internal.ParallelListOfAtoms import ParallelAtoms
import numpy as np

#DebugOutput("migration%d.log", nomaster=True)

def pot():
    #return EMT2013(PtY_parameters)
    return EMT()

#set_verbose(1)
master = world.rank == 0
if world.size == 1:
    cpulayout = None
elif world.size == 2:
    cpulayout = [2,1,1]
elif world.size == 3:
    cpulayout = [1,3,1]
elif world.size == 4:
    cpulayout = [2,1,2]
    
if master:
    atoms0 = FaceCenteredCubic(symbol='Pt', size=(15,15,30))
else:
    atoms0 = None
    
atoms0 = MakeParallelAtoms(atoms0, cpulayout)
atoms0.calc = pot()

print("*********** FIRST FORCE CALCULATION ************", file=sys.stderr)
print("len(atoms) =", len(atoms0), "   no. atoms =", atoms0.get_global_number_of_atoms(), file=sys.stderr)
f0 = atoms0.get_forces()
perturbation = 0.01 * np.random.standard_normal(atoms0.get_positions().shape)
r = atoms0.get_positions() + perturbation
atoms0.set_positions(r)
print("*********** SECOND FORCE CALCULATION ************", file=sys.stderr)

f1 = atoms0.get_forces()

print("*********** COPYING ATOMS **************", file=sys.stderr)
#atoms0.set_calculator(None)  # Cannot copy parallel calculators
atoms2 = ParallelAtoms(cpulayout, atoms0.comm, atoms0, distribute=False)
atoms2.calc = pot()
print("*********** THIRD FORCE CALCULATION ************", file=sys.stderr)
f2 = atoms2.get_forces()

#maxdev = abs(f2 - f1).max()
#print maxdev
#ReportTest("Max error 1:", maxdev, 0.0, 1e-6)

#ReportTest.Summary()

print("No crashes - success !!", file=sys.stderr)
