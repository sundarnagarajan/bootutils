#!/bin/bash
PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}

REMASTER_DIR=/root/remaster


SCRIPTS_DIR=${PROG_DIR}/../scripts
if [ ! -d ${SCRIPTS_DIR} ]; then
    echo "SCRIPTS_DIR not a directory: $SCRIPTS_DIR"
    exit 0
fi
SCRIPTS_DIR=$(readlink -e $SCRIPTS_DIR)

\cp -r $SCRIPTS_DIR ${REMASTER_DIR}/
