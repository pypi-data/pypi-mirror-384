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

#include "ParallelPotential.h"
#include "ParallelAtoms.h"
#include "DomainDecomposition.h"
#include "Vec.h"
#include "AsapMPI.h"
#include "Timing.h"
// #define ASAPDEBUG
#include "Debug.h"
#include <set>
using std::cerr;
using std::endl;
using std::flush;
using std::set;

ParallelPotential::ParallelPotential(PyObject *self, PyObject *p, int verbose) :
  Potential(self, verbose), py_potential(NULL)
{
  CONSTRUCTOR;
  DEBUGPRINT;
  par_atoms = NULL;
  if (!PyAsap_PotentialCheck(p))
    throw AsapError("Expected an Asap potential, got a ")
      << Py_TYPE(p)->tp_name;
  potential = ((PyAsap_PotentialObject *) p)->cobj;
  ASSERT(potential != NULL);
  if (!potential->Parallelizable())
    throw AsapError("This potential cannot be used in parallel simulations");
  py_potential = p;
  stress_collect_cnt = force_collect_cnt = 0;
  Py_INCREF(py_potential);
  DEBUGPRINT;
}

ParallelPotential::~ParallelPotential()
{
  DESTRUCTOR;
  Py_XDECREF(py_potential);
  if (par_atoms != NULL)
    AsapAtoms_DECREF(par_atoms);
}

void ParallelPotential::SetAtoms(PyObject *pyatoms,
				 Atoms* accessobj /* = NULL */)
{
  DEBUGPRINT;
  ASSERT(accessobj == NULL);
  par_atoms = new ParallelAtoms(pyatoms, verbose);
  atoms = par_atoms;
  potential->SetAtoms_ThroughPython(pyatoms, par_atoms);
  mpi = par_atoms->GetCommunicator();
  // This MAY have changed the Potential object as an ImagePotential may
  // have been intercalated.
  potential = ((PyAsap_PotentialObject *) py_potential)->cobj;
  ASSERT(mpi != NULL);
  DEBUGPRINT;
}

bool ParallelPotential::CalcReq_Energy(PyObject *a)
{
  USETIMER("ParallelPotential::CalcReq_Energy");
  return mpi->LogicalOr(potential->CalcReq_Energy(a));
}

bool ParallelPotential::CalcReq_Forces(PyObject *a)
{
  USETIMER("ParallelPotential::CalcReq_Forces");
  return mpi->LogicalOr(potential->CalcReq_Forces(a));
}

bool ParallelPotential::CalcReq_Virials(PyObject *a)
{
  USETIMER("ParallelPotential::CalcReq_Virials");
  return mpi->LogicalOr(potential->CalcReq_Virials(a));
}

bool ParallelPotential::CalcReq_Virial(PyObject *a)
{
  USETIMER("ParallelPotential::CalcReq_Virial");
  return mpi->LogicalOr(potential->CalcReq_Virial(a));
}

double ParallelPotential::GetPotentialEnergy(PyObject *a)
{
  USETIMER("ParallelPotential::GetPotentialEnergy");
  return mpi->Add(potential->GetPotentialEnergy(a));
}


const vector<double> &ParallelPotential::GetPotentialEnergies(PyObject *a)
{
  DEBUGPRINT;
  USETIMER("ParallelPotential::GetPotentialEnergies");
  return potential->GetPotentialEnergies(a);
  DEBUGPRINT;
}

const vector<Vec> &ParallelPotential::GetForces(PyObject *a)
{
  USETIMER("ParallelPotential::GetForces");
  DEBUGPRINT;
  par_atoms->Begin(a, true);  // Allow reopen.
  try {
    int cnt = par_atoms->GetPositionsCounter();
    if (force_collect_cnt != cnt)
      {
        DEBUGPRINT;
        const vector<Vec> &orig_forces = potential->GetForces(a);
        forces = orig_forces;
        par_atoms->CollectFromGhosts(forces);
        forces.resize(par_atoms->GetNumberOfAtoms());
        force_collect_cnt = cnt;
      }
  }
  catch (AsapErrorBase &)
  {
      atoms->End();
      throw;
  }
  par_atoms->End();
  DEBUGPRINT;
  return forces;
}

const vector<SymTensor> &ParallelPotential::GetVirials(PyObject *a)
{
  USETIMER("ParallelPotential::GetVirialss");
  DEBUGPRINT;
  par_atoms->Begin(a, true);  // Allow reopen.
  try {
    int cnt = par_atoms->GetPositionsCounter();
    if (stress_collect_cnt != cnt)
      {
        DEBUGPRINT;
        const vector<SymTensor> &orig_stresses = potential->GetVirials(a);
        stresses = orig_stresses;
        par_atoms->CollectFromGhosts(stresses);
        stresses.resize(par_atoms->GetNumberOfAtoms());
        stress_collect_cnt = cnt;
      }
  }
  catch (AsapErrorBase &)
  {
      atoms->End();
      throw;
  }
  par_atoms->End();
  DEBUGPRINT;
  return stresses;
}

SymTensor ParallelPotential::GetVirial(PyObject *a)
{
  USETIMER("ParallelPotential::GetVirial");
  DEBUGPRINT;
  SymTensor stress = potential->GetVirial(a);
  vector<double> s1(6);
  for (int i = 0; i < 6; i++)
    s1[i] = stress[i];
  vector<double> s2;
  mpi->Add(s1, s2);
  ASSERT(s2.size() == 6);
  for (int i = 0; i < 6; i++)
    stress[i] = s2[i];
  DEBUGPRINT;
  return stress;
}

void ParallelPotential::GetAtomicVolumes(vector<double> &volumes)
{
  potential->GetAtomicVolumes(volumes);
}


// void ParallelPotential::CheckNeighborLists()
// {
//   potential->CheckNeighborLists();
// }

PyObject *ParallelPotential::GetNeighborList() const
{
  return potential->GetNeighborList();
}

bool ParallelPotential::CheckAndUpdateNbList(PyObject *pyatoms)
{
  return potential->CheckAndUpdateNbList(pyatoms);
}

double ParallelPotential::GetCutoffRadius() const
{
  return potential->GetCutoffRadius();
}

double ParallelPotential::GetLatticeConstant() const
{
  return potential->GetLatticeConstant();
}

long ParallelPotential::PrintMemory() const
{
  return potential->PrintMemory();
}

void ParallelPotential::PyUpdateGhosts(PyObject *a)
{
  // Only for calling from Python in a few special cases
  par_atoms->Begin(a);
  par_atoms->UpdateGhostData();
  par_atoms->End();
}
