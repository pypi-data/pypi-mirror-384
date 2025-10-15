#!/usr/bin/env bash

set -e # exit on first error
# set -x # plot every command (debugging purposes)

if [[ "$1" == "help" || "$1" == "-help" || "$1" == "--help" ]]; then

    echo ""
    echo "usage: asgardrun.sh <executable> <options>"
    echo "usage: asgardrun.sh -plt \"<plotter opts>\" <executable> <options>"
    echo ""
    echo "runs the executable file with the given options"
    echo "adding '-of _asgardplt.h5' to save the output in a temp-file"
    echo "then calls the plotter on the temp file"
    echo "starting with the -plt switch allows passing options to the final plotter"
    echo "for example: asgardrun.sh -plt -grid continuity -dims 2 -l 5"
    echo ""

    exit 0;
fi

plt_opts=""

if [[ "$1" == "-plt" ]]; then
    plt_opts="$2"
    shift
    shift
fi

exename=$1

shift

# if an output file exists, remove it
rm -fr ./_asgardplt.h5

# check if using absolute or relative path
if [[ "$exename" == /* ]]; then
    $exename "$@" -of _asgardplt.h5
else
    ./$exename "$@" -of _asgardplt.h5
fi

if [ ! -f "./_asgardplt.h5" ]; then
    echo "ERROR: the executable '$exename' did not generate an output file"
    exit 1
fi

@Python_EXECUTABLE@ -m asgard _asgardplt.h5 $plt_opts

