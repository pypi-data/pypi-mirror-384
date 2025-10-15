'Test that the memory_usage() function does not crash.'

from asap3 import EMT, memory_usage
from ase.lattice.cubic import FaceCenteredCubic
from asap3.test.pytest_markers import serial

import pytest

@serial
def test_memory_usage():
    print("Making atoms")
    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                            size=(25,25,25), symbol="Cu")
    memory_usage(atoms)

    print("Attaching EMT potential")
    atoms.calc = EMT()
    memory_usage(atoms)

    print("Calculating forces")
    atoms.get_forces()
    memory_usage(atoms)

    print("Test passed!")
