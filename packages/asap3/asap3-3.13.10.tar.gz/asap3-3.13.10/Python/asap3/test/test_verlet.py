import pickle
import sys

import numpy as np
import pytest

from asap3 import Atoms, VelocityVerlet, EMT, MDLogger, OpenKIMsupported, AsapError
if OpenKIMsupported:
    from asap3 import OpenKIMcalculator
from asap3.test.pytest_markers import serial, withmpi, withOpenKIM
from ase.parallel import world

@pytest.fixture
def data(datadir):
    picklehack = {'encoding': 'latin1'}
    picklefile = datadir / "Verlet.pickle"
    return pickle.load(open(picklefile, "rb"), **picklehack)

@pytest.mark.core
@serial
def test_verlet(data):
    runtest_verlet(data, EMT())

def runtest_verlet(data, potential):
    timeunit = 1.018047e-14             # Seconds
    femtosecond = 1e-15 / timeunit      # Marginally different from units.fs
    stresshack = {'include_ideal_gas': True}

    init_pos = np.array(data["initial"])
    init_pos.shape = (-1,3)
    init_box = np.array(data["box"])
    init_box.shape = (3,3)
    atoms = Atoms(positions=init_pos, cell=init_box)
    atoms.set_atomic_numbers(47 * np.ones((len(atoms),)))
    atoms.calc = potential

    dyn = VelocityVerlet(atoms, 2 * femtosecond)
    dyn.attach(MDLogger(dyn, atoms, '-', peratom=True), interval=5)

    etot = None

    for i in range(10):
        dyn.run(20)
        epot = atoms.get_potential_energy() / len(atoms)
        ekin = atoms.get_kinetic_energy() / len(atoms)
        if etot is None:
            etot = epot + ekin
        else:
            assert np.isclose(epot + ekin, etot, atol=1e-3), 'Energy conservation'
            
    final_pos = np.array(data["final"])
    diff = max(abs(atoms.get_positions().flat - final_pos))
    print("Maximal deviation of positions:", diff)
    assert diff < 1e-9, 'Maximal deviation of positions'

    diff = max(abs(atoms.get_stresses(**stresshack).flat - np.array(data["stress"])))

    print("Maximal deviation of stresses:", diff)
    assert diff < 1e-9, 'Maximal deviation of stresses'


@withmpi
def test_verlet_par(data, cpulayout):
    runtest_verlet_par(data, cpulayout, EMT())

@withmpi
@withOpenKIM
def test_verlet_KIM(data, cpulayout, openkimmodel, in_tmp_dir):
    try:
        calc = OpenKIMcalculator(openkimmodel)
    except AsapError as oops:
        if oops.args[0].startswith('Failed to initialize OpenKIM model'):
            calc = None
        else:
            raise
    if calc is not None:
        runtest_verlet_par(data, cpulayout, calc, epotexpected=-3.456898)

def runtest_verlet_par(data, cpulayout, potential, epotexpected=0.058370, report=False):
    from asap3 import MakeParallelAtoms

    # Ensure same time step as in Asap-2
    timeunit = 1.018047e-14             # Seconds
    femtosecond = 1e-15 / timeunit      # Marginally different from units.fs
    isparallel = world.size > 1
    ismaster = world.rank == 0

    if isparallel:
        print("RUNNING PARALLEL VERSION OF TEST SCRIPT")
    else:
        print("RUNNING SERIAL VERSION OF TEST SCRIPT")

    if ismaster:
        init_pos = np.array(data["initial"])
        init_pos.shape = (-1,3)
        init_box = np.array(data["box"])
        init_box.shape = (3,3)
        a = Atoms(positions=init_pos, cell=init_box, pbc=(1,1,1))
        a.set_atomic_numbers(29 * np.ones(len(a)))
        #atoms = a.repeat((2,2,3))
        # Ensure same order of atoms as in ASE-2
        atoms = a.repeat((1,1,3)).repeat((1,2,1)).repeat((2,1,1))
        dx = 0.1 * np.sin(np.arange(3*len(atoms))/10.0)
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

    if report:
        report_verlet(out)

    print("Setting potential")
    atoms.calc = potential

    dyn = VelocityVerlet(atoms, 2 * femtosecond)
    # if isparallel:
    #     traj = ParallelNetCDFTrajectory("ptraj.nc", atoms, interval=20)
    # else:
    #     traj = NetCDFTrajectory("ptraj.nc", atoms, interval=20)
    # dyn.Attach(traj)
    # traj.Update()

    print("Number of atoms:", nTotalAtoms)

    epot = atoms.get_potential_energy() / nTotalAtoms
    ekin = atoms.get_kinetic_energy() / nTotalAtoms
    etotallist = [epot+ekin]
    ekinlist = [ekin]

    #report()

    if ismaster:
        print("\nE_pot = {:<12.5f}  E_kin = {:<12.5f}  E_tot = {:<12.5f}".format(epot, ekin,
                                                                    epot+ekin))
    assert np.isclose(epot, epotexpected, atol=1e-4), 'Initial potential energy'
    assert np.isclose(ekin, 0.0, atol=1e-9), 'Initial kinetic energy'

    dyn.attach(MDLogger(dyn, atoms, "-", peratom=True), interval=10)

    for i in range(40):
        dyn.run(5)
        epot = atoms.get_potential_energy() / nTotalAtoms
        ekin = atoms.get_kinetic_energy() / nTotalAtoms
        etotallist.append(epot+ekin)
        ekinlist.append(ekin)

    if ismaster:
        print("Average total energy:", sum(etotallist)/len(etotallist))
        print("Average kinetic energy:", sum(ekinlist)/len(ekinlist))

    assert np.isclose(sum(etotallist)/len(etotallist), epotexpected, atol=0.0001), 'Agv. total energy'
    assert np.isclose(sum(ekinlist)/len(ekinlist), 0.0290841, atol=0.002), 'Agv. kinetic energy' 

def report_verlet(out):
    "Debugging function - not normally used."
    for i in range(world.size):
        if i == world.rank:
            print("Data on processor", i, file=out)
            for key in atoms.arrays.keys():
                print("  ", key, atoms.arrays[key].shape, file=out)
            r = atoms.get_positions()
            if len(r):
                print("Limits to the positions:", file=out)
                print ("[%.4f, %.4f]  [%.4f, %.4f]  [%.4f, %.4f]" %
                       (min(r[:,0]), max(r[:,0]), min(r[:,1]), max(r[:,1]),
                        min(r[:,2]), max(r[:,2])), file=out)
            if world.size > 1:
                print("Ghost data on processor", i)
                for key in atoms.ghosts.keys():
                    print("  ", key, atoms.ghosts[key].shape, file=out)
                r = atoms.ghosts['positions']
                if len(r):
                    print("Limits to the ghost positions:", file=out)
                    print ("[%.4f, %.4f]  [%.4f, %.4f]  [%.4f, %.4f]" %
                           (min(r[:,0]), max(r[:,0]), min(r[:,1]), max(r[:,1]),
                            min(r[:,2]), max(r[:,2])), file=out)
        world.barrier()


