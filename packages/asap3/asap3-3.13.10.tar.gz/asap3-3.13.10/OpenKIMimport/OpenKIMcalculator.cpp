// OpenKIMcalculator.cpp - interface to OpenKIM models.
//
// This class is part of the optional Asap module to support OpenKIM
// models.  The class OpenKIMcalculator does the actual interfacing
// to the model.

// Copyright (C) 2014 Jakob Schiotz and Center for Individual
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

#include "Asap.h"
#include "OpenKIMcalculator.h"
#include "KIM_SimulatorHeaders.hpp"
#include "Atoms.h"
#include "NeighborList.h"
#include "Timing.h"
//#define ASAPDEBUG
#include "Debug.h"
#include <iostream>
#include <cstdlib>

using std::cerr;
using std::endl;
using std::flush;

#if 1
#define VERB(x) if (verbose == 1) cerr << x
#else
#define VERB(x)
#endif


static int get_neigh(void *const dataObject,
		     int const numberOfNeighborLists,
		     double const * const cutoffs,
		     int const neighborListIndex, int const particleNumber,
		     int * const numberOfNeighbors,
		     int const ** const neighborsOfParticle)
{
  OpenKIMcalculator::NeighborListData * const data =
    (OpenKIMcalculator::NeighborListData * const) dataObject;
  ASSERT(data != NULL);
  ASSERT(numberOfNeighborLists == data->nblists.size());
  NeighborLocator *nblist = data->nblists[neighborListIndex];
  ASSERT(nblist != NULL);

  nblist->GetFullNeighbors(particleNumber, data->nb_buffers[neighborListIndex]);
  *numberOfNeighbors = data->nb_buffers[neighborListIndex].size();
  *neighborsOfParticle = &(data->nb_buffers[neighborListIndex][0]);
  return false;  // Success
}

OpenKIMcalculator::OpenKIMcalculator(PyObject *self, const char *name, int verbose) : Potential(self, verbose)
{
  CONSTRUCTOR;
  DEBUGPRINT;
  kimname = name;
  model = NULL;
  model_initialized = false;
  computeargs = NULL;
  counters.nblist = counters.compute = -1;
  driftfactor = 0.05;  // Drift factor for the neighbor list.
  support_n = 0;
  nAtoms = nSize = 0;
  nAtomsAlloc = nSizeAlloc = 0;
  nblist_iterator = -10000;
  nblists.clear();
  nblist_objs.clear();
  independentlist.clear();
  this->self = self;
  // NB: No INCREF!  This is not a reference, but a pointer internal
  // to the Python object.

  // Create the KIM API object
  DEBUGPRINT;
  int error;
  int requestedUnitsAccepted = 42;
  error = KIM::Model::Create(KIM::NUMBERING::zeroBased,
                             KIM::LENGTH_UNIT::A,
                             KIM::ENERGY_UNIT::eV,
                             KIM::CHARGE_UNIT::unused,
                             KIM::TEMPERATURE_UNIT::unused,
                             KIM::TIME_UNIT::ps,
			     //KIM::TIME_UNIT::unused,
                             name,
                             &requestedUnitsAccepted,
                             &model);
  if (error)
    throw AsapError("Failed to initialize OpenKIM model: ") << name;
  assert(requestedUnitsAccepted != 42);   // Just a check that it was actually updated.
  ASSERT(model != NULL);
  
  // We now have a KIM::Model object.  For the rest of this
  // constructor, we must explicitly destroy it if an exception
  // occurs, since the OpenKIMcalculator destructor will not be called
  // if this constructor fails.
  try {
    if (!requestedUnitsAccepted)
    {
      // Deal with failure?  Asap *could* adapt to other units, but it
      // ought to be done by the model.
      throw AsapError("Units did not match OpenKIM model ") << name;
    }
    
    VerifyKimCompatibility();
  
    DEBUGPRINT;
    error = model->ComputeArgumentsCreate(&computeargs);
    if (error)
      throw AsapError("Failed to create compute arguments for OpenKIM model: ") << name;
    ASSERT(computeargs != NULL);
    
    InitParameters();
  }
  catch(const std::exception &e)
  {
    // Clean up the partially constructed object, then rethrow exception
    if (computeargs != NULL)
      model->ComputeArgumentsDestroy(&computeargs);
    KIM::Model::Destroy(&model);
    computeargs = NULL;
    model = NULL;
    throw;
  }
}

