import numpy as np

from ase import Atoms, units
from ase.data import atomic_numbers
from asap3 import Morse, PropertyNotImplementedError
from asap3.test.pytest_markers import serial

import pytest

@serial
@pytest.mark.core
def test_notimplemented():
    # Define constants and calculator
    elements = np.array([atomic_numbers['Ru'], atomic_numbers['Ar']])
    epsilon = np.array([[5.720, 0.092], [0.092, 0.008]])
    alpha = np.array([[1.475, 2.719], [2.719, 1.472]])
    rmin = np.array([[2.110, 2.563], [2.563, 4.185]])
    rcut = rmin.max() + 6.0 / alpha.min()

    calc = Morse(elements, epsilon, alpha, rmin)
    atoms = Atoms(['Ar', 'Ar'], [[0.0, 0.0, 0.0], [rcut + 1.0, 0.0, 0.0]])
    atoms.center(vacuum=10.0)
    atoms.set_pbc(True)
    atoms.calc = calc

    # This should not fail
    energy = atoms.get_potential_energy()

    #This should fail
    with pytest.raises(PropertyNotImplementedError):
        stress = atoms.get_stress()

