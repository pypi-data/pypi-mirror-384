# Copyright (C) 2025 Jakob Schiotz and Computational
# Atomic-scale Materials Design (CAMD), Department of Physics,
# Technical University of Denmark.  Email: schiotz@fysik.dtu.dk
#
# This file is part of Asap version 3.
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# version 3 as published by the Free Software Foundation.  Permission
# to use other versions of the GNU Lesser General Public License may
# granted by Jakob Schiotz or the head of department of the
# Department of Physics, Technical University of Denmark, as
# described in section 14 of the GNU General Public License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# and the GNU Lesser Public License along with this program.  If not,
# see <http://www.gnu.org/licenses/>.

import sys
import os
import string
import subprocess
import socket   # Just for the hostname
import argparse
from asap3 import __version__

asap_sbatch_doc = \
"""asap-sbatch: Submit an Asap job to Niflheim.

Usage:
    asap-sbatch [options] job.py [job-command-line]

where options are any options that could otherwise be passed to sbatch
and job-command-line is passed on to the job.  The job file MUST end in .py

In addition to the usual sbatch options, an option of the form --ASAP=X
may be passed, where X is one of the letters S, P or T specifying a
serial, parallel or multithreaded application (overriding the usual
detection).
"""

def asap_sbatch(prog='asap-sbatch', desc=asap_sbatch_doc, 
                version=__version__, args=None):
    "The asap-sbatch command"
    # Parsing of arguments is done manually, as we need to handle
    # a command line of the form
    #   asap-sbatch [arguments] script.py [script-arguments]
    # where the arguments may both be arguments to asap-sbatch
    # and unknown arguments passed on to the sbatch command.
    # argparse can help with this, but requires almost as much
    # manual work, so we just keep the orginal code from
    # scripts/asap-sbatch

    options = []
    job = []
    script = None
    asapargs = ""
    quiet = False
    private_production = False

    parse_partition = PartitionSanity()
                        
    # Parse the asap-sbatch command line
    if args == None:
        args = sys.argv[1:]
    for arg in args:
        if script is None:
            if arg.lower().endswith('.py'):
                script = arg
            else:
                if arg.upper().startswith("--ASAP="):
                    asapargs = arg[7:].upper()
                elif arg.lower() == "--quiet":
                    quiet = True
                elif arg.lower() == "--production":
                    # Developers only!
                    private_production = True
                else:
                    options.append(arg)
        else:
            job.append(arg)

    if script is None:
        raise ValueError("Cannot recognize the job script on the command line.  It must end with .py")

    # Construct the sbatch command line.
    sbatch = ["sbatch"]
    sbatch.extend(options)

    # Construct the job command line.  All options are single-quoted in
    # case they contain spaces or similar.
    jobcommand = script
    for arg in job:
        jobcommand = jobcommand + " '" + arg + "'"

    # Find default name for job
    defname = os.path.splitext(os.path.basename(script))[0]
    assert script.endswith(defname+'.py')
    # Remove weird characters
    for i, c in enumerate(defname):
        if not c in string.ascii_letters+string.digits:
            defname = defname[:i] + "_" + defname[i+1:]

    # Parse the script, collect any #SBATCH lines.
    slurmlines = ["#SBATCH -J "+defname+"\n"]
    for line in open(script):
        if line.startswith("#SBATCH"):
            slurmlines.append(line)
            if '--partition' in line:
                parse_partition(line)
        elif line.startswith("#PBS"):
            print("WARNING: PBS job control line found: ", line.strip())
            print("Passing it on to sbatch and hoping for the best ...")
            slurmlines.append(line)

    # Look for '--partition' arguments on the command line
    for opt in sbatch:
        if '--partition' in opt:
            parse_partition(opt)

    # Check that the last found partition specification is compatible with the
    # submitting node
    parse_partition.check()

    # Construct the script to be submitted.
    submitscript = "#!/bin/bash -l\n"
    for line in slurmlines:
        submitscript += line

    venv = os.getenv('VIRTUAL_ENV')
    if venv:
        if not quiet:
            print("Virtual environment detected:", venv)
        submitscript += 'source "{:s}/bin/activate"'.format(venv)
        
    if private_production:
        # Developers only!
        if not quiet:
            print("Production mode enabled on Niflheim7")
        submitscript += "export PYTHONPATH=`echo $PYTHONPATH | sed 's/development/production/g'`\n"
        submitscript += "export PATH=`echo $PATH | sed 's/development/production/g'`\n"

    submitscript += "\n"
    #submitscript += "mpirun -mca pml cm -mca mtl psm2 asap-python {0}\n".format(jobcommand)
    submitscript += 'echo "*** Simulation started at: `date`"\n' 
    submitscript += "mpirun python3 {0}\n".format(jobcommand)
    submitscript += 'echo "*** Simulation ended at: `date`"\n' 

    if "ASAPSBATCHVERBOSE" in os.environ and not quiet:
        print("Submitting job:")
        for line in submitscript.split("\n"):
            print("   ", line)
        print("Submitting with the command: ", " ".join(sbatch))
    print()

    sbatchproc = subprocess.Popen(sbatch, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, close_fds=True)
    (out, err) = sbatchproc.communicate(submitscript.encode())
    errcode = sbatchproc.wait()
    if errcode:
        print("sbatch failed with error code", str(errcode), file=sys.stderr)
        print("Command line:", sbatch, file=sys.stderr)
        print("Standard error of command:")
        print(err.decode(errors='replace'))
        sys.exit("sbatch failed")
    print(out.decode())    

