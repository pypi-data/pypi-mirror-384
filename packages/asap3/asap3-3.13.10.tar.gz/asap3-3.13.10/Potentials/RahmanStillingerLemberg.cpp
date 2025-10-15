// Copyright (C) 2008-2011 Jakob Schiotz and Center for Individual
// Nanoparticle Functionality, Department of Physics, Technical
// University of Denmark.  Email: schiotz@fysik.dtu.dk
//
// This file is part of Asap version 3.
//
// This program is free software: you can redistribute it and/or
// modify it under the terms of the GNU Lesser General Public License
// version 3 as published by the Free Software Foundation.  Permission
// to use other versions of the GNU Lesser General Public License may
// granted by Jakob Schiotz or the head of department of the
// Department of Physics, Technical University of Denmark, as
// described in section 14 of the GNU General Public License.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// and the GNU Lesser Public License along with this program.  If not,
// see <http://www.gnu.org/licenses/>.

/*
 * Calculates the revised Rahman Stillinger Lemberg (RSL2)
 */


// This implementation supports parallel simulations.  Due to the
// simplicity of RSL2, everything is handled by the
// ParallelAtoms and ParallelPotential classes, this potential only
// has to be prepared for parallel simulations in two ways:
//
// 1. After a neighborlist update, the number of atoms may have
//    changed, and arrays may have to be reallocated.
//
// 2. The neighborlist may return atoms with number higher than
//    nAtoms, these are ghosts of atoms residing on other processor,
//    and only have positions and atomic numbers.  It must be avoided
//    to update energies, forces and stresses for these, as that would
//    overwrite the end of the arrays.

#include "AsapPython.h"
#include "Asap.h"
#include "RahmanStillingerLemberg.h"
#include "NeighborList.h"
#include "Atoms.h"
#include "Vec.h"
#include "Timing.h"
#include "Debug.h"
#include <math.h>
#include <stdio.h>
#include <iostream>
#include <algorithm>

#ifndef _WIN32
#include <sys/wait.h>
#endif

using std::cerr;
using std::endl;
using std::flush;
using std::less;

#define SPARSE_MATRIX_SIZE 92  // No Pu, please!  

// Use same volume for all atoms in stress calculation.
#define SHAREVOLUME   

#if 0
#define VERB(x) if (verbose == 1) cerr << x
#else
#define VERB(x)
#endif


#ifdef SUN_SQRT_LITERAL_HACK
// SunOS compiler: sqrt does not work with a literal number (cannot decide if
// it is a double or a long double).
#define sqrt(x) sqrt((double) x)
#endif


//******************************************************************************
//                             RahmanStillingerLemberg
//******************************************************************************
RahmanStillingerLemberg::RahmanStillingerLemberg(PyObject *self,
                        int numElements,
                        const std::vector<double> &D0,
                        const std::vector<double> &R0,
                        const std::vector<double> &y,
                        const std::vector<double> &a1,
                        const std::vector<double> &b1,
                        const std::vector<double> &c1,
                        const std::vector<double> &a2,
                        const std::vector<double> &b2,
                        const std::vector<double> &c2,
                        const std::vector<double> &a3,
                        const std::vector<double> &b3,
                        const std::vector<double> &c3,
                        const std::vector<int> &elements,
                        const std::vector<double> &masses, 
                        double rCut, int verbose) : Potential(self, verbose)
{
    DEBUGPRINT;
    atoms = NULL;
    this->nAtoms = 0;
    neighborList= 0;
    neighborList_obj= 0;
    driftfactor = 0.05;
    this->numElements = numElements;
    this->latticeConstant = 0.0;
    
    memset(&counters, 0x0, sizeof(counters));

    this->rCut = rCut;

    Internalize(numElements, D0, R0, y, a1, b1, c1, a2, b2, c2, a3, b3, c3, 
        elements, masses);
    //Print();
    DEBUGPRINT;
}