OpenKIMcalculator::~OpenKIMcalculator()
{
  DESTRUCTOR;
  DEBUGPRINT;
  if (model != NULL)
    {
      if (computeargs != NULL)
	model->ComputeArgumentsDestroy(&computeargs);
      KIM::Model::Destroy(&model);
    }
  if (atoms != NULL)
    AsapAtoms_DECREF(atoms);
  for (int i = 0; i < nblist_objs.size(); ++i)
    Py_XDECREF(nblist_objs[i]);
}

void OpenKIMcalculator::InitParameters()
{
  // Get influence distance and neighbor list cutoffs
  model->GetInfluenceDistance(&influenceDistance);
  if (influenceDistance <= 0.0 || influenceDistance > 1e6)
    throw AsapError("Insane influenceDistance: ") << influenceDistance;
  if (verbose == 2)
    std::cerr << "Influence distance:" << influenceDistance << std::endl;
  const double *api_cutoffs;
  const int *api_paddingNeighborHints;
  model->GetNeighborListPointers(&numberOfNeighborLists,
				 &api_cutoffs,
				 &api_paddingNeighborHints);
  cutoffs.resize(numberOfNeighborLists);
  paddingNeighborHints.resize(numberOfNeighborLists);
  double longestcutoff = 0.0;
  for (int i = 0; i < numberOfNeighborLists; ++i)
  {
    cutoffs[i] = api_cutoffs[i];
    if (verbose == 2)
      std::cerr << "  Cutoff " << i << ": " << cutoffs[i] << "    NoNeighborOfNonContributing:: "
		<< api_paddingNeighborHints[i] << std::endl;
    if (cutoffs[i] > longestcutoff)
    {
      longestcutoff = cutoffs[i];
      masternblist = i;
    }
    if (cutoffs[i] < 0.0 || cutoffs[i] > influenceDistance)
      throw AsapError("Illegal neigborlist cutoff distance: ")
	<< cutoffs[i] << " (influence distance is " << influenceDistance << ").";
    paddingNeighborHints[i] = api_paddingNeighborHints[i];
    if (paddingNeighborHints[i] != 0 && paddingNeighborHints[i] != 1)
      throw AsapError("Illegal value of paddingNeighborHint: ") << paddingNeighborHints[i];
  }  
}

void OpenKIMcalculator::PleaseSupport(string quantity, bool alloc)
{
  DEBUGPRINT;
  if (quantity == "partialEnergy")
    support.energy = alloc;
  else if (quantity == "partialParticleEnergy")
    support.particleEnergy = alloc;
  else if (quantity == "partialForces")
    support.forces = alloc;
  else if (quantity == "partialVirial")
    support.virial = alloc;
  else if (quantity == "partialParticleVirial")
    support.particleVirial = alloc;
  else
    throw AsapError("Unknown argument to OpenKIMcalculator::PleaseAllocate: ") << quantity;
  support_n++;
  DEBUGPRINT;
}

std::map<string,string> OpenKIMcalculator::GetComputeArguments()
{
  DEBUGPRINT;
  std::map<string,string> result;
  int nnames;
  KIM::COMPUTE_ARGUMENT_NAME::GetNumberOfComputeArgumentNames(&nnames);
  ASSERT(nnames > 0);
  for (int i = 0; i < nnames; i++)
  {
    int error;
    KIM::ComputeArgumentName argname;
    error = KIM::COMPUTE_ARGUMENT_NAME::GetComputeArgumentName(i, &argname);
    ASSERT(!error);   // Should not be able to fail
    KIM::SupportStatus supportstatus;
    error = computeargs->GetArgumentSupportStatus(argname, &supportstatus);
    ASSERT(!error);   // Should not be able to fail
    result[argname.ToString()] = supportstatus.ToString();
  }
  KIM::COMPUTE_CALLBACK_NAME::GetNumberOfComputeCallbackNames(&nnames);
  ASSERT(nnames > 0);
  for (int i = 0; i < nnames; i++)
  {
    int error;
    KIM::ComputeCallbackName argname;
    error = KIM::COMPUTE_CALLBACK_NAME::GetComputeCallbackName(i, &argname);
    ASSERT(!error);   // Should not be able to fail
    KIM::SupportStatus supportstatus;
    error = computeargs->GetCallbackSupportStatus(argname, &supportstatus);
    ASSERT(!error);   // Should not be able to fail
    result[argname.ToString()] = supportstatus.ToString();
  }
  DEBUGPRINT;
  return result;
}

