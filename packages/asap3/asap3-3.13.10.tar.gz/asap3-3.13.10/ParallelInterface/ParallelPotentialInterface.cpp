// -*- C++ -*-
// ParallelPotentialInterface.cpp: Python interface to the parallel potential.
//
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
#include "ParallelPotentialInterface.h"
#include "PotentialInterface.h"
#include "ExceptionInterface.h"
#include "ParallelPotential.h"

static PyTypeObject PyAsap_ParPotType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  "_asap.ParallelPotential",
  sizeof(PyAsap_PotentialObject),
  // The rest are initialized by name for reliability.
};
  
static char ParPot_Docstring[] = "Parallel potential wrapper.\n";

static int PyAsap_ParPotInit(PyAsap_PotentialObject *self, PyObject *args,
			     PyObject *kwargs)
{
  if (PyAsap_PotentialType.tp_init((PyObject *)self, args, kwargs) < 0)
    return -1;
  static char *kwlist[] = {"potential", "verbose", NULL};
  PyObject *pypot;
  int verb = 0;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "O|i", kwlist, &pypot, &verb))
    return -1;
  if (self->cobj != NULL)
    {
      PyErr_SetString(PyAsap_ErrorObject,				
		      "ParallelPotential object already initialized.");	
      return -1;							
    }
  self->cobj = new ParallelPotential((PyObject *)self, pypot, verb);
  if (self->cobj == NULL)
    return -1;
  return 0;
}

static char PyAsap_ParPotUpdateGhosts_Docstring[] = "Update data on ghost atoms.\n";

static PyObject *PyAsap_ParPotUpdateGhosts(PyAsap_PotentialObject *self,
					   PyObject *args)
{
  PyObject *atoms = NULL;
  if (!PyArg_ParseTuple(args, "O", &atoms))
    return NULL;
  if (self->cobj == NULL)
    {
      PyErr_SetString(PyAsap_ErrorObject,
		      "ParallelPotential object not initialized.");
      return NULL;
  }
  try {
    ParallelPotential *parpot = dynamic_cast<ParallelPotential *>(self->cobj);
    ASSERT(parpot != NULL);
    parpot->PyUpdateGhosts(atoms);
  }
  POTCATCHEXCEPTION;
  Py_RETURN_NONE;
}

static PyMethodDef PyAsap_ParPotMethods[] = {
  {"update_ghost_data", (PyCFunction) PyAsap_ParPotUpdateGhosts,
   METH_VARARGS, PyAsap_ParPotUpdateGhosts_Docstring},
  {NULL}  // Sentinel
};


namespace ASAPSPACE {

int PyAsap_InitParallelPotentialInterface(PyObject *module)
{
  InitPotentialType(PyAsap_ParPotType);
  PyAsap_ParPotType.tp_init = (initproc) PyAsap_ParPotInit;
  PyAsap_ParPotType.tp_doc = ParPot_Docstring;
  PyAsap_ParPotType.tp_methods = PyAsap_ParPotMethods;
  if (PyType_Ready(&PyAsap_ParPotType) < 0)
    return -1;
  Py_INCREF(&PyAsap_ParPotType);
  PyModule_AddObject(module, "ParallelPotential",
		     (PyObject *) &PyAsap_ParPotType);
  return 0;
}

} // end namespace

