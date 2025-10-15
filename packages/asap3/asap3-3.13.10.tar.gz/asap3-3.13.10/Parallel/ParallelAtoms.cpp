// Copyright (C) 2008-2015 Jakob Schiotz and Center for Individual
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

#include "ParallelAtoms.h"
#include "Exception.h"
#include "RegularGridDecomposition.h"
#include "AsapMPI.h"
#include "Timing.h"
//#define ASAPDEBUG
#include "Debug.h"
#include <math.h>
using std::cerr;
using std::endl;
using std::flush;

static char mycobject[] = "_asap_parallelatoms_cobject";
static char invalidghosts[] = "_asap_invalidghosts";

// Exception thrown if ghosts are invalid.  Should always be caught internally.
class AsapGhostInvalid : public AsapError
{
public:
  AsapGhostInvalid(const char *m) : AsapError(m) {};
};

// #define REGARRAYINFO   // Print extra debugging info about reg. arrays.

// Local function to get stride from PyArray, even if first dimension is zero
// (PyArray_STRIDE returns 0 in that case for numpy version 1.23.X)
static npy_intp get_stride_from_array(PyArrayObject *arr)
{
  npy_intp stride = PyArray_ITEMSIZE(arr);
  for (int i = 1; i < PyArray_NDIM(arr); i++)
    stride *= PyArray_DIM(arr, i);
  ASSERT(PyArray_STRIDE(arr, 0) == 0 || PyArray_STRIDE(arr, 0) == stride);
  return stride;
}

/////////////////////////////
////
////  CONSTRUCTOR
////
/////////////////////////////


ParallelAtoms::ParallelAtoms(PyObject *py_atoms, int verbose)
{
  CONSTRUCTOR;
  this->verbose = verbose;
  hasGhosts = true;
  try {
    DEBUGPRINT;
    migrationCounter = 0;
    decorated = false;
    ghost_count = 0;
    haswarned_noatoms = false;
    mpi = new Communicator();  // Later, consider extracting from atoms.
    ASSERT(mpi != NULL);
    extract_ncells(py_atoms);  // Read nCells from Python object
    domainDecomp = NULL;
    
    nProcessor = mpi->GetProcessorNumber();
    nProcessors = mpi->GetNumberOfProcessors();
    
    int nTotalCells = 1;
    for (int i = 0; i < 3; i++)
      nTotalCells *= nCells[i];
    ASSERT(nTotalCells == nProcessors);
    
    nTotalAtoms = 0;
    // We assume that a "char" is a byte!
    ASSERT(sizeof(char) == 1);
    
    // Now, we can create the domain decomposition.  We need to access
    // data from the atoms, the easiest is to open them.
    Begin(py_atoms);
    domainDecomp = new RegularGridDecomposition(GetCell(),
						GetBoundaryConditions(),
						nCells, mpi, verbose);
    ASSERT(domainDecomp != NULL);
    End();
    DEBUGPRINT;
  }
  catch (...) {
    // If an error occurred in the constructor, the object is deallocated.
    // If refcount is non-zero, Atoms::~Atoms() will detect an error.
    DEBUGPRINT;
    refcount = 0;
    throw;
  }
  DEBUGPRINT;
}


/////////////////////////////
////
////  DESTRUCTOR
////
/////////////////////////////

ParallelAtoms::~ParallelAtoms()
{
  DESTRUCTOR;
  DEBUGPRINT;
  // Remove Python references to registered arrays
  if (verbose > 2)
    cerr << "Entering ParallelAtoms::~ParallelAtoms()" << endl;
  DEBUGPRINT;
  delete domainDecomp;
  DEBUGPRINT;
  delete mpi;
  DEBUGPRINT;
  if (verbose > 2)
    cerr << "Exiting ParallelAtoms::~ParallelAtoms()" << endl;
  DEBUGPRINT;
}


////////////////////////////////
////
////  Begin
////  (2 versions)
////
////////////////////////////////

void ParallelAtoms::Begin(PyObject *pyatoms, bool allow_reopen /* = false */)
{
  Begin(pyatoms, allow_reopen, false);
}

void ParallelAtoms::Begin(PyObject *pyatoms, bool allow_reopen, bool postmigrate)
{
  DEBUGPRINT;
  NormalAtoms::Begin(pyatoms, allow_reopen);
  if (!haswarned_noatoms)
  {
    // The test suite needs to suppress this warning.
    if (PyObject_HasAttrString(pyatoms, "suppress_warning_noatoms"))
      haswarned_noatoms = true;  // Pretend the warning has already been issued
  }
  if (nTotalAtoms == 0)
    nTotalAtoms = mpi->Add((unsigned long) nAtoms);
  if (!postmigrate && active == 1)
    {
      // Communicate the counters, so we see updates on other processors
      const int ndata = 5;  // Five counters 
      vector<int> mydata(ndata);
      vector<int> globaldata(ndata);
      mydata[0] = count_atoms;
      mydata[1] = count_cell;
      mydata[2] = count_positions;
      mydata[3] = count_numbers;
      mydata[4] = count_inverse_cell;
      mpi->Max(mydata, globaldata);
      count_atoms = globaldata[0];
      count_cell = globaldata[1];
      count_positions = globaldata[2];
      count_numbers = globaldata[3];
      count_inverse_cell = globaldata[4];
      if (decorated && ghost_count != count_positions)
	{
	  try {
	    UpdateGhostData();
	  } catch(AsapGhostInvalid &e) {
	    // The ghosts have explicitly been marked invalid.
	    double range = get_ghost_range();
	    DecorateWithGhosts(range);
	    UpdateGhostData();
	    // This may also have invalidated nTotalAtoms
	    nTotalAtoms = mpi->Add((unsigned long) nAtoms);
	  }
	  ghost_count = count_positions;
	}
    }
  DEBUGPRINT;
}

