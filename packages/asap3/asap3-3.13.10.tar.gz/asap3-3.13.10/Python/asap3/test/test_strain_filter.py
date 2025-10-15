from ase.filters import StrainFilter
from ase.optimize import MDMin
from asap3 import EMT, Langevin, Atoms, units
from ase.lattice.cubic import FaceCenteredCubic
from asap3.test.pytest_markers import ReportTest, serial
import numpy as np

import pytest

if getattr(Atoms, '_ase_handles_dynamic_stress', False):
    stresshack = {'include_ideal_gas': True}
else:
    stresshack = {}

@serial
def test_strainfilter():
    size = 5
    atoms = FaceCenteredCubic(size=(size,size,size), symbol="Cu", pbc=True)
    defsize = atoms.get_volume()
    atoms.set_cell(atoms.get_cell() * 1.1, scale_atoms=True)
    atoms.calc = EMT()

    def printvol(a):
        print("Volume:", a.get_volume(), " energy:",\
            atoms.get_potential_energy() + atoms.get_kinetic_energy(),\
            " stress:", atoms.get_stress(include_ideal_gas=True)[:3])

    f = StrainFilter(atoms, [1, 1, 1, 0, 0, 0], include_ideal_gas=True)
    opt = MDMin(f, logfile="/dev/null", dt=0.01/(atoms.get_cell()[0,0]))
    printvol(atoms)
    opt.attach(printvol, 10, atoms)
    opt.run(0.01)
    printvol(atoms)
    print("Original vol:", defsize)
    print()
    stress = atoms.get_stress(include_ideal_gas=True)
    for i in range(6):
        ReportTest("Stress component %d (T=0)" % (i,), stress[0], 0.0, 1e-5)

    atoms = FaceCenteredCubic(size=(size,size,size), symbol="Cu", pbc=True)
    atoms.calc = EMT()
    dyn = Langevin(atoms, 10*units.fs, temperature_K=500, friction=0.02)
    dyn.attach(printvol, 100, atoms)
    dyn.run(500)

    print()

    f = StrainFilter(atoms, [1, 1, 1, 0, 0, 0], include_ideal_gas=True)
    opt = MDMin(f, logfile="/dev/null", dt=0.01/(atoms.get_cell()[0,0]))
    printvol(atoms)
    opt.attach(printvol, 10, atoms)
    opt.run(0.01)
    printvol(atoms)
    print("Original vol:", defsize)
    print()

    stress = atoms.get_stress(include_ideal_gas=True)
    for i in range(6):
        ReportTest("Stress component %d (T=500K)" % (i,), stress[0], 0.0, 1e-5)
