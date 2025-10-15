#### This Makefile requires GNU make.  It is unlikely to work with other versions.
#### See installation instructions in the README file or at wiki.fysik.dtu.dk/asap
####
#### Important: All configuration should be done in the configuration files
#### named makefile-XXXX
####
#### This Makefile looks for configuration files in the following order
####   1.  makefile-local
####   2.  makefile-HOSTNAME
#### [ 3.  makefile-nifheim6   (ONLY if compiling on the Niflheim cluster) ]
####   4.  makefile-KERNELNAME-ARCH-COMPILER
####   5.  makefike-KERNELNAME-ARCH
####   6.  makefile-default
####
#### where HOSTNAME is the host name, KERNELNAME is e.g. Linux or Darwin,
#### ARCH is the architectur (e.g. x86_64), and COMPILER is "gnu" or "intel"
#### and reflects if the icc compiler is installed.
####
#### You can see the output of these variables by typing
####   make info
####
#### TO CUSTOMIZE THIS:
####
#### If you need to change an existing configuration, copy it to makefile-local
#### (or makefile-hostname) and edit it.
####
#### If you have an unsupported architecture, create a new makefike-KERNELNAME-ARCH
#### file, and edit it.  Please send it to me at schiotz@fysik.dtu.dk



# ARCH is the machine architecture, used to select compiler flags etc
# On some weird machines (Macs!) uname -m returns a name with a space in it.
# It will be replaces with an underscore
ARCH := $(shell uname -m | sed -e 's/ /_/g')
HOSTNAME := $(shell uname -n | sed -e 's/ /_/g')
KERNELNAME := $(shell uname -s | sed -e 's/ /_/g')

# The Intel compiler (icc) can be used on Pentium 4 machines to gain at least
# a factor of two in performance.  A similar gain is obtained by using the
# PathScale compiler on and AMD processor.  The COMPILER variable indicates
# which compiler should be used.  It can take the values "pathscale",
# "intel" and "gnu" on i686 and x86_64 architectures, and at least the value
# "gnu" on other architectures.  If unset, it tries to auto-detect.
ifndef COMPILER
# Test for icc command if ARCH is i686 or x86_64
ifneq (,$(filter i686 x86_64,$(ARCH)))
HAS_ICC := $(shell which icc 2> /dev/null)
HAS_ICX := $(shell which icx 2> /dev/null)
ifdef HAS_ICX
COMPILER = intel
else ifdef HAS_ICC
COMPILER = intel
else
COMPILER = gnu
endif
endif
endif

# Now include the right file for the specific architecture.
ifneq ("$(wildcard makefile-local)","")
MAKECONFIGURATION = makefile-local
else ifneq ("$(wildcard makefile-$(HOSTNAME))","")
MAKECONFIGURATION = makefile-$(HOSTNAME)
else ifneq ("$(wildcard makefile-$(FYS_PLATFORM))","")
MAKECONFIGURATION = makefile-$(FYS_PLATFORM)
else ifneq ("$(wildcard makefile-$(KERNELNAME)-$(ARCH)-$(COMPILER))","")
MAKECONFIGURATION = makefile-$(KERNELNAME)-$(ARCH)-$(COMPILER)
else ifneq ("$(wildcard makefile-$(KERNELNAME)-$(ARCH))","")
MAKECONFIGURATION = makefile-$(KERNELNAME)-$(ARCH)
else
MAKECONFIGURATION = makefile-default
endif

ifeq ($(MAKECONFIGURATION), makefile-default)
$(warning WARNING: No suitable configuration found.)
endif
$(info Getting configuration from $(MAKECONFIGURATION))
include $(MAKECONFIGURATION)

