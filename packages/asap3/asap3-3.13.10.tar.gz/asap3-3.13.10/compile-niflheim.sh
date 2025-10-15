#!/bin/bash

# Compiling ASAP for Niflheim.
#
# This script assumes that you are already on Nifhleim and in the ASAP 
# directory. 

NIFHOSTS="sylg.fysik.dtu.dk surt.fysik.dtu.dk svol.fysik.dtu.dk"
NIFAMDHOSTS="fjorm.fysik.dtu.dk"
NIFEXTRA="slid2.fysik.dtu.dk slid.fysik.dtu.dk thul.fysik.dtu.dk"
OK=n
for H in $NIFHOSTS $NIFEXTRA; do
    if [[ "$H" == `hostname` ]]; then
	OK=y
    fi
done
if [[ $OK == n ]]; then
    echo "Apparently not on a Niflheim compile node."
    echo "This script should be executed on one of these machines:"
    echo "   $NIFHOSTS"
    echo "but this is `hostname`"
    exit 1
fi

if [[ -z "$EBROOTINTEL" ]]; then
    echo "Intel compilers NOT set - enabling compilation on AMD hosts."
    NIFHOSTS="$NIFHOSTS $NIFAMDHOSTS"
fi

# Now loop over all machines and compile.  Note that `pwd` is executed
# when the command is parsed, i.e. on this machine!

CMD="cd `pwd` && make depend-maybe && make -j16 all"
if [[ -n "$VIRTUAL_ENV" ]] ; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
    CMD="source \"$VIRTUAL_ENV\"/bin/activate && $CMD"
fi
echo "Compilation command: $CMD"

for H in $NIFHOSTS; do
    echo
    echo "**** Compiling on $H ****"
    echo
    ssh $H "$CMD"
    if [[ $? -ne 0 ]]; then
	echo 
	echo '!!!!!!!  COMPILATION FAILED  !!!!!!!!'
	exit 1
    fi
done

