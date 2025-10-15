"""Module for testing various NVT dynamics algorithms.

The actual tests import this module.
"""


from ase.units import fs, kB
from ase.build import bulk
import asap3
import numpy as np
# matplotlib only imported in debugging mode (in function test_nvt)
# import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from asap3.md.velocitydistribution import (MaxwellBoltzmannDistribution,
                                             Stationary)
from asap3.test.pytest_markers import ReportTest
from asap3.io import Trajectory
from asap3.mpi import world
try:
    from asap3 import MakeParallelAtoms
except ImportError:
    pass   # Probably installed as serial-only.

def make_atoms(T, rng, size=(2,2,2), parallel=False):
    "Make atomic system suitable for test."
    atoms = bulk('Cu', cubic=True)
    atoms *= size
    if parallel:
        if world.rank == 0:
            atoms *= (2, 2, 2 * world.size)
            atoms.set_pbc(False)
            atoms.center(vacuum=2.0, axis=(0, 1))
            atoms.set_pbc(True)
        else:
            atoms = None
        atoms = MakeParallelAtoms(atoms, (1, 1, world.size))
    MaxwellBoltzmannDistribution(atoms, temperature_K=T, rng=rng)
    Stationary(atoms)
    atoms.calc = asap3.EMT()
    return atoms

class MeasureEnergy:
    "Observer measuring the energy and temperature."
    def __init__(self, atoms):
        self.atoms = atoms
        self.energies = []
        self.temperatures = []

    def __call__(self):
        e = self.atoms.get_potential_energy() + self.atoms.get_kinetic_energy()
        T = self.atoms.get_temperature()
        self.energies.append(e)
        self.temperatures.append(T)


def exponential(t, A, tau, B):
    "We fit stuff to exponentials"
    return A * np.exp(-t / tau) + B

