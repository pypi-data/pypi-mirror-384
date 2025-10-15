// EMT.cpp  --  Implements the EMT potential for multiple elements.

// Copyright (C) 2008-2011 Jakob Schiotz and Center for Individual
// Nanoparticle Functionality, Department of Physics, Technical
// University of Denmark.  Email: schiotz@fysik.dtu.dk
//
// This file is part of Asap version 3.
// Asap is released under the GNU Lesser Public License (LGPL) version 3.
// However, the parts of Asap distributed within the OpenKIM project
// (including this file) are also released under the Common Development
// and Distribution License (CDDL) version 1.0.
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

// Note: The macro ASAP_FOR_KIM is undefined when this file is
// compiled as part of Asap, but is defined when it is part of the
// OpenKIM model driver.

#include "EMT.h"
#include "Asap.h"
#include "EMTParameterProvider.h"
#include "Atoms.h"
#include "Vec.h"
#include "NeighborLocator.h"
#ifndef ASAP_FOR_KIM
#include "NeighborList.h"  // Not present in OpenKIM
#endif
#include "Exception.h"
#include "Timing.h"
#include "mass.h"
#include "Debug.h"
#include <math.h>
#include <vector>
#include <set>
#include <cstdio>
#include <iostream>
#include <algorithm>
#ifdef ASAP_MKL
#include "mkl.h"
#endif //ASAP_MKL
using std::vector;
using std::set;
using std::cerr;
using std::endl;
using std::flush;
using std::sort;

#undef INTERLEAVETHREADS


#if 1
#define VERB(x) if (verbose == 1) cerr << x
#else
#define VERB(x)
#endif

using namespace std;

// Standard mapping of the six independent parts of the stress tensor to
// vector notation
const static int stresscomp[3][3] = {{0, 5, 4}, {5, 1, 3}, {4, 3, 2}};

EMT::EMT(PyObject *self, PyObject *prov, int verbose) : Potential(self, verbose)
{
  CONSTRUCTOR;
  // Extract the parameter provider from the Python object, and store
  // the Python object.
  if (prov != NULL)
    {
      provider = ((PyAsap_EMTParamProvObject *) prov)->cobj;
      provider_obj = prov;
      Py_INCREF(provider_obj);
    }
  else
    {
      provider_obj = NULL;
      provider = NULL;
    }
  DEBUGPRINT;
  nblist = NULL;
  nblist_obj = NULL;
  driftfactor = 0.05;  // Drift factor for the neighbor list.
  initialized = false;
  always_fullnblist = false;
  atoms = NULL;
  ghostatoms = false;
  nAtoms = 0;
  nSize = 0;
#ifdef ASAP_FOR_KIM
  // Compiling EMT as an OpenKIM model
  // OpenKIM assumes that the potential energy is zero at infinite separation.
  // subtractE0 = false;
  subtractE0 = false;
#else
  // Asap defaults to using the fcc crystal as zero for the potential energy.
  subtractE0 = true;
#endif
  counters.ids = counters.nblist = counters.sigma1 = counters.sigma2 =
    counters.energies = counters.forces = counters.virials =
    counters.beforeforces = 0;
  recalc.ids = recalc.nblist = recalc.sigma1 = recalc.sigma2 =
    recalc.energies = recalc.forces = recalc.virials =
    recalc.beforeforces = false;
  skip_begin = false;
  DEBUGPRINT;
}

/// If an EMTParameterProvider was given when constructing the EMT
/// object, it will NOT be deleted, but any default parameter provider
/// and the automatically generated neigbor list will be deleted.
/// XXXX: Handle this with Python refcounting.
EMT::~EMT()
{
  DESTRUCTOR;
  Py_XDECREF(provider_obj);
  Py_XDECREF(nblist_obj);
  if (atoms != NULL)
    AsapAtoms_DECREF(atoms);
}

string EMT::GetRepresentation() const
{
  char buffer[50];
  snprintf(buffer, 50, "0x%p", this);
  return "<asap." + GetName() + "(" + provider->GetName() +
    ") potential object at " + buffer + ">";
}

long EMT::PrintMemory() const
{
  long atomsmem = 0;
  if (atoms != NULL)
    atomsmem = atoms->PrintMemory();
  long mem = 0;  // Count the big stuff.
  for (vector<vector<double> >::const_iterator i = sigma1.begin();
       i != sigma1.end(); i++)
    mem += i->size() * sizeof(int);
  for (vector<vector<double> >::const_iterator i = sigma2.begin();
       i != sigma2.end(); i++)
    mem += i->size() * sizeof(int);
  mem += Ec.size() * sizeof(double);
  mem += Eas.size() * sizeof(double);
  mem += Epot.size() * sizeof(double);
  mem += radius.size() * sizeof(double);
  mem += dEds.size() * sizeof(double);
  mem += force.size() * sizeof(Vec);
  mem += virials.size() * sizeof(SymTensor);
  mem += tmp_double.size() * sizeof(double);
  mem += id.size() * sizeof(int);
  mem = (mem + 512*1024) / (1024*1024);
  char buffer[500];
  snprintf(buffer, 500,
	   "*MEM* EMT %ld MB.  [ sizeof(int)=%ld  sizeof(double)=%ld ]",
	   mem, (long) sizeof(int), (long) sizeof(double));
  cerr << buffer << endl;
  if (nblist != NULL)
    mem += nblist->PrintMemory();
  return mem + atomsmem;
}