////////////////////////////////
////
////  Distribute
////
////////////////////////////////

void ParallelAtoms::Distribute()
{
  DEBUGPRINT;
  Migrate(true);
  DEBUGPRINT;
}


////////////////////////////////
////
////  Migrate
////
////////////////////////////////

void ParallelAtoms::Migrate(bool distributing /* = false */)
{
  DEBUGPRINT;
  USETIMER("ParallelAtoms::Migrate");
  migrationCounter++;
  if (verbose)
    {
      cerr << " Migrate[" << migrationCounter;
    }
  CheckIdentities();
  DEBUGPRINT;
  // Find out which atoms belong to which processor:
  vector< vector<int> > cells;
  vector<int> migrated;
  domainDecomp->whichProcessor(this, cells, migrated);

  // Get the send and receive lists
  const vector<int> *sendlist;
  const vector<int> *recvlist;
  vector<int> distributingsendlist, distributingrecvlist;
  // First time (distribution) migration may happen to all other processors,
  // the next times (normal migration) it will only be to neighboring
  // processors.
  DEBUGPRINT;
  if (distributing)
    {
  DEBUGPRINT;
      distributingsendlist.resize(nProcessors - 1);
      distributingrecvlist.resize(nProcessors - 1);
      for (int dp = 1; dp < nProcessors; dp++)
        {
          distributingsendlist[dp-1] = (nProcessor + dp) % nProcessors;
          distributingrecvlist[dp-1] =
            (nProcessor + nProcessors - dp) % nProcessors;
        }
      sendlist = &distributingsendlist;
      recvlist = &distributingrecvlist;
    }
  else
    {
  DEBUGPRINT;
      sendlist = domainDecomp->GetSendList();
      recvlist = domainDecomp->GetRecvList();
      // Check that no atoms have been reassigned to unreachable processors.
      int nCells = cells.size();
      for (int i = 0; i < nCells; i++)
        {
          if (cells[i].size() > 0)
            {
              // Processor i must be on the send list.
              vector<int>::const_iterator j = sendlist->begin();
              while (j != sendlist->end() && *j != i)
                ++j;
              if (j == sendlist->end())
		throw AsapError("An atom is migrating to a non-neighboring processor (It must have a huge velocity - plasma physics is not supported!).");
	    }
        }          
    }
  ASSERT((sendlist->size() == recvlist->size()) &&
         (sendlist->size() < nProcessors));
  DEBUGPRINT;

  // Extract data from Python atoms
  vector<std::string> array_names; // Sorted list of array names.
  vector<PyArrayObject *> arrays;  // Owned refs to arrays to migrate.
  get_array_names(py_arrays, array_names);
  get_arrays(py_arrays, array_names, arrays);

  DEBUGPRINT;
  // Send and receive:
  int nBytes = 0;   // Number of bytes to be communicated per atom.
  for (vector<PyArrayObject *>::const_iterator arr = arrays.begin();
       arr < arrays.end(); ++arr)
    nBytes += get_stride_from_array(*arr);

  receiveBuffer.resize(0);
  int nCommunicate = sendlist->size();
  DEBUGPRINT;
  for (int dp = 0; dp < nCommunicate; dp++)
    {
      int pSend = (*sendlist)[dp];
      int nAtomsToSend = cells[pSend].size();
      sendBuffer.resize(nAtomsToSend * nBytes);

      // Put stuff into sendBuffer
      char *b = &sendBuffer[0];
  DEBUGPRINT;
      for (int i = 0; i < nAtomsToSend; i++)
        {
          int a = cells[pSend][i];
	  for (vector<PyArrayObject *>::const_iterator arr = arrays.begin();
	       arr < arrays.end(); ++arr)
	    {
	      long stride = get_stride_from_array(*arr);
	      memcpy(b, PyArray_BYTES(*arr) + a * stride, stride);
	      b += stride;
	    }
        }
      DEBUGPRINT;
      ASSERT(b == &sendBuffer[0] + nAtomsToSend * nBytes);
      if (verbose > 1)
        cerr << nProcessor << ": sending " << nAtomsToSend
	     << " atoms of size " << nBytes << " bytes = "
             << sendBuffer.size() << " bytes to proc " << pSend << endl;
      DEBUGPRINT;
      mpi->NonBlockingSend(sendBuffer, pSend);
      DEBUGPRINT;
      int pReceive = (*recvlist)[dp];
      DEBUGPRINT;

      mpi->Receive(receiveBuffer, pReceive);
      DEBUGPRINT;
      // Wait for non-blocking send to finish:
      mpi->Wait(); 
      DEBUGPRINT;
    }
  DEBUGPRINT;

  // Copy data to new arrays
  int nMigrated = migrated.size();
  int nNewAtoms = nAtoms - nMigrated + receiveBuffer.size() / nBytes;
  vector<PyArrayObject *> new_arrays;  // New arrays for atomic data.
  make_new_arrays(new_arrays, arrays, nNewAtoms);

  migrated.push_back(nAtoms);
  int a1 = 0;
  // Loop over all segments between migrated atoms, there is one more
  // segment than nMigrated.
  int target = 0;
  DEBUGPRINT;
  for (int i = 0; i <= nMigrated; i++) 
    {
      int a2 = migrated[i];
      int n = a2 - a1;
      if (n > 0)
	{
	  for (int j = 0; j < arrays.size(); j++)
	    {
	      long stride = get_stride_from_array(arrays[j]);
	      memcpy(PyArray_BYTES(new_arrays[j]) + target * stride,
		     PyArray_BYTES(arrays[j]) + a1 * stride,
		     n * stride);
	    }
	  target += n;
	}
      a1 = a2 + 1;
    }
  ASSERT(target == nAtoms - nMigrated);
  DEBUGPRINT;
  
  // Append atoms from other processors:
  // SetNumberOfGhosts(0); XXXX
  char *b = &receiveBuffer[0];
  char *b0 = b;
  for (int a = nAtoms - nMigrated; a < nNewAtoms; a++)
    {
      for (int j = 0; j < new_arrays.size(); j++)
	{
	  long stride = get_stride_from_array(new_arrays[j]);
	  memcpy(PyArray_BYTES(new_arrays[j]) + a * stride, b, stride);
	  b += stride;
	}
    }
  ASSERT(b - b0 == receiveBuffer.size());
  nAtoms = nNewAtoms;
  DEBUGPRINT;
  release_arrays(arrays, array_names, 2);
  store_arrays(py_arrays, array_names, new_arrays);
  release_arrays(new_arrays, array_names, 2);
  CheckIdentities();
  set_ghost_range(-1.0);  // No ghosts yet.
  if (verbose)
    cerr << "]" << flush;

  decorated = false;
  // Reopen the atoms as the number of atoms has changed
  if (!distributing)  // When distributing, nothing more is done.
    {
      PyObject *my_atoms_ref = py_atoms;
      CHECKREF(my_atoms_ref);
      Py_INCREF(my_atoms_ref);  // Keep a reference while closing and reopening.
      int my_cnt_atoms = count_atoms;
      int my_cnt_pos = count_positions;
      // We now need to close the atoms and reopen them.  This is complicated by
      // the fact that we may be inside multiple calls to Begin.  We have to unwind
      // this completely, then reopen the right number of times
      int my_active = active;
      int my_expect_reopen = expect_reopen;
      while (active)
        End();
      for (int i = 0; i < my_active; i++)
        Begin(my_atoms_ref, i < my_expect_reopen, true);
      count_atoms = my_cnt_atoms + 1;
      count_positions = my_cnt_pos + 1;
      Py_DECREF(my_atoms_ref);
    }
  DEBUGPRINT;
}


