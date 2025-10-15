// -*- C++ -*-
//
// asap_kim_api.h: Common interfaces classes for Asap potentials in OpenKIM.
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


#ifndef ASAP_KIM_API_H
#define ASAP_KIM_API_H

#include "KimAtoms.h"
#include "NeighborLocator.h"

namespace ASAPSPACE {

class Potential;

class PotentialKimMixin
{
public:
  // PotentialKimMixin() {};

  virtual int ComputeArgumentsCreate(
    KIM::ModelComputeArgumentsCreate * const modelComputeArgumentsCreate) const = 0;

  // Per default, no ComputeArgumentsDestroy is needed.
  virtual int ComputeArgumentsDestroy(
    KIM::ModelComputeArgumentsDestroy * const modelComputeArgumentsDestroy) const {return 0;}
};  

// AsapKimPotential is the main object that KIM interfaces with.  It
// delegates almost everything to the actual potential, which is both
// an instance of an asap Potential and an instance of
// PotentialKimMixin (multiple inheritance!).
class AsapKimPotential
{
public:
  AsapKimPotential(KIM::ModelDriverCreate * const modelDriverCreate,
		   bool supportvirial);
  virtual ~AsapKimPotential();

  // Set the potential, it must be both a Potential and a PotentialKimMixin.
  void SetPotential(Potential *pot);
  
  static int compute_static(void *km);
  int compute(void *km);

  PyAsap_NeighborLocatorObject *CreateNeighborList(KimAtoms *atoms,
                                                   double cutoff,
                                                   double drift);

private:

  int Compute(KIM::ModelCompute const * const modelCompute,
              KIM::ModelComputeArguments const * const modelComputeArguments);
  
  // The following member functions are static, they are called as
  // functions (not methods of an instance) to set up the API,
  // information about the instance actually being set up is extracted
  // from the first argument.
  static int ComputeArgumentsCreate(
    KIM::ModelCompute const * const modelCompute,
    KIM::ModelComputeArgumentsCreate * const modelComputeArgumentsCreate);

  static int ComputeArgumentsDestroy(
    KIM::ModelCompute const * const modelCompute,
    KIM::ModelComputeArgumentsDestroy * const modelComputeArgumentsDestroy);

  static int Destroy(KIM::ModelDestroy * const modelDestroy);

  static int Compute_static(KIM::ModelCompute const * const modelCompute,
			    KIM::ModelComputeArguments const * const modelComputeArguments);


  
public:
  vector<string> paramfile_names;   // The original parameter file name list.  Possibly used by reinit.
  bool supportvirial;      // This potential supports virials.

private:
  //Data
  Potential *potential;    // The ASAP potential being used
  PotentialKimMixin *potential_as_kimmixin;   // Same potential, different interface.
  KimAtoms *atoms;
  bool need_contrib;
  const char *NBCstr;   // Neighbor list string, kept for error messages.
};

} // end namespace

#endif // not ASAP_KIM_API_H
