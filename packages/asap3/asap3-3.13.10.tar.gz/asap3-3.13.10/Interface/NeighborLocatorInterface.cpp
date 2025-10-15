// -*- C++ -*-
// NeighborLocatorInterface.cpp: Python interface to the EMT object.
//
// Copyright (C) 2008 Jakob Schiotz and Center for Individual
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
#include "NeighborLocatorInterface.h"
#include "ExceptionInterface.h"
#include "PythonConversions.h"
#include "Templates.h"
#include "NeighborLocator.h"
#include "NeighborList.h"
#include "NeighborList2013.h"
#include "NeighborCellLocator.h"
#include "SecondaryNeighborLocator.h"
#include "NormalAtoms.h"
#include "ImageAtoms.h"
#include <stddef.h>   // for offsetof

// The PyAsap_NeighborLocatorObject is defined in NeighborLocator.h

// GETSCALED enabled the get_scaled_positions method.  It may cause an assertion failed.
#undef GETSCALED

namespace ASAPSPACE {

PyTypeObject PyAsap_NeighborLocatorType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  "_asap.NeighborLocator",
  sizeof(PyAsap_NeighborLocatorObject),
  // The rest are initialized by name for reliability.
};

static char NeighborLocator_Docstring[] = "NeighborLocator object.\n";

PyAsap_NeighborLocatorObject *PyAsap_NewNeighborList(Atoms *atoms, double rCut,
                                                     double driftfactor)
{
  PyAsap_NeighborLocatorObject *self;

  self = PyObject_NEW(PyAsap_NeighborLocatorObject,
                      &PyAsap_NeighborLocatorType);
  if (self == NULL)
    throw AsapError("OOPS XXXX");
  
  self->weakrefs = NULL;
  self->fulllist = false;
  self->cobj = new NeighborList(atoms, rCut, driftfactor);
  if (self->cobj == NULL)
    {
      CHECKREF(self);
      Py_DECREF(self);
      throw AsapError("Failed to create a new NeighborList object.");
    }
  return self;
}

PyAsap_NeighborLocatorObject *PyAsap_NewNeighborList2013(Atoms *atoms, double rCut,
                                                       double driftfactor,
                                                       const TinyMatrix<double> &rcut2)
{
  PyAsap_NeighborLocatorObject *self;

  self = PyObject_NEW(PyAsap_NeighborLocatorObject,
                      &PyAsap_NeighborLocatorType);
  if (self == NULL)
    throw AsapError("OOPS XXXX");

  self->weakrefs = NULL;
  self->fulllist = false;
  self->cobj = new NeighborList2013(atoms, rCut, driftfactor, rcut2);
  if (self->cobj == NULL)
    {
      CHECKREF(self);
      Py_DECREF(self);
      throw AsapError("Failed to create a new NeighborList2013 object.");
    }
  return self;
}


PyAsap_NeighborLocatorObject *PyAsap_NewNeighborCellLocator(Atoms *atoms,
    double rCut, double driftfactor)
{
  PyAsap_NeighborLocatorObject *self;

  self = PyObject_NEW(PyAsap_NeighborLocatorObject,
		      &PyAsap_NeighborLocatorType);
  if (self == NULL)
    throw AsapError("OOPS XXXX");
  
  self->weakrefs = NULL;
  self->fulllist = false;
  self->cobj = new NeighborCellLocator(atoms, rCut, driftfactor);
  if (self->cobj == NULL)
    {
      CHECKREF(self);
      Py_DECREF(self);
      throw AsapError("Failed to create a new NeighborCellLocator object.");
    }
  return self;
}

