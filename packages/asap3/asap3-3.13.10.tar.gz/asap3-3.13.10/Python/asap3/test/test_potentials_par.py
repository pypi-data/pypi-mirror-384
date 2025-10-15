from asap3 import EMT, EMT2013, Morse, LennardJones
from asap3.EMT2013Parameters import sihb_PtY_parameters as PtY_EMT2013
import asap3
from ase.lattice.cubic import FaceCenteredCubic
from ase.lattice.compounds import L1_2
from ase.data import atomic_numbers, reference_states
from asap3.test.pytest_markers import parallel
from ase.parallel import world

import numpy as np

import os
import pickle

import pytest

pytestmark = [pytest.mark.core, ]

@pytest.fixture
def results(datadir):
    resultname = 'parallelPotentials.pickle'
    with open(datadir / resultname, 'rb') as resfile:
        return pickle.load(resfile, encoding='latin1')
    
def ljpot():
    return LennardJones([29], [0.15], [2.7], 3*2.7, False)

def morse():
    return Morse(
        elements = np.array([atomic_numbers['Ru'], atomic_numbers['Ar']]),
        epsilon = np.array([[5.720, 0.092], [0.092, 0.008]]),
        alpha = np.array([[1.475, 2.719], [2.719, 1.472]]),
        rmin = np.array([[2.110, 2.563], [2.563, 4.185]])
    )

parameters = [
    # name, element(s), pbc, calculator, stress
    ['Cu EMT periodic', 'Cu', True, EMT(), True],
    ['Cu EMT free', 'Cu', False, EMT(), True],
    ['Cu EMT mixed', 'Cu', (1,1,0), EMT(), True],
    ['AuCu3 EMT periodic', ('Au', 'Cu'), True, EMT(), True],
    ['AuCu3 EMT free', ('Au', 'Cu'), False, EMT(), True],
    ['LennardJones periodic', 'Cu', True, ljpot(), True],
    ['LennardJones free', 'Cu', False, ljpot(), True],
    ['LennardJones mixed', 'Cu', (1,1,0), ljpot(), True],
    ['Morse periodic', 'Ar', True, morse(), False],
    ['Morse free', 'Ar', False, morse(), False],
    ['Morse mixed', 'Ar', (0,1,0), morse(), False],
    ['EMT2013 Pt3Y periodic', ('Y', 'Pt'), True, EMT2013(PtY_EMT2013), True],
    ['EMT2013 Pt3Y free', ('Y', 'Pt'), False, EMT2013(PtY_EMT2013), True],
    ['EMT2013 Pt3Y mixed', ('Y', 'Pt'), (0,0,1), EMT2013(PtY_EMT2013), True],
]

@pytest.mark.skipif(world.size not in (1, 2, 4, 8), reason='Number of cores must be 1,2,4 or 8')
@pytest.mark.parametrize('name,elements,pbc,calculator,stress',
                         parameters, ids=[x[0] for x in parameters])
def test_potential_par(name, elements, pbc, calculator, stress, results, cpulayout):
    if isinstance(elements, tuple):
        atoms = myalloy(elements, pbc, cpulayout)
    else:
        atoms = myfcc(elements, pbc, cpulayout)
    atoms.calc = calculator
    dotest(atoms, name, results, dostress=stress)

def myfcc(symbol, pbc, cpulayout):
    "Make an fcc lattice with standard lattice constant"
    if world.rank == 0:
        a = FaceCenteredCubic(symbol=symbol, size=(10,10,10), pbc=pbc)    
        dx = 0.01 * np.sin(0.1 * np.arange(len(a) * 3))
        dx.shape = (len(a),3)
        a.set_positions(a.get_positions() + dx)
        a.set_momenta(np.zeros((len(a),3)))
    else:
        a = None
    if world.size > 1:
        a = asap3.MakeParallelAtoms(a, cpulayout)
    return a

def myalloy(symbols, pbc, cpulayout):
    "Create an L1_2 alloy (AB3)."
    a1 = reference_states[atomic_numbers[symbols[0]]]['a']
    a2 = reference_states[atomic_numbers[symbols[1]]]['a']
    a0 = (a1 + 3*a2)/4
    if world.rank == 0:
        a = L1_2(symbol=symbols, size=(10,10,10), latticeconstant=a0, pbc=pbc)    
        dx = 0.01 * np.sin(0.1 * np.arange(len(a) * 3))
        dx.shape = (len(a),3)
        a.set_positions(a.get_positions() + dx)
        a.set_momenta(np.zeros((len(a),3)))
    else:
        a = None
    if world.size > 1:
        a = asap3.MakeParallelAtoms(a, cpulayout)
    return a
    
    
def dotest(atoms, name, results, dostress=True):
    energy = atoms.get_potential_energy()
    forces = atoms.get_forces()
    positions = atoms.get_positions()
    if dostress:
        stresses = atoms.get_stresses()
        stress = atoms.get_stress()
    if world.size > 1:
        ids = atoms.get_ids()
    else:
        ids = np.arange(len(atoms))
    
    # Test that we still get the same
    data = results[name]
    assert np.isclose(energy, data['energy'], atol=1e-9), name + ' (energy)'
    compare(name, 'forces', forces, data['forces'], ids)
    compare(name, 'positions', positions, data['positions'], ids)
    if dostress:
        for i in range(6):
            assert np.isclose(stress[i], data['stress'][i], atol=1e-9), name + f'(stress {i})' 
        compare(name, 'stresses', stresses, data['stresses'], ids)

        
def compare(name, quantity, a, b, ids):
    keep = 50   # Keep every 50 data point
    for i in range(len(a)):
        ii = ids[i]
        if ii % keep == 0:
            x = a[i]
            y = b[ii // keep]
            for j in range(len(x)):
                testname = '%i %s (%s[%i,%i])' % (world.rank, name, quantity, ii, j)
                assert np.isclose(x[j], y[j], atol=1e-10), testname