RahmanStillingerLemberg::~RahmanStillingerLemberg()
{
    DEBUGPRINT;
    Py_XDECREF(neighborList_obj);
    if (atoms != NULL)
        AsapAtoms_DECREF(atoms);
}

//******************************************************************************
//                             Internalize
//******************************************************************************
void RahmanStillingerLemberg::Internalize(int p_numElements,
                            const std::vector<double> &p_D0,
                            const std::vector<double> &p_R0,
                            const std::vector<double> &p_y,
                            const std::vector<double> &p_a1,
                            const std::vector<double> &p_b1,
                            const std::vector<double> &p_c1,
                            const std::vector<double> &p_a2,
                            const std::vector<double> &p_b2,
                            const std::vector<double> &p_c2,
                            const std::vector<double> &p_a3,
                            const std::vector<double> &p_b3,
                            const std::vector<double> &p_c3,
                            const std::vector<int> &p_elements,
                            const std::vector<double> &p_masses) 
{
    DEBUGPRINT;
    
    //0. complete upper triangular matrices
    std::vector<double> full_D0, full_R0, full_y, full_a1, full_b1, full_c1;
    std::vector<double> full_a2, full_b2, full_c2, full_a3, full_b3, full_c3;
    
    full_D0.resize(p_numElements*p_numElements);
    full_R0.resize(p_numElements*p_numElements);
    full_y.resize(p_numElements*p_numElements);
    full_a1.resize(p_numElements*p_numElements);
    full_b1.resize(p_numElements*p_numElements);
    full_c1.resize(p_numElements*p_numElements);
    full_a2.resize(p_numElements*p_numElements);
    full_b2.resize(p_numElements*p_numElements);
    full_c2.resize(p_numElements*p_numElements);
    full_a3.resize(p_numElements*p_numElements);
    full_b3.resize(p_numElements*p_numElements);
    full_c3.resize(p_numElements*p_numElements);
    
    for(int i=0;i<p_numElements;i++) {
        for(int j=0;j<=i;j++) {
            full_D0[j*p_numElements+i]=p_D0[i*p_numElements+j];
            full_D0[i*p_numElements+j]=p_D0[i*p_numElements+j];
            full_R0[j*p_numElements+i]=p_R0[i*p_numElements+j];
            full_R0[i*p_numElements+j]=p_R0[i*p_numElements+j];
            full_y[j*p_numElements+i]=p_y[i*p_numElements+j];
            full_y[i*p_numElements+j]=p_y[i*p_numElements+j];
            full_a1[j*p_numElements+i]=p_a1[i*p_numElements+j];
            full_a1[i*p_numElements+j]=p_a1[i*p_numElements+j];
            full_b1[j*p_numElements+i]=p_b1[i*p_numElements+j];
            full_b1[i*p_numElements+j]=p_b1[i*p_numElements+j];
            full_c1[j*p_numElements+i]=p_c1[i*p_numElements+j];
            full_c1[i*p_numElements+j]=p_c1[i*p_numElements+j];
            full_a2[j*p_numElements+i]=p_a2[i*p_numElements+j];
            full_a2[i*p_numElements+j]=p_a2[i*p_numElements+j];
            full_b2[j*p_numElements+i]=p_b2[i*p_numElements+j];
            full_b2[i*p_numElements+j]=p_b2[i*p_numElements+j];
            full_c2[j*p_numElements+i]=p_c2[i*p_numElements+j];
            full_c2[i*p_numElements+j]=p_c2[i*p_numElements+j];
            full_a3[j*p_numElements+i]=p_a3[i*p_numElements+j];
            full_a3[i*p_numElements+j]=p_a3[i*p_numElements+j];
            full_b3[j*p_numElements+i]=p_b3[i*p_numElements+j];
            full_b3[i*p_numElements+j]=p_b3[i*p_numElements+j];
            full_c3[j*p_numElements+i]=p_c3[i*p_numElements+j];
            full_c3[i*p_numElements+j]=p_c3[i*p_numElements+j];
        }
    }
    
    //1. allocate the matrices
    D0.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    R0.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    y.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    a1.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    b1.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    c1.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    a2.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    b2.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    c2.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    a3.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    b3.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);
    c3.resize(SPARSE_MATRIX_SIZE*SPARSE_MATRIX_SIZE);

    //2. Fill the matrix with the values we know.
    //   a) We know that sigma[i][j] = sigma[j][i]
    //   b) The position in the array is calculated as follows:
    //      (element number of atom i)*SPARSE_MATRIX_SIZE + (element number of atom j)
    
    int ind1, ind2;
    for(int i=0; i<p_numElements; i++) {
        for(int j=0; j<=i; j++) {       
            ind1 = p_elements[i]+p_elements[j]*SPARSE_MATRIX_SIZE;
            ind2 = p_elements[j]+p_elements[i]*SPARSE_MATRIX_SIZE;
            
            D0[ind1] = full_D0[i*p_numElements+j];
            D0[ind2] = full_D0[i*p_numElements+j];
            R0[ind1] = full_R0[i*p_numElements+j];
            R0[ind2] = full_R0[i*p_numElements+j];
            y[ind1] = full_y[i*p_numElements+j];
            y[ind2] = full_y[i*p_numElements+j];
            a1[ind1] = full_a1[i*p_numElements+j];
            a1[ind2] = full_a1[i*p_numElements+j];
            b1[ind1] = full_b1[i*p_numElements+j];
            b1[ind2] = full_b1[i*p_numElements+j];
            c1[ind1] = full_c1[i*p_numElements+j];
            c1[ind2] = full_c1[i*p_numElements+j];
            a2[ind1] = full_a2[i*p_numElements+j];
            a2[ind2] = full_a2[i*p_numElements+j];
            b2[ind1] = full_b2[i*p_numElements+j];
            b2[ind2] = full_b2[i*p_numElements+j];
            c2[ind1] = full_c2[i*p_numElements+j];
            c2[ind2] = full_c2[i*p_numElements+j];
            a3[ind1] = full_a3[i*p_numElements+j];
            a3[ind2] = full_a3[i*p_numElements+j];
            b3[ind1] = full_b3[i*p_numElements+j];
            b3[ind2] = full_b3[i*p_numElements+j];
            c3[ind1] = full_c3[i*p_numElements+j];
            c3[ind2] = full_c3[i*p_numElements+j];
        }       
    }
    DEBUGPRINT;
}


