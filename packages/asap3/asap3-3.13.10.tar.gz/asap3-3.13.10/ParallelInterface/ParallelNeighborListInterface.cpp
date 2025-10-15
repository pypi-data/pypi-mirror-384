
#include "AsapPython.h"
#include "ParallelNeighborListInterface.h"
#include "NeighborLocatorInterface.h"
#include "ExceptionInterface.h"
#include "PythonConversions.h"
#include "Templates.h"
#include "SecondaryNeighborLocator.h"
#include "ParallelAtoms.h"
#include "NormalAtoms.h"
#include "ImageAtoms.h"
//#define ASAPDEBUG
#include "Debug.h"

// Note: in parallel simulations, the Python interface overrides
// PyAsap_NewNeighborCellLocator_Py with this function
PyObject *PyAsap_NewNeighborCellLocator_Parallel(PyObject *noself, PyObject *args,
                                           PyObject *kwargs)
{
  static char *kwlist[] = {"rCut", "atoms", "driftfactor", "minimum_image", NULL};

  PyObject *atoms = Py_None;
  double rCut = 0.0;
  double driftfactor = 0.05;
  int minimum_image = 1;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "dO|di:NeighborCellLocator",
                                   kwlist, &rCut, &atoms, &driftfactor, &minimum_image))
    return NULL;
  DEBUGPRINT;
  if (rCut <= 0.0)
    {
      PyErr_SetString(PyExc_ValueError,
                      "NeighborCellLocator: Cutoff must be greater than zero.");
      return NULL;
    }

  // Detect if the atoms have ghost atoms.  In that case a parallel access object
  // is used.
  DEBUGPRINT;
  Atoms *access = NULL;
  bool includeghostneighbors = false;
  if (atoms != Py_None && PyObject_HasAttrString(atoms, "ghosts"))
    {
      if (!minimum_image)
      {
        PyErr_SetString(PyExc_ValueError,
          "NeighborCellLocator: Cannot disable minimum image convention in parallel simulations.");
        return NULL;
      }
      DEBUGPRINT;
      access = new ParallelAtoms(atoms);
      includeghostneighbors = true;
      DEBUGPRINT;
    }
  try {
    DEBUGPRINT;
    if (!minimum_image)
    {
      assert(access == NULL);
      access = new NormalAtoms();
      access = new ImageAtoms(access);
      assert(access != NULL);
    }
    PyAsap_NeighborLocatorObject *self =
      PyAsap_NewSecondaryNeighborLocator(access, rCut, driftfactor);
    DEBUGPRINT;
    if (access != NULL)
      AsapAtoms_DECREF(access);
    if (includeghostneighbors)
    {
      SecondaryNeighborLocator *nb = dynamic_cast<SecondaryNeighborLocator*>(self->cobj);
      assert(nb != NULL);
      nb->EnableNeighborsOfGhosts();
    }
    if (atoms != Py_None)
    {
      DEBUGPRINT;
      self->cobj->CheckAndUpdateNeighborList(atoms);
    }
    DEBUGPRINT;
    return (PyObject *) self;
  }
  CATCHEXCEPTION;
}

