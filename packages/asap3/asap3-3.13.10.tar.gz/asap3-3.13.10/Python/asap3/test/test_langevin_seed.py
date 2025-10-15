from ase.units import fs
from asap3 import EMT
from asap3.md.langevin import Langevin
from ase.build import fcc111
from asap3.test.pytest_markers import serial
import numpy as np

import pytest

@serial
@pytest.mark.parametrize('seed', [42, None])
def test_langevin_seed(seed):
    positions = []
    for _ in range(2):
        atoms = fcc111('Au', size=(3,3,3), vacuum=10.0)
        atoms.calc = EMT()

        dyn = Langevin(atoms, timestep=5.0*fs, temperature_K=300, friction=1e-1, seed=seed)
        dyn.run(1000)

        positions.append(atoms.get_positions())

    p1, p2 = positions
    is_pos_equal = np.allclose(p1, p2)
    print("Max difference:", abs(p1 - p2).max())
    if seed is None:
        assert not is_pos_equal, "Runs differ when not seeded"
    else:
        assert is_pos_equal, "Runs are equal when seeded"
