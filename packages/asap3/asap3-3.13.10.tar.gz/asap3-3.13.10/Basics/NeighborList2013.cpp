/*
 * NeighborList2013.cpp
 *
 *  Created on: May 5, 2011
 *      Author: s072162
 */

#include "NeighborList2013.h"
#include "Debug.h"
#include "Atoms.h"
#include <iostream>

NeighborList2013::NeighborList2013(Atoms *a, double rCut, double driftfactor,
    const TinyMatrix<double> &rcut2_NB)
: NeighborList(a, rCut, driftfactor)
{
  rcut2_byz.CopyFrom(rcut2_NB);
};

//// retrieve neighbors based on rcut between the involved atoms (TinyMatrix version)
int NeighborList2013::GetNeighbors(int a1, int *neighbors, Vec *diffs,
    double *diffs2, int& size, double r) const
{
  if (r > 0.0)
    return NeighborList::GetNeighbors(a1, neighbors, diffs, diffs2, size, r);

  if (invalid)
    {
      DEBUGPRINT;
      throw AsapError("NeighborList has been invalidated, possibly by another NeighborList using the same atoms.");
    }

  if (size < nbList[a1].size())
    {
      DEBUGPRINT;
      throw AsapError("NeighborList::GetNeighbors: list overflow.");
    }

  const vector<Vec> &positions = cells->GetWrappedPositions();
  const asap_z_int *z = atoms->GetAtomicNumbers();

  // Need to use GET_CELL instead of GetCell as the atoms are not open
  // when called from the Python interface.
  Vec pos1 = positions[a1];
  int nNeighbors = 0;
  asap_z_int a1Element = z[a1];

  typedef vector<neighboritem_t>::const_iterator iterat;
  iterat terminate = nbList[a1].end();
  if (pbc[0] || pbc[1] || pbc[2])
    {
      // Periodic along at least one direction
      for (iterat a2 = nbList[a1].begin(); a2 < terminate; ++a2)
        {
          // Check to see if the potential neighboring atom should be
          // on the neighbor list of atom a1
          diffs[nNeighbors] = positions[NEIGHBOR_INDEX(*a2)] - pos1
            - translationTable_scaled[NEIGHBOR_XLAT(*a2)];
          diffs2[nNeighbors] = Length2(diffs[nNeighbors]);
          neighbors[nNeighbors] = NEIGHBOR_INDEX(*a2);
          nNeighbors++;
        }
    }
  else
    {
      // Free boundary conditions
      for (iterat a2 = nbList[a1].begin(); a2 < terminate; ++a2)
        {
          // Check to see if the potential neighboring atom should be
          // on the neighbor list of atom a1
          diffs[nNeighbors] = positions[NEIGHBOR_INDEX(*a2)] - pos1;
          diffs2[nNeighbors] = Length2(diffs[nNeighbors]);
          neighbors[nNeighbors] = NEIGHBOR_INDEX(*a2);
          nNeighbors++;
        }
    }
  int j = 0;
  const double *cut2 = rcut2_byz[a1Element];
  for (int i = 0; i < nNeighbors; i++)
    {
      if (i != j)
        {
          diffs[j] = diffs[i];
          diffs2[j] = diffs2[i];
          neighbors[j] = neighbors[i];
        }
      if (diffs2[i] <  cut2[z[neighbors[i]]])
        j++;
    }
  nNeighbors = j;
  size -= nNeighbors;
  ASSERT(size >= 0);
  return nNeighbors;
}

/// PYTHON VERSION!
void NeighborList2013::GetNeighbors(int a1, vector<int> &neighbors) const
{
  if (invalid)
    throw AsapError("NeighborList has been invalidated, possibly by another NeighborList using the same atoms.");

  neighbors.clear();
  const vector<Vec> &positions = cells->GetWrappedPositions();
  const asap_z_int *z = atoms->GetAtomicNumbers();

  Vec pos1 = positions[a1];
  asap_z_int a1Element = z[a1];

  typedef vector<neighboritem_t>::const_iterator iterat;
  iterat terminate = nbList[a1].end();
  for (iterat a2 = nbList[a1].begin(); a2 < terminate; ++a2)
    {
      Vec diff = positions[NEIGHBOR_INDEX(*a2)] - pos1
	- translationTable_scaled[NEIGHBOR_XLAT(*a2)];
      /* Assuming that the problem about accessing the element
       * type has been solved a1/2Element should be substituted
       * with the right command! */
      double d2 = Length2(diff);
      asap_z_int a2Element = z[NEIGHBOR_INDEX(*a2)];
      if (d2 < rcut2_byz[a1Element][a2Element])
	    neighbors.push_back(NEIGHBOR_INDEX(*a2));
    }
}