void RahmanStillingerLemberg::SetAtoms(PyObject *pyatoms, Atoms* accessobj /* = NULL */)
{
  if (atoms != NULL)
    {
      // SetAtoms should only do anything the first time it is called.
      // Subsequent calls should just check for accessobj being NULL.
      if (accessobj != NULL)
    throw AsapError("RahmanStillingerLemberg::SetAtoms called multiple times with accessobj != NULL");
      // SetAtoms should not do anything if called more than once!
      return;
    }

  // The first time SetAtoms is being called some initialization is done.
  if (accessobj != NULL)
    {
      atoms = accessobj;
      AsapAtoms_INCREF(atoms);
    }
  else
    atoms = new NormalAtoms();
  ASSERT(atoms != NULL);
}

//******************************************************************************
//                             Allocate
//******************************************************************************
void RahmanStillingerLemberg::Allocate()
{
  DEBUGPRINT;
  if (verbose)
    cerr << "Allocate(" << nAtoms << ") " << endl;
  ASSERT(nAtoms != 0);
  atomicEnergies.resize(nAtoms);
  forces.resize(nSize);
  virials.resize(nSize);
  DEBUGPRINT;
}

bool RahmanStillingerLemberg::CheckAndUpdateNbList(PyObject *pyatoms)
{
  atoms->Begin(pyatoms);
  bool updated = CheckNeighborLists();
  atoms->End();
  return updated;
}