////////////////////////////////
////
////  GetListOfElements
////
////////////////////////////////

void ParallelAtoms::GetListOfElements(set<int> &elements)
{
  DEBUGPRINT;
  vector<char> buf;
  int *b;
  int thisproc = mpi->GetProcessorNumber();
  int nelem;
  
  NormalAtoms::GetListOfElements(elements);  // Probably defined in Atoms.

  /* Collect elements on master */
  if (thisproc != 0) 
    {
      /* Send set to processor 0 */
      nelem = elements.size();
      buf.resize(nelem * sizeof(int));
      b = (int *) &buf[0];
      for (set<int>::iterator i = elements.begin(); i != elements.end(); ++i)
        *(b++) = *i;
      mpi->Send(buf, 0);
    }
  else
    {
      int nproc = mpi->GetNumberOfProcessors();
      for (int proc = 1; proc < nproc; proc++)
        {
          mpi->Receive(buf, proc);
          nelem = buf.size() / sizeof(int);
          if (nelem) 
            {
              b = (int *) &buf[0];
              for (int i = 0; i < nelem; i++)
                elements.insert(b[i]);
            }
        }
    }

  /* Redistribute them */
  if (thisproc == 0) 
    {
      /* Send the info */
      int nproc = mpi->GetNumberOfProcessors();
      nelem = elements.size();
      buf.resize(nelem * sizeof(int));
      b = (int *) &buf[0];
      for (set<int>::iterator i = elements.begin(); i != elements.end(); ++i)
        *(b++) = *i;
      for (int proc = 1; proc < nproc; proc++)
        mpi->Send(buf, proc);
    }
  else
    {
      elements.clear();
      mpi->Receive(buf, 0);
      nelem = buf.size() / sizeof(int);
      ASSERT(nelem);
      b = (int *) &buf[0];
      for (int i = 0; i < nelem; i++)
        elements.insert(b[i]);
    }
  if (verbose > 1)
    {
      cerr << "Processor " << thisproc << ": List of elements: ";
      for (set<int>::iterator i = elements.begin(); i != elements.end();
           ++i)
        cerr << *i;
      cerr << endl;
    }
    
  DEBUGPRINT;
}


////////////////////////////////
////
////  CheckIdentities
////
////////////////////////////////

