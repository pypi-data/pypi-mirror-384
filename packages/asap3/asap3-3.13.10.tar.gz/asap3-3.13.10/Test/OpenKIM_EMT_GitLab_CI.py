# Version of OpenKIM_EMT.py that fails if OpenKIM is not compiled in.
# Tests that OpenKIM support is correctly built on the GitLab CI.

from asap3 import *
from ase.lattice.cubic import FaceCenteredCubic
from asap3.testtools import ReportTest
from ase.build import bulk
import numpy as np
import itertools

openkimmodel = 'EMT_Asap_Standard_JacobsenStoltzeNorskov_1996_%s__%s'

shortkimid = {
    'Ag': 'MO_303974873468_001',
    'Al': 'MO_623376124862_001',
    'Au': 'MO_017524376569_001',
    'Cu': 'MO_396616545191_001',
    'Ni': 'MO_108408461881_001',
    'Pd': 'MO_066802556726_001',
    'Pt': 'MO_637493005914_001',
    }

#set_verbose(1)
step = 500

if getattr(Atoms, '_ase_handles_dynamic_stress', False):
    stresshack = {'include_ideal_gas': True}
else:
    stresshack = {}

pbc_list = itertools.cycle(((1,1,1), (0,0,0), (0,0,1)))
size_list = itertools.cycle(((10, 10, 10), (20, 5, 2), (2, 2, 2), (1, 1, 1)))
elements = ('Al', 'Ag', 'Au', 'Cu', 'Ni', 'Pd', 'Pt')

for element in elements:
    for i in (0, 1):
        pbc = next(pbc_list)
        size = next(size_list)
        txt = ("%s=%i%i%i-%i-%i-%i " % ((element,) + pbc + size))
        # Test that EMT reimported through OpenKIM gives the right results.
        atoms_kim = bulk(element).repeat(size)
        #atoms_kim = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
        #                    size=(30, 30, 30),
        #                    symbol="Cu")
        natoms = len(atoms_kim)
        atoms_kim.set_pbc(pbc)
        r = atoms_kim.get_positions()
        r.flat[:] += 0.1 * np.sin(np.arange(3*natoms))
        atoms_kim.set_positions(r)
        atoms_emt = atoms_kim.copy()
        try:
            kim = OpenKIMcalculator(openkimmodel % (element, shortkimid[element]))
        except AsapError as oops:
           if oops.args[0].startswith('Failed to initialize OpenKIM model'):
               print("OpenKIM model {} not installed - skipping test.".format(
                   openkimmodel % (element, shortkimid[element])))
               continue
           else:
               raise   # Something else went wrong.
        emt = EMT()
        emt.set_subtractE0(False)
        atoms_kim.calc = kim
        atoms_emt.calc = emt
        ek = atoms_kim.get_potential_energy()
        ee = atoms_emt.get_potential_energy()
        ReportTest(txt+"Total energy", ek, ee, 1e-8)
        ek = atoms_kim.get_potential_energies()
        ee = atoms_emt.get_potential_energies()
        for i in range(0, natoms, step):
            ReportTest(txt+"Energy of atom %i" % (i,), ek[i], ee[i], 1e-8)
        fk = atoms_kim.get_forces()
        fe = atoms_emt.get_forces()
        n = 0
        for i in range(0, natoms, step):
            n = (n + 1) % 3
            ReportTest(txt+"Force(%i) of atom %i" % (n, i), fk[i, n], fe[i, n], 1e-8)
        sk = atoms_kim.get_stress(**stresshack)
        se = atoms_emt.get_stress(**stresshack)
        for i in range(6):
            ReportTest(txt+"Stress(%i)" % (i,), sk[i], se[i], 1e-8)
        sk = atoms_kim.get_stresses(**stresshack)
        se = atoms_emt.get_stresses(**stresshack)
        for i in range(0, natoms, step):
            n = (n + 1) % 6
            # Volume per atom is not defined the same way: greater tolerance needed
            ReportTest(txt+"Stress(%i) of atom %i" % (n, i), sk[i, n], se[i, n], 1e-3)
    
ReportTest.Summary()