void OpenKIMcalculator::SetAtoms(PyObject *pyatoms, Atoms* accessobj)
{
  DEBUGPRINT;
  if (atoms != NULL)
    {
      // SetAtoms should only do anything the first time it is called.
      // Subsequent calls should just check for accessobj being NULL.
      if (accessobj != NULL)
        throw AsapError("OpenKIMcalculator::SetAtoms called multiple times with accessobj != NULL");
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
  DEBUGPRINT;
}

const vector<Vec> &OpenKIMcalculator::GetForces(PyObject *pyatoms){
  USETIMER("OpenKIMcalculator::GetForces")
  DEBUGPRINT;
  if (!support.forces)
    throw AsapError("OpenKIMcalculator not prepared to calculate forces.");
  VERB(" Forces[");
  Calculate(pyatoms);
  ASSERT(forces.size() == nSize);
  DEBUGPRINT;
  return forces;
}

const vector<double> &OpenKIMcalculator::GetPotentialEnergies(PyObject *pyatoms)
{
  USETIMER("OpenKIMcalculator::GetPotentialEnergies");
  DEBUGPRINT;
  if (!support.particleEnergy)
    throw AsapError("OpenKIMcalculator not prepared to calculate particle energies.");
  VERB(" Energies[");
  Calculate(pyatoms);
  ASSERT(particleEnergy.size() == nSize);
  // Only the nAtoms first energies are 'real'
  particleEnergy.resize(nAtoms);
  return particleEnergy;
}

double OpenKIMcalculator::GetPotentialEnergy(PyObject *pyatoms)
{
  USETIMER("OpenKIMcalculator::GetPotentialEnergy");
  DEBUGPRINT;
  VERB(" Energy[");
  Calculate(pyatoms);
  return energy;
}

const vector<SymTensor> &OpenKIMcalculator::GetVirials(PyObject *pyatoms)
{
  USETIMER("OpenKIMcalculator::GetVirials");
  DEBUGPRINT;
  if (!support.particleVirial)
    throw AsapError("OpenKIMcalculator not prepared to calculate particle virials.");
  VERB(" Virials[");
  Calculate(pyatoms);
  ASSERT(particleVirial.size() == nSize);
  return particleVirial;
}

SymTensor OpenKIMcalculator::GetVirial(PyObject *pyatoms)
{
  USETIMER("OpenKIMcalculator::GetVirial");
  DEBUGPRINT;
  if (!support.virial)
    throw AsapError("OpenKIMcalculator not prepared to calculate virial.");
  VERB(" Virial[");
  Calculate(pyatoms);
  return virial;
}

bool OpenKIMcalculator::CalcReq_Energy(PyObject *pyatoms)
{
  DEBUGPRINT;
  atoms->Begin(pyatoms);
  bool required = (!support.energy || counters.compute != atoms->GetPositionsCounter());
  atoms->End();
  return required;
}

bool OpenKIMcalculator::CalcReq_Forces(PyObject *pyatoms)
{
  DEBUGPRINT;
  atoms->Begin(pyatoms);
  bool required = (!support.forces || counters.compute != atoms->GetPositionsCounter());
  atoms->End();
  return required;
}

bool OpenKIMcalculator::CalcReq_Virials(PyObject *pyatoms)
{
  DEBUGPRINT;
  atoms->Begin(pyatoms);
  bool required = (!support.virial || counters.compute != atoms->GetPositionsCounter());
  atoms->End();
  return required;
}

bool OpenKIMcalculator::CheckAndUpdateNbList(PyObject *pyatoms)
{
  atoms->Begin(pyatoms);
  bool update = CheckNeighborList();
  if (update)
    UpdateNeighborList();
  atoms->End();
  return update;
}

bool OpenKIMcalculator::CheckNeighborList()
{
  RETURNIFASAPERROR2(false);
  USETIMER("OpenKIMcalculator::CheckNeighborList");
  DEBUGPRINT;
  ASSERT(atoms != NULL);
  bool update = (nblists.size() == 0);
  for (int i = 0; i < nblists.size(); ++i)
    update = update || nblists[i]->IsInvalid();  // Update if invalid
  if (!update && (counters.nblist != atoms->GetPositionsCounter()))
    {
      DEBUGPRINT;
      VERB("n");
      update = nblists[masternblist]->CheckNeighborList();
    }
  // May communicate
  update = atoms->UpdateBeforeCalculation(update,
                                          influenceDistance + cutoffs[masternblist] * driftfactor);
  counters.nblist = atoms->GetPositionsCounter();
  DEBUGPRINT;
  return update;
}

void OpenKIMcalculator::UpdateNeighborList()
{
  RETURNIFASAPERROR;
  USETIMER("OpenKIMcalculator::UpdateNeighborList");
  DEBUGPRINT;
  VERB("N");
  DEBUGPRINT;
  RETURNIFASAPERROR;
  if (nblists.size())
    {
      DEBUGPRINT;
      nblists[masternblist]->UpdateNeighborList();
      for (int i = 0; i < nblists.size(); ++i)
	if ((i != masternblist) && independentlist[i])
	  nblists[i]->UpdateNeighborList();
      RETURNIFASAPERROR;
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
      // First call, create the neighbor list.
      DEBUGPRINT;
      CreateNeighborList();
      RETURNIFASAPERROR;
      {
        nAtoms = atoms->GetNumberOfAtoms();
        nSize = nAtoms + atoms->GetNumberOfGhostAtoms();
        ghostatoms = atoms->HasGhostAtoms();
        Allocate();
      }
    }
  DEBUGPRINT;
}

void OpenKIMcalculator::CreateNeighborList()
{
  DEBUGPRINT;
  RETURNIFASAPERROR;
  MEMORY;
  USETIMER("OpenKIMcalculator::CreateNeighborList");
  nblists.resize(numberOfNeighborLists);
  nblist_objs.resize(numberOfNeighborLists);
  independentlist.resize(numberOfNeighborLists);
  nblistdata.nblists.resize(numberOfNeighborLists);
  nblistdata.nb_buffers.resize(numberOfNeighborLists);
  for (int i = 0; i < numberOfNeighborLists; ++i)
  {
    // Can we reuse an existing list?
    int reuse = -1;
    for (int j = 0; (j < i) && (reuse == -1); ++j)
    {
      if (cutoffs[i] == cutoffs[j])
	reuse = j;
    }
    if (reuse > -1)
    {
      nblists[i] = nblists[reuse];
      nblist_objs[i] = nblist_objs[reuse];
      Py_INCREF(nblist_objs[i]);
      independentlist[i] = false;
    }
    else
    {
      independentlist[i] = true;
      double driftdistance = driftfactor * cutoffs[masternblist];
      PyAsap_NeighborLocatorObject *nbl;
      nbl = PyAsap_NewNeighborList(atoms, cutoffs[i], driftdistance / cutoffs[i]);
      nblists[i] = nbl->cobj;
      nblist_objs[i] = (PyObject *) nbl;
      NeighborList *nblist2 = dynamic_cast<NeighborList *>(nblists[i]);
      ASSERT(nblist2 != NULL);
      nblist2->EnableFullNeighborLists();
      if (!paddingNeighborHints[i])
	nblist2->EnableNeighborsOfGhosts();
      nblists[i]->UpdateNeighborList();
    }
    nblistdata.nblists[i] = nblists[i];
    nblistdata.nb_buffers[i].clear();
  }
  int error = computeargs->SetCallbackPointer(
      KIM::COMPUTE_CALLBACK_NAME::GetNeighborList,
      KIM::LANGUAGE_NAME::cpp,
      (KIM::Function *) &get_neigh,
      &nblistdata);
  if (error)
    throw AsapError("Failed to set callback pointer for GetNeighborList ") << kimname;
  MEMORY;
}

void OpenKIMcalculator::Allocate()
{
  DEBUGPRINT;
  RETURNIFASAPERROR;
  ASSERT(support_n == 5);
  USETIMER("OpenKIMcalculator::Allocate");
  DEBUGPRINT;
  VERB(" Allocate[" << nAtoms << "," << nSize << "]" << flush);
  // WARNING: Resizing the vector may allocate way too much memory.  It
  // appears that calling reserve solves this problem.  For efficiency,
  // reserve is called with 5% extra space.  This is only necessary if the
  // atoms have ghosts, otherwise no reallocation will happen.

  // First, check if reallocation is necessary.
  ASSERT(nSize > 0);
  if (nSize != nSizeAlloc || nAtoms != nAtomsAlloc)
    {
      DEBUGPRINT;
      // Do the reserve trick if the atoms have ghosts.
      if (ghostatoms)
        {
          // Atoms have ghosts.  Reserve a bit extra memory to minimize
          // reallocation due to migration.
          // If full neighbor lists are used, reserve extra space for
          // particle energies, as they will get resized when energy is calculated.
          int nSizeRes = nSize + nSize/20;
	  if (particleContributing.capacity() < nSize)
	    particleContributing.reserve(nSizeRes);
          if (support.forces && forces.capacity() < nSize)
            forces.reserve(nSizeRes);
          if (support.particleEnergy && particleEnergy.capacity() < nSize)
            particleEnergy.reserve(nSizeRes);
          if (support.particleVirial && particleVirial.capacity() < nSize)
            particleVirial.reserve(nSizeRes);
        }
      DEBUGPRINT;
      // Resize the arrays. 
      species.resize(nSize);
      particleContributing.resize(nSize);
      for (int i = 0; i < nAtoms; ++i)
	particleContributing[i] = 1;
      for (int i = nAtoms; i < nSize; ++i)
	particleContributing[i] = 0;
      if (support.forces)
        forces.resize(nSize);
      if (support.particleEnergy)
        particleEnergy.resize(nSize);
      if (support.particleVirial)
        particleVirial.resize(nSize);
      // Now set the compute arguments.
      ASSERT(nSize > 0);
      int error;
      error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::numberOfParticles,
					      &nSize);
      ASSERT(!error);
      
      ASSERT(species.size() == nSize);
      error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::particleSpeciesCodes,
					      &species[0]);
      ASSERT(!error);
      
      ASSERT(particleContributing.size() == nSize);
      error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::particleContributing,
					      &particleContributing[0]);
      ASSERT(!error);

      error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialEnergy,
					      &energy);
      ASSERT(!error);
      
      if (support.forces)
      {
	ASSERT(forces.size() == nSize);
	error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialForces,
					        (double *) &forces[0]);
	ASSERT(!error);
      }
      if (support.particleEnergy)
      {
	ASSERT(particleEnergy.size() == nSize);
	error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialParticleEnergy,
					        &particleEnergy[0]);
	ASSERT(!error);
      }
      if (support.virial)
      {
	error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialVirial,
					        &virial[0]);
	ASSERT(!error);
      }
      if (support.particleVirial)
      {
	ASSERT(particleVirial.size() == nSize);
	error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialParticleVirial,
					        (double *) &particleVirial[0]);
	ASSERT(!error);
      }
      // coordinates will be set when the calculation is done.  
    }
  DEBUGPRINT;
}

