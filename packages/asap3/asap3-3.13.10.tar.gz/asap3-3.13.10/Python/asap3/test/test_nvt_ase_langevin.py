import numpy as np
from nvt_module import main
from ase.md.langevin import Langevin
from asap3.md.langevin import ASE_Langevin

from asap3.test.pytest_markers import serial, parallel
from ase.parallel import world

import pytest

@pytest.mark.slow
@serial
def test_nvt_ase_langevin():
    def lgvdynmaker(atoms, T0, dt, tau, rng, logint):
        # tau is the energy relaxation time.  The velocity relaxation time
        # should be the double.

        return Langevin(atoms, dt, temperature_K=T0, friction=1/(2*tau), logfile='-', loginterval=logint, rng=rng)

    rng = np.random.default_rng(271828182845904523)   # Use a fixed seed for reproducability
    main(lgvdynmaker, rng, sloppytime=True)

@pytest.mark.slow
@parallel
def test_par_nvt_ase_langevin():
    def lgvdynmaker(atoms, T0, dt, tau, rng, logint):
        # tau is the energy relaxation time.  The velocity relaxation time
        # should be the double.

        # Cannot pass the rng to Asap's Langevin, instead use it to create a seed
        seed = rng.integers(0, 1 << 30)
        print(f'Seed: {seed}')
        return ASE_Langevin(atoms, dt, temperature_K=T0, friction=1/(2*tau), logfile='-', loginterval=logint, seed=seed)

    seed = np.random.SeedSequence(2718281828459045)
    seed = seed.spawn(world.size)[world.rank]
    rng = np.random.default_rng(seed)   # Use a fixed seed for reproducability

    main(lgvdynmaker, rng, parallel=True, sloppytime=True, failfluct=True)
    # Note: Fluctuation test always fail in parallel, as the boundaries
    # are free in order to test the migration better.  But that changes the
    # heat capacity, making the test fail.
