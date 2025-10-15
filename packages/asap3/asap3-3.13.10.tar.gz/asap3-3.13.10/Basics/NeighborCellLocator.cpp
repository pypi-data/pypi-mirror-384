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

// Asap:  Copyright (C) 2008 CINF/CAMD and Jakob Schiotz

#include "NeighborCellLocator.h"
#include "Matrix3x3.h"
#include "Atoms.h"
#include "Exception.h"
#include "Timing.h"
//#define ASAPDEBUG
#include "Debug.h"
#include <cstdio>
#include <iostream>
#include <string.h>
using std::cerr;
using std::endl;
using std::flush;


// Choose between 3x3x3 and 5x5x5 search patterns.
#undef PATTERN5

#define TESTOPTIM

NeighborCellLocator::NeighborCellLocator(Atoms *a, double rCut,
					 double driftfactor) : NeighborLocator(a)
{
  CONSTRUCTOR;
  DEBUGPRINT;
  this->rCut = rCut;
  includeghostneighbors = false;  // Only true in SecondaryNeighborLocator
  rCut2 = rCut * rCut;
#ifdef PATTERN5
  minboxsize = (1 + 2.0 * driftfactor) * rCut / 2.0;
#else
  minboxsize = (1 + 2.0 * driftfactor) * rCut;
#endif
  nCells[0] = nCells[1] = nCells[2] = 0;
  nTotalCells[0] = nTotalCells[1] = nTotalCells[2] = nTotalCells[3] = 0;
  nCellsTrue[0] = nCellsTrue[1] = nCellsTrue[2] = 0;
  nCellsGapStart[0] = nCellsGapStart[1] = nCellsGapStart[2] = 0;
  nCellsGapSize[0] = nCellsGapSize[1] = nCellsGapSize[2] = 0;
  invalid = true;
  scaledPositionsValid = false;
  wrappedPositionsValid = false;
  supercell_counter = 0;
  MakeTranslationTable();
  DEBUGPRINT;
}

NeighborCellLocator::~NeighborCellLocator()
{
  DESTRUCTOR;
  DEBUGPRINT;
  for (int i = 0; i < nbCells_onthefly.size(); ++i)
    delete nbCells_onthefly[i];
  nbCells_onthefly.clear();
  DEBUGPRINT;
}

void NeighborCellLocator::EnableNeighborsOfGhosts()
{
  invalid = true;
  includeghostneighbors = true;
}

void NeighborCellLocator::MakeTranslationTable()
{
  DEBUGPRINT;
  translationTable.resize(27);
  for (int i = 0; i < 3; i++)
    for (int j = 0; j < 3; j++)
      for (int k = 0; k < 3; k++)
	translationTable[i + 3*j + 9*k] = IVec(i == 2 ? -1 : i,
					       j == 2 ? -1 : j,
					       k == 2 ? -1 : k);
  DEBUGPRINT;
}