PyAsap_NeighborLocatorObject *PyAsap_NewSecondaryNeighborLocator(Atoms *atoms,
    double rCut, double driftfactor)
{
  PyAsap_NeighborLocatorObject *self;

  self = PyObject_NEW(PyAsap_NeighborLocatorObject,
                      &PyAsap_NeighborLocatorType);
  if (self == NULL)
    throw AsapError("OOPS XXXX");

  self->weakrefs = NULL;
  self->fulllist = false;
  self->cobj = new SecondaryNeighborLocator(atoms, rCut, driftfactor);
  if (self->cobj == NULL)
    {
      CHECKREF(self);
      Py_DECREF(self);
      throw AsapError("Failed to create a new NeighborCellLocator object.");
    }
  return self;
}

char PyAsap_NewNeighborList_Docstring[] =
  "Create a neighbor list (using a stored list)\n\n\
Parameters:\n\
  rCut: The cutoff distance.\n\n\
  atoms = None: The atoms. If given, the list is initialize immediately.\n\
  driftfactor = 0.05: How large a factor of rCut the atoms may drift before\n\
    update is needed.\n\n\
This implementation is optimized for frequent access to the neighbor list.\n\
If it is only used once or a few times between each update, the\n\
NeighborCellLocator will be more efficient (and use far less memory),\n";

PyObject *PyAsap_NewNeighborList_Py(PyObject *noself, PyObject *args,
                                    PyObject *kwargs)
{
  static char *kwlist[] = {"rCut", "atoms", "driftfactor", "full", NULL};

  PyObject *atoms = Py_None;
  double rCut = 0.0;
  double driftfactor = 0.05;
  int full = 0;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "d|Odi:NeighborList", kwlist,
				   &rCut, &atoms, &driftfactor, &full))
    return NULL;
  if (rCut <= 0.0)
    {
      PyErr_SetString(PyExc_ValueError,
		      "NeighborList: Cutoff must be greater than zero.");
      return NULL;
    }
  
  try {
    PyAsap_NeighborLocatorObject *self = PyAsap_NewNeighborList(NULL, rCut,
								driftfactor);
    if (full) {
      NeighborList *nblist = dynamic_cast<NeighborList *>(self->cobj);
      ASSERT(nblist != NULL);
      nblist->EnableFullNeighborLists();
      self->fulllist = true;
    }
    
    if (atoms != Py_None)
      self->cobj->CheckAndUpdateNeighborList(atoms);
    return (PyObject *) self;
  }
  CATCHEXCEPTION;
}

char PyAsap_NewNeighborCellLocator_Docstring[] =
  "Create a neighbor list (using a cell algorithm)\n\n\
Parameters:\n\
  rCut: The cutoff distance.\n\n\
  atoms = None: The atoms. If given, the list is initialize immediately.\n\
  driftfactor = 0.05: How large a factor of rCut the atoms may drift before\n\
    update is needed.\n\n\
This implementation is optimized for low memory use and fast update, and is\n\
optimal if only accessed once or a few times.  For repeated access of the\n\
neighbor list with only occasional changes to the atoms, the NeighborList\n\
may be more efficient (but uses significantly more memory).\n";

// This function is accessed through PyAsap_NewNeighborCellLocator_Py, which
// in serial versions of Asap wraps this function, but in parallel versions
// wraps PyAsap_NewNeighborCellLocator_Parallel
PyObject *PyAsap_NewNeighborCellLocator_Serial(PyObject *noself, PyObject *args,
                                               PyObject *kwargs)
{
  static char *kwlist[] = {"rCut", "atoms", "driftfactor", "minimum_image", NULL};

  PyObject *atoms = Py_None;
  double rCut = 0.0;
  double driftfactor = 0.05;
  int minimum_image = 1;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "d|Odi:NeighborCellLocator",
				   kwlist, &rCut, &atoms, &driftfactor, &minimum_image))
    return NULL;
  if (rCut <= 0.0)
    {
      PyErr_SetString(PyExc_ValueError,
		      "NeighborCellLocator: Cutoff must be greater than zero.");
      return NULL;
    }

  try {
    Atoms *a = new NormalAtoms();
    if (!minimum_image)
      a = new ImageAtoms(a);
    PyAsap_NeighborLocatorObject *self =
      PyAsap_NewSecondaryNeighborLocator(a, rCut, driftfactor);
    AsapAtoms_DECREF(a);
    if (atoms != Py_None)
      self->cobj->CheckAndUpdateNeighborList(atoms);
    return (PyObject *) self;
  }
  CATCHEXCEPTION;
}