void EMT::SetAtoms(PyObject *pyatoms, Atoms* accessobj /* = NULL */)
{
  DEBUGPRINT;
  VERB("SetAtoms ");
  if (atoms != NULL)
    {
      // SetAtoms should only do anything the first time it is called.
      // Subsequent calls should just check for accessobj being NULL.
      if (accessobj != NULL && accessobj != atoms)
	throw AsapError("EMT::SetAtoms called multiple times with accessobj != NULL");
      // If SetAtoms is called multiple times, it should only check that no new element
      // is introduced.
      set<int> elements_set;
      atoms->Begin(pyatoms);
      atoms->GetListOfElements(elements_set);
      atoms->End();
      set<int> parameters_set;
      for (int i = 0; i < parameters.size(); i++)
      {
	parameters_set.insert(parameters[i]->Z);
      }
      for (set<int>::iterator i = elements_set.begin(); i != elements_set.end(); i++)
	if (parameters_set.find(*i) == parameters_set.end())
	  throw AsapError("You cannot introduce a new element after initializing EMT calculator: Z=") << *i;
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
  atoms->Begin(pyatoms);
  nAtoms = atoms->GetNumberOfAtoms();
  nSize = nAtoms;
    
  InitParameters();
  initialized = true;
  if (nelements == 1)
    {
      singleelement = parameters[0];
    }
  else
    {
      singleelement = 0;
    }
  atoms->End();
  DEBUGPRINT;
}

void EMT::Allocate()
{
  RETURNIFASAPERROR;
  USETIMER("EMT::Allocate");
  DEBUGPRINT;
  VERB(" Allocate[" << nAtoms << "," << nSize << "]" << flush);
  // WARNING: Resizing the vector may allocate way too much memory.  It
  // appears that calling reserve solves this problem.  For efficiency,
  // reserve is called with 5% extra space.  This is only necessary if the
  // atoms have ghosts, otherwise no reallocation will happen.

  // First, check if reallocation is necessary.
  if (nSize != force.size() || nAtoms != Eas.size())
    {
      DEBUGPRINT;
      /* Resize/intialize the internal variables. */
      sigma1.resize(nelements);
      sigma2.resize(nelements);
      // Do the reserve trick if the atoms have ghosts.
      if (ghostatoms)
        {
          if (force.capacity() < nSize)
            {
              nSizeRes = nSize + nSize/20;
              for (int i = 0; i < nelements; i++) {
                sigma1[i].reserve(nSizeRes);
                sigma2[i].reserve(nSizeRes);
              }
              id.reserve(nSizeRes);
              force.reserve(nSizeRes);
              dEds.reserve(nSizeRes);
            }
          if (Eas.capacity() < nAtoms)
            {
              nAtomsRes = nAtoms + nAtoms/20;
              Eas.reserve(nAtomsRes);
	      Epot.reserve(nAtomsRes);
	      Ec.reserve(nAtomsRes);
	      radius.reserve(nAtomsRes);
            }
        }
        
      for (int i = 0; i < nelements; i++) {
        sigma1[i].resize(nAtoms);
        sigma2[i].resize(nAtoms);
      }
      DEBUGPRINT;
      Ec.resize(nAtoms);
      Eas.resize(nAtoms);
      Epot.resize(nAtoms);
      radius.resize(nAtoms);
      dEds.resize(nSize);
      id.resize(nSize);
      force.resize(nSize);
      tmp_double.resize(nSize);
      ex2.resize(nAtoms);
      if (virials.size())
        AllocateStress();
      // The IDs are set to zero, then they do not have to be calculated if
      // there is only one element.
      if (nelements == 1)
        for (int i = 0; i < nSize; i++)
          id[i] = 0;
    }
  DEBUGPRINT;
}

// Stresses are reallocated if they exist when Allocate is called, or if
// they do not exist, and GetStress is called.
void EMT::AllocateStress()
{
  DEBUGPRINT;
  if (ghostatoms && (virials.capacity() < nSize))
    virials.reserve(nSizeRes);
  VERB(" AllocStr[" << nAtoms << "," << nSize << "]"<< flush);
  virials.resize(nSize);
  DEBUGPRINT;
}
     
void EMT::InitParameters()
{
  DEBUGPRINT;
  // Extract the elements from the list of atoms, and set up an array
  // of EMT parameters.
  set<int> elements_set;
  vector<int> elements;

  // Extract the elements from the list of atoms.
  // elements.clear();
  atoms->GetListOfElements(elements_set);
  for (set<int>::iterator i = elements_set.begin(); i != elements_set.end();
       ++i)
    elements.push_back(*i);
  nelements = elements.size();
  ASSERT(nelements == elements_set.size());
  sort(elements.begin(), elements.end());
	
  // Get the EMT parameters
  parameters.clear();
  for (vector<int>::iterator i = elements.begin(); i != elements.end(); ++i)
    parameters.push_back(provider->GetParameters(*i));

  //ASSERT(nelements == provider->GetNumberOfElements());
    
  // Calculate the quantities that can only be calculated, once the
  // elements in the simulations are known.
  provider->CalcGammaEtc();
  rFermi = provider->GetCutoffDistance();
  //rNbCut = 1.04500185048 * rFermi;
  rNbCut = provider->GetListCutoffDistance();
  cutoffslope = provider->GetCutoffSlope();
  chi = provider->GetChi();
  if (verbose)
    cerr << "EMT::InitParameters:  rFermi = " << rFermi << "  rNbCut = "
         << rNbCut << "  cutoffslope = " << cutoffslope << endl;
  DEBUGPRINT;
}

bool EMT::CalcReq_Forces(PyObject *pyatoms)
{
  atoms->Begin(pyatoms);
  bool required =  (counters.forces != atoms->GetPositionsCounter());
  atoms->End();
  return required;
}

const vector<Vec> &EMT::GetForces(PyObject *pyatoms)
{
  USETIMER("EMT::GetForces")
  DEBUGPRINT;
  VERB(" Force[");
  ASSERT(atoms != NULL);
  atoms->Begin(pyatoms);
  recalc.nblist = CheckNeighborList();
  recalc.forces = (counters.forces != atoms->GetPositionsCounter());
  if (recalc.forces)
    {
      recalc.ids = (counters.ids != atoms->GetPositionsCounter());
      recalc.sigma1 = (counters.sigma1 != atoms->GetPositionsCounter());
      recalc.beforeforces = (counters.beforeforces !=
			     atoms->GetPositionsCounter());
      DEBUGPRINT;
      CalculateForces();
      counters.beforeforces = atoms->GetPositionsCounter(); 
      counters.forces = atoms->GetPositionsCounter();
      VERB("]" << flush);
    }
  else
    {
      VERB("-]");
      ASSERT(recalc.nblist == false);
    }
  DEBUGPRINT;
  atoms->End();
  MEMORY;
  DEBUGPRINT;
  return force;
}

void EMT::CalculateForces()
{
  CHECKNOASAPERROR;
#ifdef _OPENMP
#pragma omp parallel
#endif // _OPENMP
  {
    if (recalc.nblist)
      UpdateNeighborList();
    CalculateIDs();
    CalculateSigmas(false);              /* Skip sigma2 */
    CalculateEnergiesAfterSigmas(false); /* Skip actual energy calc. */
    if (nelements > 1)
      CalculateForcesAfterEnergies();
    else
      CalculateForcesAfterEnergiesSingle();
  }
  PROPAGATEASAPERROR;
}

bool EMT::CalcReq_Virials(PyObject *pyatoms)
{
  atoms->Begin(pyatoms);
  bool required = (counters.virials != atoms->GetPositionsCounter());
  atoms->End();
  return required;
}

bool EMT::CalcReq_Virial(PyObject *pyatoms)
{
  return CalcReq_Virials(pyatoms);
}

const vector<SymTensor> &EMT::GetVirials(PyObject *pyatoms)
{
  USETIMER("EMT::GetVirials")
  DEBUGPRINT;
  VERB(" Virials[");
  ASSERT(atoms != NULL);
  atoms->Begin(pyatoms);

  recalc.nblist = CheckNeighborList();
  recalc.virials = (counters.virials != atoms->GetPositionsCounter());
  if (recalc.virials)
    {
      recalc.ids = (counters.ids != atoms->GetPositionsCounter());
      recalc.sigma1 = (counters.sigma1 != atoms->GetPositionsCounter());
      recalc.beforeforces = (counters.beforeforces !=
			     atoms->GetPositionsCounter());
      recalc.forces = (counters.forces != atoms->GetPositionsCounter());
      DEBUGPRINT;
      if (this->virials.size() == 0)
        AllocateStress();
      CalculateVirials();
    }
  else
    {
      ASSERT(recalc.nblist == false);
    }
  VERB("]" << flush);
  DEBUGPRINT;
  counters.virials = atoms->GetPositionsCounter();
  counters.beforeforces = atoms->GetPositionsCounter(); 
  counters.forces = atoms->GetPositionsCounter();
  atoms->End();
  return virials;
}

void EMT::CalculateVirials()
{
  if (recalc.virials)
    {
      CHECKNOASAPERROR;
#ifdef _OPENMP
#pragma omp parallel
#endif // _OPENMP
      {
        if (recalc.nblist)
          UpdateNeighborList();
        CalculateIDs();
        CalculateSigmas(false);                  // Skip sigma2
        CalculateEnergiesAfterSigmas(false); // Skip actual energy calc.
        if (nelements > 1)
          CalculateForcesAfterEnergies();
        else
          CalculateForcesAfterEnergiesSingle();
      }
      PROPAGATEASAPERROR;
    }
}

void EMT::GetAtomicVolumes(vector<double> &v)
{
  v.resize(nAtoms);
  const double fourpithird = 4.1887902048;  // 4 * PI / 3
  for (int i = 0; i < nAtoms; i++)
    {
      double s0 = parameters[id[i]]->seq;
      v[i] = fourpithird * s0 * s0 * s0;
    }
}

bool EMT::CalcReq_Energy(PyObject *pyatoms)
{
  atoms->Begin(pyatoms);
  bool required = (counters.energies != atoms->GetPositionsCounter());
  atoms->End();
  return required;
}

const vector<double> &EMT::GetPotentialEnergies(PyObject *pyatoms)
{
  USETIMER("EMT::GetPotentialEnergies");
  DEBUGPRINT;
  VERB(" Energies[");
  ASSERT(atoms != NULL);
  // Atoms may already be open if called from MonteCarloEMT object.
  if (!skip_begin)
    atoms->Begin(pyatoms);
  else
    skip_begin = false;
  recalc.nblist = CheckNeighborList();
  recalc.energies = (counters.energies != atoms->GetPositionsCounter());
  if (recalc.energies)
    {
      recalc.ids = (counters.ids != atoms->GetPositionsCounter());
      recalc.sigma1 = (counters.sigma1 != atoms->GetPositionsCounter());
      recalc.sigma2 = (counters.sigma2 != atoms->GetPositionsCounter());
      recalc.beforeforces = (counters.beforeforces !=
			     atoms->GetPositionsCounter());
      DEBUGPRINT;
      CalculateEnergies();
      counters.energies = atoms->GetPositionsCounter();
      counters.beforeforces = atoms->GetPositionsCounter(); 
    }
  else
    {
      ASSERT(counters.beforeforces == atoms->GetPositionsCounter());
      ASSERT(recalc.nblist == false);
      
      if(subtractE0)
	for (int i = 0; i < nAtoms; i++)
	  Epot[i] = Ec[i] + Eas[i] - parameters[id[i]]->e0;
      else
	for (int i = 0; i < nAtoms; i++)
	  Epot[i] = Ec[i] + Eas[i];

      VERB("-");
    }
  ASSERT(Epot.size() == nAtoms);
  DEBUGPRINT;
  VERB("]" << flush);
  atoms->End();
  return Epot;
}

void EMT::CalculateEnergies()
{
  CHECKNOASAPERROR;
#ifdef _OPENMP
#pragma omp parallel
#endif // _OPENMP
  {
    if (recalc.nblist)
      UpdateNeighborList();
    CalculateIDs();
    CalculateSigmas(true);
    CalculateEnergiesAfterSigmas(true);
  }
  PROPAGATEASAPERROR;
}

double EMT::GetPotentialEnergy(PyObject *pyatoms)
{
  USETIMER("EMT::GetPotentialEnergy");
  VERB(" Energy[");
  DEBUGPRINT;
  double etot = 0.0;
    
  const vector<double> &e = GetPotentialEnergies(pyatoms);
  for (int i = 0; i < nAtoms; i++)
    etot += e[i];
  DEBUGPRINT;
  VERB("]" << flush);
  return etot;
}


bool EMT::CheckAndUpdateNbList(PyObject *pyatoms)
{
  atoms->Begin(pyatoms);
  recalc.nblist = CheckNeighborList();
  if (recalc.nblist)
    UpdateNeighborList();
  atoms->End();
  return recalc.nblist;
}


bool EMT::CheckNeighborList()
{
  RETURNIFASAPERROR2(false);
  USETIMER("EMT::CheckNeighborList");
  DEBUGPRINT;
  ASSERT(atoms != NULL);
  bool update = (nblist == NULL) || nblist->IsInvalid();  // Update if invalid
  if (!update && (counters.nblist != atoms->GetPositionsCounter()))
    {
      VERB("n");
      update = nblist->CheckNeighborList();
    }
  // May communicate
  update = atoms->UpdateBeforeCalculation(update,
					  rNbCut * (1 + driftfactor));
  counters.nblist = atoms->GetPositionsCounter();
  return update;
}

void EMT::UpdateNeighborList()
{
  RETURNIFASAPERROR;
  USETIMER("EMT::UpdateNeighborList");
  DEBUGPRINT;
  VERB("N");
  DEBUGPRINT;
  RETURNIFASAPERROR;
  if (nblist)
    {
      DEBUGPRINT;
      nblist->UpdateNeighborList();
      RETURNIFASAPERROR;
#ifdef _OPENMP
#pragma omp single
#endif // _OPENMP
      {
        if ((nAtoms != atoms->GetNumberOfAtoms())
            || (nSize - nAtoms != atoms->GetNumberOfGhostAtoms()))
          {
            nAtoms = atoms->GetNumberOfAtoms();
            nSize = nAtoms + atoms->GetNumberOfGhostAtoms();
            ghostatoms = atoms->HasGhostAtoms();
            Allocate();
          }
      }
    }
  else
    {
#ifdef _OPENMP
#pragma omp barrier
#endif // _OPENMP
      // First call, create the neighbor list.
      DEBUGPRINT;
      CreateNeighborList();
      RETURNIFASAPERROR;
#ifdef _OPENMP
#pragma omp single
#endif // _OPENMP
      {
        nAtoms = atoms->GetNumberOfAtoms();
        nSize = nAtoms + atoms->GetNumberOfGhostAtoms();
        ghostatoms = atoms->HasGhostAtoms();
        Allocate();
      }
    }
  DEBUGPRINT;
}

// Will be replaced in MonteCarloEMT
void EMT::CreateNeighborList()
{
#ifdef ASAP_FOR_KIM
  // This function is never called when used as an OpenKIM potential
  // In that case, the NeighborList object does not exist, and this
  // function does not compile.
  throw AsapError("Internal inconsistency: EMT::CreateNeighborList called in KIM calculator.");
#else
  RETURNIFASAPERROR;
  MEMORY;
  USETIMER("EMT::CreateNeighborList");
  if (!initialized)
    THROW_RETURN( AsapError("EMT object has not been initialized!") );
#ifdef _OPENMP
#pragma omp single
#endif // _OPENMP
  {
      PyAsap_NeighborLocatorObject *nbl;
      nbl = PyAsap_NewNeighborList(atoms, rNbCut, driftfactor);
      nblist = nbl->cobj;
      nblist->verbose = verbose;
      nblist_obj = (PyObject *) nbl;
      MEMORY;
  }
  nblist->UpdateNeighborList();
  MEMORY;
#endif // not ASAP_FOR_KIM
}


/// IDs are a recoding of the atomic numbers used as indices into
/// various arrays.  Atomic numbers are not practical for this as they
/// are not contiguous.
void EMT::CalculateIDs()
{
  RETURNIFASAPERROR;
  USETIMER("EMT::CalculateIDs");
  DEBUGPRINT;
  if (!recalc.ids || nelements == 1)
    return;
  VERB("i");
  DEBUGPRINT;
  // If there is only one element, all IDs are 0 and do not have to be
  // calculated.  Otherwise the ID is the offset into the list of elements.
  const asap_z_int *RESTRICT z = atoms->GetAtomicNumbers();

  int nSize = this->nSize;    // These two lines help optimization.
  int *RESTRICT id = &(this->id)[0];
  for (int i = 0; i < nelements; i++)
    {
      int zcand = parameters[i]->Z;
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
      for (int j = 0; j < nSize; j++)
	if (z[j] == zcand)
	    id[j] = i;
    }
#ifdef _OPENMP
#pragma omp master
#endif // _OPENMP
  counters.ids = atoms->GetPositionsCounter();
  DEBUGPRINT;
}
    
void EMT::CalculateSigmas(bool calculatesigma2)
{
  RETURNIFASAPERROR;
  USETIMER("EMT::CalculateSigmas");
  DEBUGPRINT;
  if (!(recalc.sigma1 || (calculatesigma2 && recalc.sigma2)))
    return;
#ifdef _OPENMP
#pragma omp master
#endif // _OPENMP
  {
      if (calculatesigma2)
        {
          VERB("2");
        }
      else
        {
          VERB("1");
        }
  }

  DEBUGPRINT;
  int maxnblen = nblist->MaxNeighborListLength();
  if (maxnblen > BUFLEN)
    {
      const Vec *cell = atoms->GetCell();
      THROW_RETURN( AsapError("Neighborlist overrun (did you squeeze your atoms?).\n")
		    << "  Longest neighbor list is " << maxnblen << ".\n"
		    << "  Cell is " << cell[0] << ", " << cell[1] << ", " << cell[2] );
    }
#ifdef ASAP_FOR_KIM
  const int *contributes = atoms->GetParticleContributes();
  ASSERT(nAtoms == nSize);  // In OpenKIM, non-contributing atoms are not always at the end.
#endif
  // Buffer data:
  TinyMatrix<int> nbatch(nelements,nelements);
  TinyMatrix<int[BUFLEN]> self(nelements,nelements);
  TinyMatrix<int[BUFLEN]> other(nelements,nelements);
  TinyMatrix<Vec[BUFLEN]> rnb(nelements,nelements);
  TinyMatrix<double[BUFLEN]> sqdist(nelements,nelements);
  vector<int> other_buf(BUFLEN);
  vector<Vec> rnb_buf(BUFLEN);
  vector<double> sqdist_buf(BUFLEN);

  int nSize = this->nSize;  // Helps optimization
  DEBUGPRINT;
  /* Set sigmas to zero */
  for (int i = 0; i < nelements; i++)
    {
      double *RESTRICT s1 = &sigma1[i][0];
      double *RESTRICT s2 = &sigma2[i][0];
#ifdef _OPENMP
#pragma omp for nowait
#endif // _OPENMP
      for (int j = 0; j < nSize; j++)
        {
          s1[j] = 0.0;
          s2[j] = 0.0;
        }
    }
#ifdef _OPENMP
#pragma omp barrier
#endif // _OPENMP

  /* No atoms in batch pools */
  for (int i = 0; i < nelements; i++)
    for (int j = 0; j < nelements; j++)
      nbatch[i][j] = 0;

  // Loop over atoms
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
  for (int atom = 0; atom < nAtoms; atom++)
    {
#ifdef ASAP_FOR_KIM
      if (!contributes[atom]) continue;   // Skip non-contributing atoms.
#endif     
      int zself = id[atom];
      // Get neighbors and loop over them.  Simplest if only one element
      if (nelements == 1) 
        {
          int nbat = nbatch[0][0];  // only element
          int size = BUFLEN-nbat;
          int n;
          if (always_fullnblist)
            n = nblist->GetFullNeighbors(atom, other[0][0]+nbat,
                                         rnb[0][0]+nbat, sqdist[0][0]+nbat,
                                         size);
          else
            n = nblist->GetNeighbors(atom, other[0][0]+nbat,
                                     rnb[0][0]+nbat, sqdist[0][0]+nbat,
                                     size);
          ASSERT(size >= 0);    // REMOVE LATER !!!
          for (int i = nbat; i < nbat+n; i++)
            self[0][0][i] = atom;
          nbatch[0][0] += n;
        } 
      else 
        {
          int size = BUFLEN;
          int n;
          if (always_fullnblist)
            n = nblist->GetFullNeighbors(atom, &other_buf[0], &rnb_buf[0],
                                         &sqdist_buf[0], size);
          else
            n = nblist->GetNeighbors(atom, &other_buf[0], &rnb_buf[0],
                                     &sqdist_buf[0], size);
          ASSERT(size >= 0);     // REMOVE LATER !!!
	  int *RESTRICT id = &(this->id)[0];
          for (int i = 0; i < n; i++) 
            {
              int zother = id[other_buf[i]];
              int nbat = nbatch[zself][zother]++;  // Count this atom
              self[zself][zother][nbat] = atom;
              other[zself][zother][nbat] = other_buf[i];
              sqdist[zself][zother][nbat] = sqdist_buf[i];
            }
        }
      // Now process any full batch

      for (int zo = 0; zo < nelements; zo++)
        if (nbatch[zself][zo] >= BUFLEN - maxnblen) 
          {
            sigma_batch(self[zself][zo], other[zself][zo],
                        sqdist[zself][zo], zself, zo, nbatch[zself][zo],
                        calculatesigma2);
            nbatch[zself][zo] = 0;
          }
    }  // Loop over atoms
  /* Process the remaining incomplete batches */
  for (int zs = 0; zs < nelements; zs++)
    for (int zo = 0; zo < nelements; zo++)
      if (nbatch[zs][zo])
        sigma_batch(self[zs][zo], other[zs][zo],
                    sqdist[zs][zo], zs, zo, nbatch[zs][zo],
                    calculatesigma2);

#ifdef _OPENMP
#pragma omp single
#endif // _OPENMP
  {
    sigma2isvalid = calculatesigma2;  /* Remember if it was calculated. */
    counters.sigma1 = atoms->GetPositionsCounter();
    if (calculatesigma2)
      counters.sigma2 = atoms->GetPositionsCounter();
  }

}

void EMT::sigma_batch(int *RESTRICT self, int *RESTRICT other,
                      double *RESTRICT sq_dist, int zs, int zo, int n,
                      bool calculatesigma2, bool partialupdate /* = false */)
{
  USETIMER("EMT::sigma_batch");
#ifdef ASAP_MKL
  double *temporary = (double *) mkl_malloc(10 * BUFLEN * sizeof(double), ASAP_MKL_ALIGN);
#else // ASAP_MKL
  double *temporary = new double[4*BUFLEN];
#endif //ASAP_MKL
  double *RESTRICT dsigma1s = &temporary[0];
  double *RESTRICT dsigma2s = dsigma1s + BUFLEN;
  double *RESTRICT dsigma1o = dsigma2s + BUFLEN;
  double *RESTRICT dsigma2o = dsigma1o + BUFLEN;
  //ASSERT(dsigma2o - temporary == (4 - 1) * BUFLEN);
#ifdef ASAP_MKL
  double *RESTRICT tmp_a = dsigma2o + BUFLEN;
  double *RESTRICT tmp_b = tmp_a + BUFLEN;
  double *RESTRICT tmp_c = tmp_b + BUFLEN;
  double *RESTRICT tmp_d = tmp_c + BUFLEN;
  double *RESTRICT tmp_e = tmp_d + BUFLEN;
  double *RESTRICT tmp_f = tmp_e + BUFLEN;
  //ASSERT(tmp_f - temporary == (10 - 1) * BUFLEN);
#endif //ASAP_MKL  
  double cutslopecutdist;
  double other_eta2betaseq, self_eta2betaseq;
  double other_kappaoverbeta, self_kappaoverbeta;
  double other_kappaseq, self_kappaseq;
  double *s1s, *s1o, *s2s, *s2o;
  const emt_parameters *emtself, *emtother;

  ASSERT(n <= BUFLEN);
  
  /* Get EMT parameters   REWRITE !!! XXXX */  
  emtself = parameters[zs];
  emtother = parameters[zo];
  double cutoffslope = this->cutoffslope;
  cutslopecutdist = cutoffslope * rFermi;
  other_eta2betaseq = emtother->eta2 * Beta * emtother->seq;
  self_eta2betaseq = emtself->eta2 * Beta * emtself->seq;
  other_kappaoverbeta = emtother->kappa / Beta;
  self_kappaoverbeta = emtself->kappa / Beta;
  other_kappaseq = emtother->kappa * emtother->seq;
  self_kappaseq = emtself->kappa * emtself->seq;
  double other_eta2 = emtother->eta2;
  double self_eta2 = emtself->eta2;

  ASSERT(n <= BUFLEN);
  // We have four cases to handled, controlled by two booleans.
  // 1) Whether sigma2 needs to be calculated,  2) Whether we need a
  // different calculation for the two atoms interacting.  The latter is
  // the case if the atomic numbers are different, unless operating in
  // full neighborlist mode or doing a partial update for MonteCarloEMT,
  // in these cases calculations are not reused.
  bool calculateother = (zs != zo) && !always_fullnblist && !partialupdate;
  if (!calculateother && !calculatesigma2)
    {
#ifdef ASAP_MKL
      // dist[] = tmp_a[] = sqrt(sq_dist[])
      vdSqrt(n, sq_dist, tmp_a);
      for (int i = 0; i < n; i++)
	{
	  tmp_b[i] = cutoffslope * tmp_a[i] - cutslopecutdist;
	  tmp_c[i] = -other_eta2 * tmp_a[i] + other_eta2betaseq;
	}
      // tmp_a[] = exp(tmp_b[]) = exp(cutoffslope * dist[] - cutslopecutdist)
      vdExp(n, tmp_b, tmp_a);
      // tmp_b[] = exp(tmp_c[]) = exp(-other_eta2 * dist[] + other_eta2betaseq)
      vdExp(n, tmp_c, tmp_b);
      for (int i = 0; i < n; i++)
	{
	  double wght = 1.0 / (1.0 + tmp_a[i]);
	  dsigma1s[i] = wght * tmp_b[i];
	}
#else  // ASAP_MKL
      for (int i = 0; i < n; i++)
	{
	  /* dist = sqrt(sq_dist),  distances between atoms */
	  double dist = sqrt(sq_dist[i]);
	  /* Calculate weight factor (cutoff function) */
	  double wght = 1.0 / (1.0 + exp(cutoffslope * dist
					 - cutslopecutdist));
	  /* Contribution to sigma1 */
	  dsigma1s[i] = wght * exp(-other_eta2 * dist + other_eta2betaseq);
	}
#endif // ASAP_MKL
    }
  else if (calculateother && !calculatesigma2)
    {
#ifdef ASAP_MKL
      // dist[] = tmp_a[] = sqrt(sq_dist[])
      vdSqrt(n, sq_dist, tmp_a);
      for (int i = 0; i < n; i++)
	{
	  tmp_b[i] = cutoffslope * tmp_a[i] - cutslopecutdist;
	  tmp_c[i] = -other_eta2 * tmp_a[i] + other_eta2betaseq;
	  tmp_d[i] = -self_eta2 * tmp_a[i] + self_eta2betaseq;
	}
      // tmp_a[] = exp(tmp_b[]) = exp(cutoffslope * dist[] - cutslopecutdist)
      vdExp(n, tmp_b, tmp_a);
      // tmp_b[] = exp(tmp_c[]) = exp(-other_eta2 * dist[] + other_eta2betaseq)
      vdExp(n, tmp_c, tmp_b);
      // tmp_c[] = exp(tmp_d[]) = exp(-self_eta2 * dist[] + self_eta2betaseq)
      vdExp(n, tmp_d, tmp_c);
      for (int i = 0; i < n; i++)
	{
	  double wght = 1.0 / (1.0 + tmp_a[i]);
	  dsigma1s[i] = wght * tmp_b[i];
	  dsigma1o[i] = wght * tmp_c[i];
	}
#else // ASAP_MKL
      for (int i = 0; i < n; i++)
	{
	  /* dist = sqrt(sq_dist),  distances between atoms */
	  double dist = sqrt(sq_dist[i]);
	  /* Calculate weight factor (cutoff function) */
	  double wght = 1.0 / (1.0 + exp(cutoffslope * dist
					 - cutslopecutdist));
	  /* Contributions to sigma1 */
	  dsigma1s[i] = wght * exp(-other_eta2 * dist + other_eta2betaseq);
	  dsigma1o[i] = wght * exp(-self_eta2 * dist + self_eta2betaseq);
	}
#endif //ASAP_MKL
    }
  else if (!calculateother && calculatesigma2)
    {
#ifdef ASAP_MKL
      // dist[] = tmp_a[] = sqrt(sq_dist[])
      vdSqrt(n, sq_dist, tmp_a);
      for (int i = 0; i < n; i++)
	{
	  tmp_b[i] = cutoffslope * tmp_a[i] - cutslopecutdist;
	  tmp_c[i] = -other_eta2 * tmp_a[i] + other_eta2betaseq;
	  tmp_d[i] = -other_kappaoverbeta * tmp_a[i] + other_kappaseq;
	}
      // tmp_a[] = exp(tmp_b[]) = exp(cutoffslope * dist[] - cutslopecutdist)
      vdExp(n, tmp_b, tmp_a);
      // tmp_b[] = exp(tmp_c[]) = exp(-other_eta2 * dist[] + other_eta2betaseq)
      vdExp(n, tmp_c, tmp_b);
      // tmp_c[] = exp(tmp_d[]) = exp(-other_kappaoverbeta * dist[] + other_kappaseq)
      vdExp(n, tmp_d, tmp_c);
      for (int i = 0; i < n; i++)
	{
	  double wght = 1.0 / (1.0 + tmp_a[i]);
	  dsigma1s[i] = wght * tmp_b[i];
	  dsigma2s[i] = wght * tmp_c[i];
	}
#else // ASAP_MKL
      for (int i = 0; i < n; i++)
	{
	  /* dist = sqrt(sq_dist),  distances between atoms */
	  double dist = sqrt(sq_dist[i]);

	  /* Calculate weight factor (cutoff function) */
	  double wght = 1.0 / (1.0 + exp(cutoffslope * dist
					 - cutslopecutdist));
	  /* Contribution to sigma1 */
	  dsigma1s[i] = wght * exp(-other_eta2 * dist + other_eta2betaseq);
	  dsigma2s[i] = wght * exp(-other_kappaoverbeta * dist
					+ other_kappaseq);

	}
#endif //ASAP_MKL
   }
  else // calculateother && calculatesigma2
    {
#ifdef ASAP_MKL
      // dist[] = tmp_a[] = sqrt(sq_dist[])
      vdSqrt(n, sq_dist, tmp_a);
      for (int i = 0; i < n; i++)
	{
	  tmp_b[i] = cutoffslope * tmp_a[i] - cutslopecutdist;
	  tmp_c[i] = -other_eta2 * tmp_a[i] + other_eta2betaseq;
	  tmp_d[i] = -self_eta2 * tmp_a[i] + self_eta2betaseq;
	  tmp_e[i] = -other_kappaoverbeta * tmp_a[i] + other_kappaseq;
	  tmp_f[i] = -self_kappaoverbeta * tmp_a[i] + self_kappaseq;
	}
      // tmp_a[] = exp(tmp_b[]) = exp(cutoffslope * dist[] - cutslopecutdist)
      vdExp(n, tmp_b, tmp_a);
      // tmp_b[] = exp(tmp_c[]) = exp(-other_eta2 * dist[] + other_eta2betaseq)
      vdExp(n, tmp_c, tmp_b);
      // tmp_c[] = exp(tmp_d[]) = exp(-self_eta2 * dist[] + self_eta2betaseq)
      vdExp(n, tmp_d, tmp_c);
      // tmp_d[] = exp(tmp_e[]) = exp(-other_kappaoverbeta * dist[] + other_kappaseq)
      vdExp(n, tmp_e, tmp_d);
      // tmp_e[] = exp(tmp_f[]) = exp(-self_kappaoverbeta * dist[] + self_kappaseq)
      vdExp(n, tmp_f, tmp_e);
      for (int i = 0; i < n; i++)
	{
	  double wght = 1.0 / (1.0 + tmp_a[i]);
	  dsigma1s[i] = wght * tmp_b[i];
	  dsigma1o[i] = wght * tmp_c[i];
	  dsigma2s[i] = wght * tmp_d[i];
	  dsigma2o[i] = wght * tmp_e[i];
	}
#else // ASAP_MKL
      for (int i = 0; i < n; i++)
	{
	  /* dist = sqrt(sq_dist),  distances between atoms */
	  double dist = sqrt(sq_dist[i]);
	  /* Calculate weight factor (cutoff function) */
	  double wght = 1.0 / (1.0 + exp(cutoffslope * dist
					 - cutslopecutdist));
	  /* Contributions to sigma1 */
	  dsigma1s[i] = wght * exp(-other_eta2 * dist + other_eta2betaseq);
	  dsigma1o[i] = wght * exp(-self_eta2 * dist + self_eta2betaseq);
	  dsigma2s[i] = wght * exp(-other_kappaoverbeta * dist
				   + other_kappaseq);
	  dsigma2o[i] = wght * exp(-self_kappaoverbeta * dist + self_kappaseq);
	}
#endif // ASAP_MKL
    }

  // Distribute the results to the atoms.
  if (!partialupdate && !always_fullnblist)
    {
      // This is the normal branch, both atoms need to be updated.
      if (calculatesigma2) 
	{
	  /* Distribute contributions to sigma1 and sigma2 */
	  s1o = &sigma1[zo][0];
	  s1s = &sigma1[zs][0];
	  s2o = &sigma2[zo][0];
	  s2s = &sigma2[zs][0];
#ifdef _OPENMP
#pragma omp critical
#endif // _OPENMP
	  {
	    if (calculateother)
	      {
		for (int i = 0; i < n; i++)
		  {
		    int s = self[i];
		    int o = other[i];
		    s1o[s] += dsigma1s[i];
		    s2o[s] += dsigma2s[i];
		    if (o < nAtoms)        // Dont add to ghost atoms
		      {
			s1s[o] += dsigma1o[i];
			s2s[o] += dsigma2o[i];
		      }
		  }
	      }
	    else
	      {
		for (int i = 0; i < n; i++)
		  {
		    int s = self[i];
		    int o = other[i];
		    s1o[s] += dsigma1s[i];
		    s2o[s] += dsigma2s[i];
		    if (o < nAtoms)        // Dont add to ghost atoms
		      {
			s1s[o] += dsigma1s[i];
			s2s[o] += dsigma2s[i];
		      }
		  }
	      }
	    
	  }
	}
      else 
	{
	  /* Distribute contributions to sigma1. */
	  s1o = &sigma1[zo][0];
	  s1s = &sigma1[zs][0];
#ifdef _OPENMP
#pragma omp critical
#endif // _OPENMP
	  {
	    if (calculateother)
	      {
		for (int i = 0; i < n; i++)
		  {
		    int s = self[i];
		    int o = other[i];
		    s1o[s] += dsigma1s[i];
		    if (o < nAtoms)
		      s1s[o] += dsigma1o[i];
		  }
	      }
	    else
	      {
		for (int i = 0; i < n; i++)
		  {
		    int s = self[i];
		    int o = other[i];
		    s1o[s] += dsigma1s[i];
		    if (o < nAtoms)
		      s1s[o] += dsigma1s[i];
		  }
	      }
	  }
	}
    }
  else  // partialupdate OR always_fullnblist
    {
      // This branch may be taken by MonteCarloEMT during a partial update,
      // or by the normal EMT when not using Minimum Image Convention.  Since
      // full neighbor lists are used, only update the
      // 'self' atom, not the 'other' atom.
      // In OpenKIM, this branch is always taken.
      if (calculatesigma2)
        {
          /* Distribute contributions to sigma1 and sigma2 */
          s1o = &sigma1[zo][0];
          s2o = &sigma2[zo][0];
    #ifdef _OPENMP
    #pragma omp critical
    #endif // _OPENMP
          {
            for (int i = 0; i < n; i++)
              {
                int s = self[i];
                s1o[s] += dsigma1s[i];
                s2o[s] += dsigma2s[i];
              }
          }
        }
      else
        {
          /* Distribute contributions to sigma1 only */
          s1o = &sigma1[zo][0];
    #ifdef _OPENMP
    #pragma omp critical
    #endif // _OPENMP
          {
            for (int i = 0; i < n; i++)
              {
                int s = self[i];
                s1o[s] += dsigma1s[i];
              }
          }
        }
    }
#ifdef ASAP_MKL
  mkl_free(temporary);
#else
  delete[] temporary;
#endif
}


// Calculate the energies if calc_Epot is true, otherwise just calculate the
// derivatives needed for the forces. 
void EMT::CalculateEnergiesAfterSigmas(bool calc_Epot)
{
  RETURNIFASAPERROR;
  USETIMER("EMT::CalculateEnergiesAfterSigmas");
  DEBUGPRINT;

  //vector<double> sigma(nSize);
  double *RESTRICT sigma = &tmp_double[0];
  bool dosigmapart = (recalc.beforeforces || (calc_Epot && recalc.energies));
  bool doepotpart = (calc_Epot && recalc.energies);
  
  int zs, zo;
  double s;
  // Better performance if static ???
  ASSERT(nelements < NMAXELEMENTS);
  double inv12gamma1[NMAXELEMENTS];
  double neginvbetaeta2[NMAXELEMENTS];
  double neglambda[NMAXELEMENTS];
  double lambdaseq[NMAXELEMENTS];
  double negkappa[NMAXELEMENTS];
  double kappaseq[NMAXELEMENTS];
  double nege0lambdalambda[NMAXELEMENTS];
  double e0lambdalambdaseq[NMAXELEMENTS];
  double neg6v0kappa[NMAXELEMENTS];
  double e0lambda[NMAXELEMENTS];
  double eccnst[NMAXELEMENTS];
  double sixv0[NMAXELEMENTS];
  double neghalfv0overgamma2[NMAXELEMENTS];
  double seq[NMAXELEMENTS];
  int *id = &(this->id)[0];
  
  if (dosigmapart)
    {
#ifdef _OPENMP
#pragma omp master
#endif // _OPENMP
      {
        VERB("b");
        DEBUGPRINT;
      }
      /* Calculate total sigma1 */
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
      for (int i = 0; i < nAtoms; i++)
        {
          double s = 0.0;
          int zs = id[i];
          for (int zo = 0; zo < nelements; zo++)
            s += (*chi)[zs][zo] * sigma1[zo][i];
          if (s < 1.0e-40)
            s = 1.0e-40;
          sigma[i] = s;
        }
      ASSERT(nAtoms == radius.size() && nAtoms == Ec.size() &&
             nSize == dEds.size());
    }

  /* Calculate conbinations of EMT parameters */
  for (int i = 0; i < nelements; i++)
    {
     inv12gamma1[i] = 1.0 / (12.0 * parameters[i]->gamma1);
      neginvbetaeta2[i] = -1.0 / (Beta * parameters[i]->eta2);
      neglambda[i] = - parameters[i]->lambda;
      lambdaseq[i] = parameters[i]->lambda * parameters[i]->seq;
      negkappa[i] = - parameters[i]->kappa;
      kappaseq[i] = parameters[i]->kappa * parameters[i]->seq;
      nege0lambdalambda[i] = - parameters[i]->e0 * parameters[i]->lambda *
        parameters[i]->lambda;
      e0lambdalambdaseq[i] = parameters[i]->e0 * parameters[i]->lambda *
        parameters[i]->lambda * parameters[i]->seq;
      neg6v0kappa[i] = - 6.0 * parameters[i]->V0 * parameters[i]->kappa;
      e0lambda[i] = parameters[i]->e0 * parameters[i]->lambda;
      eccnst[i] = parameters[i]->e0 * (1.0 - parameters[i]->lambda *
                                       parameters[i]->seq);
      sixv0[i] = 6.0 * parameters[i]->V0;
      neghalfv0overgamma2[i] = -0.5 * parameters[i]->V0 /
        parameters[i]->gamma2;
      seq[i] = parameters[i]->seq;
    }

  int nAtoms = this->nAtoms;  // Helps optimization.
#define LOCALPTR(XX) double *RESTRICT XX = &(this->XX)[0]
  LOCALPTR(Ec);
  LOCALPTR(Eas);
  LOCALPTR(Epot);
  LOCALPTR(radius);
  LOCALPTR(dEds);
  LOCALPTR(ex2);
  
  if (dosigmapart)
  {
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
    for (int i = 0; i < nAtoms; i++)
    {
      asap_z_int z = id[i];  // Actually not Z (atomic no) but ID no.
      double r = seq[z] + neginvbetaeta2[z] * log(sigma[i] * inv12gamma1[z]);
      radius[i] = r;
      double ex1 = exp(neglambda[z] * r + lambdaseq[z]);
      double e2 = exp(negkappa[z] * r + kappaseq[z]);
      ex2[i] = e2;
      double tmp = (nege0lambdalambda[z] * r + e0lambdalambdaseq[z]) * ex1
           + neg6v0kappa[z] * e2;
      dEds[i] = tmp * neginvbetaeta2[z] / sigma[i];
      Ec[i] = (e0lambda[z] * r + eccnst[z]) * ex1;
    }
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
    for (int i = nAtoms; i < nSize; i++)
      dEds[i] = 0.0;
  }
  if (calc_Epot) 
    {
      DEBUGPRINT;
      if (doepotpart)
        {
#ifdef _OPENMP
#pragma omp master
#endif // _OPENMP
          {
            VERB("e");
            DEBUGPRINT;
          }
          /* We also need Eas, but only for the real atoms */
          ASSERT(sigma2isvalid);
          ASSERT(counters.sigma2 == atoms->GetPositionsCounter());
          /* Calculate total sigma2 */
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            {
              s = 0.0;
              zs = id[i];
              for (zo = 0; zo < nelements; zo++)
                s += (*chi)[zs][zo] * sigma2[zo][i];
              Eas[i] = sixv0[zs] * ex2[i] + neghalfv0overgamma2[zs] * s;
            }
        }
      /* Add the energies */
      DEBUGPRINT;
      if(subtractE0)
        {
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            Epot[i] = Ec[i] + Eas[i] - parameters[id[i]]->e0;
        }
      else
        {
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            Epot[i] = Ec[i] + Eas[i];
        }
    } // if (calc_Epot)
  
#ifdef ASAP_FOR_KIM
  // In OpenKIM, nAtoms == nSize and the non-contributing atoms had
  // their energies calculates.  Zap them.
  const int *contributes = atoms->GetParticleContributes();
  for (int i = 0; i < nAtoms; i++)
    if (!contributes[i])
      Epot[i] = Ec[i] = Eas[i] = dEds[i] = 0;
#endif // ASAP_FOR_KIM
    
  DEBUGPRINT;    
}

void EMT::CalculateForcesAfterEnergies()
{
  RETURNIFASAPERROR;
  if (!(recalc.forces || (virials.size() && recalc.virials)))
    return;
#ifdef _OPENMP
#pragma omp master
#endif // _OPENMP
  {
      VERB("f");
      if (virials.size())
        {
          VERB("s");
        }
  }
#ifdef _OPENMP
#pragma omp barrier
#endif // _OPENMP
  DEBUGPRINT;
  int maxnblen = nblist->MaxNeighborListLength();
  // Buffer data:
  TinyMatrix<int> nbatch(nelements,nelements);
  TinyMatrixOfVector<vector<int> > self(nelements,nelements, BUFLEN);
  TinyMatrixOfVector<vector<int> > other(nelements,nelements, BUFLEN);
  TinyMatrixOfVector<vector<Vec> > rnb(nelements,nelements, BUFLEN);
  TinyMatrixOfVector<vector<double> > sqdist(nelements,nelements, BUFLEN);
  TinyMatrixOfVector<vector<double> > dEdss(nelements,nelements, BUFLEN);
  TinyMatrixOfVector<vector<double> > dEdso(nelements,nelements, BUFLEN);
  vector<int> other_buf(BUFLEN);
  vector<Vec> rnb_buf(BUFLEN);
  vector<double> sqdist_buf(BUFLEN);

#ifdef ASAP_FOR_KIM
  const int *contributes = atoms->GetParticleContributes();
#endif
  
  // If there is only one element, CalculateForcesAfterEnergiesSingle should
  // be used.
  ASSERT(nelements > 1);

  int nSize = this->nSize;  // Helps optimization.
  Vec *RESTRICT force = &(this->force)[0];
  
  /* Set forces and virials to zero */
  if (virials.size())
    {
      ASSERT(virials.size() == nSize);
#ifdef _OPENMP
#pragma omp for nowait
#endif // _OPENMP
      for (int i = 0; i < nSize; i++)
        for (int j = 0; j < 6; j++)
          virials[i][j] = 0.0;
    }
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
  for (int i = 0; i < nSize; i++)
    force[i][0] = force[i][1] = force[i][2] = 0.0;

  /* Calculate forces */

  /* No atoms in batch pools */
  for (int i = 0; i < nelements; i++)
    for (int j = 0; j < nelements; j++)
      nbatch[i][j] = 0;

  // Loop over atoms
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
  for (int atom = 0; atom < nAtoms; atom++) {
#ifdef ASAP_FOR_KIM
    if (!contributes[atom]) continue;  // Skip non-contributing atom in OpenKIM, where nAtoms == nSize.
#endif
    int zself = id[atom];
    // Get neighbors and loop over them.
    int size = BUFLEN;
    int n;
    if (always_fullnblist)
      n = nblist->GetFullNeighbors(atom, &other_buf[0], &rnb_buf[0],
                                   &sqdist_buf[0], size);
    else
      n = nblist->GetNeighbors(atom, &other_buf[0], &rnb_buf[0],
                               &sqdist_buf[0], size);
    ASSERT(size >= 0);    // REMOVE LATER
    for (int i = 0; i < n; i++) {
      int zother = id[other_buf[i]];
      int nbat = nbatch[zself][zother]++;  // Count this atom
      self[zself][zother][nbat] = atom;
      other[zself][zother][nbat] = other_buf[i];
      rnb[zself][zother][nbat][0] = rnb_buf[i][0];
      rnb[zself][zother][nbat][1] = rnb_buf[i][1];
      rnb[zself][zother][nbat][2] = rnb_buf[i][2];
      sqdist[zself][zother][nbat] = sqdist_buf[i];
      dEdss[zself][zother][nbat] = dEds[atom];
      dEdso[zself][zother][nbat] = dEds[other_buf[i]];
    }
    // Now process any full batch
    for (int zo = 0; zo < nelements; zo++)
      if (nbatch[zself][zo] >= BUFLEN - maxnblen) {
        force_batch(&self[zself][zo][0], &other[zself][zo][0],
		    &rnb[zself][zo][0],
                    &sqdist[zself][zo][0], &dEdss[zself][zo][0],
                    &dEdso[zself][zo][0], zself, zo, nbatch[zself][zo]);
        nbatch[zself][zo] = 0;
      }
  }  // Loop over atoms
  /* Process the remaining incomplete batches */
  for (int zs = 0; zs < nelements; zs++)
    for (int zo = 0; zo < nelements; zo++)
      if (nbatch[zs][zo])
        force_batch(&self[zs][zo][0], &other[zs][zo][0], &rnb[zs][zo][0],
                    &sqdist[zs][zo][0], &dEdss[zs][zo][0],
                    &dEdso[zs][zo][0], zs, zo, nbatch[zs][zo]);
  DEBUGPRINT;
#ifdef _OPENMP
#pragma omp barrier
#endif // _OPENMP
}

void EMT::CalculateForcesAfterEnergiesSingle()
{
  RETURNIFASAPERROR;
  USETIMER("EMT::CalculateForcesAfterEnergiesSingle");
  if (!(recalc.forces || (virials.size() && recalc.virials)))
    return;
#ifdef _OPENMP
#pragma omp master
#endif // _OPENMP
  {
      VERB("f");
      if (virials.size())
        {
          VERB("s");
        }
  }
#ifdef _OPENMP
#pragma omp barrier
#endif // _OPENMP
  int maxnblen = nblist->MaxNeighborListLength();
  DEBUGPRINT;
  // Buffer data:
  int nbatch;
  vector<int> self(BUFLEN);
  vector<int> other(BUFLEN);
  vector<Vec> rnb(BUFLEN);
  vector<double> sqdist(BUFLEN);
  vector<double> dEdss(BUFLEN);
  vector<double> dEdso(BUFLEN);

#ifdef ASAP_FOR_KIM
  const int *contributes = atoms->GetParticleContributes();
#endif
  
  int nSize = this->nSize;   // These three lines help optimization.
  int nAtoms = this->nAtoms;
  Vec *RESTRICT force = &(this->force)[0];
  
  DEBUGPRINT;
  // If there is more than one element, CalculateForcesAfterEnergies should
  // be used.
  ASSERT(nelements == 1);
      
  /* Set forces and virials to zero */
  ASSERT(this->force.size() >= nSize);
  if (virials.size())
    {
      ASSERT(virials.size() == nSize);
#ifdef _OPENMP
#pragma omp for nowait
#endif // _OPENMP
      for (int i = 0; i < nSize; i++)
        for (int j = 0; j < 6; j++)
          virials[i][j] = 0.0;
    }
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
  for (int i = 0; i < nSize; i++)
    force[i][0] = force[i][1] = force[i][2] = 0.0;

  /* Calculate forces */

  /* No atoms in batch pool */
  DEBUGPRINT;
  nbatch = 0;

  // Loop over atoms
  DEBUGPRINT;
#ifdef _OPENMP
#pragma omp for
#endif // _OPENMP
  for (int atom = 0; atom < nAtoms; atom++) {

#ifdef ASAP_FOR_KIM
    if (!contributes[atom]) continue;  // Skip non-contributing atom in OpenKIM, where nAtoms == nSize.
#endif

    // Get neighbors and loop over them.
    int size = BUFLEN-nbatch;
    int n;
    if (always_fullnblist)
      n = nblist->GetFullNeighbors(atom, &other[nbatch], &rnb[nbatch],
                                   &sqdist[nbatch], size);
    else
      n = nblist->GetNeighbors(atom, &other[nbatch], &rnb[nbatch],
                               &sqdist[nbatch], size);
    double dEdsatom = dEds[atom];
    for (int i = nbatch; i < nbatch+n; i++) {
      self[i] = atom;
      dEdss[i] = dEdsatom;
      dEdso[i] = dEds[other[i]];
    }
    nbatch += n;
    // Now process any full batch
    if (nbatch >= BUFLEN - maxnblen) {
      force_batch(&self[0], &other[0], &rnb[0], &sqdist[0], &dEdss[0],
		  &dEdso[0], 0, 0, nbatch);
      nbatch = 0;
    }
  }  // Loop over atoms
  /* Process the remaining incomplete batch */
  DEBUGPRINT;
  if (nbatch)
    force_batch(&self[0], &other[0], &rnb[0], &sqdist[0], &dEdss[0],
		&dEdso[0], 0, 0, nbatch);
  DEBUGPRINT;
#ifdef _OPENMP
#pragma omp barrier
#endif // _OPENMP
}

// It would be natural to transfer the arrays as vector<> instead of
// as pointes, but that confuses the compiler so it cannot discover
// that various arrays are disjunct, ruining optimization.  For the
// same reason, the temporary array is not a vector<>.
void EMT::force_batch(const int *RESTRICT self, const int *RESTRICT other,
                      const Vec *RESTRICT rnb, const double *RESTRICT sq_dist,
                      const double *RESTRICT dEdss, const double *RESTRICT dEdso,
                      int zs, int zo, int n)
{
  USETIMER("EMT::force_batch");
#ifdef ASAP_MKL
  double *temporary = (double *) mkl_malloc(8 * BUFLEN * sizeof(double), ASAP_MKL_ALIGN);
  double *RESTRICT df = temporary;
  double *RESTRICT tmp_a = df + BUFLEN;
  double *RESTRICT tmp_b = tmp_a + BUFLEN;
  double *RESTRICT tmp_c = tmp_b + BUFLEN;
  double *RESTRICT tmp_d = tmp_c + BUFLEN;
  double *RESTRICT tmp_e = tmp_d + BUFLEN;
  double *RESTRICT tmp_f = tmp_e + BUFLEN;
  double *RESTRICT tmp_g = tmp_f + BUFLEN;
  //ASSERT(tmp_g - temporary == (8 - 1) * BUFLEN);
#else // ASAP_MKL
  double *temporary = new double[BUFLEN];
  double *RESTRICT df = temporary;
#endif // ASAP_MKL
  double cutslopecutdist, other_eta2betaseq, other_kappaoverbeta;
  double other_kappaseq, self_eta2betaseq, self_kappaoverbeta;
  double self_kappaseq, cnst_s, cnst_o;
  const emt_parameters *emtself, *emtother;
  //double pairA, exprcut, pairD;
  //double *tmp;

  ASSERT(n <= BUFLEN);
  
  /* Get EMT parameters */
  emtself = parameters[zs];
  emtother = parameters[zo];
  cutslopecutdist = cutoffslope * rFermi;
  other_eta2betaseq = emtother->eta2 * Beta * emtother->seq;
  other_kappaoverbeta = emtother->kappa / Beta;
  other_kappaseq = emtother->kappa * emtother->seq;
  self_eta2betaseq = emtself->eta2 * Beta * emtself->seq;
  self_kappaoverbeta = emtself->kappa / Beta;
  self_kappaseq = emtself->kappa * emtself->seq;
  double other_eta2 = emtother->eta2;
  double self_eta2 = emtself->eta2;

  cnst_s = -0.5 * emtself->V0 * (*chi)[zs][zo] / emtself->gamma2;
  cnst_o = -0.5 * emtother->V0 * (*chi)[zo][zs] / emtother->gamma2;
  double chi_zs_zo = (*chi)[zs][zo];
  double chi_zo_zs = (*chi)[zo][zs];
  // Three cases: 1) The two atoms have the same atomic number,
  // 2) they have different atomic number (less reuse of calculations)
  // 3) we use full neighbor lists (no reuse).
  if ((zs == zo) && !always_fullnblist)
    { 
#ifdef ASAP_MKL
      /* Get the distances from their squares */
      // dist[] = tmp_a[] = sqrt(sq_dist[])
      vdSqrt(n, sq_dist, tmp_a);
      // invdist[] = tmp_e[] = 1.0 / dist[]
      vdInv(n, tmp_a, tmp_e);
      for (int i = 0; i < n; i++)
        {
	  tmp_b[i] = cutoffslope * tmp_a[i] - cutslopecutdist;
	  tmp_c[i] = -other_eta2 * tmp_a[i] + other_eta2betaseq;
	  tmp_d[i] = -other_kappaoverbeta * tmp_a[i] + other_kappaseq;
	}
      // tmp_a[] = exp(tmp_b[]) = exp(cutoffslope * dist[] - cutslopecutdist)
      vdExp(n, tmp_b, tmp_a);
      // tmp_b[] = exp(tmp_c[]) = exp(-other_eta2 * dist[] + other_eta2betaseq)
      vdExp(n, tmp_c, tmp_b);
      // tmp_c[] = exp(tmp_d[]) = exp(-other_kappaoverbeta * dist[] + other_kappaseq)
      vdExp(n, tmp_d, tmp_c);
      for (int i = 0; i < n; i++)
	{
	  /* Calculate cutoff function (weight factor) */
	  double wght = 1.0 / (1.0 + tmp_a[i]);
	  /* Calculate derivative of the cutoff function. */
	  double dwdr = -cutoffslope * wght * (1 - wght);
	  double dsigma1dr = (dwdr - wght * other_eta2) * tmp_b[i];
	  double dsigma2dr = (dwdr + wght * -other_kappaoverbeta) * tmp_c[i];
	  df[i] = tmp_e[i] * (dsigma1dr * dEdss[i] * chi_zs_zo
			      + cnst_s * dsigma2dr
			      + dsigma1dr * dEdso[i] * chi_zo_zs
			      + cnst_o * dsigma2dr * (other[i] < nAtoms));
	}
#else //ASAP_MKL
      for (int i = 0; i < n; i++)
	{
	  /* Get the distances from their squares */
	  double dist = sqrt(sq_dist[i]);
	  double inv_dist = 1.0 / dist;
	  /* Calculate cutoff function (weight factor) */
	  double wght = 1.0 / (1.0 + exp(cutoffslope * dist
					 - cutslopecutdist));
	  /* Calculate derivative of the cutoff function. */
	  double dwdr = -cutoffslope * wght * (1 - wght);
	  double dsigma1dr = (dwdr - wght * other_eta2) *
	    exp(-other_eta2 * dist + other_eta2betaseq);
	  double dsigma2dr = (dwdr + wght * -other_kappaoverbeta) *
	    exp(-other_kappaoverbeta * dist + other_kappaseq);
	  df[i] = inv_dist * (dsigma1dr * dEdss[i] * chi_zs_zo
			      + cnst_s * dsigma2dr // * (self[i] < nAtoms)   always true
			      + dsigma1dr * dEdso[i] * chi_zo_zs
			      + cnst_o * dsigma2dr * (other[i] < nAtoms));
	}
#endif //ASAP_MKL
    }
  else if (!always_fullnblist)
    {
      // zs != zo.
#ifdef ASAP_MKL
      /* Get the distances from their squares */
      // dist[] = tmp_a[] = sqrt(sq_dist[])
      vdSqrt(n, sq_dist, tmp_a);
      // invdist[] = tmp_g[] = 1.0 / dist[]
      vdInv(n, tmp_a, tmp_g);
      for (int i = 0; i < n; i++)
        {
	  tmp_b[i] = cutoffslope * tmp_a[i] - cutslopecutdist;
	  tmp_c[i] = -other_eta2 * tmp_a[i] + other_eta2betaseq;
	  tmp_d[i] = -other_kappaoverbeta * tmp_a[i] + other_kappaseq;
	  tmp_e[i] = -self_eta2 * tmp_a[i] + self_eta2betaseq;
	  tmp_f[i] = -self_kappaoverbeta * tmp_a[i] + self_kappaseq;
	}
      // tmp_a[] = exp(tmp_b[]) = exp(cutoffslope * dist[] - cutslopecutdist)
      vdExp(n, tmp_b, tmp_a);
      // tmp_b[] = exp(tmp_c[]) = exp(-other_eta2 * dist[] + other_eta2betaseq)
      vdExp(n, tmp_c, tmp_b);
      // tmp_c[] = exp(tmp_d[]) = exp(-other_kappaoverbeta * dist[] + other_kappaseq)
      vdExp(n, tmp_d, tmp_c);
      // tmp_d[] = exp(tmp_e[]) = exp(-self_eta2 * dist[] + self_eta2betaseq)
      vdExp(n, tmp_e, tmp_d);
      // tmp_e[] = exp(tmp_f[]) = exp(-self_kappaoverbeta * dist[] + self_kappaseq)
      vdExp(n, tmp_f, tmp_e);
      for (int i = 0; i < n; i++)
	{
	  /* Calculate cutoff function (weight factor) */
	  double wght = 1.0 / (1.0 + tmp_a[i]);
	  /* Calculate derivative of the cutoff function. */
	  double dwdr = -cutoffslope * wght * (1 - wght);
	  double dsigma1dr_o = (dwdr - wght * other_eta2) * tmp_b[i];
	  double dsigma2dr_o = (dwdr + wght * -other_kappaoverbeta) * tmp_c[i];
	  double dsigma1dr_s = (dwdr - wght * self_eta2) * tmp_d[i];
	  double dsigma2dr_s = (dwdr + wght * -self_kappaoverbeta) * tmp_e[i];
	  df[i] = tmp_g[i] * (dsigma1dr_o * dEdss[i] * chi_zs_zo
			      + cnst_s * dsigma2dr_o
			      + dsigma1dr_s * dEdso[i] * chi_zo_zs
			      + cnst_o * dsigma2dr_s * (other[i] < nAtoms));
	}      
#else // ASAP_MKL
      for (int i = 0; i < n; i++)
	{
	  /* Get the distances from their squares */
	  double dist = sqrt(sq_dist[i]);
	  double inv_dist = 1.0 / dist;
	  /* Calculate cutoff function (weight factor) */
	  double wght = 1.0 / (1.0 + exp(cutoffslope * dist -
					 cutslopecutdist));
	  /* Calculate derivative of the cutoff function. */
	  double dwdr = -cutoffslope * wght * (1 - wght);
	  double dsigma1dr_o = (dwdr - wght * other_eta2) *
	    exp(-other_eta2 * dist + other_eta2betaseq);
	  double dsigma2dr_o = (dwdr + wght * -other_kappaoverbeta) *
	    exp(-other_kappaoverbeta * dist + other_kappaseq);
	  double dsigma1dr_s = (dwdr - wght * self_eta2) *
	    exp(-self_eta2 * dist + self_eta2betaseq);
	  double dsigma2dr_s = (dwdr + wght * -self_kappaoverbeta) *
	    exp(-self_kappaoverbeta * dist + self_kappaseq);
	  df[i] = inv_dist * (dsigma1dr_o * dEdss[i] * chi_zs_zo
			      + cnst_s * dsigma2dr_o // * (self[i] < nAtoms)  always true!
			      + dsigma1dr_s * dEdso[i] * chi_zo_zs
			      + cnst_o * dsigma2dr_s * (other[i] < nAtoms));
	}
#endif //ASAP_MKL
    }
  else
    {
      // Using full neighbor lists
#ifdef ASAP_MKL
      /* Get the distances from their squares */
      // dist[] = tmp_a[] = sqrt(sq_dist[])
      vdSqrt(n, sq_dist, tmp_a);
      // invdist[] = tmp_e[] = 1.0 / dist[]
      vdInv(n, tmp_a, tmp_e);
      for (int i = 0; i < n; i++)
        {
	  tmp_b[i] = cutoffslope * tmp_a[i] - cutslopecutdist;
	  tmp_c[i] = -other_eta2 * tmp_a[i] + other_eta2betaseq;
	  tmp_d[i] = -other_kappaoverbeta * tmp_a[i] + other_kappaseq;
	}
      // tmp_a[] = exp(tmp_b[]) = exp(cutoffslope * dist[] - cutslopecutdist)
      vdExp(n, tmp_b, tmp_a);
      // tmp_b[] = exp(tmp_c[]) = exp(-other_eta2 * dist[] + other_eta2betaseq)
      vdExp(n, tmp_c, tmp_b);
      // tmp_c[] = exp(tmp_d[]) = exp(-other_kappaoverbeta * dist[] + other_kappaseq)
      vdExp(n, tmp_d, tmp_c);
      for (int i = 0; i < n; i++)
        {
          /* Calculate cutoff function (weight factor) */
          double wght = 1.0 / (1.0 + tmp_a[i]);
          /* Calculate derivative of the cutoff function. */
          double dwdr = -cutoffslope * wght * (1 - wght);
          double dsigma1dr_o = (dwdr - wght * other_eta2) * tmp_b[i];
          double dsigma2dr_o = (dwdr + wght * -other_kappaoverbeta) * tmp_c[i];
          df[i] = tmp_e[i] * (dsigma1dr_o * dEdss[i] * chi_zs_zo
                              + cnst_s * dsigma2dr_o);
	}
#else // ASAP_MKL
      for (int i = 0; i < n; i++)
        {
          /* Get the distances from their squares */
          double dist = sqrt(sq_dist[i]);
          double inv_dist = 1.0 / dist;
          /* Calculate cutoff function (weight factor) */
          double wght = 1.0 / (1.0 + exp(cutoffslope * dist -
                                         cutslopecutdist));
          /* Calculate derivative of the cutoff function. */
          double dwdr = -cutoffslope * wght * (1 - wght);
          double dsigma1dr_o = (dwdr - wght * other_eta2) *
            exp(-other_eta2 * dist + other_eta2betaseq);
          double dsigma2dr_o = (dwdr + wght * -other_kappaoverbeta) *
            exp(-other_kappaoverbeta * dist + other_kappaseq);
          df[i] = inv_dist * (dsigma1dr_o * dEdss[i] * chi_zs_zo
                              + cnst_s * dsigma2dr_o);
        }
#endif // ASAP_MKL
    }

  distribute_force(self, other, df, rnb, n);

#ifdef ASAP_MKL
  mkl_free(temporary);
#else
  delete[] temporary;
#endif
}

void EMT::distribute_force(const int *RESTRICT self, const int *RESTRICT other,
    const double *RESTRICT df, const Vec *RESTRICT rnb, int n)
{
  /* Distribute force contributions */
#ifdef _OPENMP
#pragma omp critical
#endif // _OPENMP
  {
    for (int i = 0; i < n; i++)
      for (int j = 0; j < 3; j++)
        {
          double dfx = df[i] * rnb[i][j];
          force[self[i]][j] += dfx;
          force[other[i]][j] -= dfx;  // force has been extended to nSize.
        }

    /* Distribute virials contributions */
    if (virials.size())
      {
        for (int i = 0; i < n; i++)
          for (int alpha = 0; alpha < 3; alpha++)
            for (int beta = alpha; beta < 3; beta++)
              {
                double dsx = 0.5 * df[i] * rnb[i][alpha] * rnb[i][beta];
                int ii = stresscomp[alpha][beta];
                virials[self[i]][ii] += dsx;
                virials[other[i]][ii] += dsx;
              }
      }
  }
}

double EMT::GetLatticeConstant() const
{
    ASSERT(singleelement != 0);
    return Beta * singleelement->seq * sqrt(2.0);
}

void EMT::PrintParameters()
{
  for (int i = 0; i < nelements; i++)
    {
      const emt_parameters *p = parameters[i];
      cerr << endl;
      cerr << "Parameters for element " << i << " (" << p->name << ", Z=" << p->Z << ")" << endl;
      cerr << "E0:" << p->e0 << "  s0:" << p->seq << "  V0:" << p->V0 <<
        "  eta2:" << p->eta2 << "  kappa:" << p->kappa << "  lambda:" << p->lambda <<
        "  rFermi:" << rFermi << "  cutSlope" << cutoffslope <<
        "  gamma1:" << p->gamma1 << "  gamma2:" <<  p->gamma2 << endl <<
        endl;
      cerr << "Chi:";
      for (int j = 0; j < nelements; j++)
	cerr << " " << (*chi)[i][j];
      cerr << endl;
    }
}

void EMT::BoundaryConditionsChanged()
{
  if (nblist)
    nblist->Invalidate();
}
