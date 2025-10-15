from asap3 import EMT, EMT2013, OpenKIMsupported
if OpenKIMsupported:
    from asap3 import OpenKIMcalculator
from asap3.EMT2013Parameters import sihb_PtY_parameters
from ase.lattice.cubic import FaceCenteredCubic
from ase.lattice.compounds import L1_2
from ase.data import reference_states, atomic_numbers
from asap3.test.pytest_markers import ReportTest, serial, _openkimmodel
import numpy as np

import pytest


# Using fixtures is possible but inconvenient when parametrizing test,
# and since nothing is really gained we just use normal functions.
def make_L1_2(symbol, size, pbc):
    lc = [reference_states[atomic_numbers[s]]['a'] for s in symbol]
    lc = (3*lc[0] + lc[1])/4.0
    return L1_2(symbol=symbol, size=size, latticeconstant=lc, pbc=pbc)

testtypes = [
    # element, structure, pot, potargs, lefthanded, name
    ('Au', FaceCenteredCubic, EMT, (), False, 'EMT'),
    (('Au', 'Ag'), make_L1_2, EMT, (), False, 'EMT(alloy)'),
    ('Au', FaceCenteredCubic, EMT, (), True, 'EMT(lefthanded)'),
    ('Pt', FaceCenteredCubic, EMT2013, (sihb_PtY_parameters,), False, 'EMT2013'),
    (('Y', 'Pt'), make_L1_2, EMT2013, (sihb_PtY_parameters,), False, 'EMT2013(alloy)')
]
if OpenKIMsupported:
    testtypes += [
        ('Au', FaceCenteredCubic, OpenKIMcalculator, (_openkimmodel,), False, 'OpenKIM'),
    ]

@serial
@pytest.mark.parametrize('element,makestructure,pot,potargs,lefthanded,_', 
                         testtypes, ids=[x[-1] for x in testtypes])
def test_size_consistent(element, makestructure, pot, potargs, lefthanded, _):
    sizes = np.arange(10,0,-1)

    energy = None
    force = None
    for s in sizes:
        atoms = makestructure(symbol=element, size=(s,s,s), pbc=True)
        if lefthanded:
            uc = atoms.get_cell()
            uc[2] *= -1.0
            atoms.set_cell(uc, scale_atoms=True)
        r = atoms.get_positions()
        for i in range(0, len(r), 4):
            r[i][0] += 0.1
        atoms.set_positions(r)
        atoms.calc = pot(*potargs)
        e = atoms.get_potential_energy() / len(atoms)   
        print("%5i atoms: E = %.5f eV/atom" % (len(atoms), e))
        if energy is None:
            energy = e
        else:
            ReportTest("Energy for size %i (%i atoms)" % (s, len(atoms)),
                    e, energy, 1e-8)
        f = atoms.get_forces()
        if force is None:
            force = f[:4]
        else:
            for i in range(len(f)):
                for j in range(3):
                    ReportTest("Force for size %i atom %i of %i component %i"
                            % (s, i, len(atoms), j),
                            f[i,j], force[i % 4, j], 1e-8)
        del atoms