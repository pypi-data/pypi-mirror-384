// OpenKIMinterface.cpp - Python interface to OpenKIM models.
//
// This file is part of the optional Asap module to support OpenKIM
// models.  Defines the Python interface to the modules in the
// other files in OpenKIMimport.

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

#include "AsapPython.h"
#include "OpenKIMinterface.h"
#include "OpenKIMcalculator.h"
#include "Templates.h"
#include "ExceptionInterface.h"
#include "PotentialInterface.h"
#include "PythonConversions.h"
//#define ASAPDEBUG
#include "Debug.h"
#include <cstdlib>


namespace ASAPSPACE {

static PyTypeObject PyAsap_OpenKIMcalculatorType = {
  PyVarObject_HEAD_INIT(NULL, 0)
  "_asap.OpenKIMcalculator",
  sizeof(PyAsap_PotentialObject),
  // The rest are initialized by name for reliability.
};

char OpenKIMcalculator_Docstring[] =
    "Internal interface to an OpenKIM model\n\n\
  Parameters:\n\
    descr: OpenKIM descriptor string.\n\
    name: The name of the model.\n\n";


static int PyAsap_OpenKIMcalculatorInit(PyAsap_PotentialObject *self, PyObject *args,
                                        PyObject *kwargs)
{
  static char *kwlist[] = {"name", "verbose", NULL};
  const char *name = NULL;
  int verbose = 0;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "si:OpenKIMcalculator", kwlist,
				   &name, &verbose))
    return -1;
   
  if (PyAsap_PotentialType.tp_init((PyObject *)self, args, kwargs) < 0)
    return -1;
  try
    {
      self->cobj = new OpenKIMcalculator((PyObject *) self, name, verbose);
      self->orig_cobj = self->cobj;
    }
  catch (AsapError &e)
    {
      string msg = e.GetMessage();
      PyErr_SetString(PyAsap_ErrorObject, msg.c_str());
      return -1;
    }
  catch (AsapPythonError &e)
    {
      return -1;
    }
  if (self->cobj == NULL)
    return -1;
  return 0;
}

static PyObject *PyAsap_OpenKIMcalcGetComputeArgs(PyAsap_PotentialObject *self, PyObject *noargs)
{
  OpenKIMcalculator *cobj = dynamic_cast<OpenKIMcalculator *>(self->orig_cobj);
  ASSERT(cobj != NULL);
  std::map<string,string> arguments = cobj->GetComputeArguments();
  PyObject *result = PyDict_New();
  if (result == NULL)
    return NULL;

  for (std::map<string,string>::const_iterator it = arguments.begin(); it != arguments.end(); ++it)
  {
    PyObject *py_arg = PyUnicode_FromString(it->first.c_str());
    if (py_arg == NULL) return NULL;
    PyObject *py_sup = PyUnicode_FromString(it->second.c_str());
    if (py_sup == NULL) return NULL;
    int error = PyDict_SetItem(result, py_arg, py_sup);
    if (error)
      return NULL;
  }
  return result;
}
    
static PyObject *PyAsap_OpenKIMcalcPleaseSupport(PyAsap_PotentialObject *self,
                                                PyObject *args, PyObject *kwargs)
{
  static char *kwlist[] = {"quantity", "alloc", NULL};
  const char *quantity = NULL;
  int alloc = 0;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "si:please_support", kwlist,
                                   &quantity, &alloc))
    return NULL;
  OpenKIMcalculator *cobj = dynamic_cast<OpenKIMcalculator *>(self->orig_cobj);
  ASSERT(cobj != NULL);
  try
  {
    cobj->PleaseSupport(quantity, alloc);
  }
  catch (AsapError &e)
    {
      string msg = e.GetMessage();
      PyErr_SetString(PyAsap_ErrorObject, msg.c_str());
      return NULL;
    }
  catch (AsapPythonError &e)
    {
      return NULL;
    }
  Py_RETURN_NONE;
}

