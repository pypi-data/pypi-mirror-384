// -*- C++ -*-
// Templates.h: Templates used in the Python interface.
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

#ifndef _TEMPLATES_H
#define _TEMPLATES_H

#include "Asap.h"

namespace ASAPSPACE {

template<class T>
static PyObject *PyAsap_Representation(PyObject *self)
{
  string repr = ((T*)self)->cobj->GetRepresentation();
  return PyUnicode_FromString(repr.c_str());
}

template<class T>
static void PyAsap_Finalize(PyObject *self)
{
  if ( ((T*)self)->cobj != NULL )
  {
    delete ((T*)self)->cobj;
    ((T*)self)->cobj = NULL;
  }
}

static void PyAsap_Dealloc(PyObject *self)
{
    if (PyType_HasFeature(Py_TYPE(self), Py_TPFLAGS_HAVE_FINALIZE))
    {
      if (PyObject_CallFinalizerFromDealloc(self))
        return;
    }
    // Only clear out weakrefs if it is safe to do so.
    if (PyType_SUPPORTS_WEAKREFS(Py_TYPE(self)) && Py_REFCNT(self) == 0)
        PyObject_ClearWeakRefs(self);
    Py_TYPE(self)->tp_free(self);
}

} // end namespace

#endif // _TEMPLATES_H
