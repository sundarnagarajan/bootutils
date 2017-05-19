#!/bin/bash
# This only assumes Ubuntu/Debian naming convention for kernel
# and initrd files. Also assumes Ubuntu-specific location for
# kernel and initrd in ISO (/casper)
# Expects env var REMASTER_ISO_CHROOT_DIR to be set

PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}

ISO_EXTRACT_DIR=${PROG_DIR}/../..
ISO_EXTRACT_DIR=$(readlink -e $ISO_EXTRACT_DIR)
REMASTER_DIR=/root/remaster
KP_LIST=kernel_pkgs.list

if [ -z "$REMASTER_ISO_CHROOT_DIR" ]; then
    echo "REMASTER_ISO_CHROOT_DIR not set"
    exit 0
fi
if [ ! -d "$REMASTER_ISO_CHROOT_DIR" ]; then
    echo "REMASTER_ISO_CHROOT_DIR not a directory: $REMASTER_ISO_CHROOT_DIR"
    exit 0
fi

if [ ! -f ${REMASTER_ISO_CHROOT_DIR}/.${REMASTER_DIR}/${KP_LIST} ]; then
    echo "Kernel not updated"
    exit 0
fi

\cp ${REMASTER_ISO_CHROOT_DIR}/boot/vmlinuz-* ${ISO_EXTRACT_DIR}/casper/vmlinuz.efi
\cp ${REMASTER_ISO_CHROOT_DIR}/boot/initrd.img-* ${ISO_EXTRACT_DIR}/casper/initrd.lz