// Check that all atoms are present exactly once
void ParallelAtoms::CheckIdentities() 
{
  // This test does not work if long is a 32 bit integer.  This should
  // be a preprocessor test, but sizeof cannot be used in preprocessor
  // directives.
  if (sizeof(long) > 4)
    {
      DEBUGPRINT;
      USETIMER("ParallelAtoms::CheckIdentities");
      // ASSERT(sizeof(long) > 4);
      const long *identities = GetIdentities();
      unsigned long totident = 0;
      // If there are more than 4 billion atoms, the sum of identities
      // will overflow a 64-bit unsigned int.  That is OK if we just
      // make sure this product overflows the same way.  Assigning to
      // the instance variable junk hopefully prevents the optimizer
      // from doing the multiplication before the division.
      unsigned long expected = 0;
      if (nTotalAtoms % 2 == 0)
	{
	  // Even number of atoms
	  junk = nTotalAtoms / 2;
	  expected = junk * (nTotalAtoms - 1);
	}
      else
	{
	  junk = (nTotalAtoms - 1) / 2;
	  expected = junk * nTotalAtoms;
	}
      for (int i = 0; i < nAtoms; i++)
	totident += identities[i];
      vector<unsigned long> here(2);
      vector<unsigned long> sum;
      here[0] = nAtoms;
      here[1] = totident;
      DEBUGPRINT;
      mpi->Add(here, sum);
      DEBUGPRINT;
      if ((sum[0] != nTotalAtoms) || (sum[1] != expected))
	throw AsapError("CheckIdentities(Node ")
	  << nProcessor << "): nAtoms = "
	  << sum[0] << ", expected "
	  << nTotalAtoms  << "; sum(id) = "
	  << sum[1] << ", expected "
	  << expected;
      DEBUGPRINT;
    }}


////////////////////////////////
////
////  NewBoundaryConditions
////
////////////////////////////////

void ParallelAtoms::NewBoundaryConditions(const bool newperiodic[3])
{
  DEBUGPRINT;
  NormalAtoms::NewBoundaryConditions(newperiodic);
  delete domainDecomp;
  domainDecomp = new RegularGridDecomposition(GetCell(),
					      GetBoundaryConditions(),
					      nCells, mpi);
  // If atoms have already been distributed, they should migrate now.
  if (migrationCounter)
      Migrate(true);   // Re-distribute atoms.
  DEBUGPRINT;
}


////////////////////////////////
////
////  GetIdentities
////
////////////////////////////////

const long *ParallelAtoms::GetIdentities() const
{
  DEBUGPRINT;
  ASSERT(py_arrays != NULL && PyDict_Check(py_arrays));
  PyArrayObject *id = AsPyArray(PyDict_GetItemString(py_arrays, "ID")); // BORROWED ref!
  if (id == NULL)
    throw AsapError("Invalid ParallelAtoms object: No ID array.");
  if (PyArray_NDIM(id) != 1           // One-dimensional
      || PyArray_DIM(id, 0) != nAtoms    // One per atom
      || PyArray_TYPE(id) != NPY_LONG    // array of longs
      || !PyArray_ISCARRAY_RO(id))       // Contiguous etc.
    throw AsapError("Invalid ID array.");
  return (long *) PyArray_BYTES(id);
  DEBUGPRINT;
}


////////////////////////////////
////
////  UpdateGhostData
////
////////////////////////////////

// Helper function for ParallelAtoms::UpdateGhostData
template<class T>
static void copynum(vector<asap_z_int> &num, 
		    PyArrayObject *py_numbers, int nAt, int nGh)
{
  T *from = (T *) PyArray_DATA(py_numbers);
  for (int i = 0; i < nGh; i++)
    num[nAt + i] = (asap_z_int) from[i];
}

