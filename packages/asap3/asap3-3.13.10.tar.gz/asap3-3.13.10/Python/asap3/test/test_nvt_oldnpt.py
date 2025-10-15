import numpy as np
from asap3.test.nvt_module import main
from asap3.md.npt import NPT
from asap3.md.nvtberendsen import NVTBerendsen

from asap3.test.pytest_markers import serial, parallel
from ase.parallel import world

import pytest

@pytest.mark.slow
@serial
def test_nvt_oldnpt():
    def nptdynmaker(atoms, T0, dt, tau, rng, logint):
        return NPT(atoms, timestep=dt, temperature_K=T0, ttime=tau, logfile='-', loginterval=logint)

    def berdynmaker(atoms, T0, dt, tau, rng, logint):
        return NVTBerendsen(atoms, timestep=dt, temperature_K=T0, taut=tau, logfile='-', loginterval=logint)

    rng = np.random.default_rng(2718281828459045)   # Use a fixed seed for reproducability
    #rng = np.random.default_rng()
    main(nptdynmaker, rng, initdyn=berdynmaker, failfluct=True)
