import numpy as np
from asap3.test.nvt_module import main
from asap3.md.nvtberendsen import NVTBerendsen

from asap3.test.pytest_markers import serial, parallel
from ase.parallel import world

import pytest

## @pytest.mark.slow    # Not marked as slow so a single nvt test runs normally
@serial
def test_nvt_berendsen():
    def berdynmaker(atoms, T0, dt, tau, rng, logint):
        return NVTBerendsen(atoms, timestep=dt, temperature_K=T0, taut=tau, logfile='-', loginterval=logint)

    rng = np.random.default_rng(2718281828459045)   # Use a fixed seed for reproducability
    #rng = np.random.default_rng()
    main(berdynmaker, rng, failfluct=True)

@pytest.mark.slow
@parallel
def test_par_nvt_berendsen():
    def berdynmaker(atoms, T0, dt, tau, rng, logint):
        return NVTBerendsen(atoms, timestep=dt, temperature_K=T0, taut=tau, logfile='-', loginterval=logint)

    #rng = np.random.default_rng(2718281828459045)   # Use a fixed seed for reproducability
    rng = np.random.default_rng()
    main(berdynmaker, rng, failfluct=True,  parallel=True)
