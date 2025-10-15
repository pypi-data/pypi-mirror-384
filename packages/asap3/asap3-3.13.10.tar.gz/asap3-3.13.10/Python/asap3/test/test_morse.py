import numpy as np

from ase import Atoms, units
from ase.data import chemical_symbols, atomic_numbers
from ase.md import VelocityVerlet
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
from ase.lattice.cubic import SimpleCubic
from asap3 import Morse
from asap3.test.pytest_markers import ReportTest, serial

import pytest

#from calculators.morse import MorsePotential as Morse

# Define constants and calculator
@pytest.fixture
def elements():
    return np.array([atomic_numbers['Ru'], atomic_numbers['Ar']])

@pytest.fixture
def epsilon():
    return np.array([[5.720, 0.092], [0.092, 0.008]])

@pytest.fixture
def alpha():
    return np.array([[1.475, 2.719], [2.719, 1.472]])

@pytest.fixture
def rmin():
    return np.array([[2.110, 2.563], [2.563, 4.185]])

@pytest.fixture
def rcut(rmin, alpha):
    return rmin.max() + 6.0 / alpha.min()

@serial
@pytest.mark.core
def test_potential_cutoff(elements, epsilon, alpha, rmin, rcut):
    for e1 in elements:
        for e2 in elements:
            calc = Morse(elements, epsilon, alpha, rmin)
            atoms = Atoms([e1, e2], [[0.0, 0.0, 0.0], [rcut + 1.0, 0.0, 0.0]])
            atoms.center(vacuum=1.0)
            atoms.calc = calc

            energy = atoms.get_potential_energy()

            s1, s2 = chemical_symbols[e1], chemical_symbols[e2]
            ReportTest(f"Energy for {s1}-{s2} with r > rcut",
                       energy, 0.0, 1e-12)

@serial
@pytest.mark.core
def test_potential_minimum(elements, epsilon, alpha, rmin, rcut):
    for i, e1 in enumerate(elements):
        for j, e2 in enumerate(elements):
            calc = Morse(elements, epsilon, alpha, rmin)
            atoms = Atoms([e1, e2], [[0.0, 0.0, 0.0], [rmin[i, j], 0.0, 0.0]])
            atoms.center(vacuum=1.0)
            atoms.calc = calc

            energy = atoms.get_potential_energy()

            s1, s2 = chemical_symbols[e1], chemical_symbols[e2]
            ReportTest(f"Energy for {s1}-{s2} with r = rmin",
                       energy, -epsilon[i, j], 1e-2)

@serial
def test_energy_conservation(elements, epsilon, alpha, rmin, rcut):
    calc = Morse(elements, epsilon, alpha, rmin)
    atoms = SimpleCubic('Ar', size=(10,10,10), latticeconstant=5.0)
    n = 0
    while n < 100:
        i = np.random.randint(len(atoms)-1)
        if atoms[i].number != atomic_numbers['Ru']:
            atoms[i].number = atomic_numbers['Ru']
            n += 1
    atoms.calc = calc

    # Set initial momentum
    MaxwellBoltzmannDistribution(atoms, temperature_K=300)

    # Run dynamics
    dyn = VelocityVerlet(atoms, 1.0 * units.fs, logfile='test-energy.dat', loginterval=10)
    dyn.run(10)
    etot = (atoms.get_potential_energy() + atoms.get_kinetic_energy())/len(atoms)
    print("%-9s %-9s %-9s" % ("Epot", "Ekin", "Sum"))
    for i in range(25):
        if i:
            dyn.run(100)
        epot = atoms.get_potential_energy()/len(atoms)
        ekin = atoms.get_kinetic_energy()/len(atoms)
        print(f"{epot:9.5f} {ekin:9.5f} {epot+ekin:9.5f}")
        ReportTest("Step %i." % (i,), epot+ekin, etot, 1e-3)
