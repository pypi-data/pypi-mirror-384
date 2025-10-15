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
 * Calculates the Lennard Jones potential
 */


// This implementation supports parallel simulations.  Due to the
// simplicity of Lennard-Jones, everything is handled by the
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
#include "MetalOxideInterface2.h"
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
//                             MetalOxideInterface2
//******************************************************************************
MetalOxideInterface2::MetalOxideInterface2(PyObject *self,
    double P_, double Q_, double A_, double xi_, double r0_, double RGL_cut_,
    const std::vector<double> &q_, double kappa_,
    const std::vector<double> &D_, const std::vector<double> &alpha_, const std::vector<double> &R0_,
    const std::vector<double> &a_, const std::vector<double> &b_, double &f0_, double &oxide_cut_,
    const std::vector<double> &E_, const std::vector<double> &rho0_, const std::vector<double> &l0_,
    const std::vector<double> &B_, const std::vector<double> &C_,
        double &interface_cut_, int verbose) : Potential(self, verbose)
{
    DEBUGPRINT;

    atoms = NULL;
    nAtoms = 0;
    neighborList= 0;
    neighborList_obj= 0;
    driftfactor = 0.05;

    // RGL potential
    P = P_;
    Q = Q_;
    A = A_;
    xi = xi_;
    r0 = r0_;

    // Coulomb potential
    q.resize(3);
    q[1]=q_[0]; // Metal charge
    q[2]=q_[1]; // Oxygen charge
    kappa = kappa_;

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
    f0 = f0_;

    a.resize(3);
    a[1]=a_[0]; // Oxide-side metal
    a[2]=a_[1]; // Oxygen

    b.resize(3);
    b[1]=b_[0]; // Oxide-side metal
    b[2]=b_[1]; // Oxygen

    // Interface potential
    E=E_;
    rho0=rho0_;
    l0=l0_;
    B=B_;
    C=C_;

    // Cut-off lengths
    RGL_cut = RGL_cut_;
    oxide_cut = oxide_cut_;
    interface_cut = interface_cut_;

    // Counters
    memset(&counters, 0x0, sizeof(counters));

    DEBUGPRINT;
}

MetalOxideInterface2::~MetalOxideInterface2()
{
    DEBUGPRINT;
    Py_XDECREF(neighborList_obj);
    if (atoms != NULL)
        AsapAtoms_DECREF(atoms);
}