void ParallelAtoms::UpdateGhostData()
{
  // Potentially the ghosts could have been invalidated.  In that case
  // throw a specific error that can be caught further up.
  if (PyObject_HasAttrString(py_atoms, invalidghosts))
    throw AsapGhostInvalid("Ghosts invalid");
      
  DEBUGPRINT;
  if (verbose)
    cerr << " UG";
  vector<char> sendBuffer;
  vector<char> recvBuffer;

  USETIMER("ParallelAtoms::UpdateGhostData");
  // Check that we are not mixing data from two different ParallelAtoms objects.
  ASSERT(py_atoms != NULL);
  PyObject *mypointer = PyObject_GetAttrString(py_atoms, mycobject);
  if (mypointer == NULL)
    throw AsapError("ParallelAtoms::UpdateGhostData: failed to get ") <<
      mycobject;
  bool OK = (PyCapsule_CheckExact(mypointer) &&
	     (PyCapsule_GetPointer(mypointer, "asap3.parallelatoms") == this));
  Py_DECREF(mypointer);
  if (!OK)
    throw AsapError("ParallelAtoms::UpdateGhostData: Multiple objects are creating ghost atoms.");

  // Now we should populate the ghost data
  const vector<int> *sendlist = domainDecomp->GetSendList();
  const vector<int> *recvlist = domainDecomp->GetRecvList();
  ASSERT(sendlist->size() == recvlist->size());
  
  PyObject *py_ghosts = PyObject_GetAttrString(py_atoms, "ghosts");
  if (py_ghosts == NULL)
    throw AsapError("ParallelAtoms::UpdateGhostData: No ghosts found.");
  PyObject *py_arrays = PyObject_GetAttrString(py_atoms, "arrays");
  if (py_arrays == NULL)
    throw AsapError("ParallelAtoms::UpdateGhostData: No arrays found.");
  
  vector<std::string> array_names;          // Sorted list of array names.
  vector<PyArrayObject *> real_arrays;            // Data on real atoms.
  vector<PyArrayObject *> ghost_arrays;           // Ghost arrays to fill.
  get_array_names(py_ghosts, array_names);
  get_arrays(py_ghosts, array_names, ghost_arrays);
  get_arrays(py_arrays, array_names, real_arrays);
  int nBytes = 0;
  int pos_index = -1;
  int num_index = -1;
  // Count number of bytes and find the positions array.
  for (int i = 0; i < array_names.size(); i++)
    {
      int n = get_stride_from_array(real_arrays[i]);
      ASSERT(get_stride_from_array(ghost_arrays[i]) == n);
      ASSERT(PyArray_DIM(real_arrays[i], 0) == nAtoms);
      ASSERT(PyArray_DIM(ghost_arrays[i], 0) == nGhosts);
      nBytes += n;
      if (array_names[i].compare("positions") == 0)
	{
	  pos_index = i;
	  ASSERT(n == sizeof(Vec));
	}
      if (array_names[i].compare("numbers") == 0)
	  num_index = i;
    }
  ASSERT(pos_index >= 0);  // But no check for num_index: not compulsory.

  num_ghosts_recv_from.resize(recvlist->size());
  DEBUGPRINT;
  long offset = 0;  // Offset into receiving arrays
  // Loop over processors
  for (int dp = 0; dp < sendlist->size(); dp++)
    {
      int send_p = (*sendlist)[dp];
      const vector< pair<int, int> > &indices = ghosts[send_p];
      sendBuffer.resize(indices.size() * nBytes);
      char *b = &sendBuffer[0];
      // Loop over arrays to send
      for (int arr = 0; arr < array_names.size(); arr++)
	{
	  // Loop over atoms to send
	  typedef vector< pair<int, int> >::const_iterator VP;
	  for (VP g = indices.begin(); g != indices.end(); ++g)
	    {
	      npy_intp stride = get_stride_from_array(real_arrays[arr]);
	      char *from = PyArray_BYTES(real_arrays[arr]) +
		((long)g->first) * stride;
	      memcpy(b, from, stride);
	      b += stride;
	    }
	}
      ASSERT(b - &sendBuffer[0] == sendBuffer.size());

      // Communicate
      mpi->NonBlockingSend(sendBuffer, send_p);
      int recv_p = (*recvlist)[dp];
      recvBuffer.clear();
      mpi->Receive(recvBuffer, recv_p);
      int n_recv = recvBuffer.size() / nBytes;
      num_ghosts_recv_from[dp] = n_recv;
      b = &recvBuffer[0];
      for (int arr = 0; arr < array_names.size(); arr++)
	{
	  npy_intp stride = get_stride_from_array(ghost_arrays[arr]);
	  char *to = PyArray_BYTES(ghost_arrays[arr]) + offset * stride;
	  memcpy(to, b, n_recv * stride);
	  b += n_recv * stride;
	}
      offset += n_recv;
      mpi->Wait();
    }
  DEBUGPRINT;
  ASSERT(offset == nGhosts);
  // Now, the ghost positions should be copied into the local positions array...
  if (nGhosts > 0)
  {
    DEBUGPRINT;
    assert(positions.size() > 0);
    memcpy(&positions[nAtoms], PyArray_DATA(ghost_arrays[pos_index]),
	   nGhosts*sizeof(Vec));
    // ... and the atomic numbers.
    DEBUGPRINT;
    if (num_index >= 0)
      {
	PyArrayObject *py_numbers = ghost_arrays[num_index];
	int tn = PyArray_TYPE(py_numbers);
	if (PyArray_EquivTypenums(tn, ASAP_Z_ARRAYTYPE))
	  copynum<asap_z_int>(numbers, py_numbers, nAtoms, nGhosts);
	else if (PyArray_EquivTypenums(tn, NPY_INT32))
	  copynum<npy_int32>(numbers, py_numbers, nAtoms, nGhosts);
	else if (PyArray_EquivTypenums(tn, NPY_INT64))
	  copynum<npy_int64>(numbers, py_numbers, nAtoms, nGhosts);
	else if (PyArray_EquivTypenums(tn, NPY_INT8))
	  copynum<npy_int8>(numbers, py_numbers, nAtoms, nGhosts);
	else if (PyArray_EquivTypenums(tn, NPY_INT16))
	  copynum<npy_int16>(numbers, py_numbers, nAtoms, nGhosts);
	else
	  throw AsapError("Atomic numbers are an unsupported integer type.");
      }
  }
  
  DEBUGPRINT;
  release_arrays(real_arrays, array_names, 2);
  release_arrays(ghost_arrays, array_names, 2);
  CHECKREF(py_arrays);
  Py_DECREF(py_arrays);
  CHECKREF(py_ghosts);
  Py_DECREF(py_ghosts);
  DEBUGPRINT;
}
 

////////////////////////////////
////
////  CommunicateData
////
////////////////////////////////

