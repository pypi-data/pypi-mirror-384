"""Test the FixAtoms constraint and the Subset filter."""

from asap3 import EMT, Atoms, Langevin
from ase.lattice.cubic import FaceCenteredCubic
from asap3.md.velocitydistribution import MaxwellBoltzmannDistribution
from asap3.md.verlet import VelocityVerlet
from asap3.md.nvtberendsen import NVTBerendsen
from asap3.constraints import Filter
from asap3.constraints import FixAtoms
from ase.constraints import FixAtoms as ASE_FixAtoms
from asap3.test.pytest_markers import ReportTest, serial, parallel
from ase import units
from ase.parallel import world

import numpy as np

import pytest

@serial
@pytest.mark.core
def test_constraints():
    init = FaceCenteredCubic(size=(10,10,10), symbol='Cu', pbc=False)
    z = init.get_positions()[:,2]
    fixedatoms = np.less(z, 0.501*z.max())
    print(len(init), sum(fixedatoms))
    MaxwellBoltzmannDistribution(init, temperature_K=2000)

    print()
    print("Running simulation with Filter")
    atoms1 = Atoms(init)
    atoms1.calc = EMT()
    atoms1a = Filter(atoms1, mask=np.logical_not(fixedatoms))

    dyn = VelocityVerlet(atoms1a, 0.5*units.fs)
    dyn.run(50)
    r1 = atoms1.get_positions()

    print()
    print("Running simulation with Asap's FixAtoms")
    atoms2 = Atoms(init)
    atoms2.calc = EMT()
    atoms2.set_constraint(FixAtoms(mask=fixedatoms))

    dyn = VelocityVerlet(atoms2, 0.5*units.fs)
    dyn.run(50)
    r2 = atoms2.get_positions()

    print()
    print("Running simulation with ASE's FixAtoms")
    atoms3 = Atoms(init)
    atoms3.calc = EMT()
    # Just to be difficult, convert mask to indices
    indx = np.compress(fixedatoms, np.arange(len(atoms3)))
    assert len(indx) == fixedatoms.sum()
    atoms3.set_constraint(ASE_FixAtoms(indx))

    dyn = VelocityVerlet(atoms3, 0.5*units.fs)
    dyn.run(50)
    r3 = atoms2.get_positions()

    err = np.max(np.abs(r1 - r2).flat)
    print()
    print("Filter and Asap's FixAtoms:", err)
    ReportTest("Identical positions (Filter and Asap's FixAtoms)", err, 0.0, 1e-9)

    err = np.max(np.abs(r2 - r3).flat)
    print("ASE's and Asap's FixAtoms:", err)
    ReportTest("Identical positions (ASE's and Asap's FixAtoms)", err, 0.0, 1e-9)

    print()
    print("Running Langevin simulation with Asap's FixAtoms")
    atoms4 = Atoms(init)
    atoms4.calc = EMT()
    atoms4.set_constraint(FixAtoms(mask=fixedatoms))

    dyn = Langevin(atoms4, 0.5*units.fs, temperature_K=1000, friction=0.01)
    dyn.run(50)

    print()
    print("Running Langevin simulation with ASE's FixAtoms")
    atoms5 = Atoms(init)
    atoms5.calc = EMT()
    atoms5.set_constraint(ASE_FixAtoms(mask=fixedatoms))

    dyn = Langevin(atoms5, 0.5*units.fs, temperature_K=1000, friction=0.01)
    dyn.run(50)

    print()
    sanity = [[atoms1, "Verlet + Filter"],
            [atoms2, "Verlet + Asap's FixAtoms"],
            [atoms3, "Verlet + ASE's FixAtoms"],
            [atoms4, "Langevin + Asap's FixAtoms"],
            [atoms5, "Langevin + ASE's FixAtoms"],
            ]
    r_init = init.get_positions()
    for a, label in sanity:
        print(f"Sanity check, {label}:")
        ok = (a.get_positions() == r_init) + np.logical_not(fixedatoms)[:,np.newaxis]
        assert ok.all(), f'Stationary atoms have not moved ({label})'
        ok = (a.get_positions() != r_init) + fixedatoms[:,np.newaxis]
        assert ok.all(), f'Mobile atoms have moved ({label})'