static PyObject *PyAsap_OpenKIMcalcSetTranslation(PyAsap_PotentialObject *self,
                                                 PyObject *args, PyObject *kwargs)
{
  static char *kwlist[] = {"translation", NULL};
  PyObject *translation = NULL;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "O!:set_translation", kwlist,
                                   &PyDict_Type, &translation))
    return NULL;
  OpenKIMcalculator *cobj = dynamic_cast<OpenKIMcalculator *>(self->orig_cobj);
  ASSERT(cobj != NULL);
  cobj->ClearTranslation();
  PyObject *key, *value;
  Py_ssize_t i = 0;
  while (PyDict_Next(translation, &i, &key, &value))
    {
      int z = PyLong_AsLong(key);
      int code = PyLong_AsLong(value);
      if (z == -1 || code == -1)
        return PyErr_Format(PyExc_ValueError,
            "Illegal translation %i -> %i (or non-integer type)", z, code);
      cobj->AddTranslation(z, code);
    }
  Py_RETURN_NONE;
}

static PyObject *PyAsap_OpenKIMcalcGetTypeCode(PyAsap_PotentialObject
                                               *self, PyObject *args,
                                               PyObject *kwargs)
{
  DEBUGPRINT;
  static char *kwlist[] = {"symbol", NULL};
  const char *symbol = NULL;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "s:get_type_code",
      kwlist, &symbol))
    return NULL;
  OpenKIMcalculator *cobj = dynamic_cast<OpenKIMcalculator *>(self->orig_cobj);
  ASSERT(cobj != NULL);
  try {
      int result = cobj->GetParticleTypeCode(symbol);
      return Py_BuildValue("i", result);
  }
  CATCHEXCEPTION;
  DEBUGPRINT;
}

static PyObject *PyAsap_OpenKIMcalcGetParamNamesTypes(PyAsap_PotentialObject
						      *self, PyObject *noargs)
{
  DEBUGPRINT;
  OpenKIMcalculator *cobj = dynamic_cast<OpenKIMcalculator *>(self->orig_cobj);
  ASSERT(cobj != NULL);
  vector<string> parameternames;
  vector<int> datatypes;
  vector<int> sizes;
  vector<string> descriptions;
  try {
    cobj->GetParameterNamesAndTypes(parameternames, datatypes, sizes, descriptions);
  }
  CATCHEXCEPTION;
  int nparams = parameternames.size();
  PyObject *result = PyTuple_New(nparams);
  if (result == NULL)
    return NULL;
  for (int i = 0; i < nparams; ++i)
  {
    PyObject *info = Py_BuildValue("siis",
				   parameternames[i].c_str(),
				   datatypes[i],
				   sizes[i],
				   descriptions[i].c_str());
    PyTuple_SET_ITEM(result, i, info);
  }
  return result;
}

static PyObject *PyAsap_OpenKIMcalcGetParameter(PyAsap_PotentialObject *self,
						PyObject *args, PyObject *kwargs)
{
  static char *kwlist[] = {"index", "numpytypecode", "size", NULL};
  int index = -1;
  int numpytypecode = -1;
  int size = 0;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "iii:_get_parameter", kwlist,
                                   &index, &numpytypecode, &size))
    return NULL;
  if ((index < 0) || (numpytypecode < 0) || (size < 1))
    return PyErr_Format(PyExc_ValueError,
			"Illegal _get_parameter value: index=%i  numpytypecode=%i  size=%i",
			index, numpytypecode, size);
  OpenKIMcalculator *cobj = NULL;
  cobj = dynamic_cast<OpenKIMcalculator *>(self->orig_cobj);
  ASSERT(cobj != NULL);
  try {
    if (numpytypecode == NPY_INT)
    {
      if (size == 1)
      {
	int result;
	cobj->GetParameter(index, &result);
	return PyLong_FromLong((long) result);
      }
      else
      {
	vector<int> result(size);
	cobj->GetParameter(index, result);
	return PyAsap_ArrayFromVectorInt(result);
      }
    }
    else if (numpytypecode == NPY_DOUBLE)
    {
      if (size == 1)
      {
	double result;
	cobj->GetParameter(index, &result);
	return PyFloat_FromDouble(result);
      }
      else
      {
	vector<double> result(size);
	cobj->GetParameter(index, result);
	return PyAsap_ArrayFromVectorDouble(result);
      }
    }
    else
      return PyErr_Format(PyExc_ValueError,
			  "Unsupported numpy data type %i", numpytypecode);
  }
  CATCHEXCEPTION;
}