void NeighborCellLocator::MakeList()
{
  RETURNIFASAPERROR;
  DEBUGPRINT;
  MEMORY;
  USETIMER("NeighborCellLocator::MakeList");
  if (verbose >= 1)
    cerr << " NeighborCellLocator-Update ";
  nAtoms = atoms->GetNumberOfAtoms();
  nAllAtoms = nAtoms + atoms->GetNumberOfGhostAtoms();
  if (includeghostneighbors)
    nAtoms = nAllAtoms;
  /// Update positions and scaledpositions
  ScaleAndNormalizePositions();
  ASSERT(scaledPositions.size() == nAllAtoms);
  MEMORY;

  // If there are no atoms, we just make empty arrays and return
  if (nAllAtoms == 0)
  {
    cellIndices.resize(0);
    maxLength = 0.0;
    invalid = false;
    DEBUGPRINT;
    return;   // Nothing to do.
  }
  
  DEBUGPRINT;
  const double *cellHeights = atoms->GetCellHeights();
  const bool *atomsperiodic = atoms->GetBoundaryConditions();
  for (int i = 0; i < 3; i++)
    periodic[i] = atomsperiodic[i];
  // Check the size.  As this locator does not use minimum image
  // convention, we can allow height down to rCut rather than the
  // usual 2*rCut.
  for (int i = 0; i < 3; i++)
    if (periodic[i] && cellHeights[i] < rCut)
      THROW( AsapError("NeighborCellLocator: The height of the cell (")
        << cellHeights[i] << ") must be larger than " << rCut );

  const vector<Vec> &UNUSED(positions) = GetWrappedPositions();
  const vector<Vec> &scaledpositions = GetScaledPositions();

  MEMORY;
  // Find the system size in scaled space coordinates.  Use this to
  // determine the number of cells.  If this processor only handles
  // part of space in a periodic direction, we must search for a range
  // of coordinates not present (it will be found on the outermost
  // processors where ghosts from the other side of the simulation
  // cell appear).  This is used to massively cut down on the memory
  // consumption.
  IVec cpulayout = atoms->GetNumberOfCells();
  bool cellLayoutChanged = false;
  for (int i = 0; i < 3; i++)
    {
      bool lookforgap = periodic[i] && cpulayout[i] > 1;
      bool gapvalid = false;
      double gaplow;
      double gaphigh;    
      if (periodic[i] && cpulayout[i] == 1)
	{
	  // Periodic boundary conditions, use whole axis
	  size[i] = 1.0;
	  minimum[i] = 0.0;
	} 
      else if (lookforgap)
	{
	  // Periodic boundary conditions, use part of the axis (parallel sim).
	  double gap1start = 0.25;
	  double gap2start = 0.75;
	  double gap1low = -1.0;
	  double gap1hi = 2.0;
	  double gap2low = -1.0;
	  double gap2hi = 2.0;
	  bool gap1below = false;
	  bool gap1above = false;
	  bool gap2below = false;
	  bool gap2above = false;
	  double min, max;
	  min = max = scaledpositions[0][i];
	  for (int a = 1; a < nAllAtoms; a++)
	    {
	      double x = scaledpositions[a][i];
	      if (x > max)
		max = x;
	      else if (x < min)
		min = x;
	      if (x < gap1start && x > gap1low)
		{
		  gap1low = x;
		  gap1below = true;
		}
	      else if (x > gap1start && x < gap1hi)
		{
		  gap1hi = x;
		  gap1above = true;
		}
	      if (x < gap2start && x > gap2low)
		{
		  gap2low = x;
		  gap2below = true;
		}
	      else if (x > gap2start && x < gap2hi)
		{
		  gap2hi = x;
		  gap2above = true;
		} 
	    }
	  minimum[i] = min;
	  size[i] = max - min;
#if 0
	  cerr << "GAP: " << gap1below << " " << gap1above << " "
	       << gap1low << " " << gap1hi << " --- "
	       << gap2below << " " << gap2above << " "
	       << gap2low << " " << gap2hi << endl;
#endif
	  gapvalid = false;
	  if (gap1below && gap1above)
	    {
	      gapvalid = true;
	      gaplow = gap1low;
	      gaphigh = gap1hi;
	    }
	  if (gap2below && gap2above &&
	      (!gapvalid || (gap2hi - gap2low > gap1hi - gap1low)))
	    {
	      gapvalid = true;
	      gaplow = gap2low;
	      gaphigh = gap2hi;
	    }
	}
      else
	{
	  // Free boundary conditions.
	  // Could be merged with section above, but if statements in
	  // loops hurt performance.
	  double min, max;
	  min = max = scaledpositions[0][i];
	  for (int a = 1; a < nAllAtoms; a++)
	    {
	      double x = scaledpositions[a][i];
	      if (x > max)
		max = x;
	      else if (x < min)
		min = x;
	    }
	  minimum[i] = min;
	  size[i] = max - min;
	}
      minimum[i] -= 1e-4;
      size[i] += 2e-4;
      int nc = int(size[i] * cellHeights[i] / minboxsize);
      int gapstart, gapsize;
      if (gapvalid)
	{
	  gapstart = int(ceil(nc * (gaplow - minimum[i]) / size[i])) + 2;
	  int gapend = int(floor(nc * (gaphigh - minimum[i]) / size[i])) - 2;
	  gapsize = gapend - gapstart;
	  if (gapsize < 3)
	    {
	      gapsize = 0;
	      gapstart = nc + 1;
	    }
	}
      else
	{
	   gapsize = 0;
	   gapstart = nc + 1;
	}
      if (nc == 0)
	{
	  nc = 1;
	  minimum[i] -= 0.5 * (minboxsize / cellHeights[i] - size[i]);
	  size[i] = minboxsize / cellHeights[i];
	}      
      if (nCells[i] != nc - gapsize || nCellsTrue[i] != nc
	  || nCellsGapStart[i] != gapstart || nCellsGapSize[i] != gapsize)
	{
	  nCells[i] = nc - gapsize;
	  nCellsTrue[i] = nc;
	  nCellsGapStart[i] = gapstart;
	  nCellsGapSize[i] = gapsize;
	  cellLayoutChanged = true;
#if 0
	  cerr << "Axis " << i << "(pbc:" << periodic[i] << ") nCells="
	       << nCells[i] << "  (gap: " << gapstart << ", " << gapsize
	       << ")" << "  minimum: " << minimum[i] << " size: "
	       << size[i] << endl;
#endif
	}
    }
  nTotalCells[0] = 1;
  for (int i = 0; i < 3; i++)
    nTotalCells[i + 1] = nTotalCells[i] * nCells[i];

  if (verbose >= 2)
    cerr << endl << "nNeighborCellLocator: " << nAtoms << " atoms, " 
	 << nCells[0] << "*" << nCells[1] << "*" << nCells[2] << " = " 
	 << nTotalCells[3] << " cells, " 
	 << nAtoms / (double) nTotalCells[3] << " atoms/cell" << endl;
  // Now check if the boundary conditions have changed
  for (int i = 0; i < 3; i++)
    {
      if (periodic[i] != oldperiodic[i])
	cellLayoutChanged = true;
      oldperiodic[i] = periodic[i];
    }

  MEMORY;
  // Now reallocate the cell list, if its size has changed
  if (cellLayoutChanged || (cells.size() != nTotalCells[3]))
    {
      // Clear the old cells, create new ones.
      cells.clear();
      cells.resize(nTotalCells[3]);
      MEMORY;
      MakeNeighboringCellLists();
    }
  else
    {
      // Empty the old cells, but keep them to minimize reallocations
      ASSERT(cells.size() == nTotalCells[3]);
      for (int i = 0; i < cells.size(); i++)
	cells[i].clear();
    }
  MEMORY;
  cellIndices.resize(nAllAtoms);
  MEMORY;

  // Now we are ready to put the atoms into the cells!
  for (int a = 0; a < nAllAtoms; a++)
    {
      int index = 0;
      for (int i = 0; i < 3; i++)
	{
	  int k =
	    int((scaledpositions[a][i] - minimum[i]) / size[i] * nCellsTrue[i]);
	  ASSERT(k >= 0);
	  if (k > nCellsGapStart[i])
	    {
	      ASSERT (k > nCellsGapStart[i] + nCellsGapSize[i]);
	      k -= nCellsGapSize[i];
	    }
	  if (k == nCells[i])
	    k--;
          ASSERT(k < nCells[i]);
	  index += nTotalCells[i] * k;
	}
      cells[index].push_back(a);
      cellIndices[a] = index;
    }

  // update reference positions for neighbor list:
  atoms->GetPositions(referencePositions);
  MEMORY;

  // Find the largest cell size, and use it to calculate the max length
  maxLength = 0;
  for (int i = 0; i < cells.size(); i++)
    {
      int x = cells[i].size();
      if (x > maxLength)
	maxLength = x;
    }
#ifdef PATTERN5
  maxLength *= 5*5*5;
#else
  maxLength *= 3*3*3;
#endif
  invalid = false;
  DEBUGPRINT;
  MEMORY;
}

