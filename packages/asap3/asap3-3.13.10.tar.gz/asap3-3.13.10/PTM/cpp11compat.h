#ifndef _CPP11COMPAT_H
#define _CPP11COMPAT_H

#include "AsapPython.h"

// Define the C++11 fixed size datatypes by their NumPy equivalents,
// to avoid depending on the C++ 2011 standard (not implemented by
// some old Linux compilers and by the default compiler on MacOS).
#define uint64_t npy_uint64
#define int8_t npy_int8
#define uint32_t npy_uint32

#endif // _CPP11COMPAT_H
