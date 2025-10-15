import numpy as np
from asap3.test.npt_module import main, bulkmodulus, MDLogger
try:
    from asap3.md.nose_hoover_chain import MTKNPT
except ImportError:
    MTKNPT = None
from asap3.md.nptberendsen import NPTBerendsen

from asap3.test.pytest_markers import serial, parallel

import pytest

@pytest.mark.slow
@serial
@pytest.mark.skipif(MTKNPT is None, reason='ASE is too old')
def test_npt_mtk():
    def mktdynmaker(atoms, T0, p0, dt, *, taut, taup, rng, logint):
        dyn = MTKNPT(atoms, timestep=dt, temperature_K=T0, pressure_au=p0, 
                            tdamp=taut, pdamp=taup)
        log = MDLogger(dyn, atoms, '-', peratom=True, stress=True)
        dyn.attach(log, interval=logint)
        return dyn

    def berdynmaker(atoms, T0, p0, dt, *, taut, taup, rng, logint):
        dyn = NPTBerendsen(atoms, timestep=dt, temperature_K=T0, pressure_au=p0, 
                        taut=taut, taup=taup, compressibility_au=1 / bulkmodulus)
        log = MDLogger(dyn, atoms, '-', peratom=True, stress=True)
        dyn.attach(log, interval=logint)
        return dyn

    rng = np.random.default_rng(3141592)
    main(mktdynmaker, rng, initdyn=berdynmaker, failfluct=True)


@pytest.mark.slow
@parallel
@pytest.mark.skipif(MTKNPT is None, reason='ASE is too old')
def test_par_npt_mtk():
    def mktdynmaker(atoms, T0, p0, dt, *, taut, taup, rng, logint):
        dyn = MTKNPT(atoms, timestep=dt, temperature_K=T0, pressure_au=p0, 
                            tdamp=taut, pdamp=taup)
        log = MDLogger(dyn, atoms, '-', peratom=True, stress=True)
        dyn.attach(log, interval=logint)
        return dyn

    def berdynmaker(atoms, T0, p0, dt, *, taut, taup, rng, logint):
        dyn = NPTBerendsen(atoms, timestep=dt, temperature_K=T0, pressure_au=p0, 
                        taut=taut, taup=taup, compressibility_au=1 / bulkmodulus)
        log = MDLogger(dyn, atoms, '-', peratom=True, stress=True)
        dyn.attach(log, interval=logint)
        return dyn

    rng = np.random.default_rng(314159265)
    main(mktdynmaker, rng, initdyn=berdynmaker, failfluct=True, parallel=True)
