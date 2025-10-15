from asap3 import *
from asap3.md.verlet import VelocityVerlet
from ase.lattice.cubic import FaceCenteredCubic
from ase.io.trajectory import *
from ase.io import write
from numpy import *
import sys, os, time
from asap3.testtools import ReportTest

#DebugOutput("output.%d")
print_version(1)
delete = True
precision = 1e-8

def maketraj(atoms, t, nstep):
    e = [atoms.get_potential_energy()]
    dyn = VelocityVerlet(atoms, 5*units.fs)
    for i in range(nstep):
        dyn.run(10)
        e.append(atoms.get_potential_energy())
        if t is not None:
            t.write()
    return e

def maketraj_no_e(atoms, t, nstep):
    dyn = VelocityVerlet(atoms, 5*units.fs)
    for i in range(nstep):
        dyn.run(10)
        if t is not None:
            t.write()

def checktraj(t, e, recalc=True):
    i = 0
    for atoms in t:
        if recalc:
            atoms.calc = EMT()
        ReportTest("Checking frame %d" % (i,), atoms.get_potential_energy(),
                   e[i], precision)
        i += 1

initial = FaceCenteredCubic(size=(10,10,10), symbol="Cu", pbc=(1,0,0))


atoms = initial.copy()
atoms.calc = EMT()
print("Writing trajectory")
traj = Trajectory("traj1.traj", "w", atoms)
atoms.get_potential_energy()
traj.write()
energies = maketraj(atoms, traj, 10)
traj.close()

print("Reading trajectory (recalculating energies)")
traj = Trajectory("traj1.traj")
checktraj(traj, energies)

print("Reading trajectory (stored energies)")
traj = Trajectory("traj1.traj")
checktraj(traj, energies, recalc=False)

print("Writing a trajectory without precalculated energies.")
atoms = initial.copy()
atoms.calc = EMT()
traj = Trajectory("traj3.traj", "w", atoms, properties=['energy'])
atoms.get_potential_energy()
traj.write()
maketraj_no_e(atoms, traj, 10)
traj.close()
traj = Trajectory("traj3.traj")
checktraj(traj, energies, recalc=False)

if delete:
    print("Deleting trajectory")
    os.unlink("traj1.traj")
    os.unlink("traj3.traj")
    
ReportTest.Summary()
