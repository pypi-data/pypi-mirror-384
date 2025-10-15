// -*- C++ -*-
//
// asap_kim_api.cpp: Common interfaces classes for Asap potentials in OpenKIM.
//
// Copyright (C) 2012-2013 Jakob Schiotz and the Department of Physics,
// Technical University of Denmark.  Email: schiotz@fysik.dtu.dk
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


#include "KimAsapPython.h"
#include "asap_kim_api.h"
#include "Potential.h"
#include "KimNeighborLocator.h"
#include "KIM_ModelDriverHeaders.hpp"
#include "SymTensor.h"
#include "Debug.h"
#include <stdlib.h>
#include <string.h>

AsapKimPotential::AsapKimPotential(KIM::ModelDriverCreate * const modelDriverCreate,
				   bool supportvirial)
{
  CONSTRUCTOR;
  int error = 0;
  int numparamfiles = 0;

  potential = NULL;
  atoms = NULL;

  // Register the units.  Conversion happens in the specific model.
  
  // Store the parameter file name(s) for later use by reinit.
  modelDriverCreate->GetNumberOfParameterFiles(&numparamfiles);
  paramfile_names.resize(numparamfiles);
  for (int i = 0; i < numparamfiles; ++i)
  {
    std::string const * paramFileName;
    error = modelDriverCreate->GetParameterFileName(i, &paramFileName);
    if (error)
      throw AsapError("AsapKimPotential: Unable to get parameter file name");
    paramfile_names[i] = *paramFileName;
  }

  this->supportvirial = supportvirial;
  error = modelDriverCreate->SetModelNumbering(KIM::NUMBERING::zeroBased);
  assert(error == 0);   // Should not be able to fail.

  // Store pointers -  XXXXX FIX THESE !!  
  error = (
    modelDriverCreate->SetRoutinePointer(
      KIM::MODEL_ROUTINE_NAME::ComputeArgumentsCreate,
      KIM::LANGUAGE_NAME::cpp,
      true,
      reinterpret_cast<KIM::Function *>(AsapKimPotential::ComputeArgumentsCreate))
    || modelDriverCreate->SetRoutinePointer(
      KIM::MODEL_ROUTINE_NAME::ComputeArgumentsDestroy,
      KIM::LANGUAGE_NAME::cpp,
      true,
      reinterpret_cast<KIM::Function *>(AsapKimPotential::ComputeArgumentsDestroy))
    || modelDriverCreate->SetRoutinePointer(
      KIM::MODEL_ROUTINE_NAME::Compute,
      KIM::LANGUAGE_NAME::cpp,
      true,
      reinterpret_cast<KIM::Function *>(AsapKimPotential::Compute_static))
    || modelDriverCreate->SetRoutinePointer(
      KIM::MODEL_ROUTINE_NAME::Destroy,
      KIM::LANGUAGE_NAME::cpp,
      true,
      reinterpret_cast<KIM::Function *>(AsapKimPotential::Destroy))
    //|| modelDriverCreate->SetRefreshPointer(
    //  KIM::LANGUAGE_NAME::cpp,
    //  (KIM::Function *)2)
    );
  assert(error == 0);  // Should not be able to fail.
}

AsapKimPotential::~AsapKimPotential()
{
  DESTRUCTOR;
  if (potential != NULL)
    delete potential;
  if (atoms != NULL)
    AsapAtoms_DECREF(atoms);
}

void AsapKimPotential::SetPotential(Potential *pot)
{
  potential = pot;
  potential_as_kimmixin = dynamic_cast<PotentialKimMixin*>(pot);
  assert(potential_as_kimmixin != NULL);
}

PyAsap_NeighborLocatorObject *AsapKimPotential::CreateNeighborList(KimAtoms *atoms,
                                                                   double cutoff,
                                                                   double drift)
{
  int ier;
  PyAsap_NeighborLocatorObject *nblist;
  atoms->SetPBC(true, true, true);
  nblist = PyAsap_NewKimNeighborLocator(atoms, cutoff);
  return nblist;
}

// static member function
int AsapKimPotential::ComputeArgumentsCreate(
  KIM::ModelCompute const * const modelCompute,
  KIM::ModelComputeArgumentsCreate * const modelComputeArgumentsCreate)
{
  AsapKimPotential *modelObject;
  modelCompute->GetModelBufferPointer(reinterpret_cast<void **>(&modelObject));

  return modelObject->potential_as_kimmixin->ComputeArgumentsCreate(
      modelComputeArgumentsCreate);
}

// static member function
int AsapKimPotential::ComputeArgumentsDestroy(
  KIM::ModelCompute const * const modelCompute,
  KIM::ModelComputeArgumentsDestroy * const modelComputeArgumentsDestroy)
{
  AsapKimPotential *modelObject;
  modelCompute->GetModelBufferPointer(reinterpret_cast<void **>(&modelObject));

  return modelObject->potential_as_kimmixin->ComputeArgumentsDestroy(
      modelComputeArgumentsDestroy);
}


