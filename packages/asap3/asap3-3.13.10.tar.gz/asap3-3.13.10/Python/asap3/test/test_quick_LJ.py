#!/usr/bin/python
# Copyright (C) 2007  CAMP
# Please see the accompanying LICENSE file for further information.

# Tests the LennardJones potential.

from ase import Atoms, data

from asap3 import *
from ase.lattice.cubic import *
from ase.lattice.compounds import *
from asap3.md.verlet import VelocityVerlet
from asap3.test.pytest_markers import ReportTest, serial
from asap3.test.StressModule import *
from time import time, localtime, strftime
import numpy as np

import pytest

if getattr(Atoms, '_ase_handles_dynamic_stress', False):
    stresshack = {'include_ideal_gas': True}
else:
    stresshack = {}

def EminRadius(sigma):
 return sigma*1.122462048;

@pytest.mark.core
@serial
def test_twoAtomTest():
  #It is expected that E=0 because r>rcut
  print("\nRunning LJ twoAtomTest")
  #print ''
  elements = [29]
  epsilon  = [0.15]
  sigma    = [2.7]

  atoms=Atoms(positions=[(0.0, 0.0, 0.0),(10.0, 10.0, 10.0)],
              symbols="2Cu")
  atoms.center(vacuum=1.0)

  atoms.calc = LennardJones(elements, epsilon, sigma, -1.0, False)

 
  result = atoms.get_potential_energy()
  #print "Energy is ", result;
  ReportTest("Expected energy for two atoms with r>rcut", result, 0, 1e-12)

@pytest.mark.core
@serial
def test_twoAtomClose():
  #it is expected that E=-epsilon because we calculate r that way
  print("\nRunning LJ twoAtomClose")
  elements = [29]
  epsilon  = [0.15]
  sigma    = [2.7]

  EminR = EminRadius(sigma[0])

  atoms=Atoms(positions=[(0.0, 0.0, 0.0),(0.0, 0.0, EminR)],
                    symbols="Cu2")
  atoms.center(vacuum=1.0)

  atoms.calc = LennardJones(elements, epsilon, sigma, -1.0, False)


  result = atoms.get_potential_energy()
  ReportTest("  Expected energy for two atoms with r->Emin=-epsilon", result, -epsilon[0], 1e-14)

@pytest.mark.core
@serial
def test_twoAtomForce():
  print("\nRunning LJ twoAtomForce")
  elements = [29]
  epsilon  = [0.15]
  sigma    = [2.7]

  atoms=Atoms(positions=[(0.0, 0.0, 0.0),(0.0, 0.0, 2.0)],
              symbols="Cu2")
  atoms.center(vacuum=1.0)

  atoms.calc = LennardJones(elements, epsilon, sigma, -1.0, False)


  result = atoms.get_potential_energy()

  r = atoms.get_positions()
  r.flat[:] += 0.06 * np.sin(np.arange(3*len(atoms)))
  atoms.set_positions(r)
  resA, resB = atoms.get_forces() ;
  storedForces = [ -1.15732425,   13.10743025, -258.04517252 ]

  for a in range(1,3):
    ReportTest(("  Simple force test dimension %d" % a), resA[a],
               storedForces[a], 1e-8)


  print("  Running Verlet dynamics ({})".format("Cu"))
  dyn = VelocityVerlet(atoms, 2*units.fs)
  dyn.run(100)

  etot1 = (atoms.get_potential_energy() + atoms.get_kinetic_energy())
  dyn.run(1000)
  etot2 = (atoms.get_potential_energy() + atoms.get_kinetic_energy())
  ReportTest(("  Energy conservation ({})".format("Cu")), etot1, etot2, 1.0)

  epot = atoms.get_potential_energies()
  stress = atoms.get_stresses(**stresshack)

  e = []
  s = []
  j = 0
  for i in range(0, len(atoms), 100):
      e.append(epot[i])
      s.append(stress[i,j])
      j = (j + 1) % 6
  print("  e"+"Cu"+" =", repr(e))
  print("  s"+"Cu"+" =", repr(s))

      
