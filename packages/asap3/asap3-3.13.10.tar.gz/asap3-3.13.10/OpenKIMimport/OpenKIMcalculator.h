// OpenKIMcalculator.h - interface to OpenKIM models.
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

#ifndef _OPENKIMCALCULATOR_H
#define _OPENKIMCALCULATOR_H

#include "AsapPython.h"
#include "Asap.h"
#include "Potential.h"
#include <map>
#include <vector>

namespace KIM {
  class Model;
  class ComputeArguments;
}

namespace ASAPSPACE {

class OpenKIMcalculator : public Potential
{
public:
  class NeighborListData
  {
  public:
    vector<NeighborLocator *>nblists;
    vector<vector<int> > nb_buffers;
  };

public:
  OpenKIMcalculator(PyObject *self, const char *name, int verbose=0);
  ~OpenKIMcalculator();

  /// Indicate if a quantity should be supported (and allocated).
  void PleaseSupport(string quantity, bool alloc);

  /// Get all compute arguments/callbacks and their supported status.
  std::map<string,string> GetComputeArguments();    // KIM2: New

  /// This potential can be used in parallel simulations
  virtual bool Parallelizable() const {return true;}

  /// Check if neighbor lists need an update.
  ///
  /// Return true if the neigbor list needs an update.  In parallel
  /// simulations, the atoms will cause a communication so it returns
  /// true if an update is needed on any processor.  In parallel
  /// simulations, it also instructs the atoms to communicate their
  /// update status.

  virtual bool CheckNeighborList();
  /// Update the neighbor lists
  virtual void UpdateNeighborList();

  void ClearTranslation() {z_to_typecode.clear();}
  void AddTranslation(int z, int typecode) {z_to_typecode[z] = typecode;}

  /// Get the particle type code (number) from the particle symbol
  int GetParticleTypeCode(const char *symbol);

  virtual void SetAtoms(PyObject *pyatoms, Atoms* accessobj = NULL);

  virtual const vector<Vec> &GetForces(PyObject *pyatoms);
  virtual const vector<double> &GetPotentialEnergies(PyObject *pyatoms);
  virtual double GetPotentialEnergy(PyObject *pyatoms);
  virtual const vector<SymTensor> &GetVirials(PyObject *a);
  virtual SymTensor GetVirial(PyObject *a);

  /// Is work required to calculate the energy?
  virtual bool CalcReq_Energy(PyObject *pyatoms);

  /// Is work required to calculate the forces?
  virtual bool CalcReq_Forces(PyObject *pyatoms);

  /// Is work required to calculate the stress?
  virtual bool CalcReq_Virials(PyObject *pyatoms);

  virtual std::string GetName() const {return "OpenKIMcalculator";}

  void GetParameterNamesAndTypes(vector<string> &names, vector<int> &datatypes,
				 vector<int> &sizes, vector<string> &descriptions);

  void GetParameter(const int parameterindex, int *value);
  void GetParameter(const int parameterindex, double *value);
  void GetParameter(const int parameterindex, vector<int> &values);
  void GetParameter(const int parameterindex, vector<double> &values);

  void SetParameter(const int parameterindex, int value);
  void SetParameter(const int parameterindex, double value);
  void SetParameter(const int parameterindex, const vector<int> &values);
  void SetParameter(const int parameterindex, const vector<double> &values);

  /// Return the cutoff radius used in the potential.
  virtual double GetCutoffRadius() const {return influenceDistance;}

  /// Check and possibly update a neighbor list associated with this potential.
  ///
  /// This is the only way a neighbor list borrowed from a potential should be updated.
  /// Calling this function on a Potential not having a neighbor list is an error.
  /// Returns true if the neighbor list was actually updated.
  virtual bool CheckAndUpdateNbList(PyObject *pyatoms);

  /// Return the lattice constant of the material, if well-defined.

  /// If a lattice constant of the material can be defined, return it
  /// in Angstrom, otherwise throw an exception.
  virtual double GetLatticeConstant() const
  {throw AsapError("OpenKIMcalculator::GetLatticeConstant not supported.");}

  /// Print memory usage
  virtual long PrintMemory() const
  {throw AsapError("OpenKIMcalculator::PrintMemory not supported.");}

  //KIM_API_model *GetKimModel() {ASSERT(model_initialized); return model;}

protected:
  /// Allocate the neighbor list.
  virtual void CreateNeighborList();

  void InitParameters();
  void RefreshModel();

  void VerifyKimCompatibility();

  /// (Re)allocate storage for forces, energies and intermediate results.
  virtual void Allocate();

  /// Calculate stuff
  virtual void Calculate(PyObject *pyatoms);
  virtual void DoCalculate();

private:
  KIM::Model *model;           ///< The KIM Model object
  KIM::ComputeArguments *computeargs;   
  bool model_initialized;
  const char *kimname;         ///< Name of the OpenKIM model.
  int numberOfNeighborLists;
  vector<NeighborLocator *> nblists;     ///< The neighborlist object.
  vector<PyObject *> nblist_objs;
  int masternblist;      // Which one is the longest
  vector<bool> independentlist;   ///< Marks the lists that are unique.
  NeighborListData nblistdata;
  double driftfactor;             ///< Drift factor for the neighbor list.
  double influenceDistance;  ///< The model's influence distance
  vector<double> cutoffs;             //< The model's neighborlist cutoff, smaller or equal to the influence distance.
  vector<int> paddingNeighborHints;

  int nAtoms;      ///< Number of particles without ghost atoms
  int nSize;       ///< Number of particles with ghost atoms
  int nAtomsAlloc, nSizeAlloc;  ///< Values of nAtoms and nSize at last allocation.
  bool ghostatoms;          ///< True if atoms have ghosts.
  vector<int> species;
  vector<int> particleContributing;
  vector<Vec> forces;
  vector<double> particleEnergy;
  vector<SymTensor> particleVirial;
  double energy;
  SymTensor virial;

#if 0
  int nb_accessmode;
#endif
  vector<int> nb_buffer_n;
  vector<Vec> nb_buffer_rij;
  vector<double> nb_buffer_dist;
  int nblist_iterator;       // Next neighbor (used in iterator mode).

  std::map<asap_z_int,int> z_to_typecode;  // Translation of atomic number to KIM typecode.

  struct {
    bool energy;
    bool particleEnergy;
    bool forces;
    bool virial;
    bool particleVirial;
  } support;
  int support_n;  // Counts that they have all been set.

  /// A structure of counters to check if recalculations are necessary.
  struct {
    int nblist;
    int compute;
  } counters;

  /// A structure of bools, to remember if recalculations are necessary.
  struct {
    int nblist;
    int compute;
  } recalc;

};

} // namespace



#endif // _OPENKIMCALCULATOR_H