// static member function
int AsapKimPotential::Destroy(KIM::ModelDestroy * const modelDestroy)
{
  AsapKimPotential *modelObject;
  modelDestroy->GetModelBufferPointer(reinterpret_cast<void **>(&modelObject));

  if (modelObject != NULL)
  {
    // delete object itself
    delete modelObject;
  }

  // everything is good
  return false;
}


// static member function
int AsapKimPotential::Compute_static(KIM::ModelCompute const * const modelCompute,
				     KIM::ModelComputeArguments const * const modelComputeArguments)
{
  AsapKimPotential * modelObject;
  modelCompute->GetModelBufferPointer(reinterpret_cast<void **>(&modelObject));

  return modelObject->Compute(modelCompute, modelComputeArguments);
}

#define MYLOG(x) modelCompute->LogEntry(KIM::LOG_VERBOSITY::error, x, __LINE__, __FILE__)

int AsapKimPotential::Compute(KIM::ModelCompute const * const modelCompute,
			      KIM::ModelComputeArguments const * const modelComputeArguments)
{
  int error;
  assert(potential != NULL);

  // Information from the atoms
  int nAtoms = 0;
  int *nAtoms_p = NULL;
  
  const double *coords = NULL;
  const int *particleSpecies = NULL;
  const int *particleContributing = NULL;

  error =
    modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::numberOfParticles,
					      &nAtoms_p);
  if (error)
  {
    MYLOG("Failed to get number of atoms.");
    return error;
  }
  assert(nAtoms_p != NULL);
  nAtoms = *nAtoms_p;
  assert(nAtoms >= 0);
  
  error =
    modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::coordinates,
					      &coords)
    || modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::particleSpeciesCodes,
						 &particleSpecies)
    || modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::particleContributing,
						 &particleContributing);
  if (error)
  {
    MYLOG("Failed to get coordinates, species or contribution pointer.");
    return error;
  }
  assert(coords != NULL && particleSpecies != NULL && particleContributing != NULL);
  
  // Quantities to be computed
  double *energy = NULL;
  double *forces = NULL;
  double *particleEnergy = NULL;
  double *virial = NULL;
  double *particleVirial = NULL;

  error =
    modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialEnergy,
					      &energy)
    || modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialParticleEnergy,
						 &particleEnergy)
    || modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialForces,
						 &forces);
  if (error)
  {
    MYLOG("Failed to get energy or force pointer.");
    return error;
  }
  if (supportvirial)
  {
    error =(
      modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialVirial,
						&virial)
      || modelComputeArguments->GetArgumentPointer(KIM::COMPUTE_ARGUMENT_NAME::partialParticleVirial,
						 &particleVirial)
      );
    if (error)
    {
      MYLOG("Failed to get virial pointers.");
      return error;
    }
  }

  // Create or update the KIM replacement of the ASAP Atoms access object.
  if (atoms == NULL)
    {
      // First call, create the Atoms interface object
      atoms = new KimAtoms();
      assert(atoms != NULL);
      atoms->ReInit(modelComputeArguments, nAtoms, coords, particleSpecies, particleContributing);
      try {
	potential->SetAtoms(NULL, atoms);
      }
      catch (AsapError &e)
      {
	string msg = e.GetMessage();
	MYLOG(msg.c_str());
	return 1;
      }
    }
  else
    {
      atoms->ReInit(modelComputeArguments, nAtoms, coords, particleSpecies, particleContributing);
    }

  // Now do the actual computation
  try
  {
      if (particleEnergy != NULL)
        {
          const vector<double> &energies_v = potential->GetPotentialEnergies(NULL);
          assert(energies_v.size() == nAtoms);
          for (int i = 0; i < nAtoms; i++)
            particleEnergy[i] = energies_v[i];
        }
      if (energy != NULL)
        *energy = potential->GetPotentialEnergy(NULL);
      if (particleVirial != NULL)
        {
          const vector<SymTensor> &virials = potential->GetVirials(NULL);
          assert(virials.size() == nAtoms);
          const double *virials_ptr = (double *) &virials[0];
          for (int i = 0; i < 6*(nAtoms); i++)
            particleVirial[i] = virials_ptr[i];
        }
      if (virial != NULL)
        {
          SymTensor v = potential->GetVirial(NULL);
          for (int i = 0; i < 6; i++)
            virial[i] = v[i];
        }
      if (forces != NULL)
        {
          const vector<Vec> &forces_v = potential->GetForces(NULL);
          assert(forces_v.size() == nAtoms);
          const double *forces_v_ptr = (double *) &forces_v[0];
          for (int i = 0; i < 3*(nAtoms); i++)
            forces[i] = forces_v_ptr[i];
        }
  }
  catch (AsapError &e)
  {
      string msg = e.GetMessage();
      MYLOG(msg.c_str());
      return 1;
  }
  return 0;
}
