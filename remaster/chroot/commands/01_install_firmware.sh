#!/bin/bash
# This only assumes that linux firmware is under /lib/firmware
# should be true for most / all distributions

PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}

FIRMWARE_SRC_DIR=${PROG_DIR}/../firmware
FIRMWARE_DEST_DIR=/lib/firmware

if [ ! -d ${FIRMWARE_SRC_DIR} ]; then
    echo "FIRMWARE_SRC_DIR not a directory: $FIRMWARE_SRC_DIR"
    exit 0
fi
FIRMWARE_SRC_DIR=$(readlink -e $FIRMWARE_SRC_DIR)
test "$(ls -A $FIRMWARE_SRC_DIR)"
if [ $? -ne 0 ]; then
    echo "No firmware files to copy: $FIRMWARE_SRC_DIR"
    exit 0
fi

cp -rv ${FIRMWARE_SRC_DIR}/. $FIRMWARE_DEST_DIR/
