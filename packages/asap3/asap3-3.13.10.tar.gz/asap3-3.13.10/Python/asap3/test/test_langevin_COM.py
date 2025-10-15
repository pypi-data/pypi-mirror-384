from ase import units
from ase.build import bulk
from asap3 import EMT
from asap3.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3.md.velocitydistribution import Stationary
from asap3.md.langevin import Langevin
from numpy.linalg import norm
from asap3.test.pytest_markers import serial
import numpy as np

import pytest

# parameters
size = 2
T = 300
dt = 0.01

# setup
@pytest.fixture
def atoms():
    atoms = bulk('CuAg', 'rocksalt', a=4.0).repeat(size)
    atoms.pbc = False
    atoms.calc = EMT()
    return atoms

@serial
@pytest.mark.core
@pytest.mark.parametrize('forcease', (False, True))
def test_langevin_com(forcease, atoms):
    MaxwellBoltzmannDistribution(atoms, temperature_K=T)
    Stationary(atoms)
    dyn = Langevin(atoms, dt * units.fs, temperature_K=T, friction=0.02, forceASE=forcease)
    
    # run NVT
    mtot = atoms.get_momenta().sum(axis=0)

    print('initial momenta', mtot)
    print('initial forces', atoms.get_forces().sum(axis=0))

    dyn.run(10)

    m2 = atoms.get_momenta().sum(axis=0)
    print('momenta', m2)
    print('forces', atoms.get_forces().sum(axis=0))
    print()

    assert norm(m2) < 1e-8, f'Langevin changed center of mass with forceASE={forcease}'
