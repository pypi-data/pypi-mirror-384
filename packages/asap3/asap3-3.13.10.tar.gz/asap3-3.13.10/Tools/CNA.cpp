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

#include "AsapPython.h"
#include "CNA.h"
#include "Atoms.h"
#include "NeighborList.h"
#include "Vec.h"
#include "Timing.h"
#include "Exception.h"
#include "GetNeighborList.h"
#include "Debug.h"
#include <vector>
using std::vector;

namespace ASAPSPACE {

void CNA(PyObject *py_atoms, double rCut, vector<char> &cna)
{
  DEBUGPRINT;
  USETIMER("CNA");
  // Create a full neighbor list object
  PyObject *py_nblist = GetSecondaryNeighborList(py_atoms, rCut);
  DEBUGPRINT;
  if (py_nblist == NULL)
    throw AsapPythonError();
  NeighborLocator *nl = ((PyAsap_NeighborLocatorObject*) py_nblist)->cobj;
  ASSERT(nl != NULL);
  ASSERT(!nl->IsInvalid());
  Atoms *atoms = nl->GetAtoms();

  DEBUGPRINT;
  atoms->Begin(py_atoms);
  int nAtoms = atoms->GetNumberOfAtoms();
  int nTotal = nAtoms + atoms->GetNumberOfGhostAtoms();
  ASSERT(!nl->IsInvalid());

  vector<int> numFCC(nTotal);
  vector<int> numHCP(nTotal);
  for (unsigned int a2 = 0; a2 < nTotal; a2++)
    {
      vector<int> nbs2;
      DEBUGPRINT;
      nl->GetFullNeighbors(a2, nbs2);
      DEBUGPRINT;
      for (unsigned int n2 = 0; n2 < nbs2.size(); n2++)
        {
          int a1 = nbs2[n2];
          ASSERT(a1 < nTotal);
          if (a1 < a2)
            {
              vector<int> common;
              vector<int> nbs1;
              nl->GetFullNeighbors(a1, nbs1);
              for (unsigned int n1 = 0; n1 < nbs1.size(); n1++)
                {
                  int a3 = nbs1[n1];
                  for (unsigned int m2 = 0; m2 < nbs2.size(); m2++)
                    if (a3 == nbs2[m2])
                      common.push_back(a3);
                }
              if (common.size() == 4)
                {
                  int nBonds = 0;
                  int bondsSum = 0;
                  for (int j2 = 1; j2 < 4; j2++)
                    {
                      vector<int> nbs;
                      nl->GetFullNeighbors(common[j2], nbs);
                      for (unsigned int j1 = 0; j1 < j2; j1++)
                        for (unsigned int n = 0; n < nbs.size(); n++)
                          if (common[j1] == nbs[n])
                            {
                              nBonds++;
                              bondsSum += j1 + j2;
                              break;
                            }
                    }
                  if (nBonds == 2)
                    {
                      if (bondsSum == 6)
                        {
                          numFCC[a1]++;
                          numFCC[a2]++;
                        }
                      else
                        {
                          numHCP[a1]++;
                          numHCP[a2]++;
                        }
                    }
                }
            }
        }
    }
  // 0: fcc (421), 1: hcp (422), 2: other
  DEBUGPRINT;
  cna.resize(nAtoms);
  for (int a = 0; a < nAtoms; a++)
    {
      vector<int> nbs;
      nl->GetFullNeighbors(a, nbs);
      if (nbs.size() == 12)
        {
          if (numFCC[a] == 12)
            cna[a] = 0;
          else if (numFCC[a] == 6 && numHCP[a] == 6)
            cna[a] = 1;
          else
            cna[a] = 2;
        }
      else
        cna[a] = 2;
    }
  atoms->End();
  Py_DECREF(py_nblist);
  DEBUGPRINT;
}

} // end namespace