char PyAsap_NewFullNeighborList_Docstring[] =
  "Create a full neighbor list (using a cell algorithm)\n\n\
Parameters:\n\
  rCut: The cutoff distance.\n\n\
  atoms = None: The atoms. If given, the list is initialize immediately.\n\
  driftfactor = 0.05: How large a factor of rCut the atoms may drift before\n\
    update is needed.\n";

// Note: in parallel simulations, the Python interface overrides this
// with PyAsap_NewFullNeighborList_Parallel
PyObject *PyAsap_NewFullNeighborList(PyObject *noself, PyObject *args,
				     PyObject *kwargs)
{
  try {
    PyObject *self = PyAsap_NewNeighborCellLocator_Py(noself, args, kwargs);
    if (self == NULL)
      return NULL;
    ((PyAsap_NeighborLocatorObject *)self)->fulllist = true;
    return self;
  }
  CATCHEXCEPTION;
}

static PyObject *PyAsap_NeighborLocatorGetItem(PyAsap_NeighborLocatorObject
					       *self, Py_ssize_t n)
{
  if (n < 0 || n >= self->cobj->GetNumberOfAtoms())
    {
      PyErr_SetString(PyExc_IndexError, "NeighborLocator: index out of range.");
      return NULL;
    }
  vector<int> nbl;
  try {
    CHECKNOASAPERROR;
    if (self->fulllist)
      self->cobj->GetFullNeighbors(n, nbl);
    else
      self->cobj->GetNeighbors(n, nbl);
    PROPAGATEASAPERROR;
  }
  CATCHEXCEPTION;
  self->cobj->TranslateImageAtomsMaybe(nbl);

  return PyAsap_ArrayFromVectorInt(nbl);
}

static Py_ssize_t PyAsap_NeighborLocatorLength(PyAsap_NeighborLocatorObject
					       *self)
{
  return self->cobj->GetNumberOfAtoms();
}
 
static char PyAsap_NeighborLocatorIsFullList_Docstring[] =
  "Returns True if the neighbor list is a full list, False if it a half list.";

static PyObject *PyAsap_NeighborLocatorIsFullList(PyAsap_NeighborLocatorObject
						  *self, PyObject *noargs)
{
  if (self->fulllist)
    Py_RETURN_TRUE;
  else
    Py_RETURN_FALSE;
}

static PyObject *PyAsap_NeighborLocatorCheckAndUpdate(PyAsap_NeighborLocatorObject
					     *self, PyObject *atoms)
{
  try {
    self->cobj->CheckAndUpdateNeighborList(atoms);
  }
  CATCHEXCEPTION;
  Py_RETURN_NONE;
}

static PyObject *PyAsap_NBL_GetWrapped(PyAsap_NeighborLocatorObject *self,
				       PyObject *noargs)
{
  vector<Vec> wrappedpositions;
  self->cobj->GetWrappedPositions(wrappedpositions);
  return PyAsap_ArrayFromVectorVec(wrappedpositions);
}

#if GETSCALED
static PyObject *PyAsap_NBL_GetScaled(PyAsap_NeighborLocatorObject *self,
				       PyObject *noargs)
{
  const vector<Vec> &scaledpositions = self->cobj->GetScaledPositions();
  return PyAsap_ArrayFromVectorVec(scaledpositions);
}
#endif

static PyObject *PyAsap_NBL_PrintInfo(PyAsap_NeighborLocatorObject *self,
				     PyObject *args)
{
  int n;
  if (!PyArg_ParseTuple(args, "i:print_info", &n))
    return NULL;
  self->cobj->print_info(n);
  Py_RETURN_NONE;
}

