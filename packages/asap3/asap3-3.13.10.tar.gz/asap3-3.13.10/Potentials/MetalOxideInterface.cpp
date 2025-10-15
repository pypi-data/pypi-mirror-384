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
 * Calculates a potential for a Metal/Oxide interface including 
 * interactions within the metal and oxide
 */

#include "AsapPython.h"
#include "Asap.h"
#include "MetalOxideInterface.h"
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

#if 1
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
//                             MetalOxideInterface
//******************************************************************************
MetalOxideInterface::MetalOxideInterface(PyObject *self,
    double P, double Q, double A, double xi, double r0, double RGL_cut,
    const std::vector<double> &q_, double kappa,
    const std::vector<double> &D_, const std::vector<double> &alpha_, const std::vector<double> &R0_,
    const std::vector<double> &a_, const std::vector<double> &b_, double &f0, double &oxide_cut,
    const std::vector<double> &beta_, double gamma, double &interface_cut,
    int verbose) : Potential(self, verbose)
{
    DEBUGPRINT;
    
    atoms = NULL;
    this->nAtoms = 0;
    neighborList= 0;
    neighborList_obj= 0;
    driftfactor = 0.05;
    
    // RGL potential
    this->P = P;
    this->Q = Q;
    this->A = A;
    this->xi = xi;
    this->r0 = r0;
    
    // Coulomb potential
    q.resize(3);
    q[1]=q_[0]; // Metal charge
    q[2]=q_[1]; // Oxygen charge
    this->kappa = kappa;
    
    // Morse potential
    D.resize(5);
    D[2]=D_[0]; // Metal-metal interaction
    D[3]=D_[1]; // Metal-oxygen interaction
    D[4]=D_[2]; // Oxygen-oxygen interaction
    
    alpha.resize(5);
    alpha[2]=alpha_[0]; // Metal-metal interaction
    alpha[3]=alpha_[1]; // Metal-oxygen interaction
    alpha[4]=alpha_[2]; // Oxygen-oxygen interaction
    
    R0.resize(5);
    R0[2]=R0_[0]; // Metal-metal interaction
    R0[3]=R0_[1]; // Metal-oxygen interaction
    R0[4]=R0_[2]; // Oxygen-oxygen interaction
    
    // Additional oxide potential
    this->f0 = f0;
    
    a.resize(3);
    a[1]=a_[0]; // Oxide-side metal
    a[2]=a_[1]; // Oxygen
    
    b.resize(3);
    b[1]=b_[0]; // Oxide-side metal
    b[2]=b_[1]; // Oxygen
    
    // Fitting parameters
    this->gamma=gamma;
    
    beta.resize(3);
    beta[0]=beta_[0]; // Metal side metal
    beta[1]=beta_[1]; // Oxide side metal
    beta[2]=beta_[2]; // Oxygen
    
    // Cut-off lengths
    this->RGL_cut = RGL_cut;
    this->oxide_cut = oxide_cut;
    this->interface_cut = interface_cut;
    
    // Counters
    memset(&counters, 0x0, sizeof(counters));
    
    DEBUGPRINT;
}

MetalOxideInterface::~MetalOxideInterface()
{
    DEBUGPRINT;
    Py_XDECREF(neighborList_obj);
    if (atoms != NULL)
        AsapAtoms_DECREF(atoms);
}