void NeighborCellLocator::MakeNeighboringCellLists()
{
  DEBUGPRINT;

#ifdef PATTERN5
  int dx = 2;
#else
  int dx = 1;
#endif
  neighborCellOffsets.clear();
  for (int i = -dx; i <= dx; i++)
    for (int j = -dx; j <= dx; j++)
      for (int k = -dx; k <= dx; k++)
	neighborCellOffsets.push_back(IVec(i,j,k));

  nbCells_inside.clear();
  nbCells_left.clear();
  nbCells_right.clear();
  nbCells_top.clear();
  nbCells_bottom.clear();
  nbCells_front.clear();
  nbCells_back.clear();
  for(vector<IVec>::const_iterator nb = neighborCellOffsets.begin();
      nb != neighborCellOffsets.end(); ++nb)
    {
      IVec idx = *nb;
      IVec magic(1,3,9);
      // inside
      pair<int, translationsidx_t> data0;
      pair<int, translationsidx_t> data;
      data0.first = idx[0] + idx[1] * nTotalCells[1]
	+ idx[2] * nTotalCells[2];
      data0.second = 0;
      nbCells_inside.push_back(data0);
      // left side
      data = data0;
      if (idx[0] != -1)
	nbCells_left.push_back(data);
      else if (periodic[0])
	{
	  data.first += nCells[0];
	  data.second = 1 * magic[0];
	  nbCells_left.push_back(data);
	}
      // right side
      data = data0;
      if (idx[0] != 1)
	nbCells_right.push_back(data);
      else if (periodic[0])
	{
	  data.first -= nCells[0];
	  data.second = 2 * magic[0];
	  nbCells_right.push_back(data);
	}
      // bottom
      data = data0;
      if (idx[1] != -1)
	nbCells_bottom.push_back(data);
      else if (periodic[1])
	{
	  data.first += nTotalCells[2];
	  data.second = 1 * magic[1];
	  nbCells_bottom.push_back(data);
	}
      // top
      data = data0;
      if (idx[1] != 1)
	nbCells_top.push_back(data);
      else if (periodic[1])
	{
	  data.first -= nTotalCells[2];
	  data.second = 2 * magic[1];
	  nbCells_top.push_back(data);
	}
      // front
      data = data0;
      if (idx[2] != -1)
	nbCells_front.push_back(data);
      else if (periodic[2])
	{
	  data.first += nTotalCells[3];
	  data.second = 1 * magic[2];
	  nbCells_front.push_back(data);
	}
      // back
      data = data0;
      if (idx[2] != 1)
	nbCells_back.push_back(data);
      else if (periodic[2])
	{
	  data.first -= nTotalCells[3];
	  data.second = 2 * magic[2];
	  nbCells_back.push_back(data);
	}
    }
  DEBUGPRINT;
  //std::cerr << "************** cells.size(): " << cells.size() << std::endl;
  // Make the corner cases (literally!), and build the map
  nbCells_all.clear();
  for (int i = 0; i < nbCells_onthefly.size(); ++i)
    delete nbCells_onthefly[i];
  nbCells_onthefly.clear();
  for (int i = 0; i < cells.size(); i++)
    makeNbCells(i);
  ASSERT(nbCells_all.size() == cells.size());
}

int NeighborCellLocator::GetNeighbors(int a1, int *neighbors, Vec *diffs,
				      double *diffs2, int& size,
				      double r) const
{
  return CommonGetNeighbors(a1, neighbors, diffs, diffs2, size, r, false);
}

void NeighborCellLocator::GetNeighbors(int a1, vector<int> &neighbors) const
{
  CommonGetNeighbors(a1, neighbors, false);
}

int NeighborCellLocator::GetFullNeighbors(int a1, int *neighbors, Vec *diffs,
					  double *diffs2, int& size,
					  double r) const
{
  return CommonGetNeighbors(a1, neighbors, diffs, diffs2, size, r, true);
}


void NeighborCellLocator::GetFullNeighbors(int a1, vector<int> &neighbors) const
{
  CommonGetNeighbors(a1, neighbors, true);
}


int NeighborCellLocator::GetFullNeighborsQuery(Vec &position, int *neighbors, Vec *diffs, double *diffs2,
                          int& nb_size, double r) const
{
  if (invalid)
    throw AsapError("NeighborCellLocator has been invalidated, possibly by another NeighborList using the same atoms.") << __LINE__;

  const vector<Vec> &RESTRICT positions = GetWrappedPositions();
  // Need to use GET_CELL instead of GetCell as the atoms are not open
  // when called from the Python interface.
  const Vec *RESTRICT superCell = atoms->GET_CELL();

  // Normalize position
  Vec wrapped_scaled_position;
  Vec wrappedpos;
  ScaleAndNormalizePosition(position, &wrapped_scaled_position, &wrappedpos);

  // Find the cell of this atom
  int index = 0;
  for (int i = 0; i < 3; i++)
  {
    int k =
      int((wrapped_scaled_position[i] - minimum[i]) / size[i] * nCellsTrue[i]);
    if (k > nCellsGapStart[i])
    {
      ASSERT (k > nCellsGapStart[i] + nCellsGapSize[i]);
      k -= nCellsGapSize[i];
    }

    // When boundaries are free, k may be outside our cell range
    // We snap k back to the nearest cell and search from there
    // In principle we could stop the search here 
    // if k <= -2 or k > nCells[i]+1
    if (k >= nCells[i])
    {
      k = nCells[i]-1;
    }
    else if (k < 0)
    {
      k = 0;
    }
    index += nTotalCells[i] * k;
  }
  int thiscell = index;

  double rC2;
  if (r > 0.0)
    rC2 = r*r;
  else
    rC2 = rCut2;

  int nNeighbors = 0;

  // Ghost atoms have no neighbors - but they are neighbors to real atoms.
  const nbcell_t *neighborCells = nbCells_all.at(thiscell);

  // Loop over all neighboring cells, including this one
  for (vector< pair<int, translationsidx_t> >::const_iterator i =
      neighborCells->begin(); i < neighborCells->end(); ++i)
  {
    int othcell = i->first + thiscell;
    IVec celltranslation = translationTable[i->second];
    Vec pos1 = wrappedpos + celltranslation[0] * superCell[0] +
      celltranslation[1] * superCell[1] + celltranslation[2] * superCell[2];
    // Loop over all atoms in the cell.
    vector<int>::const_iterator aend = cells[othcell].end();

    for (vector<int>::const_iterator a2 = cells[othcell].begin();
        a2 < aend; ++a2)
    {
      diffs[nNeighbors] = positions[*a2] - pos1;
      diffs2[nNeighbors] = Length2(diffs[nNeighbors]);
      neighbors[nNeighbors] = *a2;
      nNeighbors++;
    }
  }
  // Remove neighbors too far away
  int j = 0;
  for (int i = 0; i < nNeighbors; i++)
  {
    int a2 = neighbors[i];
    if (i != j)
    {
      diffs[j] = diffs[i];
      diffs2[j] = diffs2[i];
      neighbors[j] = a2;
    }
    if (diffs2[i] < rC2)
      j++;
  }
  nNeighbors = j;
  nb_size -= nNeighbors;
  ASSERT(nb_size >= 0);
  return nNeighbors;
}