static PyObject *PyAsap_NblPrintMemory(PyAsap_NeighborLocatorObject *self,
				    PyObject *noargs)
{
  long mem = self->cobj->PrintMemory();
  return Py_BuildValue("l", mem);
}

static PyObject *PyAsap_NeighborLocatorPartialTest(PyAsap_NeighborLocatorObject
						   *self, PyObject *args)
{
  NeighborList *nblist = dynamic_cast<NeighborList *>(self->cobj);
  if (nblist == NULL) {
    PyErr_SetString(PyExc_TypeError, "Not a NeighborList object");
    return NULL;
  }
  if (!(self->fulllist)) {
    PyErr_SetString(PyExc_TypeError, "Not a full neighbor list");
    return NULL;
  }
  
  PyObject *modified;
  PyObject *atoms;
  if (!PyArg_ParseTuple(args, "OO:test_partial_updates", &modified, &atoms))
    return NULL;

  set<int> modif;
  if (PyAsap_SetIntFromArray(modif, modified) != 0)
    return NULL;
  int n;
  try {
    n = nblist->TestPartialUpdate(modif, atoms);
  }
  CATCHEXCEPTION;
  return Py_BuildValue("i", n);
}

static char PyAsap_NBL_GetNBQuery_Docstring[] =
"Get information about the neighborhood around a query point.\n\n\
Returns a 3-tuple for each query point: The indices of the neighbors,\n\
the vectors pointing towards the neighbors and the squared distances\n\
to the neighbors.\n\
Periodic boundary conditions are taken into account.\n\n\
Parameters:\n\
    query_points: Nx3 array of query point positions.\n\
    rcut (optional): The cutoff distance. If specified, must be smaller\n\
      or equal to the value specified when creating the neighbor list.\n\
";
static PyObject *PyAsap_NBL_GetNBQuery(PyAsap_NeighborLocatorObject *self,
				  PyObject *args, PyObject *kwargs)
{
  PyObject *py_arg_query_positions;
  PyArrayObject *py_arr_query_positions;
  PyObject *py_tup_return = NULL;
  double rcut = -1.0;
  static char *kwlist[] = {"query_points", "rCut", NULL};
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|d:get_neighbors",
				   kwlist, &py_arg_query_positions, &rcut))
    return NULL;
  // Check sensibility
  py_arr_query_positions = AsPyArray(py_arg_query_positions);
  if (PyArray_NDIM(py_arr_query_positions) != 2)
  {
    PyErr_SetString(PyExc_ValueError, "NeighborLocator: Expected query points to be Nx3 numpy array.");
    return NULL;
  }
  if (PyArray_SHAPE(py_arr_query_positions)[1] != 3)
  {
    PyErr_SetString(PyExc_ValueError, "NeighborLocator: Expected query points to be Nx3 numpy array.");
    return NULL;
  }
  if (PyArray_SHAPE(py_arr_query_positions)[0] < 1)
  {
    PyErr_SetString(PyExc_ValueError, "NeighborLocator: Expected query points to be Nx3 numpy array.");
    return NULL;
  }
  if (rcut > self->cobj->GetCutoffRadius())
  {
    PyErr_SetString(PyExc_ValueError, "NeighborLocator: too large cutoff.");
    return NULL;
  }
  int num_query_points = PyArray_SHAPE(py_arr_query_positions)[0];
  py_tup_return = PyTuple_New(num_query_points);
  if (py_tup_return == NULL)
  {
    Py_XDECREF(py_tup_return);
    return NULL;
  }

  int size = self->cobj->MaxNeighborListLength();
  vector<int> neighbors(size);
  vector<Vec> diff(size);
  vector<double> diff2(size);
  for (int i=0; i<num_query_points; i++)
  {
    int nnb;
    int nb_size = size;
    Vec pos;
    neighbors.resize(size);
    diff.resize(size);
    diff2.resize(size);
    pos[0] = *((npy_double *) PyArray_GETPTR2(py_arr_query_positions, i, 0));
    pos[1] = *((npy_double *) PyArray_GETPTR2(py_arr_query_positions, i, 1));
    pos[2] = *((npy_double *) PyArray_GETPTR2(py_arr_query_positions, i, 2));
    nnb = self->cobj->GetFullNeighborsQuery(pos, &neighbors[0], &diff[0],
                                         &diff2[0], nb_size, rcut);
    neighbors.resize(nnb);
    diff.resize(nnb);
    diff2.resize(nnb);
    PyObject *py_neighbors = PyAsap_ArrayFromVectorInt(neighbors);
    PyObject *py_diff = PyAsap_ArrayFromVectorVec(diff);
    PyObject *py_diff2 = PyAsap_ArrayFromVectorDouble(diff2);
    if (py_neighbors == NULL || py_diff == NULL || py_diff2 == NULL)
      {
        // Conversion failed, strange!  Clean up and abort.
        Py_XDECREF(py_neighbors);
        Py_XDECREF(py_diff);
        Py_XDECREF(py_diff2);
        return NULL;
      }
    PyObject *py_res_one_query_point = Py_BuildValue("NNN", py_neighbors, py_diff, py_diff2);
    if (py_res_one_query_point == NULL)
    {
      return NULL;
    }
    PyTuple_SET_ITEM(py_tup_return, i, py_res_one_query_point);
  }
  return py_tup_return;
}

