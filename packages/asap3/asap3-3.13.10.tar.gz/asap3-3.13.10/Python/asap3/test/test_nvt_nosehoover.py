import numpy as np
from asap3.test.nvt_module import main
from asap3.md.nvtberendsen import NVTBerendsen
import ase

from asap3.test.pytest_markers import serial, parallel
from ase.parallel import world

import pytest

@pytest.mark.slow
@serial
@pytest.mark.skipif(ase.__version__ < '3.25.0', reason='ASE is too old.')
def test_nvt_nosehoover():
    from asap3.md.nose_hoover_chain import NoseHooverChainNVT

    def nhdynmaker(atoms, T0, dt, tau, rng, logint):
        return NoseHooverChainNVT(atoms, dt, temperature_K=T0, tdamp=tau, logfile='-', loginterval=logint)

    def berdynmaker(atoms, T0, dt, tau, rng, logint):
        return NVTBerendsen(atoms, timestep=dt, temperature_K=T0, taut=tau, logfile='-', loginterval=logint)

    rng = np.random.default_rng(2718281828459045)   # Use a fixed seed for reproducability
    #rng = np.random.default_rng()

    main(nhdynmaker, rng, initdyn=berdynmaker)

@pytest.mark.slow
@parallel
@pytest.mark.skipif(ase.__version__ < '3.25.0', reason='ASE is too old.')
def test_par_nvt_nosehoover():
    from asap3.md.nose_hoover_chain import NoseHooverChainNVT

    def nhdynmaker(atoms, T0, dt, tau, rng, logint):
        return NoseHooverChainNVT(atoms, dt, temperature_K=T0, tdamp=tau, logfile='-', loginterval=logint)

    def berdynmaker(atoms, T0, dt, tau, rng, logint):
        return NVTBerendsen(atoms, timestep=dt, temperature_K=T0, taut=tau, logfile='-', loginterval=logint)

    seed = np.random.SeedSequence(2718281828459045)
    seed = seed.spawn(world.size)[world.rank]
    rng = np.random.default_rng(seed)   # Use a fixed seed for reproducability

    main(nhdynmaker, rng, initdyn=berdynmaker, parallel=True, sloppytime=True, failfluct=True)
    # Note: Fluctuation test always fail in parallel, as the boundaries
    # are free in order to test the migration better.  But that changes the
    # heat capacity, making the test fail.
