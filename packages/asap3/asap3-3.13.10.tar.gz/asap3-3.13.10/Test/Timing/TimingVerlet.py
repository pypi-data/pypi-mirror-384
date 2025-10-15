#! /usr/bin/env python

from numpy import *
from asap3 import *
from asap3.md.verlet_fast import VelocityVerlet
from asap3.md.langevin import Langevin
from ase.lattice.cubic import FaceCenteredCubic
from asap3.timing import report_timing
import sys, pickle, time, commands, os, re
import numpy as np
from asap3.testtools import ReportTest

# cpu time:  time.clock().   Wall clock time: time.time()

#Verbose(1)

usethread = (len(sys.argv) > 1 and sys.argv[1] == "-t")
if usethread:
    AsapThreads()


host = commands.getoutput("hostname")
timesteps = 100
selfcheckfilename = "timing-selfcheck.dat"
asapversion = get_version()
when = time.strftime("%a %d %b %Y %H:%M", time.localtime(time.time()))

randomstate = "randomstate.pickle"
if os.path.isfile(randomstate):
    np.random.set_state(pickle.load(open(randomstate, "rb")))
else:
    print("Saving random state for next call.")
    rndfile = open(randomstate, "wb")
    pickle.dump(np.random.get_state(), rndfile)
    rndfile.close()
    

#PrintVersion(1)
print("Running ASAP timing on "+host+".")
if re.match(r"^n\d\d\d.dcsc.fysik.dtu.dk$", host):
    print("    This is a d512 node on Niflheim.")
    fullhost = "niflheim-d512/%s" % (host.split(".")[0])
    host = "niflheim-d512"
elif re.match(r"^[stu]\d\d\d.dcsc.fysik.dtu.dk$", host):
    print("    This is an s50 node on Niflheim.")
    fullhost = "niflheim-s50/%s" % (host.split(".")[0])
    host = "niflheim-s50"
else:
    fullhost = host
print("Current time is "+when)
print("")

print("Preparing system")
initial = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                            size=(30, 30, 30),
                            symbol="Cu")
ReportTest("Number of atoms", len(initial), 108000, 0)
r = initial.get_positions()
r.flat[:] += 0.14 * sin(arange(3*len(initial)))
initial.set_positions(r)

print("Running self-test.")
atoms = Atoms(initial)
atoms.set_calculator(EMT())
e = atoms.get_potential_energies()
f = atoms.get_forces()
if os.access(selfcheckfilename, os.F_OK):
    olde, oldf = pickle.load(open(selfcheckfilename, "rb"))
    de = max(fabs(e - olde))
    df = max(fabs(f.flat[:] - oldf.flat[:]))
    print("Maximal deviation:  Energy", de, "  Force", df)
    ReportTest("Max force error", df, 0.0, 1e-11)
    ReportTest("Max energy error", de, 0.0, 1e-11)
    del olde, oldf
else:
    print("WARNING: No self-check database found, creating it.")
    pickle.dump((e, f), open(selfcheckfilename, "wb"))
del e,f,atoms

ReportTest.Summary(exit=1)

print("Preparing to run Verlet dynamics.")
atoms = Atoms(initial)
atoms.set_calculator(EMT())
dynamics = VelocityVerlet(atoms, 5*units.fs)

print("Running Verlet dynamics.")
startcpu, startwall = time.clock(), time.time()
dynamics.run(timesteps)

vcpu, vwall = time.clock() - startcpu, time.time() - startwall
vfraction = vcpu/vwall
sys.stderr.write("\n")
print("Verlet dynamics done.")
del dynamics, atoms

print("")
print("")
print("TIMING RESULTS:")
print(f"Verlet:   CPU time {vcpu:.2f}s  Wall clock time {vwall:.2f}s ({vfraction * 100:.0f}%)")
print("")

report_timing()