# Partition sanity check
class PartitionSanity:
    """Check that the submitting host and the SLURM partition match.

    On some SLURM installations, the architecture of the submitting node
    must match the architecture of the desired computate node(s).
    
    If the hostname of the submitting node is in the table below, 
    the partition name must be correct.  Unknown submit nodes always
    pass the test.
    """
    #expected_partitions = {'sylg.fysik.dtu.dk': ['xeon24', 'xeon24_512',
    #                                             'xeon24_test'],
    #                       'thul.fysik.dtu.dk': ['xeon16', 'xeon16_128', 
    #                                             'xeon16_256'],
    #                       'fjorm.fysik.dtu.dk': ['xeon8']}
    expected_partitions = {}
    def __init__(self):
        self.part = "<default>"
    
    def __call__(self, s):
        words = s.split()
        for w in words:
            if w.startswith('--partition='):
                _, part = w.split('=')[:2]
                self.part = part
    
    def check(self):
        hostname = socket.getfqdn()
        if hostname in self.expected_partitions:
            expected = self.expected_partitions[hostname]
            if self.part not in expected:
                print("You are submitting from the wrong login node:", file=sys.stderr)
                print("   Login node:", hostname, file=sys.stderr)
                print("   Matching partitions:", str(expected), file=sys.stderr)
                print("   Specified partition:", self.part, file=sys.stderr)
                print("", file=sys.stderr)
                print("Please submit this job from login node", file=sys.stderr)
                found = False
                for k, v in self.expected_partitions.items():
                    if self.part in v:
                        print("  ", k, file=sys.stderr)
                        found = True
                if not found:
                    print("   <no acceptable login node found>")
                    print()
                    print("Does the partition '{}' exist?".format(self.part))
                sys.exit(1)





if 0:
    parser = argparse.ArgumentParser(prog=prog, description=desc)
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s-{version}')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="Don't print stuff, just do it.")
    parser.add_argument('--ASAP', action="extend", nargs="+", type=str)
    # parser.add_argument('script')
    # parser.add_argument("script_args", nargs=argparse.REMAINDER)

    args, unknown = parser.parse_known_args(args)
    # Now unknown is a list of unparsed arguments, including the script name.
    # Any argument bef

    script = args.script
    if not script.endswith('.py'):
        raise ValueError('Cannot recognize the job script on the command line.'
                         '  It must end with .py')

    # Construct the job command line.  All options are single-quoted in
    # case they contain spaces or similar.
    sbatch = ["sbatch"]
    jobcommand = script
    for arg in args.script_args:
        jobcommand = jobcommand + " '" + arg + "'"

    # Find default name for job
    defname = os.path.splitext(os.path.basename(script))[0]
    assert script.endswith(defname+'.py')
    # Remove weird characters
    for i, c in enumerate(defname):
        if not c in string.ascii_letters+string.digits:
            defname = defname[:i] + "_" + defname[i+1:]

