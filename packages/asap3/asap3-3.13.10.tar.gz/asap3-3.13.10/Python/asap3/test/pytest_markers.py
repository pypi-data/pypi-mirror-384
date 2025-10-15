import pytest
from ase.parallel import world
import asap3
import numpy as np

serial = pytest.mark.skipif(world.size > 1, reason='test is serial')
parallel = pytest.mark.skipif(world.size == 1, reason='test is parallel')
withmpi = pytest.mark.skipif(not asap3.parallelpossible, reason='Asap is not compiled with MPI support')
withOpenKIM = pytest.mark.skipif(not asap3.OpenKIMsupported, reason='Asap not compiled with OpenKIM')

# Default name of OpenKIM model is defined here, so it can be used outside fixtures.
_openkimmodel = 'EMT_Asap_Standard_JacobsenStoltzeNorskov_1996_AlAgAuCuNiPdPt__MO_115316750986_001'

def ReportTest(name, value, expected, atol):
    'A simple wrapper to avoid editing old tests.'
    assert np.isclose(value, expected, atol=atol), name