void NeighborCellLocator::makeNbCells(int thiscell)
{
  IVec cellidx(thiscell % nTotalCells[1],
	       (thiscell % nTotalCells[2]) / nTotalCells[1],
	       thiscell / nTotalCells[2]);
  ASSERT(thiscell == (cellidx[0] * nTotalCells[0] +
		      cellidx[1] * nTotalCells[1] +
		      cellidx[2] * nTotalCells[2]));
  int celltype = (cellidx[0] == 0) + 2 * (cellidx[0] == nCells[0]-1)
    + 4 * (cellidx[1] == 0) + 8 * (cellidx[1] == nCells[1]-1)
    + 16 * (cellidx[2] == 0) + 32 * (cellidx[2] == nCells[2]-1);

  if (celltype == 0)
    nbCells_all[thiscell] = &nbCells_inside;
  else if (celltype == 1)
    nbCells_all[thiscell] =  &nbCells_left;
  else if (celltype == 2)
    nbCells_all[thiscell] =  &nbCells_right;
  else if (celltype == 4)
    nbCells_all[thiscell] =  &nbCells_bottom;
  else if (celltype == 8)
    nbCells_all[thiscell] =  &nbCells_top;
  else if (celltype == 16)
    nbCells_all[thiscell] =  &nbCells_front;
  else if (celltype == 32)
    nbCells_all[thiscell] =  &nbCells_back;
  else
    {
      // Edge or corner cell - make it on the fly.
      nbcell_t *NbCells = new nbcell_t;
      nbCells_onthefly.push_back(NbCells);
      NbCells->clear();
      nbCells_all[thiscell] = NbCells;

      for (vector<IVec>::const_iterator i = neighborCellOffsets.begin();
	   i != neighborCellOffsets.end(); ++i)
	{
	  IVec othercell = cellidx + *i;
	  translationsidx_t xlat = 0;
	  IVec xlatvec(0,0,0);
	  IVec magic(1,3,9);
	  bool ok = true;
	  for (int j = 0; j < 3; j++)
	    {
	      if (othercell[j] < 0)
		{
		  if (!periodic[j])
		    {
		      ok = false;
		      break;
		    }
		  othercell[j] += nCells[j];
		  //std::cerr << "*** Magic j=" << j << ": " << magic[j] << std::endl;
		  xlat += magic[j] * 1;
		  xlatvec[j] = 1;
		}
	      else if (othercell[j] >= nCells[j])
		{
		  if (!periodic[j])
		    {
		      ok = false;
		      break;
		    }
		  othercell[j] -= nCells[j];
		  //std::cerr << "*** Magic j=" << j << ": " << magic[j] << std::endl;
		  xlat += magic[j] * 2;
		  xlatvec[j] = -1;
		}
	      //std::cerr << xlat << "  ";
	    }
	  if (ok) {
	    //std::cerr << xlatvec << " ==?== " << xlat << ": " << translationTable[xlat] << std::endl;
	    ASSERT(xlatvec == translationTable.at(xlat));
	    pair<int, translationsidx_t> data;
	    data.first = (othercell[0] * nTotalCells[0] +
			  othercell[1] * nTotalCells[1] +
			  othercell[2] * nTotalCells[2]) - thiscell;
	    data.second = xlat;
	    NbCells->push_back(data);
	  }
	}
    }
}

int NeighborCellLocator::CommonGetNeighbors(int a1, int *RESTRICT neighbors, Vec *RESTRICT diffs,
					    double *RESTRICT diffs2, int& size,
					    double r, bool wantfull) const
{
  if (invalid)
    throw AsapError("NeighborCellLocator has been invalidated, possibly by another NeighborList using the same atoms.")  << __LINE__;

  const vector<Vec> &RESTRICT positions = GetWrappedPositions();
  // Need to use GET_CELL instead of GetCell as the atoms are not open
  // when called from the Python interface.
  const Vec *RESTRICT superCell = atoms->GET_CELL();

  // Find the cell of this atom
  int thiscell = cellIndices[a1];
  double rC2;
  if (r > 0.0)
    rC2 = r*r;
  else
    rC2 = rCut2;

  int nNeighbors = 0;

  // Ghost atoms have no neighbors - but they are neighbors to real atoms.
  if (a1 < nAtoms)
    {
      const nbcell_t *neighborCells = nbCells_all.at(thiscell);

      // Loop over all neighboring cells, including this one
      for (vector< pair<int, translationsidx_t> >::const_iterator i =
          neighborCells->begin(); i < neighborCells->end(); ++i)
        {
          int othcell = i->first + thiscell;
          IVec celltranslation = translationTable[i->second];
          Vec pos1 = positions[a1] + celltranslation[0] * superCell[0] +
              celltranslation[1] * superCell[1] + celltranslation[2] * superCell[2];
          // Loop over all atoms in the cell.
          vector<int>::const_iterator aend = cells[othcell].end();

          for (vector<int>::const_iterator a2 = cells[othcell].begin();
              a2 < aend; ++a2)
            {
              diffs[nNeighbors] = positions[*a2] - pos1;
              diffs2[nNeighbors] = Length2(diffs[nNeighbors]);
              neighbors[nNeighbors] = *a2;
              nNeighbors++;
            }
        }
    }
  // Remove neighbors too far away
  int j = 0;
  for (int i = 0; i < nNeighbors; i++)
    {
      int a2 = neighbors[i];
      if (i != j)
        {
          diffs[j] = diffs[i];
          diffs2[j] = diffs2[i];
          neighbors[j] = a2;
        }
      if ((diffs2[i] < rC2) && ((a2 > a1) || (wantfull && (a2 != a1))))
        j++;
    }
  nNeighbors = j;
  size -= nNeighbors;
  ASSERT(size >= 0);
  return nNeighbors;
}

void NeighborCellLocator::CommonGetNeighbors(int a1, vector<int> &neighbors,
					     bool wantfull) const
{
  if (invalid)
    throw AsapError("NeighborCellLocator has been invalidated, possibly by another NeighborList using the same atoms.") << __LINE__;
  
  const vector<Vec> &positions_x = GetWrappedPositions();
  const Vec *RESTRICT superCell = atoms->GET_CELL();

  // Find the cell of this atom
  int thiscell = cellIndices[a1];
  neighbors.resize(maxLength);
  // vector<double> d2(maxLength);
  double *RESTRICT d2 = new double[maxLength];
  int n = 0;

  const Vec *RESTRICT positions = &positions_x[0];
  int *RESTRICT neighbors_p = &neighbors[0];

  const IVec *translationTable = &(this->translationTable)[0];
  // Ghost atoms have no neighbors - but they are neighbors to real atoms.
  if (a1 < nAtoms)
    {
      const nbcell_t *neighborCells = nbCells_all.at(thiscell);

      // Loop over all neighboring cells, including this one
      vector< pair<int, translationsidx_t> >::const_iterator end =  neighborCells->end();
      for (vector< pair<int, translationsidx_t> >::const_iterator i =
             neighborCells->begin(); i < end; ++i)
        {
          int othcell = i->first + thiscell;
          IVec celltranslation = translationTable[i->second];
          Vec pos1 = positions[a1] + celltranslation[0] * superCell[0] +
            celltranslation[1] * superCell[1] + celltranslation[2] * superCell[2];
          // Loop over all atoms in the cell.
          vector<int>::const_iterator aend = cells[othcell].end();
          for (vector<int>::const_iterator a2 = cells[othcell].begin();
               a2 < aend; ++a2)
            {
              Vec diff = positions[*a2] - pos1;
              d2[n] = Length2(diff);
              neighbors_p[n] = *a2;
              n++;
            }
        }
    }
  // Remove neighbors too far away
  int j = 0;
  for (int i = 0; i < n; i++)
    {
      int a2 = neighbors[i];
      if (i != j)
        neighbors[j] = a2;
      if ((d2[i] < rCut2) && ((a2 > a1) || (wantfull && (a2 != a1))))
        j++;
    }
  neighbors.resize(j);
  delete[] d2;
}