void ParallelAtoms::CommunicateData(double* address, int n)
{
  DEBUGPRINT;
  USETIMER("ParallelPotential::CommunicateData");
  double *ghostAddress = address + n*nAtoms;
  const vector <int> *sendlist = domainDecomp->GetSendList();
  const vector <int> *recvlist = domainDecomp->GetRecvList();
  for (int dp = 0; dp < sendlist->size(); dp++)
    {
      int p = (*sendlist)[dp];
      vector< pair<int, int> >& indices = ghosts[p];
      sendBuffer.resize(indices.size() * n*sizeof(double));
      char *b = &sendBuffer[0];
      typedef vector< pair<int, int> >::const_iterator VP;
      for (VP g = indices.begin(); g != indices.end(); ++g)
        {
          memcpy(b, address + n*(g->first), n*sizeof(double));
          b += n*sizeof(double);
        }
      mpi->NonBlockingSend(sendBuffer, p);
      p = (*recvlist)[dp];
      receiveBuffer.resize(0);
      mpi->Receive(receiveBuffer, p);
      memcpy(ghostAddress, &receiveBuffer[0], receiveBuffer.size());
      ghostAddress += receiveBuffer.size() / sizeof(double);
      mpi->Wait();
    }  
  ASSERT(ghostAddress == address + n * (nAtoms + nGhosts));
  DEBUGPRINT;
}


////////////////////////////////
////
////  UpdateBeforeCalculation
////
////////////////////////////////

// Update flag and counters across processors.
//
// Called by a Potential with a flag indicating if the neighborlist
// should be updated.  In a serial simulation, just return the flag.
//
// In a parallel simulation, communicate across processors so the the
// flag passed as an argument is updated if just one processor thinks
// an update is necessary.
bool ParallelAtoms::UpdateBeforeCalculation(bool flag, double range)
{
  DEBUGPRINT;
  // First, communicate if we need to migrate and make new nb lists.
  int globalflag = mpi->Max((int) flag);
  if (globalflag)
    {
      Migrate();
      DecorateWithGhosts(range);
      UpdateGhostData();
      ghost_count = count_positions;
    }
  return globalflag;
  DEBUGPRINT;
}


////////////////////////////////
////
////  DecorateWithGhosts
////
////////////////////////////////

void ParallelAtoms::DecorateWithGhosts(double range)
{
  DEBUGPRINT;
  if (verbose)
    cerr << " DG";
  USETIMER("ParallelPotential::DecorateWithGhosts");
  // If the ghosts are marked invalid, unmark them
  if (PyObject_HasAttrString(py_atoms, invalidghosts))
    PyObject_DelAttrString(py_atoms, invalidghosts);
  
  // Delete old Ghosts:
  ghosts.resize(nProcessors);
  for (int p = 0; p < nProcessors; p++)
    ghosts[p].resize(0);

  domainDecomp->makeGhostExportLists(this, range, ghosts);
  int nGhosts;
  vector<int> outgoingghosts(nProcessors);
  vector<int> sums(nProcessors);
  for (int p = 0; p < nProcessors; p++)
    outgoingghosts[p] = int(ghosts[p].size());
  mpi->Add(outgoingghosts, sums);
  nGhosts = sums[nProcessor];
  set_number_of_ghosts(nGhosts);
  justdecorated = 1;
  decorated = true;
  if (verbose > 1)
    cerr << "Ghost atoms added: " << nGhosts << endl;
  DEBUGPRINT;
}


//******************************
//*****
//*****  HELPER METHODS
//*****
//******************************



////////////////////////////////
////
////  extract_ncells
////
////////////////////////////////

// Get the number of cells from the Python object.
void ParallelAtoms::extract_ncells(PyObject *pyatoms)
{
  DEBUGPRINT;
  ASSERT(pyatoms != NULL);
  PyArrayObject *py_cells = AsPyArray(PyObject_GetAttrString(pyatoms, "nCells"));
  if (py_cells == NULL)
    throw AsapError("No nCells. Not a ParallelAtoms object?");
  if (PyArray_NDIM(py_cells) != 1            // One-dimensional
      || PyArray_DIM(py_cells, 0) != 3          // shape = (3,)
      || PyArray_TYPE(py_cells) != NPY_LONG     // array of longs
      || !PyArray_ISCARRAY_RO(py_cells))
    {
      Py_DECREF(py_cells);
      throw AsapError("Invalid ParallelAtoms object: nCells should be integers of shape (3,).");
    }
  for (int i = 0; i < 3; i++)
    {
      long *nn = (long *) PyArray_GETPTR1(py_cells, i);
      nCells[i] = (int) *nn;
    }
  CHECKREF(py_cells);
  Py_DECREF(py_cells);
  DEBUGPRINT;
}


////////////////////////////////
////
////  get_array_names
////
////////////////////////////////
								 
// Get a sorted list of array names.
void ParallelAtoms::get_array_names(PyObject *dict, vector<std::string> &names)
{
  DEBUGPRINT;
  ASSERT(dict != NULL && PyDict_Check(dict));
  PyObject *keys = PyDict_Keys(dict);
  ASSERT(keys != NULL);
  if (PyList_Sort(keys) != 0)
    throw AsapError("Failed to sort ParallelAtoms' arrays/ghosts");
  Py_ssize_t n = PyList_GET_SIZE(keys);
  names.resize((int) n);
  for (Py_ssize_t i = 0; i < n; i++)
    {
      PyObject *pyname = PyList_GET_ITEM(keys, i);
      if (!PyUnicode_Check(pyname))
	throw AsapError("Non-string key in ghost atom dictionary.");
      // Make sure the Unicode object is ready and 8-bit data
      if ((PyUnicode_READY(pyname) == -1)
	  || (PyUnicode_KIND(pyname) != PyUnicode_1BYTE_KIND))
	throw AsapError("Non-ascii key in ghost atom dictionary.");
      // Now convert to a C++ string
      names[(int)i].assign((char *)PyUnicode_1BYTE_DATA(pyname),
			   (size_t)PyUnicode_GET_LENGTH(pyname));
    }
  Py_DECREF(keys);
  DEBUGPRINT;
}