void OpenKIMcalculator::Calculate(PyObject *pyatoms)
{
  DEBUGPRINT;
  ASSERT(atoms != NULL);
  atoms->Begin(pyatoms);
  recalc.nblist = CheckNeighborList();
  recalc.compute = (counters.compute != atoms->GetPositionsCounter());
  if (recalc.compute)
    {
      DEBUGPRINT;
      DoCalculate();
      VERB("]" << flush);
    }
  else
    {
      ASSERT(recalc.nblist == false);
      VERB("-]");
    }
  atoms->End();
  DEBUGPRINT;
}

void OpenKIMcalculator::DoCalculate()
{
  DEBUGPRINT;
  int error;
  if (recalc.nblist)
    UpdateNeighborList();
  ASSERT(nSize > 0);
  // We need to map atomic numbers to the model type codes.
  const asap_z_int *z = atoms->GetAtomicNumbers();
  ASSERT(species.size() == nSize);
  for (int i = 0; i < nSize; i++)
    species[i] = z_to_typecode.at(z[i]);
  error = computeargs->SetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::coordinates,
				      (double*) atoms->GetPositions());
  ASSERT(!error);
  int ok;
  computeargs->AreAllRequiredArgumentsAndCallbacksPresent(&ok);
  if (!ok)
    throw AsapError("computeargs->AreAllRequiredArgumentsAndCallbacksPresent() failed!");
  DEBUGPRINT;
  error = model->Compute(computeargs);
  if (error)
    throw AsapError("OpenKIMcalculator: Compute call failed for model ") << kimname;
  DEBUGPRINT;
  
  counters.compute = atoms->GetPositionsCounter();
  DEBUGPRINT;
}