int NeighborCellLocator::GetListAndTranslations(int a1,
       vector<neighboritem_t> &neighbors) const
{
  if (invalid)
    THROW( AsapError("NeighborCellLocator has been invalidated, possibly by another NeighborList using the same atoms.") << __LINE__);
  RETURNIFASAPERROR2(0);
  
  const vector<Vec> &positions = GetWrappedPositions();
  const Vec *superCell = atoms->GetCell();

  // Find the cell of this atom
  int thiscell = cellIndices[a1];
  double rC2 = rCut2;

  neighbors.clear();
  // Ghost atoms have no neighbors - but they are neighbors to real atoms.
  if (a1 < nAtoms)
    {
      const nbcell_t *neighborCells = nbCells_all.at(thiscell);

      // Loop over all neighboring cells, including this one
      for (vector< pair<int, translationsidx_t> >::const_iterator i =
             neighborCells->begin(); i < neighborCells->end(); ++i)
        {
          int othcell = i->first + thiscell;
          IVec celltranslation = translationTable[i->second];
          Vec pos1 = positions[a1] + celltranslation[0] * superCell[0] +
            celltranslation[1] * superCell[1] + celltranslation[2] * superCell[2];
          // Loop over all atoms in the cell.
          vector<int>::const_iterator aend = cells[othcell].end();
          for (vector<int>::const_iterator a2 = cells[othcell].begin();
               a2 < aend; ++a2)
            {
              double l2;
              if ((*a2 > a1) && ((l2 = Length2(positions[*a2] - pos1)) < rC2))
                {
    #ifdef SLOWASSERT
                  if (l2 < 1e-6)
                    THROW( AsapError("XX Collision between atoms ") << a1 << " and " << *a2 );
    #endif
                  //neighboritem_t data(*a2, i->second);
		  neighboritem_t NEIGHBORITEM_PACK(data, *a2, i->second);
                  neighbors.push_back(data);
                }
            }
        }
    }
  return neighbors.size();
}  

int NeighborCellLocator::GetComplementaryListAndTranslations(int a1,
       vector<neighboritem_t> &neighbors) const
{
  RETURNIFASAPERROR2(0);
  if (invalid)
    THROW( AsapError("NeighborCellLocator has been invalidated, possibly by another NeighborList using the same atoms.") << __LINE__ );
  
  const vector<Vec> &positions = GetWrappedPositions();
  const Vec *superCell = atoms->GetCell();

  // Find the cell of this atom
  int thiscell = cellIndices[a1];
  double rC2 = rCut2;

  neighbors.clear();

  // Ghost atoms have no neighbors - but they are neighbors to real atoms.
  if (a1 < nAtoms)
    {
      const nbcell_t *neighborCells = nbCells_all.at(thiscell);

      // Loop over all neighboring cells, including this one
      for (vector< pair<int, translationsidx_t> >::const_iterator i =
             neighborCells->begin(); i < neighborCells->end(); ++i)
        {
          int othcell = i->first + thiscell;
          IVec celltranslation = translationTable[i->second];
          Vec pos1 = positions[a1] + celltranslation[0] * superCell[0] +
            celltranslation[1] * superCell[1] + celltranslation[2] * superCell[2];
          // Loop over all atoms in the cell.
          vector<int>::const_iterator aend = cells[othcell].end();
          for (vector<int>::const_iterator a2 = cells[othcell].begin();
               a2 < aend; ++a2)
            {
              if ((*a2 < a1) && (Length2(positions[*a2] - pos1) < rC2))
                {
                  //neighboritem_t data(*a2, i->second);
		  neighboritem_t NEIGHBORITEM_PACK(data, *a2, i->second);
                  neighbors.push_back(data);
                }
            }
        }
    }
  return neighbors.size();
}  

double NeighborCellLocator::get_drift() const
{
  // Find the max allowed drift of an atom.
  const double *superCellHeight = atoms->GetCellHeights();
  double height = superCellHeight[0]/nCellsTrue[0];
  for (int i = 1; i < 3; i++)
    {
      double h = superCellHeight[i]/nCellsTrue[i];
      if (h < height)
	height = h;
    }
#ifdef PATTERN5
  return 0.5 * (2 * height - rCut);
#else
  return 0.5 * (height - rCut);
#endif
}

bool NeighborCellLocator::CheckNeighborList()
{
  DEBUGPRINT;
  USETIMER("NeighborCellLocator::CheckNeighborList");

  const bool *newpbc = atoms->GetBoundaryConditions();
  if (nAtoms != atoms->GetNumberOfAtoms() || oldperiodic[0] != newpbc[0]
      || oldperiodic[1] != newpbc[1] || oldperiodic[2] != newpbc[2])
    invalid = true;

  if (invalid)
      return true;   // An invalid neighbor list always need an update!

  RenormalizePositions();

  double drift = get_drift();
  double drift2 = drift * drift;
  bool updateRequired = invalid;
  const Vec *positions = atoms->GetPositions();
  
  if (!updateRequired)
    for (int n = 0; n < nAtoms; n++)
      if (Length2(positions[n] - referencePositions[n]) > drift2)
	{
	  updateRequired = true;
	  //break;   // prevents vectorization
	}
  // If we are NOT going to update the list, we need to update wrapped positions
  DEBUGPRINT;
  return updateRequired;
}
  
void NeighborCellLocator::UpdateNeighborList()
{
  RETURNIFASAPERROR;
  DEBUGPRINT;
  USETIMER("NeighborCellLocator::UpdateNeighborList");
  if (invalid && verbose)
    cerr << "NeighborCellLocator::UpdateNeighborList: NBList has been marked invalid." << endl;

  MakeList();
  DEBUGPRINT;
}

bool NeighborCellLocator::CheckAndUpdateNeighborList()
{
  DEBUGPRINT;
  bool update = CheckNeighborList();
  if (update)
    UpdateNeighborList();
  DEBUGPRINT;
  return update;
}

bool NeighborCellLocator::CheckAndUpdateNeighborList(PyObject *atoms_obj)
{
  atoms->Begin(atoms_obj);
  CHECKNOASAPERROR;
  bool res = CheckAndUpdateNeighborList();
  PROPAGATEASAPERROR;
  atoms->End();
  return res;
}

