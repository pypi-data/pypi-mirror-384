import numpy as np
from asap3.test.nvt_module import main
try:
    from asap3.md.bussi import Bussi
except ImportError:
    Bussi = None

from asap3.test.pytest_markers import serial, parallel
from ase.parallel import world

import pytest

@pytest.mark.slow
@serial
@pytest.mark.skipif(Bussi is None, reason='ASE is too old')
def test_nvt_bussi():
    def busdynmaker(atoms, T0, dt, tau, rng, logint):
        # tau is the energy relaxation time.  The velocity relaxation time
        # should be the double.
        return Bussi(atoms, dt, temperature_K=T0, taut=tau, logfile='-', loginterval=logint, rng=rng)

    rng = np.random.default_rng(2718281828459045)   # Use a fixed seed for reproducability
    #rng = np.random.default_rng()

    main(busdynmaker, rng, sloppytime=True)
    

# @pytest.mark.slow     # Not maked as slow so a single NVT test runs normally
@parallel
@pytest.mark.skipif(Bussi is None, reason='ASE is too old')
def test_par_nvt_bussi():
    def busdynmaker(atoms, T0, dt, tau, rng, logint):
        # tau is the energy relaxation time.  The velocity relaxation time
        # should be the double.
        dyn = Bussi(atoms, dt, temperature_K=T0, taut=tau, logfile='-', loginterval=logint, rng=rng)
        assert dyn.comm.size == world.size
        return dyn

    seed = np.random.SeedSequence(2718281828459045)
    seed = seed.spawn(world.size)[world.rank]
    rng = np.random.default_rng(seed)   # Use a fixed seed for reproducability

    main(busdynmaker, rng, parallel=True, sloppytime=True, failfluct=True)
    # Note: Fluctuation test always fail in parallel, as the boundaries
    # are free in order to test the migration better.  But that changes the
    # heat capacity, making the test fail.