////////////////////////////////
////
////  get_arrays
////
////////////////////////////////

// Get a list of array objects.
void ParallelAtoms::get_arrays(PyObject *dict, vector<std::string> &names,
			       vector<PyArrayObject *> &arrays)
{
  ASSERT(dict != NULL && PyDict_Check(dict));
  int n = names.size();
  arrays.resize(n);
  for (int i = 0; i < n; i++)
    {
      arrays[i] = AsPyArray(PyDict_GetItemString(dict, names[i].c_str()));
      if (arrays[i] == NULL || !PyArray_Check(arrays[i]))
	throw AsapError("Invalid data in ParallelAtoms' arrays/ghosts[") <<
	  names[i] << "].";
    }
  for (int i = 0; i < n; i++)
    {
      Py_INCREF(arrays[i]);
    }
  DEBUGPRINT;
}
      

////////////////////////////////
////
////  make_new_arrays
////
////////////////////////////////

// Make a set of new arrays corresponding to a set of old arrays
void ParallelAtoms::make_new_arrays(vector<PyArrayObject *> &newarrays,
				    vector<PyArrayObject *> &oldarrays,
				    int size)
{
  DEBUGPRINT;
  int n = oldarrays.size();
  newarrays.resize(n);
  vector<npy_intp> dims;
  for (int i = 0; i < n; i++)
    {
      int nd = PyArray_NDIM(oldarrays[i]);
      dims.resize(nd);
      dims[0] = size;
      for (int j = 1; j < nd; j++)
	dims[j] = PyArray_DIM(oldarrays[i],j);
      PyArrayObject *o = (PyArrayObject *) PyArray_SimpleNew(nd, &dims[0],
          PyArray_TYPE(oldarrays[i]));
      if (o == NULL)
	throw AsapPythonError();
      newarrays[i] = o;
    }
  DEBUGPRINT;
}



////////////////////////////////
////
////  release_arrays
////
////////////////////////////////

// Release references to arrays
void ParallelAtoms::release_arrays(vector<PyArrayObject *> &arrays,
				   vector<std::string> &names,
				   int maxcount)
{
  DEBUGPRINT;
  vector<std::string>::const_iterator name = names.begin();
  for (vector<PyArrayObject *>::iterator i = arrays.begin();
       i != arrays.end(); ++i, ++name)
    {
      if (Py_REFCNT(*i) > maxcount)
	cerr << "ASAP warning: Extra reference detected for " << name->c_str() << endl;
      CHECKREF(*i);
      Py_DECREF(*i);
    }
  arrays.clear();
  DEBUGPRINT;
}


////////////////////////////////
////
////  store_arrays
////
////////////////////////////////

// Store arrays into a dictionary.
void ParallelAtoms::store_arrays(PyObject *dict, vector<std::string> &names,
				 vector<PyArrayObject *> &arrays)
{
  DEBUGPRINT;
  ASSERT(dict != NULL && PyDict_Check(dict));
  int n = names.size();
  for (int i = 0; i < n; i++)
    {
      int x = PyDict_SetItemString(dict, names[i].c_str(), (PyObject *) arrays[i]);
      if (x != 0)
	throw AsapPythonError();
    }
  DEBUGPRINT;
}


////////////////////////////////
////
////  set_ghost_range
////
////////////////////////////////

// Store the max range where the ghosts are valid.  Negative: no ghosts yet.
void ParallelAtoms::set_ghost_range(double range)
{
  ASSERT(py_atoms != NULL);
  PyObject *x = PyFloat_FromDouble(range);
  ASSERT(x != NULL);
  int y = PyObject_SetAttrString(py_atoms, "asap_ghost_range", x);
  Py_DECREF(x);
  if (y == -1)
    throw AsapError("Failed to set atoms.asap_ghost_range.");
}


////////////////////////////////
////
////  get_ghost_range
////
////////////////////////////////

double ParallelAtoms::get_ghost_range()
{
  ASSERT(py_atoms != NULL);
  PyObject *py_x = PyObject_GetAttrString(py_atoms, "asap_ghost_range");
  if (py_x == NULL)
    throw AsapError("Failed to get atoms.asap_ghost_range.");
  if (!PyFloat_Check(py_x))
    {
      Py_DECREF(py_x);
      throw AsapError("Atoms.asap_ghost_range is not a number.");
    }
  double range = PyFloat_AS_DOUBLE(py_x);
  Py_DECREF(py_x);
  return range;
}


////////////////////////////////
////
////  set_number_of_ghosts
////
////////////////////////////////

