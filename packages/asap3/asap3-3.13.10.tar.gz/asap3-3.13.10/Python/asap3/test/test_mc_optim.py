'Test of Monte Carlo optimizations for EMT'

from asap3 import EMT, MonteCarloEMT, MonteCarloAtoms, \
    Atoms, FullNeighborList, NeighborList
from ase.lattice.cubic import FaceCenteredCubic
from ase import data
from asap3.test.pytest_markers import ReportTest, serial

import numpy as np
import time
import sys

import pytest

def checkenergies(a, a2):
    err = 0
    if 0:
        print("    Checking Cartesian positions")
        err = abs((a.get_positions() - a2.get_positions()).ravel())
        idx = np.argmax(err)
        at, co = idx/3, idx%3
        print("      err =", err[idx], "at", idx, ":", at, co)
        ReportTest("      Worst Cartesian position (%d,%d)" % (at, co),
                   a.get_positions()[at,co],
                   a2.get_positions()[at,co], 1e-10)
    print("    Checking energies")
    e1 = a.get_potential_energies()
    e2 = a2.get_potential_energies()
    err = e1 - e2
    idx = np.argmax(err)
    ReportTest(f"      Worst energy ({idx})", e1[idx], e2[idx], 1e-5)

@serial
@pytest.mark.parametrize('pbctype', ('periodic', 'free', 'mixed'))
def test_montecarlo_energies(pbctype):
    element = "Cu"
    pbcdict = dict(periodic=True, free=False, mixed=(1,0,0))
    pbc = pbcdict[pbctype]

    magnarr = np.array((0.0, 0.01, 0.1, 1.0, 3.0, 10.0))
    numarr = np.array((1, 3, 10, 50, 200, 2000, -3))
    nrun = 1
    for ntest in range(nrun):
        print()
        print("Running pass", ntest+1, "of", nrun)
        print()
        print("Periodic boundaries:", pbc)
        if nrun > 1:
            time.sleep(1)
        atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(10,10,10),
                                symbol=element, pbc=pbc)
        atoms = MonteCarloAtoms(atoms)
        print("Number of atoms:", len(atoms))
        atoms.calc = MonteCarloEMT()
        atoms.get_potential_energies()  # Force creation of neighbor list.
        atoms2 = atoms.copy()
        atoms2.calc = EMT()

        print() 
        print("Testing perturbations of single atoms")

        pick1 = np.argsort(np.random.random((len(magnarr),)))
        for magn in np.take(magnarr, pick1):
            pick2 = np.argsort(np.random.random((len(numarr),)))
            for number in np.take(numarr, pick2):
                # Pick number random atoms.
                if number < 0:
                    # Find N neighboring atoms and perturb them
                    number = -number
                    nblist = atoms.calc.get_neighborlist()
                    n = 0
                    while len(nblist[n]) < number:
                        n += 1
                    pick = np.concatenate([np.array((n,)), nblist[n][:number-1]])
                    del nblist
                else:
                    pick = np.argsort(np.random.random((len(atoms),)))[:number]
                if number > 15:
                    s = f"<<< {number} atoms >>>"
                else:
                    s = str(list(pick))
                print("  dr = %.3f: %d atoms: %s" % (magn, number, s))
                for i in pick:
                    dr = np.random.standard_normal(3)
                    dr *= magn/np.sqrt(np.dot(dr,dr))
                    atom = atoms[i]
                    atom.position = atom.position + dr
                    atom = atoms2[i]
                    atom.position = atom.position + dr
                checkenergies(atoms, atoms2)

