ASAP - Large scale molecular dynamics
=====================================

ASAP is a calculator for doing large-scale molecular dynamics (MD) within
the Atomic Simulation Environment.  The focus of ASAP is on
solid-state physics (as opposed to molecular chemistry), and in
particular metallic systems.

The documentation and manual can be found on the ASAP webpage: 
https://wiki.fysik.dtu.dk/asap

This project depends on the Atomic Simulation Environment (ASE):

* ASE homepage: https://ase-lib.org/

* ASE GitLab page: https://gitlab.com/ase/ase


INSTALLATION
------------

Please read the online installation guide:
https://asap3.readthedocs.io/en/latest/installation/Installation.html

Quick summary:

::

   pip install asap3 --user
   

MANUAL AND DOCUMENTATION
------------------------

https://asap3.readthedocs.io/en/latest/manual/Manual.html


DIRECTORY STRUCTURE
-------------------

The code is organized as follows

Basics:

  The source files for the central parts of Asap, including the calculators.

Brenner:

  The library for the Brenner potential.

Debug:

  Files helpful when debugging.

Examples:

  Example scripts.

Interface:

  The C++/Python interface.

OpenKIMexport:

  Files used for autogenerating code to contribute Asap potentials to
  the OpenKIM project.

OpenKIMimport:

  Using OpenKIM potentials within Asap.

Parallel:

  Source code for parallel simulations using MPI.

ParallelInterface:

  The C++/Python interface for parallel simulation

Python:

  The Python modules.

Test:

  The test suite.

Tools:

  C++ parts of analysis tools

scripts:

  Python scripts, mainly useful for the developers.
  

License
-------

This project is released under the Lesser GNU Public LIcense
version 3.

A few files are dual licensed and can also be used under the Common Development
and Distribution License (CDDL) version 1.0, at the choice of the
user.

The license is found in the files ``COPYING`` and ``COPYING.LESSER``.