void MetalOxideInterface::SetAtoms(PyObject *pyatoms, Atoms* accessobj /* = NULL */)
{
  if (atoms != NULL)
    {
      // SetAtoms should only do anything the first time it is called.
      // Subsequent calls should just check for accessobj being NULL.
      if (accessobj != NULL)
    throw AsapError("MetalOxideInterface::SetAtoms called multiple times with accessobj != NULL");
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
void MetalOxideInterface::Allocate()
{
    DEBUGPRINT;
    if (verbose)
        cerr << "Allocate(" << nAtoms << ", " << nSize << ") " << endl;
    ASSERT(nAtoms != 0);
    
    assignment.resize(nSize);
    monolayer.resize(nSize);
    
    metals.resize(nAtoms);
    oxides.resize(nAtoms);
    
    sigma_p.resize(nAtoms);
    sigma_q.resize(nAtoms);
    atomicEnergies.resize(nAtoms);

    forces.resize(nSize);
    
    virials.resize(nSize);
    
    DEBUGPRINT;
}

bool MetalOxideInterface::CheckAndUpdateNbList(PyObject *pyatoms)
{
  atoms->Begin(pyatoms);
  bool updated = CheckNeighborLists();
  atoms->End();
  return updated;
}


//******************************************************************************
//                             CheckNeighborLists
//******************************************************************************
bool MetalOxideInterface::CheckNeighborLists()
{
    DEBUGPRINT;
    if (counters.nblist == atoms->GetPositionsCounter() && neighborList != NULL && !neighborList->IsInvalid())
        return true;

    bool update = false;
    if (neighborList) {
        DEBUGPRINT;
        update = neighborList->CheckNeighborList();
        
        update = atoms->UpdateBeforeCalculation(update, oxide_cut * (1 + driftfactor));
        
        if (update)
            neighborList->UpdateNeighborList();

        if ((nAtoms != atoms->GetNumberOfAtoms()) || (nSize != nAtoms + atoms->GetNumberOfGhostAtoms())) {
            DEBUGPRINT;
            ASSERT(update);
        
            nAtoms = atoms->GetNumberOfAtoms();
        
            nSize = nAtoms + atoms->GetNumberOfGhostAtoms();
        
            Allocate();
        }
    }
    else {
        DEBUGPRINT;
        update = true;
        atoms->UpdateBeforeCalculation(true, oxide_cut * (1 + driftfactor));
        
        PyAsap_NeighborLocatorObject *nbl = PyAsap_NewNeighborList(atoms, oxide_cut, driftfactor);
        
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
//                               AssignAtoms
//******************************************************************************
void MetalOxideInterface::AssignAtoms()
{
    DEBUGPRINT;

    // Fill up identification arrays
    // Assignment:
    // 0 = metal-side metal atom
    // 1 = oxide-side metal atom
    // 2 = oxygen atom
    // Monolayer:
    // 0 = not monolayer atom
    // 1 = monolayer atom
    
    memset(&assignment[0], 0, nSize * sizeof(int));
    memset(&monolayer[0], 0, nSize * sizeof(int));
    memset(&metals[0], 0, nAtoms * sizeof(int));
    memset(&oxides[0], 0, nAtoms * sizeof(int));
    
    atoms->GetIntegerData("assignment", assignment, true);
    atoms->GetIntegerData("monolayer", monolayer, true);

    nMetals=0;
    nOxides=0;

    for (int n = 0; n < nAtoms; n++) {
        
        if (assignment[n]==0) {
            metals[nMetals] = n;
            nMetals += 1;
        }
        else if (assignment[n]==1 || assignment[n]==2) {
            oxides[nOxides] = n;
            nOxides += 1;
        }
    }
}

//******************************************************************************
//                               GetStresses 
//******************************************************************************
const vector<SymTensor> &MetalOxideInterface::GetVirials(PyObject *pyatoms)
{
    throw AsapNotImplementedError("MetalOxideInterface: Stresses not implemented");
}

//******************************************************************************
//                               GetForces 
//******************************************************************************
const vector<Vec> &MetalOxideInterface::GetForces(PyObject *pyatoms)
{
    ASSERT(atoms != NULL);
    atoms->Begin(pyatoms);
    CheckNeighborLists();
    AssignAtoms();
    ASSERT(nSize >= nAtoms);
    ASSERT(forces.size() == nSize);
    memset((void *) &(forces[0]), 0, nSize * sizeof(Vec)); //zero the forces
    
    RGL(atomicEnergies);
    
    RGLForces(forces);
    OxideForces(forces);
    InterfaceForces(forces);
    
    atoms->End();
    return forces;
}

//******************************************************************************
//                           GetCartesianForces
//******************************************************************************
void MetalOxideInterface::RGLForces(vector<Vec>& forces) {

    int maxNeighbors = neighborList->MaxNeighborListLength();
    int nn, kk, _maxNeighbors, nNeighbors;
    double dr, dx, beta_;
    double force_p, force_q, force_n;
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);
    
    for (int n = 0; n < nMetals; n++) {
        nn = metals[n];
        
        _maxNeighbors = maxNeighbors;
        nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], _maxNeighbors);

        for (int k = 0; k < nNeighbors; k++) {
            kk = neighbors[k];
            
            if (assignment[kk]==0){
                dr = sqrt(diffs2[k]);
                
                if (dr < RGL_cut) {
                    
                    // Modify monolayer/bulk interaction 
                    beta_=1;
                    if (monolayer[nn] + monolayer[kk] == 1) {
                        beta_=beta[0];
                    }
                    
                    force_p = 0.; force_q = 0.;
                    
                    dx = dr / r0 - 1.;
                    force_p =  -A * P / r0 * beta_ * exp(-P * dx);
                    force_q =  -xi * Q / r0 * beta_ * exp(-2. * Q * dx);
                    
                    if (kk < nAtoms) {
                        force_n = (force_p - force_q * (1. / sqrt(sigma_q[nn]) 
                            + 1. / sqrt(sigma_q[kk]))) / dr;
                    }
                    else {
                        force_n = (.5*force_p - force_q / sqrt(sigma_q[nn])) / dr;
                    }
                    
                    forces[nn] += force_n * diffs[k];
                    forces[kk] -= force_n * diffs[k];
                }
            }
        }
    }

    DEBUGPRINT;
}

void MetalOxideInterface::OxideForces(vector<Vec>& forces) {

    int maxNeighbors = neighborList->MaxNeighborListLength();
    int nn, kk, _maxNeighbors, nNeighbors, ind  ;
    double dr, force_exp, force_erfc, sqrtPi;
    double dx, expdx, result, qnn, qkk;
    
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);

    sqrtPi=1.772453851;
    
    for (int n = 0; n < nOxides; n++) {
        nn=oxides[n];
        
        _maxNeighbors = maxNeighbors;
        nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], _maxNeighbors);
        
        for (int k = 0; k < nNeighbors; k++) {
            kk = neighbors[k];

            if ((assignment[kk] == 1 || assignment[kk] == 2)){

                dr = sqrt(diffs2[k]);
                
                result = 0;
                
                if (dr < oxide_cut) {
                    
                    // Monolayer charge modification
                    qnn = q[assignment[nn]];
                    qkk = q[assignment[kk]];
                    
                    if (monolayer[nn] == 1){
                        qnn *= .5;
                    }
                    if (monolayer[kk] == 1){
                        qkk *= .5;
                    }

                    
                    // Coulomb
                    force_exp = -kappa*qnn*qkk*exp(-kappa* kappa * diffs2[k])/(sqrtPi*dr);
                    force_erfc = -.5*qnn*qkk*Erfc(kappa*dr)/diffs2[k];
                    result += (force_exp+force_erfc)/dr;
                    
                    // Morse
                    ind=assignment[nn]+assignment[kk];
                    
                    if (D[ind] != 0) {
                        dx = alpha[ind]*(dr - R0[ind]);
                        expdx=exp(-dx);
                        result += alpha[ind]*D[ind]*(expdx - expdx*expdx) / dr;
                    }
                    
                    // Additional
                    result += -.5*f0*exp((a[assignment[nn]]+a[assignment[kk]]-dr)/(b[assignment[nn]]+b[assignment[kk]])) / dr;
                    
                    // Assign resulting force
                    if (kk < nAtoms)
                        result *= 2.;
                
                    forces[nn] += result * diffs[k];
                    forces[kk] -= result * diffs[k];
                }
            }
        }
    }
    DEBUGPRINT;
}