//******************************************************************************
//                             CheckNeighborLists
//******************************************************************************
bool RahmanStillingerLemberg::CheckNeighborLists()
{
  DEBUGPRINT;
  if (counters.nblist == atoms->GetPositionsCounter() && neighborList != NULL
      && !neighborList->IsInvalid())
    return false;
  
  bool update = false;
  if (neighborList)
    {
      DEBUGPRINT;
	  update = neighborList->CheckNeighborList();
      update = atoms->UpdateBeforeCalculation(update,
                      rCut * (1 + driftfactor));
      if (update)
    neighborList->UpdateNeighborList();
      if ((nAtoms != atoms->GetNumberOfAtoms()) ||
          (nSize != nAtoms + atoms->GetNumberOfGhostAtoms()))
    {
      DEBUGPRINT;
      ASSERT(update);
      nAtoms = atoms->GetNumberOfAtoms();
      nSize = nAtoms + atoms->GetNumberOfGhostAtoms();
      Allocate();
    }
    }
  else
    {
      DEBUGPRINT;
	  update = true;
      atoms->UpdateBeforeCalculation(true, rCut * (1 + driftfactor));
      PyAsap_NeighborLocatorObject *nbl = PyAsap_NewNeighborList(atoms, rCut,
                                 driftfactor);
      neighborList_obj = (PyObject *)nbl;
      neighborList = dynamic_cast<NeighborList*>(nbl->cobj);
      ASSERT(neighborList != NULL);
      neighborList->verbose = verbose;
      neighborList->CheckAndUpdateNeighborList();
      nAtoms = atoms->GetNumberOfAtoms();
      nSize = nAtoms + atoms->GetNumberOfGhostAtoms();
      Allocate();
    }
  counters.nblist = atoms->GetPositionsCounter();
  DEBUGPRINT;
  return update;
}

//******************************************************************************
//                               GetStresses 
//******************************************************************************
const vector<SymTensor> &RahmanStillingerLemberg::GetVirials(PyObject *pyatoms)
{
    throw AsapNotImplementedError("RahmanStillingerLemberg: Stresses not implemented");
}

//******************************************************************************
//                               GetForces 
//******************************************************************************
const vector<Vec> &RahmanStillingerLemberg::GetForces(PyObject *pyatoms)
{
    ASSERT(atoms != NULL);
    atoms->Begin(pyatoms);
    CheckNeighborLists();
    ASSERT(nSize >= nAtoms);
    ASSERT(forces.size() == nSize);
    memset((void *) &(forces[0]), 0, nSize * sizeof(Vec)); //zero the forces
    GetCartesianForces(forces);
    atoms->End();
    return forces;
}

