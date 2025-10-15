"""Testing the parallel PrimiPlotter."""

from asap3 import *
from asap3.md.verlet import VelocityVerlet
from numpy import *
from pickle import *
#from Asap.Trajectories.NetCDFTrajectory import *
import sys, os, time
from asap3.testtools import *
from asap3.mpi import world
from ase.build import bulk
from ase import units
from asap3.visualize.primiplotter  import *
import shutil

debug = 0
if debug == 1:
    DebugOutput("makeverlet%d.log", nomaster=True)
elif debug == 2:
    time.sleep(world.rank)
    print("PID:", os.getpid())
    time.sleep(20)

print_version(1)
set_verbose(0)

ismaster = world.rank == 0
isparallel = world.size != 1
if world.size == 1:
    cpulayout = None
elif world.size == 2:
    cpulayout = [2,1,1]
elif world.size == 3:
    cpulayout = [1,3,1]
elif world.size == 4:
    cpulayout = [2,1,2]


gs_installed = shutil.which('gs')
if not gs_installed:
    print("Skipping test, as ghostscript (gs) is not installed.")
else:
    if isparallel:
        print("RUNNING PARALLEL VERSION OF TEST SCRIPT")
    else:
        print("RUNNING SERIAL VERSION OF TEST SCRIPT")

    if ismaster:
        atoms = bulk('Cu', cubic=True).repeat((8,8,8))
        atoms.set_pbc(False)
        atoms.center(vacuum=5.0)
        if cpulayout:
            atoms = atoms.repeat(cpulayout)
        dx = 0.1 * sin(arange(3*len(atoms))/10.0)
        dx.shape = (-1,3)
        atoms.set_positions(atoms.get_positions() + dx)
        del dx
        out = sys.stderr
    else:
        atoms = None
        out = open("/dev/null", "w")

    if isparallel:
        atoms = MakeParallelAtoms(atoms, cpulayout)
        nTotalAtoms = atoms.get_global_number_of_atoms()
    else:
        nTotalAtoms = len(atoms)

    #report()

    print("Setting potential")
    atoms.calc = EMT()

    dyn = VelocityVerlet(atoms, 5 * units.fs)

    print("Number of atoms:", nTotalAtoms)

    epot = atoms.get_potential_energy() / nTotalAtoms
    ekin = atoms.get_kinetic_energy() / nTotalAtoms
    etotallist = [epot+ekin]
    ekinlist = [ekin]

    #report()

    if ismaster:
        print("\nE_pot = {:<12.5f}  E_kin = {:<12.5f}  E_tot = {:<12.5f}".format(epot, ekin,
                                                                     epot+ekin))
    dyn.attach(MDLogger(dyn, atoms, "-", peratom=True), interval=10)

    dyn.run(100)
    e0 = (atoms.get_potential_energy() + atoms.get_kinetic_energy()) / nTotalAtoms

    if isparallel:
        plotter = ParallelPrimiPlotter(atoms)
    else:
        plotter = PrimiPlotter(atoms)
    plotter.set_output(PngFile("pplottest"))  # Save as PNG files
    plotter.set_output(PostScriptFile("pplottest"))  # Save as PS files
    dyn.attach(plotter.plot, interval=250)

    filenames =[ f'pplottest{i:04d}.{t}' for i in (0, 1) for t in ('png', 'ps')]
    if ismaster:
        for f in filenames:
            if os.path.exists(f):
                print("Removing", f)
                os.unlink(f)

    dyn.run(500)

    e = (atoms.get_potential_energy() + atoms.get_kinetic_energy()) / nTotalAtoms

    ReportTest("Energy is conserved", e, e0, 1e-4)

    # Check the output files
    if ismaster:
        for f in filenames:
            ReportTest(f"File {f} exists", os.path.exists(f), 1, 0)
            if os.path.exists(f):
                ReportTest(f"File {f} is not empty", os.path.getsize(f) != 0, 1, 0)
                print("Removing", f)
                os.unlink(f)

    ReportTest.Summary(0)