void MetalOxideInterface::InterfaceForces(vector<Vec>& forces) {

    int maxNeighbors = neighborList->MaxNeighborListLength();
    int nn, kk, _maxNeighbors, nNeighbors;
    double dr, result, dx, expdx, gamma_;
    
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);

    for (int n = 0; n < nAtoms; n++) {
        nn=n;
        
        _maxNeighbors = maxNeighbors;
        nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], _maxNeighbors);
                
        for (int k = 0; k < nNeighbors; k++) {
            
            kk = neighbors[k];
            
            result = 0;
            
            // Modify monolayer fit value gamma
            gamma_ = 1;
            if (((assignment[kk] == 0 && monolayer[kk] == 1)
               ||(assignment[nn] == 0 && monolayer[nn] == 1))) {
                gamma_ = gamma;
            }
            
            // Metal-metal interface interaction
            if (((assignment[kk] == 0 && assignment[nn] == 1)
               ||(assignment[nn] == 0 && assignment[kk] == 1))){
                
                dr = sqrt(diffs2[k]);
                
                if (dr < interface_cut) {
                    result += -.5*gamma_*f0*exp((2*beta[1]*a[1]-dr)/(2*b[1])) / dr;
                }
            } // Metal-oxygen interface interaction
            else if (((assignment[kk] == 0 && assignment[nn] == 2)
                    ||(assignment[nn] == 0 && assignment[kk] == 2))){
                
                dr = sqrt(diffs2[k]);
                
                if (dr < interface_cut) {

                    result += -.5*gamma_*beta[2]*f0*exp((a[1]+a[2]-dr)/(b[1]+b[2])) / dr;
                    
                    dx = alpha[3]*(dr - R0[3]);
                    expdx=exp(-dx);
                    
                    result += gamma_*beta[2]*D[3]*alpha[3]*(expdx - expdx*expdx) / dr;
                }
            }
            
            // Assign resulting force
            if (kk < nAtoms)
                result *= 2.;
        
            forces[nn] += result * diffs[k];
            forces[kk] -= result * diffs[k];
        }
    }
    
    DEBUGPRINT;
}