void NeighborCellLocator::GetTranslationTable(vector<IVec> &table) const
{
  DEBUGPRINT;
  table.clear();
  table.insert(table.begin(), translationTable.begin(), translationTable.end());
  DEBUGPRINT;
}

#if 0
void NeighborCellLocator::RenormalizeReferencePositions(const vector<Vec>
							&oldpos)
{
  if (!invalid)
    {
      int n = atoms->GetNumberOfAtoms();
      ASSERT(referencePositions.size() == n);
      const Vec *pos = atoms->GetPositions();
      for (int i = 0; i < n; ++i)
	referencePositions[i] += pos[i] - oldpos[i];
    }
}
#endif

const vector<Vec> &NeighborCellLocator::GetScaledPositions() const
{
  DEBUGPRINT;
  ASSERT(scaledPositionsValid);
  return scaledPositions;
}

void NeighborCellLocator::ScaleAndNormalizePositions()
{
  DEBUGPRINT;
  atoms->GetScaledPositions(scaledPositions, true);  // Get also ghosts
  ASSERT(scaledPositions.size() == nAllAtoms);
  const bool *pbc = atoms->GetBoundaryConditions();
  // Special-case fully periodic and fully free boundaries
  if (pbc[0] && pbc[1] && pbc[2])
    {
      // Fully periodic boundaries
      int spsz = scaledPositions.size();
      if (wrappedPositions.capacity() < spsz)
	wrappedPositions.reserve(spsz + spsz / 25);
      wrappedPositions.resize(spsz);
      if (offsetPositions.capacity() < spsz)
	offsetPositions.reserve(spsz + spsz / 25);
      offsetPositions.resize(scaledPositions.size());
      scaledOffsetPositions.clear();  // Not used
      const Vec *pos = atoms->GetPositions();
      const Vec *cell = atoms->GetCell();
      int n = scaledPositions.size();
      Vec *RESTRICT scaledPositions = &(this->scaledPositions)[0];   // Helps vectorization
      Vec *RESTRICT wrappedPositions = &(this->wrappedPositions)[0];
      Vec *RESTRICT offsetPositions = &(this->offsetPositions)[0];
      for (int i = 0; i < n; i++)
	{
	  scaledPositions[i][0] -= floor(scaledPositions[i][0]);
	  scaledPositions[i][1] -= floor(scaledPositions[i][1]);
	  scaledPositions[i][2] -= floor(scaledPositions[i][2]);
	  wrappedPositions[i] = cell[0] * scaledPositions[i][0]
	    + cell[1] * scaledPositions[i][1]
	    + cell[2] * scaledPositions[i][2];
	  offsetPositions[i] = wrappedPositions[i] - pos[i];
	}
      scaledPositionsValid = wrappedPositionsValid = true;
    }
  else if (!pbc[0] && !pbc[1] && !pbc[2])
    {
      // Fully free boundaries: wrappedPositions are the positions
      atoms->GetPositions(wrappedPositions, true);
      offsetPositions.clear();
      scaledOffsetPositions.clear();
      scaledPositionsValid = wrappedPositionsValid = true;
    }
  else
    {
      // Mixed boundary conditions
      double xpbc0 = (double) pbc[0];
      double xpbc1 = (double) pbc[1];
      double xpbc2 = (double) pbc[2];
      int spsz = scaledPositions.size();
      if (wrappedPositions.capacity() < spsz)
	wrappedPositions.reserve(spsz + spsz / 25);
      wrappedPositions.resize(spsz);
      if (scaledOffsetPositions.capacity() < spsz)
	scaledOffsetPositions.reserve(spsz + spsz / 25);
      scaledOffsetPositions.resize(scaledPositions.size());
      offsetPositions.clear();  // Not used
      const Vec *cell = atoms->GetCell();
      int n = scaledPositions.size();
      Vec *RESTRICT scaledPositions = &(this->scaledPositions)[0];   // Helps vectorization
      Vec *RESTRICT wrappedPositions = &(this->wrappedPositions)[0];
      Vec *RESTRICT scaledOffsetPositions = &(this->scaledOffsetPositions)[0];
      for (int i = 0; i < n; i++)
	{
	  scaledOffsetPositions[i][0] = -floor(scaledPositions[i][0]) * xpbc0;
	  scaledPositions[i][0] += scaledOffsetPositions[i][0];
	  scaledOffsetPositions[i][1] = -floor(scaledPositions[i][1]) * xpbc1;
	  scaledPositions[i][1] += scaledOffsetPositions[i][1];
	  scaledOffsetPositions[i][2] = -floor(scaledPositions[i][2]) * xpbc2;
	  scaledPositions[i][2] += scaledOffsetPositions[i][2];
	  wrappedPositions[i] = cell[0] * scaledPositions[i][0]
	    + cell[1] * scaledPositions[i][1]
	    + cell[2] * scaledPositions[i][2];
	}
      scaledPositionsValid = wrappedPositionsValid = true;
    }
  // We need the inverse cell later.
  memcpy(old_inverse_cell, atoms->GetInverseCell(), 3*sizeof(Vec));
  supercell_counter = atoms->GetCellCounter();
  DEBUGPRINT;
}