int OpenKIMcalculator::GetParticleTypeCode(const char *symbol)
{
  DEBUGPRINT;
  KIM::SpeciesName species(symbol);
  
  int code;
  int supported = 0;
  int error = model->GetSpeciesSupportAndCode(species, &supported, &code);
  if (error || !supported)
    throw AsapError("Unsupported element: ") << symbol;
  return code;
}

void OpenKIMcalculator::GetParameterNamesAndTypes(vector<string> &names, vector<int> &datatypes,
						  vector<int> &sizes, vector<string> &descr)
{
  DEBUGPRINT;
  int nparam;
  int error;
  model->GetNumberOfParameters(&nparam);
  names.resize(nparam);
  datatypes.resize(nparam);
  sizes.resize(nparam);
  descr.resize(nparam);
  for (int i = 0; i < nparam; ++i)
  {
    KIM::DataType datatype;
    int size;
    const string *name;
    const string *description;
    error = model->GetParameterMetadata(i, &datatype, &size, &name, &description);
    if (error)
      throw AsapError("Call to KIM::Model::GetParameterMetadata failed.");
    names[i] = *name;
    descr[i] = *description;
    if (datatype == KIM::DATA_TYPE::Integer)
      datatypes[i] = NPY_INT;
    else if (datatype == KIM::DATA_TYPE::Double)
      datatypes[i] = NPY_DOUBLE;
    else
      throw AsapError("OpenKIMcalculator::GetParameterNamesAndTypes encountered unknown KIM::DataType");
    sizes[i] = size;
  }
}

