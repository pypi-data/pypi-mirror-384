import asap3
import numpy as np
from ase.build import bulk
from ase.eos import EquationOfState
import numpy as np
from asap3.mpi import world
from asap3.test.pytest_markers import ReportTest, withOpenKIM, serial
import itertools

import pytest

def get_model(model):
    try:
        calc = asap3.OpenKIMcalculator(model)
    except asap3.AsapError as oops:
        if oops.args[0].startswith('Failed to initialize OpenKIM model'):
            print(f"OpenKIM model {model} not installed - skipping test.")
            calc = None
        else:
            raise
    return calc

if world.size == 1:
    sizes = [(1,1,1), (2,2,2), (5,5,5)]
else:
    sizes = [(25,25,25)]

@withOpenKIM
@pytest.mark.parametrize('size', sizes, ids=[x[0] for x in sizes])
def test_par_openKIM_Ar_Morse(cpulayout, size):
    model = 'ex_model_Ar_P_Morse'
    ismaster = world.rank == 0
    calc = get_model(model)
    if calc is not None:
        if ismaster:
            atoms = bulk('Ar', 'fcc', 5.26).repeat(size)
            print(atoms.cell)
        else:
            atoms = None
        if world.size > 1:
            atoms = asap3.MakeParallelAtoms(atoms, cpulayout)
        # calc = asap3.OpenKIMcalculator(model)   # Reuse of OpenKIM objects not yet supported.
        atoms.calc = calc

        e = atoms.get_potential_energy()/atoms.get_global_number_of_atoms()
        print("Potential energy:", e)
        ReportTest(f"Potential energy {str(size)}", e, -0.092798, 1e-5)

        eq_cell = atoms.get_cell()
        scales = np.linspace(0.97, 1.03, 7)
        energies = []
        volumes = []
        for s in scales:
            atoms.set_cell(s * eq_cell, scale_atoms=True)
            energies.append(atoms.get_potential_energy())
            volumes.append(atoms.get_volume())
        eos = EquationOfState(volumes, energies)
        v0, e0, B = eos.fit()
        v_cell = v0 * 4 / atoms.get_global_number_of_atoms()
        a0 = v_cell**(1/3)
        print("Lattice constant:", a0)
        print("Bulk modulus:", B)
        ReportTest(f"Lattice constant {str(size)}", a0, 5.2539, 1e-4)


@withOpenKIM
@pytest.mark.parametrize('size', sizes, ids=[x[0] for x in sizes])
def test_par_openKIM_multi_nbl(cpulayout, size):
    model = 'ex_model_Ar_SLJ_MultiCutoff'   # Requires multiple neighbor lists.
    ismaster = world.rank == 0
    calc = get_model(model)
    if calc is not None:
        if ismaster:
            atoms = bulk('Ar', 'fcc', 5.26).repeat(size)
        else:
            atoms = None
        if world.size > 1:
            atoms = asap3.MakeParallelAtoms(atoms, cpulayout)
        # calc = OpenKIMcalculator(model)   # Reuse of OpenKIM objects not yet supported.
        atoms.calc = calc

        e = atoms.get_potential_energy()/atoms.get_global_number_of_atoms()
        if ismaster:
            print("Potential energy:", e)
        ReportTest(f"Potential energy {str(size)}", e, -0.0104, 1e-6)

        eq_cell = atoms.get_cell()
        scales = np.linspace(0.99, 1.01, 7)
        energies = []
        volumes = []
        for s in scales:
            atoms.set_cell(s * eq_cell, scale_atoms=True)
            energies.append(atoms.get_potential_energy())
            volumes.append(atoms.get_volume())
        eos = EquationOfState(volumes, energies)
        v0, e0, B = eos.fit()
        v_cell = v0 * 4 / atoms.get_global_number_of_atoms()
        a0 = v_cell**(1/3)
        if ismaster:
            print("Lattice constant:", a0)
            print("Bulk modulus:", B)
        ReportTest(f"Lattice constant {str(size)}", a0, 5.26, 1e-5)


