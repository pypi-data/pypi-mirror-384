#!/bin/bash
PYTHON_VERSION=3.13

xasm_owd=$(pwd)
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

mydir=$(dirname $bs)
xasm_fulldir=$(readlink -f $mydir)
. ${xasm_fulldir}/checkout_common.sh

(cd ${xasm_fulldir}/../.. && setup_version python-xdis master)
checkout_finish master
