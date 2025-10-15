from asap3 import *
from ase.lattice.cubic import *
from asap3.test.pytest_markers import serial


import pytest

@serial
@pytest.mark.core
def test_exc_illegal_element():
    "Illegal elements are an error."
    atoms = FaceCenteredCubic(size=(10, 10, 10), symbol="Cu")
    z = atoms.get_atomic_numbers()
    z[7]=8
    atoms.set_atomic_numbers(z)

    with pytest.raises(AsapError):
        atoms.calc = EMT()
    
@serial
@pytest.mark.core
def test_exc_atoms_collide():
    "Atoms on top of each other."
    atoms = FaceCenteredCubic(size=(10, 10, 10), symbol="Cu")
    r = atoms.get_positions()
    r[10] = r[11]
    atoms.set_positions(r)
    atoms.calc = EMT()

    with pytest.raises(AsapError):
        e = atoms.get_potential_energy()


@serial
@pytest.mark.core
def test_exc_array_size():
    "Atoms with malformed array (size)."
    atoms = FaceCenteredCubic(size=(10, 10, 10), symbol="Cu")
    atoms.arrays['numbers'] = atoms.arrays['numbers'][:len(atoms)//2]

    with pytest.raises(AsapError):
        atoms.calc = EMT()
        e = atoms.get_potential_energy()


@serial
@pytest.mark.core
def test_exc_array_type():
    "Atoms with malformed array (type)."
    atoms = FaceCenteredCubic(size=(10, 10, 10), symbol="Cu")
    atoms.arrays['positions'] = atoms.arrays['positions'].astype(int)

    with pytest.raises(AsapError):
        atoms.calc = EMT()
        e = atoms.get_potential_energy()

