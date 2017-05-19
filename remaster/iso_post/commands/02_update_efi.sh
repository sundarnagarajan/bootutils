#!/bin/bash
PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}

EFI_DIR=${PROG_DIR}/../efi

if [ ! -d ${EFI_DIR} ]; then
    echo "EFI_DIR not a directory: $EFI_DIR"
    exit 0
fi
EFI_DIR=$(readlink -e $EFI_DIR)

ISO_EXTRACT_DIR=${PROG_DIR}/../..
ISO_EXTRACT_DIR=$(readlink -e $ISO_EXTRACT_DIR)
GRUB_CFG=${ISO_EXTRACT_DIR}/boot/grub/grub.cfg

if [ -f ${GRUB_CFG} ]; then
    \cp -f ${GRUB_CFG} ${EFI_DIR}/boot/grub/grub.cfg
fi
\cp -a ${EFI_DIR}/. ${ISO_EXTRACT_DIR}/.
