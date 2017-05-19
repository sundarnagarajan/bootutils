#!/bin/bash
PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}

(apt-get update && apt-get -y upgrade && apt-get dist-upgrade -y) 1>/dev/null
