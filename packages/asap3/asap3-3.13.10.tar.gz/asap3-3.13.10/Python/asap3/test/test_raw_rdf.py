"Test the RawRadialDistributionFunction function."

from asap3 import EMT
from asap3 import _asap
from ase.lattice.cubic import FaceCenteredCubic
from ase.lattice.compounds import NaCl
from asap3.Internal.ListOfElements import ListOfElements
from asap3.test.pytest_markers import ReportTest, serial
from numpy import sqrt, zeros, int32

import pytest

# testtypes: latticeconst, maxRDF, bins, useEMT
testtypes = ((3.6, 6.001, 100, False),
             (3.7, 6.001, 100, True),
             (3.6, 15.001, 100, False),
             (3.65, 15.001, 100, True))

@serial
@pytest.mark.core
@pytest.mark.parametrize('latconst,maxrdf,nbins,withemt', testtypes)
def test_raw_rdf_fcc(latconst, maxrdf, nbins, withemt):

    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                              symbol="Cu", size=(10,10,10),
                              latticeconstant=latconst, debug=0)
    natoms = len(atoms)
    ReportTest("Number of atoms", natoms, 4000, 0)

    if withemt:
        atoms.calc = EMT()
        print(atoms.get_potential_energy())

    result = _asap.RawRDF(atoms, maxrdf, nbins, zeros(len(atoms), int32), 1,
                          ListOfElements(atoms))
    z = atoms.get_atomic_numbers()[0]

    globalrdf, rdfdict, countdict = result

    print(globalrdf)

    ReportTest("Local and global RDF are identical",
               min( globalrdf == rdfdict[0][(z,z)]), 1, 0)
    ReportTest("Atoms are counted correctly", countdict[0][z], natoms, 0)
    
    shellpop = [12, 6, 24, 12, 24, -1]
    shell = [sqrt(i+1.0)/sqrt(2.0) for i in range(6)]
    print(shell)
    print(shellpop)
    n = 0

    dr = maxrdf/nbins

    for i in range(nbins):
        if (i+1)*dr >= shell[n] * latconst:
            if shellpop[n] == -1:
                print("Reached the end of the test data")
                break
            ReportTest(("Shell %d (%d)" % (n+1, i)), globalrdf[i],
                       natoms*shellpop[n], 0)
            n += 1
        else:
            ReportTest(("Between shells (%d)" % (i,)), globalrdf[i], 0, 0)


@serial
@pytest.mark.core
def test_raw_rdf_partial():
    latconst, maxrdf, nbins, withemt = 3.6, 6.001, 100, False

    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], symbol="Cu",
                            size=(10,10,10), latticeconstant=latconst, debug=0)
    natoms = len(atoms)
    z = atoms.get_atomic_numbers()
    z[100] = 47
    atoms.set_atomic_numbers(z)

    ReportTest("Number of atoms", natoms, 4000, 0)

    if withemt:
        atoms.calc = EMT()
        print(atoms.get_potential_energy())

    result = _asap.RawRDF(atoms, maxrdf, nbins, zeros(len(atoms), int32), 1,
                        ListOfElements(atoms))

    globalrdf, rdfdict, countdict = result

    print(globalrdf)
    print(rdfdict)
    print(countdict)

    for i in range(len(globalrdf)):
        tmp = 0
        for key, value in rdfdict[0].items():
            tmp += value[i]
        ReportTest(("Sum of partial RDFs matches global one (%d)" % (i,)),
                tmp, globalrdf[i], 0)


testtypes_NaCl = ((5.1, 6.001, 100, False),
                  (5.2, 6.001, 100, True),
                  (5.1, 15.001, 100, False),
                  (5.15, 15.001, 100, True))

@serial
@pytest.mark.parametrize('latconst, maxrdf, nbins, withemt', testtypes_NaCl)
def test_raw_rdf_NaCl(latconst, maxrdf, nbins, withemt):

    atoms = NaCl(directions=[[1,0,0],[0,1,0],[0,0,1]], symbol=("Cu","Au"),
                 size=(10,10,10), latticeconstant=latconst, debug=0)
    natoms = len(atoms)
    ReportTest("Number of atoms", natoms, 8000, 0)

    if withemt:
        atoms.calc = EMT()
        print(atoms.get_potential_energy())

    result = _asap.RawRDF(atoms, maxrdf, nbins, zeros(len(atoms), int32), 1,
                          ListOfElements(atoms))
    z = atoms.get_atomic_numbers()[0]

    globalrdf, rdfdict, countdict = result

    print(globalrdf)
    localrdf = zeros(globalrdf.shape)
    for i in (29,79):
        for j in (29,79):
            x = rdfdict[0][(i,j)]
            print("LOCAL", i, j)
            print(x)
            localrdf += x


    ReportTest("Local and global RDF are identical",
               min( globalrdf == localrdf), 1, 0)
    ReportTest("Atoms are counted correctly",
               countdict[0][29] + countdict[0][79], natoms, 0)
    
    shellpop = [6, 12, 8, 6, 24, -1]
    shell = [sqrt(i+1.0)/2.0 for i in range(6)]
    print(shell)
    print(shellpop)
    n = 0

    dr = maxrdf/nbins

    for i in range(nbins):
        if (i+1)*dr >= shell[n] * latconst:
            if shellpop[n] == -1:
                print("Reached the end of the test data")
                break
            ReportTest(("Shell %d (%d)" % (n+1, i)), globalrdf[i],
                       natoms*shellpop[n], 0)
            n += 1
        else:
            ReportTest(("Between shells (%d)" % (i,)), globalrdf[i], 0, 0)


