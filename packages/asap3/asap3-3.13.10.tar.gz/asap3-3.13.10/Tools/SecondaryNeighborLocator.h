// -*- C++ -*-
// SecondaryNeighborLocator.h:  Cell-based algorithm for finding neighbors.
//
// Copyright (C) 2008-2015 Jakob Schiotz and Center for Individual
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
//
// The SECONDARY neighbor locator is not intended to be used by a potential.
// It can be used for analysis in situations where there may already be a
// parallel potential having a (primary) neighbor locator.  The secondary
// neighbor locator then uses the primary locator to keep the ghost atoms
// updated.  It is thus an error if the secondary neighbor locator has
// longer range than the primary.  If no primary locator is present, the
// secondary will handle ghost atoms itself, until a primary locator appears
// when/if the user later adds a potential.

#ifndef SECONDARYNEIGHBORLOCATOR
#define SECONDARYNEIGHBORLOCATOR

#include "NeighborCellLocator.h"


namespace ASAPSPACE {


PyAsap_NeighborLocatorObject *PyAsap_NewSecondaryNeighborLocator(Atoms *a,
     double rCut, double driftfactor = 0.05);

class SecondaryNeighborLocator : public NeighborCellLocator
{
protected:
  /// Generate a neighbor list for atoms a with cutoff rCut.

  /// The neighbor list will contain all neighbors within the distance
  /// rCut.  The neighborlist can be reused until an atom has moved
  /// more than rCut*driftfactor.
  SecondaryNeighborLocator(Atoms *a, double rCut, double driftfactor = 0.05) :
    NeighborCellLocator(a, rCut, driftfactor)
  {py_master = NULL;}
  virtual ~SecondaryNeighborLocator() {};

  friend PyAsap_NeighborLocatorObject *PyAsap_NewSecondaryNeighborLocator(
       Atoms *a, double rCut, double driftfactor);

  friend void PyAsap_Finalize<PyAsap_NeighborLocatorObject>(PyObject *self);

public:
  /// Check the neighbor list.
  ///
  /// Check if the neighbor list can still be reused, return true if
  /// it should be updated.  Before checking, check AND UPDATE the master
  /// neighbor list, if present.
  virtual bool CheckNeighborList();

  virtual bool CheckAndUpdateNeighborList(PyObject *atoms_obj);

private:
  PyObject *py_master;

};

} // end namespace

#endif //  SECONDARYNEIGHBORLOCATOR
