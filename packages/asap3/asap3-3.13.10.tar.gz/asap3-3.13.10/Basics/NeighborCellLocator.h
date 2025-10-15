// -*- C++ -*-
// NeighborCellLocator.h:  Cell-based algorithm for finding neighbors.
//
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


#ifndef NEIGHBORCELLLOCATOR
#define NEIGHBORCELLLOCATOR

#include "AsapPython.h"
#include "Asap.h"
#include "Vec.h"
#include "NeighborLocator.h"
#include "IVec.h"
#include "Templates.h"
#include <vector>
using std::vector;
#include <map>
#include <utility>
using std::pair;
#include <math.h>
#include <stdint.h>

#define COMPACT_NBLIST

namespace ASAPSPACE {

typedef int translationsidx_t;   // Could also be unsigned char

// The datatpe neighboritem_t is mainly used in NeigbhorList.cpp
// It is a combination of an index into the atoms and an index
// into a list of translation vectors.
#ifdef COMPACT_NBLIST
// A neighborlist item is a single 32-bit unsigned integer,
// the first 5 bits are the tranlation vector index, the last 27 are
// the actual neighborlist index.
typedef uint32_t neighboritem_t;
#define NEIGHBOR_ITEM_MASK ((1 << 27) - 1)
#define NEIGHBOR_XLAT_SHIFT 27
#define NEIGHBOR_INDEX(x) ((x) & NEIGHBOR_ITEM_MASK)
#define NEIGHBOR_XLAT(x) ((x) >> NEIGHBOR_XLAT_SHIFT)
#define NEIGHBORITEM_PACK(x,a,b) x = a | (b << NEIGHBOR_XLAT_SHIFT)
#else // COMPACT_NBLIST
// A neighborlist item is a pair of an int (the actual neighborlist
// index) and a translationsidx_t, the translation vector index.
typedef pair<int,translationsidx_t> neighboritem_t;
#define NEIGHBOR_INDEX(x) (x).first
#define NEIGHBOR_XLAT(x) (x).second
#define NEIGHBORITEM_PACK(x,a,b) x; (x).first = a; (x).second = b;
#endif // COMPACT_NBLIST
  
PyAsap_NeighborLocatorObject *PyAsap_NewNeighborCellLocator(Atoms *a,
     double rCut, double driftfactor = 0.05);

class NeighborCellLocator : public NeighborLocator
{
protected:
  /// Generate a neighbor list for atoms a with cutoff rCut.

  /// The neighbor list will contain all neighbors within the distance
  /// rCut.  The neighborlist can be reused until an atom has moved
  /// more than rCut*driftfactor.
  NeighborCellLocator(Atoms *a, double rCut, double driftfactor = 0.05);
  virtual ~NeighborCellLocator();

  friend PyAsap_NeighborLocatorObject *PyAsap_NewNeighborCellLocator(
       Atoms *a, double rCut, double driftfactor);

  friend void PyAsap_Finalize<PyAsap_NeighborLocatorObject>(PyObject *self);

public:
  /// Enable neighbors of ghost atoms by calling this just after the constructor
  void EnableNeighborsOfGhosts();

  /// Check if the neighbor list can still be reused, update if not.
  bool CheckAndUpdateNeighborList();

  /// Check if the neighbor list can still be reused, update if not.
  ///
  /// This version is used when called from Python
  virtual bool CheckAndUpdateNeighborList(PyObject *atoms);

  /// Check the neighbor list.
  ///
  /// Check if the neighbor list can still be reused, return true if
  /// it should be updated.
  virtual bool CheckNeighborList();

  /// Update neighbor list
  virtual void UpdateNeighborList();

  /// Get wrapped positions of all the atoms
  const vector<Vec> &GetWrappedPositions() const {ASSERT(wrappedPositionsValid); 
    return wrappedPositions;}

  void GetWrappedPositions(vector<Vec> &wp) const {ASSERT(wrappedPositionsValid); 
    wp.insert(wp.begin(), wrappedPositions.begin(), wrappedPositions.end());}
  
  /// Get scaled positions of all the atoms
  const vector<Vec> &GetScaledPositions() const;