static PyObject *PyAsap_OpenKIMcalcSetParameter(PyAsap_PotentialObject *self,
						PyObject *args, PyObject *kwargs)
{
  static char *kwlist[] = {"index", "value", NULL};
  int index=-1;
  PyObject *py_value;
  if (!PyArg_ParseTupleAndKeywords(args, kwargs,  "iO:_get_parameter", kwlist,
                                   &index, &py_value))
    return NULL;

  OpenKIMcalculator *cobj = NULL;
  cobj = dynamic_cast<OpenKIMcalculator *>(self->orig_cobj);
  ASSERT(cobj != NULL);
  
  try {
    if (PyLong_Check(py_value))
    {
      int v = (int) PyLong_AsLong(py_value);
      if ((v == -1) && (PyErr_Occurred() != NULL))
	return NULL;
      cobj->SetParameter(index, v);
    }
    else if (PyFloat_Check(py_value))
    {
      double v = PyLong_AsLong(py_value);
      if ((v == -1.0) && (PyErr_Occurred() != NULL))
	return NULL;
      cobj->SetParameter(index, v);
    }
    else if (PyArray_Check(py_value))
    {
      if (PyArray_ISINTEGER((PyArrayObject*) py_value))
      {
	vector<int> values;
	PyAsap_VectorIntFromArray(values, py_value);
	cobj->SetParameter(index, values);
      }
      else if (PyArray_ISFLOAT((PyArrayObject*) py_value))
      {
	vector<double> values;
	PyAsap_VectorDoubleFromArray(values, py_value);
	cobj->SetParameter(index, values);
      }
      else
      {
	PyErr_SetString(PyExc_ValueError,
			"Attempting to set parameter with unsupported numpy data type.");
	return NULL;
      }
    }
    else
    {
      PyErr_SetString(PyExc_ValueError,
		      "Attempting to set parameter with unknown Python object.");
      return NULL;
    }
  }
  CATCHEXCEPTION;

  Py_RETURN_NONE;
}

static PyMethodDef PyAsap_OpenKIMcalculatorMethods[] = {
  {"_get_compute_arguments", (PyCFunction) PyAsap_OpenKIMcalcGetComputeArgs,
   METH_NOARGS, "Get the KIM ComputeArguments and their support status."},
  {"please_support", (PyCFunction) PyAsap_OpenKIMcalcPleaseSupport,
   METH_VARARGS | METH_KEYWORDS, "Enable specific property"},
  {"set_translation", (PyCFunction) PyAsap_OpenKIMcalcSetTranslation,
   METH_VARARGS | METH_KEYWORDS, "Set Z->typecode translation table."},
  {"_use_imageatoms", (PyCFunction) PyAsap_PotentialUseImageAtoms,
   METH_NOARGS, PyAsap_PotentialUseImageAtoms_Docstring},
  {"get_type_code", (PyCFunction) PyAsap_OpenKIMcalcGetTypeCode,
   METH_VARARGS | METH_KEYWORDS, "Get type code of an element"},
  {"_get_parameter_names_types", (PyCFunction) PyAsap_OpenKIMcalcGetParamNamesTypes,
   METH_NOARGS, "Get descriptions of the model parameters"},
  {"_get_parameter", (PyCFunction) PyAsap_OpenKIMcalcGetParameter,
   METH_VARARGS | METH_KEYWORDS, "Get parameter (of known size and type)."},
  {"_set_parameter", (PyCFunction) PyAsap_OpenKIMcalcSetParameter,
   METH_VARARGS | METH_KEYWORDS, "Set parameter."},
  {NULL}
};



//////////////////////////////
//
//  Module initialization
//
//////////////////////////////


int PyAsap_InitOpenKIMInterface(PyObject *module)
{

  InitPotentialType(PyAsap_OpenKIMcalculatorType);
  PyAsap_OpenKIMcalculatorType.tp_init = (initproc) PyAsap_OpenKIMcalculatorInit;
  PyAsap_OpenKIMcalculatorType.tp_doc = OpenKIMcalculator_Docstring;
  PyAsap_OpenKIMcalculatorType.tp_methods = PyAsap_OpenKIMcalculatorMethods;
  if (PyType_Ready(&PyAsap_OpenKIMcalculatorType) < 0)
    return -1;
  Py_INCREF(&PyAsap_OpenKIMcalculatorType);
  PyModule_AddObject(module, "OpenKIMcalculator", (PyObject *) &PyAsap_OpenKIMcalculatorType);

  return 0;
}

} // namespace