void NeighborCellLocator::ScaleAndNormalizePositions(const set<int> &modified,
						     vector<Vec> &scaledpos)
{
  DEBUGPRINT;
  ASSERT(modified.size() == scaledpos.size());
  atoms->GetScaledPositions(scaledpos, modified);
  const bool *pbc = atoms->GetBoundaryConditions();
  // Special-case fully periodic and fully free boundaries, as they
  // are special-cased in the normal version.
  if (pbc[0] && pbc[1] && pbc[2])
    {
      const Vec *pos = atoms->GetPositions();
      const Vec *cell = atoms->GetCell();
      vector<Vec>::iterator sp = scaledpos.begin();
      for (set<int>::const_iterator ii = modified.begin();
	   ii != modified.end(); ++ii)
	{
	  int i = *ii;
	  scaledPositions[i] = *sp;
	  scaledPositions[i][0] -= floor(scaledPositions[i][0]);
	  scaledPositions[i][1] -= floor(scaledPositions[i][1]);
	  scaledPositions[i][2] -= floor(scaledPositions[i][2]);
	  *(sp++) = scaledPositions[i];
	  wrappedPositions[i] = cell[0] * scaledPositions[i][0]
	    + cell[1] * scaledPositions[i][1]
	    + cell[2] * scaledPositions[i][2];
	  offsetPositions[i] = wrappedPositions[i] - pos[i];
	}
      scaledPositionsValid = wrappedPositionsValid = true;
    }
  else if (!pbc[0] && !pbc[1] && !pbc[2])
    {
      // Fully free boundaries: wrappedPositions are the positions
      const Vec *r = atoms->GetPositions();
      vector<Vec>::iterator sp = scaledpos.begin();
      for (set<int>::const_iterator ii = modified.begin();
	   ii != modified.end(); ++ii)
	{
	  int i = *ii;
	  scaledPositions[i] = *(sp++);
	  wrappedPositions[i] = r[i];
	}
      scaledPositionsValid = wrappedPositionsValid = true;
    }
  else
    {
      // Mixed boundary conditions
      int xpbc0 = (int) pbc[0];
      int xpbc1 = (int) pbc[1];
      int xpbc2 = (int) pbc[2];
      const Vec *cell = atoms->GetCell();
      vector<Vec>::iterator sp = scaledpos.begin();
      for (set<int>::const_iterator ii = modified.begin();
	   ii != modified.end(); ++ii)
	{
	  int i = *ii;
	  scaledPositions[i] = *sp;
	  scaledOffsetPositions[i][0] = -floor(scaledPositions[i][0]) * xpbc0;
	  scaledPositions[i][0] += scaledOffsetPositions[i][0];
	  scaledOffsetPositions[i][1] = -floor(scaledPositions[i][1]) * xpbc1;
	  scaledPositions[i][1] += scaledOffsetPositions[i][1];
	  scaledOffsetPositions[i][2] = -floor(scaledPositions[i][2]) * xpbc2;
	  scaledPositions[i][2] += scaledOffsetPositions[i][2];
	  *(sp++) = scaledPositions[i];
	  wrappedPositions[i] = cell[0] * scaledPositions[i][0]
	    + cell[1] * scaledPositions[i][1]
	    + cell[2] * scaledPositions[i][2];
	}
      scaledPositionsValid = wrappedPositionsValid = true;
    }
}

void NeighborCellLocator::ScaleAndNormalizePosition(Vec &position, Vec *outscaledpos, Vec *wrappedpos) const
{
  DEBUGPRINT;
  const bool *pbc = atoms->GET_BOUNDARY_CONDITIONS();
  const Vec *cell = atoms->GET_CELL();
  const Vec *inv = atoms->GetInverseCell();
  Vec scaledpos;

  // Convert to scaled coordinates
  for (int j = 0; j < 3; j++)
  {
    scaledpos[j] = position[0] * inv[0][j]
                 + position[1] * inv[1][j]
                 + position[2] * inv[2][j];
  }

  // Compute wrapped scaled positions
  if (pbc[0] && pbc[1] && pbc[2])
  {
    scaledpos[0] -= floor(scaledpos[0]);
    scaledpos[1] -= floor(scaledpos[1]);
    scaledpos[2] -= floor(scaledpos[2]);
  }
  else if (!pbc[0] && !pbc[1] && !pbc[2])
  {
    // Fully free boundaries: no wrapping - do nothing
    ;
  }
  else
  {
    // Mixed boundary conditions
    int xpbc0 = (int) pbc[0];
    int xpbc1 = (int) pbc[1];
    int xpbc2 = (int) pbc[2];
    Vec offsetpos;
    offsetpos[0] = -floor(scaledpos[0]) * xpbc0;
    scaledpos[0] += offsetpos[0];
    offsetpos[1] = -floor(scaledpos[1]) * xpbc1;
    scaledpos[1] += offsetpos[1];
    offsetpos[2] = -floor(scaledpos[2]) * xpbc2;
    scaledpos[2] += offsetpos[2];
  }

  // Compute wrapped position from the wrapped scaled position
  *wrappedpos = cell[0] * scaledpos[0]
    + cell[1] * scaledpos[1]
    + cell[2] * scaledpos[2];
  *outscaledpos = scaledpos;
}

void NeighborCellLocator::RenormalizePositions()
{
  DEBUGPRINT;
  scaledPositionsValid = false;
  int nAtoms = this->nAtoms;       // Helps vectorization.
  int nAllAtoms = this->nAllAtoms;  
  const bool *pbc = atoms->GetBoundaryConditions();
  if (pbc[0] && pbc[1] && pbc[2])
    {
      // Full periodic boundaries
      if (atoms->GetCellCounter() != supercell_counter)
	{
	  // The unit cell has changed, and we have full period
	  // boundary conditions.  Assume that atoms have moved along
	  // the rescaling.
	  Vec transformation[3];
	  matrixMultiply3x3(transformation, old_inverse_cell, atoms->GetCell());
	  memcpy(old_inverse_cell, atoms->GetInverseCell(), 3*sizeof(Vec));
	  supercell_counter = atoms->GetCellCounter();
	  //cerr << endl << __FUNCTION__ << ": " << referencePositions.size()
	  //     << " " << offsetPositions.size() << endl;
	  ASSERT(referencePositions.size() == nAtoms);
	  ASSERT(offsetPositions.size() == nAllAtoms);
	  vector<Vec>::iterator rp = referencePositions.begin();
	  vector<Vec>::iterator op = offsetPositions.begin();
	  for(int i = 0; i < nAtoms; ++i, ++rp, ++op)
	    {
	      *op = transformation[0] * (*op)[0] + transformation[1] * (*op)[1]
		+transformation[2] * (*op)[2];
	      *rp = transformation[0] * (*rp)[0] + transformation[1] * (*rp)[1]
		+transformation[2] * (*rp)[2];
	    }
	  ASSERT(rp == referencePositions.end());
	  for(int i = nAtoms; i < nAllAtoms; ++i, ++op)
	    *op = transformation[0] * (*op)[0] + transformation[1] * (*op)[1]
	      +transformation[2] * (*op)[2];
	  ASSERT(op == offsetPositions.end());
	}
      // We now need to rewrap
      ASSERT(wrappedPositions.size() == nAllAtoms);
      const Vec *pos = atoms->GetPositions();
      vector<Vec>::const_iterator op = offsetPositions.begin();
      vector<Vec>::iterator end = wrappedPositions.end();
      for (vector<Vec>::iterator wp = wrappedPositions.begin(); wp != end;
	   ++wp, ++pos, ++op)
	*wp = *pos + *op;
      wrappedPositionsValid = true;
    }
  else 
    {
      // Free or mixed boundary conditions
      if (atoms->GetCellCounter() != supercell_counter)
	{
	  // The unit cell has changed.  Assume that atoms have moved
	  // along the rescaling.
	  Vec transformation[3];
	  matrixMultiply3x3(transformation, old_inverse_cell, atoms->GetCell());
	  memcpy(old_inverse_cell, atoms->GetInverseCell(), 3*sizeof(Vec));
	  supercell_counter = atoms->GetCellCounter();
	  vector<Vec>::iterator end = referencePositions.end();
	  for (vector<Vec>::iterator rp = referencePositions.begin();
	       rp < end; ++rp)
	    {
	      *rp = transformation[0] * (*rp)[0] + transformation[1] * (*rp)[1]
		+transformation[2] * (*rp)[2];
	    }
	}
      if (!pbc[0] && !pbc[1] && !pbc[2])
	{
	  // Fully free boundary conditions.
	  atoms->GetPositions(wrappedPositions, true);  // Include ghosts
	  wrappedPositionsValid = true;
	}
      else
	{
	  // Mixed boundary conditions
	  const Vec *cell = atoms->GetCell();
	  atoms->GetScaledPositions(scaledPositions, true);
	  ASSERT(scaledPositions.size() == scaledOffsetPositions.size());
	  ASSERT(wrappedPositions.size() == scaledOffsetPositions.size());
	  vector<Vec>::const_iterator sop = scaledOffsetPositions.begin();
	  vector<Vec>::iterator sp = scaledPositions.begin();
	  vector<Vec>::iterator end = wrappedPositions.end();
	  for (vector<Vec>::iterator wp = wrappedPositions.begin();
	       wp != end; ++wp, ++sop, ++sp)
	    {
	      *sp += *sop;
	      *wp = cell[0] * (*sp)[0] + cell[1] * (*sp)[1]
		+ cell[2] * (*sp)[2];
	    }
	  wrappedPositionsValid = true;
	}
    }
  DEBUGPRINT;
}

