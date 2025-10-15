"""Test the FixAtoms constraint and the Subset filter."""

from asap3 import *
from ase.lattice.cubic import FaceCenteredCubic
from asap3.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3.md.verlet import VelocityVerlet
from asap3.md.nvtberendsen import NVTBerendsen
from asap3.constraints import FixAtoms, Filter
from ase.constraints import FixAtoms as ASE_FixAtoms
from asap3.test.pytest_markers import ReportTest, serial
from ase.parallel import world

import numpy as np

import pytest

def sanity(name, initial, final, fixed):
    print(f"Sanity check, {name}:")
    ok = (final == initial) + np.logical_not(fixed)[:,np.newaxis]
    assert ok.all(), 'Stationary atoms have not moved'
    ok = (final != initial) + fixed[:,np.newaxis]
    assert ok.all(), 'Mobile atoms have moved'

def sanity_parallel(name, atoms):
    initial = atoms.arrays['r_init']
    final = atoms.get_positions()
    fixed = atoms.get_tags().astype(bool)
    
    print(f"Sanity check, {name}:")
    ok = (final == initial) + np.logical_not(fixed)[:,np.newaxis]
    assert ok.all(), 'Stationary atoms have not moved'
    ok = (final != initial) + fixed[:,np.newaxis]
    assert ok.all(), 'Mobile atoms have moved'


@pytest.mark.parametrize('dynamics', ("Verlet", "NVTBerendsen", "Langevin"))
def test_change_constraint(dynamics, cpulayout):
    if cpulayout:
        # Parallel simulation
        if world.rank == 0:
            size = 5 * np.array(cpulayout)
            init = FaceCenteredCubic(size=size, symbol='Cu', pbc=False)
            z = init.get_positions()[:,2]
            fixedatoms = np.less(z, 0.501*z.max())
            print(len(init), sum(fixedatoms))
            MaxwellBoltzmannDistribution(init, temperature_K=6000)
            init.set_tags(fixedatoms)
        else:
            init = None
        nrun = 1000
    else:
        # Serial simulation
        init = FaceCenteredCubic(size=(10,10,10), symbol='Cu', pbc=False)
        z = init.get_positions()[:,2]
        fixedatoms = np.less(z, 0.501*z.max())
        print(len(init), sum(fixedatoms))
        init.set_tags(fixedatoms)
        MaxwellBoltzmannDistribution(init, temperature_K=2000)
        r_init = init.get_positions()
        nrun = 50

    print()
    print("Running simulation with Asap's FixAtoms")
    if cpulayout:
        atoms2 = MakeParallelAtoms(init, cpulayout)
        atoms2.arrays['r_init'] = atoms2.get_positions()
    else:
        atoms2 = Atoms(init)
    atoms2.calc = EMT()
    atoms2.set_constraint(FixAtoms(mask=atoms2.get_tags().astype(bool)))

    if dynamics == "Verlet":
        dyn = VelocityVerlet(atoms2, 3*units.fs)
    elif dynamics == "NVTBerendsen":
        dyn = NVTBerendsen(atoms2, 3*units.fs, temperature_K=2000, taut=200*units.fs)
    elif dynamics == "Langevin":
        dyn = Langevin(atoms2, 3*units.fs, temperature_K=2000, friction=1e-3)
    else:
        assert False
    dyn.run(50)
    r2 = atoms2.get_positions()

    if cpulayout:
        sanity_parallel(dynamics+"+FixAtoms", atoms2)
    else:
        sanity(dynamics+"+FixAtoms", r_init, r2, fixedatoms)

    x = r2[:,0]
    fixedatoms2 = np.less(x, 0.501 * x.max())
    atoms2.set_tags(fixedatoms2)
    atoms2.arrays['r_init'] = atoms2.get_positions()
    print(len(atoms2), sum(fixedatoms2))

    print("Running simulation with new FixAtoms")
    atoms2.set_constraint(FixAtoms(mask=fixedatoms2))
    #dyn = VelocityVerlet(atoms2, 2*units.fs)

    dyn.run(50)
    r3 = atoms2.get_positions()

    if cpulayout:
        sanity_parallel(dynamics+"+new-FixAtoms", atoms2)
    else:
        sanity(dynamics+"+new-FixAtoms", r2, r3, fixedatoms2)


if __name__ == '__main__':
    test_change_constraint('Verlet', [1, 1, world.size])

