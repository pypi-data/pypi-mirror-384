#include "PTMInterface.h"
#include "../PTM/index_ptm.h"  // This is in the PTM submodule
#include "GetNeighborList.h"
#include "NeighborLocator.h"
#include <algorithm>
//#define ASAPDEBUG
#include "Debug.h"

#define MIN_NBRS 6

static PyObject* error(PyObject* type, char* msg)
{
  PyErr_SetString(type, msg);
  return NULL;
}

static int32_t parse_structures(PyObject *obj_types)
{
  DEBUGPRINT;
  int32_t flags = 0;
  if (obj_types == NULL || obj_types == Py_None || obj_types == Py_True)
  {
    flags = PTM_CHECK_ALL;
  }
  else
  {
    if (!PyTuple_Check(obj_types))
    {
      PyErr_SetString(PyExc_TypeError, "types must be a tuple of strings");
      return -1;
    }

    int num_types = PyTuple_Size(obj_types);

    int i = 0;
    for (i=0;i<num_types;i++)
    {
      PyObject* obj_type = PyTuple_GetItem(obj_types, i);
      if (obj_type == NULL)
        return -1;

      if (!PyBytes_Check(obj_type))
      {
        PyErr_SetString(PyExc_TypeError, "type is not an ASCII string (bytes)");
        return -1;
      }

      char* type = PyBytes_AsString(obj_type);
      if (type == NULL)
        return -1;

      if (strcmp(type, "sc") == 0)
        flags |= PTM_CHECK_SC;
      else if (strcmp(type, "fcc") == 0)
        flags |= PTM_CHECK_FCC;
      else if (strcmp(type, "hcp") == 0)
        flags |= PTM_CHECK_HCP;
      else if (strcmp(type, "ico") == 0)
        flags |= PTM_CHECK_ICO;
      else if (strcmp(type, "bcc") == 0)
        flags |= PTM_CHECK_BCC;
      else
      {
        PyErr_SetString(PyExc_ValueError, "unrecognized type string");
        return -1;
      }
    }
  }
  DEBUGPRINT;
  return flags;
}