void OpenKIMcalculator::GetParameter(const int parameterindex, int *value)
{
  int error = model->GetParameter(parameterindex, 0, value);
  if (error)
    throw AsapError("GetParameter(int) failed for OpenKIM parameter number ") << parameterindex;
}

void OpenKIMcalculator::GetParameter(const int parameterindex, double *value)
{
  int error = model->GetParameter(parameterindex, 0, value);
  if (error)
    throw AsapError("GetParameter(double) failed for OpenKIM parameter number ") << parameterindex;
}

void OpenKIMcalculator::GetParameter(const int parameterindex, vector<int> &values)
{
  const int n = values.size();
  for (int i = 0; i < n; ++i)
  {
    int error = model->GetParameter(parameterindex, i, &values[i]);
    if (error)
      throw AsapError("GetParameter(vector<int>) failed for OpenKIM parameter number ")
	<< parameterindex << " index " << i;
  } 
}

void OpenKIMcalculator::GetParameter(const int parameterindex, vector<double> &values)
{
  const int n = values.size();
  for (int i = 0; i < n; ++i)
  {
    int error = model->GetParameter(parameterindex, i, &values[i]);
    if (error)
      throw AsapError("GetParameter(vector<double>) failed for OpenKIM parameter number ")
	<< parameterindex << " index " << i;
  } 
}

void OpenKIMcalculator::SetParameter(const int parameterindex, int value)
{
  int error = model->SetParameter(parameterindex, 0, value);
  if (error)
    throw AsapError("SetParameter(int) failed for OpenKIM parameter number ") << parameterindex;
  RefreshModel();
}

void OpenKIMcalculator::SetParameter(const int parameterindex, double value)
{
  int error = model->SetParameter(parameterindex, 0, value);
  if (error)
    throw AsapError("SetParameter(int) failed for OpenKIM parameter number ") << parameterindex;
  RefreshModel();
}

void OpenKIMcalculator::SetParameter(const int parameterindex, const vector<int> &values)
{
  const int n = values.size();
  for (int i = 0; i < n; ++i)
  {
    int error = model->SetParameter(parameterindex, i, values[i]);
    if (error)
      throw AsapError("SetParameter(vector<int>) failed for OpenKIM parameter number ")
	<< parameterindex << " index " << i;
  }
  RefreshModel();
}

void OpenKIMcalculator::SetParameter(const int parameterindex, const vector<double> &values)
{
  const int n = values.size();
  for (int i = 0; i < n; ++i)
  {
    int error = model->SetParameter(parameterindex, i, values[i]);
    if (error)
      throw AsapError("SetParameter(vector<double>) failed for OpenKIM parameter number ")
	<< parameterindex << " index " << i;
  }
  RefreshModel();
}