static char PyAsap_NBL_GetNB_Docstring[] =
"Get information about the neighbors of an atom.\n\n\
Returns three arrays: The indices of the neighbors, the squared distances\n\
to the neighbors, and the vectors pointing towards the neighbors.\n\
Periodic boundary conditions are taken into account.\n\n\
Parameters:\n\
  i: The atom queried.\n\
  rcut (optional): The cutoff distance.  If specified, must be smaller\n\
    or equal to the value specified when creating the neighbor list.\n\
";

static PyObject *PyAsap_NBL_GetNB(PyAsap_NeighborLocatorObject *self,
				  PyObject *args, PyObject *kwargs)
{
  int atom;
  double rcut = -1.0;
  static char *kwlist[] = {"n", "rCut", NULL};
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "i|d:get_neighbors",
				   kwlist, &atom, &rcut))
    return NULL;
  // Check sensibility
  if (atom < 0 || atom >= self->cobj->GetNumberOfAtoms())
    {
      PyErr_SetString(PyExc_ValueError, "NeighborLocator: atom number out of range.");
      return NULL;
    }
  if (rcut > self->cobj->GetCutoffRadius())
    { 
      PyErr_SetString(PyExc_ValueError, "NeighborLocator: too large cutoff.");
      return NULL;
    }
  int size = self->cobj->MaxNeighborListLength();
  vector<int> neighbors(size);
  vector<Vec> diff(size);
  vector<double> diff2(size);
  int nnb;
  if (self->fulllist)
    nnb = self->cobj->GetFullNeighbors(atom, &neighbors[0], &diff[0],
				       &diff2[0], size, rcut);
  else
    nnb = self->cobj->GetNeighbors(atom, &neighbors[0], &diff[0],
				   &diff2[0], size, rcut);
  neighbors.resize(nnb);
  diff.resize(nnb);
  diff2.resize(nnb);
  self->cobj->TranslateImageAtomsMaybe(neighbors);

  PyObject *py_neighbors = PyAsap_ArrayFromVectorInt(neighbors);
  PyObject *py_diff = PyAsap_ArrayFromVectorVec(diff);
  PyObject *py_diff2 = PyAsap_ArrayFromVectorDouble(diff2);
  if (py_neighbors == NULL || py_diff == NULL || py_diff2 == NULL)
    {
      // Conversion failed, strange!  Clean up and abort.
      Py_XDECREF(py_neighbors);
      Py_XDECREF(py_diff);
      Py_XDECREF(py_diff2);
      return NULL;
    }
  return Py_BuildValue("NNN", py_neighbors, py_diff, py_diff2);
}

