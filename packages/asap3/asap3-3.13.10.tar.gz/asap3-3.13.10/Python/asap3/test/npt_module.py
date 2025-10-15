"""Module for testing various NVT dynamics algorithms.

The actual tests import this module.
"""


from ase.units import fs, kB, GPa
import numpy as np
# matplotlib only imported in debugging mode (in function test_nvt)
# import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from asap3.md.velocitydistribution import (MaxwellBoltzmannDistribution,
                                             Stationary)
from asap3.md.bussi import Bussi
from asap3.md import MDLogger as _MDLogger
from asap3.test.pytest_markers import ReportTest
from asap3.mpi import world
try:
    from asap3 import MakeParallelAtoms
except ImportError:
    pass   # Probably installed as serial-only.
from asap3.test.nvt_module import make_atoms, MeasureEnergy, exponential


bulkmodulus = 140 * GPa    # Bulk modulus of Cu



class MDLogger(_MDLogger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.stress:
            self.fmt = self.fmt[:-1] + '  '
            self.fmt += 9 * " %10.5f"
            self.fmt += '\n'
    def __call__(self):
        epot = self.atoms.get_potential_energy()
        ekin = self.atoms.get_kinetic_energy()
        temp = self.atoms.get_temperature()
        global_natoms = self.atoms.get_global_number_of_atoms()
        if self.peratom:
            epot /= global_natoms
            ekin /= global_natoms
        if self.dyn is not None:
            t = self.dyn.get_time() / (1000 * fs)
            dat = (t,)
        else:
            dat = ()
        dat += (epot + ekin, epot, ekin, temp)
        if self.stress:
            dat += tuple(self.atoms.get_stress(
                include_ideal_gas=True) / GPa)
            cell = np.ravel(self.atoms.cell.array)
            assert len(cell) == 9
            dat += tuple(cell)
        self.logfile.write(self.fmt % dat)
        self.logfile.flush()

class MeasureStuff(MeasureEnergy):
    "Observer measuring energy, temperature, volume and stress"
    def __init__(self, atoms):
        super().__init__(atoms)
        self.volumes = []
        self.stresses = []

    def __call__(self):
        super().__call__()
        self.volumes.append(self.atoms.get_volume())
        self.stresses.append(self.atoms.get_stress(include_ideal_gas=True))


def test_npt(atoms, nsteps, dt, T0, p0, dynmaker, initdyn=None, rng=None,
             intval=5, plot=False, sloppytime=False, failfluct=False,
             parallel=False):
    """Run NPT dynamics, testing the behaviour.

    First, thermalize the system at constant volume using a short
    time constant.  Then relax stress/pressure with a longer time, and 
    measure this relaxation time.  Finally, run the dynamics and measure
    fluctuations in enthalpy and volume.

    Currently, the test does not measure the relaxation time of the
    temperature.

    Parameters:
    atoms:      The atoms object.
    nsteps:     Length of simulation.
    dt:         Time step.
    T0:         Expected temperature.
    p0:         Expected pressure.
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
    taut = runtime / 20    # Energy relaxation time in ideal gas
    taup = runtime / 10

    # Initial relaxation of temperature is done using Bussi dynamics
    dyn = Bussi(atoms, dt, temperature_K=T0, taut=taut, rng=rng)
    dyn.attach(MDLogger(dyn, atoms, '-', peratom=True, stress=True), interval=nsteps//10)
    dyn.run(nsteps)
    
    # We pass *half* the energy relaxation time to the generator of the dynamics,
    # as we have a solid, where the relaxation time will be twice that of the
    # ideal gas, since the same amount of potential and kinetic energy needs
    # to be added to the system.
    if initdyn is None:
        initdyn = dynmaker   # Normally use the same dynamics for both tests
    dyn = initdyn(atoms, T0, p0, dt, taut=taut/2, taup=taup, rng=rng, logint=1000)
    measure = MeasureStuff(atoms)
    dyn.attach(measure, interval=1)
    dyn.run(nsteps)
    stresses = np.array(measure.stresses)
    pressures = -stresses[:,:3].sum(axis=1) / 3

    # Fit temperature curve
    pressures = pressures[5:]
    times = np.arange(len(pressures)) * dt
    if not parallel:
        try:
            (DeltaPfit, taup_fit, P_fit), _ = curve_fit(exponential, times, pressures, (-p0, taup, p0))
        except RuntimeError:
            # Fitting failed
            DeltaPfit, taup_fit, P_fit = 0, 1, 0
            
    # Run again with smaller tau
    tausmall = runtime / 100
    logint = 5000
    if failfluct:
        logint = 1000
    dyn = dynmaker(atoms, T0, p0, dt, taut=tausmall, taup=tausmall, rng=rng, logint=logint)
    measure = MeasureStuff(atoms)
    dyn.attach(measure, interval=intval)
    com_before = atoms.get_center_of_mass()
    if parallel:
        print(f'Atoms on rank {world.rank}: {len(atoms)}')
    if failfluct:
        # No need for good statistics if it fails anyway
        dyn.run(nsteps)
    else:
        dyn.run(nsteps*10)
    if parallel:
        print(f'Atoms on rank {world.rank}: {len(atoms)}')
    com_after = atoms.get_center_of_mass()
    energies = np.array(measure.energies)
    stresses = np.array(measure.stresses)
    pressures2 = -stresses[:,:3].sum(axis=1) / 3
    volumes = np.array(measure.volumes)
    enthalpies = energies + p0 * volumes
    enthalpies = enthalpies[len(energies)//10:]
    temperatures2 = measure.temperatures
    temperatures2 = temperatures2[len(temperatures2)//5:]
    pressures2 = pressures2[len(pressures2)//5:]
    stresses = stresses[len(stresses)//5:]
    times2 = np.arange(len(temperatures2)) * dt * intval

    stdH = np.std(enthalpies)
    stdV = np.std(volumes)
    avgV = np.mean(volumes)
    avgT = np.mean(temperatures2)
    avgP = np.mean(pressures2)
    avgstr = np.mean(stresses, axis=0)
    # Expected enthalpy fluctuation: sqrt(k_B T^2 3 N k_B) = k_B * T * sqrt(3 * N)
    expected = kB * T0 * np.sqrt(3 * len(atoms))
    expectedV = np.sqrt(kB * T0 * avgV / bulkmodulus)

    # Output results
    if not parallel:
        print(f"Part 1 pressure:   {P_fit/GPa:.2f} GPa    (expected {p0/GPa:.2f})")
        print(f"Time constant:     {taup_fit/fs:.1f} fs  (expected {taup/fs:.1f}  error {(taup_fit / taup - 1) * 100:.1f}%)")
        print(f"Initial pressure offset:  {DeltaPfit/GPa:.2f} GPa")
        taup_error = 0.5 * taup/fs   # Larger than for NVT as thermostat and barostat interact
        ReportTest('Time constant', taup_fit/fs, taup/fs, taup_error)

    print(f"Observed enthalpy fluctuation: {stdH:.2f} eV")
    print(f"Expected enthalpy fluctuation: {expected:.2f} eV")
    print(f"Error: {(stdH / expected - 1) * 100:.1f}%")
    
    print(f"Average volume {avgV:.2f} Å^3")
    print(f"Observed volume fluctuation: {stdV:.2f} Å^3")
    print(f"Expected volume fluctuation: {expectedV:.2f} Å^3")
    print(f"Error: {(stdV / expectedV - 1) * 100:.1f}%")
  
    if failfluct:
        print('Failed fluctuations EXPECTED for this dynamics!')
    else:
        ReportTest("Energy fluctuations", stdH, expected, 0.15*expected)
        ReportTest("Volume fluctuations", stdV, expectedV, 0.15*expectedV)

    # Temperature error: We should be able to detect a error of 1/N_atoms
    maxtemperr = 2/3 * 3/atoms.get_number_of_degrees_of_freedom()
    # ... but not if we don't have good statistics.
    if parallel:
        maxtemperr *= 20  # System is much larger and run is shorter
    elif failfluct:
        maxtemperr *= 4
    maxperr = 0.03

    print(f'Observed average temperature:  {avgT:.2f} K   (expected {T0:.2f} K)')
    print(f'Error: {(avgT / T0 - 1) * 100:.1f}%  (max: {maxtemperr * 100:.1f}%)')
    ReportTest('Temperature', avgT, T0, T0 * maxtemperr)

    obstress = ' '.join([f'{s/GPa:.3f}' for s in avgstr])
    print(f'Observed average stress [{obstress}] GPa')
    print(f'Observed average pressure:  {avgP/GPa:.3f} GPa   (expected {p0/GPa:.3f} GPa)')
    print(f'Error: {(avgP / p0 - 1) * 100:.3f}%  (max: {maxperr * 100:.1f}%)')
    ReportTest('Pressure', avgP, p0, p0 * maxperr)

    print('Center of mass before:', com_before)
    print('Center of mass after: ', com_after)

    if plot:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.plot(times, pressures, 'b.')
        if not parallel:
            ax.plot(times, exponential(times, DeltaPfit, taup_fit, P_fit), 'k-')
        ax.plot([times[0], times[-1]], [p0, p0], 'k:')
        ax.set_title('Pressure during initial phase')
        fig2, ax2 = plt.subplots()
        ax2.plot(times2, temperatures2, 'b.')
        ax2.set_title('Temperature')
        fig3, ax3 = plt.subplots()
        ax3.plot(times2, pressures2, 'b.')
        ax3.plot([times2[0], times2[-1]], [p0, p0], 'k:')
        ax3.set_title('Pressure')
        plt.show(block=True)


def main(dynmaker, rng, repeat=1, plot=False, sloppytime=False, failfluct=False,
         initdyn=None, parallel=False):
    T0 = 300
    p0 = 2.0 * GPa
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
        c = atoms.cell 
        c[0,0] *= 0.998
        c[1,1] *= 1.002
        atoms.cell = c
        test_npt(atoms, nsteps, dt, T0, p0, dynmaker=dynmaker, initdyn=initdyn,
                 rng=rng, plot=plot, sloppytime=sloppytime, failfluct=failfluct,
                 parallel=parallel)
    if parallel:
        world.barrier()  # Needed if plotting, at least.

if __name__ == "__main__":
    print("This it not a test, but a module imported from a few tests.")