  /// Get reference positions (used by NeighborList)
  const Vec *GetReferencePositions() const {return &referencePositions[0];}
  
  /// Get information about the neighbors of atom n ("half" neighbor list)
  ///
  /// Input values: n is the number of the atom.  r (optional) is a
  /// cutoff, must be less than rCut in the constructor (not
  /// checked!).
  ///
  /// In-out values: size contains the maximum space in the arrays.
  /// It is decremented by the number of neighbors placed in the
  /// arrays.  It is an error to call GetNeighbors with too small a
  /// value of size.
  /// 
  /// Out values: neighbors[] contains the numbers of the atoms,
  /// diffs[] contains the \em relative positions of the atoms,
  /// diffs2[] contains the norms of the diffs vectors.
  ///
  /// Return value: The number of neighbors.
  int GetNeighbors(int n, int *neighbors, Vec *diffs, double *diffs2,
		   int& size, double r = -1.0) const;

  
  /// Get information about the neighbors of atom n ("half" neighbor list)
  ///
  /// This version of GetNeighbors only returns the numbers of the neighbors.
  /// It is intended for the Python interface.
  void GetNeighbors(int n, vector<int> &neighbors) const;

  int GetFullNeighbors(int n, int *neighbors, Vec *diffs, double *diffs2,
		       int& size, double r = -1.0) const;

  /// Get information about the neighbors around a query position
  ///
  /// It is intended for the Python interface
  int GetFullNeighborsQuery(Vec &position, int *neighbors, Vec *diffs, double *diffs2,
		       int& nb_size, double r = -1.0) const;

  /// Get information about the neighbors of atom n (full neighbor list)
  ///
  /// This version of GetNeighbors only returns the numbers of the neighbors.
  /// It is intended for the Python interface.
  void GetFullNeighbors(int n, vector<int> &neighbors) const;


  /// Return the neighbors and the corresponding translations.
  ///
  /// The vectors are cleared before data is put into them.
  ///
  /// Return value: The number of neighbors.
  int GetListAndTranslations(int n, vector<neighboritem_t> &neighbors) const;
  
  int GetComplementaryListAndTranslations(int n,
					  vector<neighboritem_t> &neighbors) const;

  /// Remake neighbor lists when a few atoms have been modified.
  ///
  /// This version, unlike NeighborList::RemakeList does
  /// not report back which other atoms have been affected.
  void RemakeLists_Simple(const set<int> &modified);
  
  /// Return the guaranteed maximal length of a single atom's NB list.

  /// Call this before using GetNeighbors() to make sure the arrays
  /// are big enough.  The value may change when the neighbor list is
  /// updated. 
  int MaxNeighborListLength() const {return maxLength;}

  /// Get the number of atoms in the corresponding list of atoms.
  int GetNumberOfAtoms() const {return nAtoms;}  // Used from Python.

  /// Return the cutoff distance (rCut) specified when creating this nblist.
  double GetCutoffRadius() const {return rCut;}

  /// Return the cutoff distance including twice the drift.
  ///
  /// For a NeighborCellLocator, the drift cannot be predicted and is ignored.
  double GetCutoffRadiusWithDrift() const {return rCut;}

  /// Get a copy of the table of translations (27 entries)
  void GetTranslationTable(vector<IVec> &table) const;

  /// Normalize the positions and calculate scaled space version
  ///
  /// This is used when a neighbor list is updated
  void ScaleAndNormalizePositions();
  
  /// Normalize some positions and calculate scaled space version
  ///
  /// The first argument is a set of atoms to be normalized, the
  /// corresponding scaled positions are placed in scaledpos.

  void ScaleAndNormalizePositions(const set<int> &modified,
				  vector<Vec> &scaledpos);

  /// Normalize a single position and calculate scaled space version
  ///
  /// The first argument is the position to be normalized, the
  /// corresponding wrapped and scaled position is output in outscaledpos,
  /// and the corresponding wrapped position in wrappedpos.
  void ScaleAndNormalizePosition(Vec &position,
                                 Vec *scaledpos,
                                 Vec *wrappedpos) const;