//******************************************************************************
//                           GetCartesianForces
//******************************************************************************
void RahmanStillingerLemberg::GetCartesianForces(vector<Vec>& forces)
{
    DEBUGPRINT
    
    // definitions
    const asap_z_int *z;
    int maxNeighbors, _maxNeighbors, ind, numNeighbors, nn;
    double r, t0, e1, t1, e2, t2, e3, t3, dV;
    
    maxNeighbors=neighborList->MaxNeighborListLength();
    
    vector<int> neighbors(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
        
    z = atoms->GetAtomicNumbers(); //lookup for atomic numbers
    
    for(int i=0; i<nAtoms; i++) { // iterate over all atoms
        _maxNeighbors = maxNeighbors;
        numNeighbors = neighborList->GetNeighbors(i, &neighbors[0], &diffs[0], &diffs2[0], _maxNeighbors);
        
        for(int j=0; j<numNeighbors; j++) { // iterate over all neighbors
            nn = neighbors[j];
            ind = z[i]*SPARSE_MATRIX_SIZE + z[nn]; // index in the parameter array
            
            if (D0[ind]>0){ // if D0<=0 the interaction is assumed to be zero
                r = sqrt(diffs2[j]);

                t0=D0[ind]*y[ind]*exp(y[ind]*(1-r/R0[ind]));
                
                e1=exp(b1[ind]*(r-c1[ind]));
                t1=a1[ind]*b1[ind]*e1/((1+e1)*(1+e1));
                
                e2=exp(b2[ind]*(r-c2[ind]));
                t2=a2[ind]*b2[ind]*e2/((1+e2)*(1+e2));
                
                e3=exp(b3[ind]*(r-c3[ind]));
                t3=a3[ind]*b3[ind]*e3/((1+e3)*(1+e3));
                
                dV = (t0 + t1 + t2 + t3)/r;
                
                forces[i] -= .5*dV * diffs[j];
                forces[nn] += .5*dV * diffs[j];
            }
        }
    }
    DEBUGPRINT
}

//******************************************************************************
//                             GetPotentialEnergy
//******************************************************************************
double RahmanStillingerLemberg::GetPotentialEnergy(PyObject *pyatoms)
{
  DEBUGPRINT;
  ASSERT(atoms != NULL);
  atoms->Begin(pyatoms);
  CheckNeighborLists();
  DEBUGPRINT;
  double e = CalculateEnergyAndEnergies();
  atoms->End();
  return e;
}

const vector<double> &RahmanStillingerLemberg::GetPotentialEnergies(PyObject *pyatoms)
{
  DEBUGPRINT;
  ASSERT(atoms != NULL);
  atoms->Begin(pyatoms);
  CheckNeighborLists();
  CalculateEnergyAndEnergies();
  atoms->End();
  DEBUGPRINT;
  return atomicEnergies;
}

//******************************************************************************
//                           CalculateEnergyAndEnergies
//******************************************************************************
double RahmanStillingerLemberg::CalculateEnergyAndEnergies() 
{
    if (counters.energies != atoms->GetPositionsCounter()) {
        memset(&atomicEnergies[0], 0, nAtoms * sizeof(double));
        CalculateEnergyAndEnergies(atomicEnergies);
        counters.energies = atoms->GetPositionsCounter();
    }
    double energy = 0.0;
    ASSERT(atomicEnergies.size() == nAtoms);
    for (int a = 0; a < nAtoms; a++) {
        energy +=  atomicEnergies[a];
    }
    return energy;
}

void RahmanStillingerLemberg::CalculateEnergyAndEnergies(vector<double>& atomicEnergies)
{
    DEBUGPRINT;
    
    // definitions
    const asap_z_int *z; 
    int maxNeighbors, _maxNeighbors, ind, numNeighbors, nn;
    double r, t0, t1, t2, t3, V;
    maxNeighbors=neighborList->MaxNeighborListLength();
        
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);
    
    z = atoms->GetAtomicNumbers(); //lookup for atomic numbers
    
    for(int i = 0; i<nAtoms; i++){//iterate over all atoms
        _maxNeighbors=maxNeighbors;
        numNeighbors = neighborList->GetNeighbors(i, &neighbors[0], &diffs[0], &diffs2[0], _maxNeighbors);
        
        for(int j = 0; j<numNeighbors; j++) {// iterate over all neighbors
            nn = neighbors[j];
            ind = z[i]*SPARSE_MATRIX_SIZE+z[nn];
            
            if (D0[ind]>0){ // if D0<=0 the interaction is assumed to be zero
                r = sqrt(diffs2[j]);
                
                t0 = D0[ind]*exp(y[ind]*(1-r/R0[ind]));
                t1 = a1[ind]/(1+exp(b1[ind]*(r-c1[ind])));
                t2 = a2[ind]/(1+exp(b2[ind]*(r-c2[ind])));
                t3 = a3[ind]/(1+exp(b3[ind]*(r-c3[ind])));
                            
                V = .5*(t0 + t1 + t2 + t3);
                
                atomicEnergies[i] += V;
                
                if (nn < nAtoms)
                    atomicEnergies[nn] += V;
            }
        }
    }
    DEBUGPRINT;
}

long RahmanStillingerLemberg::PrintMemory() const
{
    cerr << "*MEM*  RahmanStillingerLemberg: Memory estimate not supported." << endl;
    return 0;
}