void ParallelAtoms::set_number_of_ghosts(int nGhosts)
{
  this->nGhosts = nGhosts;
  ASSERT(py_atoms != NULL);
  // First, place a pointer to this object in the Python object to
  // detect if two different ParallelAtoms objects try to use ghosts
  // at the same time.
  PyObject *mypointer = PyCapsule_New(this, "asap3.parallelatoms", NULL);
  if (mypointer == NULL)
    throw AsapError("Creating PyCapsule failed.");
  if (PyObject_SetAttrString(py_atoms, mycobject, mypointer) == -1)
    throw AsapError("Failed to set attribute ") << mycobject;
  Py_DECREF(mypointer);
  
  // Now, resize ghost arrays.
  PyObject *py_ghosts = PyObject_GetAttrString(py_atoms, "ghosts");
  if (py_ghosts == NULL)
    throw AsapError("ParallelAtoms::set_number_of_ghosts:: No ghosts found.");

  vector<std::string> array_names;          // Sorted list of array names.
  vector<PyArrayObject *> arrays;                 // Ghost arrays to resize.
  get_array_names(py_ghosts, array_names);
  get_arrays(py_ghosts, array_names, arrays);
  vector<PyArrayObject *> new_arrays;             // New arrays for ghost data.
  make_new_arrays(new_arrays, arrays, nGhosts);
  release_arrays(arrays, array_names, 2);
  store_arrays(py_ghosts, array_names, new_arrays);
  release_arrays(new_arrays, array_names, 2);
  CHECKREF(py_ghosts);
  Py_DECREF(py_ghosts);

  // Finally, resize the vectors used for the position and the atomic numbers
  positions.resize(nAtoms + nGhosts);
  numbers.resize(nAtoms + nGhosts);
}

long ParallelAtoms::PrintMemory() const
{
  long mem = NormalAtoms::PrintMemory();
  long ghmem = 0;  // Count the big stuff.
  for (vector< vector< pair<int, int> > >::const_iterator i = ghosts.begin();
       i != ghosts.end(); ++i)
    ghmem += i->capacity();
  ghmem *= 2*sizeof(int);

  long bufmem = sendBuffer.size() + receiveBuffer.size();

  long mymem = (ghmem + bufmem + 512*1024) / (1024*1024);
  ghmem = (ghmem + 512*1024) / (1024*1024);
  bufmem = (bufmem + 512*1024) / (1024*1024);
  
  char buffer[500];
  snprintf(buffer, 500,
	   "*MEM* ParallelAtoms  %ld MB.  [ ghosts %ld MB, comm %ld MB ]",
	   mymem, ghmem, bufmem);
  cerr << buffer << endl;
  return mem + mymem;
}

void ParallelAtoms::CollectFromGhosts(vector<Vec> &data)
{
  DEBUGPRINT;
  USETIMER("ParallelPotential::CollectFromGhosts");
  ASSERT(data.size() == nAtoms + nGhosts);
  Vec *address = &data[0];
  Vec *ghostAddress = address + nAtoms;
  // Inverse communication from normally.
  const vector <int> *recvlist = domainDecomp->GetSendList();
  const vector <int> *sendlist = domainDecomp->GetRecvList();
  for (int dp = 0; dp < recvlist->size(); dp++)
    {
      // We originally received this many ghost atoms
      int orig_n_recv = num_ghosts_recv_from[dp];
      sendBuffer.resize(orig_n_recv * sizeof(Vec));
      memcpy(&sendBuffer[0], ghostAddress, orig_n_recv*sizeof(Vec));
      ghostAddress += orig_n_recv;
      mpi->NonBlockingSend(sendBuffer, (*sendlist)[dp]);
      receiveBuffer.resize(0);
      int p = (*recvlist)[dp];
      mpi->Receive(receiveBuffer, p);
      vector< pair<int, int> >& indices = ghosts[p];
      Vec *b = (Vec *) &receiveBuffer[0];
      typedef vector< pair<int, int> >::const_iterator VP;
      for (VP g = indices.begin(); g != indices.end(); ++g)
        {
          data[g->first] += *(b++);
        }
      mpi->Wait();
    }
  ASSERT(ghostAddress - &data[0] == nAtoms + nGhosts);
}

void ParallelAtoms::CollectFromGhosts(vector<SymTensor> &data)
{
  DEBUGPRINT;
  USETIMER("ParallelPotential::CollectFromGhosts");
  ASSERT(data.size() == nAtoms + nGhosts);
  SymTensor *address = &data[0];
  SymTensor *ghostAddress = address + nAtoms;
  // Inverse communication from normally.
  const vector <int> *recvlist = domainDecomp->GetSendList();
  const vector <int> *sendlist = domainDecomp->GetRecvList();
  for (int dp = 0; dp < recvlist->size(); dp++)
    {
      // We originally received this many ghost atoms
      int orig_n_recv = num_ghosts_recv_from[dp];
      sendBuffer.resize(orig_n_recv * sizeof(SymTensor));
      memcpy(&sendBuffer[0], ghostAddress, orig_n_recv*sizeof(SymTensor));
      ghostAddress += orig_n_recv;
      mpi->NonBlockingSend(sendBuffer, (*sendlist)[dp]);
      receiveBuffer.resize(0);
      int p = (*recvlist)[dp];
      mpi->Receive(receiveBuffer, p);
      vector< pair<int, int> >& indices = ghosts[p];
      SymTensor *b = (SymTensor *) &receiveBuffer[0];
      typedef vector< pair<int, int> >::const_iterator VP;
      for (VP g = indices.begin(); g != indices.end(); ++g)
        {
          data[g->first] += *(b++);
        }
      mpi->Wait();
    }
  ASSERT(ghostAddress - &data[0] == nAtoms + nGhosts);
}

  // Issue a warning if there are no atoms in the simulation, but only the first time.
void ParallelAtoms::NoAtomsErrorOrWarning()
{
  if (not haswarned_noatoms)
  {
    cerr << endl << "WARNING: No atoms on process number " << nProcessor << endl;
    haswarned_noatoms = true;
  }
}

