#!/usr/bin/env python
# Copyright (C) 2003-2020  CAMP
# Please see the accompanying LICENSE file for further information.

###### MISSING:
###
### * Verify recompilation on changes in both .cpp and .h files
### * Intel support
###
######


import os
import re
import runpy
import sys
from pathlib import Path
from subprocess import PIPE, run
from sysconfig import get_platform
from sysconfig import get_config_vars
import subprocess

from setuptools import Extension, find_packages, setup
from setuptools.command.build_ext import build_ext
from setuptools.command.develop import develop as _develop
from setuptools.command.install import install as _install

recordversion = runpy.run_path(Path(__file__).parent / 'recordversion.py')

# from config import build_interpreter, check_dependencies, write_configuration

# Get the current version number:
txt = Path('Python/asap3/version.py').read_text()
version = re.search("__version__ = '(.*)'", txt)[1]
ase_version_required = re.search("__ase_version_required__ = '(.*)'", txt)[1]

long_description = '''\
ASAP (Atomic SimulAtion Program or As Soon As Possible) is a
package for large-scale molecular dynamics within the Atomic
Simulation Environment (ASE).  It implements a number of 'classical'
potentials, most importantly the Effective Medium Theory, and also the
mechanisms for domain-decomposition of the atoms.'''


libraries = []
library_dirs = []
include_dirs = []
extra_link_args = []
extra_compile_args = ['-Wno-unknown-pragmas', '-Wno-sign-compare', '-Wno-unused-function', '-Wno-c++11-compat-deprecated-writable-strings', '-Wno-unknown-attributes']
runtime_library_dirs = []
extra_objects = []
define_macros = []
undef_macros = ['NDEBUG']

mpi_libraries = []
mpi_library_dirs = []
mpi_include_dirs = []
mpi_runtime_library_dirs = []
mpi_define_macros = []

compiler = None

folders = ['Basics', 'Potentials', 'Interface', 'Brenner', 'Tools',
           'PTM', 'PTM/qcprot', 'PTM/voronoi']
kim_folders = ['OpenKIMimport']
parallel_folders = ['Parallel', 'ParallelInterface']
exclude_files = ['Interface/AsapModule.cpp']
serial_only_files = ['Interface/AsapSerial.cpp']

# XXXX Move this to later, after identification of Intel compilers
if os.name != 'nt' and run(['which', 'mpicxx'], stdout=PIPE).returncode == 0:
    mpicompiler = 'mpicxx'
else:
    mpicompiler = None

mpilinker = mpicompiler

# Search and store current git hash if possible
try:
    from ase.utils import search_current_git_hash
    githash = search_current_git_hash('asap3')
    if githash is not None:
        define_macros += [('ASAP_GITHASH', githash)]
    else:
        print('.git directory not found. ASAP git hash not written.')
except ImportError:
    print('ASE not found. ASAP git hash not written.')

# User provided customizations:
asap_config = os.environ.get('ASAP_CONFIG')
if asap_config and not Path(asap_config).is_file():
    raise FileNotFoundError(asap_config)
for siteconfig in [asap_config,
                   'siteconfig.py']:
    if siteconfig is not None:
        path = Path(siteconfig).expanduser()
        if path.is_file():
            print('Reading configuration from', path)
            exec(path.read_text())
            break
else:  # no break
    # Make default configuration
    pass

# Try to use pkgconfig to locate OpenKIM
failed = subprocess.call("pkg-config --exists libkim-api",
                         shell=True)
if not failed:
    # pkg-config is installed and so is OpenKIM.
    kimincl = subprocess.check_output(
        "pkg-config --cflags-only-I libkim-api", shell=True).decode()
    include_dirs += [f.strip() for f in kimincl.split('-I') if f]
    include_dirs += kim_folders
    kimlibd = subprocess.check_output(
        "pkg-config --libs-only-L libkim-api", shell=True).decode()
    kimliblist = [f.strip() for f in kimlibd.split('-L') if f]
    library_dirs += kimliblist
    #runtime_library_dirs += kimliblist
    kimlibl = subprocess.check_output(
        "pkg-config --libs-only-l libkim-api", shell=True).decode()
    libraries += [f.strip() for f in kimlibl.split('-l') if f]
    kimother = subprocess.check_output(
        "pkg-config --libs-only-other libkim-api", shell=True).decode()
    if kimother.strip():
        extra_link_args += [kimother.strip()]
    define_macros += [('WITH_OPENKIM', '1')]
    folders.extend(kim_folders)

if mpicompiler:
    # Build MPI-interface into _gpaw.so:
    compiler = mpicompiler
    folders += parallel_folders
    exclude_files += serial_only_files

configvars = get_config_vars()
cmdclass = {}