  /// Normalizing new positions using the normalization already calculated.
  ///
  /// This is used when checking a neighborlist.
  void RenormalizePositions();

#if 0
  /// Renormalize the old positions using old and new positions of the atoms.
  ///
  /// This is called by a master neighbor list when it has normalized
  /// the positions of the atoms.  The argument is the positions of
  /// the atoms *before* renormalization, this method uses them
  /// together with the current positions to update its own list of
  /// old positions.
  void RenormalizeReferencePositions(const vector<Vec> &oldpos);
#endif

  /// Update reference positions of some atoms
  void UpdateReferencePositions(const set<int> &modified);
  
  /// Return the atoms access object.  Used by a few tool functions.
  virtual Atoms *GetAtoms() const {return atoms;}

  string GetName() const {return "NeighborCellLocator";}

    /// Print internal info about an atom
  virtual void print_info(int n);

  /// Print memory usage
  virtual long PrintMemory() const;

protected:
  /// Generate a new neighbor list.
  virtual void MakeList();

  /// Make the lists of neighboring cells.
  void MakeNeighboringCellLists();

  /// Make translation table
  void MakeTranslationTable();

  typedef vector< pair<int, translationsidx_t> > nbcell_t;

  void makeNbCells(int thiscell);

  int CommonGetNeighbors(int n, int *neighbors, Vec *diffs, double *diffs2,
			 int& size, double r, bool wantfull) const;

  void CommonGetNeighbors(int a1, vector<int> &neighbors,
			  bool wantfull) const;

  double get_drift() const;
  
protected:
  int nAtoms;     ///< The number of atoms excluding ghosts.
  int nAllAtoms;  ///< The number of atoms including ghosts.
  double rCut;    ///< The cutoff radius.
  double rCut2;   ///< The square of the cutoff radius.
  double minboxsize;  ///< The minimal box size
  bool periodic[3];   ///< The boundary conditions.
  bool oldperiodic[3];    ///< The boundary conditions at the last update.
  int maxLength;  ///< The guaranteed max length of a neighbor list.
  int nCells[3];  ///< Number of cells
  int nTotalCells[4];
  int nCellsTrue[3];
  int nCellsGapStart[3];
  int nCellsGapSize[3];
  bool includeghostneighbors;  ///< Include neighbors to ghost atoms.
  double size[3];     ///< Size of system in scaled space
  double minimum[3];  ///< Offset of system in scaled space
  vector<Vec> referencePositions;  ///< Positions at last update.
  vector<Vec> wrappedPositions;    ///< Wrapped positions.
  vector<Vec> scaledPositions;     ///< Scaled positions.
  vector<Vec> offsetPositions;     ///< wrappedPositions - positions.
  vector<Vec> scaledOffsetPositions;  
  bool scaledPositionsValid;
  bool wrappedPositionsValid;

  Vec old_inverse_cell[3];  ///< Inverse unit cell of last renormalization.
  int supercell_counter; ///< When was old_inverse_cell last updated?
  
  /// The list of cells containing the atoms
  vector< vector<int> > cells;

  /// The number of the cell to which an atom belongs
  vector<int> cellIndices;

  /// For each cell, a list of the neighboring cells, and their offset
  /// across the periodic boundaries.
  vector<IVec> neighborCellOffsets;

  /// List of neighboring cells, valid for ...
  nbcell_t nbCells_inside;  // ...  a cell not touching the boundary.
  nbcell_t nbCells_left;    // ...  a cell touching a single boundary.
  nbcell_t nbCells_right;
  nbcell_t nbCells_top;
  nbcell_t nbCells_bottom;
  nbcell_t nbCells_front;
  nbcell_t nbCells_back;

  /// Lists of neighboring cells for all cells.  Center and sides are
  /// pointers to the objects above, edges and corners are unique.
  std::map<int, nbcell_t*> nbCells_all; 
  vector<nbcell_t*> nbCells_onthefly;  // On-the-fly elements in nbCells_all
                                       // (for memory management).
  
  /// Table of possible translation vectors
  vector<IVec> translationTable;
};

} // end namespace

#endif //  NEIGHBORCELLLOCATOR
