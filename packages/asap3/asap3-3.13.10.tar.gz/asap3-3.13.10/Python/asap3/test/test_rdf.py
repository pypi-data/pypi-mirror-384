"Test the RawRadialDistributionFunction function."

from numpy import *
from asap3 import *
from asap3.analysis.rdf import RadialDistributionFunction
from ase.lattice.cubic import FaceCenteredCubic
from ase.lattice.compounds import NaCl
from asap3.mpi import world
from asap3.test.pytest_markers import ReportTest, serial

import pytest


ismaster = world.rank == 0
isparallel = world.size != 1

# testtypes: latticeconst, maxRDF, bins, useEMT
testtypes = ((3.6, 6.001, 100, False),
             (3.7, 6.001, 100, True),
             (3.6, 15.001, 100, False),
             (3.65, 15.001, 100, True))

@pytest.mark.parametrize('latconst,maxrdf,nbins,withemt', testtypes)
def test_rdf_fcc(latconst, maxrdf, nbins, withemt, cpulayout):
    if ismaster:
        atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]], symbol="Cu",
                              size=(10,10,10), latticeconstant=latconst)
        if isparallel:
            atoms = atoms.repeat(cpulayout)
    else:
        atoms = None
    if isparallel:
        atoms = MakeParallelAtoms(atoms, cpulayout)
    natoms = atoms.get_global_number_of_atoms()

    if withemt:
        atoms.calc = EMT()
        print(atoms.get_potential_energy())

    rdf = RadialDistributionFunction(atoms, maxrdf, nbins, verbose=True)
    z = atoms.get_atomic_numbers()[0]

    globalrdf = rdf.get_rdf()
    localrdf = rdf.get_rdf(elements=(z,z))

    print(globalrdf)

    ReportTest("Local and global RDF are identical",
               max(abs(globalrdf - localrdf)), 0.0, 1e-6)
        
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
            rho = natoms / atoms.get_volume()
            expected = shellpop[n] / (4 * pi * ((i+0.5) * dr)**2 * dr * rho)
            maxerr = shellpop[n] / (8 * pi * ((i+0.5) * dr)**3 * rho) * 0.02
            print("Shell", n+1, globalrdf[i], expected, maxerr, (globalrdf[i] - expected)/maxerr)
            ReportTest(("Shell %d (%d)" % (n+1, i)), globalrdf[i],
                       expected, maxerr)
            n += 1
        else:
            ReportTest(("Between shells (%d)" % (i,)), globalrdf[i], 0, 0)

# testtypes: latticeconst, maxRDF, bins, useEMT, save
testtypes2 = ((5.1, 6.001, 100, False, True),
             (5.2, 6.001, 100, True, False),
             (5.1, 15.001, 100, False, False),
             (5.15, 15.001, 100, True, False)
             )

@serial
@pytest.mark.xfail  # From old disabled test RDF2.py
@pytest.mark.parametrize('latconst,maxrdf,nbins,withemt,save', testtypes2)
def test_rdf_NaCl(latconst, maxrdf, nbins, withemt, save, in_tmp_dir):
    atoms = NaCl(directions=[[1,0,0],[0,1,0],[0,0,1]],
                 symbol=("Cu", "Au"), size=(10,10,10),
                 latticeconstant=latconst, debug=0)
    natoms = len(atoms)
    ReportTest("Number of atoms", natoms, 8000, 0)

    if withemt:
        atoms.calc = EMT()
        print(atoms.get_potential_energy())

    rdf = RadialDistributionFunction(atoms, maxrdf, nbins)
    if save:
        rdf.output_file("RDF2-rdf")
    z = atoms.get_atomic_numbers()[0]

    globalrdf = rdf.get_rdf()
    localrdf = zeros(globalrdf.shape, float)
    for i in (29,79):
        for j in (29,79):
            localrdf += rdf.get_rdf(elements=(i,j))

    ReportTest("Local and global RDF are identical",
               min( globalrdf == localrdf), 1, 0)
        
    shellpop = [6, 12, 8, 6, 24, -1]
    shell = [sqrt(i+1.0)/2.0 for i in range(6)]
    n = 0

    dr = maxrdf/nbins

    for i in range(nbins):
        if (i+1)*dr >= shell[n] * latconst:
            if shellpop[n] == -1:
                print("Reached the end of the test data")
                break
            rho = len(atoms) / atoms.get_volume()
            expected = shellpop[n] / (4 * pi * ((i+0.5) * dr)**2 * dr * rho)
            maxerr = shellpop[n] / (8 * pi * ((i+0.5) * dr)**3 * rho)
            print("expected, error", expected, maxerr, globalrdf[i]-expected)
            ReportTest(("Shell %d (%d)" % (n+1, i)), globalrdf[i],
                       expected, maxerr)
            n += 1
        else:
            ReportTest(("Between shells (%d)" % (i,)), globalrdf[i], 0, 0)

    if save:
        rdf = RadialDistributionFunction.load("RDF2-rdf0000.rdf")

        newglobalrdf = rdf.get_rdf()
        ReportTest("Saved and original RDF have same length",
                   len(newglobalrdf), len(globalrdf), 0)
        for i in range(len(globalrdf)):
            ReportTest("Saved and global RDF at position %d" % (i,),
                       newglobalrdf[i], globalrdf[i], 0)
            
        localrdf = zeros(globalrdf.shape, float)
        for i in (29,79):
            for j in (29,79):
                x = rdf.get_rdf(elements=(i,j))
                localrdf += x

        ReportTest("Saved local and global RDF are identical",
                   min( globalrdf == localrdf), 1, 0)

        os.unlink("RDF2-rdf0000.rdf")
    