void NeighborCellLocator::RemakeLists_Simple(const set<int> &modified)
{
  DEBUGPRINT;
  ASSERT(modified.size() > 0);
  // Transform positions to scaled space
  vector<Vec> scaledpos(modified.size());
  ScaleAndNormalizePositions(modified, scaledpos);

  const vector<Vec> &positions = GetWrappedPositions();

  // Assign to boxes.  Caveat: atom may be outsize the expected
  // interval if there are free boundary conditions.
  vector<Vec>::const_iterator sp = scaledpos.begin();
  for (set<int>::const_iterator a = modified.begin(); a != modified.end();
       ++a, ++sp)  // Loop over modified and scaledpos
    {
      // Find the new index of the atom
      int index = 0;
      for (int i = 0; i < 3; i++)
	{
	  double p = (*sp)[i];
	  if (p < minimum[i])
	    p = minimum[i];
	  if (p > minimum[i] + size[i])
	    p = minimum[i] + size[i];
	  int k = int((p - minimum[i]) / size[i] * nCellsTrue[i]);
	  if (k > nCellsGapStart[i])
	    {
#if 0
	      ASSERT (k > nCellsGapStart[i] + nCellsGapSize[i]);
#endif
	      k -= nCellsGapSize[i];
	    }
	  #if 0
	  ASSERT(k >= 0);
#endif
	  if (k == nCells[i])
	    k--;
#if 0
	  ASSERT(k < nCells[i]);
#endif
	  index += nTotalCells[i] * k;
	}
      if (index != cellIndices[*a])
	{
	  // Remove atom from old cell
	  vector<int>::iterator i = cells[cellIndices[*a]].begin();
	  vector<int>::iterator terminate = cells[cellIndices[*a]].end();
	  while ((*i != *a) && (i != terminate))
	    ++i;
	  ASSERT(*i == *a);
	  cells[cellIndices[*a]].erase(i);
	  // Add to new cell
	  cells[index].push_back(*a);
	  cellIndices[*a] = index;
	}
      // We know that the atom is now in the right box
      referencePositions[*a] = positions[*a];
    }
  DEBUGPRINT;
}

  /// Update reference positions of some atoms
void NeighborCellLocator::UpdateReferencePositions(const set<int> &modified)
{
  const Vec *pos = atoms->GetPositions();
  for (set<int>::const_iterator i = modified.begin(); i != modified.end();
       ++i)
    referencePositions[*i] = pos[*i];
}

void NeighborCellLocator::print_info(int n)
{
  cerr << "NeighborCellLocator info on atom " << n << ":" << endl;
  if (referencePositions.size() > n)
    cerr << "referencePositions: " << referencePositions[n] << endl;
  if (wrappedPositions.size() > n)
    cerr << "wrappedPositions: " << wrappedPositions[n] << endl;
  if (scaledPositions.size() > n)
    cerr << "scaledPositions: " << scaledPositions[n] << endl;
  if (offsetPositions.size() > n)
    cerr << "offsetPositions: " << offsetPositions[n] << endl;
  if (scaledOffsetPositions.size() > n)
    cerr << "scaledOffsetPositions: " << scaledOffsetPositions[n] << endl;
  cerr << "cellIndex: " << cellIndices[n] << endl;
}

long NeighborCellLocator::PrintMemory() const
{
  long mem1 = 0;
  long mem2 = 0;
  long mem3 = 0;
  long needed = 0;
  mem1 += referencePositions.capacity() * sizeof(Vec);
  mem1 += wrappedPositions.capacity() * sizeof(Vec);
  mem1 += scaledPositions.capacity() * sizeof(Vec);
  mem1 += offsetPositions.capacity() * sizeof(Vec);
  mem1 += scaledOffsetPositions.capacity() * sizeof(Vec);
  mem2 += cellIndices.capacity() * sizeof(int);
  mem2 += cells.capacity() * sizeof(vector<int>);
  needed += referencePositions.size() * sizeof(Vec);
  needed += wrappedPositions.size() * sizeof(Vec);
  needed += scaledPositions.size() * sizeof(Vec);
  needed += offsetPositions.size() * sizeof(Vec);
  needed += scaledOffsetPositions.size() * sizeof(Vec);
  needed += cellIndices.size() * sizeof(int);
  needed += cells.size() * sizeof(vector<int>);
  int longest = 0;
  int empty = 0;
  for (vector< vector<int> >::const_iterator i = cells.begin();
       i != cells.end(); ++i)
    {
      mem2 += i->capacity() * sizeof(int);
      needed += i->size() * sizeof(int);
      if (i->size() > longest)
	longest = i->size();
      if (i->size() == 0)
	empty++;
    }
  long mem = (mem1 + mem2 + mem3 + 512*1024) / (1024*1024);
  mem1 = (mem1 + 512*1024) / (1024*1024);
  mem2 = (mem2 + 512*1024) / (1024*1024);
  mem3 = (mem3 + 512*1024) / (1024*1024);
  long overhead = mem - (needed + 512*1024) / (1024*1024);
  char buffer[500];
  snprintf(buffer, 500,
	   "*MEM* NeighborCellLocator %ld MB.  [ cells: %ld MB (longest: %d, empty: %d/%d), other: %ld MB, overhead: %ld MB ]",
	   mem, mem2, longest, empty, (int) cells.size(), mem1, overhead);
  cerr << buffer << endl;
  return mem;
}