def test_nvt(atoms, nsteps, dt, T0, dynmaker, initdyn=None, rng=None,
             intval=5, plot=False, sloppytime=False, failfluct=False,
             parallel=False, trajectory=None):
    """Run NVT dynamics, testing the behaviour.

    Parameters:
    atoms:      The atoms object.
    nsteps:     Length of simulation.
    dt:         Time step.
    T0:         Expected temperature
    dynmaker:   Function making the dynamics object.
    initdyn:    Function making initialization dynamics object, if different.
    rng:        Random number generator.
    intval:     Interval for taking data.
    plot:       Plot the swing-in temperature graph (default: False).
    sloppytime: Test of swing-in time is sloppy (+/- 50% instead of +/- 1%).
                (for nondeterministic dynamics)
    failfluct:  Test of energy fluctuations is expected to fail.
                (for dynamics that does not produce a true Canonical Ensemble)
    parallel:   Disable some tests in parallel test suite.
    """
    runtime = nsteps * dt
    tau = runtime / 10    # Energy relaxation time in ideal gas

    # We pass *half* the energy relaxation time to the generator of the dynamics,
    # as we have a solid, where the relaxation time will be twice that of the
    # ideal gas, since the same amount of potential and kinetic energy needs
    # to be added to the system.
    if initdyn is None:
        initdyn = dynmaker   # Normally use the same dynamics for both tests
    dyn = initdyn(atoms, T0, dt, tau/2, rng=rng, logint=1000)
    measure = MeasureEnergy(atoms)
    dyn.attach(measure, interval=1)
    dyn.run(nsteps)
    #energies = measure.energies
    temperatures = measure.temperatures

    # Fit temperature curve
    temperatures = temperatures[5:]
    times = np.arange(len(temperatures)) * dt
    if not parallel:
        (DeltaTfit, tau_fit, T_fit), _ = curve_fit(exponential, times, temperatures, (-T0, tau, T0))

    # Run again with smaller tau
    tausmall = runtime / 100
    dyn = dynmaker(atoms, T0, dt, tausmall, rng=rng, logint=5000)
    measure = MeasureEnergy(atoms)
    dyn.attach(measure, interval=intval)
    com_before = atoms.get_center_of_mass()
    if trajectory:
        traj = Trajectory(trajectory, "w", atoms)
        dyn.attach(traj, interval=nsteps//5)
    if failfluct:
        # No need for good statistics if it fails anyway
        dyn.run(nsteps)
    else:
        dyn.run(nsteps*10)
    com_after = atoms.get_center_of_mass()
    energies = measure.energies
    energies = energies[len(energies)//10:]
    temperatures2 = measure.temperatures
    temperatures2 = temperatures2[len(temperatures2)//5:]
    times2 = np.arange(len(temperatures2)) * dt * intval

    stdE = np.std(energies)
    avgT = np.mean(temperatures2)
    # Expected energy fluctuation: sqrt(k_B T^2 3 N k_B) = k_B * T * sqrt(3 * N)
    expected = kB * T0 * np.sqrt(3 * len(atoms))

    # Output results
    if not parallel:
        print(f"Part 1 temperature:   {T_fit:.2f} K    (expected {T0:.2f})")
        print(f"Time constant:       {tau_fit/fs:.1f} fs  (expected {tau/fs:.1f}  error {(tau_fit / tau - 1) * 100:.1f}%)")
        print(f"Initial temperature offset:  {DeltaTfit:.2f} K")
        if sloppytime:
            tau_error = 0.5 * tau/fs
        else:
            tau_error = 0.01 * tau/fs
        ReportTest('Time constant', tau_fit/fs, tau/fs, tau_error)

    print(f"Observed energy fluctuation: {stdE:.2f} eV")
    print(f"Expected energy fluctuation: {expected:.2f} eV")
    print(f"Error: {(stdE / expected - 1) * 100:.1f}%")
    if failfluct:
        print('Failed fluctuations EXPECTED for this dynamics!')
    else:
        ReportTest("Energy fluctuations", stdE, expected, 0.15*expected)

    # Temperature error: We should be able to detect a error of 1/N_atoms
    maxtemperr = 2/3 * 3/atoms.get_number_of_degrees_of_freedom()
    # ... but not if we don't have good statistics.
    if parallel:
        maxtemperr *= 20  # System is much larger and run is shorter
    elif failfluct:
        maxtemperr *= 4

    print(f'Observed average temperature:  {avgT:.2f} K   (expected {T0:.2f} K)')
    print(f'Error: {(avgT / T0 - 1) * 100:.1f}%  (max: {maxtemperr * 100:.1f}%)')
    ReportTest('Temperature', avgT, T0, T0 * maxtemperr)

    print('Center of mass before:', com_before)
    print('Center of mass after: ', com_after)

    if plot:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.plot(times, temperatures, 'b.')
        if not parallel:
            ax.plot(times, exponential(times, DeltaTfit, tau_fit, T_fit), 'k-')
        fig2, ax2 = plt.subplots()
        ax2.plot(times2, temperatures2, 'b.')
        plt.show(block=True)


def main(dynmaker, rng, repeat=1, plot=False, sloppytime=False, failfluct=False,
         initdyn=None, parallel=False, trajectory=None):
    T0 = 300
    dt = 5 * fs
    nsteps = 20000

    if parallel:
        T0 = 1000
        nsteps //= 4  # The system is much bigger
        # Plot only on master
        if plot:
            plot = world.rank == 0

    for i in range(repeat):
        atoms = make_atoms(T0 / 10, rng, parallel=parallel)
        if parallel:
            print(f'Atoms on rank {world.rank}: {len(atoms)}')
        test_nvt(atoms, nsteps, dt, T0, dynmaker=dynmaker, initdyn=initdyn,
                 rng=rng, plot=plot, sloppytime=sloppytime, failfluct=failfluct,
                 parallel=parallel, trajectory=trajectory)
        if parallel:
            print(f'Atoms on rank {world.rank}: {len(atoms)}')
    if parallel:
        world.barrier()  # Needed if plotting, at least.

if __name__ == "__main__":
    print("This it not a test, but a module imported from a few tests.")