# Some versions of the Intel compilers are broken, and need to be
# blacklisted.  Remember also to blacklist them in setup.py
ifeq ($(COMPILER), intel)
DUMPVERSION=$(shell $(CXX) -dumpversion)
ifeq ($(DUMPVERSION), 15.0.1)
$(error ERROR: Cannot compile with Intel compiler version $(DUMPVERSION) due to optimization error)
endif
ifeq ($(DUMPVERSION), 17.0.1)
$(error ERROR: Cannot compile with Intel compiler version $(DUMPVERSION) due to optimization error)
endif
ifeq ($(DUMPVERSION), 17.0.2)
$(error ERROR: Cannot compile with Intel compiler version $(DUMPVERSION) due to optimization error)
endif
endif

# The python executable.  May be overridden IN THE CONFIGURATION FILE for broken installations such
# as the former DTU databar systems, or to select Python 3.
ifndef PYTHON
PYTHON=python
endif


# The version number of Asap
VERSION := $(shell $(PYTHON) Python/asap3/version.py)

# PYVER is the Python version
PYVER := $(shell $(PYTHON) -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')


# POSTFIX is used to select different object directories when compiling for 
# debugging, profiling etc.
#POSTFIX =

# Now get some include directories
ifndef PYTHON_INCLUDE
PYTHON_INCLUDE := $(shell $(PYTHON) -c 'import sysconfig; print("-I"+sysconfig.get_path("include"))')
endif
ifndef NUMPY_INCLUDE
NUMPY_INCLUDE:= $(shell $(PYTHON) -c 'import numpy; print("-I"+numpy.get_include())')
endif

# If KIM_HOME is set, set ASAP_KIM_INC and ASAP_KIM_LIB
# This is intended for a system-wide installation of OpenKIM
ifdef KIM_HOME
ifndef ASAP_KIM_INC
ASAP_KIM_INC := -I$(KIM_HOME)/include/kim-api
endif
ifndef ASAP_KIM_LIB
ASAP_KIM_LIB := -L$(KIM_HOME)/lib64 -L$(KIM_HOME)/lib -lkim-api
endif
endif

# Try to determine if pkg-config knows about OpenKIM
# Note that if KIM_HOME was set, that takes precedence.
PKGCONFIG_KNOWS_KIM := $(shell pkg-config --exists libkim-api 1>/dev/null 2>&1 && echo yes || echo no)
ifeq ($(PKGCONFIG_KNOWS_KIM),yes)
    ASAP_KIM_INC := $(shell pkg-config --cflags libkim-api)
    ASAP_KIM_LIB := $(shell pkg-config --libs libkim-api)
endif


# The object directories where object files are placed.
ifndef OBJDIR
OBJDIR = $(ARCH)$(POSTFIX)
endif
ifndef BINDIR
BINDIR = $(ARCH)
endif


# Source files

CXXSRC_BASICS = AsapObject.cpp NormalAtoms.cpp Vec.cpp Exception.cpp  \
	NeighborCellLocator.cpp NeighborList.cpp NeighborLocator.cpp Matrix3x3.cpp \
	MonteCarloAtoms.cpp Debug.cpp DynamicAtoms.cpp \
	MolecularDynamics.cpp VelocityVerlet.cpp Timing.cpp \
	NeighborList2013.cpp Langevin.cpp RandomNumbers.cpp \
	ImageAtoms.cpp ImagePotential.cpp  \

CXXSRC_POTENTIALS = Potential.cpp EMT.cpp MonteCarloEMT.cpp EMT2013.cpp \
	EMTDefaultParameterProvider.cpp EMTRasmussenParameterProvider.cpp \
	EMTPythonParameterProvider.cpp LennardJones.cpp Morse.cpp RGL.cpp \
	RahmanStillingerLemberg.cpp MetalOxideInterface.cpp \
	MetalOxideInterface2.cpp

# Do not include autogenerated Basics/version.cpp on the list above, as that
# would cause superfluous compilations.

CXXSRC_INTERFACE = PotentialInterface.cpp \
	ExceptionInterface.cpp PythonConversions.cpp \
	EMTParameterProviderInterface.cpp NeighborLocatorInterface.cpp \
	RDFInterface.cpp ToolsInterface.cpp DynamicsInterface.cpp \
	OpenMPInterface.cpp PTMInterface.cpp

CXXSRC_TOOLS = RawRadialDistribution.cpp CoordinationNumbers.cpp CNA.cpp \
	GetNeighborList.cpp FullCNA.cpp SecondaryNeighborLocator.cpp

CXXSRC_PTM = canonical.cpp graph_data.cpp convex_hull_incremental.cpp \
	index_ptm.cpp alloy_types.cpp deformation_gradient.cpp \
	normalize_vertices.cpp neighbour_ordering.cpp initialize_data.cpp

CXXSRC_PTM_QC = qcprot/quat.cpp qcprot/polar.cpp

CXXSRC_PTM_V = voronoi/cell.cpp

CSRC_EXTRA =

CXXSRC_PARALLEL = RegularGridDecomposition.cpp ParallelAtoms.cpp \
	ParallelPotential.cpp AsapMPI.cpp

SERIAL_INTERFACE = AsapSerial.cpp

CXXSRC_PARINTERFACE = AsapParallel.cpp ParallelAtomsInterface.cpp \
	ParallelPotentialInterface.cpp ParallelNeighborListInterface.cpp \
	mpimodule.cpp

CXXSRC_BRENNER = BrennerPotential.cpp caguts.cpp expand.cpp inter2d_iv.cpp \
	mtable.cpp pibond.cpp radic.cpp radicdata.cpp sili_germ.cpp \
	spgch.cpp bcuint.cpp

CXXSRC_OPENKIM = OpenKIMinterface.cpp OpenKIMcalculator.cpp 

TEMP_DOC_DIR = /tmp/Asap-documentation-$(USER)

# Default values
ifndef MPICC 
MPICC=env LAMMPICC='$(CC)' OMPI_MPICC='$(CC)' mpicc
endif
ifndef MPICXX
MPICXX=env LAMMPICXX='$(CXX)' OMPI_MPICXX='$(CXX)' mpicxx
endif
ifndef MPICFLAGS
MPICFLAGS = $(CFLAGS)
endif
ifndef MPICXXFLAGS
MPICXXFLAGS= $(CXXFLAGS)
endif
ifndef DEPENDCC
DEPENDCC = $(CC)
endif
ifndef DEPENDCXX
DEPENDCXX= $(CXX)
endif
ifndef DEPENDMPICC
DEPENDMPICC = $(MPICC)
endif
ifndef DEPENDMPICXX
DEPENDMPICXX = $(MPICXX)
endif
ifndef DEPENDFLAG
DEPENDFLAG = -MM
endif
ifndef DEPENDCLEAN
DEPENDCLEAN = sed -e 's@/usr/[^ ]*@@g' | sed -e '/^ *\\ *$$/d'
endif
ifndef LIBS
LIBS = -lm 
endif
ifndef CXXSHARED
CXXSHARED = $(CXX) -shared
endif
ifndef MPICXXSHARED
MPICXXSHARED = $(MPICXX) -shared
endif

PAROBJDIR = $(OBJDIR)$(PARPOSTFIX)

COMMONOBJS := $(CXXSRC_BASICS:%.cpp=Basics/$(OBJDIR)/%.o) \
	$(CXXSRC_POTENTIALS:%.cpp=Potentials/$(OBJDIR)/%.o) \
	$(CXXSRC_TOOLS:%.cpp=Tools/$(OBJDIR)/%.o) \
	$(CXXSRC_INTERFACE:%.cpp=Interface/$(OBJDIR)/%.o) \
	$(CXXSRC_BRENNER:%.cpp=Brenner/$(OBJDIR)/%.o) \
	$(CXXSRC_PTM:%.cpp=PTM/$(OBJDIR)/%.o) \
	$(CXXSRC_PTM_QC:qcprot/%.cpp=PTM/$(OBJDIR)/%.o) \
	$(CXXSRC_PTM_V:voronoi/%.cpp=PTM/$(OBJDIR)/%.o) \
	$(CSRC_EXTRA:%.c=Basics/$(OBJDIR)/%.o) 

ifdef ASAP_KIM_INC
COMMONOBJS += $(CXXSRC_OPENKIM:%.cpp=OpenKIMimport/$(OBJDIR)/%.o) 
endif

SERIALOBJS := $(COMMONOBJS) \
	$(SERIAL_INTERFACE:%.cpp=Interface/$(OBJDIR)/%.o)

PARALLELOBJS := $(CXXSRC_BASICS:%.cpp=Basics/$(PAROBJDIR)/%.o) \
	$(CXXSRC_POTENTIALS:%.cpp=Potentials/$(PAROBJDIR)/%.o) \
	$(CXXSRC_TOOLS:%.cpp=Tools/$(PAROBJDIR)/%.o) \
	$(CXXSRC_INTERFACE:%.cpp=Interface/$(PAROBJDIR)/%.o) \
	$(CXXSRC_BRENNER:%.cpp=Brenner/$(PAROBJDIR)/%.o) \
	$(CXXSRC_PTM:%.cpp=PTM/$(PAROBJDIR)/%.o) \
	$(CXXSRC_PTM_QC:qcprot/%.cpp=PTM/$(PAROBJDIR)/%.o) \
	$(CXXSRC_PTM_V:voronoi/%.cpp=PTM/$(PAROBJDIR)/%.o) \
	$(CSRC_EXTRA:%.c=Basics/$(PAROBJDIR)/%.o) \
	$(CXXSRC_PARALLEL:%.cpp=Parallel/$(PAROBJDIR)/%.o) \
	$(CXXSRC_PARINTERFACE:%.cpp=ParallelInterface/$(PAROBJDIR)/%.o) \
	$(CSRC_PARINTERFACE:%.c=ParallelInterface/$(PAROBJDIR)/%.o) 

ifdef ASAP_KIM_INC
PARALLELOBJS += $(CXXSRC_OPENKIM:%.cpp=OpenKIMimport/$(PAROBJDIR)/%.o) 
endif

INCLUDES = -IBasics -IPotentials -ITools -IParallel -IInterface -IParallelInterface \
	 -IBrenner 
ifdef ASAP_KIM_INC
INCLUDES += -IOpenKIMimport $(ASAP_KIM_INC)
endif
INCLUDES += $(PYTHON_INCLUDE) $(NUMPY_INCLUDE)

ifdef ASAP_KIM_LIB
LIBS += $(ASAP_KIM_LIB)
CXXFLAGS += -DWITH_OPENKIM
MPICXXFLAGS += -DWITH_OPENKIM
DEPENDFLAGS += -DWITH_OPENKIM
endif

# Name of binaries
ifndef BINSERIAL
BINSERIAL = _asap_serial.so
endif
ifndef BINPARALLEL
BINPARALLEL = _asap.so
endif

.DEFAULT: help

help:
	@echo
	@echo "ASAP version $(VERSION) compilation:"
	@echo
	@echo "To compile the full version"
	@echo "    make depend"
	@echo "    make all"
	@echo
	@echo "To compile the serial-only version:"
	@echo "    make depend"
	@echo "    make serial"
	@echo
	@echo "To make a tar file for distribution:"
	@echo "    python setup.py sdist"
	@echo
	@echo "To check the ASAP version number:"
	@echo "    make version"
	@echo
	@echo "To check configuration variables:"
	@echo "    make info"
	@echo

all: parallel

serial: $(BINDIR) Depend/$(OBJDIR)/depend.timestamp Basics/$(OBJDIR) Potentials/$(OBJDIR) Tools/$(OBJDIR) PTM/$(OBJDIR) Interface/$(OBJDIR) Brenner/$(OBJDIR) OpenKIMimport/$(OBJDIR) $(BINDIR)/$(BINSERIAL)

parallel: $(BINDIR) Depend/$(OBJDIR)/depend.timestamp Basics/$(PAROBJDIR) Potentials/$(PAROBJDIR) Tools/$(PAROBJDIR) PTM/$(PAROBJDIR) Interface/$(PAROBJDIR) Brenner/$(PAROBJDIR) OpenKIMimport/$(PAROBJDIR) Parallel/$(PAROBJDIR) ParallelInterface/$(PAROBJDIR)  $(BINDIR)/$(BINPARALLEL) 

$(BINDIR)/$(BINSERIAL): $(SERIALOBJS) Python/asap3/version.py scripts/asap-sbatch
	test -h $(BINDIR)/asap-sbatch || (cd $(BINDIR) && ln -sf ../scripts/asap-sbatch)
	$(PYTHON) recordversion.py "$(VERSION)" "serial" "$(CXX)" "$(CXXFLAGS)" > Basics/$(OBJDIR)/version.cpp
	$(CXX) -c $(CXXFLAGS) $(INCLUDES) Basics/$(OBJDIR)/version.cpp -o Basics/$(OBJDIR)/version.o 
	rm -f $@
	$(CXXSHARED) $(SERIALOBJS) Basics/$(OBJDIR)/version.o -o $@ $(LIBS)

$(BINDIR)/$(BINPARALLEL): $(PARALLELOBJS) Python/asap3/version.py scripts/asap-sbatch
	test -h $(BINDIR)/asap-sbatch || (cd $(BINDIR) && ln -sf ../scripts/asap-sbatch)
	$(PYTHON) recordversion.py "$(VERSION)" "parallel" "$(MPICXX)" "$(MPICXXFLAGS)" > Basics/$(PAROBJDIR)/version_u.cpp
	$(MPICXX) -c $(MPICXXFLAGS) $(INCLUDES) Basics/$(PAROBJDIR)/version_u.cpp -o Basics/$(PAROBJDIR)/version_u.o 
	rm -f $@
	$(MPICXXSHARED) $(PARALLELOBJS) Basics/$(PAROBJDIR)/version_u.o -o $@ $(LIBS)


clean:
	rm -rf Basics/$(OBJDIR) Potentials/$(OBJDIR) Tools/$(OBJDIR) \
		Interface/$(OBJDIR) Parallel/$(PAROBJDIR) \
		ParallelInterface/$(PAROBJDIR) Brenner/$(OBJDIR) \
		OpenKIMimport/$(OBJDIR) PTM/$(OBJDIR) $(OBJDIR) $(BINDIR)
	rm -rf Basics/$(PAROBJDIR) Potentials/$(PAROBJDIR) Tools/$(PAROBJDIR) \
		Interface/$(PAROBJDIR) Brenner/$(PAROBJDIR) \
		OpenKIMimport/$(PAROBJDIR) PTM/$(PAROBJDIR)

cleanall:
	@echo "**** Removing version.cpp files"
	find . -name 'version.cpp' -print -delete
	@echo "**** Removing .o files"
	find . -name '*.o' -print -delete
	@echo "**** Removing .a files"
	find . -name '*.a' -print -delete
	@echo "**** Removing .optrpt files (Intel optimization reports)"
	find . -name '*.optrpt' -print -delete
	@echo "**** Removing -pyc and .pyo files"
	find . -name '*.pyc' -print -delete
	find . -name '*.pyo' -print -delete
	@echo "**** Removing executables"
	find . -name 'asapserial3.so' -print -delete
	find . -name '_asap*.so' -print -delete
	find . -name 'asap-python*' -print -delete
	find . -name 'ptmmodule.so' -print -delete
	@echo "**** Removing special build targets."
	find . -name 'asap-qsub' -type l -print -delete
	find . -name 'asap-sbatch' -type l -print -delete
	@echo "**** Removing empty directories"
	find . -name '.git' -prune -o \( -type d -empty -print -exec rmdir {} + \)
	@echo "**** Removing all dependencies"
	-rm -rf Depend
	@echo "**** Removing setup.py build folder"
	-rm -rf build


Depend/$(OBJDIR)/depend.timestamp: depend.CHANGES
	@echo ''
	@echo 'ERROR: The dependencies have changed. These are the last changes:'
	@echo ''
	@echo 'Date      Version    Description'
	@tail -n 3 depend.CHANGES
	@echo ''
	@echo ''
	@echo 'INSTRUCTIONS:'
	@echo ''
	@echo 'Please run'
	@echo '    make depend'
	@echo 'and then try compiling again.'
	@echo ''
	@echo ''
	exit 1


depend: Depend/$(OBJDIR) depend-serial depend-parallel
	touch Depend/$(OBJDIR)/depend.timestamp

depend-maybe:
	$(MAKE) -q "Depend/$(OBJDIR)/depend.timestamp" || $(MAKE) depend

depend-serial:
	@echo "Creating dependencies for serial version (hidden for clarity)"
	@($(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_BASICS:%=Basics/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Basics/$(OBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_POTENTIALS:%=Potentials/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Potentials/$(OBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_TOOLS:%=Tools/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Tools/$(OBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_INTERFACE:%=Interface/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Interface/$(OBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_BRENNER:%=Brenner/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Brenner/$(OBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(SERIAL_INTERFACE:%=Interface/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Interface/$(OBJDIR)/\1@') \
	 | $(DEPENDCLEAN) > Depend/$(OBJDIR)/make.depend
ifdef ASAP_KIM_INC
	@$(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_OPENKIM:%=OpenKIMimport/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@OpenKIMimport/$(OBJDIR)/\1@' \
		| $(DEPENDCLEAN) >> Depend/$(OBJDIR)/make.depend
endif

depend-parallel: 
	@echo ""
	@echo ""
	@echo "PLEASE NOTE: If mpi is not installed, errors will be generated"
	@echo "when running the following commands.  They can be ignored."
	@echo ""
	@echo ""
	@sleep 2
	@echo "Creating dependencies for parallel version (hidden for clarity)"
	@($(DEPENDMPICXX) $(DEPENDFLAG) $(CXXSRC_PARALLEL:%=Parallel/%) $(INCLUDES) $(MPIINCLUDES)\
		| sed -e 's@^\(.*\.o:\)@Parallel/$(PAROBJDIR)/\1@'; \
	 $(DEPENDMPICXX) $(DEPENDFLAG) $(INCLUDES) $(MPIINCLUDES) \
		$(CXXSRC_PARINTERFACE:%=ParallelInterface/%) \
		| sed -e 's@^\(.*\.o:\)@ParallelInterface/$(PAROBJDIR)/\1@') \
	 | $(DEPENDCLEAN) > Depend/$(OBJDIR)/make.parallel.depend
ifneq ($(PAROBJDIR),$(OBJDIR))
	@echo "Creating dependencies for parallel version (part 2)."
	@($(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_BASICS:%=Basics/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Basics/$(PAROBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_POTENTIALS:%=Potentials/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Potentials/$(PAROBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_TOOLS:%=Tools/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Tools/$(PAROBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_INTERFACE:%=Interface/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Interface/$(PAROBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_BRENNER:%=Brenner/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Brenner/$(PAROBJDIR)/\1@'; \
	 $(DEPENDCXX) $(DEPENDFLAG) $(SERIAL_INTERFACE:%=Interface/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@Interface/$(PAROBJDIR)/\1@') \
	 | $(DEPENDCLEAN) >> Depend/$(OBJDIR)/make.parallel.depend
ifdef ASAP_KIM_INC
	@$(DEPENDCXX) $(DEPENDFLAG) $(CXXSRC_OPENKIM:%=OpenKIMimport/%) $(INCLUDES) \
		| sed -e 's@^\(.*\.o:\)@OpenKIMimport/$(PAROBJDIR)/\1@' \
		| $(DEPENDCLEAN) >> Depend/$(OBJDIR)/make.parallel.depend
endif
endif

$(BINDIR): 
	test -d $(BINDIR) || mkdir $(BINDIR)

Depend:
	test -d Depend || mkdir Depend

Depend/$(OBJDIR): Depend
	test -d Depend/$(OBJDIR) || mkdir Depend/$(OBJDIR)

-include Depend/$(OBJDIR)/make.depend
-include Depend/$(OBJDIR)/make.parallel.depend

Basics/$(OBJDIR)/%.o: Basics/%.cpp
	$(CXX) -c $(CXXFLAGS) $(INCLUDES) -o $@ $<

Basics/$(OBJDIR)/%.o: Basics/%.c
	$(CC) -c $(CFLAGS) $(INCLUDES) -o $@ $<

Potentials/$(OBJDIR)/%.o: Potentials/%.cpp
	$(CXX) -c $(CXXFLAGS) $(INCLUDES) -o $@ $<

Tools/$(OBJDIR)/%.o: Tools/%.cpp
	$(CXX) -c $(CXXFLAGS) $(INCLUDES) -o $@ $<

Brenner/$(OBJDIR)/%.o: Brenner/%.cpp 
	$(CXX) -c $(CXXFLAGS) $(INCLUDES) -o $@ $<

PTM/$(OBJDIR)/%.o: PTM/%.cpp 
	$(CXX) -c $(CXXFLAGS) $(INCLUDES) -o $@ $<

PTM/$(OBJDIR)/%.o: PTM/qcprot/%.cpp 
	$(CXX) -c $(CXXFLAGS) $(INCLUDES) -o $@ $<

PTM/$(OBJDIR)/%.o: PTM/voronoi/%.cpp 
	$(CXX) -c $(CXXFLAGS) $(INCLUDES) -o $@ $<

Interface/$(OBJDIR)/%.o: Interface/%.cpp
	$(CXX) -c $(CXXFLAGS) $(IFACEFLAGS) $(INCLUDES) -o $@ $<

ifdef ASAP_KIM_INC
OpenKIMimport/$(OBJDIR)/%.o: OpenKIMimport/%.cpp
	$(CXX) -c $(CXXFLAGS) $(IFACEFLAGS) $(INCLUDES) -o $@ $<
endif

ifneq ($(PAROBJDIR),$(OBJDIR))
# If we need to compile the common object in a different way for
# the parallel version, this is handled here.
Basics/$(PAROBJDIR)/%.o: Basics/%.cpp
	$(MPICXX) -c $(MPICXXFLAGS) $(INCLUDES) -o $@ $<

Basics/$(PAROBJDIR)/%.o: Basics/%.c
	$(MPICC) -c $(MPICFLAGS) $(INCLUDES) -o $@ $<

Potentials/$(PAROBJDIR)/%.o: Potentials/%.cpp
	$(MPICXX) -c $(MPICXXFLAGS) $(INCLUDES) -o $@ $<

Tools/$(PAROBJDIR)/%.o: Tools/%.cpp
	$(MPICXX) -c $(MPICXXFLAGS) $(INCLUDES) -o $@ $<

Brenner/$(PAROBJDIR)/%.o: Brenner/%.cpp 
	$(MPICXX) -c $(MPICXXFLAGS) $(BRENNERCFLAGS) $(INCLUDES) -o $@ $<

PTM/$(PAROBJDIR)/%.o: PTM/%.cpp 
	$(MPICXX) -c $(MPICXXFLAGS) $(INCLUDES) -o $@ $<

PTM/$(PAROBJDIR)/%.o: PTM/qcprot/%.cpp 
	$(MPICXX) -c $(MPICXXFLAGS) $(INCLUDES) -o $@ $<

PTM/$(PAROBJDIR)/%.o: PTM/voronoi/%.cpp 
	$(MPICXX) -c $(MPICXXFLAGS) $(INCLUDES) -o $@ $<

Interface/$(PAROBJDIR)/%.o: Interface/%.cpp
	$(MPICXX) -c $(MPICXXFLAGS) $(IFACEFLAGS) $(INCLUDES) -o $@ $<

ifdef ASAP_KIM_INC
OpenKIMimport/$(PAROBJDIR)/%.o: OpenKIMimport/%.cpp
	$(CXX) -c $(CXXFLAGS) $(IFACEFLAGS) $(INCLUDES) -o $@ $<
endif
endif

Parallel/$(PAROBJDIR)/%.o: Parallel/%.cpp 
	$(MPICXX) -c $(MPICXXFLAGS) $(INCLUDES) $(MPIINCLUDES) -o $@ $<

Parallel/$(PAROBJDIR)/%.o: Parallel/%.c 
	$(MPICC) -c $(MPICFLAGS) $(INCLUDES) $(MPIINCLUDES) -o $@ $<

ParallelInterface/$(PAROBJDIR)/%.o: ParallelInterface/%.cpp 
	$(MPICXX) -c $(MPICXXFLAGS) $(IFACEFLAGS) $(INCLUDES) $(MPIINCLUDES) -o $@ $<

ParallelInterface/$(PAROBJDIR)/%.o: ParallelInterface/%.c 
	$(MPICC) -c $(MPICFLAGS) $(IFACEFLAGS) $(INCLUDES) $(MPIINCLUDES) -o $@ $<

Basics/$(OBJDIR):
	mkdir Basics/$(OBJDIR)

Potentials/$(OBJDIR):
	mkdir Potentials/$(OBJDIR)

Tools/$(OBJDIR):
	mkdir Tools/$(OBJDIR)

PTM/$(OBJDIR):
	mkdir PTM/$(OBJDIR)

Interface/$(OBJDIR):
	mkdir Interface/$(OBJDIR)

Brenner/$(OBJDIR):
	mkdir Brenner/$(OBJDIR)

OpenKIMimport/$(OBJDIR):
	mkdir OpenKIMimport/$(OBJDIR)

ifneq ($(PAROBJDIR),$(OBJDIR))
Basics/$(PAROBJDIR):
	mkdir Basics/$(PAROBJDIR)

Potentials/$(PAROBJDIR):
	mkdir Potentials/$(PAROBJDIR)

Tools/$(PAROBJDIR):
	mkdir Tools/$(PAROBJDIR)

PTM/$(PAROBJDIR):
	mkdir PTM/$(PAROBJDIR)

Interface/$(PAROBJDIR):
	mkdir Interface/$(PAROBJDIR)

Brenner/$(PAROBJDIR):
	mkdir Brenner/$(PAROBJDIR)

OpenKIMimport/$(PAROBJDIR):
	mkdir OpenKIMimport/$(PAROBJDIR)
endif

Parallel/$(PAROBJDIR):
	mkdir Parallel/$(PAROBJDIR)

ParallelInterface/$(PAROBJDIR):
	mkdir ParallelInterface/$(PAROBJDIR)


########################################################
####
####  SPECIAL TARGETS:  Debugging, profiling etc
####
########################################################

version:
	@echo "ASAP version `$(PYTHON) Python/asap3/version.py`"

info:
	@echo "COMPILER = $(COMPILER)"
	@echo "HAS_ICC = $(HAS_ICC)"
	@echo "HAS_ICX = $(HAS_ICX)"
	@echo "PYTHON = $(PYTHON)"
	@echo "ARCH = $(ARCH)"
	@echo "HOSTNAME = $(HOSTNAME)"
	@echo "KERNELNAME = $(KERNELNAME)"
	@echo "PYVER = $(PYVER)"
	@echo "OBJDIR = $(OBJDIR)"
	@echo "VERSION = $(VERSION)"
	@echo "CXXFLAGS = $(CXXFLAGS)"
	@echo "INCLUDES = $(INCLUDES)"
	@echo "LIBS = $(LIBS)"