//******************************************************************************
//                             GetPotentialEnergy
//******************************************************************************
double MetalOxideInterface::GetPotentialEnergy(PyObject *pyatoms)
{
    DEBUGPRINT;
    ASSERT(atoms != NULL);
    atoms->Begin(pyatoms);
    CheckNeighborLists();
    AssignAtoms();
    DEBUGPRINT;
    double e = CalculateEnergyAndEnergies();
    atoms->End();
    return e;
}

const vector<double> &MetalOxideInterface::GetPotentialEnergies(PyObject *pyatoms)
{
    DEBUGPRINT;
    ASSERT(atoms != NULL);
    atoms->Begin(pyatoms);
    CheckNeighborLists();
    AssignAtoms();
    CalculateEnergyAndEnergies();
    atoms->End();
    DEBUGPRINT;
    return atomicEnergies;
}

//******************************************************************************
//                           CalculateEnergyAndEnergies
//******************************************************************************
double MetalOxideInterface::CalculateEnergyAndEnergies() 
{
    if (counters.energies != atoms->GetPositionsCounter()) {
        memset(&atomicEnergies[0], 0, nAtoms * sizeof(double));

        RGL(atomicEnergies);
        Oxide(atomicEnergies);
        InterfacePotential(atomicEnergies);
        counters.energies = atoms->GetPositionsCounter();
    }
    double energy = 0.0;
    ASSERT(atomicEnergies.size() == nAtoms);
    
    for (int i = 0; i < nAtoms; i++) {
        energy += atomicEnergies[i];
    }
    return energy;
}

void MetalOxideInterface::RGL(vector<double>& atomicEnergies)
{
    int maxNeighbors = neighborList->MaxNeighborListLength();
    int nn, kk, _maxNeighbors, nNeighbors;
    double dr, dx, dp, dq, beta_;
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);
    
    for (int i = 0; i < nAtoms; i++) {
        sigma_p[i] = 0.0;
        sigma_q[i] = 0.0;
    }

    for (int n = 0; n < nMetals; n++) {
        nn=metals[n];
        
        _maxNeighbors = maxNeighbors;
        nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], _maxNeighbors);
                
        for (int k = 0; k < nNeighbors; k++) {
            
            kk = neighbors[k];
            
            if (assignment[kk]==0){
                
                dr = sqrt(diffs2[k]);
                
                if (dr < RGL_cut) {
                    
                    // Modify monolayer/bulk interaction 
                    beta_=1;
                    if (monolayer[nn] + monolayer[kk] == 1) {
                        beta_=beta[0];
                    }
                    
                    // Calculate energy
                    dx = dr / r0 - 1.;
                    dp = beta_*exp(-P * dx);
                    dq = beta_*exp(-2 * Q * dx);
                    
                    sigma_p[nn] += dp;
                    sigma_q[nn] += dq;
                    
                    if (kk < nAtoms) {
                        sigma_p[kk] += dp;
                        sigma_q[kk] += dq;
                    }
                }
            }
        }
        atomicEnergies[nn] = .5*A*sigma_p[nn] - xi*sqrt(sigma_q[nn]);
    }
}

void MetalOxideInterface::Oxide(vector<double>& atomicEnergies)
{
    DEBUGPRINT;

    int maxNeighbors = neighborList->MaxNeighborListLength();
    int nn, kk, _maxNeighbors, nNeighbors, ind;
    double dr, result, dx, expdx, qnn, qkk;
    
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);
    vector<double> eShift(5);
    
    
    eShift = OxideShift();

    for (int n = 0; n < nOxides; n++) {
        nn=oxides[n];
        
        _maxNeighbors = maxNeighbors;
        nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], _maxNeighbors);
        
        for (int k = 0; k < nNeighbors; k++) {
            
            kk = neighbors[k];

            if ((assignment[kk] == 1 || assignment[kk] == 2)){
                
                dr = sqrt(diffs2[k]);
                result=0;
                
                if (dr < oxide_cut) {
                    ind=assignment[nn]+assignment[kk];
                    
                    // Monolayer charge modification
                    qnn = q[assignment[nn]];
                    qkk = q[assignment[kk]];
                    
                    if (monolayer[nn] == 1){
                        qnn *= .5;
                    }
                    if (monolayer[kk] == 1){
                        qkk *= .5;
                    }
                    

                    
                    // Coulomb
                    result += .5*qnn*qkk*Erfc(kappa*dr)/dr;

                    //~ // Morse
                    if (D[ind] != 0) {
                        
                        dx = alpha[ind]*(dr - R0[ind]);
                        expdx=exp(-dx);
                        
                        result += .5*D[ind]*(expdx*expdx - 2*expdx);
                        
                    }
                    
                    // Additional
                    result += .5*f0*(b[assignment[nn]]+b[assignment[kk]])
                        *exp((a[assignment[nn]]+a[assignment[kk]]-dr)/(b[assignment[nn]]+b[assignment[kk]]));
                    
                    // Assign resulting energy
                    atomicEnergies[nn]+=result-eShift[ind];
                    
                    if (kk < nAtoms) {
                        atomicEnergies[kk] += result-eShift[ind];
                    }
                }
            }
        }
    }
    DEBUGPRINT;
}