void MetalOxideInterface2::SetAtoms(PyObject *pyatoms, Atoms* accessobj /* = NULL */)
{
  if (atoms != NULL)
    {
      // SetAtoms should only do anything the first time it is called.
      // Subsequent calls should just check for accessobj being NULL.
      if (accessobj != NULL)
    throw AsapError("MetalOxideInterface2::SetAtoms called multiple times with accessobj != NULL");
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
void MetalOxideInterface2::Allocate()
{
    DEBUGPRINT;
    if (verbose)
        cerr << "Allocate(" << nAtoms << ", " << nSize << ") " << endl;
    ASSERT(nAtoms != 0);

    assign.resize(nSize);
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


bool MetalOxideInterface2::CheckAndUpdateNbList(PyObject *pyatoms)
{
  atoms->Begin(pyatoms);
  bool updated = CheckNeighborLists();
  atoms->End();
  return updated;
}


//******************************************************************************
//                             CheckNeighborLists
//******************************************************************************
bool MetalOxideInterface2::CheckNeighborLists()
{
    DEBUGPRINT;
    if (counters.nblist == atoms->GetPositionsCounter() && neighborList != NULL && !neighborList->IsInvalid())
        return false;

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
    return true;
}

//******************************************************************************
//                               AssignAtoms
//******************************************************************************
void MetalOxideInterface2::AssignAtoms()
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
    
    memset(&assign[0], 0, nSize * sizeof(int));
    memset(&monolayer[0], 0, nSize * sizeof(int));
    memset(&metals[0], 0, nAtoms * sizeof(int));
    memset(&oxides[0], 0, nAtoms * sizeof(int));
    
    atoms->GetIntegerData("assignment", assign, true);
    atoms->GetIntegerData("monolayer", monolayer, true);

    nMetals=0;
    nOxides=0;

    for (int n = 0; n < nAtoms; n++) {

        if (assign[n]==0) {
            metals[nMetals] = n;
            nMetals += 1;
        }
        else if (assign[n]==1 || assign[n]==2) {
            oxides[nOxides] = n;
            nOxides += 1;
        }
    }
}

//******************************************************************************
//                               GetStresses 
//******************************************************************************
const vector<SymTensor> &MetalOxideInterface2::GetVirials(PyObject *pyatoms)
{
    throw AsapNotImplementedError("MetalOxideInterface2: Stresses not implemented");
}

//******************************************************************************
//                               GetForces 
//******************************************************************************
const vector<Vec> &MetalOxideInterface2::GetForces(PyObject *pyatoms)
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
void MetalOxideInterface2::RGLForces(vector<Vec>& forces) {

    DEBUGPRINT;

    int maxNeighbors = neighborList->MaxNeighborListLength();
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);
    
    for (int n = 0; n < nMetals; n++) {
        int nn = metals[n];
        
        int maxNeighbors_ = maxNeighbors;

        int nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], maxNeighbors_);

        for (int k = 0; k < nNeighbors; k++) {
            int kk = neighbors[k];
            
            if (((assign[kk]==0) && (monolayer[nn] + monolayer[kk] != 1))){
                double dr = sqrt(diffs2[k]);
                
                if (dr < RGL_cut) {
                    
                    double dx = dr / r0 - 1.;
                    double force_p = -A * P / r0 * exp(-P * dx);
                    double force_q = -xi * Q / r0 * exp(-2. * Q * dx);
                    
                    double force_n;
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

void MetalOxideInterface2::OxideForces(vector<Vec>& forces) {

    int maxNeighbors = neighborList->MaxNeighborListLength();   
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);

    double sqrtPi = 1.772453851;
    
    for (int n = 0; n < nOxides; n++) {
        int nn = oxides[n];
        
        int maxNeighbors_ = maxNeighbors;

        int nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], maxNeighbors_);
        
        for (int k = 0; k < nNeighbors; k++) {
            int kk = neighbors[k];

            if ((assign[kk] == 1 || assign[kk] == 2)){

                double dr = sqrt(diffs2[k]);
                
                double result = 0.;
                
                if (dr < oxide_cut) {
                    
                    // Monolayer charge modification
                    double qnn = q[assign[nn]];
                    double qkk = q[assign[kk]];
                    
                    if (monolayer[nn] == 1)
                        qnn *= .5;
                    if (monolayer[kk] == 1)
                        qkk *= .5;
                    
                    // Coulomb
                    double force_exp = -kappa * qnn * qkk * exp(-kappa * kappa * diffs2[k]) / (sqrtPi * dr);
                    double force_erfc = -.5 * qnn * qkk * Erfc(kappa * dr) / diffs2[k];
                    result += (force_exp + force_erfc)/dr;
                    
                    // Morse
                    int ind = assign[nn] + assign[kk];
                    
                    if (D[ind] != 0) {
                        double dx = alpha[ind] * (dr - R0[ind]);
                        double expdx = exp(-dx);
                        result += alpha[ind] * D[ind] * (expdx - expdx*expdx) / dr;
                    }
                    
                    // Additional
                    result += -.5 * f0 * exp((a[assign[nn]] + a[assign[kk]] - dr)
                        / (b[assign[nn]] + b[assign[kk]])) / dr;
                    
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

void MetalOxideInterface2::InterfaceForces(vector<Vec>& forces) {

    int maxNeighbors = neighborList->MaxNeighborListLength();
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);

    for (int n = 0; n < nAtoms; n++) {
        
        int maxNeighbors_ = maxNeighbors;

        int nNeighbors = neighborList->GetNeighbors(n, &neighbors[0], 
            &diffs[0], &diffs2[0], maxNeighbors_);
                
        for (int k = 0; k < nNeighbors; k++) {
            
            int kk = neighbors[k];
            
            int ind = assign[n] + assign[kk];
            
            if (((assign[n] == 0 || assign[kk] == 0) && ind > 0)
             || ((monolayer[n] + monolayer[kk] == 1) && ind == 0)){

                double dr = sqrt(diffs2[k]);

                if (dr < oxide_cut) {

                    double dx = (rho0[ind] - dr)/l0[ind];
                    
                    double result = .5 * E[ind] / l0[ind] * exp(dx) * dx / dr;

                    if (C[ind] > 0.)
                        result += .5 * C[ind] * B[ind] * exp(-B[ind] * dr) / dr;
            
                    // Assign resulting force
                    if (kk < nAtoms)
                        result *= 2.;
                
                    forces[n] += result * diffs[k];
                    forces[kk] -= result * diffs[k];
                }
            }
        }
    }
    DEBUGPRINT;
}

//******************************************************************************
//                             GetPotentialEnergy
//******************************************************************************
double MetalOxideInterface2::GetPotentialEnergy(PyObject *pyatoms)
{
    DEBUGPRINT;
    ASSERT(atoms != NULL);
    atoms->Begin(pyatoms);
    CheckNeighborLists();
    AssignAtoms();
    double e = CalculateEnergyAndEnergies();
    atoms->End();
    return e;
}

const vector<double> &MetalOxideInterface2::GetPotentialEnergies(PyObject *pyatoms)
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
double MetalOxideInterface2::CalculateEnergyAndEnergies() 
{
    if (counters.energies != atoms->GetPositionsCounter()) {
        memset(&atomicEnergies[0], 0, nAtoms * sizeof(double));

        RGL(atomicEnergies);
        Oxide(atomicEnergies);
        InterfacePotential(atomicEnergies);
        counters.energies = atoms->GetPositionsCounter();
    }

    double energy = 0.;
    ASSERT(atomicEnergies.size() == nAtoms);
    
    for (int i = 0; i < nAtoms; i++)
        energy += atomicEnergies[i];

    return energy;
}

void MetalOxideInterface2::RGL(vector<double>& atomicEnergies)
{
    int maxNeighbors = neighborList->MaxNeighborListLength();
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);
    
    for (int i = 0; i < nAtoms; i++) {
        sigma_p[i] = 0.0;
        sigma_q[i] = 0.0;
    }

    for (int n = 0; n < nMetals; n++) {
        int nn=metals[n];
        
        int maxNeighbors_ = maxNeighbors;

        int nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], maxNeighbors_);
                
        for (int k = 0; k < nNeighbors; k++) {
            
            int kk = neighbors[k];
            
            if (((assign[kk]==0) && (monolayer[nn] + monolayer[kk] != 1))){
                
                double dr = sqrt(diffs2[k]);
                
                if (dr < RGL_cut) {
                    
                    // Calculate energy
                    double dx = dr / r0 - 1.;
                    double dp = exp(-P * dx);
                    double dq = exp(-2 * Q * dx);
                    
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

void MetalOxideInterface2::Oxide(vector<double>& atomicEnergies)
{
    DEBUGPRINT;

    int maxNeighbors = neighborList->MaxNeighborListLength();
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);

    vector<double> eShift(5);
        
    eShift = OxideShift();


    for (int n = 0; n < nOxides; n++) {
        int nn=oxides[n];
        
        int maxNeighbors_ = maxNeighbors;
        
        int nNeighbors = neighborList->GetNeighbors(nn, &neighbors[0], 
            &diffs[0], &diffs2[0], maxNeighbors_);
        
        for (int k = 0; k < nNeighbors; k++) {
            
            int kk = neighbors[k];

            if ((assign[kk] == 1 || assign[kk] == 2)){
                
                double dr = sqrt(diffs2[k]);
                
                double result=0.;
                
                if (dr < oxide_cut) {

                    int ind = assign[nn] + assign[kk];
                    
                    // Monolayer charge modification
                    double qnn = q[assign[nn]];
                    double qkk = q[assign[kk]];
                    
                    if (monolayer[nn] == 1)
                        qnn *= .5;
                    if (monolayer[kk] == 1)
                        qkk *= .5;
                    
                    // Coulomb
                    result += .5*qnn*qkk*Erfc(kappa*dr)/dr;

                    // Morse
                    if (D[ind] != 0) {
                        double dx = alpha[ind]*(dr - R0[ind]);
                        double expdx = exp(-dx);
                        result += .5*D[ind]*(expdx*expdx - 2*expdx);
                    }

                    // Additional
                    result += .5*f0*(b[assign[nn]] + b[assign[kk]])
                        *exp((a[assign[nn]] + a[assign[kk]] - dr) / (b[assign[nn]] + b[assign[kk]]));

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

void MetalOxideInterface2::InterfacePotential(vector<double>& atomicEnergies)
{
    DEBUGPRINT;
    int maxNeighbors = neighborList->MaxNeighborListLength();
    vector<int> neighbors(maxNeighbors);
    vector<double> diffs2(maxNeighbors);
    vector<Vec> diffs(maxNeighbors);
    
    vector<double> eShift(3);
    eShift = InterfaceShift();

    for (int n = 0; n < nAtoms; n++) {
        
        int maxNeighbors_ = maxNeighbors;

        int nNeighbors = neighborList->GetNeighbors(n, &neighbors[0], 
            &diffs[0], &diffs2[0], maxNeighbors_);
                
        for (int k = 0; k < nNeighbors; k++) {

            int kk = neighbors[k];

            int ind = assign[n] + assign[kk];

            if (((assign[n] == 0 || assign[kk] == 0) && ind > 0)
             || ((monolayer[n] + monolayer[kk] == 1) && ind == 0)){

                double dr = sqrt(diffs2[k]);

                if (dr < oxide_cut) {

                    double dx = (rho0[ind] - dr)/l0[ind];

                    double result = .5*E[ind] * (1 - dx) * exp(dx);

                    if (C[ind] > 0.)
                        result += -.5*C[ind]*exp(-B[ind] * dr);

                    atomicEnergies[n] += result - eShift[ind];

                    if (kk < nAtoms)
                        atomicEnergies[kk] += result - eShift[ind];
                }
            }
        }
    }
    DEBUGPRINT;
}

double MetalOxideInterface2::Erfc(double x) {
    // Reference for this approximation is found in Abramowitz and Stegun, 
    // Handbook of mathematical functions, eq. 7.1.26
    
    static const double a1=0.254829592, a2=-0.284496736;
    static const double a3=1.421413741, a4=-1.453152027;
    static const double a5=1.061405429, p1=0.3275911;

    double t = 1.0/(1.0 + p1 * x);
    double xsq = x * x;
    double tp = t * (a1 + t * (a2 + t * (a3 + t * (a4 + t * a5))));
    return tp * exp(-xsq);
}

long MetalOxideInterface2::PrintMemory() const
{
    cerr << "*MEM*  MetalOxideInterface2: Memory estimate not supported." << endl;
    return 0;
}

std::vector<double> MetalOxideInterface2::OxideShift() {
    std::vector<double> eShift(5);
    
    for (int n = 1; n < 3; n++) {
        for (int k = 1; k < 3; k++) {
            int ind=n+k;
            eShift[ind] = 0;
            
            eShift[ind] += .5*q[n]*q[k]*Erfc(kappa*oxide_cut)/oxide_cut;
            
            double dx = alpha[ind]*(oxide_cut - R0[ind]);
            double expdx = exp(-dx);
            eShift[ind] += .5*D[ind]*(expdx*expdx - 2*expdx);
            
            eShift[ind] += .5*f0*(b[n]+b[k])*exp((a[n]+a[k]-oxide_cut)/(b[n]+b[k]));
        }
    }
    return eShift;
}

std::vector<double> MetalOxideInterface2::InterfaceShift() {
    std::vector<double> eShift(3);
    
    for (int n = 1; n < 3; n++) {
        eShift[n] = 0;
        
        double dx = (rho0[n] - interface_cut)/l0[n];
        
        eShift[n] = .5*E[n] * (1-dx) * exp(dx);

        if (C[n] > 0.)
            eShift[n] += -.5*C[n]*exp(-B[n] * interface_cut);
    }
    return eShift;
}
