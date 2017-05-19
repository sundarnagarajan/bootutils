#!/bin/bash
PROG_PATH=${PROG_PATH:-$(readlink -e $0)}
PROG_DIR=${PROG_DIR:-$(dirname ${PROG_PATH})}
PROG_NAME=${PROG_NAME:-$(basename ${PROG_PATH})}

apt-get update 1>/dev/null
apt-get -y install grub-efi-ia32-bin grub-efi-amd64-bin grub-pc-bin 1>/dev/null
if [ $? -ne 0 ]; then
	apt-get -f install
fi