# A hack so we don't try to import numpy before it is installed.  Adapted from
# https://stackoverflow.com/questions/19919905/how-to-bootstrap-numpy-installation-in-setup-py
class build_ext_using_numpy(build_ext):
    def finalize_options(self):
        super().finalize_options()
        import numpy
        self.include_dirs.append(numpy.get_include())
cmdclass['build_ext'] = build_ext_using_numpy

if compiler is not None:
    # A hack to change the used compiler and linker, inspired by
    # https://shwina.github.io/custom-compiler-linker-extensions/
    
    class custom_build_ext(build_ext_using_numpy):
        def build_extensions(self):
            # Override the compiler executables.
            for attr in ('compiler_so', 'compiler_cxx', 'compiler_so_cxx', 'linker_so'):
                if hasattr(self.compiler, attr):
                    temp = getattr(self.compiler, attr)
                    temp[0] = compiler
                    self.compiler.set_executable(attr, temp)
            super().build_extensions()
    cmdclass['build_ext'] = custom_build_ext

    
# Check if we are making a source distribution.  In that case, we
# should remove the VersionInfo_autogen folder and all files in it.
versiondir = 'VersionInfo_autogen'
is_making_distro = 'sdist' in sys.argv
if is_making_distro and os.path.isdir(versiondir):
    print('Clearing', versiondir)
    for f in os.listdir(versiondir):
        os.remove(os.path.join(versiondir, f))
    os.rmdir(versiondir)

# Create the version.cpp file
try:
    host = os.uname()[1]
except:
    host = 'unknown'
if not is_making_distro:
    versioninfo = f'{versiondir}/version_info.cpp'
    folders.append(versiondir)
    if not os.path.exists(versiondir):
        os.mkdir(versiondir)
    if len(os.listdir(versiondir)) > 1:
        print(f'WARNING: Unexpected files in {versiondir}.')
        for f in os.listdir(versiondir):
            cleanup = os.path.join(versiondir, f)
            print(f'    Cleaning up {cleanup}')
            os.remove(cleanup)
    try:
        myCC = os.environ['CXX']
    except KeyError:
        myCC = compiler
    try:
        myCFLAGS = os.environ['CXXFLAGS']
    except KeyError:
        myCFLAGS = ' '.join(extra_compile_args)
    if mpicompiler:
        compinfo = f'setuptools with {myCC} {myCFLAGS}'
        comptext = recordversion['contents'] % (version, 'parallel', host, compinfo, version)
    else:
        compinfo = f'setuptools with {myCC} {myCFLAGS}'
        comptext = recordversion['contents'] % (version, 'serial', host, compinfo, version)
    if os.path.exists(versioninfo):
        with open(versioninfo) as versioncpp:
            oldtext = versioncpp.read()
    else:
        oldtext = None
    if oldtext != comptext:
        print('Recording version info into VersionInfo_autogen')
        print('  CC =', myCC)
        print('  CFLAGS =', myCFLAGS)
        with open(versioninfo, 'w') as versioncpp:
            versioncpp.write(comptext)

# List source files
sources = []
for folder in folders:
    sources += Path(folder).glob('*.cpp')
for name in exclude_files:
    sources.remove(Path(name))
include_dirs += folders
# We cannot add numpy include dirs now, as numpy may not yet be installed.
### include_dirs.append(np.get_include())

# Make build process deterministic (for 'reproducible build')
sources = [str(source) for source in sources]
sources.sort()

## Check if this is necessary
## check_dependencies(sources)

# Convert Path objects to str:
library_dirs = [str(dir) for dir in library_dirs]
include_dirs = [str(dir) for dir in include_dirs]

extensions = [Extension('_asap',
                        sources,
                        libraries=libraries,
                        library_dirs=library_dirs,
                        include_dirs=include_dirs,
                        define_macros=define_macros,
                        undef_macros=undef_macros,
                        extra_link_args=extra_link_args,
                        extra_compile_args=extra_compile_args,
                        runtime_library_dirs=runtime_library_dirs,
                        extra_objects=extra_objects)]

# write_configuration(define_macros, include_dirs, libraries, library_dirs,
#                     extra_link_args, extra_compile_args,
#                     runtime_library_dirs, extra_objects, mpicompiler,
#                     mpi_libraries, mpi_library_dirs, mpi_include_dirs,
#                     mpi_runtime_library_dirs, mpi_define_macros)


# pyproject.toml does not have long_description
# Not sure how to handle platforms platforms=['unix']
setup(
      # extras_require={'docs': ['sphinx-rtd-theme',
      #                          'graphviz'],
      #                 'devel': ['flake8',
      #                           'mypy',
      #                           'pytest-xdist',
      #                           'interrogate']},
      ext_modules=extensions,
      cmdclass=cmdclass,
    )