void OpenKIMcalculator::RefreshModel()
{
  int present;
  int required;
  int error = model->IsRoutinePresent(KIM::MODEL_ROUTINE_NAME::Refresh, &present, &required);
  if (!present)
    throw AsapError("Failed to refresh KIM model as Refresh routine not present.");
  
  if (verbose == 2)
    std::cerr << "Refresh called." << std::endl;
  error = model->ClearThenRefresh();
  if (error)
    throw AsapError("ClearThenRefresh failed.");
  // Test if influence distance or cutoffs have changes.
  double infl;
  model->GetInfluenceDistance(&infl);
  if (verbose == 2)
    std::cerr << "New influence distance: " << infl << std::endl;
  bool changed;
  if (infl != influenceDistance)
    changed = true;
  else
  {
    int nnb;
    const double *api_cutoffs;
    const int *api_paddingNeighborHints;

    model->GetNeighborListPointers(&nnb,
				   &api_cutoffs,
				   &api_paddingNeighborHints);
    if (nnb != cutoffs.size())
      changed = true;
    else
    {
      for (int i = 0; i < cutoffs.size(); ++i)
      {
	if (verbose == 2)
	  std::cerr << "  New cutoff " << i << ": " << api_cutoffs[i] << std::endl;
	if ((api_cutoffs[i] != cutoffs[i]) || (api_paddingNeighborHints[i] != paddingNeighborHints[i]))
	  changed = true;
      }
    }
  }
  if (changed)
  {
    // We must discard all neighbor lists, and allocate new ones
    for (int i = 0; i < nblist_objs.size(); ++i)
      Py_XDECREF(nblist_objs[i]);
    nblist_objs.clear();
    nblists.clear();
    InitParameters();
  }
}

// Check that the model does not require a KIM Routine that we do not
// know about.  This could happen if the KIM API has been extended
// without updating Asap.
// Also verify that the model does provide the routines that we do require.
void OpenKIMcalculator::VerifyKimCompatibility()
{
  int nnames;
  KIM::MODEL_ROUTINE_NAME::GetNumberOfModelRoutineNames(&nnames);
  for (int i = 0; i < nnames; ++i)
  {
    KIM::ModelRoutineName routinename;
    int error = KIM::MODEL_ROUTINE_NAME::GetModelRoutineName(i, &routinename);
    if (error)
      throw AsapError("Call to KIM::MODEL_ROUTINE_NAME::GetModelRoutineName failed.");
    // Is the Routine defined and required by the model?
    int present;
    int required;
    error = model->IsRoutinePresent(routinename, &present, &required);
    if (present && required)
    {
      // First check for known, unsupported routines.  Then check for unknown routines.
      if ((routinename == KIM::MODEL_ROUTINE_NAME::Extension)
	  || (routinename == KIM::MODEL_ROUTINE_NAME::WriteParameterizedModel))
	throw AsapError("Kim model ") << kimname
				      << " requires known but unsupported routine "
				      << routinename.ToString();
      else if ((routinename != KIM::MODEL_ROUTINE_NAME::Create)
	       && (routinename != KIM::MODEL_ROUTINE_NAME::ComputeArgumentsCreate)
	       && (routinename != KIM::MODEL_ROUTINE_NAME::Compute)
	       && (routinename != KIM::MODEL_ROUTINE_NAME::Refresh)
	       && (routinename != KIM::MODEL_ROUTINE_NAME::ComputeArgumentsDestroy)
	       && (routinename != KIM::MODEL_ROUTINE_NAME::Destroy))
	throw AsapError("Kim model ") << kimname
				      << " requires unknown routine "
				      << routinename.ToString()
				      << ": Asap should be updated!";
    }
    else if (!present)
    {
      // Check for absent routines required by this end.  Create is
      // not tested, as it has already been called.  Refresh is not
      // tested here, instead it is tested when we attempt to use it.
      if ((routinename == KIM::MODEL_ROUTINE_NAME::ComputeArgumentsCreate)
	  || (routinename == KIM::MODEL_ROUTINE_NAME::Compute)
	  || (routinename == KIM::MODEL_ROUTINE_NAME::ComputeArgumentsDestroy)
	  || (routinename == KIM::MODEL_ROUTINE_NAME::Destroy))
	throw AsapError("Kim model ") << kimname
				      << " does not provide required routine "
				      << routinename.ToString();
    }
  }
}
