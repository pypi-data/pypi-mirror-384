// VelocityVerlet.cpp  --  The Velocity Verlet molecular dynamics algorithm.
// -*- c++ -*-
//
// Copyright (C) 2001-2011 Jakob Schiotz and Center for Individual
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

#include "VelocityVerlet.h"
#include "Potential.h"
#include "DynamicAtoms.h"
//#define ASAPDEBUG
#include "Debug.h"

#include <iostream>

VelocityVerlet::VelocityVerlet(PyObject *py_atoms, Potential *calc, double timestep) :
  MolecularDynamics(py_atoms, calc, timestep)
{
  fixatoms_name = PyUnicode_FromString("FixAtoms_mult_double");
  atomic_masses_name = PyUnicode_FromString("masses");
  ASSERT(fixatoms_name != NULL);  // Probably cannot fail.
}

VelocityVerlet::~VelocityVerlet()
{
  Py_DECREF(fixatoms_name);
  Py_DECREF(atomic_masses_name);
}

void VelocityVerlet::Run2(int nsteps, PyObject *observers, PyObject *self)
{
  //std::cerr << "Thread " << thread << ": steps = " << nsteps << std::endl;
  DEBUGPRINT;

  ParseObservers(observers);
  // Masses:
  //  If no masses on atoms: use invmasses[Z[i]]
  //  Else use explicit_invmasses[i]
  const vector<double> &invmasses = atoms->GetInverseMasses();
  vector<double> explicit_invmasses;
  double halftimestep = 0.5 * timestep;
  bool needcalculation = true;
  const Vec *F;            // Forces
  Vec *r;                  // Positions
  Vec *p;                  // Momenta
  const asap_z_int *Z;     // Atomic numbers
  double *mult;            // Multiplyer implementing FixAtoms constraint
  double *explicit_masses; // Explicit masses, if given.
  DEBUGPRINT;
  for (int n = 0; n < nsteps; n++)  // nsteps-1 steps
    {
      CHECKNOASAPERROR; // Unnecessary paranoia.
      if (needcalculation)
      {
	F = GetForces();  // After first iteration, this normally does nothing as
                          // force is already calculated, but may fix rare trouble.
	r = atoms->GetPositions();
	p = atoms->GetMomenta();
	Z = atoms->GetAtomicNumbers();
	// Get FixAtoms constraint.  If present, this is a multiplyer (0.0 or 1.0).
	mult = atoms->GetDoubleDataMaybe(fixatoms_name);
	// Get explict masses from the atoms, if present.
	explicit_masses = atoms->GetDoubleDataMaybe(atomic_masses_name);
	if (explicit_masses != NULL)
	{
	  explicit_invmasses.resize(nAtoms);
	  for (int i = 0; i < nAtoms; i++)
	    explicit_invmasses[i] = 1.0 / explicit_masses[i];
	}
	DEBUGPRINT;
	needcalculation = false;
      }
      // For performance, we special-case whether mult and explict_invmasses
      // are present.  Four cases.
      if (mult == NULL && explicit_masses == NULL)
        {
#ifdef _OPENMP
#pragma omp parallel for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            {
              p[i] += halftimestep * F[i];
              r[i] += timestep * invmasses[Z[i]] * p[i];  // Position update step n.
            }
        }
      else if (mult == NULL && explicit_masses != NULL)
        {
#ifdef _OPENMP
#pragma omp parallel for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            {
              p[i] += halftimestep * F[i];
              r[i] += timestep * explicit_invmasses[i] * p[i];  // Position update step n.
            }
        }
      else if (mult != NULL && explicit_masses == NULL)
        {
#ifdef _OPENMP
#pragma omp parallel for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            {
              p[i] = mult[i] * (p[i] + halftimestep * F[i]);
              r[i] += timestep * invmasses[Z[i]] * p[i];  // Position update step n.
            }
        }
      else
        {
	  ASSERT(mult != NULL && explicit_masses != NULL);
#ifdef _OPENMP
#pragma omp parallel for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            {
              p[i] = mult[i] * (p[i] + halftimestep * F[i]);
              r[i] += timestep * explicit_invmasses[i] * p[i];  // Position update step n.
            }
        }
      F = GetForces();
      r = atoms->GetPositions();  // May have changed in parallel simulation
      p = atoms->GetMomenta();
      Z = atoms->GetAtomicNumbers();
      mult = atoms->GetDoubleDataMaybe(fixatoms_name);
      if (explicit_masses != NULL)
	{
	  explicit_masses = atoms->GetDoubleDataMaybe(atomic_masses_name);
	  ASSERT(explicit_masses != NULL);
	  explicit_invmasses.resize(nAtoms);
	  for (int i = 0; i < nAtoms; i++)
	    explicit_invmasses[i] = 1.0 / explicit_masses[i];
	}
      if (mult == NULL)
        {
#ifdef _OPENMP
#pragma omp parallel for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            {
              p[i] += halftimestep * F[i];
            }
        }
      else
        {
#ifdef _OPENMP
#pragma omp parallel for
#endif // _OPENMP
          for (int i = 0; i < nAtoms; i++)
            {
              p[i] += halftimestep * F[i] * mult[i];
            }
        }
      steps++;
      needcalculation = CallObservers(self);
      // The observers might change the positions array (e.g. wrapping into box)
      // AND cause a recalculation/migration (saving to Trajectory).
      // so we get new pointers at the beginning of this loop if an observer was called.
    }
  CleanupObservers();
  UpdateStepsInPython(self);
}