@withOpenKIM
@serial
# @pytest.mark.parametrize('reuse', (False, True))
def test_openkim_LJ_modify(reuse=False):
    # Reuseing does not work due to a neighborlist problem - should be fixed?
    model = 'LennardJones612_UniversalShifted__MO_959249795837_003'
    calc = get_model(model)
    p = calc.parameters
    # Get some parameters
    epsilon_He = p.get_parameter('epsilons', 'ut')[1,1]
    sigma_He = p.get_parameter('sigmas', 'ut')[1,1]
    # Set a parameter
    p['shift'] = 0

    helium = bulk("He", 'fcc', np.sqrt(2) * 2**(1/6) * sigma_He).repeat((5,5,5))
    helium.calc = calc

    e = helium.get_potential_energy() / len(helium)
    ReportTest("Helium energy", e, -8.24646294 * epsilon_He, 1e-6)

    if not reuse:
        calc2 = asap3.OpenKIMcalculator(model)
    else:
        calc2 = calc
    eps = calc2.parameters.get_parameter('epsilons', 'ut')
    eps[1,1] = 2 * epsilon_He
    calc2.parameters.set_parameter('epsilons', eps, 'ut')
    calc2.parameters['shift'] = 0

    if not reuse:
        helium.calc = calc2
    e2 = helium.get_potential_energy() / len(helium)

    ReportTest("Modified Helium energy", e2, 2*e, 1e-6)

emt_openkimmodel = 'EMT_Asap_Standard_JacobsenStoltzeNorskov_1996_%s__%s'

emt_shortkimid = {
    'Ag': 'MO_303974873468_001',
    'Al': 'MO_623376124862_001',
    'Au': 'MO_017524376569_001',
    'Cu': 'MO_396616545191_001',
    'Ni': 'MO_108408461881_001',
    'Pd': 'MO_066802556726_001',
    'Pt': 'MO_637493005914_001',
    }

if asap3.OpenKIMsupported:  
    elements = ('Al', 'Ag', 'Au', 'Cu', 'Ni', 'Pd', 'Pt')
else:
    elements = ()
pbc_list = ((1,1,1), (0,0,0), (0,0,1))
size_list = ((10, 10, 10), (20, 5, 2), (2, 2, 2), (1, 1, 1))

@withOpenKIM
@serial
@pytest.mark.parametrize('element', elements)
@pytest.mark.parametrize('pbc', pbc_list)
@pytest.mark.parametrize('size', size_list)
def test_openkim_emt(element, pbc, size):
    step = 500
    for i in (0, 1):
        #pbc = next(pbc_list)
        #size = next(size_list)
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
            kim = asap3.OpenKIMcalculator(emt_openkimmodel % (element, emt_shortkimid[element]))
        except asap3.AsapError as oops:
           if oops.args[0].startswith('Failed to initialize OpenKIM model'):
               print("OpenKIM model {} not installed - skipping test.".format(
                   emt_openkimmodel % (element, emt_shortkimid[element])))
               continue
           else:
               raise   # Something else went wrong.
        emt = asap3.EMT()
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
        sk = atoms_kim.get_stress(include_ideal_gas=True)
        se = atoms_emt.get_stress(include_ideal_gas=True)
        for i in range(6):
            ReportTest(txt+"Stress(%i)" % (i,), sk[i], se[i], 1e-8)
        sk = atoms_kim.get_stresses(include_ideal_gas=True)
        se = atoms_emt.get_stresses(include_ideal_gas=True)
        for i in range(0, natoms, step):
            n = (n + 1) % 6
            # Volume per atom is not defined the same way: greater tolerance needed
            ReportTest(txt+"Stress(%i) of atom %i" % (n, i), sk[i, n], se[i, n], 1.5e-3)
    