std::vector<double> MetalOxideInterface::OxideShift() {
    std::vector<double> eShift;
    double dx, expdx;
    
    eShift.resize(5);
    
    int ind;
    
    for (int n = 1; n < 3; n++) {
        for (int k = 1; k < 3; k++) {
            ind=n+k;
            eShift[ind] = 0;
            
            eShift[ind] += .5*q[n]*q[k]*Erfc(kappa*oxide_cut)/oxide_cut;
            
            dx = alpha[ind]*(oxide_cut - R0[ind]);
            dx = alpha[ind]*(oxide_cut - R0[ind]);
            expdx = exp(-dx);
            eShift[ind] += .5*D[ind]*(expdx*expdx - 2*expdx);
            
            eShift[ind] += .5*f0*(b[n]+b[k])*exp((a[n]+a[k]-oxide_cut)/(b[n]+b[k]));
        }
    }
    return eShift;
}

double MetalOxideInterface::Erfc(double x) {
    // Reference for this approximation is found in Abramowitz and Stegun, 
    // Handbook of mathematical functions, eq. 7.1.26
    
    static const double a1=0.254829592, a2=-0.284496736;
    static const double a3=1.421413741, a4=-1.453152027;
    static const double a5=1.061405429, p1=0.3275911;

    double t,tp,xsq;

    t = 1.0/(1.0+p1*x);
    xsq=x*x;
    tp = t*(a1+t*(a2+t*(a3+t*(a4+t*a5))));
    return tp*exp(-xsq);
}

void MetalOxideInterface::InterfacePotential(vector<double>& atomicEnergies)
{
    DEBUGPRINT;

    int maxNeighbors = neighborList->MaxNeighborListLength();
    int nn, kk, _maxNeighbors, nNeighbors;
    double dr, result, dx, expdx, gamma_;
    
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);

    for (int n = 0; n < nAtoms; n++) {
        nn=n;
        
        _maxNeighbors = maxNeighbors;
        nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], _maxNeighbors);
                
        for (int k = 0; k < nNeighbors; k++) {
            
            kk = neighbors[k];
            
            result = 0;
            
            // Modify monolayer fit value gamma
            gamma_ = 1;
            if (((assignment[kk] == 0 && monolayer[kk] == 1)
               ||(assignment[nn] == 0 && monolayer[nn] == 1))) {
                gamma_ = gamma;
            }
            
            // Metal-metal interface interaction
            if (((assignment[kk] == 0 && assignment[nn] == 1)
               ||(assignment[nn] == 0 && assignment[kk] == 1))){
                
                dr = sqrt(diffs2[k]);
                
                if (dr < interface_cut) {
                    result += gamma_*f0*b[1]*exp((2*beta[1]*a[1]-dr)/(2*b[1]));
                }
            } // Metal-oxygen interface interaction
            else if (((assignment[kk] == 0 && assignment[nn] == 2)
                    ||(assignment[nn] == 0 && assignment[kk] == 2))){
                

                
                dr = sqrt(diffs2[k]);
                
                if (dr < interface_cut) {

                    result += .5*gamma_*beta[2]*f0*(b[1]+b[2])
                        *exp((a[1]+a[2]-dr)/(b[1]+b[2]));
                    
                    dx = alpha[3]*(dr - R0[3]);
                    expdx=exp(-dx);
                    
                    result += .5*gamma_*beta[2]*D[3]*(expdx*expdx - 2*expdx);
                }
            }
            // Assign resulting energy
            atomicEnergies[nn]+=result;

            if (kk < nAtoms)
                atomicEnergies[kk] += result;
        }
    }
    DEBUGPRINT;
}

long MetalOxideInterface::PrintMemory() const
{
    cerr << "*MEM*  MetalOxideInterface: Memory estimate not supported." << endl;
    return 0;
}