static PyMethodDef PyAsap_NeighborLocatorMethods[] = {
  {"is_full_list", (PyCFunction) PyAsap_NeighborLocatorIsFullList,
   METH_NOARGS, PyAsap_NeighborLocatorIsFullList_Docstring},
  {"check_and_update", (PyCFunction) PyAsap_NeighborLocatorCheckAndUpdate,
   METH_O, "Check the neighbor list, update if needed."},
  {"test_partial_update", (PyCFunction) PyAsap_NeighborLocatorPartialTest,
   METH_VARARGS, "Test partial update of neighbor list.  FOR DEBUGGING ONLY!"},
  {"get_wrapped_positions", (PyCFunction) PyAsap_NBL_GetWrapped,
   METH_NOARGS, "Get wrapped positions."},
  {"get_neighbors", (PyCFunction) PyAsap_NBL_GetNB,
   METH_VARARGS|METH_KEYWORDS, PyAsap_NBL_GetNB_Docstring},
  {"get_neighbors_querypoint", (PyCFunction) PyAsap_NBL_GetNBQuery,
   METH_VARARGS|METH_KEYWORDS, PyAsap_NBL_GetNBQuery_Docstring},
#ifdef GETSCALED
  {"get_scaled_positions", (PyCFunction) PyAsap_NBL_GetScaled,
   METH_NOARGS, "Get neighborlist's idea of scaled positions."},
#endif // GETSCALED
  {"print_info", (PyCFunction) PyAsap_NBL_PrintInfo,
   METH_VARARGS, "print debugging info about an atom."},
  {"print_memory", (PyCFunction)PyAsap_NblPrintMemory,
   METH_NOARGS,  "Print an estimate of the memory usage."},
  {NULL}
};

static PySequenceMethods PyAsap_NeighborLocator_sequence = {
	(lenfunc) PyAsap_NeighborLocatorLength,	       /* sq_length */
	(binaryfunc) 0,		                       /* sq_concat */
	(ssizeargfunc) 0,		               /* sq_repeat */
	(ssizeargfunc) PyAsap_NeighborLocatorGetItem,  /* sq_item */
	0,		                               /* sq_ass_item */
	0,          		                       /* sq_contains */
	0,	                                       /* sq_inplace_concat */
	0,	                                       /* sq_inplace_repeat */
};

int PyAsap_InitNeighborLocatorInterface(PyObject *module)
{
  PyAsap_NeighborLocatorType.tp_new = NULL;  // Use factory functions
  PyAsap_NeighborLocatorType.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_FINALIZE;
  PyAsap_NeighborLocatorType.tp_methods = PyAsap_NeighborLocatorMethods;
  PyAsap_NeighborLocatorType.tp_as_sequence = &PyAsap_NeighborLocator_sequence;
  PyAsap_NeighborLocatorType.tp_repr =
    PyAsap_Representation<PyAsap_NeighborLocatorObject>;
  PyAsap_NeighborLocatorType.tp_doc = NeighborLocator_Docstring;
  PyAsap_NeighborLocatorType.tp_weaklistoffset = offsetof(PyAsap_NeighborLocatorObject,
      weakrefs);
  PyAsap_NeighborLocatorType.tp_finalize = PyAsap_Finalize<PyAsap_NeighborLocatorObject>;
  PyAsap_NeighborLocatorType.tp_dealloc = PyAsap_Dealloc;
  if (PyType_Ready(&PyAsap_NeighborLocatorType) < 0)
    return -1;
  return 0;
}


bool PyAsap_NeighborLocatorCheck(PyObject *obj)
{
  return PyObject_TypeCheck(obj, &PyAsap_NeighborLocatorType);
}

} // end namespace
