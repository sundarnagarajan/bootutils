#!/bin/bash

apt-get update && \
apt-get -y install grub-efi-ia32-bin grub-efi-amd64-bin
if [ $? -ne 0 ]; then
	apt-get -f install
fi