namespace ASAPSPACE {

class PyAsap_argsort_vector
{
public:
  PyAsap_argsort_vector(vector<double> *values) : vals(values) {}
  bool operator() (const int& a, const int& b) const { return (*vals)[a] < (*vals)[b]; }
private:
  vector<double> *vals;
};

PyObject* PyAsap_PTMall(PyObject* noself, PyObject* args, PyObject* kwargs)
{
  PyObject* obj_atoms = NULL;
  double cutoff;
  PyObject* obj_types = NULL;
  int calculate_strains = false;
  int quick = false;
  int return_nblist = false;
  PyObject *obj_return_mappings = NULL;
  int minimum_image = 1;
  DEBUGPRINT;
  
  static char* argnames[] = {"atoms", "cutoff", "target_structures",
			     "calculate_strains", "quick",
			     "return_nblist", "return_mappings", 
                             "minimum_image", NULL};
  if (!PyArg_ParseTupleAndKeywords(args, kwargs, "Od|OiiiOi:PTM_allatoms",
				   argnames, &obj_atoms, &cutoff,
                                   &obj_types, &calculate_strains, &quick,
				   &return_nblist, &obj_return_mappings,
                                   &minimum_image))
    return NULL;

  DEBUGPRINT;
  int32_t flags = parse_structures(obj_types);
  if (flags == -1)
    return NULL;

  bool use_topo = !quick;    // Topological ordering (a bit slower, but better).

  // Check if mappings should be returned
  int32_t return_mappings = 0;
  if (obj_return_mappings != NULL && obj_return_mappings != Py_None)
    {
      return_mappings = parse_structures(obj_return_mappings);
    }

  DEBUGPRINT;
  // Create a full neighbor list object
  PyObject *py_nblist = GetSecondaryNeighborList(obj_atoms, cutoff, minimum_image);
  if (py_nblist == NULL)
    return NULL;
  NeighborLocator *nl = ((PyAsap_NeighborLocatorObject*) py_nblist)->cobj;
  assert(nl != NULL);
  // Mark that this is a full list - in case it is returned to Python.
  ((PyAsap_NeighborLocatorObject*) py_nblist)->fulllist = true;

  Atoms *atoms = nl->GetAtoms();
  atoms->Begin(obj_atoms);
  npy_intp nAtoms = atoms->GetNumberOfAtoms();

  // Now allocate the arrays we need for the return values
  npy_intp dims_4[2] = {nAtoms, 4};
  npy_intp dims_3_3[3] = {nAtoms, 3, 3};

  PyObject *arr_type = PyArray_SimpleNew(1, &nAtoms, NPY_INT32);
  PyObject *arr_alloy = PyArray_SimpleNew(1, &nAtoms, NPY_INT32);
  PyObject *arr_scale = PyArray_SimpleNew(1, &nAtoms, NPY_DOUBLE);
  PyObject *arr_rmsd = PyArray_SimpleNew(1, &nAtoms, NPY_DOUBLE);
  PyObject *arr_rot = PyArray_SimpleNew(2, dims_4, NPY_DOUBLE);
  PyObject *arr_distance = PyArray_SimpleNew(1, &nAtoms, NPY_DOUBLE);
  PyObject *arr_latconst = PyArray_SimpleNew(1, &nAtoms, NPY_DOUBLE);
  PyObject *arr_strain = NULL;
  if (calculate_strains)
    arr_strain = PyArray_SimpleNew(3, dims_3_3, NPY_DOUBLE);
  if (arr_type == NULL || arr_alloy == NULL || arr_scale == NULL
      || arr_rmsd == NULL || arr_rot == NULL
      || arr_distance == NULL || arr_latconst == NULL ||
      ((arr_strain == NULL) && calculate_strains))
  {
    Py_XDECREF(arr_type);
    Py_XDECREF(arr_alloy);
    Py_XDECREF(arr_scale);
    Py_XDECREF(arr_rmsd);
    Py_XDECREF(arr_rot);
    Py_XDECREF(arr_distance);
    Py_XDECREF(arr_latconst);
    Py_XDECREF(arr_strain);
    Py_DECREF(py_nblist);
    return NULL;
  }

  // Now create the dict we may need to return the mappings
  int8_t mapping_buffer[15];
  int8_t *mapping = NULL;
  PyObject *dict_mappings = NULL;
  if (return_mappings)
    {
      mapping=mapping_buffer;
      dict_mappings = PyDict_New();
      assert(dict_mappings != NULL);  // Cannot really fail.
    }

  DEBUGPRINT;
  npy_int32 *type_p = (npy_int32*) PyArray_DATA((PyArrayObject*) arr_type);
  npy_int32 *alloy_p = (npy_int32*)PyArray_DATA((PyArrayObject*) arr_alloy);
  double *scale_p = (double *) PyArray_DATA((PyArrayObject*) arr_scale);
  double *rmsd_p = (double *) PyArray_DATA((PyArrayObject*) arr_rmsd);
  double *rot_p = (double *) PyArray_DATA((PyArrayObject*) arr_rot);
  double *distance_p = (double *) PyArray_DATA((PyArrayObject*) arr_distance);
  double *latconst_p = (double *) PyArray_DATA((PyArrayObject*) arr_latconst);
  double *strain_p = NULL;
  if (calculate_strains)
    strain_p = (double *) PyArray_DATA((PyArrayObject*) arr_strain);

  // Loop over atoms, calculate PTM
  int cnt_ptm = 0;
  int cnt_skip = 0;
  int maxnb = nl->MaxNeighborListLength();
  vector<int> neighbors(maxnb);
  vector<Vec> diffs(maxnb);
  vector<double> diffs2(maxnb);
  vector<int> indices;
  vector<Vec> ptm_neighbors(15);
  vector<int32_t> ptm_z(15);
  PyAsap_argsort_vector argsort(&diffs2);
  const asap_z_int *z = atoms->GetAtomicNumbers();

  DEBUGPRINT;
  // Sanity check for casts below
  assert(sizeof(npy_int32) == sizeof(int32_t));

  // Initialize thread-local storage for PTM routine.
  ptm_local_handle_t ptm_local_handle = ptm_initialize_local();
  assert(ptm_local_handle != NULL);
  
  DEBUGPRINT;
  for (int i = 0; i < nAtoms; i++)
  {
    int32_t myflags = flags;  // Which structure can we search for for THIS atom?
    int32_t usenb = 14;       // Number of neighbors actually used for this atom.
    int nmax = maxnb;
    int n = nl->GetFullNeighbors(i, &neighbors[0], &diffs[0], &diffs2[0], nmax);
    assert(n < maxnb);
    if (n < 14)
      {
	myflags = myflags & ~PTM_CHECK_BCC;  // Too few neighbors for BCC detection.
	usenb = 12;
      }
    if (n < 12)
      {
	myflags = myflags & ~(PTM_CHECK_FCC | PTM_CHECK_HCP | PTM_CHECK_ICO);  // No FCC/HCP/ICO check
	usenb = 6;
      }
    if (n < 6)
      {
	myflags = myflags & ~PTM_CHECK_SC;  // No SC (i.e. nothing left to check).
	usenb = 0;
      }
    if (myflags)
    {
      // Do the PTM
      // First sort the neighbors
      indices.resize(n);
      for (int j = 0; j < n; j++)
        indices[j] = j;
      std::sort(indices.begin(), indices.end(), argsort);
      ptm_neighbors[0][0] = ptm_neighbors[0][1] = ptm_neighbors[0][2] = 0.0;
      ptm_z[0] = z[i];
      for (int j = 0; j < usenb; j++)
      {
        ptm_neighbors[j+1] = diffs[indices[j]];
        ptm_z[j+1] = z[neighbors[indices[j]]];
      }
      // Do it!
      double F[9], lstsq_residual[3], P[9];
      if (calculate_strains)
        ptm_index(ptm_local_handle, usenb+1, (double *) &ptm_neighbors[0],
		  &ptm_z[0], myflags, use_topo,
                  (int32_t *) type_p, (int32_t *) alloy_p, scale_p, rmsd_p,
                  rot_p, F, lstsq_residual, strain_p, P,
		  mapping, distance_p, latconst_p);
      else
        ptm_index(ptm_local_handle, usenb+1, (double *) &ptm_neighbors[0],
		  &ptm_z[0], myflags, use_topo,
                  (int32_t *) type_p, (int32_t *) alloy_p, scale_p, rmsd_p,
                  rot_p, NULL, NULL, NULL, NULL,
		  mapping, distance_p, latconst_p);
      // Copy the mapping if needed
      if (return_mappings)
	{
	  npy_intp maplen = 0;
	  if (*type_p == PTM_MATCH_FCC && (return_mappings & PTM_CHECK_FCC))
	    maplen = 12;
	  else if (*type_p == PTM_MATCH_HCP && (return_mappings & PTM_CHECK_HCP))
	    maplen = 12;
	  else if (*type_p == PTM_MATCH_BCC && (return_mappings & PTM_CHECK_BCC))
	    maplen = 14;
	  else if (*type_p == PTM_MATCH_ICO && (return_mappings & PTM_CHECK_ICO))
	    maplen = 12;
	  else if (*type_p == PTM_MATCH_SC && (return_mappings & PTM_CHECK_SC))
	    maplen = 6;
	  if (maplen)
	    {
	      PyObject *key = PyLong_FromLong(i);
	      PyObject *value = PyArray_SimpleNew(1, &maplen, NPY_INT);
	      if (key == NULL || value == NULL || PyDict_SetItem(dict_mappings, key, value) == -1)
		{
		  Py_DECREF(arr_type);
		  Py_DECREF(arr_alloy);
		  Py_DECREF(arr_scale);
		  Py_DECREF(arr_rmsd);
		  Py_DECREF(arr_rot);
		  Py_DECREF(arr_distance);
		  Py_DECREF(arr_latconst);
		  Py_XDECREF(arr_strain);
		  Py_DECREF(py_nblist);
		  Py_DECREF(dict_mappings);
		  Py_XDECREF(key);
		  Py_XDECREF(value);
		  return NULL;
		}
	      npy_int *mapdata = (npy_int *) PyArray_DATA((PyArrayObject*) value);
	      for (int j = 0; j < maplen; j++)
		{
		  // mapdata[j] = neighbors[indices[mapping[j+1]-1]];
		  int m = mapping[j+1]-1;
		  assert(m >= 0);
		  assert(m < indices.size());
		  int idx = indices[m];
		  assert(idx >= 0 && idx < indices.size());
		  mapdata[j] = neighbors[idx];
		}
	      Py_DECREF(key);
	      Py_DECREF(value);
	    }	  
	}
      type_p++;
      alloy_p++;
      scale_p++;
      rmsd_p++;
      rot_p += 4;
      distance_p++;
      latconst_p++;
      if (calculate_strains)
        strain_p += 9;
      cnt_ptm++;
    }
    else
    {
      // Not enough neighbors
      *type_p++ = PTM_MATCH_NONE;
      *alloy_p++ = PTM_ALLOY_NONE;
      *scale_p++ =  INFINITY;
      *rmsd_p++ = INFINITY;
      *distance_p++ = INFINITY;
      *latconst_p++ = INFINITY;
      memset(rot_p, 0, 4*sizeof(double));
      rot_p += 4;
      if (calculate_strains)
      {
        memset(strain_p, 0, 9*sizeof(double));
        strain_p += 9;
      }
      cnt_skip++;
    }
  }
  DEBUGPRINT;
  atoms->End();

  // Build the return dictionary
  PyObject *result = PyDict_New();
  if (!result)
    {
      Py_DECREF(py_nblist);
      return NULL;
    }
  PyDict_SetItemString(result, "structure", arr_type);
  Py_DECREF(arr_type);
  PyDict_SetItemString(result, "alloytype", arr_alloy);
  Py_DECREF(arr_alloy);
  PyDict_SetItemString(result, "scale", arr_scale);
  Py_DECREF(arr_scale);
  PyDict_SetItemString(result, "rmsd", arr_rmsd);
  Py_DECREF(arr_rmsd);
  PyDict_SetItemString(result, "orientation", arr_rot);
  Py_DECREF(arr_rot);
  PyDict_SetItemString(result, "distance", arr_distance);
  Py_DECREF(arr_distance);
  PyDict_SetItemString(result, "latticeconstant", arr_latconst);
  Py_DECREF(arr_latconst);
  if (calculate_strains)
  {
    PyDict_SetItemString(result, "strain", arr_strain);
    Py_DECREF(arr_strain);
  }
  if (return_mappings)
    {
      PyDict_SetItemString(result, "mappings", dict_mappings);
      Py_DECREF(dict_mappings);
    }
  PyObject *info = Py_BuildValue("ii", cnt_ptm, cnt_skip);
  if (!info)
    {
      Py_DECREF(py_nblist);
      Py_DECREF(result);
      return NULL;
    }
  PyDict_SetItemString(result, "info", info);
  Py_DECREF(info);
  if (return_nblist)
    PyDict_SetItemString(result, "nblist", py_nblist);
  DEBUGPRINT;

  Py_DECREF(py_nblist);
  return result;
}

void PyAsap_InitPTMmodule()
{
  DEBUGPRINT;
  ptm_initialize_global();
  DEBUGPRINT;
}

} // namespace
