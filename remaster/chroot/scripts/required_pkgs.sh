#!/bin/bash
REQD_PKGS="grub-efi-ia32-bin grub-efi-amd64-bin grub-pc-bin grub2-common grub-common util-linux parted gdisk mount xorriso genisoimage squashfs-tools rsync"

MISSING_PKGS=$(dpkg -l $REQD_PKGS | sed -e '1,4d'| grep -v '^ii' | awk '{printf("%s ", $2)}')
if [ -n "${MISSING_PKGS%% }" ]; then
	INSTALL_CMD="sudo apt-get install $MISSING_PKGS"
else
	INSTALL_CMD="All required packages are already installed\nRequired packages: $REQD_PKGS"
fi
echo -e "$INSTALL_CMD"