#
# size=15:     will allocate the size of the cube to size=(15,15,15)
# before=100:  will run the simulation for 100*2*femtosecond before starting measuring
# steps=200:   will measure and compare the potentials for 200*(2*femtosecond)
# v0:          True: add v0 False: do not add v0
# rCut:        -1: automatically set; or any value >0
# nonSense:     uses a random set of values to test whether multidimensional params work
@pytest.mark.core
@serial
@pytest.mark.parametrize('size, before, steps, v0, rCut, nonSense', [
   (10, 10, 200, False, -1, False),
   (11, 10, 200, True, -1, True),
])
def test_dynamics(size, before, steps, v0, rCut, nonSense):
    print("\n\nStarting LJ dynamicsTest with ")
    print("  cube of size                  %d"%size)
    print("  time before measurement start %d*1*femtoseconds"%before)
    print("  measuring time                %d*femtoseconds"%steps)
    print("  add v0                        %d"%(v0==1))
    print("  rCut                          %d"%rCut)
    print("  3 kinds of atoms              %s"%(nonSense==1))

    start = time();

    nsteps = steps;
    #Warning: numbers and constants are not supposed to make sense or to be correct!!
    #         they're only here to assure that the program handles the input correctly
    if nonSense:
      elements = [29, 79, 39]
      epsilon  = [0.15, 0.00, 0.00,
                  0.10, 0.25, 0.00,
                  0.31, 0.60, 0.15]
      sigma    = [2.7 , 0.00, 0.00,
                  1.90, 2.7 , 0.00,
                  2.20, 1.50, 2.7 ]
      atoms = L1_2(directions=[[1,0,0],[0,1,0],[0,0,1]], size=(size,size,size),
                     symbol=("Cu", "Au"), pbc=(1,0,1), debug=0,
                     latticeconstant=3.95)
      atoms.calc = LennardJones(elements, epsilon, sigma, rCut, v0)
    else:
      elements = [29]
      epsilon  = [0.15]
      sigma    = [2.7]
      atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                                size=(size,size,size),
                                symbol="Cu", pbc=(1,0,1), debug=0,
                                latticeconstant=1.09*sigma[0]*1.41)
      atoms.calc = LennardJones(elements, epsilon, sigma, rCut, v0)

    r = atoms.get_positions()
    r.flat[:] += 0.06 * np.sin(np.arange(3*len(atoms)))
    atoms.set_positions(r)

    print("  Running Verlet dynamics ({})".format("Cu"))
    dyn = VelocityVerlet(atoms, 1*units.fs)
    dyn.run(before)
    
    etot1 = (atoms.get_potential_energy() + atoms.get_kinetic_energy())
    for i in range(nsteps//10):
        dyn.run(10)
        #print atoms.get_potential_energy()/len(atoms), atoms.get_kinetic_energy()/len(atoms), (atoms.get_potential_energy() + atoms.get_kinetic_energy())/len(atoms)
    etot2 = (atoms.get_potential_energy() + atoms.get_kinetic_energy())
    ReportTest(("  Energy conservation ({})".format("Cu")), etot1, etot2, 2)
    print("Before: ", etot1, " now: ", etot2, " diff= ", (etot1-etot2))
    epot = atoms.get_potential_energies()
    stress = atoms.get_stresses(**stresshack)
    print("  Reporting energies and stresses")
    
    e = []
    s = []
    j = 0
    for i in range(0, len(atoms), 100):
        e.append(epot[i])
        s.append(stress[i,j])
        j = (j + 1) % 6
    print("  e"+"Cu"+" =", repr(e))
    print("  s"+"Cu"+" =", repr(s))
    end = time();
    print("  ++++ Test runtime of the LJ dynamicsTest was %d seconds ++++\n\n" %(end-start))
    if 1:
        sumstress = np.zeros(6, float)
        for s in stress:
            sumstress += s
        totalstress = atoms.get_stress(**stresshack)
        for i in range(6):
            ReportTest("Sum of stresses (%d)" % (i,), sumstress[i]/len(atoms),
                       totalstress[i], abs(0.01*totalstress[i]))
    

@pytest.mark.core
@serial
@pytest.mark.parametrize('slow, v0', [
   (False, False),
   (False, True)
])
def test_stress(slow, v0):

    start = time();

    elements = [29]
    epsilon  = [0.15]
    sigma    = [2.7]
    if slow:
        alpha = 12.13188
        beta = 14.45392
    else:
        alpha = beta = 12
    fact = (2*alpha/beta)**(1.0/6)
    latconst = fact*sigma[0]*np.sqrt(2.0)
    bookbulk = (2*np.sqrt(2)/9) * (156*alpha/fact**14 - 42*beta/fact**8) * epsilon[0] / (fact * sigma[0]**3) / units.GPa
    
    print("Lattice const. ", latconst)

    if slow:
        symb="Cu_LJ_Full"
        size=12
        rCut=8*sigma[0]
        bookbulk *= 0.9706  # Not fully converged with this rCut
        bookc11 = 123.70
        bookc12 = 69.78
        bookc44 = 69.28
    else:
        symb="Cu_LJ_NN"
        size=10
        rCut = fact * sigma[0] * 0.5 * (1 + np.sqrt(2))
        bookc11 = 85.65
        bookc12 = 41.76
        bookc44 = 41.82

    book[symb] = {"bookbulk": (134.3, bookbulk),
                  "bookc11": (168.3, bookc11),
                  "bookc12": (122.1, bookc12),
                  "bookc44": (75.7, bookc44)}

    atoms = FaceCenteredCubic(directions=[[1,0,0],[0,1,0],[0,0,1]],
                              size=(size,size,size),
                              symbol="Cu", pbc=(1,0,1), debug=0,
                              latticeconstant=latconst)

    atoms.calc = LennardJones(elements, epsilon, sigma, rCut, v0)

    atoms.set_momenta(np.zeros((len(atoms),3), float))
    #findlatticeconst(atoms, latconst)  ## Lattice const already OK
    elasticconstants(atoms, symb, fitfact=20.0, fitfact2=20.0, **book[symb])
    end = time();
    print("&&&& Test runtime of the LJ stressTest was %d seconds &&&&" %(end-start))

