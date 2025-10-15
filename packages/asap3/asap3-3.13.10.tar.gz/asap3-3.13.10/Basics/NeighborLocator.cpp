// Copyright (C) 2008-2025 Jakob Schiotz and Center for Individual
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

// This file contains a few common functions for all NeighborLocator objects.

#include "NeighborList.h"
#include "Atoms.h"
#include "ImageAtoms.h"

NeighborLocator::NeighborLocator(Atoms *a) 
{
    invalid=true; 
    verbose=0;
    if (a == NULL)
        atoms = new NormalAtoms();
    else
    {
        atoms = a;
        AsapAtoms_INCREF(atoms);
    }
}

NeighborLocator::~NeighborLocator()
{
    AsapAtoms_DECREF(atoms);
}

int NeighborLocator::GetFullNeighbors(int n, int *neighbors, Vec *diffs,
    double *diffs2, int& size, double r) const
{
    throw AsapError("Internal error: Calling half neighbor locator as a full one.");
}

void NeighborLocator::GetFullNeighbors(int n, vector<int> &neighbors) const
{
    throw AsapError("Internal error: Calling half neighbor locator as a full one.");
}

int NeighborLocator::GetFullNeighborsQuery(Vec &pos, int *neighbors, Vec *diffs,
    double *diffs2, int& size, double r) const
{
    throw AsapError("Internal error: Calling half neighbor locator as a full one.");
}

void NeighborLocator::TranslateImageAtomsMaybe(vector<int> &neighbors) const
{
    ImageAtoms *iat = dynamic_cast<ImageAtoms *>(atoms);
    if (iat != NULL)
    {
        iat->TranslateImageAtoms(neighbors);
    }
}