@pytest.mark.core
@serial
def test_montecarlo_alloy():
    element = "Cu"
    element2 = "Ag"
    latconst = data.reference_states[data.atomic_numbers[element]]['a']
    elementnumber = data.atomic_numbers[element]
    element2number = data.atomic_numbers[element2]
    pbc = tuple(np.random.randint(0,2,3))
    print("Periodic boundaries:", pbc)

    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(10,10,10),
                            symbol=element, pbc=pbc)
    atoms2 = atoms.copy()
    atoms = MonteCarloAtoms(atoms)
    print("Number of atoms:", len(atoms))
    # Replace 10% of the atoms with element2
    newz = np.where(np.greater(np.random.random((len(atoms),)), 0.9),
                    element2number, elementnumber)
    atoms.set_atomic_numbers(newz)
    atoms2.set_atomic_numbers(newz)

    atoms.calc = MonteCarloEMT()
    atoms2.calc = EMT()
    atoms.get_potential_energy()

    for e in ((element,elementnumber), (element2,element2number)):
        print ("Number of %s atoms (Z=%d): %d"
            % (e[0], e[1], np.sum(np.equal(atoms.get_atomic_numbers(), e[1]))))

    print() 
    print("Testing perturbations of single atoms")

    magnarr = np.array((0.0, 0.01, 0.1, 1.0, 3.0, 10.0))
    numarr = np.array((1, 3, 10, len(atoms)//2, -3))
    pick1 = np.argsort(np.random.random((len(magnarr),)))
    for magn in np.take(magnarr, pick1):
        pick2 = np.argsort(np.random.random((len(numarr),)))
        for number in np.take(numarr, pick2):
            # Pick number random atoms.
            if number < 0:
                # Find N neighboring atoms and perturb them
                number = -number
                nblist = atoms.calc.get_neighborlist()
                n = 0
                while len(nblist[n]) < number:
                    n += 1
                pick = np.concatenate([np.array((n,)), nblist[n][:number-1]])
                del nblist
            else:
                pick = np.argsort(np.random.random((len(atoms),)))[:number]
            if number > 15:
                s = f"<<< {number} atoms >>>"
            else:
                s = str(list(pick))
            print("  dr = %.3f: %d atom(s): %s" % (magn, number, s))
            for i in pick:
                dr = np.random.standard_normal(3)
                dr *= magn/np.sqrt(np.dot(dr,dr))
                atom = atoms[i]
                atom.position = atom.position + dr
                atom = atoms2[i]
                atom.position = atom.position + dr

            checkenergies(atoms, atoms2)

    print()
    print("Testing alchemy")

    pick2 = np.argsort(np.random.random((len(numarr),)))
    for number in np.take(numarr, pick2):
        # Pick number random atoms.
        if number < 0:
            # Find N neighboring atoms and perturb them
            number = -number
            nblist = atoms.calc.get_neighborlist()
            n = 0
            while len(nblist[n]) < number:
                n += 1
            pick = np.concatenate([np.array((n,)), nblist[n][:number-1]])
            del nblist
        else:
            pick = np.argsort(np.random.random((len(atoms),)))[:number]
        if number > 15:
            s = f"<<< {number} atoms >>>"
        else:
            s = str(list(pick))
            print("  Alchemy, %d atoms: %s" % (number, s))
            for i in pick:
                atom = atoms[i]
                atom2 = atoms2[i]
                z = atom.number
                assert z == atom2.number
                if (z == elementnumber):
                    atom.number = element2number
                    atom2.number = element2number
                else:
                    assert z == element2number
                    atom.number = elementnumber
                    atom2.number = elementnumber
            checkenergies(atoms, atoms2)


def checklist(nb, a, cut):
    error = 0
    a2 = Atoms(a)
    nb2 = FullNeighborList(cut, a2, 0)
    print("    Checking Cartesian positions")
    err = abs((a.get_positions() - a2.get_positions()).ravel())
    idx = np.argmax(err)
    at, co = idx//3, idx%3
    print("      err =", err[idx], "at", idx, ":", at, co)
    ReportTest("      Worst Cartesian position (%d,%d)" % (at, co),
               a.get_positions()[at,co],
               a2.get_positions()[at,co], 1e-10)

    print("    Checking full list")
    for i in range(len(a)):
        l1 = list(nb[i])
        l1.sort()
        l2 = list(nb2[i])
        l2.sort()
        if not l1 == l2:
            ReportTest.BoolTest("NB lists for atom %d should be identical"
                                % (i,), False)
            print("nb1[%d] = %s" % (i, str(l1)))
            print("nb2[%d] = %s" % (i, str(l2)))
            print("pos1[%d] = %s" % (i, str(a.get_positions()[i])))
            print("pos2[%d] = %s" % (i, str(a2.get_positions()[i])))
            error += 1
            if error > 3:
                print("Too many errors, giving up!")
                raise RuntimeError("Too many errors, giving up!")


@serial
def test_montecarlo_nblist():
    listcutoff = 4.98409   # The EMT value for Cu
    element = "Cu"
    latconst = data.reference_states[data.atomic_numbers[element]]['a']
    pbc = tuple(np.random.randint(0,2,3))
    print("Periodic boundaries:", pbc)

    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(10,10,10),
                            symbol=element, pbc=pbc, debug=0)

    nblist = NeighborList(listcutoff, atoms, 0, full=True)
    print()
    print("Checking number of affected atoms.")
    #Verbose(1)

    np_atoms = Atoms(atoms, pbc=False)
    np_nblist = NeighborList(listcutoff, np_atoms, 0, full=True)

    i = np.random.randint(0, len(np_atoms))
    dr = np.random.standard_normal(3)
    dr *= 10.0/np.sqrt(np.dot(dr,dr))
    atom = np_atoms[i]
    oldpos = np.array(atom.position)
    newpos = oldpos + dr
    atom.position = newpos
    nr = np_nblist.test_partial_update(np.array([i,], np.int32), np_atoms)
    # Count who should be affected.
    r = np_atoms.get_positions() - oldpos
    r2 = np.sum(r * r, 1)
    a = np.less_equal(r2, listcutoff*listcutoff)
    r = np_atoms.get_positions() - newpos
    r2 = np.sum(r * r, 1)
    b = np.less_equal(r2, listcutoff*listcutoff)

    nr2 = np.sum(np.logical_or(a,b))
    print(nr, "atoms were affected")
    print(np.sum(a), "near old position and", np.sum(b), "near new position.")
    print(nr2, "atoms should be affected")
    ReportTest("Number of affected atoms", nr, nr2, 0)
    
    del np_atoms, np_nblist
    
    print()
    print("Testing perturbations of all the atoms")

    magnarr = np.array((0.0, 0.01, 0.1, 1.0, 3.0, 10.0))
    pick = np.argsort(np.random.random((len(magnarr),)))
    for magn in np.take(magnarr, pick):
        dx = magn * np.random.uniform(-1, 1, (len(atoms), 3))
        print("  Perturbation:", magn)
        atoms.set_positions(dx + atoms.get_positions())
        nblist.check_and_update(atoms)
        checklist(nblist, atoms, listcutoff)

    print() 
    print("Testing perturbations of single atoms")

    magnarr = np.array((0.0, 0.01, 0.1, 1.0, 3.0, 10.0))
    pick1 = np.argsort(np.random.random((len(magnarr),)))
    for magn in np.take(magnarr, pick1):
        numarr = np.array((1, 3, 10, len(atoms)//2, -3))
        pick2 = np.argsort(np.random.random((len(numarr),)))
        for number in np.take(numarr, pick2):
            # Pick number random atoms.
            if number < 0:
                # Find N neighboring atoms and perturb them
                number = -number
                n = 0
                while len(nblist[n]) < number:
                    n += 1
                pick = np.concatenate([np.array((n,)), nblist[n][:number-1]])
            else:
                pick = np.argsort(np.random.random((len(atoms),)))[:number]
            if number > 15:
                s = f"<<< {number} atoms >>>"
            else:
                s = str(list(pick))
            print("  dr = %.3f: %d atoms: %s" % (magn, number, s))
            for i in pick:
                atom = atoms[i]
                dr = np.random.standard_normal(3)
                dr *= magn/np.sqrt(np.dot(dr,dr))
                atom.position += dr

            nblist.test_partial_update(pick.astype(np.int32), atoms)
            checklist(nblist, atoms, listcutoff)
