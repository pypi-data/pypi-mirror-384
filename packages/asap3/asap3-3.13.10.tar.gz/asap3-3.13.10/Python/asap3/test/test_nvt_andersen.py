import numpy as np
from nvt_module import main
from ase.md.andersen import Andersen
import ase

from asap3.test.pytest_markers import serial, parallel
from ase.parallel import world

import pytest

@pytest.mark.slow
@serial
@pytest.mark.skipif(ase.__version__ < '3.24.0', reason='ASE is too old')
def test_nvt_andersen():
    def anddynmaker(atoms, T0, dt, tau, rng, logint):
        # tau is the energy relaxation time.  The velocity relaxation time
        # should be the double.
        aprob = dt / tau
        return Andersen(atoms, dt, temperature_K=T0, andersen_prob=aprob, logfile='-', loginterval=logint, rng=rng)

    rng = np.random.default_rng(2718281828459045)   # Use a fixed seed for reproducability
    #rng = np.random.default_rng()
    main(anddynmaker, rng, sloppytime=True)