@parallel
def test_par_constraints(cpulayout):
    from asap3 import MakeParallelAtoms

    ismaster = world.rank == 0
    isparallel = world.size != 1
    if ismaster:
        size = 5 * np.array(cpulayout)
        init = FaceCenteredCubic(size=size, symbol='Cu', pbc=False)
        z = init.get_positions()[:,2]
        fixedatoms = np.less(z, 0.501*z.max())
        print(len(init), sum(fixedatoms))
        MaxwellBoltzmannDistribution(init, temperature_K=6000)
        init.set_tags(fixedatoms)
    else:
        init = None

    print()
    print("Running simulation with Filter")
    atoms1 = MakeParallelAtoms(init, cpulayout)
    atoms1.arrays['r_init'] = atoms1.get_positions()
    atoms1.calc = EMT()
    atoms1a = Filter(atoms1, mask=np.logical_not(atoms1.get_tags()))

    dyn = VelocityVerlet(atoms1a, 3*units.fs)
    dyn.run(1000)

    print()
    print("Running simulation with Asap's FixAtoms")
    atoms2 = MakeParallelAtoms(init, cpulayout)
    atoms2.arrays['r_init'] = atoms2.get_positions()
    atoms2.calc = EMT()
    atoms2.set_constraint(FixAtoms(mask=atoms2.get_tags().astype(bool)))

    dyn = VelocityVerlet(atoms2, 3*units.fs)
    dyn.run(1000)

    print()
    print("Running NPTBerendsen simulation with Asap's FixAtoms")
    atoms3 = MakeParallelAtoms(init, cpulayout)
    atoms3.arrays['r_init'] = atoms3.get_positions()
    atoms3.calc = EMT()
    atoms3.set_constraint(FixAtoms(mask=atoms3.get_tags().astype(bool)))

    dyn = NVTBerendsen(atoms3, 3*units.fs, temperature_K=3000, taut=200*units.fs)
    dyn.run(1000)


    print()
    print("Running Langevin simulation with Asap's FixAtoms")
    atoms4 = MakeParallelAtoms(init, cpulayout)
    atoms4.arrays['r_init'] = atoms4.get_positions()
    atoms4.calc = EMT()
    atoms4.set_constraint(FixAtoms(mask=atoms4.get_tags().astype(bool)))

    dyn = Langevin(atoms4, 3*units.fs, temperature_K=3000, friction=0.01)
    dyn.run(1000)

    print()
    print("Running Verlet then Langevin simulation with Asap's FixAtoms")
    atoms5 = MakeParallelAtoms(init, cpulayout)
    atoms5.arrays['r_init'] = atoms5.get_positions()
    atoms5.calc = EMT()
    atoms5.set_constraint(FixAtoms(mask=atoms5.get_tags().astype(bool)))

    dyn = VelocityVerlet(atoms5, 3*units.fs)
    dyn.run(1000)

    dyn = Langevin(atoms5, 3*units.fs, temperature_K=3000, friction=0.01)
    dyn.run(1000)


    print()
    print("Running NVTBerendsen then Verlet simulation with Asap's FixAtoms")
    atoms6 = MakeParallelAtoms(init, cpulayout)
    atoms6.arrays['r_init'] = atoms6.get_positions()
    atoms6.calc = EMT()
    atoms6.set_constraint(FixAtoms(mask=atoms6.get_tags().astype(bool)))

    dyn = NVTBerendsen(atoms6, 3*units.fs, temperature_K=3000, taut=200*units.fs)
    dyn.run(1000)

    dyn = VelocityVerlet(atoms6, 3*units.fs)
    dyn.run(1000)


    print()
    print("Running Verlet then NVTBerendsen simulation with Asap's FixAtoms")
    atoms7 = MakeParallelAtoms(init, cpulayout)
    atoms7.arrays['r_init'] = atoms7.get_positions()
    atoms7.calc = EMT()
    atoms7.set_constraint(FixAtoms(mask=atoms7.get_tags().astype(bool)))

    dyn = VelocityVerlet(atoms7, 3*units.fs)
    dyn.run(1000)

    dyn = NVTBerendsen(atoms7, 3*units.fs, temperature_K=3000, taut=200*units.fs)
    dyn.run(1000)

    print()
    sanity = [[atoms1, "Verlet + Filter"],
              [atoms2, "Verlet + Asap's FixAtoms"],
              [atoms3, "NVTBerendsen + Asap's FixAtoms"],
              [atoms4, "Langevin + Asap's FixAtoms"],
              [atoms5, "Verlet + Langevin + Asap's FixAtoms"],
              [atoms6, "NVTBerendsen + Verlet + Asap's FixAtoms"],
              [atoms7, "Verlet + NVTBerendsen + Asap's FixAtoms"],
             ]
    for a, label in sanity:
        print(world.rank, f"Sanity check, {label}:")
        r_init = a.arrays['r_init']
        ok = (a.get_positions() == r_init) + np.logical_not(a.get_tags())[:,np.newaxis]
        assert ok.all(), 'Stationary atoms have not moved'
        ok = (a.get_positions() != r_init) + a.get_tags()[:,np.newaxis]
        ok.all(), 'Mobile atoms have moved: OK'

        
